# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Preliminary Requirements and Evidence — dynamic criteria checklist + drawer responses."""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, getdate, now_datetime

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

SECTION_KEY = "preliminary_requirements_and_evidence"

METHOD_UPLOAD = "upload"
METHOD_SELECT_OR_UPLOAD = "select_or_upload"
METHOD_VERIFICATION = "verification_reference"
METHOD_STRUCTURED = "structured"
METHOD_LINKED = "linked_section"

LINKED_SECTION_LABELS = {
	"form_of_tender": "Form of Tender",
	"statutory_declarations": "Statutory Declarations",
	"tender_security": "Tender Security",
	"confidential_business_questionnaire": "Confidential Business Questionnaire",
}

VALIDITY_VALID_ON_SUBMISSION = "valid_on_submission_deadline"
VALIDITY_VALID_THROUGH_OPENING = "valid_through_opening_date"


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open Preliminary Requirements."),
			frappe.PermissionError,
		)


def portal_preliminary_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def _load_bid_for_cfg(
	cfg_id: str,
	*,
	snapshot: dict[str, Any] | None = None,
	schema_hash: str | None = None,
):
	"""Prefer owner's Draft; if only Sealed exists, return it (do not spawn a new draft)."""
	owner = frappe.session.user
	draft_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": "Draft", "owner": owner},
		"name",
	)
	if draft_name:
		doc = _get_bid(draft_name)
		_assert_bid_owner(doc)
		return doc
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": STATUS_SEALED, "owner": owner},
		"name",
		order_by="sealed_at desc",
	)
	if sealed_name:
		doc = _get_bid(sealed_name)
		_assert_bid_owner(doc)
		return doc
	# Administrator tests may seal a bid without matching owner filter edge cases.
	if owner == "Administrator":
		any_sealed = frappe.db.get_value(
			"Electronic Bid Submission",
			{"configuration": cfg_id, "status": STATUS_SEALED},
			"name",
			order_by="sealed_at desc",
		)
		if any_sealed:
			return _get_bid(any_sealed)
	draft = create_or_get_draft(cfg_id, schema_snapshot=snapshot, schema_hash=schema_hash)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)
	return doc


def _prelim_section(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	frappe.throw(
		frappe._("Published template is missing the Preliminary Requirements section."),
		title="KT_PRELIM_SECTION_MISSING",
	)


def _cbq_bidder_entity(responses: dict[str, Any]) -> dict[str, Any]:
	cbq = responses.get("confidential_business_questionnaire")
	cbq = cbq if isinstance(cbq, dict) else {}
	entities = cbq.get("entities") if isinstance(cbq.get("entities"), list) else []
	for ent in entities:
		if isinstance(ent, dict) and cstr(ent.get("role") or "").strip().lower() in (
			"bidder",
			"lead",
			"lead_member",
			"",
		):
			return ent
	return entities[0] if entities and isinstance(entities[0], dict) else {}


def bidder_is_jv(responses: dict[str, Any]) -> bool:
	entity = _cbq_bidder_entity(responses)
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	entity_type = cstr(entity.get("entity_type") or answers.get("entity_type") or "").strip().lower()
	jv_mode = cstr(answers.get("jv_mode") or answers.get("joint_venture_status") or "").strip().lower()
	if entity_type in ("jv", "joint_venture", "constituted_jv", "intended_jv"):
		return True
	if "joint" in jv_mode or "jv" in jv_mode or "intended" in jv_mode or "constituted" in jv_mode:
		return True
	return False


def _criterion_applicable(criterion: dict[str, Any], *, is_jv: bool) -> bool:
	rule = cstr(criterion.get("applicability") or "always").strip().lower()
	if rule == "jv_only":
		return is_jv
	if rule == "single_bidder_only":
		return not is_jv
	return True


def _section_def_by_key(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == key:
			return sec
	return {}


def resolve_linked_status_and_url(
	linked_key: str,
	*,
	publication_ref: str,
	snapshot: dict[str, Any],
	responses: dict[str, Any],
) -> tuple[str, str]:
	sec = _section_def_by_key(snapshot, linked_key)
	payload = responses.get(linked_key) if isinstance(responses.get(linked_key), dict) else {}

	if linked_key == "form_of_tender":
		from kentender_procurement.tender_configurations.services.form_of_tender import (
			derive_fot_section_status,
			portal_fot_url,
		)

		return derive_fot_section_status(sec, payload), portal_fot_url(publication_ref)

	if linked_key == "statutory_declarations":
		from kentender_procurement.tender_configurations.services.statutory_declarations import (
			derive_statutory_section_status,
			portal_statutory_url,
		)

		return derive_statutory_section_status(sec, payload), portal_statutory_url(publication_ref)

	if linked_key == "tender_security":
		from kentender_procurement.tender_configurations.services.electronic_std_template import (
			resolve_tender_security_mode,
		)
		from kentender_procurement.tender_configurations.services.tender_security import (
			MODE_NONE,
			derive_tender_security_section_status,
			portal_tender_security_url,
		)

		mode = cstr(sec.get("security_mode") or "").strip()
		if not mode:
			cfg_id = cstr(snapshot.get("configuration_id") or "")
			raw = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values") if cfg_id else None
			tds = _parse_json(raw, {})
			mode = resolve_tender_security_mode(tds if isinstance(tds, dict) else {})
		if mode == MODE_NONE or not sec:
			return STATUS_NOT_APPLICABLE, portal_workspace_url(publication_ref)
		return derive_tender_security_section_status(sec, payload), portal_tender_security_url(
			publication_ref
		)

	if linked_key == "confidential_business_questionnaire":
		from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
			derive_cbq_section_status,
			portal_cbq_url,
		)

		return derive_cbq_section_status(payload, sec), portal_cbq_url(publication_ref)

	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		portal_section_url,
	)

	return STATUS_NOT_STARTED, portal_section_url(publication_ref, linked_key)


