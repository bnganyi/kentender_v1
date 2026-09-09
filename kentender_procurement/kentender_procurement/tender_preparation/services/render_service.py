# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.5/§14 — renders from the server's canonical
projection (never a browser value), and at approval stores the outputs as
private Files on the publication handoff, once (plan D4)."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe

from kentender_procurement.tender_preparation.services import digest, serializer
from kentender_procurement.tender_templates import renderer


def render(tender, version, snapshot: dict[str, Any], *, approval: dict[str, str] | None = None, with_pdf: bool = False) -> dict[str, Any]:
	context = serializer.render_context(tender, version, snapshot, approval=approval)
	out = renderer.render_both(context)
	out["context"] = context
	out["context_digest"] = digest.sha256_hex(serializer.public_context(context))
	if with_pdf:
		footer = f"{tender.tender_reference} — Page [page] of [topage]"
		out["invitation_pdf"] = renderer.to_pdf(out["invitation_html"])
		out["issued_tender_pdf"] = renderer.to_pdf(out["issued_tender_html"], footer_center=footer)
		out["invitation_pdf_digest"] = hashlib.sha256(out["invitation_pdf"]).hexdigest()
		out["issued_tender_pdf_digest"] = hashlib.sha256(out["issued_tender_pdf"]).hexdigest()
	return out


def _private_file(*, attached_to: str, file_name: str, content: bytes | str) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "File", "file_name": file_name, "is_private": 1, "attached_to_doctype": "Tender Publication Handoff",
			"attached_to_name": attached_to, "content": content,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def store_files(*, handoff_name: str, tender_reference: str, renders: dict[str, Any]) -> dict[str, str]:
	"""Four private Files on the handoff: both authoritative HTML outputs and
	both convenience PDFs. Called once inside the approval savepoint."""
	base = tender_reference.replace("/", "-")
	return {
		"invitation_html_file": _private_file(attached_to=handoff_name, file_name=f"{base}-invitation.html", content=renders["invitation_html"]),
		"issued_tender_html_file": _private_file(attached_to=handoff_name, file_name=f"{base}-tender.html", content=renders["issued_tender_html"]),
		"invitation_pdf_file": _private_file(attached_to=handoff_name, file_name=f"{base}-invitation.pdf", content=renders["invitation_pdf"]),
		"issued_tender_pdf_file": _private_file(attached_to=handoff_name, file_name=f"{base}-tender.pdf", content=renders["issued_tender_pdf"]),
	}
