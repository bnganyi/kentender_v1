"""Whitelisted Departmental Needs contracts (NDS-CHG-001 v1.6 §8).

Endpoint names are the §8.1 and §8.2 contract names exactly. No writable
DocType endpoint bypasses a command (§16.1): every mutation below runs through
`services/lifecycle.py`, which enforces scope, state, maker-checker, the
optimistic record version, the decision token and the idempotency key.

Attachment and support-lookup endpoints are gone with the concepts themselves
(§1.1, NDS-AC-029). `get_needs_intake_window` / `save_needs_intake_window` are
gone with the `Needs Intake Window` doctype (§4.1, §16.4.11): Departmental
Needs exposes no configuration route for the Needs-submission flag at all —
`get_needs_submission_state` is a plain read of the Fiscal Year fields
Configuration & Governance maintains through `/app/system-setup`.

Who is acting (AUD-XC-001). Every endpoint here acts as `frappe.session.user`
and nobody else: a request field can never name the acting principal (AUTH-ADR-001
§5.5, §15). The services keep an optional `user` argument because Planning,
the seeds and the tests call them in-process with an explicit principal, but
that argument is not part of any endpoint's signature (`_session_endpoint`
removes it) and the `**kwargs` commands refuse it (`_command_args`).

Planning's three projection commands (`project_planning_usage`,
`project_planning_disposition`, `project_planning_intake`) are deliberately not
here: they are service-to-service seams in `services/usage.py`, called in-process
by Procurement Planning, with no web route (AUD-XC-016; NDS §7.5 "registered
Planning producer only").
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

import frappe

from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.context import (
	get_needs_submission_state as _get_needs_submission_state,
	list_need_create_targets as _list_need_create_targets,
	list_need_units as _list_need_units,
	resolve_creation_context,
	selectable_financial_years,
)
from kentender_procurement.departmental_needs.services.usage import (
	planning_status_for_need as _planning_status_for_need,
)
from kentender_procurement.departmental_needs.services.workspace import (
	get_current_accepted_need as _get_current_accepted_need,
	get_need,
	get_review_task,
	get_workspace,
)


# Parameters that would let a request choose who acts. None may reach a service
# from a web request.
_PRINCIPAL_PARAMS = frozenset({"user"})
_PRINCIPAL_REFUSAL = "The acting user is always the signed-in user; a request cannot name another."


def _refuse_principal(names) -> None:
	if _PRINCIPAL_PARAMS & set(names):
		fail("NDS_SCOPE_DENIED", _PRINCIPAL_REFUSAL)


def _without_principal(fields: dict[str, Any]) -> dict[str, Any]:
	_refuse_principal(fields)
	return dict(fields)


def _session_endpoint(service: Callable[..., Any]) -> Callable[..., Any]:
	"""The whitelisted face of a service: same contract, no acting-user parameter.

	The service resolves its principal from `frappe.session.user` when `user` is
	not passed, so the endpoint simply never passes it. The public signature
	drops `user`, which is what makes Frappe discard a `user=` request field
	before the call; a direct Python call that still names one is refused.
	"""
	signature = inspect.signature(service)
	public = signature.replace(
		parameters=[p for name, p in signature.parameters.items() if name not in _PRINCIPAL_PARAMS]
	)

	@functools.wraps(service)
	def endpoint(*args: Any, **kwargs: Any) -> Any:
		return service(*args, **_without_principal(kwargs))

	endpoint.__signature__ = public  # type: ignore[attr-defined]
	endpoint.__annotations__ = {
		name: hint for name, hint in getattr(service, "__annotations__", {}).items() if name not in _PRINCIPAL_PARAMS
	}
	return endpoint


def _whitelisted(service: Callable[..., Any]) -> Callable[..., Any]:
	return frappe.whitelist()(_session_endpoint(service))


# --- §8.1 read contracts ---------------------------------------------------

resolve_needs_scope = _whitelisted(resolve_creation_context)
list_needs_financial_years = _whitelisted(selectable_financial_years)
list_need_create_targets = _whitelisted(_list_need_create_targets)
list_need_units = _whitelisted(_list_need_units)
get_needs_workspace = _whitelisted(get_workspace)
get_departmental_need = _whitelisted(get_need)
get_departmental_review_task = _whitelisted(get_review_task)
get_needs_submission_state = _whitelisted(_get_needs_submission_state)
get_current_accepted_need = _whitelisted(_get_current_accepted_need)
check_accepted_need_withdrawal_dependency = _whitelisted(lifecycle.read_withdrawal_dependency)
# §11.8A — the detail screen's own dedicated Planning-status re-check,
# separate from get_departmental_need's atomic payload (NDS-CHG-001 v1.14
# Phase 2: REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT/OLDER).
get_need_planning_status = _whitelisted(_planning_status_for_need)


# --- §8.2 commands ---------------------------------------------------------

# Frappe hands a whitelisted method the whole `form_dict`, and it only filters
# that down to the declared parameters when the method has no `**kwargs`. The
# endpoints below deliberately take `**kwargs` — so the framework's own
# transport fields arrive as ordinary keyword arguments and, forwarded verbatim
# into a keyword-only service signature, raise `TypeError` and surface to the
# browser as a 500. They are dropped here rather than absorbed by the services,
# which must keep explicit signatures (§8.2).
#
# Every other field must be one the service declares. An unknown field is a typed
# refusal rather than a `TypeError` (AUD-XC-140), and a field that would name the
# acting principal is refused outright (AUD-XC-001).
_TRANSPORT_FIELDS = frozenset({"cmd", "csrf_token", "_"})


def _command_args(
	kwargs: dict[str, Any],
	service: Callable[..., Any],
	*,
	also_accepted: frozenset[str] = frozenset(),
	set_by_endpoint: frozenset[str] = frozenset(),
) -> dict[str, Any]:
	"""The request's own fields for `service`, or a typed refusal.

	`also_accepted` names fields the endpoint itself consumes before calling the
	service; `set_by_endpoint` names service parameters the request may not set
	because the endpoint fixes them (e.g. the decision of an acceptance outcome).
	"""
	args = {key: value for key, value in kwargs.items() if key not in _TRANSPORT_FIELDS}
	_refuse_principal(args)
	known = (set(inspect.signature(service).parameters) - _PRINCIPAL_PARAMS - set(set_by_endpoint)) | set(
		also_accepted
	)
	unknown = sorted(set(args) - known)
	if unknown:
		fail("NDS_FIELD_REQUIRED", "Unknown field: " + ", ".join(unknown) + ".")
	return args


@frappe.whitelist()
def save_need_draft(**kwargs: Any) -> dict[str, Any]:
	"""Create or update the originator's Draft; first save generates the reference.

	One contract covers both, as §8.2 specifies: the presence of a Need decides
	whether this is the first save or a later one.
	"""
	need = (kwargs.get("need", "") or "").strip()
	if need:
		args = _command_args(kwargs, lifecycle.update_need)
		args.pop("need", None)
		return lifecycle.update_need(need=need, **args)
	# A first save carries no record version; one sent anyway is ignored.
	args = _command_args(kwargs, lifecycle.create_need, also_accepted=frozenset({"need", "expected_version"}))
	args.pop("need", None)
	args.pop("expected_version", None)
	return lifecycle.create_need(**args)


submit_need_revision = _whitelisted(lifecycle.submit_need)
withdraw_unaccepted_need = _whitelisted(lifecycle.withdraw_need)
create_accepted_need_successor = _whitelisted(lifecycle.create_accepted_need_successor)
cancel_accepted_need_successor = _whitelisted(lifecycle.cancel_accepted_need_successor)
request_accepted_need_withdrawal = _whitelisted(lifecycle.request_withdrawal)
decide_accepted_need_withdrawal = _whitelisted(lifecycle.decide_withdrawal)


def _review_args(kwargs: dict[str, Any]) -> dict[str, Any]:
	return _command_args(kwargs, lifecycle.review_need, set_by_endpoint=frozenset({"decision"}))


# §8.2 names one command per acceptance outcome. They share one implementation
# so the maker-checker, state, token and lineage rules cannot drift apart, but
# each is a distinct endpoint that cannot be turned into another by changing a
# request parameter.


@frappe.whitelist()
def return_need_revision(**kwargs: Any) -> dict[str, Any]:
	"""Mark the submitted version Returned and create one copied correction Draft."""
	return lifecycle.review_need(decision="return", **_review_args(kwargs))


@frappe.whitelist()
def accept_need_revision(**kwargs: Any) -> dict[str, Any]:
	"""Accept the initial or successor version and publish lineage."""
	return lifecycle.review_need(decision="accept", **_review_args(kwargs))


@frappe.whitelist()
def decline_need_revision(**kwargs: Any) -> dict[str, Any]:
	"""Close the initial Need or successor without changing an accepted version."""
	return lifecycle.review_need(decision="decline", **_review_args(kwargs))
