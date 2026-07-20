# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-00 Tender Configurations Dashboard payload (§19)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, format_datetime, get_datetime

from kentender_procurement.tender_configurations.constants import (
	ELIGIBLE_PACKAGE_STATUSES,
	STD_FAMILY_LABELS,
	STATUS_COMPLETED,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_READY_FOR_REVIEW,
	STATUS_SENT_TO_PUBLICATION,
	STATUS_UNDER_REVIEW,
	TAB_ACTION_LABELS,
	TAB_COMPLETED,
	TAB_IN_PROGRESS,
	TAB_NEEDS_ATTENTION,
	TAB_READY_FOR_PUBLICATION,
	TAB_READY_FOR_REVIEW,
	TAB_READY_TO_CONFIGURE,
	TAB_TO_STATUS,
	UI_01_ROUTE,
)
from kentender_procurement.tender_configurations.services.eligibility import (
	list_eligible_procurement_packages,
	packages_with_active_configuration,
	resolve_applicable_std_document,
	serialize_eligible_package,
)
from kentender_procurement.tender_configurations.services.std_family_map import (
	resolve_family_from_package,
	resolve_procuring_entity_name,
)


def _format_last_updated(dt) -> str:
	if not dt:
		return ""
	try:
		return format_datetime(get_datetime(dt), "yyyy-MM-dd HH:mm") + " EAT"
	except Exception:
		return cstr(dt)


def _issues_label(blockers: int, warnings: int) -> str:
	b = int(blockers or 0)
	w = int(warnings or 0)
	b_word = "Blocker" if b == 1 else "Blockers"
	w_word = "Warning" if w == 1 else "Warnings"
	return f"{b} {b_word} / {w} {w_word}"


def _next_action_for_status(status: str) -> tuple[str, str]:
	status = cstr(status)
	if status == STATUS_IN_PROGRESS:
		tab = TAB_IN_PROGRESS
	elif status == STATUS_NEEDS_ATTENTION:
		tab = TAB_NEEDS_ATTENTION
	elif status in (STATUS_READY_FOR_REVIEW, STATUS_UNDER_REVIEW):
		tab = TAB_READY_FOR_REVIEW
	elif status == STATUS_READY_FOR_PUBLICATION:
		tab = TAB_READY_FOR_PUBLICATION
	elif status in (STATUS_COMPLETED, STATUS_SENT_TO_PUBLICATION):
		tab = TAB_COMPLETED
	else:
		tab = TAB_IN_PROGRESS
	label = TAB_ACTION_LABELS[tab]
	return label, tab


def _match_search(haystacks: list[str], q: str) -> bool:
	if not q:
		return True
	ql = q.lower()
	return any(ql in cstr(h).lower() for h in haystacks if h)


def _filter_issue(blocker: int, warning: int, issue_status: str | None) -> bool:
	issue = cstr(issue_status or "").strip().lower()
	if not issue or issue in ("all", "all issues"):
		return True
	if issue in ("has blockers", "has_blockers"):
		return int(blocker or 0) > 0
	if issue in ("has warnings", "has_warnings"):
		return int(warning or 0) > 0
	if issue in ("no issues", "no_issues"):
		return int(blocker or 0) == 0 and int(warning or 0) == 0
	return True


