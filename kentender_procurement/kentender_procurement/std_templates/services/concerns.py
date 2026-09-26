# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`CreateSTDTemplateConcern`, `ListSTDTemplateConcerns`,
`ResolveSTDTemplateConcern` (STD-TPL-IMP-001 v1.0 §4.3, §6; STD-TPL-001
v0.10 §11.3 "Report concern").

A concern is a bounded record against one exact installed release. Creating
one never changes lifecycle, availability, content or any Tender; the
release owner decides whether it needs a corrected successor or a
withdrawal. Resolution is a deployment-only command naming that owner
(owner ruling R5). Invalid input returns field errors
(`STD_CONCERN_INVALID`) so the dialog keeps what was entered.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.std_templates.services import access, runtime

DOCTYPE = "STD Template Concern"
CATEGORIES: tuple[str, ...] = ("Source treatment", "Tender document", "Supplier response", "Evaluation mapping", "Contract mapping", "Renderer", "Other")
STATUSES: tuple[str, ...] = ("Open", "Acknowledged", "Resolved", "Rejected")
LIMITS = {"source_locator": (0, 140), "summary": (5, 140), "description": (10, 2000)}
EVIDENCE_TYPES = ("pdf", "png", "jpg", "jpeg")


def _clean(values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
	errors: dict[str, str] = {}
	clean: dict[str, Any] = {}
	if not isinstance(values, dict):
		return {}, {"values": "Concern values must be an object."}
	for name in set(values) - {"category", "source_locator", "summary", "description", "evidence_file_id"}:
		errors[name] = "Unknown field."
	category = cstr(values.get("category")).strip()
	if category not in CATEGORIES:
		errors["category"] = "Choose a category."
	else:
		clean["category"] = category
	for field, (low, high) in LIMITS.items():
		text = cstr(values.get(field)).strip()
		if any(token in text for token in ("<", ">", "```")):
			errors[field] = "Enter plain text."
		elif len(text) < low:
			errors[field] = "Enter a summary of at least 5 characters." if field == "summary" else ("Describe the concern in at least 10 characters." if field == "description" else "Required.")
		elif len(text) > high:
			errors[field] = f"Use {high} characters or fewer."
		else:
			clean[field] = text
	file_id = cstr(values.get("evidence_file_id")).strip()
	if file_id:
		row = frappe.db.get_value("File", file_id, ["name", "owner", "file_name", "is_private", "attached_to_doctype", "file_size"], as_dict=True)
		if not row or row.owner != frappe.session.user or row.attached_to_doctype not in (None, "", DOCTYPE):
			errors["evidence_file_id"] = "Attach the file again."
		else:
			from kentender_core.services.file_integrity import MAX_FILE_SIZE_BYTES

			ext = cstr(row.file_name).rsplit(".", 1)[-1].lower() if "." in cstr(row.file_name) else ""
			if ext not in EVIDENCE_TYPES:
				errors["evidence_file_id"] = "Attach a PDF, PNG or JPG file."
			elif int(row.file_size or 0) > MAX_FILE_SIZE_BYTES:
				errors["evidence_file_id"] = "Attach a file of 20 MB or less."
			else:
				clean["evidence_file_id"] = row.name
	return clean, errors


def create_concern(release_id: str, values: dict[str, Any], *, user: str | None = None) -> dict[str, Any]:
	access.require_reader(user)
	release = runtime.release_doc(release_id)
	clean, errors = _clean(values)
	if errors:
		return {"ok": False, "code": "STD_CONCERN_INVALID", "errors": errors}
	before = frappe.db.get_value("Installed STD Release", release.name, ["lifecycle_status", "modified"], as_dict=True)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"release_id": release.name,
			"category": clean["category"],
			"source_locator": clean.get("source_locator", ""),
			"summary": clean["summary"],
			"description": clean["description"],
			"status": "Open",
			"reported_by": cstr(user or frappe.session.user),
			"reported_at": now_datetime(),
		}
	)
	doc.flags.kt_std_concern = True
	doc.insert(ignore_permissions=True)
	if clean.get("evidence_file_id"):
		evidence = frappe.get_doc("File", clean["evidence_file_id"])
		evidence.is_private = 1
		evidence.attached_to_doctype = DOCTYPE
		evidence.attached_to_name = doc.name
		evidence.save(ignore_permissions=True)
		doc.db_set("evidence_file_id", evidence.name, update_modified=False)
	after = frappe.db.get_value("Installed STD Release", release.name, ["lifecycle_status", "modified"], as_dict=True)
	if (before.lifecycle_status, cstr(before.modified)) != (after.lifecycle_status, cstr(after.modified)):
		frappe.throw("A concern must not change the release.")  # defensive: never expected
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(
		event_type="STD Release",
		entity="STD Templates",
		document_type=DOCTYPE,
		document_name=doc.name,
		action="Concern reported",
		metadata={"release_id": release.name, "category": doc.category, "has_evidence": bool(clean.get("evidence_file_id"))},
	)
	return {"ok": True, "concern_id": doc.name, "status": doc.status, "message": "Concern reported. It does not change this release's availability."}


