# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Final Submission workflow — readiness, final review, submit, receipt (G100/G200)."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_DRAFT,
	STATUS_SEALED,
	_append_audit,
	_canonical_hash,
	_get_bid,
	_parse_json,
	_require_logged_in,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
	format_money_display,
	price_schedule_fot_projection,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_APPLICABLE,
	STATUS_NOT_STARTED,
	get_submission_checklist,
	portal_workspace_url,
)

STATE_IN_PROGRESS = "In progress"
STATE_NEEDS_ATTENTION = "Needs attention"
STATE_READY = "Ready to submit"
STATE_SUBMITTED = "Submitted"

RV_STATUS_COMPLETE = "Complete"
RV_STATUS_NEEDS_ATTENTION = "Needs attention"
RV_STATUS_NA = "Not applicable"

SUBMISSION_RESPONSE_KEY = "_submission"

# Sections marked N/A in the ready-bid test helper (still present in lean schema).
_TEST_NA_SECTION_KEYS = frozenset(
	{
		"tender_security",
		"preliminary_requirements_and_evidence",
		"qualification_and_capability",
		"technical_proposal_and_implementation_plan",
		"requirements_compliance",
	}
)


def portal_review_and_validate_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/review-and-validate"


def portal_final_bid_review_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/final-bid-review"


def portal_submit_bid_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/submit-bid"


def portal_submission_receipt_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/submission-receipt"


def _require_login() -> None:
	_require_logged_in()


def _pub_meta(publication_ref: str) -> dict[str, Any]:
	pub_ref = cstr(publication_ref or "").strip()
	if not pub_ref:
		frappe.throw(frappe._("Publication reference is required."), title="PUB_REF_REQUIRED")
	row = frappe.db.get_value(
		"IT Tender Publication Record",
		{"publication_ref": pub_ref, "status": "Published"},
		["name", "configuration", "submission_deadline"],
		as_dict=True,
	)
	if not row:
		frappe.throw(frappe._("Published tender not found."), title="PUB_NOT_FOUND")
	cfg = frappe.get_doc("Tender Configuration", row.configuration)
	return {
		"publication_id": row.name,
		"publication_ref": pub_ref,
		"configuration_id": row.configuration,
		"submission_deadline": row.submission_deadline,
		"tender_title": cstr(getattr(cfg, "tender_title", None) or ""),
		"procuring_entity": cstr(getattr(cfg, "procuring_entity", None) or ""),
		"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
	}


def _deadline_open(deadline: Any) -> bool:
	if not deadline:
		return True
	try:
		return get_datetime(deadline) > now_datetime()
	except Exception:
		return True


def _user_can_submit(bid_doc) -> bool:
	"""Owner of the draft may submit; Administrator may submit in tests/PoC."""
	user = frappe.session.user
	if not user or user == "Guest":
		return False
	if user == "Administrator":
		return True
	return cstr(bid_doc.owner) == user


def _get_owner_bid_doc(configuration_id: str):
	"""Prefer sealed bid for the session owner; else open/create draft."""
	configuration_id = cstr(configuration_id or "").strip()
	user = frappe.session.user
	filters_base = {"configuration": configuration_id}
	if user and user not in ("Guest", "Administrator"):
		filters_base["owner"] = user
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{**filters_base, "status": STATUS_SEALED},
		"name",
		order_by="sealed_at desc",
	)
	if sealed_name:
		return _get_bid(sealed_name)
	draft = create_or_get_draft(configuration_id)
	bid_id = cstr(draft.get("bid_id") or "")
	return _get_bid(bid_id) if bid_id else None


def _map_rv_status(status: str) -> str:
	if status == STATUS_COMPLETE:
		return RV_STATUS_COMPLETE
	if status == STATUS_NOT_APPLICABLE:
		return RV_STATUS_NA
	return RV_STATUS_NEEDS_ATTENTION


def _price_totals(responses: dict[str, Any]) -> dict[str, Any]:
	proj = price_schedule_fot_projection(responses.get("price_schedule"))
	rows: list[dict[str, str]] = []
	by_raw = proj.get("by_currency")
	if isinstance(by_raw, list):
		for row in by_raw:
			if not isinstance(row, dict):
				continue
			cur = cstr(row.get("currency") or "KES")
			total = row.get("grand_total")
			if total in (None, ""):
				total = row.get("total") or row.get("amount")
			display = cstr(row.get("grand_total_display") or row.get("total_display") or "")
			if not display and total not in (None, ""):
				display = format_money_display(total)
			rows.append({"currency": cur, "total": cstr(total or ""), "total_display": display or "—"})
	elif isinstance(by_raw, dict):
		for cur, val in by_raw.items():
			if isinstance(val, dict):
				total = val.get("grand_total") or val.get("total") or val.get("amount")
				display = cstr(val.get("grand_total_display") or val.get("total_display") or "")
			else:
				total = val
				display = ""
			if not display and total not in (None, ""):
				display = format_money_display(total)
			rows.append(
				{
					"currency": cstr(cur or "KES"),
					"total": cstr(total or ""),
					"total_display": display or "—",
				}
			)
	if not rows and proj.get("grand_total") not in (None, ""):
		cur = cstr(proj.get("currency") or "KES")
		display = cstr(proj.get("grand_total_display") or "")
		if not display:
			display = format_money_display(proj.get("grand_total"))
		rows.append(
			{
				"currency": cur,
				"total": cstr(proj.get("grand_total") or ""),
				"total_display": display or "—",
			}
		)
	return {
		"by_currency": rows,
		"grand_total_display": cstr(
			proj.get("grand_total_display") or (rows[0]["total_display"] if rows else "—")
		),
		"currency": cstr(proj.get("currency") or (rows[0]["currency"] if rows else "KES")),
		"complete": 1 if proj.get("complete") else 0,
	}


