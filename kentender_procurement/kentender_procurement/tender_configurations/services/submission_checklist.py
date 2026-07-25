# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A2 — Submission Checklist (Bidder Workspace Home) DTO."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime

from kentender_procurement.tender_configurations.services.available_tenders import (
	format_time_remaining,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	start_or_get_bid_workspace,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	persist_compiled_schema,
)

# Pack-10 / schema_compiler.SECTION_KEYS are NOT checklist authority (lean slice).
# Bidder checklist reads IT Tender Publication Record.electronic_template_snapshot only.

# Lazy import avoided for circular deps — documents URL helper lives beside this module.
def _portal_documents_url(publication_ref: str) -> str:
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		portal_documents_url,
	)

	return portal_documents_url(publication_ref)


def _is_document_acknowledgement_section(sec: dict[str, Any]) -> bool:
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		is_document_acknowledgement_section,
	)

	return is_document_acknowledgement_section(sec)

STATUS_NOT_STARTED = "Not Started"
STATUS_IN_PROGRESS = "In Progress"
STATUS_NEEDS_ATTENTION = "Needs Attention"
STATUS_COMPLETE = "Complete"
STATUS_NOT_APPLICABLE = "Not Applicable"
STATUS_LOCKED = "Locked"

ACTION_START_FIRST = "Start First Section"
ACTION_CONTINUE = "Continue Bid"
ACTION_FIX_ISSUES = "Fix Issues"
ACTION_REVIEW_VALIDATE = "Review & Validate"
ACTION_SUBMIT_SEAL = "Submit & Seal Bid"
ACTION_VIEW_RECEIPT = "View Receipt"

FINAL_SECTION_KEYS = frozenset(
	{
		"final_declaration_and_submit",
		"final_declaration",
		"sealed_submission",
	}
)

# Display-only overrides (schema key retained). Avoids implying a contract exists pre-award.
SECTION_TITLE_OVERRIDES = {
	"contract_terms_acknowledgement": "Contract Conditions Acknowledgement",
}


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open your bid workspace."), frappe.PermissionError)


def _section_required(sec: dict[str, Any]) -> bool:
	if "required" in sec:
		return bool(sec.get("required"))
	if "blocks_submission" in sec:
		return bool(sec.get("blocks_submission"))
	return True


def _section_key(sec: dict[str, Any]) -> str:
	return cstr(sec.get("key") or sec.get("section_key") or sec.get("id") or "").strip()


def _section_title(sec: dict[str, Any], key: str) -> str:
	if key in SECTION_TITLE_OVERRIDES:
		return SECTION_TITLE_OVERRIDES[key]
	raw = cstr(sec.get("title") or sec.get("label") or key).strip() or key
	if raw == "Contract Terms Acknowledgement":
		return "Contract Conditions Acknowledgement"
	return raw


def _section_has_validation_blockers(payload: Any) -> bool:
	"""True only for real validation failures — not merely unstarted required sections."""
	if not isinstance(payload, dict) or not payload:
		return False
	if payload.get("needs_attention") in (True, 1, "1") or payload.get("has_blockers") in (True, 1, "1"):
		return True
	errors = payload.get("validation_errors")
	if isinstance(errors, list) and len(errors) > 0:
		return True
	if isinstance(errors, dict) and errors:
		return True
	blockers = payload.get("blockers")
	if isinstance(blockers, list) and len(blockers) > 0:
		return True
	if isinstance(blockers, dict) and blockers:
		return True
	return False


def _section_is_partial(payload: Any) -> bool:
	if not isinstance(payload, dict):
		return False
	if payload.get("in_progress") in (True, 1, "1") or payload.get("partial") in (True, 1, "1"):
		return True
	return cstr(payload.get("status") or "").strip().lower() in ("in_progress", "partial", "draft")


def _has_payload(payload: Any) -> bool:
	if payload is None:
		return False
	if isinstance(payload, dict):
		meta = {
			"in_progress",
			"partial",
			"status",
			"validation_errors",
			"blockers",
			"needs_attention",
			"has_blockers",
		}
		for key, val in payload.items():
			if key in meta:
				continue
			if val not in (None, "", [], {}):
				return True
		# Opened/partial or failed validation still counts as started work.
		return _section_is_partial(payload) or _section_has_validation_blockers(payload)
	if isinstance(payload, list):
		return len(payload) > 0
	return bool(cstr(payload).strip())

