# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared preview/publication seed helpers (not Desk entrypoints)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_configurations.constants import STATUS_APPROVED_FOR_PREVIEW
from kentender_procurement.tender_configurations.seed.lean_preliminary_criteria import (
	lean_preliminary_criteria_rows,
)
from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
	FIXTURE_FULL as TP_FIXTURE_FULL,
	merge_technical_proposal_into_evaluation,
)
from kentender_procurement.tender_configurations.seed.lean_qualification_criteria import (
	FIXTURE_FULL,
	merge_qualification_into_evaluation,
)

def _approve(cfg_id: str):
	doc = frappe.get_doc("Tender Configuration", cfg_id)
	doc.status = STATUS_APPROVED_FOR_PREVIEW
	doc.review_workspace = json.dumps(
		{"approved_at": "2026-07-19 11:00:00", "approved_by": "Administrator", "checklist": []}
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def _seed_bidder_facing_config(cfg_id: str):
	"""Populate CFG blobs so required preview sections can render legally."""
	doc = frappe.get_doc("Tender Configuration", cfg_id)
	doc.tds_values = json.dumps(
		{
			"contact_officer": "Jane Doe",
			"contact_email": "procurement@example.go.ke",
			"clarification_submission_method": "E-Procurement Portal",
			"clarification_deadline": "2026-08-30T15:30",
			"pre_tender_meeting": "No",
			"tender_submission_deadline": "2026-09-15T17:00",
			"tender_opening_datetime": "2026-09-15T17:30",
			"bid_validity_period": "120",
			"bid_validity_unit": "days",
			"submission_channel": "E-Procurement Portal",
			"submission_language": "English",
			"tender_currency": "KES",
			"tender_security_required": "Yes",
			"tender_security_type": "Tender Security",
			"tender_security_amount": "50000",
			"tender_security_currency": "KES",
			"tender_security_validity_period": "14",
			"tender_security_validity_unit": "days",
			"margin_of_preference_applies": "No",
			"opening_method": "Electronic Opening",
			"opening_location": "KenTender portal",
			"opening_attendance_allowed": "Yes",
		}
	)
	doc.it_requirements = json.dumps(
		[
			{
				"requirement_id": "REQ-001",
				"title": "Helpdesk Service Continuity",
				"description": "Support continuous helpdesk operations with defined SLAs.",
				"category_label": "Business Objective",
				"treatment_label": "Mandatory",
			},
			{
				"requirement_id": "REQ-002",
				"title": "Compute Node Performance",
				"description": "Compute nodes must meet the stated processor and memory requirements.",
				"category_label": "Technical Requirement",
				"treatment_label": "Mandatory",
			},
		]
	)
	doc.evaluation_setup = json.dumps(
		merge_technical_proposal_into_evaluation(
			merge_qualification_into_evaluation(
				{
					"criteria": lean_preliminary_criteria_rows()
					+ [
						{
							"criterion_name": "Technical compliance for: REQ-002",
							"stage": "Technical",
							"evaluation_basis": "Scored",
							"marks": "50",
							"related_requirement_id": "REQ-002",
							"bidder_evidence": "Required",
						},
					]
				},
				fixture=FIXTURE_FULL,
			),
			fixture=TP_FIXTURE_FULL,
		)
	)
	doc.price_schedule = json.dumps(
		{
			"items": [
				{
					"item_name": "Price for requirement: REQ-002",
					"related_requirement_id": "REQ-002",
					"bidder_facing_description": (
						"Supply, install, and commission compute nodes meeting the "
						"specified performance requirement."
					),
					"unit": "Lot",
					"quantity": "1",
					"currency": "KES",
				}
			]
		}
	)
	doc.contract_values = json.dumps(
		{
			"contract_values": [
				{
					"contract_value_id": "SCC-01",
					"item_label": "Governing law",
					"value_or_obligation": "Governing law: Laws of Kenya",
				},
				{
					"contract_value_id": "SCC-02",
					"item_label": "Scope",
					"value_or_obligation": "Scope: All modules in Part 2",
				},
				{
					"contract_value_id": "SCC-03",
					"item_label": "Commencement",
					"value_or_obligation": (
						"Commencement within 14 days; 24 month implementation period"
					),
				},
				{
					"contract_value_id": "SCC-04",
					"item_label": "Payment",
					"value_or_obligation": "Milestone payment schedule as agreed",
				},
				{
					"contract_value_id": "SCC-05",
					"item_label": "Source code / escrow",
					"value_or_obligation": "Source code escrow within 30 days",
				},
				{
					"contract_value_id": "SCC-06",
					"item_label": "Subcontracting",
					"value_or_obligation": "Subcontracting requires prior written approval",
				},
				{
					"contract_value_id": "SCC-07",
					"item_label": "SLA",
					"value_or_obligation": "P1 response 4 hours / resolution 24 hours",
				},
				{
					"contract_value_id": "SCC-08",
					"item_label": "Performance security",
					"value_or_obligation": "10% performance security of Contract Price",
				},
				{
					"contract_value_id": "SCC-09",
					"item_label": "Warranty",
					"value_or_obligation": "Twelve-month warranty after go-live",
				},
			]
		}
	)
	doc.system_inventory = json.dumps({"not_applicable": 1, "items": []})
	doc.forms_and_evidence = json.dumps(
		{
			"forms": [
				{
					"form_id": "FE-001",
					"title": "Tender Security Form",
					"required": 1,
				}
			]
		}
	)
	doc.bidder_submission_schema = json.dumps(
		{"version": 1, "sections": [{"id": "eligibility", "title": "Eligibility"}]}
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


