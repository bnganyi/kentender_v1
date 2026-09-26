# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Source-coverage treatment summary (STD-TPL-001 v0.10 §11.3 "Coverage and
changes"; owner ruling R7).

The register records one of eight `treatment` values per source row
(§13.3). The inspection surface reports five plain buckets. The mapping is
declared here once and recorded in the manifest's `document_summary`, so the
totals come from the register data and never from a hand-typed figure:

1. `item_type = preparer_instruction`  -> Not applicable
2. `Not used by this released pattern` -> Excluded with reason
3. Supplier response / Award-derived / Contract-derived -> Structured input
4. a rendered row governed by a named condition (an insertion key of kind
   `condition`, or with a stated `condition`) or explicitly "rendered only
   when" -> Conditional
5. every other rendered row -> Rendered

Pure Python: no Frappe import.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from typing import Any

BUCKETS: tuple[str, ...] = ("Rendered", "Structured input", "Conditional", "Excluded with reason", "Not applicable")
TREATMENTS: tuple[str, ...] = (
	"Locked", "Inherited", "Officer value", "Generated", "Supplier response", "Award-derived", "Contract-derived",
	"Not used by this released pattern",
)
COVERAGE_COLUMNS = (
	"coverage_id,source_page_start,source_page_end,section_number,heading,item_type,treatment,owner_key,"
	"human_render_location,structured_rule_id,readiness_check,status,review_note"
).split(",")
INSERTION_COLUMNS = (
	"key,kind,source_treatment,source_section,owner,task,label,data_type,required,condition,validation,example,"
	"human_render_location,structured_use,downstream_use"
).split(",")
FORMS_COLUMNS = (
	"form_id,official_form_name,source_pages,included,variant_selected,fixed_text_complete,prefilled_keys,"
	"supplier_fields,award_fields,contract_fields,response_rule_ids,review_status,review_note"
).split(",")
MAPPING_RULE = (
	"preparer_instruction -> Not applicable; Not used by this released pattern -> Excluded with reason; "
	"Supplier response, Award-derived, Contract-derived -> Structured input; rendered and governed by a named "
	"condition key or 'rendered only when' -> Conditional; otherwise Rendered"
)
_KEY = re.compile(r"[a-z_]+(?:\.[a-z_]+)+")


def read_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
	reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
	rows = list(reader)
	return list(reader.fieldnames or []), rows


def condition_keys(insertion_rows: list[dict[str, str]]) -> set[str]:
	return {r["key"] for r in insertion_rows if r["kind"] == "condition" or r["condition"].strip()}


def bucket(row: dict[str, str], conditions: set[str]) -> str:
	treatment = row["treatment"]
	if row["item_type"] == "preparer_instruction":
		return "Not applicable"
	if treatment == "Not used by this released pattern":
		return "Excluded with reason"
	if treatment in ("Supplier response", "Award-derived", "Contract-derived"):
		return "Structured input"
	keys = set(_KEY.findall(row["owner_key"]))
	if keys & conditions or "rendered only when" in row["human_render_location"]:
		return "Conditional"
	return "Rendered"


def coverage_rows(coverage: list[dict[str, str]], insertion: list[dict[str, str]]) -> list[dict[str, Any]]:
	"""The read-only coverage inspection rows (§11.3 "View coverage details")."""
	conditions = condition_keys(insertion)
	out = []
	for row in coverage:
		start, end = row["source_page_start"], row["source_page_end"]
		pages = start if start == end else f"{start}–{end}"
		locator = f"Source p. {pages}" + (f" · {row['section_number']}" if row["section_number"] else "")
		kind = bucket(row, conditions)
		out.append(
			{
				"coverage_id": row["coverage_id"],
				"source_locator": locator,
				"title": row["heading"],
				"treatment": kind,
				"register_treatment": row["treatment"],
				"output_anchor": row["human_render_location"],
				"structured_rule_id": row["structured_rule_id"],
				"reason": row["review_note"] if kind in ("Excluded with reason", "Conditional", "Not applicable") else "",
				"review_status": row["status"],
			}
		)
	return out


def summary(coverage: list[dict[str, str]], insertion: list[dict[str, str]], forms: list[dict[str, str]]) -> dict[str, Any]:
	conditions = condition_keys(insertion)
	counts = Counter(bucket(row, conditions) for row in coverage)
	reviewed = sum(1 for row in coverage if row["status"] == "Reviewed")
	forms_included = sum(1 for f in forms if f["included"].strip().upper() == "TRUE")
	forms_reviewed = sum(1 for f in forms if f["review_status"].startswith("Reviewed"))
	return {
		"mapping_rule": MAPPING_RULE,
		"source_rows_total": len(coverage),
		"source_rows_reviewed": reviewed,
		"source_rows_pending_review": [row["coverage_id"] for row in coverage if row["status"] != "Reviewed"],
		"treatment_totals": {name: counts.get(name, 0) for name in BUCKETS},
		"register_treatment_totals": {name: sum(1 for r in coverage if r["treatment"] == name) for name in TREATMENTS},
		"forms_total": len(forms),
		"forms_included": forms_included,
		"forms_excluded": len(forms) - forms_included,
		"forms_reviewed": forms_reviewed,
		"forms_pending_review": [f["form_id"] for f in forms if not f["review_status"].startswith("Reviewed")],
		"insertion_points_total": len(insertion),
	}
