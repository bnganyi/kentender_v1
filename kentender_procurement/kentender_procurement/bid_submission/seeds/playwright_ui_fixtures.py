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


# -- portal worlds (plan Phase 11): this world's own suppliers, namespaced, with
#    the test password, so the canonical personas are never touched ----------------

PASSWORD = "Test@123"
SUPPLIERS = {
	"afya": {
		"facts": {
			"legal_name": "Afya Digital Supplies (Test) Limited", "country": "Kenya", "registration_number": "PVT-PW-AFYA01", "tax_identifier": "P009000101X",
			"registered_address": "Westlands Business Park, Nairobi", "official_email": "tenders@afya-pw.example", "official_phone": "+254 709 555 101", "job_title": "Managing Director",
		},
		"registrant": "pw.bds.mary@afya-pw.example", "registrant_name": "Mary Wanjiku", "representative": "pw.bds.david@afya-pw.example", "representative_name": "David Ouma",
	},
	"kisiwa": {
		"facts": {
			"legal_name": "Kisiwa Digital (Test) Limited", "country": "Kenya", "registration_number": "PVT-PW-KSW001", "tax_identifier": "P009000102X",
			"registered_address": "Mombasa Road, Nairobi", "official_email": "tenders@kisiwa-pw.example", "official_phone": "+254 709 555 102", "job_title": "Director",
		},
		"registrant": "pw.bds.grace@kisiwa-pw.example", "registrant_name": "Grace Njeri", "representative": "pw.bds.peter@kisiwa-pw.example", "representative_name": "Peter Mwangi",
	},
}
SUPPLIER_USERS = tuple(u for s in SUPPLIERS.values() for u in (s["registrant"], s["representative"]))


def _hook(name: str):
	return frappe.get_attr((frappe.get_hooks(name) or [])[-1])


def _ensure_suppliers() -> None:
	from frappe.utils.password import update_password

	for supplier in SUPPLIERS.values():
		_hook("kt_seed_supplier_account")(
			facts=supplier["facts"], registrant=supplier["registrant"], registrant_name=supplier["registrant_name"], representative=supplier["representative"],
			representative_name=supplier["representative_name"], namespace=NAMESPACE, key_prefix=NAMESPACE.lower(),
		)
	for user in SUPPLIER_USERS:
		update_password(user, PASSWORD)


def _start(tender: str, supplier: str) -> str:
	from kentender_procurement.bid_submission.seeds.canonical import seed_candidate

	facts = SUPPLIERS[supplier]
	reference = frappe.db.get_value("Tender", tender, "tender_reference")
	arrangement = seed_candidate(tender_reference=reference, at="2027-05-19 09:20:00", supplier={**facts, "namespace": NAMESPACE})
	return frappe.db.get_value("Bid Workspace", {"bidder_arrangement": arrangement}, "name")


OVERVIEW_AT = "2027-05-20 10:05:00"  # §10.1: before the clarification deadline and the addendum


def set_instant(instant: str) -> None:
	"""The live pages' trusted clock for this world (plan D18)."""
	from kentender_procurement.bid_submission.services import simulation

	simulation.set_controls(current_instant=instant)


def set_gate(*, closed: bool) -> None:
	"""This world's production gate (plan D5): the test site keeps the switch
	on so a bid can be submitted in a browser; a GATE world closes it through
	the test controls, never through the site's own setting."""
	from kentender_procurement.bid_submission.services import simulation

	simulation.set_controls(gate_closed=1 if closed else 0)


def set_bound_release(*, state: str = "") -> dict[str, Any]:
	"""BDS-DES-02-SUPERSEDED / -WITHDRAWN-RELEASE / BDS-DES-06-WITHDRAWN-RELEASE
	worlds (BDS-CHG-001 §4.4.4): every bound release reads as `state`
	("Superseded", "Withdrawn", "Integrity failed"; "" = as installed)
	through the test controls; the installed release is never changed, and
	`restore_site` resets it."""
	from kentender_procurement.bid_submission.services import simulation

	simulation.set_controls(bound_release_state=state)
	frappe.db.commit()
	return {"bound_release_state": state}


