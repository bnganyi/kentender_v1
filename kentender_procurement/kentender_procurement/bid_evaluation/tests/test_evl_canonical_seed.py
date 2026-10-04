# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Found 4 Oct 2026 on a new server: Bid Evaluation Settings there has the
default presence lapse (90 s), the dev site 0 (off). The canonical
evaluation's discussions run for minutes of fixture time without the members'
pages checking in, so every member lapsed and the clarification could not be
authorised. The seed checks in for everyone present at each step, as a
member's open page would, whatever the setting."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_evaluation.seeds import clear
from kentender_procurement.bid_evaluation.seeds import kentender_mvp_v1 as seed


class TestCanonicalEvaluationWithPresenceLapse(IntegrationTestCase):
	def test_the_canonical_evaluation_is_told_with_the_default_presence_lapse(self):
		from kentender_procurement.award.seeds import kentender_mvp_v1 as award_seed

		settings = "Bid Evaluation Settings"
		before = frappe.db.get_single_value(settings, "presence_lapse_seconds")
		tender = seed.canonical_tender()
		self.assertTrue(tender, "seed the canonical world through bid_evaluation first")

		def restore():
			frappe.db.set_single_value(settings, "presence_lapse_seconds", before)
			seed.upsert_bid_evaluation_base(commit=False)
			award_seed.upsert_award_base(commit=False)  # the award goes with a removed evaluation
			frappe.db.commit()

		self.addCleanup(restore)
		frappe.db.set_single_value(settings, "presence_lapse_seconds", 90)
		clear.wipe(tenders=[tender], namespace=seed.NAMESPACE)
		out = seed.upsert_bid_evaluation_base(commit=False)
		self.assertFalse(out["idempotent"])
		self.assertEqual([r["check"] for r in seed.validate_bid_evaluation_seed() if not r["ok"]], [])
