# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0130 / 0140 / 0150 / 0160 / 0300 / 0310 / 0320 / 0330 / 0340 / 0341 / 0350 — templates APIs for library shell."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils.data import quoted, slug

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
	STD_TEMPLATE_CODE as _WORKS_SEED_STD_TEMPLATE_CODE,
	STD_TEMPLATE_VERSION_REF as _WORKS_SEED_PLC_VERSION_REF,
)

_FILTER_FIELDS = (
	"name",
	"template_code",
	"template_title",
	"template_version",
	"procurement_category",
	"procurement_method_profile",
	"source_authority",
	"source_document_code",
	"lifecycle_status",
	"latest_validation_status",
	"status_changed_at",
	"modified",
	"owner",
	"allowed_for_tender_creation",
)
_ACTION_ROLES: dict[str, tuple[str, ...]] = {
	"view_details": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
		"STD Template Auditor",
		"STD Template Importer",
	),
	"preview_bundle": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
		"STD Template Auditor",
	),
	"validate": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
	),
	"submit_for_review": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
	),
	"new_revision": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
	),
	"view_usage": (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
		"STD Template Auditor",
	),
}


def _as_multi(value: str | Iterable[str] | None) -> list[str]:
	if value is None:
		return []
	if isinstance(value, str):
		parts = [x.strip() for x in value.split(",")]
		return [x for x in parts if x]
	return [str(x).strip() for x in value if str(x).strip()]


def _normalize_roles(raw_roles: Iterable[Any] | None) -> set[str]:
	if not raw_roles:
		return set()
	out: set[str] = set()
	for role in raw_roles:
		if isinstance(role, str):
			label = role.strip()
		elif isinstance(role, dict):
			label = str(role.get("role") or role.get("name") or "").strip()
		else:
			label = str(role).strip()
		if label:
			out.add(label)
	return out


def _has_tender_usage(names: list[str]) -> set[str]:
	if not names:
		return set()
	rows = frappe.get_all(
		"TM2 Tender",
		filters={"std_template": ("in", names)},
		fields=["std_template"],
		limit_page_length=0,
	)
	return {str(r.get("std_template") or "") for r in rows if r.get("std_template")}


def _status_match(user_statuses: list[str], row: dict[str, Any]) -> bool:
	if not user_statuses:
		return True
	lc = str(row.get("lifecycle_status") or "")
	vs = str(row.get("latest_validation_status") or "")
	mapping: dict[str, bool] = {
		"Imported Draft": lc in {gov.STATUS_IMPORTED, gov.STATUS_VALIDATION_FAILED, gov.STATUS_RETURNED},
		"Needs Attention": lc in {gov.STATUS_IMPORTED, gov.STATUS_VALIDATION_FAILED, gov.STATUS_RETURNED}
		or vs in {gov.VALIDATION_PASS_WARNINGS, gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED},
		"Ready for Review": lc in {gov.STATUS_VALIDATED, gov.STATUS_SUBMITTED, gov.STATUS_APPROVED},
		"Under Review": lc in {gov.STATUS_SUBMITTED},
		"Active": lc == gov.STATUS_ACTIVE,
		"Superseded": lc == gov.STATUS_SUPERSEDED,
		"Retired": lc == gov.STATUS_RETIRED,
	}
	return any(mapping.get(s, False) for s in user_statuses)


def _validation_match(values: list[str], row: dict[str, Any]) -> bool:
	if not values:
		return True
	vs = str(row.get("latest_validation_status") or "")
	mapping = {
		"Not Run": vs == gov.VALIDATION_NOT_RUN,
		"Passed": vs in {gov.VALIDATION_PASS, gov.VALIDATION_PASS_WARNINGS},
		"Needs Attention": vs in {gov.VALIDATION_PASS_WARNINGS},
		"Blocked": vs in {gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED},
	}
	return any(mapping.get(v, False) for v in values)


def _bundle_status(row: dict[str, Any]) -> str:
	vs = str(row.get("latest_validation_status") or "")
	if vs in {gov.VALIDATION_PASS, gov.VALIDATION_PASS_WARNINGS}:
		return "Available"
	if vs == gov.VALIDATION_NOT_RUN:
		return "Not Generated"
	if vs == gov.VALIDATION_BLOCKED:
		return "Needs Tender Values"
	return "Failed"


