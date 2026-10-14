"""The shared record picker's server side: a source registry, one search endpoint, and the rules
core enforces whatever a provider returns (masked refusals, clamping, key filtering, the actor from
the session, recent picks that only reorder).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_record_picker
"""

from __future__ import annotations

import json
import unittest
from unittest import mock

import frappe

from kentender_core.services import record_picker
from kentender_core.tests import picker_test_sources as fixtures

ALLOWED_OUT = {"id", "label", "detail", "disabled_reason", "section", "extra"}


def _use_test_sources():
	return mock.patch.object(record_picker, "_source_paths", return_value=["kentender_core.tests.picker_test_sources.sources"])


class TestRecordPicker(unittest.TestCase):
	def setUp(self):
		fixtures.calls.clear()
		patcher = _use_test_sources()
		patcher.start()
		self.addCleanup(patcher.stop)
		self.addCleanup(frappe.set_user, frappe.session.user)
		frappe.set_user("Administrator")

	def ids(self, result, section=None):
		return [r["id"] for r in result["rows"] if section is None or r["section"] == section]

	# -- refusals are masked ------------------------------------------------------------------

	def test_an_unknown_source_is_a_masked_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			record_picker.search("test.nothing")

	def test_a_provider_that_refuses_is_a_masked_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			record_picker.search("test.forbidden")

	def test_a_guest_is_a_masked_not_found(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.DoesNotExistError):
			record_picker.search("test.everyone")

	# -- what core passes to the provider -----------------------------------------------------

	def test_the_actor_is_the_session_user_and_search_takes_no_actor_argument(self):
		record_picker.search("test.everyone")
		self.assertEqual(fixtures.calls[-1]["actor"], "Administrator")
		with self.assertRaises(TypeError):
			record_picker.search("test.everyone", user="someone.else@example.test")

	def test_limit_is_one_of_the_offer(self):
		for asked, used in ((7, 20), (1000, 20), (50, 50), (20, 20), ("50", 50), (None, 20)):
			record_picker.search("test.by_provider", limit=asked)
			self.assertEqual(fixtures.calls[-1]["limit"], used, asked)

	def test_the_query_is_trimmed_and_cut_at_eighty_characters(self):
		record_picker.search("test.by_provider", query="  " + "a" * 200 + "  ")
		self.assertEqual(fixtures.calls[-1]["query"], "a" * 80)

	def test_context_may_arrive_as_json_text_and_must_be_a_small_object(self):
		record_picker.search("test.everyone", context=json.dumps({"tender": "TND-1"}))
		self.assertEqual(fixtures.calls[-1]["context"], {"tender": "TND-1"})
		record_picker.search("test.everyone", context=None)
		self.assertEqual(fixtures.calls[-1]["context"], {})
		for bad in ('["a"]', "7", '{"x": "' + "y" * 3000 + '"}', "{not json"):
			with self.assertRaises(frappe.ValidationError, msg=bad[:20]):
				record_picker.search("test.everyone", context=bad)

	# -- what comes back ----------------------------------------------------------------------

	def test_a_row_carries_only_the_contract_keys(self):
		result = record_picker.search("test.everyone")
		self.assertTrue(result["rows"])
		for row in result["rows"]:
			self.assertEqual(set(row), ALLOWED_OUT)
		self.assertNotIn("secret", json.dumps(result))
		self.assertNotIn("@moh.example", json.dumps(result), "login keywords are for matching, not display")

	def test_extra_is_handed_to_the_screen_untouched_but_only_as_short_text(self):
		result = record_picker.search("test.everyone", query="zoe")
		self.assertEqual(result["rows"][0]["extra"], {"designation": "Auditor", "department": "Internal Audit"})
		rows = {r["id"]: r["extra"] for r in record_picker.search("test.everyone")["rows"]}
		self.assertEqual(rows["amos.kamau"], {}, "a row with no extra carries an empty one")
		weird = record_picker._row({"id": "a", "label": "A", "extra": {"ok": 7, "long": "x" * 500, "nested": {"a": 1}, "list": [1], "none": None, **{f"k{i}": "v" for i in range(20)}}})
		self.assertEqual(weird["extra"]["ok"], "7")
		self.assertEqual(len(weird["extra"]["long"]), 200)
		self.assertNotIn("nested", weird["extra"])
		self.assertNotIn("list", weird["extra"])
		self.assertNotIn("none", weird["extra"])
		self.assertLessEqual(len(weird["extra"]), 8)
		self.assertEqual(record_picker._row({"id": "a", "label": "A", "extra": "not a dict"})["extra"], {})

	def test_rows_without_an_id_or_label_are_dropped_and_an_id_is_listed_once(self):
		result = record_picker.search("test.messy")
		self.assertEqual([(r["id"], r["label"]) for r in result["rows"]], [("d", "Dee"), ("a", "First A")])

	# -- before typing ------------------------------------------------------------------------

	def test_before_typing_the_order_is_near_then_recent_then_everyone_else(self):
		result = record_picker.search("test.everyone", recent=["daniel.rotich", "amina.hassan", "zoe.mwangi", "nobody.here"])
		self.assertEqual(self.ids(result, "near"), ["amina.hassan", "brian.wafula"])
		self.assertEqual(self.ids(result, "recent"), ["daniel.rotich", "zoe.mwangi"], "recent keeps the reader's order, drops people already shown and unknown ids")
		self.assertEqual(self.ids(result, "rest"), ["amos.kamau", "beatrice.kamau", "esther.njeri", "hamina.ali", "pw.tnd.both@example.test", "pw.tnd.officer@example.test"])
		self.assertEqual(len(self.ids(result)), len(set(self.ids(result))), "nobody twice")
		self.assertEqual([r["section"] for r in result["rows"]], sorted((r["section"] for r in result["rows"]), key=["near", "recent", "rest"].index))

	def test_a_recent_id_the_provider_did_not_return_reveals_nothing(self):
		result = record_picker.search("test.everyone", recent=["administrator", "someone.unlisted"])
		self.assertEqual(self.ids(result, "recent"), [])

	def test_recent_is_at_most_five_and_ten_are_read(self):
		fixtures_ids = [r["id"] for r in fixtures.PEOPLE if not r.get("near")]
		result = record_picker.search("test.everyone", recent=fixtures_ids + ["x"] * 20)
		self.assertLessEqual(len(self.ids(result, "recent")), 5)

	def test_before_typing_never_shows_more_than_the_limit_and_says_how_many_exist(self):
		result = record_picker.search("test.many")
		self.assertEqual(len(result["rows"]), 20, "a department of 120 is capped at the limit")
		self.assertEqual(result["total"], 120)
		self.assertEqual({r["section"] for r in result["rows"]}, {"near"})
		result = record_picker.search("test.many", limit=50)
		self.assertEqual(len(result["rows"]), 50)

	def test_the_rest_fills_what_the_first_two_parts_left(self):
		result = record_picker.search("test.everyone")
		self.assertEqual(len(result["rows"]), len(fixtures.PEOPLE))
		self.assertEqual(result["total"], len(fixtures.PEOPLE))
		self.assertFalse(result["typed"])

	def test_the_sources_own_wording_comes_back_with_every_search(self):
		labels = record_picker.search("test.everyone")["labels"]
		self.assertEqual(labels, {"noun": "person", "plural": "persons", "near": "Your department", "rest": "Everyone else", "hint": ""})
		labels = record_picker.search("test.many", query="p")["labels"]
		self.assertEqual(labels, {"noun": "unit", "plural": "units", "near": "Your directorate", "rest": "Other units", "hint": "Only active units are listed."})

	# -- typing -------------------------------------------------------------------------------

	def test_typing_matches_by_word_start_and_ranks_the_name_first(self):
		result = record_picker.search("test.everyone", query="ami")
		# Amina Hassan (name starts), then names with a word starting "ami" (none other), then detail words ("Aminata Desk").
		self.assertEqual(self.ids(result), ["amina.hassan", "hamina.ali"])
		self.assertEqual({r["section"] for r in result["rows"]}, {"match"})
		self.assertTrue(result["typed"])

	def test_typing_ignores_case_and_accents(self):
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="ZOE")), ["zoe.mwangi"])
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="zoë")), ["zoe.mwangi"])

	def test_every_word_typed_must_start_a_word(self):
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="kamau budget")), ["amos.kamau", "beatrice.kamau"])
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="kamau planning")), [])

	def test_a_login_matches_though_it_is_never_shown(self):
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="daniel.rotich@")), ["daniel.rotich"])

	def test_a_whole_login_finds_that_person_first_even_when_others_share_its_words(self):
		result = record_picker.search("test.everyone", query="pw.tnd.officer@example.test")
		self.assertEqual(self.ids(result)[0], "pw.tnd.officer@example.test")
		self.assertIn("pw.tnd.both@example.test", self.ids(result), "the other person still matches, just not first")
		self.assertEqual(self.ids(record_picker.search("test.everyone", query="PW.TND.BOTH@EXAMPLE.TEST"))[0], "pw.tnd.both@example.test")

	def test_an_unavailable_person_is_listed_with_the_reason_and_counted(self):
		result = record_picker.search("test.everyone", query="esther")
		row = result["rows"][0]
		self.assertEqual((row["id"], row["disabled_reason"]), ("esther.njeri", "Was involved in processing this Tender"))

	def test_total_counts_every_match_while_rows_stop_at_the_limit(self):
		result = record_picker.search("test.many", query="person")
		self.assertEqual((len(result["rows"]), result["total"]), (20, 120))

	def test_nothing_found_is_an_empty_list_with_a_zero_total(self):
		result = record_picker.search("test.everyone", query="xyz")
		self.assertEqual((result["rows"], result["total"]), ([], 0))

	# -- provider mode ------------------------------------------------------------------------

	def test_a_provider_that_filters_gives_its_own_total_and_core_does_not_refilter(self):
		result = record_picker.search("test.by_provider", query="Hass")
		self.assertEqual(self.ids(result), ["amina.hassan"])
		self.assertEqual(result["total"], 143)

	# -- resolve ------------------------------------------------------------------------------

	def test_resolve_returns_the_ids_the_actor_may_see_and_drops_the_rest(self):
		result = record_picker.resolve("test.everyone", ids=["zoe.mwangi", "esther.njeri", "nobody"])
		self.assertEqual({r["id"]: r["disabled_reason"] for r in result["rows"]}, {"zoe.mwangi": None, "esther.njeri": "Was involved in processing this Tender"})

	def test_resolve_through_a_providers_own_resolver(self):
		result = record_picker.resolve("test.by_provider", ids=json.dumps(["amina.hassan"]))
		self.assertEqual(self.ids(result), ["amina.hassan"])

	def test_resolve_of_an_unknown_source_is_masked(self):
		with self.assertRaises(frappe.DoesNotExistError):
			record_picker.resolve("test.nothing", ids=["a"])

	# -- the registry itself ------------------------------------------------------------------

	def test_a_badly_shaped_source_is_reported(self):
		bad = [
			{"key": "x.one", "noun": "p", "match": "core", "provider": "kentender_core.tests.picker_test_sources.everyone"},
			{"key": "x.one", "noun": "p", "match": "core", "provider": "kentender_core.tests.picker_test_sources.everyone"},
			{"key": "nodots", "noun": "p", "match": "core", "provider": "kentender_core.tests.picker_test_sources.everyone"},
			{"key": "x.two", "noun": "p", "match": "sideways", "provider": "kentender_core.tests.picker_test_sources.everyone"},
			{"key": "x.three", "noun": "p", "match": "provider", "provider": "kentender_core.tests.picker_test_sources.by_provider"},
			{"key": "x.four", "noun": "p", "match": "core", "provider": "kentender_core.tests.picker_test_sources.does_not_exist"},
		]
		with mock.patch.object(record_picker, "_load", return_value=bad):
			problems = " | ".join(record_picker.check_sources())
		for expected in ("x.one", "nodots", "sideways", "x.three", "x.four"):
			self.assertIn(expected, problems)


