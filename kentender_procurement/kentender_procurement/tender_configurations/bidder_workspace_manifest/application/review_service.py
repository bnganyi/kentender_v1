# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Immutable publication review package prepare + submit."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.eligibility import (
	assert_eligible_for_review,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.lifecycle_events import (
	emit_lifecycle_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.roles import (
	ROLE_APPROVER,
	ROLE_CONFIGURATOR,
	ROLE_REVIEWER,
	require_org_scope,
	require_role,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ADDENDUM_IMPACT_PLAN,
	DT_REVIEW_PACKAGE,
	DT_VALIDATION_REPORT,
)


def approve_impact_plan(
	*,
	plan_id: str,
	organization: str,
	actor_org: str | None = None,
) -> str:
	"""Mark an addendum impact plan Approved (immutable thereafter)."""
	actor = require_role(ROLE_APPROVER)
	require_org_scope(organization, actor_org=actor_org)
	name = plan_id if frappe.db.exists(DT_ADDENDUM_IMPACT_PLAN, plan_id) else frappe.db.get_value(
		DT_ADDENDUM_IMPACT_PLAN, {"plan_id": plan_id}, "name"
	)
	if not name:
		frappe.throw(_("Impact plan not found."), title="BWMF_IMPACT_PLAN")
	doc = frappe.get_doc(DT_ADDENDUM_IMPACT_PLAN, name)
	if doc.status in {"Approved", "Immutable"}:
		return doc.name
	doc.status = "Approved"
	doc.save(ignore_permissions=True)
	emit_lifecycle_event(
		event_type="addendum_impact_plan.approved",
		organization=organization,
		actor=actor,
		correlation_ref=doc.plan_id,
		affected_refs={"impact_plan": doc.name, "plan_digest": doc.plan_digest},
	)
	return doc.name


def prepare_review_package(
	*,
	package_id: str,
	compile_artifact: str,
	organization: str,
	published_tender_ref: str = "",
	published_tender_version: int | None = None,
	proposed_manifest_version: int | None = None,
	impact_plan: str = "",
	actor_org: str | None = None,
	package_version: int = 1,
) -> dict[str, Any]:
	"""Create an immutable-content review package in Prepared state (not yet frozen)."""
	actor = require_role(ROLE_CONFIGURATOR, ROLE_REVIEWER)
	require_org_scope(organization, actor_org=actor_org)

	elig = assert_eligible_for_review(compile_artifact)
	art = elig["artifact"]
	payload = elig["payload"]

	tender_ref = published_tender_ref or payload.get("published_tender_ref") or art.target_manifest_id
	tender_ver = int(
		published_tender_version
		if published_tender_version is not None
		else (payload.get("published_tender_version") or art.target_manifest_version or 1)
	)
	proposed = int(
		proposed_manifest_version
		if proposed_manifest_version is not None
		else (art.target_manifest_version or 1)
	)

	# Source binding digests from payload / envelope when present
	sources = payload.get("source_bindings") or payload.get("sources") or {}
	cfg = sources.get("configuration_snapshot") or payload.get("configuration_snapshot") or {}
	doc_pkg = sources.get("document_package") or payload.get("document_package") or {}
	std = sources.get("std") or payload.get("std") or {}
	catalogue = sources.get("catalogue") or payload.get("catalogue") or {}
	blueprint = sources.get("blueprint") or payload.get("blueprint") or {}
	policy = payload.get("submission_policy") or {}

	val_name = frappe.db.get_value(DT_VALIDATION_REPORT, {"compile_run": art.compile_run}, "name") or ""
	val_digest = ""
	if val_name:
		val_digest = frappe.db.get_value(DT_VALIDATION_REPORT, val_name, "diagnostic_digest") or ""

	impact_ref = ""
	impact_digest = ""
	if impact_plan:
		if not frappe.db.exists(DT_ADDENDUM_IMPACT_PLAN, impact_plan):
			frappe.throw(_("Addendum impact plan not found."), title="BWMF_IMPACT_PLAN")
		ip = frappe.get_doc(DT_ADDENDUM_IMPACT_PLAN, impact_plan)
		if ip.status not in {"Approved", "Immutable"}:
			frappe.throw(_("Impact plan must be approved."), title="BWMF_IMPACT_PLAN")
		impact_ref = ip.name
		impact_digest = ip.plan_digest

	# Preserve payload registry order from eligibility (includes descriptor_order).
	resources_ordered = list(elig["resources"])

	closed: dict[str, Any] = {
		"package_id": package_id,
		"package_version": package_version,
		"compile_artifact": art.name,
		"compile_artifact_id": art.artifact_id,
		"payload_digest": art.payload_digest,
		"target_manifest_id": art.target_manifest_id,
		"proposed_manifest_version": proposed,
		"published_tender_ref": tender_ref,
		"published_tender_version": tender_ver,
		"configuration_snapshot": {
			"ref": cfg.get("ref") or cfg.get("id") or "",
			"digest": cfg.get("digest") or cfg.get("content_digest") or "",
		},
		"document_package": {
			"ref": doc_pkg.get("ref") or doc_pkg.get("id") or "",
			"version": doc_pkg.get("version") or "",
			"digest": doc_pkg.get("digest") or doc_pkg.get("content_digest") or "",
		},
		"std": {
			"ref": std.get("ref") or std.get("id") or "",
			"version": std.get("version") or "",
			"content_digest": std.get("content_digest") or std.get("digest") or "",
		},
		"catalogue": {
			"ref": catalogue.get("ref") or catalogue.get("id") or "",
			"version": catalogue.get("version") or "",
			"digest": catalogue.get("digest") or catalogue.get("content_digest") or "",
		},
		"blueprint": {
			"ref": blueprint.get("ref") or blueprint.get("id") or "",
			"version": blueprint.get("version") or "",
			"digest": blueprint.get("digest") or blueprint.get("content_digest") or "",
		},
		"submission_policy": {
			"ref": policy.get("submission_authority_policy_ref") or "",
			"version": policy.get("version") or "1",
			"digest": jcs_sha256_digest(policy),
		},
		"compiler_version": (elig["envelope"].get("control") or {}).get("compiler_version") or "",
		"schema_version": (elig["envelope"].get("manifest_schema_version") or "1.0.0"),
		"validation_report_ref": val_name,
		"validation_report_digest": val_digest,
		"diagnostic_digest": art.diagnostic_digest,
		"warnings": elig["warnings"],
		"descriptor_set_digest": elig["descriptor_set_digest"],
		"resources": resources_ordered,
		"addendum_impact_plan_ref": impact_ref,
		"addendum_impact_plan_digest": impact_digest,
		"organization": organization,
		"submitting_actor": actor,
		"prepared_at": now_datetime().isoformat(),
	}
	review_digest = jcs_sha256_digest(closed)

	if frappe.db.exists(DT_REVIEW_PACKAGE, {"package_id": package_id}):
		frappe.throw(_("Duplicate package_id."), title="BWMF_DUPLICATE_STABLE_ID")
	if frappe.db.exists(DT_REVIEW_PACKAGE, {"review_package_digest": review_digest}):
		frappe.throw(_("Duplicate review_package_digest."), title="BWMF_DUPLICATE_DIGEST")

	doc = frappe.get_doc(
		{
			"doctype": DT_REVIEW_PACKAGE,
			"package_id": package_id,
			"package_version": package_version,
			"state": "Prepared",
			"review_package_digest": review_digest,
			"compile_artifact": art.name,
			"payload_digest": art.payload_digest,
			"target_manifest_id": art.target_manifest_id,
			"proposed_manifest_version": proposed,
			"published_tender_ref": tender_ref,
			"published_tender_version": tender_ver,
			"organization": organization,
			"submitter": "",
			"package_json": json.dumps(closed, sort_keys=True),
			"immutable": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	emit_lifecycle_event(
		event_type="review_package.prepared",
		organization=organization,
		actor=actor,
		correlation_ref=package_id,
		affected_refs={
			"review_package": doc.name,
			"review_package_digest": review_digest,
			"compile_artifact": art.name,
			"payload_digest": art.payload_digest,
		},
	)
	return {
		"review_package": doc.name,
		"package_id": package_id,
		"review_package_digest": review_digest,
		"state": "Prepared",
		"warnings": elig["warnings"],
	}


def submit_review_package_for_approval(
	*,
	review_package: str,
	organization: str | None = None,
	actor_org: str | None = None,
) -> dict[str, Any]:
	"""Freeze package and transition Prepared → SubmittedForApproval."""
	actor = require_role(ROLE_CONFIGURATOR, ROLE_REVIEWER)
	doc = frappe.get_doc(DT_REVIEW_PACKAGE, review_package)
	organization = organization or doc.organization
	require_org_scope(organization, actor_org=actor_org)
	if doc.organization != organization:
		frappe.throw(_("Organization scope mismatch."), title="BWMF_ORG_SCOPE")
	if doc.state != "Prepared":
		frappe.throw(
			_("Only Prepared packages can be submitted for approval."),
			title="BWMF_REVIEW_STATE",
		)
	# Re-check eligibility at submit time
	assert_eligible_for_review(doc.compile_artifact)

	doc.state = "SubmittedForApproval"
	doc.submitter = actor
	doc.submitted_at = now_datetime()
	doc.immutable = 1
	doc.save(ignore_permissions=True)

	emit_lifecycle_event(
		event_type="review_package.submitted_for_approval",
		organization=organization,
		actor=actor,
		correlation_ref=doc.package_id,
		affected_refs={
			"review_package": doc.name,
			"review_package_digest": doc.review_package_digest,
			"submitter": actor,
		},
	)
	return {
		"review_package": doc.name,
		"state": doc.state,
		"review_package_digest": doc.review_package_digest,
		"submitter": actor,
	}
