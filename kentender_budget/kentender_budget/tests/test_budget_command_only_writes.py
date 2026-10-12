# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-006 / AUD-XC-013 (Budget share) — every Budget record (Budget,
Version, Line, Line Version, Reservation, Commitment, ledger event, submission
attempt, revision request and its event) changes only through the Budget
services. A Budget Officer, a Budget Approver, a System Manager and
Administrator cannot save or delete one directly; the services still can, and
test/seed clean-up uses an explicit maintenance window."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate

from kentender_core.services.command_write_guard import (
	CommandWriteError,
	CommandWriteGuardMixin,
	fixture_insert,
	maintenance_write,
	purge_doc,
)
from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY, budget_write
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase
from kentender_budget.utils.version_stamp import stamped

# doctype -> a field a direct write would change
GUARDED = {
	"Procurement Budget": "title",
	"Procurement Budget Version": "status",
	"Procurement Budget Line": "generated_reference",
	"Procurement Budget Line Version": "approved_amount",
	"Funding Reservation": "remaining_amount",
	"Procurement Commitment": "current_amount",
	"Budget Audit Event": "amount",
	"Budget Submission Attempt": "approval_reference",
	"Budget Revision Request": "status",
	"Budget Revision Request Event": "status",
}


class TestBudgetRecordsAreCommandOnly(_PrincipalBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.world: dict[str, str] = {}

	def setUp(self):
		super().setUp()
		if self.world:
			return
		budget, line = self._new_dhi_line()
		w = type(self).world
		w["Procurement Budget"] = budget
		w["Procurement Budget Line"] = line
		version = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		w["Procurement Budget Version"] = version
		w["Procurement Budget Line Version"] = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, "name")
		w["Budget Submission Attempt"] = frappe.db.get_value("Budget Submission Attempt", {"budget_version": version}, "name")
		w["Budget Audit Event"] = frappe.db.get_value("Budget Audit Event", {"budget": budget}, "name")
		reservation = self._reserve(line, 30_000_000, reference="REQ-CMD-ONLY")
		w["Funding Reservation"] = reservation
		self._as("Administrator")
		converted = commitment_svc.convert_reservation(
			reservation=reservation, contract="CTR-CMD-ONLY", amount=10_000_000, idempotency_key=self._key("cv"),
			contract_event_id="CTR-CMD-ONLY:signed", contract_event_type="ContractSigned", caller=service_caller(PRINCIPAL_CONTRACT, reference="CTR-CMD-ONLY"),
		)
		w["Procurement Commitment"] = converted["commitment"]["commitment_id"]
		self._seed_revision_request(budget, line)

	@classmethod
	def _seed_revision_request(cls, budget: str, line: str) -> None:
		request = fixture_insert(
			frappe.get_doc(
				{"doctype": "Budget Revision Request", "budget_revision_request_id": f"BRR-CMD-{cls.suffix}", "planning_request_id": f"PLN-CMD-{cls.suffix}", "status": "Open", "budget": budget, "budget_line": line}
			)
		)
		cls.world["Budget Revision Request"] = request.name
		event = fixture_insert(
			frappe.get_doc(
				{"doctype": "Budget Revision Request Event", "event_id": f"BRE-CMD-{cls.suffix}", "budget_revision_request": request.name, "planning_request_id": f"PLN-CMD-{cls.suffix}", "outcome": "Declined", "sequence": 1, "status": "Pending"}
			)
		)
		cls.world["Budget Revision Request Event"] = event.name
		cls._cleanup.append(("Budget Revision Request Event", event.name))
		cls._cleanup.append(("Budget Revision Request", request.name))

	def _changed_value(self, doctype: str, fieldname: str, doc):
		current = doc.get(fieldname)
		field = frappe.get_meta(doctype).get_field(fieldname)
		if field.fieldtype in ("Currency", "Float"):
			return (current or 0) + 1
		if fieldname == "status":
			return "Closed" if doctype == "Procurement Budget Version" else ("Declined" if doctype == "Budget Revision Request" else "Delivered")
		return f"{current or 'x'}-edited"

	def test_every_user_save_is_refused_for_every_role_including_administrator(self):
		"""The reproduction of AUD-XC-006: `d = frappe.get_doc(...); d.<field> = ..; d.save()`
		must raise for the Officer, the Approver, System Manager and Administrator."""
		admin_like = ("Administrator",)
		for doctype, fieldname in GUARDED.items():
			name = self.world[doctype]
			for user in (self.officer, self.approver, self.dual, *admin_like):
				with self.subTest(doctype=doctype, user=user):
					self._as(user)
					doc = frappe.get_doc(doctype, name)
					setattr(doc, fieldname, self._changed_value(doctype, fieldname, doc))
					with self.assertRaises(frappe.PermissionError) as caught:
						doc.save(ignore_permissions=True)
					self.assertIsInstance(caught.exception, CommandWriteError)
					self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
		self._as("Administrator")

	def test_no_role_holds_write_create_or_delete_on_a_budget_record(self):
		"""The DocPerm is the first lock: no business role, and not System Manager,
		keeps write/create/delete/submit/share on any of the records."""
		for doctype in GUARDED:
			for perm in frappe.get_meta(doctype).permissions:
				with self.subTest(doctype=doctype, role=perm.role):
					for right in ("write", "create", "delete", "submit", "cancel", "amend", "share"):
						self.assertFalse(perm.get(right), f"{perm.role} still holds {right} on {doctype}")
		custom = frappe.get_all("Custom DocPerm", filters={"parent": ["in", list(GUARDED)]}, fields=["parent", "role", "write", "create", "delete"])
		self.assertEqual([c for c in custom if c.write or c.create or c.delete], [])

	def test_a_business_user_cannot_write_through_the_client_api(self):
		"""`frappe.client.set_value` and `.save` on an Active line's amount are refused
		at the permission layer for the Officer (the REST path of the finding)."""
		line_version = self.world["Procurement Budget Line Version"]
		before = frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount")
		self._as(self.officer)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("Procurement Budget Line Version", line_version, "approved_amount", 1_000_000_000)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("Procurement Budget Version", self.world["Procurement Budget Version"], "status", "Superseded")
		self._as(self.approver)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("Procurement Budget Version", self.world["Procurement Budget Version"], "status", "Closed")
		self._as("Administrator")
		self.assertEqual(frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount"), before)
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", self.world["Procurement Budget Version"], "status"), "Active")

	def test_every_user_delete_is_refused(self):
		for doctype in GUARDED:
			name = self.world[doctype]
			for user in (self.officer, self.approver, "Administrator"):
				with self.subTest(doctype=doctype, user=user):
					self._as(user)
					with self.assertRaises(frappe.PermissionError) as caught:
						frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
					self.assertEqual(getattr(caught.exception, "code", None), "COMMAND_ONLY_DELETE")
		self._as("Administrator")
		for doctype, name in self.world.items():
			self.assertTrue(frappe.db.exists(doctype, name), f"{doctype} {name} disappeared")

	def test_a_user_cannot_insert_a_record_directly(self):
		self._as("Administrator")
		for doctype in ("Procurement Budget", "Funding Reservation", "Procurement Commitment", "Budget Audit Event"):
			with self.subTest(doctype=doctype):
				doc = frappe.get_doc({"doctype": doctype})
				with self.assertRaises((CommandWriteError, frappe.MandatoryError)):
					doc.insert(ignore_permissions=True, ignore_mandatory=True)

	def test_the_ledger_row_is_never_updated_even_by_the_owning_service_window(self):
		event = frappe.get_doc("Budget Audit Event", self.world["Budget Audit Event"])
		event.reason = "tampered"
		with budget_write():
			with self.assertRaises(frappe.ValidationError):
				event.save(ignore_permissions=True)

	def test_the_services_can_still_write(self):
		"""The positive control: the owning service's own commands still change records."""
		self._as(self.officer)
		budget, version = self._create_active_baseline(dhi_amount=5_000_000, hwd_amount=1)
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Active")
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(succ["ok"], succ)
		self._track("Procurement Budget Version", succ["version"]["id"])
		saved = contracts.save_budget_version_draft(
			stamped({"budget_version": succ["version"]["id"], "approval_reference": f"CMD-{self.suffix}", "approval_date": add_days(nowdate(), -3), "authorised_total": 5_000_001})
		)
		self.assertTrue(saved["ok"], saved)

	def test_cleanup_uses_the_maintenance_window_and_never_inside_a_request(self):
		doc = fixture_insert(
			frappe.get_doc({"doctype": "Budget Revision Request", "budget_revision_request_id": f"BRR-TMP-{self.suffix}", "planning_request_id": f"PLN-TMP-{self.suffix}", "status": "Open", "budget": self.world["Procurement Budget"], "budget_line": self.world["Procurement Budget Line"]})
		)
		self.assertTrue(frappe.db.exists("Budget Revision Request", doc.name))
		self.assertTrue(purge_doc("Budget Revision Request", doc.name))
		self.assertFalse(frappe.db.exists("Budget Revision Request", doc.name))
		with maintenance_write(BUDGET_WRITE_FAMILY, reason="test"):
			pass
		frappe.local.request = object()
		try:
			with self.assertRaises(CommandWriteError) as caught:
				with maintenance_write(BUDGET_WRITE_FAMILY, reason="inside a request"):
					pass
			self.assertEqual(caught.exception.code, "COMMAND_MAINTENANCE_REFUSED")
		finally:
			frappe.local.request = None

	def test_the_family_is_declared_on_every_controller(self):
		for doctype in GUARDED:
			with self.subTest(doctype=doctype):
				controller = frappe.get_meta(doctype)  # loads the module
				cls = frappe.get_attr(f"kentender_budget.kentender_budget.doctype.{frappe.scrub(doctype)}.{frappe.scrub(doctype)}.{doctype.replace(' ', '')}")
				self.assertTrue(issubclass(cls, CommandWriteGuardMixin))
				self.assertEqual(cls.command_write_family, BUDGET_WRITE_FAMILY)
				self.assertIsNotNone(controller)

	@classmethod
	def tearDownClass(cls):
		# The shared world is removed by the base class's clean-up helpers.
		super().tearDownClass()
