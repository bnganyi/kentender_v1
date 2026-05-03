# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 5 §18 validation checks (WH-010). Pure helpers over ``Procurement Tender`` rows + ``configuration_json``."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from frappe.model.document import Document

from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
	_child_rows_to_dicts,
	_detect_variant_code,
	_expected_form_codes,
	_load_forms_metadata,
	_load_sample_tender,
	_parse_cfg,
)

# Mirror doc 5 / ``works_tender_hardening`` seed expectations (code -> supplier, submission, carry_forward).
_WORKS_REQ_EXPECT: dict[str, tuple[int, int, int]] = {
	"WRK_SCOPE": (1, 1, 1),
	"WRK_SITE": (1, 0, 1),
	"WRK_SPEC": (1, 0, 1),
	"WRK_DRAWINGS": (1, 0, 1),
	"WRK_ESHS": (1, 1, 1),
	"WRK_PROGRAMME": (1, 1, 0),
	"WRK_PERSONNEL": (1, 1, 0),
	"WRK_EQUIPMENT": (1, 1, 0),
	"WRK_COMPLETION": (1, 0, 1),
	"WRK_DLP": (1, 0, 1),
}

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_LOW = "Low"
SEVERITY_INFO = "Info"

AREA_WORKS = "Works Requirements"
AREA_ATTACHMENTS = "Attachments"
AREA_BOQ = "BoQ"
AREA_LOTS = "Lots"
AREA_FORMS = "Forms"
AREA_DERIVED = "Derived Models"
AREA_AUDIT = "Audit"
AREA_LEGACY = "Legacy Lockout"
AREA_STD = "STD Binding"

HARDENING_STATUS_PASS = "Pass"
HARDENING_STATUS_WARNING = "Warning"
HARDENING_STATUS_BLOCKED = "Blocked"


def _f(
	code: str,
	severity: str,
	area: str,
	message: str,
	*,
	source_object: str = "",
	resolution_hint: str = "",
	blocks_transition: bool = False,
	blocking_for: str = "",
) -> dict[str, Any]:
	return {
		"finding_code": code,
		"severity": severity,
		"area": area,
		"message": message,
		"source_object": source_object,
		"resolution_hint": resolution_hint,
		"blocks_transition": bool(blocks_transition),
		"blocking_for": blocking_for or "",
	}


def _strip_text(val: Any) -> str:
	if val is None:
		return ""
	return str(val).strip()


def _truthy_cfg(cfg: dict[str, Any], key: str) -> bool:
	v = cfg.get(key)
	if v in (1, True, "1", "true", "True", "yes", "YES"):
		return True
	if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"):
		return True
	return False


def _status_for_findings(findings: list[dict[str, Any]]) -> str:
	if not findings:
		return HARDENING_STATUS_PASS
	if any(f.get("severity") == SEVERITY_CRITICAL for f in findings):
		return HARDENING_STATUS_BLOCKED
	if any(f.get("severity") != SEVERITY_INFO for f in findings):
		return HARDENING_STATUS_WARNING
	return HARDENING_STATUS_PASS


def _rows_by_component(doc: Document) -> dict[str, Any]:
	out: dict[str, Any] = {}
	for row in doc.get("works_requirements") or []:
		code = getattr(row, "component_code", None) or row.get("component_code")
		if code:
			out[str(code)] = row
	return out


