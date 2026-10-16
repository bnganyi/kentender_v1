# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""How an independently registered contract is funded, as a board (CM-CHG-001 v0.10 sections 10.9, 20.4, 20.4A; boards D12-F, D21-F, D21-A).

One board, on the agreement tab at `agreement/funding`, drawn from the contract's own funding record (`services/contract_funding.py`) and nothing else: the head of procurement records the route and the
year shares, Finance preparation prepares a year's basis, Finance approval confirms it (never the same person for the same figures), and the head raises the one request per year. Each action a person
sees is one they may take now; the service checks again. The words are the specification's: **Year allocation required**, **Funding entry pending**, **Funding entry approved**, **Funding shortfall**,
**Already covered - no new entry required**, **No charge to this year**, **Future funding not yet confirmed**, **Funding scope needs review**, **Funding not confirmed**, **Funded outside KenTender Budget**
and **Not linked to KenTender Budget**. Supplier and public projections never see this board: it is internal."""

from __future__ import annotations

from typing import Any

from kentender_contracts.boards import chrome, kit
from kentender_contracts.boards.context import Context
from kentender_contracts.services import contract_funding as funding
from kentender_contracts.services import people, work
from kentender_core.services import contract_funding_request_contract as seam

BOARD = "D21-F"
SHARES = 4  # year shares a route dialog offers; the head can record the rest on a later change of route


OPEN = "Open funding review"


def visible(ctx: Context) -> bool:
	"""Funding is internal to the contract's own people (CM-CHG-001 v0.10 section 10.9): never a supplier's or the public's. It is drawn for an independently registered contract to those who prepare it, to Finance and to any
	internal reader once the route is recorded."""
	if ctx.doc.source_kind != "External record" or not [a for a in ctx.audiences if a != "supplier"]:
		return False
	return bool(ctx.doc.funding_route or ctx.can_prepare or people.holds(ctx.user, "Finance preparation") or people.holds(ctx.user, "Finance approval"))


def holder_name(ctx: Context, year: str) -> str:
	"""Who has the next step toward a year's funding: Finance approval until the basis is confirmed, the head until the request is raised, Budget's Officer while it is open."""
	rec = funding.get_record(ctx.case, year) if year else None
	if rec is not None and rec.request_state == "Open":
		return "Budget Officer"
	holders = work.holders(work.HOP) if rec is not None and funding.confirmed(rec) else work.holders("Finance approval")
	return ctx.name(next(iter(holders), "")) if holders else ""


def held_block(ctx: Context, hold) -> dict[str, Any]:
	"""The next-step reason on a payment screen whose payment is held for funding: the exact words, the holder and the way to the funding review (CM-CHG-001 v0.10 section 10.9, D09-F / D17)."""
	year = hold.key.rsplit(":", 1)[-1] if hold.key.rsplit(":", 1)[-1][:1].isdigit() else funding.current_year()
	return kit.blk(hold.reason, holder_name(ctx, year), [OPEN], hold.clearing)


def summary_region(ctx: Context) -> dict[str, Any]:
	"""The Funding section of the existing intake and opening screens: the route, what the funding is called and each year's position, read from the contract's own funding record."""
	view = funding.view(ctx.case)
	currency = ctx.doc.currency or "KES"
	rows = [["Funding route", view["route"] or "Not yet recorded"], ["Funding", view["label"] or ("Funding not confirmed" if not view["route"] else "By year, below")]]
	for y in view["years"]:
		rows.append([f"{y['year']}{' (this year)' if y['current'] else ''}", f"{y['label']}" + (f" — {_money(y['charge'], currency)}" if y["confirmed"] else "")])
	return kit.R("Funding", kit.r(*rows))


def attach(ctx: Context, board: dict[str, Any]) -> None:
	"""Add the Funding section to an existing screen (D12 intake, D21 opening review) with the one way into the full funding view. The screen's own primary action is never touched."""
	if not visible(ctx):
		return
	board["regions"].insert(1, summary_region(ctx))
	board["actions"][OPEN] = kit.route(ctx.case, "invoices" if board.get("tab") == "Invoices" else "agreement", "funding")
	board["s2"] = [*board.get("s2", []), OPEN]


