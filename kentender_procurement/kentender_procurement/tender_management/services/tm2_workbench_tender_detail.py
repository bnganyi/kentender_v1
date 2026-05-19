# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-08 … P9-24 — TM2 workbench tender detail through Audit & Evidence tab (doc 9 §16–17.12, §19.2).

Builds read-only DTOs for the desk workbench detail column. Action buttons use
:func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
with ``state_authorization`` (tender lifecycle) and desk ``granted_permissions`` hints.
``overview`` mirrors pack §19.2 (summary, lineage, key dates, audit tail, tab counts).
``std_readiness`` powers doc 9 §17.3 (binding, checklist, read-only derived outputs, DEM gate).
``timeline_tab`` powers doc 9 §17.4 / doc 6 §17.2–17.4 (key dates, official server time when published-active,
warnings, addendum extension history from audit).
``supplier_access_tab`` powers doc 9 §17.5 / doc 6 §18 (access rule, invitations, participation table;
no bid body content).
``clarifications_tab`` powers doc 9 §17.6 / doc 6 §19 (status summary, threads, addendum-material warning).
``addenda_tab`` powers doc 9 §17.7 / doc 6 §20 (addendum list, impact summary, revised vs previous output refs).
``submissions_tab`` powers doc 9 §17.8 / doc 6 §21 (sealed-bid metadata only until opening; no BOQ/rates pre-opening).
``opening_readiness_tab`` powers doc 9 §17.9 / doc 6 §22 (DOM + publication snapshot, closing/ORR handoff, opening rules,
Works arithmetic notice, OR2 action hints).
``evaluation_handoff_tab`` powers doc 9 §17.10 / doc 6 §23 (EHR handoff status, opening record, DEM/DSM/snapshot, opened bids,
issued addenda, mandatory criteria notice, EV2 action hints; no criteria editor).
``contract_handoff_tab`` powers doc 9 §17.11 / doc 6 §24 (**TM2 Contract Handoff Reference** / CHR, DCM, award + awarded supplier,
corrected evaluated price + BOQ ref for Works, snapshot, addenda, CON2 action hint; no term editing).
``audit_evidence_tab`` powers doc 9 §17.12 / doc 6 §25 / **P9-21a** (lifecycle stream, denied-actions table aligned with §13.3 ``sensitive_denial_events``, header + tab export via ``export_workbench_tender_evidence``).

Tests: ``tender_management.tests.test_p9_08_workbench_tender_detail``,
``tender_management.tests.test_p9_09_workbench_overview_tab``,
``tender_management.tests.test_p9_10_std_readiness_tab``,
``tender_management.tests.test_p9_11_timeline_tab``,
``tender_management.tests.test_p9_12_supplier_access_tab``,
``tender_management.tests.test_p9_13_clarifications_tab``,
``tender_management.tests.test_p9_14_addenda_tab``,
``tender_management.tests.test_p9_15_submissions_tab``,
``tender_management.tests.test_p9_16_opening_readiness_tab``,
``tender_management.tests.test_p9_17_evaluation_handoff_tab``,
``tender_management.tests.test_p9_18_contract_handoff_tab``,
``tender_management.tests.test_p9_19_audit_evidence_tab``,
``tender_management.tests.test_p9_21a_evidence_export_denied_actions``,
``tender_management.tests.test_p9_24_workbench_tender_detail_section_19_2`` (§19.2 via ``tm2_workbench_section_19_2``).
Doc 9 §25 **EX-17** — ``test_EX_17_*`` in ``test_p9_08_workbench_tender_detail`` (§17.1 tab DTOs + §16.3 action bar).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, fmt_money, format_datetime, get_datetime, get_system_timezone, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.tm2_workbench_actor_context import (
	tm2_workbench_desk_security_context,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_list import (
	_blocker_bits,
)
from kentender_procurement.tender_management.services.export_tender_evidence import (
	tender_status_in_post_opening_evidence_corridor,
)
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	_resolve_tm2,
)
from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
	_user_facing_dem_blocker,
)
from kentender_procurement.tender_management.services.tm2_workbench_terminology import (
	business_label_for_checklist_row,
	business_label_for_derived_output,
	business_label_for_output_field,
	business_label_for_readiness_status,
	business_label_for_technical_term,
	business_label_for_tender_status,
	CONTRACT_HANDOFF_SUMMARY_NOTICE,
	CONTRACT_TERMS_READ_ONLY_NOTICE,
	CONTRACT_UNCORRECTED_PRICE_EDUCATION,
	EVALUATION_CRITERIA_FIXED_NOTICE,
	EVALUATION_RULES_READ_ONLY_NOTICE,
	EVIDENCE_EXPORT_TAB_NOTICE,
	format_lifecycle_audit_display_line,
	READ_ONLY_TAB_NOTICE_ADDENDA,
	READ_ONLY_TAB_NOTICE_AUDIT,
	READ_ONLY_TAB_NOTICE_CLARIFICATIONS,
	READ_ONLY_TAB_NOTICE_CONTRACT,
	READ_ONLY_TAB_NOTICE_EVALUATION,
	READ_ONLY_TAB_NOTICE_OPENING,
	READ_ONLY_TAB_NOTICE_SUBMISSIONS,
	READ_ONLY_TAB_NOTICE_SUPPLIER_ACCESS,
	WORKS_CONTRACT_VALUE_SOURCE_NOTICE,
)
from kentender_procurement.tender_management.services.tm2_sensitive_denial_events import (
	denied_actions_for_audit_evidence_tab,
)

_OBJECT_TYPE = "TM2 Tender"

# Order + short labels for the workbench action bar (existing tender context).
_WORKBENCH_DETAIL_ACTION_CODES: tuple[tuple[str, str], ...] = (
	("TND2_VIEW", _("View")),
	("TND2_EDIT_DRAFT", _("Edit draft")),
	("TND2_BIND_STD", _("Link official template")),
	("TND2_RUN_READINESS", _("Run publication check")),
	("TND2_SUBMIT_PUBLICATION_REVIEW", _("Submit for review")),
	("TND2_RETURN_CORRECTION", _("Return for correction")),
	("TND2_APPROVE_PUBLICATION", _("Approve publication")),
	("TND2_PUBLISH", _("Publish")),
	("TND2_CANCEL", _("Cancel tender")),
	("TND2_MARK_RETENDER_REQUIRED", _("Mark retender required")),
	("TND2_SUPERSEDE", _("Supersede")),
)

_OUTPUT_DEFS: tuple[tuple[str, str, str], ...] = (
	("bundle_output_code", "bundle_current", business_label_for_technical_term("Bundle")),
	("dsm_output_code", "dsm_current", business_label_for_technical_term("DSM")),
	("dom_output_code", "dom_current", business_label_for_technical_term("DOM")),
	("dem_output_code", "dem_current", business_label_for_technical_term("DEM")),
	("dcm_output_code", "dcm_current", business_label_for_technical_term("DCM")),
)


def _timeline_bits(tm2_name: str) -> tuple[str | None, str, str]:
	rows = frappe.get_all(
		"TM2 Tender Timeline",
		filters={"tm2_tender": tm2_name},
		fields=["submission_deadline_at", "timezone"],
		limit=1,
	)
	if not rows:
		return None, "", ""
	r = rows[0]
	dt = r.get("submission_deadline_at")
	tz = cstr(r.get("timezone") or "").strip() or ""
	if not dt:
		return None, tz, ""
	label = format_datetime(dt)
	if tz:
		label = f"{label} {tz}"
	return cstr(dt) if dt else None, tz, label


def _active_binding(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={"tm2_tender": tm2_name, "is_active": 1},
		fields=[
			"name",
			"binding_code",
			"std_template",
			"std_template_code",
			"std_template_version_code",
			"std_applicability_profile_code",
			"tender_std_instance_code",
			"binding_status",
			"readiness_status",
			"bundle_output_code",
			"dsm_output_code",
			"dom_output_code",
			"dem_output_code",
			"dcm_output_code",
			"publication_snapshot_code",
			"published_snapshot_hash",
			"bound_by",
			"bound_at",
		],
		limit=1,
	)
	return rows[0] if rows else None


def _latest_readiness(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Publication Readiness",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"readiness_code",
			"readiness_status",
			"std_readiness_status",
			"package_lineage_valid",
			"template_version_active",
			"std_instance_exists",
			"parameters_complete",
			"sections_complete",
			"bundle_current",
			"dsm_current",
			"dom_current",
			"dem_current",
			"dcm_current",
			"supplier_access_valid",
			"timeline_valid",
			"unresolved_blocker_count",
			"warning_count",
			"validation_payload",
			"validated_by",
			"validated_at",
			"validation_run_number",
		],
		order_by="creation desc",
		limit=1,
	)
	return rows[0] if rows else None


