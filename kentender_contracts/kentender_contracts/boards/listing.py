# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The contracts list (boards D01 and D01-S; CM-CHG-001 v0.8 sections 6.2, 6.3, 10): My work or All contracts, filtered and paged on the server **after** the authority filter, so a total never
reveals a contract the reader may not read.

A supplier's list (D01-S, "My contracts") shows their own side only: the title, the status and their own next action, never an internal task or the person who holds it."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.boards import kit
from kentender_contracts.services import audience, clock, people, picker_sources, work
from kentender_core.services import paging

STATUSES = ["All statuses", "Preparing", "Awaiting signatures", "Active", "Closed", "Did not proceed", "Terminated"]
SOURCES = ["All sources", "KenTender award", "External record"]
VIEWS = ["My work", "All contracts"]
COLS = ["Contract", "Supplier", "Status", "Next action", "Responsible person", ""]
COLS_SUPPLIER = ["Contract", "Title", "Status", "Next action", ""]
#: the picker sources of the list's Responsible person and Managing unit filters (registered in `services.picker_sources`)
RESPONSIBLE = "contracts.register_person"
MANAGING_UNIT = "contracts.register_unit"


def _own_view(case: str, user: str, holders: set[str] | None):
	return work.view(case, user, holders=holders)


def _row_facts(case: str, user: str, grants: list[audience.Grant]) -> dict[str, Any]:
	doc = frappe.db.get_value("Contract Case", case, ["contract_id", "supplier_name", "title", "lifecycle", "source_kind", "supplier_organisation", "managing_unit"], as_dict=True) or {}
	supplier_only = [g.audience for g in grants] == ["supplier"]
	holders = None
	if supplier_only:
		from kentender_contracts.services import parties

		holders = {u.lower() for u in parties.signatories(doc.get("supplier_organisation")) + parties.representatives(doc.get("supplier_organisation"))} | {user.lower()}
	view = _own_view(case, user, holders)
	lead = view["leading"]
	mine = bool(lead) and lead["holder"].lower() == user.lower()
	anyone = [t for t in work.live(case) if t["holder"].lower() == user.lower() and t["state"] in ("actionable", "blocked", "waiting", "scheduled")]
	return {"case": case, "doc": doc, "grants": grants, "lead": lead, "mine": mine, "has_work": bool(anyone), "supplier_only": supplier_only,
		"next": lead["title"] if lead else "—", "responsible": "" if supplier_only else (frappe.db.get_value("User", lead["holder"], "full_name") or lead["holder"]) if lead else ""}


def _may_register(user: str) -> bool:
	"""A person who prepares contracts (the head of procurement, or anyone with a Contract preparation assignment) may register a contract signed before KenTender."""
	from kentender_contracts.services import picker_sources

	return bool(picker_sources.preparing_units(user))


def _register(user: str) -> list[dict[str, Any]]:
	"""Every contract the reader may read, with what the list shows of it: the authority filter comes first, so nothing here (a total, a person, a unit) reveals a contract the reader may not read."""
	rows = []
	for case in frappe.get_all("Contract Case", pluck="name", order_by="creation desc"):
		grants = audience.readable(user, case)
		if grants:
			rows.append(_row_facts(case, user, grants))
	return rows


def _internal(actor: str) -> None:
	"""The person and unit filters are an internal reader's: a supplier's list is one list of their own, and a person with no part in contracts has nothing to filter."""
	found = audience.workspace_audiences(actor)
	if not found or found == ["supplier"]:
		raise frappe.DoesNotExistError("Not found")


