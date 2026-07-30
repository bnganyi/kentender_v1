# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean Price Schedule — fixtures, calc, validation, FoT, checklist."""

from __future__ import annotations

import json
import unittest
from decimal import Decimal

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
	FIXTURE_MULTI_CURRENCY,
	FIXTURE_MULTI_LOT,
	FIXTURE_SINGLE_LOT,
	SCHEDULE_RECURRENT,
	SCHEDULE_SUPPLY,
	SECTION_KEY,
	lean_price_schedule_lines,
	lean_price_schedule_schedules,
	materialize_lean_price_schedule,
	publish_lean_price_schedule_for_tests,
)
from kentender_procurement.tender_configurations.services.form_of_tender import (
	is_price_schedule_complete,
	price_schedule_projection,
)
from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
	_to_decimal,
	complete_price_schedule,
	compute_totals,
	derive_price_schedule_section_status,
	format_money_display,
	get_price_schedule_editor,
	get_price_schedule_overview,
	get_price_schedule_review,
	hydrate_price_schedule_section,
	price_schedule_fot_projection,
	save_price_schedule_lines,
	validate_line_response,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NOT_STARTED,
	get_submission_checklist,
)


class TestLeanPriceScheduleFixtures(unittest.TestCase):
	def test_single_lot_omits_recurrent(self):
		schedules = lean_price_schedule_schedules(FIXTURE_SINGLE_LOT)
		keys = {s["schedule_key"] for s in schedules}
		self.assertEqual(keys, {SCHEDULE_SUPPLY})
		self.assertNotIn(SCHEDULE_RECURRENT, keys)

	def test_multi_lot_includes_recurrent(self):
		schedules = lean_price_schedule_schedules(FIXTURE_MULTI_LOT)
		keys = {s["schedule_key"] for s in schedules}
		self.assertIn(SCHEDULE_SUPPLY, keys)
		self.assertIn(SCHEDULE_RECURRENT, keys)
		lines = lean_price_schedule_lines(FIXTURE_MULTI_LOT)
		self.assertTrue(any(l.get("lot_id") == "lot-a" for l in lines))
		self.assertTrue(any(l.get("lot_id") == "lot-b" for l in lines))

	def test_multi_currency_permits_usd(self):
		lines = lean_price_schedule_lines(FIXTURE_MULTI_CURRENCY)
		self.assertTrue(any("USD" in (l.get("permitted_currencies") or []) for l in lines))

	def test_materialize_has_display_refs_not_hashes(self):
		mat = materialize_lean_price_schedule(FIXTURE_SINGLE_LOT)
		for row in mat["price_lines"]:
			self.assertTrue(row.get("display_reference"))
			self.assertNotIn("NSSF", cstr(row.get("description")))


class TestPriceScheduleUnit(unittest.TestCase):
	def test_blank_vs_zero(self):
		self.assertIsNone(_to_decimal(""))
		self.assertIsNone(_to_decimal(None))
		self.assertEqual(_to_decimal(0), Decimal("0"))
		self.assertEqual(_to_decimal("0"), Decimal("0"))
		self.assertEqual(_to_decimal("0.00"), Decimal("0.00"))

	def test_money_display_thousands_separators(self):
		self.assertEqual(format_money_display("3400000"), "3,400,000.00")
		self.assertEqual(format_money_display("3,400,000.00"), "3,400,000.00")
		self.assertEqual(format_money_display(Decimal("400000300")), "400,000,300.00")
		self.assertEqual(_to_decimal("3,400,000.50"), Decimal("3400000.50"))

	def test_validate_required_blank(self):
		line = {
			"line_id": "x",
			"display_reference": "1.1",
			"required": 1,
			"schedule_key": SCHEDULE_SUPPLY,
			"permitted_currencies": ["KES"],
			"zero_allowed": 0,
			"country_of_origin_required": 0,
			"quantity": "1",
			"periods": [],
		}
		errs = validate_line_response(line, {})
		self.assertTrue(any("no unit price" in e.lower() for e in errs))

	def test_validate_zero_rejected_unless_allowed(self):
		line = {
			"line_id": "x",
			"display_reference": "1.1",
			"required": 1,
			"schedule_key": SCHEDULE_SUPPLY,
			"permitted_currencies": ["KES"],
			"zero_allowed": 0,
			"country_of_origin_required": 0,
			"quantity": "1",
			"periods": [],
		}
		errs = validate_line_response(line, {"unit_price": 0, "currency": "KES"})
		self.assertTrue(any("zero" in e.lower() for e in errs))
		line["zero_allowed"] = 1
		errs2 = validate_line_response(line, {"unit_price": 0, "currency": "KES"})
		self.assertFalse(errs2)

	def test_line_total_rounding(self):
		sec = materialize_lean_price_schedule(FIXTURE_SINGLE_LOT)
		# Pack rule: round at line total — (qty * unit_price) then quantize.
		# 4 * 10.005 = 40.02 exactly → "40.02"
		resp = {
			"active_offer_id": "main",
			"lines": {
				"main::ps-si-001": {"unit_price": "10.005", "currency": "KES", "country_of_origin": "Kenya"}
			},
		}
		computed = compute_totals(sec, resp)
		kes = computed["by_currency"].get("KES") or {}
		self.assertEqual(kes.get("supply_subtotal"), "40.02")


