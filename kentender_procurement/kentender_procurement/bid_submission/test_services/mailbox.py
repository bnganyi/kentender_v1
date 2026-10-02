# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Test Mailbox (BDS-CHG-001 v0.8 owner decision OD-C), on the supplier
message transport hooks (`kt_supplier_account_message_transports` for Account
verification links, `kt_bds_supplier_message_transports` for bid hand-offs).

On a test environment it keeps each message — recipient, subject, body and
any link — in a file under the site's private folder, outside every DocType,
so a browser world can open a verification link the way a person would. On
any other site it declines (returns nothing) and the caller's real transport
is used. It is not a mail service and never claims delivery to an inbox. A
dev site may set `kt_test_mailbox_also_email` to queue each message as an email
too, for people testing by hand; the result still says test mailbox."""

from __future__ import annotations

import json
import os
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.bid_submission.services import simulation

DELIVERED = "Delivered to the test mailbox (simulation)"
# Site config switch (dev only): also queue each kept message as a real email,
# so a person testing in a browser can read the link in an inbox (Mailpit).
ALSO_EMAIL_KEY = "kt_test_mailbox_also_email"


def _path() -> str:
	return frappe.get_site_path("private", "kt_test_mailbox", "messages.jsonl")


def _read() -> list[dict[str, Any]]:
	path = _path()
	if not os.path.exists(path):
		return []
	with open(path, encoding="utf-8") as handle:
		return [json.loads(line) for line in handle if line.strip()]


def deliver(message: dict[str, Any]) -> dict[str, str] | None:
	if not simulation.enabled():
		return None
	path = _path()
	os.makedirs(os.path.dirname(path), exist_ok=True)
	row = {"to": cstr(message.get("to")).lower(), "subject": cstr(message.get("subject")), "body": cstr(message.get("body")), "link": cstr(message.get("link")), "at": cstr(now_datetime())}
	with open(path, "a", encoding="utf-8") as handle:
		handle.write(json.dumps(row, sort_keys=True) + "\n")
	if frappe.conf.get(ALSO_EMAIL_KEY):
		frappe.sendmail(recipients=[message["to"]], subject=row["subject"], message=row["body"], delayed=True)
	return {"result": DELIVERED}


def latest(to: str) -> dict[str, Any] | None:
	"""The newest message kept for `to`, or None."""
	wanted = cstr(to).lower()
	rows = [row for row in _read() if row["to"] == wanted]
	return rows[-1] if rows else None


def clear(to: str = "") -> int:
	"""Forget the messages for `to` (every message when empty); returns how many."""
	rows = _read()
	keep = [row for row in rows if to and row["to"] != cstr(to).lower()]
	path = _path()
	if os.path.exists(path):
		with open(path, "w", encoding="utf-8") as handle:
			handle.writelines(json.dumps(row, sort_keys=True) + "\n" for row in keep)
	return len(rows) - len(keep)
