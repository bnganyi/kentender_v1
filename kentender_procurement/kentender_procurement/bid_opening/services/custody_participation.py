# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ConfirmOpeningCustody (BOP-CHG-001 v0.10 §5, §7; binding row → custody
adapter and PRC pre-session `AppendProceedingEvent`; TRUST-ADR-001 v0.1 §2
"Joint opening release"; plan D18).

After the box has closed, each appointed member's authenticated join is
their participation in the joint release, confirmed with the custody service
against the exact closed manifest and roster; no separate button is drawn
(BOP-CHG-001 v0.10 §10 "without a fabricated security approval control";
§11 "appears as a member action only if the final method requires one").
The same step applies to an empty and a nonempty box, so nothing about it
reveals the bid count. A changed roster, a changed manifest or a departed
member makes that participation stale. Valid participation needs at least
two distinct members, one of them the independent member."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_opening.services import appointment, clock, custody, prc, records
from kentender_procurement.services import sequence

PARTICIPATION = "Opening Custody Participation"


def confirm(doc, user: str, key: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	row = appointment.member(doc.name, user)
	roster = appointment.roster_digest(doc.name)
	number = sequence.next_count(PARTICIPATION, {"opening_case": doc.name})
	participation_id = f"{doc.opening_id}-CUS-{number:03d}"
	answer = custody.confirm_participation(tender=doc.tender, member=user, independent=bool(row and row["is_independent"]), manifest_digest=doc.manifest_digest,
		roster_digest=roster, correlation_id=participation_id)
	records.insert(frappe.get_doc({
		"doctype": PARTICIPATION, "participation_id": participation_id, "opening_case": doc.name, "member_user": user, "manifest_digest": doc.manifest_digest,
		"roster_digest": roster, "confirmed_at": clock.now(), "participation_reference": answer.get("participation_reference") or "",
		"correlation_id": answer["correlation_id"], "outcome": answer["outcome"], "stale": 0,
	}))
	events.append_event(**prc.ref(doc.name), event_type="CustodyParticipation", source="Owner", owner_event_id=f"custody:{participation_id}",
		payload={"member": user, "outcome": answer["outcome"]}, note=f"{row['full_name'] if row else user}: {answer['outcome']}", idempotency_key=prc.key(key, f"custody:{user}"),
		actor=prc.SYSTEM_ACTOR)
	return answer


def mark_stale(case: str, user: str | None = None) -> None:
	filters = {"opening_case": case, "stale": 0}
	if user:
		filters["member_user"] = user
	for name in frappe.get_all(PARTICIPATION, filters=filters, pluck="name"):
		row = frappe.get_doc(PARTICIPATION, name)
		row.stale = 1
		records.save(row)


def valid(doc) -> bool:
	if not doc.manifest_digest:
		return False
	roster = {m["member_user"]: m for m in appointment.roster(doc.name)}
	rows = frappe.get_all(PARTICIPATION, filters={"opening_case": doc.name, "stale": 0, "outcome": custody.VERIFIED, "manifest_digest": doc.manifest_digest,
		"roster_digest": appointment.roster_digest(doc.name)}, pluck="member_user")
	members = {u for u in rows if u in roster}
	return len(members) >= 2 and any(roster[u]["is_independent"] for u in members)
