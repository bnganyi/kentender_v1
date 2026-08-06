# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-002 — PP2 WORKS master planning seed validator (spec §21, PP2-SEED-VAL-001–015)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final

import frappe
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	CHECKPOINT_ORDER,
	CURRENCY,
	DEFAULT_CHECKPOINT,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	INCLUSION_FISCAL_YEAR,
	INCLUSION_INCLUDED_AT,
	INCLUSION_NOTE,
	INCLUSION_PROCUREMENT_CATEGORY,
	INCLUSION_STATUS_INCLUDED,
	INCLUSION_STATUS_PACKAGED,
	JOURNEY_CODE,
	PE_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PKG_DESCRIPTION,
	PKG_FISCAL_YEAR,
	PKG_LINE_CODE,
	PKG_LINE_DESCRIPTION,
	PKG_LINE_QUANTITY,
	PKG_LINE_STATUS_RELEASED,
	PKG_LINE_TITLE,
	PKG_LINE_UOM,
	PKG_PREPARED_AT,
	PKG_PRIORITY,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PKG_TITLE,
	METHDEC_CODE,
	METHDEC_APPROVED_AT,
	METHDEC_CONTRACT_TYPE,
	METHDEC_DECIDED_AT,
	METHDEC_METHOD_BASIS,
	METHDEC_REVIEWER_USER_CODE,
	METHDEC_RULE_PROFILE_CODE,
	METHDEC_TEMPLATE_CODE,
	METHDEC_THRESHOLD_RESULT,
	PKGREV_CODE,
	PKGREV_AUDIT_EVENT_REF,
	PKGREV_DECIDED_AT,
	PKGREV_DECISION_REASON,
	PKGREV_FROM_STATE,
	PKGREV_TO_STATE,
	PKGRDY_CODE,
	PKGRDY_RUN_AT,
	PKGREL_RELEASED_AT,
	PKGREL_RELEASED_BY_USER_CODE,
	PKGCONSUME_AUDIT_EVENT_REF,
	PKGCONSUME_CODE,
	PKGCONSUME_CONSUMED_AT,
	PKGCONSUME_CONSUMED_BY_USER_CODE,
	PLAN_APPROVER_USER_CODE,
	PLAN_APPROVED_AT,
	PLAN_CODE,
	PLAN_CREATED_AT,
	PLAN_CREATOR_USER_CODE,
	PLAN_DESCRIPTION,
	PLAN_NAME,
	PLAN_PLANNING_CYCLE_CODE,
	SOURCE_BUDGET_STATUS_AT_INCLUSION,
	SOURCE_DEMAND_STATUS_AT_INCLUSION,
	STD_VERSION_CODE,
	TENDER_CODE,
	master_readiness_check_items,
	strict_readiness_snapshot,
	strict_release_evidence_links,
	strict_release_locked_summary,
	strict_release_passed_forward_summary,
	strict_consumption_result,
	master_planning_audit_events_for_checkpoint,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	build_summary,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.upstream import (
	validate_upstream_for_checkpoint,
)

_SUPPLIER_ROLE: Final[str] = "KenTender External Supplier"
_SUPPLIER_DENIED_DOCTYPES: Final[tuple[str, ...]] = (
	"Procurement Plan",
	"Procurement Package",
	"Planning Audit Event",
	"Procurement Handoff Card",
)


def _unsupported(checkpoint: str) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "UNSUPPORTED_CHECKPOINT",
		"message": f"Supported checkpoints are {', '.join(CHECKPOINT_ORDER)}.",
		"checkpoint": checkpoint,
	}


def _chk(
	check_id: str,
	ok: bool,
	pass_msg: str,
	fail_msg: str,
	*,
	required_action: str | None = None,
) -> dict[str, Any]:
	row: dict[str, Any] = {
		"check_id": check_id,
		"result": "PASS" if ok else "FAIL",
		"message": pass_msg if ok else fail_msg,
	}
	if not ok and required_action:
		row["required_action"] = required_action
	return row


def _checkpoint_index(checkpoint: str) -> int:
	cp = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	return CHECKPOINT_ORDER.index(cp)


def _safe_dict(val: Any) -> dict[str, Any]:
	if isinstance(val, dict):
		return val
	if not val:
		return {}
	try:
		parsed = frappe.parse_json(val)
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def _parse_dt(val: Any) -> datetime | None:
	if not val:
		return None
	if isinstance(val, datetime):
		return val
	if isinstance(val, str):
		for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
			try:
				return datetime.strptime(val.replace("+03:00", "").split(".")[0], fmt.split(".")[0])
			except ValueError:
				continue
	return None


def _demand_doc_name() -> str | None:
	return frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")


def _budget_line_doc_name() -> str | None:
	return frappe.db.get_value("Budget Line", {"generated_reference": BUDGET_LINE_CODE}, "name")


def _role_has_read(doctype: str, role: str) -> bool:
	return bool(frappe.db.get_value("DocPerm", {"parent": doctype, "role": role, "read": 1}, "name"))


def _normalize_item_codes(raw: Any) -> list[str]:
	if isinstance(raw, list):
		return sorted({str(c).strip() for c in raw if str(c).strip()})
	if isinstance(raw, str) and raw.strip():
		parsed = frappe.parse_json(raw)
		if isinstance(parsed, list):
			return sorted({str(c).strip() for c in parsed if str(c).strip()})
	return []


def _inclusion_refs_ok() -> bool:
	if not frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE):
		return False
	locked = _safe_dict(frappe.db.get_value("Procurement Handoff Card", INCLUSION_CODE, "locked_summary"))
	technical = _safe_dict(
		frappe.db.get_value("Procurement Handoff Card", INCLUSION_CODE, "technical_refs_json")
	)
	demand_ref = (locked.get("included_demand") or locked.get("demand_code") or "").strip()
	budget_ref = (locked.get("budget_line") or technical.get("budget_line_code") or "").strip()
	item_codes = _normalize_item_codes(locked.get("demand_item_codes") or technical.get("demand_item_codes"))
	return (
		demand_ref == DEMAND_CODE
		and budget_ref == BUDGET_LINE_CODE
		and item_codes == [DEMAND_ITEM_CODE]
	)


