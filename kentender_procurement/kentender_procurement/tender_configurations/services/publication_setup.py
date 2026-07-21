# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Publications queue + Publication Setup + Publish Tender (v7 A2/A3)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_AWAITING_PUBLICATION_SETUP,
	STATUS_PUBLISHED,
	STATUS_RETURNED_FOR_CORRECTION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	build_configuration_context,
)
from kentender_procurement.tender_configurations.doctype.it_tender_publication_record.it_tender_publication_record import (
	allocate_publication_ref,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PUBLICATION_DOCTYPE,
	PUBLICATION_STATUS_AWAITING,
	PUBLICATION_STATUS_PUBLISHED,
	PUBLICATION_STATUS_READY,
	PUBLICATION_STATUS_RETURNED,
	PUBLICATION_STATUS_SCHEDULED,
	cancel_publication_for_configuration,
	get_active_package_name,
	invalidate_package,
	package_summary_dto,
)

TAB_AWAITING = "awaiting_setup"
TAB_READY = "ready_to_publish"
TAB_SCHEDULED = "scheduled"
TAB_PUBLISHED = "published"
TAB_RETURNED = "returned"

TAB_TO_STATUS = {
	TAB_AWAITING: PUBLICATION_STATUS_AWAITING,
	TAB_READY: PUBLICATION_STATUS_READY,
	TAB_SCHEDULED: PUBLICATION_STATUS_SCHEDULED,
	TAB_PUBLISHED: PUBLICATION_STATUS_PUBLISHED,
	TAB_RETURNED: PUBLICATION_STATUS_RETURNED,
}

NEXT_ACTION = {
	PUBLICATION_STATUS_AWAITING: "Complete Setup",
	PUBLICATION_STATUS_READY: "Publish Tender",
	PUBLICATION_STATUS_SCHEDULED: "Manage Schedule",
	PUBLICATION_STATUS_PUBLISHED: "View Published Tender",
	PUBLICATION_STATUS_RETURNED: "Review Comments",
}


def _parse_blob(raw: Any) -> dict[str, Any]:
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


def _as_dt(value: Any):
	if not value:
		return None
	try:
		return get_datetime(value)
	except Exception:
		return None


def _visibility(pub) -> str:
	return cstr(getattr(pub, "bidder_visibility", None) or getattr(pub, "supplier_visibility", None) or "")


def _activate_flag(pub) -> int:
	return 1 if (
		getattr(pub, "activate_bidder_workspace", None)
		or getattr(pub, "bidder_workspace_activation", None)
	) else 0


def _next_action(status: str) -> str:
	return NEXT_ACTION.get(status, "Open")


def _normalize_publication_mode(
	raw: Any,
	*,
	publication_datetime: Any = None,
	status: str = "",
	allow_datetime_infer: bool = False,
) -> str:
	"""Return immediate|scheduled.

	Never treat a filled publication_datetime alone as scheduled after publish —
	immediate publish also stamps a datetime.
	"""
	mode = cstr(raw or "").strip().lower()
	if mode in ("immediate", "scheduled"):
		return mode
	if cstr(status) == PUBLICATION_STATUS_SCHEDULED:
		return "scheduled"
	if allow_datetime_infer:
		pub_dt = _as_dt(publication_datetime)
		if pub_dt and pub_dt > now_datetime():
			return "scheduled"
	return "immediate"


def _publication_mode(pub) -> str:
	return _normalize_publication_mode(
		getattr(pub, "publication_mode", None),
		publication_datetime=getattr(pub, "publication_datetime", None),
		status=cstr(getattr(pub, "status", None) or ""),
		allow_datetime_infer=False,
	)


def _looks_like_hash_id(value: str) -> bool:
	"""True for Frappe hash autonames (e.g. rubo2o74ff) — not business codes."""
	s = cstr(value or "").strip()
	if not s or len(s) < 8 or len(s) > 12:
		return False
	if "-" in s or "_" in s or " " in s:
		return False
	return s.isalnum() and any(c.isdigit() for c in s) and any(c.isalpha() for c in s)


