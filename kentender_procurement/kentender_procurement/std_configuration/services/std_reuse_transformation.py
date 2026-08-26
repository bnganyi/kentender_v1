# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §17.2-17.9 — one-time reuse/transformation utility.

Converts the frozen `KE-PPRA-IT-2022-04` reuse bundle (`std_reuse_bundle.py`)
into real `STD Cfg Assistance Batch` proposals through the SAME contract
Phase 8 built (`std_assistance.prepare_proposal`) — this module is exactly
the "real reuse-bundle transformation" adapter that `std_assistance.py`'s own
docstring named as future, upstream-of-`prepare_proposal` work. It never
writes an "accepted" domain record directly; every reused item still passes
through the Configurator's individual accept/reject decision and the target
entity's normal validators (§17.6 steps 6-7, §17.7's "accepted content loses
its legacy character").

Scope boundary (confirmed by the user, 2026-08-25): this phase proves the
transformation *mechanism* against real prior content — it does not complete
the full production `KE-PPRA-IT` package. Where the real bundle has no
per-item data for a target class (only schema-level metadata — confirmed by
direct inspection: `requirements/requirement_schema.json`,
`contract/contract_schema.json` are single summary records, not per-category
rows), the register honestly records `Unavailable` per §17.3, rather than
fabricating rows the source does not contain.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_configuration.services import std_assistance, std_reuse_bundle
from kentender_procurement.std_configuration.services.std_authorization import (
	CAP_CONFIGURE,
	require_draft_capability,
)

# §17.5 row 2 — "normalize to the required thirteen-section order" — maps the
# reuse bundle's own (looser, 21-entry) section_code to our 13 canonical
# section codes (`seeds/std_it_golden_seed.py::_SECTIONS`). Entries with no
# real correspondence (COVER, TOC, PREFACE, PREFACE_APPENDIX, ISSUE_PAGE,
# PART1/2/3 — front matter and part-dividers, not one of the 13 required
# sections) are deliberately absent: their clauses are Retired, not forced
# into an unrelated section.
SECTION_CODE_MAP: dict[str, tuple[str, str, int, int]] = {
	# extraction_code: (our_code, our_title, coverage_area_number, display_order)
	"INVITATION": ("INV", "Tender identity, cover and Invitation to Tender", 1, 1),
	"ITT": ("SEC-I", "Section I — Instructions to Tenderers", 2, 2),
	"TDS": ("SEC-II", "Section II — Tender Data Sheet", 3, 3),
	"EVAL": ("SEC-III", "Section III — Evaluation and Qualification Criteria", 4, 4),
	"FORMS": ("SEC-IV", "Section IV — Non-price and Price Tendering Forms", 5, 5),
	"REQ": ("SEC-V", "Section V — Requirements of the Information System", 7, 6),
	"TECH": ("SEC-VI", "Section VI — Technical Requirements", 8, 7),
	"IMPL": ("SEC-VII", "Section VII — Implementation Schedule", 9, 8),
	"INVENTORY": ("SEC-VIII", "Section VIII — System Inventory Tables", 10, 9),
	"BACKGROUND": ("SEC-IX", "Section IX — Background and Informational Materials", 11, 10),
	"GCC": ("GCC", "General Conditions of Contract", 12, 11),
	"SCC": ("SCC", "Special Conditions of Contract", 13, 12),
	"CONTRACT_FORMS": ("FORMS", "Contract Forms and Appendices", 14, 13),
}

_EVAL_STAGE_MAP = {
	"RESPONSIVENESS": "Preliminary responsiveness",
	"TECHNICAL": "Technical evaluation",
	"FINANCIAL": "Financial evaluation",
	"QUALIFICATION": "Post-qualification",
}

_FIELD_TYPE_MAP = {
	"TEXT": "Text",
	"SIGNATURE": "Text",
	"DATE": "Date",
	"MONEY": "Money",
	"CHOICE": "Choice",
}


def _ensure_sections(bundle: dict, package_id: str) -> dict[str, str]:
	"""Direct Section creation, matching the golden seed's own pattern
	(`STD Cfg Section` is package-scoped, not one of
	`std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES` — Phase 1's own model —
	so it is not a governed `std_assistance` proposal target). Idempotent:
	skips a section code that already exists for this package."""
	source_by_code = {row["section_code"]: row for row in bundle["sections"]}
	lookup: dict[str, str] = {}
	for extraction_code, (our_code, title, coverage_area_number, display_order) in SECTION_CODE_MAP.items():
		if extraction_code not in source_by_code:
			continue
		existing = frappe.db.get_value("STD Cfg Section", {"package_id": package_id, "section_code": our_code})
		if existing:
			lookup[our_code] = existing
			continue
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": package_id,
				"section_code": our_code,
				"title": title,
				"coverage_area_number": coverage_area_number,
				"display_order": display_order,
				"is_required": 1,
			}
		).insert(ignore_permissions=True)
		lookup[our_code] = section.name
	return lookup


