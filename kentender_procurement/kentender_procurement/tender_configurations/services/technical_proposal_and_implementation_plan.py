# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical Proposal and Implementation Plan — overview + subsection renderers."""

from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
	CONDITION_ALWAYS,
	CONDITION_ALT_PERMITTED,
	CONDITION_LOT_TOPIC,
	CONDITION_MIGRATION,
	CONDITION_TRAINING,
	CONDITION_WARRANTY,
	MODE_CONDITIONAL,
	MODE_EXCLUDED,
	MODE_OPTIONAL,
	MODE_REQUIRED,
	RENDERER_ALTERNATIVES,
	RENDERER_APPROACH,
	RENDERER_INTEGRATION,
	RENDERER_ORG,
	RENDERER_RISKS,
	RENDERER_TESTING,
	RENDERER_TRAINING,
	RENDERER_TRANSITION,
	RENDERER_WARRANTY,
	RENDERER_WORK_PLAN,
	SCOPE_LOT,
	SUB_INTEGRATION,
	SUB_ORG,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	_append_audit,
	_get_bid,
	_parse_json,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.electronic_std_template import (
	get_published_electronic_template,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_APPLICABLE,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "technical_proposal_and_implementation_plan"

ACTION_START = "Start"
ACTION_CONTINUE = "Continue"
ACTION_RESOLVE = "Resolve"
ACTION_REVIEW = "Review"

# Stitch 01 overview copy — preferred over the pre-fidelity lean boilerplate.
STITCH_BIDDER_INSTRUCTIONS = (
	"Explain how you will deliver, implement, test and hand over the proposed system."
)
_LEGACY_BIDDER_INSTRUCTIONS = (
	"Provide the technical proposal and implementation plan required by the tender."
)


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open Technical Proposal and Implementation Plan."),
			frappe.PermissionError,
		)


def portal_technical_proposal_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def portal_technical_proposal_subsection_url(publication_ref: str, subsection_key: str) -> str:
	return (
		f"{portal_technical_proposal_url(publication_ref)}/"
		f"{quote(cstr(subsection_key or '').strip(), safe='')}"
	)


def portal_technical_proposal_review_url(publication_ref: str) -> str:
	return f"{portal_technical_proposal_url(publication_ref)}/review"


def _section_def(snapshot: dict[str, Any]) -> dict[str, Any] | None:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	return None


def _payload(responses: dict[str, Any]) -> dict[str, Any]:
	raw = responses.get(SECTION_KEY)
	return raw if isinstance(raw, dict) else {}


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
	out = dict(payload) if isinstance(payload, dict) else {}
	subs = out.get("subsections")
	if not isinstance(subs, dict):
		out["subsections"] = {}
	conf = out.get("integration_confirmation")
	if not isinstance(conf, dict):
		out["integration_confirmation"] = {}
	flags = out.get("flags")
	if not isinstance(flags, dict):
		out["flags"] = {}
	return out


def _load_bid_for_cfg(
	cfg_id: str, *, snapshot: dict[str, Any] | None = None, schema_hash: str | None = None
):
	owner = frappe.session.user
	draft_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": "Draft", "owner": owner},
		"name",
	)
	if draft_name:
		return _get_bid(draft_name)
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": STATUS_SEALED, "owner": owner},
		"name",
		order_by="sealed_at desc",
	)
	if sealed_name:
		return _get_bid(sealed_name)
	draft = create_or_get_draft(
		cfg_id, bidder_label=None, schema_snapshot=snapshot, schema_hash=schema_hash
	)
	return _get_bid(cstr(draft.get("bid_id")))


def _selected_lots(responses: dict[str, Any] | None) -> list[str]:
	lot = (responses or {}).get("lot_and_alternative_selection")
	if not isinstance(lot, dict):
		return []
	raw = lot.get("selected_lots") or lot.get("lots") or []
	if isinstance(raw, list):
		return [cstr(x.get("lot_id") if isinstance(x, dict) else x) for x in raw if x]
	return []