def _money(text: str, currency: str) -> str:
	if not text:
		return "—"
	whole, _, fraction = text.partition(".")
	grouped = f"{int(whole):,}"
	return f"{currency} {grouped}{'' if not fraction.strip('0') else '.' + fraction}"


def _year_options(ctx: Context, view: dict[str, Any]) -> list[str]:
	return [y["year"] for y in view["years"]]


def _eligible(year: dict[str, Any], current: str) -> bool:
	"""May the head raise the request for this year now? Always for the current year or an earlier one; a later year only when its Budget is Active - a calendar date alone grants no funding."""
	if year["year"] <= (current or year["year"]):
		return True
	try:
		status = seam.year_status(year["year"])
	except Exception:
		status = None
	return bool(status and status.get("active"))


def _route_dialog(board: dict[str, Any], view: dict[str, Any], years: list[str]) -> None:
	authority = view.get("authority") or {}
	schedule = []
	for number in range(1, SHARES + 1):
		shown = view["years"][number - 1] if number <= len(view["years"]) else {}
		schedule.append(kit.fl(kit.sel(f"Year {number}", shown.get("year", "Select"), ["Select", *years] if years else ["Select"], f"schedule.{number}.year"),
			kit.tx(f"Share of year {number}", shown.get("schedule_amount", ""), f"schedule.{number}.amount")))
	board["dialogs"]["route"] = kit.dlg("Record how this contract is funded", [
		kit.fl(kit.sel("Funding route", view["route"] or "Select", ["Select", funding.ROUTE_BUDGET, funding.ROUTE_OUTSIDE], "route"),
			kit.tx("Responsible funding authority", authority.get("authority", ""), "authority"), kit.tx("Approved amount", authority.get("approved_amount", ""), "approved_amount"),
			kit.wide(kit.ta("Evidence of the authority (one reference per line)", "\n".join(authority.get("evidence") or []), "evidence"))),
		*schedule, kit.xh("The year shares come from the signed terms. A year with no share here is not funded."),
	], "Record funding route", command="RecordContractFundingRoute", args={})
	board["actions"]["Record funding route"] = kit.dialog("route")


def _basis_dialog(board: dict[str, Any], key: str, title: str, command: str, year: str, charge: str = "", explanation: str = "", evidence: list[str] | None = None, primary: str = "") -> None:
	board["dialogs"][key] = kit.dlg(title, [kit.fl(kit.tx("Funding charge for the year", charge, "charge"), kit.wide(kit.ta("How the charge was reached", explanation, "explanation")),
		kit.wide(kit.ta("Evidence (one reference per line)", "\n".join(evidence or []), "evidence"))),
		kit.xh("The charge is the gross funding control charge for the year: work performed and paid on the confirmed basis plus the supported remaining obligation. Dates alone, equal splits and the unpaid balance are not a basis.")],
		primary or title, command=command, args={"year": year})
	board["actions"][title] = kit.dialog(key)