def _fot_totals(responses: dict[str, Any], price_totals: dict[str, Any]) -> dict[str, Any]:
	"""FoT totals are projections from Price Schedule — never a second stored total."""
	return {
		"source": "price_schedule",
		"by_currency": price_totals.get("by_currency") or [],
		"grand_total_display": price_totals.get("grand_total_display") or "—",
		"currency": price_totals.get("currency") or "KES",
	}


def _addenda_status(checklist: dict[str, Any]) -> dict[str, Any]:
	docs = next(
		(
			s
			for s in (checklist.get("sections") or [])
			if s.get("section_key") == "tender_documents_and_addenda"
		),
		None,
	)
	if not docs:
		return {"required": 0, "acknowledged": 1, "status": RV_STATUS_NA}
	st = cstr(docs.get("status") or "")
	return {
		"required": 1 if docs.get("required") else 0,
		"acknowledged": 1 if st == STATUS_COMPLETE else 0,
		"status": _map_rv_status(st),
	}


def _blocking_issues_from_checklist(checklist: dict[str, Any]) -> list[dict[str, Any]]:
	issues: list[dict[str, Any]] = []
	for sec in checklist.get("sections") or []:
		status = cstr(sec.get("status") or "")
		if status in (STATUS_COMPLETE, STATUS_NOT_APPLICABLE):
			continue
		if status == STATUS_NOT_STARTED and not sec.get("required"):
			continue
		key = cstr(sec.get("section_key") or "")
		title = cstr(sec.get("title") or key)
		url = cstr(sec.get("action_url") or "#")
		if status == STATUS_NEEDS_ATTENTION:
			label_txt = cstr(sec.get("issues_label") or "").strip()
			if label_txt and label_txt not in ("—", "-") and "Blocker" not in label_txt:
				msg = label_txt
			else:
				msg = f"{title} needs attention before submission."
			label = "Resolve"
		elif status == STATUS_NOT_STARTED:
			msg = f"{title} has not been started."
			label = "Start"
		else:
			msg = f"{title} is incomplete."
			label = "Continue"
		# Prefer FoT-style stale review messaging when present in issues_label
		issues.append(
			{
				"message": msg,
				"section_key": key,
				"section_title": title,
				"item_id": "",
				"resolve_url": url,
				"resolve_label": label,
			}
		)
	return issues


