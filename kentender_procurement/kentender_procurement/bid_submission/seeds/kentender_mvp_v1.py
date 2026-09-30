# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical bid lifecycle (BDS-CHG-001 v0.8 §13.3 with the §10.1 facts;
plan Phase 12, D19), built through the real commands as the named actors at
the spec's own instants, interleaved with the Tenders chronology:

- 19 May 2027 09:20 — David Ouma starts Afya's bid (the Tenders stage's
  candidate step, `canonical.seed_candidate`);
- 20 May 10:10 — David completes the company and requirements tasks with the
  §10.1 facts (ApexBook Pro 14, delivery 15 Sep 2027, 36 months' warranty,
  4 hours' support response; the KCB Bank Kenya guarantee KCB/TG/2027/8841);
- 1 Jun 12:10 — after the 31 May addendum, David's next change moves the
  Draft to the current definition and he acknowledges the addendum;
- 10 Jun 10:00 — Charles Mutiso records the physical tender-security original
  (blind intake; the private match links it to the bid);
- 10 Jun 13:50 — David enters the price (250 × KES 160,000, tax
  KES 6,400,000): the Draft is complete;
- 10 Jun 14:31:58 — Mary Wanjiku signs with the Test Trust Service and the
  Test Tender Box accepts Version 1 at 14:32:01;
- 12 Jun 11:00 — after Tenders ends the submission period, Bid Submission
  closes and hands the sealed box to Bid Opening.

The certificate, signature and tender-box receipt are simulation evidence,
labelled so; the stage refuses to run where the simulated services are not
installed (a test site only). Idempotent: a canonical bid that already has
its receipt is returned untouched."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.seeds import canonical as bds_canonical

NAMESPACE = bds_canonical.NAMESPACE
DAVID = bds_canonical.DAVID
MARY = "mary.wanjiku@afyadigital.example"
CHARLES = "charles.mutiso@moh.example.test"
CLOCK = {
	"fill": "2027-05-20 10:10:00",
	"acknowledge": "2027-06-01 12:10:00",
	"intake": "2027-06-10 10:00:00",
	"complete": "2027-06-10 13:50:00",
	"submit": "2027-06-10 14:31:58",
	"close": "2027-06-12 11:00:00",
}
ACCEPT_AFTER_SECONDS = 3  # received 14:31:58, accepted 14:32:01 (§10.1)
GOODS = {"offered_make_model": "ApexBook Pro 14", "offered_delivery_date": "2027-09-15"}
WARRANTY = {"minimum_warranty_months": 36, "maximum_support_response_hours": 4}
PRICE = {"unit_price": "160000", "tax_amount": "6400000"}
SECURITY = {"security_form": "Demand Bank Guarantee", "issuer": "KCB Bank Kenya", "guarantee_reference": "KCB/TG/2027/8841"}
CERTIFICATE = {"subject_name": "Mary Wanjiku", "valid_from": "2027-01-01 00:00:00", "valid_to": "2027-12-31 23:59:59"}


def _key(step: str) -> str:
	return f"bds-seed:{step}:{uuid4().hex[:8]}"


@contextmanager
def _at(instant: str, namespace: str = NAMESPACE):
	"""Bid Submission's trusted clock at `instant`, and this world's namespace
	on everything the commands record."""
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_bds_clock", "kt_bds_fixture_namespace")}
	frappe.flags.kt_bds_clock = instant
	frappe.flags.kt_bds_fixture_namespace = namespace
	try:
		yield
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value


def _guard() -> None:
	from kentender_procurement.bid_submission.services import simulation

	if not simulation.enabled():
		frappe.throw(
			"The canonical bid lifecycle signs and submits through the Test Trust Service and the Test Tender Box, "
			"which exist only on a test site (site_config kt_bds_simulation_environment = 1)."
		)


def canonical_bid(tender: str) -> str:
	return cstr(frappe.db.get_value("Bid Workspace", {"tender": tender, "lead_organisation": _afya()}, "name"))


def _afya() -> str:
	from kentender_procurement.bid_submission.services import supplier_gateway

	return cstr((supplier_gateway.find_active_account(country=bds_canonical.AFYA_COUNTRY, registration_number=bds_canonical.AFYA_REGISTRATION) or {}).get("organisation_id"))


def _version(bid: str):
	return frappe.db.get_value("Bid Workspace", bid, "record_version")


def _answer_field(group):
	"""The response field of a requirement row (not its evidence, comment or
	compliance field) — the same choice the review page makes."""
	return next((f for f in group.fields if f.control_id not in ("CTL-EVIDENCE", "CTL-LONG-TEXT") and "compliance" not in f.label.lower()), None)


def fixture_answers(bid: str, *, at: str, actor: str = DAVID) -> dict[str, dict[str, Any]]:
	"""The §10.1 facts as each task's values by field handle, found by the
	published definition's own field keys and obligation keys."""
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context

	ctx = bid_context.load(bid, actor=actor, organisation="", at=get_datetime(at))
	out: dict[str, dict[str, Any]] = {"company": {}, "requirements": {}, "price": {}}
	for group in ctx.model.groups_of("requirements"):
		facts = group.published_facts or {}
		if group.composition_id == "COMP-GOODS-OFFER":
			for field in group.fields:
				if field.field_key in GOODS:
					out["requirements"][field.handle] = GOODS[field.field_key]
		if group.composition_id == "COMP-WARRANTY-SUPPORT" and facts.get("obligation_key") in WARRANTY:
			field = _answer_field(group)
			if field:
				out["requirements"][field.handle] = WARRANTY[facts["obligation_key"]]
	handle_of = {f.response_id: f.handle for g in ctx.model.groups_of("price") for f in g.fields}
	for row in ctx.model.price_rows:
		for name, response in (row.get("input_response_ids") or {}).items():
			if name in PRICE and response in handle_of:
				out["price"][handle_of[response]] = PRICE[name]
	from kentender_procurement.bid_submission.services import security_matching

	for group in ctx.model.groups_of("company"):
		if group.rule_id != security_matching.SECURITY_RULE:
			continue
		facts = group.published_facts or {}
		values = {**SECURITY, "instrument_amount": cstr(facts.get("amount")), "bank_guarantee_valid_until": cstr(facts.get("bank_guarantee_expiry_date"))}
		for field in group.fields:
			if field.field_key in values and values[field.field_key]:
				out["company"][field.handle] = values[field.field_key]
	return out


def _fill(bid: str, tasks: tuple[str, ...], at: str) -> None:
	from kentender_procurement.bid_submission.seeds import filling

	with _at(at):
		filling.fill_everything(bid, user=DAVID, tasks=tasks, answers=fixture_answers(bid, at=at))


def _acknowledge_addendum(bid: str) -> None:
	"""David's first change after the addendum moves the Draft to the current
	definition (§4.4.6); he then saves the acknowledgement and the affected
	responses."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import reads, save

	with _at(CLOCK["acknowledge"]):
		documents = reads.get_bid_task(bid_reference=bid, task="documents", user=DAVID)
		ticks = {f["handle"]: True for g in documents["groups"] for f in g["fields"] if f["kind"] == "confirmation" and f["editable"] and f["visible"]}
		first = save.save_bid_task(bid_reference=bid, task="documents", values=ticks, expected_record_version=_version(bid), idempotency_key=_key("acknowledge"), user=DAVID)
		if first.get("code") == "BDS_ADDENDUM_REVIEW_REQUIRED" or not first.get("ok"):
			documents = reads.get_bid_task(bid_reference=bid, task="documents", user=DAVID)
			ticks = {f["handle"]: True for g in documents["groups"] for f in g["fields"] if f["kind"] == "confirmation" and f["editable"] and f["visible"]}
			again = save.save_bid_task(bid_reference=bid, task="documents", values=ticks, expected_record_version=_version(bid), idempotency_key=_key("acknowledge-2"), user=DAVID)
			if not again.get("ok"):
				frappe.throw(f"The canonical bid could not acknowledge the addendum: {again}")
	# the responses the addendum affected are reviewed and saved again
	_fill(bid, ("company", "requirements"), CLOCK["acknowledge"])
	with _at(CLOCK["acknowledge"]):
		for task in ("company", "requirements"):
			view = reads.get_bid_task(bid_reference=bid, task=task, user=DAVID)
			if view["task"]["status"] == "Needs attention":
				values = {f["handle"]: f["value"] if f["value"] not in (None, "", []) else filling.sample_value(f) for g in view["groups"] for f in g["fields"] if f["editable"] and f["visible"] and f["kind"] != "evidence"}
				saved = save.save_bid_task(bid_reference=bid, task=task, values=values, expected_record_version=_version(bid), idempotency_key=_key(f"review-{task}"), user=DAVID)
				if not saved.get("ok"):
					frappe.throw(f"The canonical bid could not save its reviewed {task} task: {saved}")


def _record_original(tender_reference: str, bid: str) -> str:
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context, security_intake, tender_security

	with _at(CLOCK["intake"]):
		security = tender_security.response(bid_context.load(bid, actor=DAVID, organisation="", at=get_datetime(CLOCK["intake"])))
		recorded = security_intake.record_physical_tender_security_receipt(
			tender_reference=tender_reference, instrument_type=security["security_type"], issuer=security["issuer"], instrument_reference=security["reference"],
			amount=security["amount"], currency=security["currency"], received_at=CLOCK["intake"], notes="", confirmed=True, idempotency_key=_key("intake"), user=CHARLES,
		)
	if not recorded.get("ok"):
		frappe.throw(f"Charles could not record the canonical physical original: {recorded}")
	return recorded["intake_reference"]


def _submit(bid: str) -> str:
	from kentender_procurement.bid_submission.services import availability, signature, simulation, submission
	from kentender_procurement.bid_submission.test_services import trust

	organisation = frappe.db.get_value("Bid Workspace", bid, "lead_organisation")
	with _at(CLOCK["submit"]):
		if not frappe.db.exists(trust.CERTIFICATE, {"user": MARY, "organisation": organisation, "status": ("!=", "Revoked")}):
			trust.issue_certificate(user=MARY, organisation=organisation, **CERTIFICATE)
		with availability.enabled_for_test_world():
			simulation.set_controls(accept_after_seconds=ACCEPT_AFTER_SECONDS, deposit_outcome="Accept")
			try:
				request = signature.prepare_bid_signature(bid_reference=bid, confirmed=True, expected_record_version=_version(bid), idempotency_key=_key("sign"), user=MARY)
				if not request.get("ok"):
					frappe.throw(f"Mary could not sign the canonical bid: {request}")
				signed = signature.sign_with_test_trust_service(signing_request=request["signing_request"], user=MARY)
				result = submission.submit_bid(bid_reference=bid, signature_ref=signed["signature"], confirmed=True, expected_record_version=_version(bid), idempotency_key=_key("submit"), user=MARY)
			finally:
				simulation.set_controls(accept_after_seconds=0)
	if not result.get("ok"):
		frappe.throw(f"The Test Tender Box did not accept the canonical bid: {result}")
	return result["receipt_reference"]


def _close(tender: str, *, at: str = CLOCK["close"], namespace: str = NAMESPACE) -> dict[str, Any]:
	"""Bid Submission's own close for the event Tenders just wrote (the
	scheduler consumer's work, without its per-event commit)."""
	from kentender_procurement.bid_submission.services import close, tenders_gateway

	with _at(at, namespace):
		events = [e for e in tenders_gateway.pending_events(event_type=close.PERIOD_ENDED, consumer=close.CONSUMER) if e.tender == tender]
		result = close.close_bid_submission(tender=tender, source_event=events[0].name if events else "", tenders_handoff=cstr(events[0].subject_id) if events else "")
		for event in events:
			tenders_gateway.mark_event_consumed(event, consumer=close.CONSUMER)
	return result


def interleave(step: str, *, tender: str, tender_reference: str) -> dict[str, Any] | None:
	"""The Tenders seed's step callback (`upsert_tenders_base(interleave=…)`):
	the bid's own events at the moments §13.3 puts them."""
	if step == "candidate_registered":
		_guard()
		bid = canonical_bid(tender)
		_fill(bid, ("company", "requirements"), CLOCK["fill"])
		return {"bid": bid}
	if step == "addendum_effective":
		_acknowledge_addendum(canonical_bid(tender))
		return None
	if step == "before_close":
		bid = canonical_bid(tender)
		intake = _record_original(tender_reference, bid)
		_fill(bid, ("price",), CLOCK["complete"])
		return {"intake": intake, "receipt": _submit(bid)}
	if step == "closed":
		return _close(tender)
	return None


def lifecycle_complete(tender: str) -> bool:
	bid = canonical_bid(tender) if tender else ""
	return bool(bid) and bool(frappe.db.exists("Bid Receipt", {"bid_workspace": bid})) and bool(frappe.db.exists("Bid Submission Close", {"tender": tender}))


def upsert_bid_submission_base(*, commit: bool = False) -> dict[str, Any]:
	"""The `bid_submission` stage: the canonical Tender built through the
	Tenders seed with the bid's steps interleaved. One already carrying the
	lifecycle is returned untouched. A Tender the `tenders` stage built alone
	(its bid a Draft when the period closed) cannot be given the lifecycle
	afterwards — the Requisition's hand-off is consumed once — so that world
	needs a rebuild."""
	from kentender_procurement.tenders.seeds import kentender_mvp_v1 as tenders_seed

	_guard()
	# The canonical supplier account on every run, not only when the bid is
	# first built: it is idempotent, and it converges its people's sign-in
	# (the shared fixture password) on a world seeded before that existed.
	bds_canonical._hook("kt_canonical_supplier_accounts")()
	prerequisites = tenders_seed.verify_prerequisites()
	tender = cstr(frappe.db.get_value("Tender", {"requisition": prerequisites["requisition"]}, "name"))
	if tender and lifecycle_complete(tender):
		result = {"ok": True, "idempotent": True, "tender": tender, "bid": canonical_bid(tender)}
	elif tender:
		frappe.throw(
			f"The canonical Tender {tender} was seeded without the bid lifecycle. Rebuild the canonical world through this stage: "
			"make seed-canonical THROUGH=bid_submission REBUILD=True."
		)
	else:
		built = tenders_seed.upsert_tenders_base(commit=False, interleave=interleave)
		result = {"ok": True, "idempotent": False, "tender": built["tender"], "bid": canonical_bid(built["tender"]), "steps": built.get("interleaved", {})}
	if commit:
		frappe.db.commit()
	return result


def validate_bid_submission_seed() -> list[dict[str, Any]]:
	"""One row per §13.3 fact the canonical bid must carry. Never mutates."""
	from kentender_procurement.tenders.seeds import kentender_mvp_v1 as tenders_seed

	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label})

	organisation = _afya()
	check(bool(organisation), "Afya Digital Supplies Limited has an Active supplier account")
	requisition = tenders_seed.verify_prerequisites()["requisition"]
	tender = cstr(frappe.db.get_value("Tender", {"requisition": requisition}, "name"))
	bid = canonical_bid(tender) if tender else ""
	check(bool(bid), "the canonical Tender has Afya's bid")
	if not bid:
		return rows
	ws = frappe.db.get_value("Bid Workspace", bid, ["status", "current_submission_version", "fixture_namespace"], as_dict=True)
	check(ws.status == "Submitted", f"the bid is Submitted (got {ws.status!r})")
	version = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "status", "receipt"], as_dict=True) if ws.current_submission_version else None
	check(bool(version) and int(version.version_number) == 1 and version.status == "Submitted", "Submitted bid Version 1 is current")
	receipt = frappe.db.get_value("Bid Receipt", {"receipt_reference": version.receipt}, ["received_at", "accepted_at", "submitted_by", "simulation"], as_dict=True) if version else None
	check(bool(receipt) and cstr(receipt.received_at) == "2027-06-10 14:31:58", "received by the tender-box service at 10 Jun 2027, 14:31:58 EAT")
	check(bool(receipt) and cstr(receipt.accepted_at) == "2027-06-10 14:32:01", "accepted into the tender box at 10 Jun 2027, 14:32:01 EAT")
	check(bool(receipt) and receipt.submitted_by == MARY, "Mary Wanjiku submitted it")
	check(bool(receipt) and int(receipt.simulation or 0) == 1, "the receipt is labelled simulation")
	acknowledgement = frappe.db.get_value("Bid Draft Change", {"bid_workspace": bid, "actor": DAVID, "changed_at": CLOCK["acknowledge"]}, "name")
	check(bool(acknowledgement), "David changed the Draft at 1 Jun 2027, 12:10 EAT (the addendum acknowledgement)")
	intake = frappe.db.get_value("Tender Security Intake", {"recorded_by": CHARLES, "received_at": CLOCK["intake"]}, ["name", "deadline_class"], as_dict=True)
	check(bool(intake), "Charles recorded the physical original at 10 Jun 2027, 10:00 EAT")
	check(bool(intake) and bool(frappe.db.exists("Tender Security Intake Match", {"intake": intake.name, "bid_workspace": bid})), "the intake privately matches the bid")
	close = frappe.db.get_value("Bid Submission Close", {"tender": tender}, ["name", "bid_opening_handoff", "envelopes_sealed"], as_dict=True)
	check(bool(close), "Bid Submission closed at the deadline")
	check(bool(close) and int(close.envelopes_sealed or 0) == 1, "one sealed envelope was handed over")
	check(bool(close) and bool(close.bid_opening_handoff), "a Bid Opening hand-off was written")
	rerun = upsert_bid_submission_base(commit=False)
	check(rerun.get("idempotent") is True and rerun.get("bid") == bid, "a second run is idempotent")
	return rows