def _status_label(lifecycle_status: str) -> str:
	return {
		gov.STATUS_IMPORTED: "Imported Draft",
		gov.STATUS_VALIDATED: "Ready for Review",
		gov.STATUS_SUBMITTED: "Under Review",
		gov.STATUS_APPROVED: "Ready for Review",
		gov.STATUS_ACTIVE: "Active",
		gov.STATUS_SUPERSEDED: "Superseded",
		gov.STATUS_RETIRED: "Retired",
		gov.STATUS_ARCHIVED: "Archived",
		gov.STATUS_RETURNED: "Needs Attention",
		gov.STATUS_VALIDATION_FAILED: "Needs Attention",
	}.get(lifecycle_status, lifecycle_status or "Draft")


def _supersession_status(lifecycle_status: str) -> str:
	if lifecycle_status in {gov.STATUS_SUPERSEDED, gov.STATUS_RETIRED, gov.STATUS_ARCHIVED}:
		return "Superseded"
	return "Current"


def _supported_methods(raw_profile: str) -> list[str]:
	if not raw_profile:
		return []
	return [m.strip() for m in raw_profile.split(",") if m.strip()]


def _validation_label(validation_status: str) -> str:
	if validation_status in {gov.VALIDATION_PASS, gov.VALIDATION_PASS_WARNINGS}:
		return "Passed"
	if validation_status in {gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED}:
		return "Blocked"
	return "Not Run"


def _next_action_for_status(status: str) -> str:
	return {
		"Imported Draft": "Validate package.",
		"Needs Attention": "Resolve validation blockers.",
		"Ready for Review": "Submit for review.",
		"Active": "Preview bundle or create new revision.",
		"Superseded": "View supersession history.",
	}.get(status, "Review status and proceed with the recommended action.")


def _validation_category_health(status: str, validation_label: str) -> dict[str, Any]:
	if validation_label == "Passed":
		state = "Passed"
		severity = "Low"
		issues = []
		remediation = "No immediate remediation required."
	elif validation_label == "Blocked":
		state = "Blocked"
		severity = "High"
		issues = [
			"Mandatory placeholders are incomplete for at least one required section.",
			"Bundle generation prerequisites are not fully satisfied.",
		]
		remediation = "Resolve blocked categories and re-run validation."
	else:
		state = "Needs Attention" if status in {"Needs Attention", "Imported Draft"} else "Not Run"
		severity = "Medium"
		issues = [
			"Validation has not fully completed for all readiness categories.",
		]
		remediation = "Run validation and address category warnings."

	categories = [
		{"category": "Structure Integrity", "state": state},
		{"category": "Source Mappings", "state": state},
		{"category": "Placeholders And Readiness", "state": state},
		{"category": "Locked Legal Blocks", "state": "Passed" if state == "Passed" else "Needs Attention"},
	]
	return {
		"overall_status": state,
		"severity": severity,
		"categories": categories,
		"issues": issues,
		"remediation": remediation,
	}


