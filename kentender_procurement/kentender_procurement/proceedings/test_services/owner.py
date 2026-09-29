# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A simulated Proceedings owner for contract tests only (PRC-CHG-001 v0.9
§13 PRC-S01/S02, §15: "The binding seam shall be exercised by a
deterministic simulated owner before integration"). It is injected through
`frappe.flags.kt_prc_owner_adapters` by a test and is never registered on a
hook, so no page or API can reach it. A pass against it is shared-service
evidence only, never a Bid Opening ceremony."""

from __future__ import annotations

from kentender_procurement.proceedings.services.owners import SYSTEM_ACTOR


class SimulatedOwner:
	OWNER_TYPE = "Simulated Bid Opening"

	def __init__(self, *, chair: str, recorder: str, members: list[str], readers: list[str]):
		self.chair, self.recorder = chair, recorder
		self.members, self.readers = set(members), set(readers)
		self.owners: set[str] = set()

	def add(self, owner_id: str) -> None:
		self.owners.add(owner_id)

	def exists(self, owner_id: str) -> bool:
		return owner_id in self.owners

	def allows(self, owner_id: str, user: str, capacity: str) -> bool:
		if user == SYSTEM_ACTOR:
			return capacity == "owner"
		return {"owner": user == self.chair, "recorder": user == self.recorder, "member": user in self.members, "reader": user in self.readers}[capacity]
