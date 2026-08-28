# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 §10 — whitelisted service contracts. Thin wrappers only: every
guard (permission, state, SoD, generated-field immutability) lives in the
services layer (reference_data_transitions/reference_data_resolver); this
module validates presence of required input, dispatches by action, and wires
idempotency where the contract calls for it — it enforces nothing itself.

A few endpoints beyond the 12 named in §10 are exposed as pragmatic, necessary
supplements: the FY/Context state machines have actor-gated steps (e.g. FY's
own Submit, Context's Recommend) that the terse contract table doesn't name
separately from Create/Decide but that a real UI must still be able to call.
Each is marked below.
"""

from __future__ import annotations

import frappe

from kentender_core.services import reference_data_queries as queries
from kentender_core.services import reference_data_resolver as resolver
from kentender_core.services import reference_data_transitions as txn
from kentender_core.services.reference_data_idempotency import run_idempotent


def _obj(payload) -> dict:
	if isinstance(payload, str):
		return frappe.parse_json(payload) or {}
	return payload or {}


# --- PE Type -------------------------------------------------------------------------


@frappe.whitelist()
def list_pe_types():
	return queries.list_pe_types()


# --- Procuring Entity --------------------------------------------------------------


@frappe.whitelist()
def list_procuring_entities(status: str | None = None, pe_type: str | None = None, search: str | None = None):
	return queries.list_procuring_entities(status=status, pe_type=pe_type, search=search)


@frappe.whitelist()
def get_procuring_entity(pe_id: str):
	return queries.get_procuring_entity(pe_id)


@frappe.whitelist()
def create_or_revise_pe(payload=None, pe_id: str | None = None, change_reason: str | None = None):
	"""Create when pe_id is omitted; revise (propose amendment) when given."""
	if pe_id:
		return txn.propose_amendment(pe_id, change_reason or "", user=frappe.session.user)
	return txn.create_pe_draft(_obj(payload), user=frappe.session.user)


@frappe.whitelist()
def update_pe_draft(pe_id: str, payload=None):
	"""Edit a still-Draft PE's fields before Activate — §6.1's 'Create draft' and
	'Activate' are separate steps, so the draft must stay editable in between."""
	return txn.update_pe_draft(pe_id, _obj(payload), user=frappe.session.user)


@frappe.whitelist()
def decide_pe_change(
	pe_id: str,
	action: str,
	reason: str | None = None,
	effective_date=None,
	idempotency_key: str | None = None,
):
	dispatch = {
		"activate": lambda: txn.activate_pe(pe_id, user=frappe.session.user),
		"suspend": lambda: txn.suspend_pe(pe_id, reason or "", user=frappe.session.user),
		"reinstate": lambda: txn.reinstate_pe(pe_id, user=frappe.session.user),
		"retire": lambda: txn.retire_pe(
			pe_id, reason or "", effective_date or frappe.utils.today(), user=frappe.session.user
		),
	}
	if action not in dispatch:
		frappe.throw(f"Unknown Procuring Entity action: {action}", frappe.ValidationError)
	return run_idempotent(idempotency_key, "Procuring Entity", pe_id, action, dispatch[action])


# --- Financial Year -----------------------------------------------------------------


@frappe.whitelist()
def list_financial_years(record_status: str | None = None):
	return queries.list_financial_years(record_status=record_status)


@frappe.whitelist()
def get_financial_year(financial_year_id: str):
	"""Supplement — needed for §12.11's FY detail screen; not separately named in §10."""
	return queries.get_financial_year(financial_year_id)


@frappe.whitelist()
def create_financial_year(start_year):
	return txn.create_fy_draft(int(start_year), user=frappe.session.user)


@frappe.whitelist()
def make_financial_year_available(financial_year_id: str, idempotency_key: str | None = None):
	return run_idempotent(
		idempotency_key,
		"Financial Year",
		financial_year_id,
		"make_available",
		lambda: txn.make_fy_available(financial_year_id, user=frappe.session.user),
	)


@frappe.whitelist()
def retire_financial_year(financial_year_id: str, idempotency_key: str | None = None):
	"""Supplement — §10 doesn't name FY retirement separately; §6.2 has it."""
	return run_idempotent(
		idempotency_key,
		"Financial Year",
		financial_year_id,
		"retire",
		lambda: txn.retire_fy(financial_year_id, user=frappe.session.user),
	)


# --- PE Fiscal Year Context ----------------------------------------------------------


@frappe.whitelist()
def list_pe_fy_contexts(
	procuring_entity: str | None = None,
	financial_year: str | None = None,
	status: str | None = None,
	search: str | None = None,
):
	return queries.list_pe_fy_contexts(
		procuring_entity=procuring_entity, financial_year=financial_year, status=status, search=search
	)


@frappe.whitelist()
def get_pe_fy_context(context_id: str):
	return queries.get_pe_fy_context(context_id)


@frappe.whitelist()
def enable_pe_fy_context(
	procuring_entity: str,
	financial_year: str,
	active_from=None,
	active_to=None,
	idempotency_key: str | None = None,
):
	return run_idempotent(
		idempotency_key,
		"PE Fiscal Year Context",
		f"{procuring_entity}:{financial_year}",
		"enable",
		lambda: txn.enable_context(procuring_entity, financial_year, active_from, active_to, user=frappe.session.user),
	)


@frappe.whitelist()
def decide_pe_fy_context(
	context_id: str,
	action: str,
	reason: str | None = None,
	acknowledged=False,
	active_from=None,
	active_to=None,
	idempotency_key: str | None = None,
	expected_version: str | None = None,
):
	dispatch = {
		"suspend": lambda: txn.suspend_context(
			context_id, reason or "", user=frappe.session.user, expected_version=expected_version
		),
		"reinstate": lambda: txn.reinstate_context(
			context_id, user=frappe.session.user, expected_version=expected_version
		),
		"close": lambda: txn.close_context(
			context_id,
			reason or "",
			acknowledged=frappe.utils.cint(acknowledged) == 1,
			user=frappe.session.user,
			expected_version=expected_version,
		),
		"reopen": lambda: txn.reopen_context(
			context_id, reason or "", active_from, active_to, user=frappe.session.user, expected_version=expected_version
		),
	}
	if action not in dispatch:
		frappe.throw(f"Unknown PE/FY Context action: {action}", frappe.ValidationError)
	return run_idempotent(idempotency_key, "PE Fiscal Year Context", context_id, action, dispatch[action])


# --- Resolution ----------------------------------------------------------------------


@frappe.whitelist()
def resolve_authorized_contexts(remembered_context: str | None = None):
	return resolver.resolve_authorized_contexts(frappe.session.user, remembered_context=remembered_context)


@frappe.whitelist()
def validate_context_for_command(context_id: str):
	return resolver.validate_context_for_command(frappe.session.user, context_id)