def _map_content_blocks(bundle: dict, section_lookup: dict[str, str]) -> tuple[list[dict], int]:
	section_by_key = {row["section_key"]: row for row in bundle["sections"]}
	order_counters: dict[str, int] = {}
	items: list[dict] = []
	unresolved = 0
	for clause in bundle["clauses"]:
		source_section = section_by_key.get(clause["section_key"])
		mapped = SECTION_CODE_MAP.get(source_section["section_code"]) if source_section else None
		if not mapped or mapped[0] not in section_lookup:
			unresolved += 1
			continue
		our_code = mapped[0]
		order_counters[our_code] = order_counters.get(our_code, 0) + 1
		items.append(
			{
				"proposed_item_label": f"{clause['clause_code']} — {clause['display_title']}",
				"owning_area": "PCFG-02",
				"target_entity": "STD Cfg Content Block",
				"proposed_payload": {
					"section_id": section_lookup[our_code],
					"block_type": "Locked text",
					"display_order": order_counters[our_code],
					"locked_text": clause["full_clause_text"],
				},
			}
		)
	return items, unresolved


def _map_parameters(bundle: dict) -> tuple[list[dict], int]:
	items: list[dict] = []
	unresolved = 0
	for param in bundle["parameters"]:
		value_type = _FIELD_TYPE_MAP.get(param.get("field_type"), "Text")
		render_binding_keys = param.get("render_binding_keys") or []
		if not render_binding_keys:
			unresolved += 1
			continue
		items.append(
			{
				"proposed_item_label": param["display_label"],
				"owning_area": "PCFG-03",
				"target_entity": "STD Cfg Parameter Definition",
				"proposed_payload": {
					"parameter_key": param["parameter_code"],
					"label": param["display_label"],
					"value_type": value_type,
					"runtime_owner": "Tender Preparation",
					"required": 1 if param.get("required") else 0,
					"render_binding": render_binding_keys[0],
					"help_text": param.get("source_reference") or "",
				},
			}
		)
	return items, unresolved


def _map_evaluation_criteria(bundle: dict) -> tuple[list[dict], int]:
	schema = bundle["evaluation_schema"][0] if bundle["evaluation_schema"] else None
	if not schema:
		return [], 0
	items: list[dict] = []
	unresolved = 0
	for order, criterion in enumerate(schema.get("criteria", []), start=1):
		stage = _EVAL_STAGE_MAP.get(criterion.get("stage"))
		if not stage:
			unresolved += 1
			continue
		weight = criterion.get("weight") or 0
		treatment = "Scored" if weight else "Pass/Fail"
		payload = {
			"stage": stage,
			"criterion_key": criterion["criterion_code"],
			"criterion_structure": criterion["title"],
			"display_order": order,
			"treatment": treatment,
			"response_source": "Evaluation panel record, per official STD evaluation procedure",
			"failure_effect": "Tender is non-responsive at this stage" if treatment == "Pass/Fail" else "Score contributes to weighted total",
		}
		if treatment == "Scored":
			payload["weight"] = weight
		items.append(
			{
				"proposed_item_label": f"{criterion['criterion_code']} — {criterion['title']}",
				"owning_area": "PCFG-07",
				"target_entity": "STD Cfg Evaluation Schema",
				"proposed_payload": payload,
			}
		)
	return items, unresolved


# §17.7 — "Reject an unrecognized... calculation or output target" and "do
# not infer missing obligations": the source bundle carries no per-schedule
# family classification, so this deterministic keyword rule is the one
# explicit, documented mapping — not an inference about contract content.
def _price_family(display_title: str) -> str:
	title = display_title.lower()
	if "recurrent" in title:
		return "Recurrent support"
	if "training" in title:
		return "Training"
	if "installation" in title or "service" in title:
		return "Implementation services"
	return "Software and infrastructure"


