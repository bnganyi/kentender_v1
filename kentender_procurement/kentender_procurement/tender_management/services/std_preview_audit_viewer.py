# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Admin Console Step 7 — read-only preview and audit viewer summary."""

from __future__ import annotations

import html as html_module
from typing import Any

import frappe
from frappe.model.document import Document

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	RENDER_CONTEXT_BANNER,
)

PREVIEW_VIEWER_POC_WARNING = (
	"POC preview and audit: This view ties the on-screen tender-pack preview to package and "
	"configuration hashes and timestamps. It is not a final legal tender document."
)

# Markers inside rendered tender_pack.html (Step 13) for completeness heuristics.
_PREVIEW_MARKERS: tuple[tuple[str, str], ...] = (
	("poc_warning", "POC Preview Only"),
	("master_title", "STD-WORKS-POC Tender Pack Preview"),
	("forms_checklist", "Required Bidder Forms Checklist"),
	("boq_summary", "Bills of Quantities Summary"),
	("audit_summary", "Audit Summary"),
)


def _get_tender_read(tender_name: str) -> Document:
	if not tender_name:
		frappe.throw(frappe._("tender_name is required."), frappe.ValidationError)
	if not frappe.db.exists("Procurement Tender", tender_name):
		frappe.throw(
			frappe._("Procurement Tender {0} was not found.").format(tender_name),
			frappe.DoesNotExistError,
		)
	doc = frappe.get_doc("Procurement Tender", tender_name)
	doc.check_permission("read")
	return doc


def _child_rows_to_dicts(child_rows: list[Any] | None) -> list[dict[str, Any]]:
	if not child_rows:
		return []
	out: list[dict[str, Any]] = []
	for row in child_rows:
		ad = getattr(row, "as_dict", None)
		if callable(ad):
			out.append(ad())
		elif isinstance(row, dict):
			out.append(row)
		else:
			out.append(dict(row))
	return out


def _is_render_context_only(pack_html: str) -> bool:
	s = (pack_html or "").strip()
	return bool(s) and s.startswith(RENDER_CONTEXT_BANNER)


def _is_generated_preview_html(pack_html: str) -> bool:
	s = (pack_html or "").strip()
	if not s or _is_render_context_only(s):
		return False
	return "std-poc-preview" in s or "STD-WORKS-POC Tender Pack Preview" in s


def _validation_has_blockers(val_rows: list[dict[str, Any]]) -> bool:
	for m in val_rows:
		if m.get("blocks_generation") in (1, True, "1"):
			return True
		if (m.get("severity") or "").upper() in ("BLOCKER", "ERROR"):
			return True
	return False


def _compute_preview_status(
	tender: Document,
	pack_html: str,
	val_rows: list[dict[str, Any]],
) -> str:
	vs = (tender.validation_status or "").strip()
	if _validation_has_blockers(val_rows) or vs in ("Blocked", "Failed"):
		return "Blocked"
	if not _is_generated_preview_html(pack_html):
		if _is_render_context_only(pack_html) or not (pack_html or "").strip():
			return "Not Generated"
		return "Unknown"
	lv = tender.last_validated_at
	lg = tender.last_generated_at
	if lv and lg and lv > lg:
		return "Possibly Stale"
	return "Generated"


def _output_completeness(pack_html: str) -> list[dict[str, Any]]:
	if not _is_generated_preview_html(pack_html):
		return [
			{
				"id": mid,
				"label": label,
				"status": "unknown",
				"detail": "Preview HTML not generated or only render context present.",
			}
			for mid, label in _PREVIEW_MARKERS
		]
	out: list[dict[str, Any]] = []
	for mid, needle in _PREVIEW_MARKERS:
		ok = needle in pack_html
		out.append(
			{
				"id": mid,
				"label": needle,
				"status": "pass" if ok else "warn",
				"detail": "Found in preview HTML" if ok else "Marker not found in preview HTML.",
			}
		)
	return out