def get_bid_submission_readiness(published_tender_ref: str) -> dict[str, Any]:
	"""Server-derived readiness for Review & Validate / Submit (pack §4)."""
	_require_login()
	meta = _pub_meta(published_tender_ref)
	pub_ref = meta["publication_ref"]
	bid_doc = _get_owner_bid_doc(meta["configuration_id"])
	bid_id = cstr(bid_doc.name) if bid_doc else ""
	responses = _parse_json(getattr(bid_doc, "responses", None), {}) if bid_doc else {}
	bid_sealed = bool(bid_doc and cstr(bid_doc.status) == STATUS_SEALED)
	deadline_open = _deadline_open(meta["submission_deadline"])
	can_submit_perm = bool(bid_doc and _user_can_submit(bid_doc))

	checklist: dict[str, Any] = {}
	checklist_closed = False
	try:
		checklist = get_submission_checklist(pub_ref)
	except frappe.ValidationError as exc:
		# Past deadline → overview/checklist may refuse workspace access
		if "Closed" in cstr(exc) or "BID_WORKSPACE_UNAVAILABLE" in cstr(getattr(exc, "title", "") or ""):
			checklist_closed = True
			deadline_open = False
		else:
			raise
	if checklist.get("submission_deadline"):
		deadline_open = deadline_open and _deadline_open(checklist.get("submission_deadline"))
	if checklist_closed:
		deadline_open = False
	bid_sealed = bid_sealed or cstr(checklist.get("bid_status") or "") == STATUS_SEALED

	if checklist_closed and not bid_sealed:
		# Minimal readiness when checklist is unavailable after deadline
		return {
			"published_tender_ref": pub_ref,
			"bid_id": bid_id,
			"bid_status": cstr(bid_doc.status) if bid_doc else None,
			"overall_state": STATE_NEEDS_ATTENTION,
			"ready_to_submit": 0,
			"blocking_issue_count": 1,
			"blocking_issues": [
				{
					"message": "The submission deadline has passed.",
					"section_key": "",
					"section_title": "Deadline",
					"item_id": "",
					"resolve_url": f"/tenders/{quote(pub_ref, safe='')}",
					"resolve_label": "View tender",
				}
			],
			"sections": [],
			"price_schedule_totals": _price_totals(responses),
			"form_of_tender_totals": _fot_totals(responses, _price_totals(responses)),
			"addenda_acknowledgement": {"required": 0, "acknowledged": 0, "status": RV_STATUS_NA},
			"deadline_open": 0,
			"submission_deadline": meta["submission_deadline"],
			"submission_deadline_display": "—",
			"submission_permission": 1 if can_submit_perm else 0,
			"can_submit": 0,
			"tender_title": meta["tender_title"] or "",
			"procuring_entity": meta["procuring_entity"] or "",
			"bidder_label": cstr(getattr(bid_doc, "bidder_label", None) or "") if bid_doc else "",
			"workspace_url": portal_workspace_url(pub_ref),
			"review_and_validate_url": portal_review_and_validate_url(pub_ref),
			"final_bid_review_url": portal_final_bid_review_url(pub_ref),
			"submit_bid_url": portal_submit_bid_url(pub_ref),
			"submission_receipt_url": portal_submission_receipt_url(pub_ref),
			"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
			"review_nav_enabled": 0,
			"submit_nav_enabled": 0,
		}

	sections_out: list[dict[str, Any]] = []
	for sec in checklist.get("sections") or []:
		status = cstr(sec.get("status") or "")
		rv = _map_rv_status(status)
		sections_out.append(
			{
				"section_key": sec.get("section_key"),
				"title": sec.get("title"),
				"required": 1 if sec.get("required") else 0,
				"status": rv,
				"checklist_status": status,
				"issues_count": int(sec.get("issues_count") or 0),
				"issues_label": sec.get("issues_label") or "—",
				"last_updated": sec.get("last_updated") or "—",
				"action_label": "Resolve"
				if rv == RV_STATUS_NEEDS_ATTENTION
				else ("Review" if rv == RV_STATUS_COMPLETE else "Review"),
				"action_url": sec.get("action_url") or "#",
				"action_enabled": 0 if rv == RV_STATUS_NA else 1,
			}
		)

	blocking = _blocking_issues_from_checklist(checklist)
	if not deadline_open and not bid_sealed:
		blocking.append(
			{
				"message": "The submission deadline has passed.",
				"section_key": "",
				"section_title": "Deadline",
				"item_id": "",
				"resolve_url": checklist.get("overview_url") or f"/tenders/{quote(pub_ref, safe='')}",
				"resolve_label": "View tender",
			}
		)

	price_totals = _price_totals(responses)
	fot_totals = _fot_totals(responses, price_totals)
	addenda = _addenda_status(checklist)

	required_rows = [s for s in sections_out if s.get("required") and s["status"] != RV_STATUS_NA]
	all_required_complete = bool(required_rows) and all(
		s["status"] == RV_STATUS_COMPLETE for s in required_rows
	)
	any_started = any(
		s.get("checklist_status") not in (STATUS_NOT_STARTED, STATUS_NOT_APPLICABLE, "")
		for s in sections_out
	)
	has_attention = bool(checklist.get("has_blockers")) or any(
		s.get("checklist_status") == STATUS_NEEDS_ATTENTION for s in sections_out
	)

	if bid_sealed:
		overall = STATE_SUBMITTED
	elif all_required_complete and not blocking:
		overall = STATE_READY
	elif has_attention or (any_started and not all_required_complete) or blocking:
		overall = STATE_NEEDS_ATTENTION
	else:
		overall = STATE_IN_PROGRESS

	ready_to_submit = overall == STATE_READY and deadline_open and not bid_sealed

	return {
		"published_tender_ref": pub_ref,
		"bid_id": bid_id,
		"bid_status": cstr(bid_doc.status) if bid_doc else None,
		"overall_state": overall,
		"ready_to_submit": 1 if ready_to_submit else 0,
		"blocking_issue_count": len(blocking),
		"blocking_issues": blocking,
		"sections": sections_out,
		"price_schedule_totals": price_totals,
		"form_of_tender_totals": fot_totals,
		"addenda_acknowledgement": addenda,
		"deadline_open": 1 if deadline_open else 0,
		"submission_deadline": meta["submission_deadline"] or checklist.get("submission_deadline"),
		"submission_deadline_display": checklist.get("submission_deadline_display") or "—",
		"submission_permission": 1 if can_submit_perm else 0,
		"can_submit": 1 if (ready_to_submit and can_submit_perm) else 0,
		"tender_title": meta["tender_title"] or checklist.get("tender_title") or "",
		"procuring_entity": meta["procuring_entity"] or checklist.get("procuring_entity") or "",
		"bidder_label": cstr(getattr(bid_doc, "bidder_label", None) or "") if bid_doc else "",
		"workspace_url": portal_workspace_url(pub_ref),
		"review_and_validate_url": portal_review_and_validate_url(pub_ref),
		"final_bid_review_url": portal_final_bid_review_url(pub_ref),
		"submit_bid_url": portal_submit_bid_url(pub_ref),
		"submission_receipt_url": portal_submission_receipt_url(pub_ref),
		"overview_url": checklist.get("overview_url") or f"/tenders/{quote(pub_ref, safe='')}",
		"review_nav_enabled": 1 if (all_required_complete or bid_sealed or overall == STATE_READY) else 0,
		"submit_nav_enabled": 1 if (ready_to_submit or bid_sealed) else 0,
	}


