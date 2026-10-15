# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Change screens: requesting, reviewing, deciding and signing a change to the agreement in force (boards D27, D27-R, D27-A, D14, D14-P, D34, D34-A, D34-R, D34-P, D34-H, D34-L, D34-X; CM-CHG-001 v0.8 sections 5.7, 5.11, 10.5, 10.8).

Two steps have no artboard: naming the reviewers (head of procurement) and a reviewer recording and signing a recommendation. They are composed from the same vocabulary as D27-R (a comparison, a table of reviewers, a form
with a declaration) and recorded as authored in the tracker. Every figure on these screens is read from the change record; the quantity form prefills one more unit and no officer edits a rate or a percentage."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import change, events, intents, records

SYNTHETIC_NOTE = "Synthetic mechanism test — not a legally cleared production example."


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _short(value: Any) -> str:
	return formatdate(value, "d MMM yyyy") if value else "—"


def _goods_quantity(terms: dict[str, Any]) -> int:
	return sum(cint(l["quantity"]) for l in terms.get("lines", []) if l.get("kind") != "service")


def _goods_label(terms: dict[str, Any]) -> str:
	line = next((l for l in terms.get("lines", []) if l.get("kind") != "service"), {})
	return (line.get("description") or line.get("item") or "").lower()


def _comparison(ctx: Context, row, heading: str) -> dict[str, Any]:
	base, body, cur = records.loads(row.baseline_json), change.proposal(row), ctx.currency
	if row.kind == "Extension":
		quantity = sum(cint(v) for v in base["lines"].values())
		return kit.t(["Term", "Current", heading], [["Delivery date", _long(base["due"]), _long(body["proposed_date"])], ["Contract value", money(base["total"], cur), money(base["total"], cur)],
			["Quantity", str(quantity), str(quantity)]], [1, 2])
	note = records.loads(row.rule_json)
	lines = note.get("lines") or []
	return kit.t(["", "Current", heading], [["Quantity", str(sum(l["current"] for l in lines)), str(sum(l["proposed"] for l in lines))], ["Total", money(note["current_total"], cur), money(note["proposed_total"], cur)],
		["Cumulative change", "—", f"{note['cumulative_value_percent']:g}%"]], [1, 2])


def _review_rows(ctx: Context, row) -> list[list[str]]:
	return [[s["kind"], f"{ctx.name(s['reviewer'])}: {s['recommendation']}" + (f" ({s['reference']})" if s.get("reference") else "")] for s in change.slots(row) if s["state"] == "Signed"]


def _reviewers_table(ctx: Context, row) -> dict[str, Any]:
	return kit.t(["Reviewer", "Part", "Declaration", "Recommendation signed"], [[ctx.name(s["reviewer"]), s["kind"], s.get("declaration") or "Pending", when(s["signed_at"]) if s.get("signed_at") else "Not yet"] for s in change.slots(row)])


def _facts_of_review(ctx: Context, row) -> list[Any]:
	body = change.proposal(row)
	appointed = body.get("appointment") or {}
	return [kit.R("Request", _comparison(ctx, row, "Proposed"), kit.r(["Reason", row.reason])), kit.R("Appointed reviewers", _reviewers_table(ctx, row),
		kit.r(*(_review_rows(ctx, row) or [["Recommendation", "Not yet signed"]]), ["Appointment", appointed.get("reference", "—")]))]


def _evidence(row) -> list[str]:
	return [e["label"] for e in records.loads(row.evidence_json, [])]