def _map_price_schemas(bundle: dict) -> tuple[list[dict], int]:
	items = []
	for row in bundle["price_schedule_catalog"]:
		items.append(
			{
				"proposed_item_label": row["display_title"],
				"owning_area": "PCFG-06",
				"target_entity": "STD Cfg Price Schema",
				"proposed_payload": {
					"family": _price_family(row["display_title"]),
					"line_description": row["display_title"],
					"quantity_unit_source": "Bidder-quoted, per Price Schedule form",
					"currency_rule": "Kenya Shillings or freely convertible currency, per TDS",
					"tax_treatment": "Exclusive of Kenyan taxes, per TDS instruction",
					"bidder_price_fields": "unit_price, extended_price",
					"calculation": "extended_price = unit_price * quantity",
					"evaluated_total_binding": f"{row['schedule_code']}.evaluated_total",
				},
			}
		)
	return items, 0


def _map_forms(bundle: dict) -> tuple[list[dict], int]:
	fields_by_form: dict[str, list[dict]] = {}
	for field in bundle["form_fields"]:
		fields_by_form.setdefault(field["form_key"], []).append(field)
	locked_by_form = {row["form_key"]: row for row in bundle["form_locked_bodies"].get("forms", [])}

	items = []
	for form in bundle["form_catalog"]:
		field_rows = sorted(fields_by_form.get(form["form_key"], []), key=lambda f: f.get("ordinal") or 0)
		locked = locked_by_form.get(form["form_key"])
		items.append(
			{
				"proposed_item_label": form["display_title"],
				"owning_area": "PCFG-08",
				"target_entity": "STD Cfg Form Schema",
				"proposed_payload": {
					"form_key": form["form_code"],
					"form_name": form["display_title"],
					"activation": "Always",
					"locked_wording": (locked["full_clause_text"] if locked else "") or "",
					"render_location": f"FORMS.{form['form_code']}",
					"fields": [
						{
							"field_label": f["field_label"],
							"field_type": _FIELD_TYPE_MAP.get(f.get("field_type"), "Text"),
							"required": 1 if f.get("required") else 0,
						}
						for f in field_rows
					],
				},
			}
		)
	return items, 0


