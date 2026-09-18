# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.5 / §11.3 — renders the Invitation and the complete
issued Tender from the server's canonical projection (never a browser
value) through the installed bundle's renderer (plan D5). Previews render
from the saved Version and change nothing (TPR08-AC-023); the same render
is what submission freezes, so identical inputs give identical digests
(TPR08-AC-024)."""

from __future__ import annotations

import hashlib
from typing import Any

from kentender_procurement.tender_templates import renderer
from kentender_procurement.tenders.services import digest, serializer


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


def approval_block(version) -> dict[str, str] | None:
	"""The signature block once the Version is approved (§10.1: the
	Invitation is authorised by the Head of Procurement Function)."""
	if not version.approved_by:
		return None
	import frappe
	from frappe.utils import cstr

	return {
		"official_name": cstr(frappe.db.get_value("User", version.approved_by, "full_name") or version.approved_by),
		"official_title": "Head of Procurement Function",
		"approved_date": serializer.fmt_date(version.approved_at),
		"reference": f"{frappe.db.get_value('Tender', version.tender, 'tender_reference')}-V{int(version.version_number)}",
	}