# -- the request (D27, D34) --------------------------------------------------------------------------------------------------------------
def request(ctx: Context, kind: str, *, proposed: int | None = None, correcting=None) -> dict[str, Any]:
	"""The form to request a change: an extension of the delivery date (D27) or an increase of a goods quantity (D34). Quantity prefills one more unit and shows the figures the server calculates."""
	terms = ctx.terms
	name = ctx.name(ctx.user)
	corrected = {"correcting": correcting.change_no} if correcting is not None else {}
	if kind == "Extension":
		fields = [kit.ro("Current delivery", _short(terms["delivery"]["due"])), kit.dt("Proposed date", "", "proposed_date"), kit.ta("Reason", correcting.reason if correcting else "", "reason"), kit.file("Supplier request", "", "evidence"),
			kit.ro("Amount and quantity", f"{money(terms['total'], ctx.currency)}; {_goods_quantity(terms)} {_goods_label(terms)}s; no price change")]
		b = chrome.base(ctx, "D27", d="D27", name="Request delivery extension", title="Request delivery extension", tab="Obligations", next=chrome.form_turn(ctx, "RequestContractChange", "Explain the requested delivery date."),
			regions=[kit.R("Request", kit.fl(*fields))], p="Request extension", s2=["Cancel"], ev=["Agreement 1"])
		b["actions"]["Request extension"] = kit.command("RequestContractChange", kind="Extension", **corrected)
		b["actions"]["Cancel"] = kit.tab("Obligations")
		return b
	goods = [l for l in terms["lines"] if l.get("kind") != "service"]
	asked = {l["line_id"]: (proposed if proposed is not None and l is goods[0] else cint(l["quantity"]) + 1) for l in goods}
	measured = change.assess(ctx.case, "Quantity", {"quantities": asked})
	rows = [[l.get("description") or l.get("item"), str(measured_line["original"]), money(l["rate"], ctx.currency), f"#{measured_line['proposed']}"] for l in goods for measured_line in measured["lines"] if measured_line["line_id"] == l["line_id"]]
	inputs = {f"{i},3": f"quantity.{l['line_id']}" for i, l in enumerate(l for l in goods if any(m["line_id"] == l["line_id"] for m in measured["lines"]))}
	first = measured["lines"][0] if measured["lines"] else {"percent_of_original": 0.0}
	facts = kit.f(["Proposed total", money(measured.get("proposed_total", terms["total"]), ctx.currency)], ["Cumulative quantity change", f"{first['percent_of_original']:g}%"], ["Cumulative value change", f"{measured.get('cumulative_value_percent', 0):g}%"])
	blocked = measured["blocked"]
	next_ = chrome.form_turn(ctx, "RequestContractChange", "Explain the additional quantity.")
	if blocked:
		next_ = kit.blk("Proposed quantity exceeds the applicable limit", name, ["View rule", "View issue"], blocked[0]["reason"])
	reason = kit.R("Request", kit.fl(kit.ta("Reason", correcting.reason if correcting else "", "reason"), kit.file("Source request", "", "evidence")))
	if blocked:  # D34-X: the comparison of what is asked against what is in force, and the limit it exceeds; nothing to submit and nothing to edit
		top = measured["lines"][0]
		regions = [kit.R("Comparison", kit.t(["", "Current", "Proposed"], [["Quantity", str(top["current"]), str(top["proposed"])], ["Total", money(measured["current_total"], ctx.currency), money(measured["proposed_total"], ctx.currency)],
			["Cumulative change", "—", f"{measured['cumulative_value_percent']:g}%"]], [1, 2]), kit.r(["Applicable limit", f"{measured['ceiling_percent']:g}% goods quantity"]))]
	else:
		regions = [kit.R("Quantity", kit.t(["Item", "Original", "Rate", "Proposed"], rows, [1, 2, 3], inputs=inputs), facts), reason]
	b = chrome.base(ctx, "D34-X" if blocked else "D34", d="D34", name="Quantity variation", title="Request quantity change", tab="Obligations", next=next_, regions=regions,
		p="" if blocked else "Request change", s2=[] if blocked else ["Cancel"], ev=["Agreement 1"], subj="Agreement 1")
	b["actions"]["Request change"] = kit.command("RequestContractChange", kind="Quantity", **corrected)
	b["actions"]["Cancel"] = kit.tab("Obligations")
	b["actions"]["View rule"] = b["actions"]["View issue"] = kit.tab("Obligations")
	return b


# -- naming the reviewers, recording and signing a review (authored: no artboard) -------------------------------------------------------------
def appoint(ctx: Context, row) -> dict[str, Any]:
	"""The head of procurement names who reviews each part, by the Accounting Officer's appointment reference."""
	held = {s["kind"] for s in change.slots(row) if s["state"] != "Conflicted"}
	fields = [kit.tx("Appointment reference", "", "reference")] + [kit.pick(kind, "", "contracts.person", f"reviewer.{change._slug(kind)}", {"role": change.REVIEWER}, "", "reviewer") for kind in change.REVIEW_KINDS[row.kind] if kind not in held]
	b = chrome.base(ctx, "D27-N", d="D27", name="Appoint reviewers", title="Name the reviewers", tab="Obligations", next=chrome.next_block(ctx), ev=_evidence(row),
		regions=[kit.R("Request", _comparison(ctx, row, "Proposed"), kit.r(["Reason", row.reason], ["Requested by", ctx.name(row.requested_by)])), kit.R("Reviewers", kit.fl(*fields))], p="Appoint reviewers", s2=["Return for correction"])
	b["actions"]["Appoint reviewers"] = kit.command("AppointContractChangeReviewers", change=row.change_no)
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractChange", args={"change": row.change_no})
	return b


