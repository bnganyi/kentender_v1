# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PE-neutral Qualification category fixtures for lean seeds (not NSSF-specific)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

FIXTURE_FULL = "full"
FIXTURE_REDUCED = "reduced"
FIXTURE_CONDITIONAL = "conditional"

CATEGORY_CONTRACT = "contract_performance_and_litigation"
CATEGORY_FINANCIAL = "financial_capability"
CATEGORY_EXPERIENCE = "experience"
CATEGORY_PERSONNEL = "key_personnel"
CATEGORY_PARTNERS = "delivery_partners"

MODE_REQUIRED = "required"
MODE_OPTIONAL = "optional"
MODE_CONDITIONAL = "conditional"
MODE_EXCLUDED = "excluded"

SCOPE_TENDER = "tender"
SCOPE_LOT = "lot"
SCOPE_JV_MEMBER = "jv_member"

CONDITION_ALWAYS = "always"
CONDITION_KEY_POSITIONS = "key_positions_configured"
CONDITION_PARTNERS = "delivery_partners_configured"
CONDITION_EXTERNAL = "external_provider_selected"
CONDITION_JV = "bidder_is_joint_venture"


def _base_categories() -> list[dict[str, Any]]:
	"""Canonical five categories with PE-neutral IT STD thresholds."""
	return [
		{
			"category_key": CATEGORY_CONTRACT,
			"label": "Contract performance and litigation",
			"renderer": "contract_performance_litigation",
			"display_order": 10,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"requirement_summary": "Provide contract-performance and litigation history",
			"scope": SCOPE_JV_MEMBER,
			"criteria": [
				{
					"criterion_id": "con-non-performance",
					"title": "Historical contract non-performance",
					"required": True,
				},
				{
					"criterion_id": "con-pending-litigation",
					"title": "Pending litigation",
					"required": True,
				},
				{
					"criterion_id": "con-litigation-history",
					"title": "Litigation history",
					"required": True,
				},
			],
		},
		{
			"category_key": CATEGORY_FINANCIAL,
			"label": "Financial capability",
			"renderer": "financial_capability",
			"display_order": 20,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"requirement_summary": "Provide financial statements, turnover and available resources",
			"scope": SCOPE_TENDER,
			"criteria": [
				{
					"criterion_id": "fin-statements",
					"title": "Audited financial statements",
					"required": True,
					"min_years": 3,
				},
				{
					"criterion_id": "fin-turnover",
					"title": "Average annual turnover",
					"required": True,
					"min_amount": 10000000,
					"currency": "KES",
				},
				{
					"criterion_id": "fin-resources",
					"title": "Available financial resources",
					"required": True,
				},
			],
		},
		{
			"category_key": CATEGORY_EXPERIENCE,
			"label": "Experience",
			"renderer": "experience",
			"display_order": 30,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"requirement_summary": "Provide general and similar-contract experience",
			"scope": SCOPE_TENDER,
			"criteria": [
				{
					"criterion_id": "exp-general",
					"title": "General experience",
					"required": True,
					"min_qualifying_years": 5,
					"min_months_in_year": 9,
				},
				{
					"criterion_id": "exp-specific",
					"title": "Specific experience",
					"required": True,
					"min_projects": 2,
				},
			],
		},
		{
			"category_key": CATEGORY_PERSONNEL,
			"label": "Key personnel",
			"renderer": "key_personnel",
			"display_order": 40,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_KEY_POSITIONS,
			"requirement_summary": "Assign personnel to required positions",
			"scope": SCOPE_TENDER,
			"allow_duplicate_personnel": False,
			"positions": [
				{
					"position_id": "pos-project-manager",
					"title": "Project Manager",
					"qualification_summary": "Degree and at least 8 years of relevant project management experience.",
					"required": True,
				},
				{
					"position_id": "pos-lead-developer",
					"title": "Lead Developer",
					"qualification_summary": "Degree and at least 5 years of enterprise systems delivery experience.",
					"required": True,
				},
				{
					"position_id": "pos-business-analyst",
					"title": "Business Analyst",
					"qualification_summary": "At least 4 years of requirements and change analysis experience.",
					"required": True,
				},
			],
			"criteria": [],
		},
		{
			"category_key": CATEGORY_PARTNERS,
			"label": "Delivery partners",
			"renderer": "delivery_partners",
			"display_order": 50,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_PARTNERS,
			"requirement_summary": "Provide required subcontractor, vendor or manufacturer information",
			"scope": SCOPE_LOT,
			"items": [
				{
					"item_id": "dp-core-erp",
					"title": "Core application software licence and support",
					"item_kind": "goods",
					"lot_id": "",
					"required": True,
					"criteria": [
						{
							"criterion_id": "dp-auth",
							"title": "Manufacturer authorisation for this tender",
							"required": True,
							"tender_specific": True,
						},
						{
							"criterion_id": "dp-support",
							"title": "Local support capability statement",
							"required": True,
							"tender_specific": False,
						},
					],
				},
				{
					"item_id": "dp-integration",
					"title": "Integration services",
					"item_kind": "services",
					"lot_id": "",
					"required": True,
					"criteria": [
						{
							"criterion_id": "dp-sub-agreement",
							"title": "Subcontractor agreement for this tender",
							"required": True,
							"tender_specific": True,
						},
					],
				},
			],
			"criteria": [],
		},
	]


