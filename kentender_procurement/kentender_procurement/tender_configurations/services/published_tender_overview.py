# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder A1 — Published Tender Overview DTO + start/get bid workspace."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.configuration_home import (
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_DRAFT,
	STATUS_SEALED,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PUBLICATION_DOCTYPE,
	PUBLICATION_STATUS_PUBLISHED,
	package_summary_dto,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	_activate_flag,
	_visibility,
	ensure_publication_ref,
)

ACTION_START = "Start Bid"
ACTION_CONTINUE = "Continue Bid"
ACTION_VIEW_SUBMITTED = "View Submitted Bid"
ACTION_CLOSED = "Closed"
ACTION_UNAVAILABLE = "Unavailable"

WORKSPACE_NOT_STARTED = "Not Started"
WORKSPACE_DRAFT = "Draft"
WORKSPACE_SUBMITTED = "Submitted"
WORKSPACE_CLOSED = "Closed"
WORKSPACE_UNAVAILABLE = "Unavailable"


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _as_dt(value: Any):
	if not value:
		return None
	try:
		return get_datetime(value)
	except Exception:
		return None


def _resolve_publication(published_tender_ref: str):
	ref = cstr(published_tender_ref or "").strip()
	if not ref:
		frappe.throw(frappe._("Published tender reference is required."), title="PUB_REF_REQUIRED")
	name = frappe.db.get_value(PUBLICATION_DOCTYPE, {"publication_ref": ref}, "name")
	if not name and frappe.db.exists(PUBLICATION_DOCTYPE, ref):
		name = ref
	if not name:
		frappe.throw(frappe._("Published tender not found."), title="PUBLISHED_TENDER_NOT_FOUND")
	return frappe.get_doc(PUBLICATION_DOCTYPE, name)


