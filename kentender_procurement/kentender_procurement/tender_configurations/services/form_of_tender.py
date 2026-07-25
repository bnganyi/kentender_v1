# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Website Form of Tender — load, validate, save draft (Save ≠ confirm/submit)."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_DRAFT,
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


SECTION_KEY = "form_of_tender"


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open the Form of Tender."), frappe.PermissionError)


def portal_fot_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def _fot_section(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	frappe.throw(
		frappe._("Published template is missing the Form of Tender section."),
		title="KT_FOT_SECTION_MISSING",
	)


def _is_truthy(val: Any) -> bool:
	if val in (True, 1, "1", "true", "True", "yes", "Yes", "on"):
		return True
	return False


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


def validate_form_of_tender_response(
	section_def: dict[str, Any],
	response: dict[str, Any] | None,
	*,
	for_completion: bool = True,
) -> dict[str, Any]:
	"""Return field/section issues. Does not mutate response."""
	response = response if isinstance(response, dict) else {}
	issues: list[dict[str, str]] = []

	for field in section_def.get("bidder_owned_fields") or []:
		if not isinstance(field, dict):
			continue
		fk = cstr(field.get("field_key") or "")
		cond = field.get("conditional_on")
		required = bool(field.get("required"))
		if isinstance(cond, dict):
			dep = cstr(cond.get("field") or "")
			equals = cond.get("equals")
			if response.get(dep) != equals:
				continue
			required = True
		if required and not _filled(response.get(fk)):
			issues.append(
				{
					"field_key": fk,
					"code": "required",
					"message": f"{cstr(field.get('label') or fk)} is required.",
				}
			)

	status = cstr(response.get("state_owned_status") or "")
	if status == "state_owned" and not _is_truthy(response.get("state_owned_eligibility_affirmation")):
		issues.append(
			{
				"field_key": "state_owned_eligibility_affirmation",
				"code": "required",
				"message": "State-owned eligibility affirmation is required.",
			}
		)

	choice = cstr(response.get("commissions_choice") or "")
	if choice == "disclose":
		rows = response.get("commissions_rows") or []
		if not isinstance(rows, list) or not rows:
			issues.append(
				{
					"field_key": "commissions_rows",
					"code": "required",
					"message": "Disclose at least one commission, gratuity or fee row.",
				}
			)
		else:
			cols = []
			for table in section_def.get("repeatable_tables") or []:
				if isinstance(table, dict) and table.get("table_key") == "commissions_rows":
					cols = table.get("columns") or []
					break
			for idx, row in enumerate(rows):
				if not isinstance(row, dict):
					issues.append(
						{
							"field_key": f"commissions_rows[{idx}]",
							"code": "invalid_row",
							"message": f"Commission row {idx + 1} is invalid.",
						}
					)
					continue
				for col in cols:
					if not isinstance(col, dict) or not col.get("required"):
						continue
					ck = cstr(col.get("field_key") or "")
					if not _filled(row.get(ck)):
						issues.append(
							{
								"field_key": f"commissions_rows[{idx}].{ck}",
								"code": "required",
								"message": (
									f"Commission row {idx + 1}: "
									f"{cstr(col.get('label') or ck)} is required."
								),
							}
						)

	decls_resp = response.get("declarations") or {}
	if not isinstance(decls_resp, dict):
		decls_resp = {}
	for d in section_def.get("declarations") or []:
		if not isinstance(d, dict):
			continue
		if d.get("applicable") is False:
			continue
		if not d.get("required", True):
			continue
		# Associated-form style declarations (o–r) are informational in this lean slice.
		if d.get("associated_section_key"):
			continue
		did = cstr(d.get("declaration_id") or "")
		if not _is_truthy(decls_resp.get(did)):
			issues.append(
				{
					"field_key": f"declarations.{did}",
					"code": "declaration_required",
					"message": f"Accept declaration ({d.get('clause_letter')}): {d.get('title')}",
				}
			)

	# Save must never imply confirmation/submission.
	if response.get("confirmed") in (True, 1, "1") or response.get("submitted") in (True, 1, "1"):
		issues.append(
			{
				"field_key": "confirmed",
				"code": "confirm_not_allowed",
				"message": "Save cannot confirm or submit the Form of Tender in this slice.",
			}
		)

	has_any = _response_started(response)
	if not has_any:
		status_label = STATUS_NOT_STARTED
	elif issues and for_completion:
		status_label = STATUS_NEEDS_ATTENTION
	elif issues:
		status_label = STATUS_IN_PROGRESS
	elif for_completion:
		status_label = STATUS_COMPLETE
	else:
		status_label = STATUS_IN_PROGRESS

	return {
		"ok": not issues,
		"issues": issues,
		"section_status": status_label,
		"issue_count": len(issues),
	}


def _response_started(response: dict[str, Any]) -> bool:
	if not isinstance(response, dict) or not response:
		return False
	meta = {"validation_errors", "blockers", "status", "section_status", "confirmed", "submitted"}
	for key, val in response.items():
		if key in meta:
			continue
		if key == "declarations" and isinstance(val, dict):
			if any(_is_truthy(v) for v in val.values()):
				return True
			continue
		if _filled(val):
			return True
	return False


def derive_fot_section_status(section_def: dict[str, Any], response: dict[str, Any] | None) -> str:
	result = validate_form_of_tender_response(section_def, response, for_completion=True)
	return cstr(result.get("section_status") or STATUS_NOT_STARTED)


def get_form_of_tender(publication_ref: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(publication_ref)
	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(overview.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _fot_section(snapshot)

	cfg_id = cstr(backend.get("configuration_id") or tmpl["configuration_id"])
	draft = create_or_get_draft(cfg_id, schema_snapshot=snapshot, schema_hash=tmpl.get("hash"))
	bid_id = draft.get("bid_id")
	bid = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	responses = _parse_json(getattr(bid, "responses", None), {}) if bid else {}
	fot_resp = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}

	validation = validate_form_of_tender_response(section_def, fot_resp)
	# Persist server-derived status markers into the projection (not client-set completion).
	associated = []
	for card in section_def.get("associated_form_cards") or []:
		if not isinstance(card, dict):
			continue
		sk = cstr(card.get("section_key") or "")
		associated.append(
			{
				"title": cstr(card.get("title") or sk),
				"section_key": sk,
				"status": STATUS_NOT_STARTED,
				"issues_count": 0,
				"action_label": "Open",
				"action_url": f"/tenders/{quote(pub_ref, safe='')}/sections/{quote(sk, safe='')}",
				"informational_only": True,
			}
		)

	tender_owned = section_def.get("tender_owned_values") or {}
	price_summary = section_def.get("price_summary") or snapshot.get("collections", {})
	if not isinstance(price_summary, dict) or "message" not in (price_summary or {}):
		price_summary = section_def.get("price_summary") or {
			"message": "Totals are derived from the Price Schedule when completed.",
			"source": "price_schedule_when_completed",
		}

	return {
		"published_tender_ref": pub_ref,
		"bid_status": cstr(bid.status) if bid else None,
		"bid_modified": str(bid.modified) if bid else None,
		"bid_sealed": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"workspace_url": portal_workspace_url(pub_ref),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Form of Tender"),
		"bidder_instructions": cstr(section_def.get("bidder_instructions") or ""),
		"locked_legal_preamble": cstr(section_def.get("locked_legal_preamble") or ""),
		"tender_owned_values": tender_owned,
		"tender_owned_slots": section_def.get("tender_owned_slots") or [],
		"bidder_owned_fields": section_def.get("bidder_owned_fields") or [],
		"repeatable_tables": section_def.get("repeatable_tables") or [],
		"declarations": section_def.get("declarations") or [],
		"associated_forms": associated,
		"price_summary": price_summary,
		"response": fot_resp,
		"validation": validation,
		"section_status": validation["section_status"],
		"read_only": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"save_confirms": False,
		"save_submits": False,
	}


def save_form_of_tender(
	publication_ref: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = payload if isinstance(payload, dict) else {}

	# Strip illegal confirm/submit flags — Save ≠ confirm/submit.
	payload = dict(payload)
	payload.pop("confirmed", None)
	payload.pop("submitted", None)
	payload.pop("confirmation", None)
	payload["confirmed"] = False
	payload["submitted"] = False

	dto = get_form_of_tender(publication_ref)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")

	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		# Allow equal timestamps; reject when client is stale.
		try:
			if get_datetime(exp) < get_datetime(current) and exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)
		except Exception:
			if exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)

	section_def = None
	tmpl = get_published_electronic_template(cstr(dto["published_tender_ref"]))
	section_def = _fot_section(tmpl["snapshot"])
	validation = validate_form_of_tender_response(section_def, payload)

	# Store response + server-derived status markers (client cannot set Complete).
	stored = dict(payload)
	stored["section_status"] = validation["section_status"]
	stored["validation_errors"] = validation["issues"]
	stored["needs_attention"] = validation["section_status"] == STATUS_NEEDS_ATTENTION
	stored["in_progress"] = validation["section_status"] == STATUS_IN_PROGRESS
	stored["confirmed"] = False
	stored["submitted"] = False

	responses = _parse_json(doc.responses, {})
	responses[SECTION_KEY] = stored
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"section_saved",
		{
			"section_key": SECTION_KEY,
			"section_status": validation["section_status"],
			"issue_count": validation["issue_count"],
			"confirmed": False,
			"submitted": False,
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	out = get_form_of_tender(publication_ref)
	out["saved"] = True
	out["validation"] = validation
	out["section_status"] = validation["section_status"]
	return out


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def assert_fot_not_confirmed_on_save(response: dict[str, Any]) -> bool:
	"""Test helper: saved FoT payloads never carry confirmation/submission."""
	return not bool(response.get("confirmed")) and not bool(response.get("submitted"))
