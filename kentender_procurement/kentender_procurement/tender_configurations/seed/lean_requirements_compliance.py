# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean Requirements Compliance fixtures (pack 10 — PE-neutral, no NSSF hard-coding)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SECTION_KEY = "requirements_compliance"

FIXTURE_STANDARD = "standard"
FIXTURE_CONDITIONAL = "conditional"
FIXTURE_AMENDED = "amended"

MODE_REQUIRED = "required"
MODE_OPTIONAL = "optional"
MODE_CONDITIONAL = "conditional"
MODE_INFORMATIONAL = "informational"
MODE_EXCLUDED = "excluded"

SCOPE_TENDER = "tender"
SCOPE_LOT = "lot"

CONDITION_ALWAYS = "always"
CONDITION_ALT_PERMITTED = "technical_alternatives_permitted"
CONDITION_LOT_SELECTED = "lot_topic_selected"

RENDERER_ACK = "acknowledgement"
RENDERER_YES_NO = "yes_no"
RENDERER_NUMBER = "number"
RENDERER_NARRATIVE = "narrative"
RENDERER_TABLE = "repeating_table"
RENDERER_EVIDENCE = "evidence"
RENDERER_COMBINED = "combined"


def _req(
	rid: str,
	*,
	ref: str,
	title: str,
	statement: str,
	group: str,
	mode: str = MODE_REQUIRED,
	renderer: str = RENDERER_COMBINED,
	order: int = 10,
	scope: str = SCOPE_TENDER,
	condition_key: str = CONDITION_ALWAYS,
	explanation_required: bool = True,
	evidence_required: bool = False,
	alt_permitted: bool = False,
	revision: int = 1,
	change_summary: str = "",
	addendum_number: str = "",
	withdrawn: bool = False,
	response_fields: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	fields = response_fields
	if fields is None:
		fields = _default_fields_for_renderer(
			renderer,
			explanation_required=explanation_required,
			evidence_required=evidence_required,
		)
	return {
		"requirement_id": rid,
		"tender_facing_reference": ref,
		"title": title,
		"requirement_title": title,
		"description": statement,
		"requirement_statement": statement,
		"category_label": group,
		"group": group,
		"display_order": order,
		"requirement_mode": mode,
		"mandatory": 1 if mode == MODE_REQUIRED else 0,
		"renderer": renderer,
		"scope": scope,
		"condition_key": condition_key,
		"explanation_required": 1 if explanation_required else 0,
		"evidence_required": 1 if evidence_required else 0,
		"technical_alternative_permitted": 1 if alt_permitted else 0,
		"published_revision": revision,
		"bidder_facing_change_summary": change_summary,
		"updated_by_addendum": addendum_number,
		"withdrawn": 1 if withdrawn else 0,
		"response_fields": fields,
		"bidder_response_type": (
			"compliance_statement_plus_evidence_upload" if evidence_required else "yes_no_plus_compliance_statement"
		),
	}


def _default_fields_for_renderer(
	renderer: str,
	*,
	explanation_required: bool,
	evidence_required: bool,
) -> list[dict[str, Any]]:
	if renderer == RENDERER_ACK:
		return [
			{
				"field_key": "acknowledged",
				"label": "I have read and understood this requirement",
				"type": "boolean",
				"required": True,
				"help_text": "Informational requirements do not need a detailed response — confirm you have reviewed the statement.",
			}
		]
	if renderer == RENDERER_YES_NO:
		fields = [
			{
				"field_key": "compliant_yes_no",
				"label": "Does your offer meet this requirement?",
				"type": "text",
				"required": True,
				"control": "yes_no",
			}
		]
		if explanation_required:
			fields.append(
				{
					"field_key": "compliance_statement",
					"label": "Explanation",
					"type": "narrative",
					"required": True,
					"help_text": "Briefly explain how you meet this requirement.",
				}
			)
		return fields
	if renderer == RENDERER_NUMBER:
		fields = [
			{
				"field_key": "numeric_value",
				"label": "Numeric value",
				"type": "number",
				"required": True,
				"help_text": "Enter a number. Zero is a valid response.",
			}
		]
		if explanation_required:
			fields.append(
				{
					"field_key": "compliance_statement",
					"label": "Explanation",
					"type": "narrative",
					"required": True,
					"help_text": "Briefly explain how you meet this requirement.",
				}
			)
		if evidence_required:
			fields.append(
				{
					"field_key": "evidence_uploads",
					"label": "Supporting evidence",
					"type": "file",
					"required": True,
					"help_text": "Link one or more supporting files from your evidence register.",
				}
			)
		return fields
	if renderer == RENDERER_NARRATIVE:
		return [
			{
				"field_key": "compliance_statement",
				"label": "Your response",
				"type": "narrative",
				"required": True,
				"help_text": "Describe how your offer addresses this requirement.",
			}
		]
	if renderer == RENDERER_TABLE:
		return [
			{
				"field_key": "schedule_rows",
				"label": "Integration activities",
				"type": "repeating_table",
				"required": True,
				"min_rows": 1,
				"help_text": "Add one row for each planned integration activity and when it will occur.",
				"columns": [
					{"key": "activity", "label": "Activity"},
					{"key": "timing", "label": "Timing"},
				],
			}
		]
	if renderer == RENDERER_EVIDENCE:
		return [
			{
				"field_key": "evidence_uploads",
				"label": "Supporting evidence",
				"type": "file",
				"required": True,
				"help_text": "Link one or more supporting files from your evidence register.",
			}
		]
	# combined
	fields = [
		{
			"field_key": "compliant_yes_no",
			"label": "Does your offer meet this requirement?",
			"type": "text",
			"required": True,
			"control": "yes_no",
		},
		{
			"field_key": "compliance_statement",
			"label": "Explanation",
			"type": "narrative",
			"required": bool(explanation_required),
			"help_text": "Briefly explain how you meet this requirement.",
		},
	]
	if evidence_required:
		fields.append(
			{
				"field_key": "evidence_uploads",
				"label": "Supporting evidence",
				"type": "file",
				"required": True,
				"help_text": "Link one or more supporting files from your evidence register.",
			}
		)
	return fields


def _standard_rows() -> list[dict[str, Any]]:
	return [
		_req(
			"rc-cap-001",
			ref="CAP-01",
			title="Concurrent user capacity",
			statement="State the supported concurrent user capacity for the proposed system.",
			group="System Capacity",
			renderer=RENDERER_NUMBER,
			order=10,
			evidence_required=True,
			response_fields=[
				{
					"field_key": "numeric_value",
					"label": "Supported concurrent users",
					"type": "number",
					"required": True,
					"help_text": "Enter the maximum concurrent users your solution will support. Zero is allowed.",
				},
				{
					"field_key": "compliance_statement",
					"label": "Explanation",
					"type": "narrative",
					"required": True,
					"help_text": "Briefly explain how you meet this capacity requirement.",
				},
				{
					"field_key": "evidence_uploads",
					"label": "Supporting evidence",
					"type": "file",
					"required": True,
					"help_text": "Link sizing or architecture evidence from your evidence register.",
				},
			],
		),
		_req(
			"rc-cap-002",
			ref="CAP-02",
			title="Peak transaction throughput",
			statement="Describe peak transaction throughput the solution will sustain.",
			group="System Capacity",
			renderer=RENDERER_NARRATIVE,
			order=20,
		),
		_req(
			"rc-sec-001",
			ref="SEC-01",
			title="Role-based access control",
			statement="Confirm role-based access control is provided and explain the model.",
			group="Security",
			renderer=RENDERER_COMBINED,
			order=30,
			evidence_required=True,
		),
		_req(
			"rc-sec-002",
			ref="SEC-02",
			title="Encryption in transit",
			statement="TLS 1.2 or later must be used for all external interfaces.",
			group="Security",
			mode=MODE_INFORMATIONAL,
			renderer=RENDERER_ACK,
			order=40,
			explanation_required=False,
		),
		_req(
			"rc-int-001",
			ref="INT-01",
			title="Integration schedule",
			statement="Provide the planned integration activities and timing.",
			group="Integration",
			renderer=RENDERER_TABLE,
			order=50,
		),
		_req(
			"rc-sup-001",
			ref="SUP-01",
			title="Optional extended support window",
			statement="Offer an optional extended support window beyond the base warranty.",
			group="Support",
			mode=MODE_OPTIONAL,
			renderer=RENDERER_YES_NO,
			order=60,
			explanation_required=True,
		),
	]


def _conditional_rows() -> list[dict[str, Any]]:
	rows = [
		_req(
			"rc-core-001",
			ref="CORE-01",
			title="Base platform confirmation",
			statement="Confirm the proposed platform meets the published base requirements.",
			group="Core Platform",
			renderer=RENDERER_COMBINED,
			order=10,
			evidence_required=True,
		),
		_req(
			"rc-lot-a-001",
			ref="LOT-A-01",
			title="Lot A delivery approach",
			statement="Describe delivery for Lot A only.",
			group="Lot-specific",
			renderer=RENDERER_NARRATIVE,
			order=20,
			scope=SCOPE_LOT,
			condition_key=CONDITION_LOT_SELECTED,
		),
		_req(
			"rc-lot-shared-001",
			ref="LOT-S-01",
			title="Shared multi-lot coordination",
			statement="Describe coordination across selected lots (shared response).",
			group="Lot-specific",
			renderer=RENDERER_NARRATIVE,
			order=30,
			scope=SCOPE_TENDER,
		),
		_req(
			"rc-alt-001",
			ref="ALT-01",
			title="Permitted storage alternative",
			statement="Respond to the base storage requirement. A technical alternative may be linked.",
			group="Alternatives",
			mode=MODE_CONDITIONAL,
			renderer=RENDERER_COMBINED,
			order=40,
			condition_key=CONDITION_ALT_PERMITTED,
			alt_permitted=True,
			evidence_required=True,
		),
		_req(
			"rc-info-001",
			ref="INFO-01",
			title="Published interface catalogue",
			statement="The procuring entity will publish the interface catalogue with the tender pack.",
			group="Core Platform",
			mode=MODE_INFORMATIONAL,
			renderer=RENDERER_ACK,
			order=50,
			explanation_required=False,
		),
	]
	return rows


def _amended_rows() -> list[dict[str, Any]]:
	return [
		_req(
			"rc-amd-unchanged",
			ref="AMD-01",
			title="Unchanged availability target",
			statement="The solution must achieve 99.5% monthly availability.",
			group="Service Levels",
			renderer=RENDERER_COMBINED,
			order=10,
			revision=1,
		),
		_req(
			"rc-amd-changed",
			ref="AMD-02",
			title="Changed recovery time objective",
			statement="Recovery time objective must not exceed four hours (updated).",
			group="Service Levels",
			renderer=RENDERER_COMBINED,
			order=20,
			revision=2,
			change_summary="RTO tightened from eight hours to four hours.",
			addendum_number="2",
			evidence_required=True,
		),
		_req(
			"rc-amd-new",
			ref="AMD-03",
			title="Newly introduced backup frequency",
			statement="Provide daily encrypted backups with off-site retention of thirty days.",
			group="Service Levels",
			renderer=RENDERER_NARRATIVE,
			order=30,
			revision=1,
			addendum_number="2",
			change_summary="New requirement introduced by Addendum 2.",
		),
		_req(
			"rc-amd-withdrawn",
			ref="AMD-04",
			title="Withdrawn on-premise hosting option",
			statement="On-premise hosting is no longer required.",
			group="Service Levels",
			mode=MODE_EXCLUDED,
			renderer=RENDERER_YES_NO,
			order=40,
			withdrawn=True,
			addendum_number="2",
			change_summary="Requirement withdrawn by Addendum 2.",
		),
	]


def cstr_fixture(fixture: str | None) -> str:
	raw = (fixture or FIXTURE_STANDARD).strip().lower()
	if raw in ("standard", "full", "core"):
		return FIXTURE_STANDARD if raw != "full" else FIXTURE_STANDARD
	if raw in (FIXTURE_STANDARD, FIXTURE_CONDITIONAL, FIXTURE_AMENDED):
		return raw
	if raw in ("lots", "conditional_lots"):
		return FIXTURE_CONDITIONAL
	if raw in ("addendum", "amended_requirements"):
		return FIXTURE_AMENDED
	return FIXTURE_STANDARD


def lean_requirements_compliance_rows(fixture: str = FIXTURE_STANDARD) -> list[dict[str, Any]]:
	key = cstr_fixture(fixture)
	if key == FIXTURE_CONDITIONAL:
		return deepcopy(_conditional_rows())
	if key == FIXTURE_AMENDED:
		return deepcopy(_amended_rows())
	return deepcopy(_standard_rows())


def merge_requirements_compliance_into_evaluation(
	evaluation: dict[str, Any] | None,
	*,
	fixture: str = FIXTURE_STANDARD,
	flags: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Attach lean RC rows + flags for materialize into electronic template."""
	out = dict(evaluation) if isinstance(evaluation, dict) else {}
	rows = lean_requirements_compliance_rows(fixture)
	out["requirements_compliance_rows"] = rows
	out["requirements_compliance_fixture"] = cstr_fixture(fixture)
	base_flags = {
		"technical_alternatives_permitted": 0,
		"lot_topic_selected": 0,
		"selected_lots": [],
	}
	if cstr_fixture(fixture) == FIXTURE_CONDITIONAL:
		base_flags["technical_alternatives_permitted"] = 1
		base_flags["lot_topic_selected"] = 1
		base_flags["selected_lots"] = ["LOT-A"]
	if isinstance(flags, dict):
		base_flags.update(flags)
	out["requirements_compliance_flags"] = base_flags
	return out


def lean_requirements_as_it_requirements(fixture: str = FIXTURE_STANDARD) -> list[dict[str, Any]]:
	"""Shape suitable for Tender Configuration.it_requirements JSON field."""
	out: list[dict[str, Any]] = []
	for row in lean_requirements_compliance_rows(fixture):
		out.append(
			{
				"requirement_id": row["requirement_id"],
				"title": row["title"],
				"description": row["requirement_statement"],
				"category_label": row["category_label"],
				"treatment_label": (row["requirement_mode"] or MODE_REQUIRED).title(),
				"requirement_mode": row["requirement_mode"],
				"renderer": row["renderer"],
				"scope": row["scope"],
				"condition_key": row["condition_key"],
				"evidence_required": row["evidence_required"],
				"explanation_required": row["explanation_required"],
				"technical_alternative_permitted": row["technical_alternative_permitted"],
				"published_revision": row["published_revision"],
				"bidder_facing_change_summary": row["bidder_facing_change_summary"],
				"updated_by_addendum": row["updated_by_addendum"],
				"withdrawn": row["withdrawn"],
				"tender_facing_reference": row["tender_facing_reference"],
				"display_order": row["display_order"],
				"response_fields": row["response_fields"],
				"bidder_response_type": row["bidder_response_type"],
				"mandatory": row["mandatory"],
			}
		)
	return out


def publish_lean_requirements_compliance_for_tests(
	*,
	fixture: str = FIXTURE_STANDARD,
	clear: bool = True,
	flags: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Seed ui00 + lean RC fixture + publish for Playwright / integration smoke."""
	import json

	import frappe
	from frappe.utils import add_to_date, cstr, now_datetime

	from kentender_procurement.tender_configurations.constants import CANONICAL_PACKAGE_ID
	from kentender_procurement.tender_configurations.seed.preview_fixtures import (
		_approve,
		_seed_bidder_facing_config,
	)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
		generate_document_preview,
	)
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender_for_development_preview,
		save_publication_setup,
	)

	seed = seed_ui00_dashboard(clear=clear)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Lean requirements compliance publish for tests.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "evaluation_setup")
	try:
		ev = json.loads(raw) if raw else {}
	except Exception:
		ev = {}
	if not isinstance(ev, dict):
		ev = {}
	merged = merge_requirements_compliance_into_evaluation(ev, fixture=fixture, flags=flags)
	it_reqs = lean_requirements_as_it_requirements(fixture)
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"evaluation_setup": json.dumps(merged),
			"it_requirements": json.dumps(it_reqs),
		},
	)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	if cstr(gen.get("preview_status")) != "Generated":
		frappe.throw(
			frappe._("RC lean preview failed: {0}").format(gen.get("render_exception")),
			title="RC_LEAN_SEED_PREVIEW",
		)
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Requirements compliance lean notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
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
		"configuration_id": cfg_id,
		"publication_id": pub_id,
		"publication_ref": pub_ref,
		"fixture": cstr_fixture(fixture),
		"portal_workspace_url": f"/tenders/{pub_ref}/workspace",
		"portal_rc_url": f"/tenders/{pub_ref}/sections/requirements_compliance",
	}
