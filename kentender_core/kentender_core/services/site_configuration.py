# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.9 §5–§8 — site configuration commands.

One site is one Procuring Entity, configured once at first run and never
selected afterwards. Fiscal years are ERPNext `Fiscal Year` records extended
only by namespaced custom fields; departmental-needs intake is a flag on the
applicable year, open for at most one year at any instant.

Every command here takes effect on save — no draft, submission, review or
approval state exists (CFG-BR-012). Atomicity is the request transaction:
any `fail_cfg` rolls back everything, and no function in this module calls
`frappe.db.commit()`.
"""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.configuration_errors import fail_cfg
from kentender_core.services.reference_data_idempotency import run_idempotent
from kentender_core.utils.display import display_datetime, display_period

SITE_PE_DOCTYPE = "Site Procuring Entity"
FY_DOCTYPE = "Fiscal Year"
UNIT_DOCTYPE = "Organisation Unit"

FLAG_OPEN = "kentender_needs_submission_open"
FLAG_CLOSES_AT = "kentender_needs_submission_closes_at"
FLAG_CHANGED_BY = "kentender_flag_changed_by"
FLAG_CHANGED_AT = "kentender_flag_changed_at"

# CFG-CHG-002 v0.9 §4.2 — the departmental-plan intake flag follows the same
# pattern as needs intake (CFG-BR-013: at most one year open, independent of
# the needs flag). Procurement Planning reads it and never writes it.
DPP_FLAG_OPEN = "kentender_dpp_submission_open"
DPP_FLAG_CLOSES_AT = "kentender_dpp_submission_closes_at"

# CFG-CHG-002 v0.9 §4.1 / CFG-BR-014 — the statutory approval route above the
# accounting officer (regulation 40(4); Third Schedule signature block). Four
# values, no `None`: exactly one route applies to every entity.
STATUTORY_APPROVAL_ROUTES: tuple[str, ...] = (
	"Cabinet Secretary",
	"County Executive Committee Member",
	"Board of Directors",
	"Council",
)
# The route derived from the entity type when a first-run configure command
# does not name one (the System setup artboards carry no route control yet);
# it is editable afterwards through `update_procuring_entity` and is never
# blank. Recorded as PLN tracker D10.
_ROUTE_BY_PE_TYPE: dict[str, str] = {
	"National Government Ministry": "Cabinet Secretary",
	"State Department": "Cabinet Secretary",
	"Constitutional Commission": "Cabinet Secretary",
	"Other Public Entity": "Cabinet Secretary",
	"State Corporation": "Board of Directors",
	"County Corporation": "Board of Directors",
	"County Government": "County Executive Committee Member",
	"Public University": "Council",
}
_COUNTY_PE_TYPES: frozenset[str] = frozenset({"County Government", "County Corporation"})

PE_TYPES: tuple[str, ...] = (
	"National Government Ministry",
	"State Department",
	"State Corporation",
	"County Government",
	"County Corporation",
	"Constitutional Commission",
	"Public University",
	"Other Public Entity",
)

_PE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,19}$")

# KenTender records that reference a Fiscal Year, consulted by the disable
# guard (CFG-BR-010). Modules append entries here in their cutover slices —
# pre-cutover the rest still read the legacy year store.
KT_FISCAL_YEAR_REFERENCES: tuple[tuple[str, str], ...] = (
	# CU-305 — Strategy's performance targets bind to the canonical year.
	("Performance Target", "financial_year_id"),
	# NDS-CHG-001 v1.6 §16.4.11 — Departmental Needs binds to the canonical
	# year (retired its own bespoke `Financial Year` doctype).
	("Departmental Need", "financial_year"),
	# PLN-CHG-001 v1.12 §4.2/§4.7 — Procurement Planning binds its two roots
	# to the canonical year (D7). Guarded by column presence in
	# `_reference_count` until the Planning cutover lands.
	("Departmental Plan", "fiscal_year"),
	("Annual Plan", "fiscal_year"),
)


def require_configuration_administrator(actor: str | None = None) -> str:
	"""CFG §6 — Administrator and System Manager maintain configuration."""
	principal = actor or frappe.session.user
	if principal != "Administrator" and "System Manager" not in set(frappe.get_roles(principal)):
		fail_cfg("CFG_AUTHORITY_REQUIRED")
	return principal


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------


def is_configured() -> bool:
	return bool(frappe.db.get_single_value(SITE_PE_DOCTYPE, "pe_code"))


def get_site_configuration() -> dict[str, Any]:
	"""§7 `GetSiteConfiguration` — safe for any authenticated actor.

	One call answers: the site identity, whether the root Organisation Unit
	exists, and which year (if any) has needs submission open.
	"""
	if (frappe.session.user or "Guest") == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	single = frappe.get_cached_doc(SITE_PE_DOCTYPE)
	configured = bool(single.pe_code)
	root = _root_unit()
	open_year = _open_intake_year() if _flag_fields_ready() else None
	dpp_year = _open_intake_year(DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT) if _dpp_flag_fields_ready() else None

	return {
		"configured": configured,
		"procuring_entity": {
			"pe_name": single.pe_name or "",
			"pe_code": single.pe_code or "",
			"pe_type": single.pe_type or "",
			"ppra_registration": single.ppra_registration or "",
			"timezone": single.timezone or "Africa/Nairobi",
			"statutory_approval_route": single.get("statutory_approval_route") or "",
			"entity_is_county": bool(single.get("entity_is_county")),
			"configured_by": single.configured_by or "",
			"configured_at": str(single.configured_at or ""),
			"configured_at_label": display_datetime(single.configured_at),
			"expected_version": str(single.modified or ""),
		}
		if configured
		else None,
		"pe_types": list(PE_TYPES),
		"timezones": _timezone_options(single.timezone or "Africa/Nairobi"),
		"root_unit": root,
		"needs_submission": (
			{
				"fiscal_year": open_year["name"],
				"label": _fy_label(open_year["year_start_date"]),
				"closes_at": str(open_year.get(FLAG_CLOSES_AT) or ""),
			}
			if open_year
			else None
		),
		"dpp_submission": (
			{
				"fiscal_year": dpp_year["name"],
				"label": _fy_label(dpp_year["year_start_date"]),
				"closes_at": str(dpp_year.get(DPP_FLAG_CLOSES_AT) or ""),
			}
			if dpp_year
			else None
		),
		"statutory_approval_routes": list(STATUTORY_APPROVAL_ROUTES),
		"timezone": (single.timezone or "Africa/Nairobi"),
	}


# KT-STD-001 v1.2 §3A — the technical-access gate for the System setup page
# itself. `get_site_configuration` above stays open to any authenticated
# caller (it is also used by Departmental Needs and Strategy for cross-module
# reads); this wrapper is the page-load verdict for the System setup surface
# specifically, resolved as data rather than a Page-role framework denial.
FORBIDDEN = {
	"heading": "You do not have access to System setup",
	"text": "This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it.",
}


def get_system_setup_workspace() -> dict[str, Any]:
	user = frappe.session.user
	if user != "Administrator" and "System Manager" not in frappe.get_roles(user):
		return {"outcome": "FORBIDDEN", "forbidden": FORBIDDEN}
	return {"outcome": "OK", **get_site_configuration()}


def get_dpp_submission_state(fiscal_year: str = "") -> dict[str, Any]:
	"""CFG v0.9 §11.5 — the departmental-plan intake flag as modules read it.

	Read-only. With a Fiscal Year: that year's flag and close instant. Without:
	the one open year, if any. Never a permission dimension (PLN v1.12 §4.1).
	"""
	if not _dpp_flag_fields_ready():
		return {"fiscal_year": fiscal_year or "", "open": False, "closes_at": "", "installed": False}
	if fiscal_year:
		row = frappe.db.get_value(
			FY_DOCTYPE, fiscal_year, ["name", "year_start_date", DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT], as_dict=True
		)
		if not row:
			return {"fiscal_year": fiscal_year, "open": False, "closes_at": "", "installed": True}
		closes = row.get(DPP_FLAG_CLOSES_AT)
		is_open = bool(row.get(DPP_FLAG_OPEN)) and not (closes and get_datetime(closes) <= now_datetime())
		return {
			"fiscal_year": row["name"],
			"label": _fy_label(row["year_start_date"]),
			"open": is_open,
			"closes_at": str(closes or "") if is_open else "",
			"closes_label": display_datetime(closes) if is_open and closes else "",
			"installed": True,
		}
	open_year = _open_intake_year(DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT)
	if not open_year:
		return {"fiscal_year": "", "open": False, "closes_at": "", "installed": True}
	return get_dpp_submission_state(open_year["name"])


def _timezone_options(current: str) -> list[str]:
	"""CFG-DES-01 draws Timezone as a dropdown; the offer is the IANA set."""
	import zoneinfo

	zones = sorted(zoneinfo.available_timezones())
	if current and current not in zones:
		zones.insert(0, current)
	return zones


def _root_unit() -> dict[str, Any] | None:
	row = frappe.db.get_value(
		UNIT_DOCTYPE,
		{"parent_organisation_unit": ("is", "not set")},
		["name", "unit_code", "unit_name", "status"],
		as_dict=True,
	)
	if not row:
		return None
	return {
		"id": row.name,
		"code": row.unit_code,
		"name": row.unit_name,
		"status": row.status,
	}


def list_fiscal_years() -> dict[str, Any]:
	"""§7 `ListFiscalYears` — years with derived phase and intake state.

	Ordered by `year_start_date` descending (§11.3). Phase is derived from
	the request date; no `is_current` field exists (§4.2).
	"""
	require_configuration_administrator()
	fields = ["name", "year", "year_start_date", "year_end_date", "disabled", "modified"]
	if _flag_fields_ready():
		fields += [FLAG_OPEN, FLAG_CLOSES_AT]
	if _dpp_flag_fields_ready():
		fields += [DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT]
	rows = frappe.get_all(
		FY_DOCTYPE,
		fields=fields,
		order_by="year_start_date desc",
		limit_page_length=0,
	)
	today = getdate()
	out = []
	for row in rows:
		start, end = getdate(row["year_start_date"]), getdate(row["year_end_date"])
		phase = "Current" if start <= today <= end else ("Upcoming" if start > today else "Past")
		open_flag = bool(row.get(FLAG_OPEN))
		dpp_open = bool(row.get(DPP_FLAG_OPEN))
		out.append(
			{
				"fiscal_year": row["name"],
				"label": _fy_label(row["year_start_date"]),
				"year_start_date": str(row["year_start_date"]),
				"year_end_date": str(row["year_end_date"]),
				"period_label": display_period(start, end),
				"phase": phase,
				"disabled": bool(row.get("disabled")),
				"needs_submission_open": open_flag,
				"needs_submission_closes_at": str(row.get(FLAG_CLOSES_AT) or "") if open_flag else "",
				"needs_submission_closes_label": (
					display_datetime(row.get(FLAG_CLOSES_AT)) if open_flag else ""
				),
				"dpp_submission_open": dpp_open,
				"dpp_submission_closes_at": str(row.get(DPP_FLAG_CLOSES_AT) or "") if dpp_open else "",
				"dpp_submission_closes_label": (
					display_datetime(row.get(DPP_FLAG_CLOSES_AT)) if dpp_open else ""
				),
				"reference_count": _reference_count(row["name"]),
				"expected_version": str(row["modified"]),
			}
		)
	return {"fiscal_years": out, "count": len(out)}


def preview_fiscal_year(start_year: int) -> dict[str, Any]:
	"""The server-computed dialog summary (§11.3) — writes nothing."""
	require_configuration_administrator()
	start_year = _valid_start_year(start_year)
	name = _fy_name(start_year)
	return {
		"fiscal_year": name,
		"label": f"FY {start_year}/{str(start_year + 1)[-2:]}",
		"year_start_date": f"{start_year}-07-01",
		"year_end_date": f"{start_year + 1}-06-30",
		"period_label": display_period(f"{start_year}-07-01", f"{start_year + 1}-06-30"),
		"exists": bool(frappe.db.exists(FY_DOCTYPE, name)),
	}


# --------------------------------------------------------------------------
# Commands — site Procuring Entity
# --------------------------------------------------------------------------


def configure_procuring_entity(
	*,
	pe_name: str,
	pe_code: str,
	pe_type: str,
	ppra_registration: str = "",
	timezone: str = "Africa/Nairobi",
	statutory_approval_route: str = "",
	entity_is_county: bool | None = None,
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""§7 `ConfigureProcuringEntity` — first-run configuration.

	Creates the site PE and its root Organisation Unit in one transaction
	(CFG-BR-003); a failure leaves neither (CFG-AC-002). Rejected once a PE
	exists (CFG-BR-001) — reconfiguration is `update_procuring_entity`.
	"""
	actor = require_configuration_administrator()

	def _do() -> dict[str, Any]:
		if is_configured():
			fail_cfg("CFG_PE_ALREADY_CONFIGURED")
		code = (pe_code or "").strip().upper()
		name = " ".join((pe_name or "").split())
		if not _PE_CODE_PATTERN.fullmatch(code):
			fail_cfg("CFG_PE_INVALID", "Enter an uppercase entity code of 3–20 letters, digits or hyphens.")
		if not (2 <= len(name) <= 200):
			fail_cfg("CFG_PE_INVALID", "Enter the entity's official legal name (2–200 characters).")
		if pe_type not in PE_TYPES:
			fail_cfg("CFG_PE_INVALID", "Select the entity type.")
		route = _valid_route(statutory_approval_route, pe_type)
		county = _COUNTY_PE_TYPES.__contains__(pe_type) if entity_is_county is None else bool(entity_is_county)

		single = frappe.get_doc(SITE_PE_DOCTYPE)
		single.pe_name = name
		single.pe_code = code
		single.pe_type = pe_type
		single.ppra_registration = (ppra_registration or "").strip()
		single.timezone = (timezone or "Africa/Nairobi").strip() or "Africa/Nairobi"
		single.statutory_approval_route = route
		single.entity_is_county = 1 if county else 0
		single.configured_by = actor
		single.configured_at = now_datetime()
		single.save(ignore_permissions=True)

		root = _ensure_root_unit(name, code)

		correlation = frappe.generate_hash(length=12)
		log_audit_event(
			event_type="site_configuration",
			document_type=SITE_PE_DOCTYPE,
			document_name=SITE_PE_DOCTYPE,
			action="configure_procuring_entity",
			metadata={
				"pe_code": code,
				"pe_name": name,
				"root_unit": root["id"],
				"root_created": root["created"],
				"correlation_id": correlation,
			},
		)
		return {
			"configured": True,
			"pe_code": code,
			"root_unit": root["id"],
			"correlation_id": correlation,
		}

	return run_idempotent(
		idempotency_key, SITE_PE_DOCTYPE, SITE_PE_DOCTYPE, "configure_procuring_entity", _do
	)


