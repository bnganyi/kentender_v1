"""ANL-CHG-001 v0.8 §§4–8, §10A — `GetProcurementAnalytics`, on fake owners serving dataset A1.

Every figure the boards picture is reproduced from owner facts, and every
failure branch of §8 is exercised. No database rows are read or written (the
Organisation Unit, Fiscal Year and Page lookups are doubled in `analytics_a1`).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_analytics_workspace
"""

from __future__ import annotations

import copy
import json

from frappe.tests import IntegrationTestCase

from kentender_core.services import analytics_contract as ac
from kentender_core.tests import analytics_a1 as a1
from kentender_core.tests.analytics_a1 import CHARLES, DANIEL, DH, FY, HR, PETER, A1, read


def seg(region_segments):
	return [(s["label"], s["count"]) for s in region_segments]


def column(overview, key):
	return next(c for c in overview["strip"]["columns"] if c["key"] == key)


class TestOverviewCharles(IntegrationTestCase):
	"""ANL-DES-21 — Charles, All years, All departments (ANL-AC-01, 04, 14, 15, 17, 18, 19)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.out = read(CHARLES)
		cls.ov = cls.out["overview"]

	def test_header_and_tabs(self):
		o = self.out
		self.assertEqual((o["verdict"], o["title"]), ("ok", "Procurement Analytics"))
		self.assertEqual(o["updated"], "Updated 18 June 2027, 10:00 EAT")
		self.assertEqual(o["scope"], "All departments")
		self.assertEqual([t["label"] for t in o["tabs"]], ["Overview", "Needs", "Departmental planning", "Annual planning", "Requisitions", "Tender proceedings"])
		self.assertEqual([t["route"] for t in o["tabs"]][:3], [["analytics"], ["analytics", "needs"], ["analytics", "departmental-planning"]])
		self.assertTrue(o["tabs"][0]["selected"])

	def test_filter_options_come_from_the_records(self):
		f = self.out["filters"]
		self.assertEqual([x["label"] for x in f["fy_options"]], ["FY 2027/28"])
		self.assertEqual([x["label"] for x in f["dept_options"]], ["Digital Health", "Human Resources Management and Development"])
		self.assertEqual(f["messages"], [])

	def test_strip_reconciles_each_area_on_its_own_unit(self):
		strip = self.ov["strip"]
		self.assertEqual(strip["note"], "These counts describe different records and are not added together.")
		needs, dpp, ann, req, ten = (column(self.ov, k) for k in ("needs", "departmental_planning", "annual_planning", "requisitions", "tender_proceedings"))
		self.assertEqual((needs["figure"], needs["unit"]), ("2", "Needs"))
		self.assertEqual(seg(needs["segments"]), [("Accepted for planning", 2)])
		self.assertEqual((dpp["figure"], dpp["unit"]), ("2", "departmental plans"))
		self.assertEqual((ann["figure"], ann["unit"]), ("7", "Plan items in the Active Plan"))
		self.assertEqual(seg(ann["segments"]), [("Fully covered", 5), ("Partly covered", 1), ("Not covered", 1)])
		self.assertEqual((req["figure"], req["unit"]), ("7", "Requisitions"))
		self.assertEqual(seg(req["segments"]), [("Submitted to Procurement", 1), ("Authorised", 6)])
		self.assertEqual((ten["figure"], ten["unit"]), ("6", "Tenders"))
		self.assertEqual(seg(ten["segments"]), [("Preparation", 1), ("Open", 1), ("Evaluation", 1), ("Award", 2), ("Closed", 1)])
		self.assertEqual([c["outstanding"] for c in strip["columns"]],
			["No outstanding matters recorded"] * 3 + ["1 outstanding matter", "4 outstanding matters"])
		self.assertEqual(ten["link"], {"label": "View Tender proceedings", "tab": "tender-proceedings"})

	def test_every_area_segments_add_up_to_its_count(self):
		for col in self.ov["strip"]["columns"]:
			self.assertEqual(sum(s["count"] for s in col["segments"]), int(col["figure"]), col["key"])

	def test_waiting_by_band(self):
		w = self.ov["waiting"]
		self.assertEqual([b["label"] for b in w["legend"]], ["0–7 days", "8–30 days", "31–90 days", "Over 90 days"])
		self.assertEqual([(r["label"], seg(r["segments"])) for r in w["rows"]],
			[("Requisitions", [("0–7 days", 1)]), ("Tender proceedings", [("0–7 days", 3), ("8–30 days", 1)])])
		self.assertEqual(w["none_text"], "Needs, departmental planning and annual planning: no outstanding matters recorded.")
		self.assertEqual(w["caption"], "Days since each matter reached its current holder.")

	def test_plan_coverage(self):
		c = self.ov["coverage"]
		self.assertEqual(c["result"], "81% of planned value is covered by authorised requisitions")
		self.assertEqual(c["planned"], "Planned value KES 68,500,000 in the Active Plan")
		self.assertEqual([(s["label"], s["text"]) for s in c["segments"]],
			[("Covered by authorised requisitions", "KES 55,500,000"), ("Not yet covered", "KES 13,000,000")])
		self.assertEqual(c["items"], "5 Plan items fully covered, 1 partly covered, 1 not covered.")

	def test_time_between_key_steps(self):
		rows = self.ov["steps"]["rows"]
		self.assertEqual([(r["label"], r["completed"], r["median_text"], r["shortest_text"], r["longest_text"]) for r in rows], [
			("Requisition submitted to authorised", 6, "8.5 days", "6 days", "14 days"),
			("Requisition authorised to Tender started", 6, "3.5 days", "1 day", "5 days"),
			("Tender started to published", 5, "26 days", "21 days", "56 days"),
			("Bid opening complete to evaluation report sent", 2, "32.5 days", "28 days", "37 days"),
			("Evaluation report sent to AO decision recorded", 1, "13 days", "13 days", "13 days")])
		self.assertEqual(self.ov["steps"]["axis"], {"max": 60, "ticks": [0, 10, 20, 30, 40, 50, 60]})
		self.assertEqual(self.ov["steps"]["caption"], "Calendar days, last 12 months.")

	def test_funding_message_when_all_years(self):
		self.assertEqual(self.ov["funding"], {"status": "message", "message": "Choose a financial year to see its funding position."})

	def test_definitions_state_the_window_and_read_time(self):
		text = self.out["definitions"]
		self.assertIn("in the 12 months to 18 June 2027; these are not statutory periods", text)
		self.assertTrue(text.endswith("All area reads completed at 10:00 EAT."))

	def test_no_forbidden_words_or_measures_anywhere(self):
		blob = json.dumps(self.out, default=str).lower()
		for word in ("overdue", "at risk", "forecast", "savings", "utilisation", "risk score"):
			self.assertNotIn(word, blob)


class TestOtherViewers(IntegrationTestCase):
	def test_technical_operator_reads_what_charles_reads(self):
		charles, daniel = read(CHARLES), read(DANIEL)
		for key in ("overview", "filters", "definitions", "scope"):
			self.assertEqual(charles[key], daniel[key])

	def test_funding_position_for_the_whole_budget(self):
		f = read(CHARLES, fy=FY)["overview"]["funding"]
		self.assertEqual(f["status"], "ok")
		self.assertEqual((f["title"], f["version_text"]), ("Ministry of Health procurement budget FY 2027/28", "Current version 1"))
		self.assertEqual(f["registered"], "KES 150,000,000")
		self.assertEqual([(s["label"], s["text"]) for s in f["segments"]],
			[("Reserved for requisitions", "KES 55,500,000"), ("Committed to contracts", "KES 0"), ("Available to reserve", "KES 94,500,000")])
		self.assertTrue(f["segments"][1]["keep_zero"])
		self.assertEqual(f["caption"], "Available to reserve is not a cash balance. Committed to contracts is Budget's record of contract commitments; none is recorded.")
		self.assertEqual(sum(s["value"] for s in f["segments"]), 150_000_000)

	def test_no_funding_region_or_message_outside_the_audience(self):
		kinds = {ac.NEEDS, ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS, ac.REQUISITIONS, ac.TENDERS}
		self.assertIsNone(read(CHARLES, A1(kinds=kinds), fy=FY)["overview"]["funding"])
		self.assertIsNone(read(CHARLES, A1(kinds=kinds))["overview"]["funding"])

	def test_filtering_to_the_year_keeps_every_count_and_the_window(self):
		whole, yearly = read(CHARLES), read(CHARLES, fy=FY)
		self.assertEqual(whole["overview"]["strip"], yearly["overview"]["strip"])
		self.assertEqual(whole["overview"]["steps"], yearly["overview"]["steps"])
		self.assertEqual(read(CHARLES, fy=a1.FY_OTHER)["empty"], True)

	def test_peter_department_overview(self):
		out = read(PETER, A1("hr", funding_view="department"), dept=HR)
		ov = out["overview"]
		self.assertEqual(out["scope"], "Human Resources Management and Development")
		cols = {c["key"]: c for c in ov["strip"]["columns"]}
		self.assertEqual([(k, cols[k]["figure"], cols[k]["unit"]) for k in cols], [
			("needs", "1", "Need"), ("departmental_planning", "1", "departmental plan"), ("annual_planning", "4", "Plan items in the Active Plan"),
			("requisitions", "4", "Requisitions"), ("tender_proceedings", "4", "Tenders")])
		self.assertEqual(seg(cols["annual_planning"]["segments"]), [("Fully covered", 3), ("Partly covered", 1)])
		self.assertEqual(seg(cols["requisitions"]["segments"]), [("Authorised", 4)])
		self.assertEqual(seg(cols["tender_proceedings"]["segments"]), [("Preparation", 1), ("Open", 1), ("Evaluation", 1), ("Award", 1)])
		self.assertEqual(cols["tender_proceedings"]["outstanding"], "3 outstanding matters")
		self.assertEqual([(r["label"], seg(r["segments"])) for r in ov["waiting"]["rows"]], [("Tender proceedings", [("0–7 days", 2), ("8–30 days", 1)])])
		self.assertEqual(ov["waiting"]["none_text"], "Needs, departmental planning, annual planning and requisitions: no outstanding matters recorded.")
		cov = ov["coverage"]
		self.assertEqual((cov["result"], cov["planned"], cov["items"]), ("96% of planned value is covered by authorised requisitions",
			"Planned value KES 22,500,000 in the Active Plan", "3 Plan items fully covered, 1 partly covered, 0 not covered."))
		self.assertEqual([(r["completed"], r["median_text"], r["shortest_text"], r["longest_text"]) for r in ov["steps"]["rows"]],
			[(4, "7 days", "6 days", "12 days"), (4, "3.5 days", "1 day", "5 days"), (3, "29 days", "21 days", "56 days"),
			(1, "28 days", "28 days", "28 days"), (1, "13 days", "13 days", "13 days")])
		self.assertEqual(ov["funding"]["message"], "Choose a financial year to see its funding position.")

	def test_peter_department_funding_view(self):
		f = read(PETER, A1("hr", funding_view="department"), fy=FY, dept=HR)["overview"]["funding"]
		self.assertEqual(f["scope"], "Human Resources Management and Development")
		self.assertEqual(f["own"]["heading"], "Budget lines available to Human Resources Management and Development")
		self.assertEqual(f["own"]["registered"], "KES 30,000,000")
		self.assertEqual([(s["label"], s["text"]) for s in f["own"]["segments"]],
			[("Reserved for requisitions", "KES 13,500,000"), ("Committed to contracts", "KES 0"), ("Available to reserve", "KES 16,500,000")])
		self.assertEqual(f["shared"]["figures"], [{"label": "Reserved for this department's requisitions", "value": "KES 8,000,000"},
			{"label": "Committed to contracts for this department", "value": "KES 0"}])
		self.assertNotIn("registered", f["shared"])
		self.assertIn("not divided by department", f["caption"])

	def test_whole_budget_audience_with_a_department_gets_the_department_view(self):
		f = read(CHARLES, fy=FY, dept=HR)["overview"]["funding"]
		self.assertEqual(f["own"]["registered"], "KES 30,000,000")
		self.assertEqual(f["shared"]["figures"][0]["value"], "KES 8,000,000")

	def test_outsider_and_no_area(self):
		self.assertEqual(read(a1.OUTSIDER)["verdict"], "denied")
		out = read(CHARLES, A1(kinds=set()))
		self.assertEqual((out["verdict"], out["message"]), ("no_area", "No Analytics records are available to your responsibilities."))
		self.assertIsNone(out["overview"])
		self.assertEqual(len(out["tabs"]), 6)


class TestTenderTab(IntegrationTestCase):
	"""ANL-DES-22, 23, 31A (ANL-AC-04, 06, 19, 20)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.out = read(CHARLES, tab="tender-proceedings")
		cls.area = cls.out["area"]

	def test_result_outstanding_and_charts(self):
		a = self.area
		self.assertEqual(a["result_text"], "6 Tenders")
		self.assertEqual([(r["title"], r["text"], r["waiting"], r["since"]) for r in a["outstanding"]["rows"]], [
			("Supply of IT peripherals", "State the warranty period required from suppliers. Awaiting correction by Brian Wafula.", "Waiting 2 days", "since 16 June, 09:00"),
			("Supply of office desks", "Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.", "Waiting 15 days", "since 3 June, 10:00"),
			("Supply of printers", "Awaiting professional opinion by Charles Mutiso.", "Waiting 2 days", "since 16 June, 14:07"),
			("Supply of monitors", "Award decision recorded. Required bidder notices are awaiting delivery.", "Waiting 1 day", "since 17 June, 11:00")])
		stages = a["charts"]["stages"]
		self.assertEqual([(r["label"], r["count"], r["value_text"]) for r in stages["rows"]], [
			("Tender preparation and publication", 1, "KES 6,500,000"), ("Open for bids", 1, "KES 8,000,000"), ("Evaluation", 1, "KES 3,500,000"),
			("Award", 2, "KES 12,500,000"), ("Closed", 1, "KES 25,000,000")])
		self.assertEqual(stages["note"], "1 AO award decision recorded. Award amount KES 7,185,000.")
		m = a["charts"]["monthly"]
		by = {s["key"]: dict(zip([x["label"] for x in m["months"]], s["counts"])) for s in m["series"]}
		self.assertEqual(by["published"]["Apr 2027"], 4)
		self.assertEqual(by["published"]["May 2027"], 1)
		self.assertEqual((by["cancelled"]["Jun 2027 (to date)"], by["decisions"]["Jun 2027 (to date)"]), (1, 1))
		self.assertEqual(sum(by["published"].values()), 5)
		self.assertEqual([s["label"] for s in m["series"]], ["Published", "Cancelled", "AO award decisions"])
		self.assertEqual([r["label"] for r in a["steps"]["rows"]], ["Requisition authorised to Tender started", "Tender started to published",
			"Bid opening complete to evaluation report sent", "Evaluation report sent to AO decision recorded"])

	def test_register_rows(self):
		reg = self.area["register"]
		self.assertEqual(reg["footer"], "Showing 6 of 6 Tenders")
		self.assertEqual([c["label"] for c in reg["columns"]], ["Tender", "Current position", "Authorised requisition value", "Recorded AO outcome", "Action"])
		got = [(r["cells"]["tender"], r["cells"]["authorised_requisition_value"]["text"], r["cells"]["recorded_ao_outcome"]["text"]) for r in reg["rows"]]
		self.assertEqual(got[0], ({"text": "Supply of IT peripherals", "secondary": "TND-MOH-2027-041", "quiet": False}, "KES 6,500,000", "No AO award decision recorded"))
		self.assertEqual(got[4][2], "Award decision recorded 17 June 2027, 11:00 EAT")
		self.assertEqual(reg["rows"][4]["cells"]["recorded_ao_outcome"]["secondary"], "Award amount KES 7,185,000")
		self.assertEqual(got[5][2], "Cancellation recorded 16 June 2027, 12:00 EAT")
		self.assertEqual([o["label"] for o in reg["state_options"]], ["Tender preparation and publication", "Open for bids", "Evaluation", "Award", "Closed"])
		self.assertEqual(reg["state_all"], "All stages")
		self.assertTrue(all(r["action"]["route"] for r in reg["rows"]))

	def test_award_stage_filters_rows_not_charts(self):
		out = read(CHARLES, tab="tender-proceedings", state="award")["area"]
		self.assertEqual([r["cells"]["tender"]["secondary"] for r in out["register"]["rows"]], ["TND-MOH-2027-044", "TND-MOH-2027-045"])
		self.assertEqual(out["register"]["footer"], "Showing 2 of 2 matching Tenders")
		self.assertEqual(out["register"]["clear"], {"label": "Clear stage filter", "kind": "state"})
		self.assertEqual(out["scope_label"], "All 6 Tenders in this area")
		self.assertEqual(out["charts"]["stages"]["rows"][3]["selected"], True)
		self.assertEqual(out["charts"]["stages"]["rows"], self.area["charts"]["stages"]["rows"][:3] + [dict(self.area["charts"]["stages"]["rows"][3], selected=True)] + self.area["charts"]["stages"]["rows"][4:])
		self.assertEqual(out["outstanding"], self.area["outstanding"])

	def test_search_with_no_match_keeps_the_whole_area(self):
		out = read(CHARLES, tab="tender-proceedings", search="laboratory")["area"]
		reg = out["register"]
		self.assertEqual((reg["rows"], reg["footer"], reg["empty_text"], reg["clear"]), ([], "0 matching Tenders", "No records match these filters.", {"label": "Clear search", "kind": "search"}))
		self.assertEqual(out["scope_label"], "All 6 Tenders in this area")
		self.assertEqual(out["result_text"], "6 Tenders")

	def test_search_matches_reference_or_title(self):
		rows = read(CHARLES, tab="tender-proceedings", search="tnd-moh-2027-04")["area"]["register"]["rows"]
		self.assertEqual(len(rows), 6)
		self.assertEqual(len(read(CHARLES, tab="tender-proceedings", search="printers")["area"]["register"]["rows"]), 1)

	def test_one_tenders_stage_unavailable(self):
		def broken():
			recs = a1.tenders()
			t = next(r for r in recs if r["reference"].endswith("044"))
			t["bucket"], t["position"], t["outstanding"] = ac.UNAVAILABLE, "Status unavailable", None
			return recs
		provider = A1()
		provider_facts = provider.facts
		provider.facts = lambda **kw: {"records": broken()} if kw["kind"] == ac.TENDERS else provider_facts(**kw)
		out = read(CHARLES, provider, tab="tender-proceedings")["area"]
		self.assertEqual(out["result_text"], "6 Tenders")
		rows = {r["label"]: (r["count"], r["value_text"]) for r in out["charts"]["stages"]["rows"]}
		self.assertEqual(rows["Award"], (1, "KES 7,500,000"))
		self.assertEqual(rows["Status unavailable"], (1, "KES 5,000,000"))
		row = next(r for r in out["register"]["rows"] if r["cells"]["tender"]["secondary"].endswith("044"))
		self.assertEqual((row["cells"]["current_position"]["text"], row["cells"]["recorded_ao_outcome"]["text"]), ("Status unavailable", "Could not be loaded"))
		self.assertTrue(row["action"]["route"])
		unread = next(o for o in out["outstanding"]["rows"] if o["title"] == "Supply of printers")
		self.assertEqual((unread["text"], unread["waiting"], unread["since"]), ("We could not load the current position.", "", ""))
		self.assertEqual(len(out["outstanding"]["rows"]), 4)

	def test_peter_tender_tab_has_shares_and_no_amount(self):
		out = read(PETER, A1("hr"), tab="tender-proceedings", dept=HR)["area"]
		self.assertEqual(out["result_text"], "4 Tenders")
		self.assertEqual([r["title"] for r in out["outstanding"]["rows"]], ["Supply of IT peripherals", "Supply of office desks", "Supply of monitors"])
		self.assertEqual([(r["label"], r["count"], r["value_text"]) for r in out["charts"]["stages"]["rows"]],
			[("Tender preparation and publication", 1, "KES 2,500,000"), ("Open for bids", 1, "KES 8,000,000"), ("Evaluation", 1, "KES 3,500,000"), ("Award", 1, "KES 7,500,000")])
		self.assertEqual(out["charts"]["stages"]["note"], "1 AO award decision recorded.")
		first = out["register"]["rows"][0]["cells"]
		self.assertEqual(first["authorised_requisition_value"], {"text": "KES 2,500,000", "secondary": "Human Resources Management and Development share of KES 6,500,000", "quiet": False})
		self.assertEqual(first["current_position"]["secondary"], "Human Resources Management and Development contributes; Lead: Digital Health")
		self.assertEqual(out["register"]["rows"][3]["cells"]["recorded_ao_outcome"], {"text": "Award decision recorded 17 June 2027, 11:00 EAT", "secondary": "", "quiet": False})
		self.assertEqual(out["register"]["footer"], "Showing 4 of 4 Tenders")
		self.assertEqual([o["label"] for o in out["register"]["state_options"]], ["Tender preparation and publication", "Open for bids", "Evaluation", "Award"])
		monthly = {s["key"]: dict(zip([m["label"] for m in out["charts"]["monthly"]["months"]], s["counts"])) for s in out["charts"]["monthly"]["series"]}
		self.assertEqual((monthly["published"]["Apr 2027"], monthly["published"]["May 2027"], monthly["decisions"]["Jun 2027 (to date)"]), (2, 1, 1))

	def test_paging_beyond_ten_rows_is_stable(self):
		many = []
		for i in range(23):
			rec = copy.deepcopy(a1.tenders()[1])
			rec.update(id=f"T-X{i:02d}", reference=f"TND-X-{i:02d}", title=f"Tender {i:02d}", outstanding=None)
			many.append(rec)
		provider = A1()
		provider.facts = lambda **kw: {"records": copy.deepcopy(many)}
		first = read(CHARLES, provider, tab="tender-proceedings")["area"]["register"]
		self.assertEqual((len(first["rows"]), first["footer"], first["total"]), (10, "Showing 10 of 23 Tenders", 23))
		second = read(CHARLES, provider, tab="tender-proceedings", cursor=first["next_cursor"])["area"]["register"]
		third = read(CHARLES, provider, tab="tender-proceedings", cursor=second["next_cursor"])["area"]["register"]
		keys = [r["key"] for r in first["rows"] + second["rows"] + third["rows"]]
		self.assertEqual((len(second["rows"]), len(third["rows"]), len(set(keys)), third["next_cursor"]), (10, 3, 23, None))
		self.assertEqual(third["footer"], "Showing 23 of 23 Tenders")


