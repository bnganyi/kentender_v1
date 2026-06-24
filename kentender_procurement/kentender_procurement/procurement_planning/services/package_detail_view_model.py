# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-002+ — PP3 Package Detail view model (wireframe §14–19)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, fmt_money

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.api.package_detail import _actions_for_workbench
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	PLAN_ACTIVE,
	READINESS_FAILED,
	READINESS_NOT_RUN,
	READINESS_PASSED,
	READINESS_PASSED_WARNINGS,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
)
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)
from kentender_procurement.procurement_planning.services.package_lines import (
	_resolve_package_name,
	format_package_line_rows,
)
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	format_package_readiness_tab,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	format_package_release_tab,
)
from kentender_procurement.procurement_planning.services.package_review_api import (
	format_package_review_tab,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	can_submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	_tender_ref,
	derive_package_next_action,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	_may_run_readiness,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	_may_release,
)
from kentender_procurement.procurement_planning.services.package_review_api import (
	_may_approve,
	_may_return,
)

_PP3_STATUS_LABELS: dict[str, str] = {
	PKG_DRAFT: _("Draft Package"),
	PKG_IN_REVIEW: _("Needs Review"),
	PKG_RETURNED: _("Returned for Correction"),
	PKG_APPROVED: _("Approved"),
	PKG_READY_FOR_RELEASE: _("Ready to Release"),
	PKG_RELEASED: _("Released to Tender"),
	PKG_CONSUMED: _("Tender Created"),
}

_PP3_TAB_IDS: tuple[str, ...] = (
	"overview",
	"lines_funding",
	"readiness",
	"review",
	"release",
)

_PROTECTED_AFTER_RELEASE = (
	_("Scope"),
	_("Method"),
	_("Category"),
	_("Funding"),
	_("Package lines"),
	_("Estimated value"),
)

_SENT_TO_TM = (
	_("Tender title"),
	_("Procurement method"),
	_("Category"),
	_("Funding reference"),
	_("Required tender document path"),
)

_SKIP_BLOCKER_CHECK_IDS = frozenset(("package_released", "tender_created"))


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _status_label(status: str) -> str:
	st = (status or "").strip()
	return _PP3_STATUS_LABELS.get(st, st or _("In progress"))


def _value_label(amount: Any, currency: str | None) -> str:
	curr = (currency or "KES").strip() or "KES"
	return f"{fmt_money(flt(amount), currency=curr)} {curr}".strip()


def _funding_label(budget_line: dict[str, Any] | None) -> str:
	row = budget_line or {}
	if str(row.get("code") or row.get("id") or "").strip():
		return _("Budget linked")
	return _("Budget not linked")


def _blockers_label(blockers: list[str]) -> str:
	if not blockers:
		return _("None")
	if len(blockers) == 1:
		return blockers[0]
	return str(len(blockers))


def _plan_ref(plan_id: str | None) -> dict[str, str]:
	plan_name = (plan_id or "").strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"id": "", "code": "", "name": "", "fiscal_year": ""}
	row = frappe.db.get_value(
		"Procurement Plan",
		plan_name,
		("name", "plan_code", "plan_name", "fiscal_year", "status"),
		as_dict=True,
	) or {}
	fy = row.get("fiscal_year")
	fy_label = f"{fy}/{int(fy) + 1}" if fy else ""
	title = (row.get("plan_name") or row.get("plan_code") or plan_name).strip()
	return {
		"id": row.get("name") or "",
		"code": (row.get("plan_code") or row.get("name") or "").strip(),
		"name": title,
		"fiscal_year": fy_label,
		"status": (row.get("status") or "").strip(),
	}


def _active_plan_label(plan_ref: dict[str, str]) -> str:
	if not plan_ref.get("name"):
		return _("No active plan")
	name = plan_ref.get("name") or ""
	fy = plan_ref.get("fiscal_year") or ""
	if fy and fy not in name:
		return f"{name} FY {fy}"
	return name


