# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — shared constants and helpers.

Planning corrections (2026): UX labels map to existing ``Procurement Tender.tender_status``
values without schema migration. See ``OFFICER_TENDER_STATUS_*`` and
``tender_status_to_officer_ux_label``.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

# POC template allowlist (planning correction §9)
OFFICER_POC_TEMPLATE_CODE: str = "KE-PPRA-WORKS-BLDG-2022-04-POC"

# Keys merged from guided ``Procurement Tender`` fields into ``configuration_json`` (doc 8 §13).
# Derived from ``officer_guided_field_registry.get_officer_sync_field_codes()`` (all officer-editable package fields).
def get_officer_sync_config_keys() -> tuple[str, ...]:
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		get_officer_sync_field_codes,
	)

	return get_officer_sync_field_codes()


# Actual ``tender_status`` values on ``Procurement Tender`` (no migration this phase)
TENDER_STATUS_DRAFT: str = "Draft"
TENDER_STATUS_CONFIGURED: str = "Configured"
TENDER_STATUS_VALIDATION_FAILED: str = "Validation Failed"
TENDER_STATUS_VALIDATED: str = "Validated"
TENDER_STATUS_TENDER_PACK_GENERATED: str = "Tender Pack Generated"
TENDER_STATUS_POC_DEMONSTRATED: str = "POC Demonstrated"
TENDER_STATUS_CANCELLED: str = "Cancelled"

# Officer-facing UX labels (display only; storage uses ``tender_status`` above)
OFFICER_UX_DRAFT: str = "Draft"
OFFICER_UX_CONFIGURING: str = "Configuring"
OFFICER_UX_VALIDATION_FAILED: str = "Validation Failed"
OFFICER_UX_VALIDATED: str = "Validated"
OFFICER_UX_PREVIEW_GENERATED: str = "Preview Generated"
OFFICER_UX_READY_FOR_REVIEW: str = "Ready for Review"

# All non-cancelled statuses used in officer POC flows (ordered for dropdowns/tests)
OFFICER_FLOW_TENDER_STATUSES: tuple[str, ...] = (
	TENDER_STATUS_DRAFT,
	TENDER_STATUS_CONFIGURED,
	TENDER_STATUS_VALIDATION_FAILED,
	TENDER_STATUS_VALIDATED,
	TENDER_STATUS_TENDER_PACK_GENERATED,
	TENDER_STATUS_POC_DEMONSTRATED,
)


def tender_status_to_officer_ux_label(tender_status: str | None) -> str:
	"""Map stored ``tender_status`` to officer UX label (planning correction §1)."""
	if not tender_status:
		return OFFICER_UX_DRAFT
	m = {
		TENDER_STATUS_DRAFT: OFFICER_UX_DRAFT,
		TENDER_STATUS_CONFIGURED: OFFICER_UX_CONFIGURING,
		TENDER_STATUS_VALIDATION_FAILED: OFFICER_UX_VALIDATION_FAILED,
		TENDER_STATUS_VALIDATED: OFFICER_UX_VALIDATED,
		TENDER_STATUS_TENDER_PACK_GENERATED: OFFICER_UX_PREVIEW_GENERATED,
		TENDER_STATUS_POC_DEMONSTRATED: OFFICER_UX_READY_FOR_REVIEW,
		TENDER_STATUS_CANCELLED: "Cancelled",
	}
	return m.get(tender_status, tender_status)


def officer_ux_label_to_tender_status(ux_label: str | None) -> str | None:
	"""Map officer UX label back to ``tender_status`` (for tests / explicit transitions)."""
	if not ux_label:
		return None
	m = {
		OFFICER_UX_DRAFT: TENDER_STATUS_DRAFT,
		OFFICER_UX_CONFIGURING: TENDER_STATUS_CONFIGURED,
		OFFICER_UX_VALIDATION_FAILED: TENDER_STATUS_VALIDATION_FAILED,
		OFFICER_UX_VALIDATED: TENDER_STATUS_VALIDATED,
		OFFICER_UX_PREVIEW_GENERATED: TENDER_STATUS_TENDER_PACK_GENERATED,
		OFFICER_UX_READY_FOR_REVIEW: TENDER_STATUS_POC_DEMONSTRATED,
	}
	return m.get(ux_label)


