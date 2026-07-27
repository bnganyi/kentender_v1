# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PE-neutral Preliminary criteria rows for lean seeds (titles are configured text, not brand names)."""

from __future__ import annotations

from typing import Any


def lean_preliminary_criteria_rows() -> list[dict[str, Any]]:
	"""Seven criteria covering upload, select_or_upload+validity, JV N/A, and linked sections."""
	return [
		{
			"criterion_id": "prelim-business-registration",
			"criterion_name": "Business registration certificate",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Current registration evidence must be provided",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Upload a current certificate of incorporation or business registration."
			),
			"mandatory": True,
			"applicability": "always",
			"response_method": "upload",
			"accepted_file_types": [".pdf", ".png", ".jpg", ".jpeg"],
			"max_file_size_mb": 5,
			"display_order": 10,
			"criterion_group": "eligibility",
		},
		{
			"criterion_id": "prelim-tax-compliance",
			"criterion_name": "Tax compliance certificate",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Valid tax compliance evidence on the submission deadline",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Provide a tax compliance certificate that is valid on the tender submission deadline."
			),
			"mandatory": True,
			"applicability": "always",
			"response_method": "select_or_upload",
			"validity_rule": "valid_on_submission_deadline",
			"evidence_type": "tax_clearance",
			"accepted_file_types": [".pdf", ".png", ".jpg", ".jpeg"],
			"max_file_size_mb": 5,
			"display_order": 20,
			"criterion_group": "eligibility",
		},
		{
			"criterion_id": "prelim-product-authorisation",
			"criterion_name": "Product authorisation letter",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Manufacturer or authorised distributor letter required",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Upload a manufacturer authorisation or authorised distributor letter for the offered solution."
			),
			"mandatory": True,
			"applicability": "always",
			"response_method": "upload",
			"accepted_file_types": [".pdf"],
			"max_file_size_mb": 5,
			"display_order": 30,
			"criterion_group": "eligibility",
		},
		{
			"criterion_id": "prelim-jv-agreement",
			"criterion_name": "Joint Venture agreement",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Required when bidding as a joint venture",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Upload the executed Joint Venture agreement when bidding as a joint venture."
			),
			"mandatory": True,
			"applicability": "jv_only",
			"response_method": "upload",
			"accepted_file_types": [".pdf"],
			"max_file_size_mb": 10,
			"display_order": 40,
			"criterion_group": "eligibility",
		},
		{
			"criterion_id": "prelim-form-of-tender",
			"criterion_name": "Form of Tender",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Form of Tender must be completed and certified",
			"bidder_evidence": "Required",
			"evidence_instruction": "Complete and certify the Form of Tender in the bidder workspace.",
			"mandatory": True,
			"applicability": "always",
			"response_method": "linked_section",
			"linked_section_key": "form_of_tender",
			"display_order": 50,
			"criterion_group": "linked",
		},
		{
			"criterion_id": "prelim-statutory-declarations",
			"criterion_name": "Statutory Declarations",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Statutory declarations must be certified",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Complete and certify the Statutory Declarations in the bidder workspace."
			),
			"mandatory": True,
			"applicability": "always",
			"response_method": "linked_section",
			"linked_section_key": "statutory_declarations",
			"display_order": 60,
			"criterion_group": "linked",
		},
		{
			"criterion_id": "prelim-tender-security",
			"criterion_name": "Tender Security",
			"stage": "Preliminary",
			"evaluation_basis": "Pass/Fail",
			"pass_fail_rule": "Tender security or securing declaration must be provided when required",
			"bidder_evidence": "Required",
			"evidence_instruction": (
				"Provide the Tender Security or Tender-Securing Declaration required for this tender."
			),
			"mandatory": True,
			"applicability": "always",
			"response_method": "linked_section",
			"linked_section_key": "tender_security",
			"display_order": 70,
			"criterion_group": "linked",
		},
	]


def merge_lean_preliminary_into_evaluation(evaluation: dict[str, Any]) -> dict[str, Any]:
	"""Replace Preliminary-stage criteria with the lean PE-neutral set; keep other stages."""
	out = dict(evaluation or {})
	existing = out.get("criteria") if isinstance(out.get("criteria"), list) else []
	kept = [
		c
		for c in existing
		if isinstance(c, dict) and str(c.get("stage") or "").strip() != "Preliminary"
	]
	out["criteria"] = lean_preliminary_criteria_rows() + kept
	return out
