# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Guarded reads of rendered pages (BOP-CHG-001 v0.10 §4, §6, §10.4 "Read opening
record · View bid pages").

- A bid's rendered pages: only after its lawful reveal, only to the committee
  members who take part in this opening (they sign them) and, after
  completion, to the Auditor for oversight. Never to an administrator, an
  attendee or another supplier.
- The frozen opening record's pages: to participants, the Accounting Officer,
  the Head of Procurement Function and the Auditor, once frozen.
Anyone else gets Not found. Reading records no event."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_opening.services import people, record, records, renders


def _participant(case: str, user: str) -> bool:
	return any(m["member_user"] == user for m in record.participants(case)) if frappe.db.get_value(records.CASE, case, "proceeding") else False


def bid_pages(*, tender: str, entry: str, user: str) -> dict[str, Any]:
	case = records.case_for(tender)
	row = frappe.db.get_value("Opening Entry", {"opening_case": case, "entry_id": entry}, ["entry_id", "receipt_reference"], as_dict=True) if case else None
	if not row or people.technical(user):
		raise frappe.DoesNotExistError("Not found")
	state = frappe.db.get_value(records.CASE, case, "state")
	allowed = _participant(case, user) or (state == "Opening complete" and people.holds(user, people.AUDITOR))
	content = renders.read(row.entry_id) if allowed else None
	if not content:
		raise frappe.DoesNotExistError("Not found")
	return {"filename": f"Bid {row.receipt_reference}.pdf", "content": content}


def record_pages(*, tender: str, minutes_version: str, user: str) -> dict[str, Any]:
	case = records.case_for(tender)
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding") if case else None
	version = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": proceeding, "minutes_version_id": minutes_version}, "version_number") if proceeding else None
	if not version or people.technical(user):
		raise frappe.DoesNotExistError("Not found")
	allowed = _participant(case, user) or any(people.holds(user, r) for r in (people.ACCOUNTING_OFFICER, people.HEAD_OF_PROCUREMENT, people.AUDITOR))
	content = renders.read(minutes_version) if allowed else None
	if not content:
		raise frappe.DoesNotExistError("Not found")
	return {"filename": f"Opening record version {version}.pdf", "content": content}
