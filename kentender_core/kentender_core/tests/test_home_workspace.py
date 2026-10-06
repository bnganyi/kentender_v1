"""HOME-CHG-001 v0.6 §§4-8 — the `GetHomeWorkspace` composition, on fake owner providers.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_workspace
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_HOME"
NOW = datetime(2027, 6, 18, 10, 0)
PAGE = "technical-search"  # a Page that exists on every site; Home checks the root segment only


def entry(region=he.MY_WORK, n=1, **over):
	base = dict(
		region=region, owner="tenders", root=f"TND-{n}", action_id="act", title=f"Supply {n}",
		action="Do the thing", destination=[PAGE, f"TND-{n}"],
	)
	if region == he.MY_WORK:
		base["entered_at"] = datetime(2027, 6, 16, 11, 0)
	elif region == he.WAITING:
		base.update(since=datetime(2027, 6, 16, 15, 30), holder="Accounting Officer")
	elif region == he.OVERSIGHT:
		base.update(since=datetime(2027, 6, 3, 10, 0))
	elif region == he.COMING_UP:
		base.update(scheduled_at=datetime(2027, 6, 25, 11, 0))
	elif region == he.COMPLETED:
		base.update(completed_at=datetime(2027, 6, 16, 15, 30), sentence="You did it.")
	base.update(over)
	return he.make(**base)


class Provider:
	"""A fake owner. `returns[region]` is a list, None (not applicable) or an
	Exception to raise. Calls are recorded."""

	def __init__(self, **returns):
		self.returns = returns
		self.calls: list[tuple[str, str]] = []

	def __call__(self, *, user, region):
		self.calls.append((user, region))
		value = self.returns.get(region)
		if isinstance(value, Exception):
			raise value
		return value


WORLD: dict[str, str] = {}


def setUpModule():
	"""One fixture world for the whole module (owner rule: never rebuild per
	test or per class). `tearDownModule` purges it."""
	fx.ensure_site_configured()
	WORLD["unit_hr"] = fx.unit("KT Test Home HRMD", namespace=NS)
	for key, name in (("charles", "Charles Test"), ("peter", "Peter Test"), ("daniel", "Daniel Test"), ("nobody", "Nobody Test")):
		WORLD[key] = fx.user(f"home.{key}", name)
	administration.grant(user=WORLD["charles"], business_role="Head of Procurement Function", fixture_namespace=NS)
	administration.grant(user=WORLD["peter"], business_role="Head of User Department", organisation_unit=WORLD["unit_hr"], fixture_namespace=NS)
	administration.grant(user=WORLD["daniel"], business_role="Technical Operator", fixture_namespace=NS)
	frappe.db.commit()


def tearDownModule():
	purge()


class HomeTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.unit_hr = WORLD["unit_hr"]
		cls.charles, cls.peter, cls.daniel, cls.nobody = (WORLD[k] for k in ("charles", "peter", "daniel", "nobody"))

	def read(self, *providers, user=None, **kw):
		return hw.get_workspace(user or self.charles, providers=list(providers), at=NOW, **kw)

	def region(self, result, name):
		return result["regions"][name]


class TestGate(HomeTestCase):
	def test_a_non_internal_user_gets_the_denied_state_and_nothing_else(self):
		website = frappe.get_doc({"doctype": "User", "email": "kt.test.home.supplier@example.test", "first_name": "Supplier", "send_welcome_email": 0, "user_type": "Website User", "enabled": 1}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("User", website.name, force=1, ignore_permissions=True))
		provider = Provider(my_work=[entry()])
		result = hw.get_workspace(website.name, providers=[provider], at=NOW)
		self.assertEqual(result, {"state": "denied"})
		self.assertEqual(provider.calls, [])

	def test_administrator_is_a_technical_reader_with_no_business_entries(self):
		provider = Provider(my_work=[entry()])
		result = hw.get_workspace("Administrator", providers=[provider], at=NOW)
		self.assertEqual(result["state"], "ready")
		self.assertTrue(result["viewer"]["technical"])
		self.assertTrue(result["empty"])
		self.assertEqual(provider.calls, [])
		for name in he.REGIONS:
			self.assertEqual(self.region(result, name)["entries"], [])
			self.assertFalse(self.region(result, name)["applicable"])

	def test_a_technical_operator_is_a_technical_reader_too(self):
		provider = Provider(my_work=[entry()])
		result = self.read(provider, user=self.daniel)
		self.assertTrue(result["viewer"]["technical"])
		self.assertEqual(provider.calls, [])
		self.assertEqual(result["viewer"]["responsibilities"]["line"], "Technical Operator, site-wide")

	def test_a_business_user_is_not_a_technical_reader(self):
		self.assertFalse(self.read(Provider())["viewer"]["technical"])


class TestHeader(HomeTestCase):
	def test_greeting_first_name_and_update_instant(self):
		result = self.read(Provider())
		self.assertEqual(result["viewer"]["greeting"], "Good morning")
		self.assertEqual(result["viewer"]["first_name"], "Charles")
		self.assertTrue(result["updated"].startswith("18 June 2027, 10:00"), result["updated"])

	def test_responsibilities_are_every_active_one_with_scope(self):
		self.assertEqual(self.read(Provider())["viewer"]["responsibilities"]["line"], "Head of Procurement Function, site-wide")
		peter = self.read(Provider(), user=self.peter)["viewer"]["responsibilities"]
		self.assertEqual(peter["line"], "Head of User Department, KT Test Home HRMD")
		self.assertEqual(peter["items"], [{"role": "Head of User Department", "scope": "KT Test Home HRMD", "text": "Head of User Department, KT Test Home HRMD"}])

	def test_an_expired_responsibility_is_not_listed(self):
		later = datetime(2030, 1, 1, 10, 0)
		user = fx.user("home.expired", "Expired Test")
		administration.grant(user=user, business_role="Procurement Officer", fixture_namespace=NS, effective_from="2020-01-01 00:00:00", effective_to="2020-12-31 23:59:59")
		result = hw.get_workspace(user, providers=[Provider()], at=later)
		self.assertEqual(result["viewer"]["responsibilities"]["items"], [])

	def test_a_user_with_no_responsibility_still_reads_and_sees_none(self):
		result = self.read(Provider(my_work=[]), user=self.nobody)
		self.assertEqual(result["viewer"]["responsibilities"]["line"], "")
		self.assertEqual(result["state"], "ready")


class TestGreetingName(IntegrationTestCase):
	"""HOME-DES-24: "Good morning, Peter" for Dr Peter Kimani. The seeded user stores first name "Dr" and last name
	"Peter Kimani", so the greeting reads the full name and skips leading titles."""

	def test_titles_are_skipped(self):
		from kentender_core.services import home_viewer as hv

		self.assertEqual(hv.greeting_name("Dr Peter Kimani", "Dr"), "Peter")
		self.assertEqual(hv.greeting_name("Prof. Jane Wanjiku", "Prof."), "Jane")
		self.assertEqual(hv.greeting_name("Hon Amina Hassan", ""), "Amina")
		self.assertEqual(hv.greeting_name("Dr. Eng. Alfred Ochieng", ""), "Alfred")

	def test_an_ordinary_name_is_its_first_word(self):
		from kentender_core.services import home_viewer as hv

		self.assertEqual(hv.greeting_name("Charles Mutiso", "Charles"), "Charles")
		self.assertEqual(hv.greeting_name("Brian", "Brian"), "Brian")

	def test_a_name_that_is_only_a_title_stays_as_it_is(self):
		from kentender_core.services import home_viewer as hv

		self.assertEqual(hv.greeting_name("Dr", "Dr"), "Dr")

	def test_with_no_name_at_all_it_falls_back_to_the_account(self):
		from kentender_core.services import home_viewer as hv

		self.assertEqual(hv.greeting_name("", "", fallback="peter.kimani@moh.example.test"), "peter.kimani@moh.example.test")


class TestComposition(HomeTestCase):
	def test_counts_and_applicability_per_region(self):
		provider = Provider(my_work=[entry(n=1), entry(n=2)], waiting=[entry(he.WAITING, n=3)], oversight=None)
		result = self.read(provider)
		self.assertEqual(result["state"], "ready")
		self.assertEqual(self.region(result, "my_work")["count"], 2)
		self.assertEqual(self.region(result, "waiting")["count"], 1)
		self.assertFalse(self.region(result, "oversight")["applicable"])
		self.assertIsNone(self.region(result, "oversight")["count"])
		self.assertEqual(self.region(result, "oversight")["coverage"], "not_applicable")
		self.assertTrue(result["summary_visible"])
		self.assertFalse(result["empty"])

	def test_an_applicable_region_with_no_entries_still_counts_zero(self):
		result = self.read(Provider(my_work=[], waiting=[], oversight=[entry(he.OVERSIGHT, n=1)]))
		self.assertEqual(self.region(result, "my_work")["count"], 0)
		self.assertEqual(self.region(result, "waiting")["count"], 0)
		self.assertTrue(result["summary_visible"])

	def test_a_successful_all_empty_read_shows_no_counts(self):
		result = self.read(Provider(my_work=[], waiting=[], oversight=[], coming_up=[], completed=[]))
		self.assertEqual(result["state"], "ready")
		self.assertTrue(result["empty"])
		self.assertFalse(result["summary_visible"])

	def test_no_configured_provider_is_a_clean_empty_read_not_a_failure(self):
		result = self.read()
		self.assertEqual(result["state"], "ready")
		self.assertTrue(result["empty"])
		self.assertEqual(result["providers"], {"configured": 0, "failed": 0})

	def test_module_label_is_core_made(self):
		result = self.read(Provider(my_work=[entry(owner="bid_opening")]))
		self.assertEqual(self.region(result, "my_work")["entries"][0]["module"], "Bid opening")

	def test_the_first_my_work_row_alone_is_primary(self):
		rows = self.region(self.read(Provider(my_work=[entry(n=1), entry(n=2), entry(n=3)])), "my_work")["entries"]
		self.assertEqual([row["primary"] for row in rows], [True, False, False])

	def test_blocked_work_carries_its_reason_and_tag(self):
		blocked = entry(n=1, blocked=True, reason="Issue an addendum before sending this answer.")
		row = self.region(self.read(Provider(my_work=[blocked])), "my_work")["entries"][0]
		self.assertTrue(row["blocked"])
		self.assertEqual(row["reason"], "Issue an addendum before sending this answer.")

	def test_two_providers_merge_into_one_region(self):
		a, b = Provider(my_work=[entry(n=1)]), Provider(my_work=[entry(n=2, owner="award")])
		result = self.read(a, b)
		self.assertEqual(self.region(result, "my_work")["count"], 2)


class TestLabels(HomeTestCase):
	def test_each_region_shows_its_relative_and_exact_timing(self):
		result = self.read(Provider(
			my_work=[entry(n=1, entered_at=datetime(2027, 6, 16, 11, 0), due=date(2027, 6, 19))],
			coming_up=[entry(he.COMING_UP, n=2, scheduled_at=date(2027, 7, 1))],
			waiting=[entry(he.WAITING, n=3, since=datetime(2027, 6, 16, 15, 30), due=date(2027, 6, 18))],
			oversight=[entry(he.OVERSIGHT, n=4, since=datetime(2027, 6, 3, 10, 0), outstanding=True)],
			completed=[entry(he.COMPLETED, n=5)],
		))
		work = self.region(result, "my_work")["entries"][0]
		self.assertEqual(work["timing"], "Received 2 days ago (16 June, 11:00)")
		self.assertEqual(work["due"], "Due tomorrow (19 June)")
		coming = self.region(result, "coming_up")["entries"][0]
		self.assertEqual((coming["badge"], coming["exact"]), ("In 13 days", "1 July"))
		waiting = self.region(result, "waiting")["entries"][0]
		self.assertEqual(waiting["timing"], "Waiting 2 days (since 16 June, 15:30)")
		self.assertEqual(waiting["due"], "Due today (18 June)")
		self.assertEqual(waiting["holder"], "Accounting Officer")
		self.assertEqual(self.region(result, "oversight")["entries"][0]["timing"], "Outstanding 15 days (since 3 June, 10:00)")
		self.assertEqual(self.region(result, "completed")["entries"][0]["sentence"], "You did it.")

	def test_submitted_verb_is_the_owners(self):
		row = self.region(self.read(Provider(my_work=[entry(entered_verb="Submitted", entered_at=datetime(2027, 6, 17, 14, 0))])), "my_work")["entries"][0]
		self.assertEqual(row["timing"], "Submitted yesterday (17 June, 14:00)")

	def test_overdue_only_from_a_passed_owner_deadline(self):
		rows = self.region(self.read(Provider(my_work=[
			entry(n=1, entered_at=datetime(2027, 1, 4, 9, 0)),
			entry(n=2, due=date(2027, 6, 16)),
		])), "my_work")["entries"]
		by_title = {row["title"]: row for row in rows}
		self.assertEqual(by_title["Supply 1"]["due"], "")
		self.assertTrue(by_title["Supply 1"]["timing"].startswith("Received 165 days ago"))
		self.assertEqual(by_title["Supply 2"]["due"], "Overdue since 16 June")


class TestOrdering(HomeTestCase):
	def titles(self, result, region):
		return [row["title"] for row in self.region(result, region)["entries"]]

	def test_my_work_overdue_then_dated_then_oldest_undated(self):
		rows = [
			entry(n=1, entered_at=datetime(2027, 6, 17, 11, 0)),                          # undated, newer
			entry(n=2, entered_at=datetime(2027, 5, 14, 10, 0)),                          # undated, oldest
			entry(n=3, entered_at=datetime(2027, 6, 17, 9, 0), due=date(2027, 6, 25)),    # dated later
			entry(n=4, entered_at=datetime(2027, 6, 17, 9, 0), due=date(2027, 6, 19)),    # dated sooner
			entry(n=5, entered_at=datetime(2027, 6, 17, 9, 0), due=date(2027, 6, 15)),    # overdue
		]
		self.assertEqual(self.titles(self.read(Provider(my_work=rows)), "my_work"), ["Supply 5", "Supply 4", "Supply 3", "Supply 2", "Supply 1"])

	def test_a_tie_is_broken_by_a_stable_identity(self):
		a = entry(n=2, entered_at=datetime(2027, 6, 16, 11, 0))
		b = entry(n=1, entered_at=datetime(2027, 6, 16, 11, 0))
		first = self.titles(self.read(Provider(my_work=[a, b])), "my_work")
		second = self.titles(self.read(Provider(my_work=[b, a])), "my_work")
		self.assertEqual(first, second)

	def test_waiting_is_oldest_first(self):
		rows = [entry(he.WAITING, n=1, since=datetime(2027, 6, 17, 9, 0)), entry(he.WAITING, n=2, since=datetime(2027, 6, 1, 9, 0))]
		self.assertEqual(self.titles(self.read(Provider(waiting=rows)), "waiting"), ["Supply 2", "Supply 1"])

	def test_oversight_outstanding_first_by_oldest_then_updates_newest_first(self):
		rows = [
			entry(he.OVERSIGHT, n=1, since=datetime(2027, 6, 10, 9, 0)),
			entry(he.OVERSIGHT, n=2, since=datetime(2027, 6, 12, 9, 0)),
			entry(he.OVERSIGHT, n=3, since=datetime(2027, 6, 16, 9, 0), outstanding=True),
			entry(he.OVERSIGHT, n=4, since=datetime(2027, 6, 3, 9, 0), outstanding=True),
		]
		self.assertEqual(self.titles(self.read(Provider(oversight=rows)), "oversight"), ["Supply 4", "Supply 3", "Supply 2", "Supply 1"])

	def test_coming_up_earliest_first_and_completed_newest_first(self):
		coming = [entry(he.COMING_UP, n=1, scheduled_at=date(2027, 7, 1)), entry(he.COMING_UP, n=2, scheduled_at=datetime(2027, 6, 25, 11, 0))]
		done = [entry(he.COMPLETED, n=1, completed_at=datetime(2027, 6, 10, 9, 0)), entry(he.COMPLETED, n=2, completed_at=datetime(2027, 6, 17, 9, 0))]
		result = self.read(Provider(coming_up=coming, completed=done))
		self.assertEqual(self.titles(result, "coming_up"), ["Supply 2", "Supply 1"])
		self.assertEqual(self.titles(result, "completed"), ["Supply 2", "Supply 1"])


class TestOversightCount(HomeTestCase):
	def test_the_summary_counts_records_with_outstanding_matters_not_every_update(self):
		rows = [
			entry(he.OVERSIGHT, n=1, since=datetime(2027, 6, 3, 9, 0), outstanding=True),
			entry(he.OVERSIGHT, n=2, since=datetime(2027, 6, 4, 9, 0), outstanding=True),
			entry(he.OVERSIGHT, n=3, since=datetime(2027, 6, 16, 9, 0)),
		]
		region = self.region(self.read(Provider(oversight=rows)), "oversight")
		self.assertEqual(region["count"], 2)
		self.assertEqual(region["total"], 3)
		self.assertEqual(len(region["entries"]), 3)

	def test_other_regions_count_every_entry_and_total_matches(self):
		region = self.region(self.read(Provider(my_work=[entry(n=1), entry(n=2)])), "my_work")
		self.assertEqual((region["count"], region["total"]), (2, 2))

	def test_total_is_unknown_when_coverage_is_not_complete(self):
		region = self.region(self.read(Provider(my_work=[entry(n=1)]), Provider(my_work=RuntimeError("boom"))), "my_work")
		self.assertEqual((region["count"], region["total"]), (None, None))


class TestSummaryLabels(HomeTestCase):
	"""HOME §5.1 item 2: the labels are server-made; one reads singular for one (HOME-DES-24: "1 action for you")."""

	def labels(self, **providers):
		result = self.read(Provider(**providers))
		return {name: self.region(result, name)["label"] for name in ("my_work", "waiting", "oversight")}

	def test_plural_labels(self):
		got = self.labels(my_work=[entry(n=1), entry(n=2)], waiting=[entry(he.WAITING, n=3), entry(he.WAITING, n=4)], oversight=[entry(he.OVERSIGHT, n=5, outstanding=True), entry(he.OVERSIGHT, n=6, outstanding=True)])
		self.assertEqual(got, {"my_work": "actions for you", "waiting": "items you're waiting on", "oversight": "records with outstanding matters"})

	def test_singular_labels_for_one(self):
		got = self.labels(my_work=[entry(n=1)], waiting=[entry(he.WAITING, n=3)], oversight=[entry(he.OVERSIGHT, n=5, outstanding=True)])
		self.assertEqual(got, {"my_work": "action for you", "waiting": "item you're waiting on", "oversight": "record with outstanding matters"})

	def test_zero_reads_plural(self):
		self.assertEqual(self.labels(my_work=[], waiting=[], oversight=[entry(he.OVERSIGHT, n=5, outstanding=True)])["my_work"], "actions for you")

	def test_a_region_with_no_summary_column_has_no_label(self):
		result = self.read(Provider(my_work=[entry(n=1)], coming_up=[entry(he.COMING_UP, n=2)], completed=[entry(he.COMPLETED, n=3)]))
		self.assertEqual(self.region(result, "coming_up")["label"], "")
		self.assertEqual(self.region(result, "completed")["label"], "")


class TestShowMoreCount(HomeTestCase):
	"""HOME §5.1 item 5: "Show 1 more" for one left, "Show 5 more" when more than five remain."""

	def more(self, total):
		rows = [entry(n=i, entered_at=datetime(2027, 6, 1, 9, 0) + (datetime(2027, 6, 2) - datetime(2027, 6, 1)) * i) for i in range(1, total + 1)]
		return self.region(self.read(Provider(my_work=rows)), "my_work")["next_count"]

	def test_one_left(self):
		self.assertEqual(self.more(6), 1)

	def test_a_few_left(self):
		self.assertEqual(self.more(8), 3)

	def test_more_than_five_left_offers_five(self):
		self.assertEqual(self.more(20), 5)

	def test_nothing_left(self):
		self.assertEqual(self.more(5), 0)


class TestPagedFlag(HomeTestCase):
	"""The footer ("Showing 5 of 6" / "Showing 6 of 6") shows once a region has more than one page: HOME-DES-26 and 26B."""

	def rows(self, n):
		return [entry(n=i, entered_at=datetime(2027, 6, 1, 9, 0) + (datetime(2027, 6, 2) - datetime(2027, 6, 1)) * i) for i in range(1, n + 1)]

	def test_a_single_page_is_not_paged(self):
		self.assertFalse(self.region(self.read(Provider(my_work=self.rows(5))), "my_work")["paged"])

	def test_the_first_of_two_pages_is_paged(self):
		self.assertTrue(self.region(self.read(Provider(my_work=self.rows(6))), "my_work")["paged"])

	def test_the_last_page_is_still_paged_so_the_footer_can_read_six_of_six(self):
		provider = Provider(my_work=self.rows(6))
		first = self.region(self.read(provider), "my_work")
		last = self.region(self.read(provider, regions=["my_work"], cursors={"my_work": first["next_cursor"]}), "my_work")
		self.assertTrue(last["paged"])
		self.assertEqual((last["shown"], last["total"], last["next_count"]), (6, 6, 0))

	def test_an_empty_region_is_not_paged(self):
		self.assertFalse(self.region(self.read(Provider(my_work=[])), "my_work")["paged"])


class TestDedupeAndWindow(HomeTestCase):
	def test_the_same_action_from_two_providers_is_one_entry(self):
		a = Provider(my_work=[entry(n=1)])
		b = Provider(my_work=[entry(n=1)])
		self.assertEqual(self.region(self.read(a, b), "my_work")["count"], 1)

	def test_two_distinct_actions_on_one_record_stay_two(self):
		rows = [entry(n=1, action_id="opinion"), entry(n=1, action_id="notice")]
		self.assertEqual(self.region(self.read(Provider(my_work=rows)), "my_work")["count"], 2)

	def test_the_same_person_with_two_scopes_is_not_a_cross_product(self):
		# an owner that reads two scopes returns the same action twice; Home shows it once
		rows = [entry(n=1), entry(n=1), entry(n=2), entry(n=2)]
		self.assertEqual(self.region(self.read(Provider(my_work=rows)), "my_work")["count"], 2)

	def test_coming_up_does_not_repeat_a_my_work_entry(self):
		work = entry(n=1, action_id="start")
		upcoming = entry(he.COMING_UP, n=1, action_id="start")
		other = entry(he.COMING_UP, n=2)
		result = self.read(Provider(my_work=[work], coming_up=[upcoming, other]))
		self.assertEqual([r["title"] for r in self.region(result, "coming_up")["entries"]], ["Supply 2"])

	def test_oversight_does_not_repeat_a_my_work_entry(self):
		work = entry(n=1, action_id="a")
		same = entry(he.OVERSIGHT, n=1, action_id="a")
		different = entry(he.OVERSIGHT, n=1, action_id="b")
		result = self.read(Provider(my_work=[work], oversight=[same, different]))
		self.assertEqual(self.region(result, "oversight")["total"], 1)

	def test_coming_up_window_is_fourteen_calendar_days(self):
		inside = entry(he.COMING_UP, n=1, scheduled_at=date(2027, 7, 2))
		edge_out = entry(he.COMING_UP, n=2, scheduled_at=date(2027, 7, 3))
		past = entry(he.COMING_UP, n=3, scheduled_at=date(2027, 6, 17))
		today = entry(he.COMING_UP, n=4, scheduled_at=datetime(2027, 6, 18, 8, 0))
		result = self.read(Provider(coming_up=[inside, edge_out, past, today]))
		self.assertEqual(sorted(r["title"] for r in self.region(result, "coming_up")["entries"]), ["Supply 1", "Supply 4"])


class TestCompletedWindow(HomeTestCase):
	def test_completed_actions_older_than_30_days_are_left_out_without_making_the_region_partial(self):
		recent = entry(he.COMPLETED, n=1, completed_at=datetime(2027, 6, 10, 9, 0))
		old = entry(he.COMPLETED, n=2, completed_at=datetime(2027, 5, 1, 9, 0))
		region = self.region(self.read(Provider(completed=[recent, old])), "completed")
		self.assertEqual([r["title"] for r in region["entries"]], ["Supply 1"])
		self.assertEqual(region["coverage"], "complete")


class TestPaging(HomeTestCase):
	def rows(self, n):
		return [entry(n=i, entered_at=datetime(2027, 6, 1, 9, 0) + (datetime(2027, 6, 2) - datetime(2027, 6, 1)) * i) for i in range(1, n + 1)]

	def test_first_page_is_five_with_a_cursor_and_the_complete_count(self):
		region = self.region(self.read(Provider(my_work=self.rows(6))), "my_work")
		self.assertEqual([r["title"] for r in region["entries"]], [f"Supply {i}" for i in range(1, 6)])
		self.assertEqual((region["count"], region["shown"], region["remaining"]), (6, 5, 1))
		self.assertTrue(region["next_cursor"])

	def test_show_more_appends_the_rest_and_the_count_does_not_change(self):
		provider = Provider(my_work=self.rows(6))
		first = self.region(self.read(provider), "my_work")
		second = self.region(self.read(provider, regions=["my_work"], cursors={"my_work": first["next_cursor"]}), "my_work")
		self.assertEqual([r["title"] for r in second["entries"]], ["Supply 6"])
		self.assertEqual((second["count"], second["shown"], second["remaining"]), (6, 6, 0))
		self.assertIsNone(second["next_cursor"])
		self.assertFalse(any(r["primary"] for r in second["entries"]))

	def test_every_authorised_entry_is_reachable_and_the_count_is_independent_of_page_size(self):
		for size in (1, 2, 5, 7):
			with patch.object(hw, "PAGE_SIZE", size):
				provider = Provider(my_work=self.rows(6))
				seen, cursor, counts = [], None, set()
				for _ in range(10):
					region = self.region(self.read(provider, regions=["my_work"], cursors={"my_work": cursor} if cursor else None), "my_work")
					seen += [r["title"] for r in region["entries"]]
					counts.add(region["count"])
					cursor = region["next_cursor"]
					if not cursor:
						break
				self.assertEqual(seen, [f"Supply {i}" for i in range(1, 7)], size)
				self.assertEqual(counts, {6}, size)

	def test_a_stale_cursor_after_the_list_changed_still_continues_after_its_position(self):
		provider = Provider(my_work=self.rows(7))
		first = self.region(self.read(provider), "my_work")
		provider.returns["my_work"] = [e for e in self.rows(7) if e["title"] != "Supply 3"]
		second = self.region(self.read(provider, regions=["my_work"], cursors={"my_work": first["next_cursor"]}), "my_work")
		self.assertEqual([r["title"] for r in second["entries"]], ["Supply 6", "Supply 7"])

	def test_a_garbled_cursor_is_refused_not_trusted(self):
		with self.assertRaises(frappe.ValidationError):
			self.read(Provider(my_work=self.rows(6)), regions=["my_work"], cursors={"my_work": "not-a-cursor"})


class TestCoverage(HomeTestCase):
	def test_one_region_failing_leaves_the_others_and_drops_its_count(self):
		provider = Provider(my_work=[entry(n=1)], waiting=RuntimeError("boom"), oversight=[entry(he.OVERSIGHT, n=2)])
		result = self.read(provider)
		self.assertEqual(result["state"], "ready")
		self.assertEqual(self.region(result, "waiting")["coverage"], "unavailable")
		self.assertIsNone(self.region(result, "waiting")["count"])
		self.assertEqual(self.region(result, "waiting")["entries"], [])
		self.assertEqual(self.region(result, "my_work")["coverage"], "complete")
		self.assertEqual(self.region(result, "my_work")["count"], 1)
		self.assertFalse(result["empty"])

	def test_a_partial_provider_set_keeps_rows_and_has_no_total(self):
		good = Provider(my_work=[entry(n=1)])
		bad = Provider(my_work=RuntimeError("boom"))
		region = self.region(self.read(good, bad), "my_work")
		self.assertEqual(region["coverage"], "partial")
		self.assertEqual(len(region["entries"]), 1)
		self.assertIsNone(region["count"])

	def test_failure_where_nothing_else_answered_is_unavailable_not_empty(self):
		a, b = Provider(waiting=RuntimeError("boom")), Provider(waiting=None)
		self.assertEqual(self.region(self.read(a, b), "waiting")["coverage"], "unavailable")

	def test_a_failure_is_never_a_successful_empty_read(self):
		result = self.read(Provider(my_work=[], waiting=RuntimeError("boom")))
		self.assertFalse(result["empty"])

	def test_every_provider_failing_everywhere_is_total_failure(self):
		boom = RuntimeError("boom")
		result = self.read(Provider(my_work=boom, waiting=boom, oversight=boom, coming_up=boom, completed=boom))
		self.assertEqual(result["state"], "failed")

	def test_a_provider_that_cannot_be_imported_is_a_failure_not_an_absent_module(self):
		with patch.object(hw, "_hook_paths", return_value=["kentender_core.services.no_such_module.rows"]):
			result = hw.get_workspace(self.charles, at=NOW)
		self.assertEqual(result["state"], "failed")
		self.assertEqual(result["providers"]["failed"], 1)

	def test_hook_paths_are_resolved_and_called(self):
		calls = []

		def probe(*, user, region):
			calls.append((user, region))
			return [entry(n=1)] if region == "my_work" else None

		with patch.object(hw, "_hook_paths", return_value=["x.y"]), patch.object(hw, "_load", return_value=probe):
			result = hw.get_workspace(self.charles, at=NOW)
		self.assertEqual(self.region(result, "my_work")["count"], 1)
		self.assertIn((self.charles, "my_work"), calls)

	def test_an_entry_the_owner_got_wrong_is_dropped_and_the_region_is_partial(self):
		broken = dict(entry(n=2))
		broken["title"] = ""
		region = self.region(self.read(Provider(my_work=[entry(n=1), broken])), "my_work")
		self.assertEqual(region["coverage"], "partial")
		self.assertEqual(len(region["entries"]), 1)
		self.assertIsNone(region["count"])

	def test_a_destination_that_is_not_a_real_page_is_dropped_and_the_region_is_partial(self):
		bad = entry(n=2, destination=["no-such-page-xyz", "TND-2"])
		region = self.region(self.read(Provider(my_work=[entry(n=1), bad])), "my_work")
		self.assertEqual(region["coverage"], "partial")
		self.assertEqual([r["title"] for r in region["entries"]], ["Supply 1"])

	def test_a_destination_the_viewer_may_not_open_is_dropped(self):
		with patch.object(hw, "_page_permitted", return_value=False):
			region = self.region(self.read(Provider(my_work=[entry(n=1)])), "my_work")
		self.assertEqual(region["entries"], [])
		self.assertEqual(region["coverage"], "partial")


class TestEntryLink(HomeTestCase):
	def test_a_link_reaches_the_page_row_with_its_label_and_destination(self):
		linked = entry(he.OVERSIGHT, n=1, fact="Evaluation report delivered", fact_at=datetime(2027, 6, 16, 14, 7),
			link={"label": "View report", "destination": [PAGE, "TND-1", "evaluation", "report"]})
		row = self.region(self.read(Provider(oversight=[linked])), "oversight")["entries"][0]
		self.assertEqual(row["link"], {"label": "View report", "destination": {"route": [PAGE, "TND-1", "evaluation", "report"], "route_options": {}}})
		self.assertEqual(row["fact"], "Evaluation report delivered 16 June, 14:07")
		self.assertEqual(row["timing"], "Updated 15 days ago (3 June, 10:00)")  # the fact is its own line; it does not replace the timing

	def test_a_row_without_a_fact_has_an_empty_one(self):
		self.assertEqual(self.region(self.read(Provider(oversight=[entry(he.OVERSIGHT, n=1)])), "oversight")["entries"][0]["fact"], "")

	def test_a_row_without_a_link_says_so(self):
		row = self.region(self.read(Provider(oversight=[entry(he.OVERSIGHT, n=1)])), "oversight")["entries"][0]
		self.assertIsNone(row["link"])

	def test_a_link_to_a_page_the_viewer_may_not_open_drops_the_entry(self):
		linked = entry(he.OVERSIGHT, n=1, link={"label": "View report", "destination": ["no-such-page-xyz", "x"]})
		region = self.region(self.read(Provider(oversight=[linked])), "oversight")
		self.assertEqual(region["entries"], [])
		self.assertEqual(region["coverage"], "partial")


class TestFormDestination(HomeTestCase):
	"""A record Home points at that has no Page of its own (a Form route): allowed when the viewer may read that record."""

	def test_a_form_destination_the_viewer_may_read_is_kept(self):
		form = entry(n=1, destination=["Form", "User", "Administrator"])
		with patch.object(frappe, "has_permission", return_value=True) as check:
			region = self.region(self.read(Provider(my_work=[form])), "my_work")
		self.assertEqual([r["title"] for r in region["entries"]], ["Supply 1"])
		check.assert_called_with("User", "read", doc="Administrator", user=self.charles)

	def test_a_form_destination_the_viewer_may_not_read_drops_the_entry(self):
		form = entry(n=1, destination=["Form", "User", "Administrator"])
		with patch.object(frappe, "has_permission", return_value=False):
			region = self.region(self.read(Provider(my_work=[form])), "my_work")
		self.assertEqual(region["entries"], [])
		self.assertEqual(region["coverage"], "partial")

	def test_a_form_destination_naming_no_real_doctype_is_dropped(self):
		region = self.region(self.read(Provider(my_work=[entry(n=1, destination=["Form", "No Such Doctype", "x"])])), "my_work")
		self.assertEqual((region["entries"], region["coverage"]), ([], "partial"))


class TestTechnicalWork(HomeTestCase):
	"""A Technical Operator's technical work (support issues) is the one thing a technical reader is given: not a business action."""

	def read_technical(self, *technical, user=None):
		return hw.get_workspace(user or self.daniel, providers=[Provider(my_work=[entry()])], technical_providers=list(technical), at=NOW)

	def test_a_technical_reader_gets_only_the_technical_providers_my_work(self):
		business = Provider(my_work=[entry()])
		technical = Provider(my_work=[entry(n=7, owner="support", action_id="resolve", title="Issue 7")])
		result = hw.get_workspace(self.daniel, providers=[business], technical_providers=[technical], at=NOW)
		self.assertTrue(result["viewer"]["technical"])
		self.assertEqual(business.calls, [])
		self.assertEqual([row["title"] for row in self.region(result, "my_work")["entries"]], ["Issue 7"])
		self.assertEqual(self.region(result, "my_work")["entries"][0]["module"], "Support issues")
		self.assertFalse(result["empty"])
		self.assertFalse(result["summary_visible"])  # no counts for a technical reader
		for name in ("coming_up", "waiting", "oversight", "completed"):
			self.assertEqual(self.region(result, name)["entries"], [])

	def test_with_nothing_technical_to_do_the_orientation_is_unchanged(self):
		result = self.read_technical(Provider(my_work=[]))
		self.assertTrue(result["empty"])
		self.assertEqual(self.region(result, "my_work")["entries"], [])

	def test_a_failing_technical_provider_never_shows_business_work_and_does_not_break_the_page(self):
		result = self.read_technical(Provider(my_work=RuntimeError("boom")))
		self.assertEqual(result["state"], "ready")
		self.assertEqual(self.region(result, "my_work")["entries"], [])

	def test_a_business_user_is_never_read_through_the_technical_providers(self):
		technical = Provider(my_work=[entry(owner="support", action_id="resolve")])
		hw.get_workspace(self.charles, providers=[Provider()], technical_providers=[technical], at=NOW)
		self.assertEqual(technical.calls, [])


