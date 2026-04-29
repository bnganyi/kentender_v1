from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.template_version_parameters_service import (
	build_std_template_version_parameter_catalogue,
)
from kentender_procurement.std_engine.services.template_version_forms_service import (
	build_std_template_version_forms_catalogue,
)
from kentender_procurement.std_engine.services.template_version_works_service import (
	build_std_template_version_works_configuration,
)
from kentender_procurement.std_engine.services.template_version_mappings_service import (
	build_std_template_version_mappings_catalogue,
)
from kentender_procurement.std_engine.services.template_version_reviews_service import (
	build_std_template_version_reviews_approval,
)
from kentender_procurement.std_engine.services.template_version_audit_evidence_service import (
	build_std_template_version_audit_evidence,
	build_std_template_version_audit_export_csv,
)
from kentender_procurement.std_engine.services.template_version_structure_service import (
	build_std_template_version_structure_tree,
)
from kentender_procurement.std_engine.services.template_version_workbench_service import (
	build_std_template_version_workbench_summary,
)


@frappe.whitelist()
def get_std_template_version_workbench_summary(version_code: str | None = None) -> dict:
	"""Read-only + locked-section flags for STD workbench Template Version tabs (STD-CURSOR-1007)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_workbench_summary(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_structure_tree(version_code: str | None = None) -> dict:
	"""Parts / sections / clauses tree for STD workbench Template Version Structure tab (STD-CURSOR-1008)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_structure_tree(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_parameter_catalogue(version_code: str | None = None) -> dict:
	"""Parameter catalogue + dependencies for STD workbench Template Version Parameters tab (STD-CURSOR-1009)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_parameter_catalogue(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_forms_catalogue(version_code: str | None = None) -> dict:
	"""Forms catalogue + DSM/DEM/DCM preview for STD workbench Template Version Forms tab (STD-CURSOR-1010)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_forms_catalogue(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_works_configuration(version_code: str | None = None) -> dict:
	"""Works configuration payload for STD workbench Template Version Works tab (STD-CURSOR-1011)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_works_configuration(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_mappings_catalogue(version_code: str | None = None) -> dict:
	"""Extraction mappings catalogue for STD workbench Template Version Mappings tab (STD-CURSOR-1012)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_mappings_catalogue(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_reviews_approval(version_code: str | None = None) -> dict:
	"""Reviews, activation checklist, and gates for STD workbench Template Version tab (STD-CURSOR-1013)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_reviews_approval(str(version_code or "").strip())


@frappe.whitelist()
def get_std_template_version_audit_evidence(version_code: str | None = None) -> dict:
	"""Audit timeline and evidence sections for STD workbench Template Version tab (STD-CURSOR-1014)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_audit_evidence(str(version_code or "").strip())


@frappe.whitelist()
def export_std_template_version_audit_evidence_csv(version_code: str | None = None) -> dict:
	"""CSV export of audit rows for a template version (Auditor / Administrator / System Manager)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_std_template_version_audit_export_csv(str(version_code or "").strip())
