# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.18 — requirements follow the items. A request that mixes kinds of equipment gets starting
rows targeted by category, applies without retargeting, is checked per item, re-checked when items change, and
freezes exactly which items each requirement covered (REQ118-AC-001 to AC-007, AC-010)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import frappe

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd
from kentender_procurement.procurement_requisitions.services import records
from kentender_procurement.procurement_requisitions.services import scope as req_scope
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase


def _line(view: dict, unit: str) -> dict:
	return next(r for r in view["amounts"] if r["contributing_org_unit"] == unit)


def _rows(requisition: str, state: str | None = None) -> list:
	package = records.load(requisition)[2]
	return [r for r in package.technical_requirements if state is None or r.row_state == state]


class _Mixed(RequisitionCase):
	"""100 laptops for one department and 50 monitors for the other, in one request."""

	def _mixed(self, *, laptops: int = 100, monitors: int = 50) -> tuple[str, str, str, str]:
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		view = fx.editor(requisition)
		alpha, beta = _line(view, fx.ou_alpha())["drawdown_line_id"], _line(view, fx.ou_beta())["drawdown_line_id"]
		fx.add_laptops(requisition, quantities={alpha: laptops})
		fx.add_laptops(requisition, quantities={beta: monitors}, item_name="Office monitors", category="Monitor")
		items = {i["equipment_category"]: i["requisition_item_id"] for i in fx.editor(requisition)["equipment"]["rows"]}
		return requisition, alpha, items["Laptop"], items["Monitor"]

	def _flat(self, requisition: str) -> dict[str, dict]:
		out = {}
		for g in fx.editor(requisition)["requirements"]["technical_groups"]:
			for r in g["rows"]:
				out[r["characteristic_key"]] = r
		return out


class TestStartingRowsFollowTheItems(_Mixed):
	def test_each_kind_gets_its_own_defaults_and_the_package_applies_without_retargeting(self):
		requisition, _, laptop, monitor = self._mixed()
		rows = self._flat(requisition)
		self.assertEqual(rows["electrical_compatibility"]["applies_to_scope"], "All items")
		for key in ("memory", "storage_capacity", "storage_type", "processor_requirement", "required_ports"):
			self.assertEqual((rows[key]["applies_to_scope"], rows[key]["applies_to_item_ids"]), ("Item", [laptop]), key)
		for key in ("display_resolution", "panel_size"):
			self.assertEqual((rows[key]["applies_to_scope"], rows[key]["applies_to_item_ids"]), ("Item", [monitor]), key)
		self.assertEqual(rows["display_resolution"]["display"], "Full HD")
		self.assertEqual(rows["panel_size"]["value"]["value"], "24")
		# nothing targeted at every item that does not apply to every item
		for key, row in rows.items():
			if row["applies_to_scope"] == "All items":
				self.assertTrue(all(req_scope.categories_of({"applies_to_scope": "All items"}, [{"requisition_item_id": "x", "equipment_category": c}]) for c in ("Laptop", "Monitor")))
		targets = fx.editor(requisition)["requirements"]["technical_targets"]
		self.assertEqual([t["title"] for t in targets], ["Shared requirements", "Business laptops", "Office monitors"])

		fx.apply_standard_package(requisition)  # no row is retargeted by hand
		package = records.load(requisition)[2]
		self.assertEqual(package.standard_package_review_state, "Reviewed")
		view = fx.editor(requisition)
		self.assertEqual({t["key"]: t["status"] for t in view["tasks"]}["requirements"], "Complete")
		self.assertFalse([f for f in view["findings"] if f["task"] == "requirements"])

	def test_a_laptop_only_request_is_unchanged(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition)
		rows = self._flat(requisition)
		self.assertEqual(len(rows), 11)
		self.assertEqual({r["applies_to_scope"] for r in rows.values()}, {"All items"})


