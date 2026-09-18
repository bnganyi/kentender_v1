# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 — Annual Plan, Plan Item, Finance, governance and
publication read models (PLN-UI-07..14).

`GetPlanVersion` serves the Draft workbench (PLN-DES-07): summary strip with
the reserved share, the unallocated accepted-source pool (§8.1
ListAcceptedDPPSources, classification joined through the immutable
validation decision), the Plan Items, and the nine-row readiness card.
`GetPlanItem` serves the editor (PLN-DES-09/09A): read-only sources, the
Identity / Classification and method / Preference and structure cards, the
live-recomputed baseline schedule with its closed period disclosure, and —
on an Active Version — the baseline / forecast / actual tiers. `GetFinanceTask`
serves the plan-level affordability statement (PLN-DES-10);
`GetPlanGovernanceTask` the immutable snapshot (PLN-DES-11/12);
`GetPublicationTask` the attempt result (PLN-DES-13).

**Source correction required** is derived here, never stored (§4.9). Every
offer (`mutable`, `can_act`, `can_request_funding`, `can_submit`) is
computed from the same resolver the commands use (read-offer parity).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, formatdate

from kentender_procurement.procurement_planning.errors import MESSAGES
from kentender_procurement.procurement_planning.services import needs_intake, readiness, references, schedule
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

PAGE = "procurement-planning"
PLAN_READERS = (ROLE_PROCUREMENT_PLANNER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_AUDITOR, ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_ACCOUNTING_OFFICER, ROLE_PLAN_STATUTORY_APPROVER)


def _money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _eat(value) -> str:
	"""A UTC instant rendered as EAT (§12.13)."""
	if not value:
		return ""
	from frappe.utils import convert_utc_to_timezone, format_datetime, get_datetime

	local = convert_utc_to_timezone(get_datetime(value), "Africa/Nairobi")
	return f"{format_datetime(local, 'd MMM yyyy, HH:mm')} EAT"


def _unit_label(unit: str) -> str:
	return cstr(frappe.db.get_value("UOM", unit, "uom_name") or unit)


def _quantity_display(quantity, unit: str) -> str:
	return f"{flt(quantity):g} {_unit_label(unit).lower()}".strip()


def _ou_label(ou: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _plan_root(plan_reference: str):
	name = frappe.db.get_value("Annual Plan", {"plan_reference": cstr(plan_reference)})
	if not name:
		authz.not_found()
	return frappe.get_doc("Annual Plan", name)


def _open_version(plan):
	name = cstr(plan.open_successor_version) or cstr(plan.active_version)
	if not name:
		authz.not_found()
	return frappe.get_doc("Annual Plan Version", name)


def _classification_evidence(dpp_version: str) -> dict[str, dict[str, Any]]:
	"""PLN-CHG-001 v1.23 §4.4 — the **effective** classification per accepted
	entry: the latest valid correction where one exists, otherwise the original
	acceptance. New Planning work always reads through here, which is what makes
	a correction take effect without rewriting any accepted decision."""
	from kentender_procurement.procurement_planning.services import dpp_classification

	submission = frappe.db.get_value("Departmental Plan Submission", {"dpp_version": dpp_version}, "name")
	if not submission:
		return {}
	decision = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": submission, "decision": "Accept departmental plan"},
		"classifications",
	)
	accepted = json.loads(decision) if decision else {}
	out: dict[str, dict[str, Any]] = {}
	for entry_id in accepted:
		effective = dpp_classification.effective_classification(submission, entry_id)
		if effective:
			out[entry_id] = effective
	return out


def _classifications(dpp_version: str) -> dict[str, str]:
	"""Effective requirement type per accepted entry."""
	return {k: cstr(v["requirement_type"]) for k, v in _classification_evidence(dpp_version).items()}


def _line_labels(fiscal_year: str) -> dict[str, dict[str, Any]]:
	from kentender_procurement.procurement_planning.services import budget_gateway

	try:
		return budget_gateway.line_labels(fiscal_year)
	except Exception:
		return {}


def _accepted_entry_rows(fiscal_year: str) -> list[dict[str, Any]]:
	"""§8.1 ListAcceptedDPPSources — every current accepted entry that
	proceeds, its classification and its current allocation (if any)."""
	accepted = frappe.get_all(
		"Departmental Plan", filters={"fiscal_year": fiscal_year, "current_accepted_version": ("!=", "")},
		fields=["name", "organisation_unit", "current_accepted_version"],
	)
	labels = _line_labels(fiscal_year)
	rows: list[dict[str, Any]] = []
	for root in accepted:
		version = root.current_accepted_version
		classifications = _classifications(version)
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version},
			fields=["name", "entry_id", "title", "source_origin", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "not_proceeding_reason"],
		)
		ou_label = _ou_label(root.organisation_unit)
		for entry in entries:
			if cstr(entry.not_proceeding_reason).strip():
				continue
			rows.append(
				{
					"dpp_entry": entry.name,
					"entry_id": entry.entry_id,
					"title": entry.title,
					"department": ou_label,
					"organisation_unit": root.organisation_unit,
					"source_origin": entry.source_origin,
					"classification": cstr(classifications.get(entry.entry_id)),
					"quantity": flt(entry.quantity),
					"quantity_display": _quantity_display(entry.quantity, entry.unit),
					# §10.1 — Quantity and Unit are separate columns.
					"quantity_number": f"{flt(entry.quantity):g}",
					"unit_label": cstr(entry.unit),
					"unit": entry.unit,
					"source_label": (
						f"Accepted Need · {entry.need}" if entry.need else "Direct requirement"
					),
					"required_by_date": cstr(entry.required_by_date),
					"required_by_display": _date(entry.required_by_date),
					"budget_line": entry.budget_line,
					"budget_line_display": labels.get(cstr(entry.budget_line), {}).get("reference") or cstr(entry.budget_line),
					"indicative_amount": flt(entry.indicative_amount),
					"amount_display": _money(entry.indicative_amount),
				}
			)
	return rows


# --------------------------------------------------------------------------
# Source lineage (§7.1). A DPP update copies every entry onto a new document
# under the same stable entry_id. An allocation stays pinned to the document
# it was formed from; whether that document still *is* the source depends
# on the current accepted copy carrying the same facts and funding.
# --------------------------------------------------------------------------

ENTRY_SOURCE_FIELDS = (
	"source_origin", "need", "need_revision", "title", "description", "expected_operational_result",
	"quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "not_proceeding_reason",
)


def _source_signature(entry) -> tuple:
	return (
		cstr(entry.source_origin), cstr(entry.need), cstr(entry.need_revision),
		cstr(entry.title).strip(), cstr(entry.description).strip(), cstr(entry.expected_operational_result).strip(),
		flt(entry.quantity), cstr(entry.unit), cstr(entry.required_by_date),
		cstr(entry.budget_line), flt(entry.indicative_amount), cstr(entry.not_proceeding_reason).strip(),
	)


def _entry_source(dpp_entry: str):
	return frappe.db.get_value("Departmental Plan Entry", dpp_entry, ["name", "entry_id", "dpp_version", *ENTRY_SOURCE_FIELDS], as_dict=True)


def current_entry_for(dpp_entry: str) -> str:
	"""The current accepted Version's document for this entry's stable
	entry_id — `dpp_entry` itself when it is current, "" when the DPP has no
	accepted Version or the entry is gone from it."""
	entry = frappe.db.get_value("Departmental Plan Entry", dpp_entry, ["entry_id", "dpp_version"], as_dict=True)
	if not entry:
		return ""
	root_name = frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan")
	current_accepted = cstr(frappe.db.get_value("Departmental Plan", root_name, "current_accepted_version"))
	if not current_accepted:
		return ""
	if current_accepted == entry.dpp_version:
		return dpp_entry
	return cstr(frappe.db.get_value("Departmental Plan Entry", {"dpp_version": current_accepted, "entry_id": entry.entry_id}, "name"))


def same_source(dpp_entry: str, other: str) -> bool:
	"""Two documents of one entry_id are the same source when every fact
	Planning consumes and the funding specification are identical."""
	if dpp_entry == other:
		return True
	a, b = _entry_source(dpp_entry), _entry_source(other)
	return bool(a and b and a.entry_id == b.entry_id and _source_signature(a) == _source_signature(b))


def same_source_lineage(dpp_entry: str) -> list[str]:
	"""Every document under the same DPP root carrying this entry_id with the
	same facts and funding — the names an allocation may be pinned to."""
	entry = _entry_source(dpp_entry)
	if not entry:
		return [dpp_entry]
	root_name = frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan")
	versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root_name}, pluck="name")
	candidates = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": ("in", versions), "entry_id": entry.entry_id},
		fields=["name", "entry_id", "dpp_version", *ENTRY_SOURCE_FIELDS],
	)
	signature = _source_signature(entry)
	return [row.name for row in candidates if _source_signature(row) == signature]


def _with_current_copies(allocated: set[str]) -> set[str]:
	"""An allocation pinned to a predecessor copy claims the current copy too
	when nothing about the source changed; a changed source leaves the
	current copy unallocated (§7.1 — correction, never an automatic move)."""
	out = set(allocated)
	for name in allocated:
		current = current_entry_for(name)
		if current and current != name and same_source(name, current):
			out.add(current)
	return out


def _allocated_dpp_entries(plan_version: str) -> set[str]:
	names = set(frappe.get_all("Plan Source Allocation", filters={"plan_version": plan_version, "allocation_state": ("in", ("Draft", "Active"))}, pluck="dpp_entry"))
	return _with_current_copies(names)


def allocated_current_entries(fiscal_year: str) -> set[str]:
	"""Entries effectively allocated in any live Version of the year's Plan."""
	plan = frappe.db.get_value("Annual Plan", {"fiscal_year": fiscal_year}, "name")
	if not plan:
		return set()
	versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": plan}, pluck="name")
	names = set(
		frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_version": ("in", versions or ("",)), "allocation_state": ("in", ("Draft", "Active"))},
			pluck="dpp_entry",
		)
	)
	return _with_current_copies(names)


def source_correction_required(dpp_entry: str) -> bool:
	entry = frappe.db.get_value("Departmental Plan Entry", dpp_entry, ["entry_id", "dpp_version"], as_dict=True)
	if not entry:
		return True
	root_name = frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan")
	current_accepted = frappe.db.get_value("Departmental Plan", root_name, "current_accepted_version")
	if not current_accepted or current_accepted == entry.dpp_version:
		return False
	current_entry = current_entry_for(dpp_entry)
	if not current_entry:
		return True
	return not same_source(dpp_entry, current_entry)