def ensure_publication_ref(pub) -> str:
	"""Return durable business publication_ref; allocate + persist when missing."""
	ref = cstr(getattr(pub, "publication_ref", None) or "").strip()
	if ref and not _looks_like_hash_id(ref):
		return ref
	# Legacy rows used hash as display — replace with PUB-YYYY-#####.
	ref = allocate_publication_ref()
	name = cstr(getattr(pub, "name", None) or "")
	if name and frappe.db.exists(PUBLICATION_DOCTYPE, name):
		frappe.db.set_value(
			PUBLICATION_DOCTYPE,
			name,
			"publication_ref",
			ref,
			update_modified=False,
		)
		pub.publication_ref = ref
	else:
		pub.publication_ref = ref
	return ref


def _doc_package_display_ref(pub, cfg, pkg_dto: dict[str, Any] | None = None) -> str:
	pkg = pkg_dto if pkg_dto is not None else package_summary_dto(cstr(pub.confirmed_package or ""))
	for candidate in (
		pkg.get("package_code"),
		pkg.get("procurement_package_ref"),
		pkg.get("configuration_ref"),
		cstr(getattr(pub, "configuration_ref", None) or ""),
		cstr(getattr(cfg, "configuration_ref", None) or ""),
		cstr(getattr(cfg, "procurement_package_ref", None) or ""),
	):
		val = cstr(candidate or "").strip()
		if val and not _looks_like_hash_id(val):
			return val
	# Last resort: configuration name if it is a business code (e.g. TCFG-…).
	cfg_name = cstr(getattr(cfg, "name", None) or "")
	if cfg_name and not _looks_like_hash_id(cfg_name):
		return cfg_name
	return "—"


