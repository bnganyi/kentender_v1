# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HTTP / whitelisted API surface for STD Instance (REST mapping TBD).

STDINST-1200. Implement ``@frappe.whitelist`` handlers here or split by resource;
domain logic lives under ``tender_management.std_instance``.
"""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.addendum import (
	StdAddendumImpactService,
)
from kentender_procurement.tender_management.std_instance.attachment import (
	StdInstanceAttachmentService,
)
from kentender_procurement.tender_management.std_instance.binding import (
	TenderStdBindingService,
)
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
)
from kentender_procurement.tender_management.std_instance.downstream import (
	StdDownstreamConsumptionService,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.publication_lock import (
	StdPublicationLockService,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.snapshot import (
	StdInstanceSnapshotService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)


def _as_bool(value: Any, *, default: bool = False) -> bool:
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _ok(code: str, message: str, **payload: Any) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": True, "code": code, "message": message}
	out.update(payload)
	return out


def _err(code: str, message: str, *, details: Any = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "code": code, "message": message}
	if details is not None:
		out["details"] = details
	return out


def _map_exc(exc: Exception) -> tuple[str, str]:
	if isinstance(exc, frappe.DuplicateEntryError):
		return "STD_API_DUPLICATE_CONSTRAINT", str(exc)
	if isinstance(exc, frappe.PermissionError):
		return "STD_API_PERMISSION_DENIED", _("Permission denied.")
	if isinstance(exc, frappe.DoesNotExistError):
		return "STD_API_NOT_FOUND", str(exc)
	if isinstance(exc, frappe.ValidationError):
		return "STD_API_VALIDATION_FAILED", str(exc)
	return "STD_API_INTERNAL_ERROR", _("Unexpected server error.")


def _run_api(handler: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	try:
		return handler()
	except Exception as exc:
		code, msg = _map_exc(exc)
		if code == "STD_API_INTERNAL_ERROR":
			frappe.log_error(frappe.get_traceback(), "STDINST-1200 API failure")
		return _err(code, msg)


def _instance_payload(doc: Any) -> dict[str, Any]:
	return {
		"instance_code": doc.name,
		"procurement_tender": doc.procurement_tender,
		"instance_status": doc.instance_status,
		"readiness_status": doc.readiness_status,
	}


def _generate_for_type(instance_name: str, output_type: str, source_addendum_code: str | None = None) -> Any:
	ot = (output_type or "").strip().upper()
	if ot == "BUNDLE":
		return StdInstanceGeneratedOutputService.generate_bundle(
			instance_name, source_addendum_code=source_addendum_code
		)
	if ot == "DSM":
		return StdInstanceGeneratedOutputService.generate_dsm(
			instance_name, source_addendum_code=source_addendum_code
		)
	if ot == "DOM":
		return StdInstanceGeneratedOutputService.generate_dom(
			instance_name, source_addendum_code=source_addendum_code
		)
	if ot == "DEM":
		return StdInstanceGeneratedOutputService.generate_dem(
			instance_name, source_addendum_code=source_addendum_code
		)
	if ot == "DCM":
		return StdInstanceGeneratedOutputService.generate_dcm(
			instance_name, source_addendum_code=source_addendum_code
		)
	frappe.throw(_("Unsupported output_type {0}.").format(output_type), title=_("STD API"))


@frappe.whitelist()
def create_instance(procurement_tender: str, ignore_permissions: bool = False) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_INSTANCE_CREATED",
			_("STD Instance created."),
			instance=_instance_payload(
				TenderStdBindingService.create_std_instance_for_tender(
					procurement_tender,
					ignore_permissions=_as_bool(ignore_permissions),
				)
			),
		)
	)


@frappe.whitelist()
def get_instance(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_INSTANCE_FETCHED",
			_("STD Instance fetched."),
			instance=_instance_payload(frappe.get_doc("Tender STD Instance", instance_name)),
		)
	)


@frappe.whitelist()
def generate_outputs(
	instance_name: str,
	output_types: list[str] | str,
	source_addendum_code: str | None = None,
	publish_outputs: bool = False,
) -> dict[str, Any]:
	def _impl() -> dict[str, Any]:
		types = output_types
		if isinstance(types, str):
			types = [x.strip() for x in types.split(",") if x.strip()]
		generated: list[dict[str, Any]] = []
		for ot in (types or []):
			doc = _generate_for_type(instance_name, ot, source_addendum_code=source_addendum_code)
			if _as_bool(publish_outputs):
				doc = StdInstanceGeneratedOutputService.publish_output(doc.name)
			generated.append(
				{
					"output_code": doc.name,
					"output_type": doc.output_type,
					"output_status": doc.output_status,
				}
			)
		return _ok("STD_OUTPUTS_GENERATED", _("STD outputs generated."), outputs=generated, instance=instance_name)

	return _run_api(_impl)


@frappe.whitelist()
def evaluate_readiness(instance_name: str, persist: bool = True) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_READINESS_EVALUATED",
			_("Readiness evaluated."),
			result=StdInstanceReadinessService.evaluate(instance_name, persist=_as_bool(persist, default=True)),
		)
	)


@frappe.whitelist()
def lock_publication(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_PUBLICATION_LOCKED",
			_("Publication lock applied."),
			instance=_instance_payload(StdPublicationLockService.lock_for_publication(instance_name)),
		)
	)


@frappe.whitelist()
def create_publication_snapshot(instance_name: str, snapshot_reason: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_PUBLICATION_SNAPSHOT_CREATED",
			_("Publication snapshot created."),
			snapshot=StdInstanceSnapshotService.create_publication_snapshot(instance_name, snapshot_reason).name,
			instance=instance_name,
		)
	)


@frappe.whitelist()
def set_parameter_value(instance_name: str, parameter_code: str, value: str | None = None, source: str = "Officer Entry") -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_PARAMETER_SET",
			_("Parameter updated."),
			instance=_instance_payload(
				StdInstanceParameterService.set_parameter_value(
					instance_name,
					parameter_code,
					value,
					source=source,
				)
			),
		)
	)


@frappe.whitelist()
def attach_file_to_section(instance_name: str, section_code: str, file_name: str, file_reference: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_ATTACHMENT_ADDED",
			_("Attachment saved."),
			instance=_instance_payload(
				StdInstanceAttachmentService.attach_file_to_section(
					instance_name,
					section_code,
					file_name,
					file_reference,
				)
			),
		)
	)


@frappe.whitelist()
def set_works_requirement(instance_name: str, component_code: str, structured_text: str | None = None) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_WORKS_REQUIREMENT_SET",
			_("Works requirement updated."),
			instance=_instance_payload(
				StdInstanceWorksRequirementService.set_works_requirement(
					instance_name,
					component_code,
					structured_text=structured_text,
				)
			),
		)
	)


@frappe.whitelist()
def create_boq(instance_name: str, currency: str = "USD", boq_definition_code: str = "DEFAULT") -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_BOQ_CREATED",
			_("BOQ created."),
			boq=StdInstanceBoqService.create_boq_for_instance(
				instance_name,
				currency=currency,
				boq_definition_code=boq_definition_code,
			).name,
			instance=instance_name,
		)
	)


@frappe.whitelist()
def publish_output(output_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_OUTPUT_PUBLISHED",
			_("Output published."),
			output=StdInstanceGeneratedOutputService.publish_output(output_name).name,
		)
	)


@frappe.whitelist()
def analyse_addendum_impact(instance_name: str, change_types: list[str] | str) -> dict[str, Any]:
	def _impl() -> dict[str, Any]:
		cts = change_types
		if isinstance(cts, str):
			cts = [x.strip() for x in cts.split(",") if x.strip()]
		return _ok(
			"STD_ADDENDUM_IMPACT_ANALYSED",
			_("Addendum impact analysed."),
			result=StdAddendumImpactService.analyse_impact(instance_name, cts or []),
		)

	return _run_api(_impl)


@frappe.whitelist()
def create_regeneration_plan(
	instance_name: str,
	change_types: list[str] | str,
	execute: bool = False,
	publish_outputs: bool = True,
) -> dict[str, Any]:
	def _impl() -> dict[str, Any]:
		cts = change_types
		if isinstance(cts, str):
			cts = [x.strip() for x in cts.split(",") if x.strip()]
		return _ok(
			"STD_REGEN_PLAN_CREATED",
			_("Regeneration plan created."),
			result=StdAddendumImpactService.create_regeneration_plan(
				instance_name,
				cts or [],
				execute=_as_bool(execute),
				publish_outputs=_as_bool(publish_outputs, default=True),
			),
		)

	return _run_api(_impl)


@frappe.whitelist()
def get_current_outputs(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_CURRENT_OUTPUTS_FETCHED",
			_("Current outputs fetched."),
			result=StdDownstreamConsumptionService.get_current_outputs(instance_name),
		)
	)


@frappe.whitelist()
def validate_parameter_values(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_PARAMETERS_VALIDATED",
			_("Parameters validated."),
			result=StdInstanceParameterService.validate_parameter_values(instance_name),
		)
	)


@frappe.whitelist()
def lock_parameter_values(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_PARAMETERS_LOCKED",
			_("Parameters locked."),
			instance=_instance_payload(StdInstanceParameterService.lock_parameter_values(instance_name)),
		)
	)


@frappe.whitelist()
def replace_attachment_through_addendum(
	instance_name: str,
	attachment_code: str,
	file_name: str,
	file_reference: str,
	source_addendum_code: str,
) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_ATTACHMENT_REPLACED",
			_("Attachment replaced through addendum."),
			instance=_instance_payload(
				StdInstanceAttachmentService.replace_attachment_through_addendum(
					instance_name,
					attachment_code,
					file_name=file_name,
					file_reference=file_reference,
					source_addendum_code=source_addendum_code,
				)
			),
		)
	)


@frappe.whitelist()
def validate_attachment_requirements(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_ATTACHMENTS_VALIDATED",
			_("Attachment requirements validated."),
			result=StdInstanceAttachmentService.validate_attachment_requirements(instance_name),
		)
	)


@frappe.whitelist()
def validate_works_requirements(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_WORKS_REQUIREMENTS_VALIDATED",
			_("Works requirements validated."),
			result=StdInstanceWorksRequirementService.validate_works_requirements(instance_name),
		)
	)


@frappe.whitelist()
def lock_for_approval(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_APPROVAL_LOCKED",
			_("Approval lock applied."),
			instance=_instance_payload(StdPublicationLockService.lock_for_approval(instance_name)),
		)
	)


@frappe.whitelist()
def create_configuration_snapshot(instance_name: str, snapshot_reason: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_CONFIGURATION_SNAPSHOT_CREATED",
			_("Configuration snapshot created."),
			snapshot=StdInstanceSnapshotService.create_configuration_snapshot(instance_name, snapshot_reason).name,
			instance=instance_name,
		)
	)


@frappe.whitelist()
def mark_output_stale(instance_name: str, output_type: str | None = None, output_code: str | None = None) -> dict[str, Any]:
	return _run_api(
		lambda: (
			StdInstanceGeneratedOutputService.mark_output_stale(
				instance_name,
				output_type=output_type,
				output_code=output_code,
			),
			_ok("STD_OUTPUT_MARKED_STALE", _("Output marked stale."), instance=instance_name),
		)[1]
	)


@frappe.whitelist()
def get_current_dsm(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok("STD_CURRENT_DSM_FETCHED", _("Current DSM fetched."), result=StdDownstreamConsumptionService.get_current_dsm(instance_name))
	)


@frappe.whitelist()
def get_current_dom(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok("STD_CURRENT_DOM_FETCHED", _("Current DOM fetched."), result=StdDownstreamConsumptionService.get_current_dom(instance_name))
	)


@frappe.whitelist()
def get_current_dem(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok("STD_CURRENT_DEM_FETCHED", _("Current DEM fetched."), result=StdDownstreamConsumptionService.get_current_dem(instance_name))
	)


@frappe.whitelist()
def get_current_dcm(instance_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok("STD_CURRENT_DCM_FETCHED", _("Current DCM fetched."), result=StdDownstreamConsumptionService.get_current_dcm(instance_name))
	)


@frappe.whitelist()
def add_boq_bill(boq_name: str, bill_number: str, bill_title: str, bill_type: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_BOQ_BILL_ADDED",
			_("BOQ bill added."),
			boq=StdInstanceBoqService.add_bill(boq_name, bill_number, bill_title, bill_type).name,
		)
	)


@frappe.whitelist()
def add_boq_item(
	boq_name: str,
	bill_instance_code: str,
	item_number: str,
	description: str,
	unit: str,
	quantity: float,
) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_BOQ_ITEM_ADDED",
			_("BOQ item added."),
			boq=StdInstanceBoqService.add_item(
				boq_name,
				bill_instance_code,
				item_number,
				description,
				unit,
				quantity,
			).name,
		)
	)


@frappe.whitelist()
def validate_boq(boq_name: str) -> dict[str, Any]:
	return _run_api(
		lambda: _ok(
			"STD_BOQ_VALIDATED",
			_("BOQ validated."),
			result=StdInstanceBoqService.validate_boq(boq_name),
		)
	)