def resolve_item_doc_name(plan_item_id: str) -> str:
	"""A Plan Item's business id can name two live docs at once (the Active
	predecessor's frozen copy and its Draft successor's copy); the one open
	to act on wins — the same precedence `_open_version` uses."""
	rows = frappe.get_all("Annual Plan Item", filters={"plan_item_id": cstr(plan_item_id)}, fields=["name", "plan_version"])
	if not rows:
		authz.not_found()
	if len(rows) == 1:
		return rows[0].name
	plan_name = frappe.db.get_value("Annual Plan Version", rows[0].plan_version, "annual_plan")
	open_successor = cstr(frappe.db.get_value("Annual Plan", plan_name, "open_successor_version"))
	for row in rows:
		if row.plan_version == open_successor:
			return row.name
	return rows[0].name


# --------------------------------------------------------------------------
# Readiness (PLN-DES-07 card)
# --------------------------------------------------------------------------


def _item_docs(version_name: str) -> list:
	return [frappe.get_doc("Annual Plan Item", n) for n in frappe.get_all("Annual Plan Item", filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")}, order_by="creation asc", pluck="name")]


def plan_readiness(version, plan, *, stage: str = "pre_finance") -> dict[str, Any]:
	"""The exact blocker list and the readiness card. `pre_finance` (§5.6.4)
	excludes Finance confirmation and the submission-only gates; `submission`
	adds verified profiles, method evidence, feasibility and the planned
	reservation allocations against the annual budget (§5.5.3.1)."""
	from kentender_procurement.procurement_planning.services import plan_finance, strategy_gateway

	reference = readiness.reference_for(plan.fiscal_year)
	items = _item_docs(version.name)
	eligible = {row["id"] for row in strategy_gateway.list_eligible_strategic_objectives()}
	blockers: list[dict[str, Any]] = []
	per_check = {"objective": [], "reservation": [], "contents": [], "schedule": [], "method": [], "evidence": []}
	for item in items:
		allocations = readiness._allocations(item.name)
		if any(source_correction_required(a.dpp_entry) for a in allocations):
			blockers.append({"code": "PLN_SOURCE_CORRECTION_REQUIRED", "plan_item_id": item.plan_item_id, "message": f"{MESSAGES['PLN_SOURCE_CORRECTION_REQUIRED']} ({item.plan_item_id})"})
		objective_ok = bool(cstr(item.strategic_objective)) and (cstr(item.strategic_objective) in eligible or version.version_status == "Active")
		for blocker in readiness.item_blockers(item, allocations, plan.fiscal_year, objective_eligible=objective_ok, stage=stage):
			blockers.append({**blocker, "plan_item_id": item.plan_item_id, "message": f"{MESSAGES[blocker['code']]} ({item.plan_item_id})"})
			key = {
				"PLN_OBJECTIVE_INELIGIBLE": "objective", "PLN_RESERVATION_REQUIRED": "reservation",
				"PLN_PLAN_CONTENTS_INCOMPLETE": "contents", "PLN_ENTRY_INCOMPLETE": "contents",
				"PLN_SCHEDULE_INVALID": "schedule", "PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "schedule", "PLN_DELIVERY_PERIOD_REQUIRED": "schedule",
				"PLN_METHOD_NOT_ADMISSIBLE": "method", "PLN_REFERENCE_UNAVAILABLE": "method", "PLN_METHOD_EVIDENCE_REQUIRED": "evidence",
			}[blocker["code"]]
			per_check[key].append(item.plan_item_id)
	for pid in readiness.low_value_cumulative_breaches(version.name, reference):
		blockers.append({"code": "PLN_METHOD_NOT_ADMISSIBLE", "plan_item_id": pid, "message": f"Low value procurement exceeds the per-item annual limit ({pid})."})
		per_check["method"].append(pid)

	share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
	target = share["target_percent"]
	county_target = share["county"]["target_percent"]
	is_county = share["county"]["applicable"]
	if stage == "submission" and items and share["mandatory"]:
		if not share["basis"]["available"] or not share["verified"]:
			blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "message": "The planned reservation allocation cannot be assessed: the annual budget basis or the verified reservation rule is missing.", "field": "reservation_category"})
		elif not share["met"]:
			blockers.append({"code": "PLN_RESERVATION_SHORTFALL", "message": f"{MESSAGES['PLN_RESERVATION_SHORTFALL']} Required {share['required']}, planned {share['qualifying']}, shortfall {share['shortfall']}.", "shortfall": share["shortfall"]})
	advisories = readiness.splitting_advisory(version.name, reference)
	affordability = None
	if items:
		try:
			affordability = plan_finance.affordability_statement(plan, version)
		except Exception:
			affordability = None
	within_approved = bool(affordability and affordability.get("within_approved"))
	if items and affordability and not within_approved:
		blockers.append({"code": "PLN_PLAN_NOT_AFFORDABLE", "message": MESSAGES["PLN_PLAN_NOT_AFFORDABLE"], "failing_lines": affordability.get("failing_lines", [])})
	funding_current = plan_finance.funding_is_current(version, affordability) if items and affordability else False

	def _state(started: bool, failing: list[str]) -> tuple[str, str]:
		if not started:
			return "Not started", "neutral"
		return ("Complete", "live") if not failing else (f"{len(failing)} to fix", "attention")

	started = bool(items)
	checks = [
		{"check": "Every Plan Item has a Strategic Objective", **dict(zip(("result", "kind"), _state(started, per_check["objective"])))},
		{"check": "Every Plan Item has a reservation category", **dict(zip(("result", "kind"), _state(started, per_check["reservation"])))},
		{"check": "Every Plan Item records plan horizon, aggregation and lotting", **dict(zip(("result", "kind"), _state(started, per_check["contents"])))},
		{"check": "Baseline schedule follows the resolved procedure profile and the delivery boundary", **dict(zip(("result", "kind"), _state(started, per_check["schedule"])))},
		{"check": "Procurement method meets its conditions", **dict(zip(("result", "kind"), _state(started, per_check["method"] + per_check["evidence"])))},
		{"check": "Plan within approved budget", "result": ("Within approved" if within_approved else ("Exceeds approved" if affordability else "Not started")) if started else "Not started", "kind": ("live" if within_approved else "critical") if (started and affordability) else "neutral"},
		{"check": "Plan funding confirmed", "result": ("Confirmed" if funding_current else {"Awaiting confirmation": "Awaiting Finance confirmation", "Returned": "Returned by Finance", "Stale": "Confirmation stale"}.get(version.funding_state, "Not started")) if started else "Not started", "kind": "live" if funding_current else ("attention" if version.funding_state in ("Awaiting confirmation", "Returned", "Stale") else "neutral")},
		{
			"check": "Planned reservation allocation",
			"result": (
				(f"Required {share['required']} · planned {share['qualifying']} · shortfall {share['shortfall']}" if share["basis"]["available"] else "Annual budget basis not available")
				if target else f"{share['qualifying']} planned · target not published"
			),
			"kind": ("live" if share["met"] else "attention") if (target and share["basis"]["available"]) else "advisory",
		},
		{"check": "Contract splitting review", "result": ("No advisory" if not advisories else ("Confirmed" if cstr(version.splitting_confirmation).strip() else f"{len(advisories)} advisory")), "kind": "neutral" if not advisories or cstr(version.splitting_confirmation).strip() else "advisory"},
	]
	if is_county:
		checks.append({"check": "County resident-tenderer reservation", "result": (f"Required {share['county']['required']} · planned {share['county']['qualifying']} · shortfall {share['county']['shortfall']}" if county_target and share["basis"]["available"] else f"{share['county']['qualifying']} planned · county target not published"), "kind": "advisory"})
	return {
		"checks": checks,
		"blockers": blockers,
		"advisories": advisories,
		"reservation": share,
		"reservation_target": target,
		"stage": stage,
		"reference_available": bool(reference.get("available")),
		"affordability": affordability,
		"funding_current": funding_current,
		"within_approved": within_approved,
	}


# --------------------------------------------------------------------------
# GetPlanVersion (PLN-DES-07 / DES-14)
# --------------------------------------------------------------------------


def _item_rows(plan_version: str) -> list[dict[str, Any]]:
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": plan_version, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "item_state", "requirement_type", "procurement_method", "reservation_category", "baseline_delivery_completion_date"],
		order_by="creation asc",
	)
	rows = []
	for item in items:
		allocations = readiness._allocations(item.name)
		value = sum(flt(a.indicative_amount) for a in allocations)
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"item_state": item.item_state,
				"requirement_type": item.requirement_type,
				"procurement_method": cstr(item.procurement_method),
				"reservation_category": cstr(item.reservation_category) or "—",
				"completion_display": _date(item.baseline_delivery_completion_date),
				# §10.1 — Quantity and Unit are separate columns.
				"quantity_number": f"{sum(flt(a.quantity) for a in allocations):g}",
				"unit_label": cstr(allocations[0].unit) if allocations else "",
				"sources": len(allocations),
				"departments": " / ".join(sorted({_ou_label(a_ou) for a_ou in {frappe.db.get_value("Plan Source Allocation", a.name, "organisation_unit") for a in allocations}})),
				"value_display": _money(value),
				"source_correction_required": any(source_correction_required(a.dpp_entry) for a in allocations),
				# §10.6 — the row names the next thing to do to this purchase,
				# never a generic "Review required" badge (§9.4).
				"current_work": _current_work(item, allocations),
				"route": ["procurement-plan-item", item.plan_item_id],
			}
		)
	return rows


#: §9.4 — a readiness finding is concrete missing work, in the words the
#: Planner would use: "Choose a procurement method", never "Complete readiness".
CURRENT_WORK = {
	"PLN_OBJECTIVE_INELIGIBLE": "Choose a strategic objective",
	"PLN_RESERVATION_REQUIRED": "Choose who this procurement is reserved for",
	"PLN_RESERVATION_SHORTFALL": "Review the required reserved allocation",
	"PLN_PLAN_CONTENTS_INCOMPLETE": "Complete the purchase details",
	"PLN_ENTRY_INCOMPLETE": "Complete the purchase details",
	"PLN_SCHEDULE_INVALID": "Review the dates",
	"PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "Review the dates against the departmental deadline",
	"PLN_DELIVERY_PERIOD_REQUIRED": "Enter the expected delivery period",
	"PLN_METHOD_NOT_ADMISSIBLE": "Choose a procurement method that meets the conditions",
	"PLN_METHOD_EVIDENCE_REQUIRED": "Provide the evidence the method requires",
	"PLN_REFERENCE_UNAVAILABLE": "Choose a procurement method",
	"PLN_SOURCE_CORRECTION_REQUIRED": "Rebuild this purchase after a source correction",
}


