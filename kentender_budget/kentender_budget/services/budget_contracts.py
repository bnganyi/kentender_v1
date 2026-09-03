# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 — Budget/Budget Version identity, drafting and the
canonical position calculations (§5). BUD-UI-01 workspace, BUD-UI-02 version
editor Overview, BUD-UI-03 Overview tab.

Owns: `resolve_budget_context`, `save_budget_version_draft`,
`create_budget_successor_version`, and the shared position-calculation
helpers every other contract module reuses. Submit/Return/Approve/Close live
in `budget_readiness_contracts.py`; Budget Line drafting and eligible-line
reads live in `budget_line_contracts.py`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate

from kentender_budget.services.budget_authorization import (
	CAP_APPROVE,
	CAP_EDIT,
	has_budget_version_capability,
	require_budget_create_capability,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_reference import (
	allocate_budget_line_version_reference,
	allocate_budget_reference,
	allocate_budget_version_reference,
)

_ACTIVE_RESERVATION_STATUSES = ("Active", "Partially Converted", "Needs Attention")


def format_kes_compact(amount: float | None, *, currency: str = "KES") -> str:
	val = flt(amount)
	if abs(val) >= 1_000_000:
		m = val / 1_000_000.0
		if abs(m - round(m)) < 0.05:
			return f"{currency} {int(round(m))}M"
		text = f"{m:.1f}".rstrip("0").rstrip(".")
		return f"{currency} {text}M"
	return f"{currency} {val:,.0f}"


def format_kes_full(amount: float | None, *, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.0f}"


def resolve_scoped_entity(requested: str | None = None) -> str:
	"""BUD-BR-001 — hard PE scope; no unscoped / cross-entity read for a
	non-admin actor. Administrator/System Manager may pass any PE explicitly.

	Asserts scope against an already-known PE (a document's own
	procuring_entity, or an explicit caller-supplied value) — it does not
	pick "the current working context" for a screen with no PE of its own;
	that's kentender_core.services.reference_data_resolver.resolve_working_context's
	job (BUD-CHG-001 v1.2 Phase 8), used by get_budget_workspace and the
	pre-creation branch of save_budget_version_draft.

	Reads permitted_procuring_entities() directly rather than picking a
	single "the" PE for the user first — a user legitimately scoped to more
	than one Procuring Entity (e.g. a cross-entity Auditor) must be able to
	pass any one of them, not just whichever one an earlier single-PE guess
	happened to prefer."""
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	req = (requested or "").strip() or None
	pes = permitted_procuring_entities()
	if pes is None:
		return req or ""
	if not pes:
		frappe.throw(_("No procuring entity assigned"), frappe.PermissionError, title="BUDGET_SCOPE_REQUIRED")
	if req:
		if req not in pes:
			frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError, title="BUDGET_PERMISSION_DENIED")
		return req
	if len(pes) == 1:
		return next(iter(pes))
	# More than one permitted PE and no explicit target — every current call
	# site always asserts against an already-known document PE, so this is
	# ambiguous input, not a genuine "pick my working context" request.
	frappe.throw(_("A specific procuring entity is required"), frappe.PermissionError, title="BUDGET_SCOPE_REQUIRED")


def _entity_label(pe_name: str | None) -> str:
	if not pe_name:
		return ""
	return frappe.db.get_value("Procuring Entity", pe_name, "legal_name") or pe_name


def _fy_label(fy_name: str | None) -> str:
	if not fy_name:
		return ""
	return frappe.db.get_value("Financial Year", fy_name, "label") or fy_name


def _org_unit_label(org_unit: str | None) -> str:
	"""Empty owner_org_unit means PE-wide (Budget Line Version's own field
	description) — that reads as a real label everywhere it's displayed, not
	a blank cell."""
	if not org_unit:
		return _("PE-wide")
	return frappe.db.get_value("Organisation Unit", org_unit, "unit_name") or org_unit


def _user_label(user: str | None) -> str:
	if not user:
		return ""
	return frappe.db.get_value("User", user, "full_name") or user


def _display_datetime(value) -> str:
	from frappe.utils import format_datetime, get_datetime

	if not value:
		return ""
	return format_datetime(get_datetime(value))


