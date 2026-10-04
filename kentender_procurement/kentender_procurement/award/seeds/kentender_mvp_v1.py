# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical `award` stage (AWD-CHG-001 v0.4 §13; plan Phase 11; tracker
AWD4-1101).

The §13 ordinary path on the canonical Tender (TND-MOH-2027-002; four bids
since 3 Oct 2026, so Jirani, Pwani and Mlima receive unsuccessful notices in
the same batch), told with
the same commands as production on the real Evaluation delivery of 16 Jun
2027 14:07:01 — no direct lifecycle writes: receipt; Charles Mutiso signs
Professional opinion 1 at 17 Jun 09:10; Amina Hassan records Award and
notifies bidders at 10:00; Mary Wanjiku accepts at 18 Jun 09:00; the test
profile's waiting period ends and the package reaches the test Contracting
receiver at 2 Jul 09:00. Synthetic Trust, delivery and Contracting adapters
only (test environment). A complete canonical award is returned untouched;
a partial one is removed and told again. `through` stops the story at a
named step (the demo profiles)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.seeds import clear
from kentender_procurement.award.services import decision, eligibility, intake, opinion, profile, records, simulation, sources, state, supplier

HOP = "charles.mutiso@moh.example.test"
AO = "amina.hassan@moh.example.test"
MARY = "mary.wanjiku@afyadigital.example"
DANIEL = "daniel.otieno@moh.example.test"
D02R = ("The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the "
	"proposed award.")
DECR = "I accept the recommendation in the signed evaluation report and professional opinion."
#: The unsuccessful bidders and the reason each letter gives (the evaluation's ranking).
UNSUCCESSFUL = {
	"Jirani Office Supplies Limited": "Your tender met the requirements. Another responsive tender had a lower evaluated price.",
	"Pwani Tech Distributors Limited": "Your tender did not meet the published requirements recorded in the signed evaluation report.",
	"Mlima Computer Solutions Limited": "Your tender did not meet the published requirements recorded in the signed evaluation report.",
}
STEPS = ("received", "signed", "notified", "accepted", "delivered")
CLOCK = {"opinion": "2027-06-17 09:00:00", "sign": "2027-06-17 09:10:00", "decide": "2027-06-17 10:00:00", "accept": "2027-06-18 09:00:00",
	"deliver": "2027-07-02 09:00:00"}


def _guard() -> None:
	if not simulation.enabled():
		frappe.throw("The canonical award uses the simulation adapters and is seeded on a test environment only.")


def _key(step: str) -> str:
	return f"canonical-award:{step}:{frappe.generate_hash(length=6)}"


def canonical_tender() -> str:
	from kentender_procurement.bid_evaluation.seeds.kentender_mvp_v1 import canonical_tender as evl_tender

	return evl_tender()


def _delivery(tender: str) -> str | None:
	case = frappe.db.get_value("Evaluation Case", {"tender": tender, "state": "Report sent"}, "name")
	return frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": case, "status": "Delivered"}, "name", order_by="delivered_at desc") if case else None


def _ok(result: dict[str, Any], what: str) -> dict[str, Any]:
	if not result or result.get("ok") is False:
		frappe.throw(f"Canonical award: {what} failed: {result}")
	return result


def _as(user: str, fn, **kwargs) -> dict[str, Any]:
	frappe.set_user(user)
	try:
		return fn(user=user, idempotency_key=_key(fn.__name__), **kwargs)
	finally:
		frappe.set_user("Administrator")


def _version(award: str) -> int:
	return int(frappe.db.get_value(records.CASE, award, "record_version"))


def tell(tender: str, through: str = STEPS[-1]) -> str:
	"""The §13 story up to `through`; returns the award id."""
	upto = STEPS.index(through)
	delivery = _delivery(tender)
	if not delivery:
		frappe.throw("The canonical evaluation report has not been delivered. Seed through the bid_evaluation stage first.")
	frappe.db.set_value("Evaluation Report Delivery", delivery, "review_state", "Open", update_modified=False)
	frappe.flags.kt_awd_clock = str(frappe.db.get_value("Evaluation Report Delivery", delivery, "delivered_at"))
	award = _ok(intake.receive(delivery=delivery, source_kind=sources.EVALUATION), "receipt")["award"]
	if upto >= STEPS.index("signed"):
		frappe.flags.kt_awd_clock = CLOCK["opinion"]
		_ok(_as(HOP, opinion.save, award=award, conclusion="Recommend award", reason=D02R, expected_version=_version(award)), "save opinion")
		frappe.flags.kt_awd_clock = CLOCK["sign"]
		_ok(_as(HOP, opinion.sign, award=award, expected_version=_version(award)), "sign opinion")
	if upto >= STEPS.index("notified"):
		frappe.flags.kt_awd_clock = CLOCK["decide"]
		_ok(_as(AO, decision.record, award=award, outcome="Award", reason=DECR, expected_version=_version(award)), "award and notify bidders")
	if upto >= STEPS.index("accepted"):
		frappe.flags.kt_awd_clock = CLOCK["accept"]
		notice = state.successful_notice(state.current_batch(frappe.get_doc(records.CASE, award)))
		_ok(_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=notice.version), "accept")
	if upto >= STEPS.index("delivered"):
		frappe.flags.kt_awd_clock = CLOCK["deliver"]
		eligibility.refresh_case(award)
	return award