def _demand_ref(demand_key: str | None) -> dict[str, str]:
	key = (demand_key or "").strip()
	if not key:
		return {"id": "", "code": "", "name": ""}
	if frappe.db.exists("Demand", key):
		row = frappe.db.get_value("Demand", key, ("name", "demand_id", "title"), as_dict=True) or {}
	else:
		row = frappe.db.get_value(
			"Demand", {"demand_id": key}, ("name", "demand_id", "title"), as_dict=True
		) or {}
	if not row:
		return {"id": "", "code": key, "name": key}
	return {
		"id": row.get("name") or "",
		"code": (row.get("demand_id") or row.get("name") or "").strip(),
		"name": (row.get("title") or row.get("demand_id") or "").strip(),
	}


def _package_purpose(doc, demand_name: str) -> str:
	method = (doc.procurement_method or "").strip() or _("procurement")
	demand = demand_name or (doc.package_name or "").strip()
	return _("Prepare a {0} package for {1}.").format(method, demand)


def _collect_blockers(doc, readiness_tab: dict[str, Any]) -> list[str]:
	blockers = [str(x).strip() for x in get_package_completeness_blockers(doc) if str(x).strip()]
	current = readiness_tab.get("current_result") or {}
	if isinstance(current, dict):
		fail_count = cint(current.get("blocking_failure_count"))
		if fail_count > 0:
			blockers.append(_("Readiness checks have not passed."))
	business = readiness_tab.get("business_readiness") or {}
	status = (getattr(doc, "status", "") or "").strip()
	for check in business.get("checks") or []:
		if not isinstance(check, dict) or check.get("ok") is not False:
			continue
		check_id = str(check.get("id") or "").strip()
		if check_id in _SKIP_BLOCKER_CHECK_IDS and status in (PKG_DRAFT, PKG_IN_REVIEW, PKG_RETURNED, PKG_APPROVED, PKG_READY_FOR_RELEASE):
			continue
		label = str(check.get("label") or "").strip()
		if label:
			blockers.append(label)
	return blockers


def _pp3_readiness_checks(
	doc,
	*,
	plan_ref: dict[str, str],
	readiness_tab: dict[str, Any],
	inclusion_code: str,
) -> list[dict[str, Any]]:
	business = (readiness_tab.get("business_readiness") or {}).get("checks") or []
	by_id = {str(c.get("id") or ""): c for c in business if isinstance(c, dict)}

	def _ok(check_id: str, fallback: bool) -> bool:
		row = by_id.get(check_id) or {}
		if "ok" in row:
			return bool(row.get("ok"))
		return fallback

	plan_active = plan_ref.get("status") == PLAN_ACTIVE
	status = (doc.status or "").strip()
	review_ok = status in (PKG_APPROVED, PKG_READY_FOR_RELEASE, PKG_RELEASED, PKG_CONSUMED)

	spec: list[tuple[str, str, bool]] = [
		("demand_approved", _("Demand approved"), _ok("demand_approved", False)),
		("active_plan", _("Active plan exists"), plan_active),
		("demand_in_plan", _("Demand included in active plan"), bool(inclusion_code)),
		("budget_linked", _("Budget linked"), _ok("budget_linked", False)),
		("package_line", _("Package line complete"), _ok("scope_ready", False)),
		("method_selected", _("Method selected"), _ok("procurement_method_selected", False)),
		("category_selected", _("Category selected"), _ok("procurement_category_selected", False)),
		("std_path", _("Tender document path identified"), _ok("std_category_identified", False)),
		("review_complete", _("Review/approval complete where required"), review_ok),
	]
	return [{"id": cid, "label": label, "ok": ok_flag} for cid, label, ok_flag in spec]