def _is_final_submission_section(sec: dict[str, Any]) -> bool:
	key = _section_key(sec)
	if key in FINAL_SECTION_KEYS:
		return True
	title = cstr(sec.get("title") or sec.get("label") or "").strip().lower()
	return "final declaration" in title or title.endswith("and submission")


def _has_matrix_requirements(sec: dict[str, Any], schema: dict[str, Any]) -> bool:
	"""True when section (or snapshot collections) expose requirement rows for matrix roll-up."""
	if isinstance(sec.get("requirements"), list) and sec.get("requirements"):
		return True
	collections = schema.get("collections") or {}
	if isinstance(collections, dict) and collections.get("requirements"):
		return cstr(sec.get("section_key") or "") == "requirements_compliance"
	return False


def resolve_section_status(
	*,
	required: bool,
	has_responses: bool,
	not_applicable: bool = False,
	has_validation_blockers: bool = False,
	is_partial: bool = False,
	is_locked: bool = False,
	bid_sealed: bool = False,
) -> str:
	"""Map section row state to A2 Title Case labels. Needs Attention only for validation failures."""
	if is_locked and not bid_sealed:
		return STATUS_LOCKED
	if bid_sealed and has_responses:
		return STATUS_COMPLETE
	from kentender_procurement.tender_configurations.services.section_status import (
		derive_generic_section_status,
		to_display_status,
	)

	result = derive_generic_section_status(
		required=required,
		has_responses=has_responses,
		not_applicable=not_applicable,
		has_validation_blockers=has_validation_blockers,
		is_partial=is_partial,
	)
	return to_display_status(result["section_status"])


def resolve_checklist_primary_action(
	*,
	bid_sealed: bool,
	any_started: bool,
	has_blockers: bool,
	all_required_complete: bool,
	validation_ok: bool = False,
) -> tuple[str, bool]:
	"""Return (primary_action_label, enabled)."""
	if bid_sealed:
		return ACTION_VIEW_RECEIPT, True
	if has_blockers:
		return ACTION_FIX_ISSUES, True
	if not any_started:
		return ACTION_START_FIRST, True
	if not all_required_complete:
		return ACTION_CONTINUE, True
	if validation_ok:
		return ACTION_SUBMIT_SEAL, True
	return ACTION_REVIEW_VALIDATE, True


def _desk_section_bridge(configuration_id: str) -> str:
	return f"/app/it-electronic-bidder-workspace/{quote(configuration_id, safe='')}"


def portal_workspace_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/workspace"


def _load_published_electronic_schema(configuration_id: str, publication_ref: str = "") -> dict[str, Any]:
	"""Authoritative checklist schema: published electronic template snapshot."""
	filters: dict[str, Any] = {"configuration": configuration_id, "status": "Published"}
	name = None
	if publication_ref:
		name = frappe.db.get_value(
			"IT Tender Publication Record",
			{"publication_ref": cstr(publication_ref), "status": "Published"},
			"name",
		)
	if not name:
		name = frappe.db.get_value(
			"IT Tender Publication Record",
			filters,
			"name",
			order_by="published_at desc",
		)
	if not name:
		frappe.throw(
			frappe._("Published tender record not found for electronic checklist."),
			title="KT_ELECTRONIC_TEMPLATE_PUBLICATION",
		)
	raw = frappe.db.get_value(
		"IT Tender Publication Record", name, "electronic_template_snapshot"
	)
	schema = _parse_json(raw, {})
	if not schema.get("sections"):
		# One-time backfill for tenders published before the lean electronic template seal.
		try:
			from kentender_procurement.tender_configurations.services.electronic_std_template import (
				seal_electronic_template_for_development_preview,
			)

			# Backfill may run while the curated template is still Draft (F0).
			seal_electronic_template_for_development_preview(name)
			schema = _parse_json(
				frappe.db.get_value("IT Tender Publication Record", name, "electronic_template_snapshot"),
				{},
			)
		except Exception:
			frappe.throw(
				frappe._(
					"Published tender is missing electronic_template_snapshot. "
					"Legacy pack-10 SECTION_KEYS are not used for the bidder checklist."
				),
				title="KT_ELECTRONIC_TEMPLATE_SNAPSHOT_MISSING",
			)
	if not schema.get("sections"):
		frappe.throw(
			frappe._(
				"Published tender is missing electronic_template_snapshot. "
				"Legacy pack-10 SECTION_KEYS are not used for the bidder checklist."
			),
			title="KT_ELECTRONIC_TEMPLATE_SNAPSHOT_MISSING",
		)
	digest = frappe.db.get_value(
		"IT Tender Publication Record", name, "electronic_template_hash"
	)
	schema = dict(schema)
	schema["schema_hash"] = cstr(digest or "")
	return schema