PORTAL_STASH = "kt_pw_bds_supplier_support_email"


def set_portal_information(*, complete: bool) -> dict[str, Any]:
	"""BDS-DES-16 supplier-information variants: this world blanks the
	supplier support email so the portal information is Incomplete, keeping
	the site's value aside; `complete` (and `restore_site`) puts it back."""
	from kentender_core.services import public_portal

	if complete:
		_restore_portal_information()
	else:
		current = frappe.db.get_single_value(public_portal.SETTINGS, "supplier_support_email")
		if current and not frappe.db.get_default(PORTAL_STASH):
			frappe.db.set_default(PORTAL_STASH, current)
		frappe.db.set_single_value(public_portal.SETTINGS, "supplier_support_email", "", update_modified=False)
	frappe.db.commit()
	return {"status": public_portal.get_public_portal_information().get("status")}


def _restore_portal_information() -> None:
	from kentender_core.services import public_portal

	stashed = frappe.db.get_default(PORTAL_STASH)
	if stashed:
		frappe.db.set_single_value(public_portal.SETTINGS, "supplier_support_email", stashed, update_modified=False)
		from frappe.defaults import clear_default

		clear_default(PORTAL_STASH)


def reset_overview_fixture(*, commit: bool = True, started: bool = True, gate_closed: bool = False) -> dict[str, Any]:
	"""BDS-DES-02 world: the Tenders test Tender, open, with this world's
	two suppliers; Afya (Test) has started its bid when `started`."""
	set_bound_release(state="")  # a world starts on its installed release (before Tenders registers a candidate)
	state = tender_pw.reset_published_fixture(commit=False)
	_wipe_journal()
	_ensure_suppliers()
	bid = _start(state["tender"], "afya") if started else ""
	set_instant(OVERVIEW_AT)
	set_gate(closed=gate_closed)
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {"tender": state["tender"], "tender_reference": state["tender_reference"], "bid_reference": bid, "password": PASSWORD, **{f"{k}_user": v["representative"] for k, v in SUPPLIERS.items()}, "afya_signatory": SUPPLIERS["afya"]["registrant"]}


MY_BIDS_STATES = ("empty", "started", "addendum", "ready", "submitted", "withdrawn", "review", "review-evidence", "review-addendum", "pending")
# BDS-DES-11 worlds: a Ready bid whose physical original Charles has recorded;
# then either its datasheet's only file is rejected, or the addendum changes
# the Tender and David's next change moves the Draft to it.
REVIEW_STEPS = {"intake": "2027-05-20 10:20:00", "reject": "2027-05-20 10:25:00", "refresh": "2027-06-01 12:10:00"}
REVIEW_ADDENDUM_AT = "2027-06-01 12:15:00"
EICAR = b"\n% X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*\n"
ADDENDUM_AT = "2027-06-01 12:05:00"  # BDS-DES-07: after the addendum is effective, before acknowledgement
MY_BIDS_STEPS = {"fill": "2027-05-20 10:10:00", "submit": "2027-05-20 10:30:00", "withdraw": "2027-05-20 10:45:00"}
MY_BIDS_AT = "2027-05-20 11:00:00"
WITHDRAWAL_REASON = "Our pricing changed; we will submit a corrected bid."


def _pinned(instant: str | None) -> None:
	frappe.flags.kt_bds_clock = instant
	frappe.flags.kt_tenders_clock = instant


