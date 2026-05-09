# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0600 — Works publication readiness (pack-shaped API).

``run_works_readiness`` composes Works completion validators with
``StdInstanceReadinessService.evaluate`` (computation only; merged ``readiness_status``
and ``EVT_STDINST_READINESS_EVALUATED`` when ``persist=True``). Outward blocker codes follow the workstream-4 pack where they
differ from STD (e.g. ``STALE_OUTPUTS_PRESENT`` → ``OUTPUT_STALE``,
``BUNDLE_MISSING`` → ``BUNDLE_NOT_GENERATED``).

STD evaluate also emits ``UNRESOLVED_BLOCKERS`` as a trailing aggregate; it is **not** copied into this API’s blocker list (final ``Blocked``/``Ready`` follows the merged concrete codes).

When Works completion context is invalid, STD readiness is not run (avoids
``PARAMETERS_INCOMPLETE`` on non-Works bindings); nothing is persisted for that path.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_READINESS_BLOCKED,
	WORKS_READINESS_RUN,
	emit_works_completion_audit,
)
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_READINESS_EVALUATED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	WorksEvaluationOptionsService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

_INCOMPLETE_CONTEXT_CODES: frozenset[str] = frozenset(
	{
		"WORKS_CATEGORY_INVALID",
		"WORKS_BOQ_REQUIRED_BY_PROFILE",
	}
)

# STD readiness codes → pack-facing codes (outward API).
_STD_TO_PACK_BLOCKER_CODE: dict[str, str] = {
	"BUNDLE_MISSING": "BUNDLE_NOT_GENERATED",
	"DSM_MISSING": "DSM_NOT_GENERATED",
	"DOM_MISSING": "DOM_NOT_GENERATED",
	"DEM_MISSING": "DEM_NOT_GENERATED",
	"DCM_MISSING": "DCM_NOT_GENERATED",
	"STALE_OUTPUTS_PRESENT": "OUTPUT_STALE",
}

_WORKS_READINESS_BLOCKER_ORDER: tuple[str, ...] = (
	"WORKS_INSTANCE_NOT_FOUND",
	"WORKS_INSTANCE_NOT_TENDER_BOUND",
	"WORKS_CATEGORY_INVALID",
	"WORKS_BOQ_REQUIRED_BY_PROFILE",
	"WORKS_PROFILE_INVALID",
	"WORKS_TEMPLATE_LINEAGE_MISSING",
	"WORKS_INSTANCE_LOCKED",
	"TDS_SUBMISSION_DEADLINE_MISSING",
	"TDS_OPENING_DATETIME_MISSING",
	"TDS_OPENING_DATETIME_INVALID",
	"TDS_CLARIFICATION_DEADLINE_INVALID",
	"TDS_BID_VALIDITY_INVALID",
	"TENDER_SECURITY_AMOUNT_MISSING",
	"TENDER_SECURITY_CURRENCY_MISSING",
	"TDS_SITE_VISIT_DETAILS_MISSING",
	"WORKS_SPECIFICATIONS_MISSING",
	"DRAWING_REGISTER_MISSING",
	"DRAWING_FILE_MISSING",
	"DRAWING_SECTION_INVALID",
	"DRAWING_REVISION_MISSING",
	"DRAWING_DUPLICATE_REVISION",
	"TEMPLATE_OR_PROFILE_MISSING",
	"PARAMETERS_INCOMPLETE",
	"WORKS_REQUIREMENTS_INCOMPLETE",
	"REQUIRED_ATTACHMENTS_INCOMPLETE",
	"BOQ_MISSING",
	"BOQ_CURRENCY_MISSING",
	"BOQ_BILL_EMPTY",
	"BOQ_ITEM_DESCRIPTION_MISSING",
	"BOQ_ITEM_UNIT_MISSING",
	"BOQ_ITEM_QUANTITY_MISSING",
	"BOQ_ITEM_QUANTITY_INVALID",
	"BOQ_DUPLICATE_ITEM_NUMBER",
	"BOQ_PROHIBITED_FIELDS",
	"BOQ_INVALID",
	"SCC_COMPLETION_PERIOD_MISSING",
	"SCC_DEFECTS_LIABILITY_MISSING",
	"SCC_PERFORMANCE_SECURITY_MISSING",
	"SCC_LD_CAP_INVALID",
	"SCC_PAYMENT_CURRENCY_MISSING",
	"SCC_INSURANCE_MISSING",
	"BUNDLE_NOT_GENERATED",
	"DSM_NOT_GENERATED",
	"DOM_NOT_GENERATED",
	"DEM_NOT_GENERATED",
	"DCM_NOT_GENERATED",
	"BUNDLE_RENDER_FAILED",
	"OUTPUT_STALE",
	"UNRESOLVED_BLOCKERS",
)


