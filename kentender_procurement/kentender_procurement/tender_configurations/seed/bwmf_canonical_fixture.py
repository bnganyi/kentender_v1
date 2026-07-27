# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical BWMF fixture clear + reseed (dev disposable data)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	CLEAR_ORDER,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import services as bwmf
from kentender_procurement.tender_configurations.tests.helpers.bwmf_policy import explicit_submission_policy

FIXTURE_ORG = "ORG-CAL-NSSF"
FIXTURE_PARTY = "BIDDER-CAL-001"
FIXTURE_TENDER_REF = "CAL-NSSF-NSSFSPS-ICT-ERP-001-2025-2026"
FIXTURE_MANIFEST_ID = "BWMF-CAL-NSSF-ERP-001-V1"
FIXTURE_WORKSPACE_ID = "WS-CAL-NSSF-001"
FIXTURE_PREFIX = "BWMF-CAL"


def clear_bwmf_cas_files() -> int:
	"""Remove private CAS File rows under Home/BWMF-CAS (dev reset only)."""
	prior = frappe.flags.get("bwmf_force_clear")
	frappe.flags.bwmf_force_clear = True
	deleted = 0
	try:
		names = frappe.get_all(
			"File",
			filters={"folder": "Home/BWMF-CAS", "is_folder": 0},
			pluck="name",
		)
		for name in names:
			frappe.delete_doc("File", name, force=1, ignore_permissions=True)
			deleted += 1
	finally:
		frappe.flags.bwmf_force_clear = prior
	return deleted


def clear_bwmf_phase4_materialization(*, keep_preview_artifacts: bool = False) -> dict[str, int]:
	"""Clear Phase 4 materialization rows + CAS; optionally retain preview Compile Artifacts."""
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
		DT_COMPILE_ARTIFACT,
		DT_CONTENT_OBJECT,
		DT_ARTIFACT_RESOURCE_BINDING,
		DT_MANIFEST_RESOURCE,
		DT_MATERIALIZATION_REPORT,
		DT_IDEMPOTENCY_RECORD,
	)

	frappe.flags.bwmf_force_clear = True
	counts: dict[str, int] = {}
	try:
		for doctype in (
			DT_MATERIALIZATION_REPORT,
			DT_ARTIFACT_RESOURCE_BINDING,
			DT_MANIFEST_RESOURCE,
			DT_CONTENT_OBJECT,
		):
			if not frappe.db.exists("DocType", doctype):
				continue
			names = frappe.get_all(doctype, pluck="name")
			for name in names:
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			counts[doctype] = len(names)
		# finalized artifacts only
		if frappe.db.exists("DocType", DT_COMPILE_ARTIFACT):
			finals = frappe.get_all(
				DT_COMPILE_ARTIFACT,
				filters={"artifact_kind": "finalized_materialized"},
				pluck="name",
			)
			if not keep_preview_artifacts:
				# still only delete finalized here
				pass
			for name in finals:
				frappe.delete_doc(DT_COMPILE_ARTIFACT, name, force=1, ignore_permissions=True)
			counts["finalized_artifacts"] = len(finals)
		# materialize idempotency keys
		if frappe.db.exists("DocType", DT_IDEMPOTENCY_RECORD):
			keys = frappe.get_all(
				DT_IDEMPOTENCY_RECORD,
				filters={"operation": "materialize_resources"},
				pluck="name",
			)
			for name in keys:
				frappe.delete_doc(DT_IDEMPOTENCY_RECORD, name, force=1, ignore_permissions=True)
			counts["materialize_idempotency"] = len(keys)
		counts["cas_files"] = clear_bwmf_cas_files()
		frappe.db.commit()
	finally:
		frappe.flags.bwmf_force_clear = False
	return counts


def clear_bwmf_canonical_fixture() -> dict[str, int]:
	counts: dict[str, int] = {}
	frappe.flags.bwmf_force_clear = True
	try:
		for doctype in CLEAR_ORDER:
			if not frappe.db.exists("DocType", doctype):
				continue
			names = frappe.get_all(doctype, pluck="name")
			for name in names:
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			counts[doctype] = len(names)
		counts["cas_files"] = clear_bwmf_cas_files()
		frappe.db.commit()
	finally:
		frappe.flags.bwmf_force_clear = False
	return counts


