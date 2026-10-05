"""ANL-CHG-001 v0.8 §7 — `GetProcurementAnalytics`: Analytics' one read.

Core cannot import an owner module, so owners register a provider on the
`kt_analytics_providers` hook (see `analytics_contract`). For the selected tab
this module reads the fact kinds the tab needs, filters them by Financial year
and department, and computes every figure the page shows: counts, state
splits, waiting bands, month series, step medians, coverage, value totals, the
funding position, every label and every page of rows (ANL §4A, §5.4, §5.5).
The browser draws what it is given and computes nothing (ANL §16).

A failed provider is never a zero: its area reads *unavailable* with the §8
text and the other areas keep their values; an incomplete read shows the
figures it has plus the stated sentence and no percentage (plan D4). Nothing
here creates, marks or stores anything (ANL §16).

Payload (JSON-safe; every text is final)::

	verdict       "ok" | "no_area" | "denied" | "failed"
	message       the §8 text for a non-ok verdict, or ""
	title, description, updated, scope, read_at (UTC ISO)
	tab           "overview" | "needs" | "departmental-planning" | "annual-planning" | "requisitions" | "tender-proceedings"
	tabs          [{key, label, icon, route, selected}]
	filters       {fy, dept, state, fy_options, dept_options, messages, applied}
	empty         true when a permitted selection holds no records (ANL-DES-31B)
	overview      {strip, waiting, coverage, steps, funding}     (tab overview)
	area          {...}                                          (an area tab)
	definitions   the "How these figures are counted" text

Each region carries ``status`` ("ok" | "unavailable" | "incomplete"), and the
text the page shows for the other two.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

import frappe
from frappe import _
from frappe.core.doctype.page.page import get_custom_allowed_roles
from frappe.utils import cstr

from kentender_core.services import analytics_contract as ac
from kentender_core.services import analytics_measures as am
from kentender_core.services import analytics_viewer as av
from kentender_core.services import home_time as ht
from kentender_core.utils.instants import to_utc_iso

PAGE_SIZE = 10
_LOG = "kentender.analytics"

DENIED = "No Analytics records are available to your responsibilities."
FAILED = "Analytics could not be loaded."
NO_RECORDS = "No records are available in this selection."
NO_MATCH = "No records match these filters."
INCOMPLETE = "Some records could not be included, so these figures may be incomplete."
NO_STEPS = "No completed steps in these 12 months."
NO_EVENTS = "Nothing was recorded in these 12 months."
NO_OUTSTANDING = "No outstanding matters recorded"
FUNDING_CHOOSE = "Choose a financial year to see its funding position."
STRIP_NOTE = "These counts describe different records and are not added together."

NEEDS_STATES = ["Submitted", "Returned", "Accepted for planning", "Not taken forward"]
REQ_STATES = ["Draft", "Awaiting Department Approval", "Submitted to Procurement", "Returned", "Authorised",
	"Upstream correction required", "Revoked", "Withdrawn"]
DPP_STATES = ["Accepted"]

BUCKET_LABEL = {
	ac.PREPARATION: "Tender preparation and publication", ac.OPEN: "Open for bids", ac.OPENING: "Opening",
	ac.EVALUATION: "Evaluation", ac.AWARD: "Award", ac.CONTRACT: "Sent to Contract Management", ac.CLOSED: "Closed",
	ac.UNAVAILABLE: "Status unavailable",
}
BUCKET_SHORT = {
	ac.PREPARATION: "Preparation", ac.OPEN: "Open", ac.OPENING: "Opening", ac.EVALUATION: "Evaluation", ac.AWARD: "Award",
	ac.CONTRACT: "Sent to Contract Management", ac.CLOSED: "Closed", ac.UNAVAILABLE: "Status unavailable",
}

# area key, tab route key, label, icon, fact kind, singular/plural unit, strip link label, search label
AREAS: list[dict[str, Any]] = [
	{"key": "needs", "tab": "needs", "label": "Needs", "icon": "needs", "kind": ac.NEEDS, "one": "Need", "many": "Needs",
		"link": "View Needs", "search": "Search Need", "footer": "Needs"},
	{"key": "departmental_planning", "tab": "departmental-planning", "label": "Departmental planning", "icon": "departmental-planning",
		"kind": ac.DEPARTMENTAL_PLANS, "one": "departmental plan", "many": "departmental plans", "link": "View departmental planning",
		"search": "Search departmental plan", "footer": "departmental plans"},
	{"key": "annual_planning", "tab": "annual-planning", "label": "Annual planning", "icon": "annual-planning", "kind": ac.PLAN_ITEMS,
		"one": "Plan item in the Active Plan", "many": "Plan items in the Active Plan", "link": "View annual planning",
		"search": "Search Plan item", "footer": "Plan items"},
	{"key": "requisitions", "tab": "requisitions", "label": "Requisitions", "icon": "requisitions", "kind": ac.REQUISITIONS,
		"one": "Requisition", "many": "Requisitions", "link": "View Requisitions", "search": "Search Requisition", "footer": "Requisitions"},
	{"key": "tender_proceedings", "tab": "tender-proceedings", "label": "Tender proceedings", "icon": "tender-proceedings",
		"kind": ac.TENDERS, "one": "Tender", "many": "Tenders", "link": "View Tender proceedings",
		"search": "Search Tender or reference", "footer": "Tenders"},
]
AREA_BY_TAB = {area["tab"]: area for area in AREAS}
TABS = ["overview"] + [area["tab"] for area in AREAS]

STEPS = [
	{"key": "T1", "label": "Requisition submitted to authorised", "kind": ac.REQUISITIONS, "start": "submitted_at", "end": "authorised_at"},
	{"key": "T2", "label": "Requisition authorised to Tender started", "kind": ac.REQUISITIONS, "start": "authorised_at", "end": "consumed_at"},
	{"key": "T3", "label": "Tender started to published", "kind": ac.TENDERS, "start": "started_at", "end": "published_at"},
	{"key": "T4", "label": "Bid opening complete to evaluation report sent", "kind": ac.TENDERS, "start": "opening_complete_at", "end": "report_sent_at"},
	{"key": "T5", "label": "Evaluation report sent to AO decision recorded", "kind": ac.TENDERS, "start": "award_received_at", "end": "decision_at"},
]
TAB_STEPS = {"overview": ["T1", "T2", "T3", "T4", "T5"], "requisitions": ["T1", "T2"], "tender-proceedings": ["T2", "T3", "T4", "T5"]}

DEFINITIONS = (
	"Each area counts its own permitted records once. Financial year follows the record's Planning source, not its creation date. "
	"Annual planning counts items in the Active Plan. Versions and contributing departments do not add records. "
	"An award decision does not mean notices or contract work are complete. Waiting time runs from when a matter reached its current "
	"holder; it is not a judgement that work is late. Time between key steps counts calendar days between recorded events completed "
	"in the 12 months to {window_end}; these are not statutory periods. Plan coverage uses the Annual Plan's own record of value "
	"covered by authorised requisitions. Amounts are in Kenya shillings, and different kinds of amount are never added together. "
	"Counts and positions describe current position when loaded."
)


def _slug(text: str) -> str:
	return re.sub(r"[^a-z0-9]+", "_", cstr(text).lower()).strip("_")


# --------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------


def _resolve(providers: list[Any] | None) -> list[tuple[str, Any]]:
	"""(name, module or the Exception that stopped it loading). A module with
	no hook has no row; one configured but unloadable is a failure."""
	if providers is not None:
		return [(getattr(p, "__name__", f"provider-{i}"), p) for i, p in enumerate(providers)]
	resolved: list[tuple[str, Any]] = []
	for path in frappe.get_hooks(ac.HOOK) or []:
		try:
			resolved.append((path, frappe.get_module(path)))
		except Exception as error:
			frappe.logger(_LOG).error("analytics provider could not load | provider=%s", path, exc_info=True)
			resolved.append((path, error))
	return resolved


def _applies(resolved: list[tuple[str, Any]], user: str, at: datetime) -> tuple[dict[str, set[str]], int]:
	"""{provider name: kinds it serves this actor}, and the number that failed."""
	out: dict[str, set[str]] = {}
	failed = 0
	for name, provider in resolved:
		if isinstance(provider, Exception):
			failed += 1
			continue
		try:
			out[name] = set(provider.applies(user=user, at=at) or ())
		except Exception:
			frappe.logger(_LOG).error("analytics provider failed | provider=%s step=applies", name, exc_info=True)
			failed += 1
	return out, failed


class _Read:
	"""One kind read across every provider that serves it."""

	def __init__(self) -> None:
		self.status = "na"  # na | ok | failed
		self.records: list[dict[str, Any]] = []
		self.incomplete = False
		self.unavailable_measures: set[str] = set()
		self.identity_incomplete = False
		self.extra: dict[str, Any] = {}

	@property
	def ok(self) -> bool:
		return self.status == "ok"


def _read_kind(resolved, served: dict[str, set[str]], user: str, kind: str, at: datetime, **params: Any) -> _Read:
	read = _Read()
	answered = failed = 0
	seen: set[str] = set()
	for name, provider in resolved:
		if kind not in served.get(name, set()):
			continue
		try:
			result = provider.facts(user=user, kind=kind, at=at, **params)
			if not isinstance(result, dict):
				raise TypeError(f"{name} returned {type(result).__name__} for {kind}")
			if kind == ac.FUNDING:
				read.extra.update(result)
				answered += 1
				continue
			for rec in result.get("records") or []:
				try:
					ac.validate(rec)
				except ValueError:
					frappe.logger(_LOG).error("analytics record dropped | provider=%s kind=%s", name, kind, exc_info=True)
					read.incomplete = True
					continue
				if rec["id"] in seen:
					continue
				seen.add(rec["id"])
				read.records.append(rec)
			read.incomplete = read.incomplete or bool(result.get("incomplete"))
			read.identity_incomplete = read.identity_incomplete or bool(result.get("identity_incomplete"))
			read.unavailable_measures |= set(result.get("unavailable_measures") or ())
			answered += 1
		except Exception:
			frappe.logger(_LOG).error("analytics provider failed | provider=%s kind=%s", name, kind, exc_info=True)
			failed += 1
	if failed and not answered:
		read.status = "failed"
	elif answered:
		read.status = "ok"
		read.incomplete = read.incomplete or bool(failed)
	return read


# --------------------------------------------------------------------------
# Context
# --------------------------------------------------------------------------


class _Ctx:
	def __init__(self, user: str, at: datetime, viewer: dict[str, Any]) -> None:
		self.user, self.at, self.viewer = user, at, viewer
		self.fy = ""
		self.dept = ""
		self.units: set[str] | None = None  # an explicitly selected department with its descendants
		self.scope_units: set[str] | None = None  # the units whose share every value shows (selection, else the viewer's permitted set)
		self.state = ""
		self.search = ""
		self.reads: dict[str, _Read] = {}
		self.labels: dict[str, str] = {}
		self.fy_labels: dict[str, str] = {}
		self.served: set[str] = set()
		self._routes: dict[str, bool] = {}

	def unit_name(self, unit: str) -> str:
		if unit not in self.labels:
			self.labels[unit] = av.unit_label(unit)
		return self.labels[unit]

	def records(self, kind: str) -> list[dict[str, Any]]:
		read = self.reads.get(kind)
		if not read or not read.ok:
			return []
		out = []
		for rec in read.records:
			if self.fy and rec["fiscal_year"] != self.fy:
				continue
			if self.units is not None and not (set(rec["org_units"]) & self.units):
				continue
			out.append(rec)
		return out

	def share(self, lines: list[dict[str, Any]]) -> Decimal:
		return sum((l["amount"] for l in lines if self.scope_units is None or l["org_unit"] in self.scope_units), Decimal(0))

	def whole(self, lines: list[dict[str, Any]]) -> Decimal:
		return sum((l["amount"] for l in lines), Decimal(0))

	def route_ok(self, route: list[str]) -> bool:
		if not route or not all(isinstance(s, str) and s for s in route):
			return False
		root = route[0]
		if root not in self._routes:
			allowed = set(frappe.get_all("Has Role", filters={"parent": root, "parenttype": "Page"}, pluck="role"))
			allowed.update(get_custom_allowed_roles("page", root))
			self._routes[root] = bool(frappe.db.exists("Page", root)) and (not allowed or bool(allowed & set(frappe.get_roles(self.user))))
		return self._routes[root]


def _kinds_for(tab: str, served: set[str]) -> list[str]:
	if tab == "overview":
		wanted = [a["kind"] for a in AREAS]
	elif tab == "tender-proceedings":
		wanted = [ac.TENDERS, ac.REQUISITIONS]
	else:
		wanted = [AREA_BY_TAB[tab]["kind"]]
	return [k for k in wanted if k in served]


# --------------------------------------------------------------------------
# Small builders
# --------------------------------------------------------------------------


def _text(value: str, secondary: str = "", *, quiet: bool = False) -> dict[str, Any]:
	return {"text": value, "secondary": secondary, "quiet": quiet}


# One colour per meaning, stable between the strip and the chart (ANL §10A.1 rule 3). The categorical set has six
# colours; a seventh and later category, and a Tender that is closed or has no status, read in the muted tone.
BUCKET_TONE = {ac.PREPARATION: "cat-1", ac.OPEN: "cat-2", ac.OPENING: "cat-3", ac.EVALUATION: "cat-4", ac.AWARD: "cat-5",
	ac.CONTRACT: "cat-6", ac.CLOSED: "muted", ac.UNAVAILABLE: "muted"}
COVERAGE_TONE = {"full": "pair-strong", "partly": "pair-mid", "not": "pair-tint"}


def _tone(index: int) -> str:
	return f"cat-{index + 1}" if index < 6 else "muted"


def _plural_unit(area: dict[str, Any], n: int) -> str:
	return area["one"] if n == 1 else area["many"]


def _waiting_badge(days: int) -> str:
	return f"Waiting {days} day" if days == 1 else f"Waiting {days} days"


def _since_text(value: datetime) -> str:
	return f"since {value.day} {value:%B}, {value:%H:%M}"


def _state_options(area: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, str]]:
	"""The area's present states, in the owner's order, for the state select."""
	if area["key"] == "tender_proceedings":
		present = {r["bucket"] for r in records}
		return [{"key": b, "label": BUCKET_LABEL[b]} for b in ac.BUCKETS if b in present]
	labels = _state_labels(area, records)
	return [{"key": _slug(label), "label": label} for label in labels]


def _static_states(area: dict[str, Any]) -> list[str]:
	return {"needs": NEEDS_STATES, "requisitions": REQ_STATES, "departmental_planning": DPP_STATES}.get(area["key"], [])


def _state_labels(area: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
	"""Distinct current-state labels present, known states first in owner order."""
	present = {r["state"] for r in records if r.get("state")}
	order = _static_states(area)
	labels = [s for s in order if s in present]
	return labels + sorted(present - set(order))


def _record_state_key(area: dict[str, Any], rec: dict[str, Any]) -> str:
	return rec["bucket"] if area["key"] == "tender_proceedings" else _slug(rec.get("state", ""))


def _valid_state(area: dict[str, Any], state: str) -> bool:
	if not state:
		return True
	if area["key"] == "tender_proceedings":
		return state in ac.BUCKETS
	if area["key"] == "annual_planning":
		return False
	return state in {_slug(s) for s in _static_states(area)}


def _distribution(area: dict[str, Any], records: list[dict[str, Any]], *, short: bool = True) -> list[dict[str, Any]]:
	"""§4A ANL-M-01: each record is classified once; segments add up to the count."""
	key = area["key"]
	if key == "tender_proceedings":
		counts = {b: sum(1 for r in records if r["bucket"] == b) for b in ac.BUCKETS}
		return [{"key": b, "label": (BUCKET_SHORT if short else BUCKET_LABEL)[b], "count": n, "tone": BUCKET_TONE[b]}
			for b, n in counts.items() if n]
	if key == "annual_planning":
		return []  # filled by coverage states
	labels = _state_labels(area, records)
	return [{"key": _slug(label), "label": label, "count": sum(1 for r in records if r["state"] == label), "tone": _tone(i)}
		for i, label in enumerate(labels)]


def _coverage_state(planned: Decimal, covered: Decimal) -> str:
	if planned > 0 and covered >= planned:
		return "full"
	return "partly" if covered > 0 else "not"


COVERAGE_STATES = [("full", "Fully covered"), ("partly", "Partly covered"), ("not", "Not covered")]


def _item_values(ctx: _Ctx, rec: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
	"""(planned, covered, whole planned) in the department's share when one is selected."""
	allocations = rec["allocations"]
	whole = rec["planned_value"]
	mine = allocations if ctx.scope_units is None else [a for a in allocations if a["org_unit"] in ctx.scope_units]
	# Covered never exceeds planned on an allocation, so "Fully covered" means equal (ANL-M-07).
	covered = sum((min(a["covered"], a["planned"]) for a in mine), Decimal(0))
	planned = whole if ctx.scope_units is None else sum((a["planned"] for a in mine), Decimal(0))
	return planned, covered, whole