def _submit(bid: str, signatory: str) -> str:
	"""Mary signs with the Test Trust Service and the Test Tender Box accepts
	the bid, with the production switch on for this fixture process only
	(`availability.enabled_for_test_world`); the site's own setting stays off."""
	from kentender_procurement.bid_submission.services import availability, signature, simulation, submission
	from kentender_procurement.bid_submission.test_services import trust

	organisation = frappe.db.get_value("Bid Workspace", bid, "lead_organisation")
	trust.issue_certificate(user=signatory, organisation=organisation, subject_name=frappe.db.get_value("User", signatory, "full_name"), valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59")
	with availability.enabled_for_test_world():
		simulation.reset_controls()
		version = lambda: frappe.db.get_value("Bid Workspace", bid, "record_version")  # noqa: E731
		request = signature.prepare_bid_signature(bid_reference=bid, confirmed=True, expected_record_version=version(), idempotency_key=_key(), user=signatory)
		if not request.get("ok"):
			frappe.throw(f"The test bid could not be signed: {request}")
		signed = signature.sign_with_test_trust_service(signing_request=request["signing_request"], user=signatory)
		result = submission.submit_bid(bid_reference=bid, signature_ref=signed["signature"], confirmed=True, expected_record_version=version(), idempotency_key=_key(), user=signatory)
	if not result.get("ok"):
		frappe.throw(f"The test bid could not be submitted: {result}")
	return result["receipt_reference"]


def _record_original(bid: str) -> str:
	"""Charles records the physical original of this bid's own instrument
	(blind intake; the private match links it to the bid)."""
	from kentender_procurement.bid_submission.services import bid_context, security_intake, tender_security

	from frappe.utils import get_datetime

	representative = SUPPLIERS["afya"]["representative"]
	security = tender_security.response(bid_context.load(bid, actor=representative, organisation="", at=get_datetime(REVIEW_STEPS["intake"])))
	reference = frappe.db.get_value("Bid Workspace", bid, "tender_reference")
	recorded = security_intake.record_physical_tender_security_receipt(
		tender_reference=reference, instrument_type=security["security_type"], issuer=security["issuer"], instrument_reference=security["reference"],
		amount=security["amount"], currency=security["currency"], received_at="2027-05-20 10:00:00", notes="", confirmed=True, idempotency_key=_key(), user=RECORDER,
	)
	if not recorded.get("ok"):
		frappe.throw(f"The physical original could not be recorded: {recorded}")
	return recorded["intake_reference"]


def _reject_datasheet(bid: str, user: str) -> str:
	"""The Evidence rejected fixture: the datasheet's only file is removed and
	its replacement fails the Test Scanner."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import evidence, reads

	version = lambda: frappe.db.get_value("Bid Workspace", bid, "record_version")  # noqa: E731
	fields = [f for g in reads.get_bid_task(bid_reference=bid, task="requirements", user=user)["groups"] for f in g["fields"] if f["kind"] == "evidence" and f["required"] and len(f["evidence"]["files"]) == 1]
	field = next((f for f in fields if "datasheet" in f["label"].lower()), fields[0])
	evidence.remove_bid_evidence(bid_reference=bid, evidence_id=field["evidence"]["files"][0]["id"], expected_record_version=version(), idempotency_key=_key(), user=user)
	refused = evidence.upload_bid_evidence(bid_reference=bid, handle=field["handle"], filename="apexbook-datasheet.pdf", content=filling.pdf("datasheet") + EICAR, expected_record_version=version(), idempotency_key=_key(), user=user)
	if refused.get("ok"):
		frappe.throw("The test scanner accepted the EICAR test file.")
	return field["label"]


def _refresh_for_addendum(bid: str, user: str) -> None:
	"""David's first change after the addendum moves the Draft to it."""
	from kentender_procurement.bid_submission.services import reads, save

	price = reads.get_bid_task(bid_reference=bid, task="price", user=user)
	unit = next(f for g in price["groups"] for f in g["fields"] if f["kind"] == "money")
	result = save.save_bid_task(bid_reference=bid, task="price", values={unit["handle"]: unit["value"]}, expected_record_version=frappe.db.get_value("Bid Workspace", bid, "record_version"), idempotency_key=_key(), user=user)
	if not result.get("refreshed"):
		frappe.throw(f"The Draft did not move to the addendum: {result}")


def _certificate(bid: str) -> str:
	"""Mary's approved certificate from the Test Trust Service (the review and
	submit worlds: she can sign)."""
	from kentender_procurement.bid_submission.test_services import trust

	signatory = SUPPLIERS["afya"]["registrant"]
	return trust.issue_certificate(
		user=signatory, organisation=frappe.db.get_value("Bid Workspace", bid, "lead_organisation"), subject_name=frappe.db.get_value("User", signatory, "full_name"),
		valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59",
	)


# BDS-DES-12 worlds on a Ready bid, through the test controls only (plan D5).
SUBMISSION_WORLDS = {
	"normal": {}, "signature": {"trust_service_down": 1}, "service": {"custody_service_down": 1},
	"reject": {"deposit_outcome": "Reject", "rejection_reference": "TBX-REJECT-033-01"}, "uncertain": {"deposit_outcome": "Uncertain"},
}


def set_submission_world(*, world: str) -> dict[str, Any]:
	"""The signing and custody outcome for the next submission in this world."""
	from kentender_procurement.bid_submission.services import simulation

	keys = ("trust_service_down", "time_service_down", "custody_service_down", "deposit_outcome", "rejection_reference", "uncertain_resolution")
	simulation.set_controls(**{**{k: simulation.DEFAULTS[k] for k in keys}, **SUBMISSION_WORLDS[world]})
	return {"world": world}


def _submit_uncertain(bid: str, signatory: str) -> str:
	"""Mary signs and submits; the Test Tender Box does not answer, so the
	attempt stays Confirmation pending (BDS-DES-12-PENDING, §10.17)."""
	from kentender_procurement.bid_submission.services import signature, simulation, submission

	version = lambda: frappe.db.get_value("Bid Workspace", bid, "record_version")  # noqa: E731
	simulation.set_controls(deposit_outcome="Uncertain")
	request = signature.prepare_bid_signature(bid_reference=bid, confirmed=True, expected_record_version=version(), idempotency_key=_key(), user=signatory)
	signed = signature.sign_with_test_trust_service(signing_request=request["signing_request"], user=signatory)
	result = submission.submit_bid(bid_reference=bid, signature_ref=signed["signature"], confirmed=True, expected_record_version=version(), idempotency_key=_key(), user=signatory)
	if result.get("code") != "BDS_SUBMISSION_UNCERTAIN":
		frappe.throw(f"The test attempt did not stay pending: {result}")
	return result["correlation_id"]


def change_bid_as_representative(*, bid_reference: str) -> dict[str, Any]:
	"""David changes the offered model while another person has the bid open
	(the §10.17 Stale Draft world); the bid stays Ready to submit."""
	from kentender_procurement.bid_submission.services import reads, save

	david = SUPPLIERS["afya"]["representative"]
	saved_clock = frappe.flags.get("kt_bds_clock")
	frappe.flags.kt_bds_clock = MY_BIDS_AT
	try:
		field = next(f for g in reads.get_bid_task(bid_reference=bid_reference, task="requirements", user=david)["groups"] for f in g["fields"] if f.get("key") == "offered_make_model" or f["label"] == "Offered make and model")
		result = save.save_bid_task(bid_reference=bid_reference, task="requirements", values={field["handle"]: "ApexBook Pro 14 (updated)"}, expected_record_version=frappe.db.get_value("Bid Workspace", bid_reference, "record_version"), idempotency_key=_key(), user=david)
	finally:
		frappe.flags.kt_bds_clock = saved_clock
	if not result.get("ok"):
		frappe.throw(f"The representative's change was refused: {result}")
	frappe.db.commit()
	return {"record_version": frappe.db.get_value("Bid Workspace", bid_reference, "record_version")}


# -- the release pass (plan Phase 12): the §13.3 lifecycle on this world ------------------


def fill_world_bid(*, bid_reference: str, tasks: list[str] | tuple[str, ...] = ("company", "requirements", "price"), at: str = MY_BIDS_STEPS["fill"]) -> dict[str, Any]:
	"""David completes the named tasks with the §10.1 facts (the canonical
	seed's own answers), through the real commands at `at`."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.seeds import kentender_mvp_v1 as lifecycle

	david = SUPPLIERS["afya"]["representative"]
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_bds_clock", "kt_bds_fixture_namespace")}
	frappe.flags.kt_bds_clock = at
	frappe.flags.kt_bds_fixture_namespace = NAMESPACE
	try:
		filling.fill_everything(bid_reference, user=david, tasks=tuple(tasks), answers=lifecycle.fixture_answers(bid_reference, at=at, actor=david))
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	frappe.db.commit()
	return {"status": frappe.db.get_value("Bid Workspace", bid_reference, "status")}


def issue_world_addendum(*, tender_reference: str, instant: str = ADDENDUM_AT) -> dict[str, Any]:
	"""The Tenders world issues its addendum (31 May); the pages then read at `instant`."""
	tender = frappe.db.get_value("Tender", {"tender_reference": tender_reference}, "name")
	state = tender_pw._issued_addendum(tender)
	set_instant(instant)
	frappe.db.commit()
	return {"addendum": state.get("addendum")}


def world_security(*, bid_reference: str) -> dict[str, Any]:
	"""The instrument details the bid gave (what Charles reads off the original)."""
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context, tender_security

	security = tender_security.response(bid_context.load(bid_reference, actor=SUPPLIERS["afya"]["representative"], organisation="", at=get_datetime(MY_BIDS_AT)))
	return {k: security.get(k) for k in ("security_type", "issuer", "reference", "amount", "currency")}


def close_world(*, tender_reference: str, at: str = "2027-06-12 11:00:00") -> dict[str, Any]:
	"""Tenders ends the submission period at the deadline and Bid Submission
	closes the box and hands it to Bid Opening; the pages then read just after."""
	from kentender_procurement.bid_submission.seeds import kentender_mvp_v1 as lifecycle
	from kentender_procurement.tenders.services import submission_close

	tender = frappe.db.get_value("Tender", {"tender_reference": tender_reference}, "name")
	saved = frappe.flags.get("kt_tenders_clock")
	frappe.flags.kt_tenders_clock = at
	try:
		submission_close.close_tender_submission_period(tender=tender, idempotency_key=_key(), user="Administrator", force=True)
	finally:
		frappe.flags.kt_tenders_clock = saved
	closed = lifecycle._close(tender, at=at, namespace=NAMESPACE)
	set_instant(frappe.utils.add_to_date(at, seconds=1, as_string=True))
	frappe.db.commit()
	import json

	payload = json.loads(frappe.db.get_value("Bid Opening Handoff", closed["handoff"], "payload_json") or "{}")
	return {"handoff": closed["handoff"], "payload_keys": sorted(payload), "envelopes": frappe.db.get_value("Bid Submission Close", closed["close"], "envelopes_sealed"), "payload_text": json.dumps(payload)}


def issue_signatory_certificate(*, bid_reference: str) -> dict[str, Any]:
	"""Mary obtains her certificate (from the Test Trust Service)."""
	saved = frappe.flags.get("kt_bds_fixture_namespace")
	frappe.flags.kt_bds_fixture_namespace = NAMESPACE
	try:
		certificate = _certificate(bid_reference)
	finally:
		frappe.flags.kt_bds_fixture_namespace = saved
	frappe.db.commit()
	return {"certificate": certificate}


def revoke_signatory_certificate() -> dict[str, Any]:
	"""BDS-DES-12-CERTIFICATE: Mary's certificates in this world are revoked."""
	from kentender_procurement.bid_submission.test_services import trust

	refs = frappe.get_all(trust.CERTIFICATE, filters={"user": SUPPLIERS["afya"]["registrant"], "status": ("!=", "Revoked")}, pluck="certificate_ref")
	for ref in refs:
		trust.revoke_certificate(ref)
	return {"revoked": len(refs)}


def reset_my_bids_fixture(*, state: str = "ready", commit: bool = True, gate_closed: bool = False) -> dict[str, Any]:
	"""BDS-DES-05 / BDS-DES-17 worlds on the Tenders test Tender for Afya
	(Test): "empty" (no bid), "started" (a new Draft), "addendum" (a new Draft,
	then the Tenders world issues its addendum; its notice stays queued),
	"ready" (every task answered: Ready to submit),
	"submitted" (Mary signed; the Test Tender Box accepted it) or "withdrawn"
	(then withdrawn by Mary). Each step runs the real command as its actor."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import withdrawal

	if state not in MY_BIDS_STATES:
		raise ValueError(f"unknown My bids world {state!r}; one of {MY_BIDS_STATES}")
	set_bound_release(state="")  # a world starts on its installed release (before Tenders registers a candidate)
	tender = tender_pw.reset_published_fixture(commit=False)
	_wipe_journal()
	_ensure_suppliers()
	afya = SUPPLIERS["afya"]
	bid = receipt = acknowledgement = ""
	namespace = frappe.flags.get("kt_bds_fixture_namespace")
	frappe.flags.kt_bds_fixture_namespace = NAMESPACE  # this world's records are removed exactly by restore_site
	try:
		if state != "empty":
			_pinned(MY_BIDS_STEPS["fill"])
			bid = _start(tender["tender"], "afya")
		if state not in ("empty", "started", "addendum"):
			filling.fill_everything(bid, user=afya["representative"])
		if state == "addendum":
			tender_pw._issued_addendum(tender["tender"])
		if state.startswith("review") or state == "pending":
			_pinned(REVIEW_STEPS["intake"])
			_record_original(bid)
			_certificate(bid)
		if state == "review-evidence":
			_pinned(REVIEW_STEPS["reject"])
			_reject_datasheet(bid, afya["representative"])
		if state == "pending":
			_pinned(REVIEW_STEPS["reject"])
			_submit_uncertain(bid, afya["registrant"])
		if state == "review-addendum":
			tender_pw._issued_addendum(tender["tender"])
			_pinned(REVIEW_STEPS["refresh"])
			_refresh_for_addendum(bid, afya["representative"])
		if state in ("submitted", "withdrawn"):
			_pinned(MY_BIDS_STEPS["submit"])
			receipt = _submit(bid, afya["registrant"])
		if state == "withdrawn":
			_pinned(MY_BIDS_STEPS["withdraw"])
			done = withdrawal.withdraw_bid(
				bid_reference=bid, receipt_reference=receipt, reason=WITHDRAWAL_REASON, confirmed=True, expected_record_version=frappe.db.get_value("Bid Workspace", bid, "record_version"),
				idempotency_key=_key(), user=afya["registrant"],
			)
			acknowledgement = done["acknowledgement_reference"]
	finally:
		_pinned(None)
		frappe.flags.kt_bds_fixture_namespace = namespace
	set_instant(ADDENDUM_AT if state == "addendum" else REVIEW_ADDENDUM_AT if state == "review-addendum" else MY_BIDS_AT)
	set_gate(closed=gate_closed)
	set_submission_world(world="normal")
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {
		"state": state, "tender_reference": tender["tender_reference"], "bid_reference": bid, "receipt_reference": receipt, "acknowledgement_reference": acknowledgement,
		"organisation": frappe.db.get_value("Bid Workspace", bid, "lead_organisation") if bid else "",
		"password": PASSWORD, "representative": afya["representative"], "signatory": afya["registrant"], "other_user": SUPPLIERS["kisiwa"]["representative"],
	}


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	frappe.set_user("Administrator")
	_wipe_journal()
	out = tender_pw.restore_site(commit=False)
	bds_clear.wipe(tenders=[], namespace=NAMESPACE)
	# test certificates and signatures held by this world's own people (older
	# worlds issued them without the namespace stamp)
	for doctype in ("Test Trust Signature", "Test Trust Certificate"):
		frappe.db.delete(doctype, {"user": ("in", list(SUPPLIER_USERS))})
	from kentender_procurement.bid_submission.services import simulation

	simulation.reset_controls()  # the test clock and every forced world back to normal
	_restore_portal_information()
	removal = frappe.get_hooks("kt_seed_supplier_account_removal") or []
	if removal:
		frappe.get_attr(removal[-1])(namespace=NAMESPACE, users=SUPPLIER_USERS)
	if commit:
		frappe.db.commit()
	return {**out, "bid_submission_wiped": True}