class TestPerItemCompleteness(_Mixed):
	def test_clearing_a_required_row_leaves_the_item_reported_by_name_and_characteristic(self):
		requisition, *_ = self._mixed()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		for row in technical:
			if row["characteristic_key"] == "display_resolution":
				row["selected"] = False
		req = view["requirements"]
		cmd.apply_selected_requirement_package(requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"], technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		view = fx.editor(requisition)
		missing = [f for f in view["findings"] if f["code"] == "ITEM_SPECIFICATION_INCOMPLETE"]
		self.assertEqual([f["message"] for f in missing], ["Office monitors (Monitor) has no Display resolution requirement."])
		self.assertEqual(missing[0]["severity"], "Blocking")
		self.assertEqual({t["key"]: t["status"] for t in view["tasks"]}["requirements"], "Needs attention")

	def test_an_all_items_row_for_a_characteristic_that_does_not_apply_to_every_item_is_refused(self):
		requisition, *_ = self._mixed()
		view = fx.editor(requisition)
		with self.assertRaises(Exception) as ctx:
			cmd.add_technical_requirement(requisition=requisition, values={"characteristic_key": "memory", "value": 8, "applies_to_scope": "All items"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertIn("Memory does not apply to Monitor", str(ctx.exception))


class TestEditingAndCustomising(RequisitionCase):
	def _two_laptops(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition)
		fx.apply_standard_package(requisition)
		return requisition

	def test_customising_one_item_separates_it_and_changes_no_other(self):
		requisition = self._two_laptops()
		rows = [r for r in _rows(requisition) if r.characteristic_key == "storage_type"]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].applies_to_scope, "All items")
		a, b = [i.requisition_item_id for i in records.load(requisition)[2].items]
		view = fx.editor(requisition)
		cmd.customise_requirement_for_item(requisition=requisition, requirement_id=rows[0].technical_requirement_id, requisition_item_id=b, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		rows = {r.applies_to_id: r for r in _rows(requisition) if r.characteristic_key == "storage_type"}
		self.assertEqual(set(rows), {a, b})
		self.assertEqual({r.applies_to_scope for r in rows.values()}, {"Item"})
		self.assertEqual(json.loads(rows[b].applies_to_item_ids_json), [b])
		# the copy keeps the value; editing it changes that item only
		view = fx.editor(requisition)
		cmd.update_technical_requirement(requisition=requisition, technical_requirement_id=rows[b].technical_requirement_id, values={"value": "SSD"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		rows = {r.applies_to_id: r for r in _rows(requisition) if r.characteristic_key == "storage_type"}
		self.assertEqual(json.loads(rows[b].required_value_json)["value"], "SSD")
		self.assertEqual(json.loads(rows[a].required_value_json)["value"], "NVMe SSD")

	def test_customising_a_row_that_covers_one_item_is_refused(self):
		requisition = self._two_laptops()
		row = next(r for r in _rows(requisition) if r.characteristic_key == "storage_type")
		b = records.load(requisition)[2].items[1].requisition_item_id
		cmd.customise_requirement_for_item(requisition=requisition, requirement_id=row.technical_requirement_id, requisition_item_id=b, expected_record_version=fx.editor(requisition)["package_record_version"], idempotency_key=fx.key())
		with self.assertRaises(Exception):
			cmd.customise_requirement_for_item(requisition=requisition, requirement_id=next(r for r in _rows(requisition) if r.characteristic_key == "storage_type" and r.applies_to_id == b).technical_requirement_id, requisition_item_id=b, expected_record_version=fx.editor(requisition)["package_record_version"], idempotency_key=fx.key())


class TestItemChangesReconcile(_Mixed):
	def test_a_new_item_of_a_covered_kind_joins_its_rows_and_they_are_flagged_for_review(self):
		requisition, alpha, laptop, monitor = self._mixed(laptops=60)
		fx.apply_standard_package(requisition)
		view = fx.editor(requisition)
		cmd.add_same_specification_items(
			requisition=requisition, shared={"equipment_category": "Laptop", "item_name": "Business laptops"},
			rows=[{"drawdown_line_id": alpha, "quantity": 40, "intended_use": "Field deployment for the department"}],
			expected_record_version=view["package_record_version"], idempotency_key=fx.key(),
		)
		package = records.load(requisition)[2]
		new = next(i.requisition_item_id for i in package.items if i.requisition_item_id not in (laptop, monitor))
		storage = next(r for r in package.technical_requirements if r.characteristic_key == "storage_type")
		self.assertEqual(sorted(json.loads(storage.applies_to_item_ids_json)), sorted([laptop, new]))
		self.assertEqual(storage.row_state, "Needs review")
		display = next(r for r in package.technical_requirements if r.characteristic_key == "display_resolution")
		self.assertEqual((display.row_state, json.loads(display.applies_to_item_ids_json)), ("Confirmed", [monitor]), "the monitors' rows are untouched")
		self.assertEqual(package.standard_package_review_state, "Review required")
		view = fx.editor(requisition)
		self.assertTrue([f for f in view["findings"] if f["code"] == "ROW_NEEDS_REVIEW"])
		self.assertEqual({t["key"]: t["status"] for t in view["tasks"]}["requirements"], "Needs attention")
		fx.apply_standard_package(requisition)  # confirming clears it
		self.assertFalse([r for r in _rows(requisition) if r.row_state == "Needs review"])
		self.assertEqual(records.load(requisition)[2].standard_package_review_state, "Reviewed")

	def test_removing_the_only_item_of_a_kind_takes_its_rows_with_it(self):
		requisition, _, laptop, monitor = self._mixed()
		fx.apply_standard_package(requisition)
		view = fx.editor(requisition)
		cmd.remove_requisition_item(requisition=requisition, requisition_item_id=monitor, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		keys = {r.characteristic_key for r in _rows(requisition, "Confirmed")}
		self.assertNotIn("display_resolution", keys)
		self.assertNotIn("panel_size", keys)
		self.assertIn("storage_type", keys)

	def test_a_new_kind_gets_proposed_rows_for_its_own_items_only(self):
		requisition, alpha, laptop, monitor = self._mixed()
		fx.apply_standard_package(requisition)
		proposed = [r for r in _rows(requisition, "Proposed")]
		self.assertEqual(proposed, [], "every characteristic is already covered for every item")


class TestFrozenAndHandedOff(_Mixed):
	def test_the_lock_records_every_row_s_items_and_the_handoff_carries_them(self):
		requisition, alpha, laptop, monitor = self._mixed()
		fx.fill_request_information(requisition)
		fx.enter_estimates(requisition)
		fx.apply_standard_package(requisition)
		fx.send(requisition)
		fx.submit_as_hod(requisition)
		package = records.load(requisition)[2]
		for row in package.technical_requirements + package.acceptance_requirements:
			self.assertTrue(json.loads(row.applies_to_item_ids_json), f"{row.name} records its items at lock")
		authorised = fx.authorise(requisition)
		frappe.set_user("Administrator")
		payload = json.loads(frappe.get_doc("Authorised Requisition Handoff", authorised["handoff"]).payload_json)
		self.assertEqual(payload["handoff_version"], "1.5")
		by_key = {r["characteristic_key"]: r for r in payload["technical_requirements"]}
		self.assertEqual(by_key["storage_type"]["applies_to_item_ids"], [laptop])
		self.assertEqual(by_key["display_resolution"]["applies_to_item_ids"], [monitor])
		self.assertEqual(sorted(by_key["electrical_compatibility"]["applies_to_item_ids"]), sorted([laptop, monitor]))
		for family in ("technical_requirements", "acceptance_requirements"):
			self.assertTrue(all("applies_to_item_ids" in r for r in payload[family]))


class TestEarlierVersionsKeepTheirDigest(RequisitionCase):
	def test_a_row_with_no_item_list_dumps_exactly_as_before(self):
		row = SimpleNamespace(as_dict=lambda: {"name": "x", "technical_requirement_id": "TECH-001", "applies_to_scope": "All items", "applies_to_item_ids_json": None})
		with_list = SimpleNamespace(as_dict=lambda: {"technical_requirement_id": "TECH-002", "applies_to_scope": "Item", "applies_to_item_ids_json": '["RQI-001"]'})
		doc = SimpleNamespace(get=lambda field: [row, with_list])
		out = records.child_rows(doc, "technical_requirements")
		self.assertEqual(out[0], {"technical_requirement_id": "TECH-001", "applies_to_scope": "All items"})
		self.assertEqual(out[1]["applies_to_item_ids_json"], '["RQI-001"]')

	def test_legacy_rows_are_read_from_their_scope(self):
		items = [{"requisition_item_id": "A", "equipment_category": "Laptop"}, {"requisition_item_id": "B", "equipment_category": "Monitor"}]
		self.assertEqual(req_scope.item_ids({"applies_to_scope": "All items"}, items), ["A", "B"])
		self.assertEqual(req_scope.item_ids({"applies_to_scope": "Item", "applies_to_id": "B"}, items), ["B"])
		self.assertEqual(req_scope.item_ids({"applies_to_scope": "Service", "applies_to_id": "SVC-001"}, items), [])