def list_publications(
	tab: str | None = None,
	search: str | None = None,
	page: int | None = None,
	page_size: int | None = None,
) -> dict[str, Any]:
	"""A2 Publications queue."""
	if frappe.session.user == "Guest":
		frappe.throw(frappe._("Login required"), frappe.PermissionError)

	tab_key = cstr(tab or TAB_AWAITING).strip() or TAB_AWAITING
	search_q = cstr(search or "").strip()
	page_n = max(1, int(page or 1))
	size = min(100, max(1, int(page_size or 20)))

	counts = {
		TAB_AWAITING: 0,
		TAB_READY: 0,
		TAB_SCHEDULED: 0,
		TAB_PUBLISHED: 0,
		TAB_RETURNED: 0,
	}
	for key, status in TAB_TO_STATUS.items():
		counts[key] = frappe.db.count(PUBLICATION_DOCTYPE, {"status": status})

	filters: dict[str, Any] = {}
	if tab_key in TAB_TO_STATUS:
		filters["status"] = TAB_TO_STATUS[tab_key]

	or_filters = None
	if search_q:
		or_filters = [
			["publication_ref", "like", f"%{search_q}%"],
			["configuration_ref", "like", f"%{search_q}%"],
			["name", "like", f"%{search_q}%"],
		]

	rows_raw = frappe.get_all(
		PUBLICATION_DOCTYPE,
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"configuration",
			"configuration_ref",
			"publication_ref",
			"status",
			"publication_datetime",
			"submission_deadline",
			"opening_datetime",
			"confirmed_package",
			"cancel_reason",
			"modified",
		],
		order_by="modified desc",
		start=(page_n - 1) * size,
		page_length=size,
	)
	total = frappe.db.count(PUBLICATION_DOCTYPE, filters) if filters else sum(counts.values())

	rows = []
	for row in rows_raw:
		cfg = frappe.db.get_value(
			"Tender Configuration",
			row.configuration,
			[
				"tender_title",
				"procuring_entity_name",
				"procuring_entity_code",
				"std_document_label",
				"std_version",
			],
			as_dict=True,
		) or {}
		status = cstr(row.status or "")
		issues = ""
		if status == PUBLICATION_STATUS_RETURNED:
			issues = cstr(row.cancel_reason or "Returned for correction")
		pub_ref = cstr(getattr(row, "publication_ref", None) or "").strip()
		if not pub_ref or _looks_like_hash_id(pub_ref):
			# Lightweight backfill for queue rows without loading full docs.
			pub_ref = allocate_publication_ref()
			frappe.db.set_value(
				PUBLICATION_DOCTYPE,
				row.name,
				"publication_ref",
				pub_ref,
				update_modified=False,
			)
		pkg_dto = package_summary_dto(cstr(row.confirmed_package or ""))
		doc_pkg = cstr(
			pkg_dto.get("package_code")
			or pkg_dto.get("procurement_package_ref")
			or pkg_dto.get("configuration_ref")
			or row.configuration_ref
			or ""
		).strip()
		if _looks_like_hash_id(doc_pkg):
			doc_pkg = cstr(row.configuration_ref or "").strip() or "—"
		rows.append(
			{
				"publication_id": row.name,
				"publication_ref": pub_ref,
				"doc_package_ref": doc_pkg,
				"configuration_id": row.configuration,
				"configuration_ref": cstr(row.configuration_ref or ""),
				"tender_title": cstr(cfg.get("tender_title") or ""),
				"procuring_entity": cstr(
					cfg.get("procuring_entity_name") or cfg.get("procuring_entity_code") or ""
				),
				"standard_tender_document": cstr(
					cfg.get("std_document_label") or cfg.get("std_version") or ""
				),
				"status": status,
				"publication_datetime": cstr(row.publication_datetime or ""),
				"submission_deadline": cstr(row.submission_deadline or ""),
				"opening_datetime": cstr(row.opening_datetime or ""),
				"issues": issues,
				"next_action": _next_action(status),
				"setup_route": f"publication-setup/{row.name}",
			}
		)

	return {
		"tab": tab_key,
		"search": search_q,
		"page": page_n,
		"page_size": size,
		"total": total,
		"summary": {
			"awaiting_setup_count": counts[TAB_AWAITING],
			"ready_to_publish_count": counts[TAB_READY],
			"scheduled_count": counts[TAB_SCHEDULED],
			"published_count": counts[TAB_PUBLISHED],
			"returned_count": counts[TAB_RETURNED],
		},
		"rows": rows,
	}


