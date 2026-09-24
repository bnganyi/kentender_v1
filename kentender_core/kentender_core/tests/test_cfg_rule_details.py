# CFG-CHG-002 v0.14 §10.6/§10.8 (tracker CFG14-5D) — "Details" is its own
# status beside "Source check": the rule list and the saved detail say which
# required details a version still lacks, from the server, using the same
# labels the preview reports. Read-only: nothing is written.
import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services import procurement_settings as settings
from kentender_core.services import regulatory_reference as register


class TestRuleDetailsMissing(FrappeTestCase):
	def test_labels_follow_the_preview_and_the_board(self):
		self.assertEqual(
			register.rule_details_missing({}),
			["Which date determines the rule to use?", "Instrument", "Provisions", "Interpretation"],
		)
		complete = {
			"applicability_basis": "Financial year start",
			"source_instrument": "PPADR 2020",
			"provision": "r. 41",
			"interpretation": "Applies to all methods.",
		}
		self.assertEqual(register.rule_details_missing(complete), [])
		# Blank text is missing, not supplied.
		self.assertEqual(register.rule_details_missing({**complete, "provision": "   "}), ["Provisions"])

	def test_a_method_rule_without_conditions_lists_conditions_and_evidence(self):
		values = {"applicability_basis": "Financial year start", "source_instrument": "PPADR", "provision": "r. 1", "interpretation": "x"}
		self.assertEqual(register.rule_details_missing(values, conditions=[]), ["Conditions and evidence"])
		self.assertEqual(register.rule_details_missing(values, conditions=[{"condition_id": "G"}]), [])

	def test_every_read_of_a_version_carries_its_missing_details(self):
		sets = [row for row in register.list_reference_sets() if row["has_version"]]
		if not sets:
			self.skipTest("no reference versions on this site")
		row = sets[0]
		self.assertIn("details_missing", row["version"])
		detail = register.get_regulatory_reference_version(row["version"]["name"])
		self.assertEqual(detail["details_missing"], row["version"]["details_missing"])
		# The saved detail is headed by the rule's own name (§10.6).
		self.assertEqual(detail["display_name"], row["display_name"])

		methods = settings.list_method_profiles()
		if methods:
			self.assertIsInstance(methods[0]["details_missing"], list)
			# The method model has no interpretation field of its own.
			self.assertNotIn("Interpretation", methods[0]["details_missing"])


class TestKindFieldsTheBoardDraws(FrappeTestCase):
	"""§10.7 (tracker CFG14-5D) — fields the board's kind sections draw that the
	payload did not carry. Pure validation: nothing is written."""

	def test_reservation_rules_keep_applicability_conditions_and_source_references(self):
		out = register._validate_payload(
			"Reservation rules",
			{
				"obligation_code": "AGPO-ANNUAL",
				"measure_stage": "PlanningAllocation",
				"target_percent": 30,
				"applicability_conditions": "  Registered AGPO certificate  ",
				"source_references": "PPADA s.157(5)",
			},
		)
		self.assertEqual(out["applicability_conditions"], "Registered AGPO certificate")
		self.assertEqual(out["source_references"], "PPADA s.157(5)")

	def test_market_price_index_keeps_its_publication_facts(self):
		out = register._validate_payload(
			"Market price index",
			{"publication_date": "2026-07-01", "publication_reference": "PPRA MPI 2026/27", "rows": []},
		)
		self.assertEqual(out["publication_date"], "2026-07-01")
		self.assertEqual(out["publication_reference"], "PPRA MPI 2026/27")
		# Nothing published is still "not published", whatever the header says.
		self.assertFalse(out["published"])


class TestPlaywrightRulePurge(FrappeTestCase):
	"""Browser specs add real rules (tracker CFG14-5D); their cleanup removes only
	rules whose identifier starts with PW-, with their versions."""

	def setUp(self):
		# Always remove test data: a failed run must not strand its rule.
		register.purge_playwright_rules()
		frappe.db.commit()
		self.addCleanup(lambda: (register.purge_playwright_rules(), frappe.db.commit()))

	def test_removes_pw_rules_and_their_versions_and_nothing_else(self):
		frappe.set_user("Administrator")
		out = register.create_regulatory_reference(reference_key="PW-PURGE-CHECK", reference_kind="Publication obligations", display_name="PW purge check")
		register.save_regulatory_reference_version(
			reference_set=out["reference_set"],
			payload={"obligation_id": "PW-OB", "due_rule": "Immediate"},
			effective_from="2099-07-01",
		)
		frappe.db.commit()
		before = frappe.db.count(register.SET_DOCTYPE)
		removed = register.purge_playwright_rules()
		frappe.db.commit()
		self.assertGreaterEqual(removed, 2)
		self.assertFalse(frappe.db.exists(register.SET_DOCTYPE, out["reference_set"]))
		self.assertFalse(frappe.db.exists(register.DOCTYPE, {"reference_set": out["reference_set"]}))
		self.assertEqual(frappe.db.count(register.SET_DOCTYPE), before - 1)
