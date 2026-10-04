# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Proceedings contract-test world (PRC-CHG-001 v0.9 §13, §15): a
simulated owner with test-only actors and targets. A pass here is
shared-service evidence only, never a Bid Opening ceremony (PRC v0.9 §15)."""

from __future__ import annotations

from itertools import count
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.proceedings.services import attendance, attestation, events, finalize, lifecycle, minutes, reads
from kentender_procurement.proceedings.test_services import attestation as test_attestation
from kentender_procurement.proceedings.test_services.owner import SimulatedOwner

NS = "prc-contract-test"
OWNER_TYPE = SimulatedOwner.OWNER_TYPE
CHAIR = "prct.chair@example.test"  # chair and recorder
MEMBER = "prct.member@example.test"
INDEPENDENT = "prct.independent@example.test"
VISITOR = "prct.visitor@example.test"
OUTSIDER = "prct.outsider@example.test"
PEOPLE = {CHAIR: "Test Chair", MEMBER: "Test Member", INDEPENDENT: "Test Independent", VISITOR: "Test Visitor", OUTSIDER: "Test Outsider"}
ROSTER = [
	{"member_user": CHAIR, "full_name": "Test Chair", "designation": "Test designation", "committee_capacity": "Chair and recorder", "appointment_reference": "TEST-APPT-1"},
	{"member_user": MEMBER, "full_name": "Test Member", "designation": "Test designation", "committee_capacity": "Member", "appointment_reference": "TEST-APPT-1"},
	{"member_user": INDEPENDENT, "full_name": "Test Independent", "designation": "Test designation", "committee_capacity": "Independent member", "appointment_reference": "TEST-APPT-1"},
]


def ensure_people() -> None:
	for email, full_name in PEOPLE.items():
		if not frappe.db.exists("User", email):
			first, _, last = full_name.partition(" ")
			frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)
	frappe.db.commit()


def remove_people() -> None:
	for email in PEOPLE:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()


def wipe() -> None:
	"""Remove every record this world wrote (the always-remove-test-data rule)."""
	from kentender_core.utils.raw_delete import delete_rows

	names = frappe.get_all("Proceeding", filters={"fixture_namespace": NS}, pluck="name")
	if names:
		for doctype in ("Proceeding Attendance", "Proceeding Event", "Proceeding Attestation", "Proceeding Supplement", "Proceeding Session"):
			frappe.db.delete(doctype, {"proceeding": ("in", names)})
		delete_rows("Proceeding Minutes Version", {"proceeding": ("in", names)})
		delete_rows("Proceeding", {"name": ("in", names)})
	frappe.db.delete("Proceeding Command Journal", {"fixture_namespace": NS})
	frappe.db.commit()


class ProceedingsCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_people()
		cls.addClassCleanup(remove_people)
		cls.addClassCleanup(wipe)

	def setUp(self):
		self.owner = SimulatedOwner(chair=CHAIR, recorder=CHAIR, members=[r["member_user"] for r in ROSTER], readers=[CHAIR, MEMBER, INDEPENDENT])
		self._flag("kt_prc_owner_adapters", {OWNER_TYPE: self.owner})
		self._flag("kt_prc_fixture_namespace", NS)
		self._flag("kt_prc_signing_outcome", None)
		self._keys = count(1)
		self.addCleanup(wipe)

	def _flag(self, name: str, value) -> None:
		previous = frappe.flags.get(name)
		frappe.flags[name] = value
		self.addCleanup(lambda: frappe.flags.__setitem__(name, previous))

	def at(self, instant: str) -> None:
		self._flag("kt_prc_clock", instant)

	def key(self) -> str:
		return f"prct-{frappe.generate_hash(length=8)}-{next(self._keys)}"

	# -- owner-simulator conveniences ---------------------------------------
	def create(self, owner_id: str | None = None) -> dict[str, Any]:
		owner_id = owner_id or f"SIM-{frappe.generate_hash(length=6)}"
		self.owner.add(owner_id)
		self.at("2027-06-12 10:30:00")
		return lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id=owner_id, title="Test opening — synthetic bids only", idempotency_key=self.key(), actor=CHAIR)

	def version(self, result: dict[str, Any]) -> int:
		return int(frappe.db.get_value("Proceeding", result["proceeding"], "record_version"))

	def ref(self, result: dict[str, Any]) -> dict[str, Any]:
		row = frappe.db.get_value("Proceeding", result["proceeding"], ["owner_type", "owner_id", "record_version"], as_dict=True)
		return {"owner_type": row.owner_type, "owner_id": row.owner_id, "expected_version": int(row.record_version)}

	def start(self, result: dict[str, Any], *, at: str = "2027-06-12 11:00:12") -> dict[str, Any]:
		self.at(at)
		return lifecycle.start_proceeding(**self.ref(result), roster=ROSTER, custody_reference="TEST-CUSTODY-1", owner_event_id=f"start-{result['proceeding']}", idempotency_key=self.key(), actor=CHAIR)

	def owner_event(self, result: dict[str, Any], event_type: str, owner_event_id: str, *, payload: dict | None = None, **extra) -> dict[str, Any]:
		return events.append_event(**self.ref(result), event_type=event_type, source="Owner", owner_event_id=owner_event_id, payload=payload or {"event": owner_event_id},
			idempotency_key=self.key(), actor=CHAIR, **extra)

	def end(self, result: dict[str, Any], *, at: str = "2027-06-12 11:04:00", outcome_event: dict | None = None) -> dict[str, Any]:
		self.at(at)
		return lifecycle.end_proceeding(**self.ref(result), owner_event_id=f"end-{result['proceeding']}", outcome_event=outcome_event, idempotency_key=self.key(), actor=CHAIR)

	def targets(self, *, members=(CHAIR, MEMBER, INDEPENDENT), prefix: str = "T") -> list[dict[str, Any]]:
		rows = []
		for member in members:
			for n, (kind, page) in enumerate((("Minutes page", 1), ("Final minutes page", 1)), 1):
				rows.append({"target_id": f"{prefix}-{member.split('@')[0]}-{n}", "target_type": kind, "target_reference": "TEST-MINUTES", "page_number": page,
					"target_digest": frappe.generate_hash(length=16), "required_member": member, "roster_segment": 1})
		return rows

	def freeze(self, result: dict[str, Any], *, targets: list[dict] | None = None, content: str = "Test minutes version 1", at: str = "2027-06-12 11:07:00") -> dict[str, Any]:
		self.at(at)
		owner_events = [e.event_id for e in frappe.get_all("Proceeding Event", filters={"proceeding": result["proceeding"], "source": "Owner"}, fields=["event_id"])]
		return minutes.freeze_minutes(**self.ref(result), content=content, page_count=1, register_reference="TEST-REGISTER-1", register_digest="test-register-digest",
			event_ids=owner_events, targets=targets if targets is not None else self.targets(), idempotency_key=self.key(), actor=CHAIR)

	def attest_all(self, result: dict[str, Any], version: dict[str, Any], *, members=(CHAIR, MEMBER, INDEPENDENT)) -> None:
		for target in version["targets"]:
			if target["required_member"] in members:
				out = attestation.attest_target(**self.ref(result), minutes_version=version["minutes_version"], target_id=target["target_id"],
					target_digest=target["target_digest"], action="Initial", idempotency_key=self.key(), actor=target["required_member"])
				self.assertTrue(out["ok"], out)

	def current_minutes(self, result: dict[str, Any]) -> dict[str, Any]:
		return reads.read_proceeding(owner_type=OWNER_TYPE, owner_id=frappe.db.get_value("Proceeding", result["proceeding"], "owner_id"), user=CHAIR)["minutes"][-1]

	def assertCode(self, code: str, fn, *args, **kwargs):
		from kentender_procurement.proceedings.services.errors import ProceedingsError

		with self.assertRaises(ProceedingsError) as ctx:
			fn(*args, **kwargs)
		self.assertEqual(ctx.exception.code, code)
		return ctx.exception


__all__ = ["ProceedingsCase", "attendance", "attestation", "events", "finalize", "lifecycle", "minutes", "reads", "test_attestation"]
