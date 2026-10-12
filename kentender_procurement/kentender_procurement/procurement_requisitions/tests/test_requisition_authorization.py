# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §8 — the Frappe-framework permission hooks themselves.

Every other test file proves the *service-layer* gates (a command or read
function masks or refuses correctly); this file proves the two Frappe
hooks those services sit beside actually work at the framework layer —
`frappe.get_list`/`frappe.get_all` filtering through
`permission_query_conditions`, and `frappe.has_permission` on one record —
including the multi-OU EXISTS-over-child-table scope this module needed
(a `Procurement Requisition` has no single `organisation_unit` column) and
delegation from a requisition-family child DocType back to its root.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd, lifecycle
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionAuthorizationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		self.addCleanup(fx.wipe_requisition_rows)
		self.addCleanup(frappe.set_user, "Administrator")

	def _prepared(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())

	def _complete_draft(self, prepared: dict) -> None:
		fx.fill_request_information(prepared["requisition"])
		fx.add_laptops(prepared["requisition"])
		fx.enter_estimates(prepared["requisition"])
		fx.apply_standard_package(prepared["requisition"])


class TestPermissionQueryConditions(RequisitionAuthorizationCase):
	def test_an_author_of_the_contributing_unit_sees_it_in_get_list(self):
		prepared = self._prepared()
		frappe.set_user(fx.AUTHOR)
		names = frappe.get_list("Procurement Requisition", pluck="name")
		self.assertIn(prepared["requisition"], names)

	def test_an_unrelated_departmental_author_does_not_see_it(self):
		prepared = self._prepared()
		frappe.set_user(fx.OUTSIDER)  # Departmental Author on OU_BETA only
		names = frappe.get_list("Procurement Requisition", pluck="name")
		self.assertNotIn(prepared["requisition"], names)

	def test_a_site_wide_reader_sees_a_submitted_requisition_unconditionally(self):
		# AR-02: submitted work, not an unsent Draft (REQ v1.14 §8)
		_, item_id = fx.active_item()
		name = fx.submitted(item_id)
		frappe.set_user(fx.AUDITOR)
		self.assertIn(name, frappe.get_list("Procurement Requisition", pluck="name"))

	def test_a_site_wide_reader_does_not_see_an_unsent_draft(self):
		prepared = self._prepared()
		frappe.set_user(fx.AUDITOR)
		self.assertNotIn(prepared["requisition"], frappe.get_list("Procurement Requisition", pluck="name"))

	def test_an_actor_with_no_requisitions_role_sees_nothing(self):
		"""`fx.FINANCE_OFFICER` holds no DocPerm-granting Frappe Role at all
		on this DocType (none of the five §8 business roles) — Frappe's own
		base permission check refuses the query outright with a
		`PermissionError` before our own `permission_query_conditions` hook
		ever runs; it does not fall through to an empty list."""
		prepared = self._prepared()
		frappe.set_user(fx.FINANCE_OFFICER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Procurement Requisition", pluck="name")

	def test_a_child_doctype_delegates_to_its_root_via_get_list(self):
		"""`Requisition Task` has no Organisation Unit column of its own;
		its own `permission_query_conditions` registration walks back to the
		owning `Procurement Requisition`'s condition (`_CHILD_LINK`)."""
		prepared = self._prepared()
		frappe.set_user(fx.AUTHOR)
		self._complete_draft(prepared)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		from kentender_procurement.procurement_requisitions.services import lifecycle

		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		task_names = frappe.get_list("Requisition Task", pluck="name")
		self.assertIn(sent["task"], task_names)
		frappe.set_user(fx.OUTSIDER)
		self.assertNotIn(sent["task"], frappe.get_list("Requisition Task", pluck="name"))


class TestHasPermission(RequisitionAuthorizationCase):
	def test_an_author_of_the_contributing_unit_has_read_permission(self):
		prepared = self._prepared()
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.AUTHOR))

	def test_an_unrelated_actor_does_not(self):
		prepared = self._prepared()
		self.assertFalse(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.OUTSIDER))

	def test_administrator_always_has_permission(self):
		prepared = self._prepared()
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user="Administrator"))

	def test_a_site_wide_role_has_permission_on_any_submitted_record(self):
		_, item_id = fx.active_item()
		name = fx.submitted(item_id)
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=name, user=fx.PLANNER))

	def test_a_site_wide_role_has_no_permission_on_an_unsent_draft(self):
		prepared = self._prepared()
		self.assertFalse(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.PLANNER))


