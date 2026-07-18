# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-01 Tender Configuration Home payload (C1-M3 §11)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import (
	STATUS_COMPLETED,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_READY_FOR_REVIEW,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	HANDOFF_ROUTES,
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NEEDS_ATTENTION,
	STEP_NOT_AVAILABLE,
	STEP_NOT_STARTED,
	get_steps_for_family,
	merge_step_rows,
)

# Human-readable strip / home status (never raw lifecycle enums)
_STATUS_LABELS = {
	STATUS_IN_PROGRESS: "In progress",
	STATUS_NEEDS_ATTENTION: "Needs attention",
	STATUS_READY_FOR_REVIEW: "Ready for review",
	STATUS_UNDER_REVIEW: "Under review",
	STATUS_READY_FOR_PUBLICATION: "Ready for publication",
	STATUS_COMPLETED: "Completed",
}

_STATUS_TONE = {
	STATUS_IN_PROGRESS: "in_progress",
	STATUS_NEEDS_ATTENTION: "needs_attention",
	STATUS_READY_FOR_REVIEW: "ready_for_review",
	STATUS_UNDER_REVIEW: "under_review",
	STATUS_READY_FOR_PUBLICATION: "ready_for_publication",
	STATUS_COMPLETED: "completed",
}

# Next-action copy from UI-01 §5
_NEXT_BY_STEP = {
	"CFG-01": {
		"label": "Complete Tender Profile",
		"reason": "Confirm the basic tender identity and setup context before completing detailed configuration.",
		"button_label": "Continue",
	},
	"CFG-02": {
		"label": "Complete Tender Data Sheet",
		"reason": "Tender-specific instructions and parameters are still missing.",
		"button_label": "Continue",
	},
	"CFG-03": {
		"label": "Fix IT Requirements",
		"reason": "Some requirements are missing bidder response, evidence, or acceptance details.",
		"button_label": "Fix",
	},
	"CFG-04": {
		"label": "Complete Implementation Schedule",
		"reason": "The delivery approach, milestones, or acceptance checkpoints are still incomplete.",
		"button_label": "Continue",
	},
}

_DEFAULT_STEP_NEXT = {
	"label": "Continue configuration",
	"reason": "Complete the remaining configuration steps before readiness and review.",
	"button_label": "Continue",
}


