# Copyright (c) 2026, KenTender and contributors
"""STR-UI-15 / STR-FR-130+ — Strategy Performance management projection."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)
from kentender_strategy.services.strategy_contracts import (
	_entity_code,
	_entity_label,
	_ref,
	_resolve_plan,
	get_strategy_usage,
	list_plan_value_commitments,
)
from kentender_strategy.services.strategy_permissions import (
	ROLE_AUDITOR,
	ROLE_MANAGER,
	ROLE_OFFICER,
	ROLE_PLANNING,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	assert_entity_in_scope,
	entity_for_user,
	has_cross_entity_authority,
	user_roles,
)
from kentender_strategy.services.strategy_writes import list_corrective_actions

OPEN_CA_STATUSES = frozenset(
	{"Open", "In progress", "Submitted for verification"}
)
EXPORT_ROLES = frozenset(
	{
		ROLE_VIEWER,
		ROLE_MANAGER,
		ROLE_REVIEWER,
		ROLE_PLANNING,
		ROLE_AUDITOR,
		"System Manager",
	}
)
VIEW_ROLES = (
	ROLE_VIEWER,
	ROLE_OFFICER,
	ROLE_MANAGER,
	ROLE_REVIEWER,
	ROLE_PLANNING,
	ROLE_AUDITOR,
	"System Manager",
)


def can_view_strategy_performance() -> bool:
	roles = user_roles()
	if "System Manager" in roles or frappe.session.user == "Administrator":
		return True
	return bool(roles.intersection(set(VIEW_ROLES)))


def can_export_strategy_performance() -> bool:
	roles = user_roles()
	if "System Manager" in roles or frappe.session.user == "Administrator":
		return True
	return bool(roles.intersection(EXPORT_ROLES))


def _require_view() -> None:
	if not can_view_strategy_performance():
		frappe.throw(_("Not permitted to view Strategy Performance"), frappe.PermissionError)


def _money(n) -> float:
	return flt(n or 0)


def _fmt_kes(n: float) -> str:
	abs_n = abs(n)
	if abs_n >= 1_000_000:
		return f"KES {abs_n / 1_000_000:.0f}M" if abs_n % 1_000_000 == 0 else f"KES {abs_n / 1_000_000:.1f}M"
	return f"KES {abs_n:,.0f}"


def _demand_pvc_treatment_counts(plan_name: str) -> tuple[int, dict[str, int]]:
	"""DEM-INT-008 — addressed PVCs from MVP Demand related records.

	Returns ``(aligned_demand_count, treated_counts)`` where counts are keyed by
	Plan Value Commitment id. Alignment comes from Demand Strategy Reference;
	adoption comes from Demand Value Treatment. A deferred or not-applicable
	treatment is addressed only when it carries the reason required by DIA-FR-069.
	"""
	if not plan_name or not demand_doctype_available():
		return 0, {}
	if not frappe.db.exists("DocType", "Demand Strategy Reference"):
		return 0, {}

	references = frappe.get_all(
		"Demand Strategy Reference",
		filters={"plan_version_id": plan_name},
		fields=["demand"],
		limit=200,
	)
	demand_names = sorted({r.demand for r in references if r.demand})
	aligned = len(demand_names)
	if not demand_names or not frappe.db.exists("DocType", "Demand Value Treatment"):
		return aligned, {}

	rows = frappe.get_all(
		"Demand Value Treatment",
		filters={"demand": ["in", demand_names]},
		fields=["demand", "plan_value_commitment", "treatment", "rationale"],
		limit=2000,
	)
	by_key: dict[str, set[str]] = defaultdict(set)
	for r in rows:
		treatment = (r.treatment or "").strip()
		ok = bool(treatment)
		if treatment in {"Not applicable", "To be determined in Planning"}:
			ok = bool((r.rationale or "").strip())
		if not ok:
			continue
		pvc_id = (r.plan_value_commitment or "").strip()
		if pvc_id:
			by_key[pvc_id].add(r.demand)
	return aligned, {k: len(v) for k, v in by_key.items()}


def _planning_package_contribution(plan_name: str) -> tuple[int, float]:
	"""XMOD-STR-007 — aligned Procurement Package count + sum(estimated_value)."""
	if not plan_name or not frappe.db.exists("DocType", "Procurement Package"):
		return 0, 0.0
	if not frappe.db.has_column("Procurement Package", "strategy_plan_version"):
		return 0, 0.0
	fields = ["name"]
	if frappe.db.has_column("Procurement Package", "estimated_value"):
		fields.append("estimated_value")
	rows = frappe.get_all(
		"Procurement Package",
		filters={"strategy_plan_version": plan_name},
		fields=fields,
		limit=200,
	)
	total = 0.0
	for p in rows:
		total += _money(getattr(p, "estimated_value", None))
	return len(rows), total


def _safe_csv_cell(value) -> str:
	s = "" if value is None else str(value)
	if s and s[0] in ("=", "+", "-", "@"):
		return "'" + s
	return s


def _resolve_active_plan(procuring_entity: str | None, plan_code: str | None, plan_version: str | None):
	if plan_version or plan_code:
		plan = _resolve_plan(plan_version, plan_code)
		assert_entity_in_scope(plan.procuring_entity)
		return plan
	pe = procuring_entity or entity_for_user()
	if not pe and not has_cross_entity_authority():
		frappe.throw(_("Procuring entity is required"))
	filters: dict[str, Any] = {"status": "Active", "plan_type": "Entity Strategic Plan"}
	if pe:
		filters["procuring_entity"] = pe
		assert_entity_in_scope(pe)
	name = frappe.db.get_value(
		"Strategic Plan",
		filters,
		"name",
		order_by="start_date desc",
	)
	if not name:
		# Fallback: any Active plan for the entity
		filters.pop("plan_type", None)
		name = frappe.db.get_value("Strategic Plan", filters, "name", order_by="start_date desc")
	if not name:
		frappe.throw(_("No Active strategic plan found for this entity"))
	return frappe.get_doc("Strategic Plan", name)


def _parse_period(period: str | None) -> tuple[Any | None, Any | None, str | None]:
	"""Return (start, end, label). Accepts 'YYYY-MM-DD:YYYY-MM-DD' or empty."""
	if not period or period in ("All periods", "All"):
		return None, None, None
	raw = str(period).strip().replace("–", "-").replace("—", "-")
	if ":" in raw:
		a, b = raw.split(":", 1)
		try:
			return getdate(a.strip()), getdate(b.strip()), f"{a.strip()} – {b.strip()}"
		except Exception:
			return None, None, period
	return None, None, period


def _latest_verified_by_target(plan_name: str, period_start, period_end) -> dict[str, dict]:
	"""One latest Verified measurement per target (bounded query)."""
	filters: dict[str, Any] = {
		"plan_version": plan_name,
		"workflow_status": "Verified",
	}
	rows = frappe.get_all(
		"Performance Measurement",
		filters=filters,
		fields=[
			"name",
			"performance_target",
			"result_status",
			"measurement_period_start",
			"measurement_period_end",
			"actual_numeric",
			"verified_at",
		],
		order_by="measurement_period_end desc, verified_at desc",
		limit_page_length=500,
	)
	latest: dict[str, dict] = {}
	for r in rows:
		tid = r.performance_target
		if tid in latest:
			continue
		if period_start and period_end and r.measurement_period_end:
			end = getdate(r.measurement_period_end)
			if end < period_start or end > period_end:
				# Still consider if period overlaps start
				start = getdate(r.measurement_period_start) if r.measurement_period_start else end
				if end < period_start or start > period_end:
					continue
		latest[tid] = r
	return latest


def _programme_filter_targets(
	plan_name: str, programme: str | None, sub_programme: str | None
) -> tuple[set[str], dict[str, dict]]:
	"""Return target ids in scope + outcome map for those targets."""
	outcomes = frappe.get_all(
		"Strategic Outcome",
		filters={"plan_version": plan_name},
		fields=["name", "outcome_code", "title", "programme", "sub_programme"],
	)
	if programme:
		outcomes = [o for o in outcomes if o.programme == programme]
	if sub_programme:
		outcomes = [o for o in outcomes if o.sub_programme == sub_programme]
	outcome_ids = {o.name for o in outcomes}
	outcome_by_id = {o.name: o for o in outcomes}
	if not outcome_ids:
		return set(), {}

	indicators = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version": plan_name, "strategic_outcome": ["in", list(outcome_ids)]},
		fields=["name", "strategic_outcome"],
		limit_page_length=500,
	)
	ind_to_out = {i.name: i.strategic_outcome for i in indicators}
	if not ind_to_out:
		return set(), outcome_by_id

	targets = frappe.get_all(
		"Performance Target",
		filters={"plan_version": plan_name, "performance_indicator": ["in", list(ind_to_out.keys())]},
		fields=["name", "target_code", "title", "performance_indicator"],
		limit_page_length=500,
	)
	target_meta = {}
	for t in targets:
		oid = ind_to_out.get(t.performance_indicator)
		target_meta[t.name] = {
			"target": t,
			"outcome": outcome_by_id.get(oid),
			"outcome_id": oid,
		}
	return set(target_meta.keys()), target_meta


def _direction_for_outcome(
	target_ids: list[str],
	current_latest: dict[str, dict],
	prior_latest: dict[str, dict],
) -> dict:
	"""Compare On track counts vs prior period — Improving / Declining / Stable."""
	rank = {"On track": 3, "At risk": 2, "Off track": 1, "No data": 0, "Not due": 0}

	def score(latest_map):
		vals = []
		for tid in target_ids:
			st = (latest_map.get(tid) or {}).get("result_status") or "No data"
			vals.append(rank.get(st, 0))
		return sum(vals) / len(vals) if vals else 0

	if not prior_latest:
		return {"key": "stable", "label": "Stable", "icon": "trending_flat"}
	cur = score(current_latest)
	pri = score(prior_latest)
	if cur > pri + 0.15:
		return {"key": "improving", "label": "Improving", "icon": "trending_up"}
	if cur < pri - 0.15:
		return {"key": "declining", "label": "Declining", "icon": "trending_down"}
	return {"key": "stable", "label": "Stable", "icon": "trending_flat"}


def get_strategy_performance(
	procuring_entity: str | None = None,
	plan_code: str | None = None,
	plan_version: str | None = None,
	period: str | None = None,
	programme: str | None = None,
	sub_programme: str | None = None,
) -> dict:
	_require_view()
	plan = _resolve_active_plan(procuring_entity, plan_code, plan_version)
	pe = plan.procuring_entity
	period_start, period_end, period_label = _parse_period(period)
	as_at = now_datetime()

	target_ids, target_meta = _programme_filter_targets(
		plan.name, programme or None, sub_programme or None
	)
	# If no programme filter, include all targets on the plan
	if not programme and not sub_programme and not target_ids:
		targets = frappe.get_all(
			"Performance Target",
			filters={"plan_version": plan.name},
			fields=["name", "target_code", "title", "performance_indicator"],
			limit_page_length=500,
		)
		indicators = {
			i.name: i.strategic_outcome
			for i in frappe.get_all(
				"Performance Indicator",
				filters={"plan_version": plan.name},
				fields=["name", "strategic_outcome"],
				limit_page_length=500,
			)
		}
		outcomes = {
			o.name: o
			for o in frappe.get_all(
				"Strategic Outcome",
				filters={"plan_version": plan.name},
				fields=["name", "outcome_code", "title", "programme", "sub_programme"],
			)
		}
		for t in targets:
			oid = indicators.get(t.performance_indicator)
			target_meta[t.name] = {"target": t, "outcome": outcomes.get(oid), "outcome_id": oid}
		target_ids = set(target_meta.keys())

	latest = _latest_verified_by_target(plan.name, period_start, period_end)
	# Prior period for direction: same length preceding window when period set
	prior_latest: dict[str, dict] = {}
	if period_start and period_end:
		delta = (period_end - period_start).days + 1
		prior_end = frappe.utils.add_days(period_start, -1)
		prior_start = frappe.utils.add_days(prior_end, -(delta - 1))
		prior_latest = _latest_verified_by_target(plan.name, prior_start, prior_end)

	# Strip counts
	strip = {
		"active_targets": len(target_ids),
		"on_track": 0,
		"at_risk": 0,
		"off_track": 0,
		"no_data": 0,
		"not_due": 0,
		"ca_overdue": 0,
	}
	today = getdate()
	for tid in target_ids:
		m = latest.get(tid)
		if not m:
			strip["no_data"] += 1
			continue
		st = (m.result_status or "No data").strip()
		key = {
			"On track": "on_track",
			"At risk": "at_risk",
			"Off track": "off_track",
			"Not due": "not_due",
			"No data": "no_data",
		}.get(st, "no_data")
		strip[key] += 1

	# Corrective actions
	cas = list_corrective_actions(plan_version=plan.name)
	exceptions: list[dict] = []
	ca_by_target: dict[str, list] = defaultdict(list)
	for ca in cas:
		tid = (ca.get("target") or {}).get("id")
		if tid and tid in target_ids:
			ca_by_target[tid].append(ca)
		status = ca.get("status") or ""
		due = ca.get("due_date")
		overdue = bool(due and getdate(due) < today and status in OPEN_CA_STATUSES)
		if overdue:
			strip["ca_overdue"] += 1
		if status in OPEN_CA_STATUSES:
			age = None
			due_label = "—"
			if due:
				d = getdate(due)
				days = (today - d).days
				if days > 0:
					due_label = f"{days} day{'s' if days != 1 else ''} overdue"
					age = days
				else:
					due_label = f"Due {d.strftime('%d %b %Y')}"
			tgt = ca.get("target") or {}
			exceptions.append(
				{
					"type": "Corrective action overdue" if overdue else "Corrective action open",
					"kind": "corrective_action",
					"affected": _ref(tgt.get("id"), tgt.get("code"), tgt.get("name")),
					"owner": ca.get("owner") or "—",
					"due_or_age": due_label,
					"age_days": age,
					"next_action": "Review action",
					"route": ["strategy-corrective-actions", plan.plan_code],
				}
			)

	# Measurement workflow exceptions (non-Verified)
	meas_rows = frappe.get_all(
		"Performance Measurement",
		filters={"plan_version": plan.name, "workflow_status": ["in", ["Draft", "Returned", "Rejected", "Submitted"]]},
		fields=[
			"name",
			"performance_target",
			"workflow_status",
			"measurement_period_end",
			"modified",
		],
		limit_page_length=200,
	)
	for m in meas_rows:
		if m.performance_target not in target_ids:
			continue
		meta = target_meta.get(m.performance_target) or {}
		tgt = meta.get("target")
		code = tgt.target_code if tgt else None
		title = tgt.title if tgt else None
		end = getdate(m.measurement_period_end) if m.measurement_period_end else None
		overdue = bool(end and end < today and m.workflow_status in ("Draft", "Returned"))
		label = {
			"Returned": "Measurement returned",
			"Rejected": "Measurement rejected",
			"Submitted": "Measurement awaiting verification",
			"Draft": "Measurement overdue" if overdue else "Measurement incomplete",
		}.get(m.workflow_status, "Measurement exception")
		days = (today - end).days if end and overdue else None
		exceptions.append(
			{
				"type": label,
				"kind": "measurement",
				"affected": _ref(m.performance_target, code, title),
				"owner": "—",
				"due_or_age": f"{days} days overdue" if days else (m.workflow_status or "—"),
				"age_days": days,
				"next_action": "View target",
				"route": ["strategy-plan-measurements", plan.plan_code],
			}
		)

	# Outcomes rollup
	by_outcome: dict[str, list[str]] = defaultdict(list)
	for tid, meta in target_meta.items():
		oid = meta.get("outcome_id") or "_none"
		by_outcome[oid].append(tid)

	usage = get_strategy_usage(plan_version=plan.name)
	usage_groups = usage.get("groups") or {}

	def procurement_summary_for_targets(tids: list[str]) -> str:
		# Count usage rows whose target matches any tid (snapshot may not always link)
		parts = []

		def count_mod(mod):
			rows = usage_groups.get(mod) or []
			matched = [r for r in rows if (r.get("target") or {}).get("id") in tids]
			return len(matched) if matched else (len(rows) if len(by_outcome) <= 1 else 0)

		d = count_mod("Demand")
		p = count_mod("Planning")
		t = count_mod("Tender")
		c = count_mod("Contract")
		if d:
			parts.append(f"{d} approved demand{'s' if d != 1 else ''}")
		if p:
			parts.append(f"{p} procurement-plan item{'s' if p != 1 else ''}")
		if t:
			parts.append(f"{t} tender{'s' if t != 1 else ''}")
		if c:
			parts.append(f"{c} active contract{'s' if c != 1 else ''}")
		return ", ".join(parts) if parts else "No aligned procurement records"

	outcomes_out = []
	for oid, tids in by_outcome.items():
		outcome = (target_meta[tids[0]].get("outcome") if tids else None) or frappe._dict(
			outcome_code="—", title="Unassigned outcomes", name=oid
		)
		dist = {"On track": 0, "At risk": 0, "Off track": 0, "No data": 0, "Not due": 0}
		attention_bits = []
		for tid in tids:
			m = latest.get(tid)
			if not m:
				dist["No data"] += 1
				attention_bits.append("Target missing verified measurement")
				continue
			st = m.result_status or "No data"
			if st not in dist:
				dist["No data"] += 1
			else:
				dist[st] += 1
			if st in ("At risk", "Off track"):
				attention_bits.append(f"{st} target")
			for ca in ca_by_target.get(tid) or []:
				if ca.get("status") in OPEN_CA_STATUSES:
					attention_bits.append("Corrective action open")
		needs_attention = bool(
			dist["At risk"] or dist["Off track"] or any("missing" in a.lower() for a in attention_bits)
		)
		direction = _direction_for_outcome(tids, latest, prior_latest)
		outcomes_out.append(
			{
				"id": oid if oid != "_none" else None,
				"code": outcome.outcome_code if hasattr(outcome, "outcome_code") else outcome.get("outcome_code"),
				"name": outcome.title if hasattr(outcome, "title") else outcome.get("title"),
				"distribution": dist,
				"direction": direction,
				"procurement_summary": procurement_summary_for_targets(tids),
				"management_attention": attention_bits[0] if attention_bits else ("Needs attention" if needs_attention else "None"),
				"needs_attention": needs_attention,
				"action_label": "Review performance" if needs_attention else "View",
				"route": ["strategy-plan-measurements", plan.plan_code],
			}
		)

	# PVC / public value — STR-AC-028 treatment vs achievement (XMOD-STR-007).
	pvc = list_plan_value_commitments(plan_version=plan.name)
	commitments_out = []
	aligned_demands, treated_by_key = _demand_pvc_treatment_counts(plan.name)
	for row in pvc.get("rows") or []:
		obj = row.get("objective") or {}
		level = row.get("consideration_level") or ""
		pvc_id = (row.get("id") or "").strip()
		treated = treated_by_key.get(pvc_id) or 0
		if aligned_demands == 0:
			treatment = "No aligned Value Cases"
		else:
			treatment = f"{treated} of {aligned_demands} aligned Value Cases addressed"
		# Verified evidence from linked targets (achievement — not treatment)
		evidence = "No verified outcome measure"
		attention = "None"
		linked_tids = [
			(ln.get("target") or {}).get("id")
			for ln in (row.get("links") or [])
			if ln.get("link_type") == "Performance Target"
		]
		linked_tids = [t for t in linked_tids if t]
		for tid in linked_tids:
			m = latest.get(tid)
			if m:
				evidence = f"{(target_meta.get(tid) or {}).get('target').target_code if target_meta.get(tid) else tid}: {m.result_status}"
				if m.result_status in ("At risk", "Off track"):
					attention = "Corrective action open" if ca_by_target.get(tid) else m.result_status
				break
		if level.startswith("Required") and aligned_demands > 0 and treated == 0:
			attention = "1 treatment outstanding"
			exceptions.append(
				{
					"type": "Required value commitment not addressed",
					"kind": "value_commitment",
					"affected": _ref(obj.get("id"), obj.get("code"), obj.get("name")),
					"owner": row.get("responsible_owner") or "—",
					"due_or_age": "Outstanding",
					"age_days": None,
					"next_action": "Review treatment",
					"route": ["strategy-plan-value-commitments", plan.plan_code],
				}
			)
		# Funding treatment is plan-derived only (no invented totals). Prefer explicit
		# allocation language in rationale when present; otherwise an honest placeholder.
		rationale = (row.get("rationale") or "").strip()
		if "KES" in rationale.upper() or "allocation" in rationale.lower():
			funding_treatment = rationale[:120]
		elif level.lower().startswith("required"):
			funding_treatment = "Embedded in plan commitment"
		else:
			funding_treatment = "Optional — no dedicated allocation recorded"
		commitments_out.append(
			{
				"id": row.get("id"),
				"objective": obj,
				"consideration_level": level,
				"funding_treatment": funding_treatment,
				"downstream_adoption": treatment,
				# Keep legacy key for export/tests during transition.
				"downstream_treatment": treatment,
				"verified_evidence": evidence,
				"attention": attention,
				"action_label": "Review commitment" if attention != "None" else "Review commitment",
				"route": ["strategy-plan-value-commitments", plan.plan_code],
			}
		)

	# Procurement funding from Budget Lines (STR-SUP-001 — dual-read primary_*).
	budget_allocated = reserved = committed = consumed = available = 0.0
	budget_n = 0
	source_unavailable = []
	sources_available = ["Strategy"]
	try:
		bl_ok = frappe.db.exists("DocType", "Budget Line")
		use_primary = bl_ok and frappe.db.has_column("Budget Line", "primary_plan_version_id")
		use_legacy = bl_ok and frappe.db.has_column("Budget Line", "strategy_plan_version")
		if use_primary or use_legacy:
			plan_filter_field = "primary_plan_version_id" if use_primary else "strategy_plan_version"
			bl_fields = [
				"name",
				"amount_reserved",
				"amount_committed",
			]
			if frappe.db.has_column("Budget Line", "approved_amount"):
				bl_fields.append("approved_amount")
			elif frappe.db.has_column("Budget Line", "amount_allocated"):
				bl_fields.append("amount_allocated")
			if frappe.db.has_column("Budget Line", "amount_actual"):
				bl_fields.append("amount_actual")
			elif frappe.db.has_column("Budget Line", "amount_consumed"):
				bl_fields.append("amount_consumed")
			for b in frappe.get_all(
				"Budget Line",
				filters={plan_filter_field: plan.name},
				fields=bl_fields,
				limit_page_length=200,
			):
				budget_n += 1
				alloc = _money(getattr(b, "approved_amount", None) or getattr(b, "amount_allocated", None))
				res = _money(b.amount_reserved)
				com = _money(b.amount_committed)
				cons = _money(getattr(b, "amount_actual", None) or getattr(b, "amount_consumed", None))
				budget_allocated += alloc
				reserved += res
				committed += com
				consumed += cons
				available += max(0.0, alloc - res - com)
			if budget_n:
				sources_available.append("Budget & Funding")
			else:
				# DocType present but no aligned lines for this plan — not an unavailable source.
				sources_available.append("Budget & Funding")
		else:
			source_unavailable.append("Budget")
	except Exception:
		source_unavailable.append("Budget")

	if usage_groups.get("Demand"):
		sources_available.append("Demands")
	if usage_groups.get("Planning"):
		sources_available.append("Procurement Plans")
	if usage_groups.get("Tender"):
		sources_available.append("Tenders")
	else:
		# Tender module may be empty — not unavailable
		pass
	if usage_groups.get("Contract"):
		sources_available.append("Contracts")

	def stage(name, count, value, basis, route_action):
		return {
			"stage": name,
			"aligned_records": count,
			"current_value": value,
			"current_value_label": _fmt_kes(value) if value else "—",
			"basis": basis,
			"action_label": route_action,
			"route": ["strategy-plan-downstream-usage", plan.plan_code],
		}

	# Demand values — prefer total_amount (XMOD-STR-007), then legacy estimate fields.
	demand_value = 0.0
	demand_count = len(usage_groups.get("Demand") or [])
	if frappe.db.exists("DocType", "Demand") and frappe.db.has_column("Demand", "strategy_plan_version"):
		dfields = ["name"]
		for cand in ("total_amount", "estimated_cost", "total_estimate", "estimated_value", "amount"):
			if frappe.db.has_column("Demand", cand):
				dfields.append(cand)
				break
		for d in frappe.get_all(
			"Demand",
			filters={"strategy_plan_version": plan.name},
			fields=dfields,
			limit_page_length=200,
		):
			for k in d:
				if k != "name" and d.get(k) is not None:
					demand_value += _money(d.get(k))

	# Planning stage — package estimated_value when strategy_* linked (XMOD-STR-006/007).
	planning_count, planning_value = _planning_package_contribution(plan.name)
	if not planning_count:
		planning_count = len(usage_groups.get("Planning") or [])

	stages = [
		stage(
			"Approved budget",
			budget_n,
			budget_allocated,
			"Approved allocations aligned to selected targets",
			"View",
		),
		stage(
			"Approved demand",
			demand_count,
			demand_value,
			"Approved estimates for the reporting scope",
			"View demands",
		),
		stage(
			"Procurement plan",
			planning_count,
			planning_value,
			"Approved planned value",
			"View plan items",
		),
		stage(
			"Tender",
			len(usage_groups.get("Tender") or []),
			0,
			"Published estimate",
			"View tender",
		),
		stage(
			"Contract",
			len(usage_groups.get("Contract") or []),
			committed,
			"Awarded contract value",
			"View contracts",
		),
	]

	funding_comparable = budget_n > 0
	headroom = budget_allocated - demand_value if funding_comparable and demand_value else available
	total_bar = budget_allocated or (committed + reserved + available) or 1
	funding = {
		"comparable": funding_comparable,
		"budget": budget_allocated,
		"budget_label": _fmt_kes(budget_allocated) if funding_comparable else "—",
		"committed": committed,
		"committed_label": _fmt_kes(committed),
		"reserved": reserved,
		"reserved_label": _fmt_kes(reserved),
		"available": available if funding_comparable else headroom,
		"available_label": _fmt_kes(available if funding_comparable else headroom),
		"consumed": consumed,
		"consumed_label": _fmt_kes(consumed),
		"outstanding": max(committed - consumed, 0),
		"outstanding_label": _fmt_kes(max(committed - consumed, 0)),
		"committed_pct": round(100 * committed / total_bar, 2) if funding_comparable else 0,
		"reserved_pct": round(100 * reserved / total_bar, 2) if funding_comparable else 0,
		"available_pct": round(100 * available / total_bar, 2) if funding_comparable else 0,
		"basis": (
			"Available funding equals approved budget less active reservations and contract commitments. "
			"Actual expenditure is reported separately because it is already included within the committed contract obligation."
			if funding_comparable
			else "Funding comparison unavailable — budget and demand are not comparable for this scope."
		),
		"non_additivity_note": "Lifecycle values represent different stages and must not be added together.",
	}

	# Filter options
	programmes = frappe.get_all(
		"Strategy Programme",
		filters={"plan_version": plan.name},
		fields=["name", "programme_code", "title"],
		order_by="order_index asc",
	)
	subs = frappe.get_all(
		"Strategy Sub Programme",
		filters={"plan_version": plan.name},
		fields=["name", "sub_programme_code", "title", "programme"],
		order_by="order_index asc",
	)

	roles = user_roles()
	open_portfolio = bool(
		roles.intersection(
			{ROLE_OFFICER, ROLE_MANAGER, ROLE_REVIEWER, ROLE_PLANNING, "System Manager"}
		)
		or frappe.session.user == "Administrator"
	)

	empty_verified = strip["on_track"] + strip["at_risk"] + strip["off_track"] == 0

	return {
		"filters": {
			"procuring_entity": pe,
			"plan_code": plan.plan_code,
			"plan_version": plan.name,
			"period": period or "",
			"programme": programme or "",
			"sub_programme": sub_programme or "",
		},
		"reporting_period": {
			"label": period_label or _period_label_from_plan(plan),
			"start": str(period_start) if period_start else None,
			"end": str(period_end) if period_end else None,
		},
		"as_at": as_at.isoformat(sep=" ", timespec="minutes"),
		"as_at_label": as_at.strftime("%d %B %Y, %H:%M"),
		"source_coverage": {
			"available": sources_available,
			"unavailable": source_unavailable,
			"label": "Sources available: " + ", ".join(sources_available)
			if sources_available
			else "No sources available",
		},
		"plan": {
			"id": plan.name,
			"code": plan.plan_code,
			"name": plan.title,
			"status": plan.status,
			"procuring_entity": {
				"id": pe,
				"code": _entity_code(pe),
				"name": _entity_label(pe),
			},
		},
		"strip": strip,
		"outcomes": outcomes_out,
		"exceptions": exceptions,
		"procurement": {"stages": stages, "funding": funding},
		"commitments": commitments_out,
		"options": {
			"programmes": [
				{"id": p.name, "code": p.programme_code, "name": p.title} for p in programmes
			],
			"sub_programmes": [
				{
					"id": s.name,
					"code": s.sub_programme_code,
					"name": s.title,
					"programme": s.programme,
				}
				for s in subs
			],
		},
		"capabilities": {
			"export_report": can_export_strategy_performance(),
			"open_portfolio": open_portfolio,
			"change_entity": has_cross_entity_authority(),
			"empty_period": empty_verified,
		},
		"unavailable_message": (
			f"{source_unavailable[0]} data is temporarily unavailable. "
			f"{source_unavailable[0]} contribution is excluded from this view."
			if source_unavailable
			else None
		),
	}


def _period_label_from_plan(plan) -> str:
	if plan.start_date and plan.end_date:
		return f"{getdate(plan.start_date).strftime('%b %Y')} – {getdate(plan.end_date).strftime('%b %Y')}"
	return "Active plan period"


def export_strategy_performance_report(
	procuring_entity: str | None = None,
	plan_code: str | None = None,
	plan_version: str | None = None,
	period: str | None = None,
	programme: str | None = None,
	sub_programme: str | None = None,
) -> dict:
	if not can_export_strategy_performance():
		frappe.throw(_("Not permitted to export Strategy Performance report"), frappe.PermissionError)
	dto = get_strategy_performance(
		procuring_entity=procuring_entity,
		plan_code=plan_code,
		plan_version=plan_version,
		period=period,
		programme=programme,
		sub_programme=sub_programme,
	)
	buf = io.StringIO()
	w = csv.writer(buf)
	w.writerow(["Strategy Performance management report"])
	w.writerow(["Generated", _safe_csv_cell(dto["as_at"])])
	w.writerow(["As at", _safe_csv_cell(dto.get("as_at_label"))])
	w.writerow(["Plan", _safe_csv_cell(f"{dto['plan']['code']} — {dto['plan']['name']}")])
	w.writerow(["Entity", _safe_csv_cell((dto["plan"].get("procuring_entity") or {}).get("name"))])
	w.writerow(["Reporting period", _safe_csv_cell((dto.get("reporting_period") or {}).get("label"))])
	w.writerow(["Source coverage", _safe_csv_cell((dto.get("source_coverage") or {}).get("label"))])
	w.writerow([])
	w.writerow(["Strip metric", "Value"])
	for k, v in (dto.get("strip") or {}).items():
		w.writerow([_safe_csv_cell(k), _safe_csv_cell(v)])
	w.writerow([])
	w.writerow(["Exceptions"])
	w.writerow(["Type", "Code", "Name", "Owner", "Due or age", "Next action"])
	for ex in dto.get("exceptions") or []:
		aff = ex.get("affected") or {}
		w.writerow(
			[
				_safe_csv_cell(ex.get("type")),
				_safe_csv_cell(aff.get("code")),
				_safe_csv_cell(aff.get("name")),
				_safe_csv_cell(ex.get("owner")),
				_safe_csv_cell(ex.get("due_or_age")),
				_safe_csv_cell(ex.get("next_action")),
			]
		)
	w.writerow([])
	w.writerow(["Outcomes"])
	w.writerow(["Code", "Name", "On track", "At risk", "Off track", "No data", "Direction", "Attention"])
	for o in dto.get("outcomes") or []:
		d = o.get("distribution") or {}
		w.writerow(
			[
				_safe_csv_cell(o.get("code")),
				_safe_csv_cell(o.get("name")),
				_safe_csv_cell(d.get("On track")),
				_safe_csv_cell(d.get("At risk")),
				_safe_csv_cell(d.get("Off track")),
				_safe_csv_cell(d.get("No data")),
				_safe_csv_cell((o.get("direction") or {}).get("label")),
				_safe_csv_cell(o.get("management_attention")),
			]
		)
	w.writerow([])
	w.writerow(["Procurement stages"])
	w.writerow(["Stage", "Aligned records", "Current value", "Basis"])
	for s in (dto.get("procurement") or {}).get("stages") or []:
		w.writerow(
			[
				_safe_csv_cell(s.get("stage")),
				_safe_csv_cell(s.get("aligned_records")),
				_safe_csv_cell(s.get("current_value_label")),
				_safe_csv_cell(s.get("basis")),
			]
		)
	w.writerow([])
	w.writerow(["Commitments"])
	w.writerow(
		["Code", "Name", "Level", "Funding treatment", "Downstream adoption", "Evidence", "Attention"]
	)
	for c in dto.get("commitments") or []:
		obj = c.get("objective") or {}
		w.writerow(
			[
				_safe_csv_cell(obj.get("code")),
				_safe_csv_cell(obj.get("name")),
				_safe_csv_cell(c.get("consideration_level")),
				_safe_csv_cell(c.get("funding_treatment")),
				_safe_csv_cell(c.get("downstream_adoption") or c.get("downstream_treatment")),
				_safe_csv_cell(c.get("verified_evidence")),
				_safe_csv_cell(c.get("attention")),
			]
		)

	filename = f"strategy-performance-{dto['plan']['code']}-{getdate().isoformat()}.csv"
	return {
		"ok": True,
		"filename": filename,
		"content_type": "text/csv",
		"content": buf.getvalue(),
		"filters": dto.get("filters"),
		"as_at": dto.get("as_at"),
		"source_coverage": dto.get("source_coverage"),
	}