def lifecycle_complete(tender: str) -> bool:
	return frappe.db.get_value(records.CASE, {"tender": tender}, "stage") == "Sent to Contracting" and all(r["ok"] for r in validate_award_seed())


def reset(tender: str) -> None:
	clear.wipe(tenders=[tender])
	simulation.reset_controls()


def upsert_award_base(*, commit: bool = False, through: str = STEPS[-1]) -> dict[str, Any]:
	"""The `award` stage. A complete canonical award is returned untouched."""
	_guard()
	tender = canonical_tender()
	if not tender or not _delivery(tender):
		frappe.throw("The canonical evaluation report has not been delivered. Seed through the bid_evaluation stage first.")
	if through == STEPS[-1] and lifecycle_complete(tender):
		result = {"ok": True, "idempotent": True, "award": frappe.db.get_value(records.CASE, {"tender": tender}, "name")}
	else:
		reset(tender)
		profile.install_test_profile(contracting_owner=HOP, technical_operator=DANIEL)
		saved = frappe.flags.get("kt_awd_clock")
		try:
			award = tell(tender, through)
		finally:
			frappe.flags.kt_awd_clock = saved
		result = {"ok": True, "idempotent": False, "award": award, "through": through}
	if commit:
		frappe.db.commit()
	return result


def validate_award_seed() -> list[dict[str, Any]]:
	"""One row per §13 fact the canonical award must carry. Never mutates."""
	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label})

	tender = canonical_tender()
	name = frappe.db.get_value(records.CASE, {"tender": tender}, "name") if tender else None
	check(bool(name), "the canonical Tender has its award")
	if not name:
		return rows
	doc = frappe.get_doc(records.CASE, name)
	rep = state.current_report(doc)
	snap = state.snapshot(rep)
	check(doc.source_kind == "Evaluation" and rep.version_number == 1 and snap.get("digest_verified"), "Evaluation report 1 was received and verified")
	check(len([r for r in frappe.get_all(state.REPORT, filters={"award_case": name}, pluck="name")]) == 1, "one report, one case")
	signed = state.signed_opinion(doc)
	check(bool(signed) and signed.author == HOP and cstr(signed.signed_at) == CLOCK["sign"], "Charles Mutiso signed Professional opinion 1 at 17 Jun 2027, 09:10 EAT")
	d = state.committed_decision(doc)
	check(bool(d) and (d.outcome, d.decided_by, cstr(d.decided_at), d.supplier_name, d.submitted_amount) ==
		("Award", AO, CLOCK["decide"], "Afya Digital Supplies Limited", "46400000.00"), "Amina Hassan awarded Afya Digital Supplies Limited KES 46,400,000 at 10:00")
	batch = state.current_batch(doc)
	notices = state.notices(batch)
	successful = state.successful_notice(batch)
	check(bool(successful) and successful.organisation_name == "Afya Digital Supplies Limited" and successful.status == "Given"
		and cstr(successful.reply_deadline) == "2027-06-24 17:00:00", "Afya's successful notice was given, reply by 24 Jun 2027, 17:00 EAT")
	# the other three bidders are told too, each with its own reason
	unsuccessful = {n.organisation_name: n for n in notices if n.result == "Unsuccessful"}
	check(len(notices) == 1 + len(UNSUCCESSFUL) and set(unsuccessful) == set(UNSUCCESSFUL), f"{1 + len(UNSUCCESSFUL)} notices: one successful, {len(UNSUCCESSFUL)} unsuccessful")
	for name, reason in UNSUCCESSFUL.items():
		n = unsuccessful.get(name)
		content = frappe.parse_json(n.content_json) if n and n.content_json else {}
		check(bool(n) and n.status == "Given" and content.get("reason") == reason, f"{name} was told it was unsuccessful: {reason}")
	response = state.operative_response(successful) if successful else None
	check(bool(response) and (response.response, response.responder, cstr(response.received_at)) == ("Accept", MARY, CLOCK["accept"]),
		"Mary Wanjiku accepted at 18 Jun 2027, 09:00 EAT")
	pkg = eligibility.current_package(doc)
	check(bool(pkg) and pkg.status == "Delivered" and cstr(pkg.received_at) == CLOCK["deliver"] and pkg.recipient_user == HOP,
		"Contracting received the award at 2 Jul 2027, 09:00 EAT (Prepare contract: Charles Mutiso)")
	check(frappe.db.get_value(state.EVENT, {"decision": d.name if d else ""}, "status") == "Delivered", "the award decision event reached Contracting")
	check(doc.stage == "Sent to Contracting", f"the award is Sent to Contracting (got {doc.stage!r})")
	return rows
