# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-02 Tender Data Sheet GET/POST (C2-CFG2 §13)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	_parse_steps_state,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NEEDS_ATTENTION,
	STEP_NOT_STARTED,
)
from kentender_procurement.tender_configurations.services.profile import LOT_MULTIPLE

YES = "Yes"
NO = "No"

CLARIFICATION_METHODS = (
	"E-Procurement Portal",
	"Official Email",
	"Physical Submission",
	"As stated in tender notice",
)
SUBMISSION_CHANNELS = (
	"E-Procurement Portal",
	"Physical Submission",
	"Hybrid Submission",
)
SUBMISSION_LANGUAGES = ("English", "Swahili")
TENDER_CURRENCIES = ("KES", "USD")
RESERVATION_CATEGORIES = (
	"Youth",
	"Women",
	"Persons with Disabilities",
	"Local Contractors / Suppliers",
	"Other statutory reservation",
)
SECURITY_TYPES = (
	"Tender Security",
	"Tender-Securing Declaration",
	"Not Required",
)
PREFERENCE_BASES = (
	"Local supplier / contractor preference",
	"Citizen contractor / supplier preference",
	"Other allowed statutory preference",
)
OPENING_METHODS = (
	"Electronic Opening",
	"Physical Opening",
	"Hybrid Opening",
)
ELIGIBLE_TENDERS = (
	"Open to all eligible tenderers",
	"Restricted",
)
VALIDITY_UNITS = ("days", "weeks", "months")

GROUP_CATALOG: list[dict[str, str]] = [
	{
		"group_key": "communication",
		"group_label": "Tender Communication",
		"description": (
			"Define contact officer, clarification method, and pre-tender meeting information."
		),
	},
	{
		"group_key": "key_dates",
		"group_label": "Key Dates",
		"description": "Set submission, opening, and validity dates for this tender.",
	},
	{
		"group_key": "submission",
		"group_label": "Submission Rules",
		"description": (
			"Confirm channel, language, currency, alternatives, lots, and joint venture rules."
		),
	},
	{
		"group_key": "eligibility",
		"group_label": "Eligibility and Participation",
		"description": "Confirm who may participate and whether any reservation applies.",
	},
	{
		"group_key": "security",
		"group_label": "Tender Security",
		"description": (
			"Define whether tender security is required and the accepted security type."
		),
	},
	{
		"group_key": "preferences",
		"group_label": "Preferences and Reservations",
		"description": (
			"State whether margin of preference applies and what evidence is required."
		),
	},
	{
		"group_key": "bid_opening",
		"group_label": "Bid Opening",
		"description": "Confirm how and where the tender opening will take place.",
	},
]

# Keys that may be posted (lots_allowed / publication date are read-only server-side)
EDITABLE_KEYS = frozenset(
	{
		"contact_officer",
		"contact_email",
		"clarification_submission_method",
		"clarification_deadline",
		"pre_tender_meeting",
		"pre_tender_meeting_details",
		"tender_submission_deadline",
		"tender_opening_datetime",
		"bid_validity_period",
		"bid_validity_unit",
		"submission_channel",
		"submission_language",
		"tender_currency",
		"alternative_tenders_allowed",
		"joint_ventures_allowed",
		"eligible_tenderers",
		"reserved_procurement",
		"reservation_category",
		"local_participation_requirement",
		"tender_security_required",
		"tender_security_type",
		"tender_security_amount",
		"tender_security_currency",
		"tender_security_validity_period",
		"tender_security_validity_unit",
		"performance_security_required",
		"margin_of_preference_applies",
		"preference_basis",
		"preference_evidence_required",
		"opening_method",
		"opening_location",
		"opening_attendance_allowed",
		"opening_notes",
		"professional_indemnity_required",
		"professional_indemnity_amount",
		"professional_indemnity_evidence",
	}
)

BANNED_POST_KEYS = frozenset(
	{
		"lots_allowed",
		"tender_publication_date",
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
	}
)


