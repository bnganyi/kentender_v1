# Copyright (c) 2026, KenTender and contributors
# For license information, please see licence.txt

"""PLN-CHG-001 v1.2 §5.1 — the Departmental Procurement Plan lifecycle.

Commands (§8.2): OpenDepartmentalPlan, SaveNeedFunding, SaveDirectRequirement,
RemoveDirectRequirement, SubmitDepartmentalPlan, plus the §5.1 withdraw /
reopen / create-update transitions. Shape validation lives on the doctype
controllers; completeness (coverage, funding, window, authority) is enforced
here at submission — deliberately split (NDS FU-04).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, get_datetime, getdate, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	budget_gateway,
	envelope,
	needs_intake,
	references,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
)

AUTHOR_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
SUBMIT_ROLES = (ROLE_HEAD_OF_USER_DEPARTMENT,)

ATTESTATION = (
	"I certify that this Departmental Procurement Plan contains the current "
	"procurement requirements of {department} for {financial_year}, including "
	"every current accepted Departmental Need and any direct departmental "
	"requirements shown. I confirm that the quantities, required-by dates, "
	"Budget Lines and indicative amounts are ready for Procurement validation "
	"and inclusion in the Annual Procurement Plan."
)

DIRECT_FIELDS = (
	"title", "description", "expected_operational_result", "quantity", "unit",
	"required_by_date", "budget_line", "indicative_amount",
)


# --- shared helpers ---------------------------------------------------------


def _root_by_scope(pe: str, ou: str, fy: str):
	ctx = authority.resolve_context_id(pe, fy)
	name = frappe.db.get_value(
		"Departmental Plan", {"pe_fy_context": ctx, "organisation_unit": ou}, "name"
	)
	return ctx, (frappe.get_doc("Departmental Plan", name) if name else None)


def _version(version_name: str):
	if not version_name or not frappe.db.exists("Departmental Plan Version", version_name):
		authority.not_found()
	return frappe.get_doc("Departmental Plan Version", version_name)


def _root_of(version):
	return frappe.get_doc("Departmental Plan", version.departmental_plan)


def _require_author(actor: str, root, *, submit: bool = False) -> str:
	return authority.require_scope(
		actor,
		roles=SUBMIT_ROLES if submit else AUTHOR_ROLES,
		procuring_entity=root.procuring_entity,
		organisation_unit=root.organisation_unit,
	)


def _require_mutable_current(root, version) -> None:
	if version.version_status not in ("Draft",):
		fail("PLN_DPP_STALE", "This departmental plan changed. Reload and review the current Version.")
	if cstr(root.current_version) != cstr(version.name):
		fail("PLN_DPP_STALE", "This departmental plan changed. Reload and review the current Version.")


def _window(ctx: str):
	return frappe.db.get_value(
		"Departmental Plan Submission Window",
		{"pe_fy_context": ctx},
		["opens_at", "closes_at"],
		as_dict=True,
	)


def _window_open(ctx: str) -> bool:
	window = _window(ctx)
	if not window:
		return False
	now = now_datetime()
	return get_datetime(window.opens_at) <= now <= get_datetime(window.closes_at)


def _has_any_submission(root) -> bool:
	versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": root.name},
		pluck="name",
	)
	return bool(
		versions
		and frappe.get_all(
			"Departmental Plan Submission",
			filters={"dpp_version": ["in", versions]},
			limit=1,
		)
	)


def _entries(version_name: str) -> list[Any]:
	return [
		frappe.get_doc("Departmental Plan Entry", name)
		for name in frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version_name},
			order_by="creation asc",
			pluck="name",
		)
	]


def _fy_bounds(financial_year: str) -> tuple[Any, Any]:
	row = frappe.db.get_value(
		"Financial Year", financial_year, ["start_date", "end_date"], as_dict=True
	)
	return (getdate(row.start_date), getdate(row.end_date)) if row else (None, None)


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
	rows = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": root_name},
		pluck="version_number",
	)
	return max([int(n or 0) for n in rows] or [0]) + 1


def copy_entries(source_version: str, target_version, fixture_namespace: str = "") -> int:
	"""Copy every entry with its stable entry_id and funding onto a new Version."""
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
				"fixture_namespace": fixture_namespace or entry.fixture_namespace,
			}
		).insert(ignore_permissions=True)
		count += 1
	return count


# --- §8.2 commands ----------------------------------------------------------


def open_departmental_plan(
	*,
	procuring_entity: str,
	organisation_unit: str,
	financial_year: str,
	idempotency_key: str,
	user: str | None = None,
	fixture_namespace: str = "",
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {
		"procuring_entity": procuring_entity,
		"organisation_unit": organisation_unit,
		"financial_year": financial_year,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authority.require_scope(
		actor, roles=AUTHOR_ROLES, procuring_entity=procuring_entity,
		organisation_unit=organisation_unit, masked=False,
	)
	ctx, root = _root_by_scope(procuring_entity, organisation_unit, financial_year)

	if root is None:
		root = frappe.get_doc(
			{
				"doctype": "Departmental Plan",
				"dpp_reference": references.dpp_reference(
					procuring_entity, organisation_unit, financial_year
				),
				"pe_fy_context": ctx,
				"procuring_entity": procuring_entity,
				"organisation_unit": organisation_unit,
				"financial_year": financial_year,
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
		if not _window_open(ctx):
			fail("PLN_WINDOW_CLOSED", "The initial departmental-plan submission window is closed.")
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
		idempotency_key=idempotency_key, command="OpenDepartmentalPlan",
		payload=payload, result=result, document_type="Departmental Plan",
		document_name=root.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def save_need_funding(
	*,
	dpp_version: str,
	entry_id: str,
	budget_line: str,
	indicative_amount: float,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {
		"dpp_version": dpp_version, "entry_id": entry_id,
		"budget_line": budget_line, "indicative_amount": indicative_amount,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)

	name = frappe.db.get_value(
		"Departmental Plan Entry",
		{"dpp_version": version.name, "entry_id": cstr(entry_id)},
		"name",
	)
	if not name:
		authority.not_found()
	entry = frappe.get_doc("Departmental Plan Entry", name)
	if entry.source_origin != needs_intake.NEED_ORIGIN:
		fail("PLN_ENTRY_INCOMPLETE", "Only a Need-origin entry takes funding details here.")
	current = needs_intake.current_accepted_version_of(
		entry.need, root.procuring_entity, root.financial_year
	)
	if current != cstr(entry.need_version):
		fail("PLN_DPP_STALE", "This departmental plan changed. Reload and review the current Version.")
	_validate_funding(root, budget_line, indicative_amount)
	entry.budget_line = budget_line
	entry.indicative_amount = flt(indicative_amount)
	entry.save(ignore_permissions=True)
	envelope.bump(root)
	result = _result(root, version, action="need_funding_saved")
	envelope.record_command(
		idempotency_key=idempotency_key, command="SaveNeedFunding", payload=payload,
		result=result, document_type="Departmental Plan Entry", document_name=entry.name,
		actor=actor, fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def _validate_funding(root, budget_line: str, indicative_amount) -> None:
	if flt(indicative_amount) <= 0:
		fail("PLN_ENTRY_INCOMPLETE", "Complete the highlighted requirement fields before submitting.")
	eligible = budget_gateway.eligible_line_ids(
		procuring_entity=root.procuring_entity,
		financial_year=root.financial_year,
		source_org_unit=root.organisation_unit,
	)
	if cstr(budget_line) not in eligible:
		fail(
			"PLN_BUDGET_LINE_INELIGIBLE",
			"Select an Active Budget Line available to this department and Financial Year.",
		)


def save_direct_requirement(
	*,
	dpp_version: str,
	values: dict[str, Any] | str,
	entry_id: str | None = None,
	expected_record_version=None,
	idempotency_key: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(DIRECT_FIELDS)
	if unknown:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			f"Direct requirement input is limited to the eight defined values; unexpected: {sorted(unknown)}.",
		)
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
		name = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": version.name, "entry_id": cstr(entry_id)},
			"name",
		)
		if not name:
			authority.not_found()
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
		idempotency_key=idempotency_key, command="SaveDirectRequirement", payload=payload,
		result=result, document_type="Departmental Plan Entry", document_name=entry.name,
		actor=actor, fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def _validate_direct_values(root, values: dict[str, Any]) -> None:
	missing = [field for field in DIRECT_FIELDS if not cstr(values.get(field)).strip()]
	if missing:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			f"Complete the highlighted requirement fields before submitting: {', '.join(missing)}.",
		)
	if flt(values.get("quantity")) <= 0:
		fail("PLN_ENTRY_INCOMPLETE", "Quantity must be greater than zero.")
	unit_status = frappe.db.get_value("Unit Of Measure", cstr(values.get("unit")), "status")
	if cstr(unit_status) != "Active":
		fail("PLN_ENTRY_INCOMPLETE", "Select an active unit from the governed catalogue.")
	start, end = _fy_bounds(root.financial_year)
	required_by = getdate(values.get("required_by_date"))
	if not start or not (start <= required_by <= end):
		fail("PLN_ENTRY_INCOMPLETE", "Required by must fall inside the selected Financial Year.")
	_validate_funding(root, cstr(values.get("budget_line")), values.get("indicative_amount"))


def remove_direct_requirement(
	*,
	dpp_version: str,
	entry_id: str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"dpp_version": dpp_version, "entry_id": entry_id}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	_require_author(actor, root)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)
	name = frappe.db.get_value(
		"Departmental Plan Entry",
		{"dpp_version": version.name, "entry_id": cstr(entry_id)},
		["name", "source_origin"],
		as_dict=True,
	)
	if not name:
		authority.not_found()
	if name.source_origin != needs_intake.DIRECT_ORIGIN:
		fail("PLN_ENTRY_INCOMPLETE", "A current accepted Need cannot be omitted or locally deleted.")
	frappe.delete_doc(
		"Departmental Plan Entry", name.name,
		force=True, ignore_permissions=True, delete_permanently=True,
	)
	envelope.bump(root)
	result = _result(root, version, action="direct_removed")
	envelope.record_command(
		idempotency_key=idempotency_key, command="RemoveDirectRequirement", payload=payload,
		result=result, document_type="Departmental Plan Version", document_name=version.name,
		actor=actor, fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def submit_departmental_plan(
	*,
	dpp_version: str,
	certification_confirmed: bool,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"dpp_version": dpp_version, "certification_confirmed": bool(certification_confirmed)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = _version(dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	role = _require_author(actor, root, submit=True)
	envelope.check_record_version(root, expected_record_version)
	_require_mutable_current(root, version)
	if not certification_confirmed:
		fail("PLN_ENTRY_INCOMPLETE", "Confirm the departmental certification before submitting.")

	ctx = cstr(root.pe_fy_context)
	if not _has_any_submission(root) and not _window_open(ctx):
		fail("PLN_WINDOW_CLOSED", "The initial departmental-plan submission window is closed.")

	# revalidate inside the transaction: coverage, entry completeness, funding
	needs_intake.refresh_draft_entries(version)
	gaps = needs_intake.coverage_gaps(version)
	if gaps:
		fail(
			"PLN_NEED_COVERAGE_INCOMPLETE",
			"Add every current accepted Need to this departmental plan before "
			f"submitting: {', '.join(gaps)}.",
		)
	entries = _entries(version.name)
	if not entries:
		fail("PLN_ENTRY_INCOMPLETE", "A departmental plan with no entries cannot be submitted.")
	eligible = budget_gateway.eligible_line_ids(
		procuring_entity=root.procuring_entity,
		financial_year=root.financial_year,
		source_org_unit=root.organisation_unit,
	)
	for entry in entries:
		if not cstr(entry.budget_line) or flt(entry.indicative_amount) <= 0:
			fail(
				"PLN_ENTRY_INCOMPLETE",
				f"Complete the highlighted requirement fields before submitting ({entry.entry_id}).",
			)
		if cstr(entry.budget_line) not in eligible:
			fail(
				"PLN_BUDGET_LINE_INELIGIBLE",
				f"Select an Active Budget Line available to this department and Financial Year ({entry.entry_id}).",
			)

	department = cstr(
		frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name")
		or root.organisation_unit
	)
	fy_label = cstr(
		frappe.db.get_value("Financial Year", root.financial_year, "label")
		or root.financial_year
	)
	# the FY controller stores the bare period ("2098/99"); the §4.5 attestation
	# and every artboard render it as "FY 2098/99"
	if not fy_label.upper().startswith("FY"):
		fy_label = f"FY {fy_label}"
	attestation = ATTESTATION.format(department=department, financial_year=fy_label)
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
		}
		for entry in entries
	]
	content_hash = hashlib.sha256(
		json.dumps(snapshots, sort_keys=True).encode()
	).hexdigest()
	submission_number = (
		frappe.db.count(
			"Departmental Plan Submission",
			{"dpp_version": ["in", frappe.get_all(
				"Departmental Plan Version",
				filters={"departmental_plan": root.name},
				pluck="name",
			)]},
		)
		+ 1
	)
	submission = frappe.get_doc(
		{
			"doctype": "Departmental Plan Submission",
			"submission_reference": references.submission_reference(
				root.dpp_reference, version.version_number
			),
			"dpp_version": version.name,
			"submission_number": submission_number,
			"entry_snapshots": json.dumps(snapshots),
			"content_hash": content_hash,
			"attestation_text": attestation,
			"submitted_by_user": actor,
			"authority_snapshot": authority.authority_snapshot(
				actor, role=role,
				values=(root.procuring_entity, root.organisation_unit, root.financial_year),
			),
			"submitted_at": now_datetime(),
			"fixture_namespace": cstr(root.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	task = frappe.get_doc(
		{
			"doctype": "Departmental Plan Validation Task",
			"task_reference": references.validation_task_reference(
				root.dpp_reference, version.version_number
			),
			"submission": submission.name,
			"dpp_version": version.name,
			"procuring_entity": root.procuring_entity,
			"organisation_unit": root.organisation_unit,
			"financial_year": root.financial_year,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(root.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Departmental Plan Version", version.name,
		{"version_status": "Submitted", "submission": submission.name},
		update_modified=False,
	)
	envelope.bump(root, current_state="Submitted")
	root.reload()
	version.reload()
	result = _result(root, version, action="submitted", task=task.task_reference)
	result["submission_reference"] = submission.submission_reference
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitDepartmentalPlan", payload=payload,
		result=result, document_type="Departmental Plan Submission",
		document_name=submission.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def withdraw_departmental_plan_version(
	*,
	dpp_version: str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
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
	frappe.db.set_value(
		"Departmental Plan Version", version.name, "version_status", "Withdrawn",
		update_modified=False,
	)
	if root.current_accepted_version:
		envelope.bump(
			root, current_state="Accepted", current_version=root.current_accepted_version
		)
	else:
		envelope.bump(root, current_state="Withdrawn", current_version="")
	root.reload()
	version.reload()
	result = _result(root, version, action="withdrawn")
	envelope.record_command(
		idempotency_key=idempotency_key, command="WithdrawDepartmentalPlanVersion",
		payload=payload, result=result, document_type="Departmental Plan Version",
		document_name=version.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result


def create_departmental_plan_update(
	*,
	departmental_plan: str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
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
	version = _new_version(
		root,
		number=_next_version_number(root.name),
		based_on=root.current_accepted_version,
	)
	copy_entries(root.current_accepted_version, version, cstr(root.fixture_namespace))
	needs_intake.refresh_draft_entries(version)
	envelope.bump(root, current_version=version.name, current_state="Draft")
	root.reload()
	result = _result(root, version, action="update_created")
	envelope.record_command(
		idempotency_key=idempotency_key, command="CreateDepartmentalPlanUpdate",
		payload=payload, result=result, document_type="Departmental Plan Version",
		document_name=version.name, actor=actor,
		fixture_namespace=cstr(root.fixture_namespace),
	)
	return result
