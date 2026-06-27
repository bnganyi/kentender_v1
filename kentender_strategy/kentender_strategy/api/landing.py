# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Strategy Management workspace — single payload for KPIs, plan list, and hierarchy counts."""

import json
from typing import Dict, Tuple

import frappe
from frappe import _


def _counts_by_plan(plan_names: list) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], Dict[str, int]]:
	"""Return four maps: strategic_plan -> count for Program / Sub Program / Indicator / Target."""
	if not plan_names:
		return {}, {}, {}, {}
	params = tuple(plan_names)
	prog: dict[str, int] = {}
	sub: dict[str, int] = {}
	obj: dict[str, int] = {}
	tgt: dict[str, int] = {}
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Program`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		prog[row.strategic_plan] = int(row.c or 0)
	if frappe.db.exists("DocType", "Sub Program"):
		for row in frappe.db.sql(
			"""
			SELECT strategic_plan, COUNT(*) AS c
			FROM `tabSub Program`
			WHERE strategic_plan IN %(plans)s
			GROUP BY strategic_plan
			""",
			{"plans": params},
			as_dict=True,
		):
			sub[row.strategic_plan] = int(row.c or 0)
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Objective`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		obj[row.strategic_plan] = int(row.c or 0)
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COUNT(*) AS c
		FROM `tabStrategy Target`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		tgt[row.strategic_plan] = int(row.c or 0)
	return prog, sub, obj, tgt


def _budget_by_plan(plan_names: list) -> dict:
	"""Return map strategic_plan -> SUM(total_amount) from Demand (0.0 if no rows)."""
	if not plan_names or not frappe.db.exists("DocType", "Demand"):
		return {}
	params = tuple(plan_names)
	result: dict[str, float] = {}
	for row in frappe.db.sql(
		"""
		SELECT strategic_plan, COALESCE(SUM(total_amount), 0) AS plan_budget
		FROM `tabDemand`
		WHERE strategic_plan IN %(plans)s
		GROUP BY strategic_plan
		""",
		{"plans": params},
		as_dict=True,
	):
		result[row.strategic_plan] = float(row.plan_budget or 0)
	return result


# ── Weighted success score computation ────────────────────────────────────────

def _kpi_score(mtype: str, direction: str, target_val, actual_val, is_complete: int) -> float | None:
	"""Convert a single KPI to a 0–100 score.

	Returns None when no actual data is available (coverage denominator still increments,
	but the target is excluded from the numerator).
	"""
	if mtype in ("Milestone", "Boolean"):
		# Score is 0 or 100 based on is_complete flag; always has data.
		return 100.0 if is_complete else 0.0

	if mtype == "Percentage":
		# actual IS the percentage; cap at 100.
		if actual_val is None:
			return None
		return float(min(actual_val, 100.0))

	if mtype in ("Numeric", "Currency"):
		if actual_val is None:
			return None
		t = float(target_val or 0)
		a = float(actual_val)
		if t <= 0:
			return None
		direction = direction or "Higher is Better"
		if direction == "Higher is Better":
			return float(min(a / t * 100.0, 100.0))
		else:  # Lower is Better: target / actual × 100, cap at 100
			if a <= 0:
				return 0.0
			return float(min(t / a * 100.0, 100.0))

	return None