def _parse_validation_payload(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			return json.loads(raw)
		except json.JSONDecodeError:
			return {}
	return {}


def _std_template_display(std_template_name: str | None) -> dict[str, str]:
	out: dict[str, str] = {"template_code": "", "template_title": "", "lifecycle_status": ""}
	nm = cstr(std_template_name or "").strip()
	if not nm or not frappe.db.exists("STD Template", nm):
		return out
	row = frappe.db.get_value(
		"STD Template",
		nm,
		["template_code", "template_title", "lifecycle_status"],
		as_dict=True,
	)
	if not row:
		return out
	return {
		"template_code": cstr(row.get("template_code") or "").strip(),
		"template_title": cstr(row.get("template_title") or "").strip(),
		"lifecycle_status": cstr(row.get("lifecycle_status") or "").strip(),
	}


def _checklist_tri(flag: Any, *, has_readiness: bool) -> str:
	if not has_readiness:
		return "unknown"
	if flag is None:
		return "unknown"
	return "pass" if bool(int(flag or 0)) else "fail"


def _dem_missing_block(
	bind: dict[str, Any] | None,
	readiness: dict[str, Any] | None,
	vpayload: dict[str, Any],
) -> dict[str, Any] | None:
	if not bind:
		return None
	if not readiness:
		return None
	codes = list(vpayload.get("doc9_pack_codes") or [])
	in_pack = "DEM_MISSING_OR_STALE" in codes
	dem_code = cstr(bind.get("dem_output_code") or "").strip()
	dem_current = bool(int(readiness.get("dem_current") or 0))
	if in_pack or not dem_code or not dem_current:
		user_msg = _user_facing_dem_blocker("DEM_MISSING_OR_STALE")
		return {
			"blocker_code": "DEM_MISSING_OR_STALE",
			"headline": user_msg
			or _("Publication blocked: evaluation rules are missing or out of date."),
			"owner": _("STD Engine"),
			"required_action": _(
				"Complete Evaluation and Qualification Criteria, then generate or refresh the evaluation rules."
			),
			"severity": "Critical",
		}
	return None


def _build_std_readiness_tab(
	bind: dict[str, Any] | None,
	readiness: dict[str, Any] | None,
) -> dict[str, Any]:
	has_r = readiness is not None
	vpayload = _parse_validation_payload(readiness.get("validation_payload") if readiness else None)
	dem_block = _dem_missing_block(bind, readiness, vpayload)

	std_tpl_name = cstr(bind.get("std_template") or "").strip() if bind else ""
	std_disp = _std_template_display(std_tpl_name or None)
	snap = cstr(bind.get("publication_snapshot_code") or "").strip() if bind else ""
	phash = cstr(bind.get("published_snapshot_hash") or "").strip() if bind else ""
	bound_at = bind.get("bound_at") if bind else None
	bound_at_disp = format_datetime(bound_at) if bound_at else ""

	binding_block: dict[str, Any] = {
		"std_template_code": cstr(bind.get("std_template_code") or "").strip() if bind else "",
		"std_template_title": std_disp.get("template_title") or std_disp.get("template_code") or "",
		"std_template_lifecycle": std_disp.get("lifecycle_status") or "",
		"std_template_version_code": cstr(bind.get("std_template_version_code") or "").strip() if bind else "",
		"std_applicability_profile_code": cstr(bind.get("std_applicability_profile_code") or "").strip() if bind else "",
		"tender_std_instance_code": cstr(bind.get("tender_std_instance_code") or "").strip() if bind else "",
		"binding_code": cstr(bind.get("binding_code") or "").strip() if bind else "",
		"binding_status": cstr(bind.get("binding_status") or "").strip() if bind else "",
		"bound_by": cstr(bind.get("bound_by") or "").strip() if bind else "",
		"bound_at_display": bound_at_disp,
		"publication_snapshot_code": snap,
		"published_snapshot_hash": phash,
	}

	readiness_meta: dict[str, Any] = {
		"readiness_code": cstr(readiness.get("readiness_code") or "").strip() if readiness else "",
		"readiness_status": cstr(readiness.get("readiness_status") or "").strip() if readiness else "",
		"std_readiness_status": cstr(readiness.get("std_readiness_status") or "").strip() if readiness else "",
		"validation_run_number": int(readiness.get("validation_run_number") or 0) if readiness else 0,
		"validated_by": cstr(readiness.get("validated_by") or "").strip() if readiness else "",
		"validated_at_display": format_datetime(readiness.get("validated_at"))
		if readiness and readiness.get("validated_at")
		else "",
	}

	owner = _("STD Engine")
	src = _("Tender Management")

	def _row(
		rid: str,
		label: str,
		flag: Any,
		*,
		output_code: str = "",
	) -> dict[str, Any]:
		tech_label = str(label)
		return {
			"id": rid,
			"label": business_label_for_checklist_row(rid, tech_label),
			"technical_label": tech_label,
			"status": _checklist_tri(flag, has_readiness=has_r),
			"output_code": output_code,
			"owner": str(owner),
			"source_module": str(src),
		}

	checklist: list[dict[str, Any]] = [
		_row("package_lineage_valid", _("Package lineage valid"), readiness.get("package_lineage_valid") if readiness else None),
		_row("template_version_active", _("Template version active"), readiness.get("template_version_active") if readiness else None),
		_row("std_instance_exists", _("STD instance exists"), readiness.get("std_instance_exists") if readiness else None),
		_row("parameters_complete", _("Parameters complete"), readiness.get("parameters_complete") if readiness else None),
		_row("sections_complete", _("Sections complete"), readiness.get("sections_complete") if readiness else None),
		_row(
			"bundle_current",
			_("Bundle current"),
			readiness.get("bundle_current") if readiness else None,
			output_code=cstr(bind.get("bundle_output_code") or "").strip() if bind else "",
		),
		_row(
			"dsm_current",
			_("DSM current"),
			readiness.get("dsm_current") if readiness else None,
			output_code=cstr(bind.get("dsm_output_code") or "").strip() if bind else "",
		),
		_row(
			"dom_current",
			_("DOM current"),
			readiness.get("dom_current") if readiness else None,
			output_code=cstr(bind.get("dom_output_code") or "").strip() if bind else "",
		),
		_row(
			"dem_current",
			_("DEM current"),
			readiness.get("dem_current") if readiness else None,
			output_code=cstr(bind.get("dem_output_code") or "").strip() if bind else "",
		),
		_row(
			"dcm_current",
			_("DCM current"),
			readiness.get("dcm_current") if readiness else None,
			output_code=cstr(bind.get("dcm_output_code") or "").strip() if bind else "",
		),
		_row(
			"publication_snapshot",
			_("Publication snapshot available"),
			1 if snap else (0 if bind else None),
			output_code=snap,
		),
		_row("timeline_valid", _("Timeline valid"), readiness.get("timeline_valid") if readiness else None),
		_row("supplier_access_valid", _("Supplier access valid"), readiness.get("supplier_access_valid") if readiness else None),
		_row(
			"no_critical_blockers",
			_("No critical blockers (unresolved = 0)"),
			1
			if has_r and int(readiness.get("unresolved_blocker_count") or 0) == 0
			else (0 if has_r else None),
		),
	]

	derived: list[dict[str, str]] = [
		{
			"id": "bundle",
			"label": business_label_for_derived_output("bundle", _("Bundle")),
			"technical_label": "Bundle",
			"code": cstr(bind.get("bundle_output_code") or "").strip() if bind else "",
		},
		{
			"id": "dsm",
			"label": business_label_for_derived_output("dsm", _("DSM")),
			"technical_label": "DSM",
			"code": cstr(bind.get("dsm_output_code") or "").strip() if bind else "",
		},
		{
			"id": "dom",
			"label": business_label_for_derived_output("dom", _("DOM")),
			"technical_label": "DOM",
			"code": cstr(bind.get("dom_output_code") or "").strip() if bind else "",
		},
		{
			"id": "dem",
			"label": business_label_for_derived_output("dem", _("DEM")),
			"technical_label": "DEM",
			"code": cstr(bind.get("dem_output_code") or "").strip() if bind else "",
		},
		{
			"id": "dcm",
			"label": business_label_for_derived_output("dcm", _("DCM")),
			"technical_label": "DCM",
			"code": cstr(bind.get("dcm_output_code") or "").strip() if bind else "",
		},
	]

	return {
		"binding": binding_block,
		"readiness_meta": readiness_meta,
		"readiness_checklist": checklist,
		"derived_outputs": derived,
		"dem_missing_block": dem_block,
	}


def _availability_context(tm2_status: str, desk_ctx: dict[str, Any]) -> dict[str, Any]:
	out = dict(desk_ctx)
	out["object_exists"] = True
	out["state_authorization"] = {"kind": "tender", "status": (tm2_status or "").strip()}
	return out


def _action_ui_state(avail: dict[str, Any]) -> str:
	if avail.get("allowed"):
		return "enabled"
	return "disabled"


_CLAR_PENDING: tuple[str, ...] = ("Submitted", "Under Review", "Response Drafted", "Pending Approval")

# Doc 9 §17.6 wireframe + doc 6 §19.2 — filter chip order on Clarifications tab.
_CLARIFICATION_TAB_STATUS_ORDER: tuple[str, ...] = (
	"Submitted",
	"Under Review",
	"Pending Approval",
	"Published",
	"Converted to Addendum",
	"Response Drafted",
	"Rejected",
	"Withdrawn",
)

_ADDENDUM_MATERIAL_CLARIFICATION_WARNING: str = _(
	"This response appears to change tender requirements. It must be handled as an addendum, not as an ordinary clarification.",
)

# Doc 9 §17.7 / TM2 Addendum — filter chip order on Addenda tab.
_ADDENDUM_TAB_STATUS_ORDER: tuple[str, ...] = (
	"Draft",
	"Impact Analysis Pending",
	"Impact Analysis Complete",
	"Pending Legal Review",
	"Pending Approval",
	"Approved",
	"Issued",
	"Cancelled",
	"Superseded",
	"Withdrawn",
)

_TERMINAL_ADDENDUM_STATUSES: frozenset[str] = frozenset(
	{"Issued", "Cancelled", "Superseded", "Withdrawn"},
)

_MONITOR_STATUSES: frozenset[str] = frozenset(
	{
		"Published",
		"Closed",
		"Closed - No Valid Submissions",
		"Cancelled",
		"Superseded",
		"Archived",
	},
)

# Doc 6 §21.3 — tender lifecycle states where internal workbench may surface post-opening bid metadata.
_POST_OPENING_TENDER_STATUSES: frozenset[str] = frozenset(
	{
		"Opening Completed",
		"Evaluation Ready",
		"Evaluation In Progress",
		"Awarded",
		"Contract Handoff Completed",
	}
)

_SEALED_BID_INTERNAL_NOTICE: str = _(
	"Bid contents are sealed and cannot be accessed before formal opening.",
)

_BOQ_RATES_SUPPRESSED_NOTICE: str = _("Do not show BOQ line rates before lawful opening.")

# TM2 Bid Submission ``bid_status`` options (doc 9 §17.8 table / filters).
_BID_SUBMISSION_TAB_STATUS_ORDER: tuple[str, ...] = (
	"Draft",
	"Submitted",
	"Sealed",
	"Superseded",
	"Withdrawn",
	"Late Attempt Rejected",
	"Opened",
	"Excluded by System Rule",
	"Evaluation Locked",
)

_VALID_SEALED_SUBMISSION_STATUSES: frozenset[str] = frozenset(
	{"Sealed", "Opened", "Evaluation Locked"},
)

_WORKS_OPENING_ARITHMETIC_NOTICE: str = _(
	"Arithmetic correction is not performed at opening. Correction occurs only during Evaluation.",
)

_EVALUATION_CRITERIA_FIXED_NOTICE: str = EVALUATION_CRITERIA_FIXED_NOTICE

_DEM_WORKBENCH_READ_ONLY_NOTICE: str = EVALUATION_RULES_READ_ONLY_NOTICE

_DCM_WORKBENCH_READ_ONLY_NOTICE: str = CONTRACT_TERMS_READ_ONLY_NOTICE

_CONTRACT_TERMS_READ_ONLY_NOTICE: str = CONTRACT_HANDOFF_SUMMARY_NOTICE

_WORKS_CONTRACT_VALUE_SOURCE_NOTICE: str = WORKS_CONTRACT_VALUE_SOURCE_NOTICE

_CONTRACT_UNCORRECTED_PRICE_EDUCATION: str = CONTRACT_UNCORRECTED_PRICE_EDUCATION

_OPENED_BID_CODES_FOR_EVAL_TAB: frozenset[str] = frozenset({"Opened", "Evaluation Locked"})


def _count_valid_sealed_bids(tm2_name: str) -> int:
	return int(
		frappe.db.count(
			"TM2 Bid Submission",
			{"tm2_tender": tm2_name, "bid_status": ["in", list(_VALID_SEALED_SUBMISSION_STATUSES)]},
		)
	)


def _parse_sealed_submission_ref_list(raw: Any) -> list[str]:
	if isinstance(raw, dict):
		refs = raw.get("refs")
		if isinstance(refs, list):
			return [cstr(x).strip() for x in refs if cstr(x).strip()]
	if isinstance(raw, str) and raw.strip():
		try:
			d = json.loads(raw)
		except json.JSONDecodeError:
			return []
		if isinstance(d, dict):
			refs = d.get("refs")
			if isinstance(refs, list):
				return [cstr(x).strip() for x in refs if cstr(x).strip()]
	return []


def _bench_opened_bid_codes(tm2_name: str) -> list[str]:
	codes: list[str] = []
	for row in frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name},
		fields=["bid_code", "bid_status"],
		order_by="bid_code asc",
	):
		if cstr(row.get("bid_status") or "").strip() not in _OPENED_BID_CODES_FOR_EVAL_TAB:
			continue
		bc = cstr(row.get("bid_code") or "").strip()
		if bc:
			codes.append(bc)
	return sorted(set(codes))


def _bench_issued_addendum_codes(tm2_name: str) -> list[str]:
	out: list[str] = []
	for row in frappe.get_all(
		"TM2 Addendum",
		filters={"tm2_tender": tm2_name, "status": "Issued"},
		fields=["name", "addendum_code"],
		order_by="creation asc",
	):
		code = cstr(row.get("addendum_code") or row.get("name") or "").strip()
		if code:
			out.append(code)
	return sorted(set(out))


def _opening_readiness_blocker_rows(raw: Any) -> list[dict[str, str]]:
	if not raw:
		return []
	if isinstance(raw, str) and raw.strip():
		try:
			raw = json.loads(raw)
		except json.JSONDecodeError:
			return []
	if not isinstance(raw, dict):
		return []
	out: list[dict[str, str]] = []
	bl = raw.get("blockers")
	if isinstance(bl, list):
		for item in bl:
			if isinstance(item, dict):
				out.append(
					{
						"code": cstr(item.get("blocker_code") or item.get("code") or "").strip(),
						"message": cstr(item.get("message") or item.get("user_message") or "").strip(),
					},
				)
		return [b for b in out if b["code"] or b["message"]]
	code = cstr(raw.get("blocker_code") or "").strip()
	msg = cstr(raw.get("message") or raw.get("user_message") or "").strip()
	if code or msg:
		return [{"code": code, "message": msg}]
	return []


def _latest_opening_readiness_for_tm2(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Opening Readiness Record",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"opening_readiness_code",
			"readiness_status",
			"dom_output_code",
			"tender_std_instance_code",
			"tm2_tender_closing_record",
			"valid_submission_count",
			"sealed_submission_refs",
			"blocker_payload",
			"prepared_at",
			"accepted_by_opening_module_at",
			"opening_record_code",
		],
		order_by="modified desc",
		limit=1,
	)
	return rows[0] if rows else None


def _closing_record_row_for_tm2(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender Closing Record",
		filters={"tm2_tender": tm2_name},
		fields=["name", "closing_code", "closing_status", "modified"],
		order_by="modified desc",
		limit=1,
	)
	return rows[0] if rows else None


def _latest_evaluation_handoff_for_tm2(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Evaluation Handoff Record",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"evaluation_handoff_code",
			"handoff_status",
			"opening_record_code",
			"dem_output_code",
			"dsm_output_code",
			"tender_std_instance_code",
			"opened_submission_refs",
			"addendum_history_refs",
			"handoff_payload",
			"sent_at",
			"accepted_by_evaluation_at",
			"rejection_reason",
		],
		order_by="modified desc",
		limit=1,
	)
	return rows[0] if rows else None