def update_procuring_entity(*, payload: dict[str, Any], expected_version: str = "") -> dict[str, Any]:
	"""§7 `UpdateProcuringEntity` — editable descriptive fields only.

	`pe_code` in the payload is rejected outright (CFG-BR-002); the framework
	Version record captures every change (§12).
	"""
	require_configuration_administrator()
	if not is_configured():
		fail_cfg("CFG_PE_NOT_CONFIGURED")
	payload = payload or {}
	single = frappe.get_doc(SITE_PE_DOCTYPE)
	if "pe_code" in payload and (payload["pe_code"] or "").strip().upper() != (single.pe_code or ""):
		fail_cfg("CFG_PE_CODE_IMMUTABLE")
	if expected_version and str(single.modified) != str(expected_version):
		fail_cfg("CFG_VERSION_CONFLICT")

	before = {
		field: single.get(field)
		for field in (
			"pe_name",
			"pe_type",
			"ppra_registration",
			"timezone",
			"statutory_approval_route",
			"entity_is_county",
		)
	}
	if "pe_name" in payload:
		name = " ".join((payload["pe_name"] or "").split())
		if not (2 <= len(name) <= 200):
			fail_cfg("CFG_PE_INVALID", "Enter the entity's official legal name (2–200 characters).")
		single.pe_name = name
	if "pe_type" in payload:
		if payload["pe_type"] not in PE_TYPES:
			fail_cfg("CFG_PE_INVALID", "Select the entity type.")
		single.pe_type = payload["pe_type"]
	if "ppra_registration" in payload:
		single.ppra_registration = (payload["ppra_registration"] or "").strip()
	if "timezone" in payload:
		single.timezone = (payload["timezone"] or "").strip() or "Africa/Nairobi"
	if "statutory_approval_route" in payload:
		single.statutory_approval_route = _valid_route(payload["statutory_approval_route"], single.pe_type)
	if "entity_is_county" in payload:
		single.entity_is_county = 1 if payload["entity_is_county"] else 0
	if not single.get("statutory_approval_route"):
		# A site configured before v0.9 carries no route yet; derive it once
		# so the record never saves without one (CFG-BR-014).
		single.statutory_approval_route = _valid_route("", single.pe_type)
	single.save(ignore_permissions=True)

	after = {field: single.get(field) for field in before}
	log_audit_event(
		event_type="site_configuration",
		document_type=SITE_PE_DOCTYPE,
		document_name=SITE_PE_DOCTYPE,
		action="update_procuring_entity",
		metadata={"before": before, "after": after},
	)
	return {"updated": True, "expected_version": str(single.modified)}


