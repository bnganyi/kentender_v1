# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender B3/B4/B5/B7/B8/B9 — release package to Procurement Tender (hook + service).

Doc 2 sec. 16.1: ``release_procurement_package_to_tender(package_name) -> dict``.

B4: tender **Configured** + merged ``configuration_json`` when STD resolves.
B5: doc 2 sec. 17 ``XMV-BND-001`` / ``XMV-PT-001`` … ``011`` via
``planning_tender_handoff_xmv.validate_package_for_release_xmv``.
B7: doc 2 sec. 14–15 initial ``configuration_json`` via
``planning_tender_handoff_configuration`` (never ``sample_tender.json`` on this path).
B8: doc 2 sec. 18 — ``source_package_snapshot_json`` / hashes / counts + audit **Comment**;
    audit failure deletes the new tender and raises (fail-closed).
B9: doc 2 sec. 16.3 — duplicate active tender blocked on ``Procurement Tender`` validate
    (``planning_tender_handoff_duplicates``); complements idempotent release + ``XMV-PT-009``.

Hook failures must not raise: ``deliver_procurement_package_release`` swallows
exceptions per handler; this hook logs ``ok: False`` outcomes instead.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.officer_tender_config import (
	TENDER_STATUS_CONFIGURED,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_audit import (
	append_handoff_audit_comment,
	build_handoff_snapshot_and_hashes,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_configuration import (
	apply_handoff_posture_on_new_tender,
	apply_inherited_package_plan_to_tender,
	build_handoff_configuration_json,
	load_plan_for_handoff,
	procurement_category_code_from_template,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
	format_xmv_critical_message,
	validate_package_for_release_xmv,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

_PACKAGE_METHOD_TO_TENDER_METHOD = {
	"Open Tender": "OPEN_COMPETITIVE_TENDERING",
	"Restricted Tender": "RESTRICTED_COMPETITIVE_TENDERING",
	"RFQ": "OPEN_COMPETITIVE_TENDERING",
	"RFP": "OPEN_COMPETITIVE_TENDERING",
	"Direct Procurement": "OPEN_COMPETITIVE_TENDERING",
}


def _map_package_method_to_tender(method: str | None) -> str:
	if not method:
		return "OPEN_COMPETITIVE_TENDERING"
	return _PACKAGE_METHOD_TO_TENDER_METHOD.get(method, "OPEN_COMPETITIVE_TENDERING")


def _find_existing_linked_tender(package_name: str) -> str | None:
	rows = frappe.get_all(
		"Procurement Tender",
		filters={
			"procurement_package": package_name,
			"tender_status": ("!=", "Cancelled"),
		},
		pluck="name",
		limit=1,
	)
	return rows[0] if rows else None


def package_has_release_tender(package_name: str) -> bool:
	"""True if a non-cancelled ``Procurement Tender`` is linked to this package (PT-HANDOFF-AC-009)."""
	return _find_existing_linked_tender(package_name) is not None


def _apply_std_identity_to_tender(t, std_template_name: str) -> None:
	row = frappe.db.get_value(
		"STD Template",
		std_template_name,
		["template_code", "package_version", "package_hash"],
		as_dict=True,
	)
	if row:
		t.template_code = row.get("template_code") or ""
		t.template_version = row.get("package_version") or ""
		t.package_hash = row.get("package_hash") or ""


def release_procurement_package_to_tender(package_name: str) -> dict[str, Any]:
	"""Create or return a ``Procurement Tender`` for the given package (B3/B4/B5/B7).

	:param package_name: Internal name of ``Procurement Package`` (same as hook payload ``package``).
	:returns: Dict with ``ok`` bool; on success includes ``tender``, ``std_template``, ``existing``.
	"""
	if not (package_name or "").strip():
		return {"ok": False, "message": _("Package name is required.")}

	package_name = package_name.strip()

	if not frappe.db.exists("Procurement Package", package_name):
		return {"ok": False, "message": _("Procurement Package {0} was not found.").format(package_name)}

	if not frappe.has_permission("Procurement Package", "read", doc=package_name):
		return {"ok": False, "message": _("Not permitted to read Procurement Package.")}

	if not frappe.has_permission("Procurement Tender", "create"):
		return {"ok": False, "message": _("Not permitted to create Procurement Tender.")}

	pkg = frappe.get_doc("Procurement Package", package_name)

	existing = _find_existing_linked_tender(package_name)
	if existing:
		ref = frappe.db.get_value("Procurement Tender", existing, "tender_reference")
		std = frappe.db.get_value("Procurement Tender", existing, "std_template")
		st = frappe.db.get_value("Procurement Tender", existing, "tender_status")
		return {
			"ok": True,
			"existing": True,
			"tender": existing,
			"tender_reference": ref,
			"std_template": std,
			"tender_status": st,
		}

	xmv = validate_package_for_release_xmv(pkg)
	if xmv.has_critical():
		return {
			"ok": False,
			"message": format_xmv_critical_message(xmv),
			"xmv_findings": xmv.all_findings_dicts(),
		}

	std_res = resolve_std_template_for_handoff(pkg)
	std_template = std_res.std_name
	if not std_template:
		return {
			"ok": False,
			"message": _(
				"No STD Template could be resolved (set Procurement Template.default_std_template, resolve mapping ambiguity, or satisfy Works POC fallback; see {0})."
			).format(TEMPLATE_CODE),
			"xmv_findings": xmv.all_findings_dicts(),
			"std_resolution_path": std_res.path,
		}

	title = (pkg.package_name or "").strip() or _("Tender from planning package")
	ref = (pkg.package_code or "").strip() or f"REL-{pkg.name[:12]}"

	plan = load_plan_for_handoff(pkg)
	pkg_status_before = (pkg.get("status") or "").strip()

	t = frappe.new_doc("Procurement Tender")
	t.naming_series = "PT-.YYYY.-.#####"
	t.std_template = std_template
	t.tender_title = title
	t.tender_reference = ref
	t.procurement_plan = pkg.plan_id
	t.procurement_package = pkg.name
	t.procurement_template = pkg.template_id
	if pkg.package_code:
		t.source_package_code = pkg.package_code
	t.procurement_method = _map_package_method_to_tender(pkg.procurement_method)
	t.tender_scope = "NATIONAL"
	t.procurement_category = procurement_category_code_from_template(pkg.template_id)
	_apply_std_identity_to_tender(t, std_template)
	apply_inherited_package_plan_to_tender(t, pkg, plan)
	apply_handoff_posture_on_new_tender(t)
	cfg_str = build_handoff_configuration_json(t, pkg, plan)
	t.configuration_json = cfg_str
	t.tender_status = TENDER_STATUS_CONFIGURED

	_snap, snap_json, snap_hash, cfg_hash, dcnt, bcnt = build_handoff_snapshot_and_hashes(
		pkg,
		plan,
		std_template,
		std_res.path,
		[f.as_dict() for f in xmv.critical],
		[w.as_dict() for w in xmv.warnings],
		cfg_str,
		pkg_status_before,
	)
	t.source_package_snapshot_json = snap_json
	t.source_package_hash = snap_hash
	t.configuration_hash = cfg_hash
	t.source_demand_count = dcnt
	t.source_budget_line_count = bcnt

	t.insert()

	package_status_after = (
		frappe.db.get_value("Procurement Package", package_name, "status") or ""
	).strip()
	roles = list(frappe.get_roles(frappe.session.user))
	try:
		append_handoff_audit_comment(
			t.name,
			actor=frappe.session.user,
			roles=roles,
			source_package=pkg.name,
			source_plan=plan.name if plan else None,
			package_status_before=pkg_status_before,
			package_status_after=package_status_after or None,
			target_tender=t.name,
			std_template=std_template,
			xmv_findings=[],
			xmv_warnings=[w.as_dict() for w in xmv.warnings],
			snapshot_hash=snap_hash,
			configuration_hash=cfg_hash,
		)
	except Exception as exc:
		frappe.log_error(
			title="Release-to-tender: handoff audit comment failed",
			message=json.dumps({"tender": t.name, "package": package_name, "error": str(exc)}),
		)
		try:
			frappe.delete_doc("Procurement Tender", t.name, force=True, ignore_permissions=True)
		except Exception as del_exc:
			frappe.log_error(
				title="Release-to-tender: cleanup after audit failure",
				message=json.dumps({"tender": t.name, "error": str(del_exc)}),
			)
		frappe.throw(
			_("Planning-to-tender handoff could not be completed: audit trail was not written."),
			title=_("Handoff audit failed"),
		)

	out: dict[str, Any] = {
		"ok": True,
		"existing": False,
		"tender": t.name,
		"tender_reference": t.tender_reference,
		"std_template": std_template,
		"tender_status": t.tender_status,
	}
	if xmv.warnings:
		out["xmv_warnings"] = [w.as_dict() for w in xmv.warnings]
	return out


def hook_release_procurement_package_to_tender(payload: dict[str, Any] | None) -> None:
	"""Registered on ``release_procurement_package_to_tender`` hook; accepts ``build_release_payload`` shape."""
	if not isinstance(payload, dict):
		frappe.log_error(
			title="Release-to-tender: invalid payload (not a dict)",
			message=json.dumps({"payload_type": type(payload).__name__}),
		)
		return

	package = payload.get("package")
	if not package:
		frappe.log_error(
			title="Release-to-tender: missing package in payload",
			message=json.dumps({"payload_keys": list(payload.keys())}),
		)
		return

	out = release_procurement_package_to_tender(str(package))
	if not out.get("ok"):
		frappe.log_error(
			title="Release-to-tender: tender not created",
			message=json.dumps(
				{
					"package": package,
					"message": str(out.get("message", "")),
					"xmv_findings": out.get("xmv_findings"),
				}
			),
		)