def _submission_deadline(overview: dict[str, Any], cfg_id: str) -> Any:
	dates = overview.get("dates") if isinstance(overview.get("dates"), dict) else {}
	raw = (
		dates.get("submission_deadline")
		or overview.get("submission_deadline")
		or ""
	)
	if not raw and cfg_id:
		tds = _parse_json(frappe.db.get_value("Tender Configuration", cfg_id, "tds_values"), {})
		if isinstance(tds, dict):
			raw = tds.get("tender_submission_deadline") or tds.get("submission_deadline") or ""
	try:
		return getdate(raw) if raw else None
	except Exception:
		return None


def _opening_date(overview: dict[str, Any], cfg_id: str) -> Any:
	dates = overview.get("dates") if isinstance(overview.get("dates"), dict) else {}
	raw = dates.get("opening_datetime") or overview.get("opening_datetime") or ""
	if not raw and cfg_id:
		tds = _parse_json(frappe.db.get_value("Tender Configuration", cfg_id, "tds_values"), {})
		if isinstance(tds, dict):
			raw = tds.get("tender_opening_datetime") or tds.get("opening_datetime") or ""
	try:
		return getdate(raw) if raw else None
	except Exception:
		return None


def _evidence_expiry_date(item: dict[str, Any]) -> Any:
	raw = cstr(item.get("expiry_or_validity") or item.get("expiry_date") or "").strip()
	if not raw:
		return None
	try:
		return getdate(raw)
	except Exception:
		return None


def evaluate_validity(
	*,
	validity_rule: str,
	evidence_item: dict[str, Any] | None,
	submission_deadline,
	opening_date,
) -> tuple[bool, str]:
	"""Return (ok, issue_message). Empty rule → ok."""
	rule = cstr(validity_rule or "").strip()
	if not rule or rule in ("none", "no_expiry", "not_required"):
		return True, ""
	item = evidence_item if isinstance(evidence_item, dict) else {}
	expiry = _evidence_expiry_date(item)
	if expiry is None:
		return False, "This evidence is missing an expiry or validity date required by the tender."
	if rule == VALIDITY_VALID_ON_SUBMISSION:
		if submission_deadline and expiry < submission_deadline:
			return False, "This evidence expires before the tender submission deadline."
		return True, ""
	if rule == VALIDITY_VALID_THROUGH_OPENING:
		ref = opening_date or submission_deadline
		if ref and expiry < ref:
			return False, "This evidence expires before the tender opening date."
		return True, ""
	# Unknown configured rule: treat missing/past expiry relative to today when labelled expired.
	try:
		today = getdate(now_datetime())
		if expiry < today:
			return False, "This evidence has expired."
	except Exception:
		pass
	return True, ""


