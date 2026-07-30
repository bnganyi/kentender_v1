# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Small synthetic IT tender that reuses PPRA-IT-STD v1 without NSSF constants."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_to_date, cstr, now_datetime, nowdate

from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
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
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_all_complete,
)

SEED_PREFIX = "TCFG-LEAN-IT"
PACKAGE_CODE = f"{SEED_PREFIX}-PKG"
CONFIG_REF = f"{SEED_PREFIX}-DEMO"
PE_CODE = f"{SEED_PREFIX}-PE"


def _clear() -> None:
	for bid in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", bid, force=True, ignore_permissions=True)
	for pub in frappe.get_all(
		"IT Tender Publication Record",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	):
		frappe.delete_doc("IT Tender Publication Record", pub, force=True, ignore_permissions=True)
	for pkg in frappe.get_all(
		"Confirmed Tender Document Package",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	):
		frappe.delete_doc(
			"Confirmed Tender Document Package", pkg, force=True, ignore_permissions=True
		)
	for name in frappe.get_all(
		"Tender Configuration",
		filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
		pluck="name",
	):
		frappe.delete_doc("Tender Configuration", name, force=True, ignore_permissions=True)
	if frappe.db.exists("Procurement Package", PACKAGE_CODE):
		frappe.delete_doc("Procurement Package", PACKAGE_CODE, force=True, ignore_permissions=True)


