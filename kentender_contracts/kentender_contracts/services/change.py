# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Changes and amendments (CM-CHG-001 v0.8 sections 5.7, 5.11, 5.14, 5.18, 7, 19.3 rules CM-R-10 and CM-R-11; plan Phase 8; boards D27, D14, D34).

A change is a request to move a term of an agreement in force: an **extension** of the delivery date, or an **increase of a goods quantity at the issued rate**. There is no price editor: the rate is the
agreement's, and a figure no officer can edit is the only one the ceilings are calculated from. The original contract stays operative for as long as a request is pending; **only the effective successor
changes anything**.

The route is the specification's: the contract's owner or the supplier requests with grounds and evidence -> the head of procurement names the reviewers (by the Accounting Officer's appointment reference, never
the Evaluation committee that may no longer exist) -> each reviewer declares no conflict, records the recommendation and signs it -> the head of procurement submits the reviewed change -> the Accounting Officer
decides (approve, decline or return, with a reason; never a person who requested, reviewed or recommended it) -> an approval **generates an amendment**, a successor agreement version whose terms are the operative
terms with the change applied -> the supplier signs it first and the entity second -> the second proof makes it effective. An effective amendment then reaches the native purchase order and, for an increase, the
funding owner as durable operations (`intents.py`; matrix row R17-07): until they reconcile, new spending and payment on the contract are held and the screen says the update is pending. Nothing here writes
a ledger.

The ceilings (15% of an original goods quantity, 25% cumulative value) and the twelve-month bar are parameters of the verified rule profile (`rules/profile.py`), never constants; a total increase early in the
contract is the LQ-02 branch, held in production until the reviewer answers and illustrated only by the synthetic profile."""

from __future__ import annotations

import copy
from typing import Any

import frappe
from frappe.utils import add_months, cint, cstr, flt, getdate

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, clock, events, formation, intents, obligations, parties, people, picker_sources, preflight, records, segregation, service_principal, signing_flow, work
from kentender_contracts.services.errors import Guards, fail, invalid
from kentender_core.services import contract_funding_contract as funding_seam

CHANGE = "Contract Change"
CASE = "Contract Case"
AGREEMENT = "Contract Agreement Version"
SIGNATURE = "Contract Signature"
KINDS = ("Extension", "Quantity")
#: The review each kind needs before it can be submitted (section 5.11 and the D27 / D34 briefs).
REVIEW_KINDS: dict[str, tuple[str, ...]] = {
	"Extension": ("Technical review", "Committee recommendation", "Legal review"),
	"Quantity": ("Technical review", "Source and legal basis", "Funding confirmation"),
}
OPEN = ("Requested", "Reviewed", "Submitted", "Approved", "Returned")
#: The commands whose task opens a change screen, and the review parts by their form names.
COMMANDS = ("RequestContractChange", "AppointContractChangeReviewers", "RecordContractChangeReview", "SignContractChangeReview", "SubmitContractChangeForDecision", "DecideContractChange", "ActivateContractChange")
KIND_OF_SLUG = {kind.lower().replace(" ", "-"): kind for kinds in REVIEW_KINDS.values() for kind in kinds}
REVIEWER = picker_sources.REVIEWER
DECISIONS = {"Approve": "Approved", "Decline": "Declined", "Return": "Returned"}
NO_CONFLICT = "No conflict"
FUNDING_EVENT = "ContractVariationEffective"


# -- reading --------------------------------------------------------------------------------------------------------------------------
def get(case: str, number: int):
	name = frappe.db.get_value(CHANGE, {"contract_case": case, "change_no": number}, "name")
	return frappe.get_doc(CHANGE, name) if name else None


def open_change(case: str):
	"""The change in progress, if any: one at a time, so every figure is compared with the same operative terms."""
	name = frappe.db.get_value(CHANGE, {"contract_case": case, "state": ["in", list(OPEN)]}, "name", order_by="change_no desc")
	return frappe.get_doc(CHANGE, name) if name else None


def slots(row, *, live: bool = True) -> list[dict[str, Any]]:
	found = records.loads(row.reviews_json, [])
	return [s for s in found if s["state"] != "Superseded"] if live else found


def proposal(row) -> dict[str, Any]:
	return records.loads(row.proposal_json)


def amendment_of(row):
	return frappe.get_doc(AGREEMENT, frappe.db.get_value(AGREEMENT, {"contract_case": row.contract_case, "change": row.name}, "name")) if row.amendment_version else None


def subject_of(row) -> str:
	return f"change {row.change_no}"


def amendment_subject(row) -> str:
	return f"amendment {row.change_no}"


def draft_of(row) -> int:
	return cint(proposal(row).get("draft") or 1)


def _slug(kind: str) -> str:
	return kind.lower().replace(" ", "-")


def original_terms(case: str) -> dict[str, Any]:
	"""The agreement as first made effective: the baseline every ceiling is measured from."""
	agreement = formation.current_agreement(case, "Effective")
	return records.loads(agreement.terms_json) if agreement else {}


def operative_terms(case: str) -> dict[str, Any]:
	"""The terms in force now: the latest effective version, an amendment once it has taken effect."""
	found = frappe.db.get_value(AGREEMENT, {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc")
	return records.loads(found) if found else {}


def effective_changes(case: str) -> list[Any]:
	return [frappe.get_doc(CHANGE, n) for n in frappe.get_all(CHANGE, filters={"contract_case": case, "state": "Effective"}, pluck="name", order_by="change_no asc")]


def can_request(case: str, user: str) -> bool:
	"""May this person start a change: the contract's owner or a preparer, or a representative of the supplier."""
	try:
		_may_request(case, user)
		return True
	except Exception:  # noqa: BLE001 - a refusal means no
		return False


def effects(case: str, row) -> dict[str, str]:
	"""Where the operations an effective amendment started stand: kind -> the intent's state."""
	return {i.operation_kind: i.state for i in frappe.get_all(intents.INTENT, filters={"contract_case": case, "subject": amendment_subject(row)}, fields=["operation_kind", "state"])}


def latest_pending(case: str):
	"""The latest effective amendment whose order or funding update has not completed: new spending that depends on it waits."""
	pending = [row for row in effective_changes(case) if any(state not in intents.SETTLED for state in effects(case, row).values())]
	return pending[-1] if pending else None


