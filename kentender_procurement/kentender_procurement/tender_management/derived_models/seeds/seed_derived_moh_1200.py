# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1200 — Representative Works derived-model seed fixtures (pack §19).

Deterministic document names, generators for ``content_json`` (source traces),
idempotent when the fixture chain is already complete, and compatible with
``OutputConsumptionService.validate_consumption`` (including Contract after a
snapshot-bound DCM republication).

If another active STD instance already exists for the same tender reference
(e.g. STDINST-1400 ran first on ``TND-MOH-2026-001``), this seed returns
``ok: False`` with ``DERIVED_1200_ACTIVE_INSTANCE_CONFLICT`` instead of throwing.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.tender_management.seeds.seed_std_inst_1400 import (
	PACKAGE_CODE,
	WORKS_PROFILE_CODE,
	_ensure_package_exists,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
)
from kentender_procurement.tender_management.std_instance.binding import (
	TenderStdBindingService,
)
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.publication_lock import (
	StdPublicationLockService,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.snapshot import (
	StdInstanceSnapshotService,
)
from kentender_procurement.tender_management.std_instance.state import (
	StdInstanceStateService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)

# Pack §19 literals
INSTANCE_CODE = "STDINST-TND-MOH-2026-001"
TENDER_REFERENCE = "TND-MOH-2026-001"
OUT_BUNDLE = "GB-TND-MOH-2026-001-V1"
OUT_DSM = "DSM-TND-MOH-2026-001-V1"
OUT_DOM = "DOM-TND-MOH-2026-001-V1"
OUT_DEM = "DEM-TND-MOH-2026-001-V1"
OUT_DCM_V1 = "DCM-TND-MOH-2026-001-V1"
SNAP_PUB = "SNAP-PUB-TND-MOH-2026-001-V1"

CODE_ACTIVE_INSTANCE_CONFLICT = "DERIVED_1200_ACTIVE_INSTANCE_CONFLICT"
CODE_INSTANCE_TENDER_MISMATCH = "DERIVED_1200_INSTANCE_TENDER_MISMATCH"


def _ensure_package_by_code(package_code: str, package_label: str) -> str:
	"""Insert a minimal ``Procurement Package`` row when missing (same pattern as STDINST-1400)."""
	pc = (package_code or "").strip()
	if not pc:
		frappe.throw("procurement package_code is required.")
	if frappe.db.exists("Procurement Package", pc):
		return pc
	lbl = (package_label or pc).strip()
	frappe.db.sql(
		"""
		insert into `tabProcurement Package`
		(name, creation, modified, modified_by, owner, docstatus,
		 package_code, package_name, procurement_method, contract_type,
		 currency, estimated_value, status, method_override_flag, is_emergency, is_active, created_by)
		values
		(%s, now(), now(), 'Administrator', 'Administrator', 0,
		 %s, %s, 'Open Tender', 'Fixed Price', 'KES', 0, 'Draft', 0, 0, 1, 'Administrator')
		""",
		(pc, pc, lbl),
	)
	return pc


def _ensure_tender_for_reference(package_code: str, tender_reference: str) -> str:
	existing = frappe.db.get_value(
		"TM2 Tender",
		{"tender_reference": tender_reference},
		"name",
	)
	if existing:
		doc = frappe.get_doc("TM2 Tender", existing)
		if (doc.std_template or "").strip() != TEMPLATE_CODE:
			doc.std_template = TEMPLATE_CODE
			doc.save(ignore_permissions=True)
		return existing

	tender = frappe.new_doc("TM2 Tender")
	tender.std_template = TEMPLATE_CODE
	tender.tender_title = "MOH Works Tender 2026 (DERIVED-1200 fixture)"
	tender.tender_reference = tender_reference
	tender.procurement_package = package_code
	tender.procurement_category = "Works"
	tender.procuring_entity_code = "MOH"
	tender.fiscal_year = "2026"
	tender.insert(ignore_permissions=True, ignore_mandatory=True)
	return tender.name


def _fixture_complete(instance_name: str) -> bool:
	if not frappe.db.exists("Tender STD Instance", instance_name):
		return False
	if frappe.db.get_value("Tender STD Instance", instance_name, "instance_status") != "Published Locked":
		return False
	if not frappe.db.exists("Tender STD Instance Snapshot", SNAP_PUB):
		return False
	snap_tsi = frappe.db.get_value("Tender STD Instance Snapshot", SNAP_PUB, "tender_std_instance")
	if snap_tsi != instance_name:
		return False
	fixed = (OUT_BUNDLE, OUT_DSM, OUT_DOM, OUT_DEM, OUT_DCM_V1)
	for oname in fixed:
		if not frappe.db.exists("Tender STD Generated Output", oname):
			return False
		row = frappe.db.get_value(
			"Tender STD Generated Output",
			oname,
			["tender_std_instance", "output_status"],
			as_dict=True,
		)
		if row.tender_std_instance != instance_name:
			return False
		if oname == OUT_DCM_V1:
			if row.output_status not in ("Published", "Superseded"):
				return False
		elif row.output_status != "Published":
			return False

	cur_dcm = (frappe.db.get_value("Tender STD Instance", instance_name, "current_dcm_output_code") or "").strip()
	if not cur_dcm or cur_dcm == OUT_DCM_V1:
		return False
	cur = frappe.db.get_value(
		"Tender STD Generated Output",
		cur_dcm,
		["output_status", "source_instance_snapshot_code"],
		as_dict=True,
	)
	if cur.output_status != "Published":
		return False
	if (cur.source_instance_snapshot_code or "").strip() != SNAP_PUB:
		return False
	return True


def _result_summary(
	instance_name: str,
	tender_name: str,
	*,
	procurement_package_code: str,
	tender_reference: str,
	publication_snapshot_code: str,
) -> dict[str, Any]:
	cur_dcm = (frappe.db.get_value("Tender STD Instance", instance_name, "current_dcm_output_code") or "").strip()
	outputs = {
		"Bundle": OUT_BUNDLE,
		"DSM": OUT_DSM,
		"DOM": OUT_DOM,
		"DEM": OUT_DEM,
		"DCM": OUT_DCM_V1,
		"DCM_current": cur_dcm,
	}
	return {
		"ok": True,
		"code": None,
		"message": None,
		"template_code": TEMPLATE_CODE,
		"works_applicability_profile_code": WORKS_PROFILE_CODE,
		"procurement_package_code": procurement_package_code,
		"tender_reference": tender_reference,
		"tender_name": tender_name,
		"std_instance_code": instance_name,
		"instance_status": frappe.db.get_value("Tender STD Instance", instance_name, "instance_status"),
		"readiness_status": (frappe.db.get_value("Tender STD Instance", instance_name, "readiness_status") or "").strip(),
		"generated_outputs": outputs,
		"publication_snapshot_code": publication_snapshot_code,
	}


def _seed_derived_inputs(instance_name: str) -> None:
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"submission_deadline",
		"2026-12-31 10:00:00",
		ignore_publication_lock=True,
	)
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"SECURITY.TENDER_SECURITY_MODE",
		"TENDER_SECURITY",
		ignore_publication_lock=True,
	)
	# Pack §19 DCM YAML literals (explicit days / percents; not all exist as template field_codes).
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"CONTRACT.COMPLETION_PERIOD_DAYS",
		"180",
		ignore_publication_lock=True,
	)
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"CONTRACT.DEFECTS_LIABILITY_PERIOD_DAYS",
		"365",
		ignore_publication_lock=True,
	)
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"SECURITY.PERFORMANCE_SECURITY_PERCENTAGE",
		"10",
		ignore_publication_lock=True,
	)
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"CONTRACT.RETENTION_PERCENTAGE",
		"5",
		ignore_publication_lock=True,
	)
	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		"WR-COMP-001",
		structured_text="DERIVED-1200 seed works requirement.",
		requirement_status="Complete",
		attachment_required=False,
		attachment_status="Not Required",
		ignore_publication_lock=True,
	)
	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		"METHOD_STATEMENT",
		structured_text="Method statement narrative for DERIVED-1200.",
		structured_data=json.dumps({"flag_resolved": True, "required": True}),
		requirement_status="Complete",
		attachment_required=False,
		attachment_status="Not Required",
		drives_dsm=True,
		ignore_publication_lock=True,
	)

	boq = get_boq_for_instance(instance_name)
	if not boq:
		boq = StdInstanceBoqService.create_boq_for_instance(
			instance_name,
			currency="KES",
			boq_definition_code="DERIVED-1200-BOQ",
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


def _generate_and_publish_named(instance_name: str) -> None:
	specs: list[tuple[str, Any, str]] = [
		("Bundle", StdInstanceGeneratedOutputService.generate_bundle, OUT_BUNDLE),
		("DSM", StdInstanceGeneratedOutputService.generate_dsm, OUT_DSM),
		("DOM", StdInstanceGeneratedOutputService.generate_dom, OUT_DOM),
		("DEM", StdInstanceGeneratedOutputService.generate_dem, OUT_DEM),
		("DCM", StdInstanceGeneratedOutputService.generate_dcm, OUT_DCM_V1),
	]
	for _ot, fn, doc_name in specs:
		doc = fn(
			instance_name,
			ignore_generated_output_lock=True,
			output_doc_name=doc_name,
		)
		StdInstanceGeneratedOutputService.publish_output(doc.name)


def run(
	*,
	tender_reference: str | None = None,
	procurement_package_code: str | None = None,
) -> dict[str, Any]:
	"""Load or refresh the §19 MOH fixture chain."""
	frappe.set_user("Administrator")
	ref = (tender_reference or TENDER_REFERENCE).strip()
	pkg = (procurement_package_code or PACKAGE_CODE).strip()

	seed_std_template_governance_for_existing_works_poc(force_mode="active")
	if pkg == PACKAGE_CODE:
		package_name = _ensure_package_exists()
	else:
		package_name = _ensure_package_by_code(pkg, f"{pkg} (DERIVED-1200)")
	tender_name = _ensure_tender_for_reference(package_name, ref)

	if frappe.db.exists("Tender STD Instance", INSTANCE_CODE):
		existing_si = frappe.get_doc("Tender STD Instance", INSTANCE_CODE)
		if (existing_si.tm2_tender or "").strip() != tender_name:
			return {
				"ok": False,
				"code": CODE_INSTANCE_TENDER_MISMATCH,
				"message": (
					f"{INSTANCE_CODE} is bound to another tender; "
					"delete it or use a matching tender_reference."
				),
			}

	current = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tender_name)
	if current and current.name != INSTANCE_CODE:
		return {
			"ok": False,
			"code": CODE_ACTIVE_INSTANCE_CONFLICT,
			"message": (
				f"Active STD instance {current.name} already exists for tender reference {ref}; "
				"remove it or run DERIVED-1200 before STDINST-1400 on this tender."
			),
		}

	if _fixture_complete(INSTANCE_CODE):
		return _result_summary(
			INSTANCE_CODE,
			tender_name,
			procurement_package_code=package_name,
			tender_reference=ref,
			publication_snapshot_code=SNAP_PUB,
		)

	if not current:
		inst = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tender_name,
			ignore_permissions=True,
			record_template_usage=False,
			instance_name=INSTANCE_CODE,
		)
		inst.applicability_profile_code = WORKS_PROFILE_CODE
		inst.save(ignore_permissions=True)
	else:
		inst = frappe.get_doc("Tender STD Instance", INSTANCE_CODE)

	_seed_derived_inputs(inst.name)
	_generate_and_publish_named(inst.name)

	readiness = StdInstanceReadinessService.evaluate(inst.name, persist=True)
	if readiness.get("status") != "Ready":
		frappe.throw("DERIVED-1200 seed instance is not publishable.")

	StdInstanceStateService.apply_transition(inst.name, "In Configuration", ignore_permissions=True)
	StdInstanceStateService.apply_transition(inst.name, "Ready for Publication", ignore_permissions=True)

	snapshot = StdInstanceSnapshotService.create_publication_snapshot(
		inst.name,
		"DERIVED-1200 publication snapshot",
		snapshot_name=SNAP_PUB,
	)

	dcm2 = StdInstanceGeneratedOutputService.generate_dcm(
		inst.name,
		ignore_generated_output_lock=True,
		source_instance_snapshot_code=snapshot.name,
	)
	StdInstanceGeneratedOutputService.publish_output(dcm2.name)

	StdPublicationLockService.lock_for_approval(inst.name, ignore_permissions=True)
	locked = StdPublicationLockService.lock_for_publication(inst.name, ignore_permissions=True)

	return _result_summary(
		locked.name,
		tender_name,
		procurement_package_code=package_name,
		tender_reference=ref,
		publication_snapshot_code=snapshot.name,
	)


def ensure_instance_for_tests(
	tender_reference: str,
	*,
	procurement_package_code: str | None = None,
) -> dict[str, Any]:
	"""Test helper: isolated tender reference, same §19 instance / output names."""
	return run(
		tender_reference=tender_reference,
		procurement_package_code=procurement_package_code,
	)
