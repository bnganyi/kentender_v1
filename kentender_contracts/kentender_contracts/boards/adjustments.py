# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contractual delay adjustment screens (boards D36, D36-A, D36-S, D36-H, D36-E; CM-CHG-001 v0.8 sections 5.19, 10.8).

Every figure is the system's: the due date (an effective extension moves it), the day the last unit was accepted, the count basis, the eligible principal, the rate and the cap. The head of procurement records the
causation, the clause, the supplier's response and a recommendation in the dialog that submits the proposal; the Accounting Officer sees them read-only and decides. The certification with an adjustment shows
the supported gross, the authorised adjustment and the proposed cash apart, and says the adjustment is never cash."""

from __future__ import annotations

from typing import Any

from frappe.utils import cint, flt, formatdate, getdate

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context, money
from kentender_contracts.services import adjustment, holds


def _day(value: Any) -> str:
	return formatdate(value, "d MMM yyyy")


def _range(figures: dict[str, Any]) -> str:
	"""`5 calendar days (21–25 Jul inclusive)`: the days counted, from the day after the due date to the event day."""
	days = cint(figures["days"])
	first, last = getdate(figures["due"]), getdate(figures["event"])
	from frappe.utils import add_days

	start = add_days(first, 1)
	span = f"{start.day}–{last.day} {last.strftime('%b')}" if start.month == last.month else f"{_day(start)} – {_day(last)}"
	return f"{days} calendar day{'s' if days != 1 else ''} ({span} inclusive)"


def _calculation(ctx: Context, figures: dict[str, Any]) -> dict[str, Any]:
	extended = bool(figures.get("extensions"))
	due = f"{_day(figures['due'])} (effective extension)" if extended else _day(figures["due"])
	extra = [["Previous computation", f"{money(figures['prior']['amount'], figures['currency'])} — retained"]] if figures.get("prior") else [["Effective extension", "None"]]
	return kit.R("Calculation", kit.r(["Due date", due], ["Delivered", _day(figures["event"])], ["Days late", _range(figures)], ["Eligible principal", money(figures["principal"], figures["currency"])],
		["Rate", f"{figures['rate_percent']:g}% per day"], ["Cap", f"{figures['cap_percent']:g}% ({money(figures['cap'], figures['currency'])})"], *extra),
		kit.f(["Calculation", f"{money(figures['daily'], figures['currency'])} per day × {figures['days']}"], ["Proposed adjustment", money(figures["amount"], figures["currency"])]))


def _cause(row) -> dict[str, Any]:
	return kit.R("Causation and response", kit.r(["Causation", row.causation or "Not yet recorded"], ["Supplier challenge", row.supplier_response or "None recorded"]))


def _evidence(figures: dict[str, Any], row=None) -> list[str]:
	return [f"Delivery {_day(figures['event'])}", f"Clause {figures['clause']}" if figures.get("clause") else "Clause", "Supplier response 1"]


def propose(ctx: Context) -> dict[str, Any]:
	"""D36 / D36-E: the head of procurement reviews the proposed adjustment and submits it for decision, recording the causation, the clause and the supplier's response."""
	figures = adjustment.calculate(ctx.case)
	row = adjustment.live(ctx.case)
	cause = kit.R("Causation and response", kit.r(["Causation", row.causation if row else "To be recorded when you submit"], ["Supplier challenge", (row.supplier_response if row else "") or "To be recorded when you submit"]))
	if row is not None:
		figures = {**adjustment.calculation(row), **figures}
	b = chrome.base(ctx, "D36-E" if figures.get("extensions") or row is not None and adjustment.calculation(row).get("prior") else "D36", d="D36", name="Contractual delay adjustment", title="Review delivery delay", tab="Obligations",
		next=chrome.next_block(ctx), subj="All units accepted " + _day(figures["event"]), regions=[_calculation(ctx, figures), cause], p="Submit adjustment for decision", s2=[kit.disabled("Return for correction"), "View clause"],
		ev=_evidence(figures))
	b["actions"]["Submit adjustment for decision"] = kit.dialog("submit")
	b["actions"]["View clause"] = kit.tab("Agreement")
	b["dialogs"]["submit"] = kit.dlg("Submit adjustment for decision", [kit.fl(kit.tx("Causation", row.causation if row else "", "causation"), kit.tx("Clause the rate comes from", figures.get("clause", ""), "clause"),
		kit.ta("Supplier's challenge", row.supplier_response if row else "", "supplier_response"), kit.tx("Recommendation", "", "recommendation"))], "Submit", command="PrepareContractAdjustment", args={})
	return b


