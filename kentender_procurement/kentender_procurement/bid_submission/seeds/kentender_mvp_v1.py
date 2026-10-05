# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical bid lifecycle (BDS-CHG-001 v0.8 §13.3 with the §10.1 facts;
plan Phase 12, D19), built through the real commands as the named actors at
the spec's own instants, interleaved with the Tenders chronology:

- 19 May 2027 09:20 — David Ouma starts Afya's bid (the Tenders stage's
  candidate step, `canonical.seed_candidate`);
- 20 May 10:10 — David completes the company and requirements tasks with the
  §10.1 facts (ApexBook Pro 14, delivery 24 Jun 2027 — inside the published
  30 Jun latest delivery, two-year seed world; was 15 Sep — 36 months' warranty,
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

Three more suppliers bid on the same Tender (Project Owner, 3 Oct 2026: "Four
bids"; their names are proposed for KT-STD-001 v1.14), each registering its
account and starting after the 31 May addendum, so the Tenders chronology
(one registered candidate at the clarification) is unchanged, and each
submitting after Afya, so Afya's bid is still the first opened:

- Jirani Office Supplies Limited — complies; KES 48,720,000 (ranked second);
- Pwani Tech Distributors Limited — the cheapest, KES 43,500,000, but offers
  8 GB of memory against the required 16 GB (fails technical compliance);
- Mlima Computer Solutions Limited — KES 46,980,000; complete on entry (Bid
  Submission refuses a wrong security amount, date or category), but the
  evaluation committee finds its eligibility evidence fails (Bid Evaluation's
  canonical stage).

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
from kentender_procurement.tenders.seeds.kentender_mvp_v1 import CanonicalTenderNeedsRebuild

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
GOODS = {"offered_make_model": "ApexBook Pro 14", "offered_delivery_date": "2027-06-24"}
WARRANTY = {"minimum_warranty_months": 36, "maximum_support_response_hours": 4}
PRICE = {"unit_price": "160000", "tax_amount": "6400000"}
SECURITY = {"security_form": "Demand Bank Guarantee", "issuer": "KCB Bank Kenya", "guarantee_reference": "KCB/TG/2027/8841"}
CERTIFICATE = {"subject_name": "Mary Wanjiku", "valid_from": "2027-01-01 00:00:00", "valid_to": "2027-12-31 23:59:59"}


def _profile(licence: str, director: str, year: int) -> dict[str, Any]:
	from kentender_suppliers.supplier_accounts.seeds.canonical import default_profile

	return {**default_profile(director), "trade_licence_number": licence, "year_of_registration": year}


#: The other canonical bidders, in submission order (all after Afya's). Each
#: `clock` instant is when that bidder's own step happens.
BIDDERS: tuple[dict[str, Any], ...] = (
	{
		"key": "jirani",
		"facts": {
			"legal_name": "Jirani Office Supplies Limited", "country": "Kenya", "registration_number": "PVT-4J8N2Q", "tax_identifier": "P051998877J",
			"registered_address": "Enterprise Road, Industrial Area, Nairobi", "official_email": "tenders@jirani.example", "official_phone": "+254 709 555 021",
			"job_title": "Managing Director",
		},
		"signatory": "faith.atieno@jirani.example", "signatory_name": "Faith Atieno",
		"representative": "kevin.kiprono@jirani.example", "representative_name": "Kevin Kiprono", "representative_title": "Tenders Officer",
		"profile": ("TL-2027-1187", "Faith Atieno", 2011),
		"goods": {"offered_make_model": "Vertex Book 14 G3", "offered_delivery_date": "2027-06-28"},
		"warranty": {"minimum_warranty_months": 36, "maximum_support_response_hours": 6},
		"price": {"unit_price": "168000", "tax_amount": "6720000"},  # 250 × 168,000 + 6,720,000 = KES 48,720,000
		"security": {"security_form": "Demand Bank Guarantee", "issuer": "Equity Bank Kenya", "guarantee_reference": "EQ/BG/2027/3317"},
		"overrides": {}, "security_amount": "",
		"clock": {
			# two-year seed world: registered before the executed portfolio's first bids (was 1 Jun 2027)
			"account": {"register": "2027-03-02 09:00:00", "verify": "2027-03-02 09:10:00", "representative": "2027-03-02 09:20:00"},
			"start": "2027-06-02 09:15:00", "fill": "2027-06-03 11:00:00", "intake": "2027-06-11 09:30:00", "complete": "2027-06-11 10:05:00",
			"submit": "2027-06-11 10:20:00",
		},
	},
	{
		"key": "pwani",
		"facts": {
			"legal_name": "Pwani Tech Distributors Limited", "country": "Kenya", "registration_number": "PVT-7P2W5T", "tax_identifier": "P052334411P",
			"registered_address": "Nyali Road, Mombasa", "official_email": "tenders@pwanitech.example", "official_phone": "+254 709 555 032",
			"job_title": "Director",
		},
		"signatory": "salim.omar@pwanitech.example", "signatory_name": "Salim Omar",
		"representative": "lucy.wairimu@pwanitech.example", "representative_name": "Lucy Wairimu", "representative_title": "Sales Executive",
		"profile": ("TL-2027-2245", "Salim Omar", 2018),
		"goods": {"offered_make_model": "LiteBook 14S", "offered_delivery_date": "2027-06-22"},
		"warranty": {"minimum_warranty_months": 36, "maximum_support_response_hours": 8},
		"price": {"unit_price": "150000", "tax_amount": "6000000"},  # 250 × 150,000 + 6,000,000 = KES 43,500,000
		"security": {"security_form": "Demand Bank Guarantee", "issuer": "Co-operative Bank of Kenya", "guarantee_reference": "COOP/TG/2027/0562"},
		"overrides": {"memory": 8},  # 8 GB against the required 16 GB
		"security_amount": "",
		"clock": {
			"account": {"register": "2027-03-03 10:00:00", "verify": "2027-03-03 10:10:00", "representative": "2027-03-03 10:20:00"},
			"start": "2027-06-03 10:00:00", "fill": "2027-06-04 10:30:00", "intake": "2027-06-11 15:00:00", "complete": "2027-06-11 15:30:00",
			"submit": "2027-06-11 16:45:00",
		},
	},
	{
		"key": "mlima",
		"facts": {
			"legal_name": "Mlima Computer Solutions Limited", "country": "Kenya", "registration_number": "PVT-3M6L9R", "tax_identifier": "P053456712M",
			"registered_address": "Kenyatta Avenue, Nakuru", "official_email": "tenders@mlimacomputers.example", "official_phone": "+254 709 555 043",
			"job_title": "Director",
		},
		"signatory": "joseph.kimutai@mlimacomputers.example", "signatory_name": "Joseph Kimutai",
		"representative": "agnes.moraa@mlimacomputers.example", "representative_name": "Agnes Moraa", "representative_title": "Tenders Coordinator",
		"profile": ("TL-2027-3310", "Joseph Kimutai", 2016),
		"goods": {"offered_make_model": "ApexBook Pro 14", "offered_delivery_date": "2027-06-30"},
		"warranty": {"minimum_warranty_months": 36, "maximum_support_response_hours": 4},
		"price": {"unit_price": "162000", "tax_amount": "6480000"},  # 250 × 162,000 + 6,480,000 = KES 46,980,000
		"security": {"security_form": "Demand Bank Guarantee", "issuer": "NCBA Bank Kenya", "guarantee_reference": "NCBA/BG/2027/7710"},
		"overrides": {}, "security_amount": "",
		"clock": {
			"account": {"register": "2027-03-04 14:00:00", "verify": "2027-03-04 14:10:00", "representative": "2027-03-04 14:20:00"},
			"start": "2027-06-04 14:00:00", "fill": "2027-06-07 10:00:00", "intake": "2027-06-12 09:15:00", "complete": "2027-06-12 09:40:00",
			"submit": "2027-06-12 10:05:00",
		},
	},
)
BIDDER_PEOPLE: tuple[str, ...] = tuple(email for b in BIDDERS for email in (b["signatory"], b["representative"]))


class CanonicalTenderIncomplete(CanonicalTenderNeedsRebuild):
	"""The canonical Tender exists without its bid lifecycle, or not in the
	shape this run asks for (open or closed). A bid submission commits at
	once (the attempt must survive a crash), so a run that failed after the
	bids leaves this behind; `canonical.run` rebuilds on it."""


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


def _organisation(bidder: dict[str, Any]) -> str:
	from kentender_procurement.bid_submission.services import supplier_gateway

	facts = bidder["facts"]
	return cstr((supplier_gateway.find_active_account(country=facts["country"], registration_number=facts["registration_number"]) or {}).get("organisation_id"))


def bidder_bid(tender: str, bidder: dict[str, Any]) -> str:
	organisation = _organisation(bidder)
	return cstr(frappe.db.get_value("Bid Workspace", {"tender": tender, "lead_organisation": organisation}, "name")) if organisation else ""


def _afya() -> str:
	from kentender_procurement.bid_submission.services import supplier_gateway

	return cstr((supplier_gateway.find_active_account(country=bds_canonical.AFYA_COUNTRY, registration_number=bds_canonical.AFYA_REGISTRATION) or {}).get("organisation_id"))


def _version(bid: str):
	return frappe.db.get_value("Bid Workspace", bid, "record_version")


def _answer_field(group):
	"""The response field of a requirement row (not its evidence, comment or
	compliance field) — the same choice the review page makes."""
	return next((f for f in group.fields if f.control_id not in ("CTL-EVIDENCE", "CTL-LONG-TEXT") and "compliance" not in f.label.lower()), None)


def fixture_answers(
	bid: str, *, at: str, actor: str = DAVID, goods: dict[str, Any] = GOODS, warranty: dict[str, Any] = WARRANTY, price: dict[str, Any] = PRICE,
	security: dict[str, Any] = SECURITY, overrides: dict[str, Any] | None = None, security_amount: str = "",
) -> dict[str, dict[str, Any]]:
	"""The §10.1 facts (or another bidder's) as each task's values by field
	handle, found by the published definition's own field keys and obligation
	keys. `overrides` answers a requirement short of what is published;
	`security_amount` replaces the published tender-security amount."""
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context

	from kentender_procurement.bid_submission.seeds import published_answers

	ctx = bid_context.load(bid, actor=actor, organisation="", at=get_datetime(at))
	# every published requirement answered so that it meets (EVL-CHG-001 v0.4 C22:
	# the evaluation's automatic checks read these), under the §10.1 facts below
	out: dict[str, dict[str, Any]] = {"company": {}, "requirements": {}, "price": {}, **published_answers.answers(bid, actor=actor, at=at, overrides=overrides)}
	out.setdefault("price", {})
	for group in ctx.model.groups_of("requirements"):
		facts = group.published_facts or {}
		if group.composition_id == "COMP-GOODS-OFFER":
			for field in group.fields:
				if field.field_key in goods:
					out["requirements"][field.handle] = goods[field.field_key]
		if group.composition_id == "COMP-WARRANTY-SUPPORT" and facts.get("obligation_key") in warranty:
			field = _answer_field(group)
			if field:
				out["requirements"][field.handle] = warranty[facts["obligation_key"]]
	handle_of = {f.response_id: f.handle for g in ctx.model.groups_of("price") for f in g.fields}
	for row in ctx.model.price_rows:
		for name, response in (row.get("input_response_ids") or {}).items():
			if name in price and response in handle_of:
				out["price"][handle_of[response]] = price[name]
	from kentender_procurement.bid_submission.services import security_matching

	for group in ctx.model.groups_of("company"):
		if group.rule_id != security_matching.SECURITY_RULE:
			continue
		facts = group.published_facts or {}
		values = {**security, "instrument_amount": security_amount or cstr(facts.get("amount")), "bank_guarantee_valid_until": cstr(facts.get("bank_guarantee_expiry_date"))}
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


def _record_original(tender_reference: str, bid: str, *, actor: str = DAVID, at: str = CLOCK["intake"]) -> str:
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context, security_intake, tender_security

	with _at(at):
		security = tender_security.response(bid_context.load(bid, actor=actor, organisation="", at=get_datetime(at)))
		recorded = security_intake.record_physical_tender_security_receipt(
			tender_reference=tender_reference, instrument_type=security["security_type"], issuer=security["issuer"], instrument_reference=security["reference"],
			amount=security["amount"], currency=security["currency"], received_at=at, notes="", confirmed=True, idempotency_key=_key("intake"), user=CHARLES,
		)
	if not recorded.get("ok"):
		frappe.throw(f"Charles could not record the canonical physical original: {recorded}")
	return recorded["intake_reference"]


def _submit(bid: str, *, signatory: str = MARY, certificate: dict[str, Any] = CERTIFICATE, at: str = CLOCK["submit"]) -> str:
	from kentender_procurement.bid_submission.services import availability, signature, simulation, submission
	from kentender_procurement.bid_submission.test_services import trust

	organisation = frappe.db.get_value("Bid Workspace", bid, "lead_organisation")
	with _at(at):
		if not frappe.db.exists(trust.CERTIFICATE, {"user": signatory, "organisation": organisation, "status": ("!=", "Revoked")}):
			trust.issue_certificate(user=signatory, organisation=organisation, **certificate)
		with availability.enabled_for_test_world():
			simulation.set_controls(accept_after_seconds=ACCEPT_AFTER_SECONDS, deposit_outcome="Accept")
			try:
				request = signature.prepare_bid_signature(bid_reference=bid, confirmed=True, expected_record_version=_version(bid), idempotency_key=_key("sign"), user=signatory)
				if not request.get("ok"):
					frappe.throw(f"{signatory} could not sign the canonical bid: {request}")
				signed = signature.sign_with_test_trust_service(signing_request=request["signing_request"], user=signatory)
				result = submission.submit_bid(bid_reference=bid, signature_ref=signed["signature"], confirmed=True, expected_record_version=_version(bid), idempotency_key=_key("submit"), user=signatory)
			finally:
				simulation.set_controls(accept_after_seconds=0)
	if not result.get("ok"):
		frappe.throw(f"The Test Tender Box did not accept the canonical bid: {result}")
	return result["receipt_reference"]


def ensure_bidder_accounts() -> None:
	"""The other bidders' supplier accounts, each through the real commands at
	its own instants (idempotent), and their people's shared fixture password
	under the same rule as Afya's."""
	for b in BIDDERS:
		bds_canonical._hook("kt_seed_supplier_account")(
			facts=b["facts"], registrant=b["signatory"], registrant_name=b["signatory_name"], representative=b["representative"],
			representative_name=b["representative_name"], representative_title=b["representative_title"], clock=b["clock"]["account"],
			namespace=NAMESPACE, key_prefix=f"seed-{b['key']}", profile=_profile(*b["profile"]),
		)
	if frappe.conf.get("developer_mode") or frappe.flags.get("kt_fixture_passwords"):
		from frappe.utils.password import update_password

		from kentender_core.seeds.constants import TEST_PASSWORD

		for email in BIDDER_PEOPLE:
			update_password(email, TEST_PASSWORD)


def _answers(bidder: dict[str, Any], bid: str, at: str) -> dict[str, dict[str, Any]]:
	return fixture_answers(bid, at=at, actor=bidder["representative"], goods=bidder["goods"], warranty=bidder["warranty"], price=bidder["price"],
		security=bidder["security"], overrides=bidder["overrides"], security_amount=bidder["security_amount"])


def _start_and_fill(bidder: dict[str, Any], *, tender: str, tender_reference: str) -> str:
	"""Start the bid on the current (post-addendum) definition, confirm the
	documents, and complete the company and requirements tasks."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import reads, save

	bds_canonical.seed_candidate(tender_reference=tender_reference, at=bidder["clock"]["start"], supplier={
		"facts": bidder["facts"], "registrant": bidder["signatory"], "registrant_name": bidder["signatory_name"], "representative": bidder["representative"],
		"representative_name": bidder["representative_name"], "namespace": NAMESPACE,
	})
	bid = bidder_bid(tender, bidder)
	person, at = bidder["representative"], bidder["clock"]["fill"]
	with _at(at):
		documents = reads.get_bid_task(bid_reference=bid, task="documents", user=person)
		ticks = {f["handle"]: True for g in documents["groups"] for f in g["fields"] if f["kind"] == "confirmation" and f["editable"] and f["visible"]}
		if ticks:
			saved = save.save_bid_task(bid_reference=bid, task="documents", values=ticks, expected_record_version=_version(bid), idempotency_key=_key(f"documents-{bidder['key']}"), user=person)
			if not saved.get("ok"):
				frappe.throw(f"{bidder['facts']['legal_name']} could not confirm the tender documents: {saved}")
		filling.fill_everything(bid, user=person, tasks=("company", "requirements"), answers=_answers(bidder, bid, at))
	return bid


def _complete_and_submit(bidder: dict[str, Any], *, tender: str, tender_reference: str) -> dict[str, str]:
	from kentender_procurement.bid_submission.seeds import filling

	bid, clock = bidder_bid(tender, bidder), bidder["clock"]
	intake = _record_original(tender_reference, bid, actor=bidder["representative"], at=clock["intake"])
	with _at(clock["complete"]):
		filling.fill_everything(bid, user=bidder["representative"], tasks=("price",), answers=_answers(bidder, bid, clock["complete"]))
	certificate = {**CERTIFICATE, "subject_name": bidder["signatory_name"]}
	return {"bid": bid, "intake": intake, "receipt": _submit(bid, signatory=bidder["signatory"], certificate=certificate, at=clock["submit"])}


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
		# in time order: the other bidders start (2–7 Jun), Afya completes and
		# submits (10 Jun), then the others complete and submit (11–12 Jun)
		ensure_bidder_accounts()
		others = [_start_and_fill(b, tender=tender, tender_reference=tender_reference) for b in BIDDERS]
		bid = canonical_bid(tender)
		intake = _record_original(tender_reference, bid)
		_fill(bid, ("price",), CLOCK["complete"])
		out = {"intake": intake, "receipt": _submit(bid), "others": others}
		out["submitted"] = [_complete_and_submit(b, tender=tender, tender_reference=tender_reference) for b in BIDDERS]
		return out
	if step == "closed":
		return _close(tender)
	return None


#: Afya Digital Supplies Limited in the shape `BIDDERS` uses (its account is the
#: canonical one Supplier Accounts seeds; `facts` is unused for it).
AFYA_BIDDER: dict[str, Any] = {
	"key": "afya", "facts": None, "signatory": MARY, "signatory_name": "Mary Wanjiku", "representative": DAVID, "representative_name": "David Ouma",
	"warranty": WARRANTY, "security": SECURITY, "overrides": {}, "security_amount": "",
}


def portfolio_bidder(key: str) -> dict[str, Any]:
	return AFYA_BIDDER if key == "afya" else next(b for b in BIDDERS if b["key"] == key)


def portfolio_bid(
	*, tender: str, tender_reference: str, bidder_key: str, clock_map: dict[str, str], goods: dict[str, Any], price: dict[str, Any], submit: bool = True,
	security: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""One bid on an executed-portfolio Tender (two-year seed world proposal
	§5.1), through the same commands as the canonical bids, as the company's
	own people at the story's instants: Start bid (`clock_map["start"]`), the
	documents, company and requirements tasks (`fill`), and — `submit` — the
	physical security original recorded by Charles Mutiso (`intake`), the price
	(`complete`) and the signed submission (`submit`). Without `submit` the bid
	stays a Draft (a registered candidate). Idempotent per step: a submitted
	bid is returned untouched."""
	from kentender_procurement.bid_submission.seeds import filling
	from kentender_procurement.bid_submission.services import reads, save

	_guard()
	bidder = {**portfolio_bidder(bidder_key), "goods": goods, "price": price}
	if security:
		bidder["security"] = {**bidder["security"], **security}
	afya = bidder_key == "afya"
	ensure_bidder_accounts()
	existing = canonical_bid(tender) if afya else bidder_bid(tender, bidder)
	if existing and frappe.db.exists("Bid Receipt", {"bid_workspace": existing}):
		return {"ok": True, "idempotent": True, "bid": existing}
	arrangement = bds_canonical.seed_candidate(tender_reference=tender_reference, at=clock_map["start"], supplier=None if afya else {
		"facts": bidder["facts"], "registrant": bidder["signatory"], "registrant_name": bidder["signatory_name"], "representative": bidder["representative"],
		"representative_name": bidder["representative_name"], "namespace": NAMESPACE,
	})
	bid = canonical_bid(tender) if afya else bidder_bid(tender, bidder)
	person = bidder["representative"]
	with _at(clock_map["fill"]):
		documents = reads.get_bid_task(bid_reference=bid, task="documents", user=person)
		ticks = {f["handle"]: True for g in documents["groups"] for f in g["fields"] if f["kind"] == "confirmation" and f["editable"] and f["visible"]}
		if ticks:
			saved = save.save_bid_task(bid_reference=bid, task="documents", values=ticks, expected_record_version=_version(bid), idempotency_key=_key(f"documents-{bidder_key}"), user=person)
			if not saved.get("ok"):
				frappe.throw(f"{bidder_key} could not confirm the tender documents of {tender_reference}: {saved}")
		filling.fill_everything(bid, user=person, tasks=("company", "requirements"), answers=_answers(bidder, bid, clock_map["fill"]))
	out: dict[str, Any] = {"ok": True, "idempotent": False, "bid": bid, "candidate": arrangement}
	if not submit:
		return out
	out["intake"] = _record_original(tender_reference, bid, actor=person, at=clock_map["intake"])
	with _at(clock_map["complete"]):
		filling.fill_everything(bid, user=person, tasks=("price",), answers=_answers(bidder, bid, clock_map["complete"]))
	out["receipt"] = _submit(bid, signatory=bidder["signatory"], certificate={**CERTIFICATE, "subject_name": bidder["signatory_name"]}, at=clock_map["submit"])
	return out


def close_portfolio_box(tender: str, at: str) -> dict[str, Any]:
	"""Bid Submission's close of a portfolio Tender's box, after Tenders ends
	its submission period (the scheduler consumer's work)."""
	if frappe.db.exists("Bid Submission Close", {"tender": tender}):
		return {"ok": True, "idempotent": True}
	return _close(tender, at=at)


def bids_submitted(tender: str) -> bool:
	bids = [canonical_bid(tender)] + [bidder_bid(tender, b) for b in BIDDERS] if tender else []
	return bool(bids) and all(bid and frappe.db.exists("Bid Receipt", {"bid_workspace": bid}) for bid in bids)


def lifecycle_complete(tender: str) -> bool:
	"""Every canonical bid submitted, and the box closed at the deadline."""
	if not bids_submitted(tender):
		return False
	return bool(frappe.db.exists("Bid Submission Close", {"tender": tender}))


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
	ensure_bidder_accounts()
	prerequisites = tenders_seed.verify_prerequisites()
	tender = cstr(frappe.db.get_value("Tender", {"requisition": prerequisites["requisition"]}, "name"))
	if tender and lifecycle_complete(tender):
		result = {"ok": True, "idempotent": True, "tender": tender, "bid": canonical_bid(tender)}
	elif tender:
		frappe.throw(
			f"The canonical Tender {tender} was seeded without the bid lifecycle. Rebuild the canonical world through this stage: "
			"make seed-canonical CURRENT=bid_submission REBUILD=True.",
			exc=CanonicalTenderIncomplete,
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
	for b in BIDDERS:
		name = b["facts"]["legal_name"]
		other = bidder_bid(tender, b)
		check(bool(other), f"{name} has a bid on the canonical Tender")
		if not other:
			continue
		ws_other = frappe.db.get_value("Bid Workspace", other, ["status", "current_submission_version"], as_dict=True)
		check(ws_other.status == "Submitted", f"{name}'s bid is Submitted (got {ws_other.status!r})")
		rec = frappe.db.get_value("Bid Receipt", {"bid_workspace": other}, ["received_at", "submitted_by"], as_dict=True)
		check(bool(rec) and cstr(rec.received_at) == b["clock"]["submit"] and rec.submitted_by == b["signatory"],
			f"{b['signatory_name']} submitted it at {b['clock']['submit']}")
		match = frappe.db.get_value("Tender Security Intake", {"recorded_by": CHARLES, "received_at": b["clock"]["intake"]}, "name")
		check(bool(match) and bool(frappe.db.exists("Tender Security Intake Match", {"intake": match, "bid_workspace": other})),
			f"Charles's physical original for {name} privately matches its bid")
	close = frappe.db.get_value("Bid Submission Close", {"tender": tender}, ["name", "bid_opening_handoff", "envelopes_sealed"], as_dict=True)
	check(bool(close), "Bid Submission closed at the deadline")
	check(bool(close) and int(close.envelopes_sealed or 0) == 1 + len(BIDDERS), f"{1 + len(BIDDERS)} sealed envelopes were handed over")
	check(bool(close) and bool(close.bid_opening_handoff), "a Bid Opening hand-off was written")
	rerun = upsert_bid_submission_base(commit=False)
	check(rerun.get("idempotent") is True and rerun.get("bid") == bid, "a second run is idempotent")
	return rows