def _readiness_summary_label(readiness_status: str, checks: list[dict[str, Any]]) -> str:
	st = (readiness_status or "").strip()
	if st in (READINESS_PASSED, READINESS_PASSED_WARNINGS):
		return _("Passed")
	if st == READINESS_FAILED:
		return _("Failed")
	if any(not c.get("ok") for c in checks):
		return _("Failed")
	if st == READINESS_NOT_RUN:
		return _("Not run")
	return st or _("Not run")


def _review_status_label(status: str, latest_review: dict[str, Any] | None) -> str:
	st = (status or "").strip()
	if st == PKG_DRAFT or st == PKG_RETURNED:
		return _("Not submitted")
	if st == PKG_IN_REVIEW:
		return _("Needs review")
	if st in (PKG_APPROVED, PKG_READY_FOR_RELEASE, PKG_RELEASED, PKG_CONSUMED):
		return _("Approved")
	decision = (latest_review or {}).get("decision_type") or ""
	if decision:
		return str(decision).strip()
	return _("Not submitted")


def _primary_action(
	status: str,
	role_key: str,
	*,
	actions: dict[str, bool],
	readiness_may_run: dict[str, Any],
	release_may: dict[str, Any],
	submit_guard: dict[str, Any],
	approve_may: dict[str, Any],
	tender_open_route: str,
) -> dict[str, Any]:
	st = (status or "").strip()
	if st in (PKG_RELEASED, PKG_CONSUMED) and tender_open_route:
		return {
			"key": "open_tender",
			"label": _("Open Tender"),
			"visible": True,
		}
	if st == PKG_READY_FOR_RELEASE and release_may.get("allowed") and actions.get("release"):
		return {
			"key": "release_to_tender",
			"label": _("Release to Tender Management"),
			"visible": True,
		}
	if st == PKG_IN_REVIEW and approve_may.get("allowed") and actions.get("approve"):
		return {
			"key": "approve",
			"label": _("Approve"),
			"visible": True,
		}
	if st in (PKG_DRAFT, PKG_RETURNED) and submit_guard.get("allowed") and actions.get("submit"):
		return {
			"key": "submit_for_review",
			"label": _("Submit for Review"),
			"visible": True,
		}
	if readiness_may_run.get("allowed"):
		return {
			"key": "run_readiness",
			"label": _("Run Readiness Checks"),
			"visible": True,
		}
	return {"key": "", "label": "", "visible": False}


def _lines_funding_tab(doc, lines: list[dict[str, Any]], budget_line: dict[str, Any]) -> dict[str, Any]:
	currency = (doc.currency or "KES").strip() or "KES"
	total = flt(doc.estimated_value)
	funding_total = sum(flt(ln.get("amount")) for ln in lines)
	difference = total - funding_total if lines else total
	diff_label = _value_label(abs(difference), currency)
	if not lines:
		diff_label = _("Funding not confirmed")
	elif abs(difference) < 0.01:
		diff_label = _value_label(0, currency)

	rows_out: list[dict[str, Any]] = []
	for ln in lines:
		demand_item = ln.get("demand_item") or {}
		package_line = ln.get("package_line") or {}
		rows_out.append(
			{
				"demand_item_label": (demand_item.get("name") or demand_item.get("code") or "—").strip(),
				"package_line_label": (package_line.get("name") or package_line.get("code") or "—").strip(),
				"value_label": _value_label(ln.get("amount"), currency),
			}
		)

	blockers: list[str] = []
	if not budget_line.get("id") and not budget_line.get("code"):
		blockers.append(_("Budget is not linked."))
	if not lines:
		blockers.append(_("Package line is incomplete."))
	if lines and abs(difference) > 0.01:
		blockers.append(_("Package total exceeds linked funding."))

	return {
		"package_total_label": _value_label(total, currency),
		"funding_label": _funding_label(budget_line),
		"difference_label": diff_label,
		"lines": rows_out,
		"blockers": blockers,
		"has_blockers": bool(blockers),
	}