def get_publication_setup(publication_id: str) -> dict[str, Any]:
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_id):
		frappe.throw(frappe._("Publication record not found."), title="PUBLICATION_NOT_FOUND")
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, publication_id)
	if not frappe.has_permission(doc=pub, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	cfg = frappe.get_doc("Tender Configuration", pub.configuration)
	status = cstr(pub.status or "")
	locked = 1 if getattr(pub, "setup_locked", None) or status == PUBLICATION_STATUS_PUBLISHED else 0
	context = build_configuration_context(cfg)
	pkg_dto = package_summary_dto(cstr(pub.confirmed_package or ""))
	pub_ref = ensure_publication_ref(pub)
	doc_pkg_ref = _doc_package_display_ref(pub, cfg, pkg_dto)
	pub_dt = cstr(pub.publication_datetime or "")
	published_at = cstr(getattr(pub, "published_at", None) or "")
	# Immediate publish must still expose the effective stamp after publish.
	display_pub_dt = pub_dt or (published_at if status == PUBLICATION_STATUS_PUBLISHED else "")
	return {
		"publication_id": pub.name,
		"publication_ref": pub_ref,
		"configuration_id": cfg.name,
		"configuration_ref": cstr(pub.configuration_ref or cfg.configuration_ref or cfg.name),
		"tender_title": cstr(cfg.tender_title or ""),
		"procuring_entity": cstr(context.get("procuring_entity_name") or ""),
		"standard_tender_document": cstr(
			context.get("standard_tender_document_label") or cfg.std_version or ""
		),
		"context": context,
		"publication_context": {
			"publication_ref": pub_ref,
			"doc_package_ref": doc_pkg_ref,
			"procuring_entity_name": cstr(context.get("procuring_entity_name") or ""),
			"std_label": cstr(context.get("standard_tender_document_label") or cfg.std_version or ""),
			"status_label": status,
		},
		"status": status,
		"setup_locked": locked,
		"editable": 1 if not locked and status not in (PUBLICATION_STATUS_RETURNED, "Cancelled") else 0,
		"fields": {
			"publication_mode": _publication_mode(pub),
			"publication_datetime": display_pub_dt,
			"tender_notice": cstr(pub.tender_notice or ""),
			"clarification_deadline": cstr(pub.clarification_deadline or ""),
			"submission_deadline": cstr(pub.submission_deadline or ""),
			"opening_datetime": cstr(pub.opening_datetime or ""),
			"bidder_visibility": _visibility(pub),
			"activate_bidder_workspace": _activate_flag(pub),
			"acknowledgement_confirmed": 1 if getattr(pub, "acknowledgement_confirmed", None) else 0,
		},
		"confirmed_package": pkg_dto,
		"document_hash": cstr(pub.document_hash or ""),
		"can_publish": 1 if status in (PUBLICATION_STATUS_READY, PUBLICATION_STATUS_SCHEDULED) else 0,
		"can_return": 1 if status not in (PUBLICATION_STATUS_PUBLISHED, "Cancelled") else 0,
		"context_links": {
			"view_package_route": f"it-tender-package-review/{cfg.name}",
			"view_document_route": f"it-tender-configuration-render-preview/{cfg.name}",
			"download_pdf_method": (
				"kentender_procurement.tender_configurations."
				"download_tender_configuration_document_preview_pdf"
			),
			"publications_route": "publications",
		},
		"published_at": published_at,
		"published_by": cstr(getattr(pub, "published_by", None) or ""),
		"cancel_reason": cstr(pub.cancel_reason or ""),
	}


def _validate_setup_payload(payload: dict[str, Any], *, for_publish: bool = False) -> list[str]:
	errors: list[str] = []
	pub_dt = _as_dt(payload.get("publication_datetime"))
	sub_dt = _as_dt(payload.get("submission_deadline"))
	open_dt = _as_dt(payload.get("opening_datetime"))
	notice = cstr(payload.get("tender_notice") or "").strip()
	visibility = cstr(payload.get("bidder_visibility") or "").strip()
	activate = 1 if payload.get("activate_bidder_workspace") else 0

	if for_publish or payload.get("publication_datetime"):
		if not pub_dt:
			errors.append("Set the publication date and time before publishing.")
	if for_publish or notice or for_publish:
		if for_publish and not notice:
			errors.append("Add the tender notice before publishing.")
	if for_publish and not sub_dt:
		errors.append("Set the submission deadline before publishing.")
	if for_publish and not open_dt:
		errors.append("Set the opening date and time before publishing.")
	if for_publish and not visibility:
		errors.append("Select who can view this tender after publication.")
	if for_publish and not activate:
		errors.append("Activate the electronic bidder workspace before publishing.")

	if pub_dt and sub_dt and sub_dt <= pub_dt:
		errors.append("Submission deadline must be after the publication date.")
	if sub_dt and open_dt and open_dt < sub_dt:
		errors.append("Opening date and time must not be before the submission deadline.")
	return errors


def save_publication_setup(
	publication_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_id):
		frappe.throw(frappe._("Publication record not found."), title="PUBLICATION_NOT_FOUND")
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, publication_id)
	if not frappe.has_permission(doc=pub, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if cstr(pub.status) in (PUBLICATION_STATUS_PUBLISHED, PUBLICATION_STATUS_RETURNED, "Cancelled"):
		frappe.throw(frappe._("This publication cannot be edited."), title="PUBLICATION_LOCKED")
	if getattr(pub, "setup_locked", None):
		frappe.throw(frappe._("Publication setup is locked after publish."), title="PUBLICATION_LOCKED")

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}

	errors = _validate_setup_payload(payload, for_publish=False)
	# Soft validate date order even on draft save when both present.
	hard = [e for e in errors if "must" in e.lower()]
	if hard:
		frappe.throw(frappe._(hard[0]), title="PUBLICATION_VALIDATION")

	pub.flags.ignore_publication_boundary = True
	pub.publication_datetime = payload.get("publication_datetime") or None
	pub.clarification_deadline = payload.get("clarification_deadline") or None
	pub.submission_deadline = payload.get("submission_deadline") or None
	pub.opening_datetime = payload.get("opening_datetime") or None
	pub.tender_notice = cstr(payload.get("tender_notice") or "")
	visibility = cstr(payload.get("bidder_visibility") or "").strip()
	pub.bidder_visibility = visibility
	pub.supplier_visibility = visibility
	activate = 1 if payload.get("activate_bidder_workspace") else 0
	pub.activate_bidder_workspace = activate
	pub.bidder_workspace_activation = activate
	pub.acknowledgement_confirmed = 1 if payload.get("acknowledgement_confirmed") else 0
	mode = _normalize_publication_mode(
		payload.get("publication_mode"),
		publication_datetime=pub.publication_datetime,
		status="",
		allow_datetime_infer=True,
	)
	pub.publication_mode = mode

	# Transition when required setup fields are present.
	complete_errors = _validate_setup_payload(
		{
			"publication_datetime": pub.publication_datetime,
			"tender_notice": pub.tender_notice,
			"submission_deadline": pub.submission_deadline,
			"opening_datetime": pub.opening_datetime,
			"bidder_visibility": _visibility(pub),
			"activate_bidder_workspace": _activate_flag(pub),
		},
		for_publish=True,
	)
	if not complete_errors:
		pub_dt = _as_dt(pub.publication_datetime)
		if mode == "scheduled" and pub_dt and pub_dt > now_datetime():
			pub.status = PUBLICATION_STATUS_SCHEDULED
		else:
			pub.status = PUBLICATION_STATUS_READY
	else:
		pub.status = PUBLICATION_STATUS_AWAITING

	pub.save(ignore_permissions=False)
	frappe.db.commit()
	return get_publication_setup(pub.name)


