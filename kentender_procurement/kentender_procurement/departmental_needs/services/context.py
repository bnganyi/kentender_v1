"""Needs context and Fiscal Year / submission state (NDS-CHG-001 v1.6 §3, §4.1, §8.1, §16.4).

The Needs-submission flag is two namespaced fields on ERPNext's native
`Fiscal Year` (`kentender_needs_submission_open`, `_closes_at`), owned and
maintained exclusively by Configuration & Governance through
`/app/system-setup` (CFG-CHG-002 v0.6). Departmental Needs never creates,
writes or exposes a configuration route for either field — it reads them
read-only through `kentender_core.services.site_configuration`, and every
create/submit command rechecks the flag server-side inside its own
transaction so a flag that closes between page load and submit is caught
(§12.7, NDS-AC-056).

There is no `Needs Intake Window` doctype and no `Scheduled` state under
v1.6: the flag is a plain Open/Closed Boolean at the instant it is read.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate, now_datetime

from kentender_procurement.departmental_needs.constants import INTAKE_CLOSED, INTAKE_OPEN
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	creation_contexts,
	is_administrative,
	viewing_contexts,
)

FY_DOCTYPE = "Fiscal Year"
FLAG_OPEN = "kentender_needs_submission_open"
FLAG_CLOSES_AT = "kentender_needs_submission_closes_at"


def fy_label(year_start_date) -> str:
	start = getdate(year_start_date)
	return f"FY {start.year}/{str(start.year + 1)[-2:]}"


def _fiscal_year_row(financial_year: str) -> dict[str, Any]:
	"""One ERPNext `Fiscal Year` record, normalised (§3, §16.2, §16.4.11).

	Departmental Needs reads the canonical ERPNext Fiscal Year directly — no
	KenTender-owned year doctype and no `PE Fiscal Year Context` registry.
	"""
	wanted = cstr(financial_year).strip()
	row = frappe.db.get_value(
		FY_DOCTYPE, wanted, ["name", "year_start_date", "year_end_date", "disabled"], as_dict=True
	)
	if not row:
		fail("NDS_CONTEXT_REQUIRED", f"Financial year {wanted or '(blank)'} is not configured.")
	return {
		"id": row.name,
		"label": fy_label(row.year_start_date),
		"start_date": str(row.year_start_date),
		"end_date": str(row.year_end_date),
		"disabled": bool(row.disabled),
	}


def selectable_financial_year(financial_year: str) -> dict:
	"""The FY must be a configured, non-disabled year (§5.4, NDS-BR-001).

	A future or past target year is not itself an error — what governs
	*when* a Need may be created is the Needs-submission flag on that exact
	year (NDS-BR-002), not whether the year has started or ended. Only a
	missing or administratively disabled year fails closed here, with the
	§9 `NDS_CONTEXT_REQUIRED` code.
	"""
	row = _fiscal_year_row(financial_year)
	if row["disabled"]:
		fail("NDS_CONTEXT_REQUIRED", "That financial year is not available for Departmental Needs.")
	return row


# --- §4.1 / §16.4 Needs-submission flag -------------------------------------


def _flag_row(financial_year: str) -> dict[str, Any] | None:
	return frappe.db.get_value(
		FY_DOCTYPE, cstr(financial_year).strip(), [FLAG_OPEN, FLAG_CLOSES_AT], as_dict=True
	)


def needs_submission_state(financial_year: str, *, at=None) -> dict[str, Any]:
	"""The flag's derived Open/Closed state for one exact Fiscal Year (NDS-AC-003).

	Reaching `kentender_needs_submission_closes_at` closes intake with the
	same effect as a manual close (NDS-AC-055) — checked here directly
	rather than trusting only the hourly `close_due_needs_submissions` job,
	so a command issued after the instant passes but before that job has
	run is still rejected (NDS-AC-056, §16.4 step 13).
	"""
	fy = cstr(financial_year).strip()
	row = _flag_row(fy)
	if not row or not row.get(FLAG_OPEN):
		return {"financial_year": fy, "state": INTAKE_CLOSED, "closes_at": ""}
	closes_at = row.get(FLAG_CLOSES_AT)
	if closes_at and get_datetime(closes_at) <= get_datetime(at or now_datetime()):
		return {"financial_year": fy, "state": INTAKE_CLOSED, "closes_at": str(closes_at)}
	return {"financial_year": fy, "state": INTAKE_OPEN, "closes_at": str(closes_at or "")}


def require_open_intake(financial_year: str, *, at=None) -> dict[str, Any]:
	"""Gate initial creation and initial submission on the flag being Open (NDS-BR-002)."""
	state = needs_submission_state(financial_year, at=at)
	if state["state"] != INTAKE_OPEN:
		fail(
			"NDS_INTAKE_NOT_OPEN",
			"Departmental Needs submission is not open for this financial year.",
		)
	return state


def get_needs_submission_state() -> dict[str, Any]:
	"""§8.1 `get_needs_submission_state` — the one open Fiscal Year, or Closed.

	Departmental Needs exposes no command for changing the flag and no
	intake-window page (§4.1, §17) — this is the module's only read of it.
	"""
	from kentender_core.services.site_configuration import get_site_configuration

	needs_submission = get_site_configuration().get("needs_submission")
	if not needs_submission:
		return {"open": False, "financial_year": "", "label": "", "closes_at": ""}
	return {
		"open": True,
		"financial_year": needs_submission["fiscal_year"],
		"label": needs_submission["label"],
		"closes_at": cstr(needs_submission.get("closes_at") or ""),
	}


# --- §8.1 reads --------------------------------------------------------------


def selectable_financial_years(user: str | None = None) -> list[dict[str, Any]]:
	"""§8.1 `list_needs_financial_years` — years represented by existing Needs
	visible in the actor's authorised Organisation Unit scope.

	This supplies browsing filters only (§16.4 step 3); it is never itself an
	authority to create in a given year — that is `require_open_intake`.
	"""
	principal = actor(user)
	filters: dict[str, Any] = {}
	if not is_administrative(principal):
		contexts = viewing_contexts(principal)
		if not contexts:
			return []
		units = {row["organisation_unit"] for row in contexts}
		filters["organisation_unit"] = ("in", sorted(units))
	names = frappe.get_all(
		"Departmental Need", filters=filters, pluck="financial_year", distinct=True, limit_page_length=0
	)
	if not names:
		return []
	rows = frappe.get_all(
		FY_DOCTYPE,
		filters={"name": ("in", sorted(set(names)))},
		fields=["name", "year_start_date"],
		order_by="year_start_date asc",
		limit_page_length=0,
	)
	return [{"id": row.name, "label": fy_label(row.year_start_date)} for row in rows]


def list_need_create_targets(user: str | None = None) -> dict[str, Any]:
	"""§8.1 `list_need_create_targets` / §16.4 step 4.

	Combines active Departmental Author Organisation Unit assignments with
	the one ERPNext Fiscal Year whose Needs-submission flag is Open. Zero,
	one or several OU targets drive the exact Create behaviour in §12.1: no
	Fiscal Year permission, remembered filter or browser-stored context ever
	substitutes for this.
	"""
	principal = actor(user)
	organisation_units = creation_contexts(principal)
	state = get_needs_submission_state()
	return {
		"organisation_units": organisation_units,
		"financial_year": state["financial_year"] if state["open"] else "",
		"financial_year_label": state["label"] if state["open"] else "",
		"open": bool(state["open"] and organisation_units),
	}


def resolve_creation_context(*, user: str | None = None) -> dict:
	"""Exact eligible Organisation Units and Needs-submission state (§8.1)."""
	contexts = creation_contexts(user)
	state = get_needs_submission_state()
	return {
		"ok": bool(contexts),
		"outcome": "READY" if contexts else "NO_ACTIVE_OPERATIONAL_ASSIGNMENT",
		"contexts": contexts,
		"requires_selection": len(contexts) > 1,
		"needs_submission": state,
	}