def seed_bwmf_canonical_fixture(*, clear: bool = True) -> dict[str, Any]:
	if clear:
		clear_bwmf_canonical_fixture()

	content_digest = "sha256:" + ("d" * 64)
	bindings = [
		{
			"binding_id": "BIND-STD",
			"binding_type": "std_template",
			"object_ref": "STD-IT",
			"object_version": "1.0.0",
			"lifecycle_state": "approved",
			"document_content_digest": content_digest,
		}
	]
	req = bwmf.create_compile_request(
		compile_request_id=f"{FIXTURE_PREFIX}-REQ-001",
		idempotency_key=f"{FIXTURE_PREFIX}-REQ-KEY-001",
		target_manifest_id=FIXTURE_MANIFEST_ID,
		published_tender_ref=FIXTURE_TENDER_REF,
		organization=FIXTURE_ORG,
		bindings=bindings,
	)
	run = bwmf.create_compile_run(
		run_id=f"{FIXTURE_PREFIX}-RUN-001",
		idempotency_key=f"{FIXTURE_PREFIX}-RUN-KEY-001",
		compile_request=req,
		organization=FIXTURE_ORG,
	)
	bwmf.complete_compile_run_success(run_name=run, organization=FIXTURE_ORG)
	manifest = bwmf.create_manifest_version(
		manifest_id=FIXTURE_MANIFEST_ID,
		manifest_version=1,
		lifecycle_state="Draft",
		published_tender_ref=FIXTURE_TENDER_REF,
		organization=FIXTURE_ORG,
		payload={
			"manifest_id": FIXTURE_MANIFEST_ID,
			"manifest_version": 1,
			"sections": [{"section_key": "form_of_tender"}],
			"submission_policy": explicit_submission_policy(),
		},
	)
	report = bwmf.create_validation_report(report_id=f"{FIXTURE_PREFIX}-VAL-001", compile_run=run)
	approval = bwmf.create_approval(
		approval_id=f"{FIXTURE_PREFIX}-APR-001",
		manifest_name=manifest,
		validation_report=report,
	)
	publication = bwmf.create_publication(
		publication_id=f"{FIXTURE_PREFIX}-PUB-001",
		manifest_name=manifest,
		approval=approval,
		published_tender_ref=FIXTURE_TENDER_REF,
		organization=FIXTURE_ORG,
	)
	workspace = bwmf.create_workspace(
		workspace_id=FIXTURE_WORKSPACE_ID,
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
		published_tender_ref=FIXTURE_TENDER_REF,
	)
	binding = bwmf.bind_workspace_manifest(
		workspace=workspace,
		manifest_name=manifest,
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
	)
	response = bwmf.append_response_version(
		response_id=f"{FIXTURE_PREFIX}-RESP-001",
		workspace=workspace,
		manifest_name=manifest,
		section_key="form_of_tender",
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
		values={"note": "fixture"},
		expected_version=0,
	)
	evidence_item = bwmf.create_evidence_item(
		evidence_id=f"{FIXTURE_PREFIX}-EV-001",
		workspace=workspace,
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
	)
	evidence_version = bwmf.create_evidence_version(
		evidence_item=evidence_item,
		version=1,
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
		content_label="fixture-pdf",
	)
	evidence_link = bwmf.link_evidence(
		evidence_version=evidence_version,
		workspace=workspace,
		task_ref="TASK-FOT-1",
		organization=FIXTURE_ORG,
		bidder_party=FIXTURE_PARTY,
	)
	frappe.db.commit()
	return {
		"compile_request": req,
		"compile_run": run,
		"manifest": manifest,
		"validation_report": report,
		"approval": approval,
		"publication": publication,
		"workspace": workspace,
		"binding": binding,
		"response": response,
		"evidence_item": evidence_item,
		"evidence_version": evidence_version,
		"evidence_link": evidence_link,
		"workspace_id": FIXTURE_WORKSPACE_ID,
		"organization": FIXTURE_ORG,
		"bidder_party": FIXTURE_PARTY,
	}


def get_fixture_workspace_name() -> str | None:
	return frappe.db.get_value(DT_WORKSPACE, {"workspace_id": FIXTURE_WORKSPACE_ID}, "name")
