# Copyright (c) 2026, KenTender and contributors
"""Shared test-fixture helper: populates the minimum content needed for a Draft
to pass all sixteen §5 coverage rows and have zero §11.2 Blocking findings.

Needed from Phase 6 onward — `submit_for_review` (§6.1 step 7 / §16.4) now
genuinely runs the complete check and refuses to submit a bare Draft, so every
phase's "submit this Draft" test fixture needs real (if minimal) content across
every coverage area, not just an official source. Centralized here rather than
duplicated per phase's test file.
"""

from __future__ import annotations

import frappe


def populate_minimum_coverage(draft_name: str, package_id: str) -> None:
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	owner = {"reference_doctype": "STD Cfg Draft", "reference_name": draft.name}

	# Areas 2, 11, 12 — Document Structure / Background / GCC are section-scoped,
	# not owned by a Phase 2 schema doctype.
	for code, coverage_area_number in (("SEC-I", 2), ("SEC-IX", 11), ("GCC", 12)):
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": package_id,
				"section_code": f"{code}-{draft.name}",
				"title": f"Fixture section {code}",
				"coverage_area_number": coverage_area_number,
				"display_order": coverage_area_number,
				"is_required": 0,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**owner,
				"section_id": section.name,
				"block_type": "Locked text",
				"display_order": 1,
				"locked_text": f"Fixture locked text for {code}.",
			}
		).insert(ignore_permissions=True)

	# Areas 1, 3, 15 — Tender Parameters.
	param = frappe.get_doc(
		{
			"doctype": "STD Cfg Parameter Definition",
			**owner,
			"parameter_key": f"fixture.param.{draft.name}",
			"label": "Fixture parameter",
			"value_type": "Text",
			"runtime_owner": "Tender Preparation",
			"required": 1,
			"render_binding": "Section II — Tender Data Sheet",
		}
	).insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "STD Cfg Output Mapping",
			**owner,
			"source_binding_key": param.parameter_key,
			"owning_area": "PCFG-03",
			"target": "Render",
		}
	).insert(ignore_permissions=True)

	# Areas 7, 8 — IT Requirements.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Requirement Schema",
			**owner,
			"category": "Functional",
			"display_order": 1,
			"allowed_response_types": "Compliance choice",
			"acceptance_mode": "Fixture acceptance mode",
			"render_binding": "Sections V and VI",
			"bidder_response_binding": "Technical compliance response",
			"evaluation_binding": "Requirement evaluation input",
			"contract_carry_forward_binding": "Accepted supplier obligation",
		}
	).insert(ignore_permissions=True)

	# Area 9 — Implementation Schedule.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Schedule Schema",
			**owner,
			"milestone_key": f"fixture.milestone.{draft.name}",
			"title": "Fixture milestone",
			"display_order": 1,
			"required_deliverable": "Fixture deliverable",
			"completion_rule": "30 days from commencement",
			"acceptance_checkpoint": "Fixture acceptance checkpoint",
			"render_binding": "Schedule render slot",
			"contract_binding": "Contract Formation schedule",
		}
	).insert(ignore_permissions=True)

	# Area 10 — System Inventory.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Inventory Schema",
			**owner,
			"category": "Hardware",
			"price_schedule_link_policy": "Required",
			"render_binding": "Inventory render slot",
		}
	).insert(ignore_permissions=True)

	# Area 6 — Price Schedules.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Price Schema",
			**owner,
			"family": "Implementation services",
			"line_description": "Fixture line description",
			"quantity_unit_source": "Approved scope",
			"currency_rule": "Kenya Shillings",
			"tax_treatment": "VAT inclusive",
			"bidder_price_fields": "Unit price\nTax amount",
			"calculation": "Quantity x Unit price + Tax",
			"evaluated_total_binding": "Evaluated total",
		}
	).insert(ignore_permissions=True)

	# Area 4 — Evaluation and Qualification.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Evaluation Schema",
			**owner,
			"stage": "Technical evaluation",
			"criterion_key": f"fixture.criterion.{draft.name}",
			"criterion_structure": "Fixture criterion",
			"display_order": 1,
			"treatment": "Pass/Fail",
			"response_source": "Requirement response",
			"failure_effect": "Fails technical evaluation",
		}
	).insert(ignore_permissions=True)

	# Area 5, 14 — Forms and Evidence (with a field row so it isn't flagged as an
	# opaque-upload-only form).
	form = frappe.get_doc(
		{
			"doctype": "STD Cfg Form Schema",
			**owner,
			"form_key": f"fixture.form.{draft.name}",
			"form_name": "Fixture Form",
			"activation": "Always",
			"render_location": "Section IV",
		}
	)
	form.append("fields", {"field_label": "Fixture field", "field_type": "Text", "required": 1})
	form.insert(ignore_permissions=True)

	# Areas 13, 14, 16 — Contract and Outputs.
	frappe.get_doc(
		{
			"doctype": "STD Cfg Contract Schema",
			**owner,
			"value_category": "Performance security",
			"supplied_by": "Tender Preparation",
			"required_treatment": "Required",
			"scc_binding": "SCC performance security clause",
		}
	).insert(ignore_permissions=True)


def cleanup_minimum_coverage(draft_name: str, package_id: str) -> None:
	from kentender_procurement.std_configuration.services import std_lifecycle

	for doctype in std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES:
		frappe.db.delete(doctype, {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name})
	for section in frappe.get_all("STD Cfg Section", filters={"package_id": package_id}, pluck="name"):
		frappe.db.delete("STD Cfg Content Block", {"section_id": section})
		frappe.db.delete("STD Cfg Section", {"name": section})
	frappe.db.delete("STD Cfg Validation Finding", {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name})