class TestPriceSchedulePortal(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")

	def _fill_required_supply(self, pub_ref: str) -> None:
		ed = get_price_schedule_editor(pub_ref, SCHEDULE_SUPPLY)
		lines_payload = []
		for row in ed["rows"]:
			if not row.get("required"):
				continue
			lines_payload.append(
				{
					"line_id": row["line_id"],
					"unit_price": "1000",
					"currency": row["permitted_currencies"][0],
					"country_of_origin": "Kenya" if row.get("country_of_origin_required") else "",
				}
			)
		save_price_schedule_lines(
			pub_ref,
			{"schedule_key": SCHEDULE_SUPPLY, "lines": lines_payload},
		)

	def test_overview_omits_recurrent_for_single_lot(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		ov = get_price_schedule_overview(pub)
		keys = {s["schedule_key"] for s in ov["schedules"]}
		self.assertEqual(keys, {SCHEDULE_SUPPLY})
		self.assertEqual(ov["show_lot_selector"], 0)
		self.assertEqual(ov["section_status"], STATUS_NOT_STARTED)

	def test_hydrate_route_only_stub(self):
		stub = {
			"section_key": SECTION_KEY,
			"title": "Price Schedule",
			"slice_status": "route_only_not_editable_in_lean_slice",
			"price_lines": [],
		}
		hydrate_price_schedule_section(stub)
		self.assertEqual(stub.get("slice_status"), "price_schedule_implemented")
		self.assertGreaterEqual(len(stub.get("price_lines") or []), 1)

	def test_editor_progress_counts_filled_items(self):
		"""Pricing Progress 'N of M' must reflect priced rows (started), not stay at 0."""
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		ed0 = get_price_schedule_editor(pub, SCHEDULE_SUPPLY)
		self.assertEqual(ed0["progress"]["started"], 0)
		self.assertEqual(ed0["progress"]["progress_label"], "0 of 2")
		# Price only the first required line
		first = next(r for r in ed0["rows"] if r.get("required"))
		save_price_schedule_lines(
			pub,
			{
				"schedule_key": SCHEDULE_SUPPLY,
				"lines": [
					{
						"line_id": first["line_id"],
						"unit_price": "1000",
						"currency": "KES",
						"country_of_origin": "Kenya",
					}
				],
			},
		)
		ed1 = get_price_schedule_editor(pub, SCHEDULE_SUPPLY)
		self.assertEqual(ed1["progress"]["started"], 1)
		self.assertEqual(ed1["progress"]["progress_label"], "1 of 2")
		self.assertGreater(ed1["progress"]["progress_percent"], 0)

	def test_save_and_complete_single_lot(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		self._fill_required_supply(pub)
		ov = get_price_schedule_overview(pub)
		self.assertEqual(ov["schedules"][0]["status"], STATUS_COMPLETE)
		review = get_price_schedule_review(pub)
		self.assertEqual(review["complete_enabled"], 1)
		self.assertFalse(review["unresolved_issues"])
		done = complete_price_schedule(pub)
		self.assertEqual(done["section_complete_confirmed"], 1)
		self.assertEqual(done["section_status"], STATUS_COMPLETE)
		checklist = get_submission_checklist(pub)
		ps = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(ps["status"], STATUS_COMPLETE)
		self.assertIn("/sections/price_schedule", ps["action_url"])

	def test_complete_blocked_when_incomplete(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		with self.assertRaises(Exception):
			complete_price_schedule(pub)

	def test_edit_reopens_completed_section(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		self._fill_required_supply(pub)
		complete_price_schedule(pub)
		save_price_schedule_lines(
			pub,
			{
				"schedule_key": SCHEDULE_SUPPLY,
				"lines": [
					{
						"line_id": "ps-si-001",
						"unit_price": "2000",
						"currency": "KES",
						"country_of_origin": "Kenya",
					}
				],
			},
		)
		ov = get_price_schedule_overview(pub)
		self.assertIn(ov["section_status"], (STATUS_IN_PROGRESS, STATUS_COMPLETE))
		# complete_confirmed cleared
		review = get_price_schedule_review(pub)
		self.assertEqual(review["section_complete_confirmed"], 0)

	def test_fot_projection_without_discounts_on_ps(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		self._fill_required_supply(pub)
		complete_price_schedule(pub)
		bid = frappe.get_all(
			"Electronic Bid Submission",
			filters={"owner": "Administrator"},
			order_by="modified desc",
			limit=1,
			pluck="name",
		)[0]
		responses = json.loads(frappe.db.get_value("Electronic Bid Submission", bid, "responses") or "{}")
		ps = responses.get(SECTION_KEY) or {}
		self.assertTrue(is_price_schedule_complete(ps))
		proj = price_schedule_projection(ps)
		self.assertEqual(proj.get("complete"), 1)
		self.assertIsNotNone(proj.get("grand_total"))
		# FoT must show thousands separators (never raw 5000 dumps for large amounts)
		self.assertIn(",", format_money_display(proj.get("grand_total")))
		self.assertRegex(cstr(proj.get("total_display") or ""), r"[\d,]+\.\d{2}")
		fot = price_schedule_fot_projection(ps)
		self.assertIn(",", cstr(fot.get("grand_total_display") or ""))

	def test_multi_lot_overview_shows_selector(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_MULTI_LOT, clear=True)
		pub = out["publication_ref"]
		ov = get_price_schedule_overview(pub)
		self.assertEqual(ov["show_lot_selector"], 1)
		keys = {s["schedule_key"] for s in ov["schedules"]}
		self.assertIn(SCHEDULE_RECURRENT, keys)

	def test_server_rejects_client_totals_override(self):
		out = publish_lean_price_schedule_for_tests(fixture=FIXTURE_SINGLE_LOT, clear=True)
		pub = out["publication_ref"]
		save_price_schedule_lines(
			pub,
			{
				"schedule_key": SCHEDULE_SUPPLY,
				"totals": {"grand_total": "999999"},
				"computed": {"by_currency": {"KES": {"grand_total": "999999"}}},
				"lines": [
					{
						"line_id": "ps-si-001",
						"unit_price": "100",
						"currency": "KES",
						"country_of_origin": "Kenya",
					}
				],
			},
		)
		ed = get_price_schedule_editor(pub, SCHEDULE_SUPPLY)
		row = next(r for r in ed["rows"] if r["line_id"] == "ps-si-001")
		self.assertEqual(row["line_total"], "400.00")


class TestPriceScheduleStatusDerive(unittest.TestCase):
	def test_derive_not_started(self):
		sec = materialize_lean_price_schedule(FIXTURE_SINGLE_LOT)
		st, n = derive_price_schedule_section_status(sec, {})
		self.assertEqual(st, STATUS_NOT_STARTED)
		self.assertGreaterEqual(n, 1)
