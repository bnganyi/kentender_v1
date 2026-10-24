"""Hold the line on the shared record picker (AGENTS.md section 6.12): a person or a record chosen from a list that can
grow is the picker, never a plain `<select>`. This reads every Vue template in the repository and fails on a `<select>`
whose options come from a list named like people, users, members, holders, candidates, units or departments, unless
the choice is on `ALLOWED` with the reason it may stay a dropdown. It also fails on an `ALLOWED` entry that no longer
matches anything, so the register cannot rot.

A short fixed vocabulary (a role, a status, a country) is not named like this and is never flagged.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_record_picker_guard
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import frappe

# A list named like one of these is a choice of a person or a record.
NAMED_LIKE_RECORDS = re.compile(
	r"candidate|people|person|user|member|holder|officer|assignee|supplier|unit|department|organisation|org_unit|approver|reviewer|delegate|bidder|vendor",
	re.IGNORECASE,
)
SELECT = re.compile(r"<select\b[^>]*>(.*?)</select>", re.DOTALL)
OPTIONS_FROM = re.compile(r'v-for="\s*\(?\s*[\w, ]+\)?\s+in\s+([^"]+?)\s*"')
SKIPPED = ("node_modules", "/dist/", "archive/", "test-results", "playwright-report", "/.git/")

#: (file, list expression) -> why it may stay a plain dropdown. Add an entry only with a reason a reviewer can check.
ALLOWED: dict[tuple[str, str], str] = {
	("kentender_procurement/kentender_procurement/public/js/bid_portal/screens/CompanyTaskScreen.vue", "data.contact.people"):
		"the bidder's own company's few contacts, on the public portal",
	("kentender_procurement/kentender_procurement/public/js/procurement_meetings/ProcurementMeetings.vue", "data.options.departments"):
		"a filter over the departments that appear in the meetings the reader can already see",
	("kentender_procurement/kentender_procurement/public/js/procurement_requisitions/components/WorkspaceScreen.vue", "options.departments || []"):
		"a filter over the reader's own departments (\"All my departments\"); revisit if a reader can see more than about a dozen",
	("kentender_procurement/kentender_procurement/public/js/bid_opening/screens/OpenBidsScreen.vue", "members"):
		"chosen from the opening committee already on the screen (who repeats a request, who reads aloud)",
	("kentender_procurement/kentender_procurement/public/js/departmental_needs/components/NeedEditorScreen.vue", "departmentChoices"):
		"the departments the reader may write needs for; the control appears only when there is more than one",
	("kentender_procurement/kentender_procurement/public/js/departmental_needs/components/NeedEditorScreen.vue", "units"):
		"units of measure (each, box, litre): a short catalogue the reader can extend, not organisation units",
	("kentender_procurement/kentender_procurement/public/js/procurement_planning/components/DppEntryEditorScreen.vue", "editor.units || []"):
		"units of measure (each, box, litre), as on the departmental need",
}


def repository_root() -> Path:
	return Path(frappe.get_app_path("kentender_core")).resolve().parents[1]


def flagged(text: str) -> list[str]:
	"""The list expressions a template feeds a `<select>` from, that are named like people or records."""
	out = []
	for select in SELECT.finditer(text):
		for source in OPTIONS_FROM.finditer(select.group(1)):
			if NAMED_LIKE_RECORDS.search(source.group(1)):
				out.append(source.group(1))
	return out


def scan(root: Path) -> list[tuple[str, str]]:
	found: list[tuple[str, str]] = []
	for path in sorted(root.rglob("*.vue")):
		rel = path.relative_to(root).as_posix()
		if any(part in f"/{rel}" for part in SKIPPED):
			continue
		found += [(rel, expression) for expression in flagged(path.read_text(encoding="utf-8"))]
	return found


class TestTheGuardItself(unittest.TestCase):
	"""The red half: what it flags and what it leaves alone."""

	def test_a_select_over_a_people_list_is_flagged(self):
		self.assertEqual(flagged('<select v-model="x"><option v-for="c in candidates" :key="c.user">{{ c.name }}</option></select>'), ["candidates"])
		self.assertEqual(flagged('<select><option v-for="u in options.organisation_units" :value="u.id">{{ u.label }}</option></select>'), ["options.organisation_units"])
		self.assertEqual(flagged('<select><option v-for="(m, i) in members" :key="i">x</option></select>'), ["members"])

	def test_a_short_fixed_vocabulary_is_not_flagged(self):
		self.assertEqual(flagged('<select><option v-for="r in roles" :key="r">{{ r }}</option></select>'), [])
		self.assertEqual(flagged('<select><option v-for="s in statuses" :key="s">{{ s }}</option></select>'), [])
		self.assertEqual(flagged('<select><option v-for="c in countries" :key="c">{{ c }}</option></select>'), [])

	def test_a_list_outside_a_select_is_not_flagged(self):
		self.assertEqual(flagged('<ul><li v-for="m in members" :key="m">{{ m }}</li></ul>'), [])


class TestNoNewDropdownOverPeopleOrRecords(unittest.TestCase):
	def test_every_such_dropdown_in_the_repository_is_allowed_with_a_reason(self):
		unexpected = sorted(set(scan(repository_root())) - set(ALLOWED))
		self.assertEqual(
			unexpected,
			[],
			"A <select> is fed from a list named like people or records. Choose a person or a record from a list that can grow with the shared "
			"record picker (AGENTS.md section 6.12). If the list is genuinely short and fixed, add it to ALLOWED in this file with the reason.\n"
			+ "\n".join(f"  {path}: {expression}" for path, expression in unexpected),
		)

	def test_the_allowed_register_has_no_stale_entry(self):
		found = set(scan(repository_root()))
		stale = sorted(set(ALLOWED) - found)
		self.assertEqual(stale, [], "These ALLOWED entries match no template any more (the dropdown was removed, renamed or became the picker): delete them.\n"
			+ "\n".join(f"  {path}: {expression}" for path, expression in stale))

	def test_every_allowed_entry_gives_a_reason(self):
		self.assertTrue(all(reason.strip() for reason in ALLOWED.values()))
