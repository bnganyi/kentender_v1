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
		"Needs Intake Window",
		"Need Planning Usage Projection",
	}
)

RETIRED_DOCTYPES = ("Departmental Need Item", "Departmental Need Attachment", "Departmental Need Review")

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


def strip_python(source: str) -> str:
	"""Python source with comments and string literals removed."""
	return "".join(
		token.string
		for token in tokenize.generate_tokens(io.StringIO(source).readline)
		if token.type not in (tokenize.COMMENT, tokenize.STRING)
	)


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
		"""Both strippers must blank prose and keep code.

		Without this, a stripper that returned "" would make every scan above
		pass regardless of what the module contains — the failure mode caught
		twice already in this rebuild.
		"""
		py = strip_python(
			'"""Departmental Review Delegate is removed by §1.1."""\n'
			'ROLE = "Departmental Review Delegate"\n'
			"CALL = frappe.get_all\n"
		)
		self.assertNotIn("removed by", py, msg="docstring must be stripped")
		self.assertNotIn("Departmental Review Delegate", py, msg="string literal must be stripped")
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
