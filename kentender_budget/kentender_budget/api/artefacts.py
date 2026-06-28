# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Budget Line Artefacts API — Zone 3 of the Budget Workbench.

Returns the six artefact sections for a given Budget Line:
  strategy   — strategic hierarchy labels resolved from line FK fields
  demands    — Budget Reservations where source_doctype = "Demand" (or "Demand Intake")
  packages   — Procurement Packages linked to this budget line
  tenders    — TM2 Tenders linked to those packages
  contracts  — not yet linked downstream; returns []
  movements  — all Budget Reservations for this line, newest-first, event model
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

# ── Icon palette (shared with movements.py) ────────────────────────────────
_EVENT_ICON: dict[str, str] = {
	"reservation": "lock",
	"release":     "lock_open",
	"commitment":  "verified",
}

# source_doctype values that represent demand-type artefacts
_DEMAND_DOCTYPES = {"Demand", "Demand Intake"}

# source_doctype values that represent package-type artefacts
_PACKAGE_DOCTYPES = {"Procurement Package"}


def _fmt_kes(amount: float) -> str:
	return f"KES {int(round(flt(amount))):,}"


# ── Strategy section ───────────────────────────────────────────────────────

def _build_strategy(line: frappe._dict) -> dict:
	"""Resolve human-readable labels for the strategy hierarchy on the line.

	Resolution order per field:
	  1. Primary title field (program_title, title, objective_title, target_title)
	  2. Business code field (program_code, sub_program_code, objective_code, target_code)
	  3. None — never fall back to the internal primary key / hash name.
	"""

	def _label(doctype: str, name: str | None, title_field: str, code_field: str | None = None) -> str | None:
		if not name:
			return None
		title = frappe.db.get_value(doctype, name, title_field)
		if title:
			return title
		if code_field:
			code = frappe.db.get_value(doctype, name, code_field)
			if code:
				return code
		return None  # Document missing or title unpopulated — never expose the raw hash

	program_label = _label("Strategy Program", line.program, "program_title", "program_code")
	sub_program_label = _label("Sub Program", line.sub_program, "title", "sub_program_code")
	output_indicator_label = _label("Strategy Objective", line.output_indicator, "objective_title", "objective_code")
	performance_target_label = _label("Strategy Target", line.performance_target, "target_title", "target_code")

	# Narrative description: prefer Strategy Objective description, fall back to Program description
	program_description = frappe.db.get_value("Strategy Program", line.program, "description") if line.program else None
	output_indicator_description = frappe.db.get_value("Strategy Objective", line.output_indicator, "description") if line.output_indicator else None
	strategy_description = output_indicator_description or program_description or None

	return {
		"program":                  line.program,
		"program_label":            program_label,
		"program_description":      strategy_description,
		"sub_program":              line.sub_program,
		"sub_program_label":        sub_program_label,
		"output_indicator":         line.output_indicator,
		"output_indicator_label":   output_indicator_label,
		"performance_target":       line.performance_target,
		"performance_target_label": performance_target_label,
	}


# ── Reservations loader ────────────────────────────────────────────────────

def _get_reservations(budget_line_name: str) -> list[frappe._dict]:
	"""Fetch all Budget Reservations for this line, ordered newest-first."""
	return frappe.db.sql(
		"""
		SELECT
			name,
			reservation_id,
			source_doctype,
			source_docname,
			source_business_id,
			amount,
			status,
			created_at,
			released_at,
			converted_at,
			commitment_amount
		FROM `tabBudget Reservation`
		WHERE budget_line = %(line)s
		ORDER BY COALESCE(created_at, creation) DESC
		""",
		{"line": budget_line_name},
		as_dict=True,
	)


# ── Demands section ────────────────────────────────────────────────────────

def _build_demands(reservations: list[frappe._dict]) -> list[dict]:
	"""Return demand-type artefacts derived from reservations."""
	items = []
	for r in reservations:
		if (r.source_doctype or "") not in _DEMAND_DOCTYPES:
			continue
		items.append(
			{
				"ref":          r.source_business_id or r.source_docname or r.name,
				"source_doctype": r.source_doctype or "Demand",
				"source_docname": r.source_docname or "",
				"amount":       flt(r.amount),
				"status":       r.status or "",
				"reservation_id": r.reservation_id or r.name,
			}
		)
	return items


# ── Packages section ───────────────────────────────────────────────────────

def _build_packages(budget_line_name: str) -> list[dict]:
	"""Return Procurement Package artefacts linked to this budget line.

	Queries both:
	  1. Procurement Package.budget_line_id (direct FK, canonical PP2 path)
	  2. Budget Reservation.source_doctype = "Procurement Package" (reservation path)
	"""
	packages: dict[str, dict] = {}

	# 1. Direct link via Procurement Package.budget_line_id
	if frappe.db.exists("DocType", "Procurement Package"):
		rows = frappe.get_all(
			"Procurement Package",
			filters={"budget_line_id": budget_line_name},
			fields=["name", "package_code", "package_name", "status", "estimated_value", "tender_code"],
			limit=200,
		)
		for r in rows:
			packages[r.name] = {
				"name":          r.name,
				"ref":           r.package_code or r.name,
				"title":         r.package_name or r.package_code or r.name,
				"status":        r.status or "",
				"amount":        flt(r.estimated_value),
				"tender_code":   r.tender_code or "",
			}

	return list(packages.values())


