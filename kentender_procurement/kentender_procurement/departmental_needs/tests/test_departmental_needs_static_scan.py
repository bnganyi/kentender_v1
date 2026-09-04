"""NDS-901 — §16.3 schema scan: every prohibited field, object and route is absent.

§16.3 requires release evidence that the prohibited surface does not exist.
`test_departmental_needs_domain_model` already asserts this for the *root*
doctype; this module widens it to the whole module — every Needs DocType's
fields, the retired objects as definitions on disk rather than only as rows in
this site's database, the retired roles, the removed `Partially included`
projection value, and the legacy routes.

Two scanning rules learned the hard way in Phases 5, 8 and 9, and applied here:

- Never text-scan Python or JS source for a prohibited name without stripping
  comments and strings first. These modules *document* what they exclude, so a
  raw scan fires on the prose that states the rule.
- Never trust a stripper without proving it still sees code. Every scan below is
  exercised against synthetic source that commits the violation.

Schema assertions read DocType meta and the JSON on disk, which carry no prose,
so they need no stripping.
"""

from __future__ import annotations

import ast
import io
import json
import pathlib
import tokenize

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.services import lifecycle

MODULE = pathlib.Path(lifecycle.__file__).parents[1]

# §4 — the complete object set. Anything else under doctype/ is a leftover.
PERMITTED_DOCTYPES = frozenset(
	{
		"Departmental Need",
		"Departmental Need Version",
		"Departmental Need Decision",
		"Departmental Need Review Task",
		"Departmental Need Event",
		"Need Withdrawal Request",
		"Need Planning Usage Projection",
	}
)

RETIRED_DOCTYPES = (
	"Departmental Need Item",
	"Departmental Need Attachment",
	"Departmental Need Review",
	"Needs Intake Window",
)

# AUTH-ADR-001 v1.6 §1.1 / NDS-CHG-001 v1.6 §4 — doctypes this module retargeted
# away from onto ERPNext natives (D4/D5/D6). Neither the module's own DocTypes
# nor its source may still name or link to these.
RETIRED_LINK_TARGETS = ("Financial Year", "Unit Of Measure", "PE Fiscal Year Context")

# §1.1 and §2.1 — no Needs DocType may carry any of these, under any name.
PROHIBITED_FIELDS = (
	"business_justification",
	"delivery_or_use_location",
	"delivery_location",
	"indicative_cost",
	"estimated_cost",
	"unit_price",
	"currency",
	"funding_source",
	"budget_line",
	"other_unit",
	"strategic_objective",
	"strategy",
	"requirement_type",
	"procurement_category",
	"procurement_method",
	"attachment",
	"attachments",
	"source_reference",
	"authority_reference",
	"evidence",
	"notes",
	"contact",
	"pe_fy_context",
	"score",
	"completion_percentage",
	"procuring_entity",
)

# §1.1 — removed roles. `Departmental Need Requester` is the pre-v1.1 name of
# what is now `Departmental Author`.
RETIRED_ROLES = (
	"Departmental Review Delegate",
	"Needs Configuration Manager",
	"Departmental Need Requester",
)

# §1.1 — the projection is only Not included or Fully included.
REMOVED_USAGE_VALUE = "Partially included"

# §1.1 / NDS-AC-030 — replaced outright, with no redirect or alias.
LEGACY_ROUTES = (
	"departmental-needs-new",
	"departmental-needs-edit",
	"departmental-needs-review",
	"departmental-needs-detail",
	"demands-workspace",
	"demand-form",
	"demand-review",
	"demand-detail",
	"demand-performance",
)


def _docstring_positions(source: str) -> set[tuple[int, int]]:
	"""(line, col) of every module/class/function docstring's STRING token.

	A docstring is just a bare string-literal expression statement in the
	`ast` sense — nothing marks it as a token. Positions let the tokenizer
	pass below blank exactly those, and no other string literal.
	"""
	tree = ast.parse(source)
	nodes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
	positions = set()
	for node in nodes:
		body = getattr(node, "body", None)
		if not body:
			continue
		first = body[0]
		if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
			positions.add((first.value.lineno, first.value.col_offset))
	return positions


