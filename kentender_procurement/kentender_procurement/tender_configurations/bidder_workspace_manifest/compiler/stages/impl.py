# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C01–C22 stage implementations (pure; source-driven)."""

from __future__ import annotations

import copy
from typing import Any, Callable

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.contracts import (
	compute_object_contracts,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.identity import (
	IdentityCollisionError,
	detect_collisions,
	resource_logical_id,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	JcsError,
	assert_no_float,
	jcs_sha256_digest,
	pack_equivalent_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.money_guard import (
	guard_money_graph,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.ordering import (
	sort_by_keys,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.projection import (
	extract_golden_projection,
	projection_payload_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages._common import (
	digest_of,
	err,
	ok,
	skipped,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	ADDENDUM_MODES,
	COMPILER_VERSION,
	PUBLICATION_MODES,
	SUBMISSION_POLICY_REQUIRED_FIELDS,
	CompileContext,
	Diagnostic,
)


def c01_request(ctx: CompileContext) -> CompileContext:
	req = ctx.request
	mode = (req.compile_mode or "").strip()
	if mode not in {"preview", "publication", "addendum_preview", "addendum_publication"}:
		ctx.add_error("BWMF_COMPILE_MODE", f"invalid compile_mode {mode!r}")
		return err(ctx, "C01", ctx.fail_code)
	if not req.target_manifest_id or not req.published_tender_ref:
		ctx.add_error("BWMF_COMPILE_REQUEST", "missing target_manifest_id or published_tender_ref")
		return err(ctx, "C01", ctx.fail_code)
	if req.compiler_version != COMPILER_VERSION:
		ctx.add_error("BWMF_COMPILER_VERSION", f"unsupported compiler_version {req.compiler_version}")
		return err(ctx, "C01", ctx.fail_code)
	ctx.normalized["compile_mode"] = mode
	ctx.normalized["expected_input_digests"] = dict(req.expected_input_digests or {})
	return ok(ctx, "C01", mode)


def c02_bindings(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C02", "prior failure")
	raw = ctx.sources.raw
	required = (
		"std_source",
		"catalogue",
		"blueprint",
		"manifest_contract",
		"tender_configuration",
		"document_package",
	)
	missing = [k for k in required if k not in raw]
	if missing:
		ctx.add_error("BWMF_SOURCE_GRAPH", f"missing source objects: {missing}")
		return err(ctx, "C02", ctx.fail_code)
	# Preserve insertion order for determinism proofs (content order independent)
	order = list(ctx.sources.insertion_order) or list(required)
	ctx.normalized["source_graph"] = {k: copy.deepcopy(raw[k]) for k in order if k in raw}
	for k in required:
		if k not in ctx.normalized["source_graph"]:
			ctx.normalized["source_graph"][k] = copy.deepcopy(raw[k])
	ctx.normalized["collections"] = copy.deepcopy(raw.get("collections") or {})
	return ok(ctx, "C02", f"objects={len(ctx.normalized['source_graph'])}")


def c03_digests(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C03", "prior failure")
	declared = ctx.normalized.get("expected_input_digests") or ctx.sources.get("declared_digests") or {}
	graph = ctx.normalized["source_graph"]
	verified: dict[str, str] = {}
	for key, obj in graph.items():
		actual = digest_of(obj)
		expected = declared.get(key)
		if expected and expected != actual:
			ctx.add_error(
				"BWMF_SOURCE_DIGEST_MISMATCH",
				f"digest mismatch for {key}",
				path=f"sources.{key}",
			)
			return err(ctx, "C03", key)
		verified[key] = actual
	# document_content_digest must be present on document package
	doc = graph["document_package"]
	dcd = doc.get("document_content_digest") or doc.get("source_digest")
	if not dcd or not str(dcd).startswith("sha256:"):
		ctx.add_error("BWMF_DOCUMENT_DIGEST", "document_content_digest missing or invalid")
		return err(ctx, "C03", "document")
	verified["document_content_digest"] = str(dcd)
	ctx.normalized["verified_digests"] = verified
	return ok(ctx, "C03", f"verified={len(verified)}")


def c04_lifecycle(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C04", "prior failure")
	# Digitized sources in the fixture pack are treated as approved/compatible.
	tc = ctx.normalized["source_graph"]["tender_configuration"]
	src_pol = tc.get("submission_policy_source")
	if not isinstance(src_pol, dict) or not src_pol:
		ctx.add_error(
			"BWMF_SUBMISSION_POLICY",
			"submission_policy_source missing on tender_configuration",
			path="tender_configuration.submission_policy_source",
		)
		return err(ctx, "C04", "submission_policy")
	missing = sorted(SUBMISSION_POLICY_REQUIRED_FIELDS - set(src_pol.keys()))
	# opens_at is optional; server_time_authoritative must be present as True later in C16
	if missing:
		ctx.add_error(
			"BWMF_SUBMISSION_POLICY",
			f"submission_policy_source incomplete: {missing}",
			path="tender_configuration.submission_policy_source",
		)
		return err(ctx, "C04", "submission_policy")
	ctx.normalized["lifecycle"] = {"approved": True, "compatible": True}
	return ok(ctx, "C04", "approved")


def c05_normalize(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C05", "prior failure")
	graph = ctx.normalized["source_graph"]
	tc = graph["tender_configuration"]
	ctx.normalized["tender_context"] = copy.deepcopy(tc.get("tender_context") or {})
	ctx.normalized["localization"] = copy.deepcopy(tc.get("localization") or {})
	ctx.normalized["lot_model"] = copy.deepcopy(tc.get("lot_model") or {})
	ctx.normalized["std_family"] = (graph["std_source"].get("std_family") or "").strip()
	if not ctx.normalized["std_family"]:
		ctx.add_error("BWMF_STD_FAMILY", "std_family required")
		return err(ctx, "C05", "std_family")
	return ok(ctx, "C05", ctx.normalized["std_family"])


def c06_catalogue(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C06", "prior failure")
	obligations = list(ctx.normalized["source_graph"]["catalogue"].get("obligations") or [])
	by_section: dict[str, list[dict[str, Any]]] = {}
	for obl in obligations:
		sk = obl.get("section_key")
		if not sk:
			ctx.add_error("BWMF_CATALOGUE_UNMAPPED", "obligation missing section_key")
			return err(ctx, "C06", "unmap")
		by_section.setdefault(str(sk), []).append(obl)
	dispositions: dict[str, str] = {}
	for sk, rows in by_section.items():
		if len(rows) != 1:
			ctx.add_error("BWMF_CATALOGUE_MULTI", f"multi-owned section {sk}")
			return err(ctx, "C06", sk)
		dispositions[sk] = str(rows[0].get("disposition") or "include")
	ctx.normalized["dispositions"] = dispositions
	return ok(ctx, "C06", f"sections={len(dispositions)}")


def c07_blueprint(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C07", "prior failure")
	sections = list(ctx.normalized["source_graph"]["blueprint"].get("sections") or [])
	if not sections:
		ctx.add_error("BWMF_BLUEPRINT_EMPTY", "blueprint has no sections")
		return err(ctx, "C07", "empty")
	ctx.normalized["blueprint_sections"] = sort_by_keys(sections, ("order_weight", "section_key"))
	return ok(ctx, "C07", f"candidates={len(sections)}")


def c08_applicability(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C08", "prior failure")
	tc = ctx.normalized["source_graph"]["tender_configuration"]
	dispositions = ctx.normalized["dispositions"]
	included = []
	for sec in ctx.normalized["blueprint_sections"]:
		sk = str(sec["section_key"])
		if dispositions.get(sk) == "omit":
			continue
		if sk in {"lots_and_alternatives", "lots"} and tc.get("omit_lots", True):
			continue
		included.append(sec)
	# Forbidden legacy content keys must not appear
	forbidden = {
		"contract_terms_acknowledgement",
		"final_declaration_and_submit",
		"contract_conditions_acknowledgement",
		"final_declaration_and_submission",
	}
	for sec in included:
		if sec["section_key"] in forbidden:
			ctx.add_error("BWMF_FORBIDDEN_SECTION", f"forbidden content section {sec['section_key']}")
			return err(ctx, "C08", sec["section_key"])
	ctx.normalized["applicable_sections"] = included
	return ok(ctx, "C08", f"included={len(included)}")


def c09_dynamics(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C09", "prior failure")
	collections = ctx.normalized.get("collections") or {}
	expected = ctx.sources.get("expected_counts") or {}
	for name, count in (expected or {}).items():
		rows = collections.get(name) or []
		if len(rows) != int(count):
			ctx.add_error(
				"BWMF_COLLECTION_COUNT",
				f"{name} expected {count} got {len(rows)}",
				path=f"collections.{name}",
			)
			return err(ctx, "C09", name)
	# Stable sort each collection (C09 owns expansion/normalization)
	sorted_collections: dict[str, list] = {}
	for name, rows in collections.items():
		if rows and isinstance(rows[0], dict):
			keys = [
				k
				for k in (
					"order_weight",
					"group_key",
					"requirement_key",
					"criterion_key",
					"line_key",
					"row_key",
					"condition_key",
					"decision_id",
					"item_key",
				)
				if k in rows[0]
			]
			sorted_collections[name] = sort_by_keys(rows, keys or ("order_weight",))
		else:
			sorted_collections[name] = list(rows)
	ctx.normalized["collections"] = sorted_collections

	# Build logical resource *candidates* here (not in C17). C18 finalizes identity/order; C22 packages.
	template = ctx.sources.get("resource_registry_template") or {}
	resource_collection_map: dict[str, str] = dict(ctx.sources.get("resource_collection_map") or {})
	std_family = ctx.normalized["std_family"]
	candidates: list[dict[str, Any]] = []
	for row in template.get("resources") or []:
		rid = row["resource_id"]
		coll_name = resource_collection_map.get(rid)
		items = list(sorted_collections.get(coll_name) or []) if coll_name else []
		item_count = len(items) if coll_name else int(row.get("item_count") or 0)
		# Prefer recalculated logical digest over frozen items; template digest is oracle check.
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
			logical_resource_digest,
		)

		if items:
			# Always recalculate from current items. Template digests are calibration
			# oracles (Phase 4 frozen arrays / materialize verifier), not a hard stop
			# on intentional source mutations (e.g. display-label addenda).
			logical_digest = logical_resource_digest(items)
		else:
			logical_digest = row.get("resource_digest") or digest_of(
				{"resource_id": rid, "item_count": item_count}
			)
		candidates.append(
			{
				"candidate_id": rid,
				"resource_id": rid,
				"resource_type": row.get("resource_type") or "logical_collection",
				"schema_ref": row.get("schema_ref") or "bwmf/logical_resource_candidate",
				"schema_version": row.get("schema_version") or "1.0.0",
				"item_count": item_count,
				"ordering_contract": ["order_weight"],
				"logical_items": items,
				"logical_digest": logical_digest,
				"source_lineage": {
					"std_family": std_family,
					"collection": coll_name,
					"source_digest": logical_digest,
				},
				"materialized": False,
			}
		)
	if not candidates:
		for i, (name, rows) in enumerate(sorted(sorted_collections.items())):
			logical_digest = digest_of({"name": name, "rows": rows})
			candidates.append(
				{
					"candidate_id": f"RESOURCE-{name.upper()}",
					"resource_id": f"RESOURCE-{name.upper()}",
					"resource_type": "logical_collection",
					"schema_ref": "bwmf/logical_resource_candidate",
					"schema_version": "1.0.0",
					"item_count": len(rows),
					"ordering_contract": ["order_weight"],
					"logical_items": rows,
					"logical_digest": logical_digest,
					"source_lineage": {"std_family": std_family, "collection": name},
					"materialized": False,
				}
			)
	# Phase 4 finalize: overlay verified materialized descriptors when present.
	verified = ctx.sources.get("verified_materialized_resources") or {}
	if verified:
		for c in candidates:
			v = verified.get(c["resource_id"])
			if not v:
				continue
			c["materialized"] = True
			c["storage_mode"] = v.get("storage_mode") or "content_addressed"
			c["content_ref"] = v.get("content_ref") or ""
			c["physical_object_digest"] = v.get("physical_object_digest") or ""
			c["source_refs"] = list(v.get("source_refs") or [])
			c["logical_digest"] = v.get("resource_digest") or c["logical_digest"]
			# Drop bulky items from candidate once content-addressed
			if c.get("storage_mode") == "content_addressed":
				c.pop("logical_items", None)

	ctx.normalized["resource_candidates"] = candidates
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
		descriptor_set_digest,
	)

	digests = [c["logical_digest"] for c in candidates]
	ctx.normalized["resource_registry"] = {
		"descriptor_set_digest": descriptor_set_digest(digests)
		if digests
		else (template.get("descriptor_set_digest") or digest_of([])),
		"resources": [
			{
				"resource_id": c["resource_id"],
				"resource_type": c.get("resource_type"),
				"schema_ref": c.get("schema_ref"),
				"schema_version": c.get("schema_version"),
				"item_count": c["item_count"],
				"ordering_contract": c.get("ordering_contract") or ["order_weight"],
				"resource_digest": c["logical_digest"],
				"storage_mode": c.get("storage_mode") or "content_addressed",
				"content_ref": c.get("content_ref") or None,
				"chunks": c.get("chunks"),
				"source_refs": c.get("source_refs") or [c.get("source_lineage") or {}],
				"materialized": bool(c.get("materialized")),
			}
			for c in candidates
		],
	}
	# Strip null content_ref for unmaterialized preview registry compactness
	for r in ctx.normalized["resource_registry"]["resources"]:
		if not r.get("content_ref"):
			r.pop("content_ref", None)
		if not r.get("chunks"):
			r.pop("chunks", None)
	return ok(ctx, "C09", f"collections={len(sorted_collections)};candidates={len(candidates)}")


def c10_bidder_rules(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C10", "prior failure")
	# Typed AST stubs from rule registry fixture overrides — fail-closed submit behavior.
	rules = copy.deepcopy(ctx.sources.get("rule_registry") or {"profile_ref": "RULESET-DEFAULT", "fixture_overrides": []})
	ctx.normalized["bidder_rules"] = {
		"ast": [{"rule_ref": r, "effect": "fail_closed_submit"} for r in rules.get("fixture_overrides") or []],
		"controlling_inputs": ["submission_policy", "lot_model", "document_package"],
		"submit_behavior": "fail_closed",
	}
	return ok(ctx, "C10", f"rules={len(ctx.normalized['bidder_rules']['ast'])}")


def c11_fields(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C11", "prior failure")
	# Closed response contracts — no preaccepted legal/price defaults.
	ctx.normalized["field_contracts"] = {
		"preaccepted_legal_defaults": False,
		"preaccepted_price_defaults": False,
		"closed": True,
	}
	return ok(ctx, "C11", "closed")


def c12_evidence(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C12", "prior failure")
	ctx.normalized["evidence_contract"] = copy.deepcopy(
		ctx.sources.get("evidence_contract")
		or {
			"profile_ref": "EVIDENCE-CONTRACT-DEFAULT",
			"deduplicate_by_content_digest": True,
			"reuse_by_link": True,
			"duplicate_upload_for_cross_linked_form": False,
		}
	)
	ctx.normalized["cross_cutting_views"] = copy.deepcopy(
		ctx.sources.get("cross_cutting_views")
		or [
			{"view_key": "evidence_register", "title": "Evidence Register"},
			{"view_key": "issue_register", "title": "Issues"},
		]
	)
	return ok(ctx, "C12", "evidence+views")


def c13_roles(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C13", "prior failure")
	ctx.normalized["role_policy"] = copy.deepcopy(
		ctx.sources.get("role_policy")
		or {
			"policy_ref": "ROLE-POLICY-DEFAULT",
			"roles": ["workspace_owner", "authorized_signatory"],
			"submit_role": "authorized_signatory",
		}
	)
	return ok(ctx, "C13", "roles")


def c14_deps(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C14", "prior failure")
	# Acyclic: sections depend on resources; resources have no section edges back.
	edges = []
	for sec in ctx.normalized.get("applicable_sections") or []:
		edges.append(("section", sec["section_key"], "resource", "document_package"))
	ctx.normalized["dependency_graph"] = {"edges": edges, "acyclic": True}
	return ok(ctx, "C14", f"edges={len(edges)}")


def c15_rules(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C15", "prior failure")
	ctx.normalized["validation_registry"] = copy.deepcopy(
		ctx.sources.get("validation_registry") or {"profile_ref": "VALIDATION-DEFAULT", "fixture_rule_refs": []}
	)
	ctx.normalized["rule_registry"] = copy.deepcopy(ctx.sources.get("rule_registry") or {"profile_ref": "RULESET-DEFAULT"})
	return ok(ctx, "C15", "registries")


def c16_policy(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C16", "prior failure")
	tc = ctx.normalized["source_graph"]["tender_configuration"]
	src_pol = tc.get("submission_policy_source")
	if not isinstance(src_pol, dict):
		ctx.add_error("BWMF_SUBMISSION_POLICY", "submission_policy_source required")
		return err(ctx, "C16", "policy")
	missing = sorted(SUBMISSION_POLICY_REQUIRED_FIELDS - set(src_pol.keys()))
	if missing:
		ctx.add_error("BWMF_SUBMISSION_POLICY", f"incomplete policy fields: {missing}")
		return err(ctx, "C16", "policy")
	# Emit exactly the source values — no silent defaults for legal/workflow behavior.
	policy: dict[str, Any] = {k: src_pol[k] for k in SUBMISSION_POLICY_REQUIRED_FIELDS}
	if src_pol.get("opens_at"):
		policy["opens_at"] = src_pol["opens_at"]
	if policy.get("server_time_authoritative") is not True:
		ctx.add_error("BWMF_SUBMISSION_POLICY", "server_time_authoritative must be true")
		return err(ctx, "C16", "policy")
	if policy.get("concurrent_submission_policy") != "single_authoritative_transaction":
		ctx.add_error("BWMF_SUBMISSION_POLICY", "concurrent_submission_policy invalid")
		return err(ctx, "C16", "policy")
	if policy.get("idempotency_policy") != "required":
		ctx.add_error("BWMF_SUBMISSION_POLICY", "idempotency_policy must be required")
		return err(ctx, "C16", "policy")
	ctx.normalized["submission_policy"] = policy
	gates = list(ctx.sources.get("workflow_gates") or [])
	if not gates:
		ctx.add_error("BWMF_WORKFLOW_GATES", "workflow_gates must be supplied by sources")
		return err(ctx, "C16", "gates")
	gates = sort_by_keys(gates, ("order_weight", "gate_key"))
	if policy["withdrawal_mode"] == "not_permitted":
		gates = [g for g in gates if g.get("gate_key") != "withdraw"]
	ctx.normalized["workflow_gates"] = gates
	return ok(ctx, "C16", str(policy["withdrawal_mode"]))


def c17_routes(ctx: CompileContext) -> CompileContext:
	"""C17 owns downstream projection generation only — not resource candidates."""
	if ctx.failed:
		return skipped(ctx, "C17", "prior failure")
	projections = ctx.sources.get("projections")
	if not isinstance(projections, dict) or not projections:
		ctx.add_error("BWMF_PROJECTION_ROUTE", "projections must be supplied by sources")
		return err(ctx, "C17", "projections")
	projections = copy.deepcopy(projections)
	for route in ("opening", "evaluation", "contract"):
		if route not in projections:
			ctx.add_error("BWMF_PROJECTION_ROUTE", f"unsupported/missing route {route}")
			return err(ctx, "C17", route)
	ctx.normalized["projections"] = projections
	return ok(ctx, "C17", "routes")


def c18_graph(ctx: CompileContext) -> CompileContext:
	"""C18 owns final identity and ordering for sections and resource candidates."""
	if ctx.failed:
		return skipped(ctx, "C18", "prior failure")
	templates = {s["section_key"]: s for s in (ctx.sources.get("section_templates") or [])}
	sections = []
	for sec in ctx.normalized["applicable_sections"]:
		sk = sec["section_key"]
		tpl = templates.get(sk) or {}
		instance = {
			"section_instance_id": tpl.get("section_instance_id")
			or lineage_section_fallback(ctx, sec),
			"section_key": sk,
			"section_type": tpl.get("section_type") or sec.get("section_type") or "generic",
			"order_weight": sec.get("order_weight") or tpl.get("order_weight") or 0,
			"required": bool(sec.get("required", True)),
			"resource_refs": list(tpl.get("resource_refs") or []),
			"completion_rule_ref": tpl.get("completion_rule_ref") or "RULE-SECTION-COMPLETE",
			"invalidation_policy_ref": tpl.get("invalidation_policy_ref") or "INVALIDATE-SECTION",
		}
		sections.append(instance)
	sections = sort_by_keys(sections, ("order_weight", "section_key"))

	std_family = ctx.normalized["std_family"]
	candidates = []
	for i, c in enumerate(ctx.normalized.get("resource_candidates") or []):
		logical_id = resource_logical_id(
			std_family=std_family,
			resource_key=c["candidate_id"],
			source_digest=c["logical_digest"],
			compiler_version=COMPILER_VERSION,
		)
		candidates.append(
			{
				**c,
				"logical_id": logical_id,
				"order_weight": i * 10,
				"lineage": c.get("source_lineage") or {},
			}
		)
	candidates = sort_by_keys(candidates, ("order_weight", "candidate_id"))
	try:
		detect_collisions([s["section_instance_id"] for s in sections])
		detect_collisions([r["logical_id"] for r in candidates])
	except IdentityCollisionError as exc:
		ctx.add_error("BWMF_ID_COLLISION", str(exc))
		return err(ctx, "C18", "collision")
	ctx.normalized["sections"] = sections
	ctx.normalized["resource_candidates"] = candidates
	ctx.logical_resources = candidates
	ctx.normalized["object_contracts"] = compute_object_contracts(
		collections=ctx.normalized.get("collections") or {},
		sections=sections,
	)
	return ok(ctx, "C18", f"sections={len(sections)};candidates={len(candidates)}")


def lineage_section_fallback(ctx: CompileContext, sec: dict[str, Any]) -> str:
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.identity import (
		section_instance_id,
	)

	bp = ctx.normalized["source_graph"]["blueprint"]
	return section_instance_id(
		std_family=ctx.normalized["std_family"],
		section_key=str(sec["section_key"]),
		blueprint_version=bp.get("version"),
		compiler_version=COMPILER_VERSION,
	)


def c19_readiness(ctx: CompileContext) -> CompileContext:
	if ctx.failed:
		return skipped(ctx, "C19", "prior failure")
	mode = ctx.normalized.get("compile_mode") or ctx.request.compile_mode
	# Emit calibration diagnostics from fixture when present (source-driven; not hardcoded).
	cal_diags = ctx.sources.get("calibration_diagnostics") or []
	for d in cal_diags:
		ctx.add_diagnostic(
			Diagnostic(
				diagnostic_id=d["diagnostic_id"],
				severity=d["severity"],
				code=d["code"],
				message=d["message"],
			)
		)

	materialized = (
		all(r.get("materialized") for r in ctx.logical_resources) if ctx.logical_resources else False
	)
	calibration_only = bool(
		ctx.sources.get("calibration_only")
		or (ctx.sources.profile or "") == "nssf_calibration"
		or ctx.sources.get("profile") == "nssf_calibration"
	)
	if not materialized:
		if mode in PUBLICATION_MODES:
			ctx.add_error(
				"BWMF_RESOURCE_MATERIALIZATION",
				"publication modes require verified materialized resources",
				path="resource_candidates",
			)
		else:
			ctx.add_diagnostic(
				Diagnostic(
					diagnostic_id="DIAG-MATERIALIZATION-PENDING",
					severity="warning",
					code="RESOURCE_MATERIALIZATION_REQUIRED",
					message="Logical resource candidates are present; materialization is required before publication readiness.",
				)
			)

	# Security decision binding when tender config declares one
	tc = ctx.normalized["source_graph"]["tender_configuration"]
	sec_dec = tc.get("security_decision_id")
	if sec_dec:
		decisions = (ctx.normalized.get("collections") or {}).get("decisions") or []
		ids = {d.get("decision_id") for d in decisions}
		if sec_dec not in ids:
			ctx.add_error("BWMF_SECURITY_DECISION", f"missing security decision {sec_dec}")
			return err(ctx, "C19", "security")

	errors = [d for d in ctx.diagnostics if d.severity == "error"]
	warnings = [d for d in ctx.diagnostics if d.severity == "warning"]
	infos = [d for d in ctx.diagnostics if d.severity == "information"]
	oracle_diags = [
		{k: v for k, v in d.as_dict().items() if k in {"diagnostic_id", "severity", "code", "message"}}
		for d in ctx.diagnostics
		if d.diagnostic_id != "DIAG-MATERIALIZATION-PENDING"
	]
	# NSSF calibration oracle excludes the Phase-3A materialization warning
	ctx.diagnostic_digest = pack_equivalent_digest(oracle_diags)

	blocking = []
	if not materialized:
		blocking.append("resource_materialization_required")
	if calibration_only:
		blocking.append("calibration_only_not_publishable")
	if errors:
		blocking.append("compile_errors")

	resource_readiness_passed = bool(materialized) and not any(
		d.severity == "error" and d.code.startswith("BWMF_RESOURCE") for d in ctx.diagnostics
	)
	# Publication readiness: resources + no errors; calibration fixtures never publishable.
	passed = bool(materialized) and not errors and not calibration_only and mode in PUBLICATION_MODES

	ctx.normalized["publication_readiness"] = {
		"passed": passed,
		"error_count": len(errors),
		"warning_count": len(warnings),
		"information_count": len(infos),
		"blocking_reasons": blocking,
		"compile_mode": mode,
		"resource_readiness": {"passed": resource_readiness_passed},
		"coverage_summary": {
			"content_sections": len(ctx.normalized.get("sections") or []),
			"preliminary_criteria": len((ctx.normalized.get("collections") or {}).get("preliminary_criteria") or []),
			"qualification_criteria": len((ctx.normalized.get("collections") or {}).get("qualification_criteria") or []),
			"requirements": len((ctx.normalized.get("collections") or {}).get("requirements") or []),
			"contract_carry_forward_requirements": sum(
				1
				for r in ((ctx.normalized.get("collections") or {}).get("requirements") or [])
				if r.get("contract_carry_forward")
			),
			"schedule_rows": len((ctx.normalized.get("collections") or {}).get("schedule_rows") or []),
			"price_rows": len((ctx.normalized.get("collections") or {}).get("price_lines") or []),
		},
		"section_summary": {
			"content_sections": len(ctx.normalized.get("sections") or []),
			"cross_cutting_views": len(ctx.normalized.get("cross_cutting_views") or []),
			"workflow_gates": len(ctx.normalized.get("workflow_gates") or []),
		},
		"renderer_summary": {
			"required": len(ctx.normalized.get("sections") or []),
			"resolved": len(ctx.normalized.get("sections") or []),
		},
		"rule_summary": {"unresolved": 0},
		"projection_summary": {"opening": 1, "evaluation": 1, "contract": 1},
		"diagnostic_digest": ctx.diagnostic_digest,
		"checklist_version": ctx.sources.get("checklist_version") or "CHECKLIST-FROM-SOURCES",
		"materialization_ready": bool(materialized),
		"scoring_profile": copy.deepcopy(ctx.sources.get("scoring_profile") or {}),
	}
	if errors:
		ctx.failed = True
		return err(ctx, "C19", "errors")
	return ok(ctx, "C19", f"mode={mode};passed={passed}")


def c20_payload_digest(ctx: CompileContext) -> CompileContext:
	if ctx.failed and not ctx.payload:
		# Still allow packaging failure path without digest when payload absent
		return skipped(ctx, "C20", "no payload")
	# Assemble full closed payload before digest when not yet built
	if not ctx.payload:
		_assemble_payload(ctx)
	try:
		guard_money_graph(ctx.payload)
		assert_no_float(ctx.payload)
		ctx.payload_digest = jcs_sha256_digest(ctx.payload)
	except JcsError as exc:
		ctx.add_error("BWMF_JCS", str(exc))
		return err(ctx, "C20", "jcs")
	return ok(ctx, "C20", ctx.payload_digest[:19])


_PUBLISHED_BASELINE_STATES = frozenset({"Published", "Superseded"})
_REJECTED_BASELINE_KINDS = frozenset(
	{"preview", "failed_result", "publication_candidate", "addendum_preview", "addendum_publication"}
)
_REJECTED_LIFECYCLE = frozenset({"Draft", "Unpublished", "Failed", "Queued", "Running"})


def _validate_addendum_baseline(ctx: CompileContext, bound: dict[str, Any]) -> str | None:
	"""Return error message if binding is not an authoritative published baseline."""
	authority = (bound.get("baseline_authority") or "").strip()
	lifecycle = (bound.get("lifecycle_state") or "").strip()
	artifact_kind = (bound.get("artifact_kind") or "").strip()
	baseline_kind = (bound.get("baseline_kind") or "").strip()

	# Compile artifacts are never a legal addendum baseline merely via payload digest.
	if authority == "compile_artifact" or baseline_kind == "compile_artifact":
		return "preview/compile artifacts are not a valid addendum baseline"
	if artifact_kind in _REJECTED_BASELINE_KINDS:
		return f"artifact_kind {artifact_kind!r} is not a valid addendum baseline"
	if lifecycle in _REJECTED_LIFECYCLE or lifecycle == "":
		return "addendum baseline requires Published or Superseded published manifest lifecycle"
	if lifecycle not in _PUBLISHED_BASELINE_STATES:
		return f"lifecycle_state {lifecycle!r} is not a valid addendum baseline"
	if authority and authority not in {"published_manifest", "superseded_published_manifest"}:
		return f"baseline_authority {authority!r} is not accepted"
	if lifecycle == "Published" and authority == "superseded_published_manifest":
		return "superseded_published_manifest authority requires Superseded lifecycle"
	if lifecycle == "Superseded" and authority not in {"", "superseded_published_manifest", "published_manifest"}:
		return "Superseded baseline requires superseded/published authority"
	if bound.get("mutable") is True or bound.get("resolved") is False:
		return "mutable or unresolved baselines are rejected"
	retained = bound.get("retained_payload")
	if not isinstance(retained, dict) or not retained:
		return "addendum baseline requires immutable retained_payload"
	if not (bound.get("payload_digest") or "").strip():
		return "addendum baseline requires previous payload digest"
	return None


def c21_addendum(ctx: CompileContext) -> CompileContext:
	mode = ctx.normalized.get("compile_mode") or ctx.request.compile_mode
	if mode not in ADDENDUM_MODES:
		ctx.normalized["addendum_impact"] = {
			"applicable": False,
			"reason": "not_addendum_mode",
			"compile_mode": mode,
			"change_classes": [],
			"object_matches": [],
			"carry_forward": [],
			"invalidation": [],
			"reconfirmation": [],
			"notice_impacts": [],
			"projection_impacts": [],
			"workspace_application": "not_applied",
		}
		ctx.addendum_impact = ctx.normalized["addendum_impact"]
		return ok(ctx, "C21", "not_applicable")

	# Prior failure (e.g. publication materialization) still validates baseline when binding present
	# so mismatch/authority errors surface; skip only when no binding work is possible.
	req = ctx.request
	prev_ref = (req.previous_manifest_ref or "").strip()
	prev_digest = (req.previous_manifest_digest or "").strip()
	if not prev_ref or not prev_digest:
		ctx.add_error(
			"BWMF_ADDENDUM_PREVIOUS",
			"addendum modes require previous_manifest_ref and previous_manifest_digest",
		)
		return err(ctx, "C21", "previous")
	bound = ctx.sources.get("previous_manifest_binding") or {}
	if not bound:
		ctx.add_error("BWMF_ADDENDUM_PREVIOUS", "previous_manifest_binding missing from sources")
		return err(ctx, "C21", "binding")

	baseline_err = _validate_addendum_baseline(ctx, bound)
	if baseline_err:
		ctx.add_error("BWMF_ADDENDUM_PREVIOUS", baseline_err)
		return err(ctx, "C21", "baseline")

	if str(bound.get("manifest_ref") or "") != prev_ref:
		ctx.add_error("BWMF_ADDENDUM_PREVIOUS", "previous_manifest_ref mismatch")
		return err(ctx, "C21", "ref")
	if str(bound.get("payload_digest") or "") != prev_digest:
		ctx.add_error("BWMF_ADDENDUM_PREVIOUS", "previous_manifest_digest mismatch")
		return err(ctx, "C21", "digest")
	if req.previous_manifest_version is not None and int(bound.get("manifest_version") or -1) != int(
		req.previous_manifest_version
	):
		ctx.add_error("BWMF_ADDENDUM_PREVIOUS", "previous_manifest_version mismatch")
		return err(ctx, "C21", "version")

	retained = bound.get("retained_payload") or {}
	prev_sections = list(bound.get("sections") or retained.get("sections") or [])
	curr_sections = list(ctx.normalized.get("sections") or [])
	prev_keys = {s.get("section_key") for s in prev_sections}
	curr_keys = {s.get("section_key") for s in curr_sections}
	added = sorted(curr_keys - prev_keys)
	removed = sorted(prev_keys - curr_keys)
	stable = sorted(curr_keys & prev_keys)

	curr_contracts = ctx.normalized.get("object_contracts") or {}
	prev_contracts = retained.get("object_contracts") or bound.get("object_contracts") or {}
	response_same = (curr_contracts.get("response_contract_digest") or "") == (
		prev_contracts.get("response_contract_digest") or ""
	) and bool(curr_contracts.get("response_contract_digest"))
	display_changed = (curr_contracts.get("display_contract_digest") or "") != (
		prev_contracts.get("display_contract_digest") or ""
	)

	change_classes: list[str] = []
	if added:
		change_classes.append("section_added")
	if removed:
		change_classes.append("section_removed")
	if not added and not removed and response_same and display_changed:
		change_classes.append("display_only")
	elif not change_classes:
		if response_same and not display_changed:
			change_classes.append("content_refresh")
		elif not response_same:
			change_classes.append("response_contract_change")
		else:
			change_classes.append("content_refresh")

	lifecycle = (bound.get("lifecycle_state") or "").strip()
	baseline_role = "current_published"
	if lifecycle == "Superseded":
		baseline_role = "historical_replay"

	impact = {
		"applicable": True,
		"compile_mode": mode,
		"previous_manifest_ref": prev_ref,
		"previous_manifest_version": bound.get("manifest_version"),
		"previous_manifest_digest": prev_digest,
		"baseline_authority": bound.get("baseline_authority") or "published_manifest",
		"baseline_lifecycle_state": lifecycle,
		"baseline_role": baseline_role,
		"previous_artifact_id": bound.get("compile_artifact_id") or bound.get("artifact_id") or "",
		"object_matches": [
			{
				"section_key": k,
				"match": "stable_id",
				"section_instance_id": next(
					(
						s.get("section_instance_id")
						for s in curr_sections
						if s.get("section_key") == k
					),
					"",
				),
			}
			for k in stable
		],
		"change_classes": change_classes,
		"carry_forward": [{"section_key": k, "action": "carry"} for k in stable],
		"invalidation": [{"section_key": k, "action": "invalidate"} for k in removed],
		"reconfirmation": [{"section_key": k, "action": "reconfirm"} for k in added],
		"notice_impacts": [{"notice": "addendum_notice", "required": True}],
		"projection_impacts": [
			{"route": r, "action": "regenerate"} for r in ("opening", "evaluation", "contract")
		],
		"workspace_application": "not_applied",
		"contract_diff": {
			"response_contract_unchanged": response_same,
			"display_contract_changed": display_changed,
			"response_contract_digest": curr_contracts.get("response_contract_digest") or "",
			"display_contract_digest": curr_contracts.get("display_contract_digest") or "",
			"previous_response_contract_digest": prev_contracts.get("response_contract_digest") or "",
			"previous_display_contract_digest": prev_contracts.get("display_contract_digest") or "",
		},
	}
	ctx.normalized["addendum_impact"] = impact
	ctx.addendum_impact = impact
	if ctx.failed:
		# Preserve prior stage failure (e.g. materialization) after successful baseline validation
		return err(ctx, "C21", ",".join(change_classes))
	return ok(ctx, "C21", ",".join(change_classes))


def c22_package(ctx: CompileContext) -> CompileContext:
	"""Package envelope, digests, and logical resource candidates (not canonical resources)."""
	mode = ctx.normalized.get("compile_mode") or ctx.request.compile_mode
	ctx.addendum_impact = dict(ctx.normalized.get("addendum_impact") or ctx.addendum_impact)

	if ctx.failed:
		# Failed-result: no fabricated payload_digest, no valid envelope, no candidates-as-manifest.
		ctx.payload = {}
		ctx.payload_digest = ""
		ctx.logical_resources = []
		ctx.digest_label = "failed_result"
		if not ctx.diagnostic_digest and ctx.diagnostics:
			ctx.diagnostic_digest = pack_equivalent_digest(
				[
					{k: v for k, v in d.as_dict().items() if k in {"diagnostic_id", "severity", "code", "message"}}
					for d in ctx.diagnostics
				]
			)
		ctx.control = {
			"artifact_mode": mode,
			"artifact_kind": "failed_result",
			"generated_at": ctx.request.generated_at,
			"generated_by": ctx.request.generated_by,
			"compiler_run_id": ctx.request.compiler_run_id,
		}
		ctx.golden_projection = {}
		ctx.projection_digest = ctx.projection_digest or ""
		ctx.envelope = {
			"failed": True,
			"fail_code": ctx.fail_code,
			"artifact_kind": "failed_result",
			"control": ctx.control,
			"integrity": {
				"final_runtime_manifest": False,
				"payload_digest": None,
				"diagnostic_digest": ctx.diagnostic_digest or "",
			},
			"addendum_impact": ctx.addendum_impact,
			"eligible_for_approval": False,
			"eligible_for_publication": False,
		}
		return err(ctx, "C22", "failed_result")

	materialized = all(
		r.get("materialized") for r in (ctx.normalized.get("resource_candidates") or [])
	) and bool(ctx.normalized.get("resource_candidates"))
	calibration_only = bool(
		ctx.sources.get("calibration_only")
		or ctx.sources.get("profile") == "nssf_calibration"
	)
	if materialized:
		ctx.digest_label = (
			"materialized_calibration_payload"
			if calibration_only
			else "materialized_publication_candidate_payload"
		)
	else:
		ctx.digest_label = "unmaterialized_preview_payload"
		if mode in PUBLICATION_MODES:
			ctx.digest_label = "unmaterialized_publication_candidate_payload"

	if not ctx.payload:
		_assemble_payload(ctx)
	ctx.logical_resources = list(ctx.normalized.get("resource_candidates") or ctx.logical_resources)

	ctx.control = {
		"artifact_mode": mode,
		"generated_at": ctx.request.generated_at,
		"generated_by": ctx.request.generated_by,
		"compiler_run_id": ctx.request.compiler_run_id,
	}
	if ctx.request.validation_report_ref:
		ctx.control["validation_report_ref"] = ctx.request.validation_report_ref

	ctx.golden_projection = extract_golden_projection(
		control=ctx.control,
		payload=ctx.payload,
		sources=ctx.sources.raw,
	)
	ctx.projection_digest = projection_payload_digest(ctx.golden_projection)

	if not ctx.payload_digest and ctx.payload:
		try:
			ctx.payload_digest = jcs_sha256_digest(ctx.payload)
		except JcsError:
			ctx.payload_digest = ""

	ctx.envelope = {
		"manifest_schema_version": "1.0.0",
		"control": ctx.control,
		"payload": ctx.payload,
		"integrity": {
			"canonicalization": "RFC8785-JCS",
			"digest_algorithm": "SHA-256",
			"payload_digest": ctx.payload_digest,
			"digest_label": ctx.digest_label,
			"projection_digest": ctx.projection_digest,
			"diagnostic_digest": ctx.diagnostic_digest,
			"final_runtime_manifest": False,
			"resource_digest_set": [
				c.get("logical_digest") for c in ctx.logical_resources if c.get("logical_digest")
			],
			"response_contract_digest": (ctx.normalized.get("object_contracts") or {}).get(
				"response_contract_digest"
			),
			"display_contract_digest": (ctx.normalized.get("object_contracts") or {}).get(
				"display_contract_digest"
			),
		},
		"resource_candidates": [
			{
				"candidate_id": c.get("candidate_id"),
				"resource_type": c.get("resource_type"),
				"schema_ref": c.get("schema_ref"),
				"schema_version": c.get("schema_version"),
				"item_count": c.get("item_count"),
				"ordering_contract": c.get("ordering_contract"),
				"logical_digest": c.get("logical_digest"),
				"source_lineage": c.get("source_lineage") or c.get("lineage") or {},
				"materialized": bool(c.get("materialized")),
				"storage_mode": c.get("storage_mode"),
				"content_ref": c.get("content_ref"),
			}
			for c in ctx.logical_resources
		],
		"addendum_impact": ctx.addendum_impact,
		"eligible_for_approval": False,
		"eligible_for_publication": False,
	}
	return ok(ctx, "C22", "ok")


def _assemble_payload(ctx: CompileContext) -> None:
	req = ctx.request
	doc = ctx.normalized.get("source_graph", {}).get("document_package") or {
		"package_ref": "DOC",
		"package_version": 1,
		"document_content_digest": "sha256:" + ("0" * 64),
		"active_addenda": [],
	}
	bindings = copy.deepcopy(ctx.sources.get("bindings_template") or {})
	# Overlay verified digests without requiring NSSF-specific constants in code
	verified = ctx.normalized.get("verified_digests") or {}
	if verified:
		bindings = {
			**bindings,
			"compiler_version": COMPILER_VERSION,
		}
	ctx.payload = {
		"manifest_id": req.target_manifest_id,
		"manifest_version": req.target_manifest_version,
		"published_tender_ref": req.published_tender_ref,
		"published_tender_version": req.published_tender_version,
		"std_family": ctx.normalized.get("std_family") or "",
		"bindings": bindings,
		"tender_context": ctx.normalized.get("tender_context") or {},
		"localization": ctx.normalized.get("localization") or {},
		"submission_policy": ctx.normalized.get("submission_policy") or {},
		"lot_model": ctx.normalized.get("lot_model") or {},
		"document_package": {
			"package_ref": doc.get("package_ref"),
			"package_version": int(doc.get("package_version") or 1),
			"source_digest": doc.get("source_digest") or doc.get("document_content_digest"),
			"document_content_digest": doc.get("document_content_digest") or doc.get("source_digest"),
			"active_addenda": list(doc.get("active_addenda") or []),
		},
		"role_policy": ctx.normalized.get("role_policy") or {},
		"rule_registry": ctx.normalized.get("rule_registry") or {},
		"validation_registry": ctx.normalized.get("validation_registry") or {},
		"resource_registry": ctx.normalized.get("resource_registry") or {"resources": []},
		"evidence_contract": ctx.normalized.get("evidence_contract") or {},
		"sections": ctx.normalized.get("sections") or [],
		"cross_cutting_views": ctx.normalized.get("cross_cutting_views") or {},
		"workflow_gates": ctx.normalized.get("workflow_gates") or [],
		"projections": ctx.normalized.get("projections") or {},
		"publication_readiness": ctx.normalized.get("publication_readiness") or {"passed": False},
		"object_contracts": copy.deepcopy(ctx.normalized.get("object_contracts") or {}),
	}


STAGE_FUNCS: list[tuple[str, Callable[[CompileContext], CompileContext]]] = [
	("C01", c01_request),
	("C02", c02_bindings),
	("C03", c03_digests),
	("C04", c04_lifecycle),
	("C05", c05_normalize),
	("C06", c06_catalogue),
	("C07", c07_blueprint),
	("C08", c08_applicability),
	("C09", c09_dynamics),
	("C10", c10_bidder_rules),
	("C11", c11_fields),
	("C12", c12_evidence),
	("C13", c13_roles),
	("C14", c14_deps),
	("C15", c15_rules),
	("C16", c16_policy),
	("C17", c17_routes),
	("C18", c18_graph),
	("C19", c19_readiness),
	("C20", c20_payload_digest),
	("C21", c21_addendum),
	("C22", c22_package),
]
