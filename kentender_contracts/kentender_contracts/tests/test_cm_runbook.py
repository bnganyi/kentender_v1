# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RUNBOOKS.md names only things that exist (plan Phase 12, tracker CM8-1205): every `make` target is a target of the Makefile and every dotted function or module is importable, so a rename fails here and not in
the middle of a recovery."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

ROOT = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1]
RUNBOOK = ROOT / "docs/mvp-1-r1/21_contract_management/RUNBOOKS.md"


class TestTheRunbookNamesRealThings(IntegrationTestCase):
	def text(self) -> str:
		return RUNBOOK.read_text()

	def test_every_make_target_is_a_target_of_the_makefile(self):
		targets = set(re.findall(r"^([A-Za-z0-9_.-]+):", (ROOT / "Makefile").read_text(), re.M))
		named = set(re.findall(r"`make ([a-z0-9-]+)", self.text()))
		self.assertTrue(named, "the runbook names make targets")
		self.assertEqual(sorted(named - targets), [], "a make target the runbook names does not exist")

	def test_every_dotted_function_and_module_is_importable(self):
		named = set(re.findall(r"`((?:kentender_contracts|kentender_core)\.[a-z_.]+)`", self.text()))
		self.assertTrue(named)
		missing = []
		for dotted in sorted(named):
			parts = dotted.split(".")
			for cut in range(len(parts), 0, -1):  # the longest importable module prefix, then the attributes after it
				try:
					found = importlib.import_module(".".join(parts[:cut]))
				except ImportError:
					continue
				for attr in parts[cut:]:
					found = getattr(found, attr, None)
				if found is None:
					missing.append(dotted)
				break
			else:
				missing.append(dotted)
		self.assertEqual(missing, [])

	def test_the_switches_the_runbook_names_are_read_by_the_code(self):
		code = "\n".join(p.read_text() for p in (ROOT / "kentender_contracts/kentender_contracts").rglob("*.py") if "/tests/" not in p.as_posix())
		for switch in re.findall(r"`(kt_[a-z_]+)", self.text()):
			self.assertIn(switch, code, f"{switch} is not read anywhere")
