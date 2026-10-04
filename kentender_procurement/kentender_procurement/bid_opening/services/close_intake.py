# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReceiveClosedBox (BOP-CHG-001 v0.10 §4, §7; binding row → BDS manifest and
PRC reference-only owner event while Pending; BOP-A01, BOP-A04).

After the deadline, the exact closed manifest attaches to the case once and
the Bid Submission hand-off is acknowledged. Proceedings receives only an
opaque reference (hand-off ID and digest), never a count or identity. The
case becomes Ready to open, and members already present take part in the
joint release. Nothing here is visible as a bid count before Start."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.bid_opening.services import clock, custody, custody_participation, prc, presence, records


def receive_closed_box(*, tender: str, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	name = records.case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	doc = frappe.get_doc(records.CASE, name)
	if doc.state != "Awaiting deadline" or clock.now() < get_datetime(doc.effective_deadline):
		return {"ok": True, "received": False, "state": doc.state}
	manifest = custody.closed_manifest(tender)
	if manifest is None:
		return {"ok": True, "received": False, "state": doc.state}
	key = idempotency_key or f"receive:{manifest['handoff_id']}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state != "Awaiting deadline":
			return records.summary(doc, received=False)
		events.append_event(**prc.ref(doc.name), event_type="ClosedManifestReference", source="Owner", owner_event_id=f"manifest:{manifest['handoff_id']}",
			payload={"handoff": manifest["handoff_id"], "digest": manifest["digest"]}, idempotency_key=prc.key(key, "manifest"), actor=prc.SYSTEM_ACTOR)
		custody.acknowledge(manifest["handoff_id"])
		doc.update({"manifest_handoff": manifest["handoff_id"], "manifest_digest": manifest["digest"], "manifest_received_at": clock.now(), "state": "Ready to open"})
		for user in presence.present_members(doc.name):
			custody_participation.confirm(doc, user, key)
		records.bump(doc)
		return records.summary(doc, received=True)

	return records.command("ReceiveClosedBox", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"handoff": manifest["handoff_id"]}, body=body)