def _latest_contract_handoff_for_tm2(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Contract Handoff Reference",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"contract_handoff_code",
			"handoff_status",
			"award_decision_code",
			"awarded_supplier",
			"dcm_output_code",
			"tender_std_instance_code",
			"final_evaluated_price",
			"currency",
			"final_boq_reference",
			"addendum_history_refs",
			"contract_handoff_payload",
			"created_at",
			"accepted_by_contract_module_at",
			"rejection_reason",
		],
		order_by="modified desc",
		limit=1,
	)
	return rows[0] if rows else None


def _opening_tab_action_hint(
	action_code: str,
	actor: str,
	tcode: str,
	actx: dict[str, Any],
) -> dict[str, Any]:
	if not spec_for_action(action_code):
		return {
			"action_code": action_code,
			"ui_state": "disabled",
			"allowed": False,
			"user_message": "",
			"denial_code": "",
		}
	avail = get_action_availability(action_code, _OBJECT_TYPE, tcode, actor, context=actx)
	return {
		"action_code": action_code,
		"ui_state": _action_ui_state(avail),
		"allowed": bool(avail.get("allowed")),
		"user_message": cstr(avail.get("user_message") or avail.get("message") or "").strip(),
		"denial_code": cstr(avail.get("denial_code") or "").strip(),
	}


def _package_lineage(tm2: Any) -> dict[str, Any]:
	pkg_code = cstr(getattr(tm2, "procurement_package_code", None) or "").strip()
	plan_code = cstr(getattr(tm2, "procurement_plan_code", None) or "").strip()
	fy = cstr(getattr(tm2, "fiscal_year", None) or "").strip()
	pkg_link = cstr(getattr(tm2, "procurement_package", None) or "").strip()
	status = ""
	if pkg_link and frappe.db.exists("Procurement Package", pkg_link):
		status = cstr(frappe.db.get_value("Procurement Package", pkg_link, "status") or "").strip()
	return {
		"package_code": pkg_code,
		"procurement_plan_code": plan_code,
		"fiscal_year": fy,
		"package_status": status,
		"lineage_display": _("{0} · plan {1} · FY {2}").format(
			pkg_code or _("—"),
			plan_code or _("—"),
			fy or _("—"),
		),
	}


def _timeline_key_dates(tm2_name: str, tm2: Any) -> dict[str, Any]:
	rows = frappe.get_all(
		"TM2 Tender Timeline",
		filters={"tm2_tender": tm2_name},
		fields=[
			"timeline_code",
			"planned_publication_at",
			"actual_publication_at",
			"clarification_deadline_at",
			"addendum_cutoff_at",
			"submission_deadline_at",
			"opening_scheduled_at",
			"tender_validity_days",
			"timezone",
			"deadline_extended",
			"extension_source_addendum_code",
		],
		limit=1,
	)
	key_dates: list[dict[str, str]] = []
	if not rows:
		return {"timeline_code": "", "timezone": "", "key_dates": key_dates}

	r = rows[0]
	tz = cstr(r.get("timezone") or "").strip()

	def _fmt_dt(col: str, label: str) -> None:
		dt = r.get(col)
		if not dt:
			return
		lab = format_datetime(dt)
		if tz:
			lab = f"{lab} {tz}"
		key_dates.append({"field": col, "label": str(label), "value": lab})

	_fmt_dt("planned_publication_at", _("Planned publication"))
	_fmt_dt("actual_publication_at", _("Actual publication"))
	_fmt_dt("clarification_deadline_at", _("Clarification deadline"))
	_fmt_dt("addendum_cutoff_at", _("Addendum cutoff"))
	_fmt_dt("submission_deadline_at", _("Submission deadline"))
	_fmt_dt("opening_scheduled_at", _("Opening scheduled"))

	pub = getattr(tm2, "published_at", None)
	if pub:
		lab = format_datetime(pub)
		if tz:
			lab = f"{lab} {tz}"
		key_dates.append({"field": "tender_published_at", "label": str(_("Published (tender)")), "value": lab})

	tvd = int(r.get("tender_validity_days") or 0)
	if tvd > 0:
		key_dates.append(
			{
				"field": "tender_validity_days",
				"label": str(_("Tender validity")),
				"value": _("{0} days").format(tvd),
			}
		)
	if bool(int(r.get("deadline_extended") or 0)):
		ext = cstr(r.get("extension_source_addendum_code") or "").strip()
		key_dates.append(
			{
				"field": "deadline_extended",
				"label": str(_("Deadline extended")),
				"value": ext or _("Yes"),
			}
		)

	return {
		"timeline_code": cstr(r.get("timeline_code") or "").strip(),
		"timezone": tz,
		"key_dates": key_dates,
	}


# Doc 9 §17.4 — show official server time for tenders that are published / post-publication lifecycle.
_STATUSES_OFFICIAL_SERVER_TIME: frozenset[str] = frozenset(
	{
		"Published",
		"Addendum Pending",
		"Suspended Pending Addendum",
		"Closed",
		"Closed - No Valid Submissions",
		"Opening Ready",
		"Opening Completed",
		"Evaluation Ready",
		"Evaluation In Progress",
		"Awarded",
		"Contract Handoff Completed",
	}
)


def _timeline_row_for_tm2(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender Timeline",
		filters={"tm2_tender": tm2_name},
		fields=[
			"clarification_deadline_at",
			"submission_deadline_at",
			"opening_scheduled_at",
			"addendum_cutoff_at",
		],
		limit=1,
	)
	return rows[0] if rows else None


def _timeline_warnings(row: dict[str, Any] | None, tab_counts: dict[str, int]) -> list[dict[str, Any]]:
	"""Doc 6 §17.4 — ordered checks (subset; policy “too short” needs external rules)."""
	out: list[dict[str, Any]] = []
	if not row:
		return out

	def _dt(col: str) -> Any | None:
		v = row.get(col)
		if not v:
			return None
		try:
			return get_datetime(v)
		except Exception:
			return None

	cd = _dt("clarification_deadline_at")
	sd = _dt("submission_deadline_at")
	od = _dt("opening_scheduled_at")
	if cd and sd and cd > sd:
		out.append(
			{
				"warning_code": "CLAR_AFTER_SUBMISSION",
				"severity": "High",
				"message": _("Clarification deadline is after the submission deadline."),
			}
		)
	if od and sd and od < sd:
		out.append(
			{
				"warning_code": "OPENING_BEFORE_SUBMISSION",
				"severity": "Critical",
				"message": _("Opening is scheduled before the submission deadline."),
			}
		)
	add_open = int(tab_counts.get("addenda_non_terminal") or 0)
	if add_open > 0 and sd:
		now = now_datetime()
		if sd > now and (sd - now).total_seconds() <= 72 * 3600:
			out.append(
				{
					"warning_code": "PENDING_ADDENDUM_NEAR_DEADLINE",
					"severity": "Medium",
					"message": _(
						"Non-terminal addendum work is open and the submission deadline is within 72 hours.",
					),
				}
			)
	return out


def _extension_history_from_audit(tm2_name: str) -> list[dict[str, Any]]:
	"""Build extension history lines from **Addendum Issued** audit payloads (doc 9 §17.4 wireframe)."""
	out: list[dict[str, Any]] = []
	rows = frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name, "event_type": "Addendum Issued"},
		fields=["event_payload"],
		order_by="occurred_at asc",
	)
	for row in rows:
		pl = _parse_validation_payload(row.get("event_payload"))
		ac = cstr(pl.get("addendum_code") or "").strip()
		if not ac:
			continue
		tl = pl.get("timeline") if isinstance(pl.get("timeline"), dict) else {}
		new_sub = cstr(tl.get("submission_deadline_at") or "").strip()
		disp = ac
		if new_sub:
			try:
				dt = get_datetime(new_sub)
				disp = _("{0}: → {1}").format(ac, format_datetime(dt))
			except Exception:
				disp = _("{0}: {1}").format(ac, new_sub)
		out.append({"addendum_code": ac, "display_line": str(disp)})
	return out


def _build_timeline_tab(
	tm2: Any,
	tender_status: str,
	timeline_detail: dict[str, Any],
	tab_counts: dict[str, int],
) -> dict[str, Any]:
	st = cstr(tender_status or "").strip()
	td = timeline_detail or {}
	tz = cstr(td.get("timezone") or "").strip() or cstr(get_system_timezone() or "").strip() or "UTC"
	row = _timeline_row_for_tm2(tm2.name)
	warnings = _timeline_warnings(row, tab_counts)
	ext = _extension_history_from_audit(tm2.name)

	show_clock = st in _STATUSES_OFFICIAL_SERVER_TIME
	official = ""
	if show_clock:
		official = str(_("Official server time: {0} {1}").format(format_datetime(now_datetime()), tz))

	post_notice: str | None = None
	if st in _STATUSES_OFFICIAL_SERVER_TIME:
		post_notice = str(
			_(
				"After publication, direct timeline editing is disabled in this view; changes must route through an addendum when permitted.",
			),
		)

	return {
		"tender_status": st,
		"timeline_code": cstr(td.get("timeline_code") or "").strip(),
		"timezone": cstr(td.get("timezone") or "").strip(),
		"key_dates": list(td.get("key_dates") or []),
		"show_official_server_time": show_clock,
		"official_server_time_display": official,
		"post_publication_notice": post_notice,
		"warnings": warnings,
		"extension_history": ext,
	}


def _supplier_display_label(supplier_code: str, supplier_name: str | None) -> str:
	code = cstr(supplier_code or "").strip()
	nm = cstr(supplier_name or "").strip()
	if nm and code:
		return f"{nm} ({code})"
	return code or nm or _("—")


def _resolve_supplier_name(supplier_link: str | None) -> str:
	nm = cstr(supplier_link or "").strip()
	if not nm:
		return ""
	if frappe.db.exists("Supplier", nm):
		row = frappe.db.get_value("Supplier", nm, ["supplier_name"], as_dict=True)
		if row:
			return cstr(row.get("supplier_name") or "").strip()
	return ""


def _active_access_rule(tm2_name: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"TM2 Tender Access Rule",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"access_rule_code",
			"visibility",
			"requires_supplier_login_for_documents",
			"requires_invitation",
			"allows_public_notice",
			"allows_public_document_download",
			"supplier_category_restriction",
			"eligibility_service_required",
			"access_policy_snapshot",
		],
		limit=1,
	)
	return rows[0] if rows else None


def _supplier_category_restriction_summary(raw: Any) -> str:
	if raw is None:
		return ""
	if isinstance(raw, (list, tuple)):
		n = len(raw)
		return str(_("{0} category rule(s)").format(n)) if n else ""
	if isinstance(raw, dict):
		n = len(raw)
		return str(_("{0} restriction key(s)").format(n)) if n else ""
	if isinstance(raw, str) and raw.strip():
		try:
			p = json.loads(raw)
			return _supplier_category_restriction_summary(p)
		except json.JSONDecodeError:
			return _("Configured")
	return ""


def _policy_snapshot_present(raw: Any) -> bool:
	if raw is None:
		return False
	if isinstance(raw, dict):
		return bool(raw)
	if isinstance(raw, str) and raw.strip():
		try:
			return bool(json.loads(raw))
		except json.JSONDecodeError:
			return True
	return False


def _eligibility_snapshot_display(snap: Any, participation_status: str) -> dict[str, str]:
	"""Bounded eligibility summary for desk (doc 6 §18.5 — denial code when ineligible)."""
	out: dict[str, str] = {"summary": _("Not assessed"), "denial_code": ""}
	st = cstr(participation_status or "").strip()
	pl: dict[str, Any] = {}
	if isinstance(snap, dict):
		pl = snap
	elif isinstance(snap, str) and snap.strip():
		pl = _parse_validation_payload(snap)
	if st == "Ineligible":
		dc = cstr(pl.get("denial_code") or pl.get("code") or "").strip()
		out["denial_code"] = dc
		out["summary"] = _("Fail — {0}").format(dc) if dc else _("Fail — supplier ineligible")
		return out
	if pl.get("eligible") is False:
		dc = cstr(pl.get("denial_code") or pl.get("code") or "").strip()
		out["denial_code"] = dc
		out["summary"] = _("Fail — {0}").format(dc) if dc else _("Fail")
		return out
	if pl.get("eligible") is True:
		out["summary"] = _("Pass")
		return out
	status = cstr(pl.get("status") or pl.get("eligibility_status") or "").strip().lower()
	if status in ("ineligible", "fail", "failed", "no"):
		dc = cstr(pl.get("denial_code") or pl.get("code") or "").strip()
		out["denial_code"] = dc
		out["summary"] = _("Fail — {0}").format(dc) if dc else _("Fail")
	elif status in ("eligible", "pass", "ok", "yes"):
		out["summary"] = _("Pass")
	elif pl:
		out["summary"] = _("Recorded")
	else:
		out["summary"] = _("Not assessed")
	return out