def _current_work(item, allocations) -> str:
	"""The first thing this purchase still needs, named."""
	if any(source_correction_required(a.dpp_entry) for a in allocations):
		return CURRENT_WORK["PLN_SOURCE_CORRECTION_REQUIRED"]
	if not cstr(item.procurement_method):
		return CURRENT_WORK["PLN_REFERENCE_UNAVAILABLE"]
	if not cstr(item.reservation_category):
		return CURRENT_WORK["PLN_RESERVATION_REQUIRED"]
	if not cstr(item.strategic_objective):
		return CURRENT_WORK["PLN_OBJECTIVE_INELIGIBLE"]
	if not item.baseline_invitation_date:
		return CURRENT_WORK["PLN_SCHEDULE_INVALID"]
	if not cstr(item.estimate_basis).strip():
		return CURRENT_WORK["PLN_PLAN_CONTENTS_INCOMPLETE"]
	return "Ready"


def _waiting_on(version, report, *, can_sign: bool) -> str:
	"""Who the plan is waiting on now, by name where AUTH resolves one."""
	if version.version_status != "Draft" or not report or report["blockers"]:
		return ""
	if not report.get("funding_current"):
		return ""
	if can_sign:
		# This actor holds the action; the button says the rest.
		return ""
	holders = authz.users_with_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	if not holders:
		return (
			"Ready for the Head of Procurement Function to sign and submit. "
			"No one currently holds that responsibility — ask your KenTender administrator."
		)
	names = " / ".join(sorted(cstr(frappe.db.get_value("User", u, "full_name") or u) for u in holders))
	return f"Ready for the Head of Procurement Function to sign and submit · {names}"


def _preview(text: str, *, limit: int = 90) -> str:
	"""A faithful short preview: never a truncation mid-word, and never a
	summary that changes the meaning (§9.3.7)."""
	text = cstr(text).strip()
	if len(text) <= limit:
		return text
	cut = text[:limit].rsplit(" ", 1)[0]
	return f"{cut}…"


def _acceptance_history(fiscal_year: str) -> list[str]:
	"""Who accepted each departmental plan, and when — the provenance of the
	sources this plan is built from."""
	lines = []
	for task in frappe.get_all(
		"Departmental Plan Validation Task",
		filters={"fiscal_year": fiscal_year, "status": "Completed"},
		fields=["organisation_unit", "decision"],
		order_by="creation asc",
		limit_page_length=0,
	):
		decision = frappe.db.get_value(
			"Departmental Plan Validation Decision", task.decision, ["actor", "decided_at", "decision"], as_dict=True
		)
		if not decision or decision.decision != "Accept departmental plan":
			continue
		actor = cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor)
		lines.append(f"{_ou_label(task.organisation_unit)} acceptance: {actor}, {_eat(decision.decided_at)}")
	return lines


def _plan_checks(version, plan, report) -> list[dict[str, Any]]:
	"""Funding, Reserved procurement and Schedule, each as one current result
	with a link to the exact correction when it fails."""
	blockers = report["blockers"]
	codes = {b["code"] for b in blockers}
	plan_route = ["annual-procurement-plan", plan.plan_reference]

	funding_state = cstr(version.funding_state)
	funding = {
		"Not requested": "Not yet checked",
		"Awaiting confirmation": "Finance is reviewing the funding",
		"Confirmed": "Within each approved budget line",
		"Returned": "Returned by Finance",
		"Stale": "Funding needs to be checked again",
	}.get(funding_state, funding_state)

	reservation = next((b for b in blockers if b["code"] in ("PLN_RESERVATION_SHORTFALL", "PLN_REFERENCE_UNAVAILABLE") and b.get("field") == "reservation_category"), None)
	shortfall = next((b for b in blockers if b["code"] == "PLN_RESERVATION_SHORTFALL"), None)
	if shortfall:
		reservation_result = f"{_money(flt(shortfall.get('shortfall') or 0))} more qualifying allocation required"
		reservation_kind = "critical"
	elif reservation:
		reservation_result = "The reserved-procurement rule or budget basis is missing"
		reservation_kind = "critical"
	else:
		reservation_result = "Required allocation met"
		reservation_kind = "live"

	schedule_failing = [b["plan_item_id"] for b in blockers if b["code"] in ("PLN_SCHEDULE_INVALID", "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", "PLN_DELIVERY_PERIOD_REQUIRED") and b.get("plan_item_id")]
	if schedule_failing:
		schedule_result = f"{len(schedule_failing)} purchase{'s do' if len(schedule_failing) != 1 else ' does'} not meet its departmental deadline"
		schedule_kind = "critical"
	else:
		schedule_result = "All purchases meet their departmental deadlines"
		schedule_kind = "live"

	return [
		{"label": "Funding", "result": funding, "kind": "live" if funding_state == "Confirmed" else "neutral", "route": None},
		{
			"label": "Reserved procurement", "result": reservation_result, "kind": reservation_kind,
			"action": "Review reserved procurement" if reservation_kind == "critical" else "",
			"route": plan_route if reservation_kind == "critical" else None,
		},
		{"label": "Schedule", "result": schedule_result, "kind": schedule_kind, "route": None},
	]


def _signature_summary(version) -> dict[str, Any] | None:
	if not version.preparation_signature:
		return None
	row = frappe.db.get_value("Plan Preparation Signature", version.preparation_signature, ["actor", "capacity", "signed_at", "submitted_snapshot_id", "snapshot_hash"], as_dict=True)
	if not row:
		return None
	return {"actor": row.actor, "actor_name": cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor), "capacity": row.capacity, "signed_at": cstr(row.signed_at), "signed_at_display": _eat(row.signed_at), "submitted_snapshot_id": row.submitted_snapshot_id, "snapshot_hash": row.snapshot_hash}


def _open_task_for(actor: str, version) -> dict[str, Any] | None:
	"""FU-14 — the viewing actor's own open task on this Version, so the record
	route is never a dead end for its decider. Same authority as the workspace."""
	if authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor) and not authz.is_segregated(
		actor, authz.ACTION_FINANCE_DECIDE, plan_version=version.name
	):
		task = frappe.db.get_value("Plan Finance Task", {"plan_version": version.name, "status": "Open"}, "name")
		if task:
			return {"label": "Open Finance task", "route": [PAGE, "finance", task]}
	for stage, role, action in (
		("Accounting Officer adoption", ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE),
		("Statutory approval", ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE),
	):
		if not authz.has_site_role(role, actor) or authz.is_segregated(actor, action, plan_version=version.name):
			continue
		task = frappe.db.get_value("Plan Governance Task", {"plan_version": version.name, "stage": stage, "status": "Open"}, "name")
		if task:
			return {"label": "Open decision", "route": [PAGE, "review", task]}
	return None


def _version_allocation_totals(plan_version: str) -> tuple[set[str], float, float]:
	rows = frappe.get_all(
		"Plan Source Allocation", filters={"plan_version": plan_version, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["dpp_entry", "quantity", "indicative_amount"],
	)
	return {r.dpp_entry for r in rows}, sum(flt(r.quantity) for r in rows), sum(flt(r.indicative_amount) for r in rows)


def _version_changes(version) -> dict[str, Any]:
	"""U07-changes/U07-changes-update — the Version's own `change_reason`
	(§4.5) against its predecessor's source set, quantities and value. Not a
	literal per-field diff (neither Version stores a "description" field to
	compare): the Planner's own narrative is the record of *why*; this is
	the record of *what actually moved* underneath it, computed fresh from
	the live allocations rather than any frozen snapshot (a still-Draft
	successor has not frozen `source_cohort` yet)."""
	if not version.based_on_version:
		return {"is_initial": True}
	before_set, before_qty, before_value = _version_allocation_totals(version.based_on_version)
	after_set, after_qty, after_value = _version_allocation_totals(version.name)
	return {
		"is_initial": False,
		"based_on_version_number": frappe.db.get_value("Annual Plan Version", version.based_on_version, "version_number"),
		"change_reason": cstr(version.change_reason),
		"source_set_changed": before_set != after_set,
		"quantities_changed": before_qty != after_qty,
		"value_changed": before_value != after_value,
	}


def get_annual_plan(*, plan_reference: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	plan = _plan_root(plan_reference)
	authz.require_site_read(PLAN_READERS, actor)
	can_act = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	version = _open_version(plan)
	can_sign = authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor) and version.version_status == "Draft"

	all_accepted = _accepted_entry_rows(plan.fiscal_year)
	allocated_ids = _allocated_dpp_entries(version.name)
	unallocated = [row for row in all_accepted if row["dpp_entry"] not in allocated_ids]
	items = _item_rows(version.name)
	item_value = sum(flt(a.indicative_amount) for a in frappe.get_all("Plan Source Allocation", filters={"plan_version": version.name, "allocation_state": ("in", ("Draft", "Active"))}, fields=["indicative_amount"]))
	readiness_report = plan_readiness(version, plan) if version.version_status == "Draft" else None
	mutable = version.version_status == "Draft" and can_act and version.funding_state != "Awaiting confirmation"
	no_blockers = bool(readiness_report) and not readiness_report["blockers"]
	share = readiness_report["reservation"] if readiness_report else readiness.reservation_allocations(version.name, plan.fiscal_year)
	target = share["target_percent"]
	return {
		"outcome": "OK",
		"plan_reference": plan.plan_reference,
		"version_reference": version.name,
		"version_status": version.version_status,
		"version_number": version.version_number,
		"funding_state": version.funding_state,
		"record_version": int(version.record_version or 0),
		"fiscal_year": plan.fiscal_year,
		"header": {
			"eyebrow": "ANNUAL PROCUREMENT PLAN",
			"title": plan.title,
			"reference_line": f"{plan.plan_reference} · Version {version.version_number}",
			"badge": version.version_status,
		},
		"mutable": mutable,
		"can_act": can_act,
		"open_task": _open_task_for(actor, version),
		"is_correction": bool(version.correction_of_plan_version),
		"is_successor": bool(version.based_on_version),
		"has_open_successor": bool(plan.open_successor_version),
		"summary": {
			"accepted_entries": len(all_accepted),
			"allocated": len(all_accepted) - len(unallocated),
			"plan_items": len(items),
			"value_display": _money(item_value),
			"reserved_share_display": (f"{share['qualifying']} planned reservation · required {share['required']}" if (target and share["basis"]["available"]) else f"{share['qualifying']} planned reservation"),
			"reservation": share,
			# U07-overview's own strip: the same accepted-entry count under its
			# own label, plus how many departments they come from.
			"departmental_sources": len(all_accepted),
			"departments": len({row["organisation_unit"] for row in all_accepted}),
			"funding_evidence_state": version.funding_state,
		},
		"project_name": cstr(version.project_name),
		"change_reason": cstr(version.change_reason),
		"changes": _version_changes(version),
		"unallocated_sources": unallocated,
		"unallocated_caption": f"{len(unallocated)} entr{'y' if len(unallocated) == 1 else 'ies'} available" if unallocated else "",
		# §10.6 — the departmental acceptances behind this plan, as history.
		"history_lines": _acceptance_history(plan.fiscal_year),
		"current_version_number": int(
			frappe.db.get_value("Annual Plan Version", plan.active_version, "version_number") or 0
		) if plan.active_version else None,
		"plan_items": items,
		"readiness": readiness_report["checks"] if readiness_report else [],
		# §10.6 — three named results, only the ones that decide the next
		# action. The line comparisons and the reservation arithmetic stay in
		# their own detail, not on the preparation page (PLN22-CHG-005).
		"plan_checks": _plan_checks(version, plan, readiness_report) if readiness_report else [],
		"blockers": readiness_report["blockers"] if readiness_report else [],
		"splitting_advisories": readiness_report["advisories"] if readiness_report else [],
		"splitting_confirmation": cstr(version.splitting_confirmation),
		"can_request_funding": (
			(mutable and no_blockers and not unallocated and version.funding_state in ("Not requested", "Returned", "Stale"))
			or (version.version_status == "Active" and can_act and version.funding_state in ("Stale", "Returned"))  # §5.3.4 reassessment
		),
		"funding_evidence": _funding_evidence(version),
		# U07-funding's own Budget table — the per-line Approved/Planned/
		# Reserved/Committed/Available breakdown already computed for the
		# affordability gate, exposed here for direct display.
		"affordability": readiness_report["affordability"] if readiness_report else None,
		# v1.18 §6.2 — **Sign and submit Annual Plan** belongs to the Head of Procurement Function
		"can_submit": can_sign and no_blockers and not unallocated and bool(readiness_report and readiness_report["funding_current"]),
		"can_sign_and_submit": can_sign and no_blockers and not unallocated and bool(readiness_report and readiness_report["funding_current"]),
		# §10.6 U07-UPDATE — only the Planner, only on an open successor.
		"can_cancel_update": bool(can_act and version.based_on_version and version.version_status == "Draft"),
		# §10.6 U07-FINANCE-COMPLETE / §6.5 — name the actual responsible
		# person rather than offering the Planner a handover control they do
		# not hold. Where no person resolves, name the role (§6.5).
		"waiting_on": _waiting_on(version, readiness_report, can_sign=can_sign),
		"preparation_signature": _signature_summary(version),
		"late_activation_required": bool(frappe.db.get_value("Fiscal Year", plan.fiscal_year, "year_start_date") and frappe.utils.getdate(frappe.utils.nowdate()) >= frappe.utils.getdate(frappe.db.get_value("Fiscal Year", plan.fiscal_year, "year_start_date"))),
		"latest_publication": _latest_publication(version.name),
		"active_view": _active_view(version, plan) if version.version_status == "Active" else None,
	}


def _decision_line(version_name: str, stage: str) -> str:
	task = frappe.db.get_value("Plan Governance Task", {"plan_version": version_name, "stage": stage}, "decision")
	if not task:
		return ""
	row = frappe.db.get_value("Plan Governance Decision", task, ["actor", "capacity", "decided_at"], as_dict=True)
	if not row:
		return ""
	who = cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor)
	label = row.capacity if stage == "Statutory approval" else who
	return f"{label} · {_eat(row.decided_at)}"


