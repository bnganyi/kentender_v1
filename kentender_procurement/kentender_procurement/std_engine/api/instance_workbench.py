from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.instance_addendum_panel_service import (
	build_std_instance_addendum_impact_panel,
)
from kentender_procurement.std_engine.services.instance_audit_trail_service import (
	build_std_instance_audit_trail,
)
from kentender_procurement.std_engine.services.instance_boq_workbench_service import (
	build_std_instance_boq_workbench_panel,
)
from kentender_procurement.std_engine.services.instance_outputs_preview_service import (
	build_std_instance_outputs_preview,
)
from kentender_procurement.std_engine.services.instance_parameter_catalogue_service import (
	build_std_instance_parameter_catalogue,
)
from kentender_procurement.std_engine.services.instance_readiness_panel_service import (
	build_std_instance_readiness_panel,
)
from kentender_procurement.std_engine.services.instance_workbench_service import (
	build_std_instance_workbench_shell,
)
from kentender_procurement.std_engine.services.instance_works_panel_service import (
	build_std_instance_works_requirements_panel,
)
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness


@frappe.whitelist()
def get_std_instance_workbench_shell(instance_code: str | None = None) -> dict:
	"""Read-only and addendum guidance for STD workbench STD Instance tabs (STD-CURSOR-1101)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_workbench_shell(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_parameter_catalogue(instance_code: str | None = None) -> dict:
	"""Instance parameter groups with values (STD-CURSOR-1102)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_parameter_catalogue(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_works_requirements_panel(instance_code: str | None = None) -> dict:
	"""Works requirements + attachments (STD-CURSOR-1103)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_works_requirements_panel(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_boq_workbench_panel(instance_code: str | None = None) -> dict:
	"""BOQ summary + bills + items (STD-CURSOR-1104)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_boq_workbench_panel(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_outputs_preview(instance_code: str | None = None) -> dict:
	"""Generated outputs preview (STD-CURSOR-1105)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_outputs_preview(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_readiness_panel(instance_code: str | None = None) -> dict:
	"""Readiness summary + findings (STD-CURSOR-1106)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_readiness_panel(str(instance_code or "").strip())


@frappe.whitelist()
def run_std_instance_readiness_now(instance_code: str | None = None) -> dict:
	"""Run readiness engine for STD instance (STD-CURSOR-1106)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return run_std_readiness("STD_INSTANCE", str(instance_code or "").strip(), actor=frappe.session.user)


@frappe.whitelist()
def get_std_instance_addendum_impact_panel(instance_code: str | None = None) -> dict:
	"""Addendum impact analyses for instance (STD-CURSOR-1107)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_addendum_impact_panel(str(instance_code or "").strip())


@frappe.whitelist()
def get_std_instance_audit_trail(instance_code: str | None = None) -> dict:
	"""Audit events for STD instance (Phase 11 tab)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_instance_audit_trail(str(instance_code or "").strip())
