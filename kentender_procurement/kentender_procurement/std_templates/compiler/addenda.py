# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-001 v0.10 §10, §13.5.4 — addendum identity preservation.

`classify()` compares the current effective definition with a successor
definition by stable identity only: source family, immutable source
identity, rule and field key. Every prior and successor identity receives
exactly one of `unchanged`, `converted`, `fresh_response_required`,
`removed` or `new`. Labels, row positions, text similarity and client
identities are never a comparison basis. Pure Python: no Frappe import.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.std_templates.compiler.errors import fail


def _by_stable(definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
	out: dict[str, dict[str, Any]] = {}
	for row in definition["response_rows"]:
		if row["stable_key"] in out:
			fail("STD_DEFINITION_INVALID", "Duplicate stable identity in a definition.", identity=row["stable_key"])
		out[row["stable_key"]] = row
	return out


def classify(prior: dict[str, Any], successor: dict[str, Any], addendum_rules: dict[str, Any]) -> list[dict[str, Any]]:
	if prior["template_family"] != successor["template_family"] or prior["template_release_id"] != successor["template_release_id"]:
		fail("STD_DEFINITION_INVALID", "An addendum cannot change the bound template release.", identity=successor["template_release_id"])
	if prior["tender_id"] != successor["tender_id"]:
		fail("STD_DEFINITION_INVALID", "An addendum belongs to the same Tender.", identity=successor["tender_id"])
	notices = {c["classification"]: c["bidder_notice"] for c in addendum_rules["classifications"]}
	conversions = {c["conversion_id"]: c for rule in addendum_rules["identity_rules"] for c in rule["conversions"]}
	identity_rules = {r["source_family"]: r for r in addendum_rules["identity_rules"]}
	before = _by_stable(prior)
	after = _by_stable(successor)
	out: list[dict[str, Any]] = []
	for key in sorted(set(before) | set(after)):
		old = before.get(key)
		new = after.get(key)
		family = (new or old)["identity"]["source_family"]
		conversion_id = None
		if old and new:
			if old["field"]["control_id"] != new["field"]["control_id"]:
				classification = "fresh_response_required"
			elif old["material_digest"] != new["material_digest"]:
				classification = "fresh_response_required"
			elif old["required"] != new["required"]:
				permitted = identity_rules[family]["conversions"]
				match = next((c for c in permitted if c["applies_when"] == "requiredness_changed"), None)
				if match:
					classification, conversion_id = "converted", match["conversion_id"]
				else:
					classification = "fresh_response_required"
			else:
				classification = "unchanged"
		elif old:
			classification = "removed"
		else:
			classification = "new"
		copy_prior = classification == "unchanged" or (classification == "converted" and conversions[conversion_id]["copy_prior_answer"])
		out.append(
			{
				"stable_key": key,
				"source_family": family,
				"classification": classification,
				"conversion_id": conversion_id,
				"prior_response_id": old["response_id"] if old else None,
				"successor_response_id": new["response_id"] if new else None,
				"copy_prior_answer": copy_prior,
				"affected_task_id": (new or old)["task_id"],
				"bidder_notice": conversions[conversion_id]["bidder_notice"] if conversion_id else notices[classification],
			}
		)
	return out


def incomplete_required(successor: dict[str, Any], classifications: list[dict[str, Any]]) -> list[str]:
	"""Successor responses that begin incomplete: required and not copied."""
	copied = {c["successor_response_id"] for c in classifications if c["copy_prior_answer"]}
	return [
		row["response_id"]
		for row in successor["response_rows"]
		if row["required"]["rule_id"] == "RQ-ALWAYS" and row["response_id"] not in copied
	]
