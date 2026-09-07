# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5.10/D14 — supporting-material file checks.

No malware scanner exists anywhere in this bench. Rather than silently
claim a file is "clean", `check_file` records the honest result: type,
size and readability are checked directly; a malware-scan verdict is
produced only if a scanner is registered under the `kt_file_scanners` hook,
and its absence is a visible "Not scanned — no scanner configured" result,
never a fabricated pass (FOLLOW_UPS FU-05).
"""

from __future__ import annotations

import hashlib

import frappe
from frappe.utils import cstr
from frappe.utils.file_manager import get_file

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB, per §5.10
ALLOWED_EXTENSIONS: tuple[str, ...] = ("pdf", "png", "jpg", "jpeg")

_MAGIC_BYTES: dict[bytes, str] = {
	b"%PDF": "pdf",
	b"\x89PNG\r\n\x1a\n": "png",
	b"\xff\xd8\xff": "jpg",
}


def _sniff_type(content: bytes) -> str | None:
	for magic, kind in _MAGIC_BYTES.items():
		if content.startswith(magic):
			return kind
	return None


def _scanner_result(content: bytes, filename: str) -> str:
	scanners = frappe.get_hooks("kt_file_scanners") or []
	if not scanners:
		return "Not scanned — no scanner configured"
	for path in scanners:
		try:
			verdict = frappe.get_attr(path)(content=content, filename=filename)
			if verdict:
				return cstr(verdict)
		except Exception:
			frappe.logger("kentender.requisitions.files").error(f"file scanner {path} failed", exc_info=True)
	return "Not scanned — no scanner configured"


def check_file(file_doc_name: str) -> dict[str, str]:
	"""Reads the private Frappe File, checks type/size/readability, computes
	a SHA-256 digest and records the scan result. Raises
	`ProcurementRequisitionsError("REQ_FILE_INVALID", ...)` on any failed
	check; returns `{digest, check_result}` on success."""
	from kentender_procurement.procurement_requisitions.services.errors import fail

	file_doc = frappe.get_doc("File", file_doc_name)
	extension = cstr(file_doc.file_name).rsplit(".", 1)[-1].lower() if "." in cstr(file_doc.file_name) else ""
	if extension not in ALLOWED_EXTENSIONS:
		fail("REQ_FILE_INVALID", f"File type .{extension or '?'} is not permitted. Use PDF, PNG, JPG or JPEG.")

	_, content = get_file(file_doc_name)
	if isinstance(content, str):
		content = content.encode("utf-8")
	if len(content) > MAX_FILE_SIZE_BYTES:
		fail("REQ_FILE_INVALID", "File exceeds the 20 MB maximum size.")
	if not content:
		fail("REQ_FILE_INVALID", "File is empty or unreadable.")

	sniffed = _sniff_type(content)
	if sniffed is None or (sniffed != extension and not (sniffed == "jpg" and extension == "jpeg")):
		fail("REQ_FILE_INVALID", "File content does not match its declared type.")

	digest = hashlib.sha256(content).hexdigest()
	check_result = _scanner_result(content, cstr(file_doc.file_name))
	if check_result not in ("Not scanned — no scanner configured",) and check_result.lower().startswith("infected"):
		fail("REQ_FILE_INVALID", "File failed malware scanning.")
	return {"digest": digest, "check_result": check_result}
