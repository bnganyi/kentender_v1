# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Minimal **TM2 Tender** rows for STD / publication tests (replaces legacy Procurement Tender)."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE


def insert_minimal_tm2_for_std(
	*,
	tender_title: str,
	tender_reference: str,
	std_template: str | None = None,
) -> str:
	"""Insert a draft TM2 tender with STD binding fields; return document name."""
	doc = frappe.new_doc("TM2 Tender")
	doc.tender_title = tender_title
	doc.tender_reference = tender_reference
	doc.procurement_category = "Works"
	doc.procuring_entity_code = "MOH"
	doc.fiscal_year = "2026"
	doc.std_template = (std_template or TEMPLATE_CODE).strip()
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name
