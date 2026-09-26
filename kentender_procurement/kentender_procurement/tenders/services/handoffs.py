# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §5.11 — the Tender hand-off register (plan D26).

Every row of the register is one `Tender Task` opened inside the command
transaction that causes the hand-off, and closed (Completed or Cancelled)
inside the command transaction of the business transition that clears it —
never by reading a notification (KT-STD-001 v1.8 §3B.4). A task carries:

- the next holder: a named person (`holder`) when the register names one
  (the Procurement Officer who prepared the Version, the Departmental
  Author of the Requisition), otherwise every current holder of the
  Site-wide responsibility (`business_role`);
- the sender (`sender`), whose "Waiting for …" item exists while the task
  is open, for the rows where the register gives the sender one;
- the returner's comment or reason (`comment`), kept with the item.

Each opened task raises one in-product work alert for its holder(s)
(`kentender_core.services.notification_service`); the alert claims nothing
about publication or supplier notice delivery.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, nowdate

from kentender_procurement.tenders.services import envelope
from kentender_procurement.tenders.services.tender_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PROCUREMENT_OFFICER,
)

PAGE = "tenders"

HOPF_APPROVAL = "HOPF approval"
CORRECT_RETURNED = "Correct returned Tender"
AO_AUTHORISATION = "AO publication authorisation"
CORRECT_REOPENED = "Correct reopened Tender"
CHANNEL_CONFIRMATION = "HOPF channel confirmation"
REVIEW_WITHDRAWN = "Review withdrawn authorisation"
ADDENDUM_ISSUE = "HOPF addendum issue"
CORRECT_ADDENDUM = "Correct returned addendum"
CLARIFICATION_RESPONSE = "Clarification response"
REQUISITION_CORRECTION = "Requisition correction"
CANCELLATION_REVIEW = "AO cancellation review"
CANCELLATION_COMPLIANCE = "Cancellation compliance"

#: task_type → (business role, My Work title, sender waiting title or None,
#: action label, route segment). `{ref}` is the Tender reference, `{subject}`
#: the addendum / Requisition reference, `{holder}` the holder's name, `{task}`
#: the returned task's label.
REGISTER: dict[str, tuple[str, str, str | None, str, str]] = {
	HOPF_APPROVAL: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Review Tender {ref}", "Waiting for {holder} to review Tender {ref}", "Review", ""),
	CORRECT_RETURNED: (ROLE_PROCUREMENT_OFFICER, "Correct Tender {ref} — {task}", None, "Correct", "{task_key}"),
	AO_AUTHORISATION: (ROLE_ACCOUNTING_OFFICER, "Authorise publication of Tender {ref}", "Waiting for {holder} to decide publication of Tender {ref}", "Review publication", ""),
	CORRECT_REOPENED: (ROLE_PROCUREMENT_OFFICER, "Correct reopened Tender {ref}", None, "Correct", ""),
	CHANNEL_CONFIRMATION: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Confirm publication of {subject_label}", "{channel_waiting}", "Complete confirmations", "publication"),
	REVIEW_WITHDRAWN: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Review withdrawn publication authorisation for {ref}", None, "Review", ""),
	ADDENDUM_ISSUE: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Decide addendum {subject}", "Waiting for {holder} to decide addendum {subject}", "Review addendum", "addenda"),
	CORRECT_ADDENDUM: (ROLE_PROCUREMENT_OFFICER, "Correct addendum {subject}", None, "Correct addendum", "addenda"),
	CLARIFICATION_RESPONSE: (ROLE_PROCUREMENT_OFFICER, "Respond to clarification for {ref}", None, "Respond", "clarifications"),
	REQUISITION_CORRECTION: (ROLE_DEPARTMENTAL_AUTHOR, "Correct Requisition {subject}", "Waiting for {holder} to correct the requisition", "View requisition", ""),
	CANCELLATION_REVIEW: (ROLE_ACCOUNTING_OFFICER, "Consider cancellation of {ref}", "Waiting for {holder} to consider cancellation of {ref}", "Review", "cancel"),
	CANCELLATION_COMPLIANCE: (ROLE_PROCUREMENT_OFFICER, "Record cancellation notices and PPRA report for {ref}", "Waiting for cancellation compliance evidence for {ref}", "Record evidence", "cancel"),
}
#: Rows where the holder may also be the Head of Procurement Function (§6: a
#: clarification or a returned addendum may be handled by either).
SHARED_HOLDERS = {CLARIFICATION_RESPONSE: (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)}


def full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user) if user else ""


def users_with_site_role(role: str) -> list[str]:
	"""Current holders of a Site-wide responsibility (no Organisation Unit),
	in assignment order; never invented (§5.11 "resolved from responsibility
	assignments at the event")."""
	today = nowdate()
	out: list[str] = []
	for row in frappe.get_all(
		"User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"},
		fields=["user", "organisation_unit", "effective_from", "effective_to"], order_by="creation asc", limit_page_length=0,
	):
		if cstr(row.organisation_unit):
			continue
		if row.effective_from and cstr(row.effective_from) > today:
			continue
		if row.effective_to and cstr(row.effective_to) < today:
			continue
		if row.user not in out:
			out.append(row.user)
	return out


