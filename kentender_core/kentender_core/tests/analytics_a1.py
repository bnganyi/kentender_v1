"""ANL-CHG-001 v0.8 §10A.2 — dataset A1 (and its A2 view) as owner facts.

The illustrative design dataset, expressed in the provider contract
(`analytics_contract`). It is a *design* dataset, not installed records and not
seed data (ANL §13): core tests feed it to the workspace through a fake owner
so every pictured figure is proved without a database. Real-record proof is in
each owner's provider tests.

Read instant: 18 June 2027, 10:00 EAT.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal as D
from types import SimpleNamespace
from typing import Any, Iterator
from unittest.mock import patch

from kentender_core.services import analytics_contract as ac
from kentender_core.services import analytics_viewer as av
from kentender_core.services import analytics_workspace as aw

AT = datetime(2027, 6, 18, 10, 0)
FY = "FY-2027-28"
FY_OTHER = "FY-2026-27"
DH, HR, DIR, ROOT = "OU-DH", "OU-HR", "OU-DIR", "PE-MOH"
UNIT_NAMES = {DH: "Digital Health", HR: "Human Resources Management and Development", DIR: "Directorate of Digital Health and Policy", ROOT: "Ministry of Health"}
PLAN = "Ministry of Health Annual Procurement Plan"
PAGE_ROUTE = ["technical-search"]  # route_ok is patched; a real Page name keeps rows honest


def dt(day: int, month: int, hour: int = 10, minute: int = 0, year: int = 2027) -> datetime:
	return datetime(year, month, day, hour, minute)


def _route(*tail: str) -> list[str]:
	return [*PAGE_ROUTE, *tail]


def needs() -> list[dict[str, Any]]:
	def need(i, title, unit, hour):
		return ac.record(ac.NEEDS, id=i, title=title, reference=i, fiscal_year=FY, org_units=[unit], route=_route(i),
			state="Accepted for planning", state_key="accepted", accepted_at=datetime(2026, 11, 24, hour, 0), pending_successor=False)
	return [need("N-A", "Clinic equipment", DH, 11), need("N-B", "Office furniture", HR, 14)]


def plans() -> list[dict[str, Any]]:
	return [
		ac.record(ac.DEPARTMENTAL_PLANS, id="D-A", title="Digital Health departmental plan", fiscal_year=FY, org_units=[DH], route=_route("D-A"),
			state="Accepted", accepted_at=datetime(2026, 12, 2, 10, 0)),
		ac.record(ac.DEPARTMENTAL_PLANS, id="D-B", title="Human Resources Management and Development departmental plan", fiscal_year=FY,
			org_units=[HR], route=_route("D-B"), state="Accepted", accepted_at=datetime(2026, 12, 3, 10, 0)),
	]


# item, title, lead, allocations {unit: (planned, covered)}, invitation days, has proceeding
_ITEMS = [
	("I-A", "Clinic equipment", DH, {DH: (12_000_000, 0)}, None, False),
	("I-B", "IT peripherals", DH, {DH: (4_000_000, 4_000_000), HR: (2_500_000, 2_500_000)}, None, True),
	("I-C", "Network switches", HR, {HR: (9_000_000, 8_000_000)}, 25, True),
	("I-D", "Office desks", HR, {HR: (3_500_000, 3_500_000)}, 7, True),
	("I-E", "Printers", DH, {DH: (5_000_000, 5_000_000)}, -3, True),
	("I-F", "Monitors", HR, {HR: (7_500_000, 7_500_000)}, 0, True),
	("I-G", "Servers", DH, {DH: (25_000_000, 25_000_000)}, 7, True),
]


def plan_items() -> list[dict[str, Any]]:
	out = []
	for ident, title, lead, allocations, days, proceeding in _ITEMS:
		units = [lead] + [u for u in allocations if u != lead]
		out.append(ac.record(ac.PLAN_ITEMS, id=ident, title=title, fiscal_year=FY, org_units=units, route=_route(ident),
			planned_value=D(sum(p for p, _c in allocations.values())),
			allocations=[{"org_unit": u, "planned": D(p), "covered": D(c)} for u, (p, c) in allocations.items()],
			invitation_days=days, has_proceeding=proceeding, plan_title=PLAN, plan_version=1))
	return out


# id, title, state, value kind, lines {unit: amount}, submitted, authorised, consumed, tender number
_REQS = [
	("R-A", "Clinic equipment requisition", "Submitted to Procurement", ac.REQUESTED, {DH: 12_000_000}, dt(16, 6, 11), None, None, None),
	("R-B", "IT peripherals requisition", "Authorised", ac.AUTHORISED, {DH: 4_000_000, HR: 2_500_000}, dt(9, 3), dt(15, 3, 11), dt(16, 3, 9), "041"),
	("R-C", "Network switches requisition", "Authorised", ac.AUTHORISED, {HR: 8_000_000}, dt(8, 3), dt(15, 3, 11, 30), dt(19, 3, 9), "042"),
	("R-D", "Office desks requisition", "Authorised", ac.AUTHORISED, {HR: 3_500_000}, dt(3, 3), dt(15, 3, 12), dt(18, 3, 9), "043"),
	("R-E", "Printers requisition", "Authorised", ac.AUTHORISED, {DH: 5_000_000}, dt(2, 3), dt(12, 3, 11), dt(16, 3, 10), "044"),
	("R-F", "Monitors requisition", "Authorised", ac.AUTHORISED, {HR: 7_500_000}, dt(4, 3), dt(11, 3, 11), dt(16, 3, 11), "045"),
	("R-G", "Servers requisition", "Authorised", ac.AUTHORISED, {DH: 25_000_000}, dt(1, 3), dt(15, 3, 14), dt(17, 3, 9), "046"),
]


def requisitions() -> list[dict[str, Any]]:
	out = []
	for ident, title, state, kind, lines, sub, auth, cons, tender in _REQS:
		units = list(lines)
		out.append(ac.record(ac.REQUISITIONS, id=ident, title=title, fiscal_year=FY, org_units=units, route=_route(ident),
			state=state, value_kind=kind, value_lines=[ac.line(u, a) for u, a in lines.items()], submitted_at=sub, authorised_at=auth,
			consumed_at=cons, submission_events=[sub], authorisation_events=[auth] if auth else [],
			tender_reference=f"TND-MOH-2027-{tender}" if tender else "",
			outstanding=ac.outstanding("Awaiting authorisation by Charles Mutiso.", "Charles Mutiso", sub) if ident == "R-A" else None))
	return out


def _tender(num, title, units, bucket, position, req_lines, started, published, **over):
	base = dict(bucket=bucket, position=position, authorised_lines=[ac.line(u, a) for u, a in req_lines.items()], started_at=started,
		published_at=published, cancelled_at=None, opening_complete_at=None, report_sent_at=None, award_received_at=None, decision_at=None,
		decision_outcome=None, decision_events=[], award_amount=None, award_amount_visible=True, cancellation_events=[])
	base.update(over)
	return ac.record(ac.TENDERS, id=f"T-{num}", title=title, reference=f"TND-MOH-2027-{num}", fiscal_year=FY, org_units=units,
		route=_route(f"T-{num}"), **base)


def tenders() -> list[dict[str, Any]]:
	return [
		_tender("041", "Supply of IT peripherals", [DH, HR], ac.PREPARATION, "Tender preparation — warranty requirement returned for correction",
			{DH: 4_000_000, HR: 2_500_000}, dt(16, 3, 9), None, outstanding=ac.outstanding(
				"State the warranty period required from suppliers. Awaiting correction by Brian Wafula.", "Brian Wafula", dt(16, 6, 9))),
		_tender("042", "Supply of network switches", [HR], ac.OPEN, "Open for bids", {HR: 8_000_000}, dt(19, 3, 9), dt(14, 5)),
		_tender("043", "Supply of office desks", [HR], ac.EVALUATION, "Evaluation — automatic checks complete; committee review outstanding",
			{HR: 3_500_000}, dt(18, 3, 9), dt(16, 4), opening_complete_at=dt(3, 6), outstanding=ac.outstanding(
				"Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.", "Grace Wambui", dt(3, 6))),
		_tender("044", "Supply of printers", [DH], ac.AWARD, "Award — professional opinion outstanding", {DH: 5_000_000}, dt(16, 3, 10), dt(9, 4),
			opening_complete_at=dt(10, 5, 12), report_sent_at=dt(16, 6, 14, 7), award_received_at=dt(16, 6, 14, 7),
			outstanding=ac.outstanding("Awaiting professional opinion by Charles Mutiso.", "Charles Mutiso", dt(16, 6, 14, 7))),
		_tender("045", "Supply of monitors", [HR], ac.AWARD, "Award — required bidder notices awaiting delivery", {HR: 7_500_000}, dt(16, 3, 11), dt(6, 4),
			opening_complete_at=dt(7, 5, 12), report_sent_at=dt(4, 6, 15), award_received_at=dt(4, 6, 15), decision_at=dt(17, 6, 11),
			decision_outcome=ac.OUTCOME_AWARD, decision_events=[dt(17, 6, 11)], award_amount=D(7_185_000),
			outstanding=ac.outstanding("Award decision recorded. Required bidder notices are awaiting delivery.", "", dt(17, 6, 11))),
		_tender("046", "Supply of servers", [DH], ac.CLOSED, "Closed — cancelled; cancellation compliance evidence complete", {DH: 25_000_000},
			dt(17, 3, 9), dt(12, 4), cancelled_at=dt(16, 6, 12), cancellation_events=[dt(16, 6, 12)]),
	]


def funding(view: str = "whole") -> dict[str, Any]:
	lines = [
		{"label": "ICT equipment for Digital Health", "owner_org_unit": DH, "registered": D(60_000_000), "reserved": D(9_000_000), "committed": D(0), "available": D(51_000_000)},
		{"label": "Office equipment for Human Resources Management and Development", "owner_org_unit": HR, "registered": D(30_000_000), "reserved": D(13_500_000), "committed": D(0), "available": D(16_500_000)},
		{"label": "Ministry-wide ICT infrastructure", "owner_org_unit": "", "registered": D(60_000_000), "reserved": D(33_000_000), "committed": D(0), "available": D(27_000_000)},
	]
	own = {DH: "ICT equipment for Digital Health", HR: "Office equipment for Human Resources Management and Development"}
	rows = [("R-B DH", DH, DH, 4_000_000), ("R-B HR", HR, HR, 2_500_000), ("R-C", HR, "", 8_000_000), ("R-D", HR, HR, 3_500_000),
		("R-E", DH, DH, 5_000_000), ("R-F", HR, HR, 7_500_000), ("R-G", DH, "", 25_000_000)]
	reservations = [{"source_org_unit": src, "line_owner_org_unit": owner, "reserved": D(amount), "committed": D(0)} for _n, src, owner, amount in rows]
	if view == "department":
		lines = [l for l in lines if l["owner_org_unit"] in (HR,)]
		reservations = [r for r in reservations if r["source_org_unit"] == HR]
	return ac.funding(fiscal_year=FY, budget_title="Ministry of Health procurement budget FY 2027/28", version=1, as_at=AT, lines=lines,
		reservations=reservations, view=view)


class A1:
	"""A fake owner serving A1. ``audience`` ``site`` serves everything; ``hr``
	serves the HRMD-attributed part with no award amount (dataset A2)."""

	def __init__(self, audience: str = "site", *, kinds: set[str] | None = None, fail: set[str] | None = None, extra: dict[str, dict] | None = None,
			funding_view: str = "whole") -> None:
		self.audience, self.fail, self.extra, self.funding_view = audience, fail or set(), extra or {}, funding_view
		self.kinds = kinds if kinds is not None else {ac.NEEDS, ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS, ac.REQUISITIONS, ac.TENDERS, ac.FUNDING}
		self.calls: list[str] = []
		self.__name__ = "a1"

	def applies(self, *, user, at):
		return set(self.kinds)

	def facts(self, *, user, kind, at, **params):
		self.calls.append(kind)
		if kind in self.fail:
			raise RuntimeError(f"{kind} read failed")
		if kind == ac.FUNDING:
			return funding(self.funding_view)
		records = {ac.NEEDS: needs, ac.DEPARTMENTAL_PLANS: plans, ac.PLAN_ITEMS: plan_items, ac.REQUISITIONS: requisitions, ac.TENDERS: tenders}[kind]()
		if self.audience == "hr":
			records = [r for r in records if HR in r["org_units"]]
			for r in records:
				if kind == ac.TENDERS:
					r["award_amount"], r["award_amount_visible"] = None, False
		return {"records": records, **self.extra.get(kind, {})}


CHARLES = {"internal": True, "technical": False, "site_wide": True, "units": None}
DANIEL = {"internal": True, "technical": True, "site_wide": True, "units": None}
PETER = {"internal": True, "technical": False, "site_wide": False, "units": {DIR, DH, HR}}
OUTSIDER = {"internal": False, "technical": False, "site_wide": False, "units": set()}


@contextmanager
def world(viewer: dict[str, Any]) -> Iterator[None]:
	"""Doubles for the lookups that need Organisation Unit, Fiscal Year and Page
	records, so the engine runs on A1 without a database."""
	units = {DH: {DH}, HR: {HR}, DIR: {DIR, DH}}
	with patch.object(av, "describe", lambda user, at: viewer), \
		patch.object(av, "unit_label", lambda u: UNIT_NAMES.get(u, u)), \
		patch.object(av, "unit_labels", lambda us: {u: UNIT_NAMES.get(u, u) for u in us}), \
		patch.object(av, "fiscal_year_labels", lambda ns: {n: {FY: "FY 2027/28", FY_OTHER: "FY 2026/27"}.get(n, n) for n in ns}), \
		patch.object(av, "fiscal_year_exists", lambda n: n in (FY, FY_OTHER)), \
		patch.object(av, "selectable_unit", lambda u, v: u in UNIT_NAMES and u != ROOT and (v["units"] is None or u in v["units"])), \
		patch.object(av, "unit_scope", lambda u: units.get(u, {u})), \
		patch.object(av, "root_units", lambda: {ROOT}), \
		patch.object(aw._Ctx, "route_ok", lambda self, route: bool(route)):
		yield


def read(viewer, provider=None, **kwargs) -> dict[str, Any]:
	"""One Analytics read on A1 as ``viewer`` at the pictured instant."""
	provider = provider or A1()
	with world(viewer):
		return aw.get_workspace("test@example.test", providers=[provider], at=AT, **kwargs)