def _display_date(value) -> str:
	from frappe.utils import formatdate

	if not value:
		return ""
	return formatdate(value, "d MMM yyyy")


def _funding_source_label(funding_source: str | None) -> str:
	if not funding_source:
		return ""
	return frappe.db.get_value("Funding Source", funding_source, "label") or funding_source


def _resolve_budget(key: str) -> Any:
	"""Resolve Budget by generated_reference or document name."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget is required"), frappe.ValidationError)
	name = frappe.db.get_value("Budget", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget", key):
		name = key
	if not name:
		frappe.throw(_("Budget {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Budget", name)


def _resolve_budget_version(key: str) -> Any:
	"""Resolve Budget Version by generated_reference or document name."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget Version is required"), frappe.ValidationError)
	name = frappe.db.get_value("Budget Version", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget Version", key):
		name = key
	if not name:
		frappe.throw(_("Budget Version {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Budget Version", name)


def _resolve_budget_line(key: str) -> Any:
	"""Resolve Budget Line by generated_reference or document name — same
	dual-lookup pattern as _resolve_budget/_resolve_budget_version. Every URL
	that carries a Budget Line uses its code (line.code, e.g. via `go("line",
	line.code)`), never the raw hash docname."""
	key = (key or "").strip()
	if not key:
		frappe.throw(_("Budget Line is required"), frappe.ValidationError)
	name = frappe.db.get_value("Budget Line", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget Line", key):
		name = key
	if not name:
		frappe.throw(_("Budget Line {0} not found").format(key), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Budget Line", name)


def _active_version(budget_name: str) -> Any | None:
	names = frappe.get_all("Budget Version", filters={"budget": budget_name, "status": "Active"}, pluck="name")
	if not names:
		return None
	if len(names) > 1:
		frappe.throw(
			_("Multiple Active Budget Versions found for this Budget"),
			frappe.ValidationError,
			title="BUDGET_CONTEXT_AMBIGUOUS",
		)
	return frappe.get_doc("Budget Version", names[0])


def _draft_version(budget_name: str) -> Any | None:
	"""At most one open (Draft or Submitted for approval) successor may exist (§6.2)."""
	names = frappe.get_all(
		"Budget Version",
		filters={"budget": budget_name, "status": ["in", ("Draft", "Submitted for approval")]},
		pluck="name",
		order_by="version_number desc",
	)
	return frappe.get_doc("Budget Version", names[0]) if names else None


def _line_position(budget_line_name: str, budget_line_version) -> dict[str, float]:
	"""§5 canonical calculation for one Budget Line at the current time.

	`budget_line_version` supplies `approved_amount`; Reserved/Committed are
	summed from the stable Budget Line identity's reservations/commitments,
	independent of which version is being displayed.
	"""
	approved = flt(budget_line_version.approved_amount) if budget_line_version else 0.0

	reserved = flt(
		frappe.db.sql(
			"select coalesce(sum(remaining_amount), 0) from `tabFunding Reservation` "
			"where budget_line = %s and status in %s",
			(budget_line_name, _ACTIVE_RESERVATION_STATUSES),
		)[0][0]
	)

	all_reservations = frappe.get_all("Funding Reservation", filters={"budget_line": budget_line_name}, pluck="name")
	committed = 0.0
	if all_reservations:
		committed = flt(
			frappe.db.sql(
				"select coalesce(sum(current_amount), 0) from `tabProcurement Commitment` "
				"where reservation in %s and status = 'Active'",
				(all_reservations,),
			)[0][0]
		)

	available = approved - reserved - committed
	return {"approved": approved, "reserved": reserved, "committed": committed, "available": available}


def _line_version_for(budget_version_name: str, budget_line_name: str):
	name = frappe.db.get_value(
		"Budget Line Version", {"budget_version": budget_version_name, "budget_line": budget_line_name}, "name"
	)
	return frappe.get_doc("Budget Line Version", name) if name else None


def _plan_item_label(plan_item: str | None) -> str:
	"""Budget Line detail's Active reservations table shows the Plan Item's
	human reference ("PPI-MOH-2027-021 · National digital health
	infrastructure upgrade"), not its raw docname. `Funding Reservation.plan_item`
	only stores kentender_procurement's own docname (a plain Data field, not a
	Link — no schema coupling), so this reads Procurement Plan Item's own
	fields directly via frappe.db, the same cross-app read pattern already used
	for Organisation Unit/Financial Year/Funding Source (reading another app's
	doctype fields via the ORM is not "deep-importing internals" — that means
	importing its Python modules)."""
	if not plan_item:
		return ""
	code = frappe.db.get_value("Procurement Plan Item", plan_item, "plan_item_code")
	if not code:
		return plan_item
	version_name = frappe.db.get_value("Procurement Plan Item", plan_item, "current_approved_item_version")
	title = frappe.db.get_value("Procurement Plan Item Version", version_name, "requirement_title") if version_name else None
	return f"{code} · {title}" if title else code


def _line_active_reservations(budget_line: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Funding Reservation",
		filters={"budget_line": budget_line, "status": ["in", _ACTIVE_RESERVATION_STATUSES]},
		fields=["name", "generated_reference", "plan_item", "original_amount", "remaining_amount", "status"],
		order_by="creation asc",
	)
	out = []
	for r in rows:
		out.append(
			{
				"id": r.name,
				"code": r.generated_reference,
				"plan_item_label": _plan_item_label(r.plan_item),
				# §12.4 "View Plan Item uses a server-returned authorised Planning
				# URL. The Budget client does not build a route from a guessed
				# naming rule." — this is Planning's own published route shape for
				# its Plan Item editor (kentender_procurement/.../get_plan_review.py
				# builds the identical string for the same doctype/page).
				"plan_item_url": f"/app/procurement-plan-item-editor/{r.plan_item}" if r.plan_item else "",
				"original_amount": flt(r.original_amount),
				"remaining_amount": flt(r.remaining_amount),
				"status": r.status,
			}
		)
	return out


def get_budget_line_position(budget_line: str, *, as_at_version: str | None = None) -> dict[str, Any]:
	"""§9.1 `get_budget_line_position` — authorised line identity, active-version
	amount and current positions. No mutation. BUD-UI-05 Budget Line detail."""
	line = _resolve_budget_line(budget_line)
	owning_version = _line_owning_version(line.name, as_at_version)
	require_budget_version_read_scope(owning_version)
	budget = frappe.get_doc("Budget", line.budget)
	version_name = as_at_version or owning_version.name
	line_version = _line_version_for(version_name, line.name) if version_name else None
	position = _line_position(line.name, line_version)
	return {
		"id": line.name,
		"code": line.generated_reference,
		"title": line_version.title if line_version else "",
		"owner_org_unit": _org_unit_label(line_version.owner_org_unit) if line_version else "",
		"funding_source": _funding_source_label(line_version.funding_source) if line_version else "",
		"currency": line_version.currency if line_version else "KES",
		"positions": position,
		"budget": {
			"id": budget.name,
			"code": budget.generated_reference,
			"procuring_entity": {"id": budget.procuring_entity, "name": _entity_label(budget.procuring_entity)},
			"financial_year": {"id": budget.financial_year, "label": _fy_label(budget.financial_year)},
		},
		"version": {
			"id": owning_version.name,
			"version_number": owning_version.version_number,
			"status": owning_version.status,
		},
		"reservations": _line_active_reservations(line.name),
	}


def _active_version_name_for_line(budget_line: str) -> str | None:
	budget_name = frappe.db.get_value("Budget Line", budget_line, "budget")
	version = _active_version(budget_name) if budget_name else None
	return version.name if version else None


def _line_owning_version(budget_line: str, as_at_version: str | None):
	version_name = as_at_version or _active_version_name_for_line(budget_line)
	if not version_name:
		frappe.throw(_("Budget Line has no resolvable version context"), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	return frappe.get_doc("Budget Version", version_name)


def _version_totals(budget_version_name: str) -> dict[str, float]:
	"""Budget totals are the sums of the Version's line positions (§5)."""
	line_versions = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": budget_version_name},
		fields=["budget_line", "approved_amount", "title", "owner_org_unit", "funding_source", "currency"],
	)
	approved = reserved = committed = available = 0.0
	lines: list[dict[str, Any]] = []
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Budget Line", filters={"name": ["in", [lv.budget_line for lv in line_versions]]}, fields=["name", "generated_reference"]
			)
		}
		if line_versions
		else {}
	)
	for lv in line_versions:
		pos = _line_position(lv.budget_line, lv)
		approved += pos["approved"]
		reserved += pos["reserved"]
		committed += pos["committed"]
		available += pos["available"]
		lines.append(
			{
				**lv,
				"code": codes.get(lv.budget_line, ""),
				"owner_org_unit_label": _org_unit_label(lv.owner_org_unit),
				"funding_source_label": _funding_source_label(lv.funding_source),
				"positions": pos,
			}
		)
	return {
		"approved": approved,
		"reserved": reserved,
		"committed": committed,
		"available": available,
		"lines": lines,
	}


def resolve_budget_context(procuring_entity: str | None = None, financial_year: str | None = None) -> dict[str, Any]:
	"""§9.1 `resolve_budget_context` — the Active Budget/Version summary for a
	PE/FY, or a typed not-found/ambiguous/ineligible error. Never a first-PE,
	first-record or Administrator fallback (BUD-BR-001)."""
	pe = resolve_scoped_entity(procuring_entity)
	if not pe:
		frappe.throw(_("No procuring entity assigned"), frappe.PermissionError, title="BUDGET_SCOPE_REQUIRED")
	fy = (financial_year or "").strip()
	if not fy:
		frappe.throw(_("Financial Year is required"), frappe.ValidationError, title="BUDGET_SCOPE_REQUIRED")
	if not frappe.db.exists("Financial Year", fy):
		frappe.throw(_("Financial Year {0} not found").format(fy), frappe.DoesNotExistError, title="BUDGET_CONFIG_MISSING")

	budget_name = frappe.db.get_value("Budget", {"procuring_entity": pe, "financial_year": fy}, "name")
	if not budget_name:
		frappe.throw(
			_("No Budget is registered for this Procuring Entity and Financial Year"),
			frappe.DoesNotExistError,
			title="BUDGET_CONTEXT_NOT_FOUND",
		)
	budget = frappe.get_doc("Budget", budget_name)
	version = _active_version(budget_name)
	if not version:
		return {"budget": _budget_summary(budget), "version": None}
	return {"budget": _budget_summary(budget), "version": _version_summary(version)}


def _budget_summary(budget) -> dict[str, Any]:
	return {
		"id": budget.name,
		"code": budget.generated_reference,
		"title": budget.title,
		"procuring_entity": {"id": budget.procuring_entity, "name": _entity_label(budget.procuring_entity)},
		"financial_year": {"id": budget.financial_year, "label": _fy_label(budget.financial_year)},
		"currency": budget.currency,
	}


def _version_summary(version) -> dict[str, Any]:
	return {
		"id": version.name,
		"code": version.generated_reference,
		"version_number": version.version_number,
		"status": version.status,
		"approval_reference": version.approval_reference,
		# ISO (yyyy-mm-dd) — the version editor binds this straight into an
		# <input type=date>. approval_date_display is the read-only sibling
		# ("30 Sep 2026") for Workspace/Detail cards; keep both in sync here
		# rather than at each call site.
		"approval_date": str(version.approval_date) if version.approval_date else "",
		"approval_date_display": _display_date(version.approval_date),
		"authorised_total": flt(version.authorised_total),
	}


def get_budget_workspace(context_id: str | None = None) -> dict[str, Any]:
	"""BUD-UI-01 — current scoped Budget and operational position, or the
	no-baseline state, for one explicit PE Fiscal Year Context (BUD-CHG-001
	v1.2 Phase 8). No longer auto-resolves "today's" Financial Year or
	guesses a single PE for the caller — the working context is resolved
	(explicit selection, remembered preference, or auto-selected when the
	caller has exactly one) by
	kentender_core.services.reference_data_resolver.resolve_working_context,
	which also correctly distinguishes an unrestricted actor (every context)
	from a scoped one (their permitted Procuring Entities only) from a
	no-access one — see that function's own docstring. When no context can
	be resolved, the response carries selection_required=True with the
	actor's own selectable contexts, instead of ever masquerading as "no
	baseline"."""
	from kentender_core.services.reference_data_resolver import resolve_working_context

	resolved = resolve_working_context("budget", requested_context=context_id)
	if resolved["selection_required"]:
		return {
			"selection_required": True,
			"mode": resolved["mode"],
			"contexts": resolved["contexts"],
		}

	selected = resolved["selected"]
	pe = selected["procuring_entity"]["id"]
	fy = selected["financial_year"]["id"]
	result: dict[str, Any] = {
		"selection_required": False,
		"context_id": selected["context_id"],
		"procuring_entity": {"id": pe, "name": _entity_label(pe)},
		"financial_year": {"id": fy, "label": _fy_label(fy)},
		"has_budget": False,
		"can_register": False,
	}

	budget_name = frappe.db.get_value("Budget", {"procuring_entity": pe, "financial_year": fy}, "name")
	if not budget_name:
		try:
			require_budget_create_capability(frappe.session.user, pe)
			result["can_register"] = True
		except frappe.PermissionError:
			pass
		return result

	budget = frappe.get_doc("Budget", budget_name)
	version = _active_version(budget_name)
	result["has_budget"] = True
	result["budget"] = _budget_summary(budget)
	if not version:
		# A Budget row exists (an Officer saved a Draft) but nothing has been
		# Activated yet — no artboard covers this directly (BUD-DES-16 "No
		# baseline" only covers "no Budget row at all"); reuse that empty-state
		# shell with a status-appropriate action instead of inventing a new
		# visual. `action` is server-decided per AGENTS.md §6.2 — the client
		# never derives it from status itself.
		pending = _draft_version(budget_name)
		if pending:
			action = None
			if has_budget_version_capability(frappe.session.user, CAP_EDIT, pending):
				action = "open_draft"
			elif pending.status == "Submitted for approval" and has_budget_version_capability(
				frappe.session.user, CAP_APPROVE, pending
			):
				action = "open_task"
			# A Viewer (no edit/approve capability on it) gets no disclosure that
			# a Draft/Submitted version exists at all — falls back to the plain
			# "No baseline" treatment client-side, matching the no-disclosure
			# principle already applied to Forbidden/failure states (§12.1).
			if action:
				result["pending_version"] = {
					"id": pending.name,
					"code": pending.generated_reference,
					"version_number": pending.version_number,
					"status": pending.status,
					"action": action,
				}
		return result

	totals = _version_totals(version.name)
	result["version"] = _version_summary(version)
	result["positions"] = {
		"approved": totals["approved"],
		"reserved": totals["reserved"],
		"committed": totals["committed"],
		"available": totals["available"],
	}
	result["can_create_revision"] = has_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	result["lines_preview"] = [_line_preview_row(row) for row in totals["lines"][:5]]
	return result


def _line_preview_row(row: dict[str, Any]) -> dict[str, Any]:
	pos = row["positions"]
	return {
		"id": row["budget_line"],
		"code": row.get("code", ""),
		"title": row["title"],
		"owner_org_unit": row.get("owner_org_unit_label", ""),
		"approved": pos["approved"],
		"reserved": pos["reserved"],
		"committed": pos["committed"],
		"available": pos["available"],
	}


def get_budget_version_draft(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-02 Overview tab — the Draft (or Submitted) version's own field
	values, for the version editor form."""
	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)
	budget = frappe.get_doc("Budget", version.budget)
	return {
		"budget": _budget_summary(budget),
		"version": _version_summary(version),
		"based_on": _version_summary(frappe.get_doc("Budget Version", version.based_on_budget_version))
		if version.based_on_budget_version
		else None,
		"revision_type": version.revision_type or "",
		"approval_document": version.approval_document or "",
		"can_edit": version.status == "Draft" and has_budget_version_capability(frappe.session.user, CAP_EDIT, version),
	}


def get_budget_detail(budget: str) -> dict[str, Any]:
	"""BUD-UI-03 Overview tab — Active/read-only funding position + context."""
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	version = _active_version(doc.name)
	if not version:
		frappe.throw(_("No Active Budget Version"), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	require_budget_version_read_scope(version)
	totals = _version_totals(version.name)
	return {
		"budget": _budget_summary(doc),
		"version": _version_summary(version),
		"positions": {
			"approved": totals["approved"],
			"reserved": totals["reserved"],
			"committed": totals["committed"],
			"available": totals["available"],
		},
		"approval_document": version.approval_document,
		"activation": {
			"submitted_by": _user_label(version.submitted_by),
			"submitted_at": _display_datetime(version.submitted_at),
			"decided_by": _user_label(version.decided_by),
			"decided_at": _display_datetime(version.decided_at),
		},
		"can_create_revision": has_budget_version_capability(frappe.session.user, CAP_EDIT, version),
	}


def _validate_draft_payload(payload: dict) -> dict[str, str]:
	errors: dict[str, str] = {}
	approval_reference = (payload.get("approval_reference") or "").strip()
	approval_date = payload.get("approval_date")
	total = payload.get("authorised_total")

	if not approval_reference:
		errors["approval_reference"] = _("Approval reference is required")
	if not approval_date:
		errors["approval_date"] = _("Approval date is required")
	else:
		try:
			if getdate(approval_date) > getdate():
				errors["approval_date"] = _("Approval date cannot be in the future")
		except Exception:
			errors["approval_date"] = _("Enter a valid approval date")
	try:
		total_val = flt(total)
	except Exception:
		total_val = 0
	if not total or total_val <= 0:
		errors["authorised_total"] = _("Authorised total must be greater than zero")
	return errors


def save_budget_version_draft(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `save_budget_version_draft` — create or update Draft approval
	details with optimistic concurrency. Creates the Budget on first save."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	budget_key = (payload.get("budget") or "").strip()
	version_key = (payload.get("budget_version") or "").strip()

	if not budget_key and not version_key:
		# BUD-CHG-001 v1.2 Phase 8 — the caller supplies the PE/FY as one
		# explicit context_id (the working context it already selected via
		# WorkingContextPicker), not a loose procuring_entity/financial_year
		# pair. validate_context_for_command replaces the old inline
		# existence+Active check with the shared kentender_core primitive
		# every state-changing command should use (Active-only — creating a
		# Budget against a Scheduled or Closed context is not allowed, even
		# though *viewing* one is fine for history/preparation).
		from kentender_core.services.reference_data_resolver import validate_context_for_command

		context_id = (payload.get("context_id") or "").strip()
		if not context_id:
			return {"ok": False, "errors": {"context_id": _("A Procuring Entity / Financial Year context is required")}}
		validate_context_for_command(frappe.session.user, context_id)
		pe, fy = frappe.db.get_value("PE Fiscal Year Context", context_id, ["procuring_entity", "financial_year"])
		require_budget_create_capability(frappe.session.user, pe)
		if frappe.db.exists("Budget", {"procuring_entity": pe, "financial_year": fy}):
			frappe.throw(
				_("A Budget already exists for this Procuring Entity and Financial Year"),
				frappe.DuplicateEntryError,
				title="BUDGET_ALREADY_EXISTS",
			)
		errors = _validate_draft_payload(payload)
		if errors:
			return {"ok": False, "errors": errors}

		budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": allocate_budget_reference(pe, fy),
				"procuring_entity": pe,
				"financial_year": fy,
				"currency": (payload.get("currency") or "KES").strip(),
			}
		)
		budget.insert(ignore_permissions=True)
		version = _create_draft_version(budget, payload, based_on=None)
		return {"ok": True, "budget": _budget_summary(budget), "version": _version_summary(version)}

	if version_key:
		version = _resolve_budget_version(version_key)
	else:
		budget = _resolve_budget(budget_key)
		version = _draft_version(budget.name)
		if not version:
			frappe.throw(_("No Draft Budget Version to update"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	require_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	if version.status != "Draft":
		frappe.throw(_("Only a Draft version can be edited"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	expected_version = payload.get("expected_modified")
	if expected_version and str(version.modified) != str(expected_version):
		frappe.throw(_("This Budget Version was changed by someone else"), frappe.ValidationError, title="BUDGET_STALE_WRITE")

	errors = _validate_draft_payload(payload)
	if errors:
		return {"ok": False, "errors": errors}

	version.approval_reference = (payload.get("approval_reference") or "").strip()
	version.approval_date = getdate(payload.get("approval_date"))
	version.authorised_total = flt(payload.get("authorised_total"))
	if payload.get("approval_document"):
		version.approval_document = payload["approval_document"]
	if version.based_on_budget_version and payload.get("revision_type"):
		version.revision_type = payload["revision_type"]
	version.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_DRAFT_APPROVAL_SAVED, safe_record_event

	safe_record_event(
		budget=version.budget,
		budget_version=version.name,
		event_type=EVENT_DRAFT_APPROVAL_SAVED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)
	return {"ok": True, "version": _version_summary(version)}


def _create_draft_version(budget, payload: dict, *, based_on) -> Any:
	next_number = (
		frappe.db.count("Budget Version", {"budget": budget.name}) + 1
		if not based_on
		else (based_on.version_number + 1)
	)
	version = frappe.get_doc(
		{
			"doctype": "Budget Version",
			"generated_reference": allocate_budget_version_reference(budget.generated_reference, next_number),
			"budget": budget.name,
			"version_number": next_number,
			"based_on_budget_version": based_on.name if based_on else None,
			"revision_type": payload.get("revision_type") if based_on else None,
			"status": "Draft",
			"approval_reference": (payload.get("approval_reference") or "").strip(),
			"approval_date": getdate(payload.get("approval_date")) if payload.get("approval_date") else None,
			"authorised_total": flt(payload.get("authorised_total")) if payload.get("authorised_total") else None,
			"approval_document": payload.get("approval_document") or None,
			"currency": budget.currency,
			"submitted_by": None,
		}
	)
	version.insert(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_VERSION_CREATED, safe_record_event

	safe_record_event(
		budget=budget.name,
		budget_version=version.name,
		event_type=EVENT_VERSION_CREATED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)

	if based_on:
		_copy_line_versions(based_on, version)
	return version


def _copy_line_versions(source_version, target_version) -> None:
	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": source_version.name},
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount", "currency"],
	)
	for row in rows:
		line_code = frappe.db.get_value("Budget Line", row.budget_line, "generated_reference")
		frappe.get_doc(
			{
				"doctype": "Budget Line Version",
				"generated_reference": allocate_budget_line_version_reference(line_code, target_version.version_number),
				"budget_version": target_version.name,
				"budget_line": row.budget_line,
				"title": row.title,
				"owner_org_unit": row.owner_org_unit,
				"funding_source": row.funding_source,
				"approved_amount": row.approved_amount,
				"currency": row.currency,
			}
		).insert(ignore_permissions=True)


def create_budget_successor_version(budget: str, payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `create_budget_successor_version` — copy the current Active
	Version and line identities into one Draft successor. At most one open
	successor may exist (§6.2)."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	doc = _resolve_budget(budget)
	active = _active_version(doc.name)
	if not active:
		frappe.throw(_("No Active Budget Version to revise"), frappe.ValidationError, title="BUDGET_INVALID_STATE")
	require_budget_version_capability(frappe.session.user, CAP_EDIT, active)

	existing_draft = _draft_version(doc.name)
	if existing_draft:
		return {"ok": True, "version": _version_summary(existing_draft), "existing": True}

	# approval_reference/date/authorised_total/approval_document are DB-mandatory
	# on Budget Version from the first insert (see BudgetVersionEditorScreen.vue's
	# own note on this for the baseline case). A successor has no pre-creation
	# form (BUD-DES-14/15 only exist post-creation) — seed these from the prior
	# Active version, matching how _copy_line_versions seeds the line data; the
	# Officer edits them in the tabbed editor before Save/Submit.
	seeded = {
		"approval_reference": payload.get("approval_reference") or active.approval_reference,
		"approval_date": payload.get("approval_date") or str(active.approval_date),
		"authorised_total": payload.get("authorised_total") or active.authorised_total,
		"approval_document": payload.get("approval_document") or active.approval_document,
		"revision_type": payload.get("revision_type"),
	}
	version = _create_draft_version(doc, seeded, based_on=active)
	return {"ok": True, "version": _version_summary(version)}