def _plan_items(ctx: _Ctx) -> list[dict[str, Any]]:
	"""Plan items in the filtered scope, with the values the selection uses
	(ANL-M-06, M-07). A department selection uses only that department's
	allocations, for both value and state."""
	out = []
	for rec in ctx.records(ac.PLAN_ITEMS):
		planned, covered, whole = _item_values(ctx, rec)
		out.append({"rec": rec, "planned": planned, "covered": covered, "whole": whole,
			"state": _coverage_state(planned, covered), "shared": ctx.scope_units is not None and whole != planned})
	return out


def _area_segments(ctx: _Ctx, area: dict[str, Any]) -> list[dict[str, Any]]:
	records = ctx.records(area["kind"])
	if area["key"] == "annual_planning":
		items = _plan_items(ctx)
		return [{"key": k, "label": label, "count": sum(1 for i in items if i["state"] == k), "tone": COVERAGE_TONE[k]}
			for k, label in COVERAGE_STATES if any(i["state"] == k for i in items)]
	return _distribution(area, records)


def _outstanding(ctx: _Ctx, area: dict[str, Any]) -> list[dict[str, Any]]:
	"""Outstanding matters of the area's filtered records with their wait."""
	rows = []
	for rec in ctx.records(area["kind"]):
		out = rec.get("outstanding")
		if not out:
			continue
		try:
			days = am.calendar_days(out["since"], ctx.at)
		except ValueError:
			continue  # a matter that has not reached its holder yet has no wait
		rows.append({"rec": rec, "days": days, "band": am.band_key(days), "out": out})
	rows.sort(key=lambda r: (r["rec"]["reference"] or "", r["rec"]["title"], r["rec"]["id"]))
	return rows