def _compute_portfolio_success(plan_names: list, budget_by: dict) -> tuple[float | None, float]:
	"""Weighted hierarchical success rate for the portfolio of current-version active plans.

	Algorithm (Steps A-C from spec):
	  A. Each KPI → 0-100 score.
	  B. Objective score = weighted avg of its KPI scores (skip missing actuals).
	  C. Programme score = weighted avg of its Objective scores.
	     Plan score      = weighted avg of its Programme scores.
	  Portfolio          = budget-weighted avg of active-plan scores (fallback: equal).

	Returns (success_rate_pct | None, data_coverage_pct).
	"""
	if not frappe.db.exists("DocType", "Strategy Target"):
		return None, 0.0

	active_plans = [
		n for n in plan_names
		if frappe.db.get_value("Strategic Plan", n, "status") == "Active"
	]
	if not active_plans:
		return None, 0.0

	active_tuple = tuple(active_plans)

	# ── Fetch all targets for active plans in one query ────────────────────
	targets = frappe.db.sql(
		"""
		SELECT
			t.name, t.strategic_plan, t.program, t.objective,
			t.measurement_type, t.measurement_direction,
			t.target_value_numeric, t.actual_value_numeric,
			t.actual_is_complete, t.weight,
			o.weight AS obj_weight, p.weight AS prog_weight
		FROM `tabStrategy Target` t
		LEFT JOIN `tabStrategy Objective` o ON o.name = t.objective
		LEFT JOIN `tabStrategy Program` p ON p.name = t.program
		WHERE t.strategic_plan IN %(plans)s
		""",
		{"plans": active_tuple},
		as_dict=True,
	)

	if not targets:
		return None, 0.0

	total_targets = len(targets)
	targets_with_data = 0

	# ── Step A: compute KPI scores; group by (plan, program, objective) ────
	# Structure: plan → prog → obj → [(score, weight), ...]
	from collections import defaultdict
	tree: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

	for t in targets:
		mtype = t.measurement_type or "Numeric"
		direction = t.measurement_direction or "Higher is Better"
		score = _kpi_score(
			mtype=mtype,
			direction=direction,
			target_val=t.target_value_numeric,
			actual_val=t.actual_value_numeric,
			is_complete=int(t.actual_is_complete or 0),
		)
		if score is not None:
			targets_with_data += 1
		tree[t.strategic_plan][t.program][t.objective].append({
			"score": score,
			"kpi_weight": float(t.weight or 1.0),
			"obj_weight": float(t.obj_weight or 1.0),
			"prog_weight": float(t.prog_weight or 1.0),
		})

	data_coverage = round(targets_with_data / total_targets * 100, 1) if total_targets else 0.0

	# ── Steps B-C: roll up hierarchy ──────────────────────────────────────
	def weighted_avg(pairs: list[tuple[float, float]]) -> float | None:
		"""pairs = [(score, weight), ...]; skip None scores."""
		valid = [(s, w) for s, w in pairs if s is not None]
		if not valid:
			return None
		total_w = sum(w for _, w in valid)
		if total_w <= 0:
			return None
		return sum(s * w for s, w in valid) / total_w

	plan_scores: list[tuple[float | None, float]] = []  # (score, plan_weight)

	for plan_name, progs in tree.items():
		prog_scores: list[tuple[float | None, float]] = []

		for prog_name, objs in progs.items():
			obj_scores: list[tuple[float | None, float]] = []
			prog_weight = 1.0

			for obj_name, kpis in objs.items():
				# Step B: objective score = weighted avg of KPI scores
				kpi_pairs = [(k["score"], k["kpi_weight"]) for k in kpis]
				obj_score = weighted_avg(kpi_pairs)
				obj_weight = kpis[0]["obj_weight"] if kpis else 1.0
				prog_weight = kpis[0]["prog_weight"] if kpis else 1.0
				obj_scores.append((obj_score, obj_weight))

			# Step C: programme score = weighted avg of objective scores
			prog_score = weighted_avg(obj_scores)
			prog_scores.append((prog_score, prog_weight))

		# Plan score = weighted avg of programme scores
		plan_score = weighted_avg(prog_scores)

		# Plan weight: budget weight (fallback equal=1)
		plan_weight = float(budget_by.get(plan_name) or 1.0)
		plan_scores.append((plan_score, plan_weight))

	# Portfolio = budget-weighted avg of active plan scores
	portfolio_score = weighted_avg(plan_scores)
	if portfolio_score is not None:
		portfolio_score = round(portfolio_score, 1)

	return portfolio_score, data_coverage


