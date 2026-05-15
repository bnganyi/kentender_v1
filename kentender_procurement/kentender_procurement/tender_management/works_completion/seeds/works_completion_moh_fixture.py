# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-1100 — deterministic Works completion golden seed (MOH pack IDs).

Idempotent when the Tender STD Instance is already **Locked for Approval** (Works
configuration snapshot + approval lock from WORKS-COMP-0700).

**Coexistence with STDINST-1400:** both targets use ``PKG-MOH-2026-001`` and default
``TND-MOH-2026-001``. If an instance for that tender exists in a **publication-frozen**
state (``Published Locked``, etc.), this seed returns ``ok: False`` with a stable
``code`` — it does not delete or replace data. Operators use a clean site / UAT wipe
or pass ``tender_reference_suffix`` (tests) for an isolated tender.

**Profile code:** the pack label ``WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022`` is returned as
``pack_works_profile_code`` for traceability. The instance ``applicability_profile_code``
always matches ``TenderStdBindingService._codes_from_std_template`` (WORKS-COMP-0110).

Manual golden (default tender reference)::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture.run

CI / isolated tender (suffix appended to ``TND-MOH-2026-001``)::

	frappe.call(
	    "kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture.run",
	    tender_reference_suffix="CI-abc123",
	)
"""

from __future__ import annotations

import re
from typing import Any

import frappe

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.parameter import (
	INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	WorksEvaluationOptionsService,
)
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.snapshot_lock import (
	WorksSnapshotLockService,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_readiness import (
	WorksReadinessService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)

# Pack / STDINST-1400 business label for the MOH civil Works profile (template binding must match).
WORKS_PROFILE_CODE = "WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022"
PACKAGE_CODE = "PKG-MOH-2026-001"
DEFAULT_TENDER_REFERENCE = "TND-MOH-2026-001"

_CODE_ALREADY = "WORKS_COMP_1100_ALREADY_LOCKED"
_CODE_CONFLICT = "WORKS_COMP_1100_STD_INSTANCE_NOT_EDITABLE"


def _resolve_tender_reference(tender_reference_suffix: str) -> str:
	sfx = (tender_reference_suffix or "").strip()
	if not sfx:
		return DEFAULT_TENDER_REFERENCE
	clean = re.sub(r"[^A-Za-z0-9\-]", "", sfx)[:40]
	if not clean:
		return DEFAULT_TENDER_REFERENCE
	combined = f"{DEFAULT_TENDER_REFERENCE}-{clean}"
	return combined[:140]


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
		(PACKAGE_CODE, PACKAGE_CODE, "WORKS-COMP-1100 Seed Package"),
	)
	return PACKAGE_CODE


def _ensure_tender_exists(package_code: str, tender_reference: str) -> str:
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
		if (doc.procurement_package or "").strip() != package_code:
			doc.procurement_package = package_code
			doc.save(ignore_permissions=True)
		return existing

	tender = frappe.new_doc("TM2 Tender")
	tender.std_template = TEMPLATE_CODE
	tender.tender_title = "MOH Works Tender 2026 — Works completion seed"
	tender.tender_reference = tender_reference
	tender.procurement_package = package_code
	tender.procurement_category = "Works"
	tender.procuring_entity_code = "MOH"
	tender.fiscal_year = "2026"
	tender.insert(ignore_permissions=True, ignore_mandatory=True)
	return tender.name


def _ensure_instance(tender_name: str) -> Any:
	"""Bind or refresh STD instance; profile/version must match ``_codes_from_std_template`` (WORKS-COMP-0110)."""
	std = (frappe.db.get_value("TM2 Tender", tender_name, "std_template") or "").strip()
	if not std:
		frappe.throw("TM2 Tender has no std_template.", title="WORKS_COMP_1100_NO_TEMPLATE")

	version_code, profile_code = TenderStdBindingService._codes_from_std_template(std)
	current = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tender_name)
	if current:
		doc = frappe.get_doc("Tender STD Instance", current.name)
		changed = False
		if (doc.template_version_code or "").strip() != version_code:
			doc.template_version_code = version_code
			changed = True
		if (doc.applicability_profile_code or "").strip() != profile_code:
			doc.applicability_profile_code = profile_code
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
			return frappe.get_doc("Tender STD Instance", doc.name)
		return doc
	return TenderStdBindingService.create_std_instance_for_tm2_tender(
		tender_name,
		ignore_permissions=True,
		record_template_usage=False,
	)


def _latest_configuration_snapshot(std_instance: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD Instance Snapshot",
		filters={
			"tender_std_instance": std_instance,
			"snapshot_type": "Configuration",
			"snapshot_status": "Final",
		},
		pluck="name",
		order_by="creation desc",
		limit=1,
	)
	return rows[0] if rows else None


def _tds_payload(tender_reference: str) -> dict[str, Any]:
	return {
		"tender_title": f"MOH Representative Works — {tender_reference}",
		"procuring_entity_name": "Ministry of Health",
		"project_location": "Nairobi County",
		"procurement_method": "Open National",
		"submission_deadline": "2026-12-20 17:00:00",
		"opening_datetime": "2026-12-21 09:00:00",
		"clarification_deadline": "2026-12-10 12:00:00",
		"bid_validity_days": "120",
		"tender_security_required": "1",
		"tender_security_type": "Bank Guarantee",
		"tender_security_amount": "500000",
		"tender_security_currency": "KES",
		"site_visit_required": "1",
		"site_visit_datetime": "2026-11-15 10:00:00",
		"site_visit_location": "MOH Project Site Office",
		"pre_tender_meeting_required": "0",
		"pre_tender_meeting_datetime": "",
		"pre_tender_meeting_location": "",
		"bid_currency": "KES",
		"language": "en",
		"margin_of_preference_applicable": "0",
	}


def _scc_payload_aliases() -> dict[str, Any]:
	return {
		"completion_period_days": "18",
		"defects_liability_period_days": "12",
		"scc.performance_security_required": "1",
		"performance_security_percent": "10",
		"retention_percent": "10",
		"liquidated_damages_percent_per_day": "0.05% per day of delay",
		"advance_payment_allowed": "1",
		"scc.insurance_requirements": "Contractors all risks per GCC; public liability as applicable.",
		"bid_currency": "KES",
		"scc.engineer_or_project_manager": "Employer's Representative — MOH",
		"scc.payment_terms": "Interim payments against certified works; final on completion.",
		"scc.dispute_resolution_forum": "ARBITRATION",
		"maximum_liquidated_damages_percent": "10",
	}


def _evaluation_payload() -> dict[str, Any]:
	return {
		"minimum_average_annual_turnover": {
			"amount": "50000000",
			"currency": "KES",
			"years": "3",
		},
		"similar_works_experience": {
			"minimum_contracts": "2",
			"minimum_value_each": "10000000",
			"period_years": "5",
		},
		"key_personnel_required": "1",
		"equipment_schedule_required": "1",
		"margin_of_preference_applicable": "0",
	}


def _requirements_payload() -> dict[str, Any]:
	# Synthetic file paths live on drawing rows; specifications use narrative only
	# (attachment list entries must be section-bound attachment codes, not bare dicts).
	return {
		"specifications": {
			"structured_summary": (
				"Representative MOH civil works specifications seed (WORKS-COMP-1100). "
				"See drawing register file_reference paths under /files/works_seed/ for "
				"specifications_v1.pdf and employers_requirements.pdf equivalents."
			),
		},
		"method_statement_required": False,
		"work_programme_required": False,
	}


def _drawing_payload() -> dict[str, Any]:
	base = "/files/works_seed/drawings"
	return {
		"drawings": [
			{
				"drawing_code": "MOH-DWG-G-001",
				"title": "General arrangement — Level 1",
				"revision": "C",
				"file_reference": f"{base}/ga_l1_rev_c.pdf",
				"section_code": "DRAWINGS",
				"classification": "Supplier Facing",
				"issue_status": "Current",
			},
			{
				"drawing_code": "MOH-DWG-S-002",
				"title": "Structural — RC framing",
				"revision": "B",
				"file_reference": f"{base}/struct_rc_rev_b.pdf",
				"section_code": "DRAWINGS",
				"classification": "Supplier Facing",
				"issue_status": "Current",
			},
			{
				"drawing_code": "MOH-DWG-M-003",
				"title": "MEP — Riser diagram",
				"revision": "A",
				"file_reference": f"{base}/mep_riser_rev_a.pdf",
				"section_code": "DRAWINGS",
				"classification": "Supplier Facing",
				"issue_status": "Current",
			},
		],
	}


def _boq_payload() -> dict[str, Any]:
	return {
		"header": {
			"currency": "KES",
			"pricing_model": "Bills of Quantities",
			"quantity_owner": "Procuring Entity",
			"supplier_input_mode": "Rate Only",
			"amount_computation_rule": "quantity_times_rate",
			"arithmetic_correction_stage": "Evaluation",
			"boq_definition_code": "DEFAULT",
		},
		"bills": [
			{
				"bill_number": "B1",
				"bill_title": "Preliminaries and attendances",
				"bill_type": "Standard",
				"order_index": 0,
				"items": [
					{
						"item_number": "1.1",
						"description": "Site establishment and mobilization",
						"unit": "ls",
						"quantity": 1,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
			{
				"bill_number": "B2",
				"bill_title": "Structural works",
				"bill_type": "Standard",
				"order_index": 1,
				"items": [
					{
						"item_number": "2.1",
						"description": "Reinforced concrete slab 200mm",
						"unit": "m3",
						"quantity": 42,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
			{
				"bill_number": "B3",
				"bill_title": "Finishes",
				"bill_type": "Standard",
				"order_index": 2,
				"items": [
					{
						"item_number": "3.1",
						"description": "Internal emulsion paint — walls",
						"unit": "m2",
						"quantity": 850,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
		],
	}


def _apply_works_pack(std_instance: str, tender_reference: str) -> None:
	WorksTdsCompletionService.save_tds_values(std_instance, _tds_payload(tender_reference))
	WorksEvaluationOptionsService.save_evaluation_options(std_instance, _evaluation_payload())
	WorksRequirementsCompletionService.save_works_requirements(std_instance, _requirements_payload())
	WorksDrawingRegisterService.save_drawing_register(std_instance, _drawing_payload())
	WorksBoqCompletionService.save_boq(std_instance, _boq_payload())
	WorksSccCompletionService.save_scc_values(std_instance, _scc_payload_aliases())


def run(tender_reference_suffix: str = "") -> dict[str, Any]:
	"""Seed Works completion data, generate outputs, persist readiness Ready, snapshot+lock.

	:param tender_reference_suffix: When non-empty, appended to ``TND-MOH-2026-001`` for
		isolated CI runs. Empty string keeps the pack default reference (manual golden).
	"""
	frappe.set_user("Administrator")
	upsert_std_template()
	seed_std_template_governance_for_existing_works_poc(force_mode="active")

	tender_reference = _resolve_tender_reference(tender_reference_suffix)
	package_name = _ensure_package_exists()
	tender_name = _ensure_tender_exists(package_name, tender_reference)
	instance = _ensure_instance(tender_name)
	si_name = instance.name
	ap_profile = (
		frappe.db.get_value("Tender STD Instance", si_name, "applicability_profile_code") or ""
	).strip()
	st = (instance.instance_status or "").strip()

	if st == "Locked for Approval":
		return {
			"ok": True,
			"already_seeded": True,
			"code": _CODE_ALREADY,
			"message": (
				"Tender STD Instance is already Locked for Approval; "
				"WORKS-COMP-1100 seed skipped (idempotent)."
			),
			"template_code": TEMPLATE_CODE,
			"works_applicability_profile_code": ap_profile,
			"pack_works_profile_code": WORKS_PROFILE_CODE,
			"procurement_package_code": package_name,
			"tender_reference": tender_reference,
			"tender_name": tender_name,
			"std_instance_code": si_name,
			"instance_status": st,
			"configuration_snapshot": _latest_configuration_snapshot(si_name),
		}

	if st in INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION:
		return {
			"ok": False,
			"already_seeded": False,
			"code": _CODE_CONFLICT,
			"message": (
				f"Tender STD Instance is in status {st!r}, which blocks Works completion edits. "
				"This often follows STDINST-1400 (publication lock). Use a clean site / UAT wipe "
				"or pass tender_reference_suffix for an isolated tender."
			),
			"template_code": TEMPLATE_CODE,
			"works_applicability_profile_code": ap_profile,
			"pack_works_profile_code": WORKS_PROFILE_CODE,
			"procurement_package_code": package_name,
			"tender_reference": tender_reference,
			"tender_name": tender_name,
			"std_instance_code": si_name,
			"instance_status": st,
		}

	_apply_works_pack(si_name, tender_reference)
	gen_out = WorksOutputGenerationService.generate_all_works_outputs(si_name)
	readiness = WorksReadinessService.run_works_readiness(si_name, persist=True)
	if (readiness.get("status") or "").strip() != "Ready":
		frappe.throw(
			f"WORKS-COMP-1100 seed: Works readiness not Ready (status={readiness.get('status')!r}).",
			title="WORKS_COMP_1100_READINESS_NOT_READY",
		)

	lock_out = WorksSnapshotLockService.create_configuration_snapshot_and_lock(si_name)
	final_st = (lock_out.get("instance_status") or "").strip()

	return {
		"ok": True,
		"already_seeded": False,
		"code": "WORKS_COMP_1100_OK",
		"message": "WORKS-COMP-1100 representative Works completion seed applied.",
		"template_code": TEMPLATE_CODE,
		"works_applicability_profile_code": (
			frappe.db.get_value("Tender STD Instance", si_name, "applicability_profile_code") or ""
		).strip(),
		"pack_works_profile_code": WORKS_PROFILE_CODE,
		"procurement_package_code": package_name,
		"tender_reference": tender_reference,
		"tender_name": tender_name,
		"std_instance_code": si_name,
		"instance_status": final_st,
		"readiness_status": (readiness.get("status") or "").strip(),
		"generated_outputs": gen_out.get("outputs"),
		"configuration_snapshot": lock_out.get("snapshot"),
		"lock_result": lock_out,
	}


def seed_works_completion_moh_fixture(tender_reference_suffix: str = "") -> dict[str, Any]:
	"""Alias for :func:`run` (explicit symbol for imports)."""
	return run(tender_reference_suffix=tender_reference_suffix)