def held_question(case: str, row) -> bool:
	"""Whether submitting this change is held for a legal question the profile has not answered (an early total increase: LQ-02)."""
	if row.kind != "Quantity":
		return False
	measured = assess(case, "Quantity", {"quantities": proposal(row)["quantities"]})
	guards = preflight.rules(frappe.get_doc(CASE, case), "SubmitContractChangeForDecision", _branches(measured))
	return any(r["code"] == "CM_HOLD" and r["detail"].get("question") == "LQ-02" for r in guards.reasons)


# -- the figures a change is judged on -------------------------------------------------------------------------------------------------
def assess(case: str, kind: str, request: dict[str, Any]) -> dict[str, Any]:
	"""What the request would do, calculated from the operative terms and the original baseline. Nothing here is typed by a person except the proposed date or quantity.

	`problems` are form values to correct; `blocked` are limits the request exceeds (a hold with a named holder, not a field to retype)."""
	doc = frappe.get_doc(CASE, case)
	profile = preflight.profile(doc)
	operative, original = operative_terms(case), original_terms(case)
	out: dict[str, Any] = {"kind": kind, "problems": {}, "blocked": [], "early_total_increase": False, "delta": 0.0, "currency": operative.get("currency", "KES")}
	if kind == "Extension":
		current = operative["delivery"]["due"]
		out.update(current_due=current, original_due=operative["delivery"].get("original_due") or current)
		try:
			proposed = getdate(request.get("proposed_date"))
		except Exception:  # noqa: BLE001 - not a date
			proposed = None
		if not proposed:
			out["problems"]["proposed_date"] = "Enter the proposed delivery date."
		elif proposed <= getdate(current):
			out["problems"]["proposed_date"] = "Enter a date after the current delivery date."
		else:
			out.update(proposed_due=str(proposed), days=(proposed - getdate(current)).days)
		out["total"] = operative["total"]
		return out
	# a quantity change: goods lines only, increases only, at the issued rate
	ceiling = profile.parameter("goods_quantity_increase_ceiling_percent").value
	value_ceiling = profile.parameter("cumulative_goods_value_increase_ceiling_percent").value
	bar = profile.parameter("upward_price_variation_bar_months").value
	quantities = request.get("quantities") or {}
	by_id = {l["line_id"]: l for l in operative["lines"]}
	first = {l["line_id"]: l for l in original["lines"]}
	lines, delta = [], 0.0
	if not quantities:
		out["problems"]["quantities"] = "Enter the proposed quantity."
	for line_id, wanted in quantities.items():
		line = by_id.get(line_id)
		if line is None or line.get("kind") == "service":
			out["problems"][f"quantity.{line_id}"] = "Only a goods line can change its quantity here."
			continue
		try:
			proposed = cint(wanted) if str(wanted).strip().lstrip("-").isdigit() else None
		except Exception:  # noqa: BLE001
			proposed = None
		if proposed is None or proposed <= cint(line["quantity"]):
			out["problems"][f"quantity.{line_id}"] = f"Enter a quantity above the current {cint(line['quantity'])}."
			continue
		base = cint(first[line_id]["quantity"])
		percent = round((proposed - base) * 100.0 / base, 2) if base else 0.0
		added = (proposed - cint(line["quantity"])) * flt(line["rate"])
		delta += added
		lines.append({"line_id": line_id, "item": line.get("description") or line.get("item"), "original": base, "current": cint(line["quantity"]), "proposed": proposed, "rate": flt(line["rate"]),
			"percent_of_original": percent, "ceiling_percent": ceiling, "over": percent > ceiling})
	original_total = flt(original["total"])
	proposed_total = flt(operative["total"]) + delta
	cumulative = round((proposed_total - original_total) * 100.0 / original_total, 2) if original_total else 0.0
	signed = frappe.db.get_value(AGREEMENT, {"contract_case": case, "state": "Effective", "change": ["is", "not set"]}, "effective_at")
	out.update(lines=lines, current_total=flt(operative["total"]), proposed_total=proposed_total, delta=delta, cumulative_value_percent=cumulative, value_ceiling_percent=value_ceiling, ceiling_percent=ceiling, total=proposed_total)
	for line in lines:
		if line["over"]:
			out["blocked"].append({"line": line["line_id"], "reason": f"Proposed quantity {line['proposed']} is {line['percent_of_original']:g}% above the original {line['original']}; the applicable limit is {ceiling:g}%."})
	if cumulative > value_ceiling:
		out["blocked"].append({"line": "", "reason": f"The cumulative value increase would be {cumulative:g}%; the applicable limit is {value_ceiling:g}%."})
	if delta > 0 and signed and getdate(clock.now()) < add_months(getdate(signed), cint(bar)):
		out["early_total_increase"] = True  # LQ-02: held in production until the reviewer answers
	return out


