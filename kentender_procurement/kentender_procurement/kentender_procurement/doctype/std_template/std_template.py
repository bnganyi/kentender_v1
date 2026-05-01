# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	_child_rows_to_dicts,
)
from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services.std_package_validation import (
	build_rule_trace_report_html,
	build_validation_report_html,
	run_package_validation,
)
from kentender_procurement.tender_management.services.std_package_viewer import build_api_payload
from kentender_procurement.tender_management.services.std_template_loader import import_std_works_poc_template


class STDTemplate(Document):
	"""STD-WORKS-POC: imported STD template package (metadata + JSON payload). Step 9 — schema only."""


ALLOWED_PACKAGE_COMPONENTS: frozenset[str] = frozenset(
	{"manifest", "sections", "fields", "rules", "forms", "render_map", "sample_tender", "full_package"}
)


@frappe.whitelist()
def get_template_package_summary(template_name: str) -> dict:
	"""Admin Console Step 3 — structured summaries + HTML for read-only package viewer."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {"ok": False, "error": _("Invalid package_json: {0}").format(str(e))}
	return build_api_payload(doc, pkg)


@frappe.whitelist()
def get_template_package_component(template_name: str, component_name: str) -> dict:
	"""Return one package component as pretty-printed JSON (read-only)."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	if not component_name:
		frappe.throw(_("component_name is required"))
	if component_name not in ALLOWED_PACKAGE_COMPONENTS:
		frappe.throw(_("Unknown component_name"), frappe.ValidationError)

	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {"ok": False, "error": _("Invalid package_json: {0}").format(str(e))}

	if component_name == "full_package":
		body = pkg
	else:
		body = pkg.get(component_name)

	text = json.dumps(body, indent=2, sort_keys=True, default=str)
	return {"ok": True, "component_name": component_name, "json": text}


