# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 — the Tender Preparation Playwright world (plan D15,
amended: it extends Procurement Requisitions' own Playwright world on FY
2099-2100 rather than building a second one, because a real
`AuthorisedRequisitionHandoff v1.3` can only come from Requisitions' own
commands on Planning's and Budget's graphs — the same reasoning
Requisitions' tests give for extending Planning's world).

Six Tender-facing actors (officer / hopf / both / auditor / outsider /
nobody) are added to that world; one reset function per browser spec
rebuilds exactly the state its screen opens on, through the real commands
as the named actors, and returns every server-generated id. `restore_site`
delegates to Requisitions'. The Python suite and Playwright never run
together on the site.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils.password import update_password

from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_requisitions.seeds import playwright_ui_fixtures as req_pw

NS_PW = "KENTENDER_TPR_PLAYWRIGHT"
OFFICER = "pw.tpr.officer@example.test"
HOPF = "pw.tpr.hopf@example.test"
BOTH = "pw.tpr.both@example.test"
AUDITOR = "pw.tpr.auditor@example.test"
OUTSIDER = "pw.tpr.outsider@example.test"
NOBODY = "pw.tpr.nobody@example.test"
ACTORS = (OFFICER, HOPF, BOTH, AUDITOR, OUTSIDER, NOBODY)
CONTACT_OFFICE = "Playwright — Tender Preparation Contact Office"

TASK1 = {
	"tender_title": "Supply and delivery of business laptops", "issue_date": "2100-05-15", "clarification_deadline": "2100-05-27 17:00:00",
	"submission_deadline": "2100-06-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000, "pre_tender_meeting": False,
}
TASK4 = {
	"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True, "minimum_comparable_contracts": "2",
	"experience_period_years": "5", "after_sales_evidence_required": True, "after_sales_evidence": "Kenya service-centre details and escalation contacts",
}
TASK5 = {
	"inspection_location": req_pw.DELIVERY_LOCATION, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
	"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": CONTACT_OFFICE,
}


def _key() -> str:
	return f"tpr-pw-{uuid4().hex}"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw("Tender Preparation Playwright fixtures are test data. Enable developer_mode or allow_tests on this site before building them.")


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		first, _, last = full_name.partition(" ")
		doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	elif frappe.db.get_value("User", email, "user_type") != "System User":
		frappe.get_doc("User", email).add_roles("Desk User")
	update_password(email, TEST_PASSWORD)


def _grant(email: str, role: str, unit: str = "") -> None:
	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS_PW, actor="Administrator")


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	from kentender_procurement.tender_templates import registry

	_guard()
	world = req_pw.ensure_world(commit=False)
	frappe.set_user("Administrator")
	for email, name in ((OFFICER, "Playwright Tender Officer"), (HOPF, "Playwright Tender HoPF"), (BOTH, "Playwright Tender Officer-and-Head"), (AUDITOR, "Playwright Tender Auditor"), (OUTSIDER, "Playwright Tender Outsider"), (NOBODY, "Playwright Tender Nobody")):
		_user(email, name)
	_grant(OFFICER, "Procurement Officer")
	_grant(HOPF, "Head of Procurement Function")
	_grant(BOTH, "Procurement Officer")
	_grant(BOTH, "Head of Procurement Function")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", req_pw._unit("Playwright — Requisitions Outsider"))
	nobody = frappe.get_doc("User", NOBODY)
	if "Procurement Officer" not in {row.role for row in nobody.roles}:
		nobody.add_roles("Procurement Officer")
	for assignment in frappe.get_all("User Responsibility Assignment", filters={"user": NOBODY}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", assignment, ignore_permissions=True, force=True)
	if not frappe.db.exists("Contact Office", CONTACT_OFFICE):
		frappe.get_doc({"doctype": "Contact Office", "office_name": CONTACT_OFFICE, "contact_email": "tender.office@example.test", "status": "Active", "fixture_namespace": NS_PW}).insert(ignore_permissions=True)
	registry.install()
	if commit:
		frappe.db.commit()
	return {**world, "officer": OFFICER, "hopf": HOPF, "both": BOTH, "auditor": AUDITOR}


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	"""Gate / teardown entry: leave no Playwright Tender row behind, then
	hand the Requisitions world back to its own restore (intake flag)."""
	frappe.set_user("Administrator")
	_wipe_tender_side()
	return req_pw.restore_site(commit=commit)


def _wipe_tender_side() -> None:
	"""Only this world's rows: Tenders prepared on a Requisitions-Playwright
	handoff, or written by one of the six actors. Never by `owner =
	Administrator` — the canonical §16 seed's acknowledgment rows are
	Administrator-written and must survive a browser run."""
	handoffs = frappe.get_all("Authorised Requisition Handoff", filters={"fixture_namespace": req_pw.NS_PW}, pluck="name")
	tenders = set(frappe.get_all("Prepared Tender", filters={"requisition_handoff": ("in", handoffs or ("",))}, pluck="name"))
	tenders |= set(frappe.get_all("Prepared Tender", filters={"owner": ("in", ACTORS)}, pluck="name"))
	tenders = list(tenders) or [""]
	for doctype in ("Tender Preparation Event", "Tender Preparation Decision", "Tender Preparation Task", "Tender Publication Handoff", "Tender Preparation Version"):
		frappe.db.delete(doctype, {"tender": ("in", tenders)})
	frappe.db.delete("Prepared Tender", {"name": ("in", tenders)})
	frappe.db.delete("Tender Preparation Command Journal", {"idempotency_key": ("like", "tpr-pw-%")})


def wipe_tender_rows(*, commit: bool = True) -> dict[str, Any]:
	"""Public purge entry (core `purge_kentender_playwright_data`): this
	world's Tender rows only; the Requisitions world is left to its owner."""
	_guard()
	frappe.set_user("Administrator")
	_wipe_tender_side()
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS_PW}


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	_guard()
	frappe.set_user("Administrator")
	_wipe_tender_side()
	req_pw.reset_all(commit=False)
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS_PW}


