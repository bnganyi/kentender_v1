# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-19 / AUD-XC-130 — per-case sequence numbers are read from the latest committed rows.

A plain `count()` taken after waiting for the case lock answers from the transaction's
older snapshot and repeats the number the previous command committed; the helpers in
`kentender_procurement.services.sequence` use a locking read. The sweep fails on a
plain `count() + 1` in the case modules."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.services import sequence
from kentender_procurement.tests.two_connections import commit_on_other_connection, raw_row

MODULES = ("award", "bid_evaluation", "bid_opening", "proceedings")
PLAIN_COUNT_PLUS_ONE = re.compile(r"frappe\.db\.count\([^\n]*\)\s*\+\s*1\b")


class TestSequenceHelpers(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.tender = f"SEQ-TND-{uuid4().hex[:8]}"
		frappe.db.commit()
		self.addCleanup(self.purge)

	def purge(self):
		frappe.db.rollback()
		frappe.db.delete("Bid Receipt", {"tender": self.tender})
		frappe.db.commit()

	def test_next_count_sees_a_row_another_connection_committed_after_the_snapshot_opened(self):
		frappe.db.sql("select count(*) from `tabBid Receipt`")  # this transaction's snapshot opens here
		commit_on_other_connection(lambda: raw_row("Bid Receipt", tender=self.tender, receipt_reference="X-1"))
		self.assertEqual(frappe.db.count("Bid Receipt", {"tender": self.tender}) + 1, 1, "a plain count answers from the old snapshot")
		self.assertEqual(sequence.next_count("Bid Receipt", {"tender": self.tender}), 2)

	def test_next_after_uses_the_highest_committed_value(self):
		frappe.db.sql("select count(*) from `tabBid Receipt`")
		commit_on_other_connection(lambda: raw_row("Bid Receipt", tender=self.tender, version_number=7))
		self.assertEqual(sequence.next_after("Bid Receipt", {"tender": self.tender}, "version_number"), 8)
		self.assertEqual(sequence.next_after("Bid Receipt", {"tender": "SEQ-NO-SUCH-TENDER"}, "version_number"), 1)


class TestNoPlainCountPlusOneInTheCaseModules(IntegrationTestCase):
	def test_no_case_module_numbers_a_record_from_a_plain_count(self):
		root = Path(frappe.get_app_path("kentender_procurement"))
		offenders = []
		for module in MODULES:
			for path in sorted((root / module / "services").glob("*.py")):
				for number, line in enumerate(path.read_text().splitlines(), 1):
					if PLAIN_COUNT_PLUS_ONE.search(line):
						offenders.append(f"{module}/services/{path.name}:{number}")
		self.assertEqual(offenders, [], "use kentender_procurement.services.sequence.next_count under the case lock")
