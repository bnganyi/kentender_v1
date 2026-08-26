# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §9/§10 — `STD Cfg Tender Manifest` generation.

Real, substantial scope finding from this phase: the spec names **seven**
runtime manifests (§10's table: Requirement Composer, Tender Configuration,
Bidder Response, Evaluation, Contract Formation, Contract Management, Render).
Only **one** — Tender Configuration (`STD Cfg Tender Manifest`, Phase 2) — was
ever given a DocType; the other six were never modeled at all. Building six
more manifest DocTypes and their own generation logic is real, large,
undiscovered work — not something this module quietly does today. This file
implements real, live generation for the one manifest that exists; the other
six are a documented gap (tracker STD-704), not a silent omission.

The manifest is a compiled *projection* of already-authored Draft/Version
content, not an inference/synthesis engine: §9's own framing ("STD
Configuration owns... labels and help text; item types, choices and
defaults...") describes package-authored content, and Phase 1/2's domain
model already stores nearly every §7.18 item-contract property directly on
each PCFG doctype. Generation is a straight per-doctype field projection into
`STD Cfg Tender Manifest Item` rows, tagged with the correct CFG-01..09 step
per §9.4's own area/step table — not synthesis of new content.
"""

from __future__ import annotations

import frappe

# §9.4 — PCFG area -> owning CFG step. PCFG-01 has no separate content
# doctype (Phase 2) so is not itemized here; PCFG-05 splits across two CFG
# steps per §9.4 (CFG-04 Implementation Schedule, CFG-05 Inventory/Background).
_DOCTYPE_STEP: dict[str, str] = {
	"STD Cfg Parameter Definition": "CFG-02",
	"STD Cfg Requirement Schema": "CFG-03",
	"STD Cfg Schedule Schema": "CFG-04",
	"STD Cfg Inventory Schema": "CFG-05",
	"STD Cfg Price Schema": "CFG-06",
	"STD Cfg Evaluation Schema": "CFG-07",
	"STD Cfg Form Schema": "CFG-08",
	"STD Cfg Contract Schema": "CFG-09",
}

# §7.18 item contract's `value_type` enum differs in spelling from each source
# doctype's own `value_type`/`block_type`-shaped field; map what's projectable.
_VALUE_TYPE_MAP: dict[str, str] = {
	"Text": "Text",
	"Long text": "Long Text",
	"Integer": "Integer",
	"Decimal": "Decimal",
	"Money": "Money",
	"Date": "Date",
	"Datetime": "Date and Time",
	"Duration": "Duration",
	"Boolean": "Boolean",
	"Choice": "Choice",
	"Address": "Text",
	"Contact": "Text",
}


def _item_from_parameter(row: dict) -> dict:
	return {
		"item_key": row["parameter_key"],
		"step_id": "CFG-02",
		"label": row["label"],
		"help_text": row.get("help_text") or "",
		"value_type": _VALUE_TYPE_MAP.get(row["value_type"], "Text"),
		"source_mode": "Officer choice" if row["value_type"] == "Choice" else "Officer entry",
		"source_binding": "",
		"required_mode": "Always" if row.get("required") else "Optional",
		"condition": row.get("required_when") or "",
		"allowed_values": row.get("allowed_values") or "",
		"default_rule": "",
		"validation": f"min={row['minimum_value']} max={row['maximum_value']}" if row.get("minimum_value") or row.get("maximum_value") else "",
		"render_binding": row.get("render_binding") or "",
		"downstream_mapping": row.get("downstream_binding") or "",
		"completion_effect": "Blocks step" if row.get("required") else "Warning only",
	}


def _item_from_requirement(row: dict) -> dict:
	return {
		"item_key": f"requirement.{row['category'].lower().replace(' ', '_')}",
		"step_id": "CFG-03",
		"label": row["category"],
		"help_text": "",
		"value_type": "Structured Table",
		"source_mode": "Inherited locked",
		"source_binding": "Requisition Requirements Composer",
		"required_mode": "Always",
		"condition": "",
		"allowed_values": row.get("allowed_response_types") or "",
		"default_rule": "",
		"validation": "",
		"render_binding": row.get("render_binding") or "",
		"downstream_mapping": row.get("bidder_response_binding") or "",
		"completion_effect": "Blocks step",
	}


def _item_from_schedule(row: dict) -> dict:
	return {
		"item_key": row["milestone_key"],
		"step_id": "CFG-04",
		"label": row["title"],
		"help_text": "",
		"value_type": "Structured Table",
		"source_mode": "Officer entry",
		"source_binding": "",
		"required_mode": "Always",
		"condition": "",
		"allowed_values": "",
		"default_rule": "",
		"validation": row.get("completion_rule") or "",
		"render_binding": row.get("render_binding") or "",
		"downstream_mapping": row.get("contract_binding") or "",
		"completion_effect": "Blocks step",
	}


def _item_from_inventory(row: dict) -> dict:
	return {
		"item_key": f"inventory.{row['category'].lower()}",
		"step_id": "CFG-05",
		"label": f"{row['category']} inventory",
		"help_text": "",
		"value_type": "Structured Table",
		"source_mode": "Officer entry",
		"source_binding": "",
		"required_mode": "Always" if row.get("price_schedule_link_policy") == "Required" else "Optional",
		"condition": "",
		"allowed_values": "",
		"default_rule": "",
		"validation": "",
		"render_binding": row.get("render_binding") or "",
		"downstream_mapping": "",
		"completion_effect": "Blocks step" if row.get("price_schedule_link_policy") == "Required" else "Warning only",
	}


def _item_from_price(row: dict) -> dict:
	return {
		"item_key": f"price.{row['family'].lower().replace(' ', '_')}",
		"step_id": "CFG-06",
		"label": row["family"],
		"help_text": "",
		"value_type": "Structured Table",
		"source_mode": "Officer entry",
		"source_binding": "",
		"required_mode": "Always",
		"condition": "",
		"allowed_values": "",
		"default_rule": "",
		"validation": row.get("calculation") or "",
		"render_binding": "Section IV — Price Schedule Forms",
		"downstream_mapping": row.get("evaluated_total_binding") or "",
		"completion_effect": "Blocks step",
	}


def _item_from_evaluation(row: dict) -> dict:
	return {
		"item_key": row["criterion_key"],
		"step_id": "CFG-07",
		"label": row["criterion_structure"],
		"help_text": "",
		"value_type": "Choice",
		"source_mode": "Officer choice",
		"source_binding": "",
		"required_mode": "Always",
		"condition": "",
		"allowed_values": row["treatment"],
		"default_rule": "",
		"validation": "",
		"render_binding": "Section III — Evaluation and Qualification Criteria",
		"downstream_mapping": row.get("evidence_source") or "",
		"completion_effect": "Blocks step",
	}


def _item_from_form(row: dict) -> dict:
	return {
		"item_key": row["form_key"],
		"step_id": "CFG-08",
		"label": row["form_name"],
		"help_text": "",
		"value_type": "Structured Table",
		"source_mode": "Inherited locked" if row["activation"] == "Always" else "Officer choice",
		"source_binding": "",
		"required_mode": "Always" if row["activation"] == "Always" else "Conditional",
		"condition": row.get("activation_condition") or "",
		"allowed_values": "",
		"default_rule": "",
		"validation": "",
		"render_binding": row.get("render_location") or "",
		"downstream_mapping": "",
		"completion_effect": "Blocks step" if row["activation"] == "Always" else "Warning only",
	}


def _item_from_contract(row: dict) -> dict:
	return {
		"item_key": f"contract.{row['value_category'].lower().replace(' ', '_').replace('-', '_')}",
		"step_id": "CFG-09",
		"label": row["value_category"],
		"help_text": "",
		"value_type": "Text",
		"source_mode": "Officer entry",
		"source_binding": "",
		"required_mode": "Always" if row["required_treatment"] == "Required" else "Conditional",
		"condition": row.get("condition") or "",
		"allowed_values": "",
		"default_rule": "",
		"validation": "",
		"render_binding": row.get("scc_binding") or "",
		"downstream_mapping": row.get("contract_binding") or "",
		"completion_effect": "Blocks step" if row["required_treatment"] == "Required" else "Warning only",
	}


_PROJECTORS = {
	"STD Cfg Parameter Definition": _item_from_parameter,
	"STD Cfg Requirement Schema": _item_from_requirement,
	"STD Cfg Schedule Schema": _item_from_schedule,
	"STD Cfg Inventory Schema": _item_from_inventory,
	"STD Cfg Price Schema": _item_from_price,
	"STD Cfg Evaluation Schema": _item_from_evaluation,
	"STD Cfg Form Schema": _item_from_form,
	"STD Cfg Contract Schema": _item_from_contract,
}


def generate_tender_configuration_manifest(
	version_name: str, package_code: str, official_title: str, official_issue: str
) -> "frappe.model.document.Document":
	"""§9.2/§10 — one `STD Cfg Tender Manifest` per Active Version, generated
	from that Version's own reference-scoped content (already reassigned onto
	it by `activate_package` before this is called). Deterministic: rerunning
	against the same Version content produces the same items, in stable
	per-doctype-then-name order."""
	items: list[dict] = []
	for doctype, projector in _PROJECTORS.items():
		rows = frappe.get_all(
			doctype,
			filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
			fields=["*"],
			order_by="name",
		)
		for row in rows:
			items.append(projector(row))

	manifest = frappe.get_doc(
		{
			"doctype": "STD Cfg Tender Manifest",
			"manifest_type": "Tender Configuration",
			"manifest_version": "1",
			"package_code": package_code,
			"std_version_id": version_name,
			"official_title": official_title,
			"official_issue": official_issue,
			"requirement_profile": "Information Technology",
			"items": items,
		}
	)
	manifest.insert(ignore_permissions=True)
	return manifest
