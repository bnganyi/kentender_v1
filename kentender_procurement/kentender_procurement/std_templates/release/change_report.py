# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The generated preceding-release comparison (STD-TPL-001 v0.10 §13.9,
§11.3 "Changes from release …").

Compares the candidate with the structured snapshot of the exact preceding
approved release (`05_review/preceding_release.json`) across assets, source
treatments, document anchors, response rules, locked declarations,
evaluation mappings, contract mappings, supported-use boundaries and renderer
compatibility. Every change carries a kind, a stable identity, a plain
summary and its compatibility effect; the overall result is exactly
`Compatible successor`, `Breaking — not interchangeable with the preceding
release` or `First release` (owner decision OD5 dropped the v0.10 wording
"new release approval required": there is no approval step). Nobody writes
this report by hand. Pure Python.
"""

from __future__ import annotations

from typing import Any

FIRST_RELEASE = "First release"
COMPATIBLE = "Compatible successor"
BREAKING = "Breaking — not interchangeable with the preceding release"
CATEGORIES: tuple[str, ...] = (
	"Assets",
	"Source treatments",
	"Document anchors",
	"Response rules",
	"Locked declarations",
	"Evaluation mappings",
	"Contract mappings",
	"Supported use",
	"Renderer compatibility",
)
_BREAKING_CATEGORIES = frozenset({"Response rules", "Locked declarations", "Evaluation mappings", "Contract mappings", "Supported use", "Renderer compatibility"})


def _change(kind: str, category: str, identity: str, summary: str) -> dict[str, Any]:
	effect = "Breaking" if category in _BREAKING_CATEGORIES else "Compatible"
	if category == "Source treatments" and kind == "changed":
		effect = "Breaking"
	return {"change_kind": kind, "category": category, "identity": identity, "summary": summary, "compatibility_effect": effect}


def _diff_keyed(before: dict[str, Any], after: dict[str, Any], category: str, noun: str) -> list[dict[str, Any]]:
	out = []
	for key in sorted(set(before) | set(after)):
		if key not in before:
			out.append(_change("added", category, key, f"{noun} {key} added."))
		elif key not in after:
			out.append(_change("removed", category, key, f"{noun} {key} removed."))
		elif before[key] != after[key]:
			out.append(_change("changed", category, key, f"{noun} {key} changed."))
	return out


def build(candidate: dict[str, Any], preceding: dict[str, Any] | None) -> dict[str, Any]:
	"""`candidate` carries: release identity, `assets` {path: sha256},
	`coverage_treatments`, `document_anchors`, `response_rules` {id: rule},
	`declarations` {text_id: digest}, `evaluation_mappings` {id: mapping},
	`contract_mappings` {id: mapping}, `supported_use`, `renderer`."""
	report: dict[str, Any] = {
		"schema_version": 1,
		"release_id": candidate["release_id"],
		"template_key": candidate["template_key"],
		"template_release": candidate["template_release"],
		"preceding_release": preceding["template_release"] if preceding else None,
	}
	if not preceding:
		report.update({"overall_result": FIRST_RELEASE, "totals": {}, "changes": []})
		return report
	before_assets = {a["path"]: a["sha256"] for a in preceding["assets"]}
	changes: list[dict[str, Any]] = []
	changes += _diff_keyed(before_assets, candidate["assets"], "Assets", "Asset")
	changes += _diff_keyed(preceding["coverage_treatments"], candidate["coverage_treatments"], "Source treatments", "Source row")
	changes += _diff_keyed({a: True for a in preceding["document_anchors"]}, {a: True for a in candidate["document_anchors"]}, "Document anchors", "Document anchor")
	changes += _diff_keyed({r["rule_id"]: r for r in preceding["response_rules"]}, candidate["response_rules"], "Response rules", "Response rule")
	changes += _diff_keyed({d["text_id"]: d for d in preceding["declarations"]}, candidate["declarations"], "Locked declarations", "Locked declaration")
	changes += _diff_keyed({m["mapping_id"]: m for m in preceding["evaluation_mappings"]}, candidate["evaluation_mappings"], "Evaluation mappings", "Evaluation mapping")
	changes += _diff_keyed({m["mapping_id"]: m for m in preceding["contract_mappings"]}, candidate["contract_mappings"], "Contract mappings", "Contract mapping")
	changes += _diff_keyed(preceding["supported_use"], candidate["supported_use"], "Supported use", "Supported-use boundary")
	if preceding["renderer"] != candidate["renderer"]:
		changes.append(
			_change(
				"changed",
				"Renderer compatibility",
				"renderer",
				f"Renderer changed from {preceding['renderer'].get('document_engine')} to "
				f"{candidate['renderer']['renderer_profile_id']} {candidate['renderer']['supported_renderer_version']} "
				f"({candidate['renderer']['document_engine']}).",
			)
		)
	totals: dict[str, dict[str, int]] = {}
	for category in CATEGORIES:
		rows = [c for c in changes if c["category"] == category]
		totals[category] = {kind: sum(1 for c in rows if c["change_kind"] == kind) for kind in ("added", "changed", "removed")}
	breaking = any(c["compatibility_effect"] == "Breaking" for c in changes)
	report.update({"overall_result": BREAKING if breaking else COMPATIBLE, "totals": totals, "changes": changes})
	return report
