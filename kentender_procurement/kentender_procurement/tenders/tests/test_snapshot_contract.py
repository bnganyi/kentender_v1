# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Requisitions handoff v1.4 (REQ-CHG-001 v1.11/v1.12) as Tenders reads
it. The 24 Sep 2026 REQ rebuild renamed `reservation_category_value` to
`reservation_category`, `strategic_objective` to `strategic_objective_id`,
grouped the six warranty fields under `warranty_support` and replaced
`decisions` with `departmental_certification` / `procurement_authorisation`.
Tenders silently read blanks — a Youth requisition became an unreserved
Tender with no warranty months — so the snapshot translates at the seam.
DB-free."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from kentender_procurement.tenders.services import snapshot as snap

V14_PAYLOAD = {
	"handoff_version": "1.4",
	"requisition_reference": "REQ-MOH-2027-002-001",
	"strategic_objective_id": "SO-1",
	"strategic_objective_path": "Strengthen interoperable national digital health services",
	"reservation_category": "Youth",
	"warranty_support": {
		"minimum_warranty_months": 36, "onsite_support_required": 1, "maximum_support_response_hours": 8,
		"manufacturer_support_required": 1, "service_location_constraint": "Within Kenya", "support_description": "Escalation contacts.",
	},
	"departmental_certification": {"lead_org_unit_id": "OU-1", "actor": "peter.kimani@moh.example.test", "capacity": "Head of User Department", "decided_at": "2027-03-01 09:00:00", "decision": "RQD-1"},
	"procurement_authorisation": {"actor": "charles.mutiso@moh.example.test", "capacity": "Head of Procurement Function", "decided_at": "2027-03-15 10:00:00", "decision": "RQD-2"},
	"items": [],
}


def handoff(payload: dict) -> SimpleNamespace:
	return SimpleNamespace(name="RQH-1", handoff_digest="d" * 64, payload_json=json.dumps(payload))


class TestHandoffV14(unittest.TestCase):
	def test_reservation_warranty_and_objective_reach_the_names_tenders_reads(self):
		snapshot, _digest = snap.build(handoff(V14_PAYLOAD))
		self.assertEqual(snapshot["reservation_category_value"], "Youth")
		self.assertEqual(snapshot["minimum_warranty_months"], 36)
		self.assertEqual(snapshot["maximum_support_response_hours"], 8)
		self.assertEqual(snapshot["service_location_constraint"], "Within Kenya")
		self.assertTrue(snapshot["onsite_support_required"] and snapshot["manufacturer_support_required"])
		self.assertEqual(snapshot["strategic_objective"], "SO-1")
		# the owner's own fields stay exactly as sent
		self.assertEqual(snapshot["reservation_category"], "Youth")
		self.assertEqual(snapshot["warranty_support"]["minimum_warranty_months"], 36)

	def test_the_two_requisition_decisions_are_carried(self):
		snapshot, _digest = snap.build(handoff(V14_PAYLOAD))
		self.assertEqual([d["decision"] for d in snapshot["decisions"]], ["RQD-1", "RQD-2"])
		self.assertEqual([d["capacity"] for d in snapshot["decisions"]], ["Head of User Department", "Head of Procurement Function"])

	def test_an_unreserved_requisition_stays_none(self):
		payload = dict(V14_PAYLOAD, reservation_category=None)
		snapshot, _digest = snap.build(handoff(payload))
		self.assertEqual(snapshot["reservation_category_value"], "None")

	def test_the_translation_is_deterministic(self):
		self.assertEqual(snap.build(handoff(V14_PAYLOAD))[1], snap.build(handoff(V14_PAYLOAD))[1])

	def test_the_start_preview_reads_the_same_translation(self):
		from kentender_procurement.tenders.services import handoff_gateway

		payload = handoff_gateway.payload_of(handoff(V14_PAYLOAD))
		self.assertEqual(payload["reservation_category_value"], "Youth")
		self.assertEqual(payload["minimum_warranty_months"], 36)