def responsible_people(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""The people who hold the next action of the contracts this reader may read: the choices of the list's Responsible person filter, never a list of everyone."""
	_internal(actor)
	holders = {r["lead"]["holder"] for r in _register(actor) if r["lead"] and not r["supplier_only"]}
	return [{"id": u, "label": people.full_name(u), "detail": u, "keywords": u} for u in sorted(holders, key=lambda u: people.full_name(u).lower())]


def managing_units(*, query: str, context: dict, actor: str, limit: int) -> tuple[list[dict[str, Any]], int]:
	"""The units that manage the contracts this reader may read: the choices of the list's Managing unit filter."""
	from kentender_core.services import record_picker

	_internal(actor)
	units = {r["doc"].get("managing_unit") for r in _register(actor) if r["doc"].get("managing_unit")}
	kept = [row for row in (picker_sources.unit_row(u) for u in sorted(units)) if record_picker.matches(row, query)]
	return kept[:limit], len(kept)


def managing_units_by_id(*, ids: list[str], context: dict, actor: str) -> list[dict[str, Any]]:
	_internal(actor)
	units = {r["doc"].get("managing_unit") for r in _register(actor)}
	return [picker_sources.unit_row(i) for i in ids if i in units]


def workspace(user: str, *, page: Any = 1, page_size: Any = 10, view: str = "", search: str = "", status: str = "", source: str = "", responsible: str = "", unit: str = "") -> dict[str, Any]:
	audiences = audience.workspace_audiences(user)
	if not audiences:
		return {"ok": True, "screen": "workspace-forbidden"}
	chosen = view if view in VIEWS else VIEWS[1]  # unspecified is every contract the reader may read; the screen asks for My work explicitly
	rows = _register(user)
	supplier = audiences == ["supplier"]  # a supplier's list is one list, "My contracts": the My work / All contracts switch is an internal reader's
	needle = (search or "").strip().lower()
	shown = []
	for r in rows:
		d = r["doc"]
		if chosen == VIEWS[0] and not supplier and not r["has_work"]:
			continue
		if needle and needle not in " ".join(str(d.get(k) or "") for k in ("contract_id", "supplier_name", "title")).lower():
			continue
		if status and status != STATUSES[0] and d.get("lifecycle") != status:
			continue
		if source and source != SOURCES[0] and d.get("source_kind") != source.replace("External record", "External record"):
			continue
		if responsible and not (r["lead"] and r["lead"]["holder"].lower() == responsible.lower()):
			continue
		if unit and d.get("managing_unit") != unit:
			continue
		shown.append(r)
	page_rows, paging_info = paging.page_of(shown, page, page_size)
	body, routes = [], []
	for r in page_rows:
		d = r["doc"]
		cells = ["@" + d.get("contract_id", r["case"]), d.get("title") or "—" if supplier else d.get("supplier_name") or "—", "!" + d.get("lifecycle", ""), r["next"]]
		if not supplier:
			cells.append(r["responsible"] or "—")
		cells.append("@Open contract")
		body.append(cells)
		routes.append([r["case"]])
	filters = [kit.tx("Search contracts", search or "", "search")]
	if not supplier:
		# The design draws five filters in one bar: Search, Status, Source, Responsible person and Managing unit. A person or a unit chosen from a list that can grow is the shared picker (AGENTS.md section 6.12).
		filters += [kit.sel("Status", status or STATUSES[0], STATUSES, "status"), kit.sel("Source", source or SOURCES[0], SOURCES, "source"),
			kit.pick("Responsible person", responsible, RESPONSIBLE, "responsible", {}, people.full_name(responsible) if responsible else "", "person", allLabel="All people"),
			kit.pick("Managing unit", unit, MANAGING_UNIT, "unit", {}, picker_sources.unit_row(unit)["label"] if unit else "", "unit", allLabel="All units")]
	empty = "No contracts are available." if not rows or not (search or status or source or responsible or unit) else "No contracts match your search."
	board = kit.board(id="D01-S" if supplier else "D01", d="D01-S" if supplier else "D01", page="list", title="My contracts" if supplier else "Contracts", views=[] if supplier else VIEWS, view=VIEWS.index(chosen),
		filters=filters, headP="" if supplier or not _may_register(user) else "Register existing contract", cols=COLS_SUPPLIER if supplier else COLS, rows=body, rowRoutes=routes, empty=empty, emptyAct="Clear search" if (search or status or source or responsible or unit) else "", paging=paging_info,
		at=clock.when(clock.now()))
	return {"ok": True, "screen": "workspace", "audiences": audiences, "total": paging_info["total"], "page": paging_info["page"], "page_size": paging_info["page_size"],
		"rows": [{"case": r["case"], "audiences": [g.audience for g in r["grants"]]} for r in page_rows], "board": board}
