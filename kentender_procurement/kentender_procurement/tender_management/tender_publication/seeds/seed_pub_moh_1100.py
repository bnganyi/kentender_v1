# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-1100 — Publication readiness seed fixtures (Cursor pack §19).

Uses pack §19 ``PKG-MOH-2026-001`` (row ensured for other seeds); fixture tenders do
**not** link ``procurement_package`` to that code (planning handoff uniqueness). Release
lineage uses ``source_package_code`` only.
Tender references and STD instance names use ``TND-MOH-PUB1100-{TAG}`` /
``STDINST-TND-MOH-PUB1100-{TAG}`` so this seed can coexist with STDINST-1400 /
DERIVED-1200 on ``TND-MOH-2026-001``.

Variants: ``ready``, ``no_bundle``, ``stale_dem``, ``no_std_binding``, ``approved``, ``published``.

Bench::

	bench --site kentender.midas.com execute \\
		kentender_procurement.tender_management.tender_publication.seeds.seed_pub_moh_1100.run_fixture \\
		--kwargs "{'variant': 'ready'}"
"""

from __future__ import annotations

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
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.approve_tender_publication import (
	approve_tender_publication,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	ApprovalDecisionService,
	DECISION_APPROVED,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
	clear_publication_readiness_cache,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)

VALID_VARIANTS = frozenset(
	{"ready", "no_bundle", "stale_dem", "no_std_binding", "approved", "published"},
)

_TAG_BY_VARIANT: dict[str, str] = {
	"ready": "READY",
	"no_bundle": "NOBUNDLE",
	"stale_dem": "STALEDEM",
	"no_std_binding": "NOSTD",
	"approved": "APPROVED",
	"published": "PUBLISHED",
}


def fixture_codes(variant: str) -> dict[str, str]:
	"""Deterministic codes for the variant (PUB-1100 / pack §19 pattern, PUB1100 disambiguator)."""
	v = (variant or "").strip().lower()
	tag = _TAG_BY_VARIANT[v]
	return {
		"variant": v,
		"tag": tag,
		"procurement_package_code": PACKAGE_CODE,
		"tender_reference": f"TND-MOH-PUB1100-{tag}",
		"std_instance_code": f"STDINST-TND-MOH-PUB1100-{tag}",
		"release_code": f"REL-PKG-MOH-PUB1100-{tag}-001",
		"output_bundle": f"GB-TND-MOH-PUB1100-{tag}-V1",
		"output_dsm": f"DSM-TND-MOH-PUB1100-{tag}-V1",
		"output_dom": f"DOM-TND-MOH-PUB1100-{tag}-V1",
		"output_dem": f"DEM-TND-MOH-PUB1100-{tag}-V1",
		"output_dcm": f"DCM-TND-MOH-PUB1100-{tag}-V1",
	}


def _latest_approval_decision_row(tender_lookup: str) -> Any | None:
	tk = (tender_lookup or "").strip()
	if not tk:
		return None
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		return None
	filters: dict[str, str] = {"tm2_tender": tm2.name}
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters=filters,
		pluck="name",
		order_by="decided_at desc",
		limit=1,
	)
	if not rows:
		return None
	return frappe.get_doc("Tender Publication Approval Decision", rows[0])


def _is_approved_for_publication(tender_lookup: str) -> bool:
	prev = _latest_approval_decision_row(tender_lookup)
	return bool(prev and (prev.decision or "").strip() == DECISION_APPROVED)


def _is_tender_published(tender_lookup: str) -> bool:
	tm2 = resolve_tm2_tender_document(tender_lookup)
	if not tm2:
		return False
	return (frappe.db.get_value("TM2 Tender", tm2.name, "status") or "").strip() == "Published"


def _ensure_variant_package(tag: str) -> str:
	pkg_code = f"PKG-PUB1100-{tag}"
	if frappe.db.exists("Procurement Package", pkg_code):
		return pkg_code
	plan_row = frappe.db.sql("select name from `tabProcurement Plan` limit 1", as_dict=True)
	if not plan_row:
		frappe.throw(
			"PUB-1100 seed requires at least one Procurement Plan in the database.",
			exc=frappe.ValidationError,
		)
	plan_id = plan_row[0]["name"]
	frappe.db.sql(
		"""
		insert into `tabProcurement Package`
			(name, creation, modified, modified_by, owner, docstatus, idx,
			 package_code, package_name, plan_id, procurement_method, contract_type,
			 currency, estimated_value, status, method_override_flag, is_emergency, is_active, created_by)
		values
			(%s, now(), now(), 'Administrator', 'Administrator', 0, 0,
			 %s, %s, %s, 'Open Tender', 'Fixed Price', 'KES', 0, 'Draft', 0, 0, 1, 'Administrator')
		""",
		(pkg_code, pkg_code, f"PUB-1100 {tag}", plan_id),
	)
	return pkg_code


def _ensure_tm2_fixture(codes: dict[str, str]) -> tuple[str, str]:
	"""Return ``(tm2_name, tender_code)`` for this PUB-1100 variant."""
	ref = codes["tender_reference"]
	rel = codes["release_code"]
	tag = codes["tag"]
	desired_tc = f"TND-MOH-PUB1100-{tag}"
	pkg = _ensure_variant_package(tag)
	plan_id = (frappe.db.get_value("Procurement Package", pkg, "plan_id") or "").strip()
	if not plan_id:
		frappe.throw("PUB-1100: package has no plan_id.", exc=frappe.ValidationError)

	existing = frappe.db.get_value("TM2 Tender", {"tender_reference": ref}, "name")
	if existing:
		doc = frappe.get_doc("TM2 Tender", existing)
		changed = False
		if (doc.std_template or "").strip() != TEMPLATE_CODE:
			doc.std_template = TEMPLATE_CODE
			changed = True
		if (doc.source_package_code or "").strip() != rel:
			doc.source_package_code = rel
			changed = True
		if (doc.procurement_package or "").strip() != pkg:
			doc.procurement_package = pkg
			changed = True
		if (doc.procurement_plan or "").strip() != plan_id:
			doc.procurement_plan = plan_id
			changed = True
		if (doc.tender_code or "").strip() != desired_tc:
			frappe.db.set_value("TM2 Tender", existing, "tender_code", desired_tc, update_modified=False)
		if changed:
			doc.save(ignore_permissions=True)
		doc.reload()
		return existing, canonical_tm2_tender_code(doc)

	t = frappe.new_doc("TM2 Tender")
	t.tender_code = desired_tc
	t.tender_title = f"PUB-1100 MOH {ref}"
	t.tender_reference = ref
	t.procurement_package = pkg
	t.procurement_plan = plan_id
	t.procuring_entity_code = "MOH"
	t.fiscal_year = "2026"
	t.procurement_method = "Open Tender"
	t.procurement_category = "Works"
	t.tender_visibility = "Public"
	t.std_template = TEMPLATE_CODE
	t.source_package_code = rel
	t.insert(ignore_permissions=True)
	return t.name, canonical_tm2_tender_code(t)


def _ensure_tm2_access_rule(tm2_name: str) -> None:
	if frappe.db.exists("TM2 Tender Access Rule", {"tm2_tender": tm2_name}):
		return
	frappe.get_doc(
		{
			"doctype": "TM2 Tender Access Rule",
			"tm2_tender": tm2_name,
			"visibility": "Public",
			"requires_supplier_login_for_documents": 0,
			"requires_invitation": 0,
			"allows_public_notice": 1,
			"allows_public_document_download": 0,
			"eligibility_service_required": 0,
		}
	).insert(ignore_permissions=True)


def _advance_tm2_for_publish(tender_code: str, tm2_name: str) -> None:
	"""Doc 9 §9.4–9.5 — readiness run, submit for publication review, approve (Administrator seed)."""
	_ensure_tm2_access_rule(tm2_name)
	spec_r = spec_for_action("TND2_RUN_READINESS")
	spec_sub = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
	spec_ap = spec_for_action("TND2_APPROVE_PUBLICATION")
	if not spec_r or not spec_sub or not spec_ap:
		frappe.throw("PUB-1100: missing TM2 publication action specs.", exc=frappe.ValidationError)
	rout = run_publication_readiness(
		"Administrator",
		tender_code,
		context={"granted_permissions": [spec_r.required_permission]},
	)
	if not rout.get("ok"):
		frappe.throw(f"PUB-1100: run_publication_readiness failed: {rout}", exc=frappe.ValidationError)
	sout = submit_tender_for_publication_review(
		"Administrator",
		tender_code,
		context={"granted_permissions": [spec_sub.required_permission]},
	)
	if not sout.get("ok"):
		frappe.throw(f"PUB-1100: submit_tender_for_publication_review failed: {sout}", exc=frappe.ValidationError)
	aout = approve_tender_publication(
		"Administrator",
		tender_code,
		context={
			"granted_permissions": [spec_ap.required_permission],
			"sod_delegated_override_reason": "PUB-1100 seed — delegated publication approval.",
		},
	)
	if not aout.get("ok"):
		frappe.throw(f"PUB-1100: approve_tender_publication failed: {aout}", exc=frappe.ValidationError)


def _ensure_tm2_publication_approved(tm2_name: str, tender_code: str) -> None:
	if (frappe.db.get_value("TM2 Tender", tm2_name, "status") or "").strip() == "Approved for Publication":
		return
	_advance_tm2_for_publish(tender_code, tm2_name)


def _publish_tender_seed(tender_code: str) -> None:
	spec = spec_for_action("TND2_PUBLISH")
	if spec is None:
		frappe.throw("PUB-1100: TND2_PUBLISH action spec missing.", exc=frappe.ValidationError)
	PublicationTransactionService.publishTender(
		tender_code,
		actor="Administrator",
		context={"granted_permissions": [spec.required_permission]},
	)


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
		structured_text="PUB-1100 seed works requirement.",
		requirement_status="Complete",
		attachment_required=False,
		attachment_status="Not Required",
		ignore_publication_lock=True,
	)
	boq = StdInstanceBoqService.create_boq_for_instance(
		instance_name,
		currency="KES",
		boq_definition_code="PUB-1100-BOQ",
		ignore_boq_publication_lock=True,
	)
	boq = StdInstanceBoqService.add_bill(
		boq.name,
		"1",
		"General Works",
		"Normal",
		ignore_boq_publication_lock=True,
	)
	bill_code = (boq.boq_bills or [])[0].bill_instance_code
	StdInstanceBoqService.add_item(
		boq.name,
		bill_code,
		"1.1",
		"Preliminaries",
		"Item",
		1,
		item_type="Normal",
		supplier_input_mode="Rate Only",
		ignore_boq_publication_lock=True,
	)


def _advance_instance_to_ready_for_publication(instance_code: str) -> None:
	max_steps = 8
	for _ in range(max_steps):
		st = (frappe.db.get_value("Tender STD Instance", instance_code, "instance_status") or "").strip()
		if st == "Ready for Publication":
			return
		if st == "Draft":
			StdInstanceStateService.apply_transition(instance_code, "In Configuration", ignore_permissions=True)
			continue
		if st == "Validation Blocked":
			StdInstanceStateService.apply_transition(instance_code, "In Configuration", ignore_permissions=True)
			continue
		if st == "In Configuration":
			StdInstanceStateService.apply_transition(
				instance_code, "Ready for Publication", ignore_permissions=True
			)
			continue
		frappe.throw(
			f"PUB-1100: cannot reach Ready for Publication from instance status {st or 'unknown'}",
			exc=frappe.ValidationError,
		)
	frappe.throw("PUB-1100: instance state loop did not reach Ready for Publication.", exc=frappe.ValidationError)


def _generate_and_publish_named(
	instance_name: str,
	codes: dict[str, str],
	*,
	with_bundle: bool,
) -> dict[str, str]:
	out: dict[str, str] = {}
	if with_bundle:
		d = StdInstanceGeneratedOutputService.generate_bundle(
			instance_name,
			ignore_generated_output_lock=True,
			output_doc_name=codes["output_bundle"],
		)
		d = StdInstanceGeneratedOutputService.publish_output(d.name)
		out["Bundle"] = d.name

	for output_type, fn, key in (
		("DSM", StdInstanceGeneratedOutputService.generate_dsm, "output_dsm"),
		("DOM", StdInstanceGeneratedOutputService.generate_dom, "output_dom"),
		("DEM", StdInstanceGeneratedOutputService.generate_dem, "output_dem"),
		("DCM", StdInstanceGeneratedOutputService.generate_dcm, "output_dcm"),
	):
		d = fn(
			instance_name,
			ignore_generated_output_lock=True,
			output_doc_name=codes[key],
		)
		d = StdInstanceGeneratedOutputService.publish_output(d.name)
		out[output_type] = d.name
	return out


def _ensure_tm2_std_instance(tm2_name: str, tender_code: str) -> Any:
	current = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2_name)
	if current:
		return current
	ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
	spec_b = spec_for_action("TND2_BIND_STD")
	if spec_b is None:
		frappe.throw("PUB-1100: TND2_BIND_STD action spec missing.", exc=frappe.ValidationError)
	out = bind_tender_std_instance(
		"Administrator",
		tender_code,
		ver,
		prof,
		context={"granted_permissions": [spec_b.required_permission]},
	)
	if not out.get("ok"):
		frappe.throw(f"PUB-1100: bind_tender_std_instance failed: {out}", exc=frappe.ValidationError)
	si = str(out.get("tender_std_instance") or "").strip()
	if not si:
		frappe.throw("PUB-1100: bind_tender_std_instance returned no instance.", exc=frappe.ValidationError)
	return frappe.get_doc("Tender STD Instance", si)


def _build_core_instance(
	tm2_name: str,
	tender_code: str,
	codes: dict[str, str],
	*,
	with_bundle: bool,
	apply_stale_dem: bool,
) -> tuple[Any, dict[str, str]]:
	inst = _ensure_tm2_std_instance(tm2_name, tender_code)
	inst = frappe.get_doc("Tender STD Instance", inst.name)
	if (inst.applicability_profile_code or "").strip() != WORKS_PROFILE_CODE:
		inst.applicability_profile_code = WORKS_PROFILE_CODE
		inst.save(ignore_permissions=True)

	_seed_minimum_inputs(inst.name)
	outputs = _generate_and_publish_named(inst.name, codes, with_bundle=with_bundle)
	if apply_stale_dem:
		StdInstanceGeneratedOutputService.mark_output_stale(
			inst.name,
			output_type="DEM",
			ignore_generated_output_immutability=True,
		)
	return inst, outputs


def _summarize(
	tm2_name: str,
	tender_code: str,
	codes: dict[str, str],
	variant: str,
	std_instance_code: str | None,
	outputs: dict[str, str] | None,
) -> dict[str, Any]:
	clear_publication_readiness_cache()
	pub = PublicationReadinessService.runReadiness(tender_code, actor="Administrator")
	fc = [str((f.get("code") or "").strip()) for f in (pub.get("findings") or []) if (f.get("code") or "").strip()]
	dec = _latest_approval_decision_row(tender_code)
	return {
		"ok": True,
		"variant": variant,
		"tender_reference": codes["tender_reference"],
		"tender_name": tm2_name,
		"tender_code": tender_code,
		"std_instance_code": std_instance_code,
		"release_code": codes["release_code"],
		"procurement_package_code": codes["procurement_package_code"],
		"generated_outputs": outputs or {},
		"publication_readiness_status": (pub.get("status") or "").strip(),
		"publication_finding_codes": sorted(set(fc)),
		"std_readiness_status": (frappe.db.get_value("Tender STD Instance", std_instance_code, "readiness_status") or "").strip()
		if std_instance_code
		else "",
		"tender_status": (frappe.db.get_value("TM2 Tender", tm2_name, "status") or "").strip(),
		"approval_decision": ((dec.decision or "").strip() if dec else ""),
	}


def run(variant: str = "ready") -> dict[str, Any]:
	"""Load or refresh a PUB-1100 fixture variant (idempotent when rows already match)."""
	frappe.set_user("Administrator")
	v = (variant or "").strip().lower()
	if v not in VALID_VARIANTS:
		frappe.throw(
			f"Unknown PUB-1100 variant {variant!r}; expected one of {sorted(VALID_VARIANTS)}",
			exc=frappe.ValidationError,
		)

	codes = fixture_codes(v)
	seed_std_template_governance_for_existing_works_poc(force_mode="active")
	_ensure_package_exists()

	tm2_name, tender_code = _ensure_tm2_fixture(codes)
	std_instance_code: str | None = None
	outputs: dict[str, str] | None = None

	if v == "no_std_binding":
		return _summarize(tm2_name, tender_code, codes, v, None, None)

	# Idempotent short paths for approval / publication lifecycle
	if v == "published" and _is_tender_published(tender_code):
		cur = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2_name)
		std_instance_code = cur.name if cur else None
		return _summarize(tm2_name, tender_code, codes, v, std_instance_code, None)

	if v in {"approved", "published"} and _is_approved_for_publication(tender_code):
		std_si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2_name)
		std_instance_code = std_si.name if std_si else None
		_ensure_tm2_publication_approved(tm2_name, tender_code)
		if v == "published" and not _is_tender_published(tender_code):
			_publish_tender_seed(tender_code)
		return _summarize(tm2_name, tender_code, codes, v, std_instance_code, None)

	si_name = frappe.db.get_value("Tender STD Instance", {"tm2_tender": tm2_name}, "name")
	if si_name:
		std_instance_code = si_name
		inst = frappe.get_doc("Tender STD Instance", si_name)
		if v in {"ready", "approved", "published"}:
			if (inst.instance_status or "").strip() not in (
				"Ready for Publication",
				"Locked for Approval",
				"Published Locked",
			):
				_advance_instance_to_ready_for_publication(std_instance_code)
		outputs = {}
		for ot in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
			field = {
				"Bundle": "current_bundle_output_code",
				"DSM": "current_dsm_output_code",
				"DOM": "current_dom_output_code",
				"DEM": "current_dem_output_code",
				"DCM": "current_dcm_output_code",
			}[ot]
			cn = (frappe.db.get_value("Tender STD Instance", std_instance_code, field) or "").strip()
			if cn:
				outputs[ot] = cn
		if v in {"approved", "published"}:
			if not _is_approved_for_publication(tender_code):
				ConfigurationSnapshotService.createConfigurationSnapshot(tender_code, actor="Administrator")
				ApprovalDecisionService.approveForPublication(
					tender_code, {"decision_note": "PUB-1100 seed"}, actor="Administrator"
				)
			_ensure_tm2_publication_approved(tm2_name, tender_code)
			if v == "published" and not _is_tender_published(tender_code):
				_publish_tender_seed(tender_code)
			return _summarize(tm2_name, tender_code, codes, v, std_instance_code, outputs)

		if v in {"ready", "no_bundle", "stale_dem"}:
			return _summarize(tm2_name, tender_code, codes, v, std_instance_code, outputs)

	# First-time construction
	if v == "no_bundle":
		inst, outputs = _build_core_instance(tm2_name, tender_code, codes, with_bundle=False, apply_stale_dem=False)
		std_instance_code = inst.name
	elif v == "stale_dem":
		inst, outputs = _build_core_instance(tm2_name, tender_code, codes, with_bundle=True, apply_stale_dem=True)
		std_instance_code = inst.name
	else:
		inst, outputs = _build_core_instance(tm2_name, tender_code, codes, with_bundle=True, apply_stale_dem=False)
		std_instance_code = inst.name

	if v in {"ready", "approved", "published"}:
		if StdInstanceReadinessService.evaluate(std_instance_code, persist=False)["status"] != "Ready":
			frappe.throw(
				"PUB-1100: STD instance readiness is not Ready for a variant that requires it.",
				exc=frappe.ValidationError,
			)
		_advance_instance_to_ready_for_publication(std_instance_code)

	if v in {"approved", "published"}:
		ConfigurationSnapshotService.createConfigurationSnapshot(tender_code, actor="Administrator")
		ApprovalDecisionService.approveForPublication(
			tender_code, {"decision_note": "PUB-1100 seed"}, actor="Administrator"
		)
		_ensure_tm2_publication_approved(tm2_name, tender_code)
	if v == "published":
		_publish_tender_seed(tender_code)

	return _summarize(tm2_name, tender_code, codes, v, std_instance_code, outputs)


def run_fixture(variant: str = "ready") -> dict[str, Any]:
	"""``bench execute`` entrypoint (kwargs ``variant``)."""
	return run(variant=variant)