def _release_tab_pp3(
	doc,
	*,
	status: str,
	readiness_tab: dict[str, Any],
	review_status: str,
	release_raw: dict[str, Any] | None,
	release_may: dict[str, Any],
	approve_ok: bool,
	tender_ref: dict[str, str] | None,
) -> dict[str, Any]:
	st = (status or "").strip()
	readiness_ok = (readiness_tab.get("readiness_status") or "") in (
		READINESS_PASSED,
		READINESS_PASSED_WARNINGS,
	)
	review_ok = review_status == _("Approved")
	blockers: list[str] = []
	if not readiness_ok:
		blockers.append(_("Readiness checks have not passed."))
	if not review_ok and st not in (PKG_RELEASED, PKG_CONSUMED):
		blockers.append(_("Package review is not approved."))
	if not release_may.get("allowed") and st == PKG_READY_FOR_RELEASE:
		msg = str(release_may.get("message") or "").strip()
		if msg and msg not in blockers:
			blockers.append(msg)

	released = st in (PKG_RELEASED, PKG_CONSUMED) or bool(release_raw)
	if released:
		tender = tender_ref or {}
		return {
			"released": True,
			"ready_label": _("Yes"),
			"headline": _("Package released to Tender Management."),
			"subheadline": _("Tender created."),
			"next_action_label": _("Continue in Tender Management."),
			"blockers": [],
			"protected_values": [],
			"sent_values": [],
			"warning": "",
			"may_release": False,
			"tender_open_route": (release_raw or {}).get("tender_open_route") or "",
			"tender_label": tender.get("name") or "",
		}

	ready = readiness_ok and review_ok and release_may.get("allowed")
	return {
		"released": False,
		"ready_label": _("Yes") if ready else _("No"),
		"headline": _("Release to Tender Management"),
		"subheadline": "",
		"next_action_label": "",
		"blockers": blockers,
		"protected_values": list(_PROTECTED_AFTER_RELEASE),
		"sent_values": list(_SENT_TO_TM),
		"warning": _(
			"After release, this package cannot be changed unless returned through "
			"an authorized correction process."
		),
		"may_release": bool(release_may.get("allowed")),
		"tender_open_route": "",
		"tender_label": "",
	}


