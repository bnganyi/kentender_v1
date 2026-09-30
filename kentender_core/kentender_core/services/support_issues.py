# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The platform support issue (EVL-CHG-001 v0.4 §6 "Technical issues reuse the
platform support-issue record and assignment route"; plan D12, owner decision
OD-B).

One issue per failed operation identity (`module:operation_correlation`). It
names the affected operation and a safe reference, never bids, findings or
other business content. It is assigned to the current holders of the
technical responsibility (Technical Operator), who repair the underlying
service with the existing technical tools and cannot decide any business
result. The issue resolves only when the owner reports that the failed
operation has succeeded; reading it or opening it clears nothing. A repeated
failure of the same operation reuses (and if needed reopens) the same issue.

Owners call this service; they never write the record directly. The first
owner is Bid Evaluation; Bid Opening and Bid Submission keep their own
incident records until they are moved here (FU-EVL-12)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr, now_datetime

ISSUE = "Support Issue"
TECHNICAL_OPERATOR = "Technical Operator"
TRANSPORT_HOOK = "kt_support_issue_transports"
FIELDS = ["issue_id", "issue_key", "module", "operation", "operation_correlation", "reference_doctype", "reference_name", "subject", "safe_detail",
	"holder_role", "holder_users_json", "reported_by", "status", "opened_at", "resolved_at", "resolution_note", "notification_state", "notification_attempts",
	"record_version"]


def _now():
	injected = getattr(frappe.flags, "kt_support_issue_clock", None) or getattr(frappe.flags, "kt_evl_clock", None)
	if injected:
		from frappe.utils import get_datetime

		return get_datetime(injected)
	from kentender_core.services.test_clock import current_instant

	instant = current_instant()
	if instant:
		from frappe.utils import get_datetime

		return get_datetime(instant)
	return now_datetime()


def _write(doc, insert: bool = False):
	doc.flags.kt_support_issue_command = True
	if insert:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return doc


def holders(role: str = TECHNICAL_OPERATOR) -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user", distinct=True)
	return sorted(u for u in users if frappe.db.get_value("User", u, "enabled"))


def issue_key(module: str, operation_correlation: str) -> str:
	return f"{cstr(module).strip()}:{cstr(operation_correlation).strip()}"


def _view(doc) -> dict[str, Any]:
	out = {f: doc.get(f) for f in FIELDS}
	out["holder_users"] = json.loads(doc.holder_users_json or "[]")
	return out


def get(issue_id: str) -> dict[str, Any] | None:
	if not issue_id or not frappe.db.exists(ISSUE, issue_id):
		return None
	return _view(frappe.get_doc(ISSUE, issue_id))


def find(module: str, operation_correlation: str) -> dict[str, Any] | None:
	name = frappe.db.get_value(ISSUE, {"issue_key": issue_key(module, operation_correlation)}, "name")
	return get(name) if name else None


def _notify(doc) -> None:
	users = json.loads(doc.holder_users_json or "[]")
	delivered = False
	for path in frappe.get_hooks(TRANSPORT_HOOK) or []:
		result = frappe.get_attr(path)(issue=_view(doc), users=list(users))
		if result is not None:
			delivered = bool(result.get("delivered"))
			break
	else:
		delivered = _notification_log(doc, users)
	doc.notification_attempts = cint(doc.notification_attempts) + 1
	if delivered:
		doc.notification_state = "Delivered"
	elif doc.notification_state != "Delivered":
		doc.notification_state = "Failed"


def _notification_log(doc, users: list[str]) -> bool:
	from kentender_core.services.notification_service import emit_notification_log

	sent = [u for u in users if emit_notification_log(
		for_user=u, subject=doc.subject, message=f"{doc.subject}. Reference {doc.issue_id}.", document_type=ISSUE, document_name=doc.issue_id,
		event_type="Support issue", entity_scope=cstr(doc.module), route=f"/app/support-issue/{doc.issue_id}", correlation_key=f"support-issue:{doc.issue_id}",
	)]
	return bool(sent)