def review(ctx: Context, row, kind: str, *, signing: bool = False) -> dict[str, Any]:
	"""A reviewer's own part: declare no conflict and record the recommendation, then sign it."""
	slot = next(s for s in change.slots(row) if s["kind"] == kind)
	if signing:
		regions = [kit.R("Request", _comparison(ctx, row, "Proposed")), kit.R(f"Your {kind.lower()}", kit.r(["Declaration", slot["declaration"]], ["Recommendation", slot["recommendation"]], *([["Reference", slot["reference"]]] if slot.get("reference") else [])))]
		b = chrome.base(ctx, "D27-S", d="D27", name="Review the change", title=f"Sign your {kind.lower()}", tab="Obligations", next=chrome.next_block(ctx), regions=regions, p="Sign review", ev=_evidence(row))
		b["actions"]["Sign review"] = kit.command("SignContractChangeReview", change=row.change_no, kind=kind)
		return b
	choices = [change.NO_CONFLICT, "I have a conflict of interest"]
	fields = [kit.rad("Your declaration", choices, -1, "declaration"), kit.ta("Recommendation", "", "recommendation")] + ([kit.tx("Funding confirmation reference", "", "reference")] if kind == "Funding confirmation" else [])
	b = chrome.base(ctx, "D27-V", d="D27", name="Review the change", title=f"Record your {kind.lower()}", tab="Obligations", next=chrome.next_block(ctx), ev=_evidence(row),
		regions=[kit.R("Request", _comparison(ctx, row, "Proposed"), kit.r(["Reason", row.reason])), kit.R(f"Your {kind.lower()}", kit.fl(*fields))], p="Record review")
	b["actions"]["Record review"] = kit.command("RecordContractChangeReview", change=row.change_no, kind=kind)
	return b


# -- submit (D27-R, D34-R, D34-L) ----------------------------------------------------------------------------------------------------------
def submit(ctx: Context, row) -> dict[str, Any]:
	"""The head of procurement submits the reviewed request for decision. An early total increase is held for the legal question (D34-L)."""
	name = ctx.name(ctx.user)
	held = change.held_question(ctx.case, row)
	if row.kind == "Extension":
		b = chrome.base(ctx, "D27-R", d="D27", name="Request delivery extension", title="Review delivery extension request", tab="Obligations", next=chrome.next_block(ctx), regions=_facts_of_review(ctx, row),
			p="Submit change for decision", s2=["Return for correction"], ev=_evidence(row))
	else:
		note = chrome_review(ctx, row)
		b = chrome.base(ctx, "D34-L" if held else "D34-R", d="D34", name="Quantity variation", title="Review quantity change", tab="Obligations", next=chrome.next_block(ctx),
			regions=[kit.R("Comparison", _comparison(ctx, row, "Proposed"), kit.xh(SYNTHETIC_NOTE)), note], p="" if held else "Submit change for decision", s2=[] if held else ["Return for correction"], ev=_evidence(row))
		if held:
			b["next"] = kit.blk("Change requires legal review", name, ["View rule", "View request", "Return for correction"], "The proposed increase is within twelve months of signing. Its legal basis has not been established.")
			b["actions"]["View rule"] = b["actions"]["View request"] = kit.tab("Obligations")
	b["actions"]["Submit change for decision"] = kit.command("SubmitContractChangeForDecision", change=row.change_no)
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractChange", args={"change": row.change_no})
	return b


def chrome_review(ctx: Context, row) -> dict[str, Any]:
	"""The reviews a quantity change stands on, as the design's Review region: each signed part with its recommendation, and the funding it adds."""
	body = change.proposal(row)
	funding = ", ".join(f"{money(f['additional'], ctx.currency)} additional on {f['reservation']}" for f in body.get("funding", []))
	rows = _review_rows(ctx, row) + ([["Funding", funding]] if funding else [])
	return kit.R("Review", kit.r(*(rows or [["Review", "Not yet signed"]])))


