# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-1000 — Frappe-whitelisted Works completion API.

Pack §20 describes conceptual REST paths under ``/api/std-engine/works/instances/{instance_code}/…``.
This bench implements **whitelisted methods** callable via ``frappe.call`` (see
``docs/prompts/std-production-readiness/admin-revamp/STD-LIB-REST-mapping.md``).

**Response envelope:** same as STDINST-1200 — ``{"ok": true|false, "code": "...", "message": "...", ...}``
(not the alternate ``success`` / ``error_code`` spellings in the prose pack).

| Conceptual pack route | Method |
|-----------------------|--------|
| GET …/completion-status | ``get_works_completion_status`` |
| PUT …/tds-values | ``save_works_tds_values`` |
| PUT …/evaluation-options | ``save_works_evaluation_options`` |
| PUT …/works-requirements | ``save_works_requirements`` |
| PUT …/drawings | ``save_works_drawings`` |
| PUT …/boq | ``save_works_boq`` |
| POST …/boq/import | ``import_works_boq`` |
| PUT …/scc-values | ``save_works_scc_values`` |
| POST …/generate-outputs | ``generate_works_outputs`` |
| POST …/readiness | ``run_works_readiness`` |
| POST …/snapshot-and-lock | ``create_works_snapshot_and_lock`` |
| POST …/return-to-preparation | ``return_works_instance_to_preparation`` |
"""

from __future__ import annotations

import re
from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.api.std_instance import _err, _ok
from kentender_procurement.tender_management.api.std_instance import _map_exc as _std_map_exc
from kentender_procurement.tender_management.std_instance.authorization import StdAuthorizationService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.completion_status import (
	get_completion_status,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	WorksEvaluationOptionsService,
)
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)
from kentender_procurement.tender_management.works_completion.services.snapshot_lock import (
	WorksSnapshotLockService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_readiness import (
	WorksReadinessService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)

_STABLE_ERR_TITLE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")


def _map_works_exc(exc: Exception) -> tuple[str, str]:
	"""Map exceptions to API codes; prefer ``ValidationError.title`` when it looks like a stable code."""
	if isinstance(exc, frappe.ValidationError):
		title_raw = getattr(exc, "title", None)
		title = (str(title_raw).strip() if title_raw else "") or ""
		if title == "STD Authorization Denied" or "Not authorized" in str(exc):
			return "STD_API_PERMISSION_DENIED", str(exc)
		if title and _STABLE_ERR_TITLE.match(title):
			return title, str(exc)
		return "STD_API_VALIDATION_FAILED", str(exc)
	return _std_map_exc(exc)


def _run_works_api(handler: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	try:
		return handler()
	except Exception as exc:
		code, msg = _map_works_exc(exc)
		if code == "STD_API_INTERNAL_ERROR":
			frappe.log_error(frappe.get_traceback(), "WORKS-COMP-1000 API failure")
		return _err(code, msg)


def _norm_instance(instance_code: str | None) -> str:
	code = (instance_code or "").strip()
	if not code:
		frappe.throw(_("Instance code is required."), title="WORKS_API_INSTANCE_REQUIRED")
	return code


def _as_bool(value: Any, *, default: bool = False) -> bool:
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_dict(val: Any, *, label: str) -> dict[str, Any]:
	if val is None:
		return {}
	if isinstance(val, dict):
		return val
	if isinstance(val, str) and val.strip():
		parsed: Any = frappe.parse_json(val)
		if isinstance(parsed, dict):
			return parsed
	frappe.throw(_("{0} must be a JSON object.").format(label), title="WORKS_API_INVALID_PAYLOAD")


def _assert_read_instance(instance_code: str) -> None:
	"""Require read on ``Tender STD Instance`` (``get_doc`` enforces DocPerm)."""
	frappe.get_doc("Tender STD Instance", instance_code)


def _assert_edit_instance(instance_code: str) -> None:
	StdAuthorizationService.assert_can_edit_draft_instance(instance_code)


@frappe.whitelist()
def get_works_completion_status(instance_code: str) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	return _run_works_api(
		lambda: (
			_assert_read_instance(code),
			_ok(
				"WORKS_COMPLETION_STATUS",
				_("Completion status fetched."),
				status=get_completion_status(code),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_tds_values(instance_code: str, tds_values: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(tds_values, label="tds_values")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_TDS_SAVED",
				_("TDS values saved."),
				result=WorksTdsCompletionService.save_tds_values(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_evaluation_options(instance_code: str, evaluation_options: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(evaluation_options, label="evaluation_options")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_EVALUATION_OPTIONS_SAVED",
				_("Evaluation options saved."),
				result=WorksEvaluationOptionsService.save_evaluation_options(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_requirements(instance_code: str, works_requirements: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(works_requirements, label="works_requirements")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_REQUIREMENTS_SAVED",
				_("Works requirements saved."),
				result=WorksRequirementsCompletionService.save_works_requirements(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_drawings(instance_code: str, drawings_payload: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(drawings_payload, label="drawings_payload")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_DRAWINGS_SAVED",
				_("Drawing register saved."),
				result=WorksDrawingRegisterService.save_drawing_register(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_boq(instance_code: str, boq_payload: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(boq_payload, label="boq_payload")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_BOQ_SAVED",
				_("BOQ saved."),
				result=WorksBoqCompletionService.save_boq(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def import_works_boq(instance_code: str, import_payload: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(import_payload, label="import_payload")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_BOQ_IMPORTED",
				_("BOQ imported."),
				result=WorksBoqCompletionService.import_boq(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def save_works_scc_values(instance_code: str, scc_values: Any = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	payload = _as_dict(scc_values, label="scc_values")
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_SCC_SAVED",
				_("SCC values saved."),
				result=WorksSccCompletionService.save_scc_values(code, payload),
			),
		)[1]
	)


@frappe.whitelist()
def generate_works_outputs(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	return _run_works_api(
		lambda: (
			StdAuthorizationService.assert_can_generate_outputs(code),
			_ok(
				"WORKS_OUTPUTS_GENERATED",
				_("Works outputs generated."),
				result=WorksOutputGenerationService.generate_all_works_outputs(code, actor=actor),
			),
		)[1]
	)


@frappe.whitelist()
def run_works_readiness(instance_code: str, persist: Any = True, actor: str | None = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	persist_b = _as_bool(persist, default=True)

	def _impl() -> dict[str, Any]:
		if persist_b:
			_assert_edit_instance(code)
		else:
			_assert_read_instance(code)
		return _ok(
			"WORKS_READINESS_RUN",
			_("Works readiness evaluated."),
			result=WorksReadinessService.run_works_readiness(code, actor=actor, persist=persist_b),
		)

	return _run_works_api(_impl)


@frappe.whitelist()
def create_works_snapshot_and_lock(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	code = _norm_instance(instance_code)
	return _run_works_api(
		lambda: (
			_assert_edit_instance(code),
			_ok(
				"WORKS_SNAPSHOT_AND_LOCK",
				_("Configuration snapshot created and instance locked for approval."),
				result=WorksSnapshotLockService.create_configuration_snapshot_and_lock(code, actor=actor),
			),
		)[1]
	)


@frappe.whitelist()
def return_works_instance_to_preparation(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	"""Return a ``Locked for Approval`` Works instance to ``In Configuration`` (pack LOCK-002)."""
	code = _norm_instance(instance_code)
	return _run_works_api(
		lambda: (
			_assert_read_instance(code),
			_ok(
				"WORKS_RETURNED_TO_PREPARATION",
				_("Instance returned to preparation."),
				result=WorksSnapshotLockService.return_to_preparation_from_approval_lock(code, actor=actor),
			),
		)[1]
	)