def _bundle_preview_detail(
	status: str, validation_label: str, bundle_status: str, user_roles: set[str]
) -> dict[str, Any]:
	can_generate = bool(
		user_roles
		& {
			"Administrator",
			"System Manager",
			"STD Template Administrator",
			"STD Template Reviewer",
		}
	)
	has_output = bundle_status == "Available"
	warnings = 0 if has_output else (2 if validation_label == "Blocked" else 1)
	if has_output:
		preview_status = "Available"
		severity = "Low"
		last_generated = "2026-05-08 16:00"
	elif status in {"Imported Draft", "Needs Attention"}:
		preview_status = "Needs Attention"
		severity = "High" if validation_label == "Blocked" else "Medium"
		last_generated = "Not generated yet"
	else:
		preview_status = "Not Generated"
		severity = "Medium"
		last_generated = "Not generated yet"

	outline = [
		"Invitation to Tender",
		"I. Instructions to Tenderers",
		"II. Tender Data Sheet",
		"III. Evaluation and Qualification Criteria",
		"IV. Tendering Forms",
		"V. Bills of Quantities",
		"VI. Specifications",
		"VII. Drawings",
		"VIII. General Conditions of Contract",
		"IX. Special Conditions of Contract",
		"X. Contract Forms",
	]
	preview_blocks = [
		{
			"section": "Invitation to Tender",
			"content": "Official invitation and submission instructions for qualified tenderers.",
		},
		{
			"section": "Tender Data Sheet",
			"content": "Includes key submission dates, eligibility notes, and tender security references.",
		},
		{
			"section": "Contract Forms",
			"content": "Award and contract signature forms prepared for controlled tender assembly.",
		},
	]
	placeholders = [
		{
			"group": "Tender Identity",
			"rows": [
				{
					"label": "Tender Number",
					"filled_during": "Tender preparation",
					"source_section": "TDS",
					"output_impact": "Bundle, DSM",
				}
			],
		},
		{
			"group": "Dates and Deadlines",
			"rows": [
				{
					"label": "Submission Deadline",
					"filled_during": "Tender preparation",
					"source_section": "TDS",
					"output_impact": "Bundle, DOM",
				}
			],
		},
		{
			"group": "Tender Security",
			"rows": [
				{
					"label": "Tender Security Amount",
					"filled_during": "Tender preparation",
					"source_section": "ITT",
					"output_impact": "Bundle",
				}
			],
		},
		{
			"group": "BOQ and Works Requirements",
			"rows": [
				{
					"label": "Bill Item Quantities",
					"filled_during": "Tender preparation",
					"source_section": "BOQ",
					"output_impact": "Bundle, DOM",
				}
			],
		},
		{
			"group": "Contract Conditions",
			"rows": [
				{
					"label": "Performance Security Period",
					"filled_during": "Tender preparation",
					"source_section": "SCC",
					"output_impact": "Bundle, DCM",
				}
			],
		},
	]
	return {
		"status_bar": {
			"preview_status": preview_status,
			"severity": severity,
			"last_generated": last_generated,
			"output_type": "Template-level preview",
			"placeholder_count": 48,
			"render_warnings": warnings,
		},
		"outline": outline,
		"preview_blocks": preview_blocks,
		"placeholders": placeholders,
		"actions": {
			"generate_preview": {
				"allowed": can_generate,
				"visible": True,
				"message": "Allowed"
				if can_generate
				else "Unavailable: you do not have permission to regenerate bundle previews.",
			},
			"download_pdf": {
				"allowed": has_output,
				"visible": has_output,
				"message": "Allowed" if has_output else "Unavailable: preview output is not available yet.",
			},
			"download_docx": {
				"allowed": has_output,
				"visible": has_output,
				"message": "Allowed" if has_output else "Unavailable: preview output is not available yet.",
			},
			"view_placeholders": {
				"allowed": True,
				"visible": True,
				"message": "Allowed",
			},
		},
	}


def _plc_binding_codes(template_code: str, std_doc_name: str) -> tuple[str, ...]:
	"""Return version strings PLC/TM2 may store for this catalogue row."""
	codes = {(template_code or "").strip(), (std_doc_name or "").strip()}
	codes.discard("")
	if _WORKS_SEED_STD_TEMPLATE_CODE in codes:
		plc = (_WORKS_SEED_PLC_VERSION_REF or "").strip()
		if plc:
			codes.add(plc)
	return tuple(sorted(codes))


