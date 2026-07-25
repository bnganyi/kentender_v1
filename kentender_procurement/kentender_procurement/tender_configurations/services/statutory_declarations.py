# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Statutory Declarations — Review and Certify (declaration bundle)."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime, get_datetime, now_datetime

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
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "statutory_declarations"
CBQ_KEY = "confidential_business_questionnaire"

STATUS_REQUIRES_RECERTIFICATION = "Requires Recertification"

CHOICE_INDEPENDENT = "independent"
CHOICE_DISCLOSED = "disclosed"

RECORD_KEYS = (
	"independent_tender_determination",
	"sd1_not_debarred",
	"sd2_no_corruption",
	"code_of_ethics",
)

DISCLOSURE_COLUMNS = (
	"competitor_name",
	"nature_of_interaction",
	"reason",
	"complete_details",
)


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open Statutory Declarations."),
			frappe.PermissionError,
		)


def portal_statutory_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def _statutory_section(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	frappe.throw(
		frappe._("Published template is missing the Statutory Declarations section."),
		title="KT_STAT_SECTION_MISSING",
	)


def _filled(val: Any) -> bool:
	if val is None:
		return False
	if isinstance(val, bool):
		return val
	if isinstance(val, (int, float)):
		return True
	if isinstance(val, list):
		return len(val) > 0
	if isinstance(val, dict):
		return bool(val)
	return bool(cstr(val).strip())


def _is_truthy(val: Any) -> bool:
	return val in (True, 1, "1", "true", "True", "yes", "Yes", "on")


def _normalize_choice(raw: Any) -> str:
	v = cstr(raw or "").strip().lower()
	if v in (CHOICE_INDEPENDENT, "independently", "none", "no"):
		return CHOICE_INDEPENDENT
	if v in (CHOICE_DISCLOSED, "disclose", "consultation", "yes"):
		return CHOICE_DISCLOSED
	return ""


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def _cbq_bidder_entity(responses: dict[str, Any]) -> dict[str, Any]:
	cbq = responses.get(CBQ_KEY) if isinstance(responses.get(CBQ_KEY), dict) else {}
	entities = cbq.get("entities") if isinstance(cbq.get("entities"), list) else []
	for ent in entities:
		if isinstance(ent, dict) and cstr(ent.get("role") or "") in ("bidder", "lead", ""):
			return ent
	return entities[0] if entities and isinstance(entities[0], dict) else {}


def _declarant_from_cbq(entity: dict[str, Any]) -> dict[str, Any]:
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	name = cstr(answers.get("authorized_signatory_name") or entity.get("certifier_name") or "").strip()
	title = cstr(answers.get("authorized_signatory_title") or entity.get("certifier_title") or "").strip()
	authority = (
		_is_truthy(answers.get("authority_to_bind_confirmed"))
		or bool(entity.get("certified"))
		or _is_truthy(entity.get("authority_affirmed"))
	)
	postal = cstr(answers.get("declarant_postal_address") or "").strip()
	place = cstr(answers.get("declarant_place_of_residence") or "").strip()
	country = cstr(answers.get("declarant_country_of_residence") or "").strip()
	# Fallback: entity postal/country when declarant-specific fields empty.
	if not postal:
		postal = cstr(answers.get("postal_address") or "").strip()
	if not country:
		country = cstr(answers.get("country") or "").strip()
	if not place:
		place = cstr(answers.get("city") or answers.get("location") or "").strip()
	return {
		"name": name,
		"title": title,
		"postal_address": postal,
		"place_of_residence": place,
		"country_of_residence": country,
		"authority_confirmed": 1 if authority else 0,
		"legal_name": cstr(entity.get("legal_name") or "").strip(),
		"cbq_certified": 1 if entity.get("certified") else 0,
		"complete": 1
		if name and title and postal and place and country and authority and entity.get("certified")
		else 0,
	}


def validate_disclosures(response: dict[str, Any] | None) -> list[dict[str, str]]:
	response = response if isinstance(response, dict) else {}
	issues: list[dict[str, str]] = []
	choice = _normalize_choice(response.get("independent_tender_choice"))
	if choice != CHOICE_DISCLOSED:
		return issues
	rows = response.get("competitor_disclosures") or []
	if not isinstance(rows, list) or not rows:
		issues.append(
			{
				"field_key": "competitor_disclosures",
				"code": "required",
				"message": "Complete disclosure required before certification.",
			}
		)
		return issues
	for idx, row in enumerate(rows):
		if not isinstance(row, dict):
			issues.append(
				{
					"field_key": f"competitor_disclosures[{idx}]",
					"code": "invalid_row",
					"message": f"Disclosure row {idx + 1} is invalid.",
				}
			)
			continue
		for col in DISCLOSURE_COLUMNS:
			if not _filled(row.get(col)):
				issues.append(
					{
						"field_key": f"competitor_disclosures[{idx}].{col}",
						"code": "required",
						"message": f"Disclosure row {idx + 1}: {col.replace('_', ' ')} is required.",
					}
				)
	return issues


def validate_statutory_response(
	section_def: dict[str, Any],
	response: dict[str, Any] | None,
	*,
	for_completion: bool = True,
) -> dict[str, Any]:
	response = response if isinstance(response, dict) else {}
	issues = validate_disclosures(response)
	choice = _normalize_choice(response.get("independent_tender_choice"))
	certified = bool(response.get("certified"))
	started = bool(choice) or bool(response.get("competitor_disclosures")) or certified or bool(
		response.get("certification_history")
	)

	if response.get("requires_recertification"):
		status_label = STATUS_REQUIRES_RECERTIFICATION
	elif certified and for_completion:
		status_label = STATUS_COMPLETE
	elif issues and for_completion:
		status_label = STATUS_NEEDS_ATTENTION
	elif started:
		status_label = STATUS_IN_PROGRESS
	else:
		status_label = STATUS_NOT_STARTED

	return {
		"ok": not issues,
		"issues": issues,
		"section_status": status_label,
		"issue_count": len(issues),
	}


def derive_statutory_section_status(section_def: dict[str, Any], response: dict[str, Any] | None) -> str:
	result = validate_statutory_response(section_def, response, for_completion=True)
	status = cstr(result.get("section_status") or STATUS_NOT_STARTED)
	if status == STATUS_REQUIRES_RECERTIFICATION:
		return STATUS_NEEDS_ATTENTION
	return status


def is_statutory_certified(responses: dict[str, Any] | None) -> bool:
	resp = responses.get(SECTION_KEY) if isinstance(responses, dict) else {}
	if not isinstance(resp, dict):
		return False
	return bool(resp.get("certified")) and cstr(resp.get("section_status") or "") == STATUS_COMPLETE


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
	choice = _normalize_choice(payload.get("independent_tender_choice"))
	rows_in = (
		payload.get("competitor_disclosures")
		if isinstance(payload.get("competitor_disclosures"), list)
		else []
	)
	rows = []
	for row in rows_in:
		if not isinstance(row, dict):
			continue
		clean = {ck: cstr(row.get(ck) or "").strip() for ck in DISCLOSURE_COLUMNS}
		if any(clean.values()):
			rows.append(clean)
	if choice == CHOICE_INDEPENDENT:
		rows = []
	return {
		"independent_tender_choice": choice,
		"competitor_disclosures": rows,
	}


def _independent_statement(choice: str, rows: list[dict[str, Any]]) -> tuple[str, str]:
	if choice == CHOICE_INDEPENDENT:
		return (
			"The Tenderer has arrived at the Tender independently from, and without consultation, "
			"communication, agreement or arrangement with, any competitor.",
			"",
		)
	if choice == CHOICE_DISCLOSED:
		lines = []
		for i, row in enumerate(rows, start=1):
			lines.append(
				f"{i}. {row.get('competitor_name')}: {row.get('nature_of_interaction')}; "
				f"reason: {row.get('reason')}; details: {row.get('complete_details')}"
			)
		block = "Competitor disclosures:\n" + ("\n".join(lines) if lines else "(none)")
		return (
			"Consultation, communication, agreement or arrangement with one or more competitors "
			"occurred and is disclosed below.",
			block,
		)
	return ("Not answered.", "")


def _render_record(
	record_def: dict[str, Any],
	subs: dict[str, str],
) -> str:
	text = cstr(record_def.get("body") or "")
	for key, val in subs.items():
		text = text.replace("{" + key + "}", val or "—")
	return text


def _legal_records_for_ui(
	section_def: dict[str, Any],
	subs: dict[str, str],
	*,
	certified_snapshots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
	snap_by_key = {
		cstr(r.get("record_key")): r
		for r in (certified_snapshots or [])
		if isinstance(r, dict) and cstr(r.get("record_key") or "")
	}
	summaries = section_def.get("summary_statements") if isinstance(section_def.get("summary_statements"), dict) else {}
	out = []
	for rec in section_def.get("legal_records") or []:
		if not isinstance(rec, dict):
			continue
		rk = cstr(rec.get("record_key") or "")
		snap = snap_by_key.get(rk) or {}
		body = cstr(snap.get("legal_text") or "") or _render_record(rec, subs)
		appendix = ""
		if cstr(rec.get("appendix_key") or "") == "fraud_and_corruption":
			appendix = cstr(snap.get("appendix_text") or rec.get("appendix_body") or "")
			for key, val in subs.items():
				appendix = appendix.replace("{" + key + "}", val or "—")
		summary = ""
		if rk == "sd1_not_debarred":
			summary = cstr(summaries.get("sd1") or "")
		elif rk == "sd2_no_corruption":
			summary = cstr(summaries.get("sd2") or "")
		elif rk == "code_of_ethics":
			summary = cstr(summaries.get("code_of_ethics") or "")
		out.append(
			{
				"record_key": rk,
				"title": cstr(rec.get("title") or rk),
				"summary": summary,
				"legal_text": body,
				"appendix_title": cstr(rec.get("appendix_title") or ""),
				"appendix_text": appendix,
				"fraud_appendix_ack": cstr(summaries.get("fraud_appendix_ack") or "")
				if rk == "code_of_ethics"
				else "",
			}
		)
	return out


def build_readiness(
	*,
	pub_ref: str,
	responses: dict[str, Any],
	stat_response: dict[str, Any],
) -> dict[str, Any]:
	incomplete: list[dict[str, str]] = []
	entity = _cbq_bidder_entity(responses)
	declarant = _declarant_from_cbq(entity)

	if not entity.get("certified"):
		from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
			portal_cbq_url,
		)

		incomplete.append(
			{
				"section_key": CBQ_KEY,
				"title": "Confidential Business Questionnaire",
				"url": portal_cbq_url(pub_ref),
				"reason": "Certify the Confidential Business Questionnaire",
			}
		)
	elif not declarant["complete"]:
		from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
			portal_cbq_url,
		)

		incomplete.append(
			{
				"section_key": CBQ_KEY,
				"title": "Authorized declarant",
				"url": portal_cbq_url(pub_ref),
				"reason": "Complete the authorized declarant details in the CBQ",
			}
		)

	choice = _normalize_choice(stat_response.get("independent_tender_choice"))
	if not choice:
		incomplete.append(
			{
				"section_key": SECTION_KEY,
				"title": "Independent tender determination",
				"url": portal_statutory_url(pub_ref),
				"reason": "Answer how this tender was prepared",
			}
		)
	else:
		for issue in validate_disclosures(stat_response):
			incomplete.append(
				{
					"section_key": SECTION_KEY,
					"title": "Competitor disclosures",
					"url": portal_statutory_url(pub_ref),
					"reason": issue["message"],
				}
			)

	return {
		"ready": 0 if incomplete else 1,
		"incomplete_sections": incomplete,
		"incomplete_count": len(incomplete),
	}