def _addendum_acknowledgement_summary(raw: Any) -> str:
	if raw is None:
		return str(_("—"))
	if isinstance(raw, dict):
		if not raw:
			return str(_("—"))
		# Prefer simple counts when values look like bool flags per addendum.
		if all(isinstance(v, (bool, int)) for v in raw.values()):
			done = sum(1 for v in raw.values() if bool(int(v or 0)))
			return str(_("{0} / {1} acknowledged").format(done, len(raw)))
		return str(_("{0} addendum row(s)").format(len(raw)))
	if isinstance(raw, str) and raw.strip():
		try:
			return _addendum_acknowledgement_summary(json.loads(raw))
		except json.JSONDecodeError:
			return str(_("Recorded"))
	return str(_("—"))


def _last_activity_from_participation(row: dict[str, Any]) -> str:
	parsed: list[Any] = []
	for k in (
		"bid_submitted_at",
		"bid_draft_started_at",
		"withdrawn_at",
		"documents_downloaded_at",
		"interest_expressed_at",
		"first_viewed_at",
	):
		v = row.get(k)
		if not v:
			continue
		try:
			parsed.append(get_datetime(v))
		except Exception:
			continue
	if not parsed:
		return ""
	return format_datetime(max(parsed))


def _invitation_rows(tm2_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"TM2 Tender Invitation",
		filters={"tm2_tender": tm2_name},
		fields=[
			"invitation_code",
			"supplier",
			"supplier_code",
			"supplier_name_snapshot",
			"status",
			"invited_at",
			"delivered_at",
			"accepted_at",
			"declined_at",
		],
		order_by="invitation_code asc",
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		code = cstr(r.get("supplier_code") or "").strip()
		snap_nm = cstr(r.get("supplier_name_snapshot") or "").strip()
		nm = snap_nm or _resolve_supplier_name(cstr(r.get("supplier") or "").strip())
		out.append(
			{
				"invitation_code": cstr(r.get("invitation_code") or "").strip(),
				"supplier_label": _supplier_display_label(code, nm or None),
				"status": cstr(r.get("status") or "").strip(),
				"invited_at_display": format_datetime(r.get("invited_at")) if r.get("invited_at") else "",
				"delivered_at_display": format_datetime(r.get("delivered_at")) if r.get("delivered_at") else "",
				"accepted_at_display": format_datetime(r.get("accepted_at")) if r.get("accepted_at") else "",
				"declined_at_display": format_datetime(r.get("declined_at")) if r.get("declined_at") else "",
			}
		)
	return out


def _invitation_status_by_supplier(tm2_name: str) -> dict[str, str]:
	"""Latest invitation status keyed by **Supplier** link name."""
	out: dict[str, str] = {}
	rows = frappe.get_all(
		"TM2 Tender Invitation",
		filters={"tm2_tender": tm2_name},
		fields=["supplier", "status", "modified"],
		order_by="modified desc",
	)
	for r in rows:
		sup = cstr(r.get("supplier") or "").strip()
		if not sup or sup in out:
			continue
		out[sup] = cstr(r.get("status") or "").strip()
	return out


def _participation_rows(tm2_name: str, inv_by_supplier: dict[str, str], requires_invitation: bool) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"TM2 Supplier Participation",
		filters={"tm2_tender": tm2_name},
		fields=[
			"supplier",
			"supplier_code",
			"participation_code",
			"current_status",
			"clarification_count",
			"documents_downloaded_at",
			"eligibility_snapshot",
			"addendum_acknowledgement_status",
			"first_viewed_at",
			"interest_expressed_at",
			"bid_draft_started_at",
			"bid_submitted_at",
			"withdrawn_at",
		],
		order_by="supplier_code asc",
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		sup_link = cstr(r.get("supplier") or "").strip()
		scode = cstr(r.get("supplier_code") or "").strip()
		snm = _resolve_supplier_name(sup_link) if sup_link else ""
		label = _supplier_display_label(scode, snm or None)
		elig = _eligibility_snapshot_display(r.get("eligibility_snapshot"), cstr(r.get("current_status") or ""))
		if requires_invitation:
			inv_st = inv_by_supplier.get(sup_link, "")
			inv_disp = inv_st or _("None")
		else:
			inv_disp = str(_("Not required"))
		docs_ok = bool(r.get("documents_downloaded_at"))
		out.append(
			{
				"participation_code": cstr(r.get("participation_code") or "").strip(),
				"supplier_label": label,
				"eligibility_summary": elig.get("summary") or "",
				"eligibility_denial_code": elig.get("denial_code") or "",
				"invitation_status": inv_disp,
				"participation_status": cstr(r.get("current_status") or "").strip(),
				"documents_downloaded": docs_ok,
				"clarification_count": int(r.get("clarification_count") or 0),
				"addenda_ack_summary": _addendum_acknowledgement_summary(r.get("addendum_acknowledgement_status")),
				"bid_status": cstr(r.get("current_status") or "").strip(),
				"last_activity_display": _last_activity_from_participation(r),
			}
		)
	return out


def _build_supplier_access_tab(tm2_name: str) -> dict[str, Any]:
	rule = _active_access_rule(tm2_name)
	inv_by = _invitation_status_by_supplier(tm2_name)
	req_inv = bool(int(rule.get("requires_invitation") or 0)) if rule else False

	access_block: dict[str, Any] = {
		"has_rule": rule is not None,
		"access_rule_code": cstr(rule.get("access_rule_code") or "").strip() if rule else "",
		"visibility": cstr(rule.get("visibility") or "").strip() if rule else "",
		"requires_supplier_login_for_documents": bool(int(rule.get("requires_supplier_login_for_documents") or 0))
		if rule
		else False,
		"requires_invitation": req_inv,
		"allows_public_notice": bool(int(rule.get("allows_public_notice") or 0)) if rule else False,
		"allows_public_document_download": bool(int(rule.get("allows_public_document_download") or 0)) if rule else False,
		"supplier_category_restriction_summary": _supplier_category_restriction_summary(
			rule.get("supplier_category_restriction") if rule else None,
		),
		"eligibility_service_required": bool(int(rule.get("eligibility_service_required") or 0)) if rule else False,
		"has_access_policy_snapshot": _policy_snapshot_present(rule.get("access_policy_snapshot")) if rule else False,
	}

	inv_rows = _invitation_rows(tm2_name)
	part_rows = _participation_rows(tm2_name, inv_by, req_inv)

	return {
		"access_rule": access_block,
		"invitations": inv_rows,
		"participation_rows": part_rows,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_SUPPLIER_ACCESS),
	}


def _truncate_plain_text(value: Any, max_len: int = 160) -> str:
	t = cstr(value or "").strip().replace("\r", " ").replace("\n", " ")
	if len(t) <= max_len:
		return t
	return t[: max_len - 1].rstrip() + "…"


def _clarification_section_display_row(req: dict[str, Any]) -> str:
	parts: list[str] = []
	sec = cstr(req.get("related_std_section_code") or "").strip()
	cl = cstr(req.get("related_std_clause_ref") or "").strip()
	boq = cstr(req.get("related_boq_item_code") or "").strip()
	if sec:
		parts.append(str(_("Document section {0}").format(sec)))
	if cl:
		parts.append(str(_("Clause {0}").format(cl)))
	if boq:
		parts.append(str(_("BOQ {0}").format(boq)))
	return " · ".join(parts).strip() if parts else str(_("—"))


def _clar_row_test_suffix(code_or_fallback: str) -> str:
	s = cstr(code_or_fallback or "").strip().lower()
	out: list[str] = []
	for ch in s:
		if ch.isalnum() or ch in "-_":
			out.append(ch)
		else:
			out.append("-")
	val = "".join(out).strip("-")
	return val or "row"


def _build_clarifications_tab(tm2_name: str, tender_code: str) -> dict[str, Any]:
	req_rows = frappe.get_all(
		"TM2 Clarification Request",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"clarification_code",
			"supplier",
			"supplier_code",
			"related_std_section_code",
			"related_std_clause_ref",
			"related_boq_item_code",
			"question_text",
			"submitted_at",
			"status",
			"requires_addendum",
			"tm2_converted_addendum",
		],
		order_by="submitted_at desc, modified desc",
	)
	resp_rows = frappe.get_all(
		"TM2 Clarification Response",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"tm2_clarification_request",
			"modified",
			"response_code",
			"status",
			"addendum_required",
			"response_text",
			"visibility",
			"published_at",
		],
		order_by="modified desc",
	)
	latest_resp: dict[str, dict[str, Any]] = {}
	for rr in resp_rows:
		rid = cstr(rr.get("tm2_clarification_request") or "").strip()
		if rid and rid not in latest_resp:
			latest_resp[rid] = rr

	addendum_names = {
		cstr(r.get("tm2_converted_addendum") or "").strip()
		for r in req_rows
		if cstr(r.get("tm2_converted_addendum") or "").strip()
	}
	addendum_code_by_name: dict[str, str] = {}
	if addendum_names:
		for ad in frappe.get_all(
			"TM2 Addendum",
			filters={"name": ["in", list(addendum_names)]},
			fields=["name", "addendum_code"],
		):
			addendum_code_by_name[cstr(ad["name"])] = cstr(ad.get("addendum_code") or "").strip()

	raw_counts: dict[str, int] = {}
	out_rows: list[dict[str, Any]] = []
	for rq in req_rows:
		st = cstr(rq.get("status") or "").strip()
		raw_counts[st] = raw_counts.get(st, 0) + 1

		supp_link = cstr(rq.get("supplier") or "").strip()
		s_code = cstr(rq.get("supplier_code") or "").strip()
		s_label = _supplier_display_label(
			s_code,
			_resolve_supplier_name(supp_link) if supp_link else None,
		)
		clar_code = cstr(rq.get("clarification_code") or "").strip()
		rid = cstr(rq.get("name") or "").strip()
		resp = latest_resp.get(rid) or {}
		add_req = bool(int(resp.get("addendum_required") or 0)) if resp else False
		flag_req = bool(int(rq.get("requires_addendum") or 0))
		warn_text = str(_ADDENDUM_MATERIAL_CLARIFICATION_WARNING) if add_req else ""
		conv = cstr(rq.get("tm2_converted_addendum") or "").strip()
		conv_code = addendum_code_by_name.get(conv, "") if conv else ""

		sub_at = rq.get("submitted_at")
		sub_disp = format_datetime(sub_at) if sub_at else ""

		out_rows.append(
			{
				"clarification_code": clar_code,
				"row_test_suffix": _clar_row_test_suffix(clar_code or rid),
				"supplier_label": s_label,
				"section_refs_display": _clarification_section_display_row(rq),
				"status": st,
				"question_preview": _truncate_plain_text(rq.get("question_text")),
				"submitted_at_display": sub_disp,
				"latest_response_code": cstr(resp.get("response_code") or "").strip(),
				"latest_response_status": cstr(resp.get("status") or "").strip(),
				"response_visibility": cstr(resp.get("visibility") or "").strip(),
				"converted_addendum_code": conv_code,
				"request_requires_addendum": flag_req,
				"response_addendum_required": add_req,
				"addendum_material_warning_text": warn_text,
			}
		)

	known = set(_CLARIFICATION_TAB_STATUS_ORDER)
	status_filter_order = list(_CLARIFICATION_TAB_STATUS_ORDER) + [
		k for k in sorted(raw_counts.keys()) if k not in known
	]
	status_counts = {k: int(raw_counts.get(k, 0)) for k in status_filter_order}

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"status_counts": status_counts,
		"status_filter_order": status_filter_order,
		"rows": out_rows,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_CLARIFICATIONS),
	}


def _addendum_row_test_suffix(code_or_fallback: str) -> str:
	s = cstr(code_or_fallback or "").strip().lower()
	out_ch: list[str] = []
	for ch in s:
		if ch.isalnum() or ch in "-_":
			out_ch.append(ch)
		else:
			out_ch.append("-")
	val = "".join(out_ch).strip("-")
	return val or "row"


def _addendum_affects_display(add: dict[str, Any]) -> str:
	chunks: list[str] = []
	if bool(int(add.get("affects_deadline") or 0)):
		chunks.append(str(_("Deadline")))
	pit = cstr(add.get("primary_impact_type") or "").strip()
	if "BOQ" in pit or pit == "Works Requirement Change":
		chunks.append(str(_("BOQ")))
	if bool(int(add.get("affects_submission_model") or 0)):
		chunks.append(str(_("DSM")))
	if bool(int(add.get("affects_opening_model") or 0)):
		chunks.append(str(_("DOM")))
	if bool(int(add.get("affects_evaluation_model") or 0)):
		chunks.append(str(_("DEM")))
	if bool(int(add.get("affects_contract_model") or 0)):
		chunks.append(str(_("DCM")))
	return ", ".join(chunks) if chunks else str(_("None declared"))


