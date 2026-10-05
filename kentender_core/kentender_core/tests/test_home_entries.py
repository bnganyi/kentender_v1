"""HOME-CHG-001 v0.6 §4 — the transient Home entry an owner supplies.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_entries
"""

from __future__ import annotations

from datetime import date, datetime

from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he


def work(**over):
	base = dict(
		region="my_work", owner="tenders", root="TND-1", action_id="authorise-publication",
		title="Supply of UPS units", action="Authorise publication",
		destination=["tenders", "TND-1"], entered_at=datetime(2027, 6, 16, 15, 30), reference="TND-MOH-2027-047",
	)
	base.update(over)
	return he.make(**base)


class TestMake(IntegrationTestCase):
	def test_a_work_entry_carries_the_owner_facts_and_a_normalised_destination(self):
		entry = work()
		self.assertEqual(entry["identity"], ("tenders", "TND-1", "authorise-publication"))
		self.assertEqual(entry["title"], "Supply of UPS units")
		self.assertEqual(entry["reference"], "TND-MOH-2027-047")
		self.assertEqual(entry["destination"], {"route": ["tenders", "TND-1"], "route_options": {}})
		self.assertEqual(entry["entered_verb"], "Received")

	def test_destination_may_carry_route_options(self):
		entry = work(destination={"route": ["tenders", "TND-1"], "route_options": {"task_id": "T-9"}})
		self.assertEqual(entry["destination"]["route_options"], {"task_id": "T-9"})

	def test_an_entry_may_carry_one_named_link_with_its_own_destination(self):
		entry = work(link={"label": "View report", "destination": ["tenders", "TND-MOH-2027-033", "evaluation", "report"]})
		self.assertEqual(entry["link"], {"label": "View report", "destination": {"route": ["tenders", "TND-MOH-2027-033", "evaluation", "report"], "route_options": {}}})
		self.assertIsNone(work()["link"])

	def test_a_link_needs_a_label_and_a_desk_route(self):
		for bad in ({"label": "", "destination": ["tenders", "T"]}, {"label": "View report"}, {"label": "View report", "destination": ["https://x.test/a"]}):
			with self.assertRaises(ValueError):
				work(link=bad)

	def test_a_fact_names_what_happened_and_when(self):
		entry = work(fact="Evaluation report delivered", fact_at=datetime(2027, 6, 16, 14, 7))
		self.assertEqual((entry["fact"], entry["fact_at"]), ("Evaluation report delivered", datetime(2027, 6, 16, 14, 7)))
		with self.assertRaises(ValueError):
			work(fact="Evaluation report delivered")

	def test_support_issues_and_supplier_accounts_are_modules_with_their_own_labels(self):
		self.assertEqual(he.module_label("support"), "Support issues")
		self.assertEqual(he.module_label("suppliers"), "Supplier accounts")

	def test_the_owner_must_be_a_known_module(self):
		with self.assertRaises(ValueError):
			work(owner="spreadsheet")

	def test_module_label_comes_from_core_not_from_the_owner(self):
		self.assertEqual(he.MODULES["bid_opening"], "Bid opening")
		self.assertEqual(he.MODULES["budget"], "Budget & Funding")
		self.assertEqual(he.module_label("planning"), "Planning")

	def test_title_action_and_destination_are_required(self):
		for field in ("title", "action"):
			with self.assertRaises(ValueError, msg=field):
				work(**{field: ""})
		with self.assertRaises(ValueError):
			work(destination=[])

	def test_a_destination_must_be_a_desk_route_not_a_url(self):
		for bad in (["https://example.com/x"], ["/app/tenders"], ["javascript:alert(1)"], [""], "tenders"):
			with self.assertRaises(ValueError, msg=str(bad)):
				work(destination=bad)

	def test_blocked_work_must_say_why(self):
		with self.assertRaises(ValueError):
			work(blocked=True)
		entry = work(blocked=True, reason="Issue an addendum before sending this answer.")
		self.assertTrue(entry["blocked"])

	def test_my_work_needs_the_time_it_entered_the_actors_queue(self):
		with self.assertRaises(ValueError):
			work(entered_at=None)

	def test_waiting_needs_a_holder_and_a_since(self):
		kwargs = dict(region="waiting", action="Waiting for Amina Hassan to decide publication", entered_at=None)
		with self.assertRaises(ValueError):
			work(**kwargs, since=datetime(2027, 6, 16, 15, 30))  # no holder
		with self.assertRaises(ValueError):
			work(**kwargs, holder="Amina Hassan")  # no since
		entry = work(**kwargs, holder={"role": "Accounting Officer", "people": ["Amina Hassan"], "display": "Accounting Officer"}, since=datetime(2027, 6, 16, 15, 30))
		self.assertEqual(entry["holder"], "Accounting Officer")

	def test_oversight_needs_a_since_and_defaults_to_not_outstanding(self):
		with self.assertRaises(ValueError):
			work(region="oversight", entered_at=None)
		entry = work(region="oversight", entered_at=None, since=datetime(2027, 6, 3, 10, 0))
		self.assertFalse(entry["outstanding"])
		self.assertTrue(work(region="oversight", entered_at=None, since=datetime(2027, 6, 3, 10, 0), outstanding=True)["outstanding"])

	def test_coming_up_accepts_an_instant_or_a_date_only_deadline(self):
		entry = work(region="coming_up", entered_at=None, scheduled_at=date(2027, 7, 1))
		self.assertEqual(entry["scheduled_at"], date(2027, 7, 1))
		with self.assertRaises(ValueError):
			work(region="coming_up", entered_at=None)

	def test_a_completed_action_needs_its_instant_and_its_sentence(self):
		with self.assertRaises(ValueError):
			work(region="completed", entered_at=None, completed_at=datetime(2027, 6, 16, 15, 30))
		entry = work(region="completed", entered_at=None, completed_at=datetime(2027, 6, 16, 15, 30), sentence="You approved this Tender package on 16 June 2027, 15:30 EAT.")
		self.assertTrue(entry["sentence"].startswith("You approved"))

	def test_unknown_region_is_refused(self):
		with self.assertRaises(ValueError):
			work(region="inbox")

	def test_string_instants_from_the_database_are_read(self):
		entry = work(entered_at="2027-06-16 15:30:00", due="2027-06-18")
		self.assertEqual(entry["entered_at"], datetime(2027, 6, 16, 15, 30))
		self.assertEqual(entry["due"], date(2027, 6, 18))
		self.assertNotIsInstance(entry["due"], datetime)

	def test_validate_accepts_what_make_returns_and_refuses_a_hand_built_dict(self):
		he.validate(work())
		with self.assertRaises(ValueError):
			he.validate({"region": "my_work", "owner": "tenders"})
