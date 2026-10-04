# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Notify a member who has not joined (BOP-CHG-001 v0.10 §8 BOP_MEMBER_ABSENT
recovery "show Notify [name] before Start"; board c2). The chair's reminder
is an in-app notice to that member; it records nothing about the opening and
never joins anyone."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_opening.services import appointment, records


def notify_member(*, tender: str, member: str, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_core.services.notification_service import emit_notification_log

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		chair = appointment.chair(doc.name)
		target = appointment.member(doc.name, member)
		if not chair or chair["member_user"] != user or not target:
			raise frappe.DoesNotExistError("Not found")
		title = f"Join opening for {doc.tender_reference}"
		sent = emit_notification_log(for_user=member, subject=title, message=f"{chair['full_name']} is waiting for you to join the opening.", document_type=records.CASE,
			document_name=doc.name, event_type="Join opening reminder", entity_scope="Bid Opening", route=f"/app/tenders/{doc.tender_reference}/opening",
			correlation_key=f"bop-join-reminder:{doc.name}:{member}:{idempotency_key}")
		return records.summary(doc, notified=bool(sent))

	return records.command("NotifyMember", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"member": member}, body=body)