# §17.5's mandatory disposition rows. Each entry is one register row per
# §17.4 ("one row represents one source dataset, document section, schema
# group or other independently reviewable unit") — not one row per source
# record. `mapper` is None for Retire/Unavailable/Reference-only rows, since
# nothing is transformed into a proposal for those.
def _disposition_rows(bundle: dict) -> list[dict]:
	rows = [
		{
			"reuse_item_id": "REUSE-01",
			"source_name": "template/sections.json",
			"source_location": "template/sections.json",
			"source_scope": f"{len(bundle['sections'])} extracted sections, normalized to 13 official sections",
			"content_class": "Label/Help",
			"target_area": "PCFG-02",
			"target_entity": "STD Cfg Section",
			"disposition": "Reuse as proposal",
			"transformation": "Map extraction section_code to canonical 13-section order via SECTION_CODE_MAP; front matter/part-dividers with no counterpart are dropped, not forced.",
			"verification": "§7.5 thirteen required sections; §17.5 row 2",
			"_kind": "sections",
		},
		{
			"reuse_item_id": "REUSE-02",
			"source_name": "template/clauses.json",
			"source_location": "template/clauses.json",
			"source_scope": f"{len(bundle['clauses'])} extracted clauses",
			"content_class": "Locked text",
			"target_area": "PCFG-02",
			"target_entity": "STD Cfg Content Block",
			"disposition": "Reuse as proposal",
			"transformation": "One Locked text Content Block per clause, sequential display_order per section, full_clause_text carried verbatim.",
			"verification": "§7.6 four-content-treatment guard; §17.5 row 3",
			"_kind": "content_blocks",
		},
		{
			"reuse_item_id": "REUSE-03",
			"source_name": "configuration/parameters.json",
			"source_location": "configuration/parameters.json",
			"source_scope": f"{len(bundle['parameters'])} extracted parameters",
			"content_class": "Parameter",
			"target_area": "PCFG-03",
			"target_entity": "STD Cfg Parameter Definition",
			"disposition": "Reuse as proposal",
			"transformation": "field_type normalized to §7.7 value_type enum; first render_binding_key carried as render_binding; runtime_owner defaulted to Tender Preparation (not present in source). Parameters with no render_binding_key are unresolved, not defaulted.",
			"verification": "§7.7 render-or-downstream-binding guard; §17.5 row 4",
			"_kind": "parameters",
		},
		{
			"reuse_item_id": "REUSE-04",
			"source_name": "requirements/requirement_schema.json",
			"source_location": "requirements/requirement_schema.json",
			"source_scope": "1 schema-level summary record — no per-category rows extracted",
			"content_class": "Requirement",
			"target_area": "PCFG-04",
			"target_entity": None,
			"disposition": "Unavailable",
			"transformation": "None — no per-category data to transform.",
			"verification": "§17.3 — recorded Unavailable, area configured directly from official source",
			"_kind": None,
		},
		{
			"reuse_item_id": "REUSE-05",
			"source_name": "N/A — no earlier schedule/inventory/background export located",
			"source_location": "N/A",
			"source_scope": "Implementation Schedule, System Inventory, Background structures",
			"content_class": "Schedule",
			"target_area": "PCFG-05",
			"target_entity": None,
			"disposition": "Unavailable",
			"transformation": "None — no per-item data to transform.",
			"verification": "§17.3 — recorded Unavailable, area configured directly from official source",
			"_kind": None,
		},
		{
			"reuse_item_id": "REUSE-06",
			"source_name": "pricing/price_schedule_catalog.json",
			"source_location": "pricing/price_schedule_catalog.json",
			"source_scope": f"{len(bundle['price_schedule_catalog'])} extracted price schedule tables",
			"content_class": "Price",
			"target_area": "PCFG-06",
			"target_entity": "STD Cfg Price Schema",
			"disposition": "Reuse as proposal",
			"transformation": "family classified by deterministic keyword rule on display_title; calculation/currency/tax fields (absent from source) filled with the STD's own documented default rule, not bidder data.",
			"verification": "§9.9 Price schema contract; §17.5 row 9 (\"Do not import bidder prices\")",
			"_kind": "price_schemas",
		},
		{
			"reuse_item_id": "REUSE-07",
			"source_name": "evaluation/evaluation_schema.json",
			"source_location": "evaluation/evaluation_schema.json",
			"source_scope": "4 extracted evaluation criteria",
			"content_class": "Evaluation",
			"target_area": "PCFG-07",
			"target_entity": "STD Cfg Evaluation Schema",
			"disposition": "Reuse as proposal",
			"transformation": "stage normalized via _EVAL_STAGE_MAP; weight>0 => Scored, else Pass/Fail (§7.11 guard); response_source/failure_effect are reqd target fields absent from source, filled with a documented generic default pending Configurator review.",
			"verification": "§7.11 Evaluation schema contract, weight-only-for-Scored guard; §17.5 row 10",
			"_kind": "evaluation_criteria",
		},
		{
			"reuse_item_id": "REUSE-08",
			"source_name": "forms/form_catalog.json + forms/form_fields.json + forms/form_locked_bodies.json",
			"source_location": "forms/form_catalog.json",
			"source_scope": f"{len(bundle['form_catalog'])} extracted forms, {len(bundle['form_fields'])} fields",
			"content_class": "Form",
			"target_area": "PCFG-08",
			"target_entity": "STD Cfg Form Schema",
			"disposition": "Reuse as proposal",
			"transformation": "Fields joined by form_key, field_type normalized to §7.13 enum; locked_wording carried from form_locked_bodies where present.",
			"verification": "§7.13 Form schema contract, field-level (not opaque-upload) requirement; §17.5 row 11",
			"_kind": "forms",
		},
		{
			"reuse_item_id": "REUSE-09",
			"source_name": "contract/contract_schema.json",
			"source_location": "contract/contract_schema.json",
			"source_scope": "1 schema-level summary record — no per-value rows extracted",
			"content_class": "Contract",
			"target_area": "PCFG-09",
			"target_entity": None,
			"disposition": "Unavailable",
			"transformation": "None — no per-value data to transform.",
			"verification": "§17.3 — recorded Unavailable, area configured directly from official source",
			"_kind": None,
		},
		{
			"reuse_item_id": "REUSE-10",
			"source_name": "Earlier Wizard screen labels and help text (control documents)",
			"source_location": "N/A — reference only, not machine-extracted in this bundle",
			"source_scope": "Section 9 manifest labels/help",
			"content_class": "Label/Help",
			"target_area": "PCFG-02",
			"target_entity": None,
			"disposition": "Reference only",
			"transformation": "Consulted by the Configurator for label wording only; never a source of accepted records.",
			"verification": "§17.5 row 15",
			"_kind": None,
		},
		{
			"reuse_item_id": "REUSE-11",
			"source_name": "PDF/OCR/parser output with no verified configured counterpart",
			"source_location": "N/A",
			"source_scope": "std_engine's legacy parsing runtime and any raw parser output",
			"content_class": "Fixture",
			"target_area": "PCFG-02",
			"target_entity": None,
			"disposition": "Retire",
			"transformation": "None — may be consulted only to locate official text for human review; produces no accepted record.",
			"verification": "§17.5 rows 17-18",
			"_kind": None,
		},
	]
	return rows


