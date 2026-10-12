# Copyright (c) 2026, KenTender and contributors
"""AUD-XC-120 / AUD-XC-131 (Strategy) — the Strategy command journal binds a key
to (actor, command, payload), answers only after authorisation, and is
race-safe; the state-changing commands require an idempotency key and, on an
existing version, the expected version (STR §8, KT-STD-001 §11).

    bench --site kentender-test.local run-tests --app kentender_strategy \
        --module kentender_strategy.tests.test_str_idempotency_envelope
"""

from __future__ import annotations

import threading
from uuid import uuid4

import frappe

from kentender_strategy.api import strategy_consumer_api as api
from kentender_strategy.tests.test_str_chg_001_v1_8_usability import UsabilityTestBase

CONFLICT = "STRATEGY_IDEMPOTENCY_CONFLICT"
_WAIT = 30
_BLOCKED_FOR = 1.5


def _title(_unused=None) -> list[str]:
	return [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]


class _Conn:
	"""One command on its own database connection and thread."""

	def __init__(self, user, fn, *, hold=False):
		self.user, self.fn, self.hold = user, fn, hold
		self.site, self.sites_path = frappe.local.site, frappe.local.sites_path
		self.value = self.error = None
		self.titles: list[str] = []
		self.ran, self.commit_gate, self.finished = threading.Event(), threading.Event(), threading.Event()
		self.thread = threading.Thread(target=self._run, daemon=True)
		self.thread.start()

	def _run(self):
		try:
			frappe.init(site=self.site, sites_path=self.sites_path)
			frappe.connect()
			frappe.set_user(self.user)
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


