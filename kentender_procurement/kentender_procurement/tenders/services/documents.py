# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 `GetTenderDocument` / §12.3(3) — immutable
generated documents addressed by digest (plan D5). A `Tender Document` row
is written once when a freezing command runs (submit, approve, issue,
cancel); the authoritative HTML and the convenience PDF are private Files
attached to it. Audiences: `Internal` (the exact package, internal
readers), `Public` (the supplier-visible package — the same HTML, no
internal values ever entered it), `Audit` (Auditor / technical read)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tenders.services import envelope
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail

DOCTYPE = "Tender Document"
KIND_INVITATION = "Invitation"
KIND_COMPLETE = "Complete Tender"
KIND_ADDENDUM = "Addendum notice"
KIND_CANCELLATION = "Cancellation notice"
KINDS = (KIND_INVITATION, KIND_COMPLETE, KIND_ADDENDUM, KIND_CANCELLATION)
AUDIENCES = ("Internal", "Public", "Audit")


def _private_file(*, attached_to: str, file_name: str, content: bytes | str) -> str:
	doc = frappe.get_doc(
		{"doctype": "File", "file_name": file_name, "is_private": 1, "attached_to_doctype": DOCTYPE, "attached_to_name": attached_to, "content": content}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def existing(*, kind: str, digest_value: str) -> str | None:
	rows = frappe.get_all(DOCTYPE, filters={"kind": kind, "digest": digest_value}, pluck="name", limit=1)
	return rows[0] if rows else None


def store(
	*,
	tender: str,
	kind: str,
	html: str,
	digest_value: str,
	tender_version: str = "",
	addendum: str = "",
	cancellation: str = "",
	pdf: bytes | None = None,
	file_base: str,
	fixture_namespace: str = "",
) -> str:
	"""Write one immutable document row (idempotent on kind + digest) with
	its HTML file and, when given, its convenience PDF."""
	if kind not in KINDS:
		raise ValueError(kind)
	found = existing(kind=kind, digest_value=digest_value)
	if found:
		return found
	doc = envelope.insert(
		frappe.get_doc(
			{
				"doctype": DOCTYPE, "tender": tender, "tender_version": tender_version or None, "addendum": addendum or None,
				"cancellation": cancellation or None, "kind": kind, "audience": "Internal", "digest": digest_value,
				"generated_by": frappe.session.user, "generated_at": now_datetime(), "fixture_namespace": fixture_namespace,
			}
		)
	)
	html_file = _private_file(attached_to=doc.name, file_name=f"{file_base}.html", content=html)
	values = {"html_file": html_file}
	if pdf:
		values["file"] = _private_file(attached_to=doc.name, file_name=f"{file_base}.pdf", content=pdf)
	envelope.bump(doc, **values)
	return doc.name


def html_of(document_name: str) -> str:
	html_file = frappe.db.get_value(DOCTYPE, document_name, "html_file")
	if not html_file:
		return ""
	from frappe.utils.file_manager import get_file

	_, content = get_file(html_file)
	return content.decode("utf-8") if isinstance(content, bytes) else cstr(content)


def get_tender_document(*, digest_value: str, audience: str = "Internal", user: str | None = None) -> dict[str, Any]:
	"""§7.1 `GetTenderDocument` — the exact immutable document by digest for
	an authorised audience. Reads create nothing."""
	actor = authz.actor(user)
	if audience not in AUDIENCES:
		fail("TND_CONTROL_INVALID", "Unknown document audience.")
	row = frappe.db.get_value(DOCTYPE, {"digest": digest_value}, ["name", "tender", "tender_version", "addendum", "cancellation", "kind", "generated_at", "file", "html_file"], as_dict=True)
	if not row:
		authz.not_found()
	root = frappe.db.get_value("Tender", row.tender, ["tender_reference", "lead_org_unit", "contributing_org_unit_ids", "overall_status", "published_at"], as_dict=True)
	if not root:
		authz.not_found()
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	if audience == "Audit" and mode not in ("site", "technical"):
		authz.not_found()
	if audience == "Public" and not root.published_at:
		# The supplier-visible package exists only once the Tender is published.
		authz.not_found()
	file_row = frappe.db.get_value("File", row.file, ["file_name", "file_size", "file_url"], as_dict=True) if row.file else None
	return {
		"outcome": "OK",
		"document": row.name,
		"tender": row.tender,
		"tender_reference": root.tender_reference,
		"kind": row.kind,
		"audience": audience,
		"digest": digest_value,
		"generated_at": cstr(row.generated_at),
		"html": html_of(row.name),
		"pdf": {"file_name": file_row.file_name, "size": int(file_row.file_size or 0), "url": file_row.file_url, "format": "PDF"} if file_row else None,
	}


def list_for_tender(tender: str) -> list[dict[str, Any]]:
	return frappe.get_all(
		DOCTYPE, filters={"tender": tender}, fields=["name", "tender_version", "addendum", "cancellation", "kind", "digest", "file", "generated_at"],
		order_by="generated_at asc, creation asc", limit_page_length=0,
	)