def repair_organisation_root(*, idempotency_key: str = "") -> dict[str, Any]:
	"""§7 `RepairOrganisationRoot` — recreate a missing root, disturb nothing.

	No effect while a root exists. Existing parentless units are adopted
	beneath the recreated root so their subtrees keep their meaning.
	"""
	require_configuration_administrator()

	def _do() -> dict[str, Any]:
		if not is_configured():
			fail_cfg("CFG_PE_NOT_CONFIGURED")
		single = frappe.get_cached_doc(SITE_PE_DOCTYPE)
		result = _ensure_root_unit(single.pe_name, single.pe_code)
		if result["created"]:
			log_audit_event(
				event_type="site_configuration",
				document_type=UNIT_DOCTYPE,
				document_name=result["id"],
				action="repair_organisation_root",
				metadata={"adopted": result["adopted"]},
			)
		return result

	return run_idempotent(
		idempotency_key, UNIT_DOCTYPE, "root", "repair_organisation_root", _do
	)


def _ensure_root_unit(pe_name: str, pe_code: str) -> dict[str, Any]:
	root = _root_unit()
	if root:
		return {"id": root["id"], "created": False, "adopted": 0}

	# An orphan is a unit with no parent, or one whose parent row no longer
	# exists (the realistic shape of a deleted root: its children dangle).
	rows = frappe.get_all(
		UNIT_DOCTYPE,
		fields=["name", "parent_organisation_unit"],
		order_by="creation asc",
		limit_page_length=0,
	)
	names = {row["name"] for row in rows}
	orphans = [
		row["name"]
		for row in rows
		if not row["parent_organisation_unit"] or row["parent_organisation_unit"] not in names
	]
	doc = frappe.get_doc(
		{
			"doctype": UNIT_DOCTYPE,
			"unit_code": pe_code,
			"unit_name": pe_name,
			"status": "Active",
		}
	)
	# Orphaned subtree tops are still parentless at this instant; the repair
	# flag lets the root insert through, and the adoption below restores the
	# single-root invariant inside this same transaction (CFG §4.3: recreate
	# the root "without disturbing existing units" — each orphan keeps its
	# whole subtree).
	doc.flags.kt_repair_root = True
	doc.insert(ignore_permissions=True)

	adopted = 0
	for orphan in orphans:
		if orphan == doc.name:
			continue
		unit = frappe.get_doc(UNIT_DOCTYPE, orphan)
		unit.parent_organisation_unit = doc.name
		unit.save(ignore_permissions=True)
		adopted += 1
	return {"id": doc.name, "created": True, "adopted": adopted}