def get_statutory_declarations(publication_ref: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		portal_cbq_url,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(publication_ref)
	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(overview.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _statutory_section(snapshot)

	cfg_id = cstr(backend.get("configuration_id") or tmpl["configuration_id"])
	draft = create_or_get_draft(cfg_id, schema_snapshot=snapshot, schema_hash=tmpl.get("hash"))
	bid_id = draft.get("bid_id")
	bid = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	responses = _parse_json(getattr(bid, "responses", None), {}) if bid else {}
	stat = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}

	entity = _cbq_bidder_entity(responses)
	declarant = _declarant_from_cbq(entity)
	choice = _normalize_choice(stat.get("independent_tender_choice"))
	rows = (
		stat.get("competitor_disclosures")
		if isinstance(stat.get("competitor_disclosures"), list)
		else []
	)
	stmt, disc_block = _independent_statement(choice, rows)
	subs = {
		"procuring_entity_name": cstr(overview.get("procuring_entity") or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"tender_reference": pub_ref,
		"tenderer_name": declarant["legal_name"] or "—",
		"declarant_name": declarant["name"] or "—",
		"declarant_title": declarant["title"] or "—",
		"declarant_postal_address": declarant["postal_address"] or "—",
		"declarant_place_of_residence": declarant["place_of_residence"] or "—",
		"declarant_country_of_residence": declarant["country_of_residence"] or "—",
		"independent_tender_statement": stmt,
		"competitor_disclosures_block": disc_block,
		"fraud_and_corruption_appendix": "",
		"certified_at": cstr(stat.get("certified_at") or ""),
	}
	# Fill appendix into code_of_ethics render via record def
	for rec in section_def.get("legal_records") or []:
		if isinstance(rec, dict) and cstr(rec.get("record_key")) == "code_of_ethics":
			subs["fraud_and_corruption_appendix"] = cstr(rec.get("appendix_body") or "")
			break

	snapshots = stat.get("legal_records") if isinstance(stat.get("legal_records"), list) else []
	records = _legal_records_for_ui(section_def, subs, certified_snapshots=snapshots)
	readiness = build_readiness(pub_ref=pub_ref, responses=responses, stat_response=stat)
	validation = validate_statutory_response(section_def, stat)
	certified = bool(stat.get("certified"))
	certified_at = cstr(stat.get("certified_at") or "")
	certified_at_display = ""
	if certified_at:
		try:
			certified_at_display = format_datetime(get_datetime(certified_at))
		except Exception:
			certified_at_display = certified_at

	can_certify = bool(readiness["ready"]) and not certified
	status_chip = (
		"Certified"
		if certified
		else (
			"Requires Recertification"
			if stat.get("requires_recertification")
			else ("Ready to certify" if can_certify else ("Pending Disclosure" if not choice else "Incomplete"))
		)
	)

	return {
		"published_tender_ref": pub_ref,
		"bid_status": cstr(bid.status) if bid else None,
		"bid_id": bid_id,
		"bid_modified": str(bid.modified) if bid else None,
		"bid_sealed": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"workspace_url": portal_workspace_url(pub_ref),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Statutory Declarations"),
		"bidder_instructions": cstr(section_def.get("bidder_instructions") or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"procuring_entity": cstr(overview.get("procuring_entity") or ""),
		"declarant": declarant,
		"readiness": readiness,
		"independent_tender": {
			"choice": choice,
			"disclosures": rows,
			"statement": stmt,
		},
		"records": records,
		"summary_statements": section_def.get("summary_statements") or {},
		"certification": {
			"certified": 1 if certified else 0,
			"certified_at": certified_at,
			"certified_at_display": certified_at_display,
			"certified_by": cstr(stat.get("certified_by") or ""),
			"certifier_name": cstr(stat.get("certifier_name") or declarant.get("name") or ""),
			"certifier_title": cstr(stat.get("certifier_title") or declarant.get("title") or ""),
			"requires_recertification": 1 if stat.get("requires_recertification") else 0,
		},
		"can_certify": 1 if can_certify else 0,
		"status_chip": status_chip,
		"section_status": validation["section_status"],
		"validation": validation,
		"edit_links": {"cbq": portal_cbq_url(pub_ref)},
		"read_only": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"witness_implemented": 0,
	}


def save_statutory_declarations(
	publication_ref: str,
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
	payload = payload if isinstance(payload, dict) else {}

	dto = get_statutory_declarations(publication_ref)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")
	if dto.get("certification", {}).get("certified"):
		frappe.throw(
			frappe._("Certified Statutory Declarations cannot be edited. Amend by changing source data."),
			title="KT_STAT_CERTIFIED",
		)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		if exp and exp != current:
			try:
				if get_datetime(exp) < get_datetime(current):
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_STAT_CONFLICT",
					)
			except Exception:
				if exp != current:
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_STAT_CONFLICT",
					)

	tmpl = get_published_electronic_template(cstr(dto["published_tender_ref"]))
	section_def = _statutory_section(tmpl["snapshot"])
	clean = _sanitize_payload(payload)
	responses = _parse_json(doc.responses, {})
	prev = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	was_certified = bool(prev.get("certified"))

	merged = dict(prev)
	merged["independent_tender_choice"] = clean["independent_tender_choice"]
	merged["competitor_disclosures"] = clean["competitor_disclosures"]
	if was_certified:
		# Owned-input change after cert — invalidate in place.
		invalidate_statutory_certifications(doc, reason="statutory_inputs_changed")
		responses = _parse_json(doc.responses, {})
		merged = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
		merged = dict(merged)
		merged["independent_tender_choice"] = clean["independent_tender_choice"]
		merged["competitor_disclosures"] = clean["competitor_disclosures"]

	validation = validate_statutory_response(section_def, merged)
	merged["section_status"] = validation["section_status"]
	merged["validation_errors"] = [i["message"] for i in validation["issues"]]
	responses[SECTION_KEY] = merged
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"section_saved",
		{
			"section_key": SECTION_KEY,
			"independent_tender_choice": clean["independent_tender_choice"],
			"section_status": validation["section_status"],
		},
	)
	# FoT depends on statutory completeness — withdraw FoT when statutory draft changes.
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		invalidate_fot_certifications,
	)

	invalidate_fot_certifications(doc, reason="statutory_declarations_changed")
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	out = get_statutory_declarations(publication_ref)
	out["saved"] = True
	return out


