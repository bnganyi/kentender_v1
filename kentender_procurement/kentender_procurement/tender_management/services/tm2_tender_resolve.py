# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Resolve **TM2 Tender** documents from API / publication inputs (tender_code, doc name, tender_reference)."""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


def resolve_tm2_tender_document(tender_code: str) -> Document | None:
	"""Return **TM2 Tender** doc for business ``tender_code``, document ``name``, or unique ``tender_reference``."""
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return frappe.get_doc("TM2 Tender", name)
	if frappe.db.exists("TM2 Tender", tc):
		return frappe.get_doc("TM2 Tender", tc)
	rows = frappe.get_all("TM2 Tender", filters={"tender_reference": tc}, pluck="name", limit=3)
	if len(rows) == 1:
		return frappe.get_doc("TM2 Tender", rows[0])
	return None


def canonical_tm2_tender_code(tm2: Document) -> str:
	return cstr(tm2.tender_code).strip() or tm2.name
