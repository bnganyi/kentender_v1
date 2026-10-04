# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A simulated multi-session owner for contract tests only (EVL-CHG-001 v0.4
plan D4, Phase 2). It is injected through `frappe.flags.kt_prc_owner_adapters`
by a test and is never registered on a hook, so no page or API can reach it.
A pass against it is shared-service evidence only, never an evaluation."""

from __future__ import annotations

from kentender_procurement.proceedings.services.owners import SYSTEM_ACTOR


class SimulatedEvaluationOwner:
	OWNER_TYPE = "Simulated Bid Evaluation"
	proceeding_type = "Bid Evaluation"

	def __init__(self, *, chair: str, secretary: str, members: list[str], readers: list[str]):
		self.chair, self.secretary = chair, secretary
		self.members, self.readers = set(members), set(readers)
		self.owners: set[str] = set()

	def add(self, owner_id: str) -> None:
		self.owners.add(owner_id)

	def exists(self, owner_id: str) -> bool:
		return owner_id in self.owners

	def allows(self, owner_id: str, user: str, capacity: str) -> bool:
		if user == SYSTEM_ACTOR:
			return capacity == "owner"
		return {
			"owner": user == self.chair,
			"recorder": user in (self.chair, self.secretary),
			"member": user in self.members,
			"reader": user in self.readers,
		}[capacity]