def _default_resolution(code: str) -> str:
	return _("Review and correct the issue for code {0}.").format(code)


_WORKS_READINESS_BLOCKER_META: dict[str, dict[str, str]] = {
	"WORKS_INSTANCE_NOT_FOUND": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Open or create a valid Tender STD Instance for this tender."),
	},
	"WORKS_INSTANCE_NOT_TENDER_BOUND": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Bind the STD Instance to a procurement tender."),
	},
	"WORKS_CATEGORY_INVALID": {
		"severity": SEVERITY_HIGH,
		"resolution_action": _("Use a Works-category STD instance for Works readiness."),
	},
	"WORKS_BOQ_REQUIRED_BY_PROFILE": {
		"severity": SEVERITY_HIGH,
		"resolution_action": _("Align procurement category with tender configuration."),
	},
	"WORKS_PROFILE_INVALID": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Set template version and applicability profile on the instance."),
	},
	"WORKS_TEMPLATE_LINEAGE_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Align tender STD template with the instance binding."),
	},
	"WORKS_INSTANCE_LOCKED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Return the instance to an editable status or use addendum flow."),
	},
	"TDS_SUBMISSION_DEADLINE_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Complete Tender Data Sheet submission deadline."),
	},
	"TDS_OPENING_DATETIME_INVALID": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Set opening after submission deadline."),
	},
	"TENDER_SECURITY_AMOUNT_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Provide tender security amount when security is required."),
	},
	"WORKS_SPECIFICATIONS_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Complete required Works specifications."),
	},
	"DRAWING_REGISTER_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Add at least one Section VII drawing to the register."),
	},
	"BOQ_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Complete the Bills of Quantities."),
	},
	"BOQ_INVALID": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Correct BOQ structure and line items."),
	},
	"BUNDLE_NOT_GENERATED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Generate and publish the Bundle output."),
	},
	"DSM_NOT_GENERATED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Generate and publish the DSM output."),
	},
	"DOM_NOT_GENERATED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Generate and publish the DOM output."),
	},
	"DEM_NOT_GENERATED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Generate and publish the DEM output."),
	},
	"DCM_NOT_GENERATED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Generate and publish the DCM output."),
	},
	"OUTPUT_STALE": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Regenerate affected outputs after configuration changes."),
	},
	"BUNDLE_RENDER_FAILED": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Investigate failed generation job and regenerate outputs."),
	},
	"TEMPLATE_OR_PROFILE_MISSING": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Bind template version and profile on the STD instance."),
	},
	"PARAMETERS_INCOMPLETE": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Complete required STD parameter values."),
	},
	"WORKS_REQUIREMENTS_INCOMPLETE": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Complete Works requirements rows."),
	},
	"REQUIRED_ATTACHMENTS_INCOMPLETE": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Attach required supplier-facing files with section binding."),
	},
	"UNRESOLVED_BLOCKERS": {
		"severity": SEVERITY_CRITICAL,
		"resolution_action": _("Resolve all readiness blockers above."),
	},
}


def _meta_for(code: str) -> dict[str, str]:
	row = _WORKS_READINESS_BLOCKER_META.get(code) or {}
	return {
		"severity": row.get("severity") or SEVERITY_CRITICAL,
		"resolution_action": row.get("resolution_action") or _default_resolution(code),
	}