class TestPageHelpers(IntegrationTestCase):
	"""Fields the page draws from (page_needs.md): titles, flags, axis lines, the applied state."""

	def test_register_titles_and_matter_flags(self):
		for tab, title in (("needs", "Needs"), ("departmental-planning", "Departmental plans"), ("annual-planning", "Plan items"),
				("requisitions", "Requisitions"), ("tender-proceedings", "Tenders")):
			self.assertEqual(read(CHARLES, tab=tab)["area"]["register"]["title"], title)
		flags = {c["key"]: c["has_matters"] for c in read(CHARLES)["overview"]["strip"]["columns"]}
		self.assertEqual(flags, {"needs": False, "departmental_planning": False, "annual_planning": False, "requisitions": True, "tender_proceedings": True})

	def test_month_axis_lines(self):
		months = read(CHARLES, tab="needs")["area"]["charts"]["monthly"]["months"]
		self.assertEqual([m["axis_lines"] for m in months][:2], [["Jul", "2026"], ["Aug"]])
		self.assertEqual(months[6]["axis_lines"], ["Jan", "2027"])
		self.assertEqual(months[-1]["axis_lines"], ["Jun", "(to date)"])

	def test_the_applied_state_is_always_offered(self):
		reg = read(CHARLES, tab="tender-proceedings", state="opening")["area"]["register"]
		self.assertIn(("opening", "Opening"), [(o["key"], o["label"]) for o in reg["state_options"]])
		self.assertEqual(reg["rows"], [])

	def test_by_item_legend_lists_both_tones_even_when_only_one_occurs(self):
		legend = read(PETER, A1("hr"), tab="annual-planning", dept=HR)["area"]["charts"]["by_item"]["legend"]
		self.assertEqual([(x["label"], x["tone"]) for x in legend], [("Covered", "pair-strong"), ("Not yet covered", "pair-tint")])

	def test_quiet_flag_is_only_the_no_decision_line(self):
		rows = read(CHARLES, tab="tender-proceedings")["area"]["register"]["rows"]
		self.assertEqual([r["cells"]["recorded_ao_outcome"]["quiet"] for r in rows], [True, True, True, True, False, False])


