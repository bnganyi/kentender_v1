# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-101..104 — Budget money movements and Version decisions are
serialised by one lock order and decide from locking reads.

These are REAL two-connection tests: each competing command runs in its own
thread with its own `frappe.init` / `frappe.connect` (a separate MariaDB
connection and transaction), synchronised with events, against the site's
REPEATABLE READ isolation. Fixtures are committed so the other connections see
them; every test registers its rows for purge in `tearDownClass`.

Two shapes are used:

* snapshot race — connection B opens its snapshot, connection A commits its
  effect, then B runs. The lock B takes is free (A has committed), so only a
  locking READ after the lock sees A's effect. Before the fix B read its old
  snapshot and oversubscribed.
* lock-wait race — connection A holds its (uncommitted) effect while B starts;
  B must block until A commits and then decide from A's committed state. Before
  the fix the lock sets did not conflict and B finished at once on stale data.
"""

from __future__ import annotations

import threading

import frappe
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, PRINCIPAL_REQUISITIONS, service_caller
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE, owner_ou
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase
from kentender_budget.utils.version_stamp import stamped

_WAIT = 30
_BLOCKED_FOR = 1.5


class _Conn:
	"""One command on its own database connection, in its own thread."""

	def __init__(self, user, fn, *, hold=False, snapshot_first=False):
		self.user, self.fn, self.hold, self.snapshot_first = user, fn, hold, snapshot_first
		self.site, self.sites_path = frappe.local.site, frappe.local.sites_path
		self.value = self.error = None
		self.titles: list[str] = []
		self.snapshot_open = threading.Event()  # B's snapshot is established
		self.start_gate = threading.Event()  # B may now run its command
		self.ran = threading.Event()  # the command returned or raised
		self.commit_gate = threading.Event()  # A may commit (hold=True)
		self.finished = threading.Event()  # committed or rolled back
		self.thread = threading.Thread(target=self._run, daemon=True)
		if not snapshot_first:
			self.start_gate.set()
		self.thread.start()

	def _run(self):
		try:
			frappe.init(site=self.site, sites_path=self.sites_path)
			frappe.connect()
			frappe.set_user(self.user)
			if self.snapshot_first:
				frappe.db.sql("select count(*) from `tabFunding Reservation`")
				self.snapshot_open.set()
				self.start_gate.wait(_WAIT)
			try:
				self.value = self.fn()
			except BaseException as exc:  # noqa: BLE001 - handed to the test thread
				self.error = exc
				self.titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
			self.ran.set()
			if self.hold:
				self.commit_gate.wait(_WAIT)
			if self.error:
				frappe.db.rollback()
			else:
				frappe.db.commit()
		finally:
			try:
				frappe.db.close()
			except Exception:  # noqa: BLE001
				pass
			self.finished.set()

	def commit(self):
		self.commit_gate.set()
		assert self.finished.wait(_WAIT), "connection did not finish"


def _fy_ended(budget: str) -> None:
	fy = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
	frappe.db.set_value("Fiscal Year", fy, "year_end_date", add_days(nowdate(), -5))


class TestBudgetLockingRaces(_PrincipalBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.contract_principal = None

	# ----- fixtures -------------------------------------------------------

	def _req(self, ref):
		return service_caller(PRINCIPAL_REQUISITIONS, reference=ref)

	def _world(self, dhi=100_000_000, hwd=60_000_000):
		budget, version = self._create_active_baseline(dhi_amount=dhi, hwd_amount=hwd)
		dhi_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")
		hwd_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "HWD test line"}, "budget_line")
		frappe.db.commit()
		return budget, version, dhi_line, hwd_line

	def _checked(self, line, amount, ref):
		"""A funding check by the Requisitions principal; returns what the
		reserve call needs. Committed so another connection can use it."""
		self._as(self.hopf)
		key = self._key(ref)
		checked = check_reserve.check_funding(
			plan_item=f"PPI-{key}", plan_version="TEST-PLN-RACE", source_set_hash=f"HASH-{key}",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": f"PSA-{key}", "drawdown_line_id": f"DDL-{key}"}],
			correlation_id=key, caller=self._req(ref), caller_reference=ref,
		)
		self._as("Administrator")
		frappe.db.commit()
		return {"token": checked["token"], "hash": f"HASH-{key}", "key": key, "ref": ref}

	def _reserve_fn(self, c):
		return lambda: check_reserve.reserve_funding(token=c["token"], source_set_hash=c["hash"], idempotency_key=c["key"], caller=self._req(c["ref"]))

	def _reserve_now(self, line, amount, ref):
		c = self._checked(line, amount, ref)
		self._as(self.hopf)
		result = check_reserve.reserve_funding(token=c["token"], source_set_hash=c["hash"], idempotency_key=c["key"], caller=self._req(c["ref"]))
		self._as("Administrator")
		frappe.db.commit()
		return result["reservations"][0]["reservation_id"]

	def _position(self, line):
		frappe.db.commit()  # fresh snapshot
		budget = frappe.db.get_value("Procurement Budget Line", line, "budget")
		active = contracts._active_version(budget)
		return contracts._line_position(line, contracts._line_version_for(active.name, line))

	def _successor(self, budget, version, dhi_line, hwd_line, dhi, hwd):
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(succ["ok"], succ)
		new = succ["version"]["id"]
		self._track("Procurement Budget Version", new)
		saved = lines_svc.save_budget_lines_draft(stamped(
			{"budget_version": new, "lines": [{"budget_line": dhi_line, "approved_amount": dhi}, {"budget_line": hwd_line, "approved_amount": hwd}]}
		))
		self.assertTrue(saved["ok"], saved)
		submitted = readiness.submit_budget_version(stamped({"budget_version": new}))
		self.assertTrue(submitted["ok"], submitted)
		self._as("Administrator")
		frappe.db.commit()
		return new

	def _approve_fn(self, version):
		return lambda: readiness.approve_budget_version(stamped({"budget_version": version}))

	# ----- AUD-XC-101 -----------------------------------------------------

	def test_two_80m_reservations_on_a_100m_line_cannot_both_succeed(self):
		"""AUD-XC-101 / BUD18-AC-019 — B opened its snapshot before A committed 80m;
		B's reserve must still see A's reservation and refuse."""
		_budget, _version, dhi, _hwd = self._world()
		a, b = self._checked(dhi, 80_000_000, "REQ-RACE-A"), self._checked(dhi, 80_000_000, "REQ-RACE-B")
		conn_b = _Conn(self.hopf, self._reserve_fn(b), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(_WAIT))
		conn_a = _Conn(self.hopf, self._reserve_fn(a))
		self.assertTrue(conn_a.finished.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		self.assertIn("BUDGET_INSUFFICIENT_FUNDS", conn_b.titles)
		pos = self._position(dhi)
		self.assertEqual(pos["reserved"], 80_000_000)
		self.assertEqual(pos["available"], 20_000_000)

	def test_a_reservation_waiting_on_a_reservation_decides_on_the_committed_position(self):
		"""Lock-wait shape: A holds an uncommitted 80m reservation; B blocks on the
		same Budget lock, then refuses on A's committed state."""
		_budget, _version, dhi, _hwd = self._world()
		a, b = self._checked(dhi, 80_000_000, "REQ-RACE-WA"), self._checked(dhi, 80_000_000, "REQ-RACE-WB")
		conn_a = _Conn(self.hopf, self._reserve_fn(a), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b = _Conn(self.hopf, self._reserve_fn(b))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "B must wait for A's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		self.assertIn("BUDGET_INSUFFICIENT_FUNDS", conn_b.titles)
		self.assertEqual(self._position(dhi)["reserved"], 80_000_000)

	# ----- AUD-XC-102 -----------------------------------------------------

	def _two_commitments(self, dhi):
		"""Line 100m with C1 = C2 = 40m committed (available 20m)."""
		out = []
		for n in (1, 2):
			reservation = self._reserve_now(dhi, 40_000_000, f"REQ-RACE-C{n}")
			contract = self._key(f"CTR-RACE-{n}")
			res = commitment_svc.convert_reservation(
				reservation, contract, 40_000_000, self._key("CONV"),
				contract_event_id=f"{contract}:signed", contract_event_type="ContractSigned", caller=service_caller(PRINCIPAL_CONTRACT, reference=contract),
			)
			out.append((res["commitment"]["commitment_id"], contract))
		frappe.db.commit()
		return out

	def _adjust_fn(self, commitment, contract, new_total, tag):
		return lambda: commitment_svc.adjust_commitment(
			commitment, new_total, f"{contract}:var-{tag}", "ContractVariation", self._key(f"ADJ-{tag}"), caller=service_caller(PRINCIPAL_CONTRACT, reference=contract)
		)

	def test_two_commitment_increases_of_20m_cannot_both_succeed(self):
		"""AUD-XC-102 — different commitment rows on one line: B's snapshot predates
		A's committed increase; B must refuse the unfunded increase."""
		_budget, _version, dhi, _hwd = self._world()
		(c1, k1), (c2, k2) = self._two_commitments(dhi)
		conn_b = _Conn(self.hopf, self._adjust_fn(c2, k2, 60_000_000, "b"), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(_WAIT))
		conn_a = _Conn(self.hopf, self._adjust_fn(c1, k1, 60_000_000, "a"))
		self.assertTrue(conn_a.finished.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		self.assertIn("BUDGET_COMMITMENT_INCREASE_UNFUNDED", conn_b.titles)
		pos = self._position(dhi)
		self.assertEqual(pos["committed"], 100_000_000)
		self.assertGreaterEqual(pos["available"], 0)

	def test_a_commitment_increase_waits_for_a_reservation_on_the_same_line(self):
		"""AUD-XC-102 — an increase and a reservation share the line's lock."""
		_budget, _version, dhi, _hwd = self._world()
		(c1, k1), _second = self._two_commitments(dhi)
		held = self._checked(dhi, 15_000_000, "REQ-RACE-H")
		conn_a = _Conn(self.hopf, self._reserve_fn(held), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b = _Conn(self.hopf, self._adjust_fn(c1, k1, 60_000_000, "w"))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the increase must wait for the reservation's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		self.assertIn("BUDGET_COMMITMENT_INCREASE_UNFUNDED", conn_b.titles)

	# ----- AUD-XC-103 -----------------------------------------------------

	def test_approval_waits_for_a_racing_reservation_and_rechecks_the_floor(self):
		"""AUD-XC-103 (a) — line reserved 70m, successor sets it to 80m; a racing 20m
		reservation (fits under the old 100m) must not let the 80m successor
		activate under 90m protected."""
		budget, version, dhi, hwd = self._world()
		self._reserve_now(dhi, 70_000_000, "REQ-RACE-70")
		successor = self._successor(budget, version, dhi, hwd, 80_000_000, 80_000_000)
		race = self._checked(dhi, 20_000_000, "REQ-RACE-20")
		conn_a = _Conn(self.hopf, self._reserve_fn(race), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b = _Conn(self.approver, self._approve_fn(successor))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "approval must wait for the reservation's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsNone(conn_b.error)
		self.assertFalse(conn_b.value["ok"])
		self.assertEqual(conn_b.value["code"], "BUDGET_NOT_READY")
		self.assertTrue(any(i["rule"] == "BUDGET_REVISION_FLOOR_BREACH" for i in conn_b.value["blockers"]))
		pos = self._position(dhi)
		self.assertGreaterEqual(pos["approved"], pos["reserved"] + pos["committed"])

	def test_a_reservation_waits_for_an_approval_and_uses_the_new_basis(self):
		"""AUD-XC-103 (a), other ordering — the approval holds the Budget lock; the
		reservation waits, then sees the 80m ceiling (70m already reserved)."""
		budget, version, dhi, hwd = self._world()
		self._reserve_now(dhi, 70_000_000, "REQ-RACE-70B")
		successor = self._successor(budget, version, dhi, hwd, 80_000_000, 80_000_000)
		race = self._checked(dhi, 20_000_000, "REQ-RACE-20B")
		conn_a = _Conn(self.approver, self._approve_fn(successor), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertTrue(conn_a.value["ok"], conn_a.value)
		conn_b = _Conn(self.hopf, self._reserve_fn(race))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the reservation must wait for the approval's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		# The funding check was made against V1; V2 replaced it, so the token is
		# stale (and the 80m ceiling would refuse it anyway).
		self.assertTrue({"BUDGET_CHECK_STALE", "BUDGET_INSUFFICIENT_FUNDS"} & set(conn_b.titles), conn_b.titles)
		pos = self._position(dhi)
		self.assertEqual(pos["approved"], 80_000_000)
		self.assertEqual(pos["reserved"], 70_000_000)

	def test_closure_waits_for_a_racing_reservation(self):
		"""AUD-XC-103 (b) — a reservation committed while the closure waits keeps the
		Budget open: no Closed budget with an Active reservation."""
		budget, _version, dhi, _hwd = self._world()
		_fy_ended(budget)
		frappe.db.commit()
		race = self._checked(dhi, 1_000_000, "REQ-RACE-CL")
		conn_a = _Conn(self.hopf, self._reserve_fn(race), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertIsNone(conn_a.error)
		conn_b = _Conn(self.approver, lambda: readiness.close_budget(stamped({"budget": budget})))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "closure must wait for the reservation's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsNone(conn_b.error)
		self.assertFalse(conn_b.value["ok"], conn_b.value)
		self.assertEqual(conn_b.value["code"], "BUDGET_INVALID_STATE")
		frappe.db.commit()
		self.assertTrue(frappe.db.exists("Procurement Budget Version", {"budget": budget, "status": "Active"}))

	def test_a_reservation_waits_for_a_closure_and_is_refused(self):
		"""AUD-XC-103 (b), other ordering — the closure holds the lock; the
		reservation then finds the Budget Closed."""
		budget, _version, dhi, _hwd = self._world()
		_fy_ended(budget)
		frappe.db.commit()
		race = self._checked(dhi, 1_000_000, "REQ-RACE-CL2")
		conn_a = _Conn(self.approver, lambda: readiness.close_budget(stamped({"budget": budget})), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertTrue(conn_a.value["ok"], conn_a.value)
		conn_b = _Conn(self.hopf, self._reserve_fn(race))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the reservation must wait for the closure's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsInstance(conn_b.error, frappe.ValidationError)
		self.assertIn("BUDGET_CLOSED", conn_b.titles)
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget": budget}), 0)

	# ----- AUD-XC-104 -----------------------------------------------------

	def test_decision_basis_waits_for_an_approval_and_fails_stale(self):
		"""AUD-XC-104 — a Finance decision that read V1 as Active and then waited
		behind V2's approval must not be validated against the replaced basis."""
		budget, version, dhi, hwd = self._world()
		fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		line_version = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": dhi}, "name")
		successor = self._successor(budget, version, dhi, hwd, 90_000_000, 70_000_000)
		conn_a = _Conn(self.approver, self._approve_fn(successor), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertTrue(conn_a.value["ok"], conn_a.value)
		conn_b = _Conn(
			"Administrator",
			lambda: lines_svc.validate_plan_affordability_for_decision(fiscal_year, {dhi: 80_000_000}, expected_revisions={dhi: line_version, "budget_version": version}),
			snapshot_first=True,
		)
		self.assertTrue(conn_b.snapshot_open.wait(_WAIT))
		conn_b.start_gate.set()
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the decision check must wait for the approval's lock")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsNotNone(conn_b.error, "a basis replaced while waiting must fail")
		self.assertIn("BUD_BASIS_STALE", conn_b.titles)
