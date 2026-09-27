# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Browser-test worlds for Bid Submission (BDS-CHG-001 v0.8 plan Phase 7).

Built on the Tenders Playwright world (`tenders.seeds.playwright_ui_fixtures`,
FY 2099-2100): its published Tender with the canonical Afya bid as the one
candidate. Every step runs the real commands as the named actors with the
fixture clock injected. `restore_site()` removes this world's rows (the
Tenders clean-up removes every bid row of its Tenders through
`kt_tender_removal_consumers`) and the journal entries the browser pass left.

Called by the Playwright specs through `bench execute`; never by a user."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe

from kentender_procurement.bid_submission.seeds import canonical as bds_canonical
from kentender_procurement.bid_submission.seeds import clear as bds_clear
from kentender_procurement.tenders.seeds import playwright_ui_fixtures as tender_pw

NAMESPACE = "PW_BID_SUBMISSION"
RECORDER = tender_pw.HOPF
OFFICER = tender_pw.OFFICER
DAVID = bds_canonical.DAVID
BROWSER_ACTORS = (RECORDER, OFFICER, tender_pw.AUDITOR, tender_pw.BOTH)
INSTRUMENT = {"instrument_type": "Demand Bank Guarantee", "issuer": "KCB Bank Kenya", "instrument_reference": "KCB/TG/2099/4417"}
ANSWERED_AT = "2027-05-19 10:00:00"


def _key() -> str:
	return f"bds-pw-{uuid4().hex}"


def _wipe_journal() -> None:
	"""The journal rows of this world's commands: the fixture's own (stamped
	NAMESPACE) and those the browser pass wrote as the fixture actors."""
	bds_clear.wipe(tenders=[], namespace=NAMESPACE)
	frappe.db.delete("Bid Command Journal", {"actor": ("in", BROWSER_ACTORS)})


def _bid(tender: str) -> str:
	return frappe.db.get_value("Bid Workspace", {"tender": tender}, "name")


def _security_facts(tender: str) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import security_matching, tenders_gateway

	current = tenders_gateway.current_definition(tender) or {}
	for section in current.get("definition", {}).get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") == security_matching.SECURITY_RULE:
				return group.get("published_facts") or {}
	frappe.throw("The fixture Tender has no tender-security requirement.")


def _answer_security(bid: str, facts: dict[str, Any]) -> None:
	"""David answers the Company task's tender-security fields as Afya's
	representative (the same save the portal makes)."""
	from kentender_procurement.bid_submission.services import reads, save

	def task():
		return reads.get_bid_task(bid_reference=bid, task="company", user=DAVID)

	def handle(view, label, **match):
		return next(f["handle"] for g in view["groups"] for f in g["fields"] if f["label"] == label and all(f.get(k) == v for k, v in match.items()))

	def put(values):
		result = save.save_bid_task(
			bid_reference=bid, task="company", values=values, expected_record_version=frappe.db.get_value("Bid Workspace", bid, "record_version"),
			idempotency_key=_key(), user=DAVID,
		)
		if not result.get("ok"):
			frappe.throw(f"The fixture could not answer the tender security: {result}")

	put({handle(task(), "Form of Tender Security"): INSTRUMENT["instrument_type"]})
	view = task()
	put({
		handle(view, "Issuing bank or insurer"): INSTRUMENT["issuer"], handle(view, "Guarantee number"): INSTRUMENT["instrument_reference"],
		handle(view, "Amount of the instrument"): facts["amount"], handle(view, "Guarantee valid until", visible=True): facts["bank_guarantee_expiry_date"],
	})


def reset_security_intake_fixture(*, commit: bool = True, answered: bool = True) -> dict[str, Any]:
	"""A published Tender whose one bid (Afya, David Ouma) has — when
	`answered` — its tender-security instrument details saved, so a matching
	physical original can be recorded blind by the Head of Procurement
	Function."""
	state = tender_pw.reset_published_fixture(commit=False)
	_wipe_journal()
	facts = _security_facts(state["tender"])
	bid = _bid(state["tender"])
	if answered:
		saved = {flag: frappe.flags.get(flag) for flag in ("kt_bds_clock", "kt_bds_fixture_namespace")}
		frappe.flags.kt_bds_clock = ANSWERED_AT
		frappe.flags.kt_bds_fixture_namespace = NAMESPACE
		try:
			_answer_security(bid, facts)
		finally:
			for flag, value in saved.items():
				frappe.flags[flag] = value
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {
		"tender": state["tender"], "tender_reference": state["tender_reference"], "bid_reference": bid,
		"supplier_name": frappe.db.get_value("Bidder Arrangement", {"tender": state["tender"]}, "lead_legal_name") or "Afya Digital Supplies Limited",
		"amount": str(facts["amount"]), "currency": str(facts["currency"]), "permitted_forms": list(facts.get("permitted_forms") or []), **INSTRUMENT,
	}


def physical_receipt_status(*, tender_reference: str) -> dict[str, Any]:
	"""What the supplier's own bid now says about the physical original (the
	portal screen that shows it is a later slice)."""
	from kentender_procurement.bid_submission.services import reads, tenders_gateway

	root = tenders_gateway.tender_root(tender_reference)
	saved = frappe.flags.get("kt_bds_clock")
	frappe.flags.kt_bds_clock = ANSWERED_AT  # David's assignment runs on the fixture's 2027 timeline
	try:
		security = reads.get_bid_task(bid_reference=_bid(root.name), task="company", user=DAVID)["security"]
	finally:
		frappe.flags.kt_bds_clock = saved
	return {k: security.get(k) or "" for k in ("physical_receipt_status", "physical_receipt_reference", "physical_received_at")}


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	frappe.set_user("Administrator")
	_wipe_journal()
	out = tender_pw.restore_site(commit=False)
	if commit:
		frappe.db.commit()
	return {**out, "bid_submission_wiped": True}
