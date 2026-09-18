# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 test world (plan D18) — extends Procurement
Requisitions' own fixture world (which itself extends Planning's
`KENTENDER_TEST` world): an authorised, unconsumed `AuthorisedRequisitionHandoff
v1.3` can only come from Requisitions' own commands, and the Planning/
Requisitions actors already hold Head of Procurement Function, Accounting
Officer and Auditor. Tenders adds a Procurement Officer, a "both" actor who
holds every Tenders responsibility (segregation tests) and a nobody.

`authorised_handoff()` is Requisitions' own `RequisitionHandoffCase._authorised`
sequence, copied verbatim (not re-derived) so the Tenders tests never build a
subtly different Requisition than the one Requisitions itself proves.
"""

from __future__ import annotations

from uuid import uuid4

import frappe

from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as req_cmd, lifecycle as req_lifecycle
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx

NS = req_fx.NS
OFFICER = "tndt.officer@example.test"
HOPF = req_fx.HOPF
AO = req_fx.ACCOUNTING_OFFICER
BOTH = "tndt.both@example.test"  # Procurement Officer + HoPF + AO — the segregation subject
AUDITOR = req_fx.AUDITOR
OUTSIDER = req_fx.OUTSIDER  # Departmental Author in OU_BETA — never a contributing unit
NOBODY = "tndt.nobody@example.test"
DEPARTMENTAL = req_fx.AUTHOR  # Departmental Author in OU_ALPHA — the neutral reader
TENDER_ACTORS = (OFFICER, BOTH, NOBODY)

LOCATION = "Test Delivery Location — Tenders"
CONTACT_OFFICE = "Test Contact Office — Tenders"

TENDER_DOCTYPES = (
	"Tender Event", "Tender Command Journal", "Tender Document", "Tender Submission Handoff", "Tender Channel Confirmation",
	"Tender Addendum Inquiry", "Tender Addendum", "Tender Cancellation", "Tender Publication", "Tender Decision", "Tender Task",
	"Tender Version", "Tender",
)


def key() -> str:
	return uuid4().hex


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": full_name, "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
	if frappe.db.get_value("User", email, "user_type") != "System User":
		user.add_roles("Desk User")


def _grant(email: str, role: str, unit: str = "") -> None:
	from kentender_core.services import responsibility_administration as administration

	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS, actor="Administrator")


def ensure_world() -> None:
	frappe.set_user("Administrator")
	req_fx.ensure_world()
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
	for email, name in ((OFFICER, "TNDT Procurement Officer"), (BOTH, "TNDT Officer and Approver"), (NOBODY, "TNDT Nobody")):
		_user(email, name)
	_grant(OFFICER, "Procurement Officer")
	_grant(BOTH, "Procurement Officer")
	_grant(BOTH, "Head of Procurement Function")
	_grant(BOTH, "Accounting Officer")
	for doctype, field, name in (("Delivery Location", "location_name", LOCATION), ("Contact Office", "office_name", CONTACT_OFFICE)):
		if not frappe.db.exists(doctype, name):
			values = {"doctype": doctype, field: name, "address": "1 Test Street", "status": "Active", "fixture_namespace": NS}
			if doctype == "Contact Office":
				values.update({"contact_email": "procurement@example.test", "contact_phone": "+254 700 000000"})
			frappe.get_doc(values).insert(ignore_permissions=True)
	from kentender_procurement.tender_templates import registry

	registry.install()


def wipe_tender_rows() -> None:
	frappe.set_user("Administrator")
	for doctype in TENDER_DOCTYPES:
		for name in frappe.get_all(doctype, pluck="name"):
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
	frappe.db.commit()


def wipe_requisition_rows() -> None:
	req_fx.wipe_requisition_rows()


def wipe_planning_rows() -> None:
	req_fx.wipe_planning_rows()


def wipe_all() -> None:
	wipe_tender_rows()
	wipe_requisition_rows()
	wipe_planning_rows()


def restore_site() -> None:
	wipe_tender_rows()
	frappe.set_user("Administrator")
	for email in TENDER_ACTORS:
		for doctype in ("User Responsibility Assignment",):
			for name in frappe.get_all(doctype, filters={"user": email}, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	for doctype, name in (("Delivery Location", LOCATION), ("Contact Office", CONTACT_OFFICE)):
		if frappe.db.exists(doctype, name):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	frappe.db.commit()
	req_fx.restore_site()


# --------------------------------------------------------------------------
# An authorised, unconsumed handoff built through Requisitions' own commands
# --------------------------------------------------------------------------


def _complete_draft(prepared: dict, *, items: tuple[tuple[str, int, str], ...]) -> None:
	frappe.set_user(req_fx.AUTHOR)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
	version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
	req_cmd.save_requisition_summary(
		requisition=prepared["requisition"], values={"delivery_location": LOCATION, "latest_delivery_date": "2102-04-30"},
		expected_record_version=version.record_version, idempotency_key=key(),
	)
	for name, quantity, use in items:
		package_version.reload()
		req_cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": name, "quantity": quantity, "intended_use": use},
			expected_record_version=package_version.record_version, idempotency_key=key(),
		)
	package_version.reload()
	req_fx.confirm_all_proposed_requirements(prepared["requisition"], package_version)
	package_version.reload()
	req_cmd.add_acceptance_requirement(
		requisition=prepared["requisition"],
		values={"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
		expected_record_version=package_version.record_version, idempotency_key=key(),
	)


def authorised_handoff(*, items: tuple[tuple[str, int, str], ...] = (("Business laptops", 1, "Clinical training"),)) -> dict:
	"""Returns Requisitions' own `authorise_requisition` result (`handoff`,
	`requisition`, `requisition_version`, ...) for a fresh Active Plan Item."""
	_, item_id = req_fx.active_item()
	frappe.set_user(req_fx.AUTHOR)
	prepared = req_cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=key())
	_complete_draft(prepared, items=items)
	frappe.set_user(req_fx.HOD)
	root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
	submitted = req_lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user(req_fx.HOPF)
	root.reload()
	authorised = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user("Administrator")
	return authorised
