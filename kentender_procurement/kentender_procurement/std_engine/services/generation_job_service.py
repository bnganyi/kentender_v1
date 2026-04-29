from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.output_generators import OUTPUT_TYPES, _inst, build_output_payload
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object

_SAVEPOINT = "std_gen_job"

# Set to an output type name (e.g. "DSM") in tests to force a controlled failure after prior types succeed.
GENERATION_TEST_FAIL_AFTER_TYPE: str | None = None


def _resolve_output_types(scope: str | list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
	if scope in (None, "all"):
		return OUTPUT_TYPES
	if isinstance(scope, (list, tuple)):
		out: list[str] = []
		for s in scope:
			if s not in OUTPUT_TYPES:
				frappe.throw(_("Invalid output type in scope: {0}").format(s), title=_("STD generation"))
			out.append(s)
		return tuple(out)
	if isinstance(scope, str) and scope in OUTPUT_TYPES:
		return (scope,)
	frappe.throw(_("Invalid generation scope."), title=_("STD generation"))


def _job_type_for_scope(output_types: tuple[str, ...]) -> str:
	if len(output_types) == len(OUTPUT_TYPES):
		return "All"
	return output_types[0]


def _trigger_type(addendum_code: str | None) -> str:
	return "Addendum" if addendum_code else "Manual"


def _compute_job_input_hash(instance: frappe._dict, output_types: tuple[str, ...], addendum_code: str | None) -> str:
	payload = {
		"instance_code": _inst(instance, "instance_code"),
		"template_version_code": _inst(instance, "template_version_code"),
		"profile_code": _inst(instance, "profile_code"),
		"output_types": list(output_types),
		"addendum_code": addendum_code,
		"instance_status": _inst(instance, "instance_status"),
		"readiness_status": _inst(instance, "readiness_status"),
	}
	raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
	return hashlib.sha256(raw).hexdigest()


def _next_version_number(instance_code: str, output_type: str) -> int:
	row = frappe.db.sql(
		"SELECT MAX(version_number) FROM `tabSTD Generated Output` WHERE instance_code = %s AND output_type = %s",
		(instance_code, output_type),
	)
	if not row or row[0][0] is None:
		return 1
	return int(row[0][0]) + 1


def _supersede_current_outputs(instance_code: str, output_type: str, actor: str) -> None:
	for row in frappe.get_all(
		"STD Generated Output",
		filters={"instance_code": instance_code, "output_type": output_type, "status": "Current"},
		pluck="output_code",
	):
		res = transition_std_object("GENERATED_OUTPUT", row, "STD_OUTPUT_SUPERSEDE", actor)
		if not res.get("allowed"):
			frappe.throw(res.get("message") or "Cannot supersede prior output", title=_("STD generation"))
		record_std_audit_event(
			"OUTPUT_SUPERSEDED",
			"STD Generated Output",
			row,
			actor=actor,
			previous_state="Current",
			new_state="Superseded",
			metadata={"instance_code": instance_code, "output_type": output_type},
		)


def _fail_job(generation_job_code: str, actor: str, message: str) -> None:
	frappe.db.set_value(
		"STD Generation Job",
		{"generation_job_code": generation_job_code},
		{"error_message": message[:65000]},
		update_modified=False,
	)
	transition_std_object("GENERATION_JOB", generation_job_code, "STD_JOB_FAIL", actor)
	record_std_audit_event(
		"GENERATION_JOB_FAILED",
		"STD Generation Job",
		generation_job_code,
		actor=actor,
		new_state="Failed",
		reason=message[:140],
		metadata={"error": message[:2000]},
	)


@frappe.whitelist()
def generate_std_outputs(
	instance_code: str,
	scope: str | list[str] | tuple[str, ...] | None = "all",
	actor: str | None = None,
	addendum_code: str | None = None,
) -> dict[str, Any]:
	"""Create an auditable generation job and materialize STD Generated Output rows (0601 framework + 0602–0606 payloads)."""
	actor = actor or frappe.session.user
	name = frappe.db.get_value("STD Instance", {"instance_code": instance_code}, "name")
	if not name:
		frappe.throw(_("STD Instance not found."), title=_("STD generation"))
	instance = frappe.get_doc("STD Instance", name).as_dict()
	output_types = _resolve_output_types(scope)
	job_type = _job_type_for_scope(output_types)
	trigger_type = _trigger_type(addendum_code)
	generation_job_code = f"GJOB-{frappe.generate_hash(length=10).upper()}"

	job = frappe.get_doc(
		{
			"doctype": "STD Generation Job",
			"generation_job_code": generation_job_code,
			"instance_code": instance_code,
			"job_type": job_type,
			"trigger_type": trigger_type,
			"status": "Pending",
		}
	)
	job.insert(ignore_permissions=True)

	record_std_audit_event(
		"GENERATION_JOB_STARTED",
		"STD Generation Job",
		generation_job_code,
		actor=actor,
		new_state="Pending",
		metadata={"instance_code": instance_code, "scope": list(output_types)},
	)

	start = transition_std_object("GENERATION_JOB", generation_job_code, "STD_JOB_START", actor)
	if not start.get("allowed"):
		frappe.db.set_value(
			"STD Generation Job",
			{"generation_job_code": generation_job_code},
			{"error_message": (start.get("message") or "Job start denied")[:65000]},
			update_modified=False,
		)
		record_std_audit_event(
			"GENERATION_JOB_FAILED",
			"STD Generation Job",
			generation_job_code,
			actor=actor,
			new_state="Pending",
			reason="start_denied",
			metadata={"message": start.get("message")},
		)
		frappe.throw(start.get("message"), title=_("STD generation"))

	job_input_hash = _compute_job_input_hash(instance, output_types, addendum_code)
	frappe.db.set_value(
		"STD Generation Job",
		{"generation_job_code": generation_job_code},
		{"input_hash": job_input_hash},
		update_modified=False,
	)

	generated: list[dict[str, Any]] = []
	try:
		frappe.db.savepoint(_SAVEPOINT)
		ctx_base: dict[str, Any] = {
			"addendum_code": addendum_code,
			"job_input_hash": job_input_hash,
			"generation_job_code": generation_job_code,
		}
		for output_type in output_types:
			if GENERATION_TEST_FAIL_AFTER_TYPE and output_type == GENERATION_TEST_FAIL_AFTER_TYPE:
				raise frappe.ValidationError("Simulated generator failure")

			built = build_output_payload(output_type, instance, ctx_base)
			payload = built["payload"]
			in_hash = built.get("input_hash") or job_input_hash
			out_hash = built.get("output_hash")

			version_number = _next_version_number(instance_code, output_type)
			output_code = f"STDOUT-{frappe.generate_hash(length=10).upper()}"

			_supersede_current_outputs(instance_code, output_type, actor)

			out = frappe.get_doc(
				{
					"doctype": "STD Generated Output",
					"output_code": output_code,
					"instance_code": instance_code,
					"output_type": output_type,
					"version_number": version_number,
					"status": "Draft",
					"source_template_version_code": _inst(instance, "template_version_code"),
					"source_profile_code": _inst(instance, "profile_code"),
					"generated_by_job_code": generation_job_code,
					"output_payload": payload,
					"input_hash": in_hash,
					"output_hash": out_hash,
				}
			)
			out.insert(ignore_permissions=True)

			cur = transition_std_object("GENERATED_OUTPUT", output_code, "STD_OUTPUT_CURRENT", actor)
			if not cur.get("allowed"):
				raise frappe.ValidationError(cur.get("message") or "Cannot activate output")

			record_std_audit_event(
				"OUTPUT_GENERATED",
				"STD Generated Output",
				output_code,
				actor=actor,
				previous_state="Draft",
				new_state="Current",
				metadata={"output_type": output_type, "generation_job_code": generation_job_code},
			)
			generated.append({"output_code": output_code, "output_type": output_type, "version_number": version_number})

		frappe.db.release_savepoint(_SAVEPOINT)
	except Exception as exc:
		frappe.db.rollback(save_point=_SAVEPOINT)
		_fail_job(generation_job_code, actor, str(exc))
		raise

	done = transition_std_object("GENERATION_JOB", generation_job_code, "STD_JOB_COMPLETE", actor)
	if not done.get("allowed"):
		_fail_job(generation_job_code, actor, done.get("message") or "Job completion denied")
		frappe.throw(done.get("message"), title=_("STD generation"))

	record_std_audit_event(
		"GENERATION_JOB_COMPLETED",
		"STD Generation Job",
		generation_job_code,
		actor=actor,
		previous_state="Running",
		new_state="Completed",
		metadata={"outputs": [g["output_code"] for g in generated]},
	)

	return {
		"generation_job_code": generation_job_code,
		"input_hash": job_input_hash,
		"outputs": generated,
		"output_types": list(output_types),
	}
