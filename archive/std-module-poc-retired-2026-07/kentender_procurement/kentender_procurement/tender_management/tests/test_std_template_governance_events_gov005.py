# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-005 — lifecycle audit event writer (doc 7 §13.5, §17).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005
"""

from __future__ import annotations

import json

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)


def _new_gov005_std_template(template_code: str) -> Document:
	"""Minimal ``STD Template`` row for governance tests (isolated ``template_code``)."""
	doc = frappe.new_doc("STD Template")
	doc.template_code = template_code
	doc.template_name = f"STD-GOV-005 {template_code}"
	doc.template_short_name = template_code[:12]
	doc.authority = "Test Authority"
	doc.country = "KE"
	doc.procurement_category = "WORKS"
	doc.template_family = "Works"
	doc.version_label = "1.0"
	doc.template_version = "1.0"
	doc.package_version = "1"
	doc.source_authority = "Test Authority"
	doc.package_json = "{}"
	doc.package_hash = "deadbeef" * 8
	doc.package_hash_algorithm = gov.HASH_ALGORITHM
	doc.canonicalization_version = gov.CANONICALIZATION_VERSION
	doc.lifecycle_status = gov.STATUS_IMPORTED
	doc.latest_validation_status = gov.VALIDATION_NOT_RUN
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 0
	doc.is_governed_version = 1
	doc.tender_usage_count = 0
	doc.locked_due_to_usage = 0
	doc.mutation_blocked = 0
	doc.delete_blocked = 1
	doc.payload_locked = 0
	doc.is_suspended = 0
	doc.is_historical = 0
	doc.approval_override_used = 0
	doc.is_default_active_version = 0
	doc.allowed_for_import = 1
	doc.allowed_for_tender_creation = 0
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc


class TestStdTemplateGovernanceEventsGov005(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._template_code = f"GOV005-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._template_code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._template_code):
			frappe.delete_doc("STD Template", self._template_code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_005_appends_event_and_saves(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_IMPORTED,
			event_type="import",
			payload={"detail": "x"},
			from_status=None,
			to_status=gov.STATUS_IMPORTED,
			reason="seed",
		)
		reloaded = frappe.get_doc("STD Template", self._template_code)
		rows = reloaded.get("lifecycle_events") or []
		self.assertEqual(len(rows), 1)
		row = rows[0]
		self.assertEqual(row.event_code, gov.EVT_IMPORTED)
		self.assertEqual(row.event_type, "import")
		self.assertEqual(row.actor, "Administrator")
		self.assertTrue(row.actor_roles)
		self.assertIn("Administrator", row.actor_roles.split(", "))
		self.assertEqual(row.to_status, gov.STATUS_IMPORTED)
		self.assertEqual(row.reason, "seed")
		self.assertEqual(row.package_hash, self.doc.package_hash)
		self.assertEqual(row.related_template, self._template_code)

	def test_std_gov_005_payload_json_sorted_keys(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_VALIDATION_STARTED,
			event_type="validation",
			payload={"z": 1, "a": {"nested": 2, "m": 3}},
		)
		row = (frappe.get_doc("STD Template", self._template_code).lifecycle_events or [])[-1]
		self.assertIsNotNone(row.payload_json)
		parsed = json.loads(row.payload_json)
		self.assertEqual(parsed["a"]["m"], 3)
		self.assertEqual(list(parsed.keys()), ["a", "z"])

	def test_std_gov_005_validation_run_id_from_payload(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_VALIDATION_COMPLETED,
			event_type="validation",
			payload={"validation_run_id": "STD-VAL-001", "ok": True},
		)
		row = (frappe.get_doc("STD Template", self._template_code).lifecycle_events or [])[-1]
		self.assertEqual(row.validation_run_id, "STD-VAL-001")

	def test_std_gov_005_run_id_alias(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_VALIDATION_STARTED,
			event_type="validation",
			payload={"run_id": "STD-VAL-RUN-2"},
		)
		row = (frappe.get_doc("STD Template", self._template_code).lifecycle_events or [])[-1]
		self.assertEqual(row.validation_run_id, "STD-VAL-RUN-2")

	def test_std_gov_005_accepts_template_name_string(self) -> None:
		write_std_template_lifecycle_event(
			self._template_code,
			event_code=gov.EVT_MUTATION_BLOCKED,
			event_type="guard",
			payload={},
		)
		self.assertEqual(
			len(frappe.get_doc("STD Template", self._template_code).lifecycle_events or []),
			1,
		)

	def test_std_gov_005_override_flags_on_row(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_OVERRIDE_USED,
			event_type="override",
			payload={},
			override_used=True,
			override_reason="breakglass",
		)
		row = (frappe.get_doc("STD Template", self._template_code).lifecycle_events or [])[-1]
		self.assertEqual(row.override_used, 1)
		self.assertEqual(row.override_reason, "breakglass")

	def test_std_gov_005_guest_user_rejected(self) -> None:
		write_std_template_lifecycle_event(
			self.doc,
			event_code=gov.EVT_IMPORTED,
			event_type="import",
			payload={},
		)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.ValidationError):
			write_std_template_lifecycle_event(
				self.doc,
				event_code=gov.EVT_PERMISSION_BLOCKED,
				event_type="guard",
				payload={},
			)

	def test_std_gov_005_append_only_multiple_events(self) -> None:
		write_std_template_lifecycle_event(
			self.doc, gov.EVT_IMPORTED, "a", {"i": 1}
		)
		write_std_template_lifecycle_event(
			self.doc, gov.EVT_VALIDATION_STARTED, "b", {"i": 2}
		)
		final = frappe.get_doc("STD Template", self._template_code)
		self.assertEqual(len(final.lifecycle_events), 2)
		self.assertEqual(final.lifecycle_events[0].event_type, "a")
		self.assertEqual(final.lifecycle_events[1].event_type, "b")
