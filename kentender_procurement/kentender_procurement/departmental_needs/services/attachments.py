from __future__ import annotations

import hashlib
import io
import os
import zipfile
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime
from frappe.utils.file_manager import save_file

from kentender_procurement.departmental_needs.constants import STATE_DRAFT, STATE_RETURNED
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.lifecycle import (
	_check_token,
	_locked_need,
	_record_event,
	_token,
)
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	can_view,
	owner_capability,
	require_owner_command,
)

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_ACTIVE_FILES = 10

_PDF = "application/pdf"
_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PNG = "image/png"
_JPEG = "image/jpeg"

ALLOWED_TYPES: dict[str, tuple[str, ...]] = {
	".pdf": (_PDF,),
	".docx": (_DOCX,),
	".xlsx": (_XLSX,),
	".png": (_PNG,),
	".jpg": (_JPEG,),
	".jpeg": (_JPEG,),
}


def _office_xml_kind(content: bytes) -> str | None:
	"""OOXML (.docx/.xlsx) both share the ZIP signature — the real distinguishing
	signal is the declared content type inside `[Content_Types].xml`."""
	try:
		with zipfile.ZipFile(io.BytesIO(content)) as archive:
			manifest = archive.read("[Content_Types].xml").decode("utf-8", errors="ignore")
	except (zipfile.BadZipFile, KeyError):
		return None
	if "wordprocessingml.document.main" in manifest:
		return _DOCX
	if "spreadsheetml.sheet.main" in manifest:
		return _XLSX
	return None


def _signature_content_type(content: bytes) -> str | None:
	if content.startswith(b"%PDF-"):
		return _PDF
	if content.startswith(b"\x89PNG\r\n\x1a\n"):
		return _PNG
	if content.startswith(b"\xff\xd8\xff"):
		return _JPEG
	if content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06"):
		return _office_xml_kind(content)
	return None


def _validate_upload(*, filename: str, content: bytes, declared_content_type: str) -> str:
	"""Enforce §3.3: extension, declared MIME type and file signature must all
	agree. Returns the confirmed MIME type."""
	name = cstr(filename or "").strip()
	if not name or "/" in name or "\\" in name or ".." in name:
		fail("NDS_ATTACHMENT_FILENAME_INVALID", "Invalid file name.")
	ext = os.path.splitext(name)[1].lower()
	allowed_types = ALLOWED_TYPES.get(ext)
	if not allowed_types:
		fail("NDS_ATTACHMENT_TYPE_NOT_ALLOWED", "Only PDF, DOCX, XLSX, PNG and JPG/JPEG files are permitted.")
	if not content:
		fail("NDS_ATTACHMENT_EMPTY", "Empty files cannot be uploaded.")
	if len(content) > MAX_FILE_BYTES:
		fail("NDS_ATTACHMENT_TOO_LARGE", "Each supporting document is limited to 20 MB.")
	declared = cstr(declared_content_type or "").strip().lower().split(";")[0]
	if declared and declared != "application/octet-stream" and declared not in allowed_types:
		fail("NDS_ATTACHMENT_TYPE_MISMATCH", "The declared file type does not match the file extension.")
	signature_type = _signature_content_type(content)
	if signature_type not in allowed_types:
		fail("NDS_ATTACHMENT_SIGNATURE_MISMATCH", "The file's actual content does not match its extension.")
	return signature_type


def _active_count(need: str) -> int:
	return frappe.db.count("Departmental Need Attachment", {"departmental_need": need, "is_active": 1})