def _outstanding_line(n: int) -> str:
	return NO_OUTSTANDING if n == 0 else f"{n} outstanding matter" + ("" if n == 1 else "s")


def _headline(area: dict[str, Any], count: int) -> dict[str, str]:
	return {"figure": str(count), "unit": _plural_unit(area, count)}


# --------------------------------------------------------------------------
# Overview regions
# --------------------------------------------------------------------------


def _area_status(ctx: _Ctx, area: dict[str, Any]) -> str:
	read = ctx.reads.get(area["kind"])
	if read is None:
		return "na"
	return "unavailable" if read.status == "failed" else ("ok" if read.ok else "na")


def _strip(ctx: _Ctx, areas: list[dict[str, Any]]) -> dict[str, Any]:
	columns = []
	for area in areas:
		status = _area_status(ctx, area)
		column = {"key": area["key"], "tab": area["tab"], "label": area["label"], "icon": area["icon"], "status": status,
			"link": {"label": area["link"], "tab": area["tab"]}}
		if status == "unavailable":
			column.update({"message": f"{area['label']} could not be loaded.", "retry": True})
			columns.append(column)
			continue
		records = ctx.records(area["kind"])
		read = ctx.reads[area["kind"]]
		if read.identity_incomplete:
			column.update({"status": "incomplete", "message": f"{area['label']} totals are unavailable."})
			columns.append(column)
			continue
		count = len(records)
		if area["key"] == "annual_planning" and not records and not ctx.fy and ctx.units is None:
			column.update({"figure": "", "unit": "No Active Plan", "segments": [], "outstanding": NO_OUTSTANDING, "has_matters": False})
			columns.append(column)
			continue
		segments = _area_segments(ctx, area)
		if area["key"] == "annual_planning" and "coverage" in read.unavailable_measures:
			segments, column["coverage_unavailable"] = [], "Coverage unavailable"
		column.update(_headline(area, count))
		n_matters = len(_outstanding(ctx, area))
		column.update({"segments": segments, "outstanding": _outstanding_line(n_matters), "has_matters": n_matters > 0, "incomplete": read.incomplete})
		columns.append(column)
	return {"columns": columns, "note": STRIP_NOTE}