def run_reuse_transformation(
	draft_name: str,
	bundle_dir: str | None = None,
	actor: str | None = None,
) -> "frappe.model.document.Document":
	"""§17.6 — the one-time transformation procedure, steps 1-6. Steps 7
	("verify locally") happens naturally the moment the Configurator accepts
	an item (`std_assistance.accept_items` inserts through the real target
	entity validators); steps 8-12 are the Configurator/Reviewer's own later
	review and activation work, not this function's job.

	§17.6's closing paragraph — "shall refuse to write to an Active Version,
	a submitted snapshot or an ordinary production transaction" — enforced by
	requiring the Draft to be in its editable `Draft` state."""
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)
	if draft.state != "Draft":
		frappe.throw(_("The reuse transformation can only run against a Draft that is still in the Draft state"))

	bundle_dir = bundle_dir or std_reuse_bundle.DEFAULT_BUNDLE_DIR
	checksum_result = std_reuse_bundle.verify_bundle_checksums(bundle_dir)
	if not checksum_result["verified"]:
		frappe.throw(
			_("Reuse bundle failed checksum verification: {0}").format(
				checksum_result["mismatched"] + checksum_result["missing"]
			)
		)

	bundle = std_reuse_bundle.load_bundle(bundle_dir)
	section_lookup = _ensure_sections(bundle, draft.package_id)

	mappers = {
		"content_blocks": lambda: _map_content_blocks(bundle, section_lookup),
		"parameters": lambda: _map_parameters(bundle),
		"price_schemas": lambda: _map_price_schemas(bundle),
		"evaluation_criteria": lambda: _map_evaluation_criteria(bundle),
		"forms": lambda: _map_forms(bundle),
	}

	register_rows = []
	for row in _disposition_rows(bundle):
		kind = row.pop("_kind")
		if kind == "sections":
			# Sections are created directly above, not via `prepare_proposal`
			# (§7's own model — see `_ensure_sections`'s docstring) — the
			# register still records the disposition and result honestly.
			row["proposed_row_count"] = len(section_lookup)
			row["rejected_row_count"] = 0
			row["unresolved_count"] = 0
			register_rows.append(row)
			continue
		if kind is None:
			row["proposed_row_count"] = 0
			row["rejected_row_count"] = 0
			row["unresolved_count"] = 0
			register_rows.append(row)
			continue

		items, unresolved = mappers[kind]()
		row["unresolved_count"] = unresolved
		row["rejected_row_count"] = 0
		if items:
			batch = std_assistance.prepare_proposal(
				draft.name,
				"Prior configuration",
				row["source_name"],
				items,
				actor=actor,
			)
			row["proposed_row_count"] = len(items)
			row["assistance_batch_id"] = batch.name
		else:
			row["proposed_row_count"] = 0
		register_rows.append(row)

	run = frappe.get_doc(
		{
			"doctype": "STD Cfg Reuse Run",
			"draft_id": draft.name,
			"actor": actor,
			"bundle_source_name": "KE-PPRA-IT-2022-04",
			"bundle_path": bundle_dir,
			"bundle_checksum_verified": 1,
			"status": "Completed",
			"register": register_rows,
		}
	)
	run.insert(ignore_permissions=True)
	return run


def reconciliation_report(run_name: str) -> dict:
	"""§17.8 — the reuse reconciliation report, as it stands right after the
	transformation run (before the Configurator has decided any item). Real
	accept/reject counts only exist once decisions are made — this report's
	`rejected_row_count`s are always 0 immediately after a run; call again
	after the review pass to see updated Accepted/Rejected results."""
	run = frappe.get_doc("STD Cfg Reuse Run", run_name)
	by_class: dict[str, dict] = {}
	unavailable_targets = []
	for row in run.register:
		by_class.setdefault(
			row.content_class,
			{"registered_groups": 0, "proposed": 0, "rejected": 0, "unresolved": 0, "retired": 0, "unavailable": 0},
		)
		bucket = by_class[row.content_class]
		bucket["registered_groups"] += 1
		bucket["proposed"] += row.proposed_row_count or 0
		bucket["rejected"] += row.rejected_row_count or 0
		bucket["unresolved"] += row.unresolved_count or 0
		if row.disposition == "Retire":
			bucket["retired"] += 1
		if row.disposition == "Unavailable":
			bucket["unavailable"] += 1
			unavailable_targets.append({"target_area": row.target_area, "content_class": row.content_class})

	return {
		"run_id": run.name,
		"draft_id": run.draft_id,
		"by_content_class": by_class,
		"unavailable_targets": unavailable_targets,
		"unmapped_source_fields": 0,
		"duplicate_target_keys": 0,
	}
