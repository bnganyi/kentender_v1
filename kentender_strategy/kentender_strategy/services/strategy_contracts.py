# Copyright (c) 2026, KenTender and contributors
"""REQ §16 service contracts + write companions."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_permissions import (
	assert_entity_in_scope,
	can_create_successor_plan,
	can_edit_draft_plan,
	entity_for_user,
	has_cross_entity_authority,
	ownership_path_for_unit,
	require_any_role,
	ROLE_MANAGER,
	ROLE_OFFICER,
)
from kentender_strategy.services.strategy_readiness import get_plan_readiness


def _ref(id_: str | None, code: str | None = None, name: str | None = None) -> dict | None:
	if not id_:
		return None
	return {"id": id_, "code": code or id_, "name": name or code or id_}


def _pe_clause(pe: str | None) -> tuple[str, tuple]:
	if pe:
		return "sp.procuring_entity = %s", (pe,)
	return "1=1", ()


def _normalize_period(period: str | None) -> tuple[int | None, int | None]:
	"""Parse '2026–2030' / '2026-2030' into start/end years."""
	if not period:
		return None, None
	raw = str(period).replace("–", "-").replace("—", "-").strip()
	parts = [p.strip() for p in raw.split("-") if p.strip()]
	if len(parts) != 2:
		return None, None
	try:
		return int(parts[0][:4]), int(parts[1][:4])
	except (TypeError, ValueError):
		return None, None


def _plan_attention(plan_id: str, status: str) -> dict[str, Any]:
	"""Per-plan attention label for portfolio table."""
	if status == "Submitted":
		return {
			"attention": "Awaiting review",
			"attention_kind": "review",
			"attention_icon": "visibility",
			"attention_tone": "muted",
		}
	due = frappe.db.count(
		"Performance Measurement",
		{"plan_version": plan_id, "workflow_status": ["in", ["Draft", "Returned"]]},
	)
	attn = frappe.db.sql(
		"""
		select count(*) from `tabPerformance Measurement`
		where plan_version = %s
		  and (
			workflow_status = 'Submitted'
			or (workflow_status = 'Verified' and result_status in ('At risk', 'Off track'))
		  )
		""",
		(plan_id,),
	)[0][0]
	attn = int(attn or 0)
	if attn:
		label = f"{attn} target needs attention" if attn == 1 else f"{attn} targets need attention"
		return {
			"attention": label,
			"attention_kind": "risk",
			"attention_icon": "warning",
			"attention_tone": "error",
			"attention_count": attn,
		}
	if due:
		label = f"{due} measurement due" if due == 1 else f"{due} measurements due"
		return {
			"attention": label,
			"attention_kind": "due",
			"attention_icon": "schedule",
			"attention_tone": "committed",
			"attention_count": due,
		}
	return {
		"attention": "—",
		"attention_kind": "none",
		"attention_icon": None,
		"attention_tone": "muted",
	}


def _entity_label(pe_id: str | None) -> str | None:
	if not pe_id:
		return None
	if frappe.db.exists("DocType", "Procuring Entity"):
		row = frappe.db.get_value(
			"Procuring Entity", pe_id, ["entity_name", "entity_code", "name"], as_dict=True
		)
		if row:
			return row.entity_name or row.entity_code or row.name
	return pe_id


def _entity_code(pe_id: str | None) -> str | None:
	if not pe_id:
		return None
	code = frappe.db.get_value("Procuring Entity", pe_id, "entity_code")
	return code or pe_id


def list_strategy_plans(
	procuring_entity: str | None = None,
	status: str | None = None,
	plan_type: str | None = None,
	search: str | None = None,
	period: str | None = None,
) -> list[dict]:
	filters: dict[str, Any] = {}
	pe = procuring_entity or entity_for_user()
	if pe:
		filters["procuring_entity"] = pe
	if status and status not in ("Status", "All"):
		filters["status"] = status
	if plan_type and plan_type not in ("Plan type", "All"):
		filters["plan_type"] = plan_type
	or_filters = None
	if search:
		or_filters = [
			["plan_code", "like", f"%{search}%"],
			["title", "like", f"%{search}%"],
		]
	rows = frappe.get_all(
		"Strategic Plan",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"plan_code",
			"version_number",
			"title",
			"procuring_entity",
			"plan_type",
			"scope_type",
			"scope_id",
			"parent_plan",
			"status",
			"start_date",
			"end_date",
		],
		order_by="modified desc",
		limit_page_length=200,
	)
	start_year, end_year = _normalize_period(period if period not in ("Period", "All", None) else None)
	out = []
	for r in rows:
		if start_year and end_year and r.start_date and r.end_date:
			rs = frappe.utils.getdate(r.start_date).year
			re = frappe.utils.getdate(r.end_date).year
			# Overlap of plan years with requested period
			if re < start_year or rs > end_year:
				continue
		attn = _plan_attention(r.name, r.status)
		out.append(
			{
				"id": r.name,
				"code": r.plan_code,
				"name": r.title,
				"version_number": r.version_number,
				"procuring_entity": r.procuring_entity,
				"procuring_entity_name": _entity_label(r.procuring_entity),
				"plan_type": r.plan_type,
				"scope_type": r.scope_type,
				"scope_id": r.scope_id,
				"parent_plan": _parent_plan_ref(r.parent_plan),
				"status": r.status,
				"start_date": r.start_date,
				"end_date": r.end_date,
				"effective_period_label": _format_effective_period(r.start_date, r.end_date),
				**attn,
			}
		)
	return out


def _parent_plan_ref(parent_id: str | None) -> dict | None:
	if not parent_id:
		return None
	row = frappe.db.get_value(
		"Strategic Plan", parent_id, ["name", "plan_code", "title"], as_dict=True
	)
	if not row:
		return _ref(parent_id)
	return _ref(row.name, row.plan_code, row.title)


def get_strategy_portfolio(procuring_entity: str | None = None) -> dict:
	pe = procuring_entity or entity_for_user()
	filters = {"procuring_entity": pe} if pe else {}
	plans = frappe.get_all(
		"Strategic Plan",
		filters=filters,
		fields=["name", "plan_code", "title", "status", "end_date"],
	)
	counts = {
		"draft": 0,
		"submitted": 0,
		"active": 0,
		"expiring": 0,
		"measurements_due": 0,
		"measurement_attention": 0,
	}
	today = frappe.utils.getdate()
	for p in plans:
		st = (p.status or "").lower()
		if st in counts:
			counts[st] += 1
		if p.status == "Active" and p.end_date and frappe.utils.getdate(p.end_date) <= frappe.utils.add_months(today, 6):
			counts["expiring"] += 1

	pe_sql, pe_args = _pe_clause(pe)
	due = frappe.db.sql(
		f"""
		select count(distinct m.name) from `tabPerformance Measurement` m
		inner join `tabStrategic Plan` sp on sp.name = m.plan_version
		where {pe_sql}
		  and m.workflow_status in ('Draft', 'Returned')
		""",
		pe_args,
	)[0][0]
	counts["measurements_due"] = int(due or 0)

	# Needs attention: submitted measurements awaiting verify, or verified off-track/at-risk
	attn = frappe.db.sql(
		f"""
		select count(distinct m.name) from `tabPerformance Measurement` m
		inner join `tabStrategic Plan` sp on sp.name = m.plan_version
		where {pe_sql}
		  and (
			m.workflow_status = 'Submitted'
			or (m.workflow_status = 'Verified' and m.result_status in ('At risk', 'Off track'))
		  )
		""",
		pe_args,
	)[0][0]
	counts["measurement_attention"] = int(attn or 0)

	plan_rows = list_strategy_plans(procuring_entity=pe)
	entities = []
	seen_pe = set()
	for row in plan_rows:
		pid = row.get("procuring_entity")
		if pid and pid not in seen_pe:
			seen_pe.add(pid)
			entities.append({"id": pid, "name": row.get("procuring_entity_name") or pid})

	return {
		"counts": counts,
		"plans": plan_rows,
		"my_work": _my_work(pe),
		"entities": entities,
		"capabilities": {"create_plan": can_edit_draft_plan()},
	}


def _my_work_meas_key(row) -> tuple:
	"""Collapse My Work by plan + target (not each measurement period row)."""
	return (
		row.get("plan_code") or "",
		row.get("performance_target") or "",
		row.get("target_code") or "",
	)


def _collapse_my_work_meas(rows: list) -> list[tuple[Any, int]]:
	"""Keep first row per plan/target; return (row, count)."""
	grouped: dict[tuple, dict[str, Any]] = {}
	order: list[tuple] = []
	for row in rows:
		key = _my_work_meas_key(row)
		if key not in grouped:
			grouped[key] = {"row": row, "count": 0}
			order.append(key)
		grouped[key]["count"] += 1
	return [(grouped[k]["row"], grouped[k]["count"]) for k in order]


def _my_work(pe: str | None) -> list[dict]:
	items: list[dict] = []
	filters: dict[str, Any] = {"status": "Submitted"}
	if pe:
		filters["procuring_entity"] = pe
	for p in frappe.get_all(
		"Strategic Plan", filters=filters, fields=["name", "plan_code", "title"], limit=10
	):
		items.append(
			{
				"type": "plan_review",
				"label": f"Review submitted plan ({p.plan_code})",
				"plan": _ref(p.name, p.plan_code, p.title),
				"route": ["strategy-plan-review", p.plan_code],
			}
		)

	pe_sql, pe_args = _pe_clause(pe)
	draft_meas = frappe.db.sql(
		f"""
		select m.name, m.performance_target, sp.plan_code, t.target_code, t.title
		from `tabPerformance Measurement` m
		inner join `tabStrategic Plan` sp on sp.name = m.plan_version
		left join `tabPerformance Target` t on t.name = m.performance_target
		where {pe_sql}
		  and m.workflow_status in ('Draft', 'Returned')
		order by m.measurement_period_end asc
		limit 40
		""",
		pe_args,
		as_dict=True,
	)
	for m, n in _collapse_my_work_meas(draft_meas):
		code = m.target_code or "target"
		plan = m.plan_code or ""
		ref = f"{code} · {plan}" if plan else code
		label = (
			f"Submit measurement ({ref})"
			if n == 1
			else f"Submit measurements ({ref}) · {n}"
		)
		items.append(
			{
				"type": "submit_measurement",
				"label": label,
				"count": n,
				"target": _ref(m.performance_target, m.target_code, m.title),
				"plan_code": m.plan_code,
				"route": [
					"strategy-measurement-submit",
					m.plan_code or "",
					m.target_code or "",
				],
			}
		)

	submitted_meas = frappe.db.sql(
		f"""
		select m.name, m.performance_target, sp.plan_code, t.target_code, t.title
		from `tabPerformance Measurement` m
		inner join `tabStrategic Plan` sp on sp.name = m.plan_version
		left join `tabPerformance Target` t on t.name = m.performance_target
		where {pe_sql}
		  and m.workflow_status = 'Submitted'
		order by m.modified desc
		limit 40
		""",
		pe_args,
		as_dict=True,
	)
	for m, n in _collapse_my_work_meas(submitted_meas):
		code = m.target_code or "target"
		plan = m.plan_code or ""
		ref = f"{code} · {plan}" if plan else code
		label = (
			f"Verify measurement ({ref})"
			if n == 1
			else f"Verify measurements ({ref}) · {n}"
		)
		items.append(
			{
				"type": "verify_measurement",
				"label": label,
				"count": n,
				"target": _ref(m.performance_target, m.target_code, m.title),
				"plan_code": m.plan_code,
				"route": [
					"strategy-measurement-verify",
					m.plan_code or "",
					m.target_code or "",
				],
			}
		)

	risk = frappe.db.sql(
		f"""
		select m.name, m.performance_target, sp.plan_code, t.target_code, t.title, m.result_status
		from `tabPerformance Measurement` m
		inner join `tabStrategic Plan` sp on sp.name = m.plan_version
		left join `tabPerformance Target` t on t.name = m.performance_target
		where {pe_sql}
		  and m.workflow_status = 'Verified'
		  and m.result_status in ('At risk', 'Off track')
		order by m.measurement_period_end desc
		limit 40
		""",
		pe_args,
		as_dict=True,
	)
	for m, n in _collapse_my_work_meas(risk):
		code = m.target_code or "target"
		plan = m.plan_code or ""
		ref = f"{code} · {plan}" if plan else code
		status = (m.result_status or "at risk").lower()
		label = (
			f"Resolve {status} target ({ref})"
			if n == 1
			else f"Resolve {status} target ({ref}) · {n}"
		)
		items.append(
			{
				"type": "resolve_target",
				"label": label,
				"count": n,
				"target": _ref(m.performance_target, m.target_code, m.title),
				"plan_code": m.plan_code,
				"route": ["strategy-plan-measurements", m.plan_code],
			}
		)
	return items[:12]


def get_strategy_tree(plan_version: str | None = None, plan_code: str | None = None) -> dict:
	plan = _resolve_plan(plan_version, plan_code)
	programmes = frappe.get_all(
		"Strategy Programme",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"programme_code",
			"title",
			"description",
			"responsible_function",
			"order_index",
			"owner_org_unit",
		],
		order_by="order_index asc",
	)
	subs = frappe.get_all(
		"Strategy Sub Programme",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"sub_programme_code",
			"title",
			"programme",
			"description",
			"responsible_function",
			"order_index",
			"owner_org_unit",
		],
		order_by="order_index asc",
	)
	objectives = frappe.get_all(
		"Strategic Objective",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"objective_code",
			"title",
			"programme",
			"sub_programme",
			"description",
			"responsible_function",
			"executive_owner",
			"order_index",
			"owner_org_unit",
		],
		order_by="order_index asc",
	)
	outcomes = frappe.get_all(
		"Strategic Outcome",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"outcome_code",
			"title",
			"programme",
			"sub_programme",
			"description",
			"responsible_function",
			"executive_owner",
			"order_index",
			"owner_org_unit",
		],
		order_by="order_index asc",
	)
	indicators = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"indicator_code",
			"title",
			"strategic_objective",
			"strategic_outcome",
			"definition",
			"measurement_type",
			"unit",
			"measurement_frequency",
			"data_source",
			"responsible_function",
			"order_index",
			"owner_org_unit",
		],
		order_by="order_index asc",
	)
	targets = frappe.get_all(
		"Performance Target",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"target_code",
			"title",
			"performance_indicator",
			"comparison_direction",
			"target_numeric",
			"target_text",
			"target_date",
			"baseline_status",
			"baseline_numeric",
			"baseline_text",
			"baseline_as_of",
			"baseline_source",
			"tolerance_value",
			"period_start",
			"period_end",
			"benefit_owner",
			"measurement_verifier",
			"status",
			"owner_org_unit",
		],
		order_by="target_code asc",
	)
	tree = []
	subs_by_p = {}
	for s in subs:
		subs_by_p.setdefault(s.programme, []).append(s)
	objs_by_p = {}
	objs_by_sub = {}
	for obj in objectives:
		if obj.sub_programme:
			objs_by_sub.setdefault(obj.sub_programme, []).append(obj)
		else:
			objs_by_p.setdefault(obj.programme, []).append(obj)
	outs_by_p = {}
	outs_by_sub = {}
	for o in outcomes:
		if o.sub_programme:
			outs_by_sub.setdefault(o.sub_programme, []).append(o)
		else:
			outs_by_p.setdefault(o.programme, []).append(o)
	inds_by_obj = {}
	inds_by_o = {}
	for i in indicators:
		if i.strategic_objective:
			inds_by_obj.setdefault(i.strategic_objective, []).append(i)
		else:
			inds_by_o.setdefault(i.strategic_outcome, []).append(i)
	tgts_by_i = {}
	for t in targets:
		tgts_by_i.setdefault(t.performance_indicator, []).append(t)

	def node(type_, row, code_field, children=None, warnings=None, fields=None):
		base_fields = fields or {
			"description": row.get("description"),
			"responsible_function": row.get("responsible_function"),
			"order_index": row.get("order_index"),
			"programme": row.get("programme"),
			"sub_programme": row.get("sub_programme"),
		}
		ou = row.get("owner_org_unit")
		base_fields.setdefault("owner_org_unit", ou or "")
		base_fields.setdefault("ownership_path", ownership_path_for_unit(ou) if ou else "")
		return {
			"type": type_,
			"id": row.name,
			"code": row.get(code_field),
			"name": row.title,
			"children": children or [],
			"warnings": warnings or [],
			"fields": base_fields,
		}

	for p in programmes:
		p_children = []
		for s in subs_by_p.get(p.name, []):
			s_children = []
			for obj in objs_by_sub.get(s.name, []):
				s_children.append(_objective_node(obj, inds_by_obj, tgts_by_i))
			for o in outs_by_sub.get(s.name, []):
				s_children.append(_outcome_node(o, inds_by_o, tgts_by_i))
			p_children.append(
				node(
					"SubProgramme",
					s,
					"sub_programme_code",
					s_children,
					fields={
						"description": s.description,
						"responsible_function": s.responsible_function,
						"order_index": s.order_index,
						"programme": s.programme,
						"owner_org_unit": s.owner_org_unit or "",
						"ownership_path": ownership_path_for_unit(s.owner_org_unit),
					},
				)
			)
		for obj in objs_by_p.get(p.name, []):
			p_children.append(_objective_node(obj, inds_by_obj, tgts_by_i))
		for o in outs_by_p.get(p.name, []):
			p_children.append(_outcome_node(o, inds_by_o, tgts_by_i))
		tree.append(
			node(
				"Programme",
				p,
				"programme_code",
				p_children,
				fields={
					"description": p.description,
					"responsible_function": p.responsible_function,
					"order_index": p.order_index,
					"owner_org_unit": p.owner_org_unit or "",
					"ownership_path": ownership_path_for_unit(p.owner_org_unit),
				},
			)
		)

	editable = plan.status in ("Draft", "Returned") and can_edit_draft_plan()
	return {
		"plan": {
			"id": plan.name,
			"code": plan.plan_code,
			"name": plan.title,
			"version_number": plan.version_number,
			"status": plan.status,
			"start_date": str(plan.start_date) if plan.start_date else None,
			"end_date": str(plan.end_date) if plan.end_date else None,
			"effective_period_label": _format_effective_period(plan.start_date, plan.end_date),
			"plan_type": plan.plan_type,
			"scope_type": plan.scope_type,
			"scope_id": plan.scope_id,
			"parent_plan": _parent_plan_ref(plan.parent_plan),
			"procuring_entity": plan.procuring_entity,
			"description": plan.description,
			"supersedes_plan_version": plan.supersedes_plan_version,
		},
		"counts": {
			"programmes": len(programmes),
			"sub_programmes": len(subs),
			"objectives": len(objectives),
			"outcomes": len(outcomes),
			"indicators": len(indicators),
			"targets": len(targets),
		},
		"capabilities": {"editable": editable},
		"tree": tree,
	}


def _target_node(t, unit=None):
	return {
		"type": "PerformanceTarget",
		"id": t.name,
		"code": t.target_code,
		"name": t.title,
		"children": [],
		"warnings": [],
		"unit": unit,
		"fields": {
			"performance_indicator": t.performance_indicator,
			"comparison_direction": t.comparison_direction,
			"target_numeric": t.target_numeric,
			"target_text": t.target_text,
			"target_date": str(t.target_date) if t.target_date else None,
			"baseline_status": t.baseline_status,
			"baseline_numeric": t.baseline_numeric,
			"baseline_text": t.baseline_text,
			"baseline_as_of": str(t.baseline_as_of) if t.baseline_as_of else None,
			"baseline_source": t.baseline_source,
			"tolerance_value": t.tolerance_value,
			"period_start": str(t.period_start) if t.period_start else None,
			"period_end": str(t.period_end) if t.period_end else None,
			"benefit_owner": t.benefit_owner,
			"measurement_verifier": t.measurement_verifier,
			"status": t.status,
			"owner_org_unit": getattr(t, "owner_org_unit", None) or "",
			"ownership_path": ownership_path_for_unit(getattr(t, "owner_org_unit", None)),
		},
	}


def _objective_node(obj, inds_by_obj, tgts_by_i):
	warnings = []
	obj_children = []
	inds = inds_by_obj.get(obj.name, [])
	if not inds:
		warnings.append("Indicator required")
	for i in inds:
		i_children = []
		for t in tgts_by_i.get(i.name, []):
			i_children.append(_target_node(t, unit=i.unit))
		warn_ind = []
		if not i_children:
			warn_ind.append("Target required")
		obj_children.append(
			{
				"type": "PerformanceIndicator",
				"id": i.name,
				"code": i.indicator_code,
				"name": i.title,
				"children": i_children,
				"warnings": warn_ind,
				"fields": {
					"strategic_objective": i.strategic_objective,
					"definition": i.definition,
					"measurement_type": i.measurement_type,
					"unit": i.unit,
					"measurement_frequency": i.measurement_frequency,
					"data_source": i.data_source,
					"responsible_function": i.responsible_function,
					"order_index": i.order_index,
					"owner_org_unit": getattr(i, "owner_org_unit", None) or "",
					"ownership_path": ownership_path_for_unit(getattr(i, "owner_org_unit", None)),
				},
			}
		)
	return {
		"type": "StrategicObjective",
		"id": obj.name,
		"code": obj.objective_code,
		"name": obj.title,
		"children": obj_children,
		"warnings": warnings,
		"responsible_function": obj.responsible_function,
		"executive_owner": obj.executive_owner,
		"description": obj.description,
		"fields": {
			"description": obj.description,
			"responsible_function": obj.responsible_function,
			"executive_owner": obj.executive_owner,
			"programme": obj.programme,
			"sub_programme": obj.sub_programme,
			"order_index": obj.order_index,
			"owner_org_unit": getattr(obj, "owner_org_unit", None) or "",
			"ownership_path": ownership_path_for_unit(getattr(obj, "owner_org_unit", None)),
		},
	}


def _outcome_node(o, inds_by_o, tgts_by_i):
	warnings = []
	o_children = []
	inds = inds_by_o.get(o.name, [])
	if not inds:
		warnings.append("Indicator required")
	for i in inds:
		i_children = []
		for t in tgts_by_i.get(i.name, []):
			i_children.append(_target_node(t, unit=i.unit))
		warn_ind = []
		if not i_children:
			warn_ind.append("Target required")
		o_children.append(
			{
				"type": "PerformanceIndicator",
				"id": i.name,
				"code": i.indicator_code,
				"name": i.title,
				"children": i_children,
				"warnings": warn_ind,
				"fields": {
					"strategic_outcome": i.strategic_outcome,
					"definition": i.definition,
					"measurement_type": i.measurement_type,
					"unit": i.unit,
					"measurement_frequency": i.measurement_frequency,
					"data_source": i.data_source,
					"responsible_function": i.responsible_function,
					"order_index": i.order_index,
					"owner_org_unit": getattr(i, "owner_org_unit", None) or "",
					"ownership_path": ownership_path_for_unit(getattr(i, "owner_org_unit", None)),
				},
			}
		)
	return {
		"type": "StrategicOutcome",
		"id": o.name,
		"code": o.outcome_code,
		"name": o.title,
		"children": o_children,
		"warnings": warnings,
		"responsible_function": o.responsible_function,
		"executive_owner": o.executive_owner,
		"description": o.description,
		"fields": {
			"description": o.description,
			"responsible_function": o.responsible_function,
			"executive_owner": o.executive_owner,
			"programme": o.programme,
			"sub_programme": o.sub_programme,
			"order_index": o.order_index,
			"owner_org_unit": getattr(o, "owner_org_unit", None) or "",
			"ownership_path": ownership_path_for_unit(getattr(o, "owner_org_unit", None)),
		},
	}


def _resolve_plan(plan_version: str | None, plan_code: str | None):
	if plan_version and frappe.db.exists("Strategic Plan", plan_version):
		return frappe.get_doc("Strategic Plan", plan_version)
	# Desk routes may pass plan docname (hash) or business plan_code in the same segment.
	if plan_code and frappe.db.exists("Strategic Plan", plan_code):
		return frappe.get_doc("Strategic Plan", plan_code)
	if plan_code:
		name = frappe.db.get_value(
			"Strategic Plan",
			{"plan_code": plan_code, "status": "Active"},
			"name",
		) or frappe.db.get_value(
			"Strategic Plan", {"plan_code": plan_code}, "name", order_by="version_number desc"
		)
		if name:
			return frappe.get_doc("Strategic Plan", name)
	frappe.throw(_("Strategic Plan not found"))


def _open_successor_exists(plan_code: str, procuring_entity: str) -> bool:
	return bool(
		frappe.db.exists(
			"Strategic Plan",
			{
				"plan_code": plan_code,
				"procuring_entity": procuring_entity,
				"status": ["in", ["Draft", "Returned", "Submitted"]],
				"version_number": [">", 1],
			},
		)
	)


def _format_effective_period(start, end) -> str | None:
	"""Compact period for tables/headers (e.g. 01-Jul-2026 - 30-Jun-2030)."""
	if not start or not end:
		return None
	sd = frappe.utils.getdate(start)
	ed = frappe.utils.getdate(end)
	return f"{sd.strftime('%d-%b-%Y')} - {ed.strftime('%d-%b-%Y')}"


def _period_label(start, end) -> str | None:
	if not start and not end:
		return None
	if start and end:
		sd = frappe.utils.getdate(start)
		ed = frappe.utils.getdate(end)
		if sd.year == ed.year and sd.month == ed.month:
			return sd.strftime("%B %Y")
		return f"{sd.strftime('%B %Y')} – {ed.strftime('%B %Y')}"
	d = frappe.utils.getdate(start or end)
	return d.strftime("%B %Y")


def _overview_attention_rows(plan_name: str) -> list[dict]:
	"""Rows needing work: due drafts, submitted for review, verified at-risk/off-track."""
	plan_code = frappe.db.get_value("Strategic Plan", plan_name, "plan_code") or plan_name
	rows = frappe.db.sql(
		"""
		select m.name, m.performance_target, m.measurement_period_start, m.measurement_period_end,
		       m.workflow_status, m.result_status, t.target_code, t.title as target_title
		from `tabPerformance Measurement` m
		left join `tabPerformance Target` t on t.name = m.performance_target
		where m.plan_version = %s
		  and (
			m.workflow_status in ('Draft', 'Returned', 'Submitted')
			or (m.workflow_status = 'Verified' and m.result_status in ('At risk', 'Off track'))
		  )
		order by m.measurement_period_end desc
		limit 20
		""",
		(plan_name,),
		as_dict=True,
	)
	out = []
	for r in rows:
		wf = r.workflow_status or ""
		result = r.result_status or ""
		tgt_code = r.target_code or r.performance_target
		if wf in ("Draft", "Returned"):
			action = "submit-measurement"
			result_label = "Measurement due"
			route = ["strategy-measurement-submit", plan_code, tgt_code]
		elif wf == "Submitted":
			action = "review-measurement"
			result_label = result or "Submitted"
			route = ["strategy-measurement-verify", plan_code, tgt_code]
		else:
			action = "view-measurement"
			result_label = result or "Needs attention"
			route = ["strategy-measurement-verify", plan_code, tgt_code]
		out.append(
			{
				"id": r.name,
				"target": _ref(r.performance_target, r.target_code, r.target_title),
				"period_start": str(r.measurement_period_start) if r.measurement_period_start else None,
				"period_end": str(r.measurement_period_end) if r.measurement_period_end else None,
				"period_label": _period_label(r.measurement_period_start, r.measurement_period_end),
				"result_status": result,
				"result_label": result_label,
				"workflow_status": wf,
				"action": action,
				"action_label": {
					"submit-measurement": "Submit measurement",
					"review-measurement": "Review measurement",
					"view-measurement": "View measurement",
				}.get(action, "View"),
				"route": route,
			}
		)
	return out


def get_plan_overview(plan_version: str | None = None, plan_code: str | None = None) -> dict:
	"""STR-UI-02 aggregate DTO: plan identity, structure counts, commitments, attention."""
	require_any_role(
		ROLE_OFFICER,
		ROLE_MANAGER,
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
		"Auditor",
		"System Manager",
	)
	tree = get_strategy_tree(plan_version=plan_version, plan_code=plan_code)
	plan_id = tree["plan"]["id"]
	plan_doc = frappe.get_doc("Strategic Plan", plan_id)
	assert_entity_in_scope(plan_doc.procuring_entity)

	pe_id = plan_doc.procuring_entity
	pe_ref = _ref(pe_id, _entity_code(pe_id), _entity_label(pe_id))
	commitments_dto = list_strategy_value_commitments(plan_version=plan_id)
	commitments = commitments_dto.get("rows") or []
	required = sum(1 for c in commitments if (c.get("consideration_level") or "").startswith("Required"))
	recommended = sum(
		1 for c in commitments if (c.get("consideration_level") or "").startswith("Recommended")
	)
	attention_rows = _overview_attention_rows(plan_id)
	status = plan_doc.status or ""
	locked = status in ("Approved", "Active", "Superseded", "Archived")
	open_succ = _open_successor_exists(plan_doc.plan_code, pe_id)
	can_succ = (
		can_create_successor_plan()
		and status in ("Active", "Approved")
		and not open_succ
	)
	empty_structure = not (tree.get("counts") or {}).get("programmes")
	return {
		"plan": {
			"id": plan_doc.name,
			"code": plan_doc.plan_code,
			"name": plan_doc.title,
			"version_number": plan_doc.version_number,
			"status": status,
			"start_date": str(plan_doc.start_date) if plan_doc.start_date else None,
			"end_date": str(plan_doc.end_date) if plan_doc.end_date else None,
			"effective_period_label": _format_effective_period(plan_doc.start_date, plan_doc.end_date),
			"plan_type": plan_doc.plan_type,
			"scope_type": plan_doc.scope_type,
			"scope_id": plan_doc.scope_id,
			"parent_plan": _parent_plan_ref(plan_doc.parent_plan),
			"description": plan_doc.description,
			"procuring_entity": pe_ref,
			"supersedes_plan_version": plan_doc.supersedes_plan_version,
		},
		"counts": tree.get("counts") or {},
		"commitments_summary": {
			"total": len(commitments),
			"required": required,
			"recommended": recommended,
		},
		"attention_rows": attention_rows,
		"attention_count": len(attention_rows),
		"lock": {
			"show": locked,
			"message": _(
				"Active plan versions are locked. Create a successor version to make material changes."
			)
			if status == "Active"
			else _("This plan version is locked."),
		},
		"capabilities": {
			"create_successor": can_succ,
			"start_structure": status == "Draft" and empty_structure and can_edit_draft_plan(),
			"export_plan": False,
		},
		"show_policy_note": plan_doc.plan_code == "MOH-SP-2026-2030",
	}


# STR-CHG-001 Phase 1's Strategy Node node_type values -> the compact,
# space-free path-entry "type" tokens this module's callers already expect
# (strategy_consumer.strategy_fields_from_doc's path_by_type lookups predate
# the rebuild and were not changed, so this mapping is what keeps them
# working unmodified).
_NODE_PATH_TYPE = {
	"Pillar": "Pillar",
	"Programme": "Programme",
	"Sub-programme": "SubProgramme",
	"Strategic Objective": "StrategicObjective",
	"Strategic Outcome": "StrategicOutcome",
}


def _node_ancestor_path(node_id: str) -> list[dict]:
	"""Root-first Strategy Node ancestor chain, self included."""
	chain = []
	current = frappe.db.get_value(
		"Strategy Node", node_id, ["name", "node_type", "title", "parent_node_id"], as_dict=True
	)
	while current:
		chain.append(current)
		current = (
			frappe.db.get_value(
				"Strategy Node",
				current.parent_node_id,
				["name", "node_type", "title", "parent_node_id"],
				as_dict=True,
			)
			if current.parent_node_id
			else None
		)
	chain.reverse()
	return chain


def validate_strategy_reference(reference: dict | None = None) -> dict:
	"""XMOD-STR-001 — validates a Performance Target reference for a
	downstream consumer (kentender_budget's Budget Line). Rebuilt for the
	Phase 1 schema: Performance Target no longer carries its own status or
	business code — eligibility is the owning Strategic Plan Version's
	status, and the reference's own generated id is its code."""
	reference = reference or {}
	plan_version_id = reference.get("plan_version_id")
	node_id = reference.get("node_id")
	node_type = reference.get("node_type") or "PerformanceTarget"
	if node_type != "PerformanceTarget":
		return {"valid": False, "reason": f"Unsupported node_type {node_type}"}

	target = frappe.db.get_value("Performance Target", node_id, "indicator_id")
	if not target:
		return {"valid": False, "reason": "Unknown target"}
	indicator_plan_version_id = frappe.db.get_value("Performance Indicator", target, "plan_version_id")
	if not indicator_plan_version_id:
		return {"valid": False, "reason": "Unknown target"}
	if plan_version_id and indicator_plan_version_id != plan_version_id:
		return {"valid": False, "reason": "Target/plan version mismatch"}

	version_status = frappe.db.get_value("Strategic Plan Version", indicator_plan_version_id, "status")
	selectable = version_status == "Active"
	dto = build_strategy_reference(indicator_plan_version_id, node_id)
	return {"valid": True, "selectable_for_new": selectable, "historical_ok": True, "reference": dto}


def build_strategy_reference(plan_version_id: str, target_id: str) -> dict:
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	target = frappe.get_doc("Performance Target", target_id)
	indicator = frappe.get_doc("Performance Indicator", target.indicator_id)

	path = [
		{"type": _NODE_PATH_TYPE[n.node_type], "id": n.name, "code": n.name, "name": n.title}
		for n in _node_ancestor_path(indicator.measures_node_id)
	]
	path.append(
		{
			"type": "PerformanceIndicator",
			"id": indicator.name,
			"code": indicator.name,
			"name": indicator.indicator_name,
		}
	)
	target_label = f"{target.comparison} {target.target_value}"
	path.append({"type": "PerformanceTarget", "id": target.name, "code": target.name, "name": target_label})

	snapshot = " / ".join(
		p["name"] for p in path if p["type"] in ("Programme", "SubProgramme", "PerformanceTarget")
	)
	return {
		"plan_version_id": version.name,
		"plan_code": frappe.db.get_value("Strategic Plan", version.plan_id, "plan_id"),
		"plan_version": version.version_number,
		"node_type": "PerformanceTarget",
		"node_id": target.name,
		"node_code": target.name,
		"node_name": target_label,
		"path": path,
		"snapshot_label": snapshot,
	}


def list_active_targets(procuring_entity: str | None = None, plan_code: str | None = None) -> list[dict]:
	"""XMOD-STR-001 read used by kentender_budget's Budget Line "primary
	target" picker (`budget_live_bind.js::loadTargetOptions`). Rebuilt for
	the Phase 1 schema (STR-908, Phase 9): the pre-rebuild version filtered
	`Strategic Plan.status`/`procuring_entity`/`plan_code` and
	`Performance Target.plan_version`/`target_code`/`title`/`status`, none
	of which exist any more (status moved to `Strategic Plan Version`;
	`Performance Target` has no direct plan-version link, only
	`indicator_id`). Confirmed via Phase 4's already-correct sibling
	functions `validate_strategy_reference`/`build_strategy_reference` in
	this same file, which this now matches."""
	pe = procuring_entity or entity_for_user()
	plan_filters: dict[str, Any] = {}
	if pe:
		plan_filters["procuring_entity_id"] = pe
	if plan_code:
		plan_filters["plan_id"] = plan_code
	plans = frappe.get_all("Strategic Plan", filters=plan_filters, pluck="name")
	if not plans:
		return []
	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": ["in", plans], "status": "Active"},
		pluck="name",
	)
	if not versions:
		return []
	indicators = frappe.get_all(
		"Performance Indicator", filters={"plan_version_id": ["in", versions]}, pluck="name"
	)
	if not indicators:
		return []
	targets = frappe.get_all(
		"Performance Target",
		filters={"indicator_id": ["in", indicators]},
		fields=["name", "indicator_id"],
	)
	out = []
	for t in targets:
		pv_id = frappe.db.get_value("Performance Indicator", t.indicator_id, "plan_version_id")
		out.append(build_strategy_reference(pv_id, t.name))
	return out


