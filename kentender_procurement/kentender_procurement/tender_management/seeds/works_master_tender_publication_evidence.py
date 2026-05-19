# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-009 companion — WORKS master publication evidence (spec §13.3–13.5).

Ensures ``STDINST-TND-MOH-2026-001``, V2 derived outputs, ``Tender Publication Snapshot``
(``PUBSNAP-TND-MOH-2026-001-V2``), and issued addendum ``ADD-TND-MOH-2026-001-01`` exist so
``validate_procurement_lifecycle_works_master_seed`` passes VAL-SEED-014/015/020.

Idempotent — safe to run after :func:`upsert_works_master_tender`.
"""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

TENDER_CODE = "TND-MOH-2026-001"
_ADDENDUM_CODE = "ADD-TND-MOH-2026-001-01"
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.publication_lock import (
	StdPublicationLockService,
)
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	DECISION_APPROVED,
)

INSTANCE_CODE = "STDINST-TND-MOH-2026-001"
STD_VERSION_REF = "STDTV-WORKS-BUILDING-CIVIL-APR2022"
WORKS_PROFILE_CODE = "WORKS-PROFILE-BUILDING-CIVIL"
PUBSNAP_CODE = "PUBSNAP-TND-MOH-2026-001-V2"

OUT_BUNDLE = "GB-TND-MOH-2026-001-V2"
OUT_DSM = "DSM-TND-MOH-2026-001-V2"
OUT_DOM = "DOM-TND-MOH-2026-001-V2"
OUT_DEM = "DEM-TND-MOH-2026-001-V2"
OUT_DCM = "DCM-TND-MOH-2026-001-V2"

_ADDENDUM_TITLE = "Addendum No. 1 — BOQ Quantity Revision and Submission Deadline Extension"
_ADDENDUM_REASON = (
	"Correction of BOQ quantities and addition of plumbing connection item following "
	"supplier clarification and technical review."
)
_ADDENDUM_ISSUED_AT = "2026-05-18 14:20:00"
_OUT_V1_BUNDLE = "GB-TND-MOH-2026-001-V1"
_OUT_V1_DSM = "DSM-TND-MOH-2026-001-V1"
_OUT_V1_DOM = "DOM-TND-MOH-2026-001-V1"
_OUT_V1_DEM = "DEM-TND-MOH-2026-001-V1"
_OUT_V1_DCM = "DCM-TND-MOH-2026-001-V1"
_PUBSNAP_V1 = "PUBSNAP-TND-MOH-2026-001-V1"
_IMPACT_RECORD_CODE = f"AIR-{_ADDENDUM_CODE}"
_STDIA_CODE = f"STDIA-{_ADDENDUM_CODE}"
_PUBLISHED_AT = "2026-05-01 10:03:00"


def _sha256_hex(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _outputs_ready(instance_name: str) -> bool:
	for code in (OUT_BUNDLE, OUT_DSM, OUT_DOM, OUT_DEM, OUT_DCM):
		if not frappe.db.exists("Tender STD Generated Output", code):
			return False
		row = frappe.db.get_value(
			"Tender STD Generated Output",
			code,
			["tender_std_instance", "output_status"],
			as_dict=True,
		)
		if not row or row.tender_std_instance != instance_name or row.output_status != "Published":
			return False
	return True


def _seed_minimum_inputs(instance_name: str) -> None:
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"submission_deadline",
		"2026-06-05 11:00:00",
		ignore_publication_lock=True,
	)
	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		"WR-COMP-001",
		structured_text="WORKS master seed requirement.",
		requirement_status="Complete",
		attachment_required=False,
		attachment_status="Not Required",
		ignore_publication_lock=True,
	)
	boq = get_boq_for_instance(instance_name)
	if not boq:
		boq = StdInstanceBoqService.create_boq_for_instance(
			instance_name,
			currency="KES",
			boq_definition_code="WORKS-MASTER-BOQ",
			ignore_boq_publication_lock=True,
		)
	if not (boq.boq_bills or []):
		boq = StdInstanceBoqService.add_bill(
			boq.name,
			"1",
			"General Works",
			"Normal",
			ignore_boq_publication_lock=True,
		)
	if not (boq.boq_items or []):
		first_bill = boq.boq_bills[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			first_bill,
			"1.1",
			"Preliminaries",
			"Item",
			1,
			item_type="Normal",
			supplier_input_mode="Rate Only",
			ignore_boq_publication_lock=True,
		)


def _generate_and_publish_v2_outputs(instance_name: str) -> None:
	specs: list[tuple[Any, str]] = [
		(StdInstanceGeneratedOutputService.generate_bundle, OUT_BUNDLE),
		(StdInstanceGeneratedOutputService.generate_dsm, OUT_DSM),
		(StdInstanceGeneratedOutputService.generate_dom, OUT_DOM),
		(StdInstanceGeneratedOutputService.generate_dem, OUT_DEM),
		(StdInstanceGeneratedOutputService.generate_dcm, OUT_DCM),
	]
	for fn, doc_name in specs:
		if frappe.db.exists("Tender STD Generated Output", doc_name):
			continue
		doc = fn(instance_name, ignore_generated_output_lock=True, output_doc_name=doc_name)
		StdInstanceGeneratedOutputService.publish_output(doc.name)


def _ensure_std_instance(tender_code: str) -> Document:
	if frappe.db.exists("Tender STD Instance", INSTANCE_CODE):
		inst = frappe.get_doc("Tender STD Instance", INSTANCE_CODE)
		if (inst.tm2_tender or "").strip() != tender_code:
			frappe.throw(
				f"{INSTANCE_CODE} is bound to another tender ({inst.tm2_tender!r}).",
				title="WORKS master STD instance conflict",
			)
		return inst

	current = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tender_code)
	if current and current.name != INSTANCE_CODE:
		frappe.throw(
			f"Active STD instance {current.name} already exists for {tender_code}.",
			title="WORKS master STD instance conflict",
		)

	if not current:
		inst = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tender_code,
			ignore_permissions=True,
			record_template_usage=False,
			instance_name=INSTANCE_CODE,
		)
		inst.applicability_profile_code = WORKS_PROFILE_CODE
		inst.save(ignore_permissions=True)
		return frappe.get_doc("Tender STD Instance", inst.name)

	return frappe.get_doc("Tender STD Instance", INSTANCE_CODE)


def _ensure_std_instance_ready(instance: Document) -> Document:
	if not _outputs_ready(instance.name):
		_seed_minimum_inputs(instance.name)
		_generate_and_publish_v2_outputs(instance.name)
	readiness = StdInstanceReadinessService.evaluate(instance.name, persist=True)
	if readiness.get("status") != "Ready":
		frappe.throw(
			f"WORKS master STD instance is not publishable: {readiness!r}",
			title="WORKS master readiness failed",
		)
	status = (instance.instance_status or "").strip()
	if status in ("Draft", "In Configuration"):
		StdInstanceStateService.apply_transition(instance.name, "In Configuration", ignore_permissions=True)
		StdInstanceStateService.apply_transition(instance.name, "Ready for Publication", ignore_permissions=True)
	elif status == "Ready for Publication":
		pass
	elif status not in ("Published Locked", "Locked for Publication", "Locked for Approval"):
		StdInstanceStateService.apply_transition(instance.name, "In Configuration", ignore_permissions=True)
		StdInstanceStateService.apply_transition(instance.name, "Ready for Publication", ignore_permissions=True)

	_ensure_std_publication_snapshot(instance.name)

	current_status = (frappe.db.get_value("Tender STD Instance", instance.name, "instance_status") or "").strip()
	if current_status not in ("Published Locked",):
		StdPublicationLockService.lock_for_approval(instance.name, ignore_permissions=True)
		StdPublicationLockService.lock_for_publication(instance.name, ignore_permissions=True)
	return frappe.get_doc("Tender STD Instance", instance.name)


def _ensure_configuration_snapshot(instance_name: str) -> str:
	existing = frappe.get_all(
		"Tender STD Instance Snapshot",
		filters={"tender_std_instance": instance_name, "snapshot_type": "Configuration", "snapshot_status": "Final"},
		pluck="name",
		order_by="creation desc",
		limit=1,
	)
	if existing:
		return existing[0]
	cfg = StdInstanceSnapshotService.create_configuration_snapshot(
		instance_name,
		"WORKS master seed configuration snapshot",
		output_ref_overrides={
			"ref_bundle_output": OUT_BUNDLE,
			"ref_dsm_output": OUT_DSM,
			"ref_dom_output": OUT_DOM,
			"ref_dem_output": OUT_DEM,
			"ref_dcm_output": OUT_DCM,
		},
	)
	return cfg.name


def _ensure_approval_decision(tender_code: str, instance_name: str, configuration_snapshot: str) -> str:
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters={"tm2_tender": tender_code, "decision": DECISION_APPROVED},
		pluck="name",
		order_by="decided_at desc",
		limit=1,
	)
	if rows:
		return rows[0]
	doc = frappe.get_doc(
		{
			"doctype": "Tender Publication Approval Decision",
			"tm2_tender": tender_code,
			"tender_std_instance": instance_name,
			"configuration_snapshot": configuration_snapshot,
			"decision": DECISION_APPROVED,
			"decision_note": "WORKS master seed approval reference.",
			"decided_by": "Administrator",
			"decided_at": _PUBLISHED_AT,
			"payload_json": {"seed": "works_master"},
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_std_publication_snapshot(instance_name: str) -> Document:
	existing = frappe.get_all(
		"Tender STD Instance Snapshot",
		filters={"tender_std_instance": instance_name, "snapshot_type": "Publication", "snapshot_status": "Final"},
		pluck="name",
		order_by="creation desc",
		limit=1,
	)
	if existing:
		return frappe.get_doc("Tender STD Instance Snapshot", existing[0])
	return StdInstanceSnapshotService.create_publication_snapshot(
		instance_name,
		"WORKS master seed publication snapshot",
		output_ref_overrides={
			"ref_bundle_output": OUT_BUNDLE,
			"ref_dsm_output": OUT_DSM,
			"ref_dom_output": OUT_DOM,
			"ref_dem_output": OUT_DEM,
			"ref_dcm_output": OUT_DCM,
		},
	)


def _ensure_tender_publication_snapshot(
	tender_code: str,
	instance_name: str,
	std_pub: Document,
	approval_name: str,
	configuration_snapshot: str,
) -> str:
	if frappe.db.exists("Tender Publication Snapshot", {"evidence_package_code": PUBSNAP_CODE}):
		return "existing_by_code"
	existing_name = frappe.db.get_value("Tender Publication Snapshot", {"tm2_tender": tender_code}, "name")
	if existing_name:
		frappe.db.set_value(
			"Tender Publication Snapshot",
			existing_name,
			"evidence_package_code",
			PUBSNAP_CODE,
			update_modified=False,
		)
		return "patched_existing"

	pkg = frappe.db.get_value("TM2 Tender", tender_code, "procurement_package") or ""
	readiness_code = "READINESS|works-master-seed"
	evidence_code = PUBSNAP_CODE
	pub_hash = _sha256_hex(
		"|".join(
			[
				std_pub.name,
				readiness_code,
				approval_name,
				evidence_code,
			]
		)
	)
	row = frappe.get_doc(
		{
			"doctype": "Tender Publication Snapshot",
			"tm2_tender": tender_code,
			"procurement_package": pkg or None,
			"tender_std_instance": instance_name,
			"configuration_snapshot": configuration_snapshot,
			"std_publication_snapshot": std_pub.name,
			"source_template_version_code": STD_VERSION_REF,
			"applicability_profile_code": WORKS_PROFILE_CODE,
			"bundle_output_code": OUT_BUNDLE,
			"dsm_output_code": OUT_DSM,
			"dom_output_code": OUT_DOM,
			"dem_output_code": OUT_DEM,
			"dcm_output_code": OUT_DCM,
			"readiness_result_code": readiness_code,
			"approval_decision_code": approval_name,
			"evidence_package_code": evidence_code,
			"complete_publication_hash": pub_hash,
			"snapshot_status": "Final",
			"created_by": "Administrator",
			"created_at": _PUBLISHED_AT,
		}
	)
	row.insert(ignore_permissions=True)
	return "created"


def _impact_payload() -> dict[str, Any]:
	return {
		"affected_parameters": [
			{
				"parameter_key": "submission_deadline",
				"before": "2026-05-30T11:00:00+03:00",
				"after": "2026-06-05T11:00:00+03:00",
			},
			{
				"parameter_key": "opening_datetime",
				"before": "2026-05-30T11:30:00+03:00",
				"after": "2026-06-05T11:30:00+03:00",
			},
		],
		"affected_sections": ["WORKS-SEC-II", "WORKS-SEC-VI", "WORKS-SEC-III", "WORKS-SEC-IX"],
		"affected_boq_items": [
			{"item_code": "BOQ-003", "field": "quantity", "before": 850, "after": 920},
			{"item_code": "BOQ-005", "field": "quantity", "before": 95, "after": 110},
			{"item_code": "BOQ-013", "change": "ADDED", "quantity": 18, "unit": "No"},
		],
		"seed": "works_master",
	}


def _ensure_addendum_impact_record(addendum_name: str) -> str:
	if frappe.db.exists("TM2 Addendum Impact Record", _IMPACT_RECORD_CODE):
		return "existing"
	if frappe.db.exists("TM2 Addendum Impact Record", {"tm2_addendum": addendum_name}):
		return "existing_by_addendum"

	payload = _impact_payload()
	doc = frappe.get_doc(
		{
			"doctype": "TM2 Addendum Impact Record",
			"tm2_addendum": addendum_name,
			"std_impact_analysis_code": _STDIA_CODE,
			"previous_bundle_output_code": _OUT_V1_BUNDLE,
			"revised_bundle_output_code": OUT_BUNDLE,
			"previous_dsm_output_code": _OUT_V1_DSM,
			"revised_dsm_output_code": OUT_DSM,
			"previous_dom_output_code": _OUT_V1_DOM,
			"revised_dom_output_code": OUT_DOM,
			"previous_dem_output_code": _OUT_V1_DEM,
			"revised_dem_output_code": OUT_DEM,
			"previous_dcm_output_code": _OUT_V1_DCM,
			"revised_dcm_output_code": OUT_DCM,
			"previous_publication_snapshot_code": _PUBSNAP_V1,
			"revised_publication_snapshot_code": PUBSNAP_CODE,
			"deadline_extension_required": 1,
			"supplier_acknowledgement_required": 1,
			"bid_resubmission_required": 0,
			"impact_payload": payload,
			"created_at": _ADDENDUM_ISSUED_AT,
		}
	)
	doc.insert(ignore_permissions=True)
	return "created"


def _issue_addendum(doc: Document) -> None:
	doc.status = "Issued"
	doc.issued_by = doc.issued_by or "Administrator"
	doc.issued_at = doc.issued_at or _ADDENDUM_ISSUED_AT
	doc.save(ignore_permissions=True)


def _ensure_issued_addendum(tender_code: str) -> str:
	if frappe.db.exists("TM2 Addendum", _ADDENDUM_CODE):
		doc = frappe.get_doc("TM2 Addendum", _ADDENDUM_CODE)
		_ensure_addendum_impact_record(doc.name)
		st = (doc.status or "").strip()
		if st not in ("Issued", "Superseded"):
			_issue_addendum(doc)
		return "existing"

	doc = frappe.get_doc(
		{
			"doctype": "TM2 Addendum",
			"tm2_tender": tender_code,
			"tender_code": tender_code,
			"title": _ADDENDUM_TITLE,
			"reason": _ADDENDUM_REASON,
			"status": "Draft",
			"primary_impact_type": "BOQ Change",
			"affects_deadline": 1,
			"affects_submission_model": 1,
			"affects_opening_model": 1,
			"affects_evaluation_model": 1,
			"affects_contract_model": 1,
			"requires_supplier_acknowledgement": 1,
			"created_by": "Administrator",
			"created_at": "2026-05-13 09:00:00",
			"approved_by": "Administrator",
			"approved_at": "2026-05-18 11:30:00",
		}
	)
	doc.flags.ignore_tm2_add_tender_state_gate = True
	doc.insert(ignore_permissions=True)
	if doc.addendum_code != _ADDENDUM_CODE:
		frappe.throw(
			f"Expected addendum {_ADDENDUM_CODE!r}, got {doc.addendum_code!r}.",
			title="WORKS master addendum conflict",
		)
	_ensure_addendum_impact_record(doc.name)
	_issue_addendum(doc)
	return "created"


def ensure_works_master_publication_evidence() -> dict[str, Any]:
	"""Idempotently materialize spec §13.3–13.5 publication evidence for the master tender."""
	frappe.set_user("Administrator")
	if not frappe.db.exists("TM2 Tender", TENDER_CODE):
		return {"ok": False, "message": f"TM2 Tender {TENDER_CODE!r} not found."}

	seed_std_template_governance_for_existing_works_poc(force_mode="active")
	if not frappe.db.get_value("TM2 Tender", TENDER_CODE, "std_template"):
		frappe.db.set_value(
			"TM2 Tender",
			TENDER_CODE,
			"std_template",
			TEMPLATE_CODE,
			update_modified=False,
		)

	instance = _ensure_std_instance(TENDER_CODE)
	instance = _ensure_std_instance_ready(instance)
	cfg = _ensure_configuration_snapshot(instance.name)
	approval = _ensure_approval_decision(TENDER_CODE, instance.name, cfg)
	std_pub = _ensure_std_publication_snapshot(instance.name)
	tps_action = _ensure_tender_publication_snapshot(
		TENDER_CODE,
		instance.name,
		std_pub,
		approval,
		cfg,
	)
	addendum_action = _ensure_issued_addendum(TENDER_CODE)

	return {
		"ok": True,
		"tender_code": TENDER_CODE,
		"std_instance": instance.name,
		"publication_snapshot_action": tps_action,
		"addendum_action": addendum_action,
		"evidence_package_code": PUBSNAP_CODE,
	}