def _tp_flags(section_def: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
	cfg_flags = section_def.get("technical_proposal_flags")
	if not isinstance(cfg_flags, dict):
		cfg_flags = {}
	bid_flags = payload.get("flags") if isinstance(payload.get("flags"), dict) else {}
	merged = dict(cfg_flags)
	merged.update(bid_flags)
	return merged


def evaluate_named_condition(
	condition_key: str,
	*,
	subsection: dict[str, Any],
	payload: dict[str, Any],
	section_def: dict[str, Any],
	responses: dict[str, Any] | None,
) -> bool:
	key = cstr(condition_key or CONDITION_ALWAYS).strip() or CONDITION_ALWAYS
	if key in (CONDITION_ALWAYS, "", "true"):
		return True
	flags = _tp_flags(section_def, payload)
	if key == CONDITION_ALT_PERMITTED:
		return bool(int(flags.get("technical_alternatives_permitted") or 0))
	if key == CONDITION_TRAINING:
		return bool(int(flags.get("training_required_by_tds") or 0))
	if key == CONDITION_WARRANTY:
		return bool(int(flags.get("warranty_support_required_by_tds") or 0))
	if key == CONDITION_MIGRATION:
		return bool(int(flags.get("data_migration_in_requirements") or 0))
	if key == CONDITION_LOT_TOPIC:
		if not bool(int(flags.get("lot_topic_selected") or 0)):
			return False
		return bool(_selected_lots(responses))
	return False


def resolve_subsection_applicability(
	subsection: dict[str, Any],
	*,
	payload: dict[str, Any],
	section_def: dict[str, Any],
	responses: dict[str, Any] | None,
) -> tuple[bool, str]:
	mode = cstr(subsection.get("requirement_mode") or MODE_REQUIRED).strip().lower()
	if mode == MODE_EXCLUDED:
		return False, MODE_EXCLUDED
	cond_ok = evaluate_named_condition(
		cstr(subsection.get("condition_key") or CONDITION_ALWAYS),
		subsection=subsection,
		payload=payload,
		section_def=section_def,
		responses=responses,
	)
	if mode == MODE_CONDITIONAL:
		if not cond_ok:
			return False, "na"
		return True, MODE_REQUIRED
	if mode == MODE_OPTIONAL:
		if subsection.get("condition_key") not in (CONDITION_ALWAYS, "", None) and not cond_ok:
			return False, "na"
		return True, MODE_OPTIONAL
	if subsection.get("condition_key") not in (CONDITION_ALWAYS, "", None) and not cond_ok:
		return False, "na"
	return True, MODE_REQUIRED


def _sub_bucket(payload: dict[str, Any], subsection_key: str) -> dict[str, Any]:
	subs = payload.get("subsections") if isinstance(payload.get("subsections"), dict) else {}
	raw = subs.get(subsection_key)
	return raw if isinstance(raw, dict) else {}


def _narratives_complete(bucket: dict[str, Any], questions: list[dict[str, Any]]) -> tuple[int, int, list[str]]:
	answers = bucket.get("narratives") if isinstance(bucket.get("narratives"), dict) else {}
	req = [q for q in questions if isinstance(q, dict) and q.get("required", True)]
	done = 0
	issues: list[str] = []
	for q in req:
		qid = cstr(q.get("question_id"))
		val = cstr(answers.get(qid) or "").strip()
		if val:
			done += 1
		elif answers.get(qid) is not None:
			issues.append(f"{q.get('title') or qid} response is empty.")
	return done, len(req), issues


def _records_list(bucket: dict[str, Any], key: str) -> list[dict[str, Any]]:
	raw = bucket.get(key)
	if not isinstance(raw, list):
		return []
	return [r for r in raw if isinstance(r, dict)]


def calculate_completion_week(start_week: Any, duration_weeks: Any) -> int | None:
	try:
		start = int(start_week)
		dur = int(duration_weeks)
	except (TypeError, ValueError):
		return None
	if start < 1 or dur < 1:
		return None
	return start + dur - 1


def _activity_row_status(activity: dict[str, Any], *, known_ids: set[str]) -> str:
	"""Derive Stitch work-plan row status from a single activity record."""
	name = cstr(activity.get("activity") or "").strip()
	end = calculate_completion_week(activity.get("start_week"), activity.get("duration_weeks"))
	role = cstr(activity.get("project_role") or "").strip()
	dep = _normalize_dependency_id(activity.get("dependency_id"))
	started = bool(
		name
		or activity.get("start_week") not in (None, "", 0)
		or activity.get("duration_weeks") not in (None, "", 0)
		or role
		or dep
		or cstr(activity.get("deliverable") or "").strip()
		or cstr(activity.get("milestone") or "").strip()
	)
	if dep and dep not in known_ids:
		return STATUS_NEEDS_ATTENTION
	if name and end is not None and role:
		return STATUS_COMPLETE
	if started:
		if name and (end is None or not role):
			return STATUS_NEEDS_ATTENTION
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def _fields_row_status(row: dict[str, Any], *, required_fields: list[str], any_fields: list[str]) -> str:
	"""Generic Complete / In Progress / Not Started for register-style rows."""
	required_ok = all(cstr(row.get(f) or "").strip() for f in required_fields)
	started = any(cstr(row.get(f) or "").strip() for f in any_fields)
	if required_ok:
		return STATUS_COMPLETE
	if started:
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def _test_stage_row_status(stage: dict[str, Any]) -> str:
	return _fields_row_status(
		stage,
		required_fields=["test_stage", "scope", "responsible_party", "entry_criteria", "expected_output"],
		any_fields=[
			"test_stage",
			"scope",
			"responsible_party",
			"entry_criteria",
			"expected_output",
			"pe_participation",
			"work_plan_phase",
		],
	)


def _alternative_row_status(alt: dict[str, Any]) -> str:
	return _fields_row_status(
		alt,
		required_fields=["title", "affected_system_part", "description"],
		any_fields=[
			"title",
			"affected_system_part",
			"description",
			"schedule_impact",
			"price_schedule_ref",
			"supporting_info",
		],
	)


def _ensure_handover_deliverables(
	bucket: dict[str, Any], subsection: dict[str, Any]
) -> dict[str, Any]:
	"""Ensure transition bucket has a handover deliverables checklist (Stitch 06 §3)."""
	out = dict(bucket) if isinstance(bucket, dict) else {}
	existing = out.get("handover_deliverables")
	if isinstance(existing, list) and existing:
		return out
	cfg_rows = subsection.get("handover_deliverables") if isinstance(subsection, dict) else None
	defaults = cfg_rows if isinstance(cfg_rows, list) and cfg_rows else [
		{"deliverable_id": "hd-ops-manual", "title": "Operations manual", "required": 1},
		{"deliverable_id": "hd-admin-guide", "title": "Administrator guide", "required": 1},
		{"deliverable_id": "hd-source-access", "title": "Source / configuration access credentials", "required": 1},
		{"deliverable_id": "hd-training-pack", "title": "Training materials pack", "required": 0},
	]
	rows = []
	for row in defaults:
		if not isinstance(row, dict):
			continue
		did = cstr(row.get("deliverable_id") or "").strip() or f"hd-{uuid.uuid4().hex[:8]}"
		rows.append(
			{
				"deliverable_id": did,
				"title": cstr(row.get("title") or did),
				"required": 1 if row.get("required", True) else 0,
				"provided": 1 if row.get("provided") else 0,
			}
		)
	out["handover_deliverables"] = rows
	return out


def _build_consolidated_summary(payload: dict[str, Any]) -> dict[str, Any]:
	"""Review-page Consolidated Summary aggregates (Stitch 09)."""
	from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
		SUB_ALTERNATIVES,
		SUB_APPROACH,
		SUB_ORG,
		SUB_RISKS,
		SUB_TESTING,
		SUB_TRAINING,
		SUB_WORK_PLAN,
	)

	payload = _normalize_payload(payload)
	org = _sub_bucket(payload, SUB_ORG)
	wp = _sub_bucket(payload, SUB_WORK_PLAN)
	testing = _sub_bucket(payload, SUB_TESTING)
	training = _sub_bucket(payload, SUB_TRAINING)
	risks = _sub_bucket(payload, SUB_RISKS)
	alts = _sub_bucket(payload, SUB_ALTERNATIVES)

	activities = _records_list(wp, "activities")
	ends = [calculate_completion_week(a.get("start_week"), a.get("duration_weeks")) or 0 for a in activities]
	duration_weeks = max(ends) if ends else 0
	milestones = sum(1 for a in activities if cstr(a.get("milestone") or "").strip())
	roles = _records_list(org, "resource_roles")
	stages = _records_list(testing, "test_stages")
	train_rows = _records_list(training, "training_activities")
	risk_rows = _records_list(risks, "risks")
	dep_rows = _records_list(risks, "dependencies")
	alt_rows = _records_list(alts, "alternatives")
	return {
		"work_plan_duration_weeks": duration_weeks,
		"work_plan_duration_label": f"{duration_weeks} Weeks" if duration_weeks else "—",
		"activity_count": len(activities),
		"milestone_count": milestones,
		"key_personnel_roles": len(roles),
		"testing_stages": len(stages),
		"training_activities": len(train_rows),
		"risk_count": len(risk_rows),
		"dependency_count": len(dep_rows),
		"alternative_count": len(alt_rows),
		"approach_topics_answered": len(
			[
				v
				for v in (
					(_sub_bucket(payload, SUB_APPROACH).get("narratives") or {})
					if isinstance(_sub_bucket(payload, SUB_APPROACH).get("narratives"), dict)
					else {}
				).values()
				if cstr(v).strip()
			]
		),
	}


