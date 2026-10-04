# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §10 — all seven runtime manifests, one shared builder
interface.

Tender Configuration keeps its own dedicated, already-tested DocType
(`STD Cfg Tender Manifest`, Phase 2/7) as a deliberate exception — its ordered
CFG-01..09 items are richer than a generic JSON payload would represent as
usefully, and there is no functional defect forcing a migration (user
decision, 2026-08-26). The other six share one new DocType,
`STD Cfg Runtime Manifest`, keyed by (`std_version_id`, `manifest_type`).

Every one of the seven still goes through the same shape of work — build,
validate, digest, persist, all inside one atomic activation — via
`generate_all_manifests()`, the single function `std_lifecycle.activate_package`
calls. A builder failure for any manifest raises and aborts the whole
activation (§11.3: "Any failure creates no Version and no partial
manifests") — there is no partial-success path here by design.
"""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _

from kentender_procurement.std_configuration.services.std_manifest import (
	generate_tender_configuration_manifest,
)


def compute_digest(payload: dict) -> str:
	canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --- builders: deterministic projections from already-authored Version content,
# same "no synthesis" rule `std_manifest.py`'s own builders follow. -------------


def _build_requirement_composer(version_name: str) -> dict:
	categories = frappe.get_all(
		"STD Cfg Requirement Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=[
			"category",
			"display_order",
			"allowed_response_types",
			"evidence_mode",
			"acceptance_mode",
			"vendor_neutrality_trigger",
		],
		order_by="display_order",
	)
	for row in categories:
		row["row_fields"] = [
			"Category",
			"Supplier obligation",
			"Bidder response",
			"Evidence required",
			"Acceptance condition",
		]
		row["allowed_response_types"] = [
			v.strip() for v in (row.get("allowed_response_types") or "").split("\n") if v.strip()
		]
	schedule = frappe.get_all(
		"STD Cfg Schedule Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["milestone_key", "title", "required_deliverable", "completion_rule", "acceptance_checkpoint"],
		order_by="display_order",
	)
	return {"categories": categories, "schedule": schedule}


def _build_bidder_response(version_name: str) -> dict:
	forms = []
	for form in frappe.get_all(
		"STD Cfg Form Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["name", "form_key", "form_name", "activation", "evidence_rule"],
		order_by="name",
	):
		fields = frappe.get_all(
			"STD Cfg Form Schema Field",
			filters={"parent": form["name"]},
			fields=["field_label", "field_type", "required"],
			order_by="idx",
		)
		forms.append(
			{
				"form_key": form["form_key"],
				"form_name": form["form_name"],
				"activation": form["activation"],
				"evidence_rule": form.get("evidence_rule") or "",
				"fields": fields,
			}
		)
	compliance_responses = frappe.get_all(
		"STD Cfg Requirement Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["category", "allowed_response_types", "evidence_mode"],
		order_by="display_order",
	)
	price_tables = frappe.get_all(
		"STD Cfg Price Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["family", "line_description", "bidder_price_fields", "currency_rule"],
		order_by="name",
	)
	return {"forms": forms, "compliance_responses": compliance_responses, "price_tables": price_tables}


def _build_evaluation(version_name: str) -> dict:
	criteria = frappe.get_all(
		"STD Cfg Evaluation Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=[
			"criterion_key",
			"stage",
			"criterion_structure",
			"treatment",
			"response_source",
			"evidence_source",
			"weight",
			"threshold",
			"failure_effect",
		],
		order_by="display_order",
	)
	return {
		"stages": ["Preliminary responsiveness", "Technical evaluation", "Financial evaluation", "Post-qualification"],
		"criteria": criteria,
	}


def _build_contract_formation(version_name: str) -> dict:
	obligations = frappe.get_all(
		"STD Cfg Requirement Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["category", "contract_carry_forward_binding"],
		order_by="display_order",
	)
	schedule = frappe.get_all(
		"STD Cfg Schedule Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["milestone_key", "title", "completion_rule", "contract_binding"],
		order_by="display_order",
	)
	contract_values = frappe.get_all(
		"STD Cfg Contract Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name},
		fields=["value_category", "required_treatment", "scc_binding", "contract_binding"],
		order_by="name",
	)
	return {"obligations": obligations, "schedule": schedule, "contract_values": contract_values}


def _build_contract_management(version_name: str) -> dict:
	# Honest gap (documented, not hidden): Phase 2 never built a distinct
	# "post-award form" flag (§7.13 item 16's own concept). This is every
	# Contract Schema row that happens to carry a contract_binding, not a
	# specifically-flagged post-award subset — a real, smaller gap than the
	# missing-DocType one, tracked as such rather than presented as precise.
	rows = frappe.get_all(
		"STD Cfg Contract Schema",
		filters={"reference_doctype": "STD Cfg Version", "reference_name": version_name, "contract_binding": ["!=", ""]},
		fields=["value_category", "contract_binding"],
		order_by="name",
	)
	return {"post_award_mappings": rows}


def _build_render(version_name: str) -> dict:
	package_id = frappe.db.get_value("STD Cfg Version", version_name, "package_id")
	sections = []
	for section in frappe.get_all(
		"STD Cfg Section",
		filters={"package_id": package_id},
		fields=["name", "section_code", "title", "display_order", "coverage_area_number"],
		order_by="display_order",
	):
		blocks = frappe.get_all(
			"STD Cfg Content Block",
			filters={
				"reference_doctype": "STD Cfg Version",
				"reference_name": version_name,
				"section_id": section["name"],
			},
			fields=["block_type", "display_order", "locked_text", "binding_key"],
			order_by="display_order",
		)
		sections.append(
			{
				"section_code": section["section_code"],
				"title": section["title"],
				"display_order": section["display_order"],
				"coverage_area_number": section["coverage_area_number"],
				"blocks": blocks,
			}
		)
	return {"sections": sections}


# --- validators: required-shape checks, run before any payload is persisted. --


def _require_keys(payload: dict, keys: tuple[str, ...], manifest_type: str) -> None:
	missing = [k for k in keys if k not in payload]
	if missing:
		frappe.throw(
			_("{0} manifest payload is missing required key(s): {1}").format(manifest_type, ", ".join(missing)),
			frappe.ValidationError,
		)
	for key in keys:
		if not isinstance(payload[key], list):
			frappe.throw(_("{0} manifest payload key {1} must be a list").format(manifest_type, key))


_BUILDERS = {
	"Requirement Composer": _build_requirement_composer,
	"Bidder Response": _build_bidder_response,
	"Evaluation": _build_evaluation,
	"Contract Formation": _build_contract_formation,
	"Contract Management": _build_contract_management,
	"Render": _build_render,
}

_VALIDATORS = {
	"Requirement Composer": lambda p: _require_keys(p, ("categories", "schedule"), "Requirement Composer"),
	"Bidder Response": lambda p: _require_keys(p, ("forms", "compliance_responses", "price_tables"), "Bidder Response"),
	"Evaluation": lambda p: _require_keys(p, ("stages", "criteria"), "Evaluation"),
	"Contract Formation": lambda p: _require_keys(p, ("obligations", "schedule", "contract_values"), "Contract Formation"),
	"Contract Management": lambda p: _require_keys(p, ("post_award_mappings",), "Contract Management"),
	"Render": lambda p: _require_keys(p, ("sections",), "Render"),
}


def _generate_one_runtime_manifest(manifest_type: str, version_name: str) -> None:
	payload = _BUILDERS[manifest_type](version_name)
	_VALIDATORS[manifest_type](payload)
	frappe.get_doc(
		{
			"doctype": "STD Cfg Runtime Manifest",
			"manifest_type": manifest_type,
			"std_version_id": version_name,
			"schema_version": "1",
			"status": "Generated",
			"generated_at": frappe.utils.now_datetime(),
			"content_digest": compute_digest(payload),
			"payload": frappe.as_json(payload),
		}
	).insert(ignore_permissions=True)


def generate_all_manifests(version_name: str, package_code: str, official_title: str, official_issue: str) -> None:
	"""§10/§11.3 — all seven manifests, one call, one atomic activation
	transaction. Tender Configuration first (its own DocType/digest field);
	the other six follow the shared builder/validator/digest path."""
	tender_config = generate_tender_configuration_manifest(version_name, package_code, official_title, official_issue)
	# Digest only the meaningful item-contract fields (§7.18's 15 properties),
	# not Frappe's own per-row framework metadata (a fresh random child-row
	# name every generation would otherwise make the digest never stable).
	item_fields = (
		"item_key", "step_id", "label", "help_text", "value_type", "source_mode",
		"source_binding", "required_mode", "condition", "allowed_values",
		"default_rule", "validation", "render_binding", "downstream_mapping",
		"completion_effect",
	)
	clean_items = [{f: item.get(f) for f in item_fields} for item in tender_config.items]
	tender_config.content_digest = compute_digest({"items": clean_items})
	tender_config.save(ignore_permissions=True)

	for manifest_type in _BUILDERS:
		_generate_one_runtime_manifest(manifest_type, version_name)
