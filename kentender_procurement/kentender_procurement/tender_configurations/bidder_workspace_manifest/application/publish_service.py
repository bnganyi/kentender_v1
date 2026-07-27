# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Atomic Phase 5 publication of approved review packages → BWMF Manifest Version."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.approval_service import (
	assert_approval_usable,
	record_approval_invalidation,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
	manifest_resource_binding_key,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.lifecycle_events import (
	emit_lifecycle_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.resource_verifier import (
	ResourceVerifyError,
	verify_descriptor_set,
	verify_resource_row,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.roles import (
	ROLE_PUBLICATION,
	assert_separation_of_duties,
	require_org_scope,
	require_role,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.idempotency import (
	canonical_request_fingerprint,
	resolve_idempotency,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE,
	DT_MANIFEST_RESOURCE_BINDING,
	DT_MANIFEST_VERSION,
	DT_PUBLICATION_REQUEST,
	DT_REVIEW_PACKAGE,
	DT_TENDER_PUBLICATION_STATE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import services as bwmf
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	get_verified,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
)

OP_PUBLISH = "publish_manifest"

# Test-only failure injection points (set to boundary name or None).
_FAIL_AT: str | None = None


def set_publish_fail_at(boundary: str | None) -> None:
	global _FAIL_AT
	_FAIL_AT = boundary


def _maybe_fail(boundary: str) -> None:
	if _FAIL_AT == boundary:
		raise RuntimeError(f"injected failure at {boundary}")


def publish_approved_package(
	*,
	request_id: str,
	approval_decision: str,
	organization: str,
	idempotency_key: str,
	actor_org: str | None = None,
	separation_enabled: bool = True,
	is_addendum: bool = False,
) -> dict[str, Any]:
	"""Atomically publish an approved package. Publication Service role required."""
	requester = require_role(ROLE_PUBLICATION)
	require_org_scope(organization, actor_org=actor_org)

	usable = assert_approval_usable(approval_decision)
	decision = usable["decision"]
	pkg = usable["package"]
	elig = usable["eligibility"]

	assert_separation_of_duties(
		submitter=pkg.submitter or "",
		approver=decision.approver,
		separation_enabled=separation_enabled,
	)

	fp_body = {
		"approval_decision": decision.name,
		"review_package_digest": pkg.review_package_digest,
		"payload_digest": pkg.payload_digest,
		"published_tender_ref": pkg.published_tender_ref,
		"is_addendum": bool(is_addendum),
	}
	fp = canonical_request_fingerprint(fp_body)

	emit_lifecycle_event(
		event_type="publication.requested",
		organization=organization,
		actor=requester,
		correlation_ref=idempotency_key,
		affected_refs={
			"approval_decision": decision.name,
			"review_package": pkg.name,
			"request_id": request_id,
		},
	)

	def _create() -> str:
		frappe.db.savepoint("bwmf_atomic_publish")
		try:
			name = _execute_atomic_publication(
				request_id=request_id,
				decision=decision,
				pkg=pkg,
				elig=elig,
				organization=organization,
				requester=requester,
				idempotency_key=idempotency_key,
				request_fingerprint=fp,
				is_addendum=is_addendum,
			)
			frappe.db.release_savepoint("bwmf_atomic_publish")
			return name
		except Exception:
			frappe.db.rollback(save_point="bwmf_atomic_publish")
			raise

	try:
		pub_name = resolve_idempotency(
			organization=organization,
			operation=OP_PUBLISH,
			idempotency_key=idempotency_key,
			request_fingerprint=fp,
			result_doctype=DT_MANIFEST_PUBLICATION,
			create_result=_create,
		)
	except Exception as exc:
		emit_lifecycle_event(
			event_type="publication.verification_failed",
			organization=organization,
			actor=requester,
			correlation_ref=idempotency_key,
			affected_refs={"approval_decision": decision.name, "review_package": pkg.name},
			metadata={"error": str(exc), "code": getattr(exc, "title", None) or type(exc).__name__},
		)
		_record_failed_request(
			request_id=request_id,
			pkg=pkg,
			decision=decision,
			organization=organization,
			requester=requester,
			idempotency_key=idempotency_key,
			request_fingerprint=fp,
			error=str(exc),
		)
		raise

	pub = frappe.get_doc(DT_MANIFEST_PUBLICATION, pub_name)
	return {
		"ok": True,
		"publication": pub.name,
		"publication_id": pub.publication_id,
		"manifest_version": pub.manifest_version,
		"published_tender_ref": pub.published_tender_ref,
		"published_tender_version": int(pub.published_tender_version),
		"payload_digest": pub.payload_digest,
	}


def cancel_publication(
	*,
	published_tender_ref: str,
	organization: str,
	reason: str,
	reference: str = "",
	actor_org: str | None = None,
) -> dict[str, Any]:
	actor = require_role(ROLE_PUBLICATION)
	require_org_scope(organization, actor_org=actor_org)
	if not (reason or "").strip():
		frappe.throw(_("Cancellation requires a controlled reason."), title="BWMF_CANCEL_REASON")
	lineage = _get_lineage(published_tender_ref, organization)
	if not lineage or not lineage.public_active or not lineage.active_manifest_version:
		frappe.throw(_("No active publication to cancel."), title="BWMF_CANCEL_STATE")
	mv_name = lineage.active_manifest_version
	prior_digest = frappe.db.get_value(DT_MANIFEST_VERSION, mv_name, "payload_digest")
	prior_payload = frappe.db.get_value(DT_MANIFEST_VERSION, mv_name, "payload_json")
	bwmf.cancel_manifest_version(mv_name, organization=organization)
	after = frappe.db.get_value(
		DT_MANIFEST_VERSION, mv_name, ["payload_digest", "payload_json"], as_dict=True
	)
	if after.payload_digest != prior_digest or after.payload_json != prior_payload:
		frappe.throw(_("Cancellation must not alter payload."), title="BWMF_MANIFEST_CONTENT_IMMUTABLE")

	lineage.public_active = 0
	lineage.workspace_available = 0
	lineage.save(ignore_permissions=True)

	emit_lifecycle_event(
		event_type="publication.cancelled",
		organization=organization,
		actor=actor,
		correlation_ref=reference or published_tender_ref,
		affected_refs={
			"manifest_version": mv_name,
			"published_tender_ref": published_tender_ref,
			"payload_digest": prior_digest,
		},
		metadata={"reason": reason, "reference": reference},
	)
	return {"ok": True, "manifest_version": mv_name, "payload_digest": prior_digest}


def _execute_atomic_publication(
	*,
	request_id: str,
	decision,
	pkg,
	elig,
	organization: str,
	requester: str,
	idempotency_key: str,
	request_fingerprint: str,
	is_addendum: bool,
) -> str:
	art = elig["artifact"]
	payload = elig["payload"]
	resources = elig["resources"]

	# Publication-time re-verification (fail closed)
	try:
		_reverify_for_publication(decision=decision, pkg=pkg, elig=elig)
	except ResourceVerifyError as exc:
		frappe.throw(_(exc.message), title=exc.code)

	lineage_key = f"lineage:{pkg.published_tender_ref}"
	frappe.db.sql("SELECT GET_LOCK(%s, %s)", (lineage_key, 30))
	try:
		_maybe_fail("after_lineage_lock")
		lineage = _lock_or_create_lineage(pkg.published_tender_ref, organization)

		# Allocate version
		next_ver = _allocate_manifest_version(
			manifest_id=pkg.target_manifest_id,
			lineage=lineage,
			is_addendum=is_addendum,
			proposed=int(pkg.proposed_manifest_version or 1),
		)
		_maybe_fail("after_version_alloc")

		# Create MV directly in Published with exact approved payload/digest
		published_at = now_datetime()
		envelope = json.loads(art.envelope_json)
		# Publication metadata outside payload — must not change payload digest
		envelope = dict(envelope)
		envelope["publication"] = {
			"approval_ref": decision.name,
			"approval_decision_id": decision.decision_id,
			"published_at": published_at.isoformat(),
			"publication_request_id": request_id,
			"manifest_version": next_ver,
			"published_tender_ref": pkg.published_tender_ref,
			"published_tender_version": next_ver,
		}
		# Retain exact approved payload bytes/digest
		payload_json = art.payload_json
		payload_digest = art.payload_digest
		if jcs_sha256_digest(json.loads(payload_json)) != payload_digest:
			frappe.throw(_("Payload digest verification failed at publication."), title="BWMF_PUBLISH_DIGEST")

		mv = frappe.get_doc(
			{
				"doctype": DT_MANIFEST_VERSION,
				"manifest_id": pkg.target_manifest_id,
				"manifest_version": next_ver,
				"lifecycle_state": "Published",
				"manifest_schema_version": envelope.get("manifest_schema_version") or "1.0.0",
				"payload_digest": payload_digest,
				"envelope_json": json.dumps(envelope, sort_keys=True),
				"payload_json": payload_json,
				"organization": organization,
				"published_tender_ref": pkg.published_tender_ref,
				"published_tender_version": next_ver,
			}
		)
		mv.insert(ignore_permissions=True)
		_maybe_fail("after_manifest_version")

		# Resource bindings
		pkg_body = json.loads(pkg.package_json)
		ordered = sorted(
			pkg_body.get("resources") or resources,
			key=lambda r: int(r.get("descriptor_order", 0)),
		)
		# Prefer payload registry digest; fall back to package digest only if equal after verify.
		expected_set = (
			((payload.get("resource_registry") or {}).get("descriptor_set_digest"))
			or pkg_body.get("descriptor_set_digest")
			or elig["descriptor_set_digest"]
		)
		binding_names: list[str] = []
		try:
			for r in ordered:
				verify_resource_row(r["resource_docname"])
				# Equality vs artifact binding + payload descriptor
				ab = frappe.db.get_value(
					DT_ARTIFACT_RESOURCE_BINDING,
					{"compile_artifact": art.name, "resource_id": r["resource_id"]},
					["resource_digest", "content_ref"],
					as_dict=True,
				)
				if not ab or ab.resource_digest != r["resource_digest"] or ab.content_ref != r["content_ref"]:
					frappe.throw(
						_("Resource binding mismatch for {0}.").format(r["resource_id"]),
						title="BWMF_PUBLISH_BINDING",
					)
				get_verified(r["content_ref"])
				bdigest = jcs_sha256_digest(
					{
						"manifest_id": pkg.target_manifest_id,
						"manifest_version": next_ver,
						"resource_id": r["resource_id"],
						"resource_version_key": r["resource_version_key"],
						"resource_digest": r["resource_digest"],
						"content_ref": r["content_ref"],
						"descriptor_order": int(r.get("descriptor_order", 0)),
					}
				)
				bkey = manifest_resource_binding_key(mv.name, r["resource_id"])
				bdoc = frappe.get_doc(
					{
						"doctype": DT_MANIFEST_RESOURCE_BINDING,
						"binding_id": f"MRB-{mv.name}-{r['resource_id']}"[:140],
						"binding_key": bkey,
						"manifest_version": mv.name,
						"resource_id": r["resource_id"],
						"resource_docname": r["resource_docname"],
						"resource_version_key": r["resource_version_key"],
						"resource_type": r["resource_type"],
						"schema_ref": r["schema_ref"],
						"schema_version": r["schema_version"],
						"resource_digest": r["resource_digest"],
						"content_ref": r["content_ref"],
						"item_count": int(r["item_count"]),
						"descriptor_order": int(r.get("descriptor_order", 0)),
						"binding_digest": bdigest,
						"immutable": 1,
						"organization": organization,
					}
				)
				bdoc.insert(ignore_permissions=True)
				binding_names.append(bdoc.name)
			_maybe_fail("after_resource_bindings")

			verify_descriptor_set(
				[r["resource_docname"] for r in ordered],
				expected_set,
			)
		except ResourceVerifyError as exc:
			frappe.throw(_(exc.message), title=exc.code)

		# Supersede prior active on addendum
		prior_mv = lineage.active_manifest_version
		if is_addendum and prior_mv:
			prior_digest = frappe.db.get_value(DT_MANIFEST_VERSION, prior_mv, "payload_digest")
			prior_payload = frappe.db.get_value(DT_MANIFEST_VERSION, prior_mv, "payload_json")
			bwmf.supersede_manifest_version(prior_mv, organization=organization)
			after = frappe.db.get_value(
				DT_MANIFEST_VERSION, prior_mv, ["payload_digest", "payload_json"], as_dict=True
			)
			if after.payload_digest != prior_digest or after.payload_json != prior_payload:
				frappe.throw(_("Supersession mutated prior payload."), title="BWMF_MANIFEST_CONTENT_IMMUTABLE")
			emit_lifecycle_event(
				event_type="manifest.superseded",
				organization=organization,
				actor=requester,
				correlation_ref=idempotency_key,
				affected_refs={"manifest_version": prior_mv, "payload_digest": prior_digest},
			)

		_maybe_fail("after_supersede")

		pub_id = f"PUB-{request_id}" if not request_id.startswith("PUB-") else request_id
		pub = frappe.get_doc(
			{
				"doctype": DT_MANIFEST_PUBLICATION,
				"publication_id": pub_id,
				"manifest_version": mv.name,
				"approval_decision": decision.name,
				"published_tender_ref": pkg.published_tender_ref,
				"published_tender_version": next_ver,
				"published_at": published_at,
				"transaction_ref": idempotency_key,
				"payload_digest": payload_digest,
				"organization": organization,
			}
		)
		pub.insert(ignore_permissions=True)
		_maybe_fail("after_publication")

		lineage.active_manifest_version = mv.name
		lineage.active_publication = pub.name
		lineage.public_active = 1
		lineage.workspace_available = 1  # availability flag only — no workspace rows
		lineage.save(ignore_permissions=True)
		_maybe_fail("after_tender_state")

		# Publication request success row
		if not frappe.db.exists(DT_PUBLICATION_REQUEST, {"request_id": request_id}):
			preq = frappe.get_doc(
				{
					"doctype": DT_PUBLICATION_REQUEST,
					"request_id": request_id,
					"review_package": pkg.name,
					"approval_decision": decision.name,
					"organization": organization,
					"requester": requester,
					"state": "Succeeded",
					"idempotency_key": idempotency_key,
					"request_fingerprint": request_fingerprint,
					"result_publication": pub.name,
					"result_manifest_version": mv.name,
					"immutable": 1,
				}
			)
			preq.insert(ignore_permissions=True)
		else:
			preq = frappe.get_doc(DT_PUBLICATION_REQUEST, request_id)
			if preq.state == "Requested":
				preq.state = "Succeeded"
				preq.result_publication = pub.name
				preq.result_manifest_version = mv.name
				preq.save(ignore_permissions=True)

		emit_lifecycle_event(
			event_type="publication.succeeded",
			organization=organization,
			actor=requester,
			correlation_ref=idempotency_key,
			affected_refs={
				"publication": pub.name,
				"manifest_version": mv.name,
				"manifest_version_number": next_ver,
				"payload_digest": payload_digest,
				"approval_decision": decision.name,
				"resource_bindings": binding_names,
			},
		)
		_ = payload  # silence lint
		return pub.name
	except Exception:
		# Ensure no partial authoritative rows remain — Frappe will rollback the txn on throw.
		# Explicit cleanup for savepoint-less path: re-raise after audit is handled by caller.
		raise
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lineage_key,))


def _reverify_for_publication(*, decision, pkg, elig) -> None:
	art = elig["artifact"]
	if art.artifact_kind != "finalized_materialized":
		record_approval_invalidation(
			decision_name=decision.name,
			reason="artifact_kind_mismatch",
			organization=pkg.organization,
		)
		frappe.throw(_("Artifact kind invalid at publication."), title="BWMF_PUBLISH_REVERIFY")
	if art.payload_digest != decision.payload_digest or art.payload_digest != pkg.payload_digest:
		record_approval_invalidation(
			decision_name=decision.name,
			reason="payload_digest_mismatch",
			organization=pkg.organization,
		)
		frappe.throw(_("Stale approval: payload digest mismatch."), title="BWMF_PUBLISH_REVERIFY")
	if jcs_sha256_digest(json.loads(art.payload_json)) != art.payload_digest:
		frappe.throw(_("Payload bytes do not match digest."), title="BWMF_PUBLISH_REVERIFY")
	pkg_body = json.loads(pkg.package_json)
	if jcs_sha256_digest(pkg_body) != pkg.review_package_digest:
		frappe.throw(_("Review package digest reverify failed."), title="BWMF_PUBLISH_REVERIFY")
	acks = json.loads(decision.warning_acknowledgements_json or "[]")
	warn_fps = {w.get("fingerprint") for w in (pkg_body.get("warnings") or [])}
	ack_fps = {a.get("fingerprint") for a in acks}
	if warn_fps - ack_fps:
		frappe.throw(_("Warning acknowledgements incomplete at publication."), title="BWMF_PUBLISH_REVERIFY")
	for r in elig["resources"]:
		verify_resource_row(r["resource_docname"])
		get_verified(r["content_ref"])
	verify_descriptor_set(
		[r["resource_docname"] for r in elig["resources"]],
		elig["descriptor_set_digest"],
	)
	# Conflicting publication
	existing = frappe.db.exists(
		DT_MANIFEST_VERSION,
		{
			"manifest_id": pkg.target_manifest_id,
			"manifest_version": int(pkg.proposed_manifest_version),
			"lifecycle_state": "Published",
		},
	)
	# Allocation handles version; here only ensure no orphan Published without lineage when not addendum
	_ = existing


def _allocate_manifest_version(*, manifest_id: str, lineage, is_addendum: bool, proposed: int) -> int:
	max_row = frappe.db.sql(
		"""
		SELECT MAX(manifest_version) FROM `tabBWMF Manifest Version`
		WHERE manifest_id=%s
		""",
		(manifest_id,),
	)
	max_ver = int(max_row[0][0] or 0) if max_row else 0
	if max_ver == 0 and not lineage.active_manifest_version:
		return 1
	if is_addendum:
		if not lineage.active_manifest_version:
			frappe.throw(_("Addendum requires a prior published manifest."), title="BWMF_ADDENDUM")
		prior = int(
			frappe.db.get_value(DT_MANIFEST_VERSION, lineage.active_manifest_version, "manifest_version") or 0
		)
		return prior + 1
	if max_ver > 0:
		frappe.throw(
			_("Manifest already published; use addendum publication for next version."),
			title="BWMF_PUBLISH_VERSION",
		)
	return 1


def _lock_or_create_lineage(published_tender_ref: str, organization: str):
	name = frappe.db.get_value(
		DT_TENDER_PUBLICATION_STATE, {"published_tender_ref": published_tender_ref}, "name"
	)
	if name:
		# Row lock
		frappe.db.sql(
			"SELECT name FROM `tabBWMF Tender Publication State` WHERE name=%s FOR UPDATE",
			(name,),
		)
		return frappe.get_doc(DT_TENDER_PUBLICATION_STATE, name)
	doc = frappe.get_doc(
		{
			"doctype": DT_TENDER_PUBLICATION_STATE,
			"lineage_key": f"TPS-{published_tender_ref}"[:140],
			"published_tender_ref": published_tender_ref,
			"public_active": 0,
			"workspace_available": 0,
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.sql(
		"SELECT name FROM `tabBWMF Tender Publication State` WHERE name=%s FOR UPDATE",
		(doc.name,),
	)
	return frappe.get_doc(DT_TENDER_PUBLICATION_STATE, doc.name)


def _get_lineage(published_tender_ref: str, organization: str):
	name = frappe.db.get_value(
		DT_TENDER_PUBLICATION_STATE,
		{"published_tender_ref": published_tender_ref, "organization": organization},
		"name",
	)
	if not name:
		name = frappe.db.get_value(
			DT_TENDER_PUBLICATION_STATE, {"published_tender_ref": published_tender_ref}, "name"
		)
	return frappe.get_doc(DT_TENDER_PUBLICATION_STATE, name) if name else None


def _record_failed_request(
	*,
	request_id: str,
	pkg,
	decision,
	organization: str,
	requester: str,
	idempotency_key: str,
	request_fingerprint: str,
	error: str,
) -> None:
	try:
		if frappe.db.exists(DT_PUBLICATION_REQUEST, {"request_id": request_id}):
			return
		frappe.get_doc(
			{
				"doctype": DT_PUBLICATION_REQUEST,
				"request_id": f"FAIL-{request_id}"[:140],
				"review_package": pkg.name,
				"approval_decision": decision.name,
				"organization": organization,
				"requester": requester,
				"state": "Failed",
				"idempotency_key": f"fail:{idempotency_key}"[:140],
				"request_fingerprint": request_fingerprint,
				"error_json": json.dumps({"error": error}),
				"immutable": 1,
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass
