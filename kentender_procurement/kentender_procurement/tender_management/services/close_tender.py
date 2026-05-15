# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §12.1 — ``close_tender`` / ``closeTender`` (close tender at/after submission deadline).

Preconditions:

1. ``server_time`` (or server **now**) is **>=** **TM2 Tender Timeline** ``submission_deadline_at``;
2. **TM2 Tender** status **Published** (not already **Closed** / **Closed - No Valid Submissions**);
3. No blocking addendum: tender must not be **Addendum Pending** / **Suspended Pending Addendum**, and no
   **TM2 Addendum** row whose ``status`` is outside terminal states (**Issued**, **Cancelled**,
   **Superseded**, **Withdrawn**);
4. :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
   for **CLS2_CLOSE_TENDER**.

On success (order: closing record first, then tender transition):

1. Insert **TM2 Tender Closing Record** (``CLS-{tender_code}``, counts, ``closing_payload``);
2. Set tender **Closed** or **Closed - No Valid Submissions** when ``valid_submission_count == 0``;
3. Set ``closed_at`` on **TM2 Tender**;
4. Audit **Tender Closed**.

Counts (§12.1):

- **valid_submission_count** — **TM2 Bid Submission** rows in ``Submitted`` / ``Sealed`` / ``Opened`` /
  ``Evaluation Locked``;
- **withdrawn_submission_count** — ``bid_status`` **Withdrawn**;
- **late_attempt_count** — **TM2 Late Submission Attempt** rows for the tender.

Tests: ``tender_management.tests.test_p7_01_close_tender``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)

_ACTION = "CLS2_CLOSE_TENDER"
_OBJECT_TYPE = "TM2 Tender"

_CLOSED_STATUSES: frozenset[str] = frozenset({"Closed", "Closed - No Valid Submissions"})

_TERMINAL_ADDENDUM_STATUSES: frozenset[str] = frozenset(
	{"Issued", "Cancelled", "Superseded", "Withdrawn"}
)

_VALID_SUBMISSION_BID_STATUSES: frozenset[str] = frozenset(
	{
		"Submitted",
		"Sealed",
		"Opened",
		"Evaluation Locked",
	}
)


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_tm2(tender_code: str) -> Document | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return frappe.get_doc("TM2 Tender", name)
	if frappe.db.exists("TM2 Tender", tc):
		return frappe.get_doc("TM2 Tender", tc)
	return None


def _submission_deadline_at(tm2_name: str) -> Any | None:
	tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
	if not tl_name:
		return None
	return frappe.db.get_value("TM2 Tender Timeline", tl_name, "submission_deadline_at")


def _blocking_addendum_exists(tm2_name: str) -> bool:
	for st in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2_name}, pluck="status"):
		if cstr(st).strip() not in _TERMINAL_ADDENDUM_STATUSES:
			return True
	return False


def _count_valid_submissions(tm2_name: str) -> int:
	n = 0
	for st in frappe.get_all("TM2 Bid Submission", filters={"tm2_tender": tm2_name}, pluck="bid_status"):
		if cstr(st).strip() in _VALID_SUBMISSION_BID_STATUSES:
			n += 1
	return n


def _count_withdrawn_submissions(tm2_name: str) -> int:
	return int(
		frappe.db.count(
			"TM2 Bid Submission",
			{"tm2_tender": tm2_name, "bid_status": "Withdrawn"},
		)
	)


def _count_late_attempts(tm2_name: str) -> int:
	return int(frappe.db.count("TM2 Late Submission Attempt", {"tm2_tender": tm2_name}))


