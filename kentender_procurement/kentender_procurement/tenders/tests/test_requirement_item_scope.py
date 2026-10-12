# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.18 §5.7A / §9.2 — the exact items each requirement covers survive into the Tender: a handoff 1.5
snapshot, a handoff 1.4 snapshot read from scope, the goods lines the serializer draws, the STD projection helpers
and the evaluation labels (REQ118-AC-007 to AC-009). Pure: no database."""

from __future__ import annotations

import copy
import json
import unittest

from kentender_procurement.bid_evaluation.services.aggregate import requirement_label
from kentender_procurement.std_templates.compiler import projection as proj
from kentender_procurement.tenders.services import serializer, snapshot as snap
from kentender_procurement.tenders.tests import sample

LAPTOP, MONITOR = "SRC-MOH-033-001", "SRC-MOH-033-002"


def _row(tid: str, key: str, comparison: str, value, unit: str, ids: list[str], scope: str, target: str = "") -> dict:
	return {"technical_requirement_id": tid, "applies_to_scope": scope, "applies_to_id": target, "applies_to_item_ids": ids, "characteristic_key": key, "comparison": comparison, "required_value_json": json.dumps(value), "unit": unit}


def mixed_payload(*, laptops: int = 100, monitors: int = 50) -> dict:
	"""100 laptops for one department and 50 monitors for the other, as handoff 1.5."""
	payload = sample.handoff_payload()
	payload["handoff_version"] = "1.5"
	payload["items"][0].update({"quantity": laptops})
	payload["items"][1].update({"equipment_category": "Monitor", "item_name": "Office monitors", "quantity": monitors})
	both = [LAPTOP, MONITOR]
	rows = [
		_row("TECH-001", "electrical_compatibility", "Required", {"value": "Yes"}, "", both, "All items"),
		_row("TECH-002", "new_unused_equipment", "Required", {"value": "Yes"}, "", both, "All items"),
	]
	for tid, key, comparison, value, unit in sample.TECHNICAL[2:]:
		rows.append(_row(tid, key, comparison, value, unit, [LAPTOP], "Item", LAPTOP))
	rows.append(_row("TECH-012", "display_resolution", "Minimum", {"value": "Full HD"}, "", [MONITOR], "Item", MONITOR))
	rows.append(_row("TECH-013", "panel_size", "Minimum", {"value": "24"}, "inches", [MONITOR], "Item", MONITOR))
	payload["technical_requirements"] = rows
	for a in payload["acceptance_requirements"]:
		a["applies_to_item_ids"] = both
	return payload


class _Fake:
	def __init__(self, payload: dict):
		self.name, self.payload_json, self.handoff_digest = "RQH-X", json.dumps(payload), "d" * 64


def snapshot_of(payload: dict) -> dict:
	return snap.build(_Fake(payload))[0]


class TestMixedRequestInTheTender(unittest.TestCase):
	def test_laptops_and_monitors_are_separate_goods_lines_with_their_own_technical_requirements(self):
		lines = serializer.goods_lines(snapshot_of(mixed_payload()))
		self.assertEqual([(l["description"], l["equipment_category"], l["quantity"]) for l in lines], [("Business laptops", "Laptop", "100"), ("Office monitors", "Monitor", "50")])
		laptops, monitors = lines
		self.assertEqual(set(laptops["technical_requirement_ids"]), {f"TECH-{n:03d}" for n in range(1, 12)})
		self.assertEqual(set(monitors["technical_requirement_ids"]), {"TECH-001", "TECH-002", "TECH-012", "TECH-013"})
		self.assertEqual([s["requisition_item_id"] for s in laptops["source_items"]], [LAPTOP])

	def test_each_technical_row_names_what_it_applies_to(self):
		rows = {r["characteristic_key"]: r for r in serializer.technical_rows(snapshot_of(mixed_payload()))}
		self.assertEqual(rows["electrical_compatibility"]["applies_to"], "All items")
		self.assertEqual(rows["storage_type"]["applies_to"], "Business laptops")
		self.assertEqual(rows["display_resolution"]["applies_to"], "Office monitors")

	def test_a_requirement_set_keeps_two_identical_laptop_items_on_one_line_and_a_customised_item_splits(self):
		payload = sample.handoff_payload()
		payload["handoff_version"] = "1.5"
		both = [LAPTOP, MONITOR]  # the sample's two items are both laptops here
		payload["technical_requirements"] = [
			{**r, "applies_to_item_ids": both, "applies_to_scope": "Items", "applies_to_id": LAPTOP} if r["characteristic_key"] == "storage_type" else {**r, "applies_to_item_ids": both}
			for r in payload["technical_requirements"]
		]
		lines = serializer.goods_lines(snapshot_of(payload))
		self.assertEqual(len(lines), 1)
		self.assertEqual(lines[0]["quantity"], "250")
		self.assertEqual([s["requisition_item_id"] for s in lines[0]["source_items"]], both, "departmental quantities and lineage kept")
		# customise the second item's storage type: its row now covers it alone, the shared row only the first
		split = copy.deepcopy(payload)
		for r in split["technical_requirements"]:
			if r["characteristic_key"] == "storage_type":
				r.update({"applies_to_scope": "Item", "applies_to_id": LAPTOP, "applies_to_item_ids": [LAPTOP]})
		split["technical_requirements"].append(_row("TECH-099", "storage_type", "One of", {"value": "SSD"}, "", [MONITOR], "Item", MONITOR))
		lines = serializer.goods_lines(snapshot_of(split))
		self.assertEqual(len(lines), 2)

	def test_a_handoff_14_snapshot_is_read_from_scope(self):
		payload = sample.handoff_payload()
		payload["handoff_version"] = "1.4"
		snapshot = snapshot_of(payload)
		self.assertTrue(all(r["applies_to_item_ids"] == [LAPTOP, MONITOR] for r in snapshot["technical_requirements"]))
		self.assertEqual(len(serializer.goods_lines(snapshot)), 1, "unchanged: one 250-Each line")
		scoped = sample.handoff_payload()
		scoped["technical_requirements"][2].update({"applies_to_scope": "Item", "applies_to_id": LAPTOP})
		self.assertEqual(snapshot_of(scoped)["technical_requirements"][2]["applies_to_item_ids"], [LAPTOP])


class TestProjectionAndEvaluation(unittest.TestCase):
	def _projection(self) -> dict:
		snapshot = snapshot_of(mixed_payload())
		return {
			"items": [{"requisition_item_id": i["requisition_item_id"], "item_name": i["item_name"]} for i in snapshot["items"]],
			"technical_requirements": [{"technical_requirement_id": r["technical_requirement_id"], "applies_to_scope": r["applies_to_scope"], "applies_to_id": r["applies_to_id"], "applies_to_item_ids": r["applies_to_item_ids"]} for r in snapshot["technical_requirements"]],
			"related_services": [{"service_requirement_id": "SVC-001", "service_type": "Installation", "applies_to_scope": "All items", "applies_to_id": ""}],
		}

	def test_the_compiler_reads_the_exact_items(self):
		p = self._projection()
		self.assertEqual(proj.technical_ids_for_item(MONITOR, p), ["TECH-001", "TECH-002", "TECH-012", "TECH-013"])
		self.assertEqual(proj.applies_to_label(p["technical_requirements"][2], p), "Business laptops")
		self.assertEqual(proj.applies_to_label({"applies_to_scope": "Items", "applies_to_id": LAPTOP, "applies_to_item_ids": [LAPTOP, MONITOR]}, p), "Business laptops, Office monitors")

	def test_an_acceptance_check_on_a_service_is_a_valid_scope(self):
		p = self._projection()
		self.assertEqual(proj.applies_to_label({"applies_to_scope": "Service", "applies_to_id": "SVC-001"}, p), "Installation")

	def test_a_row_without_a_list_is_read_from_its_scope(self):
		p = self._projection()
		self.assertEqual(proj.row_item_ids({"applies_to_scope": "All items", "applies_to_id": ""}, p), [LAPTOP, MONITOR])
		self.assertEqual(proj.row_item_ids({"applies_to_scope": "Item", "applies_to_id": MONITOR}, p), [MONITOR])

	def test_evaluation_names_the_items_when_a_requirement_covers_only_some(self):
		self.assertEqual(requirement_label("RR-TECHNICAL", {"label": "Storage type", "applies_to": "Business laptops"}), "Storage type — Business laptops")
		self.assertEqual(requirement_label("RR-TECHNICAL", {"label": "Storage type", "applies_to": "All items"}), "Storage type")
		self.assertEqual(requirement_label("RR-ACCEPTANCE", {"check_type": "Quantity", "applies_to": "Office monitors"}), "Acceptance: Quantity — Office monitors")


if __name__ == "__main__":
	unittest.main()