def d21f(ctx: Context) -> dict[str, Any]:
	view = funding.view(ctx.case)
	currency = ctx.doc.currency or "KES"
	route = view["route"]
	hop, prep, approval = (people.holds(ctx.user, work.HOP), people.holds(ctx.user, "Finance preparation"), people.holds(ctx.user, "Finance approval"))
	years = _year_options(ctx, view)
	current = next((y["year"] for y in view["years"] if y["current"]), "")
	authority = view.get("authority") or {}
	facts = kit.r(["Funding route", route or "Not yet recorded"], ["Funding", view["label"] or ("Funding not confirmed" if not route else "By year, below")],
		["Responsible authority", authority.get("authority") or "—"], ["Authority evidence", ", ".join(authority.get("evidence") or []) or "—"])
	table = kit.t(["Year", "Share in the signed terms", "Confirmed charge", "Funding", "Confirmed by"],
		[[f"{y['year']}{' (this year)' if y['current'] else ''}", _money(y["schedule_amount"], currency), _money(y["charge"], currency) if y["confirmed"] else "Not confirmed", f"!{y['label']}",
			ctx.name(y["confirmed_by"]) if y["confirmed_by"] else "—"] for y in view["years"]], num=(1, 2)) if view["years"] else kit.xh("No financial year is recorded for this contract yet.")
	regions = [kit.R("How this contract is funded", facts), kit.R("Funding by year", table)]
	if view["held"]:
		regions.append(kit.R("Held until funded", kit.r(*[[reason, "Facts, claims, evidence and existing liabilities can still be recorded."] for reason in sorted(set(view["held"]))])))
	waiting = next((y for y in view["years"] if y["label"] == funding.S_YEAR_REQUIRED and not y["confirmed"]), None)
	if waiting and route == funding.ROUTE_BUDGET:
		holder = next(iter(work.holders("Finance approval")), "")
		regions.append(kit.R("Waiting for Finance", kit.r(["Status", funding.S_YEAR_REQUIRED], ["Holder", ctx.name(holder) if holder else "—"], ["Responsibility", "Finance approval"],
			["Where", "This contract's opening review"])))
	headline = "Record how this contract is funded." if not route and hop else "Review how this contract is funded."
	board = chrome.base(ctx, BOARD, d="D21", name="Contract funding", title="Contract funding", tab="Agreement", next=chrome.next_block(ctx) or kit.turn(headline, ctx.name(ctx.user)), regions=regions, p="", s2=[], ev=[])

	secondary: list[str] = []
	if hop:
		_route_dialog(board, view, years)
		secondary.append("Record funding route")
		if route == funding.ROUTE_BUDGET:
			for y in view["years"]:
				if y["request_state"] in ("Not requested", "Declined", "Withdrawn") and _eligible(y, current):
					first = not any(o["request_state"] in ("Open", "Completed") for o in view["years"] if o["year"] != y["year"])
					label = f"Request funding for {y['year']}" if first else f"Request annual funding for {y['year']}"
					board["actions"][label] = kit.command("RequestExistingContractFunding", year=y["year"])
					secondary.append(label)
				if y["request_state"] == "Open":
					label = f"Withdraw the request for {y['year']}"
					board["dialogs"][f"withdraw-{y['year']}"] = kit.dlg(label, [kit.fl(kit.wide(kit.ta("Why the request is withdrawn", "", "reason")))], "Withdraw request", command="WithdrawContractFundingRequest", args={"year": y["year"]})
					board["actions"][label] = kit.dialog(f"withdraw-{y['year']}")
					secondary.append(label)
	if prep and route:
		for y in view["years"]:
			if y["request_state"] in ("Not requested", "Open"):
				_basis_dialog(board, f"prepare-{y['year']}", f"Prepare the funding basis for {y['year']}", "PrepareContractFundingBasis", y["year"], y["charge"])
				secondary.append(f"Prepare the funding basis for {y['year']}")
	primary = ""
	if approval and route:
		for y in view["years"]:
			if y["request_state"] in ("Not requested", "Open") and not y["confirmed"] and (y["charge"] or y["year"] <= (current or y["year"])):
				label = f"Confirm the funding basis for {y['year']}"
				if y["charge"]:
					board["actions"][label] = kit.command("ConfirmContractFundingEvidence", year=y["year"])
				else:
					_basis_dialog(board, f"confirm-{y['year']}", label, "ConfirmContractFundingEvidence", y["year"], primary="Confirm funding basis")
				primary = primary or label
				secondary.append(label)
	board["p"], board["s2"] = primary, [s for s in secondary if s != primary]
	return board