def _parse_tds_values(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return {}
	if not isinstance(raw, dict):
		return {}
	out: dict[str, Any] = {}
	for key, val in raw.items():
		k = cstr(key).strip()
		if not k:
			continue
		if isinstance(val, (dict, list)):
			continue
		out[k] = cstr(val).strip() if val is not None else ""
	return out


def _v(values: dict[str, Any], key: str) -> str:
	return cstr(values.get(key) or "").strip()


def _yn(values: dict[str, Any], key: str) -> str:
	raw = _v(values, key).lower()
	if raw in ("yes", "y", "true", "1"):
		return YES
	if raw in ("no", "n", "false", "0"):
		return NO
	return _v(values, key)


def lots_allowed_from_profile(doc) -> str:
	lot = cstr(getattr(doc, "lot_structure", None) or "").strip()
	return YES if lot == LOT_MULTIPLE else NO


def publication_date_display(doc) -> str:
	# No publication workflow ownership yet — placeholder.
	return "—"


def _required_conditions(values: dict[str, Any]) -> list[dict[str, Any]]:
	"""Exit conditions for can_continue / progress (expand with conditionals)."""
	conds: list[dict[str, Any]] = []

	def add(key: str, label: str, met: bool, message: str):
		conds.append({"key": key, "label": label, "met": met, "message": message})

	add(
		"contact_officer",
		"Contact Officer",
		bool(_v(values, "contact_officer")),
		"Add a contact officer before continuing.",
	)
	add(
		"contact_email",
		"Contact Email",
		bool(_v(values, "contact_email")),
		"Add a contact email before continuing.",
	)
	method = _v(values, "clarification_submission_method")
	add(
		"clarification_submission_method",
		"Clarification Submission Method",
		bool(method),
		"Confirm the clarification submission method before continuing.",
	)
	if method:
		add(
			"clarification_deadline",
			"Clarification Deadline",
			bool(_v(values, "clarification_deadline")),
			"Add a clarification deadline before continuing.",
		)
	meeting = _yn(values, "pre_tender_meeting")
	add(
		"pre_tender_meeting",
		"Pre-tender Meeting",
		meeting in (YES, NO),
		"Confirm whether a pre-tender meeting is required before continuing.",
	)
	if meeting == YES:
		add(
			"pre_tender_meeting_details",
			"Pre-tender Meeting Details",
			bool(_v(values, "pre_tender_meeting_details")),
			"Add pre-tender meeting details before continuing.",
		)

	add(
		"tender_submission_deadline",
		"Tender Submission Deadline",
		bool(_v(values, "tender_submission_deadline")),
		"Submission deadline missing",
	)
	add(
		"tender_opening_datetime",
		"Tender Opening Date and Time",
		bool(_v(values, "tender_opening_datetime")),
		"Add a tender opening date and time before continuing.",
	)
	validity = _v(values, "bid_validity_period")
	add(
		"bid_validity_period",
		"Bid Validity Period",
		bool(validity) and validity.isdigit() and int(validity) > 0,
		"Add a bid validity period before continuing.",
	)

	add(
		"submission_channel",
		"Submission Channel",
		bool(_v(values, "submission_channel")),
		"Confirm the submission channel before continuing.",
	)
	add(
		"submission_language",
		"Submission Language",
		bool(_v(values, "submission_language")),
		"Confirm the submission language before continuing.",
	)
	add(
		"tender_currency",
		"Tender Currency",
		bool(_v(values, "tender_currency")),
		"Confirm the tender currency before continuing.",
	)
	alt = _yn(values, "alternative_tenders_allowed")
	add(
		"alternative_tenders_allowed",
		"Alternative Tenders Allowed",
		alt in (YES, NO),
		"Confirm whether alternative tenders are allowed before continuing.",
	)
	jv = _yn(values, "joint_ventures_allowed")
	add(
		"joint_ventures_allowed",
		"Joint Ventures Allowed",
		jv in (YES, NO),
		"Confirm whether joint ventures are allowed before continuing.",
	)

	add(
		"eligible_tenderers",
		"Eligible Tenderers",
		bool(_v(values, "eligible_tenderers")),
		"Confirm eligible tenderers before continuing.",
	)
	reserved = _yn(values, "reserved_procurement")
	add(
		"reserved_procurement",
		"Reserved Procurement",
		reserved in (YES, NO),
		"Confirm whether reserved procurement applies before continuing.",
	)
	if reserved == YES:
		add(
			"reservation_category",
			"Reservation Category",
			bool(_v(values, "reservation_category")),
			"Select a reservation category before continuing.",
		)

	sec_req = _yn(values, "tender_security_required")
	add(
		"tender_security_required",
		"Tender Security Required",
		sec_req in (YES, NO),
		"Confirm whether tender security is required before continuing.",
	)
	if sec_req == YES:
		add(
			"tender_security_type",
			"Tender Security Type",
			bool(_v(values, "tender_security_type")),
			"Select a tender security type before continuing.",
		)
		amt = _v(values, "tender_security_amount")
		add(
			"tender_security_amount",
			"Tender Security Amount",
			bool(amt),
			"Add a tender security amount before continuing.",
		)
		sec_val = _v(values, "tender_security_validity_period")
		add(
			"tender_security_validity_period",
			"Tender Security Validity Period",
			bool(sec_val) and sec_val.replace(".", "", 1).isdigit(),
			"Add a tender security validity period before continuing.",
		)

	pref = _yn(values, "margin_of_preference_applies")
	add(
		"margin_of_preference_applies",
		"Margin of Preference Applies",
		pref in (YES, NO),
		"Confirm whether margin of preference applies before continuing.",
	)
	if pref == YES:
		add(
			"preference_basis",
			"Preference Basis",
			bool(_v(values, "preference_basis")),
			"Select a preference basis before continuing.",
		)
		add(
			"preference_evidence_required",
			"Preference Evidence Required",
			bool(_v(values, "preference_evidence_required")),
			"Describe preference evidence requirements before continuing.",
		)

	add(
		"opening_method",
		"Opening Method",
		bool(_v(values, "opening_method")),
		"Confirm the opening method before continuing.",
	)
	add(
		"opening_location",
		"Opening Location / Portal",
		bool(_v(values, "opening_location")),
		"Opening location missing",
	)
	attend = _yn(values, "opening_attendance_allowed")
	add(
		"opening_attendance_allowed",
		"Opening Attendance Allowed",
		attend in (YES, NO),
		"Confirm whether opening attendance is allowed before continuing.",
	)
	return conds


GROUP_FIELD_KEYS: dict[str, tuple[str, ...]] = {
	"communication": (
		"contact_officer",
		"contact_email",
		"clarification_submission_method",
		"clarification_deadline",
		"pre_tender_meeting",
		"pre_tender_meeting_details",
	),
	"key_dates": (
		"tender_submission_deadline",
		"tender_opening_datetime",
		"bid_validity_period",
	),
	"submission": (
		"submission_channel",
		"submission_language",
		"tender_currency",
		"alternative_tenders_allowed",
		"joint_ventures_allowed",
	),
	"eligibility": (
		"eligible_tenderers",
		"reserved_procurement",
		"reservation_category",
	),
	"security": (
		"tender_security_required",
		"tender_security_type",
		"tender_security_amount",
		"tender_security_validity_period",
		"performance_security_required",
	),
	"preferences": (
		"margin_of_preference_applies",
		"preference_basis",
		"preference_evidence_required",
	),
	"bid_opening": (
		"opening_method",
		"opening_location",
		"opening_attendance_allowed",
	),
}


def _action_for_status(status: str) -> str:
	return {
		STEP_COMPLETE: "Review",
		STEP_NEEDS_ATTENTION: "Fix",
		STEP_IN_PROGRESS: "Continue",
		STEP_NOT_STARTED: "Start",
	}.get(status, "Start")


def _build_groups(values: dict[str, Any], conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
	by_key = {c["key"]: c for c in conditions}
	groups: list[dict[str, Any]] = []
	for meta in GROUP_CATALOG:
		gkey = meta["group_key"]
		field_keys = GROUP_FIELD_KEYS.get(gkey, ())
		relevant = [by_key[k] for k in field_keys if k in by_key]
		# Also include conditional keys that may not be in static list if present
		if gkey == "communication" and "clarification_deadline" in by_key:
			if by_key["clarification_deadline"] not in relevant:
				relevant.append(by_key["clarification_deadline"])
		if gkey == "communication" and "pre_tender_meeting_details" in by_key:
			if by_key["pre_tender_meeting_details"] not in relevant:
				relevant.append(by_key["pre_tender_meeting_details"])

		unmet = [c for c in relevant if not c["met"]]
		any_filled = any(_v(values, k) for k in field_keys if k in EDITABLE_KEYS or k in values)

		if not relevant and not any_filled:
			status = STEP_NOT_STARTED
			issue = "Required section not started"
		elif not unmet and relevant:
			status = STEP_COMPLETE
			issue = "—"
		elif unmet and not any_filled:
			status = STEP_NOT_STARTED
			issue = unmet[0]["message"] if unmet else "Required section not started"
			# Prefer pack sample for empty security
			if gkey == "security" and not any_filled:
				issue = "Required section not started"
		elif unmet:
			status = STEP_NEEDS_ATTENTION
			issue = unmet[0]["message"]
		else:
			status = STEP_IN_PROGRESS
			issue = "1 warning" if any_filled else "—"

		# Refine: some filled + unmet → Needs attention; some filled + no unmet but incomplete optionals → In progress
		if any_filled and unmet:
			status = STEP_NEEDS_ATTENTION
		elif any_filled and not unmet and status != STEP_COMPLETE:
			status = STEP_IN_PROGRESS
			issue = "—"

		groups.append(
			{
				"group_key": gkey,
				"group_label": meta["group_label"],
				"description": meta["description"],
				"status_label": status,
				"issue_summary": issue,
				"action_label": _action_for_status(status),
			}
		)
	return groups


def validate_tds_values(values: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	conditions = _required_conditions(values)
	blockers = [
		{"code": c["key"], "message": c["message"]} for c in conditions if not c["met"]
	]
	warnings: list[dict[str, str]] = []
	# Soft warning: opening notes empty is fine; language not English optional warn skipped
	can_continue = len(blockers) == 0
	return blockers, warnings, can_continue


def tds_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	"""For step_progress CFG-02 builder."""
	values = _parse_tds_values(getattr(doc, "tds_values", None))
	values = normalize_display_values(doc, values)
	conds = _required_conditions(values)
	return [{"key": c["key"], "label": c["label"], "met": c["met"]} for c in conds]


# Defaults injected for display only — do not count as user progress.
_PROGRESS_IGNORE_KEYS = frozenset(
	{
		"bid_validity_unit",
		"tender_security_validity_unit",
		"tender_security_currency",
		"lots_allowed",
		"tender_publication_date",
	}
)


def tds_has_progress(values: dict[str, Any]) -> bool:
	"""True when the officer has entered at least one editable TDS value."""
	for key, val in (values or {}).items():
		if key not in EDITABLE_KEYS or key in _PROGRESS_IGNORE_KEYS:
			continue
		if cstr(val).strip():
			return True
	return False


def normalize_display_values(doc, values: dict[str, Any]) -> dict[str, Any]:
	out = dict(values)
	out["lots_allowed"] = lots_allowed_from_profile(doc)
	out["tender_publication_date"] = publication_date_display(doc)
	if not out.get("bid_validity_unit"):
		out["bid_validity_unit"] = "days"
	if not out.get("tender_security_validity_unit"):
		out["tender_security_validity_unit"] = "days"
	if not out.get("tender_security_currency"):
		out["tender_security_currency"] = "KES"
	# Normalize Yes/No
	for key in (
		"pre_tender_meeting",
		"alternative_tenders_allowed",
		"joint_ventures_allowed",
		"reserved_procurement",
		"tender_security_required",
		"performance_security_required",
		"margin_of_preference_applies",
		"opening_attendance_allowed",
	):
		if key in out and out[key]:
			# Performance security also accepts authorised "Not applicable".
			if key == "performance_security_required":
				raw = cstr(out[key]).strip().lower()
				if raw in ("not applicable", "n/a", "na"):
					out[key] = "Not applicable"
				else:
					out[key] = _yn(out, key) or out[key]
			else:
				out[key] = _yn(out, key)
	return out


def _sync_cfg02_steps_state(doc, *, can_continue: bool, has_any_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-02") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_any_progress:
		# Prefer Needs attention when blockers remain and some data entered
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-02"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_tds(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	values = normalize_display_values(doc, _parse_tds_values(getattr(doc, "tds_values", None)))
	blockers, warnings, can_continue = validate_tds_values(values)
	conditions = _required_conditions(values)
	groups = _build_groups(values, conditions)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	has_progress = tds_has_progress(values)

	return {
		"configuration_id": doc.name,
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"has_progress": has_progress,
		"tds_groups": groups,
		"tds_values": values,
		"context": context,
		"options": {
			"clarification_submission_method": list(CLARIFICATION_METHODS),
			"submission_channel": list(SUBMISSION_CHANNELS),
			"submission_language": list(SUBMISSION_LANGUAGES),
			"tender_currency": list(TENDER_CURRENCIES),
			"eligible_tenderers": list(ELIGIBLE_TENDERS),
			"reservation_category": list(RESERVATION_CATEGORIES),
			"tender_security_type": list(SECURITY_TYPES),
			"preference_basis": list(PREFERENCE_BASES),
			"opening_method": list(OPENING_METHODS),
			"bid_validity_unit": list(VALIDITY_UNITS),
			"tender_security_validity_unit": list(VALIDITY_UNITS),
		},
		"guidance": {
			"title": "Tender Data Sheet Guidance",
			"body": (
				"Complete only the tender-specific instructions required for this procurement. "
				"The standard Instructions to Tenderers remain controlled by the selected "
				"Standard Tender Document and are not edited here."
			),
			"what_this_affects": (
				"Submission instructions, eligibility settings, securities, preference settings, "
				"and bid opening details."
			),
			"used_later_by": (
				"Evaluation Setup, Forms & Evidence, Contract Values, and Tender Document Preview."
			),
			"not_configured_here": (
				"Technical requirements, price items, evaluation scores, bidder forms, "
				"and SCC contract values."
			),
		},
	}


def save_configuration_tds(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	if isinstance(payload.get("tds_values"), (dict, str)):
		incoming = _parse_tds_values(payload.get("tds_values"))
	else:
		incoming = _parse_tds_values(payload)

	for banned in BANNED_POST_KEYS:
		incoming.pop(banned, None)

	current = _parse_tds_values(getattr(doc, "tds_values", None))
	merged = dict(current)
	for key, val in incoming.items():
		if key in EDITABLE_KEYS:
			merged[key] = cstr(val).strip() if val is not None else ""

	merged = normalize_display_values(doc, merged)
	# Do not persist read-only derived keys as source of truth edits
	persist = {k: v for k, v in merged.items() if k in EDITABLE_KEYS}

	blockers, warnings, can_continue = validate_tds_values(merged)
	has_progress = any(persist.get(k) for k in EDITABLE_KEYS)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	conds = tds_exit_conditions_for_doc_values(merged)
	progress = evaluate_conditions(conds)

	doc.tds_values = json.dumps(persist)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg02_steps_state(
		doc,
		can_continue=can_continue,
		has_any_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_tds(doc.name)


def tds_exit_conditions_for_doc_values(values: dict[str, Any]) -> list[dict[str, Any]]:
	conds = _required_conditions(values)
	return [{"key": c["key"], "label": c["label"], "met": c["met"]} for c in conds]