# --------------------------------------------------------------------------
# Commands — fiscal years and the needs-submission flag
# --------------------------------------------------------------------------


def add_fiscal_year(*, start_year: int, idempotency_key: str = "") -> dict[str, Any]:
	"""§7 `AddFiscalYear` — generated dates, site Company attached.

	1 July – 30 June are generated from the start year and cannot be
	overridden (CFG-BR-004); the ERPNext `year` follows its own convention.
	"""
	require_configuration_administrator()

	def _do() -> dict[str, Any]:
		year = _valid_start_year(start_year)
		name = _fy_name(year)
		if frappe.db.exists(FY_DOCTYPE, name):
			fail_cfg("CFG_FY_ALREADY_EXISTS")

		doc = frappe.get_doc(
			{
				"doctype": FY_DOCTYPE,
				"year": name,
				"year_start_date": f"{year}-07-01",
				"year_end_date": f"{year + 1}-06-30",
			}
		)
		company = _site_company()
		if company:
			doc.append("companies", {"company": company})
		doc.insert(ignore_permissions=True)

		log_audit_event(
			event_type="site_configuration",
			document_type=FY_DOCTYPE,
			document_name=doc.name,
			action="add_fiscal_year",
			metadata={"start_year": year, "company": company},
		)
		return {"fiscal_year": doc.name, "label": _fy_label(doc.year_start_date), "created": True}

	return run_idempotent(idempotency_key, FY_DOCTYPE, _fy_name(_valid_start_year(start_year)), "add_fiscal_year", _do)