def _active_view(version, plan) -> dict[str, Any]:
	"""PLN-UI-14 — the Active Plan (PLN-DES-14): items with their
	Requisition-availability projection, the schedule card and the
	governance card."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	objectives = {row["id"]: row["title"] for row in strategy_gateway.list_eligible_strategic_objectives()}
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": "Active"},
		fields=["name", "plan_item_id", "title", "requirement_type", "procurement_method", "strategic_objective", "baseline_delivery_completion_date", "record_version", *schedule.BASELINE_FIELDS],
		order_by="creation asc",
	)
	rows = []
	departments = set()
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation", filters={"plan_item": item.name, "allocation_state": "Active"},
			fields=["name", "organisation_unit", "source_origin", "quantity", "unit", "indicative_amount"],
		)
		drawn = _drawn(allocations)
		departments |= {a.organisation_unit for a in allocations}
		origins = {a.source_origin for a in allocations}
		total_qty = sum(flt(a.quantity) for a in allocations)
		unit_label = _unit_label(allocations[0].unit) if allocations else ""
		value = sum(flt(a.indicative_amount) for a in allocations)
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"department": " / ".join(sorted({_ou_label(ou) for ou in {a.organisation_unit for a in allocations}})),
				"source_origin": next(iter(origins)) if len(origins) == 1 else "Multiple",
				"strategic_objective_label": objectives.get(cstr(item.strategic_objective)) or cstr(frappe.db.get_value("Strategy Node", item.strategic_objective, "title") or ""),
				"procurement_method": cstr(item.procurement_method),
				"completion_display": _date(item.baseline_delivery_completion_date),
				"value_display": _money(value),
				"requisition_availability_display": f"{total_qty - drawn[0]:g} {unit_label.lower()} · {_money(value - drawn[1])}".strip(),
				"record_version": int(item.record_version or 0),
				"route": ["procurement-plan-item", item.plan_item_id],
			}
		)
	item_value = sum(flt(a.indicative_amount) for a in frappe.get_all("Plan Source Allocation", filters={"plan_version": version.name, "allocation_state": "Active"}, fields=["indicative_amount"]))
	publication = frappe.db.get_value(
		"Plan Publication", {"plan_version": version.name, "publication_state": "Acknowledged"}, ["name", "acknowledged_at", "external_reference"], as_dict=True,
	)
	return {
		"summary": {
			"plan_items": len(rows),
			"value_display": _money(item_value),
			"departments": len(departments),
			"activated_display": _eat(version.activated_at),
		},
		"items": rows,
		"governance_card": {
			"ao_adoption_line": _decision_line(version.name, "Accounting Officer adoption"),
			"statutory_approval_line": _decision_line(version.name, "Statutory approval"),
			"publication_line": f"Acknowledged · {_eat(publication.acknowledged_at)}" if publication else "",
			"publication": publication.name if publication else "",
			"publication_route": [PAGE, "publication", publication.name] if publication else None,
		},
	}


def _latest_publication(version_name: str) -> dict[str, Any] | None:
	row = frappe.db.get_value("Plan Publication", {"plan_version": version_name}, ["name", "publication_state"], as_dict=True)
	if not row:
		return None
	attempt_number = frappe.db.count("Publication Attempt", {"publication": row.name})
	# §9.6 "Confirmed unpublished with material defect: Publication on hold;
	# approved content retained" is a workspace-level label, not only a fact
	# on the drill-in publication screen (`get_publication_task`) — a hold
	# never changes `publication_state` itself (§5.5.2.3: "a hold is not a
	# withdrawal"), so surface it here as its own field.
	hold = frappe.db.get_value("Plan Publication Hold", {"plan_version": version_name, "hold_state": "Active"}, ["hold_kind", "reason"], as_dict=True)
	return {
		"publication": row.name, "result": row.publication_state, "attempt_number": attempt_number, "route": [PAGE, "publication", row.name],
		"held": bool(hold), "hold_kind": hold.hold_kind if hold else "", "hold_reason": hold.reason if hold else "",
	}


def _drawn(allocations: list) -> tuple[float, float]:
	names = [a.name for a in allocations]
	if not names:
		return 0.0, 0.0
	rows = frappe.get_all("Plan Drawdown Reference", filters={"allocation": ("in", names), "drawdown_state": "Active"}, fields=["quantity", "amount"])
	return sum(flt(r.quantity) for r in rows), sum(flt(r.amount) for r in rows)


# --------------------------------------------------------------------------
# GetPlanItem (PLN-DES-09 / 09A)
# --------------------------------------------------------------------------


def get_plan_item(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import strategy_gateway

	actor = authz.actor(user)
	name = resolve_item_doc_name(plan_item_id)
	item = frappe.get_doc("Annual Plan Item", name)
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	authz.require_site_read(PLAN_READERS, actor)
	can_act = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	reference = readiness.reference_for(plan.fiscal_year)
	labels = _line_labels(plan.fiscal_year)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["name", "dpp_entry", "source_origin", "need", "need_revision", "organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount"],
		order_by="creation asc",
	)
	sources, value, correction_required = [], 0.0, False
	for allocation in allocations:
		value += flt(allocation.indicative_amount)
		if source_correction_required(allocation.dpp_entry):
			correction_required = True
		entry_title = cstr(frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "title"))
		dpp_version = frappe.db.get_value("Departmental Plan Entry", allocation.dpp_entry, "dpp_version")
		dpp_root = frappe.db.get_value("Departmental Plan Version", dpp_version, "departmental_plan")
		dpp_reference = cstr(frappe.db.get_value("Departmental Plan", dpp_root, "dpp_reference"))
		dpp_version_number = frappe.db.get_value("Departmental Plan Version", dpp_version, "version_number")
		line = labels.get(cstr(allocation.budget_line), {})
		sources.append(
			{
				"requirement": entry_title,
				"department": _ou_label(allocation.organisation_unit),
				"source_origin": allocation.source_origin,
				"departmental_plan_line": f"{dpp_reference} · Submission {dpp_version_number}",
				# §10.8 "View classification details" opens the accepted
				# classification evidence for this exact source.
				"dpp_submission": cstr(
					frappe.db.get_value("Departmental Plan Submission", {"dpp_version": dpp_version}, "name")
				) if dpp_version else "",
				"need_reference_line": f"{allocation.need} · Revision {needs_intake.need_revision_number(allocation.need_revision)}" if allocation.need else "",
				"quantity_display": _quantity_display(allocation.quantity, allocation.unit),
				"quantity_number": f"{flt(allocation.quantity):g}",
				"unit_label": _unit_label(allocation.unit),
				"required_by_display": _date(allocation.required_by_date),
				"budget_line": allocation.budget_line,
				"budget_line_display": line.get("label") or cstr(allocation.budget_line),
				"amount_display": _money(allocation.indicative_amount),
			}
		)

	from kentender_procurement.procurement_planning.services import profiles, scope_lock

	objectives = strategy_gateway.list_eligible_strategic_objectives()
	objective_eligible = (not item.strategic_objective) or any(row["id"] == item.strategic_objective for row in objectives)
	category = cstr(item.procurement_category) or "Services"
	resolved = readiness.method_profile_for(item, plan.fiscal_year)
	method_profile, schedule_profile = resolved["method"], resolved["schedule"]
	if version.version_status != "Draft":
		# submitted content reads its frozen rule-profile evidence
		method_profile = profiles.method_profile_by_name(cstr(item.method_profile_version)) if item.method_profile_version else method_profile
		schedule_profile = profiles.schedule_profile_by_name(cstr(item.schedule_profile_version)) if item.schedule_profile_version else schedule_profile
	conditions = profiles.method_conditions(method_profile, procurement_category=category, planned_value=value, evidence_rows=readiness.item_evidence(item))
	applicable_on = profiles.applicability_date(item.baseline_invitation_date, plan.fiscal_year)
	admissible = profiles.admissible_methods(procurement_category=category, planned_value=value, applicability_date=applicable_on)
	categories = readiness.reservation_categories(reference)
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	blockers = readiness.item_blockers(item, allocations, plan.fiscal_year, objective_eligible=objective_eligible, stage="submission") if version.version_status == "Draft" else []
	price_index = reference.get("market_price_index", {})
	price_rows = [r for r in price_index.get("rows", []) if r.get("procurement_category") == cstr(item.procurement_category)] if price_index.get("published") else []
	period_inputs = readiness.item_period_inputs(item)
	periods = {f: int(period_inputs.get(f) or 0) for f in schedule.PERIOD_FIELDS}
	rules = profiles.period_rules(schedule_profile)
	defaults = {f: (rules[f].get("default_days") if f in rules else None) for f in schedule.PERIOD_FIELDS}
	delivery_days = readiness.item_delivery_days(item)
	baseline_map = {f: item.get(f) for f in schedule.BASELINE_FIELDS}
	lock = scope_lock.status(item.plan_item_id)
	# §9.7's own domain-specific copy for these two passive states — computed
	# here (not by the client) so every screen that reads this item shows the
	# identical wording; `notices` is empty (never both messages compete —
	# a locked item's own existing scope keeps drawing regardless of a hold).
	notices = []
	if lock["locked"]:
		notices.append(
			{
				"kind": "scope_locked",
				"heading": "Additional requirements need a separate Plan Item",
				"text": "This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.",
			}
		)
	if lock["held"]:
		notices.append(
			{
				"kind": "correction_hold",
				"heading": "New Requisition authorisations are on hold",
				"text": "An unresolved correction request affects this Plan Item. Existing authorised proceedings are unchanged.",
			}
		)
	combined = len(sources) > 1
	mutable = item.item_state == "Draft" and version.version_status == "Draft" and can_act and version.funding_state != "Awaiting confirmation"
	total_quantity_display = _quantity_display(sum(flt(a.quantity) for a in allocations), allocations[0].unit) if allocations else "—"
	return {
		"outcome": "OK",
		"plan_item_id": item.plan_item_id,
		"record_version": int(item.record_version or 0),
		"mutable": mutable,
		"can_act": can_act,
		"combined": combined,
		"is_active": version.version_status == "Active" and item.item_state == "Active",
		"source_correction_required": correction_required,
		"header": {
			"eyebrow": "PLAN ITEM",
			"title": item.title,
			"reference_line": f"{item.plan_item_id} · {version.version_status} Version {version.version_number}",
			"item_state_badge": {"Draft": "Proposed"}.get(item.item_state, item.item_state),
		},
		"plan_reference": plan.plan_reference,
		# §10.8 — one compact read-only summary under the editable fields.
		# Quantity, unit and the required date are derived from the included
		# requirements; Plan horizon is a fixed literal and is not displayed.
		"summary_line": " · ".join(
			part for part in (
				cstr(item.procurement_category),
				total_quantity_display if allocations else "",
				f"Required by {_date(item.baseline_delivery_completion_date)}" if item.baseline_delivery_completion_date else "",
			) if part and part != "—"
		),
		# §10.8 — a blocking configuration problem is one plain issue and its
		# recovery owner, never a resolver status field (PLN22-AC-005).
		"method_issue": (
			f"{cstr(item.procurement_method)} cannot be confirmed until the applicable method rule is verified in System setup."
			if cstr(item.procurement_method) and not method_profile.get("found") else ""
		),
		# §9.3.7 — a long reason leads with a faithful short preview and an
		# adjacent disclosure; the full governed text stays available.
		"aggregation_reason_preview": _preview(cstr(item.aggregation_reason)),
		"estimate_basis_preview": _preview(cstr(item.estimate_basis)),
		"sources": sources,
		"sources_caption": f"{len(sources)} sources · {sum(flt(a.quantity) for a in allocations):g} {_unit_label(allocations[0].unit).lower()} · {_money(value)}" if combined else "",
		"planned_value_display": _money(value),
		"total_quantity_display": total_quantity_display,
		"identity": {
			"title": item.title,
			"description": item.description,
			"requirement_type": item.requirement_type,
			"procurement_category": cstr(item.procurement_category),
			"aggregation_reason": cstr(item.aggregation_reason),
		},
		"scope_lock": lock,
		"notices": notices,
		"classification": {
			"strategic_objective": cstr(item.strategic_objective),
			"objective_path": cstr(item.objective_path),
			"objective_eligible": objective_eligible,
			"strategic_objectives": objectives,
			"procurement_method": cstr(item.procurement_method),
			"admissible_methods": admissible,
			"proposed_method": readiness.OPEN_TENDER if readiness.OPEN_TENDER in admissible else (admissible[0] if admissible else ""),
			"value_band": (
				f"{method_profile.get('profile')} · {method_profile.get('verification_status')}" if method_profile.get("found")
				else ("No eligibility profile in force for this method on the applicable date" if cstr(item.procurement_method) else "")
			),
			"reference_available": bool(method_profile.get("found")),
			"method_profile": {
				"found": bool(method_profile.get("found")),
				"profile": cstr(method_profile.get("profile")),
				"version_number": method_profile.get("version_number"),
				"verification_status": cstr(method_profile.get("verification_status")),
				"applicability_date": cstr(applicable_on),
				"conditions": conditions["results"],
				"admissible": conditions["admissible"],
				"evidence_complete": conditions["evidence_complete"],
				"missing_evidence": conditions["missing_evidence"],
			},
			"method_condition_evidence": readiness.item_evidence(item),
			"estimate_basis": cstr(item.estimate_basis),
			"estimate_basis_reference": cstr(item.estimate_basis_reference),
		},
		"preference": {
			"reservation_category": cstr(item.reservation_category),
			"reservation_categories": [c["category"] for c in categories],
			"county_resident_reservation": bool(item.county_resident_reservation),
			"county_control_available": is_county,
			"plan_horizon": cstr(item.plan_horizon),
			"aggregation_indicator": cstr(item.aggregation_indicator),
			"lotting_indicator": cstr(item.lotting_indicator),
			"lot_count": int(item.lot_count or 0),
			"helper": "The planned designation from the governed catalogue. Choose None where no designation applies; candidate entitlement is assessed downstream.",
			# no restriction-computation mechanism exists yet this cycle — a
			# static line, matching the spec's own "read-only example text".
			"mandatory_restrictions_line": "No additional restriction applies",
		},
		"baseline": {
			"target_invitation_date": cstr(item.baseline_invitation_date),
			"periods": periods,
			"period_inputs": period_inputs,
			"defaults": defaults,
			"using_defaults": all(periods[f] == (defaults[f] or 0) for f in schedule.PERIOD_FIELDS),
			"defaults_line": (f"Profile {schedule_profile.get('profile')} · {schedule_profile.get('verification_status')}" if schedule_profile.get("found") else "No procedure schedule profile in force for this method and category — Draft only; submission is blocked"),
			"floors": {k: r["minimum_days"] for k, r in rules.items() if r.get("minimum_days") is not None},
			"ceilings": {k: r["maximum_days"] for k, r in rules.items() if r.get("maximum_days") is not None},
			"profile": {
				"found": bool(schedule_profile.get("found")),
				"profile": cstr(schedule_profile.get("profile")),
				"version_number": schedule_profile.get("version_number"),
				"verification_status": cstr(schedule_profile.get("verification_status")),
				"complete": bool(schedule_profile.get("complete")),
				"gaps": schedule_profile.get("gaps", []),
				"counting_rule": cstr(schedule_profile.get("counting_rule")),
				"milestones": schedule_profile.get("milestones", []),
			},
			"estimated_delivery_period_days": delivery_days,
			"estimated_completion_date": cstr(item.estimated_completion_date),
			"estimated_completion_display": _date(item.estimated_completion_date),
			"rows": [
				{"milestone": m, "label": schedule.MILESTONE_LABELS[m], "date": cstr(item.get(f"baseline_{m}_date")), "date_display": _date(item.get(f"baseline_{m}_date")) if item.get(f"baseline_{m}_date") else ("Not applicable" if (schedule_profile.get("found") and m not in profiles.applicable_milestones(schedule_profile)) else "—"), "applies": (not schedule_profile.get("found")) or m in profiles.applicable_milestones(schedule_profile), "from_requisition": False, "source_boundary": m == "delivery_completion"}
				for m in schedule.MILESTONES
			],
			"delivery_boundary_ok": schedule.delivery_boundary_ok(baseline_map, delivery_days),
			"locked": version.version_status != "Draft",
		},
		"market_price_index": {"published": bool(price_rows), "rows": price_rows, "helper": "Market price index: not published for this category." if not price_rows else ""},
		"blockers": blockers,
	}


# --------------------------------------------------------------------------
# GetFinanceTask (PLN-DES-10)
# --------------------------------------------------------------------------


def _funding_evidence(version) -> dict[str, Any]:
	"""§5.3.4 — readers distinguish **Funding evidence at approval** from
	**Current funding confirmation**; a reassessment appends, never rewrites."""
	from kentender_procurement.procurement_planning.services import financial_basis, plan_finance

	chain = authz.evidence_chain(version.name) or [version.name]
	tasks = frappe.get_all("Plan Finance Task", filters={"plan_version": ("in", chain)}, pluck="name")
	decisions = frappe.get_all(
		"Plan Finance Decision", filters={"task": ("in", tasks or ("",)), "decision": "Confirm plan funding"},
		fields=["name", "decision_reference", "decided_at", "task"], order_by="decided_at asc",
	) if tasks else []

	def _row(decision):
		if not decision:
			return None
		basis = financial_basis.basis_of_decision(frappe._dict(task=decision.task))
		actor = frappe.db.get_value("Plan Finance Decision", decision.name, "actor")
		return {
			"decision": decision.decision_reference, "decided_at": cstr(decision.decided_at), "decided_at_display": _eat(decision.decided_at),
			"actor": actor, "actor_name": cstr(frappe.db.get_value("User", actor, "full_name") or actor) if actor else "",
			"basis_digest": cstr(basis.basis_digest) if basis else "", "planned_total": financial_basis.summary(basis).get("planned_total", "") if basis else "",
		}

	at_approval = None
	if version.submitted_at:
		before = [d for d in decisions if d.decided_at and d.decided_at <= version.submitted_at]
		at_approval = _row(before[-1]) if before else None
	current = _row(decisions[-1]) if decisions else None
	reuse = frappe.get_all("Plan Finance Basis Reuse", filters={"plan_version": version.name}, fields=["name", "earlier_decision", "validated_at"], order_by="validated_at desc", limit=1)
	return {
		"state": version.funding_state,
		"current": bool(current) and plan_finance.funding_is_current(version),
		"at_approval": at_approval,
		"current_confirmation": current,
		"reuse": {"earlier_decision": frappe.db.get_value("Plan Finance Decision", reuse[0].earlier_decision, "decision_reference"), "validated_at": _eat(reuse[0].validated_at)} if reuse else None,
		"open_review": frappe.db.get_value("Plan Finance Task", {"plan_version": version.name, "status": "Open"}, "task_reference") or "",
	}


_DECISION_OUTCOME_LABELS = {"Confirm plan funding": "Confirmed", "Return to planner": "Returned"}


def _finance_history(version) -> list[dict[str, Any]]:
	"""U10-history — every review attempt in order; a later Review's own
	outcome never overwrites an earlier one's."""
	from kentender_procurement.procurement_planning.services import financial_basis

	chain = authz.evidence_chain(version.name) or [version.name]
	tasks = frappe.get_all(
		"Plan Finance Task", filters={"plan_version": ("in", chain)},
		fields=["name", "task_reference", "status", "decision", "financial_basis"],
		order_by="creation asc",
	)
	rows = []
	for idx, task in enumerate(tasks, start=1):
		basis = frappe.get_doc(financial_basis.DOCTYPE, task.financial_basis) if task.financial_basis else None
		budget_version = _budget_version_display(basis)
		basis_line = budget_version or ("Current revised Budget basis" if idx > 1 else "")
		if task.decision:
			decision = frappe.get_doc("Plan Finance Decision", task.decision)
			rows.append(
				{
					"review": f"Review {idx}",
					"basis": basis_line,
					"outcome": _DECISION_OUTCOME_LABELS.get(decision.decision, decision.decision),
					"actor": cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor),
					"time_display": _date(decision.decided_at),
				}
			)
		else:
			rows.append({"review": f"Review {idx}", "basis": basis_line, "outcome": "Awaiting confirmation", "actor": "—", "time_display": "—"})
	return rows