def _load_schema(cfg, bid_doc, publication_ref: str = "") -> dict[str, Any]:
	"""Load checklist sections from published electronic template only (fail closed)."""
	return _load_published_electronic_schema(cfg.name, publication_ref=publication_ref)


def get_submission_checklist(published_tender_ref: str) -> dict[str, Any]:
	"""Screen B DTO keyed by publication_ref (auth required)."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.bidder_presentation import (
		published_tender_pdf_url,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(published_tender_ref)
	backend = resolve_published_tender_backend(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)

	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	workspace_path = portal_workspace_url(pub_ref)

	bid_sealed = False
	bid_id = backend.get("bid_id")
	receipt_code = overview.get("receipt_code")

	cfg = frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, None, publication_ref=pub_ref)

	if action == ACTION_VIEW_SUBMITTED or overview.get("bid_status") == STATUS_SEALED:
		bid_sealed = True
		started = start_or_get_bid_workspace(pub_ref)  # view_only path
		bid_id = started.get("bid_id") or bid_id
		receipt_code = started.get("receipt_code") or receipt_code
	else:
		draft = create_or_get_draft(
			cfg_id,
			schema_snapshot=schema,
			schema_hash=cstr(schema.get("schema_hash") or ""),
		)
		bid_id = draft.get("bid_id")
		receipt_code = draft.get("receipt_code")

	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	if bid_doc and cstr(bid_doc.status) == STATUS_SEALED:
		bid_sealed = True

	# Ensure draft schema matches published electronic template (not pack-10).
	if bid_doc and not bid_sealed:
		snap = _parse_json(getattr(bid_doc, "schema_snapshot", None), {})
		if not snap.get("sections") or cstr(snap.get("schema_hash") or "") != cstr(
			schema.get("schema_hash") or ""
		):
			bid_doc.schema_snapshot = json.dumps(schema)
			bid_doc.schema_hash = cstr(schema.get("schema_hash") or "")
			bid_doc.save(ignore_permissions=True)
			frappe.db.commit()
	responses = _parse_json(getattr(bid_doc, "responses", None), {}) if bid_doc else {}
	modified = getattr(bid_doc, "modified", None)

	raw_sections = [s for s in (schema.get("sections") or []) if isinstance(s, dict) and _section_key(s)]
	any_started = any(_has_payload(responses.get(_section_key(s))) for s in raw_sections)

	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		is_requirement_matrix_section,
		matrix_section_roll_up,
		portal_section_url,
	)

	# Lean slice: Review/Submit are workflow steps (not checklist sections) and remain locked.
	review_submit_locked = True

	sections_out: list[dict[str, Any]] = []
	for idx, sec in enumerate(raw_sections):
		key = _section_key(sec)
		title = _section_title(sec, key)
		required = _section_required(sec)
		not_applicable = bool(sec.get("not_applicable") or sec.get("applicable") is False)
		payload = responses.get(key)
		is_matrix = is_requirement_matrix_section(sec) or key == "requirements_compliance"
		is_fot = key == "form_of_tender"
		is_cbq = key == "confidential_business_questionnaire"
		is_docs = key == "tender_documents_and_addenda" or _is_document_acknowledgement_section(sec)
		has_responses = _has_payload(payload)
		has_validation_blockers = _section_has_validation_blockers(payload)
		is_partial = bool(has_responses and _section_is_partial(payload) and not has_validation_blockers)
		is_final = _is_final_submission_section(sec)
		is_locked = bool(is_final and review_submit_locked and not bid_sealed)

		mx_blockers = 0
		if is_docs and not not_applicable and not bid_sealed:
			from kentender_procurement.tender_configurations.services.section_status import (
				to_display_status as _status_display,
			)
			from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
				build_package_ack_context,
				derive_docs_section_status,
				resolve_addenda_for_publication,
			)

			# Reuse overview package + publication for binding context.
			pkg = {}
			pub_id = ""
			try:
				from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
					package_summary_dto,
				)

				pub_id = cstr(
					frappe.db.get_value(
						"IT Tender Publication Record",
						{"publication_ref": pub_ref, "status": "Published"},
						"name",
					)
					or ""
				)
				pkg_name = (
					frappe.db.get_value(
						"IT Tender Publication Record", pub_id, "confirmed_package"
					)
					if pub_id
					else None
				)
				pkg = package_summary_dto(pkg_name) if pkg_name else {}
			except Exception:
				pkg = {}
			addenda = resolve_addenda_for_publication(pub_id, pkg, {})
			ctx = build_package_ack_context(
				publication_ref=pub_ref,
				publication_id=pub_id,
				package=pkg,
				published_at="",
				addenda=addenda,
			)
			docs_result = derive_docs_section_status(
				sec, payload if isinstance(payload, dict) else {}, ctx, addenda=addenda
			)
			status = _status_display(docs_result["section_status"])
			has_validation_blockers = status == STATUS_NEEDS_ATTENTION
			has_responses = status != STATUS_NOT_STARTED
			is_partial = status == STATUS_IN_PROGRESS
			mx_blockers = int(docs_result.get("issue_count") or 0)
		elif is_fot and not not_applicable and not bid_sealed:
			from kentender_procurement.tender_configurations.services.form_of_tender import (
				derive_fot_section_status,
			)

			status = derive_fot_section_status(sec, payload if isinstance(payload, dict) else {})
			has_validation_blockers = status == STATUS_NEEDS_ATTENTION
			has_responses = status != STATUS_NOT_STARTED
			is_partial = status == STATUS_IN_PROGRESS
		elif is_cbq and not not_applicable and not bid_sealed:
			from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
				derive_cbq_section_status,
			)

			status = derive_cbq_section_status(payload if isinstance(payload, dict) else {}, sec)
			has_validation_blockers = status == STATUS_NEEDS_ATTENTION
			has_responses = status != STATUS_NOT_STARTED
			is_partial = status == STATUS_IN_PROGRESS
		elif is_matrix and not not_applicable and not bid_sealed and _has_matrix_requirements(sec, schema):
			status, mx_blockers = matrix_section_roll_up(sec, payload)
			has_validation_blockers = bool(mx_blockers) or has_validation_blockers
		else:
			status = resolve_section_status(
				required=required,
				has_responses=has_responses,
				not_applicable=not_applicable,
				has_validation_blockers=has_validation_blockers,
				is_partial=is_partial,
				is_locked=is_locked,
				bid_sealed=bid_sealed,
			)

		if status == STATUS_NEEDS_ATTENTION:
			issues_count = max(1, int(mx_blockers or 1))
			if is_fot and isinstance(payload, dict):
				errs = payload.get("validation_errors") or []
				if isinstance(errs, list) and errs:
					issues_count = len(errs)
			action_label, issues_label = "Resolve", f"{issues_count} Blocker" + (
				"s" if issues_count != 1 else ""
			)
		elif status == STATUS_LOCKED:
			action_label, issues_label, issues_count = "View", "Complete required sections first", 0
		elif status == STATUS_COMPLETE:
			action_label = "Review" if (is_matrix or is_fot or is_docs or is_cbq) else "View"
			issues_label, issues_count = "—", 0
		elif status == STATUS_IN_PROGRESS:
			action_label = "Continue" if (is_matrix or is_fot or is_docs or is_cbq) else "Resume"
			issues_label, issues_count = "—", 0
		elif status == STATUS_NOT_STARTED:
			action_label, issues_label, issues_count = "Start", "—", 0
		else:
			action_label, issues_label, issues_count = "View", "—", 0

		last_updated = "—"
		if has_responses and modified:
			try:
				last_updated = format_datetime(modified)
			except Exception:
				last_updated = cstr(modified)

		display_title = title if (title[:1].isdigit() and "." in title[:4]) else f"{idx + 1}. {title}"
		if is_fot:
			from kentender_procurement.tender_configurations.services.form_of_tender import (
				portal_fot_url,
			)

			action_url = portal_fot_url(pub_ref)
		elif is_cbq:
			from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
				portal_cbq_url,
			)

			action_url = portal_cbq_url(pub_ref)
		elif key == "tender_documents_and_addenda" or _is_document_acknowledgement_section(sec):
			action_url = _portal_documents_url(pub_ref)
		elif is_matrix:
			action_url = portal_section_url(pub_ref, key)
		else:
			# Other lean sections: correct Website route (placeholder until implemented).
			action_url = portal_section_url(pub_ref, key)
		action_enabled = 0 if status in (STATUS_NOT_APPLICABLE, STATUS_LOCKED) else 1
		sections_out.append(
			{
				"section_key": key,
				"title": display_title,
				"required": 1 if required else 0,
				"required_label": "Mandatory" if required else "Optional",
				"status": status,
				"issues_count": issues_count,
				"issues_label": issues_label,
				"last_updated": last_updated,
				"action_label": action_label,
				"action_url": action_url if action_enabled else "#",
				"action_enabled": action_enabled,
				"is_final_section": 1 if is_final else 0,
			}
		)

	blocker_titles = [
		cstr(s.get("title") or "").lstrip("0123456789. ").strip() or s["title"]
		for s in sections_out
		if s["status"] == STATUS_NEEDS_ATTENTION
	]
	has_blockers = bool(blocker_titles)
	required_total = sum(
		1
		for s in sections_out
		if s.get("required") and s["status"] not in (STATUS_NOT_APPLICABLE,)
	)
	required_complete = sum(1 for s in sections_out if s.get("required") and s["status"] == STATUS_COMPLETE)
	# Locked final section does not count as complete for progress.
	all_required_complete = (
		required_total > 0
		and required_complete >= required_total
		and not has_blockers
		and not any(s["status"] == STATUS_LOCKED for s in sections_out if s.get("required"))
	)
	if required_total == 0 and sections_out and not has_blockers:
		all_required_complete = all(
			s["status"] in (STATUS_COMPLETE, STATUS_NOT_APPLICABLE) for s in sections_out
		)

	primary, primary_enabled = resolve_checklist_primary_action(
		bid_sealed=bid_sealed,
		any_started=any_started,
		has_blockers=has_blockers,
		all_required_complete=all_required_complete,
		validation_ok=False,
	)
	# Lean slice: Review & Submit remain locked until later implementation.
	if primary in (ACTION_REVIEW_VALIDATE, ACTION_SUBMIT_SEAL):
		primary = ACTION_CONTINUE
		primary_enabled = True
	primary_url = workspace_path
	for s in sections_out:
		if not s.get("action_enabled"):
			continue
		if s["status"] in (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_NEEDS_ATTENTION):
			primary_url = s.get("action_url") or workspace_path
			break
	else:
		if sections_out:
			primary_url = sections_out[0].get("action_url") or workspace_path

	pct = 0
	if required_total:
		pct = int(round(100.0 * float(required_complete) / float(required_total)))
	elif sections_out:
		done = sum(1 for s in sections_out if s["status"] == STATUS_COMPLETE)
		pct = int(round(100.0 * float(done) / float(len(sections_out))))

	issues_summary = ""
	if blocker_titles:
		issues_summary = (
			f"{len(blocker_titles)} Blocker"
			+ ("s" if len(blocker_titles) != 1 else "")
			+ ": "
			+ ", ".join(blocker_titles[:3])
			+ ("…" if len(blocker_titles) > 3 else "")
			+ " require attention before submission can proceed."
		)

	deadline_raw = (overview.get("dates") or {}).get("submission_deadline") or ""
	try:
		deadline_display = format_datetime(deadline_raw) if deadline_raw else "—"
	except Exception:
		deadline_display = cstr(deadline_raw) or "—"

	return {
		"published_tender_ref": pub_ref,
		"bid_status": cstr(bid_doc.status) if bid_doc else None,
		"receipt_code": receipt_code,
		"workspace_url": workspace_path,
		"documents_url": _portal_documents_url(pub_ref),
		"tender_title": overview.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"procurement_method": next(
			(r.get("value") for r in (overview.get("tender_info") or []) if r.get("key") == "procurement_method"),
			"",
		),
		"submission_deadline": deadline_raw,
		"submission_deadline_display": deadline_display,
		"time_remaining_label": format_time_remaining(deadline_raw),
		"progress_percent": pct,
		"progress_complete": required_complete,
		"progress_total": required_total or len(sections_out),
		"sections": sections_out,
		"current_issues_summary": issues_summary,
		"has_blockers": 1 if has_blockers else 0,
		"primary_action": primary,
		"primary_action_enabled": 1 if primary_enabled else 0,
		"primary_action_url": primary_url,
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"pdf_url": published_tender_pdf_url(pub_ref),
		"workspace_status": "Submitted" if bid_sealed else ("Draft" if any_started else "Not Started"),
	}