def validate_works_requirements_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	cfg = _parse_cfg(tender_doc)
	by = _rows_by_component(tender_doc)

	def _row_text(code: str) -> str:
		r = by.get(code)
		if not r:
			return ""
		return _strip_text(getattr(r, "structured_text", None) if hasattr(r, "structured_text") else r.get("structured_text"))

	# WORKS-REQ-001 .. 004
	if not _row_text("WRK_SCOPE"):
		findings.append(
			_f(
				"WORKS-REQ-001",
				SEVERITY_CRITICAL,
				AREA_WORKS,
				"Scope of works (WRK_SCOPE) is missing or has empty structured text.",
				source_object="WRK_SCOPE",
				resolution_hint="Populate WRK_SCOPE structured text or run initialize_works_requirements.",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	if not _row_text("WRK_SITE"):
		findings.append(
			_f(
				"WORKS-REQ-002",
				SEVERITY_HIGH,
				AREA_WORKS,
				"Site information (WRK_SITE) is missing or has empty structured text.",
				source_object="WRK_SITE",
				resolution_hint="Populate WRK_SITE from tender works location and site context.",
			)
		)
	if not _row_text("WRK_SPEC"):
		findings.append(
			_f(
				"WORKS-REQ-003",
				SEVERITY_CRITICAL,
				AREA_WORKS,
				"Technical specification (WRK_SPEC) is missing or has empty structured text.",
				source_object="WRK_SPEC",
				resolution_hint="Populate WRK_SPEC structured text.",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	if not _row_text("WRK_ESHS"):
		findings.append(
			_f(
				"WORKS-REQ-004",
				SEVERITY_HIGH,
				AREA_WORKS,
				"ESHS / HSE (WRK_ESHS) is missing or has empty structured text.",
				source_object="WRK_ESHS",
				resolution_hint="Populate WRK_ESHS when ESHS requirements apply.",
			)
		)

	# WORKS-REQ-005
	rp = by.get("WRK_PROGRAMME")
	if not rp:
		findings.append(
			_f(
				"WORKS-REQ-005",
				SEVERITY_HIGH,
				AREA_WORKS,
				"Work programme component (WRK_PROGRAMME) is missing.",
				source_object="WRK_PROGRAMME",
				resolution_hint="Add WRK_PROGRAMME works requirement row.",
			)
		)
	else:
		sl = getattr(rp, "submission_linked", None) if hasattr(rp, "submission_linked") else rp.get("submission_linked")
		if not sl:
			findings.append(
				_f(
					"WORKS-REQ-005",
					SEVERITY_HIGH,
					AREA_WORKS,
					"Work programme (WRK_PROGRAMME) is not submission-linked.",
					source_object="WRK_PROGRAMME",
					resolution_hint="Mark WRK_PROGRAMME as submission-linked where required.",
				)
			)

	# WORKS-REQ-006 — expected carry-forward from seed when config implies downstream contract content
	need_cfwd = _truthy_cfg(cfg, "CONTRACT.DOWNSTREAM_CARRY_FORWARD_REQUIRED") or bool(
		_strip_text(cfg.get("TENDER.CONTRACT_DESCRIPTION"))
	)
	if need_cfwd:
		for code, (_, _, exp_cfwd) in _WORKS_REQ_EXPECT.items():
			if not exp_cfwd:
				continue
			row = by.get(code)
			if not row:
				continue
			cf = getattr(row, "contract_carry_forward", 0) if hasattr(row, "contract_carry_forward") else row.get("contract_carry_forward")
			if cf not in (1, True, "1"):
				findings.append(
					_f(
						"WORKS-REQ-006",
						SEVERITY_CRITICAL,
						AREA_WORKS,
						f"Component {code} must be flagged for contract carry-forward.",
						source_object=code,
						resolution_hint="Set contract carry-forward on components that flow into the executed contract.",
						blocks_transition=True,
						blocking_for="Contract",
					)
				)

	# WORKS-REQ-007 — supplier-facing classification vs seed expectation
	for code, (exp_sup, _, _) in _WORKS_REQ_EXPECT.items():
		row = by.get(code)
		if not row:
			continue
		sf = getattr(row, "supplier_facing", 0) if hasattr(row, "supplier_facing") else row.get("supplier_facing")
		if exp_sup and sf not in (1, True, "1"):
			findings.append(
				_f(
					"WORKS-REQ-007",
					SEVERITY_HIGH,
					AREA_WORKS,
					f"Component {code} should be supplier-facing but is not classified as such.",
					source_object=code,
					resolution_hint="Mark supplier-facing components for tender pack disclosure.",
				)
			)

	return findings


_ATTACHMENT_RULE_KEYWORDS = re.compile(
	r"\b(submission\s+requirement|opening\s+register|evaluation\s+criteria|contract\s+terms)\b",
	re.IGNORECASE,
)


def validate_section_attachments_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	rows = list(tender_doc.get("section_attachments") or [])

	def _drawing_ok() -> bool:
		for row in rows:
			at = getattr(row, "attachment_type", "") or row.get("attachment_type")
			cc = getattr(row, "component_code", "") or row.get("component_code")
			if str(at) == "Drawing" and str(cc) == "WRK_DRAWINGS":
				return True
		return False

	def _spec_ok() -> bool:
		for row in rows:
			at = getattr(row, "attachment_type", "") or row.get("attachment_type")
			cc = getattr(row, "component_code", "") or row.get("component_code")
			if str(at) == "Technical Specification" and str(cc) == "WRK_SPEC":
				return True
		return False

	if not _drawing_ok():
		findings.append(
			_f(
				"WORKS-ATT-001",
				SEVERITY_HIGH,
				AREA_ATTACHMENTS,
				"Required drawing attachment metadata is missing or not bound to WRK_DRAWINGS.",
				source_object="section_attachments",
				resolution_hint="Add Drawing rows with component_code WRK_DRAWINGS.",
			)
		)
	if not _spec_ok():
		findings.append(
			_f(
				"WORKS-ATT-002",
				SEVERITY_HIGH,
				AREA_ATTACHMENTS,
				"Required specification attachment metadata is missing or not bound to WRK_SPEC.",
				source_object="section_attachments",
				resolution_hint="Add Technical Specification rows with component_code WRK_SPEC.",
			)
		)

	att003_emitted = False
	for row in rows:
		ad = row.as_dict() if hasattr(row, "as_dict") else dict(row)
		if not _strip_text(ad.get("version")):
			findings.append(
				_f(
					"WORKS-ATT-004",
					SEVERITY_HIGH,
					AREA_ATTACHMENTS,
					"Attachment version is missing.",
					source_object=str(ad.get("attachment_code") or "attachment"),
					resolution_hint="Set a version label (e.g. V1) on each attachment row.",
				)
			)
		if (
			not att003_emitted
			and ad.get("supplier_facing") not in (1, True, "1")
			and not ad.get("internal_only")
			and str(ad.get("attachment_type")) in ("Drawing", "Technical Specification")
		):
			att003_emitted = True
			findings.append(
				_f(
					"WORKS-ATT-003",
					SEVERITY_HIGH,
					AREA_ATTACHMENTS,
					"Supplier-facing classification is missing for a required tender attachment.",
					source_object=str(ad.get("attachment_code") or ""),
					resolution_hint="Mark supplier_facing or internal_only consistently.",
				)
			)
		notes = _strip_text(ad.get("notes"))
		if notes and _ATTACHMENT_RULE_KEYWORDS.search(notes):
			findings.append(
				_f(
					"WORKS-ATT-005",
					SEVERITY_CRITICAL,
					AREA_ATTACHMENTS,
					"Attachment metadata appears to define submission, opening, evaluation, or contract rules in notes.",
					source_object=str(ad.get("attachment_code") or ""),
					resolution_hint="Do not encode procedural rules in attachment metadata; use STD configuration.",
					blocks_transition=True,
					blocking_for="Publication",
				)
			)

	return findings


def validate_works_boq_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	cfg = _parse_cfg(tender_doc)
	boq_required = _truthy_cfg(cfg, "WORKS.BOQ_REQUIRED")
	rows_raw = list(tender_doc.get("boq_items") or [])
	if not rows_raw:
		if boq_required:
			findings.append(
				_f(
					"WORKS-BOQ-001",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"No BoQ rows exist while WORKS.BOQ_REQUIRED is true.",
					source_object="boq_items",
					resolution_hint="Populate BoQ items or disable BoQ requirement in configuration.",
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		return findings

	rows = [r.as_dict() if hasattr(r, "as_dict") else dict(r) for r in rows_raw]
	bill_codes = [str(r.get("bill_code") or "").strip() for r in rows]
	if not any(bill_codes):
		findings.append(
			_f(
				"WORKS-BOQ-002",
				SEVERITY_CRITICAL,
				AREA_BOQ,
				"No bill_code values exist on BoQ rows.",
				source_object="boq_items",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	for r in rows:
		if not str(r.get("bill_code") or "").strip():
			findings.append(
				_f(
					"WORKS-BOQ-003",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"A BoQ item is missing bill_code.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		ft = str(r.get("formula_type") or "")
		cat = str(r.get("item_category") or "")
		is_measured_like = ft in ("Measured", "Daywork")
		if is_measured_like and cat != "GRAND_SUMMARY":
			for fld, label in (
				("item_number", "item number"),
				("description", "description"),
				("unit", "unit"),
			):
				if not _strip_text(r.get(fld)):
					findings.append(
						_f(
							"WORKS-BOQ-004",
							SEVERITY_CRITICAL,
							AREA_BOQ,
							f"Measured item missing {label}.",
							source_object=str(r.get("item_code") or ""),
							blocks_transition=True,
							blocking_for="Submission",
						)
					)
			qv = r.get("quantity")
			if qv is None or (isinstance(qv, str) and not str(qv).strip()):
				findings.append(
					_f(
						"WORKS-BOQ-004",
						SEVERITY_CRITICAL,
						AREA_BOQ,
						"Measured item missing quantity.",
						source_object=str(r.get("item_code") or ""),
						blocks_transition=True,
						blocking_for="Submission",
					)
				)
		qty = r.get("quantity")
		try:
			qf = float(qty) if qty not in (None, "") else None
		except (TypeError, ValueError):
			qf = None
			findings.append(
				_f(
					"WORKS-BOQ-005",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"BoQ quantity is non-numeric.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		if qf is not None and qf < 0:
			findings.append(
				_f(
					"WORKS-BOQ-005",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"BoQ quantity is negative.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)

		supplier_facing_row = r.get("pricing_required") in (1, True, "1") or r.get("is_priced_by_bidder") in (
			1,
			True,
			"1",
		)
		if is_measured_like and supplier_facing_row and r.get("quantity_locked") not in (1, True, "1"):
			findings.append(
				_f(
					"WORKS-BOQ-006",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"Supplier-facing measured item has quantity_locked = false.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		if r.get("allow_supplier_amount_edit") in (1, True, "1"):
			findings.append(
				_f(
					"WORKS-BOQ-007",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"Supplier amount edit is allowed; only rate posture should be supplier-editable.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		if ft == "Provisional Sum" and (
			r.get("supplier_rate_editable") in (1, True, "1")
			or r.get("allow_supplier_amount_edit") in (1, True, "1")
		):
			findings.append(
				_f(
					"WORKS-BOQ-008",
					SEVERITY_CRITICAL,
					AREA_BOQ,
					"Provisional sum item allows supplier rate or amount edit.",
					source_object=str(r.get("item_code") or ""),
					blocks_transition=True,
					blocking_for="Submission",
				)
			)
		if cat == "GRAND_SUMMARY" or ft == "Summary":
			if r.get("supplier_rate_editable") in (1, True, "1"):
				findings.append(
					_f(
						"WORKS-BOQ-009",
						SEVERITY_CRITICAL,
						AREA_BOQ,
						"Summary row allows supplier pricing.",
						source_object=str(r.get("item_code") or ""),
						blocks_transition=True,
						blocking_for="Submission",
					)
				)
		if not str(r.get("boq_version") or "").strip():
			findings.append(
				_f(
					"WORKS-BOQ-012",
					SEVERITY_HIGH,
					AREA_BOQ,
					"BoQ version is missing on a row.",
					source_object=str(r.get("item_code") or ""),
				)
			)

	cats = {str(r.get("item_category") or "") for r in rows}
	if _truthy_cfg(cfg, "WORKS.DAYWORKS_INCLUDED") and "DAYWORKS" not in cats:
		findings.append(
			_f(
				"WORKS-BOQ-010",
				SEVERITY_HIGH,
				AREA_BOQ,
				"Dayworks are configured but no DAYWORKS category rows exist.",
				source_object="boq_items",
			)
		)
	if _truthy_cfg(cfg, "WORKS.PROVISIONAL_SUMS_INCLUDED") and "PROVISIONAL_SUMS" not in cats:
		findings.append(
			_f(
				"WORKS-BOQ-011",
				SEVERITY_HIGH,
				AREA_BOQ,
				"Provisional sums are configured but no PROVISIONAL_SUMS category rows exist.",
				source_object="boq_items",
			)
		)

	return findings


def validate_lot_boq_linkage_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	multi = getattr(tender_doc, "og_lots_multiple_lots_enabled", None) in (1, True, "1")
	lots_raw = list(tender_doc.get("lots") or [])
	lots = [l.as_dict() if hasattr(l, "as_dict") else dict(l) for l in lots_raw]
	lot_codes = [str(l.get("lot_code") or "").strip() for l in lots if str(l.get("lot_code") or "").strip()]
	if multi and not lots:
		findings.append(
			_f(
				"WORKS-LOT-001",
				SEVERITY_CRITICAL,
				AREA_LOTS,
				"Multiple-lot tender has no lot rows.",
				source_object="lots",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	dup = [c for c, n in Counter(lot_codes).items() if n > 1]
	if dup:
		findings.append(
			_f(
				"WORKS-LOT-002",
				SEVERITY_CRITICAL,
				AREA_LOTS,
				f"Duplicate lot codes: {', '.join(sorted(set(dup)))}.",
				source_object="lots",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	lot_set = set(lot_codes)
	has_lot_registry = bool(lot_set)
	pkg_cost = getattr(tender_doc, "og_tender_estimated_cost", None)
	if multi and lots and pkg_cost not in (None, "", 0) and all(
		l.get("estimated_value") not in (None, "", 0) for l in lots
	):
		total = sum(float(l.get("estimated_value") or 0) for l in lots)
		if abs(total - float(pkg_cost)) > 0.01 * max(1.0, float(pkg_cost) or 1.0):
			# No accepted-variance field in schema — treat mismatch as High (doc §18.4).
			findings.append(
				_f(
					"WORKS-LOT-003",
					SEVERITY_HIGH,
					AREA_LOTS,
					"Lot estimated values do not sum to package estimated cost (no variance field to accept drift).",
					source_object="lots",
					resolution_hint="Align lot values with og_tender_estimated_cost or document variance when supported.",
				)
			)

	boq_rows = [b.as_dict() if hasattr(b, "as_dict") else dict(b) for b in (tender_doc.get("boq_items") or [])]
	if has_lot_registry:
		for b in boq_rows:
			lc = str(b.get("lot_code") or "").strip()
			if lc and lc not in lot_set:
				findings.append(
					_f(
						"WORKS-LOT-004",
						SEVERITY_CRITICAL,
						AREA_LOTS,
						f"BoQ row references unknown lot code {lc}.",
						source_object=str(b.get("item_code") or ""),
						blocks_transition=True,
						blocking_for="Submission",
					)
				)
	if multi and has_lot_registry:
		for b in boq_rows:
			ft = str(b.get("formula_type") or "")
			if ft == "Summary":
				continue
			if not str(b.get("lot_code") or "").strip():
				findings.append(
					_f(
						"WORKS-LOT-005",
						SEVERITY_HIGH,
						AREA_LOTS,
						"Lot-based tender has a non-summary BoQ row without lot_code.",
						source_object=str(b.get("item_code") or ""),
					)
				)
	if getattr(tender_doc, "procurement_package", None) and lots:
		for l in lots:
			if l.get("package_line") and not str(l.get("source_package_line_code") or "").strip():
				findings.append(
					_f(
						"WORKS-LOT-006",
						SEVERITY_HIGH,
						AREA_LOTS,
						"Lot is linked to a package line but source_package_line_code is missing.",
						source_object=str(l.get("lot_code") or ""),
					)
				)

	return findings


def validate_required_forms_hardening_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	if not getattr(tender_doc, "std_template", None):
		return findings

	try:
		template = engine.load_template(tender_doc.std_template)
	except Exception as exc:
		findings.append(
			_f(
				"WORKS-FORM-001",
				SEVERITY_CRITICAL,
				AREA_FORMS,
				f"Could not load STD template for required-forms validation: {exc}",
				source_object=str(tender_doc.std_template),
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
		return findings

	cfg = _parse_cfg(tender_doc)
	sample = _load_sample_tender(template)
	variant = _detect_variant_code(cfg, sample) if sample else None
	expected = set(_expected_form_codes(sample, variant)) if sample else set()
	rows = _child_rows_to_dicts(tender_doc.get("required_forms"))
	observed_active = {
		str(r.get("form_code") or "")
		for r in rows
		if r.get("form_code") and r.get("required") in (1, True, "1")
	}
	for code in sorted(expected - observed_active):
		findings.append(
			_f(
				"WORKS-FORM-001",
				SEVERITY_CRITICAL,
				AREA_FORMS,
				f"Required form {code} is missing after generation.",
				source_object=code,
				blocks_transition=True,
				blocking_for="Submission",
			)
		)

	for r in rows:
		fc = str(r.get("form_code") or "")
		st = str(r.get("stage") or "")
		scc = _strip_text(r.get("submission_component_code"))
		if st == "Bid Submission" and not scc:
			findings.append(
				_f(
					"WORKS-FORM-002",
					SEVERITY_HIGH,
					AREA_FORMS,
					f"Bid-stage form {fc} lacks submission_component_code.",
					source_object=fc,
					resolution_hint="Run link_required_forms_to_submission_components or set DSM reference.",
				)
			)

	mode = str(cfg.get("SECURITY.TENDER_SECURITY_MODE") or "")
	has_sec = "FORM_TENDER_SECURITY" in observed_active
	has_dec = "FORM_TENDER_SECURING_DECLARATION" in observed_active
	if mode == "TENDER_SECURITY" and has_dec and has_sec:
		findings.append(
			_f(
				"WORKS-FORM-003",
				SEVERITY_CRITICAL,
				AREA_FORMS,
				"Tender Security and Tender-Securing Declaration forms are both present when modes are mutually exclusive.",
				source_object="required_forms",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)
	if mode == "TENDER_SECURING_DECLARATION" and has_sec:
		findings.append(
			_f(
				"WORKS-FORM-003",
				SEVERITY_CRITICAL,
				AREA_FORMS,
				"Tender security form is active under tender-securing declaration mode.",
				source_object="FORM_TENDER_SECURITY",
				blocks_transition=True,
				blocking_for="Submission",
			)
		)

	# WORKS-FORM-004 — JV toggle vs JV information form when package defines it
	meta = _load_forms_metadata(template)
	jv_expected = (
		_truthy_cfg(cfg, "QUALIFICATION.JOINT_VENTURE_ALLOWED")
		or _truthy_cfg(cfg, "PARTICIPATION.JV_ALLOWED")
		or _truthy_cfg(cfg, "og_participation_jv_allowed")
	)
	jv_code = "FORM_JV_INFORMATION"
	if jv_expected and jv_code in meta and jv_code not in observed_active:
		findings.append(
			_f(
				"WORKS-FORM-004",
				SEVERITY_HIGH,
				AREA_FORMS,
				"JV participation is enabled but expected JV information form is absent.",
				source_object=jv_code,
			)
		)

	for r in rows:
		if not r.get("required"):
			continue
		if str(r.get("stage") or "") != "Bid Submission":
			continue
		fc = str(r.get("form_code") or "")
		fmeta = meta.get(fc, {})
		exp_pol = _strip_text(fmeta.get("evidence_policy"))
		if not exp_pol:
			continue
		pol = _strip_text(r.get("evidence_policy"))
		if not pol or pol.upper() in ("UNKNOWN", "UNCLASSIFIED", "NONE"):
			findings.append(
				_f(
					"WORKS-FORM-005",
					SEVERITY_HIGH,
					AREA_FORMS,
					f"Required bid form {fc} has missing or unclassified evidence policy.",
					source_object=fc,
				)
			)

	return findings


_MODEL_ORDER = ("Submission", "Opening", "Evaluation", "Contract Carry-Forward")
_MODEL_FINDING: dict[str, str] = {
	"Submission": "WORKS-MODEL-001",
	"Opening": "WORKS-MODEL-002",
	"Evaluation": "WORKS-MODEL-003",
	"Contract Carry-Forward": "WORKS-MODEL-004",
}


def validate_derived_model_readiness_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	rows = list(tender_doc.get("derived_model_readiness") or [])
	by_type: dict[str, Any] = {}
	for row in rows:
		mt = getattr(row, "model_type", None) or row.get("model_type")
		if mt:
			by_type[str(mt)] = row

	for mt in _MODEL_ORDER:
		fc = _MODEL_FINDING[mt]
		row = by_type.get(mt)
		if not row:
			findings.append(
				_f(
					fc,
					SEVERITY_HIGH,
					AREA_DERIVED,
					f"{mt} readiness row is missing.",
					source_object=mt,
					resolution_hint="Run initialize_derived_model_readiness.",
					blocks_transition=True,
					blocking_for="Publication",
				)
			)
			continue
		st = getattr(row, "status", None) or row.get("status")
		vs = getattr(row, "validation_status", None) or row.get("validation_status")
		if st in ("Missing", "Blocked") or vs == "Blocked":
			findings.append(
				_f(
					fc,
					SEVERITY_HIGH,
					AREA_DERIVED,
					f"{mt} readiness row is blocked or missing content.",
					source_object=getattr(row, "model_code", None) or row.get("model_code") or mt,
					blocks_transition=True,
					blocking_for="Publication",
				)
			)

	# WORKS-MODEL-005 — explicit readiness claim only (``og_dates_publication_date`` is
	# hydrated from ``DATES.PUBLICATION_DATE`` in sample config, so it must not imply claim).
	cfg = _parse_cfg(tender_doc)
	pub_claim = _truthy_cfg(cfg, "WORKS.PUBLICATION_READINESS_CLAIMED")
	if pub_claim:
		for row in rows:
			st = getattr(row, "status", None) or row.get("status")
			if st in ("Placeholder", "Missing", "Blocked"):
				findings.append(
					_f(
						"WORKS-MODEL-005",
						SEVERITY_CRITICAL,
						AREA_DERIVED,
						"Tender has a publication date set while derived models are not generated.",
						source_object=getattr(row, "model_code", None) or row.get("model_code") or "",
						blocks_transition=True,
						blocking_for="Publication",
					)
				)
				break

	return findings


def validate_audit_checks(tender_doc: Document) -> list[dict[str, Any]]:
	findings: list[dict[str, Any]] = []
	if not getattr(tender_doc, "procurement_package", None):
		findings.append(
			_f(
				"WORKS-AUDIT-001",
				SEVERITY_HIGH,
				AREA_AUDIT,
				"Procurement package reference is missing.",
				source_object="procurement_package",
			)
		)
	if not getattr(tender_doc, "std_template", None):
		findings.append(
			_f(
				"WORKS-AUDIT-002",
				SEVERITY_HIGH,
				AREA_AUDIT,
				"STD template reference is missing.",
				source_object="std_template",
			)
		)
	if not _strip_text(getattr(tender_doc, "configuration_hash", None)):
		findings.append(
			_f(
				"WORKS-AUDIT-003",
				SEVERITY_HIGH,
				AREA_AUDIT,
				"Configuration hash is missing.",
				source_object="configuration_hash",
			)
		)
	# AUDIT-004: prior hardening run recorded but snapshot not persisted
	if getattr(tender_doc, "works_hardening_checked_at", None) and not _strip_text(
		getattr(tender_doc, "works_hardening_snapshot_hash", None)
	):
		findings.append(
			_f(
				"WORKS-AUDIT-004",
				SEVERITY_HIGH,
				AREA_AUDIT,
				"Hardening snapshot hash is missing after a prior hardening check timestamp.",
				source_object="works_hardening_snapshot_hash",
			)
		)
	snap_json = _strip_text(getattr(tender_doc, "source_package_snapshot_json", None))
	if snap_json and not _strip_text(getattr(tender_doc, "source_package_hash", None)):
		findings.append(
			_f(
				"WORKS-AUDIT-005",
				SEVERITY_HIGH,
				AREA_AUDIT,
				"Source package snapshot JSON exists but source_package_hash is missing.",
				source_object="source_package_hash",
			)
		)
	return findings


def validate_legacy_lockout_checks(tender_doc: Document) -> tuple[list[dict[str, Any]], bool]:
	"""Returns (findings, legacy_lockout_checked)."""
	findings: list[dict[str, Any]] = []
	# Detectable legacy flags on current schema (doc §18.8).
	candidates = (
		("content_source_is_upload", "WORKS-LEGACY-001"),
		("manual_submission_checklist_enabled", "WORKS-LEGACY-002"),
		("manual_opening_register_enabled", "WORKS-LEGACY-003"),
		("manual_evaluation_criteria_enabled", "WORKS-LEGACY-004"),
		("manual_contract_terms_enabled", "WORKS-LEGACY-005"),
	)
	for attr, code in candidates:
		if hasattr(tender_doc, attr) and getattr(tender_doc, attr) in (1, True, "1"):
			findings.append(
				_f(
					code,
					SEVERITY_CRITICAL,
					AREA_LEGACY,
					f"Legacy manual or upload-driven tender behaviour is enabled ({attr}).",
					source_object=attr,
					blocks_transition=True,
					blocking_for="Publication",
				)
			)
	return findings, True