def _budget_version_display(basis) -> str:
	from kentender_procurement.procurement_planning.services import financial_basis

	if not basis:
		return ""
	rows = financial_basis.lines_of(basis)
	if not rows:
		return ""
	line_version = rows[0].get("line_version")
	budget_version = frappe.db.get_value("Procurement Budget Line Version", line_version, "budget_version") if line_version else None
	if not budget_version:
		return ""
	reference, version_number = frappe.db.get_value("Procurement Budget Version", budget_version, ["generated_reference", "version_number"]) or (None, None)
	return f"{reference}, Version {version_number}" if reference else ""


def _affordability_rows(statement: dict[str, Any]) -> list[dict[str, Any]]:
	"""The per-Budget-Line Approved/Planned/Reserved/Committed/Available
	breakdown — shared by `GetFinanceTask` (PLN-DES-10) and the Review
	screen's own Funding section (U11-checks)."""
	return [
		{
			"budget_line": line["budget_line"],
			"budget_line_label": f"{line.get('reference') or line['budget_line']} — {line.get('title')}" if line.get("title") else (line.get("reference") or line["budget_line"]),
			# §10.9 — the first view is Budget line, Line name, Approved,
			# Planned, Difference and Result. Reference and name are separate
			# columns, and the difference is stated rather than left to be
			# worked out from two figures.
			"budget_line_reference": cstr(line.get("reference") or line["budget_line"]),
			"line_name": cstr(line.get("title")),
			"difference_display": _money(flt(line.get("approved")) - flt(line.get("planned"))),
			"result": "Within budget" if line.get("within_approved") else "Exceeds approved amount",
			"result_kind": "live" if line.get("within_approved") else "critical",
			"funding_source": cstr(line.get("funding_source")) or "—",
			"approved_display": _money(line.get("approved")),
			"planned_display": _money(line.get("planned")),
			"within_approved": bool(line.get("within_approved")),
			"within_approved_display": "Yes" if line.get("within_approved") else "No",
			"reserved_display": _money(line.get("reserved")),
			"committed_display": _money(line.get("committed")),
			"available_display": _money(line.get("available")),
			"within_available": bool(line.get("within_available")),
			"excess_display": _money(line.get("excess_over_approved")) if not line.get("within_approved") else "",
		}
		for line in statement.get("lines", [])
	]