def _schema_sections(cfg) -> list[dict[str, Any]]:
	schema = _parse_json(getattr(cfg, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		pkg_name = cstr(getattr(cfg, "confirmed_document_package", None) or "")
		if pkg_name and frappe.db.exists("Confirmed Tender Document Package", pkg_name):
			pkg = frappe.get_doc("Confirmed Tender Document Package", pkg_name)
			schema = _parse_json(getattr(pkg, "bidder_submission_schema", None), {})
	out: list[dict[str, Any]] = []
	for sec in schema.get("sections") or []:
		if not isinstance(sec, dict):
			continue
		key = cstr(sec.get("section_key") or sec.get("key") or sec.get("id") or "").strip()
		title = cstr(sec.get("title") or sec.get("label") or key).strip()
		if not title:
			continue
		required = sec.get("required")
		if required is None:
			required = bool(sec.get("blocks_submission", True))
		out.append(
			{
				"section_key": key or title,
				"title": title,
				"required": bool(required),
				"required_label": "Required" if required else "Optional",
			}
		)
	return out


def _documents_from_package(pkg_summary: dict[str, Any], configuration_id: str) -> list[dict[str, Any]]:
	docs: list[dict[str, Any]] = []
	has_pdf = bool(pkg_summary.get("has_pdf"))
	if has_pdf:
		docs.append(
			{
				"document_key": "tender_pdf",
				"name": "Official Tender Document",
				"type": "PDF",
				"size": "",
				"icon": "picture_as_pdf",
				"can_view": True,
				"can_download": True,
				"configuration_id": configuration_id,
			}
		)
	# Package checklist items become document rows (package-driven, not mock DOCX/XLSX).
	for idx, item in enumerate(pkg_summary.get("items") or []):
		label = cstr(item).strip()
		if not label:
			continue
		if has_pdf and label.lower().startswith("generated tender pdf"):
			continue
		docs.append(
			{
				"document_key": f"pkg_item_{idx}",
				"name": label,
				"type": "Package Artifact",
				"size": "",
				"icon": "description",
				"can_view": False,
				"can_download": False,
				"configuration_id": configuration_id,
			}
		)
	return docs


def _tender_info_fields(cfg, context: dict[str, Any]) -> list[dict[str, Any]]:
	"""Schema/config-driven info rows — omit blanks; never hardcode Goods mock values."""
	tds = _parse_json(getattr(cfg, "tds_values", None), {})
	eval_setup = _parse_json(getattr(cfg, "evaluation_setup", None), {})
	candidates: list[tuple[str, str, str]] = [
		("procurement_method", "Procurement Method", cstr(context.get("procurement_method_label") or "")),
		("std_family", "STD Family", cstr(context.get("std_family_label") or cfg.std_family_label or "")),
		(
			"standard_tender_document",
			"Standard Tender Document",
			cstr(context.get("standard_tender_document_label") or getattr(cfg, "std_document_label", None) or ""),
		),
		("std_version", "STD Version", cstr(cfg.std_version or "")),
		("category", "Category", cstr(getattr(cfg, "procurement_category", None) or getattr(cfg, "category", None) or "")),
	]
	sec_req = cstr(tds.get("tender_security_required") or "").strip()
	sec_amt = cstr(tds.get("tender_security_amount") or "").strip()
	sec_cur = cstr(tds.get("tender_security_currency") or "").strip()
	if sec_req.lower() in ("yes", "1", "true") and sec_amt:
		bid_security = f"{sec_cur + ' ' if sec_cur else ''}{sec_amt}".strip()
	elif sec_req:
		bid_security = sec_req
	else:
		bid_security = ""
	candidates.append(("bid_security", "Bid Security", bid_security))

	eval_method = cstr(
		eval_setup.get("evaluation_method")
		or eval_setup.get("evaluation_method_label")
		or eval_setup.get("method")
		or ""
	).strip()
	candidates.append(("evaluation_method", "Evaluation Method", eval_method))

	out: list[dict[str, Any]] = []
	for key, label, value in candidates:
		value = cstr(value).strip()
		if not value:
			continue
		out.append({"key": key, "label": label, "value": value})
	return out


def _bid_state(configuration_id: str) -> dict[str, Any]:
	draft_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_DRAFT},
		"name",
	)
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_SEALED},
		"name",
		order_by="sealed_at desc",
	)
	bid = None
	if sealed_name:
		bid = frappe.get_doc("Electronic Bid Submission", sealed_name)
	elif draft_name:
		bid = frappe.get_doc("Electronic Bid Submission", draft_name)
	if not bid:
		return {
			"bid_id": None,
			"bid_status": None,
			"workspace_status": WORKSPACE_NOT_STARTED,
			"receipt_code": None,
			"has_draft": False,
			"has_sealed": False,
		}
	sealed = cstr(bid.status) == STATUS_SEALED
	return {
		"bid_id": bid.name,
		"bid_status": cstr(bid.status),
		"workspace_status": WORKSPACE_SUBMITTED if sealed else WORKSPACE_DRAFT,
		"receipt_code": cstr(bid.receipt_code or "") or None,
		"has_draft": not sealed,
		"has_sealed": sealed,
	}


def resolve_primary_action(
	*,
	published: bool,
	workspace_activated: bool,
	past_deadline: bool,
	has_sealed: bool,
	has_draft: bool,
) -> tuple[str, bool, str]:
	"""Return (primary_action, enabled, workspace_status_override_or_empty)."""
	if not published or not workspace_activated:
		return ACTION_UNAVAILABLE, False, WORKSPACE_UNAVAILABLE
	if past_deadline and not has_sealed:
		return ACTION_CLOSED, False, WORKSPACE_CLOSED
	if has_sealed:
		return ACTION_VIEW_SUBMITTED, True, ""
	if has_draft:
		return ACTION_CONTINUE, True, ""
	return ACTION_START, True, ""