def _inclusion_seed_strict_ok(checkpoint_idx: int) -> bool:
	if not frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE):
		return False
	row = frappe.db.get_value(
		"Procurement Handoff Card",
		INCLUSION_CODE,
		[
			"journey_code",
			"source_object_code",
			"target_object_code",
			"generated_by",
			"generated_at",
			"is_master_seed",
			"locked_summary",
			"passed_forward_summary",
			"technical_refs_json",
		],
		as_dict=True,
	)
	if not row or not cint(row.get("is_master_seed")):
		return False

	locked = _safe_dict(row.get("locked_summary"))
	passed = _safe_dict(row.get("passed_forward_summary"))
	technical = _safe_dict(row.get("technical_refs_json"))
	generated_username = str(
		frappe.db.get_value("User", row.get("generated_by"), "username") or ""
	).strip()
	generated_at = str(row.get("generated_at") or "").split(".")[0]
	item_codes = _normalize_item_codes(locked.get("demand_item_codes") or technical.get("demand_item_codes"))

	base_ok = (
		(str(row.get("journey_code") or "").strip() == JOURNEY_CODE)
		and (str(row.get("source_object_code") or "").strip() == DEMAND_CODE)
		and (str(row.get("target_object_code") or "").strip() == PLAN_CODE)
		and (generated_username == PLAN_CREATOR_USER_CODE)
		and (generated_at == INCLUSION_INCLUDED_AT)
		and (str(locked.get("procurement_plan") or "").strip() == PLAN_CODE)
		and (str(locked.get("included_demand") or "").strip() == DEMAND_CODE)
		and (str(locked.get("budget_line") or "").strip() == BUDGET_LINE_CODE)
		and item_codes == [DEMAND_ITEM_CODE]
		and (str(locked.get("inclusion_note") or "").strip() == INCLUSION_NOTE)
		and (str(locked.get("procuring_entity_code") or "").strip() == PE_CODE)
		and (str(locked.get("fiscal_year") or "").strip() == INCLUSION_FISCAL_YEAR)
		and (str(locked.get("procurement_category") or "").strip() == INCLUSION_PROCUREMENT_CATEGORY)
		and (
			str(locked.get("source_demand_status_at_inclusion") or "").strip()
			== SOURCE_DEMAND_STATUS_AT_INCLUSION
		)
		and (
			str(locked.get("source_budget_status_at_inclusion") or "").strip()
			== SOURCE_BUDGET_STATUS_AT_INCLUSION
		)
		and (str(technical.get("inclusion_code") or "").strip() == INCLUSION_CODE)
		and (str(technical.get("budget_line_code") or "").strip() == BUDGET_LINE_CODE)
		and (str(passed.get("category") or "").strip() == INCLUSION_PROCUREMENT_CATEGORY)
		and abs(flt(passed.get("estimated_value")) - flt(ESTIMATED_VALUE)) < 0.01
		and (str(passed.get("currency") or "").strip() == CURRENCY)
	)

	if not base_ok:
		return False

	package_idx = _checkpoint_index("PACKAGE_DRAFT")
	if checkpoint_idx >= package_idx:
		return (
			str(locked.get("inclusion_status") or "").strip() == INCLUSION_STATUS_PACKAGED
			and str(locked.get("created_package_code") or "").strip() == PKG_CODE
		)
	if checkpoint_idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		return (
			str(locked.get("inclusion_status") or "").strip() == INCLUSION_STATUS_INCLUDED
			and not str(locked.get("created_package_code") or "").strip()
		)
	return base_ok


def _package_refs_ok() -> bool:
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return False
	demand_name = _demand_doc_name()
	budget_name = _budget_line_doc_name()
	plan_id, inclusion_code, demand_id, budget_line_id = frappe.db.get_value(
		"Procurement Package",
		PKG_CODE,
		("plan_id", "planning_inclusion_code", "demand_id", "budget_line_id"),
	)
	return (
		(plan_id or "").strip() == PLAN_CODE
		and (inclusion_code or "").strip() == INCLUSION_CODE
		and bool(demand_name)
		and (demand_id or "").strip() == demand_name
		and bool(budget_name)
		and (budget_line_id or "").strip() == budget_name
	)


def _latest_readiness_code_ok(code: str) -> bool:
	value = (code or "").strip()
	return value == PKGRDY_CODE or value.startswith(f"PKGRDY-{PKG_CODE}-")


def _latest_review_code_ok(code: str) -> bool:
	value = (code or "").strip()
	if not value:
		return False
	if frappe.db.exists("Package Review Decision", PKGREV_CODE):
		return value == PKGREV_CODE
	return value.startswith(f"PKGREV-{PKG_CODE}-") and bool(
		frappe.db.exists("Package Review Decision", value)
	)