def _addendum_impact_analysis_status(addendum_status: str) -> str:
	s = cstr(addendum_status or "").strip()
	if s == "Draft":
		return str(_("Not requested"))
	if s == "Impact Analysis Pending":
		return str(_("In progress"))
	if s in (
		"Impact Analysis Complete",
		"Pending Legal Review",
		"Pending Approval",
		"Approved",
		"Issued",
	):
		return str(_("Complete"))
	if s in ("Cancelled", "Superseded", "Withdrawn"):
		return str(_("Closed"))
	return s or str(_("—"))


def _addendum_approval_status(addendum_status: str) -> str:
	s = cstr(addendum_status or "").strip()
	if s in ("Draft", "Impact Analysis Pending", "Impact Analysis Complete"):
		return str(_("Not in approval"))
	if s == "Pending Legal Review":
		return str(_("Legal review"))
	if s == "Pending Approval":
		return str(_("Pending approval"))
	if s == "Approved":
		return str(_("Approved"))
	if s == "Issued":
		return str(_("Issued"))
	if s in ("Cancelled", "Superseded", "Withdrawn"):
		return str(_("Closed"))
	return s or str(_("—"))


def _json_preview_lines(raw: Any, *, max_items: int = 14, max_len: int = 220) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, str):
		t = raw.strip()
		if not t:
			return []
		try:
			parsed: Any = json.loads(t)
		except json.JSONDecodeError:
			return [t[:max_len]]
		return _json_preview_lines(parsed, max_items=max_items, max_len=max_len)
	if isinstance(raw, list):
		out: list[str] = []
		for item in raw[:max_items]:
			if isinstance(item, dict):
				out.append(json.dumps(item, ensure_ascii=False)[:max_len])
			else:
				out.append(cstr(item).strip()[:max_len])
		return [x for x in out if x]
	if isinstance(raw, dict):
		return [json.dumps(raw, ensure_ascii=False)[: max_len * 2]]
	return [cstr(raw).strip()[:max_len]]


def _addendum_output_transitions(air: dict[str, Any] | None) -> list[dict[str, Any]]:
	if not air:
		return []
	pairs: tuple[tuple[str, str, str, str], ...] = (
		("bundle", str(_("Bundle")), "previous_bundle_output_code", "revised_bundle_output_code"),
		("dsm", str(_("DSM")), "previous_dsm_output_code", "revised_dsm_output_code"),
		("dom", str(_("DOM")), "previous_dom_output_code", "revised_dom_output_code"),
		("dem", str(_("DEM")), "previous_dem_output_code", "revised_dem_output_code"),
		("dcm", str(_("DCM")), "previous_dcm_output_code", "revised_dcm_output_code"),
		(
			"snapshot",
			str(_("Publication snapshot")),
			"previous_publication_snapshot_code",
			"revised_publication_snapshot_code",
		),
	)
	out: list[dict[str, Any]] = []
	for key, label, pf, rf in pairs:
		prev = cstr(air.get(pf) or "").strip()
		rev = cstr(air.get(rf) or "").strip()
		if not prev and not rev:
			continue
		arrow = f"{prev or '—'} → {rev or '—'}"
		out.append(
			{
				"output_key": key,
				"output_label": label,
				"previous_code": prev,
				"revised_code": rev,
				"arrow_display": arrow,
			}
		)
	return out


def _build_addenda_tab(tm2_name: str, tender_code: str) -> dict[str, Any]:
	add_rows = frappe.get_all(
		"TM2 Addendum",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"addendum_code",
			"addendum_number",
			"title",
			"reason",
			"status",
			"primary_impact_type",
			"affects_deadline",
			"affects_submission_model",
			"affects_opening_model",
			"affects_evaluation_model",
			"affects_contract_model",
			"requires_supplier_acknowledgement",
			"tm2_source_clarification_request",
			"issued_at",
			"approved_at",
			"created_at",
		],
		order_by="addendum_number asc, modified asc",
	)
	names = [cstr(r.get("name") or "").strip() for r in add_rows if cstr(r.get("name") or "").strip()]
	impact_by_add: dict[str, dict[str, Any]] = {}
	if names:
		for ir in frappe.get_all(
			"TM2 Addendum Impact Record",
			filters={"tm2_addendum": ["in", names]},
			fields=[
				"name",
				"tm2_addendum",
				"impact_record_code",
				"affected_parameter_refs",
				"affected_section_refs",
				"affected_boq_refs",
				"previous_bundle_output_code",
				"revised_bundle_output_code",
				"previous_dsm_output_code",
				"revised_dsm_output_code",
				"previous_dom_output_code",
				"revised_dom_output_code",
				"previous_dem_output_code",
				"revised_dem_output_code",
				"previous_dcm_output_code",
				"revised_dcm_output_code",
				"previous_publication_snapshot_code",
				"revised_publication_snapshot_code",
				"deadline_extension_required",
				"supplier_acknowledgement_required",
				"bid_resubmission_required",
			],
		):
			adn = cstr(ir.get("tm2_addendum") or "").strip()
			if adn:
				impact_by_add[adn] = ir

	raw_counts: dict[str, int] = {}
	out_rows: list[dict[str, Any]] = []
	for add in add_rows:
		st = cstr(add.get("status") or "").strip()
		raw_counts[st] = raw_counts.get(st, 0) + 1

		ad_name = cstr(add.get("name") or "").strip()
		acode = cstr(add.get("addendum_code") or "").strip()
		anum = int(add.get("addendum_number") or 0)
		air = impact_by_add.get(ad_name)
		deadline_impact = bool(int(add.get("affects_deadline") or 0))
		if air:
			deadline_impact = deadline_impact or bool(int(air.get("deadline_extension_required") or 0))
		need_ack = bool(int(add.get("requires_supplier_acknowledgement") or 0))
		if air:
			need_ack = need_ack or bool(int(air.get("supplier_acknowledgement_required") or 0))
		bid_resub = bool(int(air.get("bid_resubmission_required") or 0)) if air else False

		clr_link = cstr(add.get("tm2_source_clarification_request") or "").strip()
		clr_code = ""
		if clr_link and frappe.db.exists("TM2 Clarification Request", clr_link):
			clr_code = cstr(
				frappe.db.get_value("TM2 Clarification Request", clr_link, "clarification_code") or "",
			).strip()

		issued = add.get("issued_at")
		issued_disp = format_datetime(issued) if issued else ""

		param_lines: list[str] = []
		boq_lines: list[str] = []
		if air:
			param_lines = _json_preview_lines(air.get("affected_parameter_refs"))
			sec_lines = _json_preview_lines(air.get("affected_section_refs"))
			param_lines = (param_lines + sec_lines)[:20]
			boq_lines = _json_preview_lines(air.get("affected_boq_refs"))

		out_rows.append(
			{
				"addendum_code": acode,
				"addendum_number": anum,
				"row_test_suffix": _addendum_row_test_suffix(acode or ad_name),
				"title": cstr(add.get("title") or "").strip(),
				"status": st,
				"primary_impact_type": cstr(add.get("primary_impact_type") or "").strip(),
				"affects_display": _addendum_affects_display(add),
				"deadline_impact_display": str(_("Yes")) if deadline_impact else str(_("No")),
				"requires_supplier_acknowledgement": need_ack,
				"bid_resubmission_required": bid_resub,
				"impact_analysis_status": _addendum_impact_analysis_status(st),
				"approval_status": _addendum_approval_status(st),
				"issued_at_display": issued_disp,
				"source_clarification_code": clr_code,
				"reason_preview": _truncate_plain_text(add.get("reason"), max_len=400),
				"impact_record_code": cstr(air.get("impact_record_code") or "").strip() if air else "",
				"impact_parameter_lines": param_lines,
				"impact_boq_lines": boq_lines,
				"output_transitions": _addendum_output_transitions(air),
			}
		)

	known = set(_ADDENDUM_TAB_STATUS_ORDER)
	status_filter_order = list(_ADDENDUM_TAB_STATUS_ORDER) + [
		k for k in sorted(raw_counts.keys()) if k not in known
	]
	status_counts = {k: int(raw_counts.get(k, 0)) for k in status_filter_order}

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"status_counts": status_counts,
		"status_filter_order": status_filter_order,
		"rows": out_rows,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_ADDENDA),
	}


def _build_submissions_tab(tm2_name: str, tender_code: str, tender_status: str) -> dict[str, Any]:
	st = cstr(tender_status or "").strip()
	financials_allowed = st in _POST_OPENING_TENDER_STATUSES
	internal_sealed = not financials_allowed

	valid_sealed = int(
		frappe.db.count(
			"TM2 Bid Submission",
			{
				"tm2_tender": tm2_name,
				"bid_status": ["in", list(_VALID_SEALED_SUBMISSION_STATUSES)],
			},
		)
	)
	late_attempts = int(frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2_name}))
	withdrawn = int(frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2_name, "bid_status": "Withdrawn"}))

	receipt_by_bid: dict[str, str] = {}
	for rr in frappe.get_all(
		"TM2 Bid Receipt",
		filters={"tm2_tender": tm2_name},
		fields=["tm2_bid_submission", "receipt_code", "modified"],
		order_by="modified desc",
	):
		bn = cstr(rr.get("tm2_bid_submission") or "").strip()
		rc = cstr(rr.get("receipt_code") or "").strip()
		if bn and bn not in receipt_by_bid and rc:
			receipt_by_bid[bn] = rc

	bid_rows = frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"bid_code",
			"supplier",
			"supplier_code",
			"bid_status",
			"submitted_at",
			"sealed_at",
			"total_submitted_price",
			"currency",
		],
		order_by="submitted_at asc, modified asc",
	)

	raw_counts: dict[str, int] = {}
	out_rows: list[dict[str, Any]] = []
	for br in bid_rows:
		bst = cstr(br.get("bid_status") or "").strip()
		raw_counts[bst] = raw_counts.get(bst, 0) + 1

		bname = cstr(br.get("name") or "").strip()
		bcode = cstr(br.get("bid_code") or "").strip()
		sup_link = cstr(br.get("supplier") or "").strip()
		s_code = cstr(br.get("supplier_code") or "").strip()
		s_label = _supplier_display_label(
			s_code,
			_resolve_supplier_name(sup_link) if sup_link else None,
		)
		sub_at = br.get("submitted_at")
		sub_disp = format_datetime(sub_at) if sub_at else ""
		sealed = br.get("sealed_at")
		sealed_disp = format_datetime(sealed) if sealed else ""

		price_val = br.get("total_submitted_price")
		cur = cstr(br.get("currency") or "").strip()
		price_disp = ""
		if financials_allowed and price_val is not None:
			price_disp = cstr(price_val).strip()

		out_rows.append(
			{
				"bid_code": bcode,
				"row_test_suffix": _addendum_row_test_suffix(bcode or bname),
				"supplier_label": s_label,
				"bid_status": bst,
				"submitted_at_display": sub_disp,
				"sealed_at_display": sealed_disp,
				"receipt_code": receipt_by_bid.get(bname, ""),
				"total_submitted_price_display": price_disp,
				"currency": cur if financials_allowed else "",
			}
		)

	known = set(_BID_SUBMISSION_TAB_STATUS_ORDER)
	status_filter_order = list(_BID_SUBMISSION_TAB_STATUS_ORDER) + [
		k for k in sorted(raw_counts.keys()) if k not in known
	]
	status_counts = {k: int(raw_counts.get(k, 0)) for k in status_filter_order}

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"tender_status": st,
		"internal_view_sealed": internal_sealed,
		"post_opening_financials_allowed": financials_allowed,
		"sealed_notice": str(_SEALED_BID_INTERNAL_NOTICE) if internal_sealed else "",
		"boq_rates_suppressed_notice": str(_BOQ_RATES_SUPPRESSED_NOTICE) if internal_sealed else "",
		"summary": {
			"valid_sealed_submissions": valid_sealed,
			"late_attempts": late_attempts,
			"withdrawn_submissions": withdrawn,
		},
		"status_counts": status_counts,
		"status_filter_order": status_filter_order,
		"rows": out_rows,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_SUBMISSIONS),
	}


