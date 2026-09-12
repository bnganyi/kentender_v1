# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.8 §8/§9 / KT-STD-001 v1.5 §3A.6 — the technical-read
conformance gate.

Every module that exposes records to the shared Technical search
page/service registers two hooks:

  kt_technical_reference_resolvers -> [{"doctype", "label", "reference_field",
      "title_field", "status_field", "route": callable(name) -> list[str]}]
  kt_technical_read_probes -> [{"label", "call": callable, "kwargs":
      callable() -> dict | None}]

This suite proves, for a technical reader (Administrator and a plain
System-Manager-only user — never a coincidental business grant, mirroring
`AuthorizationTestCase`'s own `techie` fixture in
`kentender_core.tests.test_authorization`), that every registered probe:

  - runs without raising;
  - never reports back a denial outcome (FORBIDDEN / NO_AUTHORISED_CONTEXT /
    NOT_FOUND / DENIED) or a truthy `forbidden`;
  - never hands the caller decision authority: every `can_*` flag that is
    not itself about viewing/opening/reading/seeing must be falsy, every
    `actions`/`available_actions` entry must be a "view" action (or the list
    is empty), and every `permitted_actions` value must be falsy. The one
    documented exception is `can_retry` on Planning's publication task —
    AUTH-ADR-001 §8 explicitly grants System Manager a technical retry of
    the same approved payload, which is not a procurement decision.

A technical reader decides nothing (§3A.6) — they only ever get read access
via `kentender_core.services.authorization.is_technical`'s §8 bypass, which
is wired into `purpose=PURPOSE_READ` only, never into command authorisation.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_technical_read_conformance
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

DENIED_OUTCOMES = {"FORBIDDEN", "NO_AUTHORISED_CONTEXT", "NOT_FOUND", "DENIED"}
_VIEW_WORDS = ("view", "open", "read", "see")
_MIN_TOTAL_PROBES_EXECUTED = 20

# AUTH-ADR-001 v1.8 §8's own explicit carve-out: "A technical retry may be
# available to System Manager, but it retries the same approved payload and
# is not a procurement decision" (PLN-CHG-001 v1.16 §6, §8.2 `RetryPublication`).
# `plan_read.get_publication_task`'s `can_retry` is the one `can_*` flag this
# gate must not flag as decision authority — it is a technical action, not a
# business one, and `is_technical` is documented as gating it on purpose.
_TECHNICAL_ACTION_EXCEPTIONS = {"can_retry"}


def _is_view_like_can_key(key: str) -> bool:
	lowered = key.lower()
	return any(word in lowered for word in _VIEW_WORDS)


def _check_node(node: Any, path: str, failures: list[str]) -> None:
	"""Walk one probe's result, checking every nested dict for a denial
	outcome and every sign of decision authority handed to a technical
	reader (KT-STD-001 v1.5 §3A.6)."""
	if isinstance(node, dict):
		outcome = node.get("outcome")
		if outcome in DENIED_OUTCOMES:
			failures.append(f"{path}.outcome == {outcome!r} (denied) for a technical reader")
		if node.get("forbidden"):
			failures.append(f"{path}.forbidden == {node.get('forbidden')!r} (truthy) for a technical reader")

		for key, value in node.items():
			# A dict key need not be a string — e.g. Requisitions' validation
			# steps are keyed by step number (int). Only a string key can
			# ever spell a `can_*` decision flag.
			if (
				isinstance(key, str)
				and key.startswith("can_")
				and key not in _TECHNICAL_ACTION_EXCEPTIONS
				and not _is_view_like_can_key(key)
				and value
			):
				failures.append(f"{path}.{key} == {value!r} (truthy, non-view capability) for a technical reader")
			if key in ("actions", "available_actions") and isinstance(value, list):
				for index, entry in enumerate(value):
					if not isinstance(entry, dict):
						continue
					code = entry.get("code") or entry.get("name")
					if code and not _is_view_like_can_key(str(code)):
						failures.append(f"{path}.{key}[{index}] offers {code!r} (non-view action) to a technical reader")
			if key == "permitted_actions" and isinstance(value, dict):
				for action, allowed in value.items():
					if allowed and not (isinstance(action, str) and _is_view_like_can_key(action)):
						failures.append(f"{path}.permitted_actions.{action} == {allowed!r} (truthy) for a technical reader")
			_check_node(value, f"{path}.{key}", failures)
	elif isinstance(node, (list, tuple)):
		for index, item in enumerate(node):
			_check_node(item, f"{path}[{index}]", failures)


