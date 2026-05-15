# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-25 — ``tender_management.enums`` matches doc 3 §4 and doc 9 §5.3 pack slices.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tender_management_enums_p1_25
"""

from __future__ import annotations

import unittest

from kentender_procurement.tender_management import enums


class TestTenderManagementEnumsP125(unittest.TestCase):
	def test_p125_no_duplicate_values_per_tuple(self) -> None:
		for name in enums.__all__:
			if name == "as_frozenset":
				continue
			with self.subTest(name=name):
				tup = getattr(enums, name)
				self.assertIsInstance(tup, tuple)
				self.assertEqual(
					len(tup),
					len(set(tup)),
					msg=f"{name} contains duplicates: {tup}",
				)

	def test_p125_pack_aliases_reference_domain_tuples(self) -> None:
		self.assertIs(enums.PACK_TENDER_STATUS, enums.TENDER_STATUS)
		self.assertIs(enums.PACK_STD_READINESS_STATUS, enums.STD_READINESS_STATUS)
		self.assertIs(enums.PACK_ADDENDUM_STATUS, enums.ADDENDUM_STATUS)
		self.assertIs(enums.PACK_BID_STATUS, enums.BID_STATUS)

	def test_p125_doc9_pack_5_3_tender_status_literal(self) -> None:
		# Doc 9 §5.3 — Tender Status (verbatim block order)
		expected = (
			"Draft",
			"STD Instance Incomplete",
			"Ready for Publication Review",
			"Returned for Correction",
			"Approved for Publication",
			"Published",
			"Addendum Pending",
			"Suspended Pending Addendum",
			"Closed",
			"Closed - No Valid Submissions",
			"Opening Ready",
			"Opening Completed",
			"Evaluation Ready",
			"Evaluation In Progress",
			"Awarded",
			"Contract Handoff Completed",
			"Cancelled",
			"Retender Required",
			"Superseded",
			"Archived",
		)
		self.assertEqual(enums.TENDER_STATUS, expected)

	def test_p125_doc9_pack_5_3_readiness_status_literal(self) -> None:
		expected = (
			"Not Started",
			"Incomplete",
			"Blocked",
			"Warning",
			"Ready",
			"Invalidated by Change",
			"Superseded",
		)
		self.assertEqual(enums.STD_READINESS_STATUS, expected)

	def test_p125_doc9_pack_5_3_addendum_status_literal(self) -> None:
		expected = (
			"Draft",
			"Impact Analysis Pending",
			"Impact Analysis Complete",
			"Pending Legal Review",
			"Pending Approval",
			"Approved",
			"Issued",
			"Cancelled",
			"Superseded",
			"Withdrawn",
		)
		self.assertEqual(enums.ADDENDUM_STATUS, expected)

	def test_p125_doc9_pack_5_3_bid_status_literal(self) -> None:
		expected = (
			"Draft",
			"Submitted",
			"Sealed",
			"Superseded",
			"Withdrawn",
			"Late Attempt Rejected",
			"Opened",
			"Excluded by System Rule",
			"Evaluation Locked",
		)
		self.assertEqual(enums.BID_STATUS, expected)

	def test_p125_as_frozenset_matches_membership(self) -> None:
		fs = enums.as_frozenset(enums.HANDOFF_STATUS)
		self.assertEqual(fs, frozenset(enums.HANDOFF_STATUS))
		self.assertIn("Sent", fs)
		self.assertNotIn("Not A Real Status", fs)

	def test_p125_audit_event_doc_type_options_subset_of_domain_plus_other(self) -> None:
		"""DocType ``event_type`` options = doc 3 §4.18 + ``Other`` escape hatch."""
		import json
		from pathlib import Path

		json_path = (
			Path(__file__).resolve().parents[2]
			/ "kentender_procurement"
			/ "doctype"
			/ "tm2_tender_audit_event"
			/ "tm2_tender_audit_event.json"
		)
		meta = json.loads(json_path.read_text())
		opts = next(f["options"] for f in meta["fields"] if f.get("fieldname") == "event_type")
		labels = [x for x in opts.split("\n") if x.strip()]
		allowed = set(enums.AUDIT_EVENT_TYPE) | {"Other"}
		for label in labels:
			with self.subTest(label=label):
				self.assertIn(label, allowed)