def _build_opening_readiness_tab(
	tm2_name: str,
	tender_code: str,
	tender_status: str,
	procurement_category: str,
	bind: dict[str, Any] | None,
	actor: str,
	actx: dict[str, Any],
) -> dict[str, Any]:
	st = cstr(tender_status or "").strip()
	cat = cstr(procurement_category or "").strip()
	works = cat.lower() == "works"
	orr = _latest_opening_readiness_for_tm2(tm2_name)
	closing_row = _closing_record_row_for_tm2(tm2_name)

	bind_dom = cstr(bind.get("dom_output_code") or "").strip() if bind else ""
	bind_snap = cstr(bind.get("publication_snapshot_code") or "").strip() if bind else ""
	bind_tsi = cstr(bind.get("tender_std_instance_code") or "").strip() if bind else ""

	orr_dom = cstr((orr or {}).get("dom_output_code") or "").strip()
	dom_display = orr_dom or bind_dom

	closing_code = ""
	closing_status = ""
	if orr:
		cl_link = cstr(orr.get("tm2_tender_closing_record") or "").strip()
		if cl_link and frappe.db.exists("TM2 Tender Closing Record", cl_link):
			cr = frappe.db.get_value(
				"TM2 Tender Closing Record",
				cl_link,
				["closing_code", "closing_status"],
				as_dict=True,
			)
			if cr:
				closing_code = cstr(cr.get("closing_code") or "").strip()
				closing_status = cstr(cr.get("closing_status") or "").strip()
	if not closing_code and closing_row:
		closing_code = cstr(closing_row.get("closing_code") or "").strip()
		closing_status = cstr(closing_row.get("closing_status") or "").strip()

	readiness_status = cstr((orr or {}).get("readiness_status") or "").strip()
	orr_code = cstr((orr or {}).get("opening_readiness_code") or "").strip()
	valid_from_orr = orr.get("valid_submission_count") if orr else None
	try:
		valid_cnt = int(valid_from_orr) if valid_from_orr is not None else _count_valid_sealed_bids(tm2_name)
	except (TypeError, ValueError):
		valid_cnt = _count_valid_sealed_bids(tm2_name)

	sealed_refs = _parse_sealed_submission_ref_list((orr or {}).get("sealed_submission_refs")) if orr else []
	sealed_ref_count = len(sealed_refs) if sealed_refs else valid_cnt

	tsi = cstr((orr or {}).get("tender_std_instance_code") or "").strip() or bind_tsi

	prepared_at = (orr or {}).get("prepared_at")
	accepted_at = (orr or {}).get("accepted_by_opening_module_at")
	prepared_disp = format_datetime(prepared_at) if prepared_at else ""
	accepted_disp = format_datetime(accepted_at) if accepted_at else ""

	opening_rec = cstr((orr or {}).get("opening_record_code") or "").strip()
	blockers = _opening_readiness_blocker_rows((orr or {}).get("blocker_payload")) if orr else []

	handoff_ready = bool(
		orr and readiness_status in ("Ready", "Sent", "Accepted"),
	)
	dom_ok = bool(dom_display)
	opening_rules: list[dict[str, str]] = [
		{
			"id": "dom_derived_only",
			"label": str(_("Use DOM-derived fields only")),
			"status": "pass" if dom_ok else "pending",
		},
		{
			"id": "display_totals_register",
			"label": str(_("Display submitted total price only through the opening register")),
			"status": "pass" if handoff_ready else "pending",
		},
		{
			"id": "no_opening_arithmetic",
			"label": str(_("Do not perform arithmetic correction at opening")),
			"status": "pass",
		},
	]

	arith_notice = str(_WORKS_OPENING_ARITHMETIC_NOTICE) if works else ""

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"tender_status": st,
		"procurement_category": cat,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_OPENING),
		"readiness_status": readiness_status,
		"opening_readiness_code": orr_code,
		"closing_record_code": closing_code,
		"closing_record_status": closing_status,
		"dom_output_code": dom_display,
		"publication_snapshot_code": bind_snap,
		"tender_std_instance_code": tsi,
		"valid_sealed_submissions_count": valid_cnt,
		"sealed_submission_ref_count": sealed_ref_count,
		"opening_record_code": opening_rec,
		"prepared_at_display": prepared_disp,
		"accepted_by_opening_module_at_display": accepted_disp,
		"readiness_blockers": blockers,
		"opening_rules": opening_rules,
		"works_arithmetic_notice": arith_notice,
		"tab_actions": {
			"prepare_opening_readiness": _opening_tab_action_hint(
				"OR2_PREPARE_OPENING_READINESS",
				actor,
				cstr(tender_code or "").strip(),
				actx,
			),
			"send_to_opening": _opening_tab_action_hint("OR2_SEND_TO_OPENING", actor, cstr(tender_code or "").strip(), actx),
		},
	}


def _evaluation_handoff_blocker_rows(ehr: dict[str, Any] | None) -> list[dict[str, str]]:
	if not ehr:
		return []
	out: list[dict[str, str]] = []
	hp = _parse_validation_payload(ehr.get("handoff_payload"))
	bl = hp.get("blockers") if isinstance(hp, dict) else None
	if isinstance(bl, list):
		for item in bl:
			if isinstance(item, dict):
				code = cstr(item.get("blocker_code") or item.get("code") or "").strip()
				msg = cstr(item.get("message") or item.get("user_message") or "").strip()
				if code or msg:
					out.append({"code": code, "message": msg})
	if cstr(ehr.get("handoff_status") or "").strip() == "Rejected":
		r = cstr(ehr.get("rejection_reason") or "").strip()
		if r:
			out.insert(0, {"code": "HANDOFF_REJECTED", "message": r[:500]})
	return out


def _opened_submission_rows_for_eval_tab(tm2_name: str, bid_codes: list[str]) -> list[dict[str, str]]:
	rows_out: list[dict[str, str]] = []
	for bc in bid_codes:
		br = frappe.get_all(
			"TM2 Bid Submission",
			filters={"tm2_tender": tm2_name, "bid_code": bc},
			fields=["name", "supplier", "supplier_code"],
			limit=1,
		)
		s_code = ""
		if br:
			sup_link = cstr(br[0].get("supplier") or "").strip()
			s_code = cstr(br[0].get("supplier_code") or "").strip()
			lbl = _supplier_display_label(
				s_code,
				_resolve_supplier_name(sup_link) if sup_link else None,
			)
		else:
			lbl = bc
		short = s_code.strip() or lbl.strip() or bc
		rows_out.append(
			{
				"bid_code": bc,
				"supplier_code": s_code,
				"supplier_label": lbl,
				"opened_participant_display": short,
				"row_test_suffix": _addendum_row_test_suffix(bc),
			},
		)
	return rows_out


def _build_evaluation_handoff_tab(
	tm2_name: str,
	tender_code: str,
	bind: dict[str, Any] | None,
	actor: str,
	actx: dict[str, Any],
) -> dict[str, Any]:
	ehr = _latest_evaluation_handoff_for_tm2(tm2_name)
	bind_dem = cstr(bind.get("dem_output_code") or "").strip() if bind else ""
	bind_dsm = cstr(bind.get("dsm_output_code") or "").strip() if bind else ""
	bind_bundle = cstr(bind.get("bundle_output_code") or "").strip() if bind else ""
	bind_snap = cstr(bind.get("publication_snapshot_code") or "").strip() if bind else ""
	bind_tsi = cstr(bind.get("tender_std_instance_code") or "").strip() if bind else ""

	ehr_dem = cstr((ehr or {}).get("dem_output_code") or "").strip()
	ehr_dsm = cstr((ehr or {}).get("dsm_output_code") or "").strip()
	ehr_tsi = cstr((ehr or {}).get("tender_std_instance_code") or "").strip()
	dem_display = ehr_dem or bind_dem
	dsm_display = ehr_dsm or bind_dsm
	tsi_display = ehr_tsi or bind_tsi

	hp = _parse_validation_payload((ehr or {}).get("handoff_payload")) if ehr else {}
	bundle_display = cstr(hp.get("bundle_output_code") or "").strip() or bind_bundle
	snap_display = cstr(hp.get("publication_snapshot_code") or "").strip() or bind_snap

	opened_codes = _parse_sealed_submission_ref_list((ehr or {}).get("opened_submission_refs")) if ehr else []
	if not opened_codes:
		opened_codes = _bench_opened_bid_codes(tm2_name)

	addendum_codes = _parse_sealed_submission_ref_list((ehr or {}).get("addendum_history_refs")) if ehr else []
	if not addendum_codes:
		addendum_codes = _bench_issued_addendum_codes(tm2_name)

	opened_rows = _opened_submission_rows_for_eval_tab(tm2_name, opened_codes)

	handoff_status = cstr((ehr or {}).get("handoff_status") or "").strip()
	ehr_code = cstr((ehr or {}).get("evaluation_handoff_code") or "").strip()
	opn = cstr((ehr or {}).get("opening_record_code") or "").strip()
	if not opn and hp:
		opn = cstr(hp.get("opening_record_code") or "").strip()

	sent_at = (ehr or {}).get("sent_at")
	acc_at = (ehr or {}).get("accepted_by_evaluation_at")
	sent_disp = format_datetime(sent_at) if sent_at else ""
	acc_disp = format_datetime(acc_at) if acc_at else ""

	blockers = _evaluation_handoff_blocker_rows(ehr)

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_EVALUATION),
		"dem_readonly_notice": str(_DEM_WORKBENCH_READ_ONLY_NOTICE),
		"criteria_derived_notice": str(_EVALUATION_CRITERIA_FIXED_NOTICE),
		"handoff_status": handoff_status,
		"evaluation_handoff_code": ehr_code,
		"opening_record_code": opn,
		"dem_output_code": dem_display,
		"dsm_output_code": dsm_display,
		"bundle_output_code": bundle_display,
		"publication_snapshot_code": snap_display,
		"tender_std_instance_code": tsi_display,
		"opened_submissions": opened_rows,
		"opened_submissions_display": ", ".join(
			cstr(r.get("opened_participant_display") or r.get("supplier_code") or r.get("bid_code") or "").strip()
			for r in opened_rows
			if cstr(r.get("opened_participant_display") or r.get("supplier_code") or r.get("bid_code") or "").strip()
		),
		"addendum_codes": addendum_codes,
		"addenda_display": ", ".join(addendum_codes) if addendum_codes else "",
		"sent_at_display": sent_disp,
		"accepted_by_evaluation_at_display": acc_disp,
		"handoff_blockers": blockers,
		"tab_actions": {
			"prepare_evaluation_handoff": _opening_tab_action_hint(
				"EV2_PREPARE_EVALUATION_HANDOFF",
				actor,
				cstr(tender_code or "").strip(),
				actx,
			),
			"send_to_evaluation": _opening_tab_action_hint(
				"EV2_SEND_TO_EVALUATION",
				actor,
				cstr(tender_code or "").strip(),
				actx,
			),
		},
	}


def _contract_handoff_blocker_rows(chr_row: dict[str, Any] | None) -> list[dict[str, str]]:
	if not chr_row:
		return []
	out: list[dict[str, str]] = []
	hp = _parse_validation_payload(chr_row.get("contract_handoff_payload"))
	bl = hp.get("blockers") if isinstance(hp, dict) else None
	if isinstance(bl, list):
		for item in bl:
			if isinstance(item, dict):
				code = cstr(item.get("blocker_code") or item.get("code") or "").strip()
				msg = cstr(item.get("message") or item.get("user_message") or "").strip()
				if code or msg:
					out.append({"code": code, "message": msg})
	if cstr(chr_row.get("handoff_status") or "").strip() == "Rejected":
		r = cstr(chr_row.get("rejection_reason") or "").strip()
		if r:
			out.insert(0, {"code": "HANDOFF_REJECTED", "message": r[:500]})
	return out


def _format_currency_amount_for_tab(amount: Any, currency: str) -> str:
	cur = cstr(currency or "").strip() or "KES"
	try:
		val = flt(amount)
	except Exception:
		val = 0.0
	if not val:
		return ""
	try:
		return cstr(fmt_money(val, currency=cur))
	except Exception:
		return f"{val:,.2f} {cur}".strip()


def _awarded_supplier_display(supplier_link: str) -> dict[str, str]:
	nm = cstr(supplier_link or "").strip()
	if not nm:
		return {"label": "", "code": ""}
	resolved = nm
	if not frappe.db.exists("Supplier", nm):
		alt = frappe.db.get_value("Supplier", {"supplier_name": nm}, "name")
		if not alt:
			return {"label": "", "code": ""}
		resolved = str(alt)
	meta = frappe.get_meta("Supplier")
	fields: list[str] = ["supplier_name"]
	if meta.has_field("supplier_code"):
		fields.append("supplier_code")
	row = frappe.db.get_value("Supplier", resolved, fields, as_dict=True)
	if not row:
		return {"label": "", "code": ""}
	sc = cstr(row.get("supplier_code") or "").strip() if meta.has_field("supplier_code") else ""
	sn = cstr(row.get("supplier_name") or "").strip()
	lbl = _supplier_display_label(sc, sn if sn else None)
	return {"label": lbl, "code": sc}