def get_final_bid_review(published_tender_ref: str) -> dict[str, Any]:
	"""Read-only Final Bid Review DTO (pack §7)."""
	ready = get_bid_submission_readiness(published_tender_ref)
	if ready.get("overall_state") == STATE_SUBMITTED:
		pass
	elif ready.get("blocking_issue_count") or ready.get("overall_state") != STATE_READY:
		frappe.throw(
			frappe._("Resolve all blocking issues before opening Final Bid Review."),
			title="BID_NOT_READY",
		)

	meta = _pub_meta(published_tender_ref)
	bid_doc = _get_bid(ready["bid_id"]) if ready.get("bid_id") else None
	responses = _parse_json(getattr(bid_doc, "responses", None), {}) if bid_doc else {}

	price_totals = ready.get("price_schedule_totals") or _price_totals(responses)
	fot_totals = ready.get("form_of_tender_totals") or _fot_totals(responses, price_totals)

	section_summaries: list[dict[str, Any]] = []
	for sec in ready.get("sections") or []:
		if sec.get("status") == RV_STATUS_NA:
			continue
		key = cstr(sec.get("section_key") or "")
		summary = _section_response_summary(
			key,
			responses.get(key),
			sec,
			price_totals=price_totals,
			fot_totals=fot_totals,
			responses=responses,
		)
		summary_text = summary.get("summary")
		if summary_text is None or (
			not cstr(summary_text).strip()
			and not summary.get("totals_rows")
			and not summary.get("detail_rows")
		):
			summary_text = "Response recorded."
		section_summaries.append(
			{
				"section_key": key,
				"title": sec.get("title"),
				"status": sec.get("status"),
				"summary": cstr(summary_text or ""),
				"summary_label": summary.get("summary_label") or "Summary",
				"detail_rows": summary.get("detail_rows") or [],
				"totals_rows": summary.get("totals_rows") or [],
				"card_variant": summary.get("card_variant") or "default",
				"evidence_names": summary.get("evidence_names") or [],
				"review_url": sec.get("action_url") or "#",
			}
		)

	lots = _applicable_lots(responses)
	return {
		**{k: ready[k] for k in (
			"published_tender_ref",
			"bid_id",
			"tender_title",
			"procuring_entity",
			"bidder_label",
			"submission_deadline",
			"submission_deadline_display",
			"price_schedule_totals",
			"form_of_tender_totals",
			"workspace_url",
			"review_and_validate_url",
			"submit_bid_url",
			"overview_url",
		)},
		"overall_state": STATE_READY if ready.get("overall_state") != STATE_SUBMITTED else STATE_SUBMITTED,
		"status_chip": "Ready to submit" if ready.get("overall_state") != STATE_SUBMITTED else "Submitted",
		"tender_reference": meta["configuration_ref"] or meta["publication_ref"],
		"applicable_lots": lots,
		"offer_type": "Main offer",
		"sections": section_summaries,
		"read_only": 1,
	}


def _applicable_lots(responses: dict[str, Any]) -> list[str]:
	ps = responses.get("price_schedule") if isinstance(responses.get("price_schedule"), dict) else {}
	lots = ps.get("selected_lots") or ps.get("lots") or []
	if isinstance(lots, list) and lots:
		out = []
		for lot in lots:
			if isinstance(lot, dict):
				out.append(cstr(lot.get("name") or lot.get("lot_id") or lot.get("code") or ""))
			else:
				out.append(cstr(lot))
		return [x for x in out if x]
	return ["Main offer"]