class TestStrategyIdempotencyEnvelope(UsabilityTestBase):
	def tearDown(self):
		super().tearDown()
		frappe.db.commit()  # the race test committed rows; their purge must commit too

	def _draft_payload(self, tag: str) -> dict:
		return {
			"title": f"Envelope plan {tag} {self.suffix}",
			"plan_role": "Primary",
			"period_start": "2050-07-01",
			"period_end": "2055-06-30",
			"effective_from": "2050-07-01",
			"effective_to": "2055-06-30",
		}

	def _journal(self, key: str):
		name = frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, "name")
		if name:
			self._cleanup.append(("Strategy Command Journal", name))
		return name

	def _created(self, out: dict) -> None:
		self._cleanup.append(("Strategic Plan Version", out["version"]["name"]))
		self._cleanup.append(("Strategic Plan", out["plan"]["plan_id"]))

	def _submitted_version(self, tag: str):
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		author, approver = self._actors(tag)
		return version, author, approver

	# ----- the key is bound to its payload ------------------------------------

	def test_same_key_with_another_payload_is_a_typed_conflict(self):
		author, _ = self._actors("c1")
		key = f"k-{uuid4().hex}"
		frappe.set_user(author)
		first = api.save_strategy_plan_draft(payload=self._draft_payload("a"), idempotency_key=key)
		self._created(first)
		with self.assertRaises(frappe.ValidationError):
			api.save_strategy_plan_draft(payload=self._draft_payload("b"), idempotency_key=key)
		self.assertIn(CONFLICT, _title(None))
		frappe.set_user("Administrator")
		self._journal(key)
		self.assertEqual(frappe.db.count("Strategic Plan", {"title": ["like", f"Envelope plan % {self.suffix}"]}), 1)

	def test_same_key_for_another_command_is_a_typed_conflict(self):
		version, author, approver = self._submitted_version("c2")
		key = f"k-{uuid4().hex}"
		token = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		frappe.set_user(author)
		submitted = api.submit_strategy_version(version, expected_version=token, idempotency_key=key)
		self.assertEqual(submitted["status"], "Submitted for approval")
		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError):
			api.approve_strategy_version(version, expected_version=submitted["expected_version"], idempotency_key=key)
		self.assertIn(CONFLICT, _title(None))
		frappe.set_user("Administrator")
		self._journal(key)
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", version, "status"), "Submitted for approval")

	def test_another_actor_replaying_a_key_is_refused_and_sees_no_result(self):
		author, _ = self._actors("c3")
		other = self._user("otherauthor")
		self._assign(other, "CAP-STRATEGY-AUTHOR")
		key = f"k-{uuid4().hex}"
		payload = self._draft_payload("c3")
		frappe.set_user(author)
		first = api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		self._created(first)
		frappe.set_user(other)
		with self.assertRaises(frappe.ValidationError):
			api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		self.assertIn(CONFLICT, _title(None))
		frappe.set_user("Administrator")
		self._journal(key)

	def test_a_caller_without_the_responsibility_gets_no_replay(self):
		"""The authorisation answers first: a user who holds no Strategy
		responsibility is refused as such, never handed a recorded result."""
		author, _ = self._actors("c4")
		nobody = self._user("nobody")
		key = f"k-{uuid4().hex}"
		payload = self._draft_payload("c4")
		frappe.set_user(author)
		first = api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		self._created(first)
		frappe.set_user(nobody)
		with self.assertRaises(frappe.ValidationError) as caught:
			api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		self.assertEqual(getattr(caught.exception, "code", ""), "AUTH_RESPONSIBILITY_REQUIRED")
		frappe.set_user("Administrator")
		self._journal(key)

	def test_replay_by_the_same_actor_returns_the_original_result_once(self):
		version, author, approver = self._submitted_version("c5")
		frappe.set_user(author)
		from kentender_strategy.services.strategy_transitions import transition_plan_version

		transition_plan_version(version, "Submit for approval")
		frappe.set_user(approver)
		token = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		key = f"k-{uuid4().hex}"
		first = api.approve_strategy_version(version, expected_version=token, idempotency_key=key)
		second = api.approve_strategy_version(version, expected_version=token, idempotency_key=key)
		frappe.set_user("Administrator")
		self._journal(key)
		self.assertEqual(second, first)
		row = frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, ["actor", "payload_hash", "action"], as_dict=True)
		self.assertEqual(row.actor, approver)
		self.assertEqual(len(row.payload_hash), 64)
		self.assertEqual(row.action, "approve_strategy_version")

	# ----- the commands require their key and version ----------------------------

	def test_a_command_without_a_key_or_expected_version_is_refused(self):
		version, author, approver = self._submitted_version("c6")
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			api.submit_strategy_version(version, expected_version="x")
		self.assertIn("STRATEGY_IDEMPOTENCY_REQUIRED", _title(None))
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			api.submit_strategy_version(version, idempotency_key=f"k-{uuid4().hex}")
		self.assertIn("STRATEGY_VERSION_REQUIRED", _title(None))
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			api.save_strategy_plan_draft(payload=self._draft_payload("c6"))
		self.assertIn("STRATEGY_IDEMPOTENCY_REQUIRED", _title(None))
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", version, "status"), "Draft")

	# ----- the race: one execution, the other returns its result -------------------

	def test_concurrent_same_key_creates_one_plan_and_both_get_its_identity(self):
		author, _ = self._actors("race")
		payload = self._draft_payload("race")
		key = f"k-{uuid4().hex}"
		frappe.db.commit()  # the user and assignment must be visible to the other connections
		try:
			conn_a = _Conn(author, lambda: api.save_strategy_plan_draft(payload=payload, idempotency_key=key), hold=True)
			self.assertTrue(conn_a.ran.wait(_WAIT))
			self.assertIsNone(conn_a.error)
			conn_b = _Conn(author, lambda: api.save_strategy_plan_draft(payload=payload, idempotency_key=key))
			self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the duplicate must wait for the first execution")
			conn_a.commit()
			self.assertTrue(conn_b.finished.wait(_WAIT))
			self.assertIsNone(conn_b.error, conn_b.error)
			self.assertEqual(conn_b.value["plan"]["plan_id"], conn_a.value["plan"]["plan_id"])
			frappe.db.commit()
			plans = frappe.get_all("Strategic Plan", filters={"title": payload["title"]}, pluck="name")
			self.assertEqual(plans, [conn_a.value["plan"]["plan_id"]])
		finally:
			frappe.db.rollback()
			for plan in frappe.get_all("Strategic Plan", filters={"title": payload["title"]}, pluck="name"):
				for version in frappe.get_all("Strategic Plan Version", filters={"plan_id": plan}, pluck="name"):
					self._cleanup.append(("Strategic Plan Version", version))
				self._cleanup.append(("Strategic Plan", plan))
			self._journal(key)
