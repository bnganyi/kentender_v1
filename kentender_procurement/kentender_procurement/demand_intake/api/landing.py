# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA landing workbench — shell + KPI strip (D1/D2 per UI spec §3.3)."""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from kentender_procurement.demand_intake.api.dia_context import resolve_dia_role_key


def _count_demands(filters: dict | None = None) -> int:
	"""Permission-aware count for KPI parity with list visibility."""
	rows = frappe.get_list(
		"Demand",
		filters=filters or {},
		fields=[{"COUNT": "*", "as": "count"}],
		limit_page_length=1,
	)
	return cint((rows[0] or {}).get("count") if rows else 0)


def _sum_demands(filters: dict | None = None) -> float:
	"""Permission-aware sum for KPI parity with list visibility."""
	rows = frappe.get_list(
		"Demand",
		filters=filters or {},
		fields=[{"SUM": "total_amount", "as": "total"}],
		limit_page_length=1,
	)
	return flt((rows[0] or {}).get("total") if rows else 0)


def _count_rejected_or_returned_for_requester(user: str) -> int:
	"""Rejected demands plus Draft rows returned from an approval stage (return_reason set)."""
	return _count_demands({"requested_by": user, "status": "Rejected"}) + _count_demands(
		{"requested_by": user, "status": "Draft", "return_reason": ("!=", "")}
	)


def _count_returned_this_week() -> int:
	"""Draft demands returned from HoD/Finance in the last 7 days (UI spec: HoD KPI)."""
	since = now_datetime() - timedelta(days=7)
	return _count_demands(
		{
			"status": "Draft",
			"return_reason": ("!=", ""),
			"returned_at": (">=", since),
		}
	)


def _count_budget_failures() -> int:
	"""Demands whose budget reservation is in Failed state (DIA v1 signal for finance KPI)."""
	return _count_demands({"reservation_status": "Failed"})


def _kpi(
	*,
	id: str,
	label: str,
	value: float | int,
	format: str | None = None,
	select_queue_id: str | None = None,
	select_work_tab: str | None = None,
	testid: str | None = None,
) -> dict:
	row: dict = {"id": id, "label": label, "value": value}
	if format:
		row["format"] = format
	if select_queue_id:
		row["select_queue_id"] = select_queue_id
	if select_work_tab:
		row["select_work_tab"] = select_work_tab
	if testid:
		row["testid"] = testid
	return row


# H2 — DIA Smoke Test Contract §5 KPI strip (stable `data-testid` on each card slot, index 0–3).
_KPI_SLOT_TESTIDS: tuple[str, str, str, str] = (
	"dia-kpi-my-drafts",
	"dia-kpi-pending-approval",
	"dia-kpi-emergency",
	"dia-kpi-total-value",
)


def _attach_kpi_slot_testids(kpis: list[dict]) -> list[dict]:
	for i, row in enumerate(kpis):
		if i < len(_KPI_SLOT_TESTIDS) and "testid" not in row:
			row["testid"] = _KPI_SLOT_TESTIDS[i]
	return kpis


def _fail_payload(*, error_code: str, message: str, role_key: str = "requisitioner") -> dict:
	"""Non-throwing envelope so the Desk landing page can show inline help instead of a modal."""
	return {
		"ok": False,
		"error_code": error_code,
		"message": str(message),
		"role_key": role_key,
		"currency": "KES",
		"kpis": [],
		"demands": [],
	}


def _kpis_requisitioner(user: str) -> list[dict]:
	return _attach_kpi_slot_testids(
		[
			_kpi(
				id="my_drafts",
				label=_("My Drafts"),
				value=_count_demands({"requested_by": user, "status": "Draft"}),
				select_queue_id="my_drafts",
				select_work_tab="mywork",
			),
			_kpi(
				id="pending_my_action",
				label=_("Pending My Action"),
				value=_count_demands(
					{
						"requested_by": user,
						"status": ["in", ["Pending HoD Approval", "Pending Finance Approval"]],
					}
				),
				select_queue_id="submitted_by_me",
				select_work_tab="mywork",
			),
			_kpi(
				id="rejected_returned",
				label=_("Rejected / Returned"),
				value=_count_rejected_or_returned_for_requester(user),
			),
			_kpi(
				id="total_value_mine",
				label=_("Total Value of My Demands"),
				value=_sum_demands({"requested_by": user}),
				format="currency",
			),
		]
	)


def _kpis_hod() -> list[dict]:
	return _attach_kpi_slot_testids(
		[
			_kpi(
				id="pending_hod",
				label=_("Pending HoD Approval"),
				value=_count_demands({"status": "Pending HoD Approval"}),
				select_queue_id="pending_hod",
				select_work_tab="mywork",
			),
			_kpi(
				id="returned_week",
				label=_("Returned This Week"),
				value=_count_returned_this_week(),
				select_queue_id="returned_await",
				select_work_tab="mywork",
			),
			_kpi(
				id="emergency",
				label=_("Emergency Requests"),
				value=_count_demands({"demand_type": "Emergency", "status": "Pending HoD Approval"}),
				select_queue_id="emergency",
				select_work_tab="mywork",
			),
			_kpi(
				id="total_pending_value",
				label=_("Total Value Pending Approval"),
				value=_sum_demands({"status": "Pending HoD Approval"}),
				format="currency",
				select_queue_id="pending_hod",
				select_work_tab="mywork",
			),
		]
	)