def _section_response_summary(
	key: str,
	payload: Any,
	sec_row: dict[str, Any],
	*,
	price_totals: dict[str, Any] | None = None,
	fot_totals: dict[str, Any] | None = None,
	responses: dict[str, Any] | None = None,
) -> dict[str, Any]:
	payload = payload if isinstance(payload, dict) else {}
	responses = responses if isinstance(responses, dict) else {}
	price_totals = price_totals or {}
	fot_totals = fot_totals or {}
	evidence: list[str] = []
	by_currency = price_totals.get("by_currency") if isinstance(price_totals.get("by_currency"), list) else []
	totals_rows = [
		{
			"label": cstr(t.get("currency") or ""),
			"value": cstr(t.get("total_display") or "—"),
		}
		for t in by_currency
		if isinstance(t, dict)
	]

	if key == "price_schedule":
		return {
			"summary": "",
			"summary_label": "Itemized totals",
			"totals_rows": totals_rows,
			"card_variant": "price",
			"evidence_names": evidence,
		}
	if key == "form_of_tender":
		fot = payload
		cert_name = ""
		instances = fot.get("instances") if isinstance(fot.get("instances"), list) else []
		if instances and isinstance(instances[0], dict):
			cert_name = cstr(
				(instances[0].get("legal_record") or {}).get("signatory_name")
				or instances[0].get("certified_by")
				or ""
			)
		if not cert_name:
			cbq = responses.get("confidential_business_questionnaire") or {}
			for ent in cbq.get("entities") or []:
				if isinstance(ent, dict) and ent.get("certified"):
					ans = ent.get("answers") if isinstance(ent.get("answers"), dict) else {}
					cert_name = cstr(
						ent.get("certifier_name")
						or ans.get("authorized_signatory_name")
						or ""
					)
					if cert_name:
						break
		return {
			"summary": "",
			"summary_label": "Derived tender price",
			"totals_rows": totals_rows or [
				{
					"label": cstr(fot_totals.get("currency") or ""),
					"value": cstr(fot_totals.get("grand_total_display") or "—"),
				}
			],
			"detail_rows": (
				[{"label": "Authorized certifier", "value": cert_name}] if cert_name else []
			),
			"card_variant": "fot",
			"evidence_names": evidence,
		}
	if key == "tender_documents_and_addenda":
		return {
			"summary": "Official tender documents viewed; required addenda acknowledged.",
			"summary_label": "Summary",
			"evidence_names": evidence,
		}
	if key == "confidential_business_questionnaire":
		cert_name = ""
		cert_at = ""
		for ent in payload.get("entities") or []:
			if isinstance(ent, dict) and ent.get("certified"):
				cert_name = cstr(ent.get("certifier_name") or ent.get("legal_name") or "")
				cert_at = cstr(ent.get("certified_at") or "")
				break
		if cert_name:
			msg = f"Certified by {cert_name}"
			if cert_at:
				msg += f" on {cert_at[:10]}" if len(cert_at) >= 10 else f" on {cert_at}"
			return {"summary": msg + ".", "summary_label": "Summary", "evidence_names": evidence}
		return {
			"summary": "Confidential Business Questionnaire completed.",
			"summary_label": "Summary",
			"evidence_names": evidence,
		}
	if key == "statutory_declarations":
		n = 0
		for rec in payload.get("records") or payload.get("declarations") or []:
			if isinstance(rec, dict) and (rec.get("certified") or rec.get("complete")):
				n += 1
		if n:
			return {
				"summary": f"All {n} declaration(s) certified." if n else "Statutory declarations certified.",
				"summary_label": "Summary",
				"evidence_names": evidence,
			}
		return {
			"summary": "Statutory declarations certified.",
			"summary_label": "Summary",
			"evidence_names": evidence,
		}
	if key == "tender_security":
		mode = cstr(payload.get("mode") or payload.get("security_mode") or "").replace("_", " ").title()
		inst = payload.get("instrument") if isinstance(payload.get("instrument"), dict) else {}
		return {
			"summary": mode or "Tender security provided.",
			"summary_label": "Security type",
			"detail_rows": [
				r
				for r in (
					{
						"label": "Amount",
						"value": cstr(inst.get("guaranteed_amount") or payload.get("amount") or ""),
					},
					{
						"label": "Issuing institution",
						"value": cstr(inst.get("issuer_name") or ""),
					},
				)
				if r["value"]
			],
			"evidence_names": evidence,
		}
	if payload.get("certified") or (
		isinstance(payload.get("entities"), list)
		and any(isinstance(e, dict) and e.get("certified") for e in payload.get("entities") or [])
	):
		return {
			"summary": "Certified electronic response on file.",
			"summary_label": "Summary",
			"evidence_names": evidence,
		}
	if payload.get("complete") or cstr(payload.get("section_status")) == STATUS_COMPLETE:
		return {
			"summary": "Section completed.",
			"summary_label": "Summary",
			"evidence_names": evidence,
		}
	return {
		"summary": cstr(sec_row.get("issues_label") or "Response recorded.").replace("—", "").strip()
		or "Response recorded.",
		"summary_label": "Summary",
		"evidence_names": evidence,
	}


def get_submit_bid_page(published_tender_ref: str) -> dict[str, Any]:
	"""Submit Bid screen DTO (pack §8)."""
	ready = get_bid_submission_readiness(published_tender_ref)
	if ready.get("overall_state") == STATE_SUBMITTED:
		frappe.throw(
			frappe._("This bid has already been submitted."),
			title="BID_ALREADY_SUBMITTED",
		)
	if ready.get("overall_state") != STATE_READY or ready.get("blocking_issue_count"):
		frappe.throw(
			frappe._("The bid is not ready to submit. Complete Review & Validate first."),
			title="BID_NOT_READY",
		)

	meta = _pub_meta(published_tender_ref)
	user = frappe.session.user
	full_name = cstr(frappe.db.get_value("User", user, "full_name") or user)
	email = cstr(frappe.db.get_value("User", user, "email") or user)
	bid_doc = _get_bid(ready["bid_id"])
	org = cstr(bid_doc.bidder_label or "")

	return {
		**{k: ready[k] for k in (
			"published_tender_ref",
			"bid_id",
			"tender_title",
			"procuring_entity",
			"bidder_label",
			"submission_deadline",
			"submission_deadline_display",
			"price_schedule_totals",
			"form_of_tender_totals",
			"overall_state",
			"ready_to_submit",
			"can_submit",
			"submission_permission",
			"deadline_open",
			"workspace_url",
			"final_bid_review_url",
			"submission_receipt_url",
			"overview_url",
		)},
		"tender_reference": meta["configuration_ref"] or meta["publication_ref"],
		"applicable_lots": _applicable_lots(_parse_json(bid_doc.responses, {})),
		"status_chip": "Ready to submit",
		"submitter": {
			"full_name": full_name,
			"organisation": org,
			"role": "Authorised submitter" if ready.get("submission_permission") else "Reviewer",
			"email": email,
		},
		"declaration_text": (
			"I confirm that I am authorised to submit this bid on behalf of the bidder "
			"and that the electronic bid reviewed above is the bid being submitted."
		),
		"permission_message": (
			""
			if ready.get("submission_permission")
			else "You do not have permission to submit this bid."
		),
	}


