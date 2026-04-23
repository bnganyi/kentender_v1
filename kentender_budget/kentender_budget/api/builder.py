import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def _assert_budget_editable_for_builder(budget_doc):
	status = (budget_doc.status or "Draft").strip()
	if status in ("Submitted", "Approved"):
		frappe.throw(_("This budget is locked and cannot be edited from Budget Builder."))


def _budget_status_blocks_removal(status: str | None) -> bool:
	"""Approved or Submitted budgets cannot remove or delete lines from the builder."""
	st = (status or "Draft").strip()
	return st in ("Approved", "Submitted")


def _line_reference_counts(budget_line_name: str) -> tuple[int, int, int]:
	"""Returns (demand_ref_count, active_reservation_count, total_reservation_count)."""
	demand_n = 0
	if frappe.db.has_table("Demand"):
		demand_n = frappe.db.count("Demand", {"budget_line": budget_line_name})
	active_res = frappe.db.count(
		"Budget Reservation",
		{"budget_line": budget_line_name, "status": "Active"},
	)
	total_res = frappe.db.count("Budget Reservation", {"budget_line": budget_line_name})
	return demand_n, active_res, total_res


def _line_can_soft_remove(
	budget_status: str | None,
	row: dict,
	demand_n: int,
	active_res: int,
) -> bool:
	if _budget_status_blocks_removal(budget_status):
		return False
	if not int(row.get("is_active") or 0):
		return False
	if flt(row.get("amount_reserved")) > 1e-9:
		return False
	if active_res > 0:
		return False
	if demand_n > 0:
		return False
	return True


def _line_can_hard_delete(
	budget_status: str | None,
	row: dict,
	demand_n: int,
	active_res: int,
	total_res: int,
) -> bool:
	"""Permanent delete: active lines must be fully zero; inactive lines may drop ledger row if no refs/reservations."""
	if _budget_status_blocks_removal(budget_status):
		return False
	if flt(row.get("amount_reserved")) > 1e-9:
		return False
	if flt(row.get("amount_consumed") or 0) > 1e-9:
		return False
	if active_res > 0:
		return False
	if demand_n > 0:
		return False
	if total_res > 0:
		return False
	if int(row.get("is_active") or 0):
		if flt(row.get("amount_allocated")) > 1e-9:
			return False
	return True


def _lines_list_filters(lines_filter: str) -> dict | None:
	"""Return frappe.get_all filters for budget lines by visibility."""
	lf = (lines_filter or "active").strip().lower()
	if lf == "inactive":
		return {"is_active": 0}
	if lf == "all":
		return None
	if lf != "active":
		frappe.throw(_("Invalid lines filter."))
	return {"is_active": 1}


