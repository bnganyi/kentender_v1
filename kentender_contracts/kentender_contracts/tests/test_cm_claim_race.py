# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.8 (plan Phase 7; tracker CM8-701; CM-AC-11; gate CM-G07 `cm-native-gate`; proof level L2): two concurrent submissions cannot reserve the same claim entitlement.

Two separate processes each submit a claim for all eight accepted units at the same instant. The case is locked for each command, so one runs after the other: the second finds the contract changed under it,
reloads, sends the claim again and is held because nothing is left. Never are two claims for the same eight units both submitted."""

from __future__ import annotations

import json
import os
import subprocess
import time

import frappe

from kentender_contracts.services import records
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

BENCH = os.path.abspath(os.path.join(os.path.realpath(frappe.get_app_path("kentender_contracts")), "..", "..", "..", ".."))


class TestClaimRace(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def test_two_claims_at_the_same_instant_never_both_reserve_the_same_eight_units(self):
		env = tw.Environment().__enter__()
		self.addCleanup(lambda: env.__exit__(None, None, None))
		t = tw.Thread(self.people, tag="RACE")
		case = t.active()
		t.appointed()
		units = tw.fresh_serials(8)
		arrival = t.arrive(units)["arrival"]
		t.inspect(arrival, units)
		t.accept(arrival)
		frappe.db.commit()
		version = t.version()
		start_at = time.time() + 14
		env_vars = {**os.environ, "CM_RACE_CLOCK": tw.CLOCK}
		procs = [subprocess.Popen(["bench", "--site", frappe.local.site, "execute", "kentender_contracts.tests.native_support.race_claim", "--kwargs",
			str({"case": case, "actor": self.people["david"], "reference": ref, "version": version, "start_at": start_at})], cwd=BENCH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_vars)
			for ref in ("RACE-A", "RACE-B")]
		outputs = [p.communicate(timeout=240)[0] for p in procs]
		contenders = [json.loads(line[5:]) for out in outputs for line in out.splitlines() if line.startswith("RACE ")]
		frappe.db.rollback()  # see the other processes' committed work
		self.assertEqual(len(contenders), 2, outputs)
		rows = frappe.get_all("Contract Invoice", filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["claim_reference", "state", "claimed_amount"])
		submitted = [r for r in rows if r.state == "Submitted"]
		self.assertEqual(len(submitted), 1, (rows, contenders))
		self.assertEqual(submitted[0].claimed_amount, 800000)
		self.assertEqual(sorted(c.get("state") for c in contenders), ["Held", "Submitted"], contenders)
		self.assertEqual([r.state for r in rows if r.state == "Held"], ["Held"], "the claim that came second is recorded and held, never lost")
		self.assertEqual(sum(1 for r in rows if r.state in ("Submitted", "Certified")), 1, "the eight units are reserved once")
