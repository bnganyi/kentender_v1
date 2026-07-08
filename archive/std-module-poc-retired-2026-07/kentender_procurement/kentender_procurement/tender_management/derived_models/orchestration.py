# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0700 — ``DerivedModelGenerationService`` (pack §13).

Canonical orchestration for Bundle → DSM → DOM → DEM → DCM. Maps pack names::

	generateAll → generate_all
	generateOutput → generate_output
	validateGeneratedOutput → validate_generated_output

``WorksOutputGenerationService`` delegates here with ``publish=True`` and
``rollback_on_failure=True`` to preserve WORKS-COMP-0500 transactional cleanup.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.derived_models.events.audit import (
	emit_derived_model_audit,
)
from kentender_procurement.tender_management.derived_models.events.codes import (
	DERIVED_MODEL_GENERATION_REQUESTED,
)
from kentender_procurement.tender_management.derived_models.common.source_trace import (
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.common.versioning import (
	DerivedOutputVersioningService,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import OUTPUT_KEY_TO_PARENT_FIELD
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_OUTPUTS_GENERATED,
	emit_works_completion_audit,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

DERIVED_MODEL_GENERATION_TITLE = "Derived Model Generation"

DERIVED_ORCHESTRATION_JOB = "DERIVED-0700"

_OUTPUT_ORDER: tuple[tuple[str, Callable[..., Document]], ...] = (
	("Bundle", StdInstanceGeneratedOutputService.generate_bundle),
	("DSM", StdInstanceGeneratedOutputService.generate_dsm),
	("DOM", StdInstanceGeneratedOutputService.generate_dom),
	("DEM", StdInstanceGeneratedOutputService.generate_dem),
	("DCM", StdInstanceGeneratedOutputService.generate_dcm),
)

_GEN_BY_LABEL: dict[str, Callable[..., Document]] = {k: v for k, v in _OUTPUT_ORDER}


def _resolve_actor_or_job(actor_or_job: str | None) -> tuple[str | None, str | None]:
	"""Return ``(frappe_user, job_code_hint)`` from a single pack-style string."""
	if not (actor_or_job or "").strip():
		return None, None
	raw = actor_or_job.strip()
	if frappe.db.exists("User", raw):
		return raw, None
	return None, raw


def _content_dict_from_doc(doc: Document) -> dict[str, Any]:
	raw: Any = doc.get("content_json")
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			parsed: Any = json.loads(s)
		except Exception:
			frappe.throw(_("content_json is not valid JSON."), title=_(DERIVED_MODEL_GENERATION_TITLE))
		if not isinstance(parsed, dict):
			frappe.throw(_("content_json must decode to an object."), title=_(DERIVED_MODEL_GENERATION_TITLE))
		return parsed
	frappe.throw(_("content_json must be a dict or JSON string."), title=_(DERIVED_MODEL_GENERATION_TITLE))


def _assert_instance_and_inputs(instance_code: str) -> Document:
	code = (instance_code or "").strip()
	if not code:
		frappe.throw(_("Tender STD Instance code is required."), title=_(DERIVED_MODEL_GENERATION_TITLE))
	if not frappe.db.exists("Tender STD Instance", code):
		frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)
	inst = frappe.get_doc("Tender STD Instance", code)
	if not (inst.template_version_code or "").strip() or not (inst.applicability_profile_code or "").strip():
		frappe.throw(
			_("STD Instance is missing template version or applicability profile."),
			title=_(DERIVED_MODEL_GENERATION_TITLE),
			exc=frappe.ValidationError,
		)
	return inst


def _rollback_partial_outputs(instance_code: str, outputs: dict[str, str]) -> None:
	"""Best-effort cleanup for ``rollback_on_failure`` (WORKS-COMP-0500 parity)."""
	names = {n for n in outputs.values() if n}
	if not names:
		return
	for _lbl in reversed(list(outputs.keys())):
		name = outputs.get(_lbl)
		if name and frappe.db.exists("Tender STD Generated Output", name):
			try:
				frappe.delete_doc("Tender STD Generated Output", name, force=True, ignore_permissions=True)
			except Exception:
				pass
	try:
		inst = frappe.get_doc("Tender STD Instance", instance_code)
		for _k, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
			if (inst.get(field) or "").strip() in names:
				inst.set(field, None)
		inst.save(ignore_permissions=True)
	except Exception:
		pass


def _record_failure_for_output_type(
	instance_code: str,
	output_type: str,
	exc: BaseException,
	draft_doc: Document | None,
	*,
	generated_by_job_code: str | None,
) -> None:
	err = str(exc)
	if draft_doc and frappe.db.exists("Tender STD Generated Output", draft_doc.name):
		try:
			StdInstanceGeneratedOutputService.mark_output_generation_failed(draft_doc.name, error_message=err)
			return
		except Exception:
			pass
	try:
		StdInstanceGeneratedOutputService.insert_failed_output_row(
			instance_code,
			output_type,
			error_message=err,
			generated_by_job_code=generated_by_job_code,
		)
	except Exception:
		pass


class DerivedModelGenerationService:
	"""Pack §13 orchestrator over STD derived outputs (ordered generators + versioning)."""

	@staticmethod
	def generate_all(
		instance_code: str,
		actor_or_job: str | None = None,
		*,
		publish: bool = False,
		rollback_on_failure: bool = False,
		run_works_prechecks: bool = False,
		generated_by_job_code: str | None = None,
	) -> dict[str, Any]:
		"""Generate all five outputs in order; default path is Draft → Current (pack §13).

		:param actor_or_job: If this matches a Frappe ``User`` name, session switches for the call;
			otherwise it is treated as ``generated_by_job_code`` for new rows (unless ``generated_by_job_code`` is set).
		:param publish: When ``True``, each output is published after marking Current (instance pointers updated).
		:param rollback_on_failure: When ``True``, delete successful rows and clear pointers on any failure
			(used by Works output generation).
		:param run_works_prechecks: When ``True``, run ``WorksOutputGenerationService.assert_prechecks`` first.
		"""
		inst = _assert_instance_and_inputs(instance_code)
		code = inst.name

		user_hint, job_from_actor = _resolve_actor_or_job(actor_or_job)
		job_code = (generated_by_job_code or "").strip() or (job_from_actor or "").strip() or None

		prev_user = frappe.session.user
		if user_hint:
			frappe.set_user(user_hint)

		emit_derived_model_audit(
			DERIVED_MODEL_GENERATION_REQUESTED,
			instance_code=code,
			actor_or_job=job_code or user_hint,
			extra={
				"scope": "all",
				"output_types": [lbl for lbl, _fn in _OUTPUT_ORDER],
				"publish": bool(publish),
			},
		)

		outputs: dict[str, str] = {}
		draft_doc: Document | None = None
		last_label: str | None = None
		try:
			if run_works_prechecks:
				from kentender_procurement.tender_management.works_completion.services.output_generation import (
					WorksOutputGenerationService,
				)

				WorksOutputGenerationService.assert_prechecks(code)

			for label, gen_fn in _OUTPUT_ORDER:
				last_label = label
				draft_doc = None
				draft_doc = (
					gen_fn(code, generated_by_job_code=job_code)
					if job_code
					else gen_fn(code)
				)
				payload = _content_dict_from_doc(draft_doc)
				validate_derived_output_source_traces(label, payload)
				DerivedOutputVersioningService.markCurrent(draft_doc.name)
				final_name = draft_doc.name
				if publish:
					pub = StdInstanceGeneratedOutputService.publish_output(draft_doc.name)
					final_name = pub.name
				outputs[label] = final_name

			result: dict[str, Any] = {"ok": True, "outputs": outputs, "published": bool(publish)}
			if publish:
				all_labels = [label for label, _fn in _OUTPUT_ORDER]
				emit_works_completion_audit(
					WORKS_OUTPUTS_GENERATED,
					code,
					affected_outputs=all_labels,
					details={"outputs": outputs, "source": "DerivedModelGenerationService"},
					performed_by=user_hint or frappe.session.user,
				)
			return result
		except Exception as exc:
			if rollback_on_failure and outputs:
				_rollback_partial_outputs(code, outputs)
			elif last_label:
				_record_failure_for_output_type(
					code,
					last_label,
					exc,
					draft_doc,
					generated_by_job_code=job_code or DERIVED_ORCHESTRATION_JOB,
				)
			raise
		finally:
			if user_hint:
				frappe.set_user(prev_user)

	@staticmethod
	def generate_output(
		instance_code: str,
		output_type: str,
		actor_or_job: str | None = None,
		*,
		publish: bool = False,
		rollback_on_failure: bool = False,
		run_works_prechecks: bool = False,
		generated_by_job_code: str | None = None,
	) -> dict[str, Any]:
		"""Generate a single output type (same lifecycle options as ``generate_all``)."""
		enforce_sec_authorization(
			action_code="GENERATE_STD_OUTPUTS",
			actor=actor_or_job or frappe.session.user,
			object_type="Tender STD Instance",
			object_code=instance_code,
			context={"object_exists": bool(frappe.db.exists("Tender STD Instance", instance_code))},
			fallback_message="Not authorized to generate STD outputs.",
		)
		inst = _assert_instance_and_inputs(instance_code)
		code = inst.name
		ot = (output_type or "").strip()
		if ot not in OUTPUT_TYPES:
			frappe.throw(_("Invalid output_type."), title=_(DERIVED_MODEL_GENERATION_TITLE))

		gen_fn = _GEN_BY_LABEL.get(ot)
		if not gen_fn:
			frappe.throw(_("Unknown generator."), title=_(DERIVED_MODEL_GENERATION_TITLE))

		user_hint, job_from_actor = _resolve_actor_or_job(actor_or_job)
		job_code = (generated_by_job_code or "").strip() or (job_from_actor or "").strip() or None

		prev_user = frappe.session.user
		if user_hint:
			frappe.set_user(user_hint)

		emit_derived_model_audit(
			DERIVED_MODEL_GENERATION_REQUESTED,
			instance_code=code,
			output_type=ot,
			actor_or_job=job_code or user_hint,
			extra={"scope": "single", "publish": bool(publish)},
		)

		draft_doc: Document | None = None
		progress: dict[str, str] = {}
		try:
			if run_works_prechecks:
				from kentender_procurement.tender_management.works_completion.services.output_generation import (
					WorksOutputGenerationService,
				)

				WorksOutputGenerationService.assert_prechecks(code)

			draft_doc = gen_fn(code, generated_by_job_code=job_code) if job_code else gen_fn(code)
			payload = _content_dict_from_doc(draft_doc)
			validate_derived_output_source_traces(ot, payload)
			DerivedOutputVersioningService.markCurrent(draft_doc.name)
			progress[ot] = draft_doc.name
			final_name = draft_doc.name
			if publish:
				pub = StdInstanceGeneratedOutputService.publish_output(draft_doc.name)
				final_name = pub.name
				progress[ot] = pub.name
			return {"ok": True, "outputs": {ot: final_name}, "published": bool(publish)}
		except Exception as exc:
			if rollback_on_failure and progress:
				_rollback_partial_outputs(code, progress)
			elif ot:
				_record_failure_for_output_type(
					code,
					ot,
					exc,
					draft_doc,
					generated_by_job_code=job_code or DERIVED_ORCHESTRATION_JOB,
				)
			raise
		finally:
			if user_hint:
				frappe.set_user(prev_user)

	@staticmethod
	def validate_generated_output(output_code: str) -> None:
		"""Re-run source-trace validation for an existing ``Tender STD Generated Output`` row (pack §13)."""
		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		doc = frappe.get_doc("Tender STD Generated Output", name)
		ot = (doc.output_type or "").strip()
		if ot not in OUTPUT_TYPES:
			frappe.throw(_("Invalid output_type on row."), title=_(DERIVED_MODEL_GENERATION_TITLE))
		payload = _content_dict_from_doc(doc)
		if not payload:
			frappe.throw(
				_("Output has no JSON content to validate."),
				title=_(DERIVED_MODEL_GENERATION_TITLE),
				exc=frappe.ValidationError,
			)
		validate_derived_output_source_traces(ot, payload)
