# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Unit tests for WG-03 bidder-facing preview presentation layer."""

from __future__ import annotations

import unittest

from kentender_procurement.tender_configurations.services.preview_presentation import (
	assert_no_forbidden_preview_markers,
	assert_price_units_normalized,
	assert_scc_values_complete,
	expand_requirement_reference,
	format_currency_amount,
	format_datetime_bidder,
	render_evaluation_section,
	render_information_system_requirements,
	render_inventory_section,
	render_price_section,
	render_scc_section,
	render_tds_section,
	render_technical_requirements_section,
	split_requirements,
	strip_pe_only_contract_form_notes,
)


class TestPreviewPresentation(unittest.TestCase):
	def test_format_datetime_and_currency(self):
		self.assertEqual(
			format_datetime_bidder("2026-08-30T15:30"),
			"30 August 2026, 3:30 PM EAT",
		)
		self.assertEqual(format_currency_amount("50000", "KES"), "KES 50,000")

	def test_tds_clause_aware_security_and_no_raw_keys(self):
		html, err = render_tds_section(
			{
				"contact_officer": "ABC",
				"clarification_deadline": "2026-08-30T15:30",
				"pre_tender_meeting_details": "",
				"reservation_category": "",
				"tender_security_required": "Yes",
				"tender_security_amount": "50000",
				"tender_security_currency": "KES",
				"tender_security_validity_period": "14",
				"tender_security_validity_unit": "days",
				"margin_of_preference_applies": "No",
				"submission_channel": "E-Procurement Portal",
				"submission_language": "English",
				"tender_currency": "KES",
			}
		)
		self.assertIsNone(err)
		self.assertIn("KES 50,000", html)
		self.assertIn("must remain valid for 14 days", html)
		self.assertIn("Clarifications must be submitted", html)
		self.assertIn("Margin of preference does not apply", html)
		self.assertNotIn("contact_officer", html)
		self.assertNotIn("Locked standard text", html)

	def test_evaluation_expands_requirement_refs(self):
		reqs = [
			{
				"requirement_id": "REQ-001",
				"title": "Compute Node Performance",
				"category_label": "Technical Requirement",
			}
		]
		html, err = render_evaluation_section(
			[
				{
					"criterion_name": "Technical compliance for: REQ-001",
					"stage": "Technical",
					"evaluation_basis": "Scored",
					"marks": "50",
					"related_requirement_id": "REQ-001",
					"bidder_evidence": "Required",
					"evidence_instruction": "Provide datasheets",
				}
			],
			reqs,
		)
		self.assertIsNone(err)
		self.assertIn("Compute Node Performance technical compliance", html)
		self.assertIn("Scored out of 50 marks", html)
		self.assertIn("kt-preview-table", html)
		self.assertIn("Maximum marks / pass-fail rule", html)
		self.assertNotIn("REQ-001", html)
		self.assertNotIn("Technical compliance for:", html)
		self.assertNotIn("kt-preview-criterion", html)

	def test_requirement_title_recovers_when_title_is_req_id(self):
		"""CFG-03 rows may store title=REQ-001 and the label in description."""
		reqs = [
			{
				"requirement_id": "REQ-001",
				"title": "REQ-001",
				"description": "Compute Node Performance",
				"category_label": "Technical Requirement",
				"treatment_label": "Evaluation-linked",
				"evidence_instruction": "Manufacturer datasheet required",
			}
		]
		tech_html, err = render_technical_requirements_section(reqs)
		self.assertIsNone(err)
		self.assertIn("Compute Node Performance", tech_html)
		self.assertNotIn("<h3>REQ-001</h3>", tech_html)
		eval_html, err2 = render_evaluation_section(
			[
				{
					"criterion_name": "REQ-001 technical compliance",
					"related_requirement_id": "REQ-001",
					"stage": "Technical",
					"evaluation_basis": "Scored",
					"bidder_evidence": "Required",
				}
			],
			reqs,
		)
		self.assertIsNone(err2)
		self.assertIn("Compute Node Performance technical compliance", eval_html)
		self.assertNotIn("REQ-001", eval_html)
		price_html, err3 = render_price_section(
			[
				{
					"item_name": "REQ-001",
					"related_requirement_id": "REQ-001",
					"bidder_facing_description": "Price for requirement: REQ-001",
					"unit": "lot",
					"quantity": "1",
					"currency": "KES",
				}
			],
			reqs,
		)
		self.assertIsNone(err3)
		self.assertIn("Compute Node Performance", price_html)
		self.assertNotIn("REQ-001", price_html)
		self.assertIsNone(assert_no_forbidden_preview_markers(tech_html + eval_html + price_html))

	def test_price_bidder_facing_labels(self):
		reqs = [
			{"requirement_id": "REQ-001", "title": "Compute Node Performance"},
			{"requirement_id": "REQ-002", "title": "Three-Year On-site Support"},
		]
		html, err = render_price_section(
			[
				{
					"item_name": "Price for requirement: REQ-001",
					"related_requirement_id": "REQ-001",
					"bidder_facing_description": (
						"Supply, install, and commission compute nodes meeting the "
						"specified performance requirement."
					),
					"unit": "Lot",
					"quantity": "1",
					"currency": "KES",
				},
				{
					"item_name": "Item 2",
					"related_requirement_id": "REQ-002",
					"bidder_facing_description": (
						"Provide three-year on-site support and warranty services."
					),
					"unit": "Lot",
					"quantity": "1",
					"currency": "KES",
				},
			],
			reqs,
		)
		self.assertIsNone(err)
		self.assertIn("Compute Node Performance", html)
		self.assertIn("Three-Year On-site Support", html)
		self.assertIn("Electronic price entry", html)
		self.assertIn("Bidder completion method", html)
		self.assertNotIn("[Bidder to complete]", html)
		self.assertNotIn("Price for requirement:", html)
		self.assertNotIn(">Item 1<", html)
		self.assertNotIn("REQ-001", html)

	def test_requirements_split_no_duplication(self):
		reqs = [
			{
				"title": "Helpdesk Continuity",
				"category_label": "Business Objective",
				"description": "Business need",
			},
			{
				"title": "Compute Node Performance",
				"category_label": "Technical Requirement",
				"description": "Tech need",
			},
		]
		is_rows, tech_rows = split_requirements(reqs)
		self.assertEqual(len(is_rows), 1)
		self.assertEqual(len(tech_rows), 1)
		is_html, _ = render_information_system_requirements(reqs)
		tech_html, _ = render_technical_requirements_section(reqs)
		self.assertIn("Helpdesk Continuity", is_html)
		self.assertNotIn("Compute Node Performance", is_html)
		self.assertIn("Compute Node Performance", tech_html)
		self.assertNotIn("Helpdesk Continuity", tech_html)
		self.assertIn("kt-preview-table", is_html)
		self.assertIn("Requirement ID", is_html)
		self.assertIn("ELECTRONIC_SCHEMA_REFERENCE", is_html)
		self.assertNotIn("Confirm Yes/No, cite reference", is_html)

	def test_inventory_empty_is_readiness_unless_na(self):
		html, err = render_inventory_section([])
		self.assertEqual(html, "")
		self.assertIsInstance(err, dict)
		self.assertEqual(err.get("status"), "generation_blocked")
		self.assertIn("CFG-05", err.get("blocking_area") or "")
		self.assertEqual(err.get("owner_step"), "CFG-05")
		self.assertEqual(
			err.get("owner_route"),
			"it-tender-configuration-system-inventory",
		)
		html2, err2 = render_inventory_section([], not_applicable=True)
		self.assertIsNone(err2)
		self.assertIn("not applicable", html2.lower())
		self.assertNotIn("No additional requirements", html2)

	def test_inventory_uses_cfg05_item_title_fields(self):
		"""CFG-05 Complete items use item_title — preview must not treat them as empty."""
		html, err = render_inventory_section(
			[
				{
					"item_title": "Existing Server Room",
					"item_description": "Server room on third floor",
					"bidder_consideration": (
						"Bidder should account for installation constraints and rack space."
					),
					"disclosure_status_label": "Safe to disclose",
				}
			]
		)
		self.assertIsNone(err)
		self.assertIn("Existing Server Room", html)
		self.assertIn("installation constraints", html)

	def test_inventory_skips_non_disclosable_items(self):
		html, err = render_inventory_section(
			[
				{
					"item_title": "Sensitive Network Map",
					"bidder_consideration": "Internal only",
					"disclosure_status_label": "Needs disclosure review",
				}
			]
		)
		self.assertEqual(html, "")
		self.assertIsInstance(err, dict)
		self.assertIn("Safe to disclose", err.get("message") or "")

	def test_expand_and_forbidden(self):
		self.assertEqual(
			expand_requirement_reference(
				"Technical compliance for: REQ-001",
				{"REQ-001": "Compute Node Performance"},
			),
			"Compute Node Performance technical compliance",
		)
		self.assertEqual(
			expand_requirement_reference(
				"REQ-001 technical compliance",
				{"REQ-001": "Compute Node Performance"},
			),
			"Compute Node Performance technical compliance",
		)
		self.assertIsNotNone(
			assert_no_forbidden_preview_markers("Locked standard text from bound STD version.")
		)
		self.assertIsNotNone(assert_no_forbidden_preview_markers("Readiness issue: CFG-05"))
		self.assertIsNotNone(assert_no_forbidden_preview_markers("<td>REQ-001</td>"))
		self.assertIsNotNone(assert_no_forbidden_preview_markers("Source NSSF fact"))
		self.assertIsNotNone(
			assert_no_forbidden_preview_markers("Confirm Yes/No, cite reference pages")
		)

	def test_tds_excludes_opening_notes_audit(self):
		html, err = render_tds_section(
			{
				"contact_officer": "Officer",
				"clarification_deadline": "2026-08-30T15:30",
				"submission_channel": "E-Procurement Portal",
				"submission_language": "English",
				"tender_currency": "KES",
				"tender_security_required": "No",
				"margin_of_preference_applies": "No",
				"opening_notes": "Source NSSF fact: PoC submission deadline advanced",
			}
		)
		self.assertIsNone(err)
		self.assertNotIn("Source NSSF", html)
		self.assertNotIn("Opening notes", html)

	def test_scc_rejects_as_specified_and_renders_values(self):
		block = assert_scc_values_complete(
			[{"item_label": "Governing law", "value_or_obligation": "As specified"}]
		)
		self.assertIsNotNone(block)
		html, err = render_scc_section(
			[
				{"item_label": "Governing law", "value_or_obligation": "Laws of Kenya"},
				{
					"item_label": "Scope",
					"value_or_obligation": "All modules as specified in Part 2",
				},
				{
					"item_label": "Commencement",
					"value_or_obligation": "Commencement within 14 days; 24 month implementation period",
				},
				{
					"item_label": "Payment",
					"value_or_obligation": "Milestone payment schedule",
				},
				{
					"item_label": "Source code / escrow",
					"value_or_obligation": "Source code escrow within 30 days",
				},
				{
					"item_label": "Subcontracting",
					"value_or_obligation": "Subcontracting requires prior written approval",
				},
				{"item_label": "SLA", "value_or_obligation": "P1 response 4 hours"},
				{
					"item_label": "Performance security",
					"value_or_obligation": "10% performance security",
				},
				{"item_label": "Warranty", "value_or_obligation": "12 month warranty"},
			]
		)
		self.assertIsNone(err)
		self.assertIn("Laws of Kenya", html)
		self.assertNotIn("As specified</td>", html)

	def test_price_units_gate(self):
		self.assertIsNotNone(
			assert_price_units_normalized([{"item_name": "X", "unit": "Month"}])
		)
		self.assertIsNone(
			assert_price_units_normalized([{"item_name": "X", "unit": "Per month"}])
		)

	def test_strip_pe_only_contract_form_notes(self):
		raw = (
			"SECTION VIII - CONTRACT FORMS\n"
			"Notes to the Procuring Entity on preparing the Contract Forms.\n"
			"Performance Security: PE guidance only.\n"
			"Notes to Tenderers on working with the Sample Contractual Forms\n"
			"1. Notification of Intention to Award"
		)
		cleaned = strip_pe_only_contract_form_notes(raw)
		self.assertNotIn("Notes to the Procuring Entity", cleaned)
		self.assertIn("Notes to Tenderers", cleaned)
		self.assertIn("Notification of Intention", cleaned)