def _normalize_dependency_id(raw: Any) -> str:
	"""Treat explicit None / em-dash placeholders as no dependency."""
	dep = cstr(raw or "").strip()
	if not dep:
		return ""
	if dep.lower() in {"none", "null", "n/a", "na", "-", "—", "–"}:
		return ""
	return dep


def _activity_display_name(activity: dict[str, Any]) -> str:
	name = cstr(activity.get("activity") or "").strip()
	if name:
		return name
	return cstr(activity.get("activity_id") or "activity").strip() or "activity"


def validate_work_plan_activities(
	activities: list[dict[str, Any]],
	*,
	max_completion_weeks: int | None = None,
) -> list[str]:
	issues: list[str] = []
	ids = {cstr(a.get("activity_id")) for a in activities if cstr(a.get("activity_id"))}
	for a in activities:
		label = _activity_display_name(a)
		aid = cstr(a.get("activity_id") or "").strip()
		start = a.get("start_week")
		dur = a.get("duration_weeks")
		end = calculate_completion_week(start, dur)
		if end is None:
			issues.append(f'Activity "{label}": start week and duration must be positive integers.')
			continue
		dep = _normalize_dependency_id(a.get("dependency_id"))
		# Persist normalized empty so "None" never survives as a fake id.
		a["dependency_id"] = dep
		if dep:
			if dep not in ids:
				issues.append(
					f'Activity "{label}": selected dependency is not in the work plan. '
					"Choose None or another activity."
				)
			elif aid and dep == aid:
				issues.append(f'Activity "{label}": dependency cannot reference itself.')
		if max_completion_weeks and end > int(max_completion_weeks):
			issues.append(
				"The proposed schedule exceeds the permitted completion period."
			)
	# Detect simple cycles via dependency chains
	dep_map = {
		cstr(a.get("activity_id")): _normalize_dependency_id(a.get("dependency_id"))
		for a in activities
		if cstr(a.get("activity_id"))
	}
	for start_id in dep_map:
		seen: set[str] = set()
		cur = start_id
		while cur and cur in dep_map:
			if cur in seen:
				issues.append("Work-plan activities have circular dependencies.")
				return issues
			seen.add(cur)
			cur = dep_map.get(cur) or ""
	return issues


def _derive_org(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	done_n, total_n, issues = _narratives_complete(bucket, subsection.get("questions") or [])
	roles = _records_list(bucket, "resource_roles")
	matrix = _records_list(bucket, "coordination_matrix")
	# Require at least one role assignment and one matrix row for complete
	struct_done = 0
	struct_total = 2
	if roles and all(cstr(r.get("project_role")) and cstr(r.get("person_id") or r.get("person_name")) for r in roles):
		struct_done += 1
	elif roles:
		issues.append("Management responsibilities are incomplete.")
	if matrix and all(cstr(r.get("activity_or_deliverable")) for r in matrix):
		struct_done += 1
	elif matrix:
		issues.append("Responsibility and coordination matrix is incomplete.")
	progress_done = done_n + struct_done
	progress_total = total_n + struct_total
	started = bool(done_n or roles or matrix or bucket.get("narratives"))
	if issues and started:
		status = STATUS_NEEDS_ATTENTION
	elif progress_total and progress_done >= progress_total:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": progress_done,
		"required_items": progress_total,
		"progress_text": f"{progress_done} of {progress_total} complete",
		"status": status,
		"issue": issues[0] if issues else (
			"Management responsibilities are incomplete." if status == STATUS_IN_PROGRESS else ""
		),
		"started": started,
	}


