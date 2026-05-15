# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1400 — minimal publishable STD instance seed fixture."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

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

WORKS_PROFILE_CODE = "WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022"
PACKAGE_CODE = "PKG-MOH-2026-001"
TENDER_REFERENCE = "TND-MOH-2026-001"


def _ensure_package_exists() -> str:
	if frappe.db.exists("Procurement Package", PACKAGE_CODE):
		return PACKAGE_CODE
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
		(PACKAGE_CODE, PACKAGE_CODE, "STDINST-1400 Seed Package"),
	)
	return PACKAGE_CODE


def _ensure_tender_exists(package_code: str) -> str:
	existing = frappe.db.get_value(
		"TM2 Tender",
		{"tender_reference": TENDER_REFERENCE},
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
	tender.tender_title = "MOH Works Tender 2026 Seed"
	tender.tender_reference = TENDER_REFERENCE
	tender.procurement_package = package_code
	tender.procurement_category = "Works"
	tender.procuring_entity_code = "MOH"
	tender.fiscal_year = "2026"
	tender.insert(ignore_permissions=True, ignore_mandatory=True)
	return tender.name


def _ensure_instance(tender_name: str) -> Document:
	current = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tender_name)
	if current:
		return current
	inst = TenderStdBindingService.create_std_instance_for_tm2_tender(
		tender_name,
		ignore_permissions=True,
		record_template_usage=False,
	)
	inst.applicability_profile_code = WORKS_PROFILE_CODE
	inst.save(ignore_permissions=True)
	return frappe.get_doc("Tender STD Instance", inst.name)


def _seed_minimum_inputs(instance_name: str) -> None:
	StdInstanceParameterService.set_parameter_value(
		instance_name,
		"submission_deadline",
		"2026-12-31 10:00:00",
		ignore_publication_lock=True,
	)
	StdInstanceWorksRequirementService.set_works_requirement(
		instance_name,
		"WR-COMP-001",
		structured_text="Seed works requirement for STDINST-1400.",
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
			boq_definition_code="STDINST-1400-BOQ",
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


def _generate_and_publish_outputs(instance_name: str) -> dict[str, str]:
	generated: dict[str, str] = {}
	for output_type, fn in (
		("Bundle", StdInstanceGeneratedOutputService.generate_bundle),
		("DSM", StdInstanceGeneratedOutputService.generate_dsm),
		("DOM", StdInstanceGeneratedOutputService.generate_dom),
		("DEM", StdInstanceGeneratedOutputService.generate_dem),
		("DCM", StdInstanceGeneratedOutputService.generate_dcm),
	):
		doc = fn(instance_name, ignore_generated_output_lock=True)
		doc = StdInstanceGeneratedOutputService.publish_output(doc.name)
		generated[output_type] = doc.name
	return generated


def run() -> dict:
	"""Create deterministic minimal publishable fixture for STDINST-1400."""
	frappe.set_user("Administrator")
	seed_std_template_governance_for_existing_works_poc(force_mode="active")
	package_name = _ensure_package_exists()
	tender_name = _ensure_tender_exists(package_name)
	instance = _ensure_instance(tender_name)
	_seed_minimum_inputs(instance.name)
	outputs = _generate_and_publish_outputs(instance.name)
	readiness = StdInstanceReadinessService.evaluate(instance.name, persist=True)
	if readiness.get("status") != "Ready":
		frappe.throw("STDINST-1400 seed instance is not publishable.")

	StdInstanceStateService.apply_transition(instance.name, "In Configuration", ignore_permissions=True)
	StdInstanceStateService.apply_transition(instance.name, "Ready for Publication", ignore_permissions=True)
	snapshot = StdInstanceSnapshotService.create_publication_snapshot(
		instance.name,
		"STDINST-1400 seed publication snapshot",
	)
	StdPublicationLockService.lock_for_approval(instance.name, ignore_permissions=True)
	locked = StdPublicationLockService.lock_for_publication(instance.name, ignore_permissions=True)

	return {
		"ok": True,
		"template_code": TEMPLATE_CODE,
		"works_applicability_profile_code": WORKS_PROFILE_CODE,
		"procurement_package_code": package_name,
		"tender_reference": TENDER_REFERENCE,
		"tender_name": tender_name,
		"std_instance_code": locked.name,
		"instance_status": locked.instance_status,
		"readiness_status": (frappe.db.get_value("Tender STD Instance", locked.name, "readiness_status") or "").strip(),
		"generated_outputs": outputs,
		"publication_snapshot_code": snapshot.name,
	}