def get_finance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	actor = authz.actor(user)
	if not task or not frappe.db.exists("Plan Finance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Finance Task", task)
	authz.require_site_read((ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_PROCUREMENT_PLANNER, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR), actor)
	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	decided = task_doc.status != "Open"
	from kentender_procurement.procurement_planning.services import financial_basis

	statement = json.loads(task_doc.affordability_statement or "{}") if decided else plan_finance.affordability_statement(plan, version)
	if decided and task_doc.decision:
		decision_statement = frappe.db.get_value("Plan Finance Decision", task_doc.decision, "affordability_statement")
		if decision_statement:
			statement = json.loads(decision_statement)
	basis = frappe.get_doc(financial_basis.DOCTYPE, task_doc.financial_basis) if task_doc.financial_basis else None
	totals = readiness.line_totals(version.name)
	used = [line for line in statement.get("lines", []) if flt(line.get("planned")) > 0]
	items = frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("!=", "Dissolved")})
	share = readiness.reservation_allocations(version.name, plan.fiscal_year)
	target = share["target_percent"]
	within_approved = bool(statement.get("within_approved"))
	within_available = bool(statement.get("within_available"))
	can_decide = authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor) and not decided and not authz.is_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=version.name)
	rows = _affordability_rows(statement)
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"decided": decided,
		"can_decide": can_decide,
		"can_confirm": can_decide and within_approved,
		"header": {
			"eyebrow": "PLAN FUNDING CONFIRMATION",
			"title": plan.title,
			"reference_line": f"{task_doc.task_reference} · {plan.plan_reference} · Version {version.version_number}",
			"badge": "Awaiting Finance" if task_doc.status == "Open" else task_doc.status,
		},
		"summary": {
			"plan_items": items,
			"value_display": _money(sum(totals.values())),
			"lines_used": len(used),
			"reserved_share_display": (f"{share['qualifying']} planned reservation · required {share['required']}" if (target and share["basis"]["available"]) else f"{share['qualifying']} planned reservation"),
		},
		"as_at_display": _eat(statement.get("as_at")),
		"lines": rows,
		"within_approved": within_approved,
		"within_available": within_available,
		"notice": (
			{"kind": "live", "text": "The consolidated plan is within the approved budget on every Procurement Budget Line."}
			if within_approved
			else {"kind": "critical", "text": "The planned total exceeds the approved amount on one or more Procurement Budget Lines. Return the plan to the Planner."}
		),
		"advisory": None if within_available else {"kind": "advisory", "text": "The planned total exceeds the currently available amount on at least one line. Planning and drawdown run on different horizons; this blocks nothing."},
		"quiet_line": "Confirmation records that this plan fits the approved budget. It reserves no funds; reservation happens at requisition.",
		"failing_lines": statement.get("failing_lines", []),
		# v1.18 §4.7 — the immutable basis this review decides on
		"financial_basis": financial_basis.summary(basis),
		"basis_current": (financial_basis.current_digest(plan, version) == cstr(basis.basis_digest)) if (basis and not decided) else None,
		"is_reassessment": version.version_status == "Active",
		"version_status": version.version_status,
		"version_number": version.version_number,
		"history": _finance_history(version),
		"funding_evidence": _funding_evidence(version),
	}


# --------------------------------------------------------------------------
# GetPlanGovernanceTask (PLN-DES-11/12) / GetSourceEvidence (PLN-DES-12)
# --------------------------------------------------------------------------


def _governance_sources(version, plan) -> list[dict[str, Any]]:
	"""U11 Sources — every current allocation across the Version's Plan
	Items, each carrying its own `source_key` for a U12 drill-in link."""
	items = {
		i.name: i
		for i in frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")}, fields=["name", "plan_item_id", "title"])
	}
	labels = _line_labels(plan.fiscal_year)
	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_version": version.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["plan_item", "source_key", "source_origin", "organisation_unit", "quantity", "unit", "budget_line", "indicative_amount"],
		order_by="creation asc",
	)
	rows = []
	for a in allocations:
		item = items.get(a.plan_item)
		if not item:
			continue
		line = labels.get(cstr(a.budget_line), {})
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"plan_item_title": item.title,
				"department": _ou_label(a.organisation_unit),
				"source_key": a.source_key,
				"source_origin": a.source_origin,
				"quantity_display": _quantity_display(a.quantity, a.unit),
				"unit_label": _unit_label(a.unit),
				"budget_line_display": line.get("label") or cstr(a.budget_line),
				"amount_display": _money(a.indicative_amount),
			}
		)
	return rows


def _governance_method_and_schedule(version, user: str | None) -> list[dict[str, Any]]:
	"""U11-checks — one Method-and-eligibility / Schedule card per Plan
	Item, read from the same resolver `GetPlanItem` (PLN-DES-09) uses so
	the two screens never disagree on the applicable profile or dates."""
	item_ids = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")}, pluck="plan_item_id", order_by="creation asc")
	cards = []
	for plan_item_id in item_ids:
		detail = get_plan_item(plan_item_id=plan_item_id, user=user)
		mp = detail["classification"]["method_profile"]
		declarations = [c for c in mp["conditions"] if c.get("kind") != "Known fact"]
		cards.append(
			{
				"plan_item_id": plan_item_id,
				"title": detail["identity"]["title"],
				"method": {
					"method": detail["classification"]["procurement_method"],
					"profile": mp["profile"],
					"version_number": mp["version_number"],
					"conditions_complete": mp["evidence_complete"],
					"evidence_line": declarations[0]["required_evidence"] if declarations else "Method eligibility record",
					"specific_authorisation": "Required" if any(c.get("authorisation_actor") for c in declarations) else "Not required",
				},
				"schedule": {
					"target_invitation_display": _date(detail["baseline"]["target_invitation_date"]),
					"rows": detail["baseline"]["rows"],
					"periods_display": {f: f"{v} calendar days" for f, v in detail["baseline"]["periods"].items()},
					"estimated_delivery_period_days": detail["baseline"]["estimated_delivery_period_days"],
					"estimated_completion_display": detail["baseline"]["estimated_completion_display"],
					"delivery_boundary_ok": detail["baseline"]["delivery_boundary_ok"],
				},
			}
		)
	return cards


