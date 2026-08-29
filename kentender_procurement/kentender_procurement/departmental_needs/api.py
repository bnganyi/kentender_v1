"""Whitelisted Departmental Needs contracts (NDS-CHG-001 v1.1 §8).

Endpoint names are the §8.1 and §8.2 contract names exactly. No writable
DocType endpoint bypasses a command (§16.1): every mutation below runs through
`services/lifecycle.py`, which enforces scope, state, maker-checker, the
optimistic record version, the decision token and the idempotency key.

Attachment and support-lookup endpoints are gone with the concepts themselves
(§1.1, NDS-AC-029).
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.context import (
	intake_window,
	resolve_creation_context,
	save_intake_window,
)
from kentender_procurement.departmental_needs.services.usage import project_planning_usage
from kentender_procurement.departmental_needs.services.workspace import (
	get_current_accepted_need as _get_current_accepted_need,
	get_need,
	get_review_task,
	get_workspace,
)

# --- §8.1 read contracts ---------------------------------------------------

resolve_needs_contexts = frappe.whitelist()(resolve_creation_context)
get_needs_workspace = frappe.whitelist()(get_workspace)
get_departmental_need = frappe.whitelist()(get_need)
get_departmental_review_task = frappe.whitelist()(get_review_task)
get_needs_intake_window = frappe.whitelist()(intake_window)
get_current_accepted_need = frappe.whitelist()(_get_current_accepted_need)
check_accepted_need_withdrawal_dependency = frappe.whitelist()(lifecycle.check_withdrawal_dependency)


# --- §8.2 commands ---------------------------------------------------------

# Frappe hands a whitelisted method the whole `form_dict`, and it only filters
# that down to the declared parameters when the method has no `**kwargs`. The
# endpoints below deliberately take `**kwargs` — so the framework's own
# transport fields arrive as ordinary keyword arguments and, forwarded verbatim
# into a keyword-only service signature, raise `TypeError` and surface to the
# browser as a 500. They are dropped here rather than absorbed by the services,
# which must keep explicit signatures (§8.2).
_TRANSPORT_FIELDS = frozenset({"cmd", "csrf_token", "_"})


def _command_args(kwargs: dict[str, Any]) -> dict[str, Any]:
	return {key: value for key, value in kwargs.items() if key not in _TRANSPORT_FIELDS}


@frappe.whitelist()
def save_need_draft(**kwargs: Any) -> dict[str, Any]:
	"""Create or update the originator's Draft; first save generates the reference.

	One contract covers both, as §8.2 specifies: the presence of a Need decides
	whether this is the first save or a later one.
	"""
	args = _command_args(kwargs)
	need = (args.pop("need", "") or "").strip()
	if need:
		return lifecycle.update_need(need=need, **args)
	args.pop("expected_version", None)
	return lifecycle.create_need(**args)


submit_need_version = frappe.whitelist()(lifecycle.submit_need)
withdraw_unaccepted_need = frappe.whitelist()(lifecycle.withdraw_need)
create_accepted_need_successor = frappe.whitelist()(lifecycle.create_accepted_need_successor)
cancel_accepted_need_successor = frappe.whitelist()(lifecycle.cancel_accepted_need_successor)
request_accepted_need_withdrawal = frappe.whitelist()(lifecycle.request_withdrawal)
decide_accepted_need_withdrawal = frappe.whitelist()(lifecycle.decide_withdrawal)
save_needs_intake_window = frappe.whitelist()(save_intake_window)
project_need_planning_usage = frappe.whitelist()(project_planning_usage)


# §8.2 names one command per acceptance outcome. They share one implementation
# so the maker-checker, state, token and lineage rules cannot drift apart, but
# each is a distinct endpoint that cannot be turned into another by changing a
# request parameter.


@frappe.whitelist()
def return_need_version(**kwargs: Any) -> dict[str, Any]:
	"""Mark the submitted version Returned and create one copied correction Draft."""
	return lifecycle.review_need(decision="return", **_command_args(kwargs))


@frappe.whitelist()
def accept_need_version(**kwargs: Any) -> dict[str, Any]:
	"""Accept the initial or successor version and publish lineage."""
	return lifecycle.review_need(decision="accept", **_command_args(kwargs))


@frappe.whitelist()
def decline_need_version(**kwargs: Any) -> dict[str, Any]:
	"""Close the initial Need or successor without changing an accepted version."""
	return lifecycle.review_need(decision="decline", **_command_args(kwargs))