def _waiting(ctx: _Ctx, areas: list[dict[str, Any]]) -> dict[str, Any]:
	rows, quiet, unavailable = [], [], []
	for area in areas:
		status = _area_status(ctx, area)
		if status == "unavailable":
			unavailable.append(area)
			continue
		matters = _outstanding(ctx, area)
		if not matters:
			quiet.append(area["label"])
			continue
		segments = [{"key": key, "label": label, "count": sum(1 for m in matters if m["band"] == key), "tone": f"seq-{n + 1}"}
			for n, (key, label, _lo, _hi) in enumerate(am.BANDS) if any(m["band"] == key for m in matters)]
		rows.append({"key": area["key"], "label": area["label"], "icon": area["icon"], "segments": segments})
	none_text = ""
	if quiet:
		sentence = am.join_and([q[0].upper() + q[1:] if i == 0 else q[0].lower() + q[1:] for i, q in enumerate(quiet)])
		none_text = f"{sentence}: no outstanding matters recorded."
	return {"status": "incomplete" if unavailable else "ok", "incomplete_text": INCOMPLETE if unavailable else "",
		"legend": [{"key": k, "label": label, "tone": f"seq-{n + 1}"} for n, (k, label, _lo, _hi) in enumerate(am.BANDS)],
		"rows": rows, "none_text": none_text, "caption": "Days since each matter reached its current holder."}


def _coverage_region(ctx: _Ctx) -> dict[str, Any] | None:
	read = ctx.reads.get(ac.PLAN_ITEMS)
	if read is None:
		return None
	link = {"label": "View annual planning", "tab": "annual-planning"}
	if read.status == "failed" or "coverage" in read.unavailable_measures:
		return {"status": "unavailable", "message": "Plan coverage could not be loaded.", "retry": True, "link": link}
	items = _plan_items(ctx)
	if not items:
		return None
	planned = sum((i["planned"] for i in items), Decimal(0))
	covered = sum((i["covered"] for i in items), Decimal(0))
	incomplete = read.incomplete
	percent = None if incomplete else am.percent_half_up(covered, planned)
	n_full, n_part, n_not = (sum(1 for i in items if i["state"] == k) for k, _l in COVERAGE_STATES)
	unit = "Plan item" if n_full == 1 else "Plan items"
	segs = [{"key": "covered", "label": "Covered by authorised requisitions", "text": am.kes(covered), "value": float(covered), "tone": "pair-strong"},
		{"key": "not_covered", "label": "Not yet covered", "text": am.kes(planned - covered), "value": float(planned - covered), "tone": "pair-tint"}]
	return {"status": "incomplete" if incomplete else "ok", "incomplete_text": INCOMPLETE if incomplete else "", "percent": percent,
		"result": f"{percent}% of planned value is covered by authorised requisitions" if percent is not None else "",
		"planned": f"Planned value {am.kes(planned)} in the Active Plan", "segments": segs, "link": link,
		"items": f"{n_full} {unit} fully covered, {n_part} partly covered, {n_not} not covered."}


def _step_rows(ctx: _Ctx, keys: list[str]) -> dict[str, Any] | None:
	"""§4A ANL-M-04: completed transitions inside the window, with count,
	median, shortest and longest. A transition whose start event is
	unavailable is excluded and the read is marked incomplete (§4A.3)."""
	rows, incomplete, unavailable = [], False, False
	for step in [s for s in STEPS if s["key"] in keys]:
		read = ctx.reads.get(step["kind"])
		if read is None:
			continue
		if read.status == "failed":
			rows.append({"key": step["key"], "label": step["label"], "status": "unavailable", "message": "Could not be loaded."})
			unavailable = True
			continue
		values: list[int] = []
		for rec in ctx.records(step["kind"]):
			end, start = rec.get(step["end"]), rec.get(step["start"])
			if end is None or not am.in_window(end, ctx.at):
				continue
			if start is None:
				incomplete = True
				continue
			try:
				values.append(am.calendar_days(start, end))
			except ValueError:
				incomplete = True
		stats = am.step_stats(values)
		row = {"key": step["key"], "label": step["label"], "status": "ok", "completed": stats["completed"] if stats else 0}
		if stats:
			row.update({"median": stats["median"], "shortest": stats["shortest"], "longest": stats["longest"],
				"median_text": am.day_phrase(stats["median"]), "shortest_text": am.day_phrase(stats["shortest"]),
				"longest_text": am.day_phrase(stats["longest"])})
		rows.append(row)
		incomplete = incomplete or read.incomplete
	if not rows:
		return None
	any_done = any(r.get("completed") for r in rows)
	longest = [r["longest"] for r in rows if r.get("longest") is not None]
	top = am.axis_max(longest)
	return {"status": "incomplete" if (incomplete or unavailable) else "ok", "incomplete_text": INCOMPLETE if (incomplete or unavailable) else "",
		"rows": rows, "axis": {"max": top, "ticks": list(range(0, top + 1, am.AXIS_STEP))},
		"caption": "Calendar days, last 12 months.", "empty_text": "" if any_done else NO_STEPS}


# --------------------------------------------------------------------------
# Funding position (ANL-M-11, §5.5 rule 5)
# --------------------------------------------------------------------------


def _funding_region(ctx: _Ctx, resolved, served: dict[str, set[str]]) -> dict[str, Any] | None:
	if ac.FUNDING not in ctx.served:
		return None  # an actor outside the audience sees no region and no message
	if not ctx.fy:
		return {"status": "message", "message": FUNDING_CHOOSE}
	read = _read_kind(resolved, served, ctx.user, ac.FUNDING, ctx.at, fiscal_year=ctx.fy, org_unit=ctx.dept)
	if read.status == "failed":
		return {"status": "unavailable", "message": "Funding position could not be loaded.", "retry": True}
	fund = read.extra.get("funding") if "funding" in read.extra else (read.extra or None)
	if not read.ok or not fund or not fund.get("lines") and not fund.get("reservations"):
		return None
	lines, reservations = fund["lines"], fund["reservations"]
	units = ctx.units
	department = fund["view"] == "department" or units is not None
	if department and units is None:
		units = ctx.viewer["units"]  # Head of User Department with All departments: their permitted set
	base = {"status": "ok", "title": fund["budget_title"], "version_text": f"Current version {fund['version']}"}
	if not department:
		totals = {k: sum((l[k] for l in lines), Decimal(0)) for k in ("registered", "reserved", "committed", "available")}
		caption = ("Available to reserve is not a cash balance. Committed to contracts is Budget's record of contract commitments"
			+ ("; none is recorded." if totals["committed"] == 0 else "."))
		return {**base, "scope": "", "registered": am.kes(totals["registered"]), "segments": _funding_segments(totals), "caption": caption}
	own = [l for l in lines if l["owner_org_unit"] and (units is None or l["owner_org_unit"] in units)]
	mine = {k: sum((l[k] for l in own), Decimal(0)) for k in ("registered", "reserved", "committed", "available")}
	shared = [r for r in reservations if not r["line_owner_org_unit"] and (units is None or r["source_org_unit"] in units)]
	scope = ctx.unit_name(ctx.dept) if ctx.dept else _("your departments")
	return {**base, "scope": scope,
		"own": {"heading": f"Budget lines available to {scope}", "registered": am.kes(mine["registered"]), "segments": _funding_segments(mine)},
		"shared": {"heading": "Budget lines available to all departments",
			"figures": [{"label": "Reserved for this department's requisitions", "value": am.kes(sum((r["reserved"] for r in shared), Decimal(0)))},
				{"label": "Committed to contracts for this department", "value": am.kes(sum((r["committed"] for r in shared), Decimal(0)))}]},
		"caption": "Budget lines available to all departments are shared, so their allocation and available amount are not divided by department. Available to reserve is not a cash balance."}