def _action_for_status(status: str, *, linked: bool = False) -> str:
	if status == STATUS_NOT_APPLICABLE:
		return ""
	if status == STATUS_NEEDS_ATTENTION:
		return "Replace" if not linked else "Resolve"
	if status == STATUS_COMPLETE:
		return "Review"
	if status == STATUS_IN_PROGRESS:
		return "Continue"
	return "Start"


def _responses_map(payload: dict[str, Any] | None) -> dict[str, Any]:
	payload = payload if isinstance(payload, dict) else {}
	raw = payload.get("criterion_responses")
	if isinstance(raw, dict):
		return raw
	return {}


def _find_evidence(register_items: list[dict[str, Any]], evidence_id: str) -> dict[str, Any] | None:
	eid = cstr(evidence_id or "").strip()
	if not eid:
		return None
	for row in register_items:
		if isinstance(row, dict) and cstr(row.get("evidence_id")) == eid:
			return row
	return None


def derive_criterion_status(
	criterion: dict[str, Any],
	response: dict[str, Any] | None,
	*,
	is_jv: bool,
	register_items: list[dict[str, Any]],
	submission_deadline,
	opening_date,
	linked_status: str | None = None,
) -> dict[str, Any]:
	"""Server status for one criterion (including linked projection)."""
	if not _criterion_applicable(criterion, is_jv=is_jv):
		return {
			"status": STATUS_NOT_APPLICABLE,
			"action_label": "",
			"issue_message": "",
			"applicable": 0,
		}

	method = cstr(criterion.get("response_method") or "").strip()
	if method == METHOD_LINKED:
		status = linked_status or STATUS_NOT_STARTED
		if status == STATUS_NOT_APPLICABLE:
			return {
				"status": STATUS_NOT_APPLICABLE,
				"action_label": "",
				"issue_message": "",
				"applicable": 0,
			}
		return {
			"status": status,
			"action_label": _action_for_status(status, linked=True),
			"issue_message": "",
			"applicable": 1,
		}

	resp = response if isinstance(response, dict) else {}
	if not resp:
		return {
			"status": STATUS_NOT_STARTED,
			"action_label": "Start",
			"issue_message": "",
			"applicable": 1,
		}

	issue = ""
	status = STATUS_IN_PROGRESS

	if method in (METHOD_UPLOAD, METHOD_SELECT_OR_UPLOAD):
		eid = cstr(resp.get("evidence_id") or "").strip()
		file_name = cstr(resp.get("file_name") or "").strip()
		item = _find_evidence(register_items, eid) if eid else None
		if item:
			file_name = file_name or cstr(item.get("file_name") or "")
		if not eid and not file_name:
			# Partial metadata without file
			if any(cstr(resp.get(k) or "").strip() for k in ("issuer", "reference_number", "issue_date")):
				status = STATUS_IN_PROGRESS
			else:
				status = STATUS_NOT_STARTED
		elif not file_name and not (item and cstr(item.get("file_name") or "").strip()):
			status = STATUS_NEEDS_ATTENTION
			issue = "The selected evidence file is missing. Replace the upload."
		else:
			ok, issue = evaluate_validity(
				validity_rule=cstr(criterion.get("validity_rule") or ""),
				evidence_item=item or resp,
				submission_deadline=submission_deadline,
				opening_date=opening_date,
			)
			status = STATUS_COMPLETE if ok else STATUS_NEEDS_ATTENTION

	elif method == METHOD_VERIFICATION:
		fields = criterion.get("verification_fields") or [
			{"field_key": "verification_reference", "required": True}
		]
		values = resp.get("verification") if isinstance(resp.get("verification"), dict) else resp
		missing = False
		any_val = False
		for f in fields:
			if not isinstance(f, dict):
				continue
			fk = cstr(f.get("field_key") or "").strip()
			val = cstr(values.get(fk) or "").strip()
			if val:
				any_val = True
			if f.get("required", True) and not val:
				missing = True
		if not any_val:
			status = STATUS_NOT_STARTED
		elif missing:
			status = STATUS_IN_PROGRESS
		else:
			status = STATUS_COMPLETE

	elif method == METHOD_STRUCTURED:
		fields = criterion.get("structured_fields") or []
		values = resp.get("structured") if isinstance(resp.get("structured"), dict) else resp
		missing = False
		any_val = False
		for f in fields:
			if not isinstance(f, dict):
				continue
			fk = cstr(f.get("field_key") or "").strip()
			val = values.get(fk)
			filled = bool(cstr(val).strip()) if not isinstance(val, (dict, list)) else bool(val)
			if filled:
				any_val = True
			if f.get("required", True) and not filled:
				missing = True
		if not fields:
			# No configured fields — treat explicit acknowledgment flag.
			if resp.get("acknowledged") or resp.get("complete"):
				status = STATUS_COMPLETE
			else:
				status = STATUS_NOT_STARTED
		elif not any_val:
			status = STATUS_NOT_STARTED
		elif missing:
			status = STATUS_IN_PROGRESS
		else:
			status = STATUS_COMPLETE
	else:
		status = STATUS_IN_PROGRESS

	return {
		"status": status,
		"action_label": _action_for_status(status, linked=False),
		"issue_message": issue,
		"applicable": 1,
	}