def build_submission_receipt_dto(bid_doc, *, publication_ref: str = "") -> dict[str, Any]:
	"""Bidder-facing receipt — no hashes, schema names, or internal IDs."""
	meta = _pub_meta(publication_ref) if publication_ref else {}
	responses = _parse_json(bid_doc.responses, {})
	price_totals = _price_totals(responses)
	sealed_at = bid_doc.sealed_at
	try:
		sealed_display = format_datetime(sealed_at) if sealed_at else "—"
	except Exception:
		sealed_display = cstr(sealed_at) or "—"
	tz = cstr(frappe.utils.get_system_timezone() if hasattr(frappe.utils, "get_system_timezone") else "")
	if not tz:
		try:
			from frappe.utils import get_time_zone

			tz = cstr(get_time_zone() or "")
		except Exception:
			tz = ""
	submitter_name = ""
	if bid_doc.sealed_by:
		submitter_name = cstr(
			frappe.db.get_value("User", bid_doc.sealed_by, "full_name") or bid_doc.sealed_by
		)
	pub_ref = publication_ref or cstr(meta.get("publication_ref") or "")
	return {
		"published_tender_ref": pub_ref,
		"receipt_code": cstr(bid_doc.receipt_code or ""),
		"submitted_at": str(sealed_at) if sealed_at else None,
		"submitted_at_display": sealed_display,
		"timezone": tz or "Africa/Nairobi",
		"tender_title": meta.get("tender_title") or "",
		"tender_reference": meta.get("configuration_ref") or pub_ref,
		"procuring_entity": meta.get("procuring_entity") or "",
		"bidder_label": cstr(bid_doc.bidder_label or ""),
		"submitted_by": submitter_name,
		"applicable_lots": _applicable_lots(responses),
		"price_schedule_totals": price_totals,
		"submission_status": "Submitted",
		"status_chip": "Bid submitted",
		"message": "Your bid has been formally submitted.",
		"receipt_note": (
			"This receipt confirms that the electronic bid was received by KenTender "
			"at the date and time shown above."
		),
		"my_bids_url": "/tenders",
		"workspace_url": portal_workspace_url(pub_ref) if pub_ref else "/tenders",
	}