# ── Tenders section ────────────────────────────────────────────────────────

def _build_tenders(packages: list[dict]) -> list[dict]:
	"""Return TM2 Tender artefacts linked to the packages on this line."""
	if not packages or not frappe.db.exists("DocType", "TM2 Tender"):
		return []

	# Collect tender_codes from packages that have them
	tender_codes = [p["tender_code"] for p in packages if p.get("tender_code")]
	package_names = [p["name"] for p in packages]

	filters: list = []
	if tender_codes:
		filters = [["tender_code", "in", tender_codes]]
	elif package_names:
		filters = [["procurement_package", "in", package_names]]
	else:
		return []

	rows = frappe.get_all(
		"TM2 Tender",
		filters=filters,
		fields=["name", "tender_code", "tender_title", "status", "estimated_value_internal"],
		limit=200,
	)
	return [
		{
			"name":   r.name,
			"ref":    r.tender_code or r.name,
			"title":  r.tender_title or r.tender_code or r.name,
			"status": r.status or "",
			"amount": flt(r.estimated_value_internal),
		}
		for r in rows
	]


# ── Movements section ──────────────────────────────────────────────────────

def _build_movements(reservations: list[frappe._dict]) -> list[dict]:
	"""Map Budget Reservations for this line to the hub-timeline event model."""
	events = []
	for r in reservations:
		amount_str = _fmt_kes(r.amount)
		ref = r.reservation_id or r.name or ""
		src = r.source_business_id or r.source_docname or ""

		if r.status == "Active":
			desc = f"{amount_str} reserved"
			if src:
				desc += f" for {r.source_doctype or 'demand'} {src}"
			events.append(
				{
					"event_type": "reservation",
					"icon":       _EVENT_ICON["reservation"],
					"title":      "Funds Reserved",
					"desc":       desc,
					"ref":        ref,
					"ts":         str(r.created_at or ""),
				}
			)
		elif r.status == "Released":
			desc = f"{amount_str} released"
			if src:
				desc += f" from {r.source_doctype or 'demand'} {src}"
			events.append(
				{
					"event_type": "release",
					"icon":       _EVENT_ICON["release"],
					"title":      "Reservation Released",
					"desc":       desc,
					"ref":        ref,
					"ts":         str(r.released_at or r.created_at or ""),
				}
			)
		elif r.status in ("Committed", "Converted"):
			committed = flt(r.commitment_amount or r.amount)
			desc = f"{_fmt_kes(committed)} committed"
			if src:
				desc += f" ({r.source_doctype or 'package'} {src})"
			events.append(
				{
					"event_type": "commitment",
					"icon":       _EVENT_ICON["commitment"],
					"title":      "Budget Committed",
					"desc":       desc,
					"ref":        ref,
					"ts":         str(r.converted_at or r.created_at or ""),
				}
			)

	# Already ordered newest-first by SQL, but sort again to handle mixed ts fields
	events.sort(key=lambda e: e.get("ts") or "", reverse=True)
	return events


# ── Public endpoint ────────────────────────────────────────────────────────

@frappe.whitelist()
def get_budget_line_artefacts(budget_line_name: str) -> dict:
	"""Return the six artefact sections for the Budget Workbench Zone 3.

	Args:
		budget_line_name: Primary key of the Budget Line DocType.

	Returns::

		{
		  "strategy":  { program, program_label, sub_program, ..., performance_target_label },
		  "demands":   [ { ref, source_doctype, source_docname, amount, status } ],
		  "packages":  [ { name, ref, title, status, amount, tender_code } ],
		  "tenders":   [ { name, ref, title, status, amount } ],
		  "contracts": [],   # downstream — not yet linked
		  "movements": [ { event_type, icon, title, desc, ref, ts } ],
		}
	"""
	if not (budget_line_name or "").strip():
		frappe.throw(_("Budget Line is required."), frappe.MandatoryError)

	if not frappe.db.exists("Budget Line", budget_line_name):
		frappe.throw(_("Budget Line not found: {0}").format(budget_line_name))

	if not frappe.has_permission("Budget Line", "read", budget_line_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	line = frappe.db.get_value(
		"Budget Line",
		budget_line_name,
		[
			"name", "budget_line_code", "budget_line_name",
			"strategic_plan", "program", "sub_program",
			"output_indicator", "performance_target",
		],
		as_dict=True,
	)

	reservations = _get_reservations(budget_line_name)
	packages = _build_packages(budget_line_name)

	return {
		"strategy":  _build_strategy(line),
		"demands":   _build_demands(reservations),
		"packages":  packages,
		"tenders":   _build_tenders(packages),
		"contracts": [],
		"movements": _build_movements(reservations),
	}