def get_pp3_package_detail_view_model(package_code: str, actor: str) -> dict[str, Any]:
	"""Return PP3 Package Detail payload for contextual route UI."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site."),
			role_key=role_key,
		)

	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		doc.check_permission("read")
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to view this package."),
			role_key=role_key,
		)

	business_code = (doc.package_code or doc.name or "").strip()
	plan_ref = _plan_ref(doc.plan_id)
	plan_status = plan_ref.get("status") or ""
	budget_line = _budget_line_ref(doc.budget_line_id)
	inclusion_code = (doc.planning_inclusion_code or "").strip()
	inclusion = get_planning_inclusion(inclusion_code) if inclusion_code else None
	demand_key = doc.demand_id or (inclusion or {}).get("demand_code") or ""
	demand_ref = _demand_ref(demand_key)

	readiness_tab = format_package_readiness_tab(doc, business_code)
	review_tab = format_package_review_tab(doc, business_code)
	release_tab_raw = format_package_release_tab(doc, business_code).get("release")
	latest_review = review_tab.get("latest_review")

	lines = format_package_line_rows(doc)
	blockers = _collect_blockers(doc, readiness_tab)
	blockers_label = _blockers_label(blockers)
	status = (doc.status or "").strip()
	actions = _actions_for_workbench(status, role_key, plan_status=plan_status)
	if not budget_line.get("id") and not budget_line.get("code") and lines:
		for ln in lines:
			bl = ln.get("budget_line") or {}
			if str(bl.get("id") or bl.get("code") or "").strip():
				budget_line = bl
				break
	next_action = derive_package_next_action(
		status,
		role_key,
		plan_status=plan_status,
		handoff=release_tab_raw,
	)

	readiness_checks = _pp3_readiness_checks(
		doc,
		plan_ref=plan_ref,
		readiness_tab=readiness_tab,
		inclusion_code=inclusion_code,
	)
	readiness_summary = _readiness_summary_label(
		readiness_tab.get("readiness_status") or "",
		readiness_checks,
	)
	readiness_blockers = [
		f"{idx + 1}. {c['label']}."
		for idx, c in enumerate(readiness_checks)
		if not c.get("ok")
	]

	readiness_may_run = _may_run_readiness(doc, actor, business_code)
	release_may = _may_release(doc)
	submit_guard = can_submit_package_for_review(business_code, actor)
	approve_may = _may_approve(doc, actor, business_code)
	return_may = _may_return(doc, actor)
	tender_ref = _tender_ref(doc.tender_code, handoff=release_tab_raw)
	review_status_label = _review_status_label(status, latest_review)

	category = (doc.procurement_category or doc.contract_type or "").strip()
	if not category and inclusion:
		category = str(inclusion.get("procurement_category") or "").strip()

	header = {
		"title": (doc.package_name or business_code).strip(),
		"category_label": category,
		"method_label": (doc.procurement_method or "").strip(),
		"value_label": _value_label(doc.estimated_value, doc.currency),
		"meta_line": " · ".join(
			s
			for s in (
				category,
				(doc.procurement_method or "").strip(),
				_value_label(doc.estimated_value, doc.currency),
			)
			if s
		),
		"active_plan_label": _active_plan_label(plan_ref),
		"status_label": _status_label(status),
		"funding_label": _funding_label(budget_line),
		"blockers_label": blockers_label,
		"blockers": blockers,
		"next_action_label": next_action.get("label") or _("Complete readiness checks"),
	}

	primary = _primary_action(
		status,
		role_key,
		actions=actions,
		readiness_may_run=readiness_may_run,
		release_may=release_may,
		submit_guard=submit_guard,
		approve_may=approve_may,
		tender_open_route=str((release_tab_raw or {}).get("tender_open_route") or ""),
	)

	overview = {
		"source_demand_label": demand_ref.get("name") or demand_ref.get("code") or "—",
		"package_purpose": _package_purpose(doc, demand_ref.get("name") or ""),
		"status_label": _status_label(status),
		"funding_label": _funding_label(budget_line),
		"blockers_label": blockers_label,
		"blockers": blockers,
		"next_action_label": header["next_action_label"],
	}

	lines_funding = _lines_funding_tab(doc, lines, budget_line)

	readiness = {
		"summary_label": readiness_summary,
		"checks": readiness_checks,
		"blockers": readiness_blockers,
		"failed": readiness_summary == _("Failed"),
		"may_run": bool(readiness_may_run.get("allowed")),
	}

	review = {
		"status_label": review_status_label,
		"reviewer_note": (latest_review or {}).get("decision_reason") or "",
		"next_action_label": header["next_action_label"],
		"may_submit": bool(submit_guard.get("allowed") and actions.get("submit")),
		"may_approve": bool(approve_may.get("allowed") and actions.get("approve")),
		"may_return": bool(return_may.get("allowed") and actions.get("return")),
		"guidance": _(
			"Package is ready to submit when lines, funding, and readiness checks pass."
		),
	}

	release = _release_tab_pp3(
		doc,
		status=status,
		readiness_tab=readiness_tab,
		review_status=review_status_label,
		release_raw=release_tab_raw,
		release_may=release_may,
		approve_ok=review_status_label == _("Approved"),
		tender_ref=tender_ref,
	)

	return {
		"ok": True,
		"role_key": role_key,
		"package_code": business_code,
		"package_name": header["title"],
		"header": header,
		"primary_action": primary,
		"show_view_evidence": True,
		"tab_ids": list(_PP3_TAB_IDS),
		"tabs": {
			"overview": overview,
			"lines_funding": lines_funding,
			"readiness": readiness,
			"review": review,
			"release": release,
		},
		"actions": actions,
	}
