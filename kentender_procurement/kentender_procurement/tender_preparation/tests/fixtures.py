# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 test world (plan D15).

Phase 2 needs only actors: the three Site-wide responsibilities plus one
actor holding both Procurement Officer and Head of Procurement Function
(`BOTH`, for TPR-AC-023's segregation test), one outsider holding only a
departmental responsibility elsewhere, and one desk user with nothing.
Phase 4 extends this world with an authorised Requisition handoff built
through Requisitions' own commands (its `tests/fixtures.py`), never a
direct write.

`wipe_tender_rows()` is site-wide and unscoped, exactly like
`wipe_requisition_rows()`: never run the Python suite while a Tender
Preparation Playwright process is active on the site.
"""

from __future__ import annotations

from uuid import uuid4

import frappe

NS = "KENTENDER_TEST_TPR"

OFFICER = "tprt.officer@example.test"
HOPF = "tprt.hopf@example.test"
BOTH = "tprt.both@example.test"
AUDITOR = "tprt.auditor@example.test"
OUTSIDER = "tprt.outsider@example.test"
NOBODY = "tprt.nobody@example.test"

ACTORS = (
	(OFFICER, "TPRT Procurement Officer"),
	(HOPF, "TPRT Head of Procurement Function"),
	(BOTH, "TPRT Officer and Head"),
	(AUDITOR, "TPRT Auditor"),
	(OUTSIDER, "TPRT Outsider"),
	(NOBODY, "TPRT Nobody"),
)

FAMILY_WIPE_ORDER = (
	"Tender Preparation Event",
	"Tender Preparation Decision",
	"Tender Preparation Task",
	"Tender Publication Handoff",
	"Tender Preparation Version",
	"Prepared Tender",
	"Tender Preparation Command Journal",
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


def _outsider_unit() -> str:
	"""One Organisation Unit the outsider's departmental responsibility can
	point at; Planning's own test world already owns one, reuse it."""
	from kentender_procurement.procurement_planning.tests import fixtures as pln_fx

	pln_fx.ensure_world()
	return pln_fx.OU_BETA


def ensure_world() -> None:
	from kentender_core.tests import v16_fixtures as core_fx

	frappe.set_user("Administrator")
	core_fx.ensure_site_configured()
	for email, name in ACTORS:
		_user(email, name)
	_grant(OFFICER, "Procurement Officer")
	_grant(HOPF, "Head of Procurement Function")
	_grant(BOTH, "Procurement Officer")
	_grant(BOTH, "Head of Procurement Function")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", _outsider_unit())
	frappe.db.commit()


def restore_site() -> None:
	"""Class cleanup: leave no Tender-family row behind (the per-test wipe
	runs in setUp, so the last test's rows would otherwise survive)."""
	frappe.set_user("Administrator")
	wipe_tender_rows()
	frappe.db.commit()


def wipe_tender_rows() -> None:
	"""Every Tender-family row on the site (controllers refuse deletes, so
	this goes through `frappe.db.delete`, the fixture-wipe path)."""
	frappe.set_user("Administrator")
	for doctype in FAMILY_WIPE_ORDER:
		frappe.db.delete(doctype)
	frappe.db.commit()


# --------------------------------------------------------------------------
# Phase 4 — an authorised Requisition handoff built through Requisitions'
# own commands (never a direct write), and the fixture Task values.
# --------------------------------------------------------------------------

from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx  # noqa: E402

DELIVERY_LOCATION = "Test Delivery Location — Tender Preparation"
CONTACT_OFFICE = "Test Contact Office — Tender Preparation"

TASK1 = {
	"tender_title": "Supply and delivery of business laptops", "issue_date": "2102-01-15", "clarification_deadline": "2102-01-27 17:00:00",
	"submission_deadline": "2102-02-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000, "pre_tender_meeting": False,
}
TASK4 = {
	"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True,
	"minimum_comparable_contracts": "2", "experience_period_years": "5", "after_sales_evidence_required": True,
	"after_sales_evidence": "Kenya service-centre details and escalation contacts",
}
TASK5 = {
	"inspection_location": DELIVERY_LOCATION, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
	"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": CONTACT_OFFICE,
}


def ensure_link_targets() -> None:
	frappe.set_user("Administrator")
	if not frappe.db.exists("Delivery Location", DELIVERY_LOCATION):
		frappe.get_doc({"doctype": "Delivery Location", "location_name": DELIVERY_LOCATION, "address": "1 Test Street, Nairobi", "status": "Active", "fixture_namespace": NS}).insert(ignore_permissions=True)
	if not frappe.db.exists("Contact Office", CONTACT_OFFICE):
		frappe.get_doc({"doctype": "Contact Office", "office_name": CONTACT_OFFICE, "contact_email": "tender.office@example.test", "status": "Active", "fixture_namespace": NS}).insert(ignore_permissions=True)
	from kentender_procurement.tender_templates import registry

	registry.install()


def ensure_full_world() -> None:
	ensure_world()
	req_fx.ensure_world()
	ensure_link_targets()


def wipe_all() -> None:
	wipe_tender_rows()
	req_fx.wipe_requisition_rows()
	req_fx.wipe_planning_rows()


def authorised_handoff() -> str:
	"""Requisitions' own proven authorisation sequence (its `test_handoff.py`
	`_authorised()`), copied so the Tender world starts from a real v1.3
	handoff: one Business laptops item, the confirmed baseline technical
	rows, one acceptance row, Head of User Department submission, Head of
	Procurement Function authorisation."""
	from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, lifecycle

	if not frappe.db.exists("Delivery Location", "Test Delivery Location — Requisitions"):
		frappe.get_doc({"doctype": "Delivery Location", "location_name": "Test Delivery Location — Requisitions", "address": "1 Test Street", "status": "Active"}).insert(ignore_permissions=True)
	_, item_id = req_fx.active_item()
	frappe.set_user(req_fx.AUTHOR)
	prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=key())
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
	version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
	cmd.save_requisition_summary(requisition=prepared["requisition"], values={"delivery_location": "Test Delivery Location — Requisitions", "latest_delivery_date": "2102-04-30"}, expected_record_version=version.record_version, idempotency_key=key())
	cmd.add_requisition_item(
		requisition=prepared["requisition"],
		values={"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 1, "intended_use": "Clinical training"},
		expected_record_version=package_version.record_version, idempotency_key=key(),
	)
	req_fx.confirm_all_proposed_requirements(prepared["requisition"], package_version)
	cmd.add_acceptance_requirement(
		requisition=prepared["requisition"],
		values={"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
		expected_record_version=package_version.record_version, idempotency_key=key(),
	)
	frappe.set_user(req_fx.HOD)
	root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
	submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user(req_fx.HOPF)
	root.reload()
	authorised = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user("Administrator")
	return authorised["handoff"]


def prepared(handoff: str | None = None, *, user: str | None = None) -> dict:
	from kentender_procurement.tender_preparation.services import draft_commands as cmd

	handoff = handoff or authorised_handoff()
	frappe.set_user(user or OFFICER)
	result = cmd.prepare_tender(handoff=handoff, idempotency_key=key())
	frappe.set_user("Administrator")
	return result


def complete_draft(tender: str, *, user: str | None = None, overrides: dict | None = None) -> dict:
	from kentender_procurement.tender_preparation.services import draft_commands as cmd

	frappe.set_user(user or OFFICER)
	root = frappe.get_doc("Prepared Tender", tender)
	values = {**TASK1, **TASK4, **TASK5, **(overrides or {})}
	result = cmd.save_tender_draft(tender=tender, values=values, expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user("Administrator")
	return result


def submitted(*, user: str | None = None) -> dict:
	from kentender_procurement.tender_preparation.services import lifecycle

	prep = prepared(user=user)
	complete_draft(prep["tender"], user=user)
	frappe.set_user(user or OFFICER)
	root = frappe.get_doc("Prepared Tender", prep["tender"])
	result = lifecycle.submit_tender_for_approval(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user("Administrator")
	return {**prep, **result}


def approved(*, officer: str | None = None, approver: str | None = None) -> dict:
	from kentender_procurement.tender_preparation.services import lifecycle

	sub = submitted(user=officer)
	frappe.set_user(approver or HOPF)
	root = frappe.get_doc("Prepared Tender", sub["tender"])
	result = lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=key())
	frappe.set_user("Administrator")
	return {**sub, **result}