def _enrich_pack_blocker(code: str, message: str) -> dict[str, Any]:
	meta = _meta_for(code)
	return {
		"code": code,
		"severity": meta["severity"],
		"message": message,
		"resolution_action": meta["resolution_action"],
	}


def _normalize_std_blocker(item: dict[str, str]) -> dict[str, Any]:
	raw_code = (item.get("code") or "").strip()
	pack_code = _STD_TO_PACK_BLOCKER_CODE.get(raw_code, raw_code)
	msg = (item.get("message") or "").strip() or pack_code
	return _enrich_pack_blocker(pack_code, msg)


def _collect_works_validator_blockers(instance_code: str) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for fn in (
		WorksTdsCompletionService.validate_tds_values,
		WorksBoqCompletionService.validate_boq,
		WorksSccCompletionService.validate_scc_values,
		WorksDrawingRegisterService.validate_drawing_register,
		WorksEvaluationOptionsService.validate_evaluation_options,
		WorksRequirementsCompletionService.validate_works_requirements,
	):
		res = fn(instance_code)
		for b in res.get("blockers") or []:
			code = (b.get("code") or "").strip()
			if not code:
				continue
			msg = (b.get("message") or "").strip() or code
			sev = (b.get("severity") or SEVERITY_CRITICAL).strip()
			meta = _meta_for(code)
			if sev == SEVERITY_HIGH or meta["severity"] == SEVERITY_HIGH:
				sev = SEVERITY_HIGH
			else:
				sev = SEVERITY_CRITICAL
			out.append(
				{
					"code": code,
					"severity": sev,
					"message": msg,
					"resolution_action": meta["resolution_action"],
				}
			)
	return out