_GOVERNANCE_STAGE_OUTCOME = {"Adopt and submit": "Adopted and submitted", "Approve": "Approved", "Return for correction": "Returned"}


def _governance_schedule_result(version, plan) -> str:
	report = plan_readiness(version, plan, stage="submission")
	failing = [
		b for b in report["blockers"]
		if b["code"] in ("PLN_SCHEDULE_INVALID", "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", "PLN_DELIVERY_PERIOD_REQUIRED")
	]
	if not failing:
		return "All purchases meet departmental deadlines"
	return f"{len(failing)} purchase{'s do' if len(failing) != 1 else ' does'} not meet its departmental deadline"


def _governance_issues(version, plan, *, funding_current: bool, share) -> list[str]:
	"""Every material issue, in the actor's words, before their decision.

	§10.10: the decision never precedes a hidden material issue. An empty list
	means the screen says "No blocking issues" — which it may only do when
	there genuinely are none.
	"""
	issues: list[str] = []
	if not funding_current:
		issues.append(
			"The budget has changed since Finance checked this plan. "
			"Procurement must obtain a new funding check before this plan can be adopted."
		)
	if share["mandatory"] and not share["met"]:
		issues.append(f"Reserved procurement is below the required amount by {_money(share['shortfall'])}.")
	report = plan_readiness(version, plan, stage="submission")
	for blocker in report["blockers"]:
		message = cstr(blocker.get("message"))
		if message and message not in issues:
			issues.append(message)
	return issues


def _governance_history(version) -> list[dict[str, Any]]:
	"""U11-decisions — every completed review in order (Finance,
	Preparation, Accounting Officer adoption, Statutory approval), plus
	the current open stage as **Awaiting decision**; a later stage's row
	never overwrites an earlier one's (mirrors `_finance_history`)."""
	rows = []
	finance_task = frappe.db.get_value("Plan Finance Task", {"plan_version": version.name, "decision": ("is", "set")}, "decision", order_by="creation asc")
	if finance_task:
		decision = frappe.get_doc("Plan Finance Decision", finance_task)
		rows.append(
			{
				"stage": "Finance", "actor": cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor),
				"capacity": "Finance Confirmation Officer", "outcome": _DECISION_OUTCOME_LABELS.get(decision.decision, decision.decision),
				"date_display": _eat(decision.decided_at),
			}
		)
	if version.preparation_signature:
		sig = frappe.db.get_value("Plan Preparation Signature", version.preparation_signature, ["actor", "capacity", "signed_at"], as_dict=True)
		if sig:
			rows.append(
				{
					"stage": "Preparation", "actor": cstr(frappe.db.get_value("User", sig.actor, "full_name") or sig.actor),
					"capacity": sig.capacity, "outcome": "Signed and submitted", "date_display": _eat(sig.signed_at),
				}
			)
	for stage in ("Accounting Officer adoption", "Statutory approval"):
		task = frappe.db.get_value("Plan Governance Task", {"plan_version": version.name, "stage": stage}, ["name", "decision", "capacity"], as_dict=True)
		if not task:
			continue
		if task.decision:
			decision = frappe.get_doc("Plan Governance Decision", task.decision)
			rows.append(
				{
					"stage": stage, "actor": cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor),
					"capacity": decision.capacity, "outcome": _GOVERNANCE_STAGE_OUTCOME.get(decision.decision, decision.decision),
					"date_display": _eat(decision.decided_at),
				}
			)
		else:
			rows.append({"stage": stage, "actor": "—", "capacity": task.capacity, "outcome": "Awaiting decision", "date_display": "—"})
	return rows


def get_plan_governance_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_governance

	actor = authz.actor(user)
	if not task or not frappe.db.exists("Plan Governance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Governance Task", task)
	role = ROLE_ACCOUNTING_OFFICER if task_doc.stage == "Accounting Officer adoption" else ROLE_PLAN_STATUTORY_APPROVER
	authz.require_site_read((role, ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR), actor)
	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	snapshot = json.loads(version.submitted_snapshot) if version.submitted_snapshot else {}
	rows = snapshot.get("rows", snapshot if isinstance(snapshot, list) else [])
	total_value = sum(flt(row.get("value")) for row in rows)
	for row in rows:
		# The purpose comes from the sources, not from a separate field: it is
		# what the department said the requirement is for.
		row.setdefault(
			"purpose",
			cstr(
				frappe.db.get_value(
					"Departmental Plan Entry",
					frappe.db.get_value(
						"Plan Source Allocation",
						{"plan_item_id": row.get("plan_item_id"), "allocation_state": ("!=", "Released")},
						"dpp_entry",
					),
					"expected_operational_result",
				)
				or ""
			),
		)
	authority_card = None
	if task_doc.stage == "Statutory approval":
		ao_decision = frappe.db.get_value("Plan Governance Task", {"plan_version": version.name, "stage": "Accounting Officer adoption"}, "decision")
		ao_actor, ao_decided_at = "", ""
		if ao_decision:
			row = frappe.db.get_value("Plan Governance Decision", ao_decision, ["actor", "decided_at"], as_dict=True)
			ao_actor = cstr(frappe.db.get_value("User", row.actor, "full_name") or row.actor) if row else ""
			ao_decided_at = _eat(row.decided_at) if row else ""
		is_board = plan_governance.is_collective_capacity(task_doc.capacity)
		authority_card = {
			"capacity": "Governing body" if is_board else task_doc.capacity,
			"capacity_detail": task_doc.capacity,
			"is_board": is_board,
			"ao_adoption_line": f"{ao_actor} · {ao_decided_at}" if ao_actor else "",
		}
	target = snapshot.get("reservation_target_percent")
	share = snapshot.get("reserved_share_percent", 0)
	advisory_line = (
		f"Reserved share {share:.0f}% of plan value · target {target:.0f}%. " if target else f"Reserved share {share:.0f}% of plan value. "
	) + ("No contract splitting advisory." if not snapshot.get("splitting_advisory_count") else f"{snapshot['splitting_advisory_count']} contract splitting advisory confirmed by the Planner.")
	action = authz.ACTION_AO_DECIDE if task_doc.stage == "Accounting Officer adoption" else authz.ACTION_STATUTORY_DECIDE
	can_decide = task_doc.status == "Open" and authz.has_site_role(role, actor) and not authz.is_segregated(actor, action, plan_version=version.name)
	funding_current = plan_finance.funding_is_current(version)
	funding_evidence = _funding_evidence(version)
	confirmation = funding_evidence.get("current_confirmation") or {}
	reference = readiness.reference_for(plan.fiscal_year)
	share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"stage": task_doc.stage,
		# §10.10 — the decision summary every governance actor sees first.
		# Three figures, three results, then either "No blocking issues" or
		# the exact issues. The actor must not have to assemble this.
		"decision_summary": {
			"value_display": _money(total_value),
			"purchases": len(rows),
			"departments": len({r["department"] for r in rows if r.get("department")}),
			"funding": "Within approved budget" if funding_current else "Funding needs to be checked again",
			"funding_kind": "live" if funding_current else "critical",
			"reservation": "Required allocation met" if share["met"] or not share["mandatory"] else (
				f"{_money(share['shortfall'])} more qualifying allocation required"
			),
			"reservation_kind": "live" if (share["met"] or not share["mandatory"]) else "critical",
			"schedule": _governance_schedule_result(version, plan),
			"issues": _governance_issues(version, plan, funding_current=funding_current, share=share),
		},
		"can_decide": can_decide,
		"plan_reference": plan.plan_reference,
		"version_number": version.version_number,
		"header": {
			"eyebrow": f"{task_doc.stage.upper()} · {plan.plan_reference} · VERSION {version.version_number}",
			"title": plan.title,
			"badge": version.version_status,
		},
		"authority_card": authority_card,
		"decision_statement": (
			f"I adopt the complete consolidated Annual Procurement Plan Version {version.version_number} shown above and submit it for the statutory approval applicable to this Procuring Entity."
			if task_doc.stage == "Accounting Officer adoption"
			else (
				f"I record the {authority_card['capacity_detail']}'s resolution approving the complete consolidated Annual Procurement Plan Version {version.version_number}."
				if authority_card and authority_card["is_board"]
				else f"I approve the complete consolidated Annual Procurement Plan Version {version.version_number} as adopted by the Accounting Officer."
			)
		),
		"items": rows,
		"caption": f"{len(rows)} Plan Item{'s' if len(rows) != 1 else ''} · {_money(total_value)}",
		"advisory_line": advisory_line,
		"late_activation_reason": cstr(frappe.db.get_value("Late Activation Explanation", {"plan_version": version.name}, "reason", order_by="recorded_at desc") or ""),
		"late_activation_explanations": frappe.get_all("Late Activation Explanation", filters={"plan_version": version.name}, fields=["name", "reason", "actor", "recorded_at", "supersedes"], order_by="recorded_at asc"),
		"preparation_signature": _signature_summary(version),
		"confirm_label": "Adopt and submit" if task_doc.stage == "Accounting Officer adoption" else "Approve Annual Procurement Plan",
		"return_dialog": (
			{"title": "Return Plan Version for correction?", "lede": f"The submitted Version {version.version_number} remains unchanged. State the correction required."}
			if task_doc.stage == "Accounting Officer adoption"
			else {"title": "Return adopted Plan Version for correction?", "lede": f"The Accounting-Officer-adopted Version {version.version_number} remains unchanged. State the correction required."}
		),
		# v1.18 §6.3/D-register — a positive decision additionally needs a
		# current funding basis (U11-stale); Return stays available regardless.
		"funding_current": funding_current,
		"can_decide_positive": can_decide and funding_current,
		"sources": _governance_sources(version, plan),
		"funding": {
			"rows": _affordability_rows(plan_finance.affordability_statement(plan, version)),
			"statement_as_at": confirmation.get("decided_at_display", ""),
			"confirmed_by": confirmation.get("actor_name", ""),
			"at_approval": funding_evidence.get("at_approval"),
			"current": funding_evidence.get("current"),
		},
		"method_and_schedule": _governance_method_and_schedule(version, user),
		"reservation": {
			"target_percent": share["target_percent"],
			"required_allocation_display": _money(share["required"]) if share["required"] not in ("", None) else "Not mandatory",
			"planned_qualifying_display": _money(share["qualifying"]),
			"shortfall_display": _money(share["shortfall"]) if share["shortfall"] not in ("", None) else "",
			"share_of_annual_display": f"{share['percent_of_annual']:.2f}%" if share["basis"]["available"] else "",
			"budget_basis_reference": share["basis"]["budget_reference"],
			"budget_version_display": f"Version {share['basis']['version_reference']}" if share["basis"]["version_reference"] else "",
			"county_requirement_display": (f"{share['county']['target_percent']}%" if share["county"]["applicable"] else "Not applicable"),
			"met": share["met"],
		},
		"changes": _version_changes(version),
		"history": _governance_history(version),
		"can_download_review_pack": True,
	}


