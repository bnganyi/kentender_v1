"""CTX-CHG-001 — the working context: global PE preference + per-module FY/OU.

One service owns *persistence and resolution* of the user's working context;
each module keeps *eligibility* (what it may offer). The durable rule:
permissions determine what the user may access; context only filters what the
user is currently working on — it is visible, reversible, module-appropriate
and never authoritative. Every resolution therefore re-validates against the
caller's live eligibility; a saved value that is no longer offered resolves to
"unselected" (prompt again), never to access and never to an error.

Persistence is ``frappe.defaults`` under three snake_case key families:

- ``kt_working_procuring_entity``           — one global PE per user;
- ``kt_{module}_financial_year``            — one FY per module per user;
- ``kt_{module}_org_unit``                  — one OU per module per user.

The keys MUST stay scrub-stable (``key == frappe.scrub(key)``):
``frappe.defaults.get_user_default()`` silently fails to round-trip a
Title-Case/spaced key — ``is_a_user_permission_key()`` (frappe/defaults.py)
treats any key where ``key != frappe.scrub(key)`` as a User-Permission-backed
key and resolves it through that separate mechanism instead of returning the
stored value. Confirmed live twice in this repo: Budget's original
"KT Budget Working Context" experiment, and Planning's "KT Planning Procuring
Entity"/"KT Planning Financial Year" keys, which never restored at all.
``_module_key`` asserts the property so a regression cannot ship quietly.

PE eligibility has exactly one rule —
:func:`kentender_core.services.org_scope_access.permitted_procuring_entities`
(``None`` = unrestricted) intersected with Active Procuring Entities. Modules
may *narrow* the offer they present, never widen it. FY eligibility stays
module-owned: the module passes its offered list via ``offered=`` (Needs
filters by Financial Year User Permissions; Planning speaks ERPNext labels);
:func:`default_fy_options` provides the registry-backed default (the
``PE Fiscal Year Context`` rows for the PE) for modules without special
vocabulary.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

GLOBAL_PE_KEY = "kt_working_procuring_entity"

# Dimensions a module may remember. A fixed vocabulary keeps the defaults
# namespace enumerable (patches can find every key) and typo-proof.
_DIMENSIONS = ("financial_year", "org_unit")


def _module_key(module: str, dimension: str) -> str:
	if dimension not in _DIMENSIONS:
		raise ValueError(f"Unknown working-context dimension {dimension!r}")
	key = f"kt_{cstr(module).strip().lower()}_{dimension}"
	if key != frappe.scrub(key):
		# A non-scrub-stable key would silently stop round-tripping through
		# frappe.defaults (see module docstring) — refuse loudly instead.
		raise ValueError(f"Working-context key {key!r} is not scrub-stable")
	return key


def _get_default(key: str, user: str) -> str | None:
	return cstr(frappe.defaults.get_user_default(key, user=user)).strip() or None


def _set_default(key: str, value: str, user: str) -> None:
	frappe.defaults.set_user_default(key, value, user=user)


# --- Procuring Entity (global) ---------------------------------------------


def pe_label(pe_id: str) -> str:
	"""One canonical display name for a Procuring Entity.

	The repo reads ``legal_name`` in some modules and ``entity_name`` in
	others (with per-module feature detection); this is the one place that
	decides. ``legal_name`` wins, then ``entity_name``, then the id.
	"""
	meta = frappe.get_meta("Procuring Entity")
	fields = [f for f in ("legal_name", "entity_name") if meta.has_field(f)]
	if not fields:
		return cstr(pe_id)
	row = frappe.db.get_value("Procuring Entity", pe_id, fields, as_dict=True)
	if not row:
		return cstr(pe_id)
	for field in fields:
		if cstr(row.get(field)).strip():
			return cstr(row.get(field)).strip()
	return cstr(pe_id)


def _pe_snapshot(row: Any) -> dict[str, Any]:
	return {
		"id": row.name,
		"code": cstr(getattr(row, "entity_code", "") or row.name),
		"name": cstr(getattr(row, "legal_name", "") or "").strip()
		or cstr(getattr(row, "entity_name", "") or "").strip()
		or row.name,
	}


def pe_options(user: str | None = None) -> dict[str, Any]:
	"""The Procuring Entities `user` may work in, plus a mode tag.

	Modes: "unrestricted" (Administrator/System Manager — every Active PE),
	"single", "multiple", "none". The one canonical eligibility rule is
	``permitted_procuring_entities`` (None = unrestricted); only Active
	entities are offered as a *working* context — a Suspended or Retired PE
	stays reachable through record links and module reads where their own
	rules allow, it is simply not offered as the place to work next.
	"""
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	user = user or frappe.session.user
	pes = permitted_procuring_entities(user)
	filters: dict[str, Any] = {"status": "Active"}
	if pes is not None:
		if not pes:
			return {"mode": "none", "options": []}
		filters["name"] = ["in", sorted(pes)]
	meta = frappe.get_meta("Procuring Entity")
	fields = ["name"] + [f for f in ("entity_code", "legal_name", "entity_name") if meta.has_field(f)]
	rows = frappe.get_all("Procuring Entity", filters=filters, fields=fields, order_by="name asc")
	options = [_pe_snapshot(row) for row in rows]
	if pes is None:
		mode = "unrestricted"
	elif not options:
		mode = "none"
	elif len(options) == 1:
		mode = "single"
	else:
		mode = "multiple"
	return {"mode": mode, "options": options}


def get_working_pe(user: str | None = None, *, requested: str | None = None) -> dict[str, Any]:
	"""Resolve the caller's global working Procuring Entity.

	Resolution order (never authoritative, revalidated on every call):
	explicit ``requested`` (validated against the offer, then persisted — a
	deep link is a deliberate choice) → the saved preference if still
	offered → auto-select when exactly one option exists → ``None`` with
	``selection_required``. ``can_switch`` is the rail-visibility rule: the
	switcher renders only when the user can genuinely switch.
	"""
	user = user or frappe.session.user
	offer = pe_options(user)
	by_id = {opt["id"]: opt for opt in offer["options"]}

	requested = cstr(requested).strip() or None
	selected = None
	if requested:
		selected = by_id.get(requested)
		if not selected:
			frappe.throw(
				"This Procuring Entity is not available to you.",
				frappe.PermissionError,
				title="KT_PE_NOT_AUTHORIZED",
			)
		_set_default(GLOBAL_PE_KEY, selected["id"], user)

	if not selected:
		saved = _get_default(GLOBAL_PE_KEY, user)
		if saved:
			selected = by_id.get(saved)

	if not selected and len(offer["options"]) == 1:
		selected = offer["options"][0]

	return {
		"mode": offer["mode"],
		"options": offer["options"],
		"selected": selected,
		"selection_required": selected is None and offer["mode"] != "none",
		"can_switch": offer["mode"] == "unrestricted" or len(offer["options"]) > 1,
	}


def select_working_pe(pe_id: str, user: str | None = None) -> dict[str, Any]:
	"""Persist `pe_id` as the caller's global working PE, after validating it
	is offered. Stores a preference only — never an authorization grant."""
	return get_working_pe(user, requested=cstr(pe_id).strip())


# --- Financial Year (per module) -------------------------------------------


def default_fy_options(procuring_entity: str) -> list[dict[str, Any]]:
	"""Registry-backed FY offer for one PE: its non-Suspended
	``PE Fiscal Year Context`` rows, newest year first. Scheduled/Active/
	Closed are all selectable — preparing an upcoming FY or reviewing a prior
	one are normal work; "today" is only ever a default suggestion."""
	pe = cstr(procuring_entity).strip()
	if not pe:
		return []
	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": pe, "context_status": ["!=", "Suspended"]},
		fields=["name", "financial_year", "context_status"],
		order_by="financial_year desc",
	)
	options = []
	for row in rows:
		fy = frappe.db.get_value(
			"Financial Year", row.financial_year, ["label", "start_date", "end_date"], as_dict=True
		)
		options.append(
			{
				"id": row.financial_year,
				"label": cstr(fy.label) if fy else row.financial_year,
				"start_date": str(fy.start_date) if fy else None,
				"end_date": str(fy.end_date) if fy else None,
				"context_id": row.name,
				"context_status": row.context_status,
			}
		)
	return options


def _normalize_options(offered: list[Any]) -> list[dict[str, Any]]:
	out = []
	for item in offered or []:
		if isinstance(item, dict):
			identifier = cstr(item.get("id")).strip()
			if identifier:
				out.append({**item, "id": identifier})
		else:
			identifier = cstr(item).strip()
			if identifier:
				out.append({"id": identifier, "label": identifier})
	return out


def _resolve_module_dimension(
	module: str,
	dimension: str,
	user: str,
	*,
	requested: str | None,
	offered: list[dict[str, Any]],
	not_offered_title: str,
) -> dict[str, Any]:
	key = _module_key(module, dimension)
	by_id = {opt["id"]: opt for opt in offered}

	requested = cstr(requested).strip() or None
	selected = None
	if requested:
		selected = by_id.get(requested)
		if not selected:
			frappe.throw(
				"This selection is not available to you.",
				frappe.PermissionError,
				title=not_offered_title,
			)
		_set_default(key, selected["id"], user)

	if not selected:
		saved = _get_default(key, user)
		if saved:
			selected = by_id.get(saved)

	if not selected and len(offered) == 1:
		selected = offered[0]

	return {
		"options": offered,
		"selected": selected,
		"selection_required": selected is None and bool(offered),
	}


def get_module_fy(
	module: str,
	user: str | None = None,
	*,
	requested: str | None = None,
	offered: list[Any] | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""Resolve `module`'s remembered Financial Year within the offered list.

	``offered`` is the module's own eligibility (opaque ids or option dicts);
	when omitted, the registry-backed :func:`default_fy_options` for
	``procuring_entity`` applies. Core validates membership, remembers and
	auto-selects — it never invents eligibility.
	"""
	user = user or frappe.session.user
	options = _normalize_options(
		offered if offered is not None else default_fy_options(cstr(procuring_entity))
	)
	return _resolve_module_dimension(
		module,
		"financial_year",
		user,
		requested=requested,
		offered=options,
		not_offered_title="KT_FY_NOT_OFFERED",
	)


def select_module_fy(
	module: str,
	fy_id: str,
	user: str | None = None,
	*,
	offered: list[Any] | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	return get_module_fy(
		module,
		user,
		requested=cstr(fy_id).strip(),
		offered=offered,
		procuring_entity=procuring_entity,
	)


# --- Organisation Unit (per module; Departmental Needs) ---------------------


def get_module_ou(
	module: str,
	user: str | None = None,
	*,
	requested: str | None = None,
	offered: list[Any] | None = None,
) -> dict[str, Any]:
	"""Resolve `module`'s remembered Organisation Unit within ``offered``.

	Unlike FY there is no registry default: the module always supplies its
	own eligible units (Needs derives them from its viewing contexts).
	"""
	user = user or frappe.session.user
	return _resolve_module_dimension(
		module,
		"org_unit",
		user,
		requested=requested,
		offered=_normalize_options(offered or []),
		not_offered_title="KT_OU_NOT_OFFERED",
	)


def select_module_ou(
	module: str, ou_id: str, user: str | None = None, *, offered: list[Any] | None = None
) -> dict[str, Any]:
	return get_module_ou(module, user, requested=cstr(ou_id).strip(), offered=offered)