def open_issue(*, module: str, operation: str, operation_correlation: str, subject: str, reference_doctype: str = "", reference_name: str = "",
		safe_detail: str = "", holder_role: str = TECHNICAL_OPERATOR, reported_by: str = "", fixture_namespace: str = "") -> dict[str, Any]:
	"""The one issue for this operation identity: created once, reopened on a
	repeated failure after resolution, notified to its holders."""
	key = issue_key(module, operation_correlation)
	if not cstr(operation_correlation).strip() or not cstr(subject).strip():
		raise ValueError("A support issue needs an operation identity and a subject.")
	name = frappe.db.get_value(ISSUE, {"issue_key": key}, "name")
	if name:
		doc = frappe.get_doc(ISSUE, name)
		if doc.status == "Resolved":
			doc.status, doc.resolved_at, doc.resolution_note = "Open", None, ""
			doc.record_version = cint(doc.record_version) + 1
			_notify(doc)
			_write(doc)
		return {**_view(doc), "created": False}
	count = frappe.db.count(ISSUE) + 1
	issue_id = f"SI-{_now().year}-{count:05d}"
	while frappe.db.exists(ISSUE, issue_id):
		count += 1
		issue_id = f"SI-{_now().year}-{count:05d}"
	doc = frappe.get_doc({
		"doctype": ISSUE, "issue_id": issue_id, "issue_key": key, "module": module, "operation": operation, "operation_correlation": operation_correlation,
		"reference_doctype": reference_doctype, "reference_name": reference_name, "subject": cstr(subject).strip(), "safe_detail": cstr(safe_detail).strip(),
		"holder_role": holder_role, "holder_users_json": json.dumps(holders(holder_role)), "reported_by": reported_by if reported_by and frappe.db.exists("User", reported_by) else None,
		"status": "Open", "opened_at": _now(), "notification_state": "Pending", "notification_attempts": 0, "record_version": 1,
		"fixture_namespace": fixture_namespace,
	})
	_notify(doc)
	_write(doc, insert=True)
	return {**_view(doc), "created": True}


def resolve_on_success(*, module: str, operation_correlation: str, note: str = "") -> dict[str, Any] | None:
	"""The owner reports that the failed operation has now succeeded."""
	name = frappe.db.get_value(ISSUE, {"issue_key": issue_key(module, operation_correlation)}, "name")
	if not name:
		return None
	doc = frappe.get_doc(ISSUE, name)
	if doc.status != "Resolved":
		doc.status, doc.resolved_at, doc.resolution_note = "Resolved", _now(), cstr(note).strip() or "The failed operation succeeded."
		doc.record_version = cint(doc.record_version) + 1
		_write(doc)
	return _view(doc)


def retry_notice(issue_id: str) -> dict[str, Any]:
	doc = frappe.get_doc(ISSUE, issue_id)
	_notify(doc)
	_write(doc)
	return _view(doc)


def for_holder(user: str) -> list[dict[str, Any]]:
	"""Open issues assigned to `user` by their current technical responsibility."""
	out = []
	for name in frappe.get_all(ISSUE, filters={"status": "Open"}, pluck="name", order_by="opened_at asc"):
		doc = frappe.get_doc(ISSUE, name)
		if user in holders(doc.holder_role):
			out.append(_view(doc))
	return out


def my_work_rows(user: str) -> dict[str, list[dict[str, Any]]]:
	"""The holder's work item for each open issue (EVL-CHG-001 v0.4 §7.3 last
	row); it clears only on repair and successful reconciliation."""
	rows = []
	for issue in for_holder(user):
		rows.append({
			"task_id": f"support-issue:{issue['issue_id']}", "task_type": "support_issue.resolve", "title": issue["subject"], "reference": issue["issue_id"],
			"module": cstr(issue["module"]), "stage": "Support", "fiscal_year": "", "organisation_unit": "", "assignment": issue["holder_role"], "status": "Assigned",
			"received_at": cstr(issue["opened_at"]), "due_at": "", "action_label": "View issue", "route": ["support-issue", issue["issue_id"]], "route_options": {},
			"concurrency_token": "", "can_claim": False, "can_open": True, "comment": "",
		})
	return {"assigned": rows, "claimable": [], "waiting": []}