def seed_lean_synthetic_it_published(*, clear: bool = True) -> dict[str, Any]:
	"""Create a tiny IT tender, confirm package, publish with the same PPRA template."""
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)

	frappe.set_user("Administrator")
	if clear:
		_clear()

	ensure_active_canonical_ppra_it_std(force_reimport=False)
	if not frappe.db.exists("Procuring Entity", PE_CODE):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": PE_CODE,
				"entity_name": "Lean Demo Procuring Entity",
			}
		).insert(ignore_permissions=True, ignore_mandatory=True)

	title = "Lean Demo IT Services Tender"
	if not frappe.db.exists("Procurement Package", PACKAGE_CODE):
		pkg = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_code": PACKAGE_CODE,
				"package_name": title,
				"status": PKG_APPROVED,
				"procurement_method": "Open Tender",
				"contract_type": "Fixed Price",
				"procuring_entity_code": PE_CODE,
				"required_std_category": "Information Technology",
				"procurement_category": "Services",
				"currency": "KES",
				"is_active": 1,
				"approved_at": nowdate(),
			}
		)
		pkg.flags.ignore_validate = True
		pkg.insert(ignore_permissions=True, ignore_mandatory=True)
	else:
		frappe.db.set_value("Procurement Package", PACKAGE_CODE, {"status": PKG_APPROVED})

	if frappe.db.exists("Tender Configuration", CONFIG_REF):
		frappe.delete_doc("Tender Configuration", CONFIG_REF, force=True, ignore_permissions=True)

	cfg = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": CONFIG_REF,
			"tender_title": title,
			"status": STATUS_APPROVED_FOR_PREVIEW,
			"procurement_package": PACKAGE_CODE,
			"procurement_package_ref": PACKAGE_CODE,
			"package_title": title,
			"procuring_entity_name": "Lean Demo Procuring Entity",
			"procuring_entity_code": PE_CODE,
			"procurement_method": "Open Tender",
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": CANONICAL_PACKAGE_ID,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"short_scope_summary": "Supply and implement a lean demonstration IT service package.",
			"lot_structure": "Single lot",
			"configuration_note": "Synthetic lean IT fixture — no NSSF constants.",
			"blocker_count": 0,
			"warning_count": 0,
			"steps_state": steps_state_all_complete(),
			"approval_date": nowdate(),
			"tds_values": json.dumps(
				{
					"tender_currency": "KES",
					"bid_validity_period": "90",
					"bid_validity_unit": "days",
					"tender_security_required": "Yes",
					"tender_security_type": "Tender Security",
					"tender_security_amount": "10000",
					"tender_security_currency": "KES",
					"tender_security_validity_period": "28",
					"tender_security_validity_unit": "days",
					"submission_channel": "E-Procurement Portal",
					"alternatives_permitted": "No",
					"opening_method": "Electronic Opening",
					"pre_tender_meeting": "No",
					"margin_of_preference_applies": "No",
				}
			),
			"it_requirements": json.dumps(
				[
					{
						"requirement_id": "LEAN-REQ-001",
						"title": "Service desk availability",
						"description": "Provide business-hours service desk coverage.",
						"requirement_family": "General Requirements",
						"category_label": "Business Objective",
						"treatment_label": "Mandatory",
					},
					{
						"requirement_id": "LEAN-REQ-002",
						"title": "Secure hosting",
						"description": "Host the solution in an approved secure environment.",
						"requirement_family": "System Requirements",
						"category_label": "Technical Requirement",
						"treatment_label": "Mandatory",
					},
				]
			),
			"evaluation_setup": json.dumps(
				merge_technical_proposal_into_evaluation(
					merge_qualification_into_evaluation(
						{
							"technical_pass_mark": 70,
							"technical_scoring_total": 100,
							"criteria": lean_preliminary_criteria_rows()
							+ [
								{
									"criterion_name": "Relevant experience",
									"stage": "Technical",
									"evaluation_basis": "Pass/Fail",
								},
								{
									"criterion_name": "Technical approach",
									"stage": "Technical",
									"evaluation_basis": "Scored",
									"marks": "100",
								},
							],
						},
						fixture=FIXTURE_FULL,
					),
					fixture=TP_FIXTURE_FULL,
				)
			),
			"implementation_schedule": json.dumps(
				{
					"milestones": [
						{
							"milestone_id": "LEAN-MS-01",
							"name": "Kick-off",
							"sequence": "1",
						}
					]
				}
			),
			"price_schedule": json.dumps(
				{
					"items": [
						{
							"item_name": "Lean IT services lot",
							"unit": "Lot",
							"quantity": "1",
							"currency": "KES",
						}
					]
				}
			),
			"contract_values": json.dumps(
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
							"value_or_obligation": "Scope: Lean demo IT services",
						},
						{
							"contract_value_id": "SCC-03",
							"item_label": "Commencement",
							"value_or_obligation": "Commencement within 14 days",
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
			),
			"system_inventory": json.dumps({"not_applicable": 1, "items": []}),
			"forms_and_evidence": json.dumps(
				{
					"submission_items": [
						{
							"item_id": "FORM-LEAN-001",
							"title": "Lean demo form",
							"category": "Standard Form",
						}
					]
				}
			),
			"bidder_submission_schema": json.dumps(
				{
					"version": 1,
					"schema_hash": "lean-synthetic",
					"sections": [
						{"key": "form_of_tender", "title": "Form of Tender", "required": True}
					],
				}
			),
			"evaluation_schema": json.dumps({"version": 1, "criteria": []}),
			"price_schedule_schema": json.dumps({"version": 1, "items": []}),
			"forms_evidence_schema": json.dumps({"version": 1, "items": []}),
		}
	)
	cfg.insert(ignore_permissions=True)
	schema_blob = json.dumps(
		{
			"version": 1,
			"schema_hash": "lean-synthetic",
			"sections": [{"key": "form_of_tender", "title": "Form of Tender", "required": True}],
		}
	)
	frappe.db.set_value(
		"Tender Configuration",
		cfg.name,
		{"bidder_submission_schema": schema_blob},
		update_modified=False,
	)
	frappe.db.commit()
	cfg.reload()

	gen = generate_document_preview(cfg.name)
	if cstr(gen.get("preview_status")) != "Generated":
		frappe.throw(
			frappe._("Lean synthetic preview failed: {0}").format(gen.get("render_exception")),
			title="LEAN_SEED_PREVIEW",
		)
	conf = confirm_document_preview(cfg.name, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Lean synthetic IT tender notice.",
			"clarification_deadline": str(add_to_date(now, days=1)),
			"submission_deadline": str(add_to_date(now, days=10)),
			"opening_datetime": str(add_to_date(now, days=11)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	published = publish_tender_for_development_preview(pub_id)
	pub_ref = cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)
	return {
		"configuration_id": cfg.name,
		"configuration_ref": CONFIG_REF,
		"publication_id": pub_id,
		"publication_ref": pub_ref,
		"electronic_template_id": frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "electronic_template_id"
		),
		"electronic_template_hash": frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "electronic_template_hash"
		),
		"tender_title": title,
	}
