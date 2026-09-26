# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`release_manifest.json` (STD-TPL-001 v0.10 §13.9) and the owner decision
that binds it (§13.10; STD-TPL-IMP-001 v1.0 §5.1).

The manifest inventories every controlled asset, carries the named
constituent digests, the structured read projections the STD Templates
surface shows, the verification results and blockers, and is always
`Candidate` when constructed. Installation later binds the separate owner
decision and derives the lifecycle without rewriting approved bytes.
Pure Python: no Frappe import.
"""

from __future__ import annotations

import mimetypes
from collections import Counter
from typing import Any

from kentender_procurement.std_templates.compiler.canonical import is_sha256
from kentender_procurement.std_templates.compiler.errors import fail

MANIFEST_FIELDS: tuple[str, ...] = (
	"schema_version", "release_id", "template_key", "template_release", "display_name", "product_profile_id",
	"renderer_profile_id", "supported_renderer_version", "status", "supported_use", "rejected_use",
	"official_source_title", "official_source_digest", "source_retrieved_at", "repository_commit", "tool_versions",
	"assets", "document_summary", "response_summary", "evaluation_summary", "contract_summary", "reservation_support",
	"verification_results", "blockers", "source_checked_by", "source_checked_at", "source_check_outcome",
	"release_gates_digest", "release_change_report_digest", "validation_report_digest", "bundle_digest", "built_by", "built_at",
)
CONSTITUENT_DIGESTS: tuple[str, ...] = (
	"product_profile_digest", "response_rules_digest", "downstream_rules_digest", "addendum_identity_rules_digest",
)
ALL_FIELDS: tuple[str, ...] = MANIFEST_FIELDS + CONSTITUENT_DIGESTS + ("input_bundle_digest",)
LIFECYCLE_STATES: tuple[str, ...] = ("Candidate", "Available", "Superseded", "Withdrawn")
DECISIONS: tuple[str, ...] = ("APPROVE EXACT MANIFEST", "CORRECT AND RE-REVIEW", "REJECT PRODUCT RELEASE")
OWNER_DECISION_KEYS: tuple[str, ...] = (
	"schema_version", "release_id", "template_key", "template_release", "bundle_digest", "manifest_digest", "decision",
	"decided_by", "decided_at", "decision_record",
)

_ROLES: tuple[tuple[str, str], ...] = (
	("01_source/pages/", "Source page image"),
	("01_source/", "Official source"),
	("02_master/", "Document master"),
	("03_registers/", "Register"),
	("04_fixture/reservation_variants/", "Reservation variant fixture"),
	("04_fixture/", "Fixture"),
	("05_review/", "Review evidence"),
	("06_runtime/", "Runtime asset"),
)


def asset_role(path: str) -> str:
	for prefix, role in _ROLES:
		if path.startswith(prefix):
			return role
	return "Other"


def mime_type(path: str) -> str:
	if path.endswith(".json"):
		return "application/json"
	if path.endswith(".md"):
		return "text/markdown"
	if path.endswith(".csv"):
		return "text/csv"
	if path.endswith(".py"):
		return "text/x-python"
	return mimetypes.guess_type(path)[0] or "application/octet-stream"


def asset_rows(entries: list[tuple[str, str]], sizes: dict[str, int]) -> list[dict[str, Any]]:
	return [
		{"path": path, "sha256": digest, "byte_size": sizes[path], "asset_role": asset_role(path), "mime_type": mime_type(path)}
		for path, digest in entries
	]


# ---------------------------------------------------------------------------
# read projections (versioned; not editable UI metadata)
# ---------------------------------------------------------------------------


def document_summary(coverage_summary: dict[str, Any], insertion: list[dict[str, str]], forms: list[dict[str, str]]) -> dict[str, Any]:
	by_treatment: dict[str, list[str]] = {}
	for row in insertion:
		by_treatment.setdefault(row["source_treatment"], []).append(row["label"] or row["key"])
	included = [f for f in forms if f["included"].strip().upper() == "TRUE"]
	return {
		"schema_version": 1,
		"outputs": [
			{
				"output_id": "invitation",
				"title": "Invitation to Tender",
				"master": "02_master/invitation_to_tender.html",
				"summary": "Separate public notice; never embedded in the issued Tender.",
				"preview_asset": "04_fixture/moh_invitation_expected.pdf",
			},
			{
				"output_id": "issued_tender",
				"title": "Complete issued Tender",
				"master": "02_master/complete_tender.html",
				"summary": f"Cover, contents and Sections I–VIII; {len(included)} of {len(forms)} official forms published.",
				"preview_asset": "04_fixture/moh_expected.pdf",
			},
		],
		"coverage": coverage_summary,
		"inherited_from_requisition": sorted(set(by_treatment.get("Inherited", []))),
		"entered_during_tender_preparation": sorted(set(by_treatment.get("Officer value", []))),
		"generated_by_kentender": sorted(set(by_treatment.get("Generated", []))),
		"review_pack": "Download review pack",
	}


def response_summary(profile: dict[str, Any], rules: list[dict[str, Any]], fixture_definition: dict[str, Any], fixture_projection: dict[str, Any]) -> dict[str, Any]:
	family_rules = Counter(r["source_family"] for r in rules)
	locked = [r for r in rules if "locked_text" in r]
	evidence_fields = sum(1 for r in rules for f in r["field_definitions"] if f["control_id"] == "CTL-EVIDENCE-REFERENCE")
	groups = {g["group_key"] for s in fixture_definition["sections"] for g in s["groups"]}
	goods = [s for s in fixture_definition["sections"] if s["section_id"] == "TASK-REQUIREMENTS"][0]["groups"]
	goods_groups = [g for g in goods if g["source_family"] == "goods"]
	return {
		"schema_version": 1,
		"tasks": [{"task_id": t["task_id"], "order": t["order"], "label": t["label"], "purpose": t["purpose"]} for t in sorted(profile["tasks"], key=lambda t: t["order"])],
		"controls": [c["label"] for c in profile["controls"]],
		"compositions": [c["label"] for c in profile["compositions"]],
		"response_rule_count": len(rules),
		"response_family_rule_counts": dict(sorted(family_rules.items())),
		"declaration_treatment": f"{len(locked)} locked declarations; each repeats the anchored official wording and is affirmed against its exact text version.",
		"evidence_treatment": f"{evidence_fields} evidence-reference fields; each states its evidence type, count and link to the exact response.",
		"price_treatment": "Unit price and tax per published price row; line and Tender totals are calculated and read-only.",
		"fixture": {
			"tender_reference": fixture_projection["tender"]["reference"],
			"goods_lines": len(goods_groups),
			"requisition_items_grouped": sum(len(g["source_lineage"]["source_lineage"]) for g in goods_groups),
			"technical_requirements": len(fixture_projection["technical_requirements"]),
			"warranty_support_facts": len(fixture_projection["warranty_support"]),
			"acceptance_checks": len(fixture_projection["acceptance_requirements"]),
			"related_services": len(fixture_projection["related_services"]),
			"goods_price_schedules": 1 if any(r["kind"] == "Goods" for r in fixture_definition["price_rows"]) else 0,
			"response_groups": len(groups),
			"response_rows": len(fixture_definition["response_rows"]),
		},
	}


def evaluation_summary(profile: dict[str, Any], rules: list[dict[str, Any]], mappings: list[dict[str, Any]]) -> dict[str, Any]:
	labels = {r["rule_id"]: r for r in rules}
	by_group: dict[str, list[str]] = {}
	not_evaluated: list[dict[str, str]] = []
	for m in mappings:
		if m["evaluation_treatment"] == "Evaluated":
			by_group.setdefault(m["evaluation_group_id"], []).append(m["response_rule_id"])
		else:
			not_evaluated.append({"response_rule_id": m["response_rule_id"], "reason": m["reason"]})
	return {
		"schema_version": 1,
		"groups": [
			{
				"evaluation_group_id": g["evaluation_group_id"],
				"label": g["label"],
				"purpose": g["purpose"],
				"response_rule_ids": sorted(by_group.get(g["evaluation_group_id"], [])),
				"response_rule_count": len(by_group.get(g["evaluation_group_id"], [])),
			}
			for g in sorted(profile["evaluation_groups"], key=lambda g: g["order"])
		],
		"not_evaluated": not_evaluated,
		"weighted_criteria": 0,
		"technical_compliance_is_single_gate": True,
		"rule_count_checked": len(labels),
	}


def contract_summary(profile: dict[str, Any], mappings: list[dict[str, Any]]) -> dict[str, Any]:
	by_destination: dict[str, list[str]] = {}
	not_carried: list[dict[str, str]] = []
	for m in mappings:
		if m["contract_treatment"] == "Carried forward":
			by_destination.setdefault(m["contract_destination"], []).append(m["response_rule_id"])
		else:
			not_carried.append({"response_rule_id": m["response_rule_id"], "reason": m["reason"]})
	return {
		"schema_version": 1,
		"destinations": [
			{"contract_destination_id": d["contract_destination_id"], "label": d["label"], "response_rule_ids": sorted(by_destination.get(d["contract_destination_id"], []))}
			for d in profile["contract_destinations"]
		],
		"not_carried_forward": not_carried,
	}


def reservation_support(profile: dict[str, Any], mappings: list[dict[str, Any]], variants: list[dict[str, Any]]) -> dict[str, Any]:
	use = profile["supported_use"]
	reservation_mapping = next((m for m in mappings if m["response_rule_id"] == "RR-RESERVATION"), None)
	return {
		"schema_version": 1,
		"categories": list(use["reservation_categories"]),
		"county_residents": dict(use["county_residents"]),
		"eligibility_group_id": reservation_mapping["evaluation_group_id"] if reservation_mapping else None,
		"contract_treatment": reservation_mapping["contract_treatment"] if reservation_mapping else None,
		"award_reporting_treatment": reservation_mapping["award_reporting_treatment"] if reservation_mapping else None,
		"planning_designation_is_entitlement": False,
		"variants": variants,
	}


# ---------------------------------------------------------------------------
# validation (installer and validator)
# ---------------------------------------------------------------------------


def validate_shape(manifest: dict[str, Any]) -> None:
	if not isinstance(manifest, dict):
		fail("STD_RELEASE_INTEGRITY_FAILED", "The release manifest is not an object.", identity="release_manifest.json")
	keys = set(manifest)
	if keys != set(ALL_FIELDS):
		fail(
			"STD_RELEASE_INTEGRITY_FAILED",
			f"Manifest fields differ: missing {sorted(set(ALL_FIELDS) - keys)}, unknown {sorted(keys - set(ALL_FIELDS))}.",
			identity="release_manifest.json",
		)
	if manifest["status"] != "Candidate":
		fail("STD_RELEASE_INTEGRITY_FAILED", "A constructed manifest must be Candidate.", identity="status")
	for name in ("official_source_digest", "release_gates_digest", "release_change_report_digest", "validation_report_digest", "bundle_digest", "input_bundle_digest") + CONSTITUENT_DIGESTS:
		if not is_sha256(manifest[name]):
			fail("STD_RELEASE_INTEGRITY_FAILED", f"{name} is not a lowercase SHA-256 value.", identity=name)
	paths = [a["path"] for a in manifest["assets"]]
	if paths != sorted(paths, key=lambda p: p.encode("utf-8")) or len(set(paths)) != len(paths):
		fail("STD_RELEASE_INTEGRITY_FAILED", "Manifest assets are not unique and bytewise sorted.", identity="assets")


def validate_owner_decision(decision: dict[str, Any], manifest: dict[str, Any], manifest_digest: str) -> list[str]:
	"""Problems that stop the decision binding this exact manifest."""
	problems: list[str] = []
	if set(decision) != set(OWNER_DECISION_KEYS):
		return ["The owner decision fields differ from the released contract."]
	if decision["decision"] not in DECISIONS:
		problems.append("The owner decision is not one of the three permitted decisions.")
	for key in ("release_id", "template_key", "template_release", "bundle_digest"):
		if decision[key] != manifest[key]:
			problems.append(f"The owner decision names a different {key}.")
	if decision["manifest_digest"] != manifest_digest:
		problems.append("The owner decision names a different manifest.")
	if not str(decision.get("decided_by") or "").strip() or not str(decision.get("decided_at") or "").strip():
		problems.append("The owner decision has no named decider and time.")
	return problems
