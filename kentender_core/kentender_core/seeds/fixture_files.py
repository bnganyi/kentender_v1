# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Synthetic evidence files for seeds — real bytes of the stated type,
labelled inside as fixtures (SEED-001 v1.3 §3.7, SEED-AC-028: evidence
references must resolve to actual bytes, and synthetic evidence is labelled
as such)."""

from __future__ import annotations

import frappe


def labelled_pdf(label: str) -> bytes:
	"""A one-page PDF with a correct cross-reference table — Frappe's upload
	check parses every PDF (frappe.utils.pdf.pdf_contains_js), so a header
	alone is refused."""
	text = f"KenTender fixture, not a real document: {label}".replace("(", "[").replace(")", "]")
	stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
	objects = [
		b"<< /Type /Catalog /Pages 2 0 R >>",
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
		b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
	]
	out = bytearray(b"%PDF-1.4\n")
	offsets = []
	for number, body in enumerate(objects, start=1):
		offsets.append(len(out))
		out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
	xref = len(out)
	out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
	for offset in offsets:
		out += f"{offset:010d} 00000 n \n".encode()
	out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
	return bytes(out)


def attached_pdf(file_name: str, *, label: str, doctype: str, name: str) -> str:
	"""A private labelled PDF attached to `doctype`/`name`, so it goes with
	that record (the canonical clear removes files whose record is gone).
	Returns its file URL."""
	return (
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"is_private": 1,
				"content": labelled_pdf(label),
				"attached_to_doctype": doctype,
				"attached_to_name": name,
			}
		)
		.insert(ignore_permissions=True)
		.file_url
	)