class TestRequisitionsAndPlanning(IntegrationTestCase):
	def test_requisitions_tab(self):
		a = read(CHARLES, tab="requisitions")["area"]
		self.assertEqual(a["result_text"], "7 Requisitions")
		self.assertEqual([(r["title"], r["waiting"], r["since"]) for r in a["outstanding"]["rows"]], [("Clinic equipment requisition", "Waiting 2 days", "since 16 June, 11:00")])
		self.assertEqual([(r["label"], r["count"], r["value_text"]) for r in a["charts"]["states"]["rows"]],
			[("Submitted to Procurement", 1, "KES 12,000,000 requested"), ("Authorised", 6, "KES 55,500,000 authorised")])
		m = a["charts"]["monthly"]
		by = {s["key"]: dict(zip([x["label"] for x in m["months"]], s["counts"])) for s in m["series"]}
		self.assertEqual((by["submitted"]["Mar 2027"], by["authorised"]["Mar 2027"], by["submitted"]["Jun 2027 (to date)"]), (6, 6, 1))
		self.assertEqual([r["label"] for r in a["steps"]["rows"]], ["Requisition submitted to authorised", "Requisition authorised to Tender started"])
		rows = a["register"]["rows"]
		self.assertEqual(rows[0]["cells"]["requisition"]["text"], "Clinic equipment requisition")
		self.assertEqual((rows[0]["cells"]["requisition_value"]["text"], rows[0]["cells"]["tender_relationship"]["text"]), ("KES 12,000,000 requested", "No Tender created"))
		self.assertEqual(rows[1]["cells"]["tender_relationship"]["text"], "TND-MOH-2027-041 created")
		self.assertEqual(a["register"]["footer"], "Showing 7 of 7 Requisitions")
		self.assertEqual([o["label"] for o in a["register"]["state_options"]], ["Submitted to Procurement", "Authorised"])

	def test_requisition_state_filter_changes_rows_only(self):
		a = read(CHARLES, tab="requisitions", state="authorised")["area"]
		self.assertEqual((len(a["register"]["rows"]), a["register"]["footer"]), (6, "Showing 6 of 6 matching Requisitions"))
		self.assertEqual(len(a["charts"]["states"]["rows"]), 2)

	def test_annual_planning_tab(self):
		a = read(CHARLES, tab="annual-planning")["area"]
		self.assertEqual(a["result_text"], "7 Plan items in the Active Plan")
		self.assertEqual(a["secondary"], "No outstanding matters recorded in this selection.")
		self.assertEqual(a["source"], "Ministry of Health Annual Procurement Plan, Active Version 1")
		self.assertEqual(a["figures"], [{"label": "Planned value", "value": "KES 68,500,000"}, {"label": "Covered by authorised requisitions", "value": "KES 55,500,000 (81%)"}])
		items = a["charts"]["by_item"]["rows"]
		self.assertEqual([r["label"] for r in items], ["Servers", "Clinic equipment", "Network switches", "Monitors", "IT peripherals", "Printers", "Office desks"])
		self.assertEqual([(s["label"], s["text"]) for s in items[2]["segments"]], [("Covered", "KES 8,000,000"), ("Not yet covered", "KES 1,000,000")])
		self.assertEqual([(s["label"], s["text"]) for s in items[1]["segments"]], [("Not yet covered", "KES 12,000,000")])
		depts = a["charts"]["by_department"]
		self.assertEqual([(r["label"], r["percent_text"]) for r in depts["rows"]], [("Digital Health", "74%"), ("Human Resources Management and Development", "96%")])
		self.assertEqual([(s["label"], s["text"]) for s in depts["rows"][0]["segments"]], [("Covered", "KES 34,000,000"), ("Not yet covered", "KES 12,000,000")])
		self.assertEqual(depts["caption"], "IT peripherals is shared: KES 4,000,000 is attributed to Digital Health and KES 2,500,000 to Human Resources Management and Development.")
		timing = a["charts"]["timing"]
		self.assertEqual([(r["label"], r["text"]) for r in timing["rows"]], [
			("Network switches", "25 days after approved date"), ("Office desks", "7 days after approved date"), ("Servers", "7 days after approved date"),
			("Monitors", "On the approved date"), ("Printers", "3 days before approved date"), ("IT peripherals", "No date recorded")])
		self.assertNotIn("Clinic equipment", [r["label"] for r in timing["rows"]])
		reg = a["register"]
		self.assertEqual(reg["state_options"], [])
		self.assertEqual(reg["rows"][0]["cells"]["department"]["text"], "Digital Health")
		self.assertEqual(next(r for r in reg["rows"] if r["key"] == "I-B")["cells"]["department"]["text"],
			"Digital Health; Human Resources Management and Development contributes")
		self.assertEqual(next(r for r in reg["rows"] if r["key"] == "I-A")["cells"]["covered_by_authorised_requisitions"]["text"], "KES 0")

	def test_peter_annual_planning_uses_only_his_allocations(self):
		a = read(PETER, A1("hr"), tab="annual-planning", dept=HR)["area"]
		self.assertEqual(a["result_text"], "4 Plan items in the Active Plan")
		self.assertEqual(a["figures"][1]["value"], "KES 21,500,000 (96%)")
		items = {r["label"]: r for r in a["charts"]["by_item"]["rows"]}
		self.assertEqual(items["IT peripherals"]["share_note"], "Human Resources Management and Development share")
		self.assertEqual([(s["label"], s["text"]) for s in items["IT peripherals"]["segments"]], [("Covered", "KES 2,500,000")])
		self.assertEqual(len(a["charts"]["by_department"]["rows"]), 1)
		self.assertEqual(a["charts"]["by_department"]["caption"], "")
		row = next(r for r in a["register"]["rows"] if r["key"] == "I-B")
		self.assertEqual(row["cells"]["planned_value"], {"text": "KES 2,500,000", "secondary": "Human Resources Management and Development share of KES 6,500,000", "quiet": False})
		self.assertEqual([r["label"] for r in a["charts"]["timing"]["rows"]], ["Network switches", "Office desks", "Monitors", "IT peripherals"])

	def test_needs_and_departmental_planning_tabs(self):
		n = read(CHARLES, tab="needs")["area"]
		self.assertEqual((n["result_text"], n["secondary"]), ("2 Needs accepted for planning", "No outstanding matters recorded in this selection."))
		by = dict(zip([m["label"] for m in n["charts"]["monthly"]["months"]], n["charts"]["monthly"]["series"][0]["counts"]))
		self.assertEqual((by["Nov 2026"], sum(by.values())), (2, 2))
		self.assertEqual([(r["title"], r["position"]) for r in n["register"]["rows"]], [("Clinic equipment", "Accepted for planning"), ("Office furniture", "Accepted for planning")])
		self.assertEqual(n["register"]["footer"], "Showing 2 of 2 Needs")
		self.assertEqual(n["register"]["layout"], "compact")
		d = read(CHARLES, tab="departmental-planning")["area"]
		self.assertEqual(d["result_text"], "2 departmental plans accepted")
		self.assertEqual(dict(zip([m["label"] for m in d["charts"]["monthly"]["months"]], d["charts"]["monthly"]["series"][0]["counts"]))["Dec 2026"], 2)
		self.assertEqual(d["register"]["footer"], "Showing 2 of 2 departmental plans")