@frappe.whitelist()
def validate_std_package(template_name: str) -> dict[str, Any]:
	"""Admin Console Step 4 — structured package validation (read-only)."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {
			"ok": False,
			"error": _("Invalid package_json: {0}").format(str(e)),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	result = run_package_validation(doc, pkg)
	result["html"] = build_validation_report_html(result)
	return result


@frappe.whitelist()
def trace_std_rules_for_sample(template_name: str, variant_code: str | None = None) -> dict[str, Any]:
	"""Admin Step 4 — rule trace for primary sample or a scenario variant."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		loaded = engine.load_template(template_name)
	except frappe.DoesNotExistError:
		raise
	except Exception as e:
		return {"ok": False, "error": str(e), "html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>"}
	try:
		cfg = engine.load_sample_config(loaded, variant_code or None)
		lots = engine.load_sample_lots(loaded, variant_code or None)
		boq = engine.load_sample_boq_rows(loaded, variant_code or None)
	except ValueError as e:
		return {
			"ok": False,
			"error": str(e),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	trace = engine.trace_rules(loaded, cfg, lots=lots, boq_items=boq)
	trace_source = "PRIMARY_SAMPLE" if not variant_code else "SAMPLE_VARIANT"
	out: dict[str, Any] = {
		"ok": bool(trace.get("ok")),
		"trace_source": trace_source,
		"variant_code": variant_code,
		"tender": None,
		"template_code": trace.get("template_code"),
		"configuration_hash": trace.get("configuration_hash"),
		"summary": trace.get("summary"),
		"rules": trace.get("rules"),
		"validation_result": trace.get("validation_result"),
	}
	out["html"] = build_rule_trace_report_html(out)
	return out


@frappe.whitelist()
def trace_std_rules_for_tender(tender_name: str) -> dict[str, Any]:
	"""Admin Step 4 — rule trace for an existing Procurement Tender."""
	if not tender_name:
		frappe.throw(_("tender_name is required"))
	tender = frappe.get_doc("Procurement Tender", tender_name)
	if not frappe.has_permission("Procurement Tender", "read", doc=tender):
		frappe.throw(_("Not permitted to read Procurement Tender"), frappe.PermissionError)
	if not tender.std_template:
		err = _("Procurement Tender has no STD Template linked.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	raw = tender.configuration_json
	if not raw:
		err = _("configuration_json is empty on this tender.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	try:
		cfg = json.loads(raw)
	except json.JSONDecodeError as e:
		return {
			"ok": False,
			"error": str(e),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	if not isinstance(cfg, dict):
		err = _("configuration_json must be a JSON object.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	lots = _child_rows_to_dicts(getattr(tender, "lots", None))
	boq = _child_rows_to_dicts(getattr(tender, "boq_items", None))
	try:
		loaded = engine.load_template(tender.std_template)
	except frappe.DoesNotExistError:
		raise
	except Exception as e:
		return {"ok": False, "error": str(e), "html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>"}
	trace = engine.trace_rules(loaded, cfg, lots=lots, boq_items=boq)
	out: dict[str, Any] = {
		"ok": bool(trace.get("ok")),
		"trace_source": "DEMO_TENDER",
		"variant_code": None,
		"tender": tender.name,
		"template_code": trace.get("template_code"),
		"configuration_hash": trace.get("configuration_hash"),
		"summary": trace.get("summary"),
		"rules": trace.get("rules"),
		"validation_result": trace.get("validation_result"),
	}
	out["html"] = build_rule_trace_report_html(out)
	return out


@frappe.whitelist()
def create_or_open_std_demo_tender(
	template_name: str,
	variant_code: str | None = None,
) -> dict[str, Any]:
	"""Admin Step 5 — create a new demo Procurement Tender linked to this STD Template (primary or variant sample)."""
	if variant_code in (None, "", "null"):
		variant_code = None
	if not template_name:
		frappe.throw(_("template_name is required"))
	std_doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=std_doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	if not frappe.has_permission("Procurement Tender", "create"):
		frappe.throw(_("Not permitted to create Procurement Tender"), frappe.PermissionError)

	import time

	t_ref = f"STD-DEMO-{int(time.time())}"
	marker = (
		"STD DEMO WORKSPACE — POC demonstration record for STD-WORKS-POC. "
		"Not for production procurement."
	)
	tender = frappe.new_doc("Procurement Tender")
	tender.naming_series = "PT-.YYYY.-.#####"
	tender.tender_title = _("STD-WORKS-POC Demo Tender")
	tender.tender_reference = t_ref
	tender.std_template = std_doc.name
	tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
	tender.tender_scope = "NATIONAL"
	tender.poc_notes = f"{marker} template={std_doc.name}"
	try:
		engine.populate_sample_tender(tender, variant_code=variant_code or None)
	except ValueError as e:
		return {"ok": False, "error": str(e), "message": str(e)}
	# Sample config overwrites title/reference; restore demo workspace identity.
	tender.tender_reference = t_ref
	tender.tender_title = _("STD-WORKS-POC Demo Tender")
	tender.tender_status = "Configured"
	tender.validation_status = "Not Validated"
	tender.set("validation_messages", [])
	tender.set("required_forms", [])
	tender.insert()
	frappe.db.commit()
	return {
		"ok": True,
		"message": _("Demo tender ready."),
		"tender": tender.name,
		"template_code": tender.template_code or std_doc.template_code,
		"variant_code": variant_code,
		"route": f"/app/procurement-tender/{tender.name}",
	}


@frappe.whitelist()
def reimport_std_template_package(template_name: str | None = None) -> dict:
	"""Re-run controlled STD-WORKS-POC seed import (Admin Console Step 3)."""
	# Spec: System Manager / technical admin — restrict to elevated roles only.
	roles = set(frappe.get_roles())
	if not roles.intersection({"System Manager", "Administrator"}):
		frappe.throw(
			_("Re-import is restricted to System Manager or Administrator."),
			frappe.PermissionError,
		)
	# template_name accepted for API symmetry; loader is fixed to POC package.
	return import_std_works_poc_template()