class TestMatches(unittest.TestCase):
	"""`matches` is the word-start rule a source that filters in the database applies to what it fetched."""

	row = {"id": "a", "label": "Zoë Mwangi", "detail": "Auditor · Internal Audit", "keywords": "zoe.mwangi@moh.example"}

	def test_the_same_rule_as_search(self):
		for text, expected in (("zoe", True), ("ZOË mw", True), ("audit", True), ("internal aud", True), ("zoe.mwangi@moh.example", True), ("oe", False), ("zoe finance", False), ("xyz", False)):
			self.assertEqual(record_picker.matches(self.row, text), expected, text)

	def test_nothing_typed_matches_everything(self):
		self.assertTrue(record_picker.matches(self.row, ""))
		self.assertTrue(record_picker.matches(self.row, "   "))


class TestRegisteredSources(unittest.TestCase):
	def test_every_source_any_app_registers_has_the_documented_shape(self):
		"""Reads the real hooks: an app that adds a badly shaped source fails here."""
		self.assertEqual(record_picker.check_sources(), [])


class TestPeopleNear(unittest.TestCase):
	"""Near the reader = the same home organisation unit, read through core's own staff-home-unit
	read. The home unit orders suggestions; it never decides who may be chosen."""

	def test_people_who_share_the_actors_home_unit_are_near(self):
		with mock.patch("kentender_core.services.staff_home_unit.get_staff_home_organisation_unit", return_value={"state": "Recorded", "organisation_unit": "MOH-SCM"}), \
				mock.patch.object(frappe, "get_all", return_value=["a@x", "c@x"]) as get_all:
			near = record_picker.people_near("me@x", ["a@x", "b@x", "c@x"])
		self.assertEqual(near, {"a@x", "c@x"})
		self.assertEqual(get_all.call_args.kwargs["filters"]["name"], ("in", ["a@x", "b@x", "c@x"]))

	def test_an_actor_with_no_home_unit_has_no_one_near(self):
		with mock.patch("kentender_core.services.staff_home_unit.get_staff_home_organisation_unit", return_value={"state": "Not recorded", "organisation_unit": ""}):
			self.assertEqual(record_picker.people_near("me@x", ["a@x"]), set())


class TestEndpoints(unittest.TestCase):
	"""The whitelisted layer: explicit signatures, so Frappe's transport fields never reach the service."""

	def setUp(self):
		patcher = _use_test_sources()
		patcher.start()
		self.addCleanup(patcher.stop)
		self.addCleanup(frappe.set_user, frappe.session.user)
		frappe.set_user("Administrator")

	def test_search_through_the_api_with_json_text_arguments(self):
		from kentender_core.api import record_picker as api

		result = api.search("test.everyone", query="ami", context='{"tender": "T"}', recent='["zoe.mwangi"]', limit="20")
		self.assertEqual([r["id"] for r in result["rows"]], ["amina.hassan", "hamina.ali"])

	def test_both_endpoints_are_whitelisted_and_take_no_actor(self):
		import inspect

		from kentender_core.api import record_picker as api

		for fn in (api.search, api.resolve):
			self.assertIn(fn, frappe.whitelisted)
			params = inspect.signature(fn).parameters
			self.assertFalse(any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()), "no **kwargs: transport fields must not reach the service")
			self.assertFalse({"user", "actor"} & set(params))