# Cursor boundary prompt — forbidden capability phrases (scope doc §21); used in baseline tests
OFFICER_SCOPE_BOUNDARY_FORBIDDEN_PHRASES: tuple[str, ...] = (
	"Build template editor",
	"Build bidder portal",
	"Build tender publication workflow",
	"Build PDF generation",
	"Build production BoQ module",
)


def load_officer_fields_document(package_path: Path | None = None) -> dict[str, Any]:
	"""Load ``fields.json`` from the STD-WORKS-POC package (officer field model source)."""
	from kentender_procurement.tender_management.services.std_template_loader import (
		get_template_package_path,
		load_json_file,
	)

	root = package_path if package_path is not None else get_template_package_path()
	return load_json_file(root / "fields.json")


def build_officer_guided_field_model(fields_doc: dict[str, Any]) -> dict[str, Any]:
	"""Build grouped officer field model from a ``fields.json`` payload (doc 3 §6–§7)."""
	groups: dict[str, Any] = {g["group_code"]: {**g, "fields": []} for g in fields_doc.get("field_groups", [])}
	for field in fields_doc.get("fields", []):
		gc = field.get("group_code")
		if gc not in groups:
			continue
		required_mode = "Always" if field.get("required_by_default") else "Optional"
		if field.get("poc_required") and not field.get("required_by_default"):
			required_mode = "POC required"
		groups[gc]["fields"].append(
			{
				"field_code": field.get("field_code"),
				"label": field.get("label"),
				"field_type": field.get("field_type"),
				"required_mode": required_mode,
				"ordinary_user_editable": bool(field.get("ordinary_user_editable", True)),
				"help_text": field.get("help_text"),
			}
		)
	ordered = sorted(groups.values(), key=lambda g: int(g.get("render_order") or 999))
	return {"template_code": fields_doc.get("template_code"), "groups": ordered}


def build_officer_config_overlay_from_tender_doc(tender_doc: Any) -> dict[str, Any]:
	"""Map guided ``Procurement Tender`` columns to flat STD configuration keys (doc 8 §13.1)."""
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		build_officer_config_overlay_from_registry,
	)

	return build_officer_config_overlay_from_registry(tender_doc)


def merge_officer_overlay_into_configuration(
	existing: dict[str, Any], tender_doc: Any
) -> dict[str, Any]:
	"""Deep-merge officer-owned keys; preserve unknown ``configuration_json`` keys."""
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		merge_registry_overlay_into_configuration,
	)

	merged = merge_registry_overlay_into_configuration(existing, tender_doc)
	# System keys are not ordinary-user-editable in ``fields.json`` but must round-trip for the engine.
	merged["SYSTEM.TEMPLATE_CODE"] = getattr(tender_doc, "template_code", None) or merged.get(
		"SYSTEM.TEMPLATE_CODE", ""
	)
	merged["SYSTEM.PACKAGE_VERSION"] = getattr(tender_doc, "template_version", None) or merged.get(
		"SYSTEM.PACKAGE_VERSION", ""
	)
	merged["SYSTEM.PACKAGE_HASH"] = getattr(tender_doc, "package_hash", None) or merged.get(
		"SYSTEM.PACKAGE_HASH", ""
	)
	merged["SYSTEM.PROCUREMENT_CATEGORY"] = (
		getattr(tender_doc, "procurement_category", None) or merged.get("SYSTEM.PROCUREMENT_CATEGORY") or "WORKS"
	)
	return merged


def apply_officer_configuration_stale_marks(tender_doc: Any) -> None:
	"""After officer-owned config changes: invalidate validation and downstream preview (doc 8 §9.2)."""
	tender_doc.validation_status = "Not Validated"
	tender_doc.set("validation_messages", [])
	st = getattr(tender_doc, "tender_status", None) or ""
	if st in (
		TENDER_STATUS_VALIDATED,
		TENDER_STATUS_VALIDATION_FAILED,
		TENDER_STATUS_TENDER_PACK_GENERATED,
		TENDER_STATUS_POC_DEMONSTRATED,
	):
		tender_doc.tender_status = TENDER_STATUS_CONFIGURED
	tender_doc.generated_tender_pack_html = ""


def get_officer_guided_field_model(package_path: Path | None = None) -> dict[str, Any]:
	"""Return grouped guided configuration model for the Works POC package."""
	fields_doc = load_officer_fields_document(package_path)
	return build_officer_guided_field_model(fields_doc)