def _funding_segments(totals: dict[str, Decimal]) -> list[dict[str, Any]]:
	spec = [("reserved", "Reserved for requisitions", "family-1"), ("committed", "Committed to contracts", "family-2"), ("available", "Available to reserve", "family-3")]
	return [{"key": k, "label": label, "text": am.kes(totals[k]), "value": float(totals[k]), "tone": tone, "keep_zero": k == "committed"}
		for k, label, tone in spec]


# --------------------------------------------------------------------------
# Area tabs
# --------------------------------------------------------------------------


def _outstanding_rows(ctx: _Ctx, matters: list[dict[str, Any]], unread: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
	rows = [{"key": m["rec"]["id"], "title": m["rec"]["title"], "text": m["out"]["text"], "waiting": _waiting_badge(m["days"]),
		"since": _since_text(m["out"]["since"]), "route": m["rec"]["route"] if ctx.route_ok(m["rec"]["route"]) else None} for m in matters]
	# ANL-DES-31F: a Tender whose stage could not be read says so, with no waiting time (nothing is known about its wait).
	for rec in unread or []:
		rows.append({"key": rec["id"], "title": rec["title"], "text": "We could not load the current position.", "waiting": "", "since": "",
			"route": rec["route"] if ctx.route_ok(rec["route"]) else None})
	rows.sort(key=lambda r: next(((m["rec"]["reference"] or "", m["rec"]["title"]) for m in matters if m["rec"]["id"] == r["key"]),
		next(((u["reference"] or "", u["title"]) for u in unread or [] if u["id"] == r["key"]), ("", ""))))
	return rows


def _monthly(ctx: _Ctx, title: str, series: list[tuple[str, str, list[Any]]]) -> dict[str, Any]:
	months = am.window_months(ctx.at)
	built = []
	for n, (key, label, instants) in enumerate(series):
		built.append({"key": key, "label": label, "counts": am.month_counts(instants, ctx.at), "tone": _tone(n)})
	empty = not any(sum(s["counts"]) for s in built)
	return {"title": title, "months": [{"key": m["key"], "label": m["label"], "axis_lines": _axis_lines(m, i)} for i, m in enumerate(months)], "series": built,
		"empty_text": NO_EVENTS if empty else ""}


def _axis_lines(month: dict[str, Any], index: int) -> list[str]:
	"""The month under its bar: ``Jul`` over ``2026`` for the first slot and each January, ``(to date)`` for the current month."""
	lines = [month["label"].split(" ")[0]]
	if index == 0 or month["start"].month == 1:
		lines.append(str(month["start"].year))
	if month["label"].endswith("(to date)"):
		lines.append("(to date)")
	return lines


def _row_action(ctx: _Ctx, rec: dict[str, Any]) -> dict[str, Any]:
	return {"label": "View record", "route": rec["route"] if ctx.route_ok(rec["route"]) else None}


def _contrib_line(ctx: _Ctx, rec: dict[str, Any]) -> str:
	"""Dept selection: a contributor names its lead (``X contributes; Lead: Y``)."""
	if ctx.units is None or not rec["org_units"] or rec["org_units"][0] in ctx.units:
		return ""
	mine = [u for u in rec["org_units"] if u in ctx.units]
	if not mine:
		return ""
	return f"{ctx.unit_name(mine[0])} contributes; Lead: {ctx.unit_name(rec['org_units'][0])}"


def _share_line(ctx: _Ctx, whole: Decimal, share: Decimal) -> str:
	if ctx.units is None or whole == share or not ctx.dept:
		return ""
	return f"{ctx.unit_name(ctx.dept)} share of {am.kes(whole)}"


def _outcome_cell(ctx: _Ctx, rec: dict[str, Any]) -> dict[str, str]:
	if rec["bucket"] == ac.UNAVAILABLE:
		return _text("Could not be loaded")
	if rec["cancelled_at"]:
		return _text(f"Cancellation recorded {ht.long_instant(rec['cancelled_at'])}")
	if rec["decision_at"] and rec["decision_outcome"]:
		verb = "Award decision" if rec["decision_outcome"] == ac.OUTCOME_AWARD else "No award decision"
		secondary = ""
		if rec["decision_outcome"] == ac.OUTCOME_AWARD and rec["award_amount_visible"] and rec["award_amount"] is not None and ctx.units is None:
			secondary = f"Award amount {am.kes(rec['award_amount'])}"
		return _text(f"{verb} recorded {ht.long_instant(rec['decision_at'])}", secondary)
	return _text("No AO award decision recorded", quiet=True)


def _register(ctx: _Ctx, area: dict[str, Any], records: list[dict[str, Any]], cursor: str | None) -> dict[str, Any]:
	key = area["key"]
	state_options = [] if key == "annual_planning" else _state_options(area, records)
	rows_src = [r for r in records if not ctx.state or _record_state_key(area, r) == ctx.state]
	if ctx.search:
		needle = ctx.search.lower()
		rows_src = [r for r in rows_src if needle in r["title"].lower() or needle in (r["reference"] or "").lower()]
	rows_src.sort(key=lambda r: ((r["reference"] or ""), r["title"], r["id"]))
	sort_key = lambda r: [r["reference"] or "", r["title"], r["id"]]
	start = 0
	if cursor:
		try:
			after = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
			start = next((i for i, r in enumerate(rows_src) if sort_key(r) > after), len(rows_src))
		except (ValueError, json.JSONDecodeError):
			start = 0
	page = rows_src[start:start + PAGE_SIZE]
	next_cursor = None
	if start + PAGE_SIZE < len(rows_src) and page:
		next_cursor = base64.urlsafe_b64encode(json.dumps(sort_key(page[-1])).encode()).decode()
	shown = start + len(page)
	filtered = bool(ctx.state or ctx.search)
	unit = area["footer"]
	if not rows_src:
		footer = f"0 matching {unit}" if filtered else f"0 {unit}"
	elif filtered:
		footer = f"Showing {shown} of {len(rows_src)} matching {unit}"
	else:
		footer = f"Showing {shown} of {len(rows_src)} {unit}"
	clear = None
	if ctx.search:
		clear = {"label": "Clear search", "kind": "search"}
	elif ctx.state:
		clear = {"label": "Clear stage filter" if key == "tender_proceedings" else "Clear state filter", "kind": "state"}
	rows = [_register_row(ctx, area, r) for r in page]
	layout = "table" if key in ("annual_planning", "requisitions", "tender_proceedings") else "compact"
	if ctx.state and not any(o["key"] == ctx.state for o in state_options):
		label = BUCKET_LABEL.get(ctx.state) or next((st for st in _static_states(area) if _slug(st) == ctx.state), ctx.state)
		state_options = [*state_options, {"key": ctx.state, "label": label}]
	return {"layout": layout, "title": area["footer"][0].upper() + area["footer"][1:], "search_label": area["search"], "state_options": state_options,
		"state_all": "All stages" if key == "tender_proceedings" else "All states", "columns": _columns(key), "rows": rows,
		"footer": footer, "empty_text": NO_MATCH if not rows_src and filtered else "", "clear": clear,
		"total": len(rows_src), "next_cursor": next_cursor, "partial": bool(ctx.reads[area["kind"]].identity_incomplete)}


def _columns(key: str) -> list[dict[str, str]]:
	cols = {
		"needs": [], "departmental_planning": [],
		"annual_planning": ["Plan item", "Department", "Planned value", "Covered by authorised requisitions", "Action"],
		"requisitions": ["Requisition", "Current position", "Requisition value", "Tender relationship", "Action"],
		"tender_proceedings": ["Tender", "Current position", "Authorised requisition value", "Recorded AO outcome", "Action"],
	}[key]
	return [{"key": _slug(c), "label": c} for c in cols]


def _register_row(ctx: _Ctx, area: dict[str, Any], rec: dict[str, Any]) -> dict[str, Any]:
	key = area["key"]
	row: dict[str, Any] = {"key": rec["id"], "action": _row_action(ctx, rec)}
	if key in ("needs", "departmental_planning"):
		row.update({"title": rec["title"], "position": rec["state"]})
	elif key == "annual_planning":
		planned, covered, whole = _item_values(ctx, rec)
		lead = ctx.unit_name(rec["org_units"][0]) if rec["org_units"] else ""
		others = [ctx.unit_name(u) for u in rec["org_units"][1:]]
		dept = lead + "".join(f"; {o} contributes" for o in others)
		row["cells"] = {"plan_item": _text(rec["title"]), "department": _text(dept),
			"planned_value": _text(am.kes(planned), _share_line(ctx, whole, planned)),
			"covered_by_authorised_requisitions": _text(am.kes(covered))}
	elif key == "requisitions":
		share = ctx.share(rec["value_lines"])
		if rec["value_kind"]:
			value = _text(f"{am.kes(share)} {rec['value_kind']}", _share_line(ctx, ctx.whole(rec["value_lines"]), share))
		else:
			value = _text("—")
		rel = f"{rec['tender_reference']} created" if rec["tender_reference"] else "No Tender created"
		row["cells"] = {"requisition": _text(rec["title"]), "current_position": _text(rec["state"]),
			"requisition_value": value, "tender_relationship": _text(rel)}
	else:
		share = ctx.share(rec["authorised_lines"])
		row["cells"] = {
			"tender": _text(rec["title"], rec["reference"]),
			"current_position": _text(rec["position"], _contrib_line(ctx, rec)),
			"authorised_requisition_value": _text(am.kes(share), _share_line(ctx, ctx.whole(rec["authorised_lines"]), share)),
			"recorded_ao_outcome": _outcome_cell(ctx, rec)}
	return row


def _area_tab(ctx: _Ctx, area: dict[str, Any], cursor: str | None) -> dict[str, Any]:
	key = area["key"]
	status = _area_status(ctx, area)
	base = {"key": key, "tab": area["tab"], "label": area["label"], "icon": area["icon"], "status": status}
	if status == "unavailable":
		return {**base, "message": f"{area['label']} could not be loaded.", "retry": True}
	read = ctx.reads[area["kind"]]
	records = ctx.records(area["kind"])
	n = len(records)
	if read.identity_incomplete:
		base.update({"result_text": f"{area['label']} totals are unavailable.", "partial": True})
	elif key == "annual_planning" and not records and not ctx.fy and ctx.units is None:
		base["result_text"] = "No Active Plan"
	else:
		base["result_text"] = f"{n} {_plural_unit(area, n)}"
		states = _state_labels(area, records) if key in ("needs", "departmental_planning") else []
		if len(states) == 1 and n:
			base["result_text"] += f" {states[0][0].lower() + states[0][1:]}"
	base["figure"], base["unit"] = str(n), _plural_unit(area, n)
	base["incomplete_text"] = INCOMPLETE if read.incomplete else ""
	matters = _outstanding(ctx, area)
	unread = [r for r in records if r.get("bucket") == ac.UNAVAILABLE and not r.get("outstanding")]
	base["outstanding"] = {"title": "Outstanding work", "rows": _outstanding_rows(ctx, matters, unread)}
	base["secondary"] = "" if (matters or unread) else "No outstanding matters recorded in this selection."
	base["scope_label"] = f"All {n} {_plural_unit(area, n)} in this area" if (ctx.state or ctx.search) and n else ""
	base["charts"] = _charts(ctx, area, records)
	steps = TAB_STEPS.get(area["tab"])
	base["steps"] = _step_rows(ctx, steps) if steps else None
	if key == "annual_planning":
		base.update(_annual_extras(ctx, records))
	base["register"] = _register(ctx, area, records, cursor)
	return base


def _charts(ctx: _Ctx, area: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
	key = area["key"]
	if key == "needs":
		return {"monthly": _monthly(ctx, "Accepted for planning each month", [("accepted", "Accepted for planning", [r["accepted_at"] for r in records])])}
	if key == "departmental_planning":
		return {"monthly": _monthly(ctx, "Departmental plans accepted each month", [("accepted", "Departmental plans accepted", [r["accepted_at"] for r in records])])}
	if key == "requisitions":
		states = []
		for i, label in enumerate(_state_labels(area, records)):
			mine = [r for r in records if r["state"] == label]
			kinds = {r["value_kind"] for r in mine}
			value = ""
			if len(kinds) == 1 and None not in kinds:
				value = f"{am.kes(sum((ctx.share(r['value_lines']) for r in mine), Decimal(0)))} {kinds.pop()}"
			states.append({"key": _slug(label), "label": label, "count": len(mine), "value_text": value, "tone": _tone(i)})
		return {"states": {"title": "Requisitions by current state", "value_header": "Requisition value", "rows": states},
			"monthly": _monthly(ctx, "Recorded each month", [("submitted", "Submitted to Procurement", [e for r in records for e in r["submission_events"]]),
				("authorised", "Authorised", [e for r in records for e in r["authorisation_events"]])])}
	if key == "tender_proceedings":
		return _tender_charts(ctx, records)
	return _planning_charts(ctx)


def _tender_charts(ctx: _Ctx, records: list[dict[str, Any]]) -> dict[str, Any]:
	rows = []
	for bucket in ac.BUCKETS:
		mine = [r for r in records if r["bucket"] == bucket]
		if not mine:
			continue
		rows.append({"key": bucket, "label": BUCKET_LABEL[bucket], "count": len(mine), "tone": BUCKET_TONE[bucket], "selected": ctx.state == bucket,
			"value_text": am.kes(sum((ctx.share(r["authorised_lines"]) for r in mine), Decimal(0)))})
	decided = [r for r in records if r["decision_events"] or (r["decision_at"] and r["decision_outcome"])]
	n_events = len(decided)
	note = ""
	if decided:
		note = f"{n_events} AO award decision{'s' if n_events != 1 else ''} recorded."
		awarded = [r for r in decided if r["decision_outcome"] == ac.OUTCOME_AWARD]
		if awarded and ctx.units is None and all(r["award_amount_visible"] and r["award_amount"] is not None for r in awarded):
			note += f" Award amount {am.kes(sum((r['award_amount'] for r in awarded), Decimal(0)))}."
	return {"stages": {"title": "Tenders by stage", "value_header": "Authorised requisition value", "rows": rows, "note": note},
		"monthly": _monthly(ctx, "Recorded each month", [("published", "Published", [r["published_at"] for r in records]),
			("cancelled", "Cancelled", [e for r in records for e in r["cancellation_events"]]),
			("decisions", "AO award decisions", [e for r in records for e in r["decision_events"]])])}


def _planning_charts(ctx: _Ctx) -> dict[str, Any]:
	items = _plan_items(ctx)
	items.sort(key=lambda i: (-i["planned"], i["rec"]["title"]))
	by_item = []
	for item in items:
		covered, rest = item["covered"], item["planned"] - item["covered"]
		by_item.append({"key": item["rec"]["id"], "label": item["rec"]["title"], "share_note": f"{ctx.unit_name(ctx.dept)} share" if item["shared"] and ctx.dept else "",
			"segments": [s for s in (
				{"key": "covered", "label": "Covered", "text": am.kes(covered), "value": float(covered), "tone": "pair-strong"} if covered > 0 else None,
				{"key": "not_covered", "label": "Not yet covered", "text": am.kes(rest), "value": float(rest), "tone": "pair-tint"} if rest > 0 else None) if s]})
	by_dept: dict[str, dict[str, Decimal]] = {}
	for item in items:
		for alloc in item["rec"]["allocations"]:
			if ctx.scope_units is not None and alloc["org_unit"] not in ctx.scope_units:
				continue
			slot = by_dept.setdefault(alloc["org_unit"], {"planned": Decimal(0), "covered": Decimal(0)})
			slot["planned"] += alloc["planned"]
			slot["covered"] += min(alloc["covered"], alloc["planned"])
	dept_rows = []
	for unit, v in sorted(by_dept.items(), key=lambda kv: (-kv[1]["planned"], ctx.unit_name(kv[0]))):
		rest = v["planned"] - v["covered"]
		pct = am.percent_half_up(v["covered"], v["planned"])
		dept_rows.append({"key": unit, "label": ctx.unit_name(unit), "percent_text": f"{pct}%" if pct is not None else "",
			"segments": [s for s in (
				{"key": "covered", "label": "Covered", "text": am.kes(v["covered"]), "value": float(v["covered"]), "tone": "pair-strong"} if v["covered"] > 0 else None,
				{"key": "not_covered", "label": "Not yet covered", "text": am.kes(rest), "value": float(rest), "tone": "pair-tint"} if rest > 0 else None) if s]})
	caption = ""
	if ctx.scope_units is None:
		parts = []
		for item in items:
			allocs = [a for a in item["rec"]["allocations"] if a["covered"] > 0]
			if len(allocs) > 1:
				owners = [f"{am.kes(a['covered'])} {'is attributed ' if n == 0 else ''}to {ctx.unit_name(a['org_unit'])}" for n, a in enumerate(allocs)]
				parts.append(f"{item['rec']['title']} is shared: {am.join_and(owners)}.")
		caption = " ".join(parts)
	timing = [i for i in items if i["rec"]["has_proceeding"]]
	timing.sort(key=lambda i: (i["rec"]["invitation_days"] is None, -(i["rec"]["invitation_days"] or 0), i["rec"]["title"]))
	trows = []
	for item in timing:
		days = item["rec"]["invitation_days"]
		if days is None:
			text = "No date recorded"
		elif days == 0:
			text = "On the approved date"
		else:
			text = f"{abs(days)} day{'s' if abs(days) != 1 else ''} {'after' if days > 0 else 'before'} approved date"
		trows.append({"key": item["rec"]["id"], "label": item["rec"]["title"], "days": days, "text": text})
	span = max([abs(r["days"]) for r in trows if r["days"] is not None] or [0])
	legend = [{"key": "covered", "label": "Covered", "tone": "pair-strong"}, {"key": "not_covered", "label": "Not yet covered", "tone": "pair-tint"}]
	return {"by_item": {"title": "Coverage by Plan item", "rows": by_item, "legend": legend},
		"by_department": {"title": "Coverage by department", "rows": dept_rows, "caption": caption},
		"timing": {"title": "Tender invitation timing", "rows": trows, "span": span,
			"caption": "Actual invitation date compared with the date approved in the Active Plan."}}


def _annual_extras(ctx: _Ctx, records: list[dict[str, Any]]) -> dict[str, Any]:
	items = _plan_items(ctx)
	if not items:
		return {"source": "", "figures": []}
	read = ctx.reads[ac.PLAN_ITEMS]
	titles = []
	for item in items:
		line = f"{item['rec']['plan_title']}, Active Version {item['rec']['plan_version']}"
		if line not in titles:
			titles.append(line)
	planned = sum((i["planned"] for i in items), Decimal(0))
	covered = sum((i["covered"] for i in items), Decimal(0))
	percent = None if read.incomplete or "coverage" in read.unavailable_measures else am.percent_half_up(covered, planned)
	figures = [{"label": "Planned value", "value": am.kes(planned)}]
	if "coverage" not in read.unavailable_measures:
		figures.append({"label": "Covered by authorised requisitions", "value": am.kes(covered) + (f" ({percent}%)" if percent is not None else "")})
	return {"source": "; ".join(titles), "figures": figures}


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def _tabs(selected: str) -> list[dict[str, Any]]:
	tabs = [{"key": "overview", "label": "Overview", "icon": "", "route": ["analytics"], "selected": selected == "overview"}]
	for area in AREAS:
		tabs.append({"key": area["tab"], "label": area["label"], "icon": area["icon"], "route": ["analytics", area["tab"]], "selected": selected == area["tab"]})
	return tabs


def _definitions(ctx: _Ctx, failed_areas: list[dict[str, Any]]) -> str:
	text = DEFINITIONS.format(window_end=ht.long_instant(ctx.at).rsplit(",", 1)[0])
	clock = ht.long_instant(ctx.at).rsplit(", ", 1)[-1]
	if failed_areas:
		names = am.join_and([a["label"] for a in failed_areas])
		reads = "read is" if len(failed_areas) == 1 else "reads are"
		return f"{text} The {names} {reads} unavailable. Other area reads completed at {clock}."
	return f"{text} All area reads completed at {clock}."


def _base(ctx: _Ctx, tab: str, verdict: str, message: str = "") -> dict[str, Any]:
	return {"verdict": verdict, "message": message, "title": "Procurement Analytics",
		"description": "See where procurement work stands, how long key steps take and how much planned value is covered.",
		"read_at": to_utc_iso(ctx.at), "updated": f"Updated {ht.long_instant(ctx.at)}",
		"scope": ctx.unit_name(ctx.dept) if ctx.dept else _("All departments"), "tab": tab, "tabs": _tabs(tab),
		"filters": {"fy": ctx.fy, "dept": ctx.dept, "state": ctx.state, "fy_options": [], "dept_options": [], "messages": [], "applied": False},
		"empty": False, "overview": None, "area": None, "definitions": ""}


def get_access(user: str, *, providers: list[Any] | None = None, at: datetime | None = None) -> dict[str, Any]:
	"""May this user open Analytics at all? One cheap role check per owner:
	no scan. Home's gated link and the page's first paint use it."""
	at = at or ht.now()
	viewer = av.describe(user, at)
	if not viewer["internal"]:
		return {"allowed": False, "areas": [], "failed": 0}
	served, failed = _applies(_resolve(providers), user, at)
	kinds = set().union(*served.values()) if served else set()
	return {"allowed": bool(kinds) or bool(failed), "areas": [a["tab"] for a in AREAS if a["kind"] in kinds], "failed": failed}


def get_workspace(user: str, *, tab: str = "overview", fy: str = "", dept: str = "", state: str = "", search: str = "",
		cursor: str | None = None, providers: list[Any] | None = None, at: datetime | None = None) -> dict[str, Any]:
	at = at or ht.now()
	tab = tab if tab in TABS else "overview"
	viewer = av.describe(user, at)
	ctx = _Ctx(user, at, viewer)
	ctx.search = cstr(search).strip()
	if not viewer["internal"]:
		return _base(ctx, tab, "denied", DENIED)
	resolved = _resolve(providers)
	served_by, failed_applies = _applies(resolved, user, at)
	ctx.served = set().union(*served_by.values()) if served_by else set()
	area_kinds = [a["kind"] for a in AREAS if a["kind"] in ctx.served]
	if not area_kinds and not failed_applies:
		return _base(ctx, tab, "no_area", DENIED)
	if not area_kinds and failed_applies:
		return _base(ctx, tab, "failed", FAILED)

	messages: list[str] = []
	if fy:
		if av.fiscal_year_exists(fy):
			ctx.fy = fy
		else:
			messages.append("Choose an available financial year.")
	if dept:
		if av.selectable_unit(dept, viewer):
			ctx.dept, ctx.units = dept, av.unit_scope(dept)
		else:
			messages.append("Choose a department in your permitted area.")
	area = AREA_BY_TAB.get(tab)
	if state:
		if area and _valid_state(area, state):
			ctx.state = state
		else:
			messages.append("Choose an available state.")

	ctx.scope_units = ctx.units if ctx.units is not None else viewer["units"]
	for kind in _kinds_for(tab, ctx.served):
		ctx.reads[kind] = _read_kind(resolved, served_by, user, kind, at)
	areas = [a for a in AREAS if a["kind"] in ctx.served]
	if area and area["kind"] not in ctx.served:
		return {**_base(ctx, tab, "no_area", DENIED), "filters": {**_base(ctx, tab, "ok")["filters"], "messages": messages}}
	needed = [a for a in areas if a["kind"] in ctx.reads] if tab == "overview" else [area]
	if tab == "overview" and needed and all(ctx.reads[a["kind"]].status == "failed" for a in needed):
		out = _base(ctx, tab, "failed", FAILED)
		out["filters"] = _filters(ctx, messages)
		return out

	out = _base(ctx, tab, "ok")
	out["filters"] = _filters(ctx, messages)
	if messages:
		# ANL-AC-13: an invalid or unpermitted choice shows its message and never widens the selection, so no figure is
		# drawn for it. The valid parts of the selection stay in the filter row (§8 "preserve other valid filters").
		return out
	failed_areas = [a for a in areas if a["kind"] in ctx.reads and ctx.reads[a["kind"]].status == "failed"]
	out["definitions"] = _definitions(ctx, failed_areas)
	occupied = any(ctx.records(a["kind"]) for a in areas if a["kind"] in ctx.reads)
	if tab == "overview":
		if not occupied and not failed_areas:
			out["empty"], out["message"] = True, NO_RECORDS
			return out
		out["overview"] = {"strip": _strip(ctx, areas), "waiting": _waiting(ctx, areas), "coverage": _coverage_region(ctx),
			"steps": _step_rows(ctx, TAB_STEPS["overview"]), "funding": _funding_region(ctx, resolved, served_by)}
	else:
		out["area"] = _area_tab(ctx, area, cursor)
		if not out["area"].get("register", {}).get("total") and not ctx.records(area["kind"]) and out["area"]["status"] == "ok" and not failed_areas:
			out["empty"], out["message"] = True, NO_RECORDS
	return out


def _filters(ctx: _Ctx, messages: list[str]) -> dict[str, Any]:
	"""Options come from the records the actor may know; a selected value is always offered."""
	fys: set[str] = set()
	units: set[str] = set()
	for read in ctx.reads.values():
		if not read.ok:
			continue
		for rec in read.records:
			if rec["fiscal_year"]:
				fys.add(rec["fiscal_year"])
			units.update(rec["org_units"])
	if ctx.fy:
		fys.add(ctx.fy)
	units -= av.root_units()
	if ctx.viewer["units"] is not None:
		units &= ctx.viewer["units"]
	if ctx.dept:
		units.add(ctx.dept)
	fy_labels = av.fiscal_year_labels(fys)
	names = av.unit_labels(units)
	fy_options = sorted(({"id": k, "label": v} for k, v in fy_labels.items()), key=lambda o: o["label"])
	dept_options = sorted(({"id": k, "label": v} for k, v in names.items()), key=lambda o: o["label"])
	ctx.labels.update(names)
	return {"fy": ctx.fy, "dept": ctx.dept, "state": ctx.state, "fy_options": fy_options, "dept_options": dept_options,
		"messages": messages, "applied": bool(ctx.fy or ctx.dept), "invalid": bool(messages)}