def close_tender(
	actor: str,
	tender_code: str,
	server_time: datetime | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""§12.1 — close a **Published** tender after the submission deadline; persist **TM2 Tender Closing Record**."""
	ctx = dict(context or {})
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
		)

	tc = cstr(tm2.tender_code).strip() or tm2.name
	st = cstr(tm2.status).strip()
	if st in _CLOSED_STATUSES:
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("This tender is already closed."),
			extra={"tender_status": st},
		)
	if st != "Published":
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Closing requires the tender to be published."),
			extra={"tender_status": st},
		)

	if _blocking_addendum_exists(tm2.name):
		codes = [
			cstr(r.get("addendum_code") or r.get("name"))
			for r in frappe.get_all(
				"TM2 Addendum",
				filters={"tm2_tender": tm2.name},
				fields=["name", "addendum_code", "status"],
			)
			if cstr(r.get("status")).strip() not in _TERMINAL_ADDENDUM_STATUSES
		]
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Closing is blocked while a non-terminal addendum exists."),
			extra={"pending_addendum_refs": codes},
		)

	deadline_at = _submission_deadline_at(tm2.name)
	if not deadline_at:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Submission deadline is not configured for this tender."),
		)

	close_ts = server_time or now_datetime()
	if get_datetime(close_ts) < get_datetime(deadline_at):
		return _deny(
			DenialCode.AUTH_STATE_DENIED.value,
			_("Closing is only allowed at or after the submission deadline (server time)."),
			extra={"submission_deadline_at": str(deadline_at), "server_time": str(close_ts)},
		)

	if frappe.db.exists("TM2 Tender Closing Record", {"tm2_tender": tm2.name}):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("A tender closing record already exists for this tender."),
		)

	avail = get_action_availability(
		_ACTION,
		_OBJECT_TYPE,
		tc,
		actor,
		context={**ctx, "object_exists": True},
	)
	if not avail.get("allowed"):
		dc = _map_auth_denial(str(avail.get("denial_code") or ""))
		return _deny(
			dc,
			str(avail.get("user_message") or avail.get("message") or dc),
			extra={"availability": avail},
		)

	valid_n = _count_valid_submissions(tm2.name)
	withdrawn_n = _count_withdrawn_submissions(tm2.name)
	late_n = _count_late_attempts(tm2.name)

	if valid_n == 0:
		closing_status = "Closed With No Valid Submissions"
		next_tender_status = "Closed - No Valid Submissions"
	else:
		closing_status = "Closed On Time"
		next_tender_status = "Closed"

	payload = {
		"tender_code": tc,
		"valid_submission_count": valid_n,
		"withdrawn_submission_count": withdrawn_n,
		"late_attempt_count": late_n,
		"server_time": str(close_ts),
	}

	cl_doc = frappe.get_doc(
		{
			"doctype": "TM2 Tender Closing Record",
			"tm2_tender": tm2.name,
			"closing_status": closing_status,
			"valid_submission_count": valid_n,
			"withdrawn_submission_count": withdrawn_n,
			"late_attempt_count": late_n,
			"submission_deadline_at": deadline_at,
			"closed_at": close_ts,
			"closed_by": actor,
			"closing_payload": payload,
		}
	)
	cl_doc.insert(ignore_permissions=True)
	cl_doc.reload()

	frappe.db.set_value(
		"TM2 Tender",
		tm2.name,
		{
			"status": next_tender_status,
			"closed_at": close_ts,
		},
		update_modified=False,
	)

	audit_payload = {
		**payload,
		"tm2_tender_closing_record": cl_doc.name,
		"tender_status_after": next_tender_status,
		"closing_code": cl_doc.closing_code,
	}
	append_tender_audit_event(
		tc,
		"Tender Closed",
		actor,
		audit_payload,
		related_object_type="TM2 Tender Closing Record",
		related_object_code=cl_doc.name,
		previous_state="Published",
		new_state=next_tender_status,
		enforce_section_13_2=False,
	)

	return {
		"ok": True,
		"actor": actor,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"tender_status": next_tender_status,
		"tm2_tender_closing_record": cl_doc.name,
		"closing_code": cl_doc.closing_code,
		"valid_submission_count": valid_n,
		"withdrawn_submission_count": withdrawn_n,
		"late_attempt_count": late_n,
	}


def closeTender(
	actor: str,
	tender_code: str,
	server_time: datetime | None = None,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`close_tender`."""
	return close_tender(actor, tender_code, server_time=server_time, context=context)