def _cfg_bool(configuration: dict[str, Any], field_code: str) -> bool:
	val = configuration.get(field_code)
	if val is True or val is False:
		return bool(val)
	if isinstance(val, str):
		return val.strip().lower() in ("1", "true", "yes")
	return bool(val)


def get_officer_conditional_state(configuration: dict[str, Any] | None) -> dict[str, Any]:
	"""Derive client hints for conditional visibility and consequence notices (doc 4 §8–§9).

	``configuration`` uses flat ``field_code -> value`` keys (same as ``sample_tender.json``).
	Server validation remains authoritative; this output guides Desk show/hide only.
	"""
	cfg = configuration or {}
	hidden: list[str] = []
	notices: list[dict[str, str]] = []

	if not _cfg_bool(cfg, "PARTICIPATION.RESERVATION_APPLICABLE"):
		hidden.append("PARTICIPATION.RESERVED_GROUP")
	else:
		notices.append(
			{
				"code": "RESERVATION_BRANCH",
				"level": "info",
				"message": (
					"Reserved tender settings affect eligibility and may change bidder "
					"participation requirements."
				),
			}
		)

	if not _cfg_bool(cfg, "PARTICIPATION.JV_ALLOWED"):
		hidden.append("PARTICIPATION.MAX_JV_MEMBERS")
	else:
		notices.append(
			{
				"code": "JV_BRANCH",
				"level": "info",
				"message": (
					"Joint ventures are allowed. The bidder forms checklist will include joint "
					"venture information requirements."
				),
			}
		)

	if (cfg.get("METHOD.TENDER_SCOPE") or "").upper() != "INTERNATIONAL":
		hidden.append("PARTICIPATION.FOREIGN_TENDERER_LOCAL_INPUT_RULE_APPLICABLE")
	else:
		notices.append(
			{
				"code": "INTERNATIONAL_SCOPE",
				"level": "info",
				"message": (
					"International scope may require additional information from foreign tenderers, "
					"including local input or participation information where applicable."
				),
			}
		)

	mode = (cfg.get("SECURITY.TENDER_SECURITY_MODE") or "").upper()
	if mode != "TENDER_SECURITY":
		for fc in (
			"SECURITY.TENDER_SECURITY_TYPE",
			"SECURITY.TENDER_SECURITY_AMOUNT",
			"SECURITY.TENDER_SECURITY_CURRENCY",
			"SECURITY.TENDER_SECURITY_VALIDITY_DAYS_AFTER_TENDER_VALIDITY",
		):
			hidden.append(fc)
	if mode == "TENDER_SECURITY":
		notices.append(
			{
				"code": "TENDER_SECURITY_MODE",
				"level": "info",
				"message": (
					"Tender security is selected. The system will require tender security details "
					"and include the Tender Security form in the required forms checklist."
				),
			}
		)
	elif mode == "TENDER_SECURING_DECLARATION":
		notices.append(
			{
				"code": "TENDER_SECURING_DECLARATION",
				"level": "info",
				"message": (
					"Tender-securing declaration is selected. The system will include the "
					"Tender-Securing Declaration form instead of the Tender Security form."
				),
			}
		)

	if not _cfg_bool(cfg, "SECURITY.PERFORMANCE_SECURITY_REQUIRED"):
		hidden.append("SECURITY.PERFORMANCE_SECURITY_PERCENTAGE")
	else:
		notices.append(
			{
				"code": "PERFORMANCE_SECURITY",
				"level": "info",
				"message": (
					"Performance security is required. The successful bidder will be expected to "
					"provide the relevant contract security form."
				),
			}
		)

	if _cfg_bool(cfg, "SECURITY.ADVANCE_PAYMENT_SECURITY_REQUIRED"):
		notices.append(
			{
				"code": "ADVANCE_PAYMENT_SECURITY",
				"level": "info",
				"message": (
					"Advance payment security is required. The successful bidder may need to "
					"provide an advance payment security instrument before advance payment is made."
				),
			}
		)

	if _cfg_bool(cfg, "SECURITY.RETENTION_MONEY_SECURITY_REQUIRED"):
		notices.append(
			{
				"code": "RETENTION_MONEY_SECURITY",
				"level": "info",
				"message": (
					"Retention money security is required. The contract-stage forms checklist will "
					"include the retention money security form."
				),
			}
		)

	if not _cfg_bool(cfg, "ALTERNATIVES.ALTERNATIVE_TENDERS_ALLOWED"):
		hidden.extend(
			(
				"ALTERNATIVES.ALTERNATIVE_TENDER_TYPE",
				"ALTERNATIVES.ALTERNATIVE_SCOPE_DESCRIPTION",
			)
		)
	else:
		notices.append(
			{
				"code": "ALTERNATIVES_ALLOWED",
				"level": "info",
				"message": (
					"Alternative tenders are allowed. The tender must describe the permitted "
					"alternative scope, and the required forms checklist will include alternative "
					"technical proposal requirements."
				),
			}
		)

	if not _cfg_bool(cfg, "LOTS.MULTIPLE_LOTS_ENABLED"):
		hidden.extend(("LOTS.LOT_EVALUATION_METHOD", "LOTS.LOT_AWARD_METHOD"))
	else:
		notices.append(
			{
				"code": "MULTIPLE_LOTS",
				"level": "info",
				"message": (
					"This tender is divided into lots. You must provide lot information and define "
					"how lots will be evaluated and awarded."
				),
			}
		)

	if not _cfg_bool(cfg, "DATES.SITE_VISIT_REQUIRED"):
		hidden.extend(("DATES.SITE_VISIT_DATE", "DATES.SITE_VISIT_LOCATION"))
	else:
		notices.append(
			{
				"code": "SITE_VISIT_MANDATORY",
				"level": "info",
				"message": (
					"A mandatory site visit requires a date, time, and location before the tender "
					"can be previewed."
				),
			}
		)

	if not _cfg_bool(cfg, "DATES.PRE_TENDER_MEETING_REQUIRED"):
		hidden.extend(("DATES.PRE_TENDER_MEETING_DATE", "DATES.PRE_TENDER_MEETING_LOCATION"))
	else:
		notices.append(
			{
				"code": "PRE_TENDER_MEETING_MANDATORY",
				"level": "info",
				"message": (
					"A mandatory pre-tender meeting requires a date, time, and location before the "
					"tender can be previewed."
				),
			}
		)

	if _cfg_bool(cfg, "WORKS.DAYWORKS_INCLUDED"):
		notices.append(
			{
				"code": "DAYWORKS_INCLUDED",
				"level": "info",
				"message": (
					"Dayworks are included. The BoQ must contain a Dayworks category row before "
					"validation can pass."
				),
			}
		)

	if _cfg_bool(cfg, "WORKS.PROVISIONAL_SUMS_INCLUDED"):
		notices.append(
			{
				"code": "PROVISIONAL_SUMS_INCLUDED",
				"level": "info",
				"message": (
					"Provisional sums are included. The BoQ must contain a Provisional Sums category "
					"row before validation can pass."
				),
			}
		)

	return {"hidden_fields": sorted(set(hidden)), "notices": notices}