class TestRetry(HomeTestCase):
	def test_retry_reads_only_the_named_region(self):
		provider = Provider(my_work=[entry(n=1)], waiting=[entry(he.WAITING, n=2)])
		result = self.read(provider, regions=["waiting"])
		self.assertEqual(list(result["regions"]), ["waiting"])
		self.assertEqual({region for _, region in provider.calls}, {"waiting"})

	def test_coming_up_and_oversight_also_read_my_work_to_deduplicate_but_do_not_return_it(self):
		provider = Provider(my_work=[entry(n=1, action_id="a")], coming_up=[entry(he.COMING_UP, n=1, action_id="a")])
		result = self.read(provider, regions=["coming_up"])
		self.assertEqual(list(result["regions"]), ["coming_up"])
		self.assertEqual(result["regions"]["coming_up"]["entries"], [])
		self.assertIn("my_work", {region for _, region in provider.calls})

	def test_an_unknown_region_name_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.read(Provider(), regions=["inbox"])


class TestReadsCreateNothing(HomeTestCase):
	def test_loading_paging_and_retrying_write_nothing(self):
		provider = Provider(my_work=[entry(n=i) for i in range(1, 8)], waiting=[entry(he.WAITING, n=9)])
		before = frappe.db.transaction_writes
		first = self.read(provider)
		self.read(provider, regions=["my_work"], cursors={"my_work": first["regions"]["my_work"]["next_cursor"]})
		self.read(provider, regions=["waiting"])
		self.assertEqual(frappe.db.transaction_writes, before)


