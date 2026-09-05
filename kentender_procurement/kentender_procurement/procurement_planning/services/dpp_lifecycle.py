# Copyright (c) 2026, KenTender and contributors
# For license information, please see licence.txt

"""PLN-CHG-001 v1.12 §5.1 — the Departmental Procurement Plan lifecycle.

Commands (§8.2): OpenDepartmentalPlan, SaveNeedFunding (which also records the
§4.4 not-proceeding outcome), SaveDirectRequirement, RemoveDirectRequirement,
SubmitDepartmentalPlan, plus the §5.1 withdraw / reopen / create-update
transitions. Shape validation lives on the doctype controllers; completeness
(coverage, funding, intake flag, authority) is enforced here at submission.

Authority is the role-bound assignment resolved by
`planning_authorization` (D2): Author/HoD for the DPP's Organisation Unit
subtree. Intake is the `kentender_dpp_submission_open` flag on the ERPNext
Fiscal Year, read through Configuration & Governance (D8) and never written.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate, now_datetime

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	envelope,
	needs_intake,
	references,
)
from kentender_procurement.procurement_planning.services import planning_authorization as authz

ATTESTATION = (
	"I certify that this Departmental Procurement Plan contains the current "
	"procurement requirements of {department} for {financial_year}, including "
	"every current accepted Departmental Need either planned or recorded as not "
	"proceeding, and any direct departmental requirements shown. I confirm that "
	"the quantities, required-by dates, Procurement Budget Lines and indicative "
	"amounts are ready for Procurement validation and inclusion in the Annual "
	"Procurement Plan."
)

DIRECT_FIELDS = (
	"title", "description", "expected_operational_result", "quantity", "unit",
	"required_by_date", "budget_line", "indicative_amount",
)


# --- shared helpers ---------------------------------------------------------


def _root_by_scope(organisation_unit: str, fiscal_year: str):
	name = frappe.db.get_value(
		"Departmental Plan", {"fiscal_year": fiscal_year, "organisation_unit": organisation_unit}, "name"
	)
	return frappe.get_doc("Departmental Plan", name) if name else None


def _version(version_name: str):
	if not version_name or not frappe.db.exists("Departmental Plan Version", version_name):
		authz.not_found()
	return frappe.get_doc("Departmental Plan Version", version_name)


def _require_author(actor: str, root, *, submit: bool = False):
	if submit:
		return authz.require_dpp_hod(root.organisation_unit, actor)
	return authz.require_dpp_author(root.organisation_unit, actor)


def _require_mutable_current(root, version) -> None:
	if version.version_status not in ("Draft",):
		fail("PLN_DPP_STALE")
	if cstr(root.current_version) != cstr(version.name):
		fail("PLN_DPP_STALE")


def _window_open(fiscal_year: str) -> bool:
	return bool(site_configuration.get_dpp_submission_state(fiscal_year).get("open"))


def _has_any_submission(root) -> bool:
	versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root.name}, pluck="name")
	return bool(versions and frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ["in", versions]}, limit=1))


def _entries(version_name: str) -> list[Any]:
	return [
		frappe.get_doc("Departmental Plan Entry", name)
		for name in frappe.get_all(
			"Departmental Plan Entry", filters={"dpp_version": version_name}, order_by="creation asc", pluck="name"
		)
	]


def _fy_bounds(fiscal_year: str) -> tuple[Any, Any]:
	row = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	return (getdate(row.year_start_date), getdate(row.year_end_date)) if row else (None, None)


def _result(root, version=None, *, action: str = "", task: str = "", idempotent: bool = False) -> dict[str, Any]:
	return {
		"ok": True,
		"idempotent": idempotent,
		"action": action,
		"departmental_plan": root.name,
		"dpp_reference": root.dpp_reference,
		"current_state": root.current_state,
		"current_version": cstr(root.current_version),
		"current_accepted_version": cstr(root.current_accepted_version),
		"version_reference": cstr(version.version_reference) if version is not None else "",
		"record_version": int(root.record_version or 0),
		"task": task,
	}


def _new_version(root, *, number: int, based_on: str = "", returned_from: str = ""):
	return frappe.get_doc(
		{
			"doctype": "Departmental Plan Version",
			"version_reference": f"{root.dpp_reference}-V{number}",
			"departmental_plan": root.name,
			"version_number": number,
			"based_on_version": based_on or None,
			"returned_from_submission": returned_from or None,
			"version_status": "Draft",
			"record_version": 0,
			"fixture_namespace": root.fixture_namespace,
		}
	).insert(ignore_permissions=True)


def _next_version_number(root_name: str) -> int:
	rows = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root_name}, pluck="version_number")
	return max([int(n or 0) for n in rows] or [0]) + 1


def copy_entries(source_version: str, target_version, fixture_namespace: str = "") -> int:
	"""Copy every entry with its stable entry_id, funding and outcome onto a new Version."""
	count = 0
	for entry in _entries(source_version):
		frappe.get_doc(
			{
				"doctype": "Departmental Plan Entry",
				"entry_id": entry.entry_id,
				"dpp_version": target_version.name,
				"source_origin": entry.source_origin,
				"need": entry.need,
				"need_version": entry.need_version,
				"title": entry.title,
				"description": entry.description,
				"expected_operational_result": entry.expected_operational_result,
				"quantity": entry.quantity,
				"unit": entry.unit,
				"required_by_date": entry.required_by_date,
				"budget_line": entry.budget_line,
				"indicative_amount": entry.indicative_amount,
				"not_proceeding_reason": entry.not_proceeding_reason,
				"fixture_namespace": fixture_namespace or entry.fixture_namespace,
			}
		).insert(ignore_permissions=True)
		count += 1
	return count


def entry_is_complete(entry) -> bool:
	"""§5.1 — funded, or (Need-origin only) recorded as not proceeding."""
	if entry.source_origin == needs_intake.NEED_ORIGIN and cstr(entry.not_proceeding_reason).strip():
		return True
	return bool(cstr(entry.budget_line)) and flt(entry.indicative_amount) > 0


# --- §8.2 commands ----------------------------------------------------------


def open_departmental_plan(
	*,
	organisation_unit: str,
	fiscal_year: str,
	idempotency_key: str,
	user: str | None = None,
	fixture_namespace: str = "",
) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"organisation_unit": organisation_unit, "fiscal_year": fiscal_year}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not frappe.db.exists("Fiscal Year", fiscal_year) or frappe.db.get_value("Fiscal Year", fiscal_year, "disabled"):
		fail("PLN_NO_CONTEXT")
	if not frappe.db.exists("Organisation Unit", organisation_unit):
		fail("PLN_NO_CONTEXT")
	authz.require_dpp_author(organisation_unit, actor, masked=False)
	root = _root_by_scope(organisation_unit, fiscal_year)

	if root is None:
		root = frappe.get_doc(
			{
				"doctype": "Departmental Plan",
				"dpp_reference": references.dpp_reference(organisation_unit, fiscal_year),
				"fiscal_year": fiscal_year,
				"organisation_unit": organisation_unit,
				"current_state": "Draft",
				"record_version": 0,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
		version = _new_version(root, number=1)
		envelope.bump(root, current_version=version.name)
		needs_intake.refresh_draft_entries(version)
		result = _result(root, version, action="opened")
	elif root.current_state == "Withdrawn" and not root.current_accepted_version:
		if not _window_open(fiscal_year):
			fail("PLN_WINDOW_CLOSED")
		version = _new_version(root, number=_next_version_number(root.name))
		envelope.bump(root, current_version=version.name, current_state="Draft")
		needs_intake.refresh_draft_entries(version)
		result = _result(root, version, action="reopened")
	else:
		version = _version(root.current_version) if root.current_version else None
		if version is not None and version.version_status == "Draft":
			needs_intake.refresh_draft_entries(version)
		result = _result(root, version, action="reused", idempotent=True)

	envelope.record_command(
		idempotency_key=idempotency_key, command="OpenDepartmentalPlan", payload=payload, result=result,
		document_type="Departmental Plan", document_name=root.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def save_need_funding(
	*,
	dpp_version: str,
	entry_id: str,
	budget_line: str = "",
	indicative_amount: float | None = None,
	not_proceeding_reason: str = "",
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.2 `SaveNeedFunding` — Procurement Budget Line and amount on a
	Need-origin entry; or, with `not_proceeding_reason` (20–500 characters),
	the §4.4 not-proceeding outcome, which clears the funding specification."""
	actor = authz.actor(user)
	reason = cstr(not_proceeding_reason).strip()
	payload = {
		"dpp_version": dpp_version, "entry_id": entry_id, "budget_line": budget_line,
		"indicative_amount": indicative_amount, "not_proceeding_reason": reason,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)

	name = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": version.name, "entry_id": cstr(entry_id)}, "name")
	if not name:
		authz.not_found()
	entry = frappe.get_doc("Departmental Plan Entry", name)
	if entry.source_origin != needs_intake.NEED_ORIGIN:
		fail("PLN_ENTRY_INCOMPLETE", "Only a Need-origin entry takes funding details here.")
	current = needs_intake.current_accepted_version_of(entry.need, root.fiscal_year)
	if current != cstr(entry.need_version):
		fail("PLN_DPP_STALE")
	if reason:
		if not (20 <= len(reason) <= 500):
			fail("PLN_ENTRY_INCOMPLETE", "State why the department is not proceeding (20–500 characters).")
		entry.not_proceeding_reason = reason
		entry.budget_line = None
		entry.indicative_amount = 0
		action = "need_not_proceeding"
	else:
		_validate_funding(root, budget_line, indicative_amount)
		entry.budget_line = budget_line
		entry.indicative_amount = flt(indicative_amount)
		entry.not_proceeding_reason = None
		action = "need_funding_saved"
	entry.save(ignore_permissions=True)
	envelope.bump(root)
	result = _result(root, version, action=action)
	envelope.record_command(
		idempotency_key=idempotency_key, command="SaveNeedFunding", payload=payload, result=result,
		document_type="Departmental Plan Entry", document_name=entry.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def _validate_funding(root, budget_line: str, indicative_amount) -> None:
	if flt(indicative_amount) <= 0:
		fail("PLN_ENTRY_INCOMPLETE", detail={"field": "indicative_amount"})
	eligible = budget_gateway.eligible_line_ids(fiscal_year=root.fiscal_year, source_org_unit=root.organisation_unit)
	if cstr(budget_line) not in eligible:
		fail("PLN_BUDGET_LINE_INELIGIBLE", detail={"field": "budget_line"})


def save_direct_requirement(
	*,
	dpp_version: str,
	values: dict[str, Any] | str,
	entry_id: str | None = None,
	expected_record_version=None,
	idempotency_key: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(DIRECT_FIELDS)
	if unknown:
		fail("PLN_ENTRY_INCOMPLETE", f"Direct requirement input is limited to the eight defined values; unexpected: {sorted(unknown)}.")
	payload = {"dpp_version": dpp_version, "entry_id": entry_id, **{k: cstr(values.get(k)) for k in DIRECT_FIELDS}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)
	_validate_direct_values(root, values)

	if entry_id:
		name = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": version.name, "entry_id": cstr(entry_id)}, "name")
		if not name:
			authz.not_found()
		entry = frappe.get_doc("Departmental Plan Entry", name)
		if entry.source_origin != needs_intake.DIRECT_ORIGIN:
			fail("PLN_ENTRY_INCOMPLETE", "A Need-origin entry cannot be edited as a direct requirement.")
		entry.update({field: values.get(field) for field in DIRECT_FIELDS})
		entry.save(ignore_permissions=True)
		action = "direct_updated"
	else:
		entry = frappe.get_doc(
			{
				"doctype": "Departmental Plan Entry",
				"entry_id": references.entry_id(root.dpp_reference),
				"dpp_version": version.name,
				"source_origin": needs_intake.DIRECT_ORIGIN,
				"fixture_namespace": cstr(root.fixture_namespace),
				**{field: values.get(field) for field in DIRECT_FIELDS},
			}
		).insert(ignore_permissions=True)
		action = "direct_added"
	envelope.bump(root)
	result = _result(root, version, action=action)
	result["entry_id"] = entry.entry_id
	envelope.record_command(
		idempotency_key=idempotency_key, command="SaveDirectRequirement", payload=payload, result=result,
		document_type="Departmental Plan Entry", document_name=entry.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def _validate_direct_values(root, values: dict[str, Any]) -> None:
	missing = [field for field in DIRECT_FIELDS if not cstr(values.get(field)).strip()]
	if missing:
		fail("PLN_ENTRY_INCOMPLETE", f"Complete the highlighted requirement fields before submitting: {', '.join(missing)}.", {"fields": missing})
	if flt(values.get("quantity")) <= 0:
		fail("PLN_ENTRY_INCOMPLETE", "Quantity must be greater than zero.", {"field": "quantity"})
	# CFG v0.9 §4.5 — units come only from enabled ERPNext UOM records.
	if not frappe.db.get_value("UOM", cstr(values.get("unit")), "enabled"):
		fail("PLN_ENTRY_INCOMPLETE", "Select an enabled unit of measure.", {"field": "unit"})
	start, end = _fy_bounds(root.fiscal_year)
	required_by = getdate(values.get("required_by_date"))
	if not start or not (start <= required_by <= end):
		fail("PLN_ENTRY_INCOMPLETE", "Required by must fall inside the selected Financial Year.", {"field": "required_by_date"})
	_validate_funding(root, cstr(values.get("budget_line")), values.get("indicative_amount"))


def remove_direct_requirement(
	*, dpp_version: str, entry_id: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"dpp_version": dpp_version, "entry_id": entry_id}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)
	row = frappe.db.get_value(
		"Departmental Plan Entry", {"dpp_version": version.name, "entry_id": cstr(entry_id)}, ["name", "source_origin"], as_dict=True
	)
	if not row:
		authz.not_found()
	if row.source_origin != needs_intake.DIRECT_ORIGIN:
		fail("PLN_ENTRY_INCOMPLETE", "A current accepted Need cannot be omitted or locally deleted.")
	frappe.delete_doc("Departmental Plan Entry", row.name, force=True, ignore_permissions=True, delete_permanently=True)
	envelope.bump(root)
	result = _result(root, version, action="direct_removed")
	envelope.record_command(
		idempotency_key=idempotency_key, command="RemoveDirectRequirement", payload=payload, result=result,
		document_type="Departmental Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def submit_departmental_plan(
	*, dpp_version: str, certification_confirmed: bool, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"dpp_version": dpp_version, "certification_confirmed": bool(certification_confirmed)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	assignment = _require_author(actor, root, submit=True)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)
	if not certification_confirmed:
		fail("PLN_ENTRY_INCOMPLETE", "Confirm the departmental certification before submitting.")

	# §5.1 — the flag gates the first submission and a reopened root with no
	# accepted predecessor; corrections and update successors may follow after
	# the window closes. Rechecked here, inside the transaction (CFG-AC-014).
	if not _has_any_submission(root) and not _window_open(root.fiscal_year):
		fail("PLN_WINDOW_CLOSED")

	needs_intake.refresh_draft_entries(version)
	gaps = needs_intake.coverage_gaps(version)
	if gaps:
		fail("PLN_NEED_COVERAGE_INCOMPLETE", f"Add every current accepted Need to this departmental plan before submitting: {', '.join(gaps)}.")
	entries = _entries(version.name)
	if not entries:
		fail("PLN_ENTRY_INCOMPLETE", "A departmental plan with no entries cannot be submitted.")
	eligible = budget_gateway.eligible_line_ids(fiscal_year=root.fiscal_year, source_org_unit=root.organisation_unit)
	for entry in entries:
		if not entry_is_complete(entry):
			fail("PLN_ENTRY_INCOMPLETE", f"Complete the highlighted requirement fields before submitting ({entry.entry_id}).", {"entry_id": entry.entry_id})
		if cstr(entry.budget_line) and cstr(entry.budget_line) not in eligible:
			fail("PLN_BUDGET_LINE_INELIGIBLE", f"Select an Active Procurement Budget Line available to this department and Financial Year ({entry.entry_id}).", {"entry_id": entry.entry_id})

	department = cstr(frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name") or root.organisation_unit)
	attestation = ATTESTATION.format(department=department, financial_year=references.fy_label(root.fiscal_year))
	snapshots = [
		{
			"entry_id": entry.entry_id,
			"source_origin": entry.source_origin,
			"source_line_id": cstr(entry.need) or entry.entry_id,
			"need": cstr(entry.need),
			"need_version": cstr(entry.need_version),
			"title": entry.title,
			"description": entry.description,
			"expected_operational_result": entry.expected_operational_result,
			"quantity": flt(entry.quantity),
			"unit": cstr(entry.unit),
			"required_by_date": cstr(entry.required_by_date),
			"budget_line": cstr(entry.budget_line),
			"indicative_amount": flt(entry.indicative_amount),
			"not_proceeding_reason": cstr(entry.not_proceeding_reason),
		}
		for entry in entries
	]
	content_hash = hashlib.sha256(json.dumps(snapshots, sort_keys=True).encode()).hexdigest()
	submission_number = (
		frappe.db.count(
			"Departmental Plan Submission",
			{"dpp_version": ["in", frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root.name}, pluck="name")]},
		)
		+ 1
	)
	submission = frappe.get_doc(
		{
			"doctype": "Departmental Plan Submission",
			"submission_reference": references.submission_reference(root.dpp_reference, version.version_number),
			"dpp_version": version.name,
			"submission_number": submission_number,
			"entry_snapshots": json.dumps(snapshots),
			"content_hash": content_hash,
			"attestation_text": attestation,
			"submitted_by_user": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"submitted_at": now_datetime(),
			"fixture_namespace": cstr(root.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	task = frappe.get_doc(
		{
			"doctype": "Departmental Plan Validation Task",
			"task_reference": references.validation_task_reference(root.dpp_reference, version.version_number),
			"submission": submission.name,
			"dpp_version": version.name,
			"organisation_unit": root.organisation_unit,
			"fiscal_year": root.fiscal_year,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(root.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Departmental Plan Version", version.name, {"version_status": "Submitted", "submission": submission.name}, update_modified=False,
	)
	envelope.bump(root, current_state="Submitted")
	root.reload()
	version.reload()
	result = _result(root, version, action="submitted", task=task.task_reference)
	result["submission_reference"] = submission.submission_reference
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitDepartmentalPlan", payload=payload, result=result,
		document_type="Departmental Plan Submission", document_name=submission.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def withdraw_departmental_plan_version(
	*, dpp_version: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"dpp_version": dpp_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root, submit=True)
	envelope.check_record_version(root, expected_record_version)
	if version.version_status not in ("Draft", "Returned") or cstr(root.current_version) != version.name:
		fail("PLN_DPP_STALE", "Only the current Draft or Returned Version can be withdrawn.")
	frappe.db.set_value("Departmental Plan Version", version.name, "version_status", "Withdrawn", update_modified=False)
	if root.current_accepted_version:
		envelope.bump(root, current_state="Accepted", current_version=root.current_accepted_version)
	else:
		envelope.bump(root, current_state="Withdrawn", current_version="")
	root.reload()
	version.reload()
	result = _result(root, version, action="withdrawn")
	envelope.record_command(
		idempotency_key=idempotency_key, command="WithdrawDepartmentalPlanVersion", payload=payload, result=result,
		document_type="Departmental Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def create_departmental_plan_update(
	*, departmental_plan: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"departmental_plan": departmental_plan}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root = envelope.locked("Departmental Plan", departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Accepted" or not root.current_accepted_version:
		fail("PLN_DPP_STALE", "Only an accepted departmental plan can take an update.")
	if cstr(root.current_version) != cstr(root.current_accepted_version):
		fail("PLN_DPP_STALE", "An open update already exists for this departmental plan.")
	version = _new_version(root, number=_next_version_number(root.name), based_on=root.current_accepted_version)
	copy_entries(root.current_accepted_version, version, cstr(root.fixture_namespace))
	needs_intake.refresh_draft_entries(version)
	envelope.bump(root, current_version=version.name, current_state="Draft")
	root.reload()
	result = _result(root, version, action="update_created")
	envelope.record_command(
		idempotency_key=idempotency_key, command="CreateDepartmentalPlanUpdate", payload=payload, result=result,
		document_type="Departmental Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result
