# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §6.1/§6.5 — five validation groups, three visible
tasks, exact arithmetic; pure and DB-free (REQ19-AC-008, -014, -015, -016,
-018, -049, -080, -085)."""

from __future__ import annotations

import json
import unittest

from kentender_procurement.procurement_requisitions.services import catalogue, validation


def eligibility(**overrides):
	base = {
		"contributing_org_unit_ids": ["OU-HRMD", "OU-DHI"],
		"plan_completion_boundary": "2027-12-31",
		"estimated_completion_date": "2027-09-24",
		"sources": [
			{"plan_item_line_id": "PSA-1", "remaining_quantity": "100", "remaining_amount": "20000000.00", "required_by_date": "2027-12-31"},
			{"plan_item_line_id": "PSA-2", "remaining_quantity": "150", "remaining_amount": "30000000.00", "required_by_date": "2027-12-31"},
		],
	}
	base.update(overrides)
	return base


def version(**overrides):
	base = {
		"requirement_title": "Clinical training and deployment laptops for digital health rollout",
		"delivery_location": "LOC-AFYA", "latest_delivery_date": "2027-09-30", "related_services_required": False,
		"drawdown_lines": [
			{"drawdown_line_id": "DL-001", "plan_item_line_id": "PSA-1", "contributing_org_unit": "OU-HRMD", "department_name": "Human Resources Management and Development", "requested_quantity": "100", "requested_value": "20000000.00"},
			{"drawdown_line_id": "DL-002", "plan_item_line_id": "PSA-2", "contributing_org_unit": "OU-DHI", "department_name": "Digital Health", "requested_quantity": "150", "requested_value": "30000000.00"},
		],
	}
	base.update(overrides)
	return base


def _confirmed_package():
	proposal = catalogue.proposal_for(["Laptop"])
	return {
		**proposal["support"],
		"standard_package_review_state": "Reviewed",
		"items": [
			{"requisition_item_id": "RQI-001", "drawdown_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training for Human Resources Management and Development staff"},
			{"requisition_item_id": "RQI-002", "drawdown_line_id": "DL-002", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 150, "intended_use": "Field digital-health deployment for Digital Health staff"},
		],
		"technical_requirements": [
			{"technical_requirement_id": f"TECH-{i + 1:03d}", "row_state": "Confirmed", "characteristic_key": r["characteristic_key"], "applies_to_scope": "All items", "applies_to_id": "", "required_value_json": json.dumps(r["value"]), "reason": ""}
			for i, r in enumerate(proposal["technical"])
		],
		"acceptance_requirements": [
			{"acceptance_requirement_id": f"ACC-{i + 1:03d}", "row_state": "Confirmed", **a} for i, a in enumerate(proposal["acceptance"])
		],
		"related_services": [],
		"supporting_materials": [],
	}


def package(**overrides):
	base = _confirmed_package()
	base.update(overrides)
	return base


def statuses(report):
	return {t["key"]: t["status"] for t in report["tasks"]}


class TestTasksOverGroups(unittest.TestCase):
	def test_the_complete_fixture_is_ready_with_one_date_warning(self):
		report = validation.validate(version=version(), package=package(), eligibility=eligibility())
		self.assertEqual(report["blocking_count"], 0)
		self.assertTrue(report["ready"])
		self.assertEqual(statuses(report), {"request_details": "Complete", "requirements": "Complete", "review_submit": "Not started"})
		self.assertEqual([g for g in report["groups"]], list(validation.GROUPS))
		warnings = [f for f in report["findings"] if f["severity"] == "Warning"]
		self.assertEqual([w["message"] for w in warnings], ["The requested delivery date is 6 days after the plan’s estimated completion date."])

	def test_des03_base_request_details_needs_attention_and_requirements_not_started(self):
		report = validation.validate(version=version(), package=package(items=[], technical_requirements=[], acceptance_requirements=[], standard_package_review_state="Not generated"), eligibility=eligibility())
		self.assertEqual(statuses(report), {"request_details": "Needs attention", "requirements": "Not started", "review_submit": "Not started"})
		messages = [f["message"] for f in report["findings"] if f["group"] == "equipment_items"]
		self.assertIn("Add the laptop request matching the requested quantities.", messages)

	def test_des05_review_required_blocks_requirements(self):
		report = validation.validate(version=version(), package=package(standard_package_review_state="Review required"), eligibility=eligibility())
		self.assertEqual(statuses(report)["requirements"], "Needs attention")
		codes = [f["code"] for f in report["findings"] if f["group"] == "technical_support"]
		self.assertEqual(codes, ["PACKAGE_REVIEW_REQUIRED"])
		self.assertFalse(report["ready"])

	def test_proposed_rows_never_count_as_acceptance(self):
		proposed = [{**a, "row_state": "Proposed"} for a in package()["acceptance_requirements"]]
		report = validation.validate(version=version(), package=package(acceptance_requirements=proposed), eligibility=eligibility())
		self.assertIn("MISSING_ACCEPTANCE_ROW", [f["code"] for f in report["findings"]])


class TestExactReconciliation(unittest.TestCase):
	def test_the_board_save_validation_message(self):
		items = package()["items"]
		items[1] = {**items[1], "quantity": 140}
		report = validation.validate(version=version(), package=package(items=items), eligibility=eligibility())
		mismatch = [f for f in report["findings"] if f["code"] == "QUANTITY_MISMATCH"]
		self.assertEqual(mismatch[0]["message"], "Requested equipment quantity for Digital Health is 140 Each but the approved requirement requests 150 Each")
		self.assertEqual(mismatch[0]["section"], "equipment")

	def test_requested_above_remaining_is_balance_changed_by_one_cent(self):
		lines = version()["drawdown_lines"]
		lines[0] = {**lines[0], "requested_value": "20000000.01"}
		report = validation.validate(version=version(drawdown_lines=lines), package=package(), eligibility=eligibility())
		self.assertIn("BALANCE_CHANGED", [f["code"] for f in report["findings"]])

	def test_a_department_the_item_never_included_is_refused(self):
		lines = version()["drawdown_lines"]
		lines[0] = {**lines[0], "contributing_org_unit": "OU-OTHER"}
		report = validation.validate(version=version(drawdown_lines=lines), package=package(), eligibility=eligibility())
		self.assertIn("DEPARTMENT_NOT_CONTRIBUTING", [f["code"] for f in report["findings"]])


class TestDates(unittest.TestCase):
	def test_after_the_plan_boundary_blocks(self):
		report = validation.validate(version=version(latest_delivery_date="2028-01-01"), package=package(), eligibility=eligibility())
		self.assertIn("DATE_BEYOND_BOUNDARY", [f["code"] for f in report["findings"]])

	def test_the_estimate_only_warns(self):
		report = validation.validate(version=version(latest_delivery_date="2027-12-31"), package=package(), eligibility=eligibility())
		self.assertEqual(report["blocking_count"], 0)
		self.assertEqual(report["warning_count"], 1)


class TestRequirementsRules(unittest.TestCase):
	def test_satisfactory_alone_is_rejected(self):
		rows = package()["acceptance_requirements"]
		rows[0] = {**rows[0], "pass_condition": "Satisfactory"}
		report = validation.validate(version=version(), package=package(acceptance_requirements=rows), eligibility=eligibility())
		self.assertIn("SUBJECTIVE_ACCEPTANCE", [f["code"] for f in report["findings"]])

	def test_an_operative_file_needs_a_structured_link(self):
		material = {"supporting_material_id": "MAT-001", "treatment": "Forms part of requirement", "linked_requirement_ids_json": "[]"}
		report = validation.validate(version=version(), package=package(supporting_materials=[material]), eligibility=eligibility())
		self.assertIn("FILE_UNLINKED", [f["code"] for f in report["findings"]])
		linked = {**material, "linked_requirement_ids_json": json.dumps(["TECH-001"])}
		report = validation.validate(version=version(), package=package(supporting_materials=[linked]), eligibility=eligibility())
		self.assertNotIn("FILE_UNLINKED", [f["code"] for f in report["findings"]])

	def test_a_brand_without_equivalence_blocks(self):
		rows = package()["technical_requirements"]
		idx = next(i for i, r in enumerate(rows) if r["characteristic_key"] == "processor_requirement")
		rows[idx] = {**rows[idx], "required_value_json": json.dumps({"value": "Intel Core i7"})}
		report = validation.validate(version=version(), package=package(technical_requirements=rows), eligibility=eligibility())
		self.assertIn("RESTRICTIVE_TERM", [f["code"] for f in report["findings"]])

	def test_duplicate_characteristic_for_the_same_target_blocks(self):
		rows = package()["technical_requirements"]
		rows.append({**rows[2], "technical_requirement_id": "TECH-099"})
		report = validation.validate(version=version(), package=package(technical_requirements=rows), eligibility=eligibility())
		self.assertIn("DUPLICATE_CHARACTERISTIC", [f["code"] for f in report["findings"]])

	def test_integration_service_is_unsupported(self):
		service = {"service_requirement_id": "SVC-001", "service_type": "Configuration", "required_result": "Integrate the laptops with the national HMIS", "quantity_or_coverage": "All", "completion_date": "2027-09-30", "acceptance_evidence": "Test result"}
		report = validation.validate(version=version(related_services_required=True), package=package(related_services=[service]), eligibility=eligibility())
		self.assertIn("SERVICE_COMPLEX", [f["code"] for f in report["findings"]])

	def test_missing_warranty_is_bound_to_its_field(self):
		report = validation.validate(version=version(), package=package(minimum_warranty_months=None), eligibility=eligibility())
		finding = next(f for f in report["findings"] if f["section"] == "warranty_support")
		self.assertEqual(finding["message"], "Enter the minimum warranty in months.")
		self.assertEqual(finding["row"], {"kind": "field", "id": "minimum_warranty_months"})


def _codes(report, code):
	return [f for f in report["findings"] if f["code"] == code]


class TestCategoryApplicability(unittest.TestCase):
	"""AUD-REQ-005 (REQ §6.3, REQ19-AC-009): only characteristics applicable to the
	selected category are accepted; a category change revalidates the rows."""

	def _with_row(self, key, value, *, scope="All items", target="", items=None):
		rows = package()["technical_requirements"]
		rows.append({"technical_requirement_id": "TECH-090", "row_state": "Confirmed", "characteristic_key": key, "applies_to_scope": scope, "applies_to_id": target, "required_value_json": json.dumps({"value": value}), "reason": ""})
		extra = {} if items is None else {"items": items}
		return validation.validate(version=version(), package=package(technical_requirements=rows, **extra), eligibility=eligibility())

	def test_a_printer_only_characteristic_on_all_laptop_items_blocks(self):
		report = self._with_row("print_speed", 30)
		found = _codes(report, "CONTROL_INVALID")
		self.assertEqual([f["row"] for f in found], [{"kind": "technical_requirement", "id": "TECH-090"}])
		self.assertIn("Print speed", found[0]["message"])
		self.assertEqual(found[0]["severity"], "Blocking")

	def test_an_all_items_row_must_suit_every_item_category(self):
		items = package()["items"]
		items[1] = {**items[1], "equipment_category": "Monitor"}
		report = self._with_row("memory", 8, items=items)  # Laptop and Monitor: memory is not a Monitor characteristic
		self.assertTrue(_codes(report, "CONTROL_INVALID"))

	def test_an_item_scoped_row_is_judged_by_that_items_category_only(self):
		items = package()["items"]
		items[1] = {**items[1], "equipment_category": "Monitor"}
		def mine(report):
			return [f for f in _codes(report, "CONTROL_INVALID") if f["row"]["id"] == "TECH-090"]

		self.assertFalse(mine(self._with_row("display_resolution", "QHD", scope="Item", target="RQI-002", items=items)))
		self.assertTrue(mine(self._with_row("display_resolution", "QHD", scope="Item", target="RQI-001", items=items)))

	def test_a_category_change_makes_the_old_rows_blocking(self):
		items = [{**i, "equipment_category": "Monitor"} for i in package()["items"]]
		report = validation.validate(version=version(), package=package(items=items), eligibility=eligibility())
		labels = " ".join(f["message"] for f in _codes(report, "CONTROL_INVALID"))
		self.assertIn("Memory", labels)  # the laptop package's rows no longer fit Monitors

	def test_the_complete_laptop_package_is_unaffected(self):
		report = validation.validate(version=version(), package=package(), eligibility=eligibility())
		self.assertFalse(_codes(report, "CONTROL_INVALID"))

	def test_catalogue_applies_is_the_one_rule(self):
		self.assertFalse(catalogue.CATALOGUE_BY_KEY["print_speed"].applies("Monitor"))
		self.assertEqual(catalogue.inapplicable_categories(catalogue.CATALOGUE_BY_KEY["print_speed"], ["Printer", "Monitor", "Monitor"]), ["Monitor"])


class TestRestrictiveWordingEverywhereItReachesTheTender(unittest.TestCase):
	"""AUD-REQ-006 (REQ §6.3/§6.5, REQ19-AC-018): brand or restrictive wording
	is a Blocking finding in every free-text field that reaches the Tender,
	not only in technical TEXT rows."""

	def _blocked(self, report, kind, row_id):
		return [f for f in _codes(report, "RESTRICTIVE_TERM") if f["row"] == {"kind": kind, "id": row_id}]

	def test_an_item_name_or_intended_use(self):
		items = package()["items"]
		items[0] = {**items[0], "item_name": "Dell Latitude 5440 laptops"}
		items[1] = {**items[1], "intended_use": "Field deployment on Lenovo ThinkPad units for staff"}
		report = validation.validate(version=version(), package=package(items=items), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "item", "RQI-001"))
		self.assertTrue(self._blocked(report, "item", "RQI-002"))

	def test_an_acceptance_pass_condition(self):
		rows = package()["acceptance_requirements"]
		rows[0] = {**rows[0], "pass_condition": "Delivered units must be Dell Latitude 5440 devices"}
		report = validation.validate(version=version(), package=package(acceptance_requirements=rows), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "acceptance", rows[0]["acceptance_requirement_id"]))

	def test_a_related_service_result_and_coverage(self):
		service = {"service_requirement_id": "SVC-001", "service_type": "Installation", "required_result": "Install and enrol all laptops in Microsoft Intune", "quantity_or_coverage": "All units", "completion_date": "2027-09-30", "acceptance_evidence": "Test result"}
		report = validation.validate(version=version(related_services_required=True), package=package(related_services=[service]), eligibility=eligibility())
		self.assertFalse(self._blocked(report, "service", "SVC-001"))
		service = {**service, "required_result": "Install the Dell Command Update tool on all laptops"}
		report = validation.validate(version=version(related_services_required=True), package=package(related_services=[service]), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "service", "SVC-001"))

	def test_a_supporting_material_title_and_purpose(self):
		material = {"supporting_material_id": "MAT-001", "title": "Dell Latitude 5440 datasheet", "purpose": "Shows the layout", "treatment": "Reference only", "linked_requirement_ids_json": "[]"}
		report = validation.validate(version=version(), package=package(supporting_materials=[material]), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "material", "MAT-001"))

	def test_the_other_value_of_a_non_text_control(self):
		rows = package()["technical_requirements"]
		rows.append({"technical_requirement_id": "TECH-091", "row_state": "Confirmed", "characteristic_key": "storage_type", "applies_to_scope": "All items", "applies_to_id": "", "required_value_json": json.dumps({"value": "Other", "other": "Samsung PM9A1"}), "other_value": "Samsung PM9A1", "reason": ""})
		report = validation.validate(version=version(), package=package(technical_requirements=rows), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "technical_requirement", "TECH-091"))

	def test_the_requirement_title(self):
		report = validation.validate(version=version(requirement_title="Dell laptops for digital health rollout"), package=package(), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "field", "requirement_title"))

	def test_equivalent_wording_with_a_recorded_reason_is_allowed_where_the_row_has_a_reason(self):
		rows = package()["technical_requirements"]
		idx = next(i for i, r in enumerate(rows) if r["characteristic_key"] == "processor_requirement")
		rows[idx] = {**rows[idx], "required_value_json": json.dumps({"value": "Intel Core i7 or equivalent"}), "reason": "Needed to run the national health information client at clinic sites."}
		report = validation.validate(version=version(), package=package(technical_requirements=rows), eligibility=eligibility())
		self.assertFalse(_codes(report, "RESTRICTIVE_TERM"))

	def test_a_row_with_no_reason_field_cannot_be_excused_by_equivalent_wording_alone(self):
		rows = package()["acceptance_requirements"]
		rows[0] = {**rows[0], "pass_condition": "Delivered units are Dell Latitude 5440 or equivalent"}
		report = validation.validate(version=version(), package=package(acceptance_requirements=rows), eligibility=eligibility())
		self.assertTrue(self._blocked(report, "acceptance", rows[0]["acceptance_requirement_id"]))

	def test_the_clean_package_has_no_finding(self):
		report = validation.validate(version=version(), package=package(), eligibility=eligibility())
		self.assertFalse(_codes(report, "RESTRICTIVE_TERM"))