def decide(ctx: Context, row) -> dict[str, Any]:
	"""D36-A: the Accounting Officer's decision on the exact proposal."""
	figures = adjustment.calculation(row)
	b = chrome.base(ctx, "D36-A", d="D36", name="Contractual delay adjustment", title="Review delivery delay", tab="Obligations", next=chrome.next_block(ctx), subj="All units accepted " + _day(figures["event"]),
		regions=[_calculation(ctx, figures), _cause(row), kit.R("Recommendation", kit.r(["Technical/legal recommendation", figures.get("recommendation") or "Not recorded"]))], p="Approve adjustment", s2=["Decline", "Return for correction"],
		ev=_evidence(figures))
	args = {"adjustment": row.name}
	b["actions"]["Approve adjustment"] = kit.dialog("approve")
	b["actions"]["Decline"] = kit.dialog("decline")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["approve"] = kit.dlg("Approve adjustment", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractAdjustment", args={**args, "decision": "Approve"})
	b["dialogs"]["decline"] = kit.dlg("Decline adjustment", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractAdjustment", args={**args, "decision": "Decline"})
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm decision", command="DecideContractAdjustment", args={**args, "decision": "Return"})
	return b


def certification(ctx: Context, invoice, gross: float, row) -> dict[str, Any]:
	"""D36-S: the certification of an invoice that carries an authorised adjustment: gross, adjustment and proposed cash apart; Finance applies the adjustment through the reviewed native mapping."""
	figures = adjustment.calculation(row)
	cur = figures["currency"]
	b = chrome.base(ctx, "D36-S", d="D36", name="Contractual delay adjustment", title="Review invoice", tab="Invoices", next=chrome.next_block(ctx),
		regions=[kit.R("Certification", kit.t(["Supported gross", "Authorised adjustment", "Proposed cash"], [[money(gross, cur), money(row.amount, cur), money(gross - flt(row.amount), cur)]], [0, 1, 2]),
			kit.xh(f"Finance applies the adjustment through the reviewed native mapping; the invoice rate is not edited. The {money(row.amount, cur)} is a noncash adjustment, never cash."))],
		p="Sign certification", s2=["View calculation"], ev=_evidence(figures))
	b["actions"]["Sign certification"] = kit.command("SignContractCertification", invoice=invoice.name)
	b["actions"]["View calculation"] = kit.tab("Obligations")
	return b


def held(ctx: Context) -> dict[str, Any]:
	"""D36-H: the native deduction mapping is unverified, so payment of the affected invoice waits with its Finance owner."""
	row = adjustment.live(ctx.case) or adjustment.pending_application(ctx.case)[0]
	figures = adjustment.calculation(row)
	owner = ctx.name(next(iter(__import__("kentender_contracts.services.work", fromlist=["holders"]).holders("Finance preparation")), ""))
	b = chrome.base(ctx, "D36-H", d="D36", name="Contractual delay adjustment", title="Review delivery delay", tab="Obligations",
		next=kit.blk("This action is on hold.", owner, ["View calculation", "View issue"], "The native deduction mapping is not verified; payment is held."), subj="All units accepted " + _day(figures["event"]),
		regions=[_calculation(ctx, figures), _cause(row)], p="", s2=[], ev=_evidence(figures))
	b["actions"]["View calculation"] = b["actions"]["View issue"] = kit.tab("Obligations")
	return b


def is_held(case: str) -> bool:
	return any(h.key == "adjustment mapping" for h in holds.open_holds(case))