def _derive_narrative_renderer(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	done_n, total_n, issues = _narratives_complete(bucket, subsection.get("questions") or [])
	started = bool(done_n or bucket.get("narratives"))
	if issues and started:
		status = STATUS_NEEDS_ATTENTION
	elif total_n and done_n >= total_n:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	empty_label = "Testing approach has not been provided." if subsection.get("renderer") == RENDERER_TESTING else ""
	return {
		"completed_items": done_n,
		"required_items": total_n,
		"progress_text": f"{done_n} of {total_n} complete" if total_n else "0 of 0 complete",
		"status": status,
		"issue": issues[0] if issues else (empty_label if status == STATUS_NOT_STARTED else ""),
		"started": started,
	}


def _derive_transition(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	bucket = _ensure_handover_deliverables(bucket, subsection)
	base = _derive_narrative_renderer(subsection, bucket)
	handover = [
		r
		for r in (bucket.get("handover_deliverables") or [])
		if isinstance(r, dict)
	]
	req_h = [r for r in handover if r.get("required", True)]
	done_h = [r for r in req_h if r.get("provided")]
	extra_total = len(req_h)
	extra_done = len(done_h)
	base["completed_items"] = int(base.get("completed_items") or 0) + extra_done
	base["required_items"] = int(base.get("required_items") or 0) + extra_total
	base["progress_text"] = f"{base['completed_items']} of {base['required_items']} complete"
	base["started"] = bool(base.get("started") or any(r.get("provided") for r in handover))
	if extra_total and extra_done < extra_total:
		if base["status"] == STATUS_COMPLETE:
			base["status"] = STATUS_IN_PROGRESS
			base["issue"] = "Required handover deliverables have not been confirmed."
		elif base["status"] == STATUS_NOT_STARTED and base["started"]:
			base["status"] = STATUS_IN_PROGRESS
	return base


def _derive_work_plan(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	activities = _records_list(bucket, "activities")
	min_n = int(subsection.get("min_activities") or 1)
	max_weeks = subsection.get("max_completion_weeks")
	try:
		max_weeks_i = int(max_weeks) if max_weeks not in (None, "") else 52
	except (TypeError, ValueError):
		max_weeks_i = 52
	issues = validate_work_plan_activities(activities, max_completion_weeks=max_weeks_i)
	for a in activities:
		end = calculate_completion_week(a.get("start_week"), a.get("duration_weeks"))
		if end is not None:
			a["completion_week"] = end
		if not cstr(a.get("project_role") or "").strip():
			issues.append("Two work-plan activities have no responsible role.")
	# Deduplicate role issue message
	if sum(1 for a in activities if not cstr(a.get("project_role") or "").strip()) == 1:
		issues = [i for i in issues if "no responsible role" not in i]
		if any(not cstr(a.get("project_role") or "").strip() for a in activities):
			issues.append("A work-plan activity has no responsible role.")
	known_ids = {cstr(a.get("activity_id")) for a in activities if cstr(a.get("activity_id"))}
	complete_rows = [
		a
		for a in activities
		if cstr(a.get("activity") or "").strip()
		and calculate_completion_week(a.get("start_week"), a.get("duration_weeks")) is not None
		and cstr(a.get("project_role") or "").strip()
		and (
			not _normalize_dependency_id(a.get("dependency_id"))
			or _normalize_dependency_id(a.get("dependency_id")) in known_ids
		)
	]
	started = bool(activities)
	# Denominator is at least the configured minimum, and never less than rows present.
	progress_total = max(min_n, len(activities)) if activities else max(min_n, 1)
	if issues and started:
		status = STATUS_NEEDS_ATTENTION
	elif len(complete_rows) >= min_n and not issues:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": len(complete_rows),
		"required_items": progress_total,
		"progress_text": f"{len(complete_rows)} of {progress_total} activities complete",
		# Stitch 03 KPI — configured contractual period in weeks (not activity counts).
		"contractual_period_label": f"{max_weeks_i} Weeks",
		"status": status,
		"issue": issues[0] if issues else "",
		"started": started,
	}


def _derive_training(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	rows = _records_list(bucket, "training_activities")
	min_n = int(subsection.get("min_activities") or 1)
	# Ignore blank stub rows; count any row with content toward the progress denominator.
	present = [
		r
		for r in rows
		if cstr(r.get("audience")) or cstr(r.get("topic")) or cstr(r.get("delivery_method"))
	]
	complete = [
		r
		for r in present
		if cstr(r.get("audience")) and cstr(r.get("topic")) and cstr(r.get("delivery_method"))
	]
	started = bool(present)
	progress_total = max(min_n, len(present)) if present else max(min_n, 1)
	incomplete = bool(present) and len(complete) < len(present)
	if len(complete) >= min_n and not incomplete:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": len(complete),
		"required_items": progress_total,
		"progress_text": f"{len(complete)} of {progress_total} complete",
		"status": status,
		"issue": "",
		"started": started,
	}


def _derive_testing(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	base = _derive_narrative_renderer(subsection, bucket)
	stages = _records_list(bucket, "test_stages")
	min_n = int(subsection.get("min_test_stages") or 1)
	present_stages = [
		s
		for s in stages
		if cstr(s.get("test_stage"))
		or cstr(s.get("scope"))
		or cstr(s.get("responsible_party"))
		or cstr(s.get("entry_criteria"))
		or cstr(s.get("expected_output"))
	]
	complete_stages = [
		s for s in present_stages if cstr(s.get("test_stage")) and cstr(s.get("scope"))
	]
	# Stages are a separate required workstream — include them in progress (like handover on transition).
	stage_total = max(min_n, len(present_stages)) if present_stages else min_n
	base["completed_items"] = int(base.get("completed_items") or 0) + len(complete_stages)
	base["required_items"] = int(base.get("required_items") or 0) + stage_total
	base["progress_text"] = f"{base['completed_items']} of {base['required_items']} complete"
	base["started"] = bool(base.get("started") or present_stages)
	stages_ok = len(complete_stages) >= min_n and len(complete_stages) >= len(present_stages)
	if not stages_ok:
		if base["status"] == STATUS_COMPLETE:
			base["status"] = STATUS_IN_PROGRESS
			base["issue"] = "Required testing stages have not been provided."
		elif base["status"] == STATUS_NOT_STARTED and base["started"]:
			base["status"] = STATUS_IN_PROGRESS
			if not complete_stages:
				base["issue"] = "Required testing stages have not been provided."
	if not base["issue"] and base["status"] == STATUS_NOT_STARTED:
		base["issue"] = "Testing approach has not been provided."
	return base


def _derive_risks(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	risks = _records_list(bucket, "risks")
	assumptions = _records_list(bucket, "assumptions")
	deps = _records_list(bucket, "dependencies")
	min_r = int(subsection.get("min_risks") or 1)
	present_r = [
		r
		for r in risks
		if cstr(r.get("risk")) or cstr(r.get("mitigation") or r.get("proposed_mitigation"))
	]
	complete_r = [
		r
		for r in present_r
		if cstr(r.get("risk")) and cstr(r.get("mitigation") or r.get("proposed_mitigation"))
	]
	started = bool(present_r or assumptions or deps)
	progress_total = max(min_r, len(present_r)) if present_r else max(min_r, 1)
	incomplete = bool(present_r) and len(complete_r) < len(present_r)
	if len(complete_r) >= min_r and not incomplete:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": len(complete_r),
		"required_items": progress_total,
		"progress_text": f"{len(complete_r)} of {progress_total} risks complete",
		"status": status,
		"issue": "",
		"started": started,
	}


def _derive_alternatives(subsection: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	alts = _records_list(bucket, "alternatives")
	# Alternatives are optional content when the subsection is applicable — complete if none or all rows valid
	invalid = [
		a
		for a in alts
		if not (cstr(a.get("title") or a.get("alternative_title")) and cstr(a.get("description")))
	]
	started = bool(alts)
	if invalid:
		status = STATUS_NEEDS_ATTENTION
		issue = "A technical alternative is incomplete."
	elif not started:
		# Applicable but empty is Complete (base proposal remains mandatory elsewhere)
		status = STATUS_COMPLETE
		issue = ""
	else:
		status = STATUS_COMPLETE
		issue = ""
	return {
		"completed_items": len(alts) - len(invalid),
		"required_items": 0,
		"progress_text": f"{len(alts)} alternative(s)" if alts else "No alternatives proposed",
		"status": status,
		"issue": issue,
		"started": started,
	}


def _derive_integration(payload: dict[str, Any]) -> dict[str, Any]:
	conf = payload.get("integration_confirmation") if isinstance(payload.get("integration_confirmation"), dict) else {}
	confirmed = bool(conf.get("confirmed"))
	return {
		"completed_items": 1 if confirmed else 0,
		"required_items": 1,
		"progress_text": "Confirmed" if confirmed else "0 of 1 complete",
		"status": STATUS_COMPLETE if confirmed else STATUS_NOT_STARTED,
		"issue": "" if confirmed else "Integration responsibility has not been confirmed.",
		"started": confirmed,
	}


def derive_subsection_state(
	subsection: dict[str, Any],
	payload: dict[str, Any],
	*,
	section_def: dict[str, Any],
	responses: dict[str, Any] | None = None,
) -> dict[str, Any]:
	applicable, display_mode = resolve_subsection_applicability(
		subsection,
		payload=payload,
		section_def=section_def,
		responses=responses,
	)
	key = cstr(subsection.get("subsection_key"))
	title = cstr(subsection.get("title") or key)
	base = {
		"subsection_key": key,
		"title": title,
		"description": cstr(subsection.get("description") or ""),
		"renderer": cstr(subsection.get("renderer") or ""),
		"requirement_mode": cstr(subsection.get("requirement_mode") or MODE_REQUIRED),
		"display_mode": display_mode,
		"applicable": 1 if applicable else 0,
		"optional": 1 if display_mode == MODE_OPTIONAL else 0,
		"scope": cstr(subsection.get("scope") or "tender"),
	}
	if display_mode == MODE_EXCLUDED:
		return {
			**base,
			"status": STATUS_NOT_APPLICABLE,
			"progress_text": "Not applicable",
			"issue": "",
			"action_label": "",
			"started": False,
		}
	if not applicable:
		return {
			**base,
			"status": STATUS_NOT_APPLICABLE,
			"progress_text": "Not applicable",
			"issue": "",
			"action_label": "",
			"started": False,
		}

	renderer = cstr(subsection.get("renderer") or "")
	bucket = _sub_bucket(payload, key)
	if renderer == RENDERER_INTEGRATION or key == SUB_INTEGRATION:
		derived = _derive_integration(payload)
	elif renderer == RENDERER_ORG:
		derived = _derive_org(subsection, bucket)
	elif renderer == RENDERER_WORK_PLAN:
		derived = _derive_work_plan(subsection, bucket)
	elif renderer == RENDERER_TRAINING:
		derived = _derive_training(subsection, bucket)
	elif renderer == RENDERER_TESTING:
		derived = _derive_testing(subsection, bucket)
	elif renderer == RENDERER_RISKS:
		derived = _derive_risks(subsection, bucket)
	elif renderer == RENDERER_ALTERNATIVES:
		derived = _derive_alternatives(subsection, bucket)
	elif renderer == RENDERER_TRANSITION:
		derived = _derive_transition(subsection, bucket)
	elif renderer in (RENDERER_APPROACH, RENDERER_WARRANTY):
		derived = _derive_narrative_renderer(subsection, bucket)
	else:
		# Unsupported renderer with no questions → config error surfaced as Needs attention
		qs = subsection.get("questions") or []
		if not qs and renderer not in (RENDERER_WORK_PLAN, RENDERER_TRAINING, RENDERER_RISKS, RENDERER_ALTERNATIVES, RENDERER_INTEGRATION):
			derived = {
				"completed_items": 0,
				"required_items": 1,
				"progress_text": "0 of 1 complete",
				"status": STATUS_NEEDS_ATTENTION,
				"issue": "This subsection has no supported renderer or configured questions.",
				"started": False,
			}
		else:
			derived = _derive_narrative_renderer(subsection, bucket)

	status = derived["status"]
	if display_mode == MODE_OPTIONAL and status == STATUS_NOT_STARTED:
		# Optional never blocks; treat empty optional as Complete for section roll-up
		pass
	action = ACTION_START
	if status == STATUS_NEEDS_ATTENTION:
		action = ACTION_RESOLVE
	elif status == STATUS_COMPLETE:
		action = ACTION_REVIEW
	elif derived.get("started") or status == STATUS_IN_PROGRESS:
		action = ACTION_CONTINUE
	# Integration is confirmed on the review surface — Start until confirmed, Review after.
	# (Do not force Review while status is Not Started.)

	return {
		**base,
		"status": status,
		"progress_text": derived.get("progress_text") or "",
		"contractual_period_label": derived.get("contractual_period_label") or "",
		"issue": derived.get("issue") or "",
		"action_label": action,
		"started": bool(derived.get("started")),
		"completed_items": int(derived.get("completed_items") or 0),
		"required_items": int(derived.get("required_items") or 0),
	}


def technical_proposal_blocker_messages(
	section_def: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
) -> list[str]:
	payload_n = _normalize_payload(payload or {})
	msgs: list[str] = []
	for s in section_def.get("subsections") or []:
		if not isinstance(s, dict):
			continue
		st = derive_subsection_state(s, payload_n, section_def=section_def, responses=responses)
		if st.get("display_mode") != MODE_REQUIRED or not st.get("applicable"):
			continue
		if st["status"] in (STATUS_NEEDS_ATTENTION, STATUS_IN_PROGRESS, STATUS_NOT_STARTED):
			msg = cstr(st.get("issue") or "").strip()
			if not msg:
				msg = f"{st.get('title')}: required information is incomplete."
			msgs.append(msg)
	return msgs


def technical_proposal_first_action_url(
	published_tender_ref: str,
	section_def: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
) -> str:
	"""Deep-link checklist Resolve to the first incomplete applicable subsection (or review).

	Start/Continue/Review use ``portal_technical_proposal_url`` (section overview) so navigation
	matches Qualification and other multi-surface bidder sections.
	"""
	payload_n = _normalize_payload(payload or {})
	pub = cstr(published_tender_ref or "").strip()
	for s in section_def.get("subsections") or []:
		if not isinstance(s, dict):
			continue
		st = derive_subsection_state(s, payload_n, section_def=section_def, responses=responses)
		if not st.get("applicable") or st.get("display_mode") == MODE_EXCLUDED:
			continue
		if st.get("display_mode") == MODE_OPTIONAL and st["status"] == STATUS_NOT_STARTED:
			continue
		if st["status"] in (STATUS_NEEDS_ATTENTION, STATUS_IN_PROGRESS, STATUS_NOT_STARTED):
			key = st["subsection_key"]
			if key == SUB_INTEGRATION or st.get("renderer") == RENDERER_INTEGRATION:
				return portal_technical_proposal_review_url(pub)
			return portal_technical_proposal_subsection_url(pub, key)
	return portal_technical_proposal_url(pub)


def derive_technical_proposal_section_status(
	section_def: dict[str, Any] | None,
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
) -> str:
	if not isinstance(section_def, dict):
		return STATUS_NOT_APPLICABLE
	payload = _normalize_payload(payload or {})
	subs = [s for s in (section_def.get("subsections") or []) if isinstance(s, dict)]
	if not subs:
		return STATUS_NOT_STARTED
	states = [
		derive_subsection_state(s, payload, section_def=section_def, responses=responses) for s in subs
	]
	applicable_required = [
		st
		for st in states
		if st.get("applicable") and st.get("display_mode") == MODE_REQUIRED
	]
	if not applicable_required:
		# Only optional/na — still need integration if present as required
		return STATUS_NOT_APPLICABLE if all(not st.get("applicable") for st in states) else STATUS_COMPLETE

	if any(st["status"] == STATUS_NEEDS_ATTENTION for st in applicable_required):
		return STATUS_NEEDS_ATTENTION
	if all(st["status"] == STATUS_COMPLETE for st in applicable_required):
		return STATUS_COMPLETE
	if any(st.get("started") or st["status"] == STATUS_IN_PROGRESS for st in applicable_required):
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def _personnel_refs(responses: dict[str, Any] | None) -> list[dict[str, Any]]:
	"""Reference Key Personnel from Qualification without copying profiles."""
	qual = (responses or {}).get("qualification_and_capability")
	if not isinstance(qual, dict):
		return []
	people = qual.get("personnel") if isinstance(qual.get("personnel"), list) else []
	out = []
	for p in people:
		if not isinstance(p, dict):
			continue
		pid = cstr(p.get("person_id"))
		if not pid:
			continue
		out.append(
			{
				"person_id": pid,
				"full_name": cstr(p.get("full_name") or ""),
				"providing_member": cstr(p.get("providing_member") or ""),
			}
		)
	return out


def get_technical_proposal(published_tender_ref: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview,
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	if not section_def:
		frappe.throw(
			frappe._("Technical Proposal section is not available for this tender."),
			title="KT_TP_MISSING",
		)
	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	responses = _parse_json(bid.responses, {})
	payload = _normalize_payload(_payload(responses))
	overview = get_published_tender_overview(pub_ref)
	sealed = cstr(bid.status) == STATUS_SEALED

	rows = []
	req_complete = 0
	req_total = 0
	for sub in section_def.get("subsections") or []:
		if not isinstance(sub, dict):
			continue
		st = derive_subsection_state(sub, payload, section_def=section_def, responses=responses)
		if st.get("display_mode") == MODE_EXCLUDED:
			continue
		if st.get("applicable") and st.get("display_mode") == MODE_REQUIRED:
			req_total += 1
			if st["status"] == STATUS_COMPLETE:
				req_complete += 1
		if st.get("renderer") == RENDERER_INTEGRATION or st.get("subsection_key") == SUB_INTEGRATION:
			st["action_url"] = portal_technical_proposal_review_url(pub_ref) if st.get("applicable") else ""
		else:
			st["action_url"] = (
				portal_technical_proposal_subsection_url(pub_ref, st["subsection_key"])
				if st.get("applicable")
				else ""
			)
		mode = cstr(st.get("requirement_mode") or MODE_REQUIRED)
		if not st.get("applicable"):
			req_label = "Conditional" if mode == MODE_CONDITIONAL else (
				"Optional" if st.get("optional") else "Required"
			)
		elif st.get("optional") or mode == MODE_OPTIONAL:
			req_label = "Optional"
		elif mode == MODE_CONDITIONAL:
			req_label = "Conditional"
		else:
			req_label = "Required"
		rows.append(
			{
				"subsection_key": st["subsection_key"],
				"title": st["title"],
				"description": st["description"],
				"requirement_label": req_label,
				"progress_text": st["progress_text"],
				"status": st["status"],
				"issue": st.get("issue") or "",
				"action_label": st.get("action_label") or "",
				"action_url": st.get("action_url") or "",
				"optional": st.get("optional") or 0,
				"applicable": st.get("applicable") or 0,
			}
		)

	section_status = derive_technical_proposal_section_status(
		section_def, payload, responses=responses
	)
	progress_pct = int(round((100.0 * req_complete) / req_total)) if req_total else 0
	raw_instructions = cstr(section_def.get("bidder_instructions") or "").strip()
	bidder_instructions = (
		STITCH_BIDDER_INSTRUCTIONS
		if (not raw_instructions or raw_instructions == _LEGACY_BIDDER_INSTRUCTIONS)
		else raw_instructions
	)
	return {
		"published_tender_ref": pub_ref,
		"bid_id": bid.name,
		"bid_modified": cstr(getattr(bid, "modified", None) or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Technical Proposal and Implementation Plan"),
		"bidder_instructions": bidder_instructions,
		"workspace_url": portal_workspace_url(pub_ref),
		"review_url": portal_technical_proposal_review_url(pub_ref),
		"section_status": section_status,
		"progress_complete": req_complete,
		"progress_total": req_total,
		"progress_percent": progress_pct,
		"progress_label": f"{req_complete} of {req_total} required subsections complete",
		"subsections": rows,
		"read_only": 1 if sealed else 0,
		"bid_sealed": 1 if sealed else 0,
	}


def get_technical_proposal_subsection(published_tender_ref: str, subsection_key: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview,
		resolve_published_tender_backend,
	)

	skey = cstr(subsection_key or "").strip()
	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	if not section_def:
		frappe.throw(frappe._("Technical Proposal section is not available."), title="KT_TP_MISSING")
	subsection = next(
		(
			s
			for s in (section_def.get("subsections") or [])
			if isinstance(s, dict) and cstr(s.get("subsection_key")) == skey
		),
		None,
	)
	if not subsection:
		frappe.throw(frappe._("Unknown technical proposal subsection."), title="KT_TP_UNKNOWN")

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	responses = _parse_json(bid.responses, {})
	payload = _normalize_payload(_payload(responses))
	st = derive_subsection_state(subsection, payload, section_def=section_def, responses=responses)
	if st.get("display_mode") == MODE_EXCLUDED or not st.get("applicable"):
		frappe.throw(
			frappe._("This subsection is not applicable for the current submission."),
			title="KT_TP_NOT_APPLICABLE",
		)
	overview = get_published_tender_overview(pub_ref)
	bucket = _sub_bucket(payload, skey)
	# Enrich work-plan rows for Stitch matrix (labels, status, completion week).
	activities = _records_list(bucket, "activities")
	id_labels = {
		cstr(a.get("activity_id")): cstr(a.get("activity") or a.get("activity_id"))
		for a in activities
		if cstr(a.get("activity_id"))
	}
	known_ids = set(id_labels)
	for a in activities:
		end = calculate_completion_week(a.get("start_week"), a.get("duration_weeks"))
		if end is not None:
			a["completion_week"] = end
		dep = _normalize_dependency_id(a.get("dependency_id"))
		a["dependency_id"] = dep
		if not dep:
			a["dependency_label"] = ""
		elif dep in id_labels:
			a["dependency_label"] = id_labels[dep]
		else:
			# Never show internal ids; never look like "None" (em-dash).
			a["dependency_label"] = "Missing"
		a["row_status"] = _activity_row_status(a, known_ids=known_ids)
	# Testing / alternatives — Stitch Status column (derived, not stored).
	for stage in _records_list(bucket, "test_stages"):
		stage["row_status"] = _test_stage_row_status(stage)
	for alt in _records_list(bucket, "alternatives"):
		alt["row_status"] = _alternative_row_status(alt)
	# Default handover deliverables for transition when config/bucket empty.
	if cstr(subsection.get("renderer") or "") == RENDERER_TRANSITION:
		bucket = _ensure_handover_deliverables(bucket, subsection)
	sealed = cstr(bid.status) == STATUS_SEALED
	cbq = responses.get("confidential_business_questionnaire")
	cbq_form = {}
	if isinstance(cbq, dict):
		cbq_form = cbq.get("form") if isinstance(cbq.get("form"), dict) else cbq

	# Evidence refs: id + display title/type only (no hashes/paths).
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		_load_register,
		_project_item,
		portal_evidence_url,
	)

	register = _load_register(bid)
	saved_evidence = []
	for row in register.get("items") or []:
		if not isinstance(row, dict):
			continue
		proj = _project_item(dict(row))
		saved_evidence.append(
			{
				"evidence_id": cstr(proj.get("evidence_id") or ""),
				"title": cstr(proj.get("title") or ""),
				"evidence_type": cstr(proj.get("evidence_type") or ""),
				"file_name": cstr(proj.get("file_name") or ""),
			}
		)
	linked_ids = bucket.get("evidence_ids") if isinstance(bucket.get("evidence_ids"), list) else []
	linked_evidence = []
	by_id = {e["evidence_id"]: e for e in saved_evidence if e.get("evidence_id")}
	for eid in linked_ids:
		item = by_id.get(cstr(eid))
		if item:
			linked_evidence.append(item)

	return {
		"published_tender_ref": pub_ref,
		"bid_id": bid.name,
		"bid_modified": cstr(getattr(bid, "modified", None) or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"procuring_entity": cstr(overview.get("procuring_entity") or ""),
		"section_key": SECTION_KEY,
		"subsection_key": skey,
		"title": st["title"],
		"description": st["description"],
		"renderer": st["renderer"],
		"status": st["status"],
		"progress_text": st["progress_text"],
		"contractual_period_label": st.get("contractual_period_label") or "",
		"completed_items": int(st.get("completed_items") or 0),
		"required_items": int(st.get("required_items") or 0),
		"issue": st.get("issue") or "",
		"config": subsection,
		"bucket": bucket,
		"personnel_refs": _personnel_refs(responses),
		"selected_lots": _selected_lots(responses),
		"saved_evidence": saved_evidence,
		"linked_evidence": linked_evidence,
		"evidence_url": portal_evidence_url(pub_ref),
		"authoritative": {
			"bidder_legal_name": cstr(cbq_form.get("legal_name") or cbq_form.get("bidder_name") or ""),
			"tender_reference": pub_ref,
			"tender_title": cstr(overview.get("tender_title") or ""),
			"procuring_entity": cstr(overview.get("procuring_entity") or ""),
		},
		"personnel_category_url": (
			f"/tenders/{quote(pub_ref, safe='')}/sections/qualification_and_capability/key_personnel"
		),
		"section_url": portal_technical_proposal_url(pub_ref),
		"review_url": portal_technical_proposal_review_url(pub_ref),
		"workspace_url": portal_workspace_url(pub_ref),
		"read_only": 1 if sealed else 0,
		"bid_sealed": 1 if sealed else 0,
	}


def get_technical_proposal_review(published_tender_ref: str) -> dict[str, Any]:
	overview = get_technical_proposal(published_tender_ref)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	responses = _parse_json(bid.responses, {})
	payload = _normalize_payload(_payload(responses))
	conf = payload.get("integration_confirmation") or {}
	overview["integration_confirmation"] = {
		"confirmed": 1 if conf.get("confirmed") else 0,
		"user": cstr(conf.get("user") or ""),
		"timestamp": cstr(conf.get("timestamp") or ""),
	}
	overview["consolidated_summary"] = _build_consolidated_summary(payload)
	overview["section_url"] = portal_technical_proposal_url(pub_ref)
	overview["page_title"] = "Review Technical Proposal and Implementation Plan"
	return overview


def save_technical_proposal_subsection(
	published_tender_ref: str,
	subsection_key: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	incoming = payload if isinstance(payload, dict) else {}
	skey = cstr(subsection_key or "").strip()

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	if not section_def:
		frappe.throw(frappe._("Technical Proposal section is not available."), title="KT_TP_MISSING")
	subsection = next(
		(
			s
			for s in (section_def.get("subsections") or [])
			if isinstance(s, dict) and cstr(s.get("subsection_key")) == skey
		),
		None,
	)
	if not subsection:
		frappe.throw(frappe._("Unknown technical proposal subsection."), title="KT_TP_UNKNOWN")

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	doc = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	if expected_modified and cstr(doc.modified) != cstr(expected_modified):
		frappe.throw(
			frappe._("This draft was updated elsewhere. Reload and try again."),
			title="KT_TP_CONFLICT",
		)

	responses = _parse_json(doc.responses, {})
	section_payload = _normalize_payload(_payload(responses))
	st_before = derive_subsection_state(
		subsection, section_payload, section_def=section_def, responses=responses
	)
	if st_before.get("display_mode") == MODE_EXCLUDED or not st_before.get("applicable"):
		frappe.throw(frappe._("This subsection is not applicable."), title="KT_TP_NOT_APPLICABLE")

	bucket_in = incoming.get("bucket") if isinstance(incoming.get("bucket"), dict) else incoming
	if not isinstance(bucket_in, dict):
		bucket_in = {}
	bucket_in.pop("status", None)

	# Normalize activities
	acts = bucket_in.get("activities")
	if isinstance(acts, list):
		for a in acts:
			if not isinstance(a, dict):
				continue
			if not cstr(a.get("activity_id")):
				a["activity_id"] = f"act-{uuid.uuid4().hex[:10]}"
			a["dependency_id"] = _normalize_dependency_id(a.get("dependency_id"))
			end = calculate_completion_week(a.get("start_week"), a.get("duration_weeks"))
			if end is not None:
				a["completion_week"] = end

	section_payload["subsections"][skey] = bucket_in
	if isinstance(incoming.get("flags"), dict):
		section_payload["flags"].update(incoming["flags"])

	responses[SECTION_KEY] = section_payload
	doc.responses = json.dumps(responses)
	_append_audit(
		doc,
		"section_saved",
		{"section_key": SECTION_KEY, "subsection_key": skey, "published_tender_ref": pub_ref},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return get_technical_proposal_subsection(pub_ref, skey)


def confirm_integration_responsibility(
	published_tender_ref: str,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Record integration confirmation (section completion — does not seal the bid)."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	if not section_def:
		frappe.throw(frappe._("Technical Proposal section is not available."), title="KT_TP_MISSING")

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	doc = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	if expected_modified and cstr(doc.modified) != cstr(expected_modified):
		frappe.throw(
			frappe._("This draft was updated elsewhere. Reload and try again."),
			title="KT_TP_CONFLICT",
		)

	responses = _parse_json(doc.responses, {})
	section_payload = _normalize_payload(_payload(responses))
	section_payload["integration_confirmation"] = {
		"confirmed": 1,
		"user": frappe.session.user,
		"timestamp": str(now_datetime()),
	}
	# Also mark subsection bucket for overview consistency
	section_payload["subsections"][SUB_INTEGRATION] = {"confirmed": 1}
	responses[SECTION_KEY] = section_payload
	doc.responses = json.dumps(responses)
	_append_audit(
		doc,
		"section_saved",
		{
			"section_key": SECTION_KEY,
			"event": "integration_confirmed",
			"published_tender_ref": pub_ref,
			"user": frappe.session.user,
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_technical_proposal_review(pub_ref)