class TestFailuresAndStates(IntegrationTestCase):
	"""ANL §8 and ANL-DES-31 (ANL-AC-08, 13, 23)."""

	def test_one_area_unavailable_keeps_the_others(self):
		out = read(CHARLES, A1(fail={ac.NEEDS}))
		needs = column(out["overview"], "needs")
		self.assertEqual((needs["status"], needs["message"], needs["retry"]), ("unavailable", "Needs could not be loaded.", True))
		self.assertNotIn("figure", needs)
		self.assertEqual(column(out["overview"], "requisitions")["figure"], "7")
		self.assertTrue(out["definitions"].endswith("The Needs read is unavailable. Other area reads completed at 10:00 EAT."))
		self.assertEqual(out["overview"]["waiting"]["status"], "incomplete")
		self.assertEqual(out["overview"]["coverage"]["status"], "ok")

	def test_all_reads_failed(self):
		out = read(CHARLES, A1(fail={ac.NEEDS, ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS, ac.REQUISITIONS, ac.TENDERS}))
		self.assertEqual((out["verdict"], out["message"]), ("failed", "Analytics could not be loaded."))
		self.assertIsNone(out["overview"])

	def test_a_tab_whose_area_fails_says_so_and_names_no_zero(self):
		out = read(CHARLES, A1(fail={ac.TENDERS}), tab="tender-proceedings")
		self.assertEqual(out["verdict"], "ok")
		self.assertEqual((out["area"]["status"], out["area"]["message"], out["area"]["retry"]), ("unavailable", "Tender proceedings could not be loaded.", True))
		self.assertNotIn("register", out["area"])

	def test_coverage_unavailable_keeps_the_count(self):
		out = read(CHARLES, A1(extra={ac.PLAN_ITEMS: {"unavailable_measures": ["coverage"]}}))
		cov = out["overview"]["coverage"]
		self.assertEqual((cov["status"], cov["message"], cov["retry"]), ("unavailable", "Plan coverage could not be loaded.", True))
		self.assertNotIn("percent", cov)
		col = column(out["overview"], "annual_planning")
		self.assertEqual((col["figure"], col["segments"], col["coverage_unavailable"], col["outstanding"]), ("7", [], "Coverage unavailable", "No outstanding matters recorded"))

	def test_incomplete_read_withholds_the_percentage(self):
		out = read(CHARLES, A1(extra={ac.PLAN_ITEMS: {"incomplete": True}}))
		cov = out["overview"]["coverage"]
		self.assertEqual((cov["status"], cov["percent"], cov["result"], cov["incomplete_text"]), ("incomplete", None, "",
			"Some records could not be included, so these figures may be incomplete."))
		self.assertEqual(cov["segments"][0]["text"], "KES 55,500,000")

	def test_identity_incomplete_claims_no_total(self):
		out = read(CHARLES, A1(extra={ac.NEEDS: {"identity_incomplete": True}}))
		col = column(out["overview"], "needs")
		self.assertEqual((col["status"], col["message"]), ("incomplete", "Needs totals are unavailable."))
		self.assertNotIn("figure", col)

	def test_a_step_whose_owner_failed_is_unavailable_and_others_stand(self):
		out = read(CHARLES, A1(fail={ac.REQUISITIONS}))
		rows = {r["key"]: r for r in out["overview"]["steps"]["rows"]}
		self.assertEqual((rows["T1"]["status"], rows["T2"]["status"], rows["T3"]["status"]), ("unavailable", "unavailable", "ok"))
		self.assertEqual(rows["T3"]["median_text"], "26 days")
		self.assertEqual(out["overview"]["steps"]["status"], "incomplete")

	def test_a_start_event_missing_excludes_the_step_and_marks_incomplete(self):
		def facts():
			recs = a1.tenders()
			for r in recs:
				if r["reference"].endswith("042"):
					r["started_at"] = None
			return recs
		provider = A1()
		base = provider.facts
		provider.facts = lambda **kw: {"records": facts()} if kw["kind"] == ac.TENDERS else base(**kw)
		steps = read(CHARLES, provider)["overview"]["steps"]
		t3 = next(r for r in steps["rows"] if r["key"] == "T3")
		self.assertEqual((t3["completed"], steps["status"]), (4, "incomplete"))

	def test_empty_selection_is_not_an_error(self):
		provider = A1()
		provider.facts = lambda **kw: {"records": []}
		out = read(CHARLES, provider)
		self.assertEqual((out["verdict"], out["empty"], out["message"]), ("ok", True, "No records are available in this selection."))
		self.assertIsNone(out["overview"])

	def test_invalid_filters_keep_the_valid_parts_and_never_widen(self):
		# ANL-AC-13: the message is shown, the valid parts stay in the filter row, and no figure is drawn for the invalid choice.
		out = read(CHARLES, fy="bogus", dept=HR)
		self.assertEqual(out["filters"]["messages"], ["Choose an available financial year."])
		self.assertEqual((out["filters"]["fy"], out["filters"]["dept"], out["filters"]["invalid"]), ("", HR, True))
		self.assertEqual((out["verdict"], out["overview"], out["area"], out["empty"]), ("ok", None, None, False))
		peter = read(PETER, A1("hr"), dept="OU-OUTSIDE")
		self.assertEqual(peter["filters"]["messages"], ["Choose a department in your permitted area."])
		self.assertIsNone(peter["overview"])
		bad = read(CHARLES, tab="tender-proceedings", state="nonsense")
		self.assertEqual(bad["filters"]["messages"], ["Choose an available state."])
		self.assertIsNone(bad["area"])
		self.assertEqual([x["label"] for x in bad["filters"]["dept_options"]], ["Digital Health", "Human Resources Management and Development"])
		self.assertEqual(read(CHARLES, tab="annual-planning", state="x")["filters"]["messages"], ["Choose an available state."])
		both = read(CHARLES, fy="bogus", dept="OU-X")
		self.assertEqual(both["filters"]["messages"], ["Choose an available financial year.", "Choose a department in your permitted area."])
		self.assertFalse(read(CHARLES)["filters"]["invalid"])

	def test_unknown_tab_reads_as_overview(self):
		self.assertEqual(read(CHARLES, tab="nope")["tab"], "overview")

	def test_no_active_plan_is_not_zero_items(self):
		provider = A1()
		base = provider.facts
		provider.facts = lambda **kw: {"records": []} if kw["kind"] == ac.PLAN_ITEMS else base(**kw)
		col = column(read(CHARLES, provider)["overview"], "annual_planning")
		self.assertEqual((col["unit"], col["figure"]), ("No Active Plan", ""))
		self.assertEqual(read(CHARLES, provider, tab="annual-planning")["area"]["result_text"], "No Active Plan")
		self.assertIsNone(read(CHARLES, provider)["overview"]["coverage"])

	def test_a_provider_that_returns_bad_records_makes_the_read_incomplete_not_zero(self):
		provider = A1()
		base = provider.facts
		def bad(**kw):
			out = base(**kw)
			if kw["kind"] == ac.NEEDS:
				out["records"].append({"kind": ac.NEEDS, "id": "bad", "title": "x"})
			return out
		provider.facts = bad
		out = read(CHARLES, provider, tab="needs")
		self.assertEqual(out["area"]["incomplete_text"], "Some records could not be included, so these figures may be incomplete.")
		self.assertEqual(out["area"]["result_text"], "2 Needs accepted for planning")

	def test_access_is_a_cheap_role_check(self):
		from kentender_core.services import analytics_workspace as aw
		provider = A1(kinds={ac.TENDERS})
		with a1.world(CHARLES):
			access = aw.get_access("x@example.test", providers=[provider], at=a1.AT)
		self.assertEqual(access, {"allowed": True, "areas": ["tender-proceedings"], "failed": 0})
		self.assertEqual(provider.calls, [])
		with a1.world(a1.OUTSIDER):
			self.assertFalse(aw.get_access("x@example.test", providers=[provider], at=a1.AT)["allowed"])
