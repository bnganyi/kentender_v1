# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Package Readiness checks (P2-006)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe import _
from frappe.utils import cint, flt, now_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	READINESS_FAILED,
	READINESS_PASSED,
	READINESS_PASSED_WARNINGS,
	READINESS_STALE,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	get_current_package_method_decision,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReadiness,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_APPROVED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))
_REVIEW_APPROVAL_TYPES = frozenset(("Approved", "Release Authorized"))
_VALUE_TOLERANCE = 0.01

PP2_READY_CHECKS: tuple[tuple[str, str, bool], ...] = (
	("PP2-READY-001", "Approved demand exists", True),
	("PP2-READY-002", "Demand approval certificate exists", True),
	("PP2-READY-003", "Budget funding confirmation exists", True),
	("PP2-READY-004", "Demand included in procurement plan", True),
	("PP2-READY-005", "Package line exists", True),
	("PP2-READY-006", "Package line maps to demand item", True),
	("PP2-READY-007", "Package line maps to budget line", True),
	("PP2-READY-008", "Package total matches package lines", True),
	("PP2-READY-009", "Procurement category selected", True),
	("PP2-READY-010", "Procurement method selected", True),
	("PP2-READY-011", "Method justification/derivation recorded", True),
	("PP2-READY-012", "Required STD category identified", True),
	("PP2-READY-013", "Planned schedule dates present", False),
	("PP2-READY-014", "Required review/approval complete", True),
	("PP2-READY-015", "Release handoff can be generated", True),
)


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _guard_check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


def _handoff_code(prefix: str, journey_code: str) -> str:
	return f"{prefix}-{_journey_suffix(journey_code)}"


def _load_package(package_code: str) -> dict[str, Any] | None:
	package_code = (package_code or "").strip()
	if not package_code or not frappe.db.exists("Procurement Package", package_code):
		return None
	return frappe.db.get_value(
		"Procurement Package",
		package_code,
		[
			"name",
			"package_code",
			"package_name",
			"status",
			"plan_id",
			"planning_inclusion_code",
			"demand_id",
			"budget_line_id",
			"journey_code",
			"estimated_value",
			"currency",
			"procurement_category",
			"procurement_method",
			"required_std_category",
			"required_std_type",
			"schedule_start",
			"schedule_end",
			"locked_after_release",
		],
		as_dict=True,
	)


def _load_active_lines(package_code: str) -> list[dict[str, Any]]:
	return frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code, "is_active": 1},
		fields=[
			"name",
			"package_line_code",
			"demand_id",
			"demand_item_code",
			"budget_line_id",
			"amount",
		],
		limit_page_length=500,
		order_by="creation asc",
	)


def _demand_code_from_ref(demand_ref: str) -> str:
	if not demand_ref:
		return ""
	if not demand_consumers_live():
		return demand_ref
	row = frappe.db.get_value("Demand", demand_ref, ("demand_id", "name"), as_dict=True)
	if not row:
		return demand_ref
	return (row.demand_id or row.name or demand_ref).strip()


def _budget_line_code_from_ref(budget_ref: str) -> str:
	if not budget_ref:
		return ""
	# MVP-1: generated_reference; legacy budget_line_code may be absent.
	code = frappe.db.get_value("Budget Line", budget_ref, "generated_reference")
	if not code:
		try:
			code = frappe.db.get_value("Budget Line", budget_ref, "budget_line_code")
		except Exception:
			code = None
	return (code or budget_ref).strip()


def _handoff_exists(handoff_code: str, *, title: str | None = None) -> bool:
	if not handoff_code or not frappe.db.exists("Procurement Handoff Card", handoff_code):
		return False
	if not title:
		return True
	card_title = frappe.db.get_value("Procurement Handoff Card", handoff_code, "handoff_title")
	return (card_title or "").strip() == title


def _method_decision_fingerprint(decision: dict[str, Any] | None) -> tuple[Any, ...]:
	if not decision:
		return ()
	return (
		decision.get("procurement_category"),
		decision.get("procurement_method"),
		decision.get("required_std_category"),
		decision.get("required_std_type"),
		decision.get("method_basis"),
		bool(decision.get("override_flag")),
		decision.get("override_reason"),
	)