def derive_preliminary_section_status(
	sec: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
	snapshot: dict[str, Any] | None = None,
	register_items: list[dict[str, Any]] | None = None,
	submission_deadline=None,
	opening_date=None,
	publication_ref: str = "",
) -> str:
	"""Roll-up status for checklist (Needs Attention > In Progress > Complete > Not Started)."""
	criteria = sec.get("criteria") if isinstance(sec.get("criteria"), list) else []
	if not criteria:
		return STATUS_NOT_STARTED

	responses = responses if isinstance(responses, dict) else {}
	snapshot = snapshot if isinstance(snapshot, dict) else {}
	register_items = register_items if isinstance(register_items, list) else []
	is_jv = bidder_is_jv(responses)
	resp_map = _responses_map(payload)

	statuses: list[str] = []
	for crit in criteria:
		if not isinstance(crit, dict):
			continue
		cid = cstr(crit.get("criterion_id") or "")
		linked_status = None
		if cstr(crit.get("response_method")) == METHOD_LINKED:
			lk = cstr(crit.get("linked_section_key") or "")
			if lk and publication_ref:
				linked_status, _ = resolve_linked_status_and_url(
					lk,
					publication_ref=publication_ref,
					snapshot=snapshot,
					responses=responses,
				)
			elif lk:
				# Checklist path without pub_ref — derive from payloads only.
				linked_status, _ = resolve_linked_status_and_url(
					lk,
					publication_ref="__",
					snapshot=snapshot,
					responses=responses,
				)
		derived = derive_criterion_status(
			crit,
			resp_map.get(cid),
			is_jv=is_jv,
			register_items=register_items,
			submission_deadline=submission_deadline,
			opening_date=opening_date,
			linked_status=linked_status,
		)
		if not derived.get("applicable"):
			continue
		statuses.append(cstr(derived.get("status")))

	if not statuses:
		return STATUS_NOT_STARTED
	if any(s == STATUS_NEEDS_ATTENTION for s in statuses):
		return STATUS_NEEDS_ATTENTION
	if all(s == STATUS_COMPLETE for s in statuses):
		return STATUS_COMPLETE
	if all(s == STATUS_NOT_STARTED for s in statuses):
		return STATUS_NOT_STARTED
	return STATUS_IN_PROGRESS


def preliminary_blocker_messages(
	sec: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any],
	snapshot: dict[str, Any],
	register_items: list[dict[str, Any]],
	submission_deadline=None,
	opening_date=None,
	publication_ref: str = "",
) -> list[str]:
	messages: list[str] = []
	resp_map = _responses_map(payload)
	is_jv = bidder_is_jv(responses)
	for crit in sec.get("criteria") or []:
		if not isinstance(crit, dict):
			continue
		cid = cstr(crit.get("criterion_id") or "")
		title = cstr(crit.get("title") or "Requirement")
		linked_status = None
		if cstr(crit.get("response_method")) == METHOD_LINKED:
			lk = cstr(crit.get("linked_section_key") or "")
			if lk:
				linked_status, _ = resolve_linked_status_and_url(
					lk,
					publication_ref=publication_ref or "__",
					snapshot=snapshot,
					responses=responses,
				)
		derived = derive_criterion_status(
			crit,
			resp_map.get(cid),
			is_jv=is_jv,
			register_items=register_items,
			submission_deadline=submission_deadline,
			opening_date=opening_date,
			linked_status=linked_status,
		)
		if not derived.get("applicable"):
			continue
		st = cstr(derived.get("status"))
		if st == STATUS_COMPLETE:
			continue
		if st == STATUS_NEEDS_ATTENTION:
			extra = cstr(derived.get("issue_message") or "").strip()
			messages.append(
				f"{title}: needs attention" + (f" — {extra}" if extra else "")
			)
		elif st == STATUS_NOT_STARTED:
			messages.append(f"{title}: not started")
		else:
			messages.append(f"{title}: incomplete")
	return messages