def get_submission_receipt(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	meta = _pub_meta(published_tender_ref)
	bid_doc = _get_owner_bid_doc(meta["configuration_id"])
	if not bid_doc or cstr(bid_doc.status) != STATUS_SEALED:
		frappe.throw(frappe._("Receipt is available only after submission."), title="BID_NOT_SEALED")
	return build_submission_receipt_dto(bid_doc, publication_ref=meta["publication_ref"])


def _seal_bid_document(bid_doc, *, declaration_confirmed: bool) -> dict[str, Any]:
	"""Persist seal on Electronic Bid Submission (internal integrity hash retained)."""
	if cstr(bid_doc.status) == STATUS_SEALED:
		return bid_doc

	from kentender_procurement.tender_configurations.services.bid_evidence import (
		freeze_evidence_for_seal,
	)

	responses = _parse_json(bid_doc.responses, {})
	now = now_datetime()
	responses[SUBMISSION_RESPONSE_KEY] = {
		"confirmed": 1 if declaration_confirmed else 0,
		"confirmed_at": str(now),
		"confirmed_by": frappe.session.user,
	}
	# Reject client-supplied status/time/totals by overwriting from server only
	bid_doc.responses = json.dumps(responses, ensure_ascii=False)
	bid_doc.save(ignore_permissions=True)

	evidence_snap = freeze_evidence_for_seal(bid_doc.name)
	bid_doc = _get_bid(bid_doc.name)
	responses = _parse_json(bid_doc.responses, {})
	seal_hash = _canonical_hash(
		{
			"responses": responses,
			"schema_hash": bid_doc.schema_hash,
			"configuration_id": bid_doc.configuration,
			"std_version": bid_doc.std_version,
			"evidence_versions": evidence_snap.get("versions") or [],
		}
	)
	receipt = (
		f"EBD-{cstr(bid_doc.configuration_ref or bid_doc.configuration)}-"
		f"{frappe.generate_hash(length=8).upper()}"
	)
	now = now_datetime()
	bid_doc.status = STATUS_SEALED
	bid_doc.sealed_at = now
	bid_doc.sealed_by = frappe.session.user
	bid_doc.seal_hash = seal_hash
	bid_doc.receipt_code = receipt
	bid_doc.receipt_issued_at = now
	_append_audit(bid_doc, "sealed", {"receipt_code": receipt})
	_append_audit(bid_doc, "receipt_issued", {"receipt_code": receipt})
	bid_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bid_doc


def submit_bid(published_tender_ref: str, *, declaration_confirmed: bool | int = False) -> dict[str, Any]:
	"""Atomic portal submit (pack §11). Client cannot supply time/status/totals."""
	_require_login()
	confirmed = bool(int(declaration_confirmed)) if not isinstance(declaration_confirmed, bool) else declaration_confirmed
	if not confirmed:
		frappe.throw(
			frappe._("Confirm the final declaration before submitting."),
			title="DECLARATION_REQUIRED",
		)

	meta = _pub_meta(published_tender_ref)
	ready = get_bid_submission_readiness(meta["publication_ref"])
	bid_doc = _get_owner_bid_doc(meta["configuration_id"])
	if bid_doc and cstr(bid_doc.status) == STATUS_SEALED:
		return build_submission_receipt_dto(bid_doc, publication_ref=meta["publication_ref"])

	if not ready.get("deadline_open"):
		frappe.throw(frappe._("The submission deadline has passed."), title="DEADLINE_PASSED")
	if not ready.get("submission_permission"):
		frappe.throw(
			frappe._("You do not have permission to submit this bid."),
			frappe.PermissionError,
		)
	if ready.get("blocking_issue_count") or ready.get("overall_state") != STATE_READY:
		frappe.throw(
			frappe._("Submission validation failed. Resolve blocking issues and try again."),
			title="BID_VALIDATION_FAILED",
		)

	if not bid_doc:
		frappe.throw(frappe._("Electronic bid not found."), title="BID_NOT_FOUND")
	# Re-check owner at seal time
	if not _user_can_submit(bid_doc):
		frappe.throw(
			frappe._("You do not have permission to submit this bid."),
			frappe.PermissionError,
		)

	sealed = _seal_bid_document(bid_doc, declaration_confirmed=True)
	return build_submission_receipt_dto(sealed, publication_ref=meta["publication_ref"])


def _mark_sections_na_in_snapshot(snap: dict[str, Any], keys: frozenset[str]) -> dict[str, Any]:
	out = dict(snap)
	sections = []
	for sec in snap.get("sections") or []:
		if not isinstance(sec, dict):
			continue
		row = dict(sec)
		key = cstr(row.get("section_key") or row.get("key") or "")
		if key in keys:
			row["not_applicable"] = True
			row["applicable"] = False
			row["required"] = False
		sections.append(row)
	out["sections"] = sections
	return out


def _seed_complete_cbq_for_tests(pub_ref: str, bid_id: str) -> None:
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		CONFLICT_ROW_KEYS,
		certify_cbq_entity,
		get_confidential_business_questionnaire,
		save_confidential_business_questionnaire,
	)

	dto = get_confidential_business_questionnaire(pub_ref)
	entities = [e for e in (dto.get("entities") or []) if isinstance(e, dict)]
	if not entities:
		entities = [
			{
				"entity_id": "ent-bidder-1",
				"role": "bidder",
				"legal_name": "Lean Demo Bidder Ltd",
				"entity_type": "company",
			}
		]
	ent = dict(entities[0])
	ent["entity_type"] = "company"
	ent["legal_name"] = "Lean Demo Bidder Ltd"
	ent["answers"] = {
		"submission_type": "single",
		"country": "Kenya",
		"city": "Nairobi",
		"location": "Westlands",
		"building": "Acme Tower",
		"floor": "5",
		"postal_address": "P.O. Box 12345",
		"contact_person": "Jane Doe",
		"contact_email": "jane@lean-demo.example",
		"nature_of_business": "ICT systems integration",
		"max_business_value": "50000000",
		"currency": "KES",
		"trade_licence_number": "TL-100",
		"licence_expiry": "2027-12-31",
		"registering_body": {
			"name": "Registrar of Companies",
			"country": "Kenya",
			"physical_address": "Sheria House",
			"postal_address": "P.O. Box 30031",
			"email": "roc@example.go.ke",
			"phone": "+254700000000",
		},
		"stock_exchange_listed": "no",
		"pe_interest_disclosure": "no",
		"company_type": "private_limited",
		"share_capital_nominal": "1000000",
		"share_capital_issued": "1000000",
		"directors": [
			{
				"name": "Jane Doe",
				"nationality": "KE",
				"citizenship": "Kenyan",
				"shares_percent": "100",
			}
		],
		"authorized_signatory_name": "Jane Doe",
		"authorized_signatory_title": "Managing Director",
		"authority_to_bind_confirmed": "yes",
		"declarant_postal_address": "P.O. Box 12345",
		"declarant_place_of_residence": "Nairobi",
		"declarant_country_of_residence": "Kenya",
		"state_owned_enterprise": "no",
	}
	ent["conflict_rows"] = {k: {"answer": "no", "details": ""} for k in CONFLICT_ROW_KEYS}
	saved = save_confidential_business_questionnaire(
		pub_ref, {"entities": [ent], "history": []}
	)
	saved_ents = [
		e for e in (saved.get("entities") or []) if isinstance(e, dict)
	]
	entity_id = cstr((saved_ents[0] if saved_ents else ent).get("entity_id") or "")
	if not entity_id:
		frappe.throw(frappe._("CBQ entity id missing after save."), title="CBQ_SEED")
	certify_cbq_entity(
		pub_ref,
		entity_id,
		certifier_name="Jane Doe",
		certifier_title="Managing Director",
		authority_affirmed=1,
	)