def _build_source_snapshot(
	pkg: dict[str, Any],
	lines: list[dict[str, Any]],
	method_decision: dict[str, Any] | None,
) -> dict[str, Any]:
	package_code = (pkg.get("package_code") or pkg.get("name") or "").strip()
	demand_ref = (pkg.get("demand_id") or "").strip()
	if not demand_ref and lines:
		demand_ref = (lines[0].get("demand_id") or "").strip()
	budget_ref = (pkg.get("budget_line_id") or "").strip()
	if not budget_ref and lines:
		budget_ref = (lines[0].get("budget_line_id") or "").strip()
	line_codes = sorted(
		(l.get("package_line_code") or l.get("name") or "").strip()
		for l in lines
		if (l.get("package_line_code") or l.get("name"))
	)
	std_version = ""
	if method_decision:
		std_version = (method_decision.get("required_std_type") or "").strip()
	if not std_version:
		std_version = (pkg.get("required_std_type") or "").strip()
	category = (method_decision or {}).get("procurement_category") or pkg.get("procurement_category") or ""
	method = (method_decision or {}).get("procurement_method") or pkg.get("procurement_method") or ""
	std_category = (
		(method_decision or {}).get("required_std_category")
		or pkg.get("required_std_category")
		or ""
	)
	return {
		"package_code": package_code,
		"demand_code": _demand_code_from_ref(demand_ref),
		"budget_line_code": _budget_line_code_from_ref(budget_ref),
		"estimated_value": flt(pkg.get("estimated_value")),
		"currency": (pkg.get("currency") or "").strip(),
		"procurement_category": (category or "").strip(),
		"procurement_method": (method or "").strip(),
		"package_line_codes": line_codes,
		"required_std_category": (std_category or "").strip(),
		"required_std_template_version_code": std_version,
		"planning_inclusion_code": (pkg.get("planning_inclusion_code") or "").strip(),
		"method_decision_fingerprint": list(_method_decision_fingerprint(method_decision)),
	}


def _snapshot_fingerprint(snapshot: dict[str, Any]) -> str:
	payload = dict(snapshot or {})
	return json.dumps(payload, sort_keys=True, default=str)


def _make_check_item(
	*,
	check_id: str,
	business_label: str,
	blocking: bool,
	ok: bool,
	message: str,
	required_action: str | None,
	source_object_type: str,
	source_object_code: str,
) -> dict[str, Any]:
	if ok:
		result = "PASS"
	elif not blocking:
		result = "WARN"
	else:
		result = "FAIL"
	return {
		"check_id": check_id,
		"business_label": business_label,
		"result": result,
		"blocking": blocking,
		"message": message,
		"required_action": required_action if not ok else None,
		"source_object_type": source_object_type,
		"source_object_code": source_object_code,
	}


def _latest_approved_review(package_code: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Package Review Decision",
		filters={
			"package_code": package_code,
			"decision_type": ("in", list(_REVIEW_APPROVAL_TYPES)),
		},
		fields=["review_decision_code", "decision_type", "decided_at"],
		order_by="decided_at desc",
		limit=1,
	)
	return rows[0] if rows else None