def summary_for(release_id: str, *, user: str | None = None) -> dict[str, Any]:
	"""`ListSTDTemplateConcerns` for the release detail: status counts and the
	caller's own concerns (release-owner queues read every concern)."""
	principal = cstr(user or frappe.session.user)
	rows = frappe.get_all(DOCTYPE, filters={"release_id": release_id}, fields=["name", "category", "summary", "status", "reported_by", "reported_at", "source_locator"], order_by="reported_at desc", limit_page_length=0)
	counts = {status: sum(1 for r in rows if r.status == status) for status in STATUSES}
	own = [
		{"concern_id": r.name, "category": r.category, "summary": r.summary, "status": r.status, "source_locator": r.source_locator or ""}
		for r in rows
		if r.reported_by == principal
	]
	return {"counts": counts, "total": len(rows), "own": own, "categories": list(CATEGORIES)}


def list_concerns(release_id: str = "", status: str = "") -> list[dict[str, Any]]:
	"""The release-owner queue (deployment command; ruling R5)."""
	filters: dict[str, Any] = {}
	if release_id:
		filters["release_id"] = release_id
	if status:
		filters["status"] = status
	return frappe.get_all(DOCTYPE, filters=filters, fields=["name", "release_id", "category", "summary", "status", "reported_by", "reported_at"], order_by="reported_at asc", limit_page_length=0)


def resolve_concern(concern_id: str, status: str, resolution_note: str, release_owner: str, successor_release_id: str = "") -> dict[str, Any]:
	"""`bench --site <site> execute kentender_procurement.std_templates.services.concerns.resolve_concern --kwargs ...`
	Records the release owner's resolution; never edits the release."""
	if status not in ("Acknowledged", "Resolved", "Rejected"):
		frappe.throw("Resolution status must be Acknowledged, Resolved or Rejected.")
	if not cstr(release_owner).strip() or not cstr(resolution_note).strip():
		frappe.throw("Name the release owner and state the resolution.")
	if successor_release_id and not frappe.db.exists("Installed STD Release", successor_release_id):
		frappe.throw("Unknown successor release.")
	doc = frappe.get_doc(DOCTYPE, concern_id)
	doc.status = status
	doc.resolved_by = cstr(release_owner).strip()
	doc.resolved_at = now_datetime()
	doc.resolution_note = cstr(resolution_note).strip()
	doc.successor_release_id = successor_release_id or None
	doc.flags.kt_std_concern_resolve = True
	doc.save(ignore_permissions=True)
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type="STD Release", entity="STD Templates", document_type=DOCTYPE, document_name=doc.name, action=f"Concern {status.lower()}", performed_by=frappe.session.user, metadata={"release_owner": doc.resolved_by, "successor_release_id": successor_release_id})
	frappe.db.commit()
	return {"ok": True, "concern_id": doc.name, "status": doc.status}
