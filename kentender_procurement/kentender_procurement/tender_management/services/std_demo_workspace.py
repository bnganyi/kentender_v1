# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Admin Console Step 5 — read-only HTML context for STD demo workspace on Procurement Tender."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.document import Document

STD_POC_TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"
DEMO_MARKER = "STD DEMO WORKSPACE"

BANNER_TEXT = (
	"POC Demo Workspace: This record is used to demonstrate STD-WORKS-POC package behavior. "
	"It is not a production tender and must not be published or used for a real procurement process."
)

RENDER_CONTEXT_PREFIX = "// STD POC RENDER CONTEXT"


def _child_rows_to_dicts(child_rows: list[Any] | None) -> list[dict[str, Any]]:
	if not child_rows:
		return []
	rows: list[dict[str, Any]] = []
	for row in child_rows:
		as_dict = getattr(row, "as_dict", None)
		if callable(as_dict):
			rows.append(as_dict())
		elif isinstance(row, dict):
			rows.append(row)
		else:
			rows.append(dict(row))
	return rows


def is_std_demo_tender(doc: Document) -> bool:
	poc = (getattr(doc, "poc_notes", None) or "") or ""
	if DEMO_MARKER in poc:
		return True
	st = (getattr(doc, "std_template", None) or "") or ""
	return st == STD_POC_TEMPLATE_NAME


def _pack_preview_state(doc: Document) -> str:
	pack_html = getattr(doc, "generated_tender_pack_html", None) or ""
	if not pack_html:
		return "none"
	if pack_html.startswith(RENDER_CONTEXT_PREFIX):
		return "render_context_only"
	return "preview_html"


def build_demo_workspace_context(doc: Document) -> dict[str, Any]:
	cfg: dict[str, Any] = {}
	raw = getattr(doc, "configuration_json", None) or ""
	if raw:
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, dict):
				cfg = parsed
		except json.JSONDecodeError:
			cfg = {}

	lots = _child_rows_to_dicts(doc.get("lots"))
	boq = _child_rows_to_dicts(doc.get("boq_items"))
	categories = sorted(
		{str(b.get("item_category") or "") for b in boq if b.get("item_category")}
	)
	required = doc.get("required_forms") or []
	val_msg = doc.get("validation_messages") or []

	lots_preview: list[dict[str, str]] = []
	for lot in lots[:12]:
		lots_preview.append(
			{
				"lot_code": str(lot.get("lot_code") or ""),
				"lot_title": str(lot.get("lot_title") or ""),
			}
		)

	return {
		"banner_text": BANNER_TEXT,
		"tender_name": doc.name,
		"tender_title": doc.tender_title or "",
		"tender_reference": doc.tender_reference or "",
		"std_template": doc.std_template or "",
		"template_code": doc.template_code or "",
		"template_version": doc.template_version or "",
		"tender_status": doc.tender_status or "",
		"validation_status": doc.validation_status or "",
		"procurement_method": doc.procurement_method or "",
		"tender_scope": doc.tender_scope or "",
		"configuration_hash": doc.configuration_hash or "",
		"package_hash": doc.package_hash or "",
		"last_validated_at": str(doc.last_validated_at or ""),
		"last_generated_at": str(doc.last_generated_at or ""),
		"modified": str(doc.modified or ""),
		"owner": doc.owner or "",
		"cfg_method": str(cfg.get("METHOD.PROCUREMENT_METHOD") or ""),
		"cfg_template_code": str(cfg.get("SYSTEM.TEMPLATE_CODE") or ""),
		"cfg_package_version": str(cfg.get("SYSTEM.PACKAGE_VERSION") or ""),
		"lot_count": len(lots),
		"lots_preview": lots_preview,
		"boq_count": len(boq),
		"boq_categories": categories,
		"required_form_count": len(required),
		"validation_message_count": len(val_msg),
		"pack_preview_state": _pack_preview_state(doc),
	}


def render_demo_workspace_html(doc: Document) -> str:
	ctx = build_demo_workspace_context(doc)
	try:
		from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
			get_demo_inspector_summary,
		)
		from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
			get_preview_audit_summary,
		)

		ins = get_demo_inspector_summary(doc.name)
		ctx["forms_inspector_html"] = ins.get("forms_html") or ""
		ctx["boq_inspector_html"] = ins.get("boq_html") or ""
		pa = get_preview_audit_summary(doc.name)
		ctx["preview_audit_html"] = pa.get("html") or ""
	except Exception as exc:
		ctx["forms_inspector_html"] = (
			f'<div class="alert alert-warning">Required forms inspector failed to load: '
			f"{frappe.utils.escape_html(str(exc))}</div>"
		)
		ctx["boq_inspector_html"] = (
			f'<div class="alert alert-warning">BoQ inspector failed to load: '
			f"{frappe.utils.escape_html(str(exc))}</div>"
		)
		ctx["preview_audit_html"] = (
			f'<div class="alert alert-warning">Preview and audit viewer failed to load: '
			f"{frappe.utils.escape_html(str(exc))}</div>"
		)
	return frappe.render_template(
		"templates/std_admin_console/demo_workspace.html",
		ctx,
	)