def lean_qualification_categories(fixture: str = FIXTURE_FULL) -> list[dict[str, Any]]:
	"""Return category configuration for the named fixture (full / reduced / conditional)."""
	cats = deepcopy(_base_categories())
	key = cstr_fixture(fixture)
	if key == FIXTURE_REDUCED:
		for cat in cats:
			ck = cat["category_key"]
			if ck in (CATEGORY_FINANCIAL, CATEGORY_EXPERIENCE):
				cat["requirement_mode"] = MODE_REQUIRED
				cat["condition_key"] = CONDITION_ALWAYS
			else:
				cat["requirement_mode"] = MODE_EXCLUDED
				cat["condition_key"] = CONDITION_ALWAYS
		return cats
	if key == FIXTURE_CONDITIONAL:
		for cat in cats:
			ck = cat["category_key"]
			if ck == CATEGORY_PERSONNEL:
				cat["requirement_mode"] = MODE_OPTIONAL
				cat["condition_key"] = CONDITION_KEY_POSITIONS
			elif ck == CATEGORY_PARTNERS:
				cat["requirement_mode"] = MODE_CONDITIONAL
				cat["condition_key"] = CONDITION_EXTERNAL
			elif ck in (CATEGORY_CONTRACT, CATEGORY_FINANCIAL, CATEGORY_EXPERIENCE):
				cat["requirement_mode"] = MODE_REQUIRED
				cat["condition_key"] = CONDITION_ALWAYS
		return cats
	# full
	return cats


def cstr_fixture(fixture: str | None) -> str:
	raw = (fixture or FIXTURE_FULL).strip().lower()
	if raw in (FIXTURE_FULL, FIXTURE_REDUCED, FIXTURE_CONDITIONAL):
		return raw
	return FIXTURE_FULL


def lean_qualification_stage_rows(fixture: str = FIXTURE_FULL) -> list[dict[str, Any]]:
	"""Flat stage=Qualification rows for calibration counts (not NSSF labels)."""
	rows: list[dict[str, Any]] = []
	order = 100
	for cat in lean_qualification_categories(fixture):
		if cat.get("requirement_mode") == MODE_EXCLUDED:
			continue
		for crit in cat.get("criteria") or []:
			if not isinstance(crit, dict):
				continue
			rows.append(
				{
					"criterion_id": crit.get("criterion_id"),
					"criterion_name": crit.get("title") or cat.get("label"),
					"stage": "Qualification",
					"evaluation_basis": "Pass/Fail",
					"mandatory": bool(crit.get("required", True)),
					"display_order": order,
					"category_key": cat.get("category_key"),
				}
			)
			order += 10
		for pos in cat.get("positions") or []:
			if not isinstance(pos, dict):
				continue
			rows.append(
				{
					"criterion_id": pos.get("position_id"),
					"criterion_name": pos.get("title"),
					"stage": "Qualification",
					"evaluation_basis": "Pass/Fail",
					"mandatory": bool(pos.get("required", True)),
					"display_order": order,
					"category_key": cat.get("category_key"),
				}
			)
			order += 10
		for item in cat.get("items") or []:
			if not isinstance(item, dict):
				continue
			rows.append(
				{
					"criterion_id": item.get("item_id"),
					"criterion_name": item.get("title"),
					"stage": "Qualification",
					"evaluation_basis": "Pass/Fail",
					"mandatory": bool(item.get("required", True)),
					"display_order": order,
					"category_key": cat.get("category_key"),
				}
			)
			order += 10
	return rows


def merge_qualification_into_evaluation(
	evaluation: dict[str, Any] | None,
	*,
	fixture: str = FIXTURE_FULL,
) -> dict[str, Any]:
	"""Attach qualification_categories and merge Qualification-stage criteria into evaluation_setup."""
	out = dict(evaluation) if isinstance(evaluation, dict) else {}
	existing = out.get("criteria") if isinstance(out.get("criteria"), list) else []
	kept = [
		r
		for r in existing
		if isinstance(r, dict) and (r.get("stage") or "") != "Qualification"
	]
	out["criteria"] = kept + lean_qualification_stage_rows(fixture)
	out["qualification_categories"] = lean_qualification_categories(fixture)
	out["qualification_fixture"] = cstr_fixture(fixture)
	return out