def _load_register_items(doc) -> list[dict[str, Any]]:
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		_derive_status,
		_load_register,
	)

	register = _load_register(doc)
	items = []
	for row in register.get("items") or []:
		if isinstance(row, dict):
			r = dict(row)
			r["status"] = _derive_status(r)
			items.append(r)
	return items


def get_preliminary_requirements(publication_ref: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		_project_item,
		portal_evidence_url,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview,
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(publication_ref)
	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(overview.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _prelim_section(snapshot)
	criteria_defs = [
		c for c in (section_def.get("criteria") or []) if isinstance(c, dict)
	]

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	bid_id = cstr(bid.name if bid else "")
	responses = _parse_json(getattr(bid, "responses", None), {}) if bid else {}
	payload = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	resp_map = _responses_map(payload)
	register_items = _load_register_items(bid) if bid else []
	is_jv = bidder_is_jv(responses)
	deadline = _submission_deadline(overview, cfg_id)
	opening = _opening_date(overview, cfg_id)
	sealed = bool(bid and cstr(bid.status) == STATUS_SEALED)

	evidence_group: list[dict[str, Any]] = []
	linked_group: list[dict[str, Any]] = []
	complete_count = 0
	applicable_count = 0

	for crit in criteria_defs:
		cid = cstr(crit.get("criterion_id") or "")
		method = cstr(crit.get("response_method") or "")
		linked_key = cstr(crit.get("linked_section_key") or "")
		linked_status = None
		linked_url = ""
		if method == METHOD_LINKED and linked_key:
			linked_status, linked_url = resolve_linked_status_and_url(
				linked_key,
				publication_ref=pub_ref,
				snapshot=snapshot,
				responses=responses,
			)
		derived = derive_criterion_status(
			crit,
			resp_map.get(cid),
			is_jv=is_jv,
			register_items=register_items,
			submission_deadline=deadline,
			opening_date=opening,
			linked_status=linked_status,
		)
		row = {
			"criterion_id": cid,
			"title": cstr(crit.get("title") or ""),
			"evidence_instruction": cstr(crit.get("evidence_instruction") or ""),
			"mandatory": 1 if crit.get("mandatory") else 0,
			"required_label": "Required" if crit.get("mandatory") else "Conditional",
			"applicability": cstr(crit.get("applicability") or "always"),
			"response_method": method,
			"linked_section_key": linked_key,
			"linked_section_title": cstr(
				crit.get("linked_section_title")
				or LINKED_SECTION_LABELS.get(linked_key, "")
			),
			"linked_section_url": linked_url,
			"validity_rule": cstr(crit.get("validity_rule") or ""),
			"accepted_file_types": list(crit.get("accepted_file_types") or []),
			"max_file_size_mb": int(crit.get("max_file_size_mb") or 5),
			"evidence_type": cstr(crit.get("evidence_type") or "supporting_document"),
			"structured_fields": list(crit.get("structured_fields") or []),
			"verification_fields": list(crit.get("verification_fields") or []),
			"status": derived["status"],
			"action_label": derived["action_label"],
			"issue_message": derived.get("issue_message") or "",
			"applicable": derived.get("applicable") or 0,
			"response": resp_map.get(cid) or {},
		}
		if derived.get("applicable"):
			applicable_count += 1
			if derived["status"] == STATUS_COMPLETE:
				complete_count += 1
		# Hide N/A from tables (still counted out of progress).
		if not derived.get("applicable"):
			continue
		if method == METHOD_LINKED:
			linked_group.append(row)
		else:
			evidence_group.append(row)

	# Saved evidence options for select_or_upload drawers (never preselected).
	saved_evidence = [_project_item(r) for r in register_items]
	for item in saved_evidence:
		ok, issue = evaluate_validity(
			validity_rule=VALIDITY_VALID_ON_SUBMISSION,
			evidence_item=item,
			submission_deadline=deadline,
			opening_date=opening,
		)
		# Per-criterion validity is applied at derive time; flag generic expiry for UI label.
		expiry = _evidence_expiry_date(item)
		item["eligibility_label"] = ""
		item["eligible"] = 1
		if expiry and deadline and expiry < deadline:
			item["eligibility_label"] = "Expired"
			item["eligible"] = 0
		elif not ok:
			item["eligibility_label"] = "Ineligible"
			item["eligible"] = 0
		_ = issue

	section_status = derive_preliminary_section_status(
		section_def,
		payload,
		responses=responses,
		snapshot=snapshot,
		register_items=register_items,
		submission_deadline=deadline,
		opening_date=opening,
		publication_ref=pub_ref,
	)
	all_complete = (
		applicable_count > 0
		and complete_count == applicable_count
		and section_status == STATUS_COMPLETE
	)

	return {
		"published_tender_ref": pub_ref,
		"bid_id": bid_id,
		"bid_modified": cstr(getattr(bid, "modified", None) or ""),
		"tender_title": cstr(
			overview.get("tender_title")
			or frappe.db.get_value("Tender Configuration", cfg_id, "tender_title")
			or ""
		),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Preliminary Requirements and Evidence"),
		"bidder_instructions": cstr(
			section_def.get("bidder_instructions")
			or "Provide the documents and information required for preliminary examination."
		),
		"workspace_url": portal_workspace_url(pub_ref),
		"evidence_url": portal_evidence_url(pub_ref),
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"section_status": section_status,
		"status_chip": section_status,
		"progress_complete": complete_count,
		"progress_total": applicable_count,
		"progress_label": f"{complete_count} of {applicable_count} requirements complete",
		"show_completion_banner": 1 if all_complete else 0,
		"completion_banner_text": (
			"All preliminary requirements have responses. "
			"Responsiveness is determined after tender opening."
		),
		"evidence_group": evidence_group,
		"linked_group": linked_group,
		"saved_evidence": saved_evidence,
		"submission_deadline": str(deadline) if deadline else "",
		"opening_date": str(opening) if opening else "",
		"is_jv": 1 if is_jv else 0,
		"read_only": 1 if sealed else 0,
		"bid_sealed": 1 if sealed else 0,
	}


def _validate_upload_against_criterion(
	criterion: dict[str, Any], *, filename: str, content: bytes
) -> None:
	name = cstr(filename or "").strip()
	if not name or "/" in name or "\\" in name or ".." in name:
		frappe.throw(frappe._("Invalid file name."), title="Upload rejected")
	ext = os.path.splitext(name)[1].lower()
	allowed = [cstr(x).lower() for x in (criterion.get("accepted_file_types") or [])]
	if allowed and ext not in allowed:
		frappe.throw(
			frappe._("File type {0} is not accepted. Use {1}.").format(
				ext or "(none)", ", ".join(allowed)
			),
			title="File type not accepted",
		)
	max_mb = int(criterion.get("max_file_size_mb") or 5)
	if len(content) > max_mb * 1024 * 1024:
		frappe.throw(
			frappe._("File exceeds the maximum allowed size of {0} MB.").format(max_mb),
			title="File too large",
		)
	if not content:
		frappe.throw(frappe._("Empty files cannot be uploaded."), title="Upload rejected")


def save_preliminary_response(
	publication_ref: str,
	criterion_id: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save one criterion response. No magical defaults; explicit payload required."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		link_evidence,
		upload_evidence,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = payload if isinstance(payload, dict) else {}

	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _prelim_section(snapshot)
	cid = cstr(criterion_id or "").strip()
	criterion = next(
		(
			c
			for c in (section_def.get("criteria") or [])
			if isinstance(c, dict) and cstr(c.get("criterion_id")) == cid
		),
		None,
	)
	if not criterion:
		frappe.throw(frappe._("Unknown preliminary requirement."), title="KT_PRELIM_UNKNOWN")

	method = cstr(criterion.get("response_method") or "")
	if method == METHOD_LINKED:
		frappe.throw(
			frappe._("This requirement is completed in another section."),
			title="KT_PRELIM_LINKED",
		)

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	doc = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	if expected_modified and cstr(doc.modified) != cstr(expected_modified):
		frappe.throw(
			frappe._("This draft was updated elsewhere. Reload and try again."),
			title="KT_PRELIM_CONFLICT",
		)

	responses = _parse_json(doc.responses, {})
	section_payload = (
		responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	)
	resp_map = _responses_map(section_payload)
	is_jv = bidder_is_jv(responses)
	if not _criterion_applicable(criterion, is_jv=is_jv):
		frappe.throw(
			frappe._("This requirement is not applicable to the current bidder."),
			title="KT_PRELIM_NOT_APPLICABLE",
		)

	row: dict[str, Any] = {"criterion_id": cid, "response_method": method, "saved_at": str(now_datetime())}

	if method in (METHOD_UPLOAD, METHOD_SELECT_OR_UPLOAD):
		action = cstr(payload.get("action") or "").strip().lower()
		if action == "clear":
			row = {"criterion_id": cid, "response_method": method, "cleared": 1}
			resp_map.pop(cid, None)
			# Fall through to empty — treat as not started
			resp_map[cid] = row
		elif action == "select" or (payload.get("evidence_id") and not payload.get("content_b64")):
			eid = cstr(payload.get("evidence_id") or "").strip()
			if not eid:
				frappe.throw(
					frappe._("Select a saved evidence item explicitly."),
					title="KT_PRELIM_SELECT_REQUIRED",
				)
			items = _load_register_items(doc)
			item = _find_evidence(items, eid)
			if not item:
				frappe.throw(frappe._("Selected evidence was not found."), title="KT_PRELIM_EVIDENCE_MISSING")
			from kentender_procurement.tender_configurations.services.published_tender_overview import (
				get_published_tender_overview,
			)

			overview = get_published_tender_overview(pub_ref)
			deadline = _submission_deadline(overview, cfg_id)
			opening = _opening_date(overview, cfg_id)
			ok, issue = evaluate_validity(
				validity_rule=cstr(criterion.get("validity_rule") or ""),
				evidence_item=item,
				submission_deadline=deadline,
				opening_date=opening,
			)
			if not ok:
				frappe.throw(
					frappe._(issue or "Selected evidence is not eligible for this tender."),
					title="KT_PRELIM_EVIDENCE_INELIGIBLE",
				)
			link_evidence(
				pub_ref,
				evidence_id=eid,
				target_kind="preliminary_criterion",
				target_key=cid,
			)
			row.update(
				{
					"evidence_id": eid,
					"file_name": cstr(item.get("file_name") or ""),
					"file_url": cstr(item.get("file_url") or ""),
					"issuer": cstr(item.get("issuer") or ""),
					"reference_number": cstr(item.get("reference_number") or ""),
					"issue_date": cstr(item.get("issue_date") or ""),
					"expiry_or_validity": cstr(item.get("expiry_or_validity") or ""),
					"source": "selected",
				}
			)
			resp_map[cid] = row
		elif action == "upload" or payload.get("content_b64") or payload.get("filename"):
			filename = cstr(payload.get("filename") or "").strip()
			content_b64 = cstr(payload.get("content_b64") or "").strip()
			if not filename or not content_b64:
				frappe.throw(
					frappe._("Upload a file to save this response."),
					title="KT_PRELIM_UPLOAD_REQUIRED",
				)
			try:
				blob = base64.b64decode(content_b64)
			except Exception:
				frappe.throw(frappe._("File content could not be decoded."), title="KT_PRELIM_FILE_INVALID")
				blob = b""
			_validate_upload_against_criterion(criterion, filename=filename, content=blob)
			meta = {
				"issuer": cstr(payload.get("issuer") or ""),
				"reference_number": cstr(payload.get("reference_number") or ""),
				"issue_date": cstr(payload.get("issue_date") or ""),
				"expiry_or_validity": cstr(
					payload.get("expiry_or_validity") or payload.get("expiry_date") or ""
				),
			}
			uploaded = upload_evidence(
				pub_ref,
				title=cstr(payload.get("title") or criterion.get("title") or filename),
				evidence_type=cstr(criterion.get("evidence_type") or "supporting_document"),
				filename=filename,
				content_b64=content_b64,
				content_type=cstr(payload.get("content_type") or "application/pdf"),
				metadata=meta,
			)
			item = uploaded.get("item") if isinstance(uploaded.get("item"), dict) else {}
			eid = cstr(item.get("evidence_id") or "")
			if eid:
				link_evidence(
					pub_ref,
					evidence_id=eid,
					target_kind="preliminary_criterion",
					target_key=cid,
				)
			row.update(
				{
					"evidence_id": eid,
					"file_name": cstr(item.get("file_name") or filename),
					"file_url": cstr(item.get("file_url") or ""),
					"issuer": meta["issuer"],
					"reference_number": meta["reference_number"],
					"issue_date": meta["issue_date"],
					"expiry_or_validity": meta["expiry_or_validity"],
					"source": "uploaded",
				}
			)
			# Re-check validity after upload (expired certs must not complete).
			overview = None
			from kentender_procurement.tender_configurations.services.published_tender_overview import (
				get_published_tender_overview,
			)

			overview = get_published_tender_overview(pub_ref)
			deadline = _submission_deadline(overview, cfg_id)
			opening = _opening_date(overview, cfg_id)
			ok, issue = evaluate_validity(
				validity_rule=cstr(criterion.get("validity_rule") or ""),
				evidence_item=row,
				submission_deadline=deadline,
				opening_date=opening,
			)
			if not ok:
				# Persist response but surface as needs attention via derive — allow save of expired? Plan: expired → Needs attention. Allow save.
				row["validity_issue"] = issue
			resp_map[cid] = row
		else:
			frappe.throw(
				frappe._("Provide an explicit upload or saved-evidence selection."),
				title="KT_PRELIM_RESPONSE_REQUIRED",
			)

	elif method == METHOD_VERIFICATION:
		fields = criterion.get("verification_fields") or [
			{"field_key": "verification_reference", "label": "Verification reference", "required": True}
		]
		values = payload.get("verification") if isinstance(payload.get("verification"), dict) else payload
		stored: dict[str, Any] = {}
		for f in fields:
			if not isinstance(f, dict):
				continue
			fk = cstr(f.get("field_key") or "").strip()
			if not fk:
				continue
			stored[fk] = cstr(values.get(fk) or "").strip()
			if f.get("required", True) and not stored[fk]:
				frappe.throw(
					frappe._("Enter the required verification details."),
					title="KT_PRELIM_VERIFICATION_REQUIRED",
				)
		row["verification"] = stored
		resp_map[cid] = row

	elif method == METHOD_STRUCTURED:
		fields = criterion.get("structured_fields") or []
		values = payload.get("structured") if isinstance(payload.get("structured"), dict) else payload
		stored = {}
		for f in fields:
			if not isinstance(f, dict):
				continue
			fk = cstr(f.get("field_key") or "").strip()
			if not fk:
				continue
			stored[fk] = values.get(fk)
			if f.get("required", True) and not cstr(stored[fk] if stored[fk] is not None else "").strip():
				frappe.throw(
					frappe._("Complete all required fields for this response."),
					title="KT_PRELIM_STRUCTURED_REQUIRED",
				)
		if not fields and payload.get("acknowledged"):
			row["acknowledged"] = 1
		else:
			row["structured"] = stored
		resp_map[cid] = row
	else:
		frappe.throw(frappe._("Unsupported response method."), title="KT_PRELIM_METHOD")

	# Reload doc after evidence ops (upload may have saved).
	doc = _get_bid(doc.name)
	responses = _parse_json(doc.responses, {})
	section_payload = (
		responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	)
	# Merge maps in case evidence save raced — prefer our resp_map for this cid.
	existing_map = _responses_map(section_payload)
	existing_map[cid] = resp_map[cid]
	section_payload = dict(section_payload)
	section_payload["criterion_responses"] = existing_map
	responses[SECTION_KEY] = section_payload
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"section_saved",
		{"section_key": SECTION_KEY, "criterion_id": cid, "response_method": method},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return get_preliminary_requirements(pub_ref)