def get_source_evidence(*, task: str, source_key: str, user: str | None = None) -> dict[str, Any]:
	"""U12 — the exact origin chain for one reviewed allocation, reached
	only from its own Review task (never a bare public lookup): the Need's
	own department acceptance (where Need-origin), the DPP's certification
	and the Planner's acceptance for planning, plus whether a newer
	accepted Need revision now exists (§10.5's own three variants)."""
	actor = authz.actor(user)
	task_doc = frappe.db.get_value("Plan Governance Task", task, ["name", "plan_version", "stage"], as_dict=True)
	if not task_doc:
		authz.not_found()
	role = ROLE_ACCOUNTING_OFFICER if task_doc.stage == "Accounting Officer adoption" else ROLE_PLAN_STATUTORY_APPROVER
	authz.require_site_read((role, ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR), actor)
	version = frappe.get_doc("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	allocation = frappe.db.get_value(
		"Plan Source Allocation",
		{"plan_version": version.name, "source_key": source_key, "allocation_state": ("in", ("Draft", "Active"))},
		["name", "plan_item", "dpp_entry", "source_origin", "need", "need_revision", "organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount"],
		as_dict=True,
	)
	if not allocation:
		authz.not_found()
	plan_item = frappe.db.get_value("Annual Plan Item", allocation.plan_item, ["plan_item_id", "title"], as_dict=True)
	entry = frappe.get_doc("Departmental Plan Entry", allocation.dpp_entry)
	dpp_version = frappe.get_doc("Departmental Plan Version", entry.dpp_version)
	dpp_root = frappe.db.get_value("Departmental Plan", dpp_version.departmental_plan, "dpp_reference")
	labels = _line_labels(plan.fiscal_year)
	line = labels.get(cstr(allocation.budget_line), {})

	certified = None
	if dpp_version.submission:
		sub = frappe.db.get_value("Departmental Plan Submission", dpp_version.submission, ["submitted_by_user", "submitted_at"], as_dict=True)
		if sub:
			certified = {"actor": sub.submitted_by_user, "actor_name": cstr(frappe.db.get_value("User", sub.submitted_by_user, "full_name") or sub.submitted_by_user), "display": _eat(sub.submitted_at)}
	accepted_for_planning = None
	validation_decision = frappe.db.get_value(
		"Departmental Plan Validation Decision", {"submission": dpp_version.submission, "decision": "Accept departmental plan"},
		["actor", "decided_at"], as_dict=True,
	) if dpp_version.submission else None
	if validation_decision:
		accepted_for_planning = {
			"actor": validation_decision.actor, "actor_name": cstr(frappe.db.get_value("User", validation_decision.actor, "full_name") or validation_decision.actor),
			"display": _eat(validation_decision.decided_at),
		}

	need_accepted, has_newer_revision, newer_revision_number = None, False, None
	if allocation.source_origin == needs_intake.NEED_ORIGIN and allocation.need:
		need_decision = frappe.db.get_value(
			"Departmental Need Decision", {"departmental_need": allocation.need, "need_revision": allocation.need_revision, "action": "Accept for planning"},
			["actor", "occurred_at"], as_dict=True, order_by="occurred_at asc",
		)
		if need_decision:
			need_accepted = {
				"actor": need_decision.actor, "actor_name": cstr(frappe.db.get_value("User", need_decision.actor, "full_name") or need_decision.actor),
				"display": _eat(need_decision.occurred_at),
			}
		current_revision = needs_intake.current_accepted_revision_of(allocation.need, plan.fiscal_year)
		if current_revision and current_revision != cstr(allocation.need_revision):
			has_newer_revision = True
			newer_revision_number = needs_intake.need_revision_number(current_revision)

	return {
		"outcome": "OK",
		"task": task_doc.name,
		"source_key": source_key,
		"plan_reference": plan.plan_reference,
		"version_number": version.version_number,
		"plan_item_id": plan_item.plan_item_id,
		"title": entry.title,
		"quantity_display": _quantity_display(allocation.quantity, allocation.unit),
		"required_by_display": _date(allocation.required_by_date),
		"amount_display": _money(allocation.indicative_amount),
		"description": cstr(entry.description),
		"expected_operational_result": cstr(entry.expected_operational_result),
		"source_origin": allocation.source_origin,
		"department": _ou_label(allocation.organisation_unit),
		"need_reference": cstr(allocation.need),
		"need_revision_number": needs_intake.need_revision_number(allocation.need_revision) if allocation.need_revision else None,
		"departmental_plan_reference": dpp_root,
		"submission_number": dpp_version.version_number,
		"dpp_entry_id": entry.entry_id,
		"budget_line_display": line.get("label") or cstr(allocation.budget_line),
		"planning_amount_display": _money(allocation.indicative_amount),
		"need_accepted": need_accepted,
		"certified": certified,
		"accepted_for_planning": accepted_for_planning,
		"has_newer_revision": has_newer_revision,
		"newer_revision_number": newer_revision_number,
		"back_route": ["procurement-planning", "review", task_doc.name],
	}


def build_review_pack(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""PLN18-AC-025 / PLN18-UX-14 — the protected review pack: the complete
	governed content already on the Review screen, plus every source's own
	evidence index, as one downloadable document (§10.4's own **Download
	review pack**). Scoped to the same read model, not the post-approval
	`plan_json` public contract (that snapshot does not exist yet at this
	pre-approval stage)."""
	review = get_plan_governance_task(task=task, user=user)
	evidence_index = [get_source_evidence(task=task, source_key=row["source_key"], user=user) for row in review["sources"]]
	return {
		"schema": "KenTenderPlanReviewPack.v1",
		"generated_at": _eat(frappe.utils.now_datetime()),
		"task_reference": review["task_reference"],
		"stage": review["stage"],
		"status": review["status"],
		"header": review["header"],
		"items": review["items"],
		"sources": review["sources"],
		"funding": review["funding"],
		"method_and_schedule": review["method_and_schedule"],
		"reservation": review["reservation"],
		"changes": review["changes"],
		"history": review["history"],
		"evidence_index": evidence_index,
	}


# --------------------------------------------------------------------------
# GetPublicationTask (PLN-DES-13)
# --------------------------------------------------------------------------


def get_publication_task(*, publication: str, user: str | None = None) -> dict[str, Any]:
	"""§10.13 — the retry/reconcile screen for one `Plan Publication`: its
	Treasury-evidence gate, the attempt history and the current publication
	state. The full protected review pack (source evidence, web/PDF/JSON
	exports) is Phase 3F/3G work; this is the minimal state a technical
	retry or an AO's Treasury-evidence check needs today."""
	from kentender_core.services.authorization import is_technical

	actor = authz.actor(user)
	if not publication or not frappe.db.exists("Plan Publication", publication):
		authz.not_found()
	doc = frappe.get_doc("Plan Publication", publication)
	authz.require_site_read(PLAN_READERS, actor)
	version = frappe.get_doc("Annual Plan Version", doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	destination = frappe.db.get_value("Annual Plan Publication Destination", doc.destination, ["destination_id", "title"], as_dict=True) or {}
	attempts = frappe.get_all(
		"Publication Attempt", filters={"publication": doc.name}, fields=["name", "attempt_number", "result", "attempted_at", "completed_at", "external_reference", "failure_reason"],
		order_by="attempt_number asc",
	)
	treasury = frappe.db.get_value(
		"Treasury Submission Evidence", {"plan_version": version.name, "evidence_state": "Current"},
		["name", "submitted_at", "channel", "dispatch_reference", "recorded_at"], as_dict=True,
	)
	hold = frappe.db.get_value("Plan Publication Hold", {"plan_version": version.name, "hold_state": "Active"}, ["name", "hold_kind", "reason", "raised_at"], as_dict=True)
	badge, badge_kind = {
		"Acknowledged": ("Acknowledged", "live"), "Failed": ("Publication failed", "critical"),
		"Indeterminate": ("Result unknown — reconcile", "attention"), "Held": ("On hold", "attention"),
	}.get(doc.publication_state, ("Pending", "attention"))
	return {
		"outcome": "OK",
		"publication": doc.name,
		"publication_id": doc.publication_id,
		"header": {"eyebrow": "ANNUAL PLAN PUBLICATION", "title": "Publication result", "reference_line": f"{plan.plan_reference} · Version {version.version_number}", "badge": badge, "badge_kind": badge_kind},
		"plan_reference": plan.plan_reference,
		"plan_title": plan.title,
		"version": {"reference": version.version_reference, "status": version.version_status, "number": version.version_number},
		"destination": {"id": destination.get("destination_id", ""), "title": destination.get("title", "")},
		"publication_state": doc.publication_state,
		"package_hash": doc.package_hash,
		"external_reference": cstr(doc.external_reference),
		"acknowledged_display": _eat(doc.acknowledged_at),
		"attempts": [
			{"attempt_number": a.attempt_number, "result": a.result, "attempted_display": _eat(a.attempted_at), "completed_display": _eat(a.completed_at), "external_reference": cstr(a.external_reference), "failure_reason": cstr(a.failure_reason)}
			for a in attempts
		],
		"treasury_evidence": (
			{"recorded": True, "submitted_display": _eat(treasury.submitted_at), "channel": treasury.channel, "dispatch_reference": treasury.dispatch_reference}
			if treasury else {"recorded": False}
		),
		"hold": {"active": bool(hold), "kind": hold.hold_kind if hold else "", "reason": cstr(hold.reason) if hold else "", "raised_display": _eat(hold.raised_at) if hold else ""},
		"quiet_notice": "Publication is a system worker action after statutory approval. Retry and reconciliation are technical actions, never a business decision.",
		"can_retry": is_technical(actor) and doc.publication_state == "Failed",
		"can_reconcile": is_technical(actor) and doc.publication_state == "Indeterminate",
	}