def _package_seed_strict_ok(checkpoint_idx: int) -> bool:
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return False
	row = frappe.db.get_value(
		"Procurement Package",
		PKG_CODE,
		[
			"package_name",
			"package_description",
			"plan_id",
			"planning_inclusion_code",
			"demand_id",
			"budget_line_id",
			"procurement_category",
			"procurement_method",
			"required_std_category",
			"required_std_type",
			"required_std_template_version_code",
			"procuring_entity_code",
			"fiscal_year",
			"package_priority",
			"currency",
			"estimated_value",
			"journey_code",
			"status",
			"readiness_status",
			"release_code",
			"tender_code",
			"locked_after_release",
			"latest_readiness_code",
			"latest_review_code",
			"is_master_seed",
			"created_by",
			"prepared_at",
		],
		as_dict=True,
	)
	if not row or not cint(row.get("is_master_seed")):
		return False

	demand_name = _demand_doc_name()
	budget_name = _budget_line_doc_name()
	created_username = str(
		frappe.db.get_value("User", row.get("created_by"), "username") or ""
	).strip()
	prepared_at = str(row.get("prepared_at") or "").split(".")[0]

	base_ok = (
		(str(row.get("package_name") or "").strip() == PKG_TITLE)
		and (str(row.get("package_description") or "").strip() == PKG_DESCRIPTION)
		and (str(row.get("plan_id") or "").strip() == PLAN_CODE)
		and (str(row.get("planning_inclusion_code") or "").strip() == INCLUSION_CODE)
		and bool(demand_name)
		and (str(row.get("demand_id") or "").strip() == demand_name)
		and bool(budget_name)
		and (str(row.get("budget_line_id") or "").strip() == budget_name)
		and (str(row.get("procurement_category") or "").strip() == PKG_PROCUREMENT_CATEGORY)
		and (str(row.get("procurement_method") or "").strip() == "Open Tender")
		and (str(row.get("required_std_category") or "").strip() == PKG_REQUIRED_STD_CATEGORY)
		and (str(row.get("required_std_type") or "").strip() == PKG_REQUIRED_STD_TYPE)
		and (
			str(row.get("required_std_template_version_code") or "").strip() == STD_VERSION_CODE
		)
		and (str(row.get("procuring_entity_code") or "").strip() == PE_CODE)
		and (str(row.get("fiscal_year") or "").strip() == PKG_FISCAL_YEAR)
		and (str(row.get("package_priority") or "").strip() == PKG_PRIORITY)
		and (str(row.get("currency") or "").strip() == CURRENCY)
		and abs(flt(row.get("estimated_value")) - flt(ESTIMATED_VALUE)) < 0.01
		and (str(row.get("journey_code") or "").strip() == JOURNEY_CODE)
		and (created_username == PLAN_CREATOR_USER_CODE)
		and (prepared_at == PKG_PREPARED_AT)
	)

	if not base_ok:
		return False

	ready_idx = _checkpoint_index("READY_FOR_RELEASE")
	released_idx = _checkpoint_index("RELEASED_TO_TENDER")
	consumed_idx = _checkpoint_index("CONSUMED_BY_TENDER")

	if checkpoint_idx >= consumed_idx:
		return (
			str(row.get("status") or "").strip() == PKG_CONSUMED
			and str(row.get("release_code") or "").strip() == PKGREL_CODE
			and str(row.get("tender_code") or "").strip() == TENDER_CODE
			and bool(cint(row.get("locked_after_release")))
			and str(row.get("readiness_status") or "").strip() == "Passed"
			and _latest_readiness_code_ok(str(row.get("latest_readiness_code") or ""))
			and _latest_review_code_ok(str(row.get("latest_review_code") or ""))
		)
	if checkpoint_idx >= released_idx:
		return (
			str(row.get("status") or "").strip() == PKG_RELEASED
			and str(row.get("release_code") or "").strip() == PKGREL_CODE
			and not str(row.get("tender_code") or "").strip()
			and bool(cint(row.get("locked_after_release")))
			and str(row.get("readiness_status") or "").strip() == "Passed"
			and _latest_readiness_code_ok(str(row.get("latest_readiness_code") or ""))
			and _latest_review_code_ok(str(row.get("latest_review_code") or ""))
		)
	if checkpoint_idx >= ready_idx:
		return (
			str(row.get("status") or "").strip() == PKG_READY_FOR_RELEASE
			and not str(row.get("release_code") or "").strip()
			and not str(row.get("tender_code") or "").strip()
			and not cint(row.get("locked_after_release"))
			and str(row.get("readiness_status") or "").strip() == "Passed"
			and _latest_readiness_code_ok(str(row.get("latest_readiness_code") or ""))
			and _latest_review_code_ok(str(row.get("latest_review_code") or ""))
		)
	if checkpoint_idx >= _checkpoint_index("PACKAGE_DRAFT"):
		return (
			str(row.get("status") or "").strip() == PKG_DRAFT
			and not str(row.get("release_code") or "").strip()
			and not str(row.get("tender_code") or "").strip()
			and not cint(row.get("locked_after_release"))
			and str(row.get("readiness_status") or "").strip() == "Not Run"
		)
	return base_ok


def _package_line_refs_ok() -> bool:
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if not line_name:
		return False
	demand_name = _demand_doc_name()
	budget_name = _budget_line_doc_name()
	demand_id, demand_item_code, budget_line_id = frappe.db.get_value(
		"Procurement Package Line",
		line_name,
		("demand_id", "demand_item_code", "budget_line_id"),
	)
	return (
		bool(demand_name)
		and (demand_id or "").strip() == demand_name
		and (demand_item_code or "").strip() == DEMAND_ITEM_CODE
		and bool(budget_name)
		and (budget_line_id or "").strip() == budget_name
	)