def _funding_split(case: str, delta: float, given: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
	"""How the additional amount is funded: the one reservation behind the contract by default, otherwise exactly as the request names it. Never an arbitrary allocation by the officer."""
	allocations = operative_terms(case).get("funding", {}).get("allocations", [])
	reservations = [a["reservation"] for a in allocations]
	if not given:
		if len(reservations) == 1:
			return [{"reservation": reservations[0], "additional": round(delta, 2)}]
		invalid({"funding": "Name how each source funds the additional amount."})
	clean = [{"reservation": cstr(g.get("reservation")), "additional": round(flt(g.get("additional")), 2)} for g in given]
	problems = "" if clean and all(c["reservation"] in reservations and c["additional"] > 0 for c in clean) else "Each source named must already fund this contract, with an amount above zero."
	if not problems and abs(sum(c["additional"] for c in clean) - delta) > 0.005:
		problems = f"The sources must fund exactly the additional {delta:,.2f}."
	invalid({"funding": problems})
	return clean


# -- the request ----------------------------------------------------------------------------------------------------------------------
def _may_request(case: str, actor: str) -> None:
	"""The contract's owner or a person who prepares contracts for its unit, or a representative of the supplier."""
	from kentender_contracts.services import issues, payment

	try:
		payment._claim_authority(case, actor)
	except Exception:  # noqa: BLE001 - not the supplier: the owner's side may request
		issues._may_manage(case, actor)


def _hop_task(case: str, command: str, title: str, subject: str, version: int) -> None:
	work.assign(case, command, title, subject, version, work.holders(work.HOP), role=work.HOP)


def request_change(case: str, *, kind: str, request: dict[str, Any], reason: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str, correcting: int = 0,
		funding: list[dict[str, Any]] | None = None) -> dict[str, Any]:
	"""`RequestContractChange`: grounds, impact and evidence. Records the request against the operative terms and asks the head of procurement to name the reviewers. A request that exceeds a limit is not
	recorded as approvable: it is refused with the limit and its holder. `correcting` is the number of a change returned for correction, which is revised in place with its history kept."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		invalid({"kind": "" if kind in KINDS else "Choose the kind of change.", "reason": "" if cstr(reason).strip() else "Explain why the change is needed.",
			"evidence": "" if evidence and all(cstr(e.get("label")).strip() for e in evidence) else "Attach the request that supports it."})
		if "rate" in request or "price" in request or "amount" in request:
			invalid({"rate": "The rate is fixed by the contract; a change moves a quantity or a date."})
		running = open_change(case)
		returned = get(case, correcting) if correcting else None
		if returned is not None and returned.state != "Returned":
			fail("CM_CHANGED", change=returned.name, state=returned.state)
		if running is not None and (returned is None or running.name != returned.name):
			fail("CM_CHANGED", reason="Another change to this contract is in progress. It is decided before another is requested.", change=running.name)
		measured = assess(case, kind, request)
		invalid(measured["problems"])
		guards = Guards()
		for limit in measured["blocked"]:
			guards.add("CM_HOLD", hold="CHANGE_LIMIT_EXCEEDED", kind="Rule limit", reason=limit["reason"], holder="Head of procurement function", clears_with="A request within the applicable limit; a change above a limit is not approved through this form", consequence="RequestContractChange")
		guards.raise_if_any()
		stored = {"kind": kind, **({"proposed_date": measured["proposed_due"]} if kind == "Extension" else {"quantities": {l["line_id"]: l["proposed"] for l in measured["lines"]}, "funding": _funding_split(case, measured["delta"], funding) if measured["delta"] > 0 else []})}
		if returned is None:
			number = records.next_number(CHANGE, {"contract_case": case}, "change_no")
			row = records.new(CHANGE, contract_case=case, change_no=number, kind=kind, state="Requested", baseline_json=records.dumps(_baseline(case)), proposal_json=records.dumps({**stored, "draft": 1}), reason=cstr(reason).strip(),
				evidence_json=records.dumps(evidence), reviews_json=records.dumps([]), decision_json=records.dumps({}), rule_json=records.dumps(_rule_note(measured)), requested_by=actor, requested_at=clock.now(), record_version=1)
		else:
			row = returned
			slots_now = [{**s, "state": "Superseded"} for s in records.loads(row.reviews_json, [])]
			records.update(row, state="Requested", kind=kind, baseline_json=records.dumps(_baseline(case)), proposal_json=records.dumps({**stored, "draft": draft_of(row) + 1}), reason=cstr(reason).strip(), evidence_json=records.dumps(evidence),
				reviews_json=records.dumps(slots_now), rule_json=records.dumps(_rule_note(measured)), record_version=cint(row.record_version) + 1)
			work.finish(case, command="RequestContractChange", subject=subject_of(row), actor=actor)
		_hop_task(case, "AppointContractChangeReviewers", "Name the reviewers for the requested change.", subject_of(row), draft_of(row))
		events.record(case, "Change requested", actor, f"{kind} change {row.change_no} requested.", change=row.name, **{k: v for k, v in stored.items() if k != "funding"})
		records.bump(doc)
		return records.summary(doc, change=row.name, change_no=row.change_no)

	return records.command("RequestContractChange", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "kind": kind, "request": request, "reason": reason, "evidence": evidence,
		"correcting": correcting, "funding": funding or []}, body=body, authorise=lambda: _may_request(case, actor))


def _baseline(case: str) -> dict[str, Any]:
	terms = operative_terms(case)
	return {"due": terms["delivery"]["due"], "total": terms["total"], "lines": {l["line_id"]: cint(l["quantity"]) for l in terms["lines"]}, "version": frappe.db.get_value(AGREEMENT, {"contract_case": case, "state": "Effective"}, "version_no", order_by="version_no desc")}


def _rule_note(measured: dict[str, Any]) -> dict[str, Any]:
	return {k: measured.get(k) for k in ("current_due", "proposed_due", "days", "lines", "current_total", "proposed_total", "delta", "cumulative_value_percent", "value_ceiling_percent", "early_total_increase")}


# -- the reviewers ----------------------------------------------------------------------------------------------------------------------
def appoint_reviewers(case: str, *, change: int, reference: str, reviewers: dict[str, str], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`AppointContractChangeReviewers`: the head of procurement names who reviews each part, with the Accounting Officer's appointment reference. The requester cannot review their own request."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state != "Requested":
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		held = {s["kind"]: s for s in slots(row) if s["state"] != "Conflicted"}  # a reviewer who declared a conflict is replaced; the others stand
		needed = [k for k in REVIEW_KINDS[row.kind] if k not in held]
		problems = {f"reviewers.{k}": "Choose a person with an account." for k in needed if not frappe.db.exists("User", cstr(reviewers.get(k)))}
		problems.update({f"reviewers.{k}": "Choose a person who holds a contract responsibility." for k in needed if k not in problems and not picker_sources.eligible_reviewer(reviewers[k])})
		invalid({"reference": "" if cstr(reference).strip() else "Enter the appointment reference.", **problems})
		for kind in needed:
			if reviewers[kind].lower() == cstr(row.requested_by).lower():
				invalid({f"reviewers.{kind}": "The person who requested the change cannot review it."})
		entries = [{"kind": k, "reviewer": reviewers[k], "state": "Appointed", "declaration": "", "recommendation": "", "reference": "", "proof": "", "signed_at": ""} for k in needed]
		kept = [{**s, "state": "Superseded"} if s["state"] == "Conflicted" else s for s in records.loads(row.reviews_json, [])]
		body_ = proposal(row)
		body_["appointment"] = {"reference": cstr(reference).strip(), "by": actor, "at": str(clock.now())}
		records.update(row, reviews_json=records.dumps(kept + entries), proposal_json=records.dumps(body_), record_version=cint(row.record_version) + 1)
		work.finish(case, command="AppointContractChangeReviewers", subject=subject_of(row), actor=actor)
		for entry in entries:
			work.assign(case, "RecordContractChangeReview", f"Record your {entry['kind'].lower()} of the requested change.", f"{subject_of(row)} review {_slug(entry['kind'])}", draft_of(row), [entry["reviewer"]], role="Change reviewer")
		events.record(case, "Reviewers named", actor, f"Reviewers named for change {row.change_no} (appointment {cstr(reference).strip()}).", change=row.name, reference=cstr(reference).strip())
		records.bump(doc)
		return records.summary(doc, change=row.name, reviewers=len(entries))

	return records.command("AppointContractChangeReviewers", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change, "reference": reference, "reviewers": reviewers}, body=body,
		authorise=authorise)


def _slot_of(row, kind: str, actor: str) -> dict[str, Any]:
	slot = next((s for s in slots(row) if s["kind"] == kind), None)
	if slot is None or slot["reviewer"].lower() != actor.lower():
		fail("CM_AUTHORITY", missing="appointment", reason="You are not the appointed reviewer of this part.", provisioned_by="Head of procurement function recommends; Accounting Officer appoints")
	return slot


def record_review(case: str, *, change: int, kind: str, recommendation: str, declaration: str, reference: str = "", expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordContractChangeReview`: the appointed reviewer declares whether they have a conflict and records the recommendation (and, for the funding confirmation, its reference). Signing is the next step."""
	preflight.exists(case)

	def authorise() -> None:
		row = get(case, change)
		if row is None:
			raise frappe.DoesNotExistError("Not found")
		_slot_of(row, kind, actor)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row.state != "Requested":
			fail("CM_CHANGED", change=row.name, state=row.state)
		invalid({"declaration": "" if declaration in (NO_CONFLICT, "Conflict") else "Declare whether you have a conflict.", "recommendation": "" if cstr(recommendation).strip() else "Record your recommendation.",
			"reference": "" if kind != "Funding confirmation" or cstr(reference).strip() else "Enter the funding confirmation reference."})
		segregation.change_roles_separate(actor, action="recommend", requesters=[row.requested_by], recommenders=[], reviewers=[])
		found = records.loads(row.reviews_json, [])
		live = next(s for s in found if s["kind"] == kind and s["state"] != "Superseded")
		if live["state"] == "Signed":
			fail("CM_CHANGED", reason="This review is signed.")
		if declaration == "Conflict":
			live.update(state="Conflicted", declaration="Conflict")
			records.update(row, reviews_json=records.dumps(found), record_version=cint(row.record_version) + 1)
			work.finish(case, command="RecordContractChangeReview", subject=f"{subject_of(row)} review {_slug(kind)}", actor=actor)
			_hop_task(case, "AppointContractChangeReviewers", f"Name another reviewer for the {kind.lower()}.", subject_of(row), draft_of(row))
			events.record(case, "Reviewer conflict", actor, f"A reviewer declared a conflict on the {kind.lower()} of change {row.change_no}.", change=row.name)
			records.bump(doc)
			return records.summary(doc, change=row.name, conflicted=True)
		live.update(state="Recorded", declaration=NO_CONFLICT, recommendation=cstr(recommendation).strip(), reference=cstr(reference).strip(), recorded_at=str(clock.now()))
		records.update(row, reviews_json=records.dumps(found), record_version=cint(row.record_version) + 1)
		work.finish(case, command="RecordContractChangeReview", subject=f"{subject_of(row)} review {_slug(kind)}", actor=actor)
		work.assign(case, "SignContractChangeReview", f"Sign your {kind.lower()} of the requested change.", f"{subject_of(row)} review {_slug(kind)}", draft_of(row), [actor], role="Change reviewer")
		events.record(case, "Review recorded", actor, f"The {kind.lower()} of change {row.change_no} was recorded.", change=row.name)
		records.bump(doc)
		return records.summary(doc, change=row.name)

	return records.command("RecordContractChangeReview", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change, "kind": kind, "recommendation": recommendation,
		"declaration": declaration, "reference": reference}, body=body, authorise=authorise)