def evaluate_pp2_readiness_checks(package_code: str) -> dict[str, Any]:
	"""Evaluate all PP2-READY checks for a package (pure read)."""
	package_code = (package_code or "").strip()
	pkg = _load_package(package_code)
	if not pkg:
		return {
			"checks": [],
			"blocking_failure_count": 0,
			"warning_count": 0,
			"result_status": READINESS_FAILED,
			"source_snapshot_json": {},
		}

	lines = _load_active_lines(package_code)
	method_decision = get_current_package_method_decision(package_code)
	snapshot = _build_source_snapshot(pkg, lines, method_decision)
	journey_code = (pkg.get("journey_code") or "").strip()

	demand_ref = (pkg.get("demand_id") or "").strip()
	if not demand_ref and lines:
		demand_ref = (lines[0].get("demand_id") or "").strip()
	demand_code = _demand_code_from_ref(demand_ref)
	demand_status = ""
	if demand_ref:
		demand_status = (frappe.db.get_value("Demand", demand_ref, "status") or "").strip()

	inclusion_code = (pkg.get("planning_inclusion_code") or "").strip()
	inclusion = get_planning_inclusion(inclusion_code) if inclusion_code else None

	demapp_code = _handoff_code("DEMAPP", journey_code) if journey_code else ""
	budconf_code = _handoff_code("BUDCONF", journey_code) if journey_code else ""

	line_sum = sum(flt(l.get("amount")) for l in lines)
	package_total = flt(pkg.get("estimated_value"))
	total_matches = bool(lines) and abs(package_total - line_sum) <= _VALUE_TOLERANCE

	category = (
		(method_decision or {}).get("procurement_category")
		or pkg.get("procurement_category")
		or ""
	).strip()
	method = (
		(method_decision or {}).get("procurement_method")
		or pkg.get("procurement_method")
		or ""
	).strip()
	std_category = (
		(method_decision or {}).get("required_std_category")
		or pkg.get("required_std_category")
		or ""
	).strip()
	std_type = (
		(method_decision or {}).get("required_std_type")
		or pkg.get("required_std_type")
		or ""
	).strip()
	method_basis = ((method_decision or {}).get("method_basis") or "").strip()
	override_flag = bool((method_decision or {}).get("override_flag"))
	override_reason = ((method_decision or {}).get("override_reason") or "").strip()
	method_justified = bool(method_basis) and (not override_flag or bool(override_reason))

	review = _latest_approved_review(package_code)
	schedule_ok = bool(pkg.get("schedule_start") and pkg.get("schedule_end"))

	release_ok = bool(
		journey_code
		and lines
		and category
		and method
		and std_category
		and all(l.get("budget_line_id") for l in lines)
	)

	check_results: dict[str, dict[str, Any]] = {}

	def _fail_action(label: str) -> str:
		return _("Resolve {0} and rerun readiness checks.").format(label)

	check_results["PP2-READY-001"] = _make_check_item(
		check_id="PP2-READY-001",
		business_label="Approved demand exists",
		blocking=True,
		ok=bool(demand_ref) and demand_status in _APPROVED_DEMAND_STATUSES,
		message=(
			_("Demand {0} is approved.").format(demand_code)
			if demand_ref and demand_status in _APPROVED_DEMAND_STATUSES
			else _("An approved demand must be linked to this package.")
		),
		required_action=_fail_action(_("demand approval")) if not demand_ref or demand_status not in _APPROVED_DEMAND_STATUSES else None,
		source_object_type="Demand",
		source_object_code=demand_code or demand_ref,
	)

	check_results["PP2-READY-002"] = _make_check_item(
		check_id="PP2-READY-002",
		business_label="Demand approval certificate exists",
		blocking=True,
		ok=_handoff_exists(demapp_code, title="Demand Approval Certificate"),
		message=(
			_("Demand approval certificate exists.")
			if _handoff_exists(demapp_code, title="Demand Approval Certificate")
			else _("Demand approval certificate handoff is missing.")
		),
		required_action=_fail_action(_("demand approval certificate")) if not _handoff_exists(demapp_code, title="Demand Approval Certificate") else None,
		source_object_type="Demand Approval Certificate",
		source_object_code=demapp_code,
	)

	check_results["PP2-READY-003"] = _make_check_item(
		check_id="PP2-READY-003",
		business_label="Budget funding confirmation exists",
		blocking=True,
		ok=_handoff_exists(budconf_code, title="Budget Funding Confirmation"),
		message=(
			_("Budget funding confirmation exists.")
			if _handoff_exists(budconf_code, title="Budget Funding Confirmation")
			else _("Budget funding confirmation handoff is missing.")
		),
		required_action=_fail_action(_("budget funding confirmation")) if not _handoff_exists(budconf_code, title="Budget Funding Confirmation") else None,
		source_object_type="Budget Funding Confirmation",
		source_object_code=budconf_code,
	)

	inclusion_ok = bool(inclusion_code and inclusion)
	check_results["PP2-READY-004"] = _make_check_item(
		check_id="PP2-READY-004",
		business_label="Demand included in procurement plan",
		blocking=True,
		ok=inclusion_ok,
		message=(
			_("Demand included in procurement plan.")
			if inclusion_ok
			else _("Planning inclusion record is missing or invalid.")
		),
		required_action=_fail_action(_("planning inclusion")) if not inclusion_ok else None,
		source_object_type="Planning Inclusion",
		source_object_code=inclusion_code,
	)

	lines_ok = bool(lines)
	first_line = lines[0] if lines else {}
	check_results["PP2-READY-005"] = _make_check_item(
		check_id="PP2-READY-005",
		business_label="Package line exists",
		blocking=True,
		ok=lines_ok,
		message=_("Package line exists.") if lines_ok else _("At least one active package line is required."),
		required_action=_fail_action(_("package lines")) if not lines_ok else None,
		source_object_type="Procurement Package Line",
		source_object_code=(first_line.get("package_line_code") or first_line.get("name") or package_code),
	)

	demand_item_ok = lines_ok and all((l.get("demand_item_code") or "").strip() for l in lines)
	check_results["PP2-READY-006"] = _make_check_item(
		check_id="PP2-READY-006",
		business_label="Package line maps to demand item",
		blocking=True,
		ok=demand_item_ok,
		message=(
			_("Package line maps to demand item.")
			if demand_item_ok
			else _("Every active package line must map to a demand item.")
		),
		required_action=_fail_action(_("demand item links")) if not demand_item_ok else None,
		source_object_type="Demand Item",
		source_object_code=(first_line.get("demand_item_code") or ""),
	)

	budget_link_ok = lines_ok and all(l.get("budget_line_id") for l in lines)
	budget_line_code = _budget_line_code_from_ref(
		(first_line.get("budget_line_id") or pkg.get("budget_line_id") or "")
	)
	check_results["PP2-READY-007"] = _make_check_item(
		check_id="PP2-READY-007",
		business_label="Package line maps to budget line",
		blocking=True,
		ok=budget_link_ok,
		message=(
			_("Package line maps to budget line.")
			if budget_link_ok
			else _("Every active package line must map to a budget line.")
		),
		required_action=_fail_action(_("budget line links")) if not budget_link_ok else None,
		source_object_type="Budget Line",
		source_object_code=budget_line_code,
	)

	check_results["PP2-READY-008"] = _make_check_item(
		check_id="PP2-READY-008",
		business_label="Package total matches package lines",
		blocking=True,
		ok=total_matches,
		message=(
			_("Package total matches package lines.")
			if total_matches
			else _("Package estimated value must equal the sum of active line amounts.")
		),
		required_action=_fail_action(_("package total reconciliation")) if not total_matches else None,
		source_object_type="Procurement Package",
		source_object_code=package_code,
	)

	check_results["PP2-READY-009"] = _make_check_item(
		check_id="PP2-READY-009",
		business_label="Procurement category selected",
		blocking=True,
		ok=bool(category),
		message=(
			_("Procurement category selected.")
			if category
			else _("Procurement category must be recorded.")
		),
		required_action=_fail_action(_("procurement category")) if not category else None,
		source_object_type="Package Method Decision",
		source_object_code=(method_decision or {}).get("method_decision_code") or f"METHDEC-{package_code}",
	)

	check_results["PP2-READY-010"] = _make_check_item(
		check_id="PP2-READY-010",
		business_label="Procurement method selected",
		blocking=True,
		ok=bool(method),
		message=(
			_("Procurement method selected.")
			if method
			else _("Procurement method must be recorded.")
		),
		required_action=_fail_action(_("procurement method")) if not method else None,
		source_object_type="Package Method Decision",
		source_object_code=(method_decision or {}).get("method_decision_code") or f"METHDEC-{package_code}",
	)

	check_results["PP2-READY-011"] = _make_check_item(
		check_id="PP2-READY-011",
		business_label="Method justification/derivation recorded",
		blocking=True,
		ok=method_justified,
		message=(
			_("Method justification/derivation recorded.")
			if method_justified
			else _("Method basis and override justification must be recorded.")
		),
		required_action=_fail_action(_("method justification")) if not method_justified else None,
		source_object_type="Package Method Decision",
		source_object_code=(method_decision or {}).get("method_decision_code") or f"METHDEC-{package_code}",
	)

	std_ok = bool(std_category or std_type)
	check_results["PP2-READY-012"] = _make_check_item(
		check_id="PP2-READY-012",
		business_label="Required STD category identified",
		blocking=True,
		ok=std_ok,
		message=(
			_("Required STD category identified.")
			if std_ok
			else _("Required STD category or type must be identified.")
		),
		required_action=_fail_action(_("STD category")) if not std_ok else None,
		source_object_type="STD Template",
		source_object_code=std_type or std_category,
	)

	check_results["PP2-READY-013"] = _make_check_item(
		check_id="PP2-READY-013",
		business_label="Planned schedule dates present",
		blocking=False,
		ok=schedule_ok,
		message=(
			_("Planned schedule dates present.")
			if schedule_ok
			else _("Schedule start and end dates are recommended for this package.")
		),
		required_action=None if schedule_ok else _("Set schedule start and end dates on the package."),
		source_object_type="Procurement Package",
		source_object_code=package_code,
	)

	review_ok = bool(review)
	check_results["PP2-READY-014"] = _make_check_item(
		check_id="PP2-READY-014",
		business_label="Required review/approval complete",
		blocking=True,
		ok=review_ok,
		message=(
			_("Required review/approval complete.")
			if review_ok
			else _("An approved package review decision is required.")
		),
		required_action=_fail_action(_("package review approval")) if not review_ok else None,
		source_object_type="Package Review Decision",
		source_object_code=(review or {}).get("review_decision_code") or f"PKGREV-{package_code}-001",
	)

	pkgrel_code = _handoff_code("PKGREL", journey_code) if journey_code else ""
	check_results["PP2-READY-015"] = _make_check_item(
		check_id="PP2-READY-015",
		business_label="Release handoff can be generated",
		blocking=True,
		ok=release_ok,
		message=(
			_("Release handoff can be generated.")
			if release_ok
			else _("Package is not ready to generate a Planning Release Package handoff.")
		),
		required_action=_fail_action(_("release prerequisites")) if not release_ok else None,
		source_object_type="Planning Release Package",
		source_object_code=pkgrel_code or package_code,
	)

	checks = [check_results[cid] for cid, _, _ in PP2_READY_CHECKS]
	blocking_failure_count = sum(
		1 for c in checks if c.get("blocking") and c.get("result") == "FAIL"
	)
	warning_count = sum(1 for c in checks if c.get("result") == "WARN")
	if blocking_failure_count:
		result_status = READINESS_FAILED
	elif warning_count:
		result_status = READINESS_PASSED_WARNINGS
	else:
		result_status = READINESS_PASSED

	return {
		"checks": checks,
		"blocking_failure_count": blocking_failure_count,
		"warning_count": warning_count,
		"result_status": result_status,
		"source_snapshot_json": snapshot,
	}


