# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Accepting a Departmental Need starts that department's Draft plan.

The Head of Department who accepts a Need has already decided the department
has something to plan, so Planning does not then ask them to press **Start
departmental plan**: it subscribes to the published
`DepartmentalNeedAccepted.v2` event and opens the Draft itself, with the
accepted requirement already in it.

These tests drive the real publisher, so they exercise the whole chain — the
`Departmental Need Event` row, the `doc_events` subscriber and the Planning
command it calls — rather than the handler in isolation.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.services import events as nds_events
from kentender_procurement.procurement_planning.services import dpp_lifecycle
from kentender_procurement.procurement_planning.tests import fixtures as fx

NEED_TWO = "NEED-PLNT-0002"
NEED_TWO_V1 = "NEED-PLNT-0002-V1"


def key() -> str:
	return uuid4().hex


class DppAutostartCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self._wipe_events()
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(self._wipe_events)

	def _wipe_events(self) -> None:
		"""The published outbox rows these tests mint (NDS-owned, and the
		source `current_accepted_sources` replays from)."""
		frappe.db.delete("Departmental Need Event", {"departmental_need": ("in", (fx.NEED, NEED_TWO))})

	# --- fixtures ----------------------------------------------------------

	def accept(self, need: str = "", revision: str = "") -> str:
		"""Publish the acceptance exactly as `review_need` does (NDS §7.1)."""
		need_doc = frappe.get_doc("Departmental Need", need or fx.NEED)
		version = frappe.get_doc("Departmental Need Revision", revision or fx.NEED_V1)
		return nds_events.publish_accepted(need_doc, version)

	def second_need(self) -> None:
		"""A second accepted Need in the same department and year."""
		if not frappe.db.exists("Departmental Need", NEED_TWO):
			frappe.get_doc(
				{
					"doctype": "Departmental Need", "need_reference": NEED_TWO, "organisation_unit": fx.OU_ALPHA,
					"financial_year": fx.FY_OPEN, "current_state": "Accepted for planning", "record_version": 1,
					"fixture_namespace": fx.NS,
				}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Departmental Need Revision", NEED_TWO_V1):
			frappe.get_doc(
				{
					"doctype": "Departmental Need Revision", "need_revision_id": NEED_TWO_V1, "departmental_need": NEED_TWO,
					"revision_number": 1, "revision_status": "Accepted", "title": "Second test requirement",
					"description": "Procure and implement the second test requirement.",
					"expected_operational_result": "The department can operate the second tested capability.",
					"indicative_quantity": 2, "unit": fx.UNIT, "required_by_date": "2102-05-31",
					"fixture_namespace": fx.NS,
				}
			).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Departmental Need", NEED_TWO,
			{"current_revision": NEED_TWO_V1, "current_accepted_revision": NEED_TWO_V1}, update_modified=False,
		)
		self.addCleanup(frappe.db.delete, "Departmental Need Revision", {"name": NEED_TWO_V1})
		self.addCleanup(frappe.db.delete, "Departmental Need", {"name": NEED_TWO})
		self.addCleanup(frappe.db.delete, "Need Planning Intake Projection", {"departmental_need": NEED_TWO})

	def root(self):
		name = frappe.db.get_value(
			"Departmental Plan", {"organisation_unit": fx.OU_ALPHA, "fiscal_year": fx.FY_OPEN}, "name"
		)
		return frappe.get_doc("Departmental Plan", name) if name else None

	def entries(self, version: str) -> list[dict]:
		return frappe.get_all(
			"Departmental Plan Entry", filters={"dpp_version": version},
			fields=["need", "need_revision", "source_origin"], limit_page_length=0,
		)

	# --- the rule ----------------------------------------------------------

	def test_accepting_a_need_starts_the_departmental_plan(self):
		self.assertIsNone(self.root(), "the department starts with no plan")

		self.accept()

		root = self.root()
		self.assertIsNotNone(root, "acceptance did not start the departmental plan")
		self.assertEqual(root.current_state, "Draft")
		version = frappe.get_doc("Departmental Plan Version", root.current_version)
		self.assertEqual(version.version_status, "Draft")
		self.assertEqual(version.version_number, 1)
		# The accepted requirement is in the Draft already — the department
		# opens a plan with its work in it, not an empty shell.
		entries = self.entries(version.name)
		self.assertEqual([e["need"] for e in entries], [fx.NEED])
		self.assertEqual(entries[0]["need_revision"], fx.NEED_V1)

	def test_a_later_acceptance_joins_the_same_draft(self):
		self.accept()
		root = self.root()
		version = root.current_version

		self.second_need()
		self.accept(NEED_TWO, NEED_TWO_V1)

		self.assertEqual(self.root().name, root.name, "a second acceptance must not start a second plan")
		self.assertEqual(self.root().current_version, version, "the Draft Submission number must not move")
		self.assertEqual(
			sorted(e["need"] for e in self.entries(version)), [fx.NEED, NEED_TWO]
		)

	def test_replaying_one_acceptance_changes_nothing(self):
		event = self.accept()
		root = self.root()

		replay = dpp_lifecycle.ensure_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, trigger_event=event,
		)

		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["departmental_plan"], root.name)
		self.assertEqual(self.root().record_version, root.record_version)

	def test_a_withdrawn_plan_is_not_reopened_by_an_acceptance(self):
		"""§5.1.5 keeps reopening a withdrawn initial Draft an HoD decision."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		frappe.set_user(fx.HOD)
		dpp_lifecycle.withdraw_departmental_submission(
			dpp_version=opened["current_version"], reason="The department is not planning this year.",
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user("Administrator")

		self.accept()

		root = self.root()
		self.assertEqual(root.current_state, "Withdrawn")
		self.assertEqual(frappe.db.count("Departmental Plan Version", {"departmental_plan": root.name}), 1)

	def test_an_unknown_department_is_dropped_rather_than_failing(self):
		outcome = dpp_lifecycle.ensure_departmental_plan(
			organisation_unit="OU-DOES-NOT-EXIST", fiscal_year=fx.FY_OPEN, trigger_event=f"NDE-{key()}",
		)

		self.assertEqual(outcome["action"], "no_context")
		self.assertFalse(outcome["ok"])

	def test_the_acceptance_survives_a_failure_to_start_the_plan(self):
		"""Starting the plan is a consequence of acceptance, never a condition
		of it: a Planning failure is logged and dropped, and the published
		event — the acceptance itself — still stands."""
		with patch.object(dpp_lifecycle, "ensure_departmental_plan", side_effect=RuntimeError("planning is unwell")):
			event = self.accept()

		self.assertTrue(frappe.db.exists("Departmental Need Event", {"event_id": event}))
		self.assertIsNone(self.root())
