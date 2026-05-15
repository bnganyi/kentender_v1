# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-08 — doc 9 §8.4 stub mode + §20.1–20.2 fixture (no full STD engine in CI).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_08_stub_mode_pack
"""

from __future__ import annotations

import json

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.tm2_std_adapter import (
	STD_ADAPTER_OUTPUT_REFS_V83_KEYS,
	extract_std_output_refs_contract_v83,
)
from kentender_procurement.tender_management.services.tm2_stub_seed import (
	assert_stub_fixture_contains_required_codes,
	get_stub_output_refs_v83,
	load_tm2_works_open_tender_fixture,
	tm2_stub_fixture_path,
)


class TestP308StubModePack(IntegrationTestCase):
	def test_p3_08_fixture_file_exists_and_is_valid_json(self) -> None:
		path = tm2_stub_fixture_path()
		self.assertTrue(path.is_file(), path)
		with path.open(encoding="utf-8") as fh:
			data = json.load(fh)
		self.assertEqual(data.get("tender_code"), "TND-MOH-2026-001")

	def test_p3_08_required_codes_present(self) -> None:
		assert_stub_fixture_contains_required_codes()

	def test_p3_08_output_refs_v83_matches_doc_8_3_keys(self) -> None:
		v83 = get_stub_output_refs_v83()
		self.assertEqual(frozenset(v83), frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))
		snap = {"ok": True, **v83}
		self.assertEqual(extract_std_output_refs_contract_v83(snap), v83)

	def test_p3_08_loader_idempotent_cached(self) -> None:
		a = load_tm2_works_open_tender_fixture()
		b = load_tm2_works_open_tender_fixture()
		self.assertIs(a, b)

	def test_p3_08_supplier_list_complete(self) -> None:
		data = load_tm2_works_open_tender_fixture()
		sup = data.get("suppliers")
		self.assertIsInstance(sup, list)
		self.assertEqual(set(sup), {"SUP-ALPHA", "SUP-BETA", "SUP-GAMMA", "SUP-DELTA"})