def invalidate_statutory_certifications(bid_doc, *, reason: str = "source_changed") -> bool:
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	stat = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	if not stat.get("certified") and not stat.get("legal_records"):
		return False
	history = stat.get("certification_history") if isinstance(stat.get("certification_history"), list) else []
	history.append(
		{
			"withdrawn_at": str(now_datetime()),
			"reason": reason,
			"legal_records": stat.get("legal_records"),
			"certified_at": stat.get("certified_at"),
			"certified_by": stat.get("certified_by"),
			"independent_tender_choice": stat.get("independent_tender_choice"),
			"competitor_disclosures": stat.get("competitor_disclosures"),
		}
	)
	stat = dict(stat)
	stat["certification_history"] = history
	stat["certified"] = 0
	stat["certified_at"] = ""
	stat["certified_by"] = ""
	stat["legal_records"] = []
	stat["requires_recertification"] = 1
	stat["section_status"] = STATUS_REQUIRES_RECERTIFICATION
	responses[SECTION_KEY] = stat
	bid_doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		bid_doc,
		"statutory_certification_invalidated",
		{"section_key": SECTION_KEY, "reason": reason},
	)
	return True


def certify_statutory_declarations(
	publication_ref: str,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	dto = get_statutory_declarations(publication_ref)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")
	if not dto.get("can_certify"):
		frappe.throw(
			frappe._("Complete all prerequisites and the independent-tender disclosure before certifying."),
			title="KT_STAT_NOT_READY",
		)

	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		if exp and exp != current:
			try:
				if get_datetime(exp) < get_datetime(current):
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_STAT_CONFLICT",
					)
			except Exception:
				if exp != current:
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_STAT_CONFLICT",
					)

	declarant = dto.get("declarant") or {}
	if not declarant.get("complete"):
		frappe.throw(
			frappe._("Complete the authorized declarant details in the CBQ."),
			title="KT_STAT_DECLARANT",
		)

	# Re-fetch readiness after permission/ownership checks
	fresh = get_statutory_declarations(publication_ref)
	if not fresh.get("can_certify"):
		frappe.throw(
			frappe._("Complete all prerequisites before certifying."),
			title="KT_STAT_NOT_READY",
		)

	tmpl = get_published_electronic_template(cstr(fresh["published_tender_ref"]))
	section_def = _statutory_section(tmpl["snapshot"])
	now = now_datetime()
	ind = fresh.get("independent_tender") or {}
	choice = _normalize_choice(ind.get("choice"))
	rows = ind.get("disclosures") if isinstance(ind.get("disclosures"), list) else []
	stmt, disc_block = _independent_statement(choice, rows)
	subs = {
		"procuring_entity_name": cstr(fresh.get("procuring_entity") or ""),
		"tender_title": cstr(fresh.get("tender_title") or ""),
		"tender_reference": cstr(fresh.get("published_tender_ref") or ""),
		"tenderer_name": cstr(declarant.get("legal_name") or ""),
		"declarant_name": cstr(declarant.get("name") or ""),
		"declarant_title": cstr(declarant.get("title") or ""),
		"declarant_postal_address": cstr(declarant.get("postal_address") or ""),
		"declarant_place_of_residence": cstr(declarant.get("place_of_residence") or ""),
		"declarant_country_of_residence": cstr(declarant.get("country_of_residence") or ""),
		"independent_tender_statement": stmt,
		"competitor_disclosures_block": disc_block,
		"fraud_and_corruption_appendix": "",
		"certified_at": str(now),
	}
	legal_snapshots = []
	for rec in section_def.get("legal_records") or []:
		if not isinstance(rec, dict):
			continue
		rk = cstr(rec.get("record_key") or "")
		appendix = ""
		if cstr(rec.get("appendix_key") or "") == "fraud_and_corruption":
			appendix = cstr(rec.get("appendix_body") or "")
			subs["fraud_and_corruption_appendix"] = appendix
		legal_text = _render_record(rec, subs)
		legal_snapshots.append(
			{
				"record_key": rk,
				"title": cstr(rec.get("title") or rk),
				"legal_text": legal_text,
				"appendix_text": appendix if rk == "code_of_ethics" else "",
				"tenderer_name": subs["tenderer_name"],
				"tender_reference": subs["tender_reference"],
				"declarant_name": subs["declarant_name"],
				"declarant_title": subs["declarant_title"],
				"certified_by": frappe.session.user,
				"certified_at": str(now),
			}
		)

	if len(legal_snapshots) != 4:
		frappe.throw(
			frappe._("Statutory Declarations template must define exactly four legal records."),
			title="KT_STAT_RECORDS",
		)

	responses = _parse_json(doc.responses, {})
	stat = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	stat = dict(stat)
	stat["independent_tender_choice"] = choice
	stat["competitor_disclosures"] = deepcopy(rows)
	stat["legal_records"] = legal_snapshots
	stat["certified"] = 1
	stat["certified_at"] = str(now)
	stat["certified_by"] = frappe.session.user
	stat["certifier_name"] = declarant.get("name")
	stat["certifier_title"] = declarant.get("title")
	stat["requires_recertification"] = 0
	stat["section_status"] = STATUS_COMPLETE
	stat["validation_errors"] = []
	stat["complete"] = True
	responses[SECTION_KEY] = stat
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"statutory_certified",
		{
			"section_key": SECTION_KEY,
			"event_type": "statutory_certified",
			"record_count": len(legal_snapshots),
			"certified_by": frappe.session.user,
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	out = get_statutory_declarations(publication_ref)
	out["certified"] = True
	return out


def seed_statutory_certified_for_tests(publication_ref: str) -> dict[str, Any]:
	"""Test helper: answer independent + certify (requires CBQ already certified with declarant)."""
	save_statutory_declarations(
		publication_ref,
		{"independent_tender_choice": CHOICE_INDEPENDENT, "competitor_disclosures": []},
	)
	return certify_statutory_declarations(publication_ref)
