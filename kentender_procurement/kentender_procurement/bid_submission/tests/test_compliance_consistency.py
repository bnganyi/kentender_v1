# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A requirement row asks the same fact twice: the bidder's Compliance answer
and the offered value. They must not contradict each other. The published
requirement says what meets it (a minimum, a maximum, an exact answer, one of
a list, every listed option, a minimum count of each port); where it can be
decided, "Comply" with a value that falls short, or "Do not comply" with a value
that meets it, is a Must fix on both fields. A truthful "Do not comply" with a
value that falls short stays a Review note, and a free-text requirement is left
to the evaluator."""

from __future__ import annotations

from unittest import TestCase

from kentender_procurement.bid_submission.services import consistency, reads
from kentender_procurement.bid_submission.tests.support import DAVID
from kentender_procurement.bid_submission.tests.test_save_bid_task import SaveCase

MEMORY = {"comparison": "Minimum", "control": "INTEGER", "required_value": {"value": 16}, "required_value_display": "16", "unit": "GB", "label": "Memory"}
DISPLAY = {"comparison": "Minimum", "control": "DECIMAL", "required_value": {"value": "14.0"}, "required_value_display": "14.0", "unit": "inches"}
RESPONSE = {"comparison": "Maximum", "control": "INTEGER", "required_value": {"value": 8}, "required_value_display": "8 hours", "unit": "hours"}
ONSITE = {"comparison": "Required", "control": "YES_NO", "required_value": {"value": "Yes"}, "required_value_display": "Yes", "unit": ""}
STORAGE = {"comparison": "One of", "control": "SELECT", "required_value": {"value": "NVMe SSD"}, "required_value_display": "NVMe SSD", "unit": ""}
NETWORK = {"comparison": "Required", "control": "MULTI_SELECT", "required_value": {"values": ["Wi-Fi 6", "Bluetooth 5 or later"]}, "required_value_display": "Wi-Fi 6 and Bluetooth 5 or later", "unit": ""}
PORTS = {"comparison": "Required", "control": "PORT_LIST", "required_value": {"ports": [{"port_type": "USB-C", "minimum_count": 2}, {"port_type": "HDMI", "minimum_count": 1}]}, "required_value_display": "USB-C ×2; HDMI ×1", "unit": ""}
PROCESSOR = {"comparison": "Minimum", "control": "TEXT", "required_value": {"value": "64-bit, 10 cores"}, "required_value_display": "64-bit, 10 cores", "unit": ""}


class TestWhatMeetsARequirement(TestCase):
	def test_each_kind_of_published_requirement_is_decided_the_way_it_reads(self):
		meets = consistency.meets
		self.assertEqual([meets(MEMORY, 16), meets(MEMORY, 32), meets(MEMORY, 8)], [True, True, False])
		self.assertEqual([meets(DISPLAY, "14.00"), meets(DISPLAY, "13.9")], [True, False])
		self.assertEqual([meets(RESPONSE, 8), meets(RESPONSE, 4), meets(RESPONSE, 12)], [True, True, False])
		self.assertEqual([meets(ONSITE, "Yes"), meets(ONSITE, "No")], [True, False])
		self.assertEqual([meets(STORAGE, "NVMe SSD"), meets(STORAGE, "eMMC")], [True, False])
		self.assertEqual([meets(NETWORK, ["Wi-Fi 6", "Bluetooth 5 or later", "5G"]), meets(NETWORK, ["Wi-Fi 6"])], [True, False])
		self.assertEqual(meets(PORTS, [{"port_type": "USB-C", "count": 2}, {"port_type": "HDMI", "count": 1}, {"port_type": "Audio", "count": 1}]), True)
		self.assertEqual(meets(PORTS, [{"port_type": "USB-C", "count": 1}, {"port_type": "HDMI", "count": 1}]), False)

	def test_what_cannot_be_decided_is_left_undecided(self):
		self.assertIsNone(consistency.meets(PROCESSOR, "Core i7, 12 cores"))  # free text: only a person can judge it
		for blank in (None, "", []):
			self.assertIsNone(consistency.meets(MEMORY, blank))
		self.assertIsNone(consistency.meets(MEMORY, "lots"))  # not a number: the value rule reports that
		self.assertIsNone(consistency.meets({"control": "INTEGER", "comparison": "Minimum", "required_value": {}}, 4))

	def test_only_the_contradictions_are_named_and_in_words_that_say_what_to_do(self):
		both = consistency.contradiction(MEMORY, "Comply", 8)
		self.assertIn("does not meet this requirement (minimum 16 GB). You offered 8 GB.", both["compliance"])
		self.assertIn("Choose Do not comply, or change the offered value", both["compliance"])
		self.assertIn("you stated that you comply", both["offered"])
		meets = consistency.contradiction(MEMORY, "Do not comply", 32)
		self.assertIn("meets this requirement (minimum 16 GB)", meets["compliance"])
		self.assertIn("Choose Comply, or change the offered value", meets["compliance"])
		self.assertIsNone(consistency.contradiction(MEMORY, "Comply", 16))
		self.assertIsNone(consistency.contradiction(MEMORY, "Do not comply", 8))  # an honest deviation
		self.assertIsNone(consistency.contradiction(PROCESSOR, "Do not comply", "anything"))
		self.assertIsNone(consistency.contradiction(MEMORY, None, 8))


class TestWhatIsMissing(TestCase):
	"""The message says what falls short, not just that something does: a bidder
	who gave one of three required ports must not read it as the one port being
	refused."""

	def test_each_kind_says_what_falls_short(self):
		short = consistency.shortfall
		self.assertEqual(short(MEMORY, 8), "You offered 8 GB.")
		self.assertEqual(short(RESPONSE, 12), "You offered 12 hours.")
		self.assertEqual(short(ONSITE, "No"), "You offered No.")
		self.assertEqual(short(STORAGE, "eMMC"), "You offered eMMC.")
		self.assertEqual(short(NETWORK, ["Wi-Fi 6"]), "Not offered: Bluetooth 5 or later.")
		self.assertEqual(short(PORTS, [{"port_type": "USB-C", "count": 2}]), "Still needed: HDMI ×1.")
		self.assertEqual(short(PORTS, [{"port_type": "USB-C", "count": 1}]), "Still needed: USB-C 1 of 2, HDMI ×1.")
		self.assertEqual(short(PORTS, [{"port_type": "USB-C", "count": 2}, {"port_type": "HDMI", "count": 1}]), "")  # nothing is short
		self.assertEqual(short(PROCESSOR, "anything"), "")

	def test_the_contradiction_carries_it_on_both_fields(self):
		words = consistency.contradiction(PORTS, "Comply", [{"port_type": "USB-C", "count": 2}])
		self.assertIn("Still needed: HDMI ×1.", words["compliance"])
		self.assertIn("Still needed: HDMI ×1.", words["offered"])
		self.assertIn("Choose Do not comply, or change the offered value.", words["compliance"])
		self.assertIn("you stated that you comply", words["offered"])
		meets = consistency.contradiction(MEMORY, "Do not comply", 32)
		self.assertNotIn("You offered", meets["compliance"])  # a value that meets it has no shortfall to name


class TestAValueThatMeetsARequirement(TestCase):
	def test_the_value_offered_for_each_kind_meets_what_it_is_offered_against(self):
		for facts in (MEMORY, DISPLAY, RESPONSE, ONSITE, STORAGE, NETWORK, PORTS):
			with self.subTest(requirement=facts["required_value_display"]):
				value = consistency.meeting_value(facts)
				self.assertIs(consistency.meets(facts, value), True, value)
		self.assertEqual(consistency.meeting_value(MEMORY), 16)  # an integer stays an integer
		self.assertEqual(consistency.meeting_value(DISPLAY), "14.0")  # a decimal stays the text the rule reads
		self.assertEqual(consistency.meeting_value(PORTS), [{"port_type": "USB-C", "count": 2}, {"port_type": "HDMI", "count": 1}])
		self.assertIsNone(consistency.meeting_value(PROCESSOR))  # free text: the caller writes its own


class TestContradictionsAreMustFix(SaveCase):
	def row(self, heading):
		return next(g for g in self.task("requirements")["groups"] if g["heading"] == heading)

	def pair(self, heading):
		fields = {f["label"]: f for f in self.row(heading)["fields"]}
		return fields["Compliance"], fields["Offered value"]

	def answer(self, heading, compliance, offered):
		comp, off = self.pair(heading)
		self.assertTrue(self.save({comp["handle"]: compliance, off["handle"]: offered}, task="requirements")["ok"])  # a draft may hold anything; readiness decides
		return self.pair(heading)

	def test_a_contradiction_is_a_must_fix_on_both_fields_and_blocks_the_row(self):
		comp, off = self.answer("Memory", "Comply", 8)
		self.assertEqual((comp["issue"]["severity"], off["issue"]["severity"]), ("Must fix", "Must fix"))
		self.assertIn("does not meet this requirement", comp["issue"]["text"])
		self.assertIn("you stated that you comply", off["issue"]["text"])
		view = reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)
		self.assertNotEqual(next(r["status"] for r in view["technical"] if r["label"] == "Memory"), "Complete")
		# the bid is not ready while a contradiction stands, and is again once it is resolved (other rows aside)
		before = sum(1 for g in view["groups"] for f in g["fields"] if f.get("issue") and f["issue"]["severity"] == "Must fix" and f["label"] in ("Compliance", "Offered value") and g["heading"] == "Memory")
		self.assertEqual(before, 2)

	def test_the_other_contradiction_and_the_ways_out(self):
		comp, off = self.answer("Memory", "Do not comply", 32)
		self.assertEqual((comp["issue"]["severity"], off["issue"]["severity"]), ("Must fix", "Must fix"))
		self.assertIn("meets this requirement", comp["issue"]["text"])
		comp, off = self.answer("Memory", "Comply", 32)  # change the answer: consistent
		self.assertEqual((comp["issue"], off["issue"]), (None, None))
		comp, off = self.answer("Memory", "Do not comply", 8)  # a truthful deviation is only a Review note
		self.assertEqual((comp["issue"]["severity"], off["issue"]), ("Review note", None))

	def test_a_yes_no_requirement_is_checked_too(self):
		comp, off = self.answer("On-site support", "Do not comply", "Yes")
		self.assertEqual((comp["issue"]["severity"], off["issue"]["severity"]), ("Must fix", "Must fix"))
		comp, off = self.answer("On-site support", "Comply", "Yes")
		self.assertEqual((comp["issue"], off["issue"]), (None, None))
