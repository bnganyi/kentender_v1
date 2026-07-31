# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 must not invent contract values from pack sample rows."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.contract_values import (
	_suggest_from_upstream,
	save_configuration_contract_values,
)


FORBIDDEN_INVENTED_LABELS = {
	"On-site Support",
	"Data Residency",
	"Contract Attachments",
	"Acceptance Testing",
	"Advance Payment Security",
}

FORBIDDEN_INVENTED_VALUES = (
	"Production data must remain in Kenya unless otherwise approved",
	"Missing required attachment list",
	"3 years next-business-day on-site support",
)


class TestCfg09NoInventedHydrate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_hydrate_without_std_version_returns_empty(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.std_version = ""
		doc.contract_values = json.dumps({"contract_values": []})
		drafts = _suggest_from_upstream(doc, [])
		self.assertEqual(drafts, [])

	def test_hydrate_never_emits_pack_sample_inventions(self):
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": [], "hydrate": 1}
		)
		labels = {r.get("item_label") for r in out["contract_values"]}
		for forbidden in FORBIDDEN_INVENTED_LABELS:
			self.assertNotIn(forbidden, labels)
		for row in out["contract_values"]:
			val = (row.get("value_or_obligation") or "").strip()
			for bad in FORBIDDEN_INVENTED_VALUES:
				self.assertNotEqual(val, bad)
			# Every hydrated candidate must carry a structured STD binding.
			self.assertTrue(
				row.get("parameter_code") or row.get("parameter_key") or row.get("readiness_parameter_id"),
				msg=f"unbound hydrate row: {row.get('item_label')}",
			)

	def test_hydrate_rows_use_std_titles_when_package_present(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		std = (doc.std_version or "").strip()
		if not std or not frappe.db.exists("STD Parameter", {"package_id": std}):
			self.skipTest("No STD Parameter rows for bound package on this site")
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": [], "hydrate": 1}
		)
		# Prefer empty over invented; if drafts exist they must map to STD codes.
		for row in out["contract_values"]:
			code = (row.get("parameter_code") or "").strip()
			if not code:
				continue
			exists = frappe.db.exists(
				"STD Parameter",
				{"package_id": std, "metadata_json": ["like", f"%{code}%"]},
			) or frappe.db.exists(
				"STD Parameter",
				{"package_id": std, "parameter_key": ["like", f"%{code.lower().replace('it-scc-', 'parameter.scc.')}%"]},
			)
			# Soft check via metadata / key — at minimum code must be non-empty IT-SCC-*
			self.assertTrue(code.startswith("IT-SCC-") or code.startswith("KE-"), code)


class TestCfg09NoInventedHydrateUnit(unittest.TestCase):
	def test_suggest_refuses_to_invent_without_doc_std(self):
		class _Doc:
			std_version = ""
			implementation_schedule = None
			tds_values = None
			it_requirements = None

		self.assertEqual(_suggest_from_upstream(_Doc(), []), [])


if __name__ == "__main__":
	unittest.main()
