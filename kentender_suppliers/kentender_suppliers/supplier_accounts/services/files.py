# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Account evidence files (BDS-CHG-001 v0.8 §4.7, §5.5; plan D16). Type,
size and readability are checked here; the malware verdict comes only from
a scanner registered on `kt_file_scanners` (kentender_core file_integrity).
A file is Available only with a clean verdict; with no scanner it is kept as
"Not scanned" and cannot support a signatory; an infected file is refused
and nothing is stored. The reasons shown are safe: type, size or scan."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import file_integrity

ALLOWED = ("pdf", "png", "jpg", "jpeg")
MAX_BYTES = file_integrity.MAX_FILE_SIZE_BYTES
REASONS = {
	"empty": "The file is empty.",
	"size": "Upload a file of 20 MB or less.",
	"type": "Upload a PDF, PNG or JPEG file.",
	"scan": "The file did not pass the malware check.",
	"unreadable": "The file could not be read. Upload a complete PDF, PNG or JPEG file.",
}


def check(content: bytes | None, filename: str) -> dict[str, Any]:
	"""`{ok, reason?, digest, size, check_result, status}` for one upload."""
	name = cstr(filename).strip()
	extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
	data = content or b""
	if not data:
		return {"ok": False, "reason": REASONS["empty"]}
	if len(data) > MAX_BYTES:
		return {"ok": False, "reason": REASONS["size"]}
	sniffed = file_integrity.sniff_type(data)
	if extension not in ALLOWED or sniffed is None or (sniffed != extension and not (sniffed == "jpg" and extension == "jpeg")):
		return {"ok": False, "reason": REASONS["type"]}
	if file_integrity.unreadable(data):
		return {"ok": False, "reason": REASONS["unreadable"]}
	verdict = file_integrity.scanner_result(data, name)
	if file_integrity.is_infected(verdict):
		return {"ok": False, "reason": REASONS["scan"]}
	return {
		"ok": True, "digest": hashlib.sha256(data).hexdigest(), "size": len(data), "check_result": cstr(verdict),
		"status": "Available" if cstr(verdict).lower().startswith("clean") else "Not scanned",
	}


def store(*, attached_to: str, filename: str, content: bytes) -> str:
	doc = frappe.get_doc({
		"doctype": "File", "file_name": cstr(filename).strip(), "is_private": 1,
		"attached_to_doctype": "Supplier Account Evidence", "attached_to_name": attached_to, "content": content,
	})
	doc.insert(ignore_permissions=True)
	return doc.name