def _build_contract_handoff_tab(
	tm2_name: str,
	tender_code: str,
	procurement_category: str,
	bind: dict[str, Any] | None,
	actor: str,
	actx: dict[str, Any],
) -> dict[str, Any]:
	cat = cstr(procurement_category or "").strip()
	works = cat.lower() == "works"
	chr_row = _latest_contract_handoff_for_tm2(tm2_name)

	bind_dcm = cstr(bind.get("dcm_output_code") or "").strip() if bind else ""
	bind_snap = cstr(bind.get("publication_snapshot_code") or "").strip() if bind else ""
	bind_tsi = cstr(bind.get("tender_std_instance_code") or "").strip() if bind else ""

	chr_dcm = cstr((chr_row or {}).get("dcm_output_code") or "").strip()
	chr_tsi = cstr((chr_row or {}).get("tender_std_instance_code") or "").strip()
	dcm_display = chr_dcm or bind_dcm
	tsi_display = chr_tsi or bind_tsi

	hp = _parse_validation_payload((chr_row or {}).get("contract_handoff_payload")) if chr_row else {}
	snap_display = cstr(hp.get("publication_snapshot_code") or "").strip() or bind_snap

	award_code = cstr((chr_row or {}).get("award_decision_code") or "").strip() or cstr(hp.get("award_decision_code") or "").strip()
	chr_code = cstr((chr_row or {}).get("contract_handoff_code") or "").strip()
	handoff_status = cstr((chr_row or {}).get("handoff_status") or "").strip()

	sup_link = cstr((chr_row or {}).get("awarded_supplier") or "").strip() or cstr(hp.get("awarded_supplier") or "").strip()
	sup_disp = _awarded_supplier_display(sup_link)

	cur = cstr((chr_row or {}).get("currency") or hp.get("currency") or "").strip() or "KES"
	price_raw = (chr_row or {}).get("final_evaluated_price") if chr_row else None
	if price_raw is None and hp:
		price_raw = hp.get("final_evaluated_price")
	price_disp = _format_currency_amount_for_tab(price_raw, cur) if price_raw not in (None, "") else ""

	boq_ref = cstr((chr_row or {}).get("final_boq_reference") or "").strip() if chr_row else ""
	if not boq_ref and hp:
		boq_ref = cstr(hp.get("final_boq_reference") or "").strip()

	addendum_codes = _parse_sealed_submission_ref_list((chr_row or {}).get("addendum_history_refs")) if chr_row else []
	if not addendum_codes:
		addendum_codes = _bench_issued_addendum_codes(tm2_name)

	created_at = (chr_row or {}).get("created_at")
	acc_at = (chr_row or {}).get("accepted_by_contract_module_at")
	created_disp = format_datetime(created_at) if created_at else ""
	acc_disp = format_datetime(acc_at) if acc_at else ""

	blockers = _contract_handoff_blocker_rows(chr_row)

	works_value_notice = str(_WORKS_CONTRACT_VALUE_SOURCE_NOTICE) if works else ""
	uncorrected_edu = str(_CONTRACT_UNCORRECTED_PRICE_EDUCATION) if works else ""

	return {
		"tender_code": cstr(tender_code or "").strip(),
		"procurement_category": cat,
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_CONTRACT),
		"dcm_readonly_notice": str(_DCM_WORKBENCH_READ_ONLY_NOTICE),
		"contract_terms_notice": str(_CONTRACT_TERMS_READ_ONLY_NOTICE),
		"works_contract_value_source_notice": works_value_notice,
		"uncorrected_price_education_notice": uncorrected_edu,
		"handoff_status": handoff_status,
		"contract_handoff_code": chr_code,
		"award_decision_code": award_code,
		"awarded_supplier_label": sup_disp.get("label") or "",
		"awarded_supplier_code": sup_disp.get("code") or "",
		"dcm_output_code": dcm_display,
		"publication_snapshot_code": snap_display,
		"tender_std_instance_code": tsi_display,
		"final_evaluated_price_display": price_disp,
		"currency": cur,
		"final_boq_reference": boq_ref,
		"addendum_codes": addendum_codes,
		"addenda_display": ", ".join(addendum_codes) if addendum_codes else "",
		"created_at_display": created_disp,
		"accepted_by_contract_module_at_display": acc_disp,
		"handoff_blockers": blockers,
		"tab_actions": {
			"create_contract_handoff": _opening_tab_action_hint(
				"CON2_CREATE_CONTRACT_HANDOFF",
				actor,
				cstr(tender_code or "").strip(),
				actx,
			),
		},
	}


def _audit_lifecycle_timeline(tm2_name: str, limit: int = 120) -> list[dict[str, Any]]:
	lim = max(1, min(int(limit or 120), 200))
	rows = frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name},
		fields=[
			"event_type",
			"occurred_at",
			"new_state",
			"previous_state",
			"denial_code",
		],
		order_by="occurred_at asc, creation asc",
		limit=lim,
	)
	out: list[dict[str, Any]] = []
	for idx, row in enumerate(rows):
		et = cstr(row.get("event_type") or "").strip()
		dc = cstr(row.get("denial_code") or "").strip()
		if et == "Access Denied" or dc:
			continue
		occ = row.get("occurred_at")
		ts = format_datetime(occ) if occ else ""
		line = format_lifecycle_audit_display_line(
			ts,
			et,
			cstr(row.get("previous_state") or "").strip(),
			cstr(row.get("new_state") or "").strip(),
		)
		out.append(
			{
				"occurred_at": cstr(occ) if occ else "",
				"display_line": line,
				"event_type": et,
				"row_test_suffix": str(idx),
			}
		)
	return out


def _build_audit_evidence_tab(
	tm2_name: str,
	tender_code: str,
	tender_status: str,
	actor: str,
	actx: dict[str, Any],
) -> dict[str, Any]:
	st = cstr(tender_status or "").strip()
	return {
		"tender_code": cstr(tender_code or "").strip(),
		"read_only_notice": str(READ_ONLY_TAB_NOTICE_AUDIT),
		"evidence_export_notice": str(EVIDENCE_EXPORT_TAB_NOTICE),
		"include_confidential_toggle_allowed": tender_status_in_post_opening_evidence_corridor(st),
		"lifecycle_events": _audit_lifecycle_timeline(tm2_name),
		"sensitive_denials": denied_actions_for_audit_evidence_tab(tm2_name),
		"tab_actions": {
			"export_tender_evidence": _opening_tab_action_hint(
				"AUD2_EXPORT_EVIDENCE",
				actor,
				cstr(tender_code or "").strip(),
				actx,
			),
		},
	}


def _recent_audit_events(tm2_name: str, limit: int = 10) -> list[dict[str, str]]:
	rows = frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name},
		fields=[
			"event_type",
			"occurred_at",
			"new_state",
			"previous_state",
			"denial_code",
			"reason",
		],
		order_by="occurred_at desc",
		limit=max(1, min(limit, 25)),
	)
	out: list[dict[str, str]] = []
	for row in rows:
		occ = row.get("occurred_at")
		ts = format_datetime(occ) if occ else ""
		ev = cstr(row.get("event_type") or "").strip()
		line = format_lifecycle_audit_display_line(
			ts,
			ev,
			cstr(row.get("previous_state") or "").strip(),
			cstr(row.get("new_state") or "").strip(),
		)
		out.append(
			{
				"occurred_at": cstr(occ) if occ else "",
				"display_line": line,
				"event_type": ev,
			}
		)
	return out


def _tab_counts(tm2_name: str) -> dict[str, int]:
	clar = int(
		frappe.db.count(
			"TM2 Clarification Request",
			{"tm2_tender": tm2_name, "status": ["in", list(_CLAR_PENDING)]},
		)
	)
	add_open = int(
		frappe.db.count(
			"TM2 Addendum",
			{
				"tm2_tender": tm2_name,
				"status": ["not in", list(_TERMINAL_ADDENDUM_STATUSES)],
			},
		)
	)
	bids = int(frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2_name}))
	return {
		"clarifications_open": clar,
		"addenda_non_terminal": add_open,
		"bid_submissions": bids,
	}


def _next_step_from_actions(actions: list[dict[str, Any]], bsum: str, st: str) -> dict[str, str]:
	enabled_non_view = [
		a
		for a in actions
		if a.get("ui_state") == "enabled" and str(a.get("action_code") or "") != "TND2_VIEW"
	]
	if enabled_non_view:
		a = enabled_non_view[0]
		av = a.get("availability") or {}
		head = str(a.get("label") or a.get("action_code") or "").strip()
		reason = str(av.get("user_message") or "").strip()
		if not reason and bsum:
			reason = bsum
		if not reason:
			reason = _("This action is permitted for the current lifecycle state.")
		return {"headline": _("Next step: {0}").format(head), "reason": reason}
	for a in actions:
		if a.get("ui_state") == "enabled" and str(a.get("action_code") or "") == "TND2_VIEW":
			return {
				"headline": _("Next step: open the tender record"),
				"reason": _("Use View when you need the full tender record."),
			}
	if bsum:
		return {"headline": _("Address blockers before progressing"), "reason": bsum}
	if st in _MONITOR_STATUSES:
		return {
			"headline": _("Monitor lifecycle and downstream work"),
			"reason": _("Use downstream tabs and related modules as this tender advances."),
		}
	return {
		"headline": _("Complete setup and reviews"),
		"reason": _("Run publication checks, resolve document readiness gaps, or advance publication review as applicable."),
	}


def _output_lines(binding: dict[str, Any] | None, readiness: dict[str, Any] | None) -> list[str]:
	lines: list[str] = []
	for code_field, cur_field, label in _OUTPUT_DEFS:
		code = ""
		if binding:
			code = cstr(binding.get(code_field) or "").strip()
		current = False
		if readiness is not None:
			current = bool(int(readiness.get(cur_field) or 0))
		if code:
			suffix = " ✓" if current else " · " + _("review pending")
			lines.append(f"{label}: {code}{suffix}")
		else:
			lines.append(f"{label}: " + _("—"))
	return lines