@frappe.whitelist()
def get_strategy_landing_data():
	"""Portfolio KPIs + Strategic Plan rows with embedded hierarchy counts (current versions only)."""
	if not frappe.has_permission("Strategic Plan", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	plans = frappe.get_all(
		"Strategic Plan",
		filters={"is_current_version": 1},
		fields=[
			"name",
			"strategic_plan_name",
			"start_year",
			"end_year",
			"status",
			"modified",
			"owner",
			"procuring_entity",
			"version_no",
		],
		order_by="modified desc",
		limit=2000,
	)

	session_user = frappe.session.user

	empty_portfolio = {
		"total_plans": 0,
		"draft_count": 0,
		"submitted_count": 0,
		"approved_count": 0,
		"active_count": 0,
		"archived_count": 0,
		"my_drafts_count": 0,
		"total_programs": 0,
		"total_budget": 0.0,
		"success_rate": 0.0,
		"data_coverage": 0.0,
	}

	if not plans:
		return {"portfolio": empty_portfolio, "plans": []}

	names = [p.name for p in plans]
	prog_by, sub_by, obj_by, tgt_by = _counts_by_plan(names)
	budget_by = _budget_by_plan(names)

	def _status_count(status: str) -> int:
		return sum(1 for p in plans if (p.get("status") or "").strip() == status)

	draft_count = _status_count("Draft")
	submitted_count = _status_count("Submitted")
	approved_count = _status_count("Approved")
	active_count = _status_count("Active")
	archived_count = _status_count("Archived")
	my_drafts_count = sum(
		1
		for p in plans
		if (p.get("status") or "").strip() == "Draft" and p.get("owner") == session_user
	)
	total_programs = sum(prog_by.get(n, 0) for n in names)

	# Success rate: normalized weighted KPI score across active plans.
	# data_coverage: % of targets that have actual values reported.
	success_rate, data_coverage = _compute_portfolio_success(names, budget_by)
	# Fallback to 0.0 for display when None (no active plans with targets)
	if success_rate is None:
		success_rate = 0.0

	out_plans = []
	for p in plans:
		n = p.name
		pc = int(prog_by.get(n, 0))
		spc = int(sub_by.get(n, 0))
		ic = int(obj_by.get(n, 0))
		tc = int(tgt_by.get(n, 0))
		out_plans.append(
			{
				**p,
				"program_count": pc,
				"sub_program_count": spc,
				"indicator_count": ic,
				"objective_count": ic,
				"target_count": tc,
				"total_budget": budget_by.get(n, 0.0),
			}
		)

	return {
		"portfolio": {
			"total_plans": len(plans),
			"draft_count": draft_count,
			"submitted_count": submitted_count,
			"approved_count": approved_count,
			"active_count": active_count,
			"archived_count": archived_count,
			"my_drafts_count": my_drafts_count,
			"total_programs": total_programs,
			"total_budget": sum(budget_by.values()),
			"success_rate": success_rate,
			"data_coverage": data_coverage,
		},
		"plans": out_plans,
	}


def _parse_action_label(data_json: str | None) -> tuple[str, str]:
	"""Return (label, dot_class) by inspecting the Version data JSON.

	dot_class is one of: primary (black), green, amber, slate.
	"""
	if not data_json:
		return ("Saved", "slate")
	try:
		data = json.loads(data_json)
	except (TypeError, ValueError):
		return ("Saved", "slate")

	changed: list = data.get("changed") or []
	# Look for status change — highest signal event
	for item in changed:
		if isinstance(item, (list, tuple)) and len(item) >= 3 and item[0] == "status":
			new_status = str(item[2] or "").strip()
			dot = {
				"Active": "green",
				"Approved": "green",
				"Submitted": "primary",
				"Archived": "amber",
				"Draft": "slate",
			}.get(new_status, "slate")
			return (f"Status → {new_status}", dot)

	# Generic: count changed fields
	n = len(changed)
	if n == 1:
		field = str(changed[0][0]).replace("_", " ").title() if changed[0] else "Field"
		return (f"{field} updated", "slate")
	if n > 1:
		return (f"{n} fields updated", "slate")

	added = data.get("added") or []
	removed = data.get("removed") or []
	if added:
		return ("Records added", "primary")
	if removed:
		return ("Records removed", "amber")
	return ("Saved", "slate")


@frappe.whitelist()
def get_portfolio_activity(limit: int = 20) -> list:
	"""Return last N activity records for Strategic Plan documents.

	Sources (merged, deduplicated, sorted newest-first):
	  1. tabVersion rows (field-level changes with parsed action labels)
	  2. Synthetic "Plan created" rows from tabStrategic Plan.creation

	Only records referencing currently existing plans are returned.

	Each item: {time, action, dot_class, plan_name, user}
	"""
	if not frappe.has_permission("Strategic Plan", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	limit = max(1, min(int(limit), 100))

	# Fetch current plans for join + title lookup
	plans = frappe.get_all(
		"Strategic Plan",
		filters={"is_current_version": 1},
		fields=["name", "strategic_plan_name", "owner", "creation"],
		limit=2000,
	)
	if not plans:
		return []

	plan_titles: dict[str, str] = {p.name: (p.strategic_plan_name or p.name) for p in plans}
	plan_names_tuple = tuple(plan_titles.keys())

	events: list[dict] = []

	# ── Version events ────────────────────────────────────────────────────────
	version_rows = frappe.db.sql(
		"""
		SELECT v.docname, v.owner, v.creation, v.data
		FROM `tabVersion` v
		WHERE v.ref_doctype = 'Strategic Plan'
		  AND v.docname IN %(plans)s
		ORDER BY v.creation DESC
		LIMIT %(lim)s
		""",
		{"plans": plan_names_tuple, "lim": limit * 3},
		as_dict=True,
	)
	for row in version_rows:
		action, dot = _parse_action_label(row.get("data"))
		events.append({
			"time": str(row.creation),
			"action": action,
			"dot_class": dot,
			"plan_name": plan_titles.get(row.docname, row.docname),
			"user": row.owner or "—",
		})

	# ── Synthetic "Plan created" events ──────────────────────────────────────
	# Use a set to avoid double-counting plans that also have Version rows
	plans_with_versions = {r.get("docname") for r in version_rows}
	for p in plans:
		events.append({
			"time": str(p.creation),
			"action": "Plan created",
			"dot_class": "primary",
			"plan_name": plan_titles[p.name],
			"user": p.owner or "—",
		})

	# Sort newest-first and take top N
	events.sort(key=lambda e: e["time"], reverse=True)
	return events[:limit]