def _parse_check_items(raw: Any) -> list[dict[str, Any]]:
	checks = raw
	if isinstance(checks, str):
		checks = frappe.parse_json(checks)
	if isinstance(checks, dict):
		inner = checks.get("checks")
		checks = inner if isinstance(inner, list) else []
	if not isinstance(checks, list):
		checks = []
	return checks


def _format_readiness_row(row: dict[str, Any]) -> dict[str, Any]:
	checks = _parse_check_items(row.get("check_items_json"))
	snapshot = row.get("source_snapshot_json")
	if isinstance(snapshot, str):
		snapshot = frappe.parse_json(snapshot)
	if not isinstance(snapshot, dict):
		snapshot = {}
	return {
		"readiness_code": row.get("readiness_code"),
		"package_code": row.get("package_code"),
		"run_by": row.get("run_by"),
		"run_at": row.get("run_at"),
		"result_status": row.get("result_status"),
		"blocking_failure_count": cint(row.get("blocking_failure_count")),
		"warning_count": cint(row.get("warning_count")),
		"stale": bool(cint(row.get("stale"))),
		"stale_reason": row.get("stale_reason"),
		"is_current": bool(cint(row.get("is_current"))),
		"checks": checks,
		"source_snapshot_json": snapshot,
	}


def get_current_package_readiness_result(package_code: str) -> dict[str, Any] | None:
	package_code = (package_code or "").strip()
	if not package_code:
		return None
	row = frappe.db.get_value(
		"Package Readiness Result",
		{"package_code": package_code, "is_current": 1},
		[
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
		],
		as_dict=True,
		order_by="modified desc",
	)
	if not row:
		return None
	return _format_readiness_row(row)