def get_workbench_tender_action_availability(
	actor: str,
	tender_code: str,
	action_code: str,
	extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§16.3 / §19.3 — single-action availability (used before execute / doc 9 POST body).

	``extra_context`` is merged into the workbench §7.3 context (doc 9 §19.3 ``context`` object).
	"""
	tc = cstr(tender_code or "").strip()
	ac = cstr(action_code or "").strip()
	if not tc or not ac:
		return {"ok": False, "message": _("Tender code and action code are required.")}
	tm2 = _resolve_tm2(tc)
	if not tm2:
		return {"ok": False, "message": _("Tender not found.")}
	tcode = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status or "").strip()
	desk = tm2_workbench_desk_security_context(actor)
	ctx = _availability_context(st, desk)
	if extra_context:
		ctx = {**ctx, **dict(extra_context)}
	if not spec_for_action(ac):
		return {"ok": False, "message": _("Unknown action code.")}
	avail = get_action_availability(ac, _OBJECT_TYPE, tcode, actor, context=ctx)
	return {"ok": True, "availability": avail}


_BATCH_ACTION_AVAIL_MAX = 50


def resolve_section_19_3_object_type(object_type: str | None) -> str:
	"""Map doc 9 §19.3 example ``Tender`` to registry ``TM2 Tender``."""
	ot = cstr(object_type or "").strip()
	if not ot or ot.lower() in ("tender", "tm2 tender"):
		return _OBJECT_TYPE
	return ot


def post_section_19_3_tm2_action_availability(
	actor: str,
	action_code: str,
	object_code: str,
	object_type: str | None = None,
	extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §19.3 single POST — ``object_code`` is business tender code when type is TM2."""
	ot = resolve_section_19_3_object_type(object_type)
	oc = cstr(object_code or "").strip()
	ac = cstr(action_code or "").strip()
	if ot != _OBJECT_TYPE:
		return {"ok": False, "message": _("Unsupported object_type for TM2 action availability.")}
	return get_workbench_tender_action_availability(actor, oc, ac, extra_context=extra_context)


def batch_workbench_tender_action_availability(
	actor: str,
	tender_code: str,
	action_codes: list[str],
	*,
	extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §19.3 batch — evaluate multiple ``action_codes`` for one tender (§7.3 per item)."""
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required."), "items": []}
	tm2 = _resolve_tm2(tc)
	if not tm2:
		return {"ok": False, "message": _("Tender not found."), "items": []}
	tcode = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status or "").strip()
	desk = tm2_workbench_desk_security_context(actor)
	ctx = _availability_context(st, desk)
	if extra_context:
		ctx = {**ctx, **dict(extra_context)}
	codes = [cstr(c or "").strip() for c in (action_codes or []) if cstr(c or "").strip()]
	if not codes:
		return {"ok": False, "message": _("At least one action code is required."), "items": []}
	if len(codes) > _BATCH_ACTION_AVAIL_MAX:
		return {
			"ok": False,
			"message": _("Too many action codes (max {0}).").format(_BATCH_ACTION_AVAIL_MAX),
			"items": [],
		}
	items: list[dict[str, Any]] = []
	for ac in codes:
		if not spec_for_action(ac):
			items.append(
				{
					"action_code": ac,
					"availability": {
						"action_code": ac,
						"object_type": _OBJECT_TYPE,
						"object_code": tcode,
						"allowed": False,
						"denial_code": "",
						"risk_level": "low",
						"required_permission": "",
						"user_message": str(_("Unknown action code.")),
						"blockers": [],
						"confirmation_required": False,
						"reason_required": False,
						"message": str(_("Unknown action code.")),
						"requires_confirmation": False,
						"audit_on_attempt": False,
						"object_state": "",
					},
				}
			)
			continue
		avail = get_action_availability(ac, _OBJECT_TYPE, tcode, actor, context=ctx)
		items.append({"action_code": ac, "availability": avail})
	return {
		"ok": True,
		"tender_code": tcode,
		"object_type": _OBJECT_TYPE,
		"items": items,
	}


def _build_status_ribbon(
	tender_status: str,
	readiness_status: str,
	blocker_summary: str,
) -> list[dict[str, Any]]:
	badges: list[dict[str, Any]] = []
	st = cstr(tender_status or "").strip()
	rs = cstr(readiness_status or "").strip()
	if st:
		sev = "warning" if st in ("STD Instance Incomplete", "Returned for Correction", "Addendum Pending") else "neutral"
		if st in ("Published", "Approved for Publication", "Opening Ready", "Evaluation Ready"):
			sev = "ready"
		badges.append(
			{
				"id": "lifecycle",
				"label": _("Lifecycle"),
				"value": business_label_for_tender_status(st),
				"severity": sev,
				"target_tab": "tm2-tab-overview",
			}
		)
	if rs:
		sev = "ready" if rs == "Ready" else "warning" if rs in ("Not Ready", "Ready With Warnings") else "blocked" if rs == "Blocked" else "neutral"
		badges.append(
			{
				"id": "readiness",
				"label": _("Document readiness"),
				"value": business_label_for_readiness_status(rs),
				"severity": sev,
				"target_tab": "tm2-tab-preparation",
			}
		)
	if blocker_summary:
		badges.append(
			{
				"id": "blockers",
				"label": _("Blockers"),
				"value": blocker_summary,
				"severity": "blocked",
				"target_tab": "tm2-tab-preparation",
			}
		)
	return badges


def get_workbench_tender_detail(actor: str, tender_code: str) -> dict[str, Any]:
	"""Return header lines, state cards, action bar, tab DTOs through §17.12 (``audit_evidence_tab``).

	For doc 9 §19.2 integration shape (nine required areas + readiness/handoff rollups), use
	:func:`~kentender_procurement.tender_management.services.tm2_workbench_section_19_2.get_section_19_2_tender_detail`
	or whitelist :func:`~kentender_procurement.tender_management.api.tm2_workbench.get_workbench_tender_detail_section_19_2`.
	"""
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required.")}

	tm2 = _resolve_tm2(tc)
	if not tm2:
		return {"ok": False, "message": _("Tender not found.")}

	tcode = cstr(tm2.tender_code).strip() or tm2.name
	title = cstr(tm2.tender_title or "").strip()
	st = cstr(tm2.status or "").strip()
	vis = cstr(tm2.tender_visibility or "").strip()
	pkg = cstr(tm2.procurement_package_code or "").strip()
	pe = cstr(tm2.procuring_entity_code or "").strip()
	method = cstr(tm2.procurement_method or "").strip()
	cat = cstr(tm2.procurement_category or "").strip()
	rs = cstr(tm2.std_readiness_status or "").strip()
	std_bound = bool(int(tm2.std_bound or 0))

	desk = tm2_workbench_desk_security_context(actor)
	actx = _availability_context(st, desk)

	bind = _active_binding(tm2.name)
	readiness = _latest_readiness(tm2.name)
	_iso, _tz, deadline_label = _timeline_bits(tm2.name)

	snap_code = ""
	if bind:
		snap_code = cstr(bind.get("publication_snapshot_code") or "").strip()
	std_ver = ""
	if bind:
		std_ver = cstr(bind.get("std_template_version_code") or "").strip()

	impacted_publication_refs: list[str] = []
	if bind:
		for code_field, _cur, label in _OUTPUT_DEFS:
			c = cstr(bind.get(code_field) or "").strip()
			if c:
				impacted_publication_refs.append(f"{label}: {c}")
		if snap_code:
			impacted_publication_refs.append(_("Snapshot: {0}").format(snap_code))

	header_lines = [
		f"{tcode} · {title}",
		_("{0} · {1} · {2} · {3}").format(pkg, pe, method, cat),
		_("{0} · {1} · {2}").format(
			business_label_for_tender_status(st),
			vis,
			deadline_label or _("No deadline set"),
		),
	]
	technical_header_lines = [
		_("Official document version: {0} · Published tender evidence snapshot: {1}").format(
			std_ver or _("—"),
			snap_code or _("—"),
		),
	]

	row_for_blockers = {"status": st, "std_readiness_status": rs}
	_bc, bsum = _blocker_bits(row_for_blockers)

	supplier_line = _("Supplier access: not assessed")
	if readiness is not None:
		ok_sup = bool(int(readiness.get("supplier_access_valid") or 0))
		supplier_line = _("Supplier access: {0}").format(_("Valid") if ok_sup else _("Not valid"))

	timeline_line = _("Timeline: {0}").format(deadline_label or _("No deadline set"))
	if readiness is not None and not bool(int(readiness.get("timeline_valid") or 0)):
		timeline_line += " · " + _("checks pending")

	binding_line = _("No active tender document binding")
	if bind:
		binding_line = _("Tender document binding {0} · {1} · readiness {2}").format(
			cstr(bind.get("binding_code") or "").strip() or _("—"),
			cstr(bind.get("binding_status") or "").strip() or _("—"),
			business_label_for_readiness_status(cstr(bind.get("readiness_status") or "").strip())
			or cstr(bind.get("readiness_status") or "").strip()
			or _("—"),
		)

	readiness_line = _("Latest publication readiness check: {0}").format(
		cstr(readiness.get("readiness_code") or "").strip() if readiness else _("—"),
	)
	if readiness:
		readiness_line += " · " + business_label_for_readiness_status(
			cstr(readiness.get("readiness_status") or "").strip(),
		)

	state_cards = [
		{"id": "tender_state", "title": _("Tender state"), "lines": [business_label_for_tender_status(st)]},
		{"id": "std_binding", "title": _("Tender document binding"), "lines": [binding_line]},
		{
			"id": "readiness",
			"title": _("Document readiness"),
			"lines": [business_label_for_readiness_status(rs), readiness_line],
		},
		{"id": "outputs", "title": _("Document outputs"), "lines": _output_lines(bind, readiness)},
		{
			"id": "publication_snapshot",
			"title": _("Published tender evidence snapshot"),
			"lines": [snap_code or _("None")],
		},
		{"id": "timeline", "title": _("Timeline"), "lines": [timeline_line]},
		{"id": "supplier_access", "title": _("Supplier access"), "lines": [supplier_line]},
		{
			"id": "blockers",
			"title": _("Blockers"),
			"lines": [
				_("{0} open · {1} warnings").format(
					int(readiness.get("unresolved_blocker_count") or 0) if readiness else 0,
					int(readiness.get("warning_count") or 0) if readiness else 0,
				),
				bsum or _("No tender-level blockers"),
			],
		},
	]

	actions: list[dict[str, Any]] = []
	for acode, short_label in _WORKBENCH_DETAIL_ACTION_CODES:
		spec = spec_for_action(acode)
		if not spec:
			continue
		avail = get_action_availability(acode, _OBJECT_TYPE, tcode, actor, context=actx)
		actions.append(
			{
				"action_code": acode,
				"label": str(short_label),
				"ui_state": _action_ui_state(avail),
				"availability": avail,
			}
		)

	timeline_detail = _timeline_key_dates(tm2.name, tm2)
	next_step = _next_step_from_actions(actions, bsum, st)
	events = _recent_audit_events(tm2.name)
	tabs = _tab_counts(tm2.name)

	std_tpl_code = ""
	if bind:
		std_tpl_code = cstr(bind.get("std_template_code") or "").strip()
	std_binding_summary: dict[str, Any] = {
		"std_template_code": std_tpl_code,
		"std_template_version_code": std_ver or "",
		"std_applicability_profile_code": cstr(bind.get("std_applicability_profile_code") or "").strip() if bind else "",
		"binding_code": cstr(bind.get("binding_code") or "").strip() if bind else "",
		"binding_status": cstr(bind.get("binding_status") or "").strip() if bind else "",
		"publication_snapshot_code": snap_code or "",
	}
	output_refs: dict[str, str] = {}
	output_refs_labeled: list[dict[str, str]] = []
	if bind:
		for code_field, _cur, label in _OUTPUT_DEFS:
			code = cstr(bind.get(code_field) or "").strip()
			output_refs[code_field] = code
			if code:
				output_refs_labeled.append(
					{
						"field": code_field,
						"label": label,
						"code": code,
					},
				)
		snap_ref = cstr(bind.get("publication_snapshot_code") or "").strip()
		if snap_ref:
			output_refs_labeled.append(
				{
					"field": "publication_snapshot_code",
					"label": business_label_for_output_field("publication_snapshot_code"),
					"code": snap_ref,
				},
			)

	overview: dict[str, Any] = {
		"tender_summary": {
			"tender_code": tcode,
			"tender_title": title,
			"procurement_method": method,
			"procurement_category": cat,
			"procuring_entity_code": pe,
			"procurement_package_code": pkg,
			"tender_visibility": vis,
			"std_readiness_status": rs,
			"tender_status": st,
		},
		"package_lineage": _package_lineage(tm2),
		"current_state": {"status": st, "std_readiness_status": rs},
		"current_required_action": next_step,
		"timeline": timeline_detail,
		"std_binding": std_binding_summary,
		"output_refs": output_refs,
		"output_refs_labeled": output_refs_labeled,
		"publication_snapshot_code": snap_code,
		"blockers_summary": bsum,
		"tab_counts": tabs,
		"recent_audit_events": events,
	}

	std_readiness_payload = _build_std_readiness_tab(bind, readiness)
	timeline_tab_payload = _build_timeline_tab(tm2, st, timeline_detail, tabs)
	supplier_access_tab_payload = _build_supplier_access_tab(tm2.name)
	clarifications_tab_payload = _build_clarifications_tab(tm2.name, tcode)
	addenda_tab_payload = _build_addenda_tab(tm2.name, tcode)
	submissions_tab_payload = _build_submissions_tab(tm2.name, tcode, st)
	opening_readiness_tab_payload = _build_opening_readiness_tab(
		tm2.name, tcode, st, cat, bind, actor, actx,
	)
	evaluation_handoff_tab_payload = _build_evaluation_handoff_tab(tm2.name, tcode, bind, actor, actx)
	contract_handoff_tab_payload = _build_contract_handoff_tab(tm2.name, tcode, cat, bind, actor, actx)
	audit_evidence_tab_payload = _build_audit_evidence_tab(tm2.name, tcode, st, actor, actx)

	return {
		"ok": True,
		"tender_code": tcode,
		"tender_title": title,
		"tender_status": st,
		"tm2_tender": tm2.name,
		"header_lines": header_lines,
		"technical_header_lines": technical_header_lines,
		"status_ribbon": _build_status_ribbon(st, rs, bsum),
		"display": {
			"tender_status_label": business_label_for_tender_status(st),
			"readiness_status_label": business_label_for_readiness_status(rs),
		},
		"state_cards": state_cards,
		"actions": actions,
		"blocker_summary": bsum,
		"std_bound": std_bound,
		"std_readiness": std_readiness_payload,
		"timeline_tab": timeline_tab_payload,
		"supplier_access_tab": supplier_access_tab_payload,
		"clarifications_tab": clarifications_tab_payload,
		"addenda_tab": addenda_tab_payload,
		"submissions_tab": submissions_tab_payload,
		"opening_readiness_tab": opening_readiness_tab_payload,
		"evaluation_handoff_tab": evaluation_handoff_tab_payload,
		"contract_handoff_tab": contract_handoff_tab_payload,
		"audit_evidence_tab": audit_evidence_tab_payload,
		"overview": overview,
		"legal": {
			"audit_notice": _(
				"This action is recorded in the tender audit trail with your user, timestamp, and tender state.",
			),
		},
		"impacted_publication_refs": impacted_publication_refs,
		"publish_target_status": _("Published"),
	}