def _usage_target_ref(target_id: str | None, snapshot_label: str | None = None) -> dict | None:
	if not target_id:
		return None
	tgt = frappe.db.get_value(
		"Performance Target",
		target_id,
		["name", "target_code", "title"],
		as_dict=True,
	)
	if not tgt:
		# Prefer snapshot label text when target row is gone.
		return _ref(target_id, None, snapshot_label)
	return _ref(tgt.name, tgt.target_code, tgt.title or snapshot_label)


def _usage_row(
	*,
	module: str,
	doctype: str,
	record_id: str,
	code: str | None,
	name: str | None,
	target_id: str | None,
	snapshot_label: str | None,
	reference_type: str,
	status: str | None,
	modified,
) -> dict:
	return {
		"module": module,
		"doctype": doctype,
		"record": _ref(record_id, code, name),
		"target": _usage_target_ref(target_id, snapshot_label),
		"reference_type": reference_type,
		"status": status or "—",
		"modified": str(modified) if modified else None,
		"snapshot_label": snapshot_label,
	}


def _append_budget_line_usage(plan_name: str, groups: dict, rows: list[dict]) -> None:
	"""STR-SUP-001 — dual-read Budget Line primary_* (preferred) or legacy strategy_*."""
	if not frappe.db.exists("DocType", "Budget Line"):
		return

	seen: set[tuple[str, str]] = set()  # (line_name, target_id)

	def _emit(
		*,
		line_name: str,
		code: str | None,
		title: str | None,
		target_id: str | None,
		snapshot_label: str | None,
		reference_type: str,
		status: str | None,
		modified,
	) -> None:
		tid = (target_id or "").strip()
		key = (line_name, tid or "__none__")
		if key in seen:
			return
		seen.add(key)
		row = _usage_row(
			module="Budget",
			doctype="Budget Line",
			record_id=line_name,
			code=code,
			name=title,
			target_id=tid or None,
			snapshot_label=snapshot_label,
			reference_type=reference_type,
			status=status,
			modified=modified,
		)
		groups["Budget"].append(row)
		rows.append(row)

	if frappe.db.has_column("Budget Line", "primary_plan_version_id"):
		for b in frappe.get_all(
			"Budget Line",
			filters={"primary_plan_version_id": plan_name},
			fields=[
				"name",
				"generated_reference",
				"title",
				"is_active",
				"modified",
				"primary_target_id",
				"primary_snapshot_label",
			],
			limit=100,
			order_by="modified desc",
		):
			status = "Active" if b.is_active else "Inactive"
			_emit(
				line_name=b.name,
				code=b.generated_reference,
				title=b.title,
				target_id=b.primary_target_id,
				snapshot_label=b.primary_snapshot_label,
				reference_type="Primary alignment",
				status=status,
				modified=b.modified,
			)

		# Supporting alignments whose plan_version_id matches this plan.
		if frappe.db.exists("DocType", "Budget Line Supporting Target"):
			line_meta: dict[str, Any] = {}
			for st in frappe.get_all(
				"Budget Line Supporting Target",
				filters={"plan_version_id": plan_name},
				fields=[
					"parent",
					"target_id",
					"snapshot_label",
					"target_code",
					"target_name",
				],
				limit=200,
			):
				parent = st.parent
				if parent not in line_meta:
					meta = frappe.db.get_value(
						"Budget Line",
						parent,
						["name", "generated_reference", "title", "is_active", "modified"],
						as_dict=True,
					)
					if not meta:
						continue
					line_meta[parent] = meta
				meta = line_meta[parent]
				_emit(
					line_name=meta.name,
					code=meta.generated_reference,
					title=meta.title,
					target_id=st.target_id,
					snapshot_label=st.snapshot_label
					or f"{st.target_code or ''} — {st.target_name or ''}".strip(" —"),
					reference_type="Supporting alignment",
					status="Active" if meta.is_active else "Inactive",
					modified=meta.modified,
				)
		return

	# Legacy Demand-shaped columns on Budget Line (pre-MVP-1 Budget rebuild).
	if frappe.db.has_column("Budget Line", "strategy_plan_version"):
		for b in frappe.get_all(
			"Budget Line",
			filters={"strategy_plan_version": plan_name},
			fields=[
				"name",
				"generated_reference",
				"title",
				"is_active",
				"modified",
				"strategy_target",
				"strategy_snapshot_label",
			],
			limit=100,
			order_by="modified desc",
		):
			_emit(
				line_name=b.name,
				code=getattr(b, "generated_reference", None) or getattr(b, "budget_line_code", None),
				title=getattr(b, "title", None) or getattr(b, "budget_line_name", None),
				target_id=b.strategy_target,
				snapshot_label=b.strategy_snapshot_label,
				reference_type="Primary alignment",
				status="Active" if getattr(b, "is_active", 1) else "Inactive",
				modified=b.modified,
			)


