# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0700 — ``EvidencePackageService``.

Assemble, validate, and export audit-grade publication evidence (pack §15).

**Import note:** do not import ``ConfigurationSnapshotService`` here — it loads
``PublicationReadinessService``, which imports this module (circular). Use the same SQL
shape as ``getCurrentConfigurationSnapshot`` inline.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_EVIDENCE_PACKAGE_ASSEMBLED,
	AUDIT_TENDER_PUBLICATION_EVIDENCE_PACKAGE_EXPORTED,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance
from kentender_procurement.tender_management.std_instance.parameter import OUTPUT_KEY_TO_PARENT_FIELD
from kentender_procurement.tender_management.std_instance.readiness import VALID_CURRENT_OUTPUT_STATUSES

# Match ``approval_decision.DECISION_APPROVED`` without importing that module (circular via publication_readiness).
_DECISION_APPROVED_FOR_PUBLICATION = "Approved for Publication"

Phase = Literal["readiness", "publication", "export"]

EXPORT_FORMAT_JSON_MANIFEST = "JSON_MANIFEST"
EXPORT_FORMAT_AUDIT_LOG = "AUDIT_LOG_EXPORT"
EXPORT_FORMAT_PDF_BUNDLE = "PDF_BUNDLE"
EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE = "GENERATED_MODEL_JSON_ARCHIVE"
EXPORT_FORMAT_ATTACHMENTS_ARCHIVE = "DOCUMENT_ATTACHMENTS_ARCHIVE"


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _sha256_hex(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(obj: Any) -> str:
	return _sha256_hex(json.dumps(obj, sort_keys=True, default=str, separators=(",", ":")))


def _planning_release_ok(tender: Document) -> bool:
	if _strip(tender.get("source_package_code")):
		return True
	pkg = _strip(tender.get("procurement_package"))
	if not pkg or not frappe.db.exists("Procurement Package", pkg):
		return False
	st = _strip(frappe.db.get_value("Procurement Package", pkg, "status"))
	return st == "Released to Tender"


def _procurement_plan_or_package_ref_ok(tender: Document) -> bool:
	return bool(
		_strip(tender.get("procurement_plan"))
		or _strip(tender.get("procurement_package"))
		or _strip(tender.get("source_package_code")),
	)


def _is_works_tender(tender: Document) -> bool:
	return _strip(tender.get("procurement_category")).upper() == "WORKS"


def _emit_evidence_export_audit(
	tc: str,
	act: str,
	fmt: str,
	*,
	partial: bool,
	manifest: dict[str, Any],
) -> None:
	si_name = _strip(str((manifest.get("std_instance") or {}).get("name") or "")) or None
	emit_publication_audit_event(
		event_type=AUDIT_TENDER_PUBLICATION_EVIDENCE_PACKAGE_EXPORTED,
		tender_code=tc,
		action="evidence_package_exported",
		performed_by=act,
		instance_code=si_name,
		details={"format": fmt, "partial": partial},
	)


def _get_current_configuration_summary(tender_code: str) -> dict[str, Any] | None:
	tc = _strip(tender_code)
	tm2 = resolve_tm2_tender_document(tc)
	if not tm2:
		return None
	si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
	if not si:
		return None
	row = frappe.db.sql(
		"""
		select name
		from `tabTender STD Instance Snapshot`
		where tender_std_instance = %s
			and snapshot_type = 'Configuration'
			and snapshot_status = 'Final'
		order by created_at desc, modified desc
		limit 1
		""",
		(si.name,),
		as_dict=True,
	)
	if not row:
		return None
	doc = frappe.get_doc("Tender STD Instance Snapshot", row[0].name)
	return {
		"snapshot_code": doc.name,
		"tm2_tender": tm2.name,
		"tender_std_instance": doc.tender_std_instance,
		"snapshot_type": doc.snapshot_type,
		"snapshot_status": doc.snapshot_status,
		"ref_bundle_output": doc.ref_bundle_output,
		"ref_dsm_output": doc.ref_dsm_output,
		"ref_dom_output": doc.ref_dom_output,
		"ref_dem_output": doc.ref_dem_output,
		"ref_dcm_output": doc.ref_dcm_output,
		"parameter_values_hash": doc.parameter_values_hash,
		"works_requirements_hash": doc.works_requirements_hash,
		"attachments_hash": doc.attachments_hash,
		"boq_hash": doc.boq_hash,
		"complete_instance_hash": doc.complete_instance_hash,
		"source_template_version_code": doc.source_template_version_code,
		"readiness_summary_json": _strip(getattr(doc, "readiness_summary_json", None) or ""),
	}


def _latest_approved_decision_doc(tender_code: str, *, tm2_name: str | None = None) -> Document | None:
	tc = _strip(tender_code)
	or_filters: list[dict[str, Any]] = []
	if tm2_name:
		or_filters.append({"tm2_tender": tm2_name})
	elif tc:
		tm2r = resolve_tm2_tender_document(tc)
		if tm2r:
			or_filters.append({"tm2_tender": tm2r.name})
	if not or_filters:
		return None
	rows = frappe.get_all(
		"Tender Publication Approval Decision",
		or_filters=or_filters,
		pluck="name",
		order_by="decided_at desc",
		limit=20,
	)
	for name in rows:
		doc = frappe.get_doc("Tender Publication Approval Decision", name)
		if _strip(doc.decision) == _DECISION_APPROVED_FOR_PUBLICATION:
			return doc
	return None


def _latest_final_tender_publication_snapshot_name(
	tender_code: str,
	*,
	tm2_name: str | None = None,
) -> str | None:
	tc = _strip(tender_code)
	or_filters: list[dict[str, Any]] = []
	if tm2_name:
		or_filters.append({"tm2_tender": tm2_name})
	elif tc:
		tm2r = resolve_tm2_tender_document(tc)
		if tm2r:
			or_filters.append({"tm2_tender": tm2r.name})
	if not or_filters:
		return None
	names = frappe.get_all(
		"Tender Publication Snapshot",
		filters={"snapshot_status": "Final"},
		or_filters=or_filters,
		pluck="name",
		order_by="created_at desc, modified desc",
		limit=1,
	)
	return names[0] if names else None


def _audit_event_count_for_tender(tender_code: str, *, tm2_name: str | None = None) -> int:
	if tm2_name:
		return int(
			frappe.db.count(
				"Audit Event",
				{"document_type": "TM2 Tender", "document_name": tm2_name},
			)
		)
	tc = _strip(tender_code)
	tm2r = resolve_tm2_tender_document(tc)
	if not tm2r:
		return 0
	return int(
		frappe.db.count(
			"Audit Event",
			{"document_type": "TM2 Tender", "document_name": tm2r.name},
		)
	)


def _output_row(code: str) -> Document | None:
	if not code or not frappe.db.exists("Tender STD Generated Output", code):
		return None
	return frappe.get_doc("Tender STD Generated Output", code)


def _has_scc_evidence(inst: Document) -> bool:
	for row in inst.parameter_values or []:
		pc = _strip(row.parameter_code)
		if pc.lower().startswith("scc."):
			if _strip(row.value) and (row.value_status or "").strip() in ("Provided", "Invalid"):
				return True
	for _ot, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
		out_name = _strip(inst.get(field))
		out = _output_row(out_name)
		if out and _strip(out.output_status) in VALID_CURRENT_OUTPUT_STATUSES and _strip(out.output_hash):
			return True
	return False


def _lineage_ok(tender: Document) -> bool:
	return bool(
		_strip(tender.get("source_package_code"))
		or _strip(tender.get("source_package_hash"))
		or _strip(tender.get("package_hash"))
		or _strip(tender.get("source_package_snapshot_json")),
	)


def _collect_validation(
	tc: str,
	*,
	phase: Phase,
	require_tender_publication_snapshot: bool,
) -> dict[str, Any]:
	missing: list[str] = []
	raw = _strip(tc)
	if not raw:
		return {
			"ok": False,
			"missing": ["tender_record"],
			"message": _("TM2 Tender not found."),
			"manifest": {},
			"fingerprint": {},
		}
	tm2 = resolve_tm2_tender_document(raw)
	if not tm2:
		return {
			"ok": False,
			"missing": ["tender_record"],
			"message": _("TM2 Tender not found."),
			"manifest": {},
			"fingerprint": {},
		}
	canonical = canonical_tm2_tender_code(tm2)
	tender: Document = tm2
	si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
	inst = frappe.get_doc("Tender STD Instance", si.name) if si else None

	manifest: dict[str, Any] = {
		"tender_code": canonical,
		"tm2_tender": tm2.name,
		"tender_title": _strip(tender.tender_title),
		"tender_reference": _strip(tender.get("tender_reference")),
		"procurement_category": _strip(tender.procurement_category),
		"planning": {
			"source_package_code": _strip(tender.get("source_package_code")),
			"procurement_plan": _strip(tender.get("procurement_plan")),
			"procurement_package": _strip(tender.get("procurement_package")),
			"source_package_hash": _strip(tender.get("source_package_hash")),
			"package_hash": _strip(tender.get("package_hash")),
			"has_source_package_snapshot_json": bool(_strip(tender.get("source_package_snapshot_json"))),
		},
	}

	# Planning / release / lineage are enforced by ``PublicationReadinessService`` (PUB-0110).
	# Re-checking here would duplicate findings and disturb denial-title priority in PUB-0400.
	if phase != "readiness":
		if not _procurement_plan_or_package_ref_ok(tender):
			missing.append("procurement_plan_or_package_reference")
		if not _planning_release_ok(tender):
			missing.append("planning_to_tender_release_record")

	if not (_strip(tender.get("std_template")) or _strip(tender.get("template_code"))):
		missing.append("std_template")

	if not si or not inst:
		missing.append("std_instance")
		fp = _fingerprint(
			manifest,
			missing,
			inst,
			tender,
			phase,
			None,
			None,
			None,
			require_tps=require_tender_publication_snapshot,
		)
		return {
			"ok": not missing,
			"missing": missing,
			"message": _("; ").join(missing) if missing else "",
			"manifest": manifest,
			"fingerprint": fp,
		}

	manifest["std_instance"] = {
		"name": inst.name,
		"template_version_code": _strip(inst.template_version_code),
		"applicability_profile_code": _strip(inst.applicability_profile_code),
	}

	if not _strip(inst.template_version_code):
		missing.append("std_template_version")
	if not _strip(inst.applicability_profile_code):
		missing.append("applicability_profile")

	tds_ok = any(
		_strip(row.value) and (row.value_status or "").strip() == "Provided"
		for row in (inst.parameter_values or [])
	)
	if not tds_ok:
		missing.append("tds_values")

	if not _has_scc_evidence(inst):
		missing.append("scc_values")

	if _is_works_tender(tender):
		boq = get_boq_for_instance(inst.name)
		if not boq:
			missing.append("boq")
		else:
			manifest["boq"] = {"name": boq.name, "status": _strip(boq.status)}
		req_rows = [r for r in (inst.works_requirements or []) if _strip(getattr(r, "requirement_code", None))]
		if not req_rows:
			missing.append("works_requirements")
		else:
			manifest["works_requirements"] = {"row_count": len(req_rows)}
		manifest["drawings_register"] = {"row_count": len(inst.drawing_register or [])}
	else:
		manifest["boq"] = None
		manifest["works_requirements"] = "not_applicable"
		manifest["drawings_register"] = "not_applicable"

	outputs_manifest: dict[str, Any] = {}
	if phase == "readiness":
		# Output currency is covered by ``StdInstanceReadinessService`` + traceability in PUB-0110.
		for otype, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
			code = _strip(inst.get(field))
			row = _output_row(code)
			outputs_manifest[otype] = {
				"code": code or None,
				"output_status": _strip(row.output_status) if row else None,
				"has_hash": bool(_strip(row.output_hash)) if row else False,
			}
	else:
		for otype, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
			code = _strip(inst.get(field))
			row = _output_row(code)
			if not row:
				missing.append(f"output_{otype.lower()}")
				outputs_manifest[otype] = {"code": code or None, "present": False}
				continue
			st = _strip(row.output_status)
			oh = _strip(row.output_hash)
			outputs_manifest[otype] = {
				"code": code,
				"output_status": st,
				"output_hash": oh,
			}
			if st not in VALID_CURRENT_OUTPUT_STATUSES or st != "Published":
				missing.append(f"output_{otype.lower()}_not_published")
			if not oh:
				missing.append(f"output_{otype.lower()}_hash_missing")

	manifest["generated_outputs"] = outputs_manifest

	if phase != "readiness":
		if not _lineage_ok(tender):
			missing.append("source_document_lineage")

	cfg: dict[str, Any] | None = None
	dec: Document | None = None
	tps_name: str | None = None

	if phase in ("publication", "export"):
		cfg = _get_current_configuration_summary(canonical)
		if not cfg:
			missing.append("configuration_snapshot")
		else:
			manifest["configuration_snapshot"] = cfg
			for hkey in ("parameter_values_hash", "complete_instance_hash"):
				if not _strip(str(cfg.get(hkey) or "")):
					missing.append(f"configuration_snapshot_{hkey}")
			if _is_works_tender(tender):
				for hkey in ("boq_hash", "works_requirements_hash"):
					if not _strip(str(cfg.get(hkey) or "")):
						missing.append(f"configuration_snapshot_{hkey}")

		dec = _latest_approved_decision_doc(canonical, tm2_name=tm2.name)
		if not dec:
			missing.append("approval_decision")
		else:
			manifest["approval_decision"] = {"name": dec.name, "configuration_snapshot": _strip(dec.configuration_snapshot)}
			if cfg and _strip(dec.configuration_snapshot) != _strip(str(cfg.get("snapshot_code") or "")):
				missing.append("approval_decision_configuration_mismatch")

		if cfg:
			# Readiness results: require non-empty summary captured on configuration snapshot.
			if not _strip(str(cfg.get("readiness_summary_json") or "")):
				missing.append("readiness_results_on_configuration_snapshot")

		aud = _audit_event_count_for_tender(canonical, tm2_name=tm2.name)
		manifest["audit_events"] = {"tm2_tender_audit_rows": aud, "procurement_tender_rows": 0}
		if aud < 1:
			missing.append("audit_events")

	if require_tender_publication_snapshot:
		tps_name = _latest_final_tender_publication_snapshot_name(canonical, tm2_name=tm2.name)
		if not tps_name:
			missing.append("publication_snapshot")
		else:
			manifest["publication_snapshot"] = {"name": tps_name}

	fp = _fingerprint(manifest, missing, inst, tender, phase, cfg, dec, tps_name, require_tps=require_tender_publication_snapshot)
	msg = _("Missing required evidence: {0}").format(", ".join(missing)) if missing else ""
	return {
		"ok": not missing,
		"missing": missing,
		"message": msg,
		"manifest": manifest,
		"fingerprint": fp,
	}


def _fingerprint(
	manifest: dict[str, Any],
	missing: list[str],
	inst: Document | None,
	tender: Document,
	phase: Phase,
	cfg: dict[str, Any] | None,
	dec: Document | None,
	tps_name: str | None,
	*,
	require_tps: bool,
) -> dict[str, Any]:
	"""Stable subset for ``EVIDENCE|…`` binding hash."""
	out: dict[str, Any] = {
		"phase": phase,
		"tender_code": manifest.get("tender_code"),
		"planning_ok": _planning_release_ok(tender) and _procurement_plan_or_package_ref_ok(tender),
		"category": _strip(tender.get("procurement_category")),
	}
	if inst:
		out["instance"] = inst.name
		out["template_version_code"] = _strip(inst.template_version_code)
		out["applicability_profile_code"] = _strip(inst.applicability_profile_code)
		oh = {}
		for otype, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
			code = _strip(inst.get(field))
			row = _output_row(code)
			oh[otype] = _strip(row.output_hash) if row else None
		out["output_hashes"] = oh
	if cfg:
		out["configuration_snapshot"] = _strip(str(cfg.get("snapshot_code") or ""))
		out["parameter_values_hash"] = _strip(str(cfg.get("parameter_values_hash") or ""))
		out["complete_instance_hash"] = _strip(str(cfg.get("complete_instance_hash") or ""))
	if dec:
		out["approval_decision"] = dec.name
	if require_tps:
		out["publication_snapshot"] = tps_name
	out["missing_keys"] = sorted(missing)
	return out


class EvidencePackageService:
	"""Audit-grade publication evidence (pack §15)."""

	@staticmethod
	def evidence_package_code_from_validation(tender_code: str, validation: dict[str, Any]) -> str:
		"""Stable code persisted on ``Tender Publication Snapshot.evidence_package_code``."""
		tc = _strip(tender_code)
		fp = validation.get("fingerprint") if isinstance(validation.get("fingerprint"), dict) else {}
		return "EVIDENCE|" + _sha256_json({"tender_code": tc, "fingerprint": fp})

	@staticmethod
	def validate_for_readiness_gate(procurement_tender: str) -> dict[str, Any]:
		"""PUB-0110 / PUB-0400 — evidence items available **before** tender publication snapshot exists."""
		tc = _strip(procurement_tender)
		return _collect_validation(tc, phase="readiness", require_tender_publication_snapshot=False)

	@staticmethod
	def validateEvidencePackage(
		procurement_tender: str,
		*,
		require_tender_publication_snapshot: bool | None = None,
	) -> dict[str, Any]:
		"""Full gate for publish / export (configuration snapshot, approval, published outputs, audits).

		When ``require_tender_publication_snapshot`` is ``None``, it is **required** iff the tender
		is **Published** or a Final ``Tender Publication Snapshot`` already exists.
		"""
		tc = _strip(procurement_tender)
		if require_tender_publication_snapshot is None:
			tm2 = resolve_tm2_tender_document(tc)
			if not tm2:
				require_tender_publication_snapshot = False
			else:
				canon = canonical_tm2_tender_code(tm2)
				st = _strip(frappe.db.get_value("TM2 Tender", tm2.name, "status") or "")
				has_tps = bool(_latest_final_tender_publication_snapshot_name(canon, tm2_name=tm2.name))
				require_tender_publication_snapshot = st == "Published" or has_tps
		return _collect_validation(
			tc,
			phase="publication",
			require_tender_publication_snapshot=bool(require_tender_publication_snapshot),
		)

	@staticmethod
	def assembleEvidencePackage(procurement_tender: str, actor_or_system: str | None = None) -> dict[str, Any]:
		"""Build manifest + fingerprint; validates publication phase first."""
		tc = _strip(procurement_tender)
		act = _strip(actor_or_system) or _strip(frappe.session.user) or "Administrator"
		val = EvidencePackageService.validateEvidencePackage(tc, require_tender_publication_snapshot=None)
		manifest = val.get("manifest") or {}
		canon = _strip(str(manifest.get("tender_code") or tc))
		code = EvidencePackageService.evidence_package_code_from_validation(canon, val)
		if val.get("ok"):
			si_name = _strip(str((manifest.get("std_instance") or {}).get("name") or "")) or None
			emit_publication_audit_event(
				event_type=AUDIT_TENDER_PUBLICATION_EVIDENCE_PACKAGE_ASSEMBLED,
				tender_code=canon,
				action="evidence_package_assembled",
				performed_by=act,
				instance_code=si_name,
				details={"evidence_package_code": code},
			)
		return {
			"ok": val.get("ok", False),
			"tender_code": canon,
			"actor": act,
			"evidence_package_code": code,
			"validation": val,
			"manifest": manifest,
		}

	@staticmethod
	def exportEvidencePackage(
		procurement_tender: str,
		export_format: str,
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Export a slice of the evidence package (pack §15 ``format`` values).

		Authorization: ``PublicationAuthorizationService`` (PUB-0800).
		"""
		from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
			PublicationAuthorizationService,
		)

		tc = _strip(procurement_tender)
		fmt = _strip(export_format)
		act = _strip(actor) or _strip(frappe.session.user) or "Administrator"
		tm2 = resolve_tm2_tender_document(tc)
		canon = canonical_tm2_tender_code(tm2) if tm2 else tc
		enforce_sec_authorization(
			action_code="EXPORT_EVIDENCE_PACKAGE",
			actor=act,
			object_type="TM2 Tender",
			object_code=canon,
			context={"object_exists": bool(tm2)},
			fallback_message="Not authorized to export evidence package.",
		)

		if act == "Guest":
			frappe.throw(_("Evidence export is not allowed for this user."), exc=frappe.ValidationError)
		PublicationAuthorizationService.assertCanExportPublicationEvidence(act)

		# Post-publish / snapshot export: require full evidence including publication snapshot when present.
		val = EvidencePackageService.validateEvidencePackage(tc, require_tender_publication_snapshot=None)
		if not val.get("ok"):
			frappe.throw(
				_("{0}").format(_strip(str(val.get("message") or _("Evidence package validation failed.")))),
				exc=frappe.ValidationError,
			)

		assembled = EvidencePackageService.assembleEvidencePackage(tc, actor_or_system=act)
		manifest = assembled.get("manifest") or {}
		audit_tc = _strip(str(manifest.get("tender_code") or canon))

		if fmt == EXPORT_FORMAT_JSON_MANIFEST:
			_emit_evidence_export_audit(audit_tc, act, fmt, partial=False, manifest=manifest)
			return {"ok": True, "format": fmt, "partial": False, "data": manifest}

		if fmt == EXPORT_FORMAT_AUDIT_LOG:
			if tm2:
				rows = frappe.get_all(
					"TM2 Tender Audit Event",
					filters={"tm2_tender": tm2.name},
					fields=[
						"name",
						"event_type",
						"actor",
						"timestamp",
						"event_payload",
						"publication_snapshot_code",
					],
					order_by="creation asc",
					limit=5000,
				)
			else:
				rows = []
			_emit_evidence_export_audit(audit_tc, act, fmt, partial=False, manifest=manifest)
			return {"ok": True, "format": fmt, "partial": False, "data": {"events": rows}}

		if fmt == EXPORT_FORMAT_GENERATED_MODEL_ARCHIVE:
			si_name = _strip(str((manifest.get("std_instance") or {}).get("name") or ""))
			if not si_name:
				return {"ok": False, "format": fmt, "partial": True, "message": _("No STD instance on manifest.")}
			inst = frappe.get_doc("Tender STD Instance", si_name)
			archive: dict[str, Any] = {}
			for otype, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
				code = _strip(inst.get(field))
				row = _output_row(code)
				if not row:
					archive[otype] = None
					continue
				cj: Any = row.content_json
				if isinstance(cj, str):
					cj = frappe.parse_json(cj) if (cj or "").strip() else {}
				archive[otype] = {
					"code": code,
					"output_status": row.output_status,
					"output_hash": row.output_hash,
					"content_json": cj if isinstance(cj, dict) else {},
				}
			_emit_evidence_export_audit(audit_tc, act, fmt, partial=False, manifest=manifest)
			return {"ok": True, "format": fmt, "partial": False, "data": archive}

		if fmt in (EXPORT_FORMAT_PDF_BUNDLE, EXPORT_FORMAT_ATTACHMENTS_ARCHIVE):
			_emit_evidence_export_audit(audit_tc, act, fmt, partial=True, manifest=manifest)
			return {
				"ok": True,
				"format": fmt,
				"partial": True,
				"message": _("Format is not yet implemented; reserved for PUB-0800 / storage integration."),
				"data": None,
			}

		frappe.throw(_("Unknown export format: {0}").format(fmt), exc=frappe.ValidationError)