class TestMemo(HomeTestCase):
	def test_a_provider_scan_runs_once_per_read_even_though_every_region_calls_it(self):
		from kentender_core.services import home_support

		scans = []

		def provider(*, user, region):
			rows = home_support.memo("fake-owner", lambda: scans.append(1) or [entry(n=1)])
			return rows if region == "my_work" else None

		self.read(provider)
		self.assertEqual(len(scans), 1)
		self.read(provider)
		self.assertEqual(len(scans), 2)  # a new read scans afresh: no stale rows survive a read

	def test_the_memo_is_per_user(self):
		from kentender_core.services import home_support

		seen = []
		home_support.reset()
		home_support.memo("k", lambda: seen.append("a") or 1, user="a@example.test")
		home_support.memo("k", lambda: seen.append("b") or 2, user="b@example.test")
		self.assertEqual(seen, ["a", "b"])


class TestApi(HomeTestCase):
	def test_the_endpoint_accepts_json_strings_for_its_list_arguments(self):
		from kentender_core.api import home as api

		frappe.set_user(self.charles)
		self.addCleanup(frappe.set_user, "Administrator")
		provider = Provider(my_work=[entry(n=i) for i in range(1, 8)])
		with patch.object(hw, "_hook_paths", return_value=["x.y"]), patch.object(hw, "_load", return_value=provider):
			result = api.get_home_workspace(regions='["my_work"]', cursors="{}")
		self.assertEqual(list(result["regions"]), ["my_work"])
		self.assertEqual(result["regions"]["my_work"]["count"], 7)
