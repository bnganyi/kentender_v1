# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared evidence-file integrity check (TPR-CHG-001 v0.8 §4.7/§5.5(4)/
§12.3(4), REQ-CHG-001 v1.6 §5.10 — plan D10).

No malware scanner exists anywhere in this bench. Rather than silently claim
a file is "clean", `check_file` records the honest result: type, size and
readability are checked directly; a malware-scan verdict is produced only if
a scanner is registered under the `kt_file_scanners` hook, and its absence
is a visible "Not scanned — no scanner configured" result, never a
fabricated pass. Lifted from Procurement Requisitions' `files.py` so that
Requisition supporting materials and Tender publication evidence share one
implementation and one truthful vocabulary.
"""

from __future__ import annotations

import hashlib
from typing import Callable

import frappe
from frappe.utils import cstr
from frappe.utils.file_manager import get_file

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
DEFAULT_ALLOWED_EXTENSIONS: tuple[str, ...] = ("pdf", "png", "jpg", "jpeg")
NOT_SCANNED = "Not scanned — no scanner configured"

_MAGIC_BYTES: dict[bytes, str] = {
	b"%PDF": "pdf",
	b"\x89PNG\r\n\x1a\n": "png",
	b"\xff\xd8\xff": "jpg",
}


def sniff_type(content: bytes) -> str | None:
	for magic, kind in _MAGIC_BYTES.items():
		if content.startswith(magic):
			return kind
	return None


def scanner_result(content: bytes, filename: str) -> str:
	scanners = frappe.get_hooks("kt_file_scanners") or []
	if not scanners:
		return NOT_SCANNED
	for path in scanners:
		try:
			verdict = frappe.get_attr(path)(content=content, filename=filename)
			if verdict:
				return cstr(verdict)
		except Exception:
			frappe.logger("kentender.core.file_integrity").error(f"file scanner {path} failed", exc_info=True)
	return NOT_SCANNED


def is_infected(check_result: str) -> bool:
	return cstr(check_result).lower().startswith("infected")


def check_file(
	file_doc_name: str,
	*,
	allowed_extensions: tuple[str, ...] = DEFAULT_ALLOWED_EXTENSIONS,
	fail: Callable[[str], None],
) -> dict[str, str]:
	"""Reads the private Frappe File, checks type/size/readability, computes
	a SHA-256 digest and records the scan result. Calls `fail(message)` —
	the caller's own error function, bound to its own error code — on any
	failed check; returns `{digest, check_result, media_type, size}`."""
	if not file_doc_name or not frappe.db.exists("File", file_doc_name):
		fail("The supporting file could not be found.")
	file_doc = frappe.get_doc("File", file_doc_name)
	name = cstr(file_doc.file_name)
	extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
	if extension not in allowed_extensions:
		fail(f"File type .{extension or '?'} is not permitted. Use {', '.join(e.upper() for e in allowed_extensions)}.")

	_, content = get_file(file_doc_name)
	if isinstance(content, str):
		content = content.encode("utf-8")
	if len(content) > MAX_FILE_SIZE_BYTES:
		fail("File exceeds the 20 MB maximum size.")
	if not content:
		fail("File is empty or unreadable.")

	sniffed = sniff_type(content)
	if sniffed is None or (sniffed != extension and not (sniffed == "jpg" and extension == "jpeg")):
		fail("File content does not match its declared type.")

	digest = hashlib.sha256(content).hexdigest()
	check_result = scanner_result(content, name)
	if is_infected(check_result):
		fail("File failed malware scanning.")
	return {"digest": digest, "check_result": check_result, "media_type": sniffed, "size": str(len(content))}