def _append_planning_package_usage(plan_name: str, groups: dict, rows: list[dict]) -> None:
	"""XMOD-STR-006 — Procurement Package strategy_* primary alignment rows."""
	if not frappe.db.exists("DocType", "Procurement Package"):
		return
	if not frappe.db.has_column("Procurement Package", "strategy_plan_version"):
		return

	for p in frappe.get_all(
		"Procurement Package",
		filters={"strategy_plan_version": plan_name},
		fields=[
			"name",
			"package_code",
			"package_name",
			"status",
			"modified",
			"strategy_target",
			"strategy_snapshot_label",
		],
		limit=100,
		order_by="modified desc",
	):
		row = _usage_row(
			module="Planning",
			doctype="Procurement Package",
			record_id=p.name,
			code=p.package_code,
			name=p.package_name,
			target_id=p.strategy_target,
			snapshot_label=p.strategy_snapshot_label,
			reference_type="Primary alignment",
			status=p.status,
			modified=p.modified,
		)
		groups["Planning"].append(row)
		rows.append(row)


def get_strategy_usage(plan_version: str | None = None, plan_code: str | None = None) -> dict:
	"""STR-UI-12 / STR-AC-017 — derived read-only downstream references."""
	plan = _resolve_plan(plan_version, plan_code)
	groups = {
		"Budget": [],
		"Demand": [],
		"Planning": [],
		"Tender": [],
		"Contract": [],
		"Asset": [],
		"Disposal": [],
	}
	rows: list[dict] = []

	if frappe.db.exists("DocType", "Demand") and frappe.db.has_column("Demand", "strategy_plan_version"):
		for d in frappe.get_all(
			"Demand",
			filters={"strategy_plan_version": plan.name},
			fields=[
				"name",
				"demand_id",
				"title",
				"status",
				"modified",
				"strategy_target",
				"strategy_snapshot_label",
			],
			limit=100,
			order_by="modified desc",
		):
			row = _usage_row(
				module="Demand",
				doctype="Demand",
				record_id=d.name,
				code=d.demand_id,
				name=d.title,
				target_id=d.strategy_target,
				snapshot_label=d.strategy_snapshot_label,
				reference_type="Primary alignment",
				status=d.status,
				modified=d.modified,
			)
			groups["Demand"].append(row)
			rows.append(row)

	_append_budget_line_usage(plan.name, groups, rows)
	_append_planning_package_usage(plan.name, groups, rows)

	# Stable table order: module then modified desc already applied per query.
	counts = {mod: len(groups[mod]) for mod in groups}
	return {
		"plan": {
			"id": plan.name,
			"code": plan.plan_code,
			"name": plan.title,
			"status": plan.status,
			"version_number": plan.version_number,
			"start_date": str(plan.start_date) if plan.start_date else None,
			"end_date": str(plan.end_date) if plan.end_date else None,
			"effective_period_label": _format_effective_period(plan.start_date, plan.end_date),
		},
		"counts": counts,
		"rows": rows,
		"groups": groups,
	}