def _app_of(hook_path: str) -> str:
	return hook_path.split(".", 1)[0]


class TestTechnicalReadConformance(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		# A plain System-Manager-only user (`is_technical` admits Administrator
		# and any System Manager) — the same fixture-user pattern
		# `test_authorization.AuthorizationTestCase`'s own `techie` uses, so a
		# technical reader's access is never coincidental with a business
		# grant this suite happened to set up.
		cls.techie = fx.user("techread.smoke", "Techread Smoke", roles=("System Manager",))

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def _resolver_hooks() -> list[str]:
		return frappe.get_hooks("kt_technical_reference_resolvers") or []

	@staticmethod
	def _probe_hooks() -> list[str]:
		return frappe.get_hooks("kt_technical_read_probes") or []

	def test_every_app_registering_resolvers_also_registers_probes(self):
		resolver_apps = {_app_of(path) for path in self._resolver_hooks()}
		probe_apps = {_app_of(path) for path in self._probe_hooks()}
		missing = resolver_apps - probe_apps
		self.assertFalse(
			missing,
			f"app(s) registering kt_technical_reference_resolvers but no kt_technical_read_probes: {sorted(missing)}",
		)

	def test_resolvers_are_structurally_valid(self):
		for hook_path in self._resolver_hooks():
			resolvers = frappe.get_attr(hook_path)()
			self.assertIsInstance(resolvers, list, f"{hook_path} did not return a list")
			for entry in resolvers:
				doctype = entry["doctype"]
				with self.subTest(hook=hook_path, doctype=doctype):
					self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} does not exist")
					meta = frappe.get_meta(doctype)
					self.assertIsNotNone(
						meta.get_field(entry["reference_field"]),
						f"{doctype}.reference_field {entry['reference_field']!r} is not a real field",
					)
					self.assertIsNotNone(
						meta.get_field(entry["title_field"]),
						f"{doctype}.title_field {entry['title_field']!r} is not a real field",
					)
					if entry.get("status_field"):
						self.assertIsNotNone(
							meta.get_field(entry["status_field"]),
							f"{doctype}.status_field {entry['status_field']!r} is not a real field",
						)
					sample = frappe.get_all(doctype, limit=1, order_by="modified desc", pluck="name")
					name = sample[0] if sample else "DOES-NOT-EXIST"
					route = entry["route"](name)
					self.assertIsInstance(route, list, f"{doctype}.route({name!r}) did not return a list")
					self.assertTrue(route, f"{doctype}.route({name!r}) returned an empty list")
					self.assertTrue(
						all(isinstance(segment, str) for segment in route),
						f"{doctype}.route({name!r}) returned non-string segments: {route!r}",
					)

	def test_technical_readers_get_view_only_access_on_every_probe(self):
		executed_by_app: dict[str, int] = {}
		executed_total = 0
		table: list[str] = []

		for user in ("Administrator", self.techie):
			frappe.set_user(user)
			try:
				for hook_path in self._probe_hooks():
					app = _app_of(hook_path)
					probes = frappe.get_attr(hook_path)()
					self.assertIsInstance(probes, list, f"{hook_path} did not return a list")
					for probe in probes:
						label = f"{user} :: {probe['label']}"
						kwargs = probe["kwargs"]()
						if kwargs is None:
							table.append(f"{label}: SKIPPED (no fixture on this site)")
							continue
						try:
							result = probe["call"](**kwargs)
						except Exception as exc:  # noqa: BLE001 - re-raised with the probe label attached
							raise AssertionError(f"probe {label} raised {exc!r}") from exc

						failures: list[str] = []
						_check_node(result, label, failures)
						if failures:
							table.append(f"{label}: FAILED\n  " + "\n  ".join(failures))
						else:
							table.append(f"{label}: OK")
						self.assertFalse(failures, f"{label}:\n" + "\n".join(failures))

						executed_total += 1
						executed_by_app[app] = executed_by_app.get(app, 0) + 1
			finally:
				frappe.set_user("Administrator")

		report = "\n".join(table)
		registering_apps = {_app_of(path) for path in self._probe_hooks()}
		for app in registering_apps:
			self.assertGreater(
				executed_by_app.get(app, 0),
				0,
				f"every probe registered by {app} was skipped (no fixture found on this site)\n\n{report}",
			)
		self.assertGreaterEqual(
			executed_total,
			_MIN_TOTAL_PROBES_EXECUTED,
			f"only {executed_total} probe executions across both technical readers "
			f"(need >= {_MIN_TOTAL_PROBES_EXECUTED})\n\n{report}",
		)
