# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §6.3/§6.4 — the code-owned catalogue: control types,
range/option validation and baseline proposal, pure and DB-free.
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
			"display_size": 14.0,
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

	def test_baseline_proposal_for_laptop_includes_electrical_and_storage_type(self):
		proposed = catalogue.propose_baseline("Laptop")
		keys = {p["characteristic_key"] for p in proposed}
		self.assertIn("electrical_compatibility", keys)
		self.assertIn("new_unused_equipment", keys)
		self.assertIn("storage_type", keys)
		storage = next(p for p in proposed if p["characteristic_key"] == "storage_type")
		self.assertIn("NVMe SSD", storage["required_value_json"])

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
