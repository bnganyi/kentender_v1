# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §6.3/§6.4 — the code-owned catalogue: control types,
range/option validation, exact decimals and the versioned requirement
proposals (`LAPTOP-REQUIREMENTS-V1`), pure and DB-free.
"""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_requisitions.services import catalogue


class TestCatalogueShape(unittest.TestCase):
	def test_every_characteristic_key_is_unique(self):
		keys = [c.key for c in catalogue.CHARACTERISTICS]
		self.assertEqual(len(keys), len(set(keys)))

	def test_fixture_laptop_specification_validates(self):
		"""§16.3's TECH-001..011 rows must all validate cleanly."""
		cases = {
			"electrical_compatibility": "Yes",
			"new_unused_equipment": "Yes",
			"memory": 16,
			"storage_capacity": 512,
			"storage_type": "NVMe SSD",
			"display_size": "14.0",
			"battery_runtime": 8,
			"processor_requirement": "64-bit business-class processor, minimum 10 cores or equivalent benchmark",
			"operating_system_compatibility": "Approved organisational Windows environment",
		}
		for key, value in cases.items():
			ch = catalogue.CATALOGUE_BY_KEY[key]
			result = catalogue.validate_value(ch, value)
			self.assertIn("value", result)

		multi = catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["network_connectivity"], ["Wi-Fi 6", "Bluetooth 5 or later"])
		self.assertEqual(multi["values"], ["Wi-Fi 6", "Bluetooth 5 or later"])

		ports = catalogue.validate_value(
			catalogue.CATALOGUE_BY_KEY["required_ports"],
			[{"port_type": "USB-C", "minimum_count": 2}, {"port_type": "USB-A", "minimum_count": 2}, {"port_type": "HDMI", "minimum_count": 1}],
		)
		self.assertEqual(len(ports["ports"]), 3)

	def test_out_of_range_integer_is_rejected(self):
		with self.assertRaises(catalogue.CatalogueValueError):
			catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["memory"], 1000)

	def test_unknown_select_option_is_rejected(self):
		with self.assertRaises(catalogue.CatalogueValueError):
			catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["storage_type"], "Floppy disk")

	def test_short_text_is_rejected(self):
		with self.assertRaises(catalogue.CatalogueValueError):
			catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["processor_requirement"], "x")

	def test_characteristics_for_monitor_excludes_laptop_only_rows(self):
		keys = {c.key for c in catalogue.characteristics_for("Monitor")}
		self.assertIn("display_resolution", keys)
		self.assertNotIn("processor_requirement", keys)

	def test_network_and_power_function_are_split_keys(self):
		"""§6.3 lists 'Equipment function' twice with different applies_to and
		options — REQ-CHG-001 v1.6 D10 splits it into two catalogue keys."""
		self.assertNotEqual(
			catalogue.CATALOGUE_BY_KEY["network_function"].options,
			catalogue.CATALOGUE_BY_KEY["power_function"].options,
		)


class TestExactDecimals(unittest.TestCase):
	def test_a_decimal_characteristic_keeps_its_exact_string(self):
		self.assertEqual(catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["display_size"], "14.0"), {"value": "14.0"})

	def test_a_float_or_excess_scale_is_refused(self):
		for bad in (14.0, "14.005"):
			with self.subTest(bad=bad), self.assertRaises(catalogue.CatalogueValueError):
				catalogue.validate_value(catalogue.CATALOGUE_BY_KEY["display_size"], bad)


class TestLaptopStandardProfile(unittest.TestCase):
	"""§13.1 / REQ19-AC-089 — every suggestion visible: 11 technical rows,
	6 warranty/support values, 5 acceptance checks, exact values."""

	def setUp(self):
		self.proposal = catalogue.proposal_for(["Laptop"])

	def test_profile_identity(self):
		self.assertEqual(self.proposal["profile_key"], "LAPTOP-REQUIREMENTS-V1")
		self.assertEqual(self.proposal["profile_version"], "1")
		self.assertTrue(self.proposal["proposal_digest"])

	def test_exactly_eleven_technical_rows_in_three_groups_all_items(self):
		rows = self.proposal["technical"]
		self.assertEqual(
			[(r["group"], r["label"], r["comparison"], r["display"], r["unit"]) for r in rows],
			[
				("Basic equipment", "Electrical compatibility", "Required", "Yes — suitable for Kenyan mains supply", ""),
				("Basic equipment", "New and unused equipment", "Required", "Yes", ""),
				("Performance and storage", "Memory", "Minimum", "16", "GB"),
				("Performance and storage", "Storage capacity", "Minimum", "512", "GB"),
				("Performance and storage", "Storage type", "One of", "NVMe SSD", ""),
				("Performance and storage", "Display size", "Minimum", "14.0", "inches"),
				("Performance and storage", "Battery runtime", "Minimum", "8", "hours"),
				("Performance and storage", "Processor requirement", "Minimum", "64-bit business-class processor, minimum 10 cores or equivalent benchmark", ""),
				("Performance and storage", "Operating-system compatibility", "Required", "Approved organisational Windows environment", ""),
				("Connectivity", "Network connectivity", "Required", "Wi-Fi 6 and Bluetooth 5 or later", ""),
				("Connectivity", "Required ports", "Required", "USB-C ×2; USB-A ×2; HDMI ×1", ""),
			],
		)
		self.assertTrue(all(r["applies_to_scope"] == "All items" for r in rows))

	def test_six_support_values_and_five_acceptance_checks(self):
		self.assertEqual(self.proposal["support"], {
			"minimum_warranty_months": 36, "onsite_support_required": True, "maximum_support_response_hours": 8,
			"manufacturer_support_required": True, "service_location_constraint": "Within Kenya",
			"support_description": "Supplier to provide escalation and warranty-contact details.",
		})
		self.assertEqual(
			[(a["check_type"], a["evidence_type"]) for a in self.proposal["acceptance"]],
			[("Quantity", "Inspection record"), ("Physical condition", "Inspection record"), ("Required specification", "Inspection record"),
			 ("Functional test", "Test result"), ("Documents received", "Certificate")],
		)

	def test_the_digest_changes_when_the_proposal_would(self):
		self.assertNotEqual(self.proposal["proposal_digest"], catalogue.proposal_for(["Desktop computer"])["proposal_digest"])
		self.assertEqual(self.proposal["proposal_digest"], catalogue.proposal_for(["Laptop"])["proposal_digest"])

	def test_another_category_gets_the_catalogue_driven_proposal_not_the_laptop_preset(self):
		desktop = catalogue.proposal_for(["Desktop computer"])
		self.assertEqual(desktop["profile_key"], "IT-EQUIPMENT-CATALOGUE-V1")
		keys = [r["characteristic_key"] for r in desktop["technical"]]
		self.assertEqual(keys, ["electrical_compatibility", "new_unused_equipment", "storage_type"])
		self.assertEqual(len(desktop["acceptance"]), 5)

	def test_no_equipment_means_no_proposal(self):
		self.assertEqual(catalogue.proposal_for([])["technical"], [])
