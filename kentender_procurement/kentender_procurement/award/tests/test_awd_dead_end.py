# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""No dead ends (AWD-CHG-001 v0.4 §5.9; KT-STD-001 §3B.7; AWD-AC-022; tracker
AWD4-1003). Every synthetic stage × every internal viewer yields a sound
next-step answer: a turn has an action, a block names its fixes, a wait
names its holder; a technical reader never gets a turn."""

from __future__ import annotations

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.award.seeds import playwright_ui_fixtures as pw
from kentender_procurement.award.services import next_steps, reads, records, simulation
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, DANIEL, HOP, NAOMI, NS, AwardCase


class TestDeadEnds(AwardCase):
	def test_every_stage_and_viewer(self):
		failures = []
		for stage, (build, _instant, _switches) in pw.STAGES.items():
			from kentender_procurement.award.seeds import clear

			clear.wipe(namespace=NS)
			clear.wipe(namespace=pw.NS)
			syn.clear()
			simulation.reset_controls()
			frappe.flags.kt_awd_fixture_namespace = NS
			world = build()
			doc = frappe.get_doc(records.CASE, world.award)
			for user in (HOP, AO, NAOMI, DANIEL):
				answer = next_steps.answer(doc, user)
				found = ns.problems(answer)
				if user == DANIEL and answer["kind"] in ns.TURN_KINDS:
					found.append("technical reader given a turn")
				if answer["kind"] == ns.KIND_YOUR_TURN and user in (HOP, AO):
					acts = reads.record(award=doc.name, user=user)["actions"]
					if not any(acts.values()) and not answer.get("primary_action"):
						found.append("your turn with no enabled action")
				if found:
					failures.append(f"{stage} / {user}: {answer.get('headline')!r} — {found}")
		self.assertEqual(failures, [])
