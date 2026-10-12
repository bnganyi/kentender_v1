# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-008 / AUD-XC-014 / AUD-XC-015 — the Departmental Needs records change
only through the Needs commands, and are read only inside the NDS §6 matrix.

Drives the same paths a `PUT /api/resource`, `DELETE /api/resource` and
`frappe.client` call reach (`frappe.client.set_value`, `.delete`, a document
`save`), as the business roles the audit named, and proves the command route
still works."""

from __future__ import annotations

import frappe
import frappe.tests
from frappe.utils import now_datetime

from kentender_core.services.command_write_guard import CommandWriteError, maintenance_write
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import AUTHOR, FY, PLANNER, REVIEWER
from kentender_procurement.departmental_needs.services import lifecycle, need_authorization
from kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle import (
	REASON,
	DepartmentalNeedsCommandCase,
)
from kentender_procurement.departmental_needs.write_family import NEEDS_WRITE_FAMILY

BUSINESS_WRITERS = (AUTHOR, REVIEWER, "Administrator")

NEEDS_FAMILY = (
	"Departmental Need", "Departmental Need Revision", "Departmental Need Review Task", "Need Withdrawal Request",
	"Need Planning Usage Projection", "Need Planning Intake Projection", "Need Planning Disposition Projection",
	# RG-08: the outbox and the decision record are command-only too
	"Departmental Need Event", "Departmental Need Decision",
)

RIGHTS = ("write", "create", "delete", "submit", "cancel", "amend", "share")


def rights_held(doctypes):
	"""Every (doctype, role, right) the DocPerm and Custom DocPerm tables grant
	among the write-side rights. Read from the tables, not from meta, so a
	Custom DocPerm added after the last migrate is seen too."""
	held = []
	for table in ("DocPerm", "Custom DocPerm"):
		for row in frappe.get_all(table, filters={"parent": ("in", list(doctypes))}, fields=["parent", "role", *RIGHTS]):
			held.extend((row.parent, row.role, right) for right in RIGHTS if row.get(right))
	return held



class TestNeedsDocPermsGrantNoWrite(frappe.tests.IntegrationTestCase):
	"""The DocPerm is the first lock (AUD-XC-008, AUD-XC-014): after a migrate
	no role, System Manager included, holds a write-side right on a
	command-only Needs record."""

	def test_no_role_holds_a_write_side_right_on_a_needs_record(self):
		self.assertEqual(rights_held(NEEDS_FAMILY), [])


class NeedsWorld(DepartmentalNeedsCommandCase):
	"""An accepted Need with an open withdrawal request, plus a Draft Need."""

	def build_world(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"], expected_version=accepted["record_version"], idempotency_key=self.key(), reason=REASON,
		)
		draft = self.create()
		frappe.set_user("Administrator")
		self.need = accepted["need"]
		self.revision = accepted["current_accepted_revision"]
		self.request = requested["withdrawal_request"]
		self.task = requested["task"]
		self.draft_need = draft["need"]
		self.draft_revision = draft["current_revision"]
		return accepted


class TestNeedRecordsAreCommandOnly(NeedsWorld):
	def setUp(self):
		super().setUp()
		self.build_world()

	def assert_set_value_refused(self, user, doctype, name, fieldname, value):
		before = frappe.db.get_value(doctype, name, fieldname)
		frappe.set_user(user)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value(doctype, name, fieldname, value)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(doctype, name, fieldname), before)

	def test_lifecycle_fields_cannot_be_set_over_the_client_api(self):
		cases = (
			("Departmental Need", lambda s: s.draft_need, "current_state", "Accepted for planning"),
			("Departmental Need", lambda s: s.need, "current_accepted_revision", lambda s: s.draft_revision),
			("Departmental Need Revision", lambda s: s.revision, "revision_status", "Draft"),
			("Departmental Need Revision", lambda s: s.draft_revision, "revision_status", "Accepted"),
			("Departmental Need Review Task", lambda s: s.task, "status", "Completed"),
			("Need Withdrawal Request", lambda s: s.request, "status", "Approved"),
		)
		for user in BUSINESS_WRITERS:
			for doctype, name_of, fieldname, value in cases:
				with self.subTest(user=user, doctype=doctype, field=fieldname):
					offered = value(self) if callable(value) else value
					self.assert_set_value_refused(user, doctype, name_of(self), fieldname, offered)

	def test_a_document_save_is_refused_by_the_guard_whoever_saves_it(self):
		# DocPerm is the first lock; this proves the second one on its own.
		cases = (
			("Departmental Need", "draft_need", {"current_state": "Accepted for planning"}),
			("Departmental Need Revision", "revision", {"revision_status": "Draft", "title": "Changed after acceptance"}),
			("Departmental Need Review Task", "task", {"status": "Completed"}),
			("Need Withdrawal Request", "request", {"status": "Approved"}),
		)
		for user in BUSINESS_WRITERS:
			for doctype, attribute, values in cases:
				with self.subTest(user=user, doctype=doctype):
					frappe.set_user("Administrator")
					doc = frappe.get_doc(doctype, getattr(self, attribute))
					doc.update(values)
					frappe.set_user(user)
					with self.assertRaises(CommandWriteError) as caught:
						doc.save(ignore_permissions=True)
					self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
					frappe.set_user("Administrator")
					for field, value in values.items():
						self.assertNotEqual(frappe.db.get_value(doctype, getattr(self, attribute), field), value)

	def test_the_accepted_revision_cannot_be_rewritten_by_flipping_its_status(self):
		# The audit's reproduction: one save sets revision_status = Draft and edits content.
		frappe.set_user(AUTHOR)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("Departmental Need Revision", self.revision, {"revision_status": "Draft", "title": "Changed after acceptance"})
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Departmental Need Revision", self.revision, "revision_status"), "Accepted")
		self.assertNotEqual(frappe.db.get_value("Departmental Need Revision", self.revision, "title"), "Changed after acceptance")

	def test_a_new_need_record_cannot_be_inserted_directly(self):
		frappe.set_user("Administrator")
		with self.assertRaises(CommandWriteError) as caught:
			frappe.get_doc(
				{"doctype": "Departmental Need", "need_reference": "NDS-REST-BYPASS", "organisation_unit": self.ou, "financial_year": FY, "current_state": "Draft"}
			).insert(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")

	def test_the_command_route_still_writes_the_same_records(self):
		frappe.set_user(AUTHOR)
		draft = frappe.get_doc("Departmental Need", self.draft_need)
		saved = lifecycle.update_need(
			need=self.draft_need, expected_version=draft.record_version, idempotency_key=self.key(),
			**self.content(title="Command route title still saves"),
		)
		frappe.set_user("Administrator")
		self.assertEqual(saved["need"], self.draft_need)
		self.assertEqual(frappe.db.get_value("Departmental Need Revision", self.draft_revision, "title"), "Command route title still saves")


class TestNeedEventsAndDecisionsAreCommandOnly(NeedsWorld):
	"""RG-08 / AUD-XC-013: the Needs outbox row starts a departmental plan the
	moment it is inserted, and the decision row is the Needs audit record. Neither
	may be written or deleted outside a Needs command, by anyone."""

	def setUp(self):
		super().setUp()
		self.build_world()
		self.event = frappe.get_all("Departmental Need Event", filters={"departmental_need": self.need}, pluck="name", order_by="sequence desc")[0]
		self.decision = frappe.get_all("Departmental Need Decision", filters={"departmental_need": self.need}, pluck="name")[0]

	def test_the_event_and_decision_rows_cannot_be_rewritten_or_deleted(self):
		for user in BUSINESS_WRITERS:
			for doctype, name, fieldname, value in (
				("Departmental Need Event", self.event, "status", "Delivered"),
				("Departmental Need Decision", self.decision, "reason", "rewritten"),
			):
				with self.subTest(user=user, doctype=doctype):
					before = frappe.db.get_value(doctype, name, fieldname)
					frappe.set_user(user)
					with self.assertRaises(frappe.PermissionError):
						frappe.client.set_value(doctype, name, fieldname, value)
					with self.assertRaises(frappe.PermissionError):
						frappe.client.delete(doctype, name)
					with self.assertRaises(CommandWriteError) as caught:
						frappe.delete_doc(doctype, name, ignore_permissions=True)
					self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE")
					frappe.set_user("Administrator")
					self.assertEqual(frappe.db.get_value(doctype, name, fieldname), before)
					self.assertTrue(frappe.db.exists(doctype, name))

	def test_a_posted_accepted_need_event_is_refused_and_starts_no_plan(self):
		# The audit's reproduction: POST an accepted-Need event as a technical user.
		template = frappe.get_doc("Departmental Need Event", self.event)
		plans_before = frappe.db.count("Departmental Plan")
		events_before = frappe.db.count("Departmental Need Event")
		frappe.set_user("Administrator")
		forged = frappe.get_doc(
			{
				"doctype": "Departmental Need Event", "event_id": "NDE-REST-BYPASS", "event_type": template.event_type,
				"departmental_need": template.departmental_need, "sequence": 9999, "need_revision": template.need_revision,
				"occurred_at": template.occurred_at, "payload": template.payload, "status": "Pending",
			}
		)
		with self.assertRaises(CommandWriteError) as caught:
			forged.insert()
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
		self.assertEqual(frappe.db.count("Departmental Need Event"), events_before)
		self.assertEqual(frappe.db.count("Departmental Plan"), plans_before)

	def test_a_posted_decision_is_refused(self):
		template = frappe.get_doc("Departmental Need Decision", self.decision)
		frappe.set_user("Administrator")
		forged = frappe.copy_doc(template)
		forged.decision_id = "NDD-REST-BYPASS"
		forged.idempotency_key = "rest-bypass-decision"
		with self.assertRaises(CommandWriteError) as caught:
			forged.insert()
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
		self.assertFalse(frappe.db.exists("Departmental Need Decision", "NDD-REST-BYPASS"))


class TestPlanningIntakeProjectionIsReadOnly(NeedsWorld):
	def setUp(self):
		super().setUp()
		self.build_world()
		# Accepting a Need normally has Planning project its position already; make
		# sure one exists to try to change, and remove the one this test made.
		if not frappe.db.exists("Need Planning Intake Projection", self.need):
			self.addCleanup(frappe.db.delete, "Need Planning Intake Projection", {"name": self.need})
			with maintenance_write(NEEDS_WRITE_FAMILY, reason="test: a projected Planning position to try to change"):
				frappe.get_doc(
					{"doctype": "Need Planning Intake Projection", "name": self.need, "departmental_need": self.need, "need_revision": self.revision, "position": "Update required", "source_event_id": f"rest-bypass-{self.need}", "source_event_time": now_datetime()}
				).insert(ignore_permissions=True)
		self.projection = self.need
		self.position = frappe.db.get_value("Need Planning Intake Projection", self.need, "position")

	def test_no_business_role_can_edit_or_delete_the_projection(self):
		for user in (AUTHOR, REVIEWER, PLANNER, "Administrator"):
			with self.subTest(user=user):
				frappe.set_user(user)
				with self.assertRaises(frappe.PermissionError):
					frappe.client.set_value("Need Planning Intake Projection", self.projection, "position", "After current submission" if self.position != "After current submission" else "Update required")
				with self.assertRaises(frappe.PermissionError):
					frappe.client.delete("Need Planning Intake Projection", self.projection)
				frappe.set_user("Administrator")
				self.assertEqual(frappe.db.get_value("Need Planning Intake Projection", self.projection, "position"), self.position)

	def test_a_direct_delete_is_refused_even_with_permissions_ignored(self):
		frappe.set_user("Administrator")
		with self.assertRaises(CommandWriteError) as caught:
			frappe.delete_doc("Need Planning Intake Projection", self.projection, ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE")


class TestNeedReadScope(NeedsWorld):
	"""NDS §6 — Author: own Needs; Planner: current accepted only; one predicate
	for lists and direct routes."""

	def setUp(self):
		super().setUp()
		self.build_world()

	def listed(self, doctype: str, user: str, **kwargs) -> set[str]:
		return {row.name for row in frappe.get_list(doctype, user=user, limit_page_length=0, **kwargs)}

	def test_the_planner_reads_no_draft_or_returned_need_and_no_draft_revision(self):
		self.assertEqual(self.listed("Departmental Need", PLANNER, filters={"current_state": ("in", ("Draft", "Returned"))}), set())
		self.assertIn(self.need, self.listed("Departmental Need", PLANNER))
		self.assertNotIn(self.draft_need, self.listed("Departmental Need", PLANNER))
		self.assertNotIn(self.draft_revision, self.listed("Departmental Need Revision", PLANNER))
		self.assertIn(self.revision, self.listed("Departmental Need Revision", PLANNER))
		frappe.set_user(PLANNER)
		self.assertFalse(frappe.has_permission("Departmental Need", "read", doc=self.draft_need))
		self.assertFalse(frappe.has_permission("Departmental Need Revision", "read", doc=self.draft_revision))

	def test_the_planner_does_not_read_withdrawal_requests_or_review_tasks(self):
		self.assertEqual(self.listed("Need Withdrawal Request", PLANNER), set())

	def test_the_author_lists_only_their_own_needs_and_revisions(self):
		own = {n for n in self.listed("Departmental Need", AUTHOR)}
		for name in own:
			self.assertEqual(frappe.db.get_value("Departmental Need", name, "owner"), AUTHOR)
		revisions = self.listed("Departmental Need Revision", AUTHOR)
		self.assertIn(self.draft_revision, revisions)
		for name in revisions:
			need = frappe.db.get_value("Departmental Need Revision", name, "departmental_need")
			self.assertIn(need, own)

	def test_the_head_of_department_reads_the_department_including_a_draft(self):
		self.assertIn(self.draft_need, self.listed("Departmental Need", REVIEWER))
		self.assertIn(self.request, self.listed("Need Withdrawal Request", REVIEWER))

	def test_the_list_and_the_direct_route_agree_for_every_need_and_role(self):
		everything = frappe.get_all("Departmental Need", pluck="name")
		for user in (AUTHOR, REVIEWER, PLANNER):
			listed = self.listed("Departmental Need", user)
			revisions = self.listed("Departmental Need Revision", user)
			frappe.set_user(user)
			try:
				for name in everything:
					with self.subTest(user=user, need=name):
						self.assertEqual(bool(frappe.has_permission("Departmental Need", "read", doc=name)), name in listed)
				for name in frappe.get_all("Departmental Need Revision", pluck="name"):
					with self.subTest(user=user, revision=name):
						self.assertEqual(bool(frappe.has_permission("Departmental Need Revision", "read", doc=name)), name in revisions)
			finally:
				frappe.set_user("Administrator")

	def test_a_technical_reader_still_reads_everything(self):
		self.assertEqual(need_authorization.permission_query_conditions("Administrator", "Departmental Need"), "")
		self.assertEqual(self.listed("Departmental Need", "Administrator"), set(frappe.get_all("Departmental Need", pluck="name")))