def _checks_fingerprint(checks: list[dict[str, Any]]) -> str:
	slim = [
		{
			"check_id": c.get("check_id"),
			"result": c.get("result"),
		}
		for c in checks
	]
	return json.dumps(slim, sort_keys=True)


def _readiness_code(package_code: str) -> str:
	count = frappe.db.count("Package Readiness Result", {"package_code": package_code})
	return f"PKGRDY-{package_code}-{count + 1:03d}"


def _sync_package_readiness_fields(
	package_code: str, *, readiness_code: str, result_status: str
) -> None:
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{
			"readiness_status": result_status,
			"latest_readiness_code": readiness_code,
		},
		update_modified=True,
	)


def can_run_package_readiness_checks(package_code: str, actor: str) -> dict[str, Any]:
	"""Read-only guard — whether readiness checks may be run for a package."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	package_code = (package_code or "").strip()

	pkg = _load_package(package_code)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageReadiness.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	locked = bool(cint(pkg.get("locked_after_release")))
	checks.append(_guard_check("not_locked", _("Package is not locked after release"), not locked))
	if locked:
		blockers.append(
			_blocker(
				PackageReadiness.LOCKED_AFTER_RELEASE,
				_("Package is locked after release; readiness cannot be rerun."),
			)
		)

	return {"allowed": not blockers, "blockers": blockers, "checks": checks}


def _assert_can_run_or_throw(package_code: str, actor: str) -> None:
	guard = can_run_package_readiness_checks(package_code, actor)
	if guard.get("allowed"):
		return
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Readiness checks cannot be run for this package."),
		title=first.get("code") or PackageReadiness.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def reconcile_package_readiness_staleness(package_code: str) -> dict[str, Any]:
	"""Mark current readiness stale when live source snapshot diverges."""
	package_code = (package_code or "").strip()
	current = get_current_package_readiness_result(package_code)
	if not current or current.get("stale"):
		return {"stale": bool(current and current.get("stale")), "action": "none", "readiness_code": None}

	pkg = _load_package(package_code)
	if not pkg:
		return {"stale": False, "action": "none", "readiness_code": None}

	lines = _load_active_lines(package_code)
	method_decision = get_current_package_method_decision(package_code)
	live_snapshot = _build_source_snapshot(pkg, lines, method_decision)
	stored_snapshot = current.get("source_snapshot_json") or {}

	if _snapshot_fingerprint(stored_snapshot) == _snapshot_fingerprint(live_snapshot):
		return {
			"stale": False,
			"action": "none",
			"readiness_code": current.get("readiness_code"),
		}

	stale_reason = _("Readiness is stale because package data changed. Rerun readiness checks.")
	readiness_code = current.get("readiness_code")
	frappe.db.set_value(
		"Package Readiness Result",
		readiness_code,
		{
			"stale": 1,
			"stale_reason": stale_reason,
			"result_status": READINESS_STALE,
		},
		update_modified=True,
	)
	_sync_package_readiness_fields(
		package_code,
		readiness_code=readiness_code,
		result_status=READINESS_STALE,
	)
	return {"stale": True, "action": "marked_stale", "readiness_code": readiness_code}


def _find_matching_current_result(
	package_code: str, evaluation: dict[str, Any]
) -> dict[str, Any] | None:
	current = get_current_package_readiness_result(package_code)
	if not current or current.get("stale"):
		return None
	live_fp = _snapshot_fingerprint(evaluation.get("source_snapshot_json") or {})
	stored_fp = _snapshot_fingerprint(current.get("source_snapshot_json") or {})
	if live_fp != stored_fp:
		return None
	if _checks_fingerprint(current.get("checks") or []) != _checks_fingerprint(
		evaluation.get("checks") or []
	):
		return None
	if (current.get("result_status") or "") != (evaluation.get("result_status") or ""):
		return None
	return current


def _clear_current_flags(package_code: str) -> None:
	for code in frappe.get_all(
		"Package Readiness Result",
		filters={"package_code": package_code, "is_current": 1},
		pluck="readiness_code",
	):
		frappe.db.set_value("Package Readiness Result", code, "is_current", 0)


def _persist_readiness_result(
	*,
	package_code: str,
	actor: str,
	evaluation: dict[str, Any],
) -> str:
	_clear_current_flags(package_code)
	readiness_code = _readiness_code(package_code)
	doc = frappe.get_doc(
		{
			"doctype": "Package Readiness Result",
			"readiness_code": readiness_code,
			"package_code": package_code,
			"run_by": actor,
			"run_at": now_datetime(),
			"result_status": evaluation.get("result_status"),
			"blocking_failure_count": evaluation.get("blocking_failure_count") or 0,
			"warning_count": evaluation.get("warning_count") or 0,
			"check_items_json": {"checks": evaluation.get("checks") or []},
			"source_snapshot_json": evaluation.get("source_snapshot_json") or {},
			"stale": 0,
			"stale_reason": None,
			"is_current": 1,
			"is_master_seed": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	_sync_package_readiness_fields(
		package_code,
		readiness_code=readiness_code,
		result_status=evaluation.get("result_status") or READINESS_FAILED,
	)
	return readiness_code


def _format_response(
	*,
	action: str,
	readiness_code: str,
	package_code: str,
	evaluation: dict[str, Any],
) -> dict[str, Any]:
	readiness = get_current_package_readiness_result(package_code)
	return {
		"ok": True,
		"action": action,
		"readiness_code": readiness_code,
		"package_code": package_code,
		"result_status": evaluation.get("result_status"),
		"blocking_failure_count": evaluation.get("blocking_failure_count") or 0,
		"warning_count": evaluation.get("warning_count") or 0,
		"stale": bool(readiness and readiness.get("stale")),
		"checks": evaluation.get("checks") or [],
		"readiness": readiness,
	}


def run_package_readiness_checks(package_code: str, actor: str) -> dict[str, Any]:
	"""Run PP2 readiness checks, persist result, sync package, and audit."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()
	_assert_can_run_or_throw(package_code, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_run_readiness_checks(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)

	evaluation = evaluate_pp2_readiness_checks(package_code)
	matching = _find_matching_current_result(package_code, evaluation)
	if matching:
		return _format_response(
			action="recalled",
			readiness_code=matching.get("readiness_code") or "",
			package_code=package_code,
			evaluation=evaluation,
		)

	reconcile_package_readiness_staleness(package_code)

	readiness_code = _persist_readiness_result(
		package_code=package_code,
		actor=actor_user,
		evaluation=evaluation,
	)
	record_planning_audit_event(
		event_type="Readiness Check Run",
		object_type="Package Readiness Result",
		object_code=readiness_code,
		to_state=evaluation.get("result_status"),
		evidence_ref=readiness_code,
		actor=actor_user,
	)
	return _format_response(
		action="created",
		readiness_code=readiness_code,
		package_code=package_code,
		evaluation=evaluation,
	)
