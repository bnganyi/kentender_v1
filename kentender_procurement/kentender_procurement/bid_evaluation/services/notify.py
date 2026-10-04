# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Courtesy notices for Bid Evaluation work (EVL-CHG-001 v0.4 §7.3:
"Notification means in-product task plus a courtesy notice; notice delivery
does not prove task completion"; plan D11).

Each notice links to the evaluation route and carries a correlation key, so
the same event never notifies the same person twice. The work item itself is
derived from state by the My Work provider; a notice never clears it."""

from __future__ import annotations

from kentender_procurement.bid_evaluation.services import records


def route(doc) -> str:
	return f"/app/tenders/{doc.tender_reference}/evaluation"


def tell(doc, users: list[str], *, subject: str, message: str, key: str, event_type: str = "Bid evaluation") -> int:
	from kentender_core.services.notification_service import emit_notification_log

	sent = 0
	for user in dict.fromkeys(u for u in users if u):
		if emit_notification_log(for_user=user, subject=subject, message=message, document_type=records.CASE, document_name=doc.name, event_type=event_type,
				entity_scope="Bid Evaluation", route=route(doc), correlation_key=f"evl-{key}:{doc.name}:{user}"):
			sent += 1
	return sent