FAMILY_RECORDS = (
	"IT Equipment Requirement Package",
	"IT Equipment Requirement Package Version",
	"Requisition Event",
	"Requisition Correction Outcome",
	"Requisition Command Journal",
)
LINGERING = "reqt.lingering.auditor@example.test"


class TestFamilyRecordsReadThroughTheirRequisition(RequisitionAuthorizationCase):
	"""AUD-XC-025 — the package, event, correction-outcome and journal records
	carry business-role read DocPerm, so each needs the registered predicate:
	a role held without a live assignment reads none of them."""

	def _authorised(self) -> str:
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		frappe.set_user("Administrator")
		return requisition

	def _lingering_auditor(self) -> str:
		"""The Frappe Role `Auditor` with no assignment behind it (a lapsed holder until the daily reconcile)."""
		from kentender_procurement.procurement_planning.tests import fixtures as pln_fx

		pln_fx._user(LINGERING, "REQ Test Lingering Auditor")
		frappe.get_doc("User", LINGERING).add_roles("Auditor")
		self.addCleanup(self._remove_lingering)
		return LINGERING

	def _remove_lingering(self) -> None:
		frappe.set_user("Administrator")
		for contact in frappe.get_all("Contact Email", filters={"email_id": LINGERING}, pluck="parent"):
			frappe.delete_doc("Contact", contact, force=1, ignore_permissions=True)
		if frappe.db.exists("User", LINGERING):
			frappe.delete_doc("User", LINGERING, force=1, ignore_permissions=True)

	def _rows(self, requisition: str) -> dict[str, list[str]]:
		root = frappe.get_doc("Procurement Requisition", requisition)
		package = frappe.db.get_value("IT Equipment Requirement Package", {"requisition": requisition}, "name")
		return {
			"IT Equipment Requirement Package": [package],
			"IT Equipment Requirement Package Version": frappe.get_all("IT Equipment Requirement Package Version", filters={"package": package}, pluck="name"),
			"Requisition Event": frappe.get_all("Requisition Event", filters={"requisition": requisition}, pluck="name"),
			"Requisition Command Journal": frappe.get_all("Requisition Command Journal", filters={"document_name": ("in", [root.name, root.current_version, root.handoff])}, pluck="name"),
		}

	def test_every_family_doctype_registers_both_hooks(self):
		hooks = frappe.get_hooks("has_permission")
		query = frappe.get_hooks("permission_query_conditions")
		for doctype in FAMILY_RECORDS:
			self.assertTrue(hooks.get(doctype), f"{doctype}: no has_permission")
			self.assertTrue(query.get(doctype), f"{doctype}: no permission_query_conditions")

	def test_a_site_wide_reader_with_an_assignment_reads_each_record(self):
		rows = self._rows(self._authorised())
		self.assertTrue(all(rows[doctype] for doctype in ("IT Equipment Requirement Package", "IT Equipment Requirement Package Version", "Requisition Event", "Requisition Command Journal")), rows)
		for doctype, names in rows.items():
			frappe.set_user(fx.AUDITOR)
			self.assertTrue(set(names) <= set(frappe.get_list(doctype, pluck="name", limit_page_length=0)), doctype)
			for name in names:
				self.assertTrue(frappe.has_permission(doctype, doc=name, user=fx.AUDITOR), f"{doctype} {name}")

	def test_a_role_without_a_live_assignment_reads_none_of_them(self):
		rows = self._rows(self._authorised())
		lingering = self._lingering_auditor()
		for doctype, names in rows.items():
			frappe.set_user(lingering)
			self.assertFalse(set(names) & set(frappe.get_list(doctype, pluck="name", limit_page_length=0)), doctype)
			for name in names:
				self.assertFalse(frappe.has_permission(doctype, doc=name, user=lingering), f"{doctype} {name}")

	def test_a_technical_reader_still_reads_every_record(self):
		rows = self._rows(self._authorised())
		for doctype, names in rows.items():
			for name in names:
				self.assertTrue(frappe.has_permission(doctype, doc=name, user="Administrator"), f"{doctype} {name}")