def _parse_steps_state(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except (TypeError, ValueError):
			return {}
	return {}


def _method_label(raw: str | None) -> str:
	method = cstr(raw or "").strip()
	if not method:
		return ""
	# Display-friendly: Open Tender → Open National Tender when short seed value
	if method.lower() in ("open tender", "ont"):
		return "Open National Tender"
	return method


def _entity_display_name(doc) -> str:
	"""Prefer human name; never leave raw PE-* codes in the strip when a name exists."""
	name = cstr(getattr(doc, "procuring_entity_name", None) or "").strip()
	code = cstr(getattr(doc, "procuring_entity_code", None) or "").strip()
	if name and not name.upper().startswith("PE-"):
		return name
	lookup = code or name
	if lookup and frappe.db.exists("Procuring Entity", lookup):
		resolved = frappe.db.get_value("Procuring Entity", lookup, "entity_name")
		if resolved:
			return cstr(resolved)
	if name:
		return name
	return code


def build_configuration_context(doc) -> dict[str, Any]:
	"""Shared 8-cell strip DTO for UI-01 and all CFG/WF wizard pages (C1-M3 §4)."""
	status = cstr(doc.status or STATUS_IN_PROGRESS)
	blockers = int(doc.blocker_count or 0)
	warnings = int(doc.warning_count or 0)
	return {
		"procurement_package_ref": cstr(doc.procurement_package_ref or ""),
		"procurement_title": cstr(doc.tender_title or doc.package_title or ""),
		"procuring_entity_name": _entity_display_name(doc),
		"procurement_method_label": _method_label(doc.procurement_method),
		"std_family_label": cstr(doc.std_family_label or ""),
		"standard_tender_document_label": cstr(getattr(doc, "std_document_label", None) or ""),
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"blocker_count": blockers,
		"warning_count": warnings,
		"status_tone": _STATUS_TONE.get(status, "in_progress"),
		"issues_label": (
			f"{blockers} Blockers / {warnings} Warnings"
			if blockers or warnings
			else "None"
		),
	}


def _pick_next_action(steps: list[dict[str, Any]], doc) -> dict[str, Any]:
	# Prefer Needs attention, then first incomplete / not started / in progress
	attention = next((s for s in steps if s["status_label"] == STEP_NEEDS_ATTENTION), None)
	if attention:
		copy = _NEXT_BY_STEP.get(attention["id"], {
			"label": f"Fix {attention['title']}",
			"reason": "This step has blockers or warnings that require attention.",
			"button_label": "Fix",
		})
		return {
			"label": copy["label"],
			"reason": copy["reason"],
			"button_label": copy["button_label"],
			"route": attention["route"],
			"step_id": attention["id"],
		}

	incomplete = next(
		(
			s
			for s in steps
			if s["status_label"]
			in (STEP_NOT_STARTED, "In progress", STEP_NOT_AVAILABLE)
			and s["status_label"] != STEP_COMPLETE
		),
		None,
	)
	# Skip Not available yet for primary CTA — find first startable
	startable = next(
		(
			s
			for s in steps
			if s["status_label"] in (STEP_NOT_STARTED, "In progress")
		),
		None,
	)
	target = startable or incomplete
	if target and target["status_label"] != STEP_NOT_AVAILABLE:
		copy = _NEXT_BY_STEP.get(target["id"], _DEFAULT_STEP_NEXT)
		btn = target["action_label"] if target["action_label"] != "View required step" else "Continue"
		return {
			"label": copy["label"] if target["id"] in _NEXT_BY_STEP else f"Complete {target['title']}",
			"reason": copy["reason"] if target["id"] in _NEXT_BY_STEP else _DEFAULT_STEP_NEXT["reason"],
			"button_label": btn if target["id"] not in _NEXT_BY_STEP else copy["button_label"],
			"route": target["route"],
			"step_id": target["id"],
		}

	# All configuration steps complete — workflow gates (§5)
	status = cstr(doc.status or "")
	if status in (STATUS_IN_PROGRESS, STATUS_NEEDS_ATTENTION):
		return {
			"label": "Run Readiness Check",
			"reason": "Check the configuration for blockers and warnings before review.",
			"button_label": "Run Readiness Check",
			"route": HANDOFF_ROUTES["readiness_check"],
			"step_id": None,
		}
	if status == STATUS_READY_FOR_REVIEW:
		return {
			"label": "Submit for Review",
			"reason": "The configuration has passed readiness checks and can be sent for review.",
			"button_label": "Submit for Review",
			"route": HANDOFF_ROUTES["review_status"],
			"step_id": None,
		}
	if status == STATUS_UNDER_REVIEW:
		return {
			"label": "Open Review Workspace",
			"reason": "The configuration is under review.",
			"button_label": "Open Review Workspace",
			"route": HANDOFF_ROUTES["review_status"],
			"step_id": None,
		}
	if status == STATUS_READY_FOR_PUBLICATION:
		return {
			"label": "Mark Ready for Publication",
			"reason": "The package is confirmed and can be handed to Tender Management.",
			"button_label": "Mark Ready for Publication",
			"route": HANDOFF_ROUTES["publication_handoff"],
			"step_id": None,
		}
	if status == STATUS_COMPLETED:
		return {
			"label": "Open in Tender Management",
			"reason": "This configuration has been handed off.",
			"button_label": "Open in Tender Management",
			"route": HANDOFF_ROUTES["publication_handoff"],
			"step_id": None,
		}
	return {
		"label": "Submit for Review",
		"reason": "The configuration has passed readiness checks and can be sent for review.",
		"button_label": "Submit for Review",
		"route": HANDOFF_ROUTES["review_status"],
		"step_id": None,
	}


def _build_handoff(doc, steps: list[dict[str, Any]]) -> dict[str, Any]:
	all_complete = all(s["status_label"] == STEP_COMPLETE for s in steps)
	status = cstr(doc.status or "")
	blockers = int(doc.blocker_count or 0)

	if blockers > 0:
		readiness_status = "Blockers found"
		readiness_action = "View Readiness Report"
		readiness_route = HANDOFF_ROUTES["readiness_check"]
	elif all_complete and status in (
		STATUS_READY_FOR_REVIEW,
		STATUS_UNDER_REVIEW,
		STATUS_READY_FOR_PUBLICATION,
		STATUS_COMPLETED,
	):
		readiness_status = "Passed"
		readiness_action = "View Readiness Report"
		readiness_route = HANDOFF_ROUTES["readiness_check"]
	elif all_complete:
		readiness_status = "Not run"
		readiness_action = "Run Readiness Check"
		readiness_route = HANDOFF_ROUTES["readiness_check"]
	else:
		readiness_status = "Not run"
		readiness_action = None
		readiness_route = None

	if status == STATUS_UNDER_REVIEW:
		review_status, review_action, review_route = (
			"Under review",
			"Open Review Workspace",
			HANDOFF_ROUTES["review_status"],
		)
	elif status in (STATUS_READY_FOR_PUBLICATION, STATUS_COMPLETED):
		review_status, review_action, review_route = (
			"Approved",
			"Open Review Workspace",
			HANDOFF_ROUTES["review_status"],
		)
	elif status == STATUS_READY_FOR_REVIEW:
		review_status, review_action, review_route = (
			"Not submitted",
			"Submit for Review",
			HANDOFF_ROUTES["review_status"],
		)
	else:
		review_status, review_action, review_route = "Not submitted", None, None

	if status in (STATUS_READY_FOR_PUBLICATION, STATUS_COMPLETED):
		preview_status = "Confirmed" if status == STATUS_COMPLETED else "Not confirmed"
		preview_action = "Open Tender Document Preview"
		preview_route = HANDOFF_ROUTES["tender_document_preview"]
	elif status == STATUS_UNDER_REVIEW or (
		status == STATUS_READY_FOR_REVIEW and readiness_status == "Passed"
	):
		preview_status = "Available after review"
		preview_action = None
		preview_route = None
	else:
		preview_status = "Available after review"
		preview_action = None
		preview_route = None

	if status == STATUS_COMPLETED:
		pub_status, pub_action, pub_route = (
			"Handed off",
			"Open in Tender Management",
			HANDOFF_ROUTES["publication_handoff"],
		)
	elif status == STATUS_READY_FOR_PUBLICATION:
		pub_status, pub_action, pub_route = (
			"Ready for handoff",
			"Mark Ready for Publication",
			HANDOFF_ROUTES["publication_handoff"],
		)
	else:
		pub_status, pub_action, pub_route = "Available after preview", None, None

	return {
		"readiness_check": {
			"label": "Readiness Check",
			"description": "Checks all configuration steps and shows blockers or warnings before review.",
			"status_label": readiness_status,
			"action_label": readiness_action,
			"route": readiness_route,
		},
		"review_status": {
			"label": "Review Status",
			"description": "Shows whether the configuration has been submitted, returned, or approved by reviewers.",
			"status_label": review_status,
			"action_label": review_action,
			"route": review_route,
		},
		"tender_document_preview": {
			"label": "Tender Document Preview",
			"description": (
				"Opens the generated tender document after review approval so the package "
				"can be confirmed before handoff."
			),
			"status_label": preview_status,
			"action_label": preview_action,
			"route": preview_route,
		},
		"publication_handoff": {
			"label": "Publication Handoff",
			"description": (
				"Marks the approved and confirmed package ready for Tender Management; "
				"this does not publish the tender."
			),
			"status_label": pub_status,
			"action_label": pub_action,
			"route": pub_route,
		},
	}


def get_configuration_home(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	catalog = get_steps_for_family(doc.std_family_key)
	steps_state = _parse_steps_state(getattr(doc, "steps_state", None))
	steps = merge_step_rows(catalog, steps_state)
	context = build_configuration_context(doc)
	next_action = _pick_next_action(steps, doc)
	handoff = _build_handoff(doc, steps)

	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": context["procurement_package_ref"],
		"procurement_title": context["procurement_title"],
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"configuration_status_label": context["configuration_status_label"],
		"blocker_count": context["blocker_count"],
		"warning_count": context["warning_count"],
		"context": context,
		"next_action": next_action,
		"configuration_steps": steps,
		"handoff": handoff,
	}


def default_steps_state_for_seed(*, needs_attention: bool = False) -> dict[str, Any]:
	"""Deterministic steps_state for UI-00/UI-01 seeds."""
	if not needs_attention:
		return {
			"CFG-01": {"status_label": STEP_NOT_STARTED},
		}
	return steps_state_showcase_nine_cards()


def steps_state_all_complete() -> dict[str, Any]:
	"""All CFG-01…09 Complete (lifecycle handoff demos)."""
	return {
		f"CFG-0{i}": {"status_label": STEP_COMPLETE, "last_updated_label": "Yesterday"}
		for i in range(1, 10)
	}


def steps_state_showcase_nine_cards() -> dict[str, Any]:
	"""
	One home surface showing every allowed step status across CFG-01…09
	(C1-M3 design mock layout; pack labels — never Locked/Ready).
	"""
	return {
		"CFG-01": {"status_label": STEP_COMPLETE, "last_updated_label": "2h ago"},
		"CFG-02": {"status_label": STEP_COMPLETE, "last_updated_label": "5h ago"},
		"CFG-03": {
			"status_label": STEP_NEEDS_ATTENTION,
			"blocker_count": 2,
			"warning_count": 1,
			"last_updated_label": "Today",
		},
		"CFG-04": {
			"status_label": STEP_IN_PROGRESS,
			"last_updated_label": "Today",
			"progress_pct": 67,
		},
		"CFG-05": {"status_label": STEP_NOT_STARTED},
		"CFG-06": {"status_label": STEP_NOT_STARTED},
		"CFG-07": {"status_label": STEP_NOT_STARTED},
		"CFG-08": {"status_label": STEP_NOT_STARTED},
		"CFG-09": {"status_label": STEP_NOT_AVAILABLE},
	}


def steps_state_focus_cfg(step_id: str, *, status_label: str | None = None) -> dict[str, Any]:
	"""
	Build steps_state where prior steps are Complete, focus step uses status_label
	(default Not started), later steps Not available yet — for per-CFG mockups.
	"""
	ids = [f"CFG-0{i}" for i in range(1, 10)]
	if step_id not in ids:
		raise ValueError(f"Unknown step_id {step_id}")
	focus_status = status_label or STEP_NOT_STARTED
	idx = ids.index(step_id)
	out: dict[str, Any] = {}
	for i, sid in enumerate(ids):
		if i < idx:
			out[sid] = {"status_label": STEP_COMPLETE, "last_updated_label": "Yesterday"}
		elif i == idx:
			row: dict[str, Any] = {"status_label": focus_status, "last_updated_label": "Today"}
			if focus_status == STEP_NEEDS_ATTENTION:
				row["blocker_count"] = 2
				row["warning_count"] = 1
			if focus_status == STEP_IN_PROGRESS:
				row["progress_pct"] = 67
			out[sid] = row
		else:
			out[sid] = {"status_label": STEP_NOT_AVAILABLE}
	return out