def _paginate(rows: list, page: int, page_size: int) -> tuple[list, dict[str, Any]]:
	page = max(1, int(page or 1))
	page_size = max(1, min(100, int(page_size or 20)))
	total = len(rows)
	start = (page - 1) * page_size
	end = start + page_size
	return rows[start:end], {
		"page": page,
		"page_size": page_size,
		"total": total,
		"total_pages": max(1, (total + page_size - 1) // page_size),
	}


def _summary_counts() -> dict[str, int]:
	configured = packages_with_active_configuration()
	eligible = frappe.get_all(
		"Procurement Package",
		filters={"status": ("in", list(ELIGIBLE_PACKAGE_STATUSES)), "is_active": 1},
		pluck="name",
	)
	ready = 0
	for name in eligible:
		if name in configured:
			continue
		pkg = frappe.get_doc("Procurement Package", name)
		std = resolve_applicable_std_document(pkg)
		if std.get("ok"):
			ready += 1

	def count_status(*statuses: str) -> int:
		return frappe.db.count("Tender Configuration", {"status": ("in", list(statuses))})

	return {
		"ready_to_configure_count": ready,
		"in_progress_count": count_status(STATUS_IN_PROGRESS),
		"needs_attention_count": count_status(STATUS_NEEDS_ATTENTION),
		"ready_for_review_count": count_status(STATUS_READY_FOR_REVIEW, STATUS_UNDER_REVIEW),
		"ready_for_publication_count": count_status(STATUS_READY_FOR_PUBLICATION),
		"completed_count": count_status(STATUS_COMPLETED, STATUS_SENT_TO_PUBLICATION),
	}


def _filter_options() -> dict[str, list]:
	entities = frappe.get_all(
		"Tender Configuration",
		fields=["procuring_entity_name"],
		distinct=True,
		limit=200,
	)
	entity_names = sorted(
		{cstr(r.procuring_entity_name) for r in entities if r.procuring_entity_name}
	)
	# Also from eligible packages
	pkg_entities = frappe.get_all(
		"Procurement Package",
		filters={"status": ("in", list(ELIGIBLE_PACKAGE_STATUSES))},
		fields=["procuring_entity_code"],
		limit=200,
	)
	for r in pkg_entities:
		label = resolve_procuring_entity_name(r.procuring_entity_code)
		if label and label not in entity_names:
			entity_names.append(label)
	entity_names = sorted(set(entity_names))

	methods = set(
		frappe.get_all(
			"Tender Configuration",
			fields=["procurement_method"],
			pluck="procurement_method",
		)
	)
	methods |= set(
		frappe.get_all(
			"Procurement Package",
			filters={"status": ("in", list(ELIGIBLE_PACKAGE_STATUSES))},
			pluck="procurement_method",
		)
	)
	methods = sorted(cstr(m) for m in methods if m)

	return {
		"std_families": list(STD_FAMILY_LABELS),
		"procuring_entities": entity_names,
		"procurement_methods": methods,
	}


def _package_rows(
	*,
	search: str,
	std_family: str,
	procuring_entity: str,
	procurement_method: str,
) -> list[dict[str, Any]]:
	configured = packages_with_active_configuration()
	packages = frappe.get_all(
		"Procurement Package",
		filters={"status": ("in", list(ELIGIBLE_PACKAGE_STATUSES)), "is_active": 1},
		fields=[
			"name",
			"package_code",
			"package_name",
			"status",
			"procurement_method",
			"procurement_category",
			"required_std_category",
			"required_std_template_version_code",
			"procuring_entity_code",
			"approved_at",
			"modified",
		],
		order_by="approved_at desc, modified desc",
		limit=500,
	)

	rows: list[dict[str, Any]] = []
	for pkg in packages:
		if pkg.name in configured:
			continue
		std = resolve_applicable_std_document(pkg)
		if not std.get("ok"):
			continue
		ser = serialize_eligible_package(pkg, configured)
		if std_family and std_family.lower() not in ("all", "all families"):
			if cstr(ser.get("std_family_label")).lower() != std_family.lower():
				continue
		if procuring_entity and procuring_entity.lower() not in ("all", "all entities"):
			if cstr(ser.get("procuring_entity_name")).lower() != procuring_entity.lower():
				continue
		if procurement_method and procurement_method.lower() not in ("all", "all methods"):
			method_hay = {
				cstr(ser.get("procurement_method_label")).lower(),
				cstr(pkg.procurement_method).lower(),
			}
			if procurement_method.lower() not in method_hay:
				continue
		if not _match_search(
			[
				ser.get("planning_package_ref"),
				ser.get("procurement_title"),
				ser.get("procuring_entity_name"),
			],
			search,
		):
			continue
		rows.append(
			{
				"row_type": "approved_procurement_package",
				"package_id": ser["package_id"],
				"procurement_package_ref": ser["planning_package_ref"],
				"package_title": ser["procurement_title"],
				"std_family": ser["std_family_label"],
				"standard_tender_document_label": ser.get("applicable_std_document_label"),
				"procuring_entity_name": ser["procuring_entity_name"],
				"procurement_method_label": ser["procurement_method_label"],
				"approval_date": ser.get("approval_date"),
				"action_label": TAB_ACTION_LABELS[TAB_READY_TO_CONFIGURE],
				"action_route": "open_create_configuration_modal",
			}
		)
	return rows


def _configuration_rows(
	*,
	tab: str,
	search: str,
	std_family: str,
	procuring_entity: str,
	procurement_method: str,
	issue_status: str,
) -> list[dict[str, Any]]:
	status_filter = TAB_TO_STATUS.get(tab)
	filters: dict[str, Any] = {}
	if isinstance(status_filter, tuple):
		filters["status"] = ("in", list(status_filter))
	elif status_filter:
		filters["status"] = status_filter

	configs = frappe.get_all(
		"Tender Configuration",
		filters=filters,
		fields=[
			"name",
			"configuration_ref",
			"procurement_package_ref",
			"tender_title",
			"std_family_label",
			"std_document_label",
			"procuring_entity_name",
			"procurement_method",
			"status",
			"blocker_count",
			"warning_count",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)

	rows: list[dict[str, Any]] = []
	for c in configs:
		if std_family and std_family.lower() not in ("all", "all families"):
			if cstr(c.std_family_label).lower() != std_family.lower():
				continue
		if procuring_entity and procuring_entity.lower() not in ("all", "all entities"):
			if cstr(c.procuring_entity_name).lower() != procuring_entity.lower():
				continue
		if procurement_method and procurement_method.lower() not in ("all", "all methods"):
			if cstr(c.procurement_method).lower() != procurement_method.lower():
				continue
		if not _filter_issue(c.blocker_count, c.warning_count, issue_status):
			continue
		if not _match_search(
			[
				c.configuration_ref,
				c.procurement_package_ref,
				c.tender_title,
				c.procuring_entity_name,
			],
			search,
		):
			continue
		action_label, _tab = _next_action_for_status(c.status)
		# Under Review still shows Submit-oriented queue but continue opens home
		if c.status == STATUS_UNDER_REVIEW:
			action_label = "View Configuration"
		rows.append(
			{
				"row_type": "tender_configuration",
				"configuration_id": c.name,
				"configuration_ref": c.configuration_ref,
				"procurement_package_ref": c.procurement_package_ref,
				"tender_title": c.tender_title,
				"std_family": c.std_family_label,
				"standard_tender_document_label": c.std_document_label,
				"procuring_entity_name": c.procuring_entity_name,
				"procurement_method_label": c.procurement_method,
				"status_label": c.status,
				"blocker_count": int(c.blocker_count or 0),
				"warning_count": int(c.warning_count or 0),
				"issues_label": _issues_label(c.blocker_count, c.warning_count),
				"last_updated_at": str(c.modified) if c.modified else None,
				"last_updated_label": _format_last_updated(c.modified),
				"next_action_label": action_label,
				"next_action_route": f"/desk/{UI_01_ROUTE}?configuration_id={c.name}",
			}
		)
	return rows


def get_dashboard(
	tab: str | None = None,
	search: str | None = None,
	std_family: str | None = None,
	procuring_entity: str | None = None,
	procurement_method: str | None = None,
	issue_status: str | None = None,
	page: int | str = 1,
	page_size: int | str = 20,
) -> dict[str, Any]:
	tab = cstr(tab or TAB_READY_TO_CONFIGURE).strip() or TAB_READY_TO_CONFIGURE
	search = cstr(search or "").strip()
	std_family = cstr(std_family or "").strip()
	procuring_entity = cstr(procuring_entity or "").strip()
	procurement_method = cstr(procurement_method or "").strip()
	issue_status = cstr(issue_status or "").strip()

	summary = _summary_counts()
	filters = _filter_options()

	ready_rows: list[dict[str, Any]] = []
	config_rows: list[dict[str, Any]] = []
	pagination: dict[str, Any]

	if tab == TAB_READY_TO_CONFIGURE:
		all_rows = _package_rows(
			search=search,
			std_family=std_family,
			procuring_entity=procuring_entity,
			procurement_method=procurement_method,
		)
		page_rows, pagination = _paginate(all_rows, int(page or 1), int(page_size or 20))
		ready_rows = page_rows
	else:
		all_rows = _configuration_rows(
			tab=tab,
			search=search,
			std_family=std_family,
			procuring_entity=procuring_entity,
			procurement_method=procurement_method,
			issue_status=issue_status,
		)
		page_rows, pagination = _paginate(all_rows, int(page or 1), int(page_size or 20))
		config_rows = page_rows

	return {
		"summary": summary,
		"filters": filters,
		"tab": tab,
		"ready_to_configure_packages": ready_rows,
		"configurations": config_rows,
		"pagination": pagination,
	}