def _build_usage_detail(
	template_code: str, std_doc_name: str, _status: str, _bundle_preview_status: str
) -> dict[str, Any]:
	"""PLC usage for STD-LIB Usage tab (aggregates Procurement Journey + TM2 Tender rows).

	Uses ``ignore_permissions`` so hidden technical reference fields participate in filtering
	while the enclosing ``get_std_library_template_detail`` call remains authenticated.
	"""
	bindings = set(_plc_binding_codes(template_code, std_doc_name))
	std_link_name = (std_doc_name or "").strip() or (template_code or "").strip()

	code_list = list(bindings)
	journey_rows_raw: list[dict[str, Any]] = frappe.get_list(
		"Procurement Journey",
		filters={"docstatus": ("!=", 2), "std_template_version_ref": ("in", code_list)},
		fields=[
			"name",
			"journey_code",
			"journey_title",
			"tm2_tender_ref",
			"procuring_entity_code",
		],
		order_by="modified desc",
		limit=150,
		# Field-level hides std_template_version_ref for most roles; this read serves the
		# authorised STD catalogue detail surface (`get_std_library_template_detail`).
		ignore_permissions=True,
	)

	link_tender_refs: set[str] = set()
	journeys_out: list[dict[str, Any]] = []
	for jr in journey_rows_raw:
		jc = str(jr.get("journey_code") or "").strip()
		title = str(jr.get("journey_title") or "").strip()
		entity = str(jr.get("procuring_entity_code") or "").strip()
		ref = str(jr.get("tm2_tender_ref") or "").strip()
		journeys_out.append(
			{
				"journey_code": jc,
				"title": title,
				"procuring_entity": entity,
				"open_route": f"/desk/plc-procurement-journey/{quoted(jc)}"
				if jc
				else "/desk/plc-procurement-journey",
				"view_label": _("Open journey"),
			}
		)
		if ref:
			link_tender_refs.add(ref)

	tenders_by_name: dict[str, dict[str, Any]] = {}

	blist = sorted(bindings)
	or_filters: list[Any] = [
		["template_version", "in", blist],
		["template_code", "in", blist],
	]
	if std_link_name:
		or_filters.append(["std_template", "=", std_link_name])

	found = frappe.get_list(
		"TM2 Tender",
		filters={"docstatus": ("!=", 2)},
		or_filters=or_filters,
		fields=[
			"name",
			"tender_code",
			"tender_title",
			"status",
			"procuring_entity_code",
			"template_version",
		],
		order_by="modified desc",
		limit=200,
		ignore_permissions=True,
	)
	for t in found:
		nm = str(t.get("name") or "").strip()
		if nm:
			tenders_by_name[nm] = dict(t)

	if link_tender_refs:
		linked = frappe.get_list(
			"TM2 Tender",
			filters={
				"docstatus": ("!=", 2),
				"name": ("in", list(link_tender_refs)),
			},
			fields=[
				"name",
				"tender_code",
				"tender_title",
				"status",
				"procuring_entity_code",
				"template_version",
			],
			limit=min(len(link_tender_refs), 250) + 5,
			ignore_permissions=True,
		)
		for t in linked:
			nm = str(t.get("name") or "").strip()
			if nm:
				tenders_by_name[nm] = dict(t)

	tenders_out: list[dict[str, Any]] = []
	doc_slug = slug("TM2 Tender")
	for nm in sorted(tenders_by_name.keys(), key=lambda k: tenders_by_name[k].get("tender_code") or k):
		trow = tenders_by_name[nm]
		tenders_out.append(
			{
				"code": str(trow.get("tender_code") or "").strip(),
				"title": str(trow.get("tender_title") or "").strip(),
				"status": str(trow.get("status") or "").strip(),
				"procuring_entity": str(trow.get("procuring_entity_code") or "").strip(),
				"view_label": _("Open tender"),
				"open_route": f"/desk/{quoted(doc_slug)}/{quoted(nm)}",
			}
		)

	return {
		"summary": {
			"tenders_using_count": len(tenders_out),
			"journeys_using_count": len(journeys_out),
		},
		"journeys": journeys_out,
		"tenders": tenders_out,
		"instances": [],
		"outputs": [],
		"addenda": [],
	}


def _supersession_detail(
	version_code: str, status: str, lifecycle_status: str, user_roles: set[str]
) -> dict[str, Any]:
	principle_text = (
		"Existing published tenders remain bound to the STD version used at publication unless "
		"a formal addendum or supersession process applies."
	)
	if lifecycle_status == gov.STATUS_SUPERSEDED:
		supersedes = f"{version_code}-PREV"
		superseded_by = f"{version_code}-NEXT"
		reason = "PPRA policy update"
		effective_date = "2026-05-08"
	elif lifecycle_status == gov.STATUS_ACTIVE:
		supersedes = f"{version_code}-PREV"
		superseded_by = ""
		reason = "PPRA correction"
		effective_date = "Pending new revision"
	else:
		supersedes = ""
		superseded_by = ""
		reason = "Not yet superseded"
		effective_date = "Not set"

	can_create_revision = bool(
		lifecycle_status in {gov.STATUS_ACTIVE, gov.STATUS_SUPERSEDED}
		and user_roles & set(_ACTION_ROLES.get("new_revision", ()))
	)
	return {
		"lineage": {
			"current_version": version_code,
			"supersedes": supersedes,
			"superseded_by": superseded_by,
			"reason": reason,
			"effective_date": effective_date,
		},
		"impact": {
			"existing_tender_impact": principle_text,
			"new_tenders_impact": (
				"New tenders must use the newest approved version once supersession is effective."
				if status in {"Active", "Superseded"}
				else "New tenders continue to use the current approved version."
			),
		},
		"principle_text": principle_text,
		"actions": {
			"create_new_revision": {
				"label": "Create New Revision",
				"allowed": can_create_revision,
				"message": "Allowed"
				if can_create_revision
				else "Unavailable: create new revision is only allowed for Active or Superseded versions with permission.",
			},
			"view_previous_version": {
				"allowed": bool(supersedes),
				"message": "Allowed" if supersedes else "Unavailable: no prior version linked.",
			},
			"view_superseding_version": {
				"allowed": bool(superseded_by),
				"message": "Allowed" if superseded_by else "Unavailable: no superseding version linked.",
			},
		},
	}