def strip_python(source: str) -> str:
	"""Python source with comments and docstrings removed.

	Ordinary string literals (a doctype name passed to ``frappe.get_all``, a
	role name in a filter dict) are kept. An earlier version of this stripper
	removed every STRING token, which also erased the very string literals
	the scans below exist to catch — a doctype or role name almost never
	appears as a bare Python identifier, only as a quoted argument. That made
	every source scan in this file vacuous against the realistic violation.
	Confirmed by testing the old stripper directly: it silently ate
	``"User Permission"`` out of a call it was supposed to flag.
	"""
	doc_positions = _docstring_positions(source)
	out = []
	for token in tokenize.generate_tokens(io.StringIO(source).readline):
		if token.type == tokenize.COMMENT:
			continue
		if token.type == tokenize.STRING and token.start in doc_positions:
			continue
		out.append(token.string)
	return "".join(out)


def strip_js(source: str) -> str:
	"""JS/Vue source with // and /* */ comments blanked, strings preserved.

	Strings stay because a route or class name in JS is usually *in* a string —
	blanking them would make the scan vacuous. Comments go because that is where
	the prose lives.
	"""
	out: list[str] = []
	i, n = 0, len(source)
	quote: str | None = None
	while i < n:
		ch = source[i]
		if quote:
			out.append(ch)
			if ch == "\\" and i + 1 < n:
				out.append(source[i + 1])
				i += 2
				continue
			if ch == quote:
				quote = None
			i += 1
			continue
		if ch in "\"'`":
			quote = ch
			out.append(ch)
			i += 1
			continue
		if ch == "/" and i + 1 < n and source[i + 1] == "/":
			while i < n and source[i] != "\n":
				out.append(" ")
				i += 1
			continue
		if ch == "/" and i + 1 < n and source[i + 1] == "*":
			end = source.find("*/", i + 2)
			end = n if end == -1 else end + 2
			out.append("".join(" " if c != "\n" else "\n" for c in source[i:end]))
			i = end
			continue
		out.append(ch)
		i += 1
	return "".join(out)


def _python_sources() -> list[tuple[str, str]]:
	return [
		(str(p.relative_to(MODULE)), p.read_text())
		for p in sorted(MODULE.rglob("*.py"))
		if "tests" not in p.parts and "__pycache__" not in p.parts
	]


def _client_sources() -> list[tuple[str, str]]:
	root = MODULE.parents[0] / "public"
	files = list((root / "js" / "departmental_needs").rglob("*.vue"))
	files += list((root / "js" / "departmental_needs").rglob("*.js"))
	files += [root / "js" / "departmental_needs_page.js"]
	return [(str(p.relative_to(root)), p.read_text()) for p in sorted(files) if p.exists()]


class DepartmentalNeedsSchemaScanTest(IntegrationTestCase):
	"""§16.3 — the prohibited surface is absent from the schema."""

	def test_no_needs_doctype_carries_a_prohibited_field(self):
		offenders = []
		for doctype in sorted(PERMITTED_DOCTYPES):
			if not frappe.db.exists("DocType", doctype):
				self.fail(f"{doctype} is part of §4 but missing from the site")
			fields = {f.fieldname for f in frappe.get_meta(doctype).fields}
			offenders += [f"{doctype}.{name}" for name in PROHIBITED_FIELDS if name in fields]
		self.assertEqual(offenders, [], msg="§1.1/§2.1 prohibit these fields outright")

	def test_no_needs_doctype_links_to_a_retired_doctype(self):
		"""D4/D5/D6 — no Link field may target the doctypes this module
		retargeted away from: the custom Financial Year/Unit Of Measure, or
		PE Fiscal Year Context. Reads real DocType meta, not source text."""
		offenders = []
		for doctype in sorted(PERMITTED_DOCTYPES):
			for field in frappe.get_meta(doctype).fields:
				if field.fieldtype == "Link" and field.options in RETIRED_LINK_TARGETS:
					offenders.append(f"{doctype}.{field.fieldname} -> {field.options}")
		self.assertEqual(offenders, [], msg="a Link field still targets a retired doctype")

	def test_the_module_defines_exactly_the_section_4_doctypes(self):
		"""On disk, not just in this database.

		A retired doctype's row can be dropped by a patch while its JSON stays
		in the tree — and `bench migrate` syncs DocTypes *from disk*, so the
		definition would simply come back on the next migrate, on this site or
		a fresh one.
		"""
		defined = {
			json.loads(path.read_text())["name"]
			for path in (MODULE / "doctype").rglob("*.json")
			if path.stem == path.parent.name
		}
		self.assertEqual(defined, set(PERMITTED_DOCTYPES))
		for doctype in RETIRED_DOCTYPES:
			with self.subTest(doctype=doctype):
				self.assertNotIn(doctype, defined, msg="retired definition still on disk")
				self.assertFalse(frappe.db.exists("DocType", doctype))

	def test_partially_included_is_gone_from_the_projection(self):
		options = frappe.get_meta("Need Planning Usage Projection").get_field("usage").options
		values = [line.strip() for line in (options or "").split("\n") if line.strip()]
		self.assertEqual(values, ["Not included", "Fully included"])
		self.assertNotIn(REMOVED_USAGE_VALUE, options or "")

	def test_retired_roles_exist_nowhere(self):
		for role in RETIRED_ROLES:
			with self.subTest(role=role):
				self.assertFalse(
					frappe.db.exists("Role", role),
					msg=f"{role} is removed by §1.1",
				)
				assigned = frappe.get_all("Has Role", filters={"role": role}, limit=1)
				self.assertEqual(assigned, [], msg=f"{role} is still assigned to a user")


