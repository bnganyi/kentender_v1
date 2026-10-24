# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dispatch of a notice or message to the other party (CM-CHG-001 v0.8 sections 5.7, 5.15, 7 `SendContractCorrespondence`).

A message is **delivered** only when there is evidence it reached the party. The supplier's channel here is their own portal: the message is placed where their representatives read it and each is told in
the platform's own notifications, and the delivery is kept with a reference. The reference is derived from the operation identity, so a retry of the same message finds the same delivery and sends nothing
twice (`find`). A failure raises `Failed`; the caller keeps the message Unsent and retries it. Tests make the channel fail with `frappe.flags.kt_cm_dispatch_fault = "fail"`."""

from __future__ import annotations

import hashlib

import frappe

from kentender_contracts.services import events

EVENT = "Notice delivered"


class Failed(Exception):
	"""The channel could not deliver."""


def _reference(identity: str) -> str:
	return "DLV-" + hashlib.sha256(identity.encode()).hexdigest()[:10].upper()


def find(identity: str) -> str | None:
	"""The delivery an operation identity already made, so a retry is never a second send."""
	reference = _reference(identity)
	return reference if frappe.db.exists("Contract Event", {"event_type": EVENT, "summary": ["like", f"%{reference}%"]}) else None


def deliver(identity: str, *, case: str, recipients: list[str], subject: str, text: str) -> str:
	if frappe.flags.get("kt_cm_dispatch_fault") == "fail":
		raise Failed("The message could not be delivered.")
	if not recipients:
		raise Failed("The supplier has no one to receive it.")
	reference = _reference(identity)
	for user in recipients:
		try:
			frappe.get_doc({"doctype": "Notification Log", "for_user": user, "type": "Alert", "subject": subject, "email_content": text, "document_type": "Contract Case", "document_name": case}).insert(ignore_permissions=True)
		except Exception:  # noqa: BLE001 - a notification that cannot be shown does not undo the delivery
			frappe.log_error(title="Contract Management could not notify a recipient")
	events.record(case, EVENT, "Administrator", f"{subject}: delivered to {len(recipients)} recipient(s) ({reference}).", reference=reference, identity=identity, recipients=recipients)
	return reference