def _advanced_detail(lifecycle_status: str, user_roles: set[str]) -> dict[str, Any]:
	intro_text = (
		"Advanced Technical View is for reviewing structured sections, parameters, forms, BOQ "
		"rules, source mappings, readiness rules, and generated model definitions. Most STD "
		"administration tasks can be completed from Summary, Validation, and Bundle Preview."
	)
	has_advanced_permission = bool(
		user_roles
		& {
			"Administrator",
			"System Manager",
			"STD Template Administrator",
			"STD Template Reviewer",
			"STD Template Auditor",
		}
	)
	is_active = lifecycle_status == gov.STATUS_ACTIVE
	targets = [
		{"code": "DSM", "label": "Submission Requirements (DSM)"},
		{"code": "DOM", "label": "Opening Register (DOM)"},
		{"code": "DEM", "label": "Evaluation Rules (DEM)"},
		{"code": "DCM", "label": "Contract Carry-Forward (DCM)"},
		{"code": "BUNDLE", "label": "Tender Document Bundle"},
	]
	mapping_rows = [
		{
			"source": "Tender Data Sheet - Submission Deadline",
			"target_code": "DSM",
			"target_label": "Submission Requirements (DSM)",
			"generated_element": "submission_requirements.deadline",
			"mandatory": "Yes",
			"status": "Valid",
			"last_validated": "2026-05-08 17:00",
		},
		{
			"source": "Opening Procedure - Register Format",
			"target_code": "DOM",
			"target_label": "Opening Register (DOM)",
			"generated_element": "opening_register.schema",
			"mandatory": "Yes",
			"status": "Missing",
			"last_validated": "2026-05-08 17:00",
			"validation_blocker": {
				"tab": "validation",
				"reason": "Source mapping entry is missing for opening register schema.",
			},
		},
		{
			"source": "Evaluation Criteria - Weighted Rule",
			"target_code": "DEM",
			"target_label": "Evaluation Rules (DEM)",
			"generated_element": "evaluation_rules.weighted_criteria",
			"mandatory": "No",
			"status": "Invalid",
			"last_validated": "2026-05-08 17:00",
			"validation_blocker": {
				"tab": "validation",
				"reason": "Mapping target format is invalid for evaluation rule output.",
			},
		},
	]
	return {
		"intro_text": intro_text,
		"sections": [
			{"key": "sections_clauses", "label": "Sections and Clauses"},
			{"key": "parameters", "label": "Parameters"},
			{"key": "forms", "label": "Forms"},
			{"key": "boq_rules", "label": "Works / BOQ Rules"},
			{"key": "source_mappings", "label": "Source Mappings"},
			{"key": "readiness_rules", "label": "Readiness Rules"},
			{"key": "generated_models", "label": "Generated Model Definitions"},
			{"key": "raw_package_data", "label": "Raw Package Data"},
		],
		"raw_package": {
			"collapsed_by_default": True,
			"technical_label": "Technical (Read-Only)",
			"read_only": True,
			"visible_for_advanced_users": has_advanced_permission,
		},
		"editing": {
			"enabled": False,
			"reason": (
				"Editing is disabled for Active versions."
				if is_active
				else "Advanced shell is read-only in this phase."
			),
		},
		"source_mappings": {
			"targets": targets,
			"rows": mapping_rows,
			"read_only": True,
		},
	}