def get_preview_audit_summary(tender_name: str) -> dict[str, Any]:
	tender = _get_tender_read(tender_name)
	warnings: list[str] = []

	pack_html = (getattr(tender, "generated_tender_pack_html", None) or "") or ""
	val_rows = _child_rows_to_dicts(tender.get("validation_messages"))
	req_forms = tender.get("required_forms") or []
	boq = tender.get("boq_items") or []

	if not tender.std_template:
		warnings.append("Tender has no STD Template linked.")

	if not (tender.configuration_hash or "").strip():
		warnings.append("Configuration hash is missing; reproducibility is incomplete.")

	if not (tender.package_hash or "").strip():
		warnings.append("Package hash is missing on the tender form.")

	preview_status = _compute_preview_status(tender, pack_html, val_rows)

	if preview_status == "Generated" and not val_rows and (tender.validation_status or "") in (
		"",
		"Not Validated",
	):
		warnings.append("Validation has not been run; preview may not be reliable.")

	severity_counts: dict[str, int] = {}
	for m in val_rows:
		sev = str(m.get("severity") or "UNKNOWN").upper()
		severity_counts[sev] = severity_counts.get(sev, 0) + 1

	sample_msgs = [str(m.get("message") or "")[:200] for m in val_rows[:8]]

	validation_summary = {
		"validation_status": tender.validation_status or "",
		"message_count": len(val_rows),
		"severity_counts": severity_counts,
		"has_blockers": _validation_has_blockers(val_rows),
		"sample_messages": sample_msgs,
	}

	required_forms_summary = {
		"row_count": len(req_forms),
	}

	boq_summary = {
		"row_count": len(boq),
	}

	std_name = tender.std_template or ""
	source_document_code = ""
	package_version = ""
	try:
		if std_name:
			std_doc = frappe.get_doc("STD Template", std_name)
			source_document_code = (getattr(std_doc, "source_document_code", None) or "") or ""
			package_version = (getattr(std_doc, "package_version", None) or "") or ""
	except Exception as e:
		warnings.append(f"Could not read STD Template: {e}")

	audit = {
		"tender_name": tender.name,
		"tender_title": tender.tender_title or "",
		"tender_reference": tender.tender_reference or "",
		"std_template": std_name,
		"template_code": tender.template_code or "",
		"template_version": tender.template_version or "",
		"source_document_code": source_document_code,
		"package_version": package_version,
		"package_hash": tender.package_hash or "",
		"configuration_hash": tender.configuration_hash or "",
		"last_validated_at": str(tender.last_validated_at or ""),
		"last_generated_at": str(tender.last_generated_at or ""),
		"preview_html_length": len(pack_html),
		"preview_is_render_context_only": _is_render_context_only(pack_html),
	}

	links = {
		"std_template": std_name,
		"std_template_desk_path": f"/app/std-template/{std_name}" if std_name else "",
		"procurement_tender_desk_path": f"/app/procurement-tender/{tender.name}",
	}

	max_srcdoc = 400_000
	preview_body = pack_html if _is_generated_preview_html(pack_html) else ""
	if len(preview_body) > max_srcdoc:
		warnings.append(
			f"Preview HTML truncated for safe viewer embedding ({len(preview_body)} chars → {max_srcdoc})."
		)
		preview_body = preview_body[:max_srcdoc]

	preview_iframe_srcdoc = html_module.escape(preview_body) if preview_body else ""

	out: dict[str, Any] = {
		"ok": True,
		"tender": tender.name,
		"poc_warning": PREVIEW_VIEWER_POC_WARNING,
		"preview_status": preview_status,
		"output_completeness": _output_completeness(pack_html),
		"validation_summary": validation_summary,
		"required_forms_summary": required_forms_summary,
		"boq_summary": boq_summary,
		"audit": audit,
		"warnings": warnings,
		"links": links,
		"preview_iframe_srcdoc": preview_iframe_srcdoc,
	}
	out["html"] = render_preview_audit_viewer_html(out)
	return out


def render_preview_audit_viewer_html(payload: dict[str, Any]) -> str:
	return frappe.render_template(
		"templates/std_admin_console/preview_audit_viewer.html",
		payload,
	)
