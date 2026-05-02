#!/usr/bin/env python3
"""One-off patcher: inject guided ``offcfg_*`` fields + doc-8-ish section order into Procurement Tender."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from kentender_procurement.tender_management.services.officer_guided_field_registry import (  # noqa: E402
	OFFICER_FIELD_SYNONYMS,
	get_officer_guided_field_specs,
	group_label_for_code,
)

DOC_PATH = (
	ROOT
	/ "kentender_procurement"
	/ "kentender_procurement"
	/ "doctype"
	/ "procurement_tender"
	/ "procurement_tender.json"
)

GROUP_ORDER = [
	"TENDER_IDENTITY",
	"METHOD_PARTICIPATION",
	"DATES_MEETINGS",
	"SECURITIES",
	"ALTERNATIVES_LOTS",
	"QUALIFICATION",
	"WORKS_REQUIREMENTS",
	"CONTRACT_SCC",
]


def _section_field(fieldname: str, label: str, collapsible: int = 0) -> dict:
	row: dict = {"fieldname": fieldname, "fieldtype": "Section Break", "label": label}
	if collapsible:
		row["collapsible"] = 1
	return row


def _offcfg_row(spec) -> dict:
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		_frappe_fieldtype,
	)

	ft = _frappe_fieldtype(spec.std_field_type)
	row: dict = {
		"fieldname": spec.doctype_fieldname,
		"fieldtype": ft,
		"label": spec.label,
	}
	if spec.help_text:
		row["description"] = spec.help_text[:140]
	if ft == "Select" and spec.options:
		row["options"] = "\n".join(spec.options)
	return row


def main() -> None:
	specs = get_officer_guided_field_specs()
	by_group: dict[str, list] = defaultdict(list)
	for s in specs:
		by_group[s.group_code].append(s)
	for g in by_group:
		by_group[g].sort(key=lambda x: x.field_code)

	syn_vals = set(OFFICER_FIELD_SYNONYMS.values())

	doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
	by_name = {f["fieldname"]: f for f in doc["fields"]}

	def pick(fname: str) -> dict:
		return dict(by_name[fname])

	guided_blocks: list[dict] = []
	for gc in GROUP_ORDER:
		if gc == "TENDER_IDENTITY":
			pass
		elif gc == "METHOD_PARTICIPATION":
			guided_blocks.append(
				_section_field(
					"section_guided_method_participation",
					group_label_for_code(gc),
					collapsible=1,
				)
			)
			guided_blocks.append(pick("procurement_method"))
			guided_blocks.append(pick("procurement_category"))
			guided_blocks.append(pick("tender_scope"))
		else:
			section_fn = f"section_guided_{gc.lower()}"
			guided_blocks.append(_section_field(section_fn, group_label_for_code(gc), collapsible=1))
		for spec in by_group.get(gc, []):
			if spec.doctype_fieldname in syn_vals:
				continue
			guided_blocks.append(_offcfg_row(spec))

	# Tail: configuration + validation + children (preserve existing definitions).
	tail_names = [
		"section_configuration",
		"html_officer_guided_notices",
		"configuration_json",
		"configuration_hash",
		"section_validation",
		"tender_status",
		"validation_status",
		"last_validated_at",
		"last_generated_at",
		"section_lots",
		"lots",
		"section_boq",
		"boq_items",
		"section_required_forms",
		"required_forms",
		"section_validation_messages",
		"validation_messages",
		"section_generated_pack",
		"generated_tender_pack_html",
		"section_poc_notes",
		"poc_notes",
	]

	# Doc 8 §11: POC boundary (10), template summary (20), then guided work.
	head_names = [
		"section_officer_poc_boundary",
		"html_officer_poc_boundary",
		"section_template_reference",
		"std_template",
		"template_code",
		"template_version",
		"package_hash",
		"section_std_demo_workspace",
		"html_std_demo_workspace",
		"section_tender_identity",
		"naming_series",
		"tender_title",
		"tender_reference",
	]

	new_fields: list[dict] = []
	for fn in head_names:
		new_fields.append(pick(fn))
	new_fields.extend(guided_blocks)
	for fn in tail_names:
		new_fields.append(pick(fn))

	doc["fields"] = new_fields
	doc["field_order"] = [f["fieldname"] for f in new_fields]

	# Update section labels for clarity
	for f in doc["fields"]:
		if f["fieldname"] == "section_tender_identity":
			f["label"] = "30. Tender Identity"
		if f["fieldname"] == "section_configuration":
			f["label"] = "130. Configuration store (technical)"
		if f["fieldname"] == "section_validation":
			f["label"] = "140. Validation status"
		if f["fieldname"] == "section_required_forms":
			f["label"] = "150. Required Forms"
		if f["fieldname"] == "section_boq":
			f["label"] = "160. BoQ Items"
		if f["fieldname"] == "section_validation_messages":
			f["label"] = "170. Validation Messages"
		if f["fieldname"] == "section_generated_pack":
			f["label"] = "180. Generated Tender Pack"
		if f["fieldname"] == "section_lots":
			f["label"] = "90. Lots"
		if f["fieldname"] == "section_poc_notes":
			f["label"] = "190. POC Notes"

	DOC_PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
	print("Wrote", DOC_PATH, "fields", len(new_fields))


if __name__ == "__main__":
	main()
