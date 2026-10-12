# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.15 — enter each fact once, derive the rest.

Items are the only place a quantity is typed; a source line's requested
quantity is derived from them and bounded by what remains; the requester enters
one estimated total cost per source (no prefill, no rounding); a wholly unused
source is omitted at submission; the frozen values are what is authorised and
reserved. REQ115-AC-001 to AC-013 (the Planning/Budget/Tender halves of AC-009
are in tenders/tests/test_partial_requisition_remainder.py)."""

from __future__ import annotations

import json
from decimal import Decimal

import frappe

from kentender_procurement.patches import req_chg_001_v115_review_carried_over_drafts as carried_over_patch
from kentender_procurement.procurement_requisitions.services import draft_commands as cmd
from kentender_procurement.procurement_requisitions.services import goods_template, lifecycle, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

REASON = "Replace the processor wording with a measurable, supplier-neutral minimum."


def _line(view: dict, unit: str) -> dict:
	return next(r for r in view["amounts"] if r["contributing_org_unit"] == unit)


def _lines(requisition: str) -> list:
	return list(records.load(requisition)[1].drawdown_lines)


class TestNothingIsDefaulted(RequisitionCase):
	def test_prepare_requests_nothing_and_the_lead_follows_what_remains(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		root, version, _ = records.load(requisition)
		self.assertEqual(sorted((l.requested_quantity, l.requested_value) for l in version.drawdown_lines), [("0", "0.00"), ("0", "0.00")])
		self.assertEqual(root.lead_org_unit_id, fx.ou_alpha(), "no estimate yet: the established rule is applied to what remains (30m beats 20m)")
		view = fx.editor(requisition)
		self.assertEqual([(r["requested_quantity_value"], r["requested_value_value"]) for r in view["amounts"]], [("0", ""), ("0", "")])
		self.assertEqual(view["summary"]["estimated_total"], "", "no estimated total until the requester enters one")
		self.assertFalse(view["summary"]["review_required"])

	def test_the_lead_follows_the_entered_estimates_once_they_exist(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.add_laptops(requisition)
		view = fx.editor(requisition)
		alpha, beta = _line(view, fx.ou_alpha()), _line(view, fx.ou_beta())
		fx.enter_estimates(requisition, values={alpha["drawdown_line_id"]: "1000000.00", beta["drawdown_line_id"]: "5000000.00"})
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "lead_org_unit_id"), fx.ou_beta())


class TestItemsAreTheOnlyQuantity(RequisitionCase):
	def test_twenty_printers_typed_once_then_authorised_with_the_entered_estimate(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		line = fx.editor(requisition)["amounts"][0]["drawdown_line_id"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition, quantities={line: 20}, category="Printer", item_name="Office printers")
		view = fx.editor(requisition)
		row = view["amounts"][0]
		self.assertEqual(row["requested_quantity_value"], "20", "the requested quantity is derived from the item")
		self.assertEqual(view["summary"]["requested_quantity"], "20 Each")
		self.assertEqual(view["summary"]["after_quantity"], "230 Each")
		self.assertFalse([f for f in view["findings"] if f["code"] == "QUANTITY_MISMATCH"], "there is no mismatch to report")
		fx.enter_estimates(requisition, values={line: "3000000.00"})
		view = fx.editor(requisition)
		self.assertEqual(view["summary"]["estimated_total"], "KES 3,000,000.00")
		self.assertEqual(view["summary"]["after_value"], "KES 47,000,000.00")
		fx.apply_standard_package(requisition)
		fx.send(requisition)
		fx.submit_as_hod(requisition)
		authorised = fx.authorise(requisition)
		frappe.set_user("Administrator")
		_, version, _ = records.load(requisition)
		self.assertEqual([(l.requested_quantity, l.requested_value) for l in version.drawdown_lines], [("20", "3000000.00")], "the frozen values are the derived quantity and the entered estimate")
		payload = json.loads(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "payload_json"))
		self.assertEqual([(l["requested_quantity"], l["requested_value"]) for l in payload["drawdown_lines"]], [("20", "3000000.00")])
		reservations = frappe.get_all("Funding Reservation", filters={"drawdown_line_id": line}, fields=["original_amount"])
		self.assertEqual([Decimal(str(r.original_amount)) for r in reservations], [Decimal("3000000.00")], "the reservation equals the frozen estimate, not a recalculation")

	def test_the_requested_quantity_follows_every_add_edit_and_remove(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		line = fx.editor(requisition)["amounts"][0]["drawdown_line_id"]
		result = fx.add_laptops(requisition, quantities={line: 30})
		self.assertEqual(_lines(requisition)[0].requested_quantity, "30")
		item = result["items"][0]
		view = fx.editor(requisition)
		cmd.update_requisition_item(requisition=requisition, requisition_item_id=item, values={"quantity": 45}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertEqual(_lines(requisition)[0].requested_quantity, "45")
		view = fx.editor(requisition)
		cmd.remove_requisition_item(requisition=requisition, requisition_item_id=item, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertEqual(_lines(requisition)[0].requested_quantity, "0")

	def test_an_item_quantity_over_the_limit_is_refused_with_the_real_limit_and_creates_nothing(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		line = view["amounts"][0]["drawdown_line_id"]
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.add_laptops(requisition, quantities={line: 251})
		self.assertCode(ctx, "REQ_QUANTITY_EXCEEDS_AVAILABLE")
		self.assertIn("at most 250 Each", str(ctx.exception))
		self.assertIn("you entered 251", str(ctx.exception))
		self.assertEqual(records.load(requisition)[2].items, [])
		fx.add_laptops(requisition, quantities={line: 200})
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.add_laptops(requisition, quantities={line: 60}, item_name="More laptops")
		self.assertCode(ctx, "REQ_QUANTITY_EXCEEDS_AVAILABLE")
		self.assertIn("at most 50 Each", str(ctx.exception), "the limit is what is left after the items already entered")
		item = records.load(requisition)[2].items[0].requisition_item_id
		view = fx.editor(requisition)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.update_requisition_item(requisition=requisition, requisition_item_id=item, values={"quantity": 251}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_QUANTITY_EXCEEDS_AVAILABLE")
		self.assertEqual(_lines(requisition)[0].requested_quantity, "200")

	def test_the_requested_quantity_cannot_be_typed(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		line = view["amounts"][0]["drawdown_line_id"]
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_requisition_summary(
				requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": line, "requested_quantity": "40", "requested_value": "1.00"}]},
				expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key(),
			)
		self.assertCode(ctx, "REQ_CONTROL_INVALID")
		self.assertEqual(_lines(requisition)[0].requested_quantity, "0")


class TestTheEstimatedTotalCost(RequisitionCase):
	def _save(self, requisition: str, line: str, value, view: dict | None = None):
		view = view or fx.editor(requisition)
		return cmd.save_requisition_summary(
			requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": line, "requested_value": value}]},
			expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key(),
		)

	def test_it_is_exact_bounded_by_what_remains_and_never_rounded(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		line = fx.editor(requisition)["amounts"][0]["drawdown_line_id"]
		self._save(requisition, line, "3000000.00")
		self.assertEqual(_lines(requisition)[0].requested_value, "3000000.00")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			self._save(requisition, line, "50000000.01")
		self.assertCode(ctx, "REQ_ESTIMATE_EXCEEDS_ALLOWANCE")
		self.assertIn("KES 50,000,000.00", str(ctx.exception))
		self.assertIn("KES 50,000,000.01", str(ctx.exception))
		for bad in ("1.005", 100.0, "12,5"):
			with self.subTest(value=bad):
				with self.assertRaises(ProcurementRequisitionsError) as ctx:
					self._save(requisition, line, bad)
				self.assertCode(ctx, "REQ_MONEY_PRECISION_INVALID")
		self.assertEqual(_lines(requisition)[0].requested_value, "3000000.00", "a refused save changes nothing")
		self._save(requisition, line, "")
		self.assertEqual(_lines(requisition)[0].requested_value, "0.00", "an empty field clears the estimate")

	def test_a_contributor_cannot_enter_another_departments_estimate(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition, fx.CONTRIBUTOR)
		alpha = _line(view, fx.ou_alpha())
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_requisition_summary(
				requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": alpha["drawdown_line_id"], "requested_value": "1.00"}]},
				expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key(), user=fx.CONTRIBUTOR,
			)
		self.assertCode(ctx, "REQ_RESPONSIBILITY_REQUIRED")
		beta = _line(view, fx.ou_beta())
		cmd.save_requisition_summary(
			requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": beta["drawdown_line_id"], "requested_value": "2000000.00"}]},
			expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key(), user=fx.CONTRIBUTOR,
		)
		self.assertEqual(next(l for l in _lines(requisition) if l.contributing_org_unit == fx.ou_beta()).requested_value, "2000000.00")


class TestUnusedAndIncompleteSources(RequisitionCase):
	def _blocking(self, requisition: str) -> list[dict]:
		return [f for f in fx.editor(requisition)["findings"] if f["severity"] == "Blocking"]

	def _two_department_draft(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		view = fx.editor(requisition)
		return requisition, _line(view, fx.ou_alpha())["drawdown_line_id"], _line(view, fx.ou_beta())["drawdown_line_id"]

	def test_items_without_an_estimate_and_an_estimate_without_items_each_block_with_a_correction_message(self):
		requisition, alpha, beta = self._two_department_draft()
		fx.add_laptops(requisition, quantities={alpha: 50})
		messages = [f["message"] for f in self._blocking(requisition) if f["code"] == "SOURCE_INCOMPLETE"]
		self.assertEqual(len(messages), 1)
		self.assertTrue(messages[0].startswith("Enter the estimated total cost for "), messages[0])
		fx.enter_estimates(requisition, values={alpha: "10000000.00"})
		self.assertFalse([f for f in self._blocking(requisition) if f["code"] == "SOURCE_INCOMPLETE"])
		view = fx.editor(requisition)
		cmd.save_requisition_summary(requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": beta, "requested_value": "1000000.00"}]}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		messages = [f["message"] for f in self._blocking(requisition) if f["code"] == "SOURCE_INCOMPLETE"]
		self.assertEqual(len(messages), 1)
		self.assertIn("or clear its estimated total cost", messages[0])

	def test_nothing_entered_is_blocked_and_asks_for_an_item_and_an_estimate(self):
		requisition, _, _ = self._two_department_draft()
		view = fx.editor(requisition)
		self.assertEqual(view["footer_hints"]["request_details"], "Add at least one item and enter its estimated total cost.")

	def test_a_wholly_unused_source_is_omitted_from_the_snapshot_and_is_neither_drawn_nor_reserved(self):
		requisition, alpha, beta = self._two_department_draft()
		fx.add_laptops(requisition, quantities={alpha: 50})
		fx.enter_estimates(requisition, values={alpha: "10000000.00"})
		fx.apply_standard_package(requisition)
		self.assertTrue(fx.editor(requisition)["review"]["result"], "one used source is enough: the Draft is ready")
		fx.send(requisition)
		fx.submit_as_hod(requisition)
		_, version, _ = records.load(requisition)
		self.assertEqual([l.drawdown_line_id for l in version.drawdown_lines], [alpha])
		self.assertEqual([l["drawdown_line_id"] for l in goods_template.omitted_lines(version)], [beta], "the omitted source is kept as history")
		authorised = fx.authorise(requisition)
		frappe.set_user("Administrator")
		payload = json.loads(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "payload_json"))
		self.assertEqual([l["drawdown_line_id"] for l in payload["drawdown_lines"]], [alpha])
		self.assertEqual(payload["contributing_org_unit_ids"], [fx.ou_alpha()], "a Version's contributing departments are its retained sources' departments")
		self.assertEqual(frappe.db.count("Funding Reservation", {"drawdown_line_id": beta}), 0)
		self.assertEqual(frappe.db.count("Funding Reservation", {"drawdown_line_id": alpha}), 1)

	def test_a_returned_copy_gets_the_omitted_source_back_unused(self):
		requisition, alpha, beta = self._two_department_draft()
		fx.add_laptops(requisition, quantities={alpha: 50})
		fx.enter_estimates(requisition, values={alpha: "10000000.00"})
		fx.apply_standard_package(requisition)
		fx.send(requisition)
		frappe.set_user(fx.HOD)
		task = fx.open_task(requisition, "Head of User Department")
		lifecycle.return_to_department_author(
			task=task, reason=REASON, affected_section="Request details",
			expected_record_version=frappe.db.get_value("Requisition Task", task, "record_version"), idempotency_key=fx.key(),
		)
		frappe.set_user("Administrator")
		_, copied, _ = records.load(requisition)
		self.assertEqual(sorted((l.drawdown_line_id, l.requested_quantity, l.requested_value) for l in copied.drawdown_lines), sorted([(alpha, "50", "10000000.00"), (beta, "0", "0.00")]))


class TestOneDeliveryLocation(RequisitionCase):
	def test_a_location_chosen_in_the_dialog_is_the_requests_location_too(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		self.assertIn("Select the delivery location.", view["footer_hints"]["request_details"])
		line = view["amounts"][0]["drawdown_line_id"]
		location = fx.delivery_location()
		cmd.add_same_specification_items(
			requisition=requisition, shared={"equipment_category": "Laptop", "item_name": "Business laptops", "delivery_location": location},
			rows=[{"drawdown_line_id": line, "quantity": 20, "intended_use": "Field deployment for the department"}],
			expected_record_version=view["package_record_version"], idempotency_key=fx.key(),
		)
		self.assertEqual(records.load(requisition)[1].delivery_location, location)
		view = fx.editor(requisition)
		self.assertEqual(view["request_information"]["delivery_location"], location)
		self.assertNotIn("Select the delivery location.", [f["message"] for f in view["findings"]])


class TestMixedRequestKeepsEachKindEditable(RequisitionCase):
	"""v1.17 §13.4C — items that share a specification are one group; a request with
	laptops and monitors has two, and either can be renamed or recategorised alone."""

	def test_each_specification_is_its_own_group_and_is_edited_on_its_own(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		view = fx.editor(requisition)
		alpha, beta = _line(view, fx.ou_alpha())["drawdown_line_id"], _line(view, fx.ou_beta())["drawdown_line_id"]
		fx.add_laptops(requisition, quantities={alpha: 10})
		fx.add_laptops(requisition, quantities={beta: 5}, item_name="Office monitors", category="Monitor")
		equipment = fx.editor(requisition)["equipment"]
		self.assertIsNone(equipment["shared_specification"], "no single shared specification once the kinds differ")
		self.assertEqual([(g["item_name"], g["equipment_category"], len(g["requisition_item_ids"])) for g in equipment["groups"]], [("Business laptops", "Laptop", 1), ("Office monitors", "Monitor", 1)])
		by_name = {r["item_name"]: r["requisition_item_id"] for r in equipment["rows"]}
		self.assertEqual([g["requisition_item_ids"] for g in equipment["groups"]], [[by_name["Business laptops"]], [by_name["Office monitors"]]])

		monitors = equipment["groups"][1]
		shared = {k: monitors[k] for k in ("equipment_category", "delivery_location", "latest_delivery_date")} | {"item_name": "Desktop monitors"}
		cmd.update_shared_item_details(
			requisition=requisition, requisition_item_ids=monitors["requisition_item_ids"], shared=shared,
			expected_record_version=fx.editor(requisition)["package_record_version"], idempotency_key=fx.key(),
		)
		after = fx.editor(requisition)["equipment"]["groups"]
		self.assertEqual([g["item_name"] for g in after], ["Business laptops", "Desktop monitors"], "only the named group changed")


class TestCarriedOverDrafts(RequisitionCase):
	def test_a_draft_carried_over_from_v114_must_be_reviewed_before_it_can_be_submitted(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.complete_draft(item_id)
		root, version, _ = records.load(requisition)
		line = version.drawdown_lines[0].drawdown_line_id
		frappe.db.set_value("Requisition Version", version.name, "unreviewed_line_ids_json", json.dumps([line]))  # what the patch does
		view = fx.editor(requisition)
		self.assertTrue(view["summary"]["review_required"])
		self.assertIn("AMOUNTS_REVIEW_REQUIRED", [f["code"] for f in view["findings"]])
		self.assertTrue(view["amounts"][0]["needs_review"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.send(requisition)
		self.assertCode(ctx, "REQ_BLOCKING_FINDINGS")
		fx.enter_estimates(requisition)  # the requester reviews and saves the line
		view = fx.editor(requisition)
		self.assertFalse(view["summary"]["review_required"])
		self.assertNotIn("AMOUNTS_REVIEW_REQUIRED", [f["code"] for f in view["findings"]])
		fx.send(requisition)

	def test_the_patch_marks_existing_drafts_once_and_never_a_reviewed_or_new_one(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		version = records.load(requisition)[1]
		frappe.db.set_value("Requisition Version", version.name, "unreviewed_line_ids_json", None)
		carried_over_patch.execute()
		marked = json.loads(frappe.db.get_value("Requisition Version", version.name, "unreviewed_line_ids_json"))
		self.assertEqual(marked, sorted(l.drawdown_line_id for l in version.drawdown_lines))
		frappe.db.set_value("Requisition Version", version.name, "unreviewed_line_ids_json", json.dumps([]))  # reviewed
		carried_over_patch.execute()
		self.assertEqual(json.loads(frappe.db.get_value("Requisition Version", version.name, "unreviewed_line_ids_json")), [], "a reviewed Draft is never re-marked")


class TestWordingIsNeutral(RequisitionCase):
	def test_no_user_facing_text_names_a_product_outside_the_chosen_category(self):
		_, item_id = fx.active_item(quantity=250)
		requisition = fx.prepare(item_id)["requisition"]
		line = fx.editor(requisition)["amounts"][0]["drawdown_line_id"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition, quantities={line: 20}, category="Printer", item_name="Office printers")
		view = fx.editor(requisition)
		texts = [f["message"] for f in view["findings"]] + list(view["footer_hints"].values())
		texts += [view["equipment"]["shared_specification"]["label"], view["equipment"]["shared_specification"]["summary"]]
		for section in view["review"]["sections"]:
			texts += [section["title"], section["summary"]]
		for text in texts:
			self.assertNotIn("laptop", text.lower(), text)
