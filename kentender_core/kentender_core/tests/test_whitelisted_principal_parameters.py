"""No whitelisted function names the acting principal in its request fields.

AUD-XC-001 / AUD-XC-003 / AUTH-ADR-001 §5.5 and §15: "The client never supplies
... effective role, permitted scope or available action as authority" and "Timestamps
and actors are system-generated". A whitelisted function that takes `user=` or
`actor=` from the request and then acts as that person lets any signed-in account
act as anyone. A whitelisted endpoint acts as `frappe.session.user` only; code
that must act as an explicit principal (Planning, seeds, tests) calls an internal,
non-whitelisted service function.

Two independent scans, so neither a decorator nor an alias hides an offender:

* a static scan of every `@frappe.whitelist`-decorated function in every
  `kentender_*` app (reads source; imports nothing);
* a scan of Frappe's own registry of whitelisted callables (`frappe.whitelisted`),
  after importing every module that mentions `whitelist`, which also covers the
  `frappe.whitelist()(fn)` / wrapper forms. The signature it reads is the
  endpoint's public one (`inspect.signature` honours `__signature__`).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pathlib

import frappe
from frappe.tests import IntegrationTestCase

# Parameter names that would let a request choose who acts.
ACTING_PARAMETER_NAMES = frozenset(
	{
		"user",
		"actor",
		"acting_user",
		"acting",
		"as_user",
		"on_behalf_of",
		"principal",
		"made_by",
		"requested_by",
		"performed_by",
		"submitted_by",
		"approved_by",
		"decided_by",
		"signed_by",
		"recorded_by",
		"issued_by",
		"created_by",
	}
)

# (module, function, parameter) where the name identifies the *subject* of the
# operation, not the person performing it. The acting person is still the session
# user; the endpoint authorises that session user against the subject.
SUBJECT_NOT_ACTOR = {
	# Responsibility administration: `user` is the grantee (or the grantee of the
	# scheduled assignment being previewed/edited). The grantor is the session user
	# and is checked by `responsibility_administration`.
	("kentender_core.api.responsibility_api", "grant_responsibility", "user"),
	("kentender_core.api.responsibility_api", "update_scheduled_responsibility", "user"),
	("kentender_core.api.responsibility_api", "preview_responsibility_assignment", "user"),
	# Bid Opening: `made_by` is the speaker the Secretary records a ceremony comment for (an observer or
	# a bidder's representative), a label on the record. The actor is the session user, checked by `_call`.
	("kentender_procurement.bid_opening.api", "record_comment_for_evaluation", "made_by"),
}

# `**kwargs` endpoints: the request can carry any field, `user` included, past the signature. Each is
# reviewed here with the reason its body cannot forward a principal.
KWARGS_REVIEWED = {
	# The four Needs commands pass their kwargs through `_command_args`, which calls `_refuse_principal`
	# (departmental_needs/api.py) and covered by test_departmental_needs_principal.
	("kentender_procurement.departmental_needs.api", "save_need_draft", "**kwargs"),
	("kentender_procurement.departmental_needs.api", "return_need_revision", "**kwargs"),
	("kentender_procurement.departmental_needs.api", "accept_need_revision", "**kwargs"),
	("kentender_procurement.departmental_needs.api", "decline_need_revision", "**kwargs"),
}

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _apps() -> list[pathlib.Path]:
	return sorted(path for path in REPO_ROOT.glob("kentender_*") if (path / path.name).is_dir())


def _source_files():
	for app in _apps():
		for path in (app / app.name).rglob("*.py"):
			parts = set(path.relative_to(app).parts)
			if parts & {"tests", "node_modules", "patches"} or path.name.startswith("test_"):
				continue
			yield app, path


def _module_name(app: pathlib.Path, path: pathlib.Path) -> str:
	name = ".".join(path.relative_to(app).with_suffix("").parts)
	return name[: -len(".__init__")] if name.endswith(".__init__") else name


def _is_whitelist(node: ast.expr) -> bool:
	target = node.func if isinstance(node, ast.Call) else node
	return isinstance(target, ast.Attribute) and target.attr == "whitelist" or (
		isinstance(target, ast.Name) and target.id == "whitelist"
	)


def _acting_parameters(names) -> list[str]:
	return sorted(
		name
		for name in names
		if name in ACTING_PARAMETER_NAMES or name.endswith(("_actor", "_acting_user", "_made_by", "_requested_by"))
	)


def _is_tolerated(module: str, function: str, parameter: str) -> bool:
	return (module, function, parameter) in SUBJECT_NOT_ACTOR or (module, function, parameter) in KWARGS_REVIEWED


def static_offenders(source: str, module: str) -> list[tuple[str, str, str]]:
	found = []
	for node in ast.walk(ast.parse(source)):
		if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
			continue
		if not any(_is_whitelist(decorator) for decorator in node.decorator_list):
			continue
		arguments = node.args
		names = [a.arg for a in arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
		found += [(module, node.name, parameter) for parameter in _acting_parameters(names)]
		if arguments.kwarg is not None:
			found.append((module, node.name, f"**{arguments.kwarg.arg}"))
	return found


class TestNoWhitelistedFunctionNamesTheActingPrincipal(IntegrationTestCase):
	def test_the_static_scan_sees_a_decorated_offender(self):
		"""The scan must still see code: proved against source that commits the violation."""
		source = "import frappe\n\n@frappe.whitelist()\ndef release(reservation, actor=None):\n\tpass\n"
		self.assertEqual(static_offenders(source, "m"), [("m", "release", "actor")])
		self.assertEqual(static_offenders("def release(actor=None):\n\tpass\n", "m"), [])

	def test_the_static_scan_sees_a_kwargs_endpoint_and_the_by_named_parameters(self):
		"""RG-41: a `**kwargs` endpoint can forward `user` into a service whatever its signature says, and the
		name list must not stop at `user`/`actor`."""
		kwargs_source = "import frappe\n\n@frappe.whitelist()\ndef save(**kwargs):\n\tpass\n"
		self.assertEqual(static_offenders(kwargs_source, "m"), [("m", "save", "**kwargs")])
		for name in ("made_by", "requested_by", "performed_by", "approved_by", "submitted_by"):
			source = f"import frappe\n\n@frappe.whitelist()\ndef act({name}=None):\n\tpass\n"
			self.assertEqual(static_offenders(source, "m"), [("m", "act", name)], name)
		self.assertEqual(static_offenders("def save(**kwargs):\n\tpass\n", "m"), [])

	def test_no_decorated_whitelisted_function_takes_an_acting_user_parameter(self):
		offenders = []
		scanned = 0
		for app, path in _source_files():
			source = path.read_text()
			if "whitelist" not in source:
				continue
			scanned += 1
			module = _module_name(app, path)
			offenders += [hit for hit in static_offenders(source, module) if not _is_tolerated(*hit)]
		self.assertGreater(scanned, 20, "the scan found almost no whitelisted modules; the repo root moved")
		self.assertEqual(
			offenders,
			[],
			"a whitelisted function takes a request field that names the acting principal; act as "
			"frappe.session.user and move explicit-principal callers to an internal service function: "
			+ ", ".join(f"{m}.{f}({p})" for m, f, p in offenders),
		)

	def test_no_registered_whitelisted_callable_exposes_an_acting_user_parameter(self):
		"""Covers `frappe.whitelist()(fn)` aliases and wrappers, which no decorator scan can see."""
		for app, path in _source_files():
			if "whitelist" not in path.read_text():
				continue
			module = _module_name(app, path)
			importlib.import_module(module)
		offenders = []
		inspected = 0
		for function in list(frappe.whitelisted):
			module = getattr(function, "__module__", "") or ""
			if not module.startswith("kentender_"):
				continue
			inspected += 1
			name = getattr(function, "__name__", "")
			for parameter in _acting_parameters(inspect.signature(function).parameters):
				if not _is_tolerated(module, name, parameter):
					offenders.append((module, name, parameter))
		self.assertGreater(inspected, 100)
		self.assertEqual(
			sorted(offenders),
			[],
			"a whitelisted callable exposes a parameter that names the acting principal: "
			+ ", ".join(f"{m}.{f}({p})" for m, f, p in sorted(offenders)),
		)

	def test_the_allow_list_has_no_stale_entries(self):
		"""An entry for an endpoint that no longer takes that parameter must be deleted."""
		live = set()
		for app, path in _source_files():
			source = path.read_text()
			if "whitelist" in source:
				live |= set(static_offenders(source, _module_name(app, path)))
		self.assertEqual(sorted((SUBJECT_NOT_ACTOR | KWARGS_REVIEWED) - live), [])