def _review_digest(row, slot: dict[str, Any]) -> str:
	return records.digest({"change": row.name, "kind": slot["kind"], "reviewer": slot["reviewer"], "recommendation": slot["recommendation"], "reference": slot["reference"], "declaration": slot["declaration"], "proposal": proposal(row)})


def sign_review(case: str, *, change: int, kind: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignContractChangeReview`: the reviewer's recommendation signed through the shared facade. When every part is signed, the head of procurement is asked to submit the change for decision."""
	preflight.exists(case)
	subject = lambda row: f"{subject_of(row)} review {_slug(kind)} signing"  # noqa: E731

	def authorise() -> None:
		row = get(case, change)
		if row is None:
			raise frappe.DoesNotExistError("Not found")
		_slot_of(row, kind, actor)

	def attempt() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		slot = _slot_of(row, kind, actor)
		if slot["state"] == "Signed":
			return records.summary(doc, change=row.name, already=True)
		if slot["state"] != "Recorded":
			fail("CM_CHANGED", reason="Record your recommendation first.", state=slot["state"])
		guards = preflight.holds(Guards(), case, "new_signing_attempt", except_keys=[f"operation:{signing_flow.existing(case, subject(row), draft_of(row), 'sign')}"] if signing_flow.existing(case, subject(row), draft_of(row), "sign") else [])
		guards.raise_if_any()
		intent = signing_flow.record(case, subject(row), draft_of(row), "sign")
		return records.summary(doc, change=row.name, intent=intent.name)

	recorded = records.command("SignContractChangeReview", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change, "kind": kind}, authorise=authorise, body=attempt)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	row = get(case, change)
	slot = next(s for s in slots(row) if s["kind"] == kind)
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=f"{row.name}:{_slug(kind)}", target_digest=_review_digest(row, slot), version=draft_of(row), action=f"Sign the {kind.lower()} of the requested contract change")
	if signing_flow.settled(result):
		return _apply_review_signature(case, change, kind, result["reference"], actor)
	with records.atomic():
		work.incident(case, "RestoreContractOperation", "Restore signing", f"{subject(row)}", draft_of(row))
		events.record(case, "Signing not completed", actor, f"The {kind.lower()} of change {row.change_no} was not signed ({result['state'].lower()}).", intent=recorded["intent"])
	frappe.db.commit()
	signing_flow.unfinished(result, kind=kind)


def _apply_review_signature(case: str, change: int, kind: str, proof: str, actor: str) -> dict[str, Any]:
	with records.atomic():
		doc = records.lock(case)
		row = get(case, change)
		found = records.loads(row.reviews_json, [])
		live = next(s for s in found if s["kind"] == kind and s["state"] != "Superseded")
		if live["state"] == "Signed":
			return records.summary(doc, change=row.name, already=True)
		live.update(state="Signed", proof=proof, signed_at=str(clock.now()))
		complete = all(s["state"] == "Signed" for s in found if s["state"] != "Superseded") and {s["kind"] for s in found if s["state"] != "Superseded"} >= set(REVIEW_KINDS[row.kind])
		records.update(row, reviews_json=records.dumps(found), state="Reviewed" if complete else row.state, record_version=cint(row.record_version) + 1)
		work.finish(case, command="SignContractChangeReview", subject=f"{subject_of(row)} review {_slug(kind)}", actor=actor)
		work.finish(case, command="RestoreContractOperation", subject=f"{subject_of(row)} review {_slug(kind)} signing", actor=actor)
		events.record(case, "Review signed", actor, f"The {kind.lower()} of change {row.change_no} was signed.", change=row.name, proof=proof)
		if complete:
			_hop_task(case, "SubmitContractChangeForDecision", "Submit the supported request for decision." if row.kind == "Extension" else "Submit the change for decision.", subject_of(row), draft_of(row))
			events.record(case, "Change reviewed", actor, f"Change {row.change_no} has every required review.", change=row.name)
		records.bump(doc)
	frappe.db.commit()
	return records.summary(frappe.get_doc(CASE, case), change=row.name, reviewed=complete)


# -- submit, return and decide -----------------------------------------------------------------------------------------------------------
def _branches(measured: dict[str, Any]) -> set[str]:
	return {"early_total_increase"} if measured.get("early_total_increase") else set()


def _current(case: str, row) -> dict[str, Any]:
	"""The request measured again against the terms in force now: if they moved since the request, the change must be requested again."""
	if cint(records.loads(row.baseline_json).get("version")) != cint(_baseline(case)["version"]):
		fail("CM_CHANGED", reason="The contract changed after this request was made. Request the change again.", change=row.name)
	request = {"proposed_date": proposal(row).get("proposed_date")} if row.kind == "Extension" else {"quantities": proposal(row)["quantities"]}
	return assess(case, row.kind, request)


def submit_for_decision(case: str, *, change: int, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SubmitContractChangeForDecision`: the head of procurement freezes the reviewed change for the Accounting Officer. The rules and every open hold are asked first."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state != "Reviewed":
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		measured = _current(case, row)
		guards = preflight.rules(doc, "SubmitContractChangeForDecision", _branches(measured))
		preflight.holds(guards, case, "vary_contract")
		for limit in measured["blocked"]:
			guards.add("CM_HOLD", hold="CHANGE_LIMIT_EXCEEDED", kind="Rule limit", reason=limit["reason"], holder="Head of procurement function", clears_with="A request within the applicable limit", consequence="SubmitContractChangeForDecision")
		guards.raise_if_any()
		records.update(row, state="Submitted", rule_json=records.dumps({**records.loads(row.rule_json), **_rule_note(measured), "submitted_by": actor, "submitted_at": str(clock.now())}), record_version=cint(row.record_version) + 1)
		work.finish(case, command="SubmitContractChangeForDecision", subject=subject_of(row), actor=actor)
		work.assign(case, "DecideContractChange", "Decide the requested delivery date." if row.kind == "Extension" else "Decide the quantity change.", subject_of(row), draft_of(row), work.holders("Accounting Officer"), role="Accounting Officer")
		events.record(case, "Change submitted", actor, f"Change {row.change_no} submitted for decision.", change=row.name)
		records.bump(doc)
		return records.summary(doc, change=row.name)

	return records.command("SubmitContractChangeForDecision", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change}, body=body, authorise=authorise)