def holders_of(task) -> list[str]:
	"""The people who hold this item now."""
	if cstr(task.get("holder")):
		return [cstr(task.holder)]
	roles = SHARED_HOLDERS.get(cstr(task.task_type), (cstr(task.business_role),))
	out: list[str] = []
	for role in roles:
		for user in users_with_site_role(role):
			if user not in out:
				out.append(user)
	return out


def holder_label(task) -> str:
	""""Charles Mutiso" / "Amina Hassan" / the responsibility when no one holds it."""
	people = [full_name(u) for u in holders_of(task)]
	return ", ".join(people) if people else cstr(task.business_role)


def _context(root, task) -> dict[str, str]:
	subject = cstr(task.get("subject_reference") or "")
	return {"ref": cstr(root.tender_reference), "subject": subject}


def open_task(
	root,
	version,
	*,
	task_type: str,
	subject_type: str = "",
	subject_id: str = "",
	holder: str = "",
	sender: str = "",
	comment: str = "",
	notify: bool = True,
) -> Any:
	"""Open one register row (idempotent per tender + type + subject while
	open) and alert its holder(s)."""
	role = REGISTER[task_type][0]
	filters = {"tender": root.name, "task_type": task_type, "status": "Open"}
	if subject_id:
		filters["subject_id"] = subject_id
	existing = frappe.db.get_value("Tender Task", filters, "name")
	if existing:
		return frappe.get_doc("Tender Task", existing)
	task = envelope.insert(
		frappe.get_doc(
			{
				"doctype": "Tender Task", "tender": root.name, "tender_version": version.name if version else None, "task_type": task_type, "business_role": role,
				"holder": holder or None, "sender": sender or None, "comment": comment or "", "subject_type": subject_type, "subject_id": subject_id, "status": "Open",
				"task_token": envelope.token(), "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
	)
	if notify:
		_notify(root, task)
	return task


def title_for(root, task) -> str:
	return REGISTER[cstr(task.task_type)][1].format(**_labels(root, task))


def waiting_title_for(root, task) -> str:
	template = REGISTER[cstr(task.task_type)][2]
	return template.format(**_labels(root, task)) if template else ""


def _labels(root, task) -> dict[str, str]:
	from kentender_procurement.tenders.services import lifecycle

	subject = subject_reference(task)
	affected = ""
	task_key = ""
	if cstr(task.task_type) == CORRECT_RETURNED and task.tender_version:
		predecessor = cstr(frappe.db.get_value("Tender Version", task.tender_version, "predecessor_version"))
		affected = cstr(frappe.db.get_value("Tender Version", predecessor, "return_affected_task")) if predecessor else ""
		task_key = lifecycle.AFFECTED_TASK_KEYS.get(affected, "requirements")
	is_addendum = cstr(task.subject_type) == "Tender Addendum"
	holder = holder_label(task)
	return {
		"ref": cstr(root.tender_reference), "subject": subject, "holder": holder, "task": affected or "Supplier and contract requirements", "task_key": task_key,
		"subject_label": f"addendum {subject}" if is_addendum else f"Tender {cstr(root.tender_reference)}",
		"channel_waiting": (f"Waiting for addendum {subject} to be published" if is_addendum else f"Waiting for {holder} to confirm publication of Tender {cstr(root.tender_reference)}"),
	}


def subject_reference(task) -> str:
	subject_type, subject_id = cstr(task.subject_type), cstr(task.subject_id)
	if subject_type == "Tender Addendum" and subject_id:
		return cstr(frappe.db.get_value("Tender Addendum", subject_id, "addendum_reference"))
	if subject_type == "Procurement Requisition" and subject_id:
		return cstr(frappe.db.get_value("Procurement Requisition", subject_id, "requisition_reference") or subject_id)
	return subject_id


def route_for(root, task) -> list[str]:
	segment = REGISTER[cstr(task.task_type)][4].format(**_labels(root, task))
	route = [PAGE, cstr(root.tender_reference)]
	if segment:
		route.append(segment)
	if segment in ("addenda", "clarifications") and cstr(task.subject_id):
		route.append(cstr(task.subject_id))
	if cstr(task.task_type) == REQUISITION_CORRECTION:
		reference = subject_reference(task)
		return ["procurement-requisitions", reference] if reference else route
	return route


def _notify(root, task) -> None:
	from kentender_core.services.notification_service import emit_notification_log

	title = title_for(root, task)
	message = cstr(task.comment) or title
	for user in holders_of(task):
		emit_notification_log(
			for_user=user, subject=title, message=message, document_type="Tender", document_name=root.name, event_type="Alert",
			entity_scope="Tenders", route="/app/" + "/".join(route_for(root, task)), correlation_key=f"tender-task:{task.name}", from_user=cstr(task.sender) or None,
		)


def close(task, *, status: str = "Completed", decision: str = "") -> None:
	values: dict[str, Any] = {"status": status}
	if decision:
		values["decision"] = decision
	envelope.bump(task, **values)


def close_open(root, *, task_types: tuple[str, ...] = (), subject_id: str = "", status: str = "Completed", decision: str = "") -> int:
	filters: dict[str, Any] = {"tender": root.name, "status": "Open"}
	if task_types:
		filters["task_type"] = ("in", task_types)
	if subject_id:
		filters["subject_id"] = subject_id
	count = 0
	for name in frappe.get_all("Tender Task", filters=filters, pluck="name"):
		close(frappe.get_doc("Tender Task", name), status=status, decision=decision)
		count += 1
	return count