def _package_line_seed_strict_ok(checkpoint_idx: int) -> bool:
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if not line_name:
		return False
	demand_name = _demand_doc_name()
	budget_name = _budget_line_doc_name()
	row = frappe.db.get_value(
		"Procurement Package Line",
		line_name,
		(
			"package_id",
			"demand_id",
			"demand_item_code",
			"budget_line_id",
			"line_title",
			"line_description",
			"procurement_category",
			"unit_of_measure",
			"quantity",
			"estimated_unit_cost",
			"amount",
			"currency",
			"line_status",
			"is_active",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	base_ok = (
		(str(row.get("package_id") or "").strip() == PKG_CODE)
		and bool(demand_name)
		and (str(row.get("demand_id") or "").strip() == demand_name)
		and (str(row.get("demand_item_code") or "").strip() == DEMAND_ITEM_CODE)
		and bool(budget_name)
		and (str(row.get("budget_line_id") or "").strip() == budget_name)
		and (str(row.get("line_title") or "").strip() == PKG_LINE_TITLE)
		and (str(row.get("line_description") or "").strip() == PKG_LINE_DESCRIPTION)
		and (str(row.get("procurement_category") or "").strip() == PKG_PROCUREMENT_CATEGORY)
		and (str(row.get("unit_of_measure") or "").strip() == PKG_LINE_UOM)
		and abs(flt(row.get("quantity")) - flt(PKG_LINE_QUANTITY)) < 0.01
		and abs(flt(row.get("estimated_unit_cost")) - flt(ESTIMATED_VALUE)) < 0.01
		and abs(flt(row.get("amount")) - flt(ESTIMATED_VALUE)) < 0.01
		and (str(row.get("currency") or "").strip() == CURRENCY)
		and bool(cint(row.get("is_active")))
		and bool(cint(row.get("is_master_seed")))
	)

	if not base_ok:
		return False

	released_idx = _checkpoint_index("RELEASED_TO_TENDER")
	if checkpoint_idx >= released_idx:
		return (str(row.get("line_status") or "").strip() == PKG_LINE_STATUS_RELEASED)
	if checkpoint_idx >= _checkpoint_index("PACKAGE_DRAFT"):
		return (str(row.get("line_status") or "").strip() == PKG_DRAFT)
	return base_ok


def _package_totals_match() -> bool:
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return False
	pkg_total = flt(frappe.db.get_value("Procurement Package", PKG_CODE, "estimated_value"))
	line_total = flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(amount), 0)
			FROM `tabProcurement Package Line`
			WHERE package_id = %s AND is_active = 1
			""",
			PKG_CODE,
		)[0][0]
	)
	return abs(pkg_total - line_total) < 0.01


def _method_decision_ok() -> bool:
	row = frappe.db.get_value(
		"Package Method Decision",
		{"package_code": PKG_CODE},
		("procurement_category", "procurement_method"),
		as_dict=True,
	)
	if not row:
		return False
	return (row.procurement_category or "").strip() == "Works" and (
		row.procurement_method or ""
	).strip() == "Open Tender"


def _method_decision_seed_strict_ok(checkpoint_idx: int) -> bool:
	if not frappe.db.exists("Package Method Decision", METHDEC_CODE):
		return False
	row = frappe.db.get_value(
		"Package Method Decision",
		METHDEC_CODE,
		(
			"method_decision_code",
			"package_code",
			"procurement_category",
			"procurement_method",
			"contract_type_expectation",
			"required_std_category",
			"required_std_type",
			"method_basis",
			"threshold_check_result",
			"template_code",
			"rule_profile_code",
			"override_flag",
			"override_reason",
			"decided_by",
			"decided_at",
			"approved_by",
			"approved_at",
			"is_current",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	decided_username = str(
		frappe.db.get_value("User", row.get("decided_by"), "username") or ""
	).strip()
	decided_at = str(row.get("decided_at") or "").split(".")[0]

	base_ok = (
		(str(row.get("method_decision_code") or "").strip() == METHDEC_CODE)
		and (str(row.get("package_code") or "").strip() == PKG_CODE)
		and (str(row.get("procurement_category") or "").strip() == PKG_PROCUREMENT_CATEGORY)
		and (str(row.get("procurement_method") or "").strip() == "Open Tender")
		and (str(row.get("contract_type_expectation") or "").strip() == METHDEC_CONTRACT_TYPE)
		and (str(row.get("required_std_category") or "").strip() == PKG_REQUIRED_STD_CATEGORY)
		and (str(row.get("required_std_type") or "").strip() == PKG_REQUIRED_STD_TYPE)
		and (str(row.get("method_basis") or "").strip() == METHDEC_METHOD_BASIS)
		and (str(row.get("threshold_check_result") or "").strip() == METHDEC_THRESHOLD_RESULT)
		and (str(row.get("template_code") or "").strip() == METHDEC_TEMPLATE_CODE)
		and (str(row.get("rule_profile_code") or "").strip() == METHDEC_RULE_PROFILE_CODE)
		and not cint(row.get("override_flag"))
		and not str(row.get("override_reason") or "").strip()
		and (decided_username == PLAN_CREATOR_USER_CODE)
		and (decided_at == METHDEC_DECIDED_AT)
		and bool(cint(row.get("is_current")))
		and bool(cint(row.get("is_master_seed")))
	)

	if not base_ok:
		return False

	ready_idx = _checkpoint_index("READY_FOR_RELEASE")
	if checkpoint_idx >= ready_idx:
		approved_username = str(
			frappe.db.get_value("User", row.get("approved_by"), "username") or ""
		).strip()
		approved_at = str(row.get("approved_at") or "").split(".")[0]
		return (
			approved_username == METHDEC_REVIEWER_USER_CODE
			and approved_at == METHDEC_APPROVED_AT
		)

	return not str(row.get("approved_by") or "").strip() and not row.get("approved_at")


def _parse_readiness_check_items(raw: Any) -> list[dict[str, Any]]:
	checks = raw
	if isinstance(checks, str):
		checks = frappe.parse_json(checks)
	if isinstance(checks, dict):
		checks = checks.get("checks") or []
	return checks if isinstance(checks, list) else []


def _readiness_check_items_strict_ok(check_items: list[dict[str, Any]]) -> bool:
	expected = {item["check_id"]: item for item in master_readiness_check_items()}
	if len(check_items) != len(expected):
		return False
	by_id = {item.get("check_id"): item for item in check_items if item.get("check_id")}
	if len(by_id) != len(expected):
		return False
	for check_id, expected_item in expected.items():
		actual = by_id.get(check_id)
		if not actual:
			return False
		if (actual.get("result") or "").strip() != "PASS":
			return False
		if (actual.get("source_object_code") or "").strip() != expected_item["source_object_code"]:
			return False
		if (actual.get("message") or "").strip() != expected_item["message"]:
			return False
	return True


def _readiness_snapshot_strict_ok(snapshot: Any) -> bool:
	if isinstance(snapshot, str):
		snapshot = frappe.parse_json(snapshot)
	if not isinstance(snapshot, dict):
		return False
	expected = strict_readiness_snapshot()
	for key, value in expected.items():
		if key == "estimated_value":
			if abs(flt(snapshot.get(key)) - flt(value)) >= 0.01:
				return False
			continue
		if key == "required_std_template_version_code":
			actual = (snapshot.get(key) or "").strip()
			if actual not in {STD_VERSION_CODE, PKG_REQUIRED_STD_TYPE}:
				return False
			continue
		if snapshot.get(key) != value:
			return False
	return True


def _readiness_seed_strict_ok(checkpoint_idx: int) -> bool:
	del checkpoint_idx
	if not frappe.db.exists("Package Readiness Result", PKGRDY_CODE):
		return False
	row = frappe.db.get_value(
		"Package Readiness Result",
		PKGRDY_CODE,
		(
			"readiness_code",
			"package_code",
			"run_by",
			"run_at",
			"result_status",
			"blocking_failure_count",
			"warning_count",
			"check_items_json",
			"source_snapshot_json",
			"stale",
			"stale_reason",
			"is_current",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	run_username = str(
		frappe.db.get_value("User", row.get("run_by"), "username") or ""
	).strip()
	run_at = str(row.get("run_at") or "").split(".")[0]
	check_items = _parse_readiness_check_items(row.get("check_items_json"))

	return (
		(str(row.get("readiness_code") or "").strip() == PKGRDY_CODE)
		and (str(row.get("package_code") or "").strip() == PKG_CODE)
		and (run_username == PLAN_CREATOR_USER_CODE)
		and (run_at == PKGRDY_RUN_AT)
		and (str(row.get("result_status") or "").strip() == READINESS_PASSED)
		and cint(row.get("blocking_failure_count")) == 0
		and cint(row.get("warning_count")) == 0
		and not cint(row.get("stale"))
		and not str(row.get("stale_reason") or "").strip()
		and bool(cint(row.get("is_current")))
		and bool(cint(row.get("is_master_seed")))
		and _readiness_check_items_strict_ok(check_items)
		and _readiness_snapshot_strict_ok(row.get("source_snapshot_json"))
	)


def _review_decision_seed_strict_ok(checkpoint_idx: int) -> bool:
	if not frappe.db.exists("Package Review Decision", PKGREV_CODE):
		return False
	row = frappe.db.get_value(
		"Package Review Decision",
		PKGREV_CODE,
		(
			"review_decision_code",
			"package_code",
			"decision_type",
			"decided_by",
			"decided_at",
			"from_state",
			"to_state",
			"decision_reason",
			"required_correction",
			"readiness_code",
			"method_decision_code",
			"audit_event_ref",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	decided_username = str(
		frappe.db.get_value("User", row.get("decided_by"), "username") or ""
	).strip()
	decided_at = str(row.get("decided_at") or "").split(".")[0]

	base_ok = (
		(str(row.get("review_decision_code") or "").strip() == PKGREV_CODE)
		and (str(row.get("package_code") or "").strip() == PKG_CODE)
		and (str(row.get("decision_type") or "").strip() == "Approved")
		and (decided_username == METHDEC_REVIEWER_USER_CODE)
		and (decided_at == PKGREV_DECIDED_AT)
		and (str(row.get("from_state") or "").strip() == PKGREV_FROM_STATE)
		and (str(row.get("to_state") or "").strip() == PKGREV_TO_STATE)
		and (str(row.get("decision_reason") or "").strip() == PKGREV_DECISION_REASON)
		and not str(row.get("required_correction") or "").strip()
		and (str(row.get("method_decision_code") or "").strip() == METHDEC_CODE)
		and (str(row.get("audit_event_ref") or "").strip() == PKGREV_AUDIT_EVENT_REF)
		and bool(cint(row.get("is_master_seed")))
	)

	if not base_ok:
		return False

	ready_idx = _checkpoint_index("READY_FOR_RELEASE")
	if checkpoint_idx >= ready_idx:
		return (str(row.get("readiness_code") or "").strip() == PKGRDY_CODE)

	return True


def _release_locked_summary_strict_ok(locked: Any) -> bool:
	locked_dict = _safe_dict(locked)
	if not locked_dict:
		return False
	expected = strict_release_locked_summary()
	for key, value in expected.items():
		if key == "estimated_value":
			if abs(flt(locked_dict.get(key)) - flt(value)) >= 0.01:
				return False
			continue
		if key in ("demand_item_codes", "package_line_codes"):
			actual = locked_dict.get(key) or []
			if list(actual) != list(value):
				return False
			continue
		if locked_dict.get(key) != value:
			return False
	return True


def _release_passed_forward_strict_ok(passed_forward: Any) -> bool:
	passed_dict = _safe_dict(passed_forward)
	if not passed_dict:
		return False
	expected = strict_release_passed_forward_summary()
	for key, value in expected.items():
		if key == "estimated_value":
			if abs(flt(passed_dict.get(key)) - flt(value)) >= 0.01:
				return False
			continue
		if key == "package_line_codes" or key == "source_approval_refs":
			actual = passed_dict.get(key) or []
			if list(actual) != list(value):
				return False
			continue
		if passed_dict.get(key) != value:
			return False
	return True


def _parse_handoff_evidence_links(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, str):
		raw = frappe.parse_json(raw)
	if isinstance(raw, dict):
		links = raw.get("links") or []
	elif isinstance(raw, list):
		links = raw
	else:
		links = []
	return [link for link in links if isinstance(link, dict)]


def _release_evidence_strict_ok(raw: Any, *, include_tender: bool = False) -> bool:
	links = _parse_handoff_evidence_links(raw)
	expected = strict_release_evidence_links(include_tender=include_tender)
	if len(links) < len(expected):
		return False
	for expected_link in expected:
		match = next(
			(
				link
				for link in links
				if (link.get("object_code") or "").strip() == expected_link["object_code"]
				and (link.get("object_type") or "").strip() == expected_link["object_type"]
			),
			None,
		)
		if not match:
			return False
		for field in ("label", "module", "visibility"):
			if (match.get(field) or "").strip() != expected_link[field]:
				return False
	return True


def _release_seed_strict_ok(checkpoint_idx: int) -> bool:
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return False
	row = frappe.db.get_value(
		"Procurement Handoff Card",
		PKGREL_CODE,
		(
			"handoff_code",
			"journey_code",
			"source_module",
			"target_module",
			"source_object_type",
			"source_object_code",
			"target_object_type",
			"target_object_code",
			"status",
			"generated_by",
			"generated_at",
			"consumed_by",
			"consumed_at",
			"locked_summary",
			"passed_forward_summary",
			"evidence_links_json",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	generated_at = str(row.get("generated_at") or "").split(".")[0]
	released_idx = _checkpoint_index("RELEASED_TO_TENDER")
	consumed_idx = _checkpoint_index("CONSUMED_BY_TENDER")
	links = _parse_handoff_evidence_links(row.get("evidence_links_json"))
	include_tender = any(
		(link.get("object_code") or "").strip() == TENDER_CODE for link in links
	)

	base_ok = (
		(str(row.get("handoff_code") or "").strip() == PKGREL_CODE)
		and (str(row.get("journey_code") or "").strip() == JOURNEY_CODE)
		and (str(row.get("source_module") or "").strip() == "Procurement Planning")
		and (str(row.get("target_module") or "").strip() == "Tender Management")
		and (str(row.get("source_object_type") or "").strip() == "Procurement Package")
		and (str(row.get("source_object_code") or "").strip() == PKG_CODE)
		and (str(row.get("generated_by") or "").strip() == PKGREL_RELEASED_BY_USER_CODE)
		and (generated_at == PKGREL_RELEASED_AT)
		and bool(cint(row.get("is_master_seed")))
		and _release_locked_summary_strict_ok(row.get("locked_summary"))
		and _release_passed_forward_strict_ok(row.get("passed_forward_summary"))
		and _release_evidence_strict_ok(row.get("evidence_links_json"), include_tender=include_tender)
	)
	if not base_ok:
		return False

	if checkpoint_idx == released_idx:
		return (
			(str(row.get("status") or "").strip() == "Handed Off")
			and not (row.get("target_object_code") or "").strip()
			and not (row.get("target_object_type") or "").strip()
			and not (row.get("consumed_by") or "").strip()
			and not row.get("consumed_at")
		)
	if checkpoint_idx >= consumed_idx:
		consumed_at = str(row.get("consumed_at") or "").split(".")[0]
		return (
			(str(row.get("status") or "").strip() == "Consumed")
			and (str(row.get("target_object_code") or "").strip() == TENDER_CODE)
			and (str(row.get("target_object_type") or "").strip() == "TM2 Tender")
			and (str(row.get("consumed_by") or "").strip() == PKGCONSUME_CONSUMED_BY_USER_CODE)
			and (consumed_at == PKGCONSUME_CONSUMED_AT)
			and _release_evidence_strict_ok(row.get("evidence_links_json"), include_tender=True)
		)
	return True


def _release_locked_summary_ok() -> bool:
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return False
	locked = frappe.db.get_value("Procurement Handoff Card", PKGREL_CODE, "locked_summary")
	return _release_locked_summary_strict_ok(locked)


def _consumption_result_strict_ok(raw: Any) -> bool:
	if isinstance(raw, str):
		raw = frappe.parse_json(raw)
	if not isinstance(raw, dict):
		return False
	expected = strict_consumption_result()
	for key, value in expected.items():
		if key == "changed_values":
			if list(raw.get(key) or []) != list(value):
				return False
			continue
		if raw.get(key) != value:
			return False
	return True


def _consumption_seed_strict_ok() -> bool:
	if not frappe.db.exists("Planning Release Consumption Record", PKGCONSUME_CODE):
		return False
	row = frappe.db.get_value(
		"Planning Release Consumption Record",
		PKGCONSUME_CODE,
		(
			"consumption_code",
			"release_code",
			"package_code",
			"consumed_by_module",
			"consumed_by",
			"consumed_at",
			"target_object_type",
			"target_object_code",
			"consumption_status",
			"consumption_result_json",
			"return_reason",
			"audit_event_ref",
			"is_master_seed",
		),
		as_dict=True,
	)
	if not row:
		return False

	consumed_username = str(
		frappe.db.get_value("User", row.get("consumed_by"), "username") or ""
	).strip()
	consumed_at = str(row.get("consumed_at") or "").split(".")[0]

	return (
		(str(row.get("consumption_code") or "").strip() == PKGCONSUME_CODE)
		and (str(row.get("release_code") or "").strip() == PKGREL_CODE)
		and (str(row.get("package_code") or "").strip() == PKG_CODE)
		and (str(row.get("consumed_by_module") or "").strip() == "Tender Management")
		and (consumed_username == PKGCONSUME_CONSUMED_BY_USER_CODE)
		and (consumed_at == PKGCONSUME_CONSUMED_AT)
		and (str(row.get("target_object_type") or "").strip() == "TM2 Tender")
		and (str(row.get("target_object_code") or "").strip() == TENDER_CODE)
		and (str(row.get("consumption_status") or "").strip() == "Consumed")
		and not str(row.get("return_reason") or "").strip()
		and (str(row.get("audit_event_ref") or "").strip() == PKGCONSUME_AUDIT_EVENT_REF)
		and bool(cint(row.get("is_master_seed")))
		and _consumption_result_strict_ok(row.get("consumption_result_json"))
	)


def _consumption_links_tender() -> bool:
	return _consumption_seed_strict_ok()


def _audit_actor_username(actor: str | None) -> str:
	if not actor or not frappe.db.exists("User", actor):
		return ""
	return str(frappe.db.get_value("User", actor, "username") or "").strip()


def _nullable_state(value: Any) -> str:
	return str(value or "").strip()


def _audit_event_row_strict_ok(row: dict[str, Any] | None, expected: dict[str, Any]) -> bool:
	if not row:
		return False
	occurred_at = str(row.get("occurred_at") or "").split(".")[0]
	expected_at = str(expected.get("occurred_at") or "").split(".")[0]
	actor_username = _audit_actor_username(row.get("actor"))
	expected_actor = str(expected.get("actor_user_code") or "").strip()
	return (
		(str(row.get("event_code") or "").strip() == expected.get("event_code"))
		and (str(row.get("event_type") or "").strip() == expected.get("event_type"))
		and (str(row.get("object_type") or "").strip() == expected.get("object_type"))
		and (str(row.get("object_code") or "").strip() == expected.get("object_code"))
		and (actor_username == expected_actor)
		and (occurred_at == expected_at)
		and (_nullable_state(row.get("from_state")) == _nullable_state(expected.get("from_state")))
		and (_nullable_state(row.get("to_state")) == _nullable_state(expected.get("to_state")))
		and (str(row.get("evidence_ref") or "").strip() == expected.get("evidence_ref"))
		and (str(row.get("journey_code") or "").strip() == JOURNEY_CODE)
		and bool(cint(row.get("is_master_seed")))
	)


def _audit_events_seed_strict_ok(idx: int) -> bool:
	expected_rows = master_planning_audit_events_for_checkpoint(CHECKPOINT_ORDER[idx])
	if not expected_rows:
		return True
	allowed_codes = {row["event_code"] for row in expected_rows}
	rows = frappe.get_all(
		"Planning Audit Event",
		filters={"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		fields=[
			"name",
			"event_code",
			"event_type",
			"object_type",
			"object_code",
			"actor",
			"occurred_at",
			"from_state",
			"to_state",
			"evidence_ref",
			"journey_code",
			"is_master_seed",
		],
		order_by="occurred_at asc, event_code asc",
	)
	master_rows = [row for row in rows if (row.get("event_code") or "").strip() in allowed_codes]
	if len(master_rows) != len(expected_rows):
		return False
	times = [_parse_dt(row.get("occurred_at")) for row in master_rows]
	if any(t is None for t in times):
		return False
	if not all(times[i] <= times[i + 1] for i in range(len(times) - 1)):
		return False
	for actual, expected in zip(master_rows, expected_rows, strict=True):
		if not _audit_event_row_strict_ok(actual, expected):
			return False
	return True


def _audit_events_ordered(idx: int) -> bool:
	return _audit_events_seed_strict_ok(idx)


def _supplier_access_denied() -> bool:
	"""Structural DocPerm deny for supplier role (roles matrix §4.11)."""
	for doctype in _SUPPLIER_DENIED_DOCTYPES:
		if _role_has_read(doctype, _SUPPLIER_ROLE):
			return False
	return True


def _plan_seed_strict_ok() -> bool:
	row = frappe.db.get_value(
		"Procurement Plan",
		PLAN_CODE,
		[
			"plan_name",
			"plan_description",
			"fiscal_year",
			"planning_cycle_code",
			"procuring_entity",
			"status",
			"is_master_seed",
			"created_by",
			"approved_by",
			"created_at",
			"approved_at",
		],
		as_dict=True,
	)
	if not row:
		return False
	entity = str(frappe.db.get_value("Procuring Entity", row.get("procuring_entity"), "entity_code") or "").strip()
	created_username = str(frappe.db.get_value("User", row.get("created_by"), "username") or "").strip()
	approved_username = str(frappe.db.get_value("User", row.get("approved_by"), "username") or "").strip()
	created_at = str(row.get("created_at") or "").split(".")[0]
	approved_at = str(row.get("approved_at") or "").split(".")[0]
	allowed_statuses = {"Active", "Approved"}
	return (
		(str(row.get("plan_name") or "").strip() == PLAN_NAME)
		and (str(row.get("plan_description") or "").strip() == PLAN_DESCRIPTION)
		and (str(row.get("fiscal_year") or "").strip() in {"2026", "2026/2027"})
		and (str(row.get("planning_cycle_code") or "").strip() == PLAN_PLANNING_CYCLE_CODE)
		and (entity in {PE_CODE, "MOH"})
		and (str(row.get("status") or "").strip() in allowed_statuses)
		and bool(cint(row.get("is_master_seed")))
		and (created_username == PLAN_CREATOR_USER_CODE)
		and (approved_username == PLAN_APPROVER_USER_CODE)
		and (created_at == PLAN_CREATED_AT)
		and (approved_at == PLAN_APPROVED_AT)
	)


def _append_checkpoint_checks(checks: list[dict[str, Any]], idx: int) -> None:
	if idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		plan_ok = _plan_seed_strict_ok()
		checks.append(
			_chk(
				"PP2-SEED-VAL-001",
				plan_ok,
				f"Procurement Plan {PLAN_CODE} matches strict seed fields.",
				f"Procurement Plan {PLAN_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at INCLUDED_IN_PLAN or higher to repair PLAN-MOH-2026.",
			)
		)
		incl_ok = _inclusion_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-002",
				incl_ok,
				f"Planning inclusion {INCLUSION_CODE} matches strict seed fields.",
				f"Planning inclusion {INCLUSION_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at INCLUDED_IN_PLAN or higher to repair PLANINCL-MOH-2026-001.",
			)
		)
		demand_ok = _inclusion_refs_ok()
		checks.append(
			_chk(
				"PP2-SEED-VAL-003",
				demand_ok,
				f"Inclusion {INCLUSION_CODE} references demand {DEMAND_CODE}, budget line, and demand item.",
				f"Inclusion {INCLUSION_CODE} missing demand, budget line, or demand item references.",
				required_action="Reload planning inclusion handoff locked_summary and technical refs.",
			)
		)

	if idx >= _checkpoint_index("PACKAGE_DRAFT"):
		pkg_ok = _package_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-004",
				pkg_ok,
				f"Procurement Package {PKG_CODE} matches strict seed fields.",
				f"Procurement Package {PKG_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at PACKAGE_DRAFT or higher to repair PKG-MOH-2026-001.",
			)
		)
		refs_ok = _package_refs_ok()
		checks.append(
			_chk(
				"PP2-SEED-VAL-005",
				refs_ok,
				f"Package {PKG_CODE} references plan, inclusion, demand, and budget line.",
				f"Package {PKG_CODE} missing plan/inclusion/demand/budget references.",
				required_action="Repair package traceability fields on PKG-MOH-2026-001.",
			)
		)
		line_ok = _package_line_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-006",
				line_ok,
				f"Package line {PKG_LINE_CODE} matches strict seed fields.",
				f"Package line {PKG_LINE_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at PACKAGE_DRAFT or higher to repair PKGLINE-MOH-2026-001-001.",
			)
		)
		totals_ok = _package_totals_match()
		checks.append(
			_chk(
				"PP2-SEED-VAL-007",
				totals_ok,
				f"Package {PKG_CODE} total equals active line total.",
				f"Package {PKG_CODE} total does not equal active line total.",
				required_action="Reconcile package estimated_value with line amounts.",
			)
		)
		method_ok = _method_decision_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-008",
				method_ok,
				f"Method decision {METHDEC_CODE} matches strict seed fields.",
				f"Method decision {METHDEC_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at PACKAGE_DRAFT or higher to repair METHDEC-PKG-MOH-2026-001.",
			)
		)

	if idx >= _checkpoint_index("READY_FOR_RELEASE"):
		readiness_ok = _readiness_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-009",
				readiness_ok,
				f"Readiness result {PKGRDY_CODE} matches strict seed fields.",
				f"Readiness result {PKGRDY_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at READY_FOR_RELEASE or higher to repair PKGRDY-PKG-MOH-2026-001-001.",
			)
		)
		review_ok = _review_decision_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-016",
				review_ok,
				f"Review decision {PKGREV_CODE} matches strict seed fields.",
				f"Review decision {PKGREV_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at READY_FOR_RELEASE or higher to repair PKGREV-PKG-MOH-2026-001-001.",
			)
		)
		audit_ok = _audit_events_ordered(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-014",
				audit_ok,
				f"Master-seed Planning Audit Events for {JOURNEY_CODE} match strict spec and order.",
				f"Planning Audit Events for {JOURNEY_CODE} missing, drifted, or out of order.",
				required_action="Repair planning audit timeline (see P3-015).",
			)
		)

	if idx >= _checkpoint_index("RELEASED_TO_TENDER"):
		release_ok = bool(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
		checks.append(
			_chk(
				"PP2-SEED-VAL-010",
				release_ok,
				f"Planning release {PKGREL_CODE} exists.",
				f"Planning release {PKGREL_CODE} not found.",
				required_action="Run seed loader through RELEASED_TO_TENDER.",
			)
		)
		summary_ok = _release_locked_summary_ok()
		checks.append(
			_chk(
				"PP2-SEED-VAL-011",
				summary_ok,
				f"Release {PKGREL_CODE} locked summary matches strict seed fields.",
				f"Release {PKGREL_CODE} locked summary missing or drifted from strict seed fields.",
				required_action="Repair release handoff locked_summary JSON.",
			)
		)
		release_strict_ok = _release_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-017",
				release_strict_ok,
				f"Planning release {PKGREL_CODE} matches strict seed fields.",
				f"Planning release {PKGREL_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at RELEASED_TO_TENDER or higher to repair PKGREL-MOH-2026-001.",
			)
		)
		locked_ok = bool(cint(frappe.db.get_value("Procurement Package", PKG_CODE, "locked_after_release")))
		checks.append(
			_chk(
				"PP2-SEED-VAL-013",
				locked_ok,
				f"Package {PKG_CODE} is locked after release.",
				f"Package {PKG_CODE} is not locked after release.",
				required_action="Release package through PP2 release service.",
			)
		)

	if idx >= _checkpoint_index("CONSUMED_BY_TENDER"):
		consumed_ok = _consumption_links_tender()
		checks.append(
			_chk(
				"PP2-SEED-VAL-012",
				consumed_ok,
				f"Consumption record {PKGCONSUME_CODE} matches strict seed fields.",
				f"Consumption record {PKGCONSUME_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at CONSUMED_BY_TENDER to repair PKGCONSUME-MOH-2026-001.",
			)
		)
		consumption_strict_ok = _consumption_seed_strict_ok()
		checks.append(
			_chk(
				"PP2-SEED-VAL-018",
				consumption_strict_ok,
				f"Consumption record {PKGCONSUME_CODE} matches strict seed fields.",
				f"Consumption record {PKGCONSUME_CODE} missing or drifted from strict seed fields.",
				required_action="Run seed_procurement_planning_works_master at CONSUMED_BY_TENDER to repair PKGCONSUME-MOH-2026-001.",
			)
		)
		audit_strict_ok = _audit_events_seed_strict_ok(idx)
		checks.append(
			_chk(
				"PP2-SEED-VAL-019",
				audit_strict_ok,
				f"Planning audit events for {JOURNEY_CODE} match strict seed timeline at CONSUMED_BY_TENDER.",
				f"Planning audit events for {JOURNEY_CODE} missing or drifted from strict seed timeline.",
				required_action="Run seed_procurement_planning_works_master at CONSUMED_BY_TENDER to repair PPAUD-MOH-2026-* events.",
			)
		)


def run_validate(*, checkpoint: str = DEFAULT_CHECKPOINT) -> dict[str, Any]:
	"""Validate WORKS master planning seed at the requested checkpoint."""
	frappe.set_user("Administrator")
	cp = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	if cp not in CHECKPOINT_ORDER:
		return _unsupported(cp)

	idx = _checkpoint_index(cp)
	checks: list[dict[str, Any]] = []

	upstream = validate_upstream_for_checkpoint(cp)
	if not upstream.get("ok"):
		summary = build_summary(
			checkpoint=cp,
			ok=False,
			failures=[upstream.get("message") or "Upstream validation failed."],
		)
		return {
			**upstream,
			**summary,
			"passed": 0,
			"failed": 0,
			"checks": checks,
		}

	_append_checkpoint_checks(checks, idx)

	supplier_ok = _supplier_access_denied()
	checks.append(
		_chk(
			"PP2-SEED-VAL-015",
			supplier_ok,
			"Supplier role has no read access to internal Planning seed records.",
			"Supplier role can read internal Planning seed records.",
			required_action="Remove supplier DocPerm on Planning internal DocTypes.",
		)
	)

	passed = sum(1 for c in checks if c.get("result") == "PASS")
	failed = sum(1 for c in checks if c.get("result") == "FAIL")
	failures = [c["message"] for c in checks if c.get("result") == "FAIL"]
	summary = build_summary(checkpoint=cp, ok=failed == 0, failures=failures)

	return {
		"ok": failed == 0,
		"checkpoint": cp,
		"passed": passed,
		"failed": failed,
		"checks": checks,
		**summary,
	}