def publish_tender(publication_id: str) -> dict[str, Any]:
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_id):
		frappe.throw(frappe._("Publication record not found."), title="PUBLICATION_NOT_FOUND")
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, publication_id)
	if not frappe.has_permission(doc=pub, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if cstr(pub.status) == PUBLICATION_STATUS_PUBLISHED:
		out = get_publication_setup(pub.name)
		out["published"] = True
		return out
	if cstr(pub.status) in (PUBLICATION_STATUS_RETURNED, "Cancelled"):
		frappe.throw(frappe._("Returned publications cannot be published."), title="PUBLICATION_STATE")

	payload = {
		"publication_datetime": pub.publication_datetime,
		"tender_notice": pub.tender_notice,
		"clarification_deadline": pub.clarification_deadline,
		"submission_deadline": pub.submission_deadline,
		"opening_datetime": pub.opening_datetime,
		"bidder_visibility": _visibility(pub),
		"activate_bidder_workspace": _activate_flag(pub),
	}
	errors = _validate_setup_payload(payload, for_publish=True)
	# Integrity checks against confirmed package.
	if not pub.confirmed_package or not frappe.db.exists(
		"Confirmed Tender Document Package", pub.confirmed_package
	):
		errors.append("Confirmed tender document is missing. Return the tender for correction.")
	else:
		pkg = frappe.get_doc("Confirmed Tender Document Package", pub.confirmed_package)
		if not pkg.bidder_submission_schema:
			errors.append("Bidder submission setup is missing. Return the tender for correction.")
		if not pkg.evaluation_schema:
			errors.append("Evaluation setup is missing. Return the tender for correction.")
		if not pkg.price_schedule_schema:
			errors.append("Price schedule is missing. Return the tender for correction.")
		if not pkg.forms_evidence_schema:
			errors.append("Forms and evidence setup is missing. Return the tender for correction.")
		if not pkg.document_hash:
			errors.append("Tender integrity check failed. Return the tender for correction.")

	if errors:
		frappe.throw(frappe._(errors[0]), title="PUBLICATION_VALIDATION")

	pub.flags.ignore_publication_boundary = True
	pub.flags.ignore_publication_lock = True
	pub.status = PUBLICATION_STATUS_PUBLISHED
	pub.setup_locked = 1
	pub.activate_bidder_workspace = 1
	pub.bidder_workspace_activation = 1
	pub.published_at = now_datetime()
	pub.published_by = frappe.session.user
	# Immediate publish: stamp the effective visibility datetime when missing.
	if not pub.publication_datetime:
		pub.publication_datetime = pub.published_at
	ensure_publication_ref(pub)
	pub.save(ignore_permissions=False)

	cfg = frappe.get_doc("Tender Configuration", pub.configuration)
	cfg.status = STATUS_PUBLISHED
	cfg.flags.ignore_mandatory = True
	cfg.flags.ignore_f1_publication_lock = True
	cfg.save(ignore_permissions=False)

	# Durable activation audit for Bid Submissions downstream.
	frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": PUBLICATION_DOCTYPE,
			"reference_name": pub.name,
			"content": (
				f"Publish Tender: bidder workspace activated; visibility={_visibility(pub)}; "
				f"submission_deadline={cstr(pub.submission_deadline or '')}"
			),
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	out = get_publication_setup(pub.name)
	out["published"] = True
	out["bidder_workspace_activated"] = True
	return out


def return_publication_for_correction(
	publication_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_id):
		frappe.throw(frappe._("Publication record not found."), title="PUBLICATION_NOT_FOUND")
	pub = frappe.get_doc(PUBLICATION_DOCTYPE, publication_id)
	if not frappe.has_permission(doc=pub, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if cstr(pub.status) == PUBLICATION_STATUS_PUBLISHED:
		frappe.throw(
			frappe._("Published tenders cannot be returned from Publication Setup."),
			title="PUBLICATION_STATE",
		)

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	reason = cstr(payload.get("reason") or "").strip()
	if not reason:
		frappe.throw(frappe._("Reason for return is required."), title="RETURN_REQUIRED")

	configuration_id = pub.configuration
	cancel_publication_for_configuration(configuration_id, reason=reason)
	pkg_name = cstr(pub.confirmed_package or "") or get_active_package_name(configuration_id)
	if pkg_name:
		invalidate_package(pkg_name, reason=reason)

	cfg = frappe.get_doc("Tender Configuration", configuration_id)
	preview = _parse_blob(getattr(cfg, "document_preview", None))
	preview["preview_status"] = "Not generated"
	preview["user_confirmed"] = 0
	preview["preview_html"] = ""
	preview.pop("confirmed_at", None)
	preview.pop("confirmed_by", None)
	preview.pop("document_hash", None)
	preview.pop("confirmed_package_id", None)
	preview["return"] = {
		"reason": reason,
		"at": str(now_datetime()),
		"by": frappe.session.user,
		"from": "publication",
	}
	cfg.document_preview = json.dumps(preview)
	cfg.status = STATUS_RETURNED_FOR_CORRECTION
	cfg.publication_package = None
	cfg.confirmed_document_package = None
	cfg.it_publication_record = None
	cfg.readiness_report = None
	cfg.review_workspace = None
	cfg.flags.ignore_mandatory = True
	cfg.flags.ignore_f1_publication_lock = True
	cfg.save(ignore_permissions=False)
	frappe.db.commit()
	return {
		"returned": True,
		"publication_id": publication_id,
		"configuration_id": configuration_id,
		"status": STATUS_RETURNED_FOR_CORRECTION,
		"reason": reason,
	}