def _failed_render_blockers(instance_code: str) -> list[dict[str, Any]]:
	doc = frappe.get_doc("Tender STD Instance", instance_code)
	failed_types: list[str] = []
	for logical, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
		name = (doc.get(field) or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			continue
		st = (frappe.db.get_value("Tender STD Generated Output", name, "output_status") or "").strip()
		if st == "Failed":
			failed_types.append(logical)
	if not failed_types:
		return []
	meta = _meta_for("BUNDLE_RENDER_FAILED")
	types_s = ", ".join(sorted(failed_types))
	return [
		{
			"code": "BUNDLE_RENDER_FAILED",
			"severity": meta["severity"],
			"message": _("Generated output(s) in Failed status: {0}").format(types_s),
			"resolution_action": meta["resolution_action"],
		}
	]


def _sort_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
	order_index = {c: i for i, c in enumerate(_WORKS_READINESS_BLOCKER_ORDER)}

	def sort_key(b: dict[str, Any]) -> tuple[int, str]:
		c = (b.get("code") or "").strip()
		return (order_index.get(c, len(_WORKS_READINESS_BLOCKER_ORDER)), c)

	return sorted(blockers, key=sort_key)


def _dedupe_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
	seen: set[str] = set()
	out: list[dict[str, Any]] = []
	for b in blockers:
		c = (b.get("code") or "").strip()
		if not c or c in seen:
			continue
		seen.add(c)
		out.append(b)
	return out


def _context_top_level_status(ctx_blockers: list[dict[str, str]]) -> str:
	codes = {(b.get("code") or "").strip() for b in ctx_blockers}
	if codes and codes <= _INCOMPLETE_CONTEXT_CODES:
		return "Incomplete"
	return "Blocked"


def _emit_works_readiness_audit_events(
	instance_code: str,
	status: str,
	blockers: list[dict[str, Any]],
	*,
	persist: bool,
	performed_by: str | None,
) -> None:
	"""WORKS-COMP-0900 — every run logs ``WORKS_READINESS_RUN``; ``Blocked`` also logs ``WORKS_READINESS_BLOCKED``."""
	codes = [str(x.get("code") or "") for x in blockers]
	details: dict[str, Any] = {
		"status": status,
		"blocker_codes": codes,
		"persist": persist,
	}
	emit_works_completion_audit(
		WORKS_READINESS_RUN,
		instance_code,
		details=details,
		performed_by=performed_by,
	)
	if (status or "").strip() == "Blocked":
		emit_works_completion_audit(
			WORKS_READINESS_BLOCKED,
			instance_code,
			details=details,
			performed_by=performed_by,
		)


class WorksReadinessService:
	"""Pack §16 readiness — composed checks with STD persistence/audit."""

	@staticmethod
	def run_works_readiness(
		instance_code: str,
		actor: str | None = None,
		*,
		persist: bool = True,
	) -> dict[str, Any]:
		"""Return pack-shaped readiness result for a Works STD instance.

		:param persist: when context is valid, save ``readiness_status`` to the merged pack result and emit
			``EVT_STDINST_READINESS_EVALUATED`` once (STD evaluate runs with ``persist=False``, ``emit_audit=False``).
		"""
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			audit_user = act or frappe.session.user
			if not code:
				bl = [
					_enrich_pack_blocker("WORKS_INSTANCE_NOT_FOUND", str(_("Instance code is required.")))
				]
				_emit_works_readiness_audit_events(
					"",
					"Blocked",
					bl,
					persist=persist,
					performed_by=audit_user,
				)
				return {
					"status": "Blocked",
					"instance_code": "",
					"blockers": bl,
					"warnings": [],
				}

			ctx = validate_works_completion_context(code)
			if not ctx.get("valid"):
				ctx_blockers = list(ctx.get("blockers") or [])
				st = _context_top_level_status(ctx_blockers)
				blockers = [
					_enrich_pack_blocker(
						(b.get("code") or "").strip(),
						(b.get("message") or "").strip() or (b.get("code") or "").strip(),
					)
					for b in ctx_blockers
					if (b.get("code") or "").strip()
				]
				sorted_bl = _sort_blockers(blockers)
				_emit_works_readiness_audit_events(
					code,
					st,
					sorted_bl,
					persist=persist,
					performed_by=audit_user,
				)
				return {
					"status": st,
					"instance_code": code,
					"blockers": sorted_bl,
					"warnings": [],
				}

			merged: list[dict[str, Any]] = []
			merged.extend(_collect_works_validator_blockers(code))

			std_res = StdInstanceReadinessService.evaluate(
				code,
				persist=False,
				emit_audit=False,
			)
			tds_ok = bool(WorksTdsCompletionService.validate_tds_values(code).get("valid"))
			wr_ok = bool(WorksRequirementsCompletionService.validate_works_requirements(code).get("valid"))
			for item in std_res.get("blockers") or []:
				raw = (item.get("code") or "").strip()
				# Synthetic aggregate from STD evaluate — final Blocked/Ready uses merged list.
				if raw == "UNRESOLVED_BLOCKERS":
					continue
				if raw == "PARAMETERS_INCOMPLETE" and tds_ok:
					continue
				if raw == "WORKS_REQUIREMENTS_INCOMPLETE" and wr_ok:
					continue
				merged.append(_normalize_std_blocker(item))

			merged.extend(_failed_render_blockers(code))

			merged = _dedupe_blockers(merged)
			merged = _sort_blockers(merged)

			top = "Ready" if not merged else "Blocked"

			if persist:
				inst_doc = frappe.get_doc("Tender STD Instance", code)
				inst_doc.readiness_status = top
				inst_doc.save(ignore_permissions=True)

			if persist:
				emit_std_instance_event(
					EVT_STDINST_READINESS_EVALUATED,
					instance_code=code,
					details={
						"status": top,
						"blocker_codes": [str(x.get("code") or "") for x in merged],
						"persisted": True,
						"works_readiness": True,
					},
				)

			_emit_works_readiness_audit_events(
				code,
				top,
				merged,
				persist=persist,
				performed_by=audit_user,
			)

			return {
				"status": top,
				"instance_code": code,
				"blockers": merged,
				"warnings": list(std_res.get("warnings") or []),
			}
		finally:
			frappe.set_user(prev_user)
