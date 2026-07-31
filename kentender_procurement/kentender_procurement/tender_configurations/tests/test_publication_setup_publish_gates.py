# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Publication Setup must surface ordinary-publish gates before Publish Tender."""

from __future__ import annotations

import unittest

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.publication_setup import (
	_electronic_template_publish_gate,
	get_publication_setup,
)


class TestPublicationSetupPublishGates(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_electronic_template_gate_ready_when_approved(self):
		gate = _electronic_template_publish_gate()
		self.assertEqual(gate.get("ready"), 1, gate)
		self.assertEqual(gate.get("status"), "Approved")
		self.assertFalse(cstr(gate.get("blocker") or "").strip())

	def test_ready_publication_can_publish_when_template_approved(self):
		pub_id = frappe.db.get_value(
			"IT Tender Publication Record",
			{"status": "Ready to Publish"},
			"name",
		)
		if not pub_id:
			self.skipTest("No Ready to Publish publication available for gate check.")
		setup = get_publication_setup(pub_id)
		blockers = setup.get("publish_blockers") or []
		self.assertFalse(
			any("electronic STD template" in cstr(b) for b in blockers),
			blockers,
		)
		# Package integrity may still block; template gate itself must be clear.
		gate = setup.get("electronic_template_approval") or {}
		self.assertEqual(gate.get("ready"), 1, gate)
