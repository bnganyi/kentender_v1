from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def _current_output_code(instance_code: str, output_type: str) -> str | None:
	return frappe.db.get_value(
		"STD Generated Output",
		{"instance_code": instance_code, "output_type": output_type, "status": "Current", "is_stale": 0},
		"output_code",
	)


def _binding_payload(tender_code: str, instance_doc) -> dict[str, Any]:
	payload = {
		"tender_code": tender_code,
		"std_instance_code": instance_doc.instance_code,
		"std_template_version_code": instance_doc.template_version_code,
		"std_profile_code": instance_doc.profile_code,
		"std_bundle_code": _current_output_code(instance_doc.instance_code, "Bundle"),
		"std_dsm_code": _current_output_code(instance_doc.instance_code, "DSM"),
		"std_dom_code": _current_output_code(instance_doc.instance_code, "DOM"),
		"std_dem_code": _current_output_code(instance_doc.instance_code, "DEM"),
		"std_dcm_code": _current_output_code(instance_doc.instance_code, "DCM"),
		"std_readiness_status": instance_doc.readiness_status,
	}
	payload["std_outputs_current"] = int(
		all(payload.get(k) for k in ("std_bundle_code", "std_dsm_code", "std_dom_code", "std_dem_code", "std_dcm_code"))
		and payload.get("std_readiness_status") == "Ready"
	)
	return payload


@frappe.whitelist()
def bind_std_instance_to_tender(tender_code: str, std_instance_code: str, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-0901: bind tender reference to STD instance and current generated outputs."""
	if not tender_code:
		frappe.throw(_("Tender code is required."), title=_("STD binding"))
	name = frappe.db.get_value("STD Instance", {"instance_code": std_instance_code}, "name")
	if not name:
		frappe.throw(_("STD instance not found."), title=_("STD binding"))
	inst = frappe.get_doc("STD Instance", name)
	payload = _binding_payload(tender_code, inst)

	binding_name = frappe.db.get_value("STD Tender Binding", {"tender_code": tender_code}, "name")
	if binding_name:
		doc = frappe.get_doc("STD Tender Binding", binding_name)
		doc.update(payload)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "STD Tender Binding", **payload}).insert(ignore_permissions=True)
	return {"binding_code": doc.name, **payload}


@frappe.whitelist()
def get_tender_std_binding(tender_code: str) -> dict[str, Any]:
	name = frappe.db.get_value("STD Tender Binding", {"tender_code": tender_code}, "name")
	if not name:
		return {"binding": None}
	doc = frappe.get_doc("STD Tender Binding", name)
	return {"binding": doc.as_dict()}