def _audit_detail(version_code: str, user_roles: set[str]) -> dict[str, Any]:
	can_view_denied = bool(
		user_roles
		& {
			"Administrator",
			"System Manager",
			"STD Template Administrator",
			"STD Template Reviewer",
			"STD Template Auditor",
		}
	)
	rows = [
		{
			"timestamp": "2026-05-08 16:45",
			"actor": "Administrator",
			"event": "Package Imported",
			"object": version_code,
			"result": "Success",
			"reason": "Structured package accepted.",
			"audit_code": "STD_TEMPLATE_IMPORTED",
		},
		{
			"timestamp": "2026-05-08 16:47",
			"actor": "Administrator",
			"event": "Validation Run",
			"object": version_code,
			"result": "Success",
			"reason": "Validation completed.",
			"audit_code": "STD_TEMPLATE_VALIDATION_COMPLETED",
		},
		{
			"timestamp": "2026-05-08 16:48",
			"actor": "Administrator",
			"event": "Bundle Preview Generated",
			"object": version_code,
			"result": "Success",
			"reason": "Template-level bundle preview generated.",
			"audit_code": "STD_TEMPLATE_BUNDLE_PREVIEW_GENERATED",
		},
		{
			"timestamp": "2026-05-08 16:50",
			"actor": "System Manager",
			"event": "Mutation Attempt Blocked",
			"object": version_code,
			"result": "Denied",
			"reason": "Active version is immutable.",
			"audit_code": "STD_TEMPLATE_MUTATION_BLOCKED",
		},
	]
	if not can_view_denied:
		rows = [r for r in rows if r.get("result") != "Denied"]
	return {
		"read_only": True,
		"denied_visible": can_view_denied,
		"rows": rows,
	}


def _action_availability(row: dict[str, Any], user_roles: set[str]) -> dict[str, dict[str, Any]]:
	lifecycle_status = str(row.get("lifecycle_status") or "")
	bundle_status = _bundle_status(row)
	allowed_by_state = {
		"view_details": True,
		"preview_bundle": bundle_status in {"Available", "Not Generated"},
		"validate": lifecycle_status
		in {gov.STATUS_IMPORTED, gov.STATUS_VALIDATION_FAILED, gov.STATUS_RETURNED},
		"submit_for_review": lifecycle_status
		in {gov.STATUS_VALIDATED, gov.STATUS_APPROVED, gov.STATUS_SUBMITTED},
		"new_revision": lifecycle_status in {gov.STATUS_ACTIVE, gov.STATUS_SUPERSEDED},
		"view_usage": True,
	}
	out: dict[str, dict[str, Any]] = {}
	for action_code, state_ok in allowed_by_state.items():
		role_ok = bool(user_roles & set(_ACTION_ROLES.get(action_code, ())))
		allowed = bool(state_ok and role_ok)
		out[action_code] = {
			"allowed": allowed,
			"message": _("Allowed")
			if allowed
			else _("Unavailable: this action is not available in the current state or role."),
		}
	return out


def _queue_match(queue: str, row: dict[str, Any]) -> bool:
	if not queue:
		return True
	lc = str(row.get("lifecycle_status") or "")
	vs = str(row.get("latest_validation_status") or "")
	return {
		"active": lc == gov.STATUS_ACTIVE,
		"needs_attention": lc in {gov.STATUS_IMPORTED, gov.STATUS_VALIDATION_FAILED, gov.STATUS_RETURNED}
		or vs in {gov.VALIDATION_PASS_WARNINGS, gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED},
		"ready_review": lc in {gov.STATUS_VALIDATED, gov.STATUS_SUBMITTED, gov.STATUS_APPROVED},
		"superseded": lc == gov.STATUS_SUPERSEDED,
		"package_imports": lc == gov.STATUS_IMPORTED,
		"bundle_issues": vs in {gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED},
	}.get(queue, True)


def _date_in_range(d: date | None, from_date: date | None, to_date: date | None) -> bool:
	if not d:
		return False if from_date or to_date else True
	if from_date and d < from_date:
		return False
	if to_date and d > to_date:
		return False
	return True


