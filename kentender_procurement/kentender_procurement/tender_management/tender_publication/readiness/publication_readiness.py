# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0110 — ``PublicationReadinessService`` (tender-scope readiness gate).

Combines planning release, STD binding/instance, ``StdInstanceReadinessService``,
output trace validation, and evidence gate (via ``EvidencePackageService`` stub).

Cursor pack §6 / std engine §6. Status enum: Not Run, Incomplete, Blocked, Warning,
Ready, Invalidated (``Invalidated`` is not emitted by this service until PUB-0320).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.derived_models.common.source_trace import (
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
	PublicationAuthorizationService,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.readiness.readiness_finding import (
	publication_finding_from_code,
	publication_finding_from_std_blocker,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	PUBLICATION_READINESS_GATE_FAILED,
	is_critical_code,
	is_warning_code,
)
from kentender_procurement.tender_management.tender_publication.readiness.validator import (
	validate_publication_readiness_finding,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED,
	AUDIT_TENDER_PUBLICATION_READINESS_PASSED,
	AUDIT_TENDER_PUBLICATION_READINESS_RUN,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	VALID_CURRENT_OUTPUT_STATUSES,
	StdInstanceReadinessService,
)

# Last ``runReadiness`` result per canonical **TM2** ``tender_code`` (in-process cache).
_latest: dict[str, dict[str, Any]] = {}


def clear_publication_readiness_cache() -> None:
	"""Clear in-process cache (tests / idempotent seeds)."""
	_latest.clear()


def invalidate_readiness_for_tender(tender_code: str, *, actor: str | None = None) -> None:
	"""Mark cached publication readiness as **Invalidated** (PUB-0310 / PUB-0320 return paths)."""
	tc = _readiness_cache_key(tender_code)
	if not tc:
		return
	_latest[tc] = {
		"tender_code": tc,
		"status": "Invalidated",
		"findings": [],
		"actor": (actor or "").strip(),
	}


_OUTPUT_TYPE_TO_NOT_CURRENT: dict[str, str] = {
	"Bundle": "BUNDLE_NOT_CURRENT",
	"DSM": "DSM_NOT_CURRENT",
	"DOM": "DOM_NOT_CURRENT",
	"DEM": "DEM_NOT_CURRENT",
	"DCM": "DCM_NOT_CURRENT",
}


def _readiness_cache_key(raw: str) -> str:
	r = (raw or "").strip()
	if not r:
		return ""
	tm2 = resolve_tm2_tender_document(r)
	if tm2:
		return canonical_tm2_tender_code(tm2)
	return r


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
	by_code: dict[str, dict[str, Any]] = {}
	for row in findings:
		code = (row.get("code") or "").strip()
		if not code:
			continue
		if code not in by_code:
			by_code[code] = row
	return list(by_code.values())


def _aggregate_status(findings: list[dict[str, Any]]) -> str:
	if any(is_critical_code((f.get("code") or "")) for f in findings):
		return "Blocked"
	if any(is_warning_code((f.get("code") or "")) for f in findings):
		return "Warning"
	return "Ready"


def _planning_release_findings(tender: Document) -> list[dict[str, Any]]:
	"""Planning-to-tender release: snapshot code or released package (pack §6.1)."""
	if (tender.get("source_package_code") or "").strip():
		return []
	pkg = (tender.get("procurement_package") or "").strip()
	if not pkg:
		return [publication_finding_from_code("RELEASE_RECORD_MISSING")]
	if not frappe.db.exists("Procurement Package", pkg):
		return [publication_finding_from_code("RELEASE_RECORD_MISSING")]
	st = (frappe.db.get_value("Procurement Package", pkg, "status") or "").strip()
	if st != "Released to Tender":
		return [publication_finding_from_code("RELEASE_RECORD_MISSING")]
	return []


def _traceability_findings(inst: Document) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for output_type, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
		out_name = (inst.get(field) or "").strip()
		if not out_name or not frappe.db.exists("Tender STD Generated Output", out_name):
			continue
		row = frappe.get_doc("Tender STD Generated Output", out_name)
		st = (row.output_status or "").strip()
		if st not in VALID_CURRENT_OUTPUT_STATUSES:
			continue
		cj: Any = row.content_json
		if isinstance(cj, str):
			cj = frappe.parse_json(cj) if (cj or "").strip() else {}
		if not isinstance(cj, dict):
			cj = {}
		try:
			validate_derived_output_source_traces(output_type, cj)
		except frappe.ValidationError:
			out.append(
				publication_finding_from_code(
					"OUTPUT_TRACE_MISSING",
					message=_("Generated output {0} failed trace validation.").format(output_type),
				),
			)
	return out


def _std_instance_findings(instance_name: str, std_blockers: list[dict[str, str]]) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	stale_present = False
	stale_message: str | None = None
	for b in std_blockers:
		code = (b.get("code") or "").strip()
		if not code or code == "UNRESOLVED_BLOCKERS":
			continue
		if code == "STALE_OUTPUTS_PRESENT":
			stale_present = True
			stale_message = (b.get("message") or "").strip() or None
			continue
		try:
			findings.append(
				publication_finding_from_std_blocker(code, message=(b.get("message") or "").strip() or None),
			)
		except frappe.ValidationError:
			continue

	if stale_present:
		inst = frappe.get_doc("Tender STD Instance", instance_name)
		raw_flags = parse_outputs_stale_flags(inst)
		norm = {str(x).strip().lower() for x in raw_flags}
		by_lower = {k.lower(): k for k in OUTPUT_KEY_TO_PARENT_FIELD}
		added = False
		for fl in norm:
			canonical = by_lower.get(fl)
			if not canonical:
				continue
			pub = _OUTPUT_TYPE_TO_NOT_CURRENT.get(canonical)
			if pub:
				findings.append(publication_finding_from_code(pub))
				added = True
		if not added:
			findings.append(
				publication_finding_from_code(
					"DEM_NOT_CURRENT",
					message=stale_message
					or _("Stale generated outputs are present; regenerate affected models."),
				),
			)
	return findings


class PublicationReadinessService:
	"""Tender-level publication readiness (PUB-0110)."""

	@staticmethod
	def runReadiness(tender_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Evaluate readiness for **TM2 Tender** (document ``name``, ``tender_code``, or ``tender_reference``)."""
		raw = (tender_code or "").strip()
		if not raw:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		tc_key = canonical_tm2_tender_code(tm2)

		act_eval = (actor or "").strip() or (frappe.session.user or "")
		PublicationAuthorizationService.assertCanRunPublicationReadiness(act_eval)

		tender: Document = tm2
		findings: list[dict[str, Any]] = []

		findings.extend(_planning_release_findings(tender))

		si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
		if not si:
			findings.append(publication_finding_from_code("STD_BINDING_MISSING"))
		else:
			if not (si.template_version_code or "").strip() or not (si.applicability_profile_code or "").strip():
				findings.append(publication_finding_from_code("TEMPLATE_LINEAGE_INVALID"))
			ev = StdInstanceReadinessService.evaluate(si.name, persist=False, emit_audit=False)
			if (ev.get("status") or "").strip() != "Ready":
				findings.extend(_std_instance_findings(si.name, list(ev.get("blockers") or [])))
			# Traceability on current outputs (pack §6 — Output Traceability).
			findings.extend(_traceability_findings(si))

		evidence = EvidencePackageService.validate_for_readiness_gate(tc_key)
		if not bool(evidence.get("ok", False)):
			findings.append(
				publication_finding_from_code(
					"EVIDENCE_PACKAGE_FAILED",
					message=str(evidence.get("message") or evidence.get("reason") or "").strip()
					or None,
				),
			)

		findings = _dedupe_findings(findings)
		for row in findings:
			validate_publication_readiness_finding(row)

		status = _aggregate_status(findings)

		result: dict[str, Any] = {
			"tender_code": tc_key,
			"status": status,
			"findings": findings,
			"actor": (actor or "").strip(),
		}
		_latest[tc_key] = result

		si_log = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
		inst_for_audit = si_log.name if si_log else None
		st_out = (result.get("status") or "").strip()
		fcodes = [
			str((f.get("code") or "").strip())
			for f in (result.get("findings") or [])
			if (f.get("code") or "").strip()
		]
		if st_out == "Ready":
			etype = AUDIT_TENDER_PUBLICATION_READINESS_PASSED
		elif st_out == "Blocked":
			etype = AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED
		else:
			etype = AUDIT_TENDER_PUBLICATION_READINESS_RUN
		emit_publication_audit_event(
			event_type=etype,
			tender_code=tc_key,
			action="publication_readiness_evaluated",
			performed_by=act_eval,
			instance_code=inst_for_audit,
			details={"readiness_status": st_out, "finding_codes": fcodes},
		)
		return result

	@staticmethod
	def getLatestReadiness(tender_code: str) -> dict[str, Any]:
		"""Return last ``runReadiness`` result, or ``Not Run`` when none."""
		tc = _readiness_cache_key(tender_code)
		if tc in _latest:
			return dict(_latest[tc])
		return {"tender_code": tc or (tender_code or "").strip(), "status": "Not Run", "findings": [], "actor": ""}

	@staticmethod
	def assertReadyForApproval(tender_code: str) -> None:
		"""``frappe.throw`` unless latest evaluation is ``Ready`` (not ``Warning``)."""
		PublicationReadinessService._assert_ready(tender_code, _("approval"))

	@staticmethod
	def assertReadyForPublication(tender_code: str) -> None:
		"""``frappe.throw`` unless latest evaluation is ``Ready``."""
		PublicationReadinessService._assert_ready(tender_code, _("publication"))

	@staticmethod
	def _assert_ready(tender_code: str, label: str) -> None:
		res = PublicationReadinessService.runReadiness(tender_code, frappe.session.user)
		if (res.get("status") or "").strip() != "Ready":
			codes = ", ".join((f.get("code") or "") for f in (res.get("findings") or []) if f.get("code"))
			frappe.throw(
				_("Tender is not ready for {0} (status {1}). Findings: {2}").format(
					label,
					res.get("status"),
					codes or _("none"),
				),
				title=PUBLICATION_READINESS_GATE_FAILED,
				exc=frappe.ValidationError,
			)