def upload_attachment(*, need: str, expected_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""NDS-CHG-002 §3.3 — accepts a single multipart `file` field. New uploads
	start `scan_status="Pending"` (quarantined until a scanner integration calls
	`mark_attachment_scanned`); quarantine blocks submission, never draft save."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("NDS_IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.")
	existing = frappe.db.get_value("Departmental Need Attachment", {"idempotency_key": key}, "name")
	if existing:
		return _attachment_result(frappe.get_doc("Departmental Need Attachment", existing), reused=True)
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("edit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_CONTENT_LOCKED", "Only Draft or Returned Departmental Needs may receive new attachments.")
	if _active_count(doc.name) >= MAX_ACTIVE_FILES:
		fail("NDS_ATTACHMENT_LIMIT_REACHED", "A Departmental Need may hold at most 10 active supporting documents.")
	request = getattr(frappe.local, "request", None)
	if not request or "file" not in request.files:
		fail("NDS_ATTACHMENT_FILE_MISSING", "No file uploaded (form field `file`).")
	upload = request.files["file"]
	content = upload.stream.read()
	filename = upload.filename or "attachment"
	mime_type = _validate_upload(filename=filename, content=content, declared_content_type=upload.mimetype or "")
	digest = hashlib.sha256(content).hexdigest()
	attachment = frappe.get_doc({
		"doctype": "Departmental Need Attachment", "attachment_reference": f"NDA-{uuid4().hex.upper()}",
		"departmental_need": doc.name, "original_filename": filename, "file_size": len(content),
		"mime_type": mime_type, "sha256_digest": digest, "uploaded_by": principal,
		"uploaded_at": now_datetime(), "scan_status": "Pending", "is_active": 1, "idempotency_key": key,
	}).insert(ignore_permissions=True)
	saved = save_file(f"{attachment.name}-{filename}", content, "Departmental Need Attachment", attachment.name, is_private=1)
	attachment.db_set("file", saved.file_url, update_modified=False)
	_record_event(
		doc, action="Attach document", prior=doc.status, result=doc.status, principal=principal,
		idempotency_key=f"{key}:review", reason=filename,
	)
	return _attachment_result(attachment, reused=False)


def remove_attachment(*, need: str, attachment: str, expected_token: str, idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	"""Logical removal only (NDS-CHG-002 §3.3) — the row and its File are
	retained; a Submitted snapshot's attachment references are unaffected
	since only Draft/Returned attachments may ever be removed."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("NDS_IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.")
	if frappe.db.exists("Departmental Need Review", {"idempotency_key": key}):
		att = frappe.get_doc("Departmental Need Attachment", cstr(attachment).strip())
		return {"ok": True, "idempotent": True, "attachment": att.name, "is_active": bool(att.is_active)}
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("edit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_CONTENT_LOCKED", "Only Draft or Returned Departmental Needs may have attachments removed.")
	att = frappe.get_doc("Departmental Need Attachment", cstr(attachment).strip())
	if att.departmental_need != doc.name:
		fail("NDS_NOT_FOUND", "Attachment not found on this Departmental Need.")
	if not att.is_active:
		fail("NDS_ATTACHMENT_ALREADY_REMOVED", "This attachment has already been removed.")
	att.is_active = 0
	att.removed_by = principal
	att.removed_at = now_datetime()
	att.save(ignore_permissions=True)
	_record_event(
		doc, action="Remove document", prior=doc.status, result=doc.status, principal=principal,
		idempotency_key=idempotency_key, reason=reason or att.original_filename,
	)
	return {"ok": True, "attachment": att.name, "is_active": False}


def mark_attachment_scanned(*, attachment: str, clean: bool) -> dict[str, Any]:
	"""The malware-scanner integration point (§3.3). Not exposed as a public
	API — a real scanning service (or, in this environment, a test) calls this
	directly once it has a verdict for a Pending attachment."""
	att = frappe.get_doc("Departmental Need Attachment", cstr(attachment).strip())
	if att.scan_status != "Pending":
		fail("NDS_ATTACHMENT_ALREADY_SCANNED", "This attachment has already been scanned.")
	att.scan_status = "Clean" if clean else "Failed"
	att.save(ignore_permissions=True)
	return {"ok": True, "attachment": att.name, "scan_status": att.scan_status}


def list_attachments(*, need: str, user: str | None = None) -> list[dict[str, Any]]:
	"""Only active attachments are ever listed to a viewer (NDS-FR-038)."""
	principal = actor(user)
	doc = frappe.get_doc("Departmental Need", need)
	allowed, _profile = can_view(doc, principal)
	if not allowed:
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	rows = frappe.get_all(
		"Departmental Need Attachment", filters={"departmental_need": doc.name, "is_active": 1},
		fields=["name", "attachment_reference", "original_filename", "file_size", "mime_type", "scan_status", "uploaded_by", "uploaded_at"],
		order_by="uploaded_at asc",
	)
	return rows


def download_attachment(*, need: str, attachment: str, user: str | None = None) -> None:
	"""Streams the file directly (never a public object URL) — matches this
	repo's established `document_preview.py::download_document_preview_pdf`
	permission-then-stream idiom. Only a Clean, active attachment is ever
	served (NDS-FR-038)."""
	principal = actor(user)
	doc = frappe.get_doc("Departmental Need", need)
	allowed, _profile = can_view(doc, principal)
	if not allowed:
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	att = frappe.get_doc("Departmental Need Attachment", cstr(attachment).strip())
	if att.departmental_need != doc.name or not att.is_active or att.scan_status != "Clean":
		fail("NDS_NOT_FOUND", "Attachment not found.")
	file_doc = frappe.get_doc("File", {"file_url": att.file})
	# `get_content()` may text-decode a mostly-printable file (e.g. our own
	# fixture PDFs), which would corrupt binary content — read the stored
	# bytes directly instead, matching the digest we recorded on upload.
	with open(file_doc.get_full_path(), "rb") as fh:
		content = fh.read()
	frappe.local.response.filename = att.original_filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"


def _attachment_result(att, *, reused: bool) -> dict[str, Any]:
	return {
		"ok": True, "idempotent": reused, "attachment": att.name, "attachment_reference": att.attachment_reference,
		"original_filename": att.original_filename, "file_size": att.file_size, "mime_type": att.mime_type,
		"scan_status": att.scan_status,
	}