def _kpis_finance() -> list[dict]:
	return _attach_kpi_slot_testids(
		[
			_kpi(
				id="pending_finance",
				label=_("Pending Finance Approval"),
				value=_count_demands({"status": "Pending Finance Approval"}),
				select_queue_id="pending_finance",
				select_work_tab="mywork",
			),
			_kpi(
				id="budget_failures",
				label=_("Budget Failures"),
				value=_count_budget_failures(),
				select_queue_id="budget_exceptions",
				select_work_tab="mywork",
			),
			_kpi(
				id="emergency_fin",
				label=_("Emergency Requests"),
				value=_count_demands({"demand_type": "Emergency", "status": "Pending Finance Approval"}),
				select_queue_id="emergency_fin",
				select_work_tab="mywork",
			),
			_kpi(
				id="total_pending_fin_value",
				label=_("Total Value Pending Approval"),
				value=_sum_demands({"status": "Pending Finance Approval"}),
				format="currency",
				select_queue_id="pending_finance",
				select_work_tab="mywork",
			),
		]
	)


def _kpis_procurement() -> list[dict]:
	return _attach_kpi_slot_testids(
		[
			_kpi(
				id="approved",
				label=_("Approved"),
				value=_count_demands({"status": "Approved"}),
				select_queue_id="approved_not_planned",
				select_work_tab="approved",
			),
			_kpi(
				id="planning_ready",
				label=_("Planning Ready"),
				value=_count_demands({"status": "Planning Ready"}),
				select_queue_id="planning_ready",
				select_work_tab="approved",
			),
			_kpi(
				id="emergency_approved",
				label=_("Emergency Approved"),
				value=_count_demands({"demand_type": "Emergency", "status": ["in", ["Approved", "Planning Ready"]]}),
				select_queue_id="emergency_approved",
				select_work_tab="approved",
			),
			_kpi(
				id="total_ready_value",
				label=_("Total Value Ready for Planning"),
				value=_sum_demands({"status": ["in", ["Approved", "Planning Ready"]]}),
				format="currency",
				select_queue_id="all_approved",
				select_work_tab="approved",
			),
		]
	)


def _kpis_auditor() -> list[dict]:
	return _attach_kpi_slot_testids(
		[
			_kpi(
				id="all_demands",
				label=_("All Demands"),
				value=_count_demands({}),
				select_queue_id="all_demands",
				select_work_tab="all",
			),
			_kpi(
				id="pending_total",
				label=_("Pending Approvals"),
				value=_count_demands({"status": ["in", ["Pending HoD Approval", "Pending Finance Approval"]]}),
				select_queue_id="pending_hod",
				select_work_tab="all",
			),
			_kpi(
				id="rejected_total",
				label=_("Rejected"),
				value=_count_demands({"status": "Rejected"}),
				select_queue_id="dia_rejected",
				select_work_tab="rejected",
			),
			_kpi(
				id="total_value_all",
				label=_("Total Demand Value"),
				value=_sum_demands({}),
				format="currency",
				select_queue_id="all_demands",
				select_work_tab="all",
			),
		]
	)


@frappe.whitelist()
def get_dia_landing_shell_data():
	"""KPI strip + meta for Demand Intake landing (D1 shell, D2 KPI semantics)."""
	if not frappe.db.exists("DocType", "Demand"):
		site = frappe.local.site or "this site"
		return _fail_payload(
			error_code="DEMAND_NOT_INSTALLED",
			message=_(
				"The Demand document type is not installed on site {0}. "
				"Confirm `kentender_procurement` is installed, then run: bench --site {0} migrate"
			).format(site),
		)
	from kentender_procurement.demand_intake.api.dia_access import user_has_dia_workspace_access

	if not user_has_dia_workspace_access():
		return _fail_payload(
			error_code="DIA_ACCESS_DENIED",
			message=_("You are not allowed to access the Demand Intake workspace."),
		)
	if not frappe.has_permission("Demand", "read"):
		return _fail_payload(
			error_code="NO_READ_PERMISSION",
			message=_(
				"You do not have permission to read Demand records. Ask an administrator to grant Demand read access for your role."
			),
		)

	user = frappe.session.user
	role_key = resolve_dia_role_key()

	if role_key == "requisitioner":
		kpis = _kpis_requisitioner(user)
	elif role_key == "hod":
		kpis = _kpis_hod()
	elif role_key == "finance":
		kpis = _kpis_finance()
	elif role_key in ("procurement", "admin"):
		kpis = _kpis_procurement()
	elif role_key == "auditor":
		kpis = _kpis_auditor()
	else:
		kpis = _kpis_requisitioner(user)

	currency = "KES"
	try:
		currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "KES"
	except Exception:
		pass

	return {
		"ok": True,
		"role_key": role_key,
		"currency": currency,
		"kpis": kpis,
		"demands": [],
	}