def _get_builder_payload(budget_name: str, lines_filter: str = "active"):
	budget = frappe.db.get_value(
		"Budget",
		budget_name,
		[
			"name",
			"budget_name",
			"currency",
			"total_budget_amount",
			"strategic_plan",
			"status",
			"rejection_reason",
			"rejected_by",
			"rejected_at",
		],
		as_dict=True,
	)
	if not budget:
		frappe.throw(_("Budget not found."))

	line_filters: dict = {"budget": budget.name}
	extra = _lines_list_filters(lines_filter)
	if extra:
		line_filters.update(extra)

	line_rows = frappe.get_all(
		"Budget Line",
		filters=line_filters,
		fields=[
			"name",
			"budget_line_code",
			"budget_line_name",
			"amount_allocated",
			"amount_reserved",
			"amount_consumed",
			"amount_available",
			"is_active",
			"removed_at",
			"removed_by",
			"funding_source",
			"strategic_plan",
			"program",
			"sub_program",
			"output_indicator",
			"performance_target",
			"notes",
		],
		order_by="budget_line_code asc, modified asc",
		limit=5000,
	)
	budget_status = budget.status or "Draft"
	program_names = {r.program for r in line_rows if r.get("program")}
	sub_program_names = {r.sub_program for r in line_rows if r.get("sub_program")}
	out_indicator_names = {r.output_indicator for r in line_rows if r.get("output_indicator")}
	target_names = {r.performance_target for r in line_rows if r.get("performance_target")}
	funding_names = {r.funding_source for r in line_rows if r.get("funding_source")}
	program_labels = {}
	program_codes = {}
	sub_program_labels = {}
	sub_program_codes = {}
	indicator_labels = {}
	indicator_codes = {}
	target_labels = {}
	target_codes = {}
	funding_labels = {}
	if program_names:
		for row in frappe.get_all(
			"Strategy Program",
			filters={"name": ["in", list(program_names)]},
			fields=["name", "program_title", "program_code"],
			limit=5000,
		):
			program_labels[row.name] = row.program_title or row.name
			program_codes[row.name] = (row.program_code or "").strip()
	if sub_program_names:
		sub_program_fields = ["name", "title"]
		if frappe.get_meta("Sub Program").has_field("sub_program_code"):
			sub_program_fields.append("sub_program_code")
		for row in frappe.get_all(
			"Sub Program",
			filters={"name": ["in", list(sub_program_names)]},
			fields=sub_program_fields,
			limit=5000,
		):
			sub_program_labels[row.name] = row.title or row.name
			sub_program_codes[row.name] = (row.get("sub_program_code") or "").strip()
	if out_indicator_names:
		for row in frappe.get_all(
			"Strategy Objective",
			filters={"name": ["in", list(out_indicator_names)]},
			fields=["name", "objective_title", "objective_code"],
			limit=5000,
		):
			indicator_labels[row.name] = row.objective_title or row.name
			indicator_codes[row.name] = (row.objective_code or "").strip()
	if target_names:
		target_fields = ["name", "target_title"]
		if frappe.get_meta("Strategy Target").has_field("target_code"):
			target_fields.append("target_code")
		for row in frappe.get_all(
			"Strategy Target",
			filters={"name": ["in", list(target_names)]},
			fields=target_fields,
			limit=5000,
		):
			target_labels[row.name] = row.target_title or row.name
			target_codes[row.name] = (row.get("target_code") or "").strip()
	if funding_names:
		for row in frappe.get_all(
			"Funding Source",
			filters={"name": ["in", list(funding_names)]},
			fields=["name", "title"],
			limit=5000,
		):
			funding_labels[row.name] = row.title or row.name

	budget_lines = []
	for row in line_rows:
		allocated = flt(row.amount_allocated)
		reserved = flt(row.amount_reserved)
		consumed = flt(row.amount_consumed or 0)
		available = flt(row.amount_available)
		demand_n, active_res, total_res = _line_reference_counts(row.name)
		row_dict = {
			"name": row.name,
			"budget_line_code": row.budget_line_code,
			"budget_line_name": row.budget_line_name,
			"amount_allocated": allocated,
			"amount_reserved": reserved,
			"amount_consumed": consumed,
			"amount_available": available,
			"is_active": int(row.is_active or 0),
			"removed_at": row.get("removed_at"),
			"removed_by": row.get("removed_by"),
			"is_allocated": bool(allocated > 0),
			"allocation_state": "Allocated" if allocated > 0 else "Unallocated",
			"funding_source": row.funding_source,
			"funding_source_label": funding_labels.get(row.funding_source, row.funding_source),
			"strategic_plan": row.strategic_plan,
			"program": row.program,
			"program_label": program_labels.get(row.program, row.program),
			"program_code": program_codes.get(row.program, ""),
			"sub_program": row.sub_program,
			"sub_program_label": sub_program_labels.get(row.sub_program, row.sub_program),
			"sub_program_code": sub_program_codes.get(row.sub_program, ""),
			"output_indicator": row.output_indicator,
			"output_indicator_label": indicator_labels.get(row.output_indicator, row.output_indicator),
			"output_indicator_code": indicator_codes.get(row.output_indicator, ""),
			"performance_target": row.performance_target,
			"performance_target_label": target_labels.get(row.performance_target, row.performance_target),
			"performance_target_code": target_codes.get(row.performance_target, ""),
			"notes": row.notes or "",
		}
		row_dict["can_remove"] = _line_can_soft_remove(budget_status, row_dict, demand_n, active_res)
		row_dict["can_hard_delete"] = _line_can_hard_delete(budget_status, row_dict, demand_n, active_res, total_res)
		budget_lines.append(row_dict)

	# Portfolio totals: active lines only (inactive lines excluded from allocation math)
	all_active = frappe.get_all(
		"Budget Line",
		filters={"budget": budget.name, "is_active": 1},
		fields=[
			"amount_allocated",
			"amount_reserved",
			"amount_consumed",
			"amount_available",
		],
		limit=5000,
	)
	total_budget = flt(budget.total_budget_amount)
	allocated_sum = sum(flt(r.get("amount_allocated")) for r in all_active)
	reserved_sum = sum(flt(r.get("amount_reserved")) for r in all_active)
	available_sum = sum(flt(r.get("amount_available")) for r in all_active)
	line_total_active = len(all_active)
	lines_allocated_active = sum(1 for r in all_active if flt(r.get("amount_allocated")) > 0)
	lines_unallocated_active = max(0, line_total_active - lines_allocated_active)
	remaining_amount = max(0.0, total_budget - allocated_sum)

	return {
		"budget": {
			"name": budget.name,
			"budget_name": budget.budget_name,
			"currency": budget.currency,
			"total_budget_amount": total_budget,
			"strategic_plan": budget.strategic_plan,
			"status": budget.status or "Draft",
			"rejection_reason": budget.get("rejection_reason"),
			"rejected_by": budget.get("rejected_by"),
			"rejected_at": budget.get("rejected_at"),
		},
		"totals": {
			"total_budget_amount": total_budget,
			"allocated_sum": allocated_sum,
			"remaining_amount": remaining_amount,
			"reserved_sum": reserved_sum,
			"available_sum": available_sum,
			"line_total": line_total_active,
			"lines_allocated": lines_allocated_active,
			"lines_unallocated": lines_unallocated_active,
		},
		"lines_filter": (lines_filter or "active").strip().lower(),
		"budget_lines": budget_lines,
	}


