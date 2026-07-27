# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Immutable approval / return decisions for review packages."""

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
	assert_separation_of_duties,
	require_org_scope,
	require_role,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_APPROVAL_DECISION,
	DT_INVALIDATION_EVENT,
	DT_REVIEW_PACKAGE,
)


def approve_review_package(
	*,
	decision_id: str,
	review_package: str,
	warning_acknowledgements: list[dict[str, Any]] | None = None,
	comment: str = "",
	organization: str | None = None,
	actor_org: str | None = None,
	separation_enabled: bool = True,
) -> dict[str, Any]:
	"""Approve exact package digest. Does not publish."""
	approver = require_role(ROLE_APPROVER)
	doc = frappe.get_doc(DT_REVIEW_PACKAGE, review_package)
	organization = organization or doc.organization
	require_org_scope(organization, actor_org=actor_org)
	if doc.state != "SubmittedForApproval":
		frappe.throw(_("Package must be SubmittedForApproval."), title="BWMF_APPROVAL_STATE")
	assert_separation_of_duties(
		submitter=doc.submitter or "",
		approver=approver,
		separation_enabled=separation_enabled,
	)
	# Re-verify artifact still matches package digests
	elig = assert_eligible_for_review(doc.compile_artifact)
	if elig["artifact"].payload_digest != doc.payload_digest:
		frappe.throw(_("Artifact payload digest no longer matches package."), title="BWMF_APPROVAL_STALE")
	pkg = json.loads(doc.package_json)
	if jcs_sha256_digest(pkg) != doc.review_package_digest:
		frappe.throw(_("Review package digest mismatch."), title="BWMF_APPROVAL_STALE")

	acks = _normalize_acks(warning_acknowledgements or [], approver=approver)
	_assert_all_warnings_acked(pkg.get("warnings") or [], acks)

	binding = {
		"review_package_digest": doc.review_package_digest,
		"compile_artifact": doc.compile_artifact,
		"payload_digest": doc.payload_digest,
		"target_manifest_id": doc.target_manifest_id,
		"proposed_manifest_version": int(doc.proposed_manifest_version),
		"published_tender_ref": doc.published_tender_ref,
		"published_tender_version": int(doc.published_tender_version),
		"configuration_snapshot_digest": (pkg.get("configuration_snapshot") or {}).get("digest") or "",
		"document_package_digest": (pkg.get("document_package") or {}).get("digest") or "",
		"std": pkg.get("std") or {},
		"catalogue": pkg.get("catalogue") or {},
		"blueprint": pkg.get("blueprint") or {},
		"submission_policy": pkg.get("submission_policy") or {},
		"validation_report_ref": pkg.get("validation_report_ref") or "",
		"validation_report_digest": pkg.get("validation_report_digest") or "",
		"diagnostic_digest": pkg.get("diagnostic_digest") or "",
		"descriptor_set_digest": pkg.get("descriptor_set_digest") or "",
		"warning_acknowledgements": acks,
		"approver": approver,
		"organization": organization,
		"decision": "approved",
		"comment": comment or "",
		"decided_at": now_datetime().isoformat(),
	}
	return _persist_decision(
		decision_id=decision_id,
		review_package=doc,
		decision="approved",
		binding=binding,
		acks=acks,
		approver=approver,
		organization=organization,
		return_reason="",
		correction_owner="",
	)


def return_review_package(
	*,
	decision_id: str,
	review_package: str,
	return_reason: str,
	correction_owner: str,
	warning_acknowledgements: list[dict[str, Any]] | None = None,
	organization: str | None = None,
	actor_org: str | None = None,
	separation_enabled: bool = True,
) -> dict[str, Any]:
	approver = require_role(ROLE_APPROVER)
	doc = frappe.get_doc(DT_REVIEW_PACKAGE, review_package)
	organization = organization or doc.organization
	require_org_scope(organization, actor_org=actor_org)
	if doc.state != "SubmittedForApproval":
		frappe.throw(_("Package must be SubmittedForApproval."), title="BWMF_APPROVAL_STATE")
	if not (return_reason or "").strip():
		frappe.throw(_("Return requires a controlled reason."), title="BWMF_RETURN_REASON")
	if not (correction_owner or "").strip():
		frappe.throw(_("Return requires a correction owner."), title="BWMF_RETURN_REASON")
	assert_separation_of_duties(
		submitter=doc.submitter or "",
		approver=approver,
		separation_enabled=separation_enabled,
	)
	pkg = json.loads(doc.package_json)
	acks = _normalize_acks(warning_acknowledgements or [], approver=approver)
	binding = {
		"review_package_digest": doc.review_package_digest,
		"compile_artifact": doc.compile_artifact,
		"payload_digest": doc.payload_digest,
		"decision": "returned",
		"return_reason": return_reason,
		"correction_owner": correction_owner,
		"approver": approver,
		"organization": organization,
		"decided_at": now_datetime().isoformat(),
	}
	return _persist_decision(
		decision_id=decision_id,
		review_package=doc,
		decision="returned",
		binding=binding,
		acks=acks,
		approver=approver,
		organization=organization,
		return_reason=return_reason,
		correction_owner=correction_owner,
	)


