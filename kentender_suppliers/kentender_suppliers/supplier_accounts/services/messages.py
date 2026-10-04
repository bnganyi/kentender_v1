# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Account messages (verification links). A transport is a callable
`(message) -> dict | None` registered on `kt_supplier_account_message_transports`;
the last one that takes the message wins (a transport returns None to
decline, as a test-environment double does on a real site). With none taking
it, Frappe's outgoing email queue is used and the result is only ever
"Queued" — never a delivery claim. Tests set
`frappe.flags.kt_account_message_transport` to capture messages."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_supplier_account_message_transports"


def email_transport(message: dict[str, Any]) -> dict[str, Any]:
	frappe.sendmail(recipients=[message["to"]], subject=message["subject"], message=message["body"], delayed=True)
	return {"result": "Queued"}


def send(message: dict[str, Any]) -> dict[str, Any]:
	override = frappe.flags.get("kt_account_message_transport")
	if override:
		return override(message)
	for path in reversed(frappe.get_hooks(HOOK) or []):
		answer = frappe.get_attr(path)(message)
		if answer:
			return answer
	return email_transport(message)