@frappe.whitelist()
def get_budget_builder_data(budget_name: str, lines_filter: str | None = "active"):
	"""Return shell data for Budget Builder (B3.1, read-only)."""
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not frappe.has_permission("Budget", "read", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return _get_builder_payload(budget_name, lines_filter=lines_filter or "active")


@frappe.whitelist()
def upsert_budget_line(
	budget_name: str,
	budget_line_name: str,
	amount_allocated: float,
	budget_line_code: str | None = None,
	funding_source: str | None = None,
	program: str | None = None,
	sub_program: str | None = None,
	output_indicator: str | None = None,
	performance_target: str | None = None,
	notes: str | None = None,
	is_active: int | None = 1,
	budget_line_id: str | None = None,
	lines_filter: str | None = "active",
):
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not frappe.has_permission("Budget", "write", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not (budget_line_name or "").strip():
		frappe.throw(_("Budget Line Name is required."))
	if flt(amount_allocated) < 0:
		frappe.throw(_("Allocated amount must be zero or greater."))

	budget_doc = frappe.get_doc("Budget", budget_name)
	_assert_budget_editable_for_builder(budget_doc)
	code_value = (budget_line_code or "").strip()
	line_name = budget_line_id
	if not line_name and code_value:
		line_name = frappe.db.get_value(
			"Budget Line",
			{"budget": budget_name, "budget_line_code": code_value},
			"name",
		)
	line_doc = frappe.get_doc("Budget Line", line_name) if line_name else frappe.new_doc("Budget Line")
	if line_name and not int(line_doc.is_active or 0):
		frappe.throw(_("This budget line was removed and cannot be edited from Budget Builder."))
	line_doc.budget = budget_name
	line_doc.procuring_entity = budget_doc.procuring_entity
	line_doc.fiscal_year = budget_doc.fiscal_year
	line_doc.currency = budget_doc.currency
	line_doc.budget_line_name = budget_line_name.strip()
	if code_value:
		line_doc.budget_line_code = code_value
	line_doc.amount_allocated = flt(amount_allocated)
	line_doc.funding_source = funding_source
	line_doc.program = program
	line_doc.sub_program = sub_program
	line_doc.output_indicator = output_indicator
	line_doc.performance_target = performance_target
	line_doc.notes = notes or ""
	line_doc.is_active = 1 if cint(is_active) else 0
	line_doc.strategic_plan = budget_doc.strategic_plan
	line_doc.save(ignore_permissions=False)
	return _get_builder_payload(budget_name, lines_filter=lines_filter or "active")


@frappe.whitelist()
def remove_budget_line(budget_name: str, budget_line_id: str, lines_filter: str | None = "active"):
	"""Soft-remove (deactivate) a budget line with governance checks."""
	if not budget_name or not budget_line_id:
		frappe.throw(_("Budget and Budget Line are required."))
	if not frappe.has_permission("Budget", "write", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	budget_doc = frappe.get_doc("Budget", budget_name)
	_assert_budget_editable_for_builder(budget_doc)
	if _budget_status_blocks_removal(budget_doc.status):
		frappe.throw(_("Cannot remove budget lines while the budget is submitted or approved."))

	line_doc = frappe.get_doc("Budget Line", budget_line_id)
	if line_doc.budget != budget_name:
		frappe.throw(_("Budget Line does not belong to this budget."))

	# Already removed: idempotent no-op (must run before _line_can_soft_remove, which is false for inactive lines).
	if not int(line_doc.is_active or 0):
		return _get_builder_payload(budget_name, lines_filter=lines_filter or "active")

	row_dict = line_doc.as_dict()
	demand_n, active_res, _total_res = _line_reference_counts(line_doc.name)
	if not _line_can_soft_remove(budget_doc.status, row_dict, demand_n, active_res):
		frappe.throw(
			_(
				"Cannot remove Budget Line. It is in use by active allocations or downstream processes, "
				"or the line is not eligible for removal."
			)
		)

	line_doc.is_active = 0
	line_doc.removed_at = now_datetime()
	line_doc.removed_by = frappe.session.user
	line_doc.save(ignore_permissions=False)
	return _get_builder_payload(budget_name, lines_filter=lines_filter or "active")


@frappe.whitelist()
def delete_budget_line_permanent(budget_name: str, budget_line_id: str, lines_filter: str | None = "active"):
	"""Hard-delete only when zero financial and reference impact."""
	if not budget_name or not budget_line_id:
		frappe.throw(_("Budget and Budget Line are required."))
	if not frappe.has_permission("Budget", "write", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	budget_doc = frappe.get_doc("Budget", budget_name)
	_assert_budget_editable_for_builder(budget_doc)
	if _budget_status_blocks_removal(budget_doc.status):
		frappe.throw(_("Cannot delete budget lines while the budget is submitted or approved."))

	line_doc = frappe.get_doc("Budget Line", budget_line_id)
	if line_doc.budget != budget_name:
		frappe.throw(_("Budget Line does not belong to this budget."))

	row_dict = line_doc.as_dict()
	demand_n, active_res, total_res = _line_reference_counts(line_doc.name)
	if not _line_can_hard_delete(budget_doc.status, row_dict, demand_n, active_res, total_res):
		frappe.throw(
			_(
				"Cannot delete this budget line permanently. "
				"Requires zero allocation, zero reserved and consumed amounts, no reservations, "
				"no downstream references, and no active reservations."
			)
		)

	try:
		frappe.flags.budget_line_force_delete = True
		# Governance enforced above; caller already passed Budget write check.
		frappe.delete_doc("Budget Line", budget_line_id, ignore_permissions=True)
	finally:
		frappe.flags.budget_line_force_delete = False

	return _get_builder_payload(budget_name, lines_filter=lines_filter or "active")