def record_approval_invalidation(
	*,
	decision_name: str,
	reason: str,
	organization: str,
	actor: str = "",
) -> str:
	"""Append-only invalidation — never rewrite the approval decision row."""
	actor = actor or frappe.session.user
	decision = frappe.get_doc(DT_APPROVAL_DECISION, decision_name)
	# BWMF Invalidation Event is workspace-scoped; governance uses lifecycle events only.
	_ = DT_INVALIDATION_EVENT
	return emit_lifecycle_event(
		event_type="approval.invalidated_at_publication",
		organization=organization,
		actor=actor,
		correlation_ref=decision.decision_id,
		affected_refs={
			"approval_decision": decision.name,
			"review_package_digest": decision.review_package_digest,
			"payload_digest": decision.payload_digest,
		},
		metadata={"reason": reason},
	)


def assert_approval_usable(decision_name: str) -> dict[str, Any]:
	"""Derive whether an approval still matches its bound package/artifact."""
	decision = frappe.get_doc(DT_APPROVAL_DECISION, decision_name)
	if decision.decision != "approved":
		frappe.throw(_("Approval decision is not an approval."), title="BWMF_APPROVAL_UNUSABLE")
	if decision.state == "Invalidated":
		frappe.throw(_("Approval decision was invalidated."), title="BWMF_APPROVAL_UNUSABLE")
	pkg = frappe.get_doc(DT_REVIEW_PACKAGE, decision.review_package)
	if pkg.review_package_digest != decision.review_package_digest:
		frappe.throw(_("Approval review_package_digest mismatch."), title="BWMF_APPROVAL_UNUSABLE")
	if pkg.payload_digest != decision.payload_digest:
		frappe.throw(_("Approval payload_digest mismatch."), title="BWMF_APPROVAL_UNUSABLE")
	if pkg.state != "Approved":
		frappe.throw(_("Review package is not Approved."), title="BWMF_APPROVAL_UNUSABLE")
	elig = assert_eligible_for_review(pkg.compile_artifact)
	if elig["artifact"].payload_digest != decision.payload_digest:
		frappe.throw(_("Approved artifact digest no longer matches."), title="BWMF_APPROVAL_UNUSABLE")
	binding = json.loads(decision.binding_json)
	if binding.get("descriptor_set_digest") != (json.loads(pkg.package_json).get("descriptor_set_digest")):
		frappe.throw(_("Approval descriptor-set binding stale."), title="BWMF_APPROVAL_UNUSABLE")
	return {"decision": decision, "package": pkg, "eligibility": elig}


def _persist_decision(
	*,
	decision_id: str,
	review_package,
	decision: str,
	binding: dict[str, Any],
	acks: list[dict[str, Any]],
	approver: str,
	organization: str,
	return_reason: str,
	correction_owner: str,
) -> dict[str, Any]:
	if frappe.db.exists(DT_APPROVAL_DECISION, {"decision_id": decision_id}):
		frappe.throw(_("Duplicate decision_id."), title="BWMF_DUPLICATE_STABLE_ID")
	decided_at = now_datetime()
	binding["decided_at"] = decided_at.isoformat()
	row = frappe.get_doc(
		{
			"doctype": DT_APPROVAL_DECISION,
			"decision_id": decision_id,
			"review_package": review_package.name,
			"review_package_digest": review_package.review_package_digest,
			"payload_digest": review_package.payload_digest,
			"decision": decision,
			"state": "Active",
			"approver": approver,
			"organization": organization,
			"decided_at": decided_at,
			"return_reason": return_reason or "",
			"correction_owner": correction_owner or "",
			"warning_acknowledgements_json": json.dumps(acks, sort_keys=True),
			"binding_json": json.dumps(binding, sort_keys=True),
			"immutable": 1,
		}
	)
	row.insert(ignore_permissions=True)

	review_package.state = "Approved" if decision == "approved" else "Returned"
	review_package.save(ignore_permissions=True)

	event = "review_package.approved" if decision == "approved" else "review_package.returned"
	emit_lifecycle_event(
		event_type=event,
		organization=organization,
		actor=approver,
		correlation_ref=decision_id,
		affected_refs={
			"approval_decision": row.name,
			"review_package": review_package.name,
			"review_package_digest": review_package.review_package_digest,
			"payload_digest": review_package.payload_digest,
		},
		metadata={"decision": decision, "return_reason": return_reason},
	)
	return {
		"approval_decision": row.name,
		"decision_id": decision_id,
		"decision": decision,
		"review_package": review_package.name,
		"state": review_package.state,
		"published": False,
	}


def _normalize_acks(acks: list[dict[str, Any]], *, approver: str) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	now = now_datetime().isoformat()
	for a in acks:
		fp = str(a.get("fingerprint") or "")
		code = str(a.get("code") or "")
		if not fp or not code:
			frappe.throw(_("Warning acknowledgement requires code and fingerprint."), title="BWMF_WARNING_ACK")
		out.append(
			{
				"code": code,
				"fingerprint": fp,
				"approver": a.get("approver") or approver,
				"acknowledged_at": a.get("acknowledged_at") or now,
				"comment": a.get("comment") or "",
			}
		)
	return out


def _assert_all_warnings_acked(warnings: list[dict[str, Any]], acks: list[dict[str, Any]]) -> None:
	ack_fps = {a["fingerprint"] for a in acks}
	missing = [w for w in warnings if w.get("fingerprint") not in ack_fps]
	if missing:
		frappe.throw(
			_("Unacknowledged warnings block approval: {0}.").format(
				", ".join(w.get("code") or "?" for w in missing)
			),
			title="BWMF_WARNING_UNACKED",
		)