def open_needs_submission(
	*,
	fiscal_year: str,
	closes_at: str = "",
	reason: str = "",
	expected_version: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""§7 `OpenNeedsSubmission` — atomic open, closing any other open year.

	CFG-BR-006: at most one year is open at any instant. MariaDB has no
	partial unique index, so the equivalent database-level guard is a row
	lock over every currently-open row inside this same transaction — two
	concurrent opens serialise on the lock, and the loser sees the winner's
	state before writing.
	"""
	return _open_intake_flag(
		FLAG_OPEN,
		FLAG_CLOSES_AT,
		"needs_submission",
		fiscal_year=fiscal_year,
		closes_at=closes_at,
		reason=reason,
		expected_version=expected_version,
		idempotency_key=idempotency_key,
	)


def close_needs_submission(
	*, fiscal_year: str, reason: str = "", expected_version: str = "", idempotency_key: str = ""
) -> dict[str, Any]:
	"""§7 `CloseNeedsSubmission` — audited with actor, instant and reason."""
	return _close_intake_flag(
		FLAG_OPEN,
		FLAG_CLOSES_AT,
		"needs_submission",
		fiscal_year=fiscal_year,
		reason=reason,
		expected_version=expected_version,
		idempotency_key=idempotency_key,
	)


def open_dpp_submission(
	*,
	fiscal_year: str,
	closes_at: str = "",
	reason: str = "",
	expected_version: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""CFG v0.9 §4.2 / CFG-BR-013 — open departmental-plan intake for one year,
	atomically closing any other year that has it open. Independent of the
	needs flag: both may be open for different years at once."""
	return _open_intake_flag(
		DPP_FLAG_OPEN,
		DPP_FLAG_CLOSES_AT,
		"dpp_submission",
		fiscal_year=fiscal_year,
		closes_at=closes_at,
		reason=reason,
		expected_version=expected_version,
		idempotency_key=idempotency_key,
	)


def close_dpp_submission(
	*, fiscal_year: str, reason: str = "", expected_version: str = "", idempotency_key: str = ""
) -> dict[str, Any]:
	"""CFG v0.9 §4.2 — close departmental-plan intake, audited."""
	return _close_intake_flag(
		DPP_FLAG_OPEN,
		DPP_FLAG_CLOSES_AT,
		"dpp_submission",
		fiscal_year=fiscal_year,
		reason=reason,
		expected_version=expected_version,
		idempotency_key=idempotency_key,
	)


def _open_intake_flag(
	flag_open: str,
	flag_closes_at: str,
	purpose: str,
	*,
	fiscal_year: str,
	closes_at: str,
	reason: str,
	expected_version: str,
	idempotency_key: str,
) -> dict[str, Any]:
	actor = require_configuration_administrator()
	_require_flag_fields(flag_open)

	def _do() -> dict[str, Any]:
		doc = _locked_fiscal_year(fiscal_year, expected_version)
		if doc.get("disabled"):
			fail_cfg("CFG_INTAKE_NOT_OPEN", "A disabled financial year cannot open submission.")

		close_instant = None
		if (closes_at or "").strip():
			close_instant = get_datetime(closes_at)
			if close_instant <= now_datetime():
				fail_cfg("CFG_INTAKE_CLOSE_INSTANT_INVALID")

		# The database-level equivalent guard: lock all open rows, then close
		# them in this same transaction (one atomic command, never two writes
		# the user issues separately — §5.1).
		frappe.db.sql(f"select name from `tabFiscal Year` where `{flag_open}` = 1 for update")
		previously_open = frappe.get_all(FY_DOCTYPE, filters={flag_open: 1}, pluck="name", limit_page_length=0)
		closed: list[str] = []
		for other in previously_open:
			if other == doc.name:
				continue
			_write_flag(other, open_flag=0, closes_at=None, actor=actor, flag_open=flag_open, flag_closes_at=flag_closes_at)
			closed.append(other)
			log_audit_event(
				event_type="site_configuration",
				document_type=FY_DOCTYPE,
				document_name=other,
				action=f"close_{purpose}",
				metadata={"reason": f"Replaced by {doc.name}", "replaced_by": doc.name},
			)

		_write_flag(doc.name, open_flag=1, closes_at=close_instant, actor=actor, flag_open=flag_open, flag_closes_at=flag_closes_at)
		log_audit_event(
			event_type="site_configuration",
			document_type=FY_DOCTYPE,
			document_name=doc.name,
			action=f"open_{purpose}",
			metadata={
				"reason": reason or "",
				"closes_at": str(close_instant or ""),
				"closed_other_years": closed,
			},
		)
		return {"fiscal_year": doc.name, "open": True, "closed_other_years": closed}

	return run_idempotent(idempotency_key, FY_DOCTYPE, fiscal_year, f"open_{purpose}", _do)


def _close_intake_flag(
	flag_open: str,
	flag_closes_at: str,
	purpose: str,
	*,
	fiscal_year: str,
	reason: str,
	expected_version: str,
	idempotency_key: str,
) -> dict[str, Any]:
	actor = require_configuration_administrator()
	_require_flag_fields(flag_open)

	def _do() -> dict[str, Any]:
		doc = _locked_fiscal_year(fiscal_year, expected_version)
		if not doc.get(flag_open):
			fail_cfg("CFG_INTAKE_NOT_OPEN")
		_write_flag(doc.name, open_flag=0, closes_at=None, actor=actor, flag_open=flag_open, flag_closes_at=flag_closes_at)
		log_audit_event(
			event_type="site_configuration",
			document_type=FY_DOCTYPE,
			document_name=doc.name,
			action=f"close_{purpose}",
			metadata={"reason": reason or ""},
		)
		return {"fiscal_year": doc.name, "open": False}

	return run_idempotent(idempotency_key, FY_DOCTYPE, fiscal_year, f"close_{purpose}", _do)


def set_fiscal_year_disabled(
	*, fiscal_year: str, disabled: bool, expected_version: str = ""
) -> dict[str, Any]:
	"""§7 `SetFiscalYearDisabled` — blocked by references or an open flag,
	with exact blockers (CFG-BR-010). History retained; never a delete."""
	require_configuration_administrator()

	doc = _locked_fiscal_year(fiscal_year, expected_version)
	if disabled:
		blockers: list[str] = []
		if _flag_fields_ready() and doc.get(FLAG_OPEN):
			blockers.append("Needs submission is open for this financial year.")
		if _dpp_flag_fields_ready() and doc.get(DPP_FLAG_OPEN):
			blockers.append("Departmental plan submission is open for this financial year.")
		count = _reference_count(doc.name)
		if count:
			blockers.append(f"{count} KenTender records reference this financial year.")
		if blockers:
			fail_cfg("CFG_FY_IN_USE", " ".join(blockers))

	frappe.db.set_value(FY_DOCTYPE, doc.name, "disabled", 1 if disabled else 0)
	log_audit_event(
		event_type="site_configuration",
		document_type=FY_DOCTYPE,
		document_name=doc.name,
		action="set_fiscal_year_disabled",
		metadata={"disabled": bool(disabled)},
	)
	return {"fiscal_year": doc.name, "disabled": bool(disabled)}


def close_due_needs_submissions() -> dict[str, Any]:
	"""CFG-BR-008 — the hourly job closing any year whose instant has passed.

	A convenience, never the security control: every dependent module command
	rechecks the flag server-side in its own transaction (§11.3). Audited
	with `System` as actor.
	"""
	return _close_due(FLAG_OPEN, FLAG_CLOSES_AT, "needs_submission")


def close_due_dpp_submissions() -> dict[str, Any]:
	"""CFG v0.9 §4.2 — the same hourly closure for departmental-plan intake."""
	return _close_due(DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT, "dpp_submission")


def _close_due(flag_open: str, flag_closes_at: str, purpose: str) -> dict[str, Any]:
	if not frappe.db.has_column(FY_DOCTYPE, flag_open):
		return {"closed": []}
	due = frappe.get_all(
		FY_DOCTYPE,
		filters={flag_open: 1, flag_closes_at: ("<=", now_datetime())},
		pluck="name",
		limit_page_length=0,
	)
	closed = []
	for name in due:
		_write_flag(name, open_flag=0, closes_at=None, actor="System", flag_open=flag_open, flag_closes_at=flag_closes_at)
		log_audit_event(
			event_type="site_configuration",
			document_type=FY_DOCTYPE,
			document_name=name,
			action=f"close_{purpose}",
			performed_by="Administrator",
			metadata={"reason": "Scheduled close instant reached.", "actor": "System"},
		)
		closed.append(name)
	return {"closed": closed}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _valid_start_year(start_year) -> int:
	try:
		year = int(start_year)
	except (TypeError, ValueError):
		year = 0
	if not (1000 <= year <= 9999):
		fail_cfg("CFG_PE_INVALID", "Enter a four-digit start year.")
	return year


def _fy_name(start_year: int) -> str:
	# ERPNext convention (§4.2): `2027-2028`.
	return f"{start_year}-{start_year + 1}"


def _fy_label(year_start_date) -> str:
	start = getdate(year_start_date)
	return f"FY {start.year}/{str(start.year + 1)[-2:]}"


def _site_company() -> str:
	default = frappe.defaults.get_global_default("company")
	if default and frappe.db.exists("Company", default):
		return default
	companies = frappe.get_all("Company", pluck="name", limit_page_length=2)
	return companies[0] if len(companies) == 1 else ""


def _valid_route(route: str, pe_type: str) -> str:
	"""CFG-BR-014 — a route is always present; derive from the entity type when
	the caller names none, refuse an unknown value."""
	value = (route or "").strip()
	if not value:
		return _ROUTE_BY_PE_TYPE.get(pe_type or "", "Cabinet Secretary")
	if value not in STATUTORY_APPROVAL_ROUTES:
		fail_cfg("CFG_PE_INVALID", "Select the statutory approval route.")
	return value


def _locked_fiscal_year(fiscal_year: str, expected_version: str):
	frappe.db.sql("select name from `tabFiscal Year` where name = %s for update", fiscal_year)
	if not frappe.db.exists(FY_DOCTYPE, fiscal_year):
		fail_cfg("CFG_PE_INVALID", "That financial year does not exist.")
	doc = frappe.db.get_value(
		FY_DOCTYPE,
		fiscal_year,
		["name", "year_start_date", "year_end_date", "disabled", "modified",
		 *((FLAG_OPEN, FLAG_CLOSES_AT) if _flag_fields_ready() else ()),
		 *((DPP_FLAG_OPEN, DPP_FLAG_CLOSES_AT) if _dpp_flag_fields_ready() else ())],
		as_dict=True,
	)
	if expected_version and str(doc.modified) != str(expected_version):
		fail_cfg("CFG_VERSION_CONFLICT")
	return doc


def _write_flag(
	fiscal_year: str,
	*,
	open_flag: int,
	closes_at,
	actor: str,
	flag_open: str = FLAG_OPEN,
	flag_closes_at: str = FLAG_CLOSES_AT,
) -> None:
	frappe.db.set_value(
		FY_DOCTYPE,
		fiscal_year,
		{
			flag_open: open_flag,
			flag_closes_at: closes_at,
			FLAG_CHANGED_BY: actor if actor != "System" else "Administrator",
			FLAG_CHANGED_AT: now_datetime(),
		},
	)


def _open_intake_year(flag_open: str = FLAG_OPEN, flag_closes_at: str = FLAG_CLOSES_AT) -> dict[str, Any] | None:
	rows = frappe.get_all(
		FY_DOCTYPE,
		filters={flag_open: 1},
		fields=["name", "year_start_date", flag_closes_at],
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _reference_count(fiscal_year: str) -> int:
	total = 0
	for doctype, fieldname in KT_FISCAL_YEAR_REFERENCES:
		if frappe.db.exists("DocType", doctype) and frappe.db.has_column(doctype, fieldname):
			total += frappe.db.count(doctype, {fieldname: fiscal_year})
	return total


def _flag_fields_ready() -> bool:
	return frappe.db.has_column(FY_DOCTYPE, FLAG_OPEN)


def _dpp_flag_fields_ready() -> bool:
	return frappe.db.has_column(FY_DOCTYPE, DPP_FLAG_OPEN)


def _require_flag_fields(flag_open: str = FLAG_OPEN) -> None:
	if not frappe.db.has_column(FY_DOCTYPE, flag_open):
		fail_cfg(
			"CFG_PE_INVALID",
			"The financial-year intake fields are not installed yet. Run a migration first.",
		)