def _officer_required_because_text(activation_source: str) -> str:
	src = (activation_source or "").strip()
	if "DEFAULT" in src and "RULE:" in src:
		return (
			"Required by the standard default forms for this procurement type and by "
			"your current tender configuration rules."
		)
	if src == "DEFAULT":
		return "Required by default for this procurement category."
	if "RULE:" in src:
		first_rule = src.split("RULE:")[1].split(";")[0].strip()
		return f"Required because tender rule {first_rule} applies to this configuration."
	return "Required based on the current tender configuration."


def shape_officer_required_forms_checklist(
	engine_rows: list[dict[str, Any]],
) -> dict[str, Any]:
	"""Map engine ``resolve_required_forms`` rows to officer-facing checklist (doc 5)."""
	out: list[dict[str, Any]] = []
	for row in engine_rows:
		out.append(
			{
				"form_code": row.get("form_code"),
				"form_title": row.get("form_title"),
				"display_group": row.get("display_group"),
				"required": bool(row.get("required")),
				"required_because": _officer_required_because_text(row.get("activation_source") or ""),
				"respondent_type": row.get("respondent_type"),
				"workflow_stage": row.get("workflow_stage"),
				"evidence_policy": row.get("evidence_policy"),
				"display_order": row.get("display_order"),
			}
		)
	return {"rows": out, "count": len(out)}


