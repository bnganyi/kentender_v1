# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Readiness evaluation — ``StdInstanceReadinessService``; blockers for publication.

STDINST-0700.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.attachment import (
	StdInstanceAttachmentService,
)
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	StdInstanceParameterService,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_READINESS_EVALUATED,
)

BLOCKER_MESSAGES: dict[str, str] = {
	"TEMPLATE_OR_PROFILE_MISSING": "Template/profile binding is incomplete.",
	"PARAMETERS_INCOMPLETE": "Required parameter values are incomplete or invalid.",
	"WORKS_REQUIREMENTS_INCOMPLETE": "Works requirements are incomplete.",
	"REQUIRED_ATTACHMENTS_INCOMPLETE": "Required attachments are incomplete.",
	"BOQ_MISSING": "BOQ must exist before publication readiness can pass.",
	"BOQ_INVALID": "BOQ is invalid and must be corrected.",
	"BUNDLE_MISSING": "Bundle output must exist and be current.",
	"DSM_MISSING": "DSM output must exist and be current.",
	"DOM_MISSING": "DOM output must exist and be current.",
	"DEM_MISSING": "DEM output must exist and be current.",
	"DCM_MISSING": "DCM output must exist and be current.",
	"STALE_OUTPUTS_PRESENT": "Stale outputs are present and must be regenerated.",
	"UNRESOLVED_BLOCKERS": "Unresolved readiness blockers remain.",
}

OUTPUT_TYPE_TO_BLOCKER_CODE: dict[str, str] = {
	"Bundle": "BUNDLE_MISSING",
	"DSM": "DSM_MISSING",
	"DOM": "DOM_MISSING",
	"DEM": "DEM_MISSING",
	"DCM": "DCM_MISSING",
}

VALID_CURRENT_OUTPUT_STATUSES: frozenset[str] = frozenset({"Published", "Current"})

BLOCKER_ORDER: tuple[str, ...] = (
	"TEMPLATE_OR_PROFILE_MISSING",
	"PARAMETERS_INCOMPLETE",
	"WORKS_REQUIREMENTS_INCOMPLETE",
	"REQUIRED_ATTACHMENTS_INCOMPLETE",
	"BOQ_MISSING",
	"BOQ_INVALID",
	"BUNDLE_MISSING",
	"DSM_MISSING",
	"DOM_MISSING",
	"DEM_MISSING",
	"DCM_MISSING",
	"STALE_OUTPUTS_PRESENT",
	"UNRESOLVED_BLOCKERS",
)


def _blocker(code: str, message: str | None = None) -> dict[str, str]:
	return {"code": code, "message": message or BLOCKER_MESSAGES.get(code, code)}


class StdInstanceReadinessService:
	"""Evaluate whether a ``Tender STD Instance`` is publishable."""

	@staticmethod
	def evaluate(
		instance_name: str,
		*,
		persist: bool = True,
		emit_audit: bool = True,
	) -> dict[str, Any]:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		blockers: list[dict[str, str]] = []
		warnings: list[dict[str, str]] = []

		if not (doc.template_version_code or "").strip() or not (doc.applicability_profile_code or "").strip():
			blockers.append(_blocker("TEMPLATE_OR_PROFILE_MISSING"))

		params = StdInstanceParameterService.validate_parameter_values(instance_name)
		if not params.get("ok", False):
			blockers.append(_blocker("PARAMETERS_INCOMPLETE"))

		works = StdInstanceWorksRequirementService.validate_works_requirements(instance_name)
		if not works.get("ok", False):
			blockers.append(_blocker("WORKS_REQUIREMENTS_INCOMPLETE"))

		attach = StdInstanceAttachmentService.validate_attachment_requirements(instance_name)
		works_attachment_blocking = bool(works.get("blocking"))
		if not attach.get("ok", False) or works_attachment_blocking:
			blockers.append(_blocker("REQUIRED_ATTACHMENTS_INCOMPLETE"))

		boq_doc = get_boq_for_instance(instance_name)
		if not boq_doc:
			blockers.append(_blocker("BOQ_MISSING"))
		else:
			boq_result = StdInstanceBoqService.validate_boq(boq_doc.name)
			if not boq_result.get("ok", False):
				blockers.append(_blocker("BOQ_INVALID"))

		for output_type in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
			field = OUTPUT_KEY_TO_PARENT_FIELD[output_type]
			output_name = (doc.get(field) or "").strip()
			if not output_name:
				blockers.append(_blocker(OUTPUT_TYPE_TO_BLOCKER_CODE[output_type]))
				continue
			if not frappe.db.exists("Tender STD Generated Output", output_name):
				blockers.append(_blocker(OUTPUT_TYPE_TO_BLOCKER_CODE[output_type]))
				continue
			status = (frappe.db.get_value("Tender STD Generated Output", output_name, "output_status") or "").strip()
			if status not in VALID_CURRENT_OUTPUT_STATUSES:
				blockers.append(_blocker(OUTPUT_TYPE_TO_BLOCKER_CODE[output_type]))

		stale_flags = parse_outputs_stale_flags(doc)
		if stale_flags:
			blockers.append(_blocker("STALE_OUTPUTS_PRESENT", _("Stale outputs present: {0}").format(", ".join(stale_flags))))

		if blockers:
			blockers.append(_blocker("UNRESOLVED_BLOCKERS"))

		ordered: list[dict[str, str]] = []
		for code in BLOCKER_ORDER:
			for item in blockers:
				if item["code"] == code:
					ordered.append(item)

		status = "Ready" if not ordered else "Blocked"

		if persist:
			doc.readiness_status = status
			doc.save(ignore_permissions=True)

		if emit_audit:
			emit_std_instance_event(
				EVT_STDINST_READINESS_EVALUATED,
				instance_code=instance_name,
				details={
					"status": status,
					"blocker_codes": [x["code"] for x in ordered],
					"persisted": bool(persist),
				},
			)
		return {
			"status": status,
			"blockers": ordered,
			"warnings": warnings,
			"instance": instance_name,
		}

	@staticmethod
	def is_ready(instance_name: str, *, persist: bool = True) -> bool:
		return StdInstanceReadinessService.evaluate(instance_name, persist=persist)["status"] == "Ready"

	@staticmethod
	def evaluate_and_blockers(instance_name: str, *, persist: bool = True) -> tuple[str, list[dict[str, str]]]:
		out = StdInstanceReadinessService.evaluate(instance_name, persist=persist)
		return out["status"], out["blockers"]