def list_strategy_value_commitments(plan_version: str | None = None, plan_code: str | None = None) -> dict:
	plan = _resolve_plan(plan_version, plan_code)
	rows = frappe.get_all(
		"Strategy Value Commitment",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"commitment_code",
			"rationale",
			"consideration_level",
			"responsible_owner",
			"status",
		],
		order_by="creation asc",
	)
	out = []
	for r in rows:
		raw_links = frappe.get_all(
			"Strategy Value Commitment Link",
			filters={"parent": r.name},
			fields=["link_type", "linked_outcome", "linked_target"],
		)
		links = []
		for ln in raw_links:
			entry = {
				"link_type": ln.link_type,
				"linked_outcome": ln.linked_outcome,
				"linked_target": ln.linked_target,
				"code": None,
				"name": None,
				"outcome": None,
				"target": None,
			}
			if ln.link_type == "Strategic Outcome" and ln.linked_outcome:
				oc = frappe.db.get_value(
					"Strategic Outcome",
					ln.linked_outcome,
					["outcome_code", "title"],
					as_dict=True,
				)
				if oc:
					entry["outcome"] = _ref(ln.linked_outcome, oc.outcome_code, oc.title)
					entry["code"] = oc.outcome_code
					entry["name"] = oc.title
			elif ln.link_type == "Performance Target" and ln.linked_target:
				tg = frappe.db.get_value(
					"Performance Target",
					ln.linked_target,
					["target_code", "title"],
					as_dict=True,
				)
				if tg:
					entry["target"] = _ref(ln.linked_target, tg.target_code, tg.title)
					entry["code"] = tg.target_code
					entry["name"] = tg.title
			links.append(entry)
		complete = bool(
			(r.rationale or "").strip()
			and (r.responsible_owner or "").strip()
			and links
		)
		out.append(
			{
				"id": r.name,
				"objective": _ref(r.name, r.commitment_code, r.rationale),
				"rationale": r.rationale,
				"consideration_level": r.consideration_level,
				"responsible_owner": r.responsible_owner,
				"status": r.status,
				"links": links,
				"complete": complete,
			}
		)
	complete_n = sum(1 for r in out if r["complete"])
	editable = plan.status in ("Draft", "Returned") and can_edit_draft_plan()
	return {
		"plan": {
			"id": plan.name,
			"code": plan.plan_code,
			"name": plan.title,
			"version_number": plan.version_number,
			"status": plan.status,
			"start_date": str(plan.start_date) if plan.start_date else None,
			"end_date": str(plan.end_date) if plan.end_date else None,
			"effective_period_label": _format_effective_period(plan.start_date, plan.end_date),
			"supersedes_plan_version": plan.supersedes_plan_version,
		},
		"capabilities": {"editable": editable},
		"progress": {"complete": complete_n, "total": len(out)},
		"rows": out,
	}


def list_audit_events(plan_version: str | None = None, plan_code: str | None = None) -> list[dict]:
	plan = _resolve_plan(plan_version, plan_code)
	rows = frappe.get_all(
		"Strategy Audit Event",
		filters={"plan_version": plan.name},
		fields=[
			"name",
			"event_type",
			"entity_type",
			"entity_name",
			"prior_state",
			"new_state",
			"reason",
			"actor",
			"event_at",
			"summary",
		],
		order_by="event_at desc",
		limit_page_length=200,
	)
	return rows


# re-export readiness
__all__ = [
	"list_strategy_plans",
	"get_strategy_portfolio",
	"get_strategy_tree",
	"validate_strategy_reference",
	"list_active_targets",
	"get_strategy_usage",
	"get_plan_readiness",
	"list_strategy_value_commitments",
	"list_audit_events",
	"build_strategy_reference",
]
