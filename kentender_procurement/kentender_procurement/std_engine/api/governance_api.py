# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Governance write APIs — legal review, validation rerun, activation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.std_engine.services.activation_readiness_service import (
	evaluate_activation_readiness,
	sync_activation_flags,
)
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import (
	approve_all_pending,
	approve_verbatim_objects,
)
from kentender_procurement.std_engine.services.envelope import build_package_context
from kentender_procurement.std_engine.validation.validation_engine import ValidationEngine

READINESS_ROLES = ("System Manager", "Administrator", "Legal Reviewer", "Procurement Reviewer")
LEGAL_REVIEW_ROLES = ("System Manager", "Administrator", "Legal Reviewer")
ACTIVATION_ROLES = ("System Manager", "Administrator")


@frappe.whitelist(methods=["GET"])
def get_activation_readiness(package_id: str) -> dict[str, Any]:
	frappe.only_for(READINESS_ROLES)
	readiness = evaluate_activation_readiness(package_id)
	ctx = build_package_context(package_id)
	return {
		"ok": True,
		"packageContext": ctx,
		"data": readiness,
	}


@frappe.whitelist(methods=["POST"])
def approve_legal_review(package_id: str, approve_all: bool = True) -> dict[str, Any]:
	frappe.only_for(LEGAL_REVIEW_ROLES)
	if cint(approve_all):
		result = approve_all_pending(package_id)
	else:
		result = approve_verbatim_objects(package_id)
	readiness = sync_activation_flags(package_id)
	return {"ok": True, "approval": result, "readiness": readiness}


@frappe.whitelist(methods=["POST"])
def rerun_validation(package_id: str) -> dict[str, Any]:
	frappe.only_for(LEGAL_REVIEW_ROLES)
	result = ValidationEngine().run_for_package(package_id, run_type="MANUAL_RERUN")
	readiness = sync_activation_flags(package_id)
	return {
		"ok": True,
		"validation": {
			"runKey": result.run_key,
			"summary": result.summary,
		},
		"readiness": readiness,
	}


@frappe.whitelist(methods=["POST"])
def activate_std_version(package_id: str) -> dict[str, Any]:
	frappe.only_for(ACTIVATION_ROLES)
	if not getattr(frappe.conf, "developer_mode", False):
		frappe.only_for(LEGAL_REVIEW_ROLES)
	result = activate_version(package_id)
	return {"ok": True, "activation": result}