# -- the decision (D14, D34-A) ---------------------------------------------------------------------------------------------------------------
def decide(ctx: Context, row) -> dict[str, Any]:
	"""The Accounting Officer's decision: approve, decline or return, each with a reason."""
	body = change.proposal(row)
	if row.kind == "Extension":
		b = chrome.base(ctx, "D14", d="D14", name="Extension review", title="Review delivery extension", tab="Obligations", next=chrome.next_block(ctx), subj="Agreement 1 · change 1 draft 1",
			regions=[kit.R("Requested change", _comparison(ctx, row, "Requested"), kit.r(["Reason", row.reason], ["Recommendation", next((s["recommendation"] for s in change.slots(row) if s["kind"] == "Committee recommendation"), "")])),
				kit.R("Supporting evidence", kit.lk(*(_evidence(row) + [s["kind"] for s in change.slots(row)])))],
			p="Approve extension", s2=["Decline", "Return for correction"], ev=_evidence(row) + [s["kind"] for s in change.slots(row)])
		approve_title, decline_title = "Approve extension", "Decline extension"
	else:
		b = chrome.base(ctx, "D34-A", d="D34", name="Quantity variation", title="Review quantity change", tab="Obligations", next=chrome.next_block(ctx),
			regions=[kit.R("Comparison", _comparison(ctx, row, "Proposed"), kit.xh(SYNTHETIC_NOTE)), chrome_review(ctx, row)], p="Approve change", s2=["Decline", "Return for correction"], ev=_evidence(row))
		approve_title, decline_title = "Approve change", "Decline change"
	primary = b["p"]
	args = {"change": row.change_no}
	b["actions"][primary] = kit.dialog("approve")
	b["actions"]["Decline"] = kit.dialog("decline")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["approve"] = kit.dlg(approve_title, [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractChange", args={**args, "decision": "Approve"})
	b["dialogs"]["decline"] = kit.dlg(decline_title, [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractChange", args={**args, "decision": "Decline"})
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractChange", args={**args, "decision": "Return"})
	return b


# -- the amendment (D27-A, D34-P, D14-P) -----------------------------------------------------------------------------------------------------
def sign(ctx: Context, row, *, entity: bool = False) -> dict[str, Any]:
	"""Sign the amendment: the supplier's signatory first, the entity's second. The same screen serves both; it never shows an operative term the amendment has not yet changed."""
	amendment = change.amendment_of(row)
	party = "Entity" if entity else "Supplier"
	other = "The supplier has signed; the amendment takes effect when you sign." if entity else f"The amendment takes effect only after both required signatures. {ctx.name((records.loads(amendment.terms_json)['parties']['entity'] or {}).get('user'))} signs the same version next."
	identifier = "D27-A" if row.kind == "Extension" else "D34-P"
	regions = [kit.R(f"Amendment {row.change_no}", _comparison(ctx, row, "Amended"), *([kit.lk(f"View amendment {row.change_no}")] if row.kind == "Extension" else []), kit.xh(other))]
	if row.kind == "Quantity":
		regions[0]["b"].insert(1, kit.xh(SYNTHETIC_NOTE))
	b = chrome.base(ctx, identifier, d=identifier.split("-")[0], name="Sign amendment", title="Sign amendment", tab="Obligations", next=chrome.next_block(ctx), subj=f"Amendment {row.change_no}",
		back="Back to my contracts" if not entity else "Back to contracts", regions=regions, p="Sign amendment", s2=["Report a problem"], ev=[f"Amendment {row.change_no}", f"Decision {row.change_no}"])
	b["actions"]["Sign amendment"] = kit.command("SignContractVersion", change=row.change_no, party=party)
	b["actions"][f"View amendment {row.change_no}"] = kit.route(ctx.case, "agreement", "amendment", str(row.change_no))
	b["actions"]["Report a problem"] = kit.dialog("problem")
	b["dialogs"]["problem"] = kit.dlg("Report a problem", [kit.fl(kit.tx("Title", "", "title"), kit.ta("Description", "", "description"))], "Report", command="RecordContractIssue", args={})
	return b


def pending(ctx: Context, row) -> dict[str, Any]:
	"""Approved, the amendment not yet effective (D14-P): what was decided and that the operative term is still the old one."""
	body = records.loads(row.decision_json)
	decision = f"Approved {when(row.decided_at)}"
	operative = _long(ctx.terms["delivery"]["due"]) if row.kind == "Extension" else f"{_goods_quantity(ctx.terms)} {_goods_label(ctx.terms)}s"
	label = "Operative delivery date" if row.kind == "Extension" else "Operative quantity"
	b = chrome.base(ctx, "D14-P", d="D14", name="Extension review", title="Review delivery extension" if row.kind == "Extension" else "Review quantity change", tab="Obligations", next=chrome.next_block(ctx),
		regions=[kit.R("Decision", kit.r(["Decision", decision], [label, f"{operative} — amendment not yet effective"]))], s2=["View amendment", "View decision"], ev=[])
	b["actions"]["View amendment"] = kit.route(ctx.case, "agreement", "amendment", str(row.change_no))
	b["actions"]["View decision"] = kit.tab("History")
	return b


def amendment_view(ctx: Context, row) -> dict[str, Any]:
	"""The amendment itself: its comparison and generated text, read-only."""
	from kentender_contracts.boards.agreement import _plain_paragraphs

	amendment = change.amendment_of(row)
	b = chrome.base(ctx, "D02-V", d="D02", name="Amendment", title=f"Amendment {row.change_no}", tab="Agreement", back="Back to contract", next=None, ev=[],
		regions=[kit.R(f"Amendment {row.change_no}", _comparison(ctx, row, "Amended")), kit.R("Amendment text", *[kit.xh(p) for p in _plain_paragraphs(amendment.rendered_html)])], p="")
	b["actions"]["Back to contract"] = kit.route(ctx.case, "agreement")
	return b


def effective_pending(ctx: Context, row) -> dict[str, Any]:
	"""The change is in force but the order or the funding update has not completed (D34-H): spending that depends on it is held until the owner's result is read."""
	states = change.effects(ctx.case, row)
	order, funding = states.get("Purchase order"), states.get("Funding adjustment")
	facts = [["Operative quantity", str(_goods_quantity(ctx.terms))] if row.kind == "Quantity" else ["Operative delivery date", _long(ctx.terms["delivery"]["due"])]]
	if funding is not None:
		facts.append(["Budget adjustment", "Acknowledged" if funding in intents.SETTLED else "Pending"])
	facts += [["Order update", "Done" if order in intents.SETTLED else "Pending"], ["New spending", "Held for the changed quantity" if row.kind == "Quantity" else "Held until the order is updated"]]
	b = chrome.base(ctx, "D34-H", d="D34", name="Quantity variation", title="Contract change recorded", tab="Obligations", next=chrome.next_block(ctx), regions=[kit.R("Change", kit.r(*facts), *([kit.xh(SYNTHETIC_NOTE)] if row.kind == "Quantity" else []))],
		s2=["View update status", "View amendment"], ev=[])
	b["actions"]["View update status"] = kit.tab("Obligations")
	b["actions"]["View amendment"] = kit.route(ctx.case, "agreement", "amendment", str(row.change_no))
	return b


def register(ctx: Context) -> dict[str, Any]:
	"""The Contract changes region of the Obligations tab: every change, what it asks and where it stands."""
	rows = []
	for number in frappe.get_all("Contract Change", filters={"contract_case": ctx.case}, pluck="change_no", order_by="change_no asc"):
		row = change.get(ctx.case, number)
		what = f"Delivery date to {_short(change.proposal(row)['proposed_date'])}" if row.kind == "Extension" else "Quantity to " + ", ".join(str(v) for v in change.proposal(row)["quantities"].values())
		rows.append([f"Change {row.change_no}", what, row.state, ctx.name(row.requested_by)])
	return kit.R("Contract changes", kit.t(["Change", "What", "Status", "Requested by"], rows))


def activate(ctx: Context, row) -> dict[str, Any]:
	"""Both parties have signed: bring the amendment into effect (authored: no artboard). It waits only for its effective date or for a rule or hold to clear."""
	due = change.proposal(row).get("effective_on")
	b = chrome.base(ctx, "D14-E", d="D14", name="Bring the amendment into effect", title=f"Bring amendment {row.change_no} into effect", tab="Obligations", next=chrome.next_block(ctx),
		regions=[kit.R(f"Amendment {row.change_no}", _comparison(ctx, row, "Amended"), kit.r(["Signed by", "The supplier and the entity"], ["Takes effect", _long(due) if due else "When brought into effect"]))],
		p="Bring into effect", ev=[f"Amendment {row.change_no}", f"Decision {row.change_no}"])
	b["actions"]["Bring into effect"] = kit.command("ActivateContractChange", change=row.change_no)
	return b