def get_published_tender_overview(published_tender_ref: str) -> dict[str, Any]:
	"""GET-equivalent overview DTO for Screen A (bidder published tender overview)."""
	pub = _resolve_publication(published_tender_ref)
	pub_ref = ensure_publication_ref(pub)
	status = cstr(pub.status or "")
	published = status == PUBLICATION_STATUS_PUBLISHED
	activated = bool(_activate_flag(pub))
	visibility = _visibility(pub)

	cfg_id = cstr(pub.configuration or "").strip()
	if not cfg_id or not frappe.db.exists("Tender Configuration", cfg_id):
		frappe.throw(frappe._("Linked tender configuration not found."), title="TCFG_NOT_FOUND")
	cfg = frappe.get_doc("Tender Configuration", cfg_id)
	context = build_configuration_context(cfg)
	pkg = package_summary_dto(cstr(pub.confirmed_package or "") or None)

	submission_deadline = _as_dt(getattr(pub, "submission_deadline", None))
	clarification_deadline = _as_dt(getattr(pub, "clarification_deadline", None))
	now = now_datetime()
	past_deadline = bool(submission_deadline and now > submission_deadline)
	clarification_closed = bool(clarification_deadline and now > clarification_deadline)

	bid = _bid_state(cfg_id)
	action, enabled, status_override = resolve_primary_action(
		published=published,
		workspace_activated=activated,
		past_deadline=past_deadline,
		has_sealed=bool(bid["has_sealed"]),
		has_draft=bool(bid["has_draft"]),
	)
	workspace_status = status_override or bid["workspace_status"]

	status_chip = "Closed" if past_deadline else ("Open" if published and activated else "Unavailable")

	return {
		"published_tender_ref": pub_ref,
		"publication_id": pub.name,
		"publication_status": status,
		"configuration_id": cfg.name,
		"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
		"tender_title": cstr(context.get("procurement_title") or cfg.tender_title or ""),
		"procuring_entity": cstr(context.get("procuring_entity_name") or ""),
		"scope_summary": cstr(getattr(cfg, "short_scope_summary", None) or pub.tender_notice or ""),
		"status_chip": status_chip,
		"bidder_visibility": visibility,
		"activate_bidder_workspace": 1 if activated else 0,
		"dates": {
			"published_at": cstr(pub.published_at or pub.publication_datetime or ""),
			"clarification_deadline": cstr(pub.clarification_deadline or ""),
			"submission_deadline": cstr(pub.submission_deadline or ""),
			"opening_datetime": cstr(pub.opening_datetime or ""),
		},
		"past_submission_deadline": 1 if past_deadline else 0,
		"clarification_deadline_passed": 1 if clarification_closed else 0,
		"ask_question_enabled": 0 if clarification_closed else 1,
		"documents": _documents_from_package(pkg, cfg.name),
		"confirmed_package": pkg,
		"submission_sections": _schema_sections(cfg),
		"tender_info": _tender_info_fields(cfg, context),
		"clarifications": [],
		"workspace_status": workspace_status,
		"primary_action": action,
		"primary_action_enabled": 1 if enabled else 0,
		"bid_id": bid["bid_id"],
		"bid_status": bid["bid_status"],
		"receipt_code": bid["receipt_code"],
		"bidder_workspace_route": f"/tenders/{cstr(pub_ref).strip()}/workspace",
		"desk_section_bridge_url": f"it-electronic-bidder-workspace/{cfg.name}",
	}


def start_or_get_bid_workspace(
	published_tender_ref: str,
	bidder_label: str | None = None,
) -> dict[str, Any]:
	"""POST-equivalent: create or return draft workspace; refuse Closed/Unavailable."""
	overview = get_published_tender_overview(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)
	if action == ACTION_VIEW_SUBMITTED:
		return {
			"created": False,
			"view_only": True,
			"bid_id": overview.get("bid_id"),
			"receipt_code": overview.get("receipt_code"),
			"configuration_id": overview.get("configuration_id"),
			"primary_action": action,
			"bidder_workspace_route": overview.get("bidder_workspace_route"),
			"overview": overview,
		}
	draft = create_or_get_draft(overview["configuration_id"], bidder_label=bidder_label)
	refreshed = get_published_tender_overview(published_tender_ref)
	return {
		"created": overview.get("primary_action") == ACTION_START,
		"view_only": False,
		"bid_id": draft.get("bid_id"),
		"receipt_code": draft.get("receipt_code"),
		"configuration_id": overview.get("configuration_id"),
		"primary_action": refreshed.get("primary_action"),
		"bidder_workspace_route": overview.get("bidder_workspace_route"),
		"draft": draft,
		"overview": refreshed,
	}