def return_change(case: str, *, change: int, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReturnContractChange`: the head of procurement (before submission) or the Accounting Officer (instead of deciding) sends the request back with the reason; the requester corrects it."""
	preflight.exists(case)

	def authorise() -> None:
		if not people.holds(actor, "Accounting Officer"):
			preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state not in ("Reviewed", "Submitted"):
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		invalid({"reason": "" if cstr(reason).strip() else "Enter why the request is returned."})
		_return(doc, row, actor, cstr(reason).strip())
		return records.summary(doc, change=row.name)

	return records.command("ReturnContractChange", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change, "reason": reason}, body=body, authorise=authorise)


def _return(doc, row, actor: str, reason: str) -> None:
	decision = {"outcome": "Returned", "reason": reason, "by": actor, "at": str(clock.now())}
	records.update(row, state="Returned", decision_json=records.dumps(decision), decided_by=actor, decided_at=clock.now(), record_version=cint(row.record_version) + 1)
	for command in ("SubmitContractChangeForDecision", "DecideContractChange", "AppointContractChangeReviewers", "RecordContractChangeReview", "SignContractChangeReview"):
		work.finish(doc.name, command=command, subject=subject_of(row), state="Superseded", actor=actor)
	work.assign(doc.name, "RequestContractChange", "Correct the change request.", subject_of(row), draft_of(row), [row.requested_by], role="Contract owner")
	events.record(doc.name, "Change returned", actor, f"Change {row.change_no} returned for correction.", change=row.name, reason=reason)
	records.bump(doc)


def decide(case: str, *, change: int, decision: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`DecideContractChange`: the Accounting Officer approves, declines or returns, with a reason. Approval generates the amendment and asks both parties to sign it; nothing changes yet."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require(actor, "Accounting Officer")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state != "Submitted":
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		invalid({"decision": "" if decision in DECISIONS else "Choose approve, decline or return.", "reason": "" if cstr(reason).strip() else "Enter the reason for the decision."})
		signed = [s["reviewer"] for s in slots(row)]
		segregation.change_roles_separate(actor, action="decide", requesters=[row.requested_by], recommenders=signed, reviewers=signed)
		if decision == "Return":
			_return(doc, row, actor, cstr(reason).strip())
			return records.summary(doc, change=row.name)
		measured = _current(case, row)
		guards = preflight.rules(doc, "DecideContractChange", _branches(measured))
		preflight.holds(guards, case, "vary_contract")
		guards.raise_if_any()
		stamp = {"outcome": DECISIONS[decision], "reason": cstr(reason).strip(), "by": actor, "at": str(clock.now())}
		work.finish(case, command="DecideContractChange", subject=subject_of(row), actor=actor)
		if decision == "Decline":
			records.update(row, state="Declined", decision_json=records.dumps(stamp), decided_by=actor, decided_at=clock.now(), record_version=cint(row.record_version) + 1)
			events.record(case, "Change declined", actor, f"Change {row.change_no} declined.", change=row.name, reason=stamp["reason"])
			records.bump(doc)
			return records.summary(doc, change=row.name)
		version = _generate_amendment(doc, row, measured, actor)
		records.update(row, state="Approved", decision_json=records.dumps(stamp), decided_by=actor, decided_at=clock.now(), amendment_version=version, record_version=cint(row.record_version) + 1)
		events.record(case, "Change approved", actor, f"Change {row.change_no} approved; amendment {row.change_no} is out for signature.", change=row.name, amendment=version)
		records.bump(doc)
		return records.summary(doc, change=row.name, amendment_version=version)

	return records.command("DecideContractChange", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change, "decision": decision, "reason": reason}, body=body, authorise=authorise)


# -- the amendment ---------------------------------------------------------------------------------------------------------------------
def _amended_terms(case: str, row, measured: dict[str, Any]) -> dict[str, Any]:
	new = copy.deepcopy(operative_terms(case))
	effective_on = proposal(row).get("effective_on") or ""
	if row.kind == "Extension":
		delivery = new["delivery"]
		delivery.setdefault("original_due", delivery["due"])
		delivery.setdefault("extensions", []).append({"change": row.change_no, "from": delivery["due"], "to": measured["proposed_due"], "effective_on": effective_on})
		delivery["due"] = measured["proposed_due"]
	else:
		wanted = {l["line_id"]: l["proposed"] for l in measured["lines"]}
		for line in new["lines"]:
			if line["line_id"] in wanted:
				line["quantity"] = wanted[line["line_id"]]
				line["amount"] = wanted[line["line_id"]] * flt(line["rate"])
		new["total"] = measured["proposed_total"]
		by_reservation = {f["reservation"]: f["additional"] for f in proposal(row).get("funding", [])}
		for allocation in new.get("funding", {}).get("allocations", []):
			allocation["amount"] = flt(allocation["amount"]) + by_reservation.get(allocation["reservation"], 0)
	new["amendment"] = {"change": row.name, "number": row.change_no, "kind": row.kind, "effective_on": effective_on}
	return new


def _render(row, before: dict[str, Any], after: dict[str, Any]) -> str:
	head = f"<h1>AMENDMENT {row.change_no} TO THE CONTRACT AGREEMENT</h1><p>{after['parties']['entity']['name']} and {after['parties']['supplier']['name']} agree to the following change to {after['title']}.</p>"
	if row.kind == "Extension":
		body = f"<p>The delivery date moves from {before['delivery']['due']} to {after['delivery']['due']}. The price and quantities are unchanged.</p>"
	else:
		rows = "".join(f"<tr><td>{b['description']}</td><td>{cint(b['quantity'])}</td><td>{cint(a['quantity'])}</td><td>{flt(a['rate']):,.2f}</td></tr>" for b, a in zip(before["lines"], after["lines"], strict=True) if cint(b["quantity"]) != cint(a["quantity"]))
		body = f"<table><tr><th>Item</th><th>Was</th><th>Becomes</th><th>Rate</th></tr>{rows}</table><p>The total moves from {before['currency']} {flt(before['total']):,.2f} to {after['currency']} {flt(after['total']):,.2f}.</p>"
	return head + body + "<p>Every other term of the agreement is unchanged.</p>"


def _generate_amendment(doc, row, measured: dict[str, Any], actor: str) -> int:
	case = doc.name
	before, after = operative_terms(case), _amended_terms(case, row, measured)
	html = _render(row, before, after)
	version = records.next_number(AGREEMENT, {"contract_case": case}, "version_no")
	agreement = records.new(AGREEMENT, contract_case=case, version_no=version, state="Awaiting signatures", amount=after["total"], currency=after["currency"], operative_date=proposal(row).get("effective_on") or None, terms_json=records.dumps(after),
		items_json=records.dumps(after["lines"]), missing_json=records.dumps([]), rendered_html=html, rendered_digest=records.digest({"text": html, "change": row.name, "terms": records.digest(after)}), frozen_at=clock.now(), change=row.name,
		source_package=frappe.db.get_value(AGREEMENT, {"contract_case": case, "change": ["is", "not set"]}, "source_package"), record_version=1)
	parties_ = after["parties"]
	for sequence, (party, who) in enumerate((("Supplier", parties_["supplier"]), ("Entity", parties_["entity"])), start=1):
		records.new(SIGNATURE, contract_case=case, agreement_version=version, party=party, sequence=sequence, signer=who["user"], capacity=who["capacity"], state="Requested" if sequence == 1 else "Waiting", record_version=1)
	subject = amendment_subject(row)
	work.assign(case, "SignContractVersion", f"Review and sign amendment {row.change_no}.", subject, version, [parties_["supplier"]["user"]], role="Authorised signatory")
	work.assign(case, work.waiting_command("SignContractVersion", "supplier"), "Waiting for the supplier's signature.", subject, version, sorted(set(work.holders(work.HOP)) | {actor}), role=work.HOP, state="Waiting")
	return version


# -- signing the amendment --------------------------------------------------------------------------------------------------------------
def _slot(case: str, amendment, party: str):
	name = frappe.db.get_value(SIGNATURE, {"contract_case": case, "agreement_version": amendment.version_no, "party": party}, "name")
	return frappe.get_doc(SIGNATURE, name) if name else None


def sign_amendment(case: str, *, change: int, party: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignContractVersion` for an amendment: the supplier's authorised signatory first, then the entity's, each through the shared facade. The second proof makes the amendment effective (unless its
	effective date is later, or a rule or hold stops it, in which case the activation waits as its own step with the proofs kept)."""
	preflight.exists(case)

	def attempt() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state != "Approved":
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		amendment = amendment_of(row)
		slot = _slot(case, amendment, party)
		if slot is None or slot.state == "Signed":
			return records.summary(doc, signature=slot.name if slot else "", already=True)
		if slot.signer.lower() != actor.lower():
			fail("CM_AUTHORITY", missing="mandate", reason="This signature is for another person.", capacity=party)
		if party == "Entity" and (_slot(case, amendment, "Supplier").state != "Signed"):
			fail("CM_CHANGED", reason="The supplier signs first.", waiting_for="supplier signature")
		subject = f"signature {party.lower()} {amendment_subject(row)}"
		existing = signing_flow.existing(case, subject, amendment.version_no, f"sign-{party.lower()}")
		guards = preflight.holds(Guards(), case, "new_signing_attempt", except_keys=[f"operation:{existing}"] if existing else [])
		guards.raise_if_any()
		intent = signing_flow.record(case, subject, amendment.version_no, f"sign-{party.lower()}")
		return records.summary(doc, change=row.name, signature=slot.name, intent=intent.name, party=party)

	recorded = records.command("SignContractVersion", case=case, idempotency_key=idempotency_key, actor=actor, payload={"party": party, "expected": expected_version, "change": change},
		authorise=lambda: formation._authorise_signing(case, party, actor), body=attempt)
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	row = get(case, change)
	amendment = amendment_of(row)
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=amendment.name, target_digest=amendment.rendered_digest, version=amendment.version_no, action=f"Sign amendment {row.change_no} as the {party.lower()}")
	if signing_flow.settled(result):
		return _apply_signature(case, change, recorded["signature"], result["reference"], actor, result["method"])
	pending = result["state"] in ("Attempting", "Uncertain", "Recorded")
	with records.atomic():
		doc = records.lock(case)
		slot = frappe.get_doc(SIGNATURE, recorded["signature"])
		records.update(slot, state="Pending" if pending else "Failed", correlation_id=frappe.db.get_value(intents.INTENT, recorded["intent"], "operation_identity"))
		records.bump(doc)
		work.incident(case, "RestoreContractOperation", "Restore signing", f"signature {party.lower()} {amendment_subject(row)}", amendment.version_no)
		events.record(case, "Signing not completed", actor, f"The {party.lower()} signature of amendment {row.change_no} was not completed ({result['state'].lower()}).", intent=recorded["intent"])
	frappe.db.commit()
	signing_flow.unfinished(result, party=party)


def _apply_signature(case: str, change: int, slot_name: str, proof: str, actor: str, method: str) -> dict[str, Any]:
	activated = False
	with records.atomic():
		doc = records.lock(case)
		row = get(case, change)
		slot = frappe.get_doc(SIGNATURE, slot_name)
		if slot.state == "Signed":
			return records.summary(doc, signature=slot.name, state="Signed", party=slot.party)
		amendment = amendment_of(row)
		records.update(slot, state="Signed", proof_reference=proof, method=method or signing_flow.METHOD, signed_at=clock.now(), record_version=cint(slot.record_version) + 1)
		subject = amendment_subject(row)
		work.finish(case, command="RestoreContractOperation", subject=f"signature {slot.party.lower()} {subject}", actor=actor)
		events.record(case, "Signed", actor, f"Amendment {row.change_no} signed for the {slot.party.lower()}.", signature=slot.name, proof=proof)
		work.finish(case, command="SignContractVersion", subject=subject, actor=actor)
		if slot.party == "Supplier":
			entity = _slot(case, amendment, "Entity")
			records.update(entity, state="Requested" if entity.state == "Waiting" else entity.state)
			work.assign(case, "SignContractVersion", f"Review and sign amendment {row.change_no}.", subject, amendment.version_no, [entity.signer], role="Entity contract signing")
			work.assign(case, work.waiting_command("SignContractVersion", "entity"), "Waiting for the entity's signature.", subject, amendment.version_no, work.holders(work.HOP) + [slot.signer], role=work.HOP, state="Waiting")
			records.bump(doc)
		else:
			activated = _activate_if_ready(doc, row, amendment, actor)
	frappe.db.commit()
	if activated:
		carry_out_effects(case, actor)
	return records.summary(frappe.get_doc(CASE, case), signature=slot_name, state="Signed", party=slot.party, **({"effective": True} if activated else {}))


# -- taking effect ---------------------------------------------------------------------------------------------------------------------
def _activate_if_ready(doc, row, amendment, actor: str) -> bool:
	"""Both proofs are in. The amendment takes effect now unless its effective date is later or a rule or hold stops it; then it waits, signed, for `ActivateContractChange`."""
	due = proposal(row).get("effective_on")
	guards = preflight.rules(doc, "ActivateContractChange")
	preflight.holds(guards, doc.name, "vary_contract")
	if (due and getdate(due) > getdate(clock.now())) or guards:
		work.assign(doc.name, "ActivateContractChange", f"Bring amendment {row.change_no} into effect.", amendment_subject(row), amendment.version_no, work.holders(work.HOP), role=work.HOP, state="Scheduled" if due and not guards else "Open")
		records.bump(doc)
		return False
	_make_effective(doc, row, amendment, actor)
	return True


def activate_change(case: str, *, change: int, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ActivateContractChange`: bring a fully signed amendment into effect once its date has come and nothing stops it."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		row = get(case, change)
		if row is None or row.state != "Approved":
			fail("CM_CHANGED", change=change, state=row.state if row else "")
		amendment = amendment_of(row)
		if not all(_slot(case, amendment, p).state == "Signed" for p in ("Supplier", "Entity")):
			fail("CM_CHANGED", reason="Both parties must sign the amendment first.")
		due = proposal(row).get("effective_on")
		guards = preflight.rules(doc, "ActivateContractChange")
		preflight.holds(guards, case, "vary_contract")
		if due and getdate(due) > getdate(clock.now()):
			guards.add("CM_HOLD", hold="effective date", kind="Effective date", reason=f"The amendment takes effect on {due}.", holder="Head of procurement function", clears_with="The effective date arrives", consequence="ActivateContractChange")
		guards.raise_if_any()
		_make_effective(doc, row, amendment, actor)
		return records.summary(doc, change=row.name, effective=True)

	recorded = records.command("ActivateContractChange", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "change": change}, body=body, authorise=authorise)
	frappe.db.commit()
	carry_out_effects(case, actor)
	return recorded


def _make_effective(doc, row, amendment, actor: str) -> None:
	"""The amendment is in force (the same transaction as the second proof): the terms change, and the order and funding updates are recorded as durable operations."""
	case, subject = doc.name, amendment_subject(row)
	terms = records.loads(amendment.terms_json)
	records.update(amendment, state="Effective", effective_at=clock.now(), record_version=cint(amendment.record_version) + 1)
	records.update(row, state="Effective", effective_at=clock.now(), record_version=cint(row.record_version) + 1)
	work.finish(case, command="ActivateContractChange", subject=subject, actor=actor)
	records.bump(doc, contract_value=terms["total"])
	intents.record(case, subject, amendment.version_no, "Purchase order", "update", recovery_owner="Technical operator; Budget owner")
	if flt(terms["total"]) != flt(records.loads(frappe.db.get_value(AGREEMENT, {"contract_case": case, "state": "Effective", "version_no": ["<", amendment.version_no]}, "terms_json", order_by="version_no desc") or "{}").get("total")):
		intents.record(case, subject, amendment.version_no, "Funding adjustment", "update", recovery_owner="Technical operator; Budget owner")
	events.record(case, "Change effective", actor, f"Amendment {row.change_no} is in force.", change=row.name, amendment=amendment.name, **({"due": terms["delivery"]["due"]} if row.kind == "Extension" else {"total": terms["total"]}))
	obligations.on_variation_effective(case, row.name, row.change_no, clock.now())
	if row.kind == "Extension":
		from kentender_contracts.services import adjustment

		adjustment.on_due_changed(case, actor)


def carry_out_effects(case: str, actor: str = "") -> dict[str, Any]:
	"""Carry each effective amendment's pending order update and funding adjustment through their owners, each in its own transaction. Safe to repeat: the owner is read first by identity."""
	out = []
	for row in effective_changes(case):
		amendment = amendment_of(row)
		terms = records.loads(amendment.terms_json)
		subject = amendment_subject(row)
		for kind in ("Purchase order", "Funding adjustment"):
			name = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": kind, "subject": subject}, "name")
			if not name or frappe.db.get_value(intents.INTENT, name, "state") in intents.SETTLED:
				continue
			if kind == "Purchase order":
				result = intents.execute(name, lambda identity, t=terms: _update_order(case, identity, t), lambda identity, t=terms: _order_reflects(case, identity, t), native_doctype="Purchase Order update")
			else:
				result = intents.execute(name, lambda identity, t=terms, n=row.change_no: _adjust_funding(case, identity, t, n), lambda identity: _funding_found(identity), native_doctype="Procurement Commitment")
			out.append({"kind": kind, "subject": subject, **result})
			with records.atomic():
				if result["state"] in intents.SETTLED:
					work.finish(case, command="RestoreContractOperation", subject=subject, actor=actor)
					events.record(case, f"{kind} linked", actor, f"{kind} update for amendment {row.change_no} linked.", intent=name, reference=result["reference"])
				else:
					work.incident(case, "RestoreContractOperation", "Restore contract operation", subject, amendment.version_no)
					events.record(case, "Operation pending", actor, f"{kind} update for amendment {row.change_no} did not complete ({result['state'].lower()}).", intent=name)
			frappe.db.commit()
	return {"ok": True, "operations": out}


def _order_items(case: str, terms: dict[str, Any]) -> list[dict[str, Any]]:
	mapping = terms["particulars"]["item_mapping"]
	return [{"item_code": mapping[l["line_id"]], "qty": l["quantity"], "rate": l["rate"]} for l in terms["lines"] if l["line_id"] in mapping]


def _marker(case: str, identity: str) -> str:
	return f"{formation.native_order(case)}#{records.short(identity)}"


def _update_order(case: str, identity: str, terms: dict[str, Any]) -> tuple[str, str]:
	order = formation.native_order(case)
	if not order:
		raise RuntimeError("The purchase order has not been created yet.")
	try:
		with service_principal.acting():
			adapter.update_order(order, items=_order_items(case, terms), schedule_date=terms["delivery"]["due"])
	except frappe.ValidationError as exc:
		raise intents.OwnerRefused(str(exc)) from exc
	return _marker(case, identity), "Purchase Order update"


def _order_reflects(case: str, identity: str, terms: dict[str, Any]) -> str | None:
	order = formation.native_order(case)
	return _marker(case, identity) if order and adapter.order_reflects(order, items=_order_items(case, terms), schedule_date=terms["delivery"]["due"]) else None


def _adjust_funding(case: str, identity: str, terms: dict[str, Any], number: int) -> tuple[str, str]:
	allocations = [{"reservation": a["reservation"], "new_total": a["amount"]} for a in terms["funding"]["allocations"]]
	try:
		done = funding_seam.adjust(identity, contract=case, allocations=allocations, event_id=f"{case}|amendment {number}", event_type=FUNDING_EVENT)
	except funding_seam.Refused as exc:
		raise intents.OwnerRefused(str(exc)) from exc
	return done["reference"], "Procurement Commitment"


def _funding_found(identity: str) -> str | None:
	found = funding_seam.recall(identity)
	return found["reference"] if found else None