def get_officer_boq_readiness_summary(
	configuration: dict[str, Any],
	boq_rows: list[dict[str, Any]],
	*,
	existing_lot_codes: frozenset[str] | None = None,
) -> dict[str, Any]:
	"""Officer-facing BoQ coverage + POC boundary hints (doc 6)."""
	from kentender_procurement.tender_management.services.std_template_engine import (
		summarize_boq_rows,
	)

	cfg = configuration or {}
	summary = summarize_boq_rows(boq_rows)
	categories = set(summary.get("categories") or [])
	missing_required: list[str] = []
	if _cfg_bool(cfg, "WORKS.DAYWORKS_INCLUDED") and "DAYWORKS" not in categories:
		missing_required.append("DAYWORKS")
	if _cfg_bool(cfg, "WORKS.PROVISIONAL_SUMS_INCLUDED") and "PROVISIONAL_SUMS" not in categories:
		missing_required.append("PROVISIONAL_SUMS")

	invalid_lot_refs: list[dict[str, Any]] = []
	if existing_lot_codes:
		allowed = set(existing_lot_codes)
		for row in boq_rows:
			lot_code = row.get("lot_code")
			cat = row.get("item_category")
			if cat == "GRAND_SUMMARY" or not lot_code:
				continue
			if lot_code not in allowed:
				invalid_lot_refs.append(
					{"item_code": row.get("item_code"), "lot_code": lot_code}
				)

	warnings: list[str] = []
	if missing_required:
		warnings.append(
			"POC BoQ: configuration expects categories "
			f"{', '.join(missing_required)} but no matching BoQ rows were found."
		)
	if invalid_lot_refs:
		warnings.append(
			"POC BoQ: some rows reference lot codes that are not defined on this tender."
		)

	return {
		**summary,
		"missing_required_categories": missing_required,
		"invalid_lot_refs": invalid_lot_refs,
		"warnings": warnings,
		"poc_boundary_notice": (
			"POC BoQ Boundary: representative structured rows only — not production BoQ authoring, "
			"pricing, or measurement."
		),
	}


def apply_officer_preview_audit_labels(summary: dict[str, Any]) -> dict[str, Any]:
	"""Extend ``get_preview_audit_summary`` payload for officer Desk (doc 7; planning §10).

	Expects ``summary["audit"]`` to carry at least ``template_code`` and ``tender_status``.
	"""
	out = copy.deepcopy(summary)
	audit = dict(out.get("audit") or {})
	ts = audit.get("tender_status")
	if isinstance(ts, str) and ts:
		audit["officer_tender_status_ux_label"] = tender_status_to_officer_ux_label(ts)
	code = (audit.get("template_code") or "").strip()
	name = (audit.get("template_name") or audit.get("tender_title") or "").strip()
	short = (audit.get("template_short_name") or "").strip()
	if code and short:
		primary = f"{short} ({code})"
	elif code and name:
		primary = f"{name} ({code})"
	elif code:
		primary = code
	else:
		primary = ""
	audit["template_identity_primary"] = primary
	out["audit"] = audit
	return out


def get_officer_preview_audit_summary_enriched(tender_name: str) -> dict[str, Any]:
	"""Wrapper: preview/audit summary + officer display labels (no fork of audit logic)."""
	import frappe

	from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
		get_preview_audit_summary,
	)

	base = get_preview_audit_summary(tender_name)
	tender = frappe.get_doc("Procurement Tender", tender_name)
	audit = dict(base.get("audit") or {})
	audit["tender_status"] = tender.tender_status
	if tender.std_template:
		try:
			std = frappe.get_doc("STD Template", tender.std_template)
			audit["template_name"] = std.template_name or ""
			audit["template_short_name"] = std.template_short_name or ""
		except Exception:
			pass
	base["audit"] = audit
	return apply_officer_preview_audit_labels(base)


def get_officer_required_forms_checklist_preview(
	configuration: dict[str, Any],
) -> dict[str, Any]:
	"""Run validation + required-forms resolution via engine; return officer-shaped rows."""
	from kentender_procurement.tender_management.services.std_template_engine import (
		load_template,
		resolve_required_forms,
		validate_config,
	)

	template = load_template(OFFICER_POC_TEMPLATE_CODE)
	vr = validate_config(template, configuration)
	rows = resolve_required_forms(template, configuration, vr)
	shaped = shape_officer_required_forms_checklist(rows)
	return {
		**shaped,
		"validation_status": vr.get("status"),
		"activation_keys": sorted((vr.get("active_forms") or {}).keys()),
	}