# --- states ------------------------------------------------------------------


def reset_workspace_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-01/02 opening state: one authorised, unconsumed handoff."""
	world = ensure_world(commit=False)
	_wipe_tender_side()
	state = req_pw.reset_authorised_fixture(commit=False)
	if commit:
		frappe.db.commit()
	return {**world, "requisition": state["requisition"], "handoff": state["handoff"]}


def reset_draft_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-03 opening state: a fresh Draft on that handoff."""
	from kentender_procurement.tender_preparation.services import draft_commands as cmd

	state = reset_workspace_fixture(commit=False)
	with _as(OFFICER):
		prepared = cmd.prepare_tender(handoff=state["handoff"], idempotency_key=_key())
	if commit:
		frappe.db.commit()
	return {**state, "tender": prepared["tender"], "tender_reference": prepared["tender_reference"], "tender_version": prepared["tender_version"]}


def _complete(tender: str, actor: str = OFFICER) -> None:
	from kentender_procurement.tender_preparation.services import draft_commands as cmd

	with _as(actor):
		root = frappe.get_doc("Prepared Tender", tender)
		result = cmd.save_tender_draft(tender=tender, values={**TASK1, **TASK4, **TASK5}, expected_record_version=root.record_version, idempotency_key=_key())
		if not result.get("ok"):
			frappe.throw(f"fixture draft did not save: {result}")
		root.reload()
		cmd.run_tender_readiness(tender=tender, expected_record_version=root.record_version, idempotency_key=_key())


def reset_complete_draft_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-03 (all tasks complete) and TPR-DES-04 opening state."""
	state = reset_draft_fixture(commit=False)
	_complete(state["tender"])
	if commit:
		frappe.db.commit()
	return state


def _submit(tender: str, actor: str = OFFICER) -> dict[str, Any]:
	from kentender_procurement.tender_preparation.services import lifecycle

	with _as(actor):
		root = frappe.get_doc("Prepared Tender", tender)
		return lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=root.record_version, idempotency_key=_key())


def reset_submitted_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-05 opening state: Version 1 submitted, one HoPF task."""
	state = reset_complete_draft_fixture(commit=False)
	submitted = _submit(state["tender"])
	if commit:
		frappe.db.commit()
	return {**state, "task": submitted["task"]}


def reset_returned_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""A returned Version 1 with its Draft successor Version 2 (the officer's correction state)."""
	from kentender_procurement.tender_preparation.services import lifecycle

	state = reset_submitted_fixture(commit=False)
	with _as(HOPF):
		root = frappe.get_doc("Prepared Tender", state["tender"])
		returned = lifecycle.return_tender_for_correction(task=state["task"], reason="Confirm whether manufacturer authorisation is necessary and update the evidence requirement.", expected_record_version=root.record_version, idempotency_key=_key())
	if commit:
		frappe.db.commit()
	return {**state, "returned_version": returned["returned_version"], "tender_version": returned["tender_version"]}


def reset_approved_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-06 opening state: returned once, corrected, resubmitted and
	approved — Version 2, exactly as the artboard shows (plan C3)."""
	from kentender_procurement.tender_preparation.services import lifecycle

	state = reset_returned_fixture(commit=False)
	_complete(state["tender"])
	submitted = _submit(state["tender"])
	with _as(HOPF):
		root = frappe.get_doc("Prepared Tender", state["tender"])
		approved = lifecycle.approve_tender_for_publication(task=submitted["task"], expected_record_version=root.record_version, idempotency_key=_key())
	if commit:
		frappe.db.commit()
	return {**state, "task": submitted["task"], "publication_handoff": approved["publication_handoff"], "approved_version": approved["tender_version"]}


def reset_consumed_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""The approved Tender after the downstream acknowledgment (reopen refused)."""
	from kentender_procurement.tender_preparation.services import publication

	state = reset_approved_fixture(commit=False)
	frappe.set_user("Administrator")
	acknowledged = publication.acknowledge_publication_consumed(tender=state["tender"], correlation_id=_key(), published_on="2100-05-15")
	if commit:
		frappe.db.commit()
	return {**state, "acknowledged": acknowledged.get("action")}