@frappe.whitelist()
def get_std_library_templates(
	search: str | None = None,
	procurement_category: str | None = None,
	procurement_method: str | None = None,
	status: str | list[str] | tuple[str, ...] | None = None,
	source_authority: str | None = None,
	validation_status: str | list[str] | tuple[str, ...] | None = None,
	supersession_status: str | list[str] | tuple[str, ...] | None = None,
	used_by_tenders: str | None = None,
	bundle_preview_status: str | list[str] | tuple[str, ...] | None = None,
	revision_from: str | None = None,
	revision_to: str | None = None,
	queue: str | None = None,
	limit: int | None = 200,
) -> dict:
	"""Return filtered STD templates for STD-LIB-0130/0140."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	rows = frappe.get_all(
		"STD Template",
		fields=list(_FILTER_FIELDS),
		order_by="modified desc",
		limit_page_length=max(1, min(int(limit or 200), 1000)),
	)
	names = [str(r.get("name") or "") for r in rows if r.get("name")]
	used_names = _has_tender_usage(names)

	search_q = (search or "").strip().lower()
	status_values = _as_multi(status)
	validation_values = _as_multi(validation_status)
	supersession_values = _as_multi(supersession_status)
	bundle_values = _as_multi(bundle_preview_status)
	q = (queue or "").strip()
	used_filter = (used_by_tenders or "").strip()
	from_date = getdate(revision_from) if revision_from else None
	to_date = getdate(revision_to) if revision_to else None
	user_roles = _normalize_roles(frappe.get_roles(frappe.session.user) or [])

	out: list[dict[str, Any]] = []
	items: list[dict[str, Any]] = []
	for row in rows:
		name = str(row.get("name") or "")
		lc = str(row.get("lifecycle_status") or "")
		vs = str(row.get("latest_validation_status") or "")
		proc_cat = str(row.get("procurement_category") or "")
		method = str(row.get("procurement_method_profile") or "")
		authority = str(row.get("source_authority") or "")
		search_blob = " ".join(
			[
				str(row.get("template_title") or ""),
				str(row.get("template_code") or ""),
				str(row.get("template_version") or ""),
				authority,
				proc_cat,
				method,
				str(row.get("source_document_code") or ""),
			]
		).lower()
		if search_q and search_q not in search_blob:
			continue
		if procurement_category and procurement_category != proc_cat:
			continue
		if procurement_method and procurement_method != method:
			continue
		if source_authority and source_authority != authority:
			continue
		if not _status_match(status_values, row):
			continue
		if not _validation_match(validation_values, row):
			continue
		if supersession_values:
			sup_state = "Superseded" if lc in {gov.STATUS_SUPERSEDED, gov.STATUS_RETIRED, gov.STATUS_ARCHIVED} else "Current"
			if sup_state not in supersession_values:
				continue
		bundle_state = _bundle_status(row)
		if bundle_values and bundle_state not in bundle_values:
			continue
		if used_filter == "Used" and name not in used_names:
			continue
		if used_filter == "Unused" and name in used_names:
			continue
		rev_dt = getdate(row.get("status_changed_at") or row.get("modified"))
		if not _date_in_range(rev_dt, from_date, to_date):
			continue
		if not _queue_match(q, row):
			continue

		raw_version = str(row.get("template_code") or name or "").strip()
		version_code = raw_version or name
		used_count = 1 if name in used_names else 0
		methods = _supported_methods(method)
		method_label = methods[0] if methods else (method or "")
		owner_id = str(row.get("owner") or "").strip()
		owner_label = owner_id
		if owner_id:
			owner_label = frappe.db.get_value("User", owner_id, "full_name") or owner_id
		active_version_label = str(row.get("template_version") or "").strip() or _("Revision not set")
		out.append(
			{
				"name": name,
				"template_code": row.get("template_code"),
				"template_title": row.get("template_title"),
				"template_version": row.get("template_version"),
				"procurement_category": proc_cat,
				"procurement_method": method,
				"source_authority": authority,
				"lifecycle_status": lc,
				"latest_validation_status": vs,
				"bundle_preview_status": bundle_state,
				"used_by_tenders": name in used_names,
			}
		)
		items.append(
			{
				"version_code": version_code,
				"title": str(row.get("template_title") or version_code),
				"revision_label": active_version_label,
				"active_version_label": active_version_label,
				"status": _status_label(lc),
				"procurement_category": proc_cat,
				"procurement_method": method_label,
				"supported_methods": methods,
				"source_authority": authority,
				"owner": owner_label,
				"validation_status": _validation_label(vs),
				"bundle_preview_status": bundle_state,
				"used_by_tender_count": used_count,
				"usage_count": used_count,
				"supersession_status": _supersession_status(lc),
				"action_availability": _action_availability(row, user_roles),
			}
		)

	return {
		"ok": True,
		"rows": out,
		"items": items,
		"total_count": len(out),
		"queue": q or None,
		"applied_filters": {
			"search": search or "",
			"procurement_category": procurement_category or "",
			"procurement_method": procurement_method or "",
			"status": status_values,
			"source_authority": source_authority or "",
			"validation_status": validation_values,
			"supersession_status": supersession_values,
			"used_by_tenders": used_filter or "Any",
			"bundle_preview_status": bundle_values,
			"revision_from": revision_from or "",
			"revision_to": revision_to or "",
		},
	}


@frappe.whitelist()
def get_std_library_template_detail(version_code: str) -> dict:
	"""Return selected template detail header payload for STD-LIB-0150."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	code = str(version_code or "").strip()
	if not code:
		frappe.throw(_("Version code is required."))

	row = frappe.get_all(
		"STD Template",
		filters={"template_code": code},
		fields=[
			"name",
			"template_code",
			"template_title",
			"template_version",
			"procurement_category",
			"procurement_method_profile",
			"source_authority",
			"source_document_code",
			"lifecycle_status",
			"latest_validation_status",
		],
		limit_page_length=1,
	)
	if not row:
		frappe.throw(_("STD Template version not found."), frappe.DoesNotExistError)
	doc = row[0]
	lifecycle_status = str(doc.get("lifecycle_status") or "")
	status = _status_label(lifecycle_status)
	if status == "Active":
		state_banner = _(
			"This STD version is active and immutable. Create a new revision to make changes."
		)
	elif status == "Needs Attention":
		state_banner = _(
			"This STD package needs attention before it can be reviewed or activated."
		)
	elif status == "Imported Draft":
		state_banner = _("This STD package has been imported and must be validated before use.")
	else:
		state_banner = _("Review this STD version status before proceeding.")
	source_doc_code = str(doc.get("source_document_code") or "").strip()
	methods = _supported_methods(str(doc.get("procurement_method_profile") or ""))
	procurement_category = str(doc.get("procurement_category") or "")
	validation_label = _validation_label(str(doc.get("latest_validation_status") or ""))
	bundle_preview = _bundle_status(doc)
	next_action = _next_action_for_status(status)
	user_roles = _normalize_roles(frappe.get_roles(frappe.session.user) or [])

	validation_health = _validation_category_health(status, validation_label)
	bundle_preview_detail = _bundle_preview_detail(status, validation_label, bundle_preview, user_roles)
	usage_detail = _build_usage_detail(
		str(doc.get("template_code") or code),
		str(doc.get("name") or code),
		status,
		bundle_preview,
	)
	supersession_detail = _supersession_detail(code, status, lifecycle_status, user_roles)
	advanced_detail = _advanced_detail(lifecycle_status, user_roles)
	audit_detail = _audit_detail(code, user_roles)
	return {
		"ok": True,
		"detail": {
			"title": str(doc.get("template_title") or code),
			"version_code": str(doc.get("template_code") or code),
			"revision_label": str(doc.get("template_version") or "").strip() or _("Revision not set"),
			"status": status,
			"authority": str(doc.get("source_authority") or ""),
			"validation_status": validation_label,
			"bundle_preview_status": bundle_preview,
			"state_banner": state_banner,
			"summary": {
				"identity": {
					"title": str(doc.get("template_title") or code),
					"revision": str(doc.get("template_version") or "").strip() or _("Revision not set"),
					"authority": str(doc.get("source_authority") or ""),
					"template_family": source_doc_code.split("-")[0] if source_doc_code else "STD-GENERAL",
				},
				"source_evidence": {
					"source_document": source_doc_code or _("Not registered"),
					"source_file": _("Available"),
					"source_hash": _("Available"),
					"evidence_status": _("Registered"),
				},
				"supported_use": {
					"category": procurement_category or _("Not set"),
					"methods": methods,
					"contract_type": _("Admeasurement / Unit Rate"),
					"requires_boq": _("Yes"),
				},
				"health_summary": {
					"validation": validation_label,
					"bundle_preview": bundle_preview,
					"generated_models": _("Available"),
				},
				"output_summary": {
					"line": _("Structured template outputs are ready for controlled tender assembly."),
				},
				"next_action": {
					"status": status,
					"action": next_action,
				},
			},
			"validation": validation_health,
			"bundle_preview": bundle_preview_detail,
			"usage": usage_detail,
			"supersession": supersession_detail,
			"advanced": advanced_detail,
			"audit": audit_detail,
		},
	}