def _seed_complete_price_schedule_for_tests(pub_ref: str) -> None:
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		complete_price_schedule,
		get_price_schedule_editor,
		get_price_schedule_overview,
		save_price_schedule_lines,
	)

	overview = get_price_schedule_overview(pub_ref)
	schedules = overview.get("schedules") or []
	schedule_key = ""
	for s in schedules:
		if isinstance(s, dict) and cstr(s.get("schedule_key")):
			schedule_key = cstr(s.get("schedule_key"))
			break
	if not schedule_key:
		schedule_key = "supply"
	editor = get_price_schedule_editor(pub_ref, schedule_key)
	lines_out: list[dict[str, Any]] = []
	for row in editor.get("rows") or editor.get("lines") or []:
		if not isinstance(row, dict):
			continue
		lid = cstr(row.get("line_id") or "")
		if not lid:
			continue
		required = row.get("required") in (1, "1", True, "true") or row.get("is_required")
		if not required:
			continue
		lines_out.append(
			{
				"line_id": lid,
				"unit_price": "1000",
				"country_of_origin": "Kenya",
				"currency": cstr(row.get("currency") or "KES"),
			}
		)
	if not lines_out:
		# Fallback: price every editor row
		for row in editor.get("rows") or editor.get("lines") or []:
			if not isinstance(row, dict):
				continue
			lid = cstr(row.get("line_id") or "")
			if not lid:
				continue
			lines_out.append(
				{
					"line_id": lid,
					"unit_price": "1000",
					"country_of_origin": "Kenya",
					"currency": cstr(row.get("currency") or "KES"),
				}
			)
	if lines_out:
		save_price_schedule_lines(
			pub_ref,
			{
				"schedule_key": schedule_key,
				"lines": lines_out,
				"discounts_offered": "no",
			},
		)
	complete_price_schedule(pub_ref)


def seed_ready_lean_bid_for_final_submission_tests(
	*,
	fixture: str = "single_lot",
	clear: bool = True,
) -> dict[str, Any]:
	"""Publish lean PS, mark heavy sections N/A, complete docs/CBQ/statutory/PS/FoT."""
	from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
		publish_lean_price_schedule_for_tests,
	)
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		certify_form_of_tender,
		get_form_of_tender,
		save_form_of_tender,
	)
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		seed_statutory_certified_for_tests,
	)
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		acknowledge_tender_documents,
	)

	_require_login()
	pub = publish_lean_price_schedule_for_tests(fixture=fixture, clear=clear)
	pub_ref = cstr(pub.get("publication_ref") or "")
	cfg_id = cstr(pub.get("configuration_id") or "")
	pub_id = cstr(pub.get("publication_id") or "")

	# Mark complex sections N/A on publication snapshot + draft schema
	raw = frappe.db.get_value("IT Tender Publication Record", pub_id, "electronic_template_snapshot")
	snap = _parse_json(raw, {})
	snap = _mark_sections_na_in_snapshot(snap, _TEST_NA_SECTION_KEYS)
	frappe.db.set_value(
		"IT Tender Publication Record",
		pub_id,
		"electronic_template_snapshot",
		json.dumps(snap, ensure_ascii=False),
	)

	draft = create_or_get_draft(cfg_id, schema_snapshot=snap, schema_hash=cstr(snap.get("schema_hash") or ""))
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	doc.schema_snapshot = json.dumps(snap, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	get_form_of_tender(pub_ref)
	acknowledge_tender_documents(pub_ref)
	_seed_complete_price_schedule_for_tests(pub_ref)
	_seed_complete_cbq_for_tests(pub_ref, bid_id)

	doc = _get_bid(bid_id)
	doc.bidder_label = "Lean Demo Bidder Ltd"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	seed_statutory_certified_for_tests(pub_ref)
	save_form_of_tender(pub_ref, {"commissions_choice": "no", "commissions_rows": []})
	certify_form_of_tender(pub_ref)

	ready = get_bid_submission_readiness(pub_ref)
	return {
		"publication_ref": pub_ref,
		"publication_id": pub_id,
		"configuration_id": cfg_id,
		"bid_id": bid_id,
		"overall_state": ready.get("overall_state"),
		"ready_to_submit": ready.get("ready_to_submit"),
	}