class DepartmentalNeedsSourceScanTest(IntegrationTestCase):
	"""§16.3 — the prohibited surface is absent from the module's own code."""

	def test_module_python_names_no_retired_role(self):
		offenders = [
			f"{relative}: {role}"
			for relative, source in _python_sources()
			for role in RETIRED_ROLES
			if role in strip_python(source)
		]
		self.assertEqual(offenders, [], msg="a retired role name survives in module code")

	def test_module_python_names_no_legacy_route(self):
		offenders = [
			f"{relative}: {route}"
			for relative, source in _python_sources()
			for route in LEGACY_ROUTES
			if route in strip_python(source)
		]
		self.assertEqual(offenders, [], msg="NDS-AC-030 — no legacy route, alias or redirect")

	def test_module_python_names_no_retired_link_target(self):
		offenders = [
			f"{relative}: {name}"
			for relative, source in _python_sources()
			for name in RETIRED_LINK_TARGETS
			if name in strip_python(source)
		]
		self.assertEqual(offenders, [], msg="D4/D5/D6 — a retired doctype name survives in module code")

	def test_module_python_names_no_user_permission_authority_read(self):
		"""NDS-AC-044 — the resolver, not `frappe.get_all("User Permission", ...)`."""
		offenders = [
			relative
			for relative, source in _python_sources()
			if "User Permission" in strip_python(source)
		]
		self.assertEqual(offenders, [], msg="a parallel User Permission read survives in module code")

	def test_client_bundle_names_no_legacy_route_or_removed_value(self):
		offenders = []
		for relative, source in _client_sources():
			code = strip_js(source)
			offenders += [f"{relative}: {route}" for route in LEGACY_ROUTES if route in code]
			if REMOVED_USAGE_VALUE in code:
				offenders.append(f"{relative}: {REMOVED_USAGE_VALUE}")
		self.assertEqual(offenders, [], msg="the client still references a removed route or value")

	def test_the_module_exposes_no_attachment_surface(self):
		"""§1.1 removes supporting attachments; §2.1 repeats it as an exclusion."""
		offenders = []
		for relative, source in _python_sources():
			code = strip_python(source)
			for token in ("attach_file", "File", "attachments"):
				if token == "File":
					# Match the doctype access specifically, not the word.
					if 'get_doc("File"' in source or "'File'" in code:
						offenders.append(f"{relative}: File doctype")
					continue
				if token in code:
					offenders.append(f"{relative}: {token}")
		self.assertEqual(offenders, [], msg="no attachment surface may exist in this module")

	def test_the_scans_are_not_vacuous(self):
		"""The Python stripper must blank prose but keep real code strings.

		Without this, a stripper that returned "" would make every scan above
		pass regardless of what the module contains — the failure mode caught
		twice already in this rebuild. An earlier version of `strip_python`
		blanked *every* string literal, including the ones the scans exist to
		catch (a doctype or role name is realistically only ever a quoted
		argument, never a bare identifier) — that regression is exactly what
		the second assertion below now guards against.
		"""
		py = strip_python(
			'"""Departmental Review Delegate is removed by §1.1."""\n'
			'ROLE = "Departmental Review Delegate"\n'
			"CALL = frappe.get_all\n"
		)
		self.assertNotIn("removed by", py, msg="docstring must be stripped")
		self.assertIn("Departmental Review Delegate", py, msg="a real string-literal violation must survive")
		self.assertIn("frappe.get_all", py, msg="code must survive stripping")

		js = strip_js(
			"// departmental-needs-edit is retired\n"
			'const route = "departmental-needs-edit";\n'
		)
		self.assertNotIn("retired", js, msg="comment must be blanked")
		self.assertIn("departmental-needs-edit", js, msg="string literal must survive in JS")

		# And the real inputs are non-empty, so the scans have something to read.
		self.assertGreater(len(_python_sources()), 15)
		self.assertGreater(len(_client_sources()), 15)
