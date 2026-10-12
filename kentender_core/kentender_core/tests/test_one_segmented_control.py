# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One segmented control (Yes/No, Permanent/Acting ...): the design pack's `.seg` / `.seg-opt`, defined once in the shared
Industry stylesheet and used by every screen.

Why a guard: the control had grown four definitions — the pack's, a legacy `.kt-seg.kt-seg-inline` that inherited the 12 px
height of the old colour-swatch bar (so its labels were clipped on every screen that used it), an override in the admin
configuration stylesheet that restyled every `.seg-opt` site-wide, and copies named for their module (`tnd-seg`, `pln-seg`).
Each module fixed its own copy, and the same defect came back in the next one. A new screen must use `seg` / `seg-opt`.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_one_segmented_control
"""

from __future__ import annotations

import re
from pathlib import Path

from frappe.tests import IntegrationTestCase

REPO = Path(__file__).resolve().parents[3]
SHARED = REPO / "kentender_core/kentender_core/public/css/kt_industry_tokens.css"
SKIP = ("node_modules", "/dist/", "/test-results/", "/archive/", "/retired/")

# `seg`, `seg-opt` and a module-prefixed copy of either (`tnd-seg-opt`) or the legacy inline variant (`kt-seg-inline`).
# `kt-seg` alone is the old colour-swatch bar, a different component; `*-seg-select` is a select, not this control.
COPY = re.compile(r"(?<![\w-])(?:[a-z]{2,4}-seg(?:-opt|-inline)?|seg-inline)(?![\w-])")


def _sources(*suffixes: str):
	for path in REPO.rglob("*"):
		if path.suffix in suffixes and path.is_file() and not any(part in path.as_posix() for part in SKIP):
			yield path


def _is_copy(token: str) -> bool:
	return bool(COPY.fullmatch(token)) and token != "kt-seg"


class TestOneSegmentedControl(IntegrationTestCase):
	def test_the_shared_stylesheet_defines_the_control_and_no_legacy_variant(self):
		css = re.sub(r"/\*.*?\*/", "", SHARED.read_text(encoding="utf-8"), flags=re.S)
		for selector in (".kt-industry .seg ", ".kt-industry .seg-opt ", ".kt-industry .seg-opt:has(input:checked)", ".kt-industry .seg-opt.is-disabled"):
			self.assertIn(selector, css, f"the shared stylesheet must define {selector.strip()}")
		self.assertNotIn("kt-seg-inline", css, "the legacy inline variant (it inherits the swatch bar's 12 px height) is gone")

	def test_no_other_stylesheet_defines_a_segmented_control(self):
		offenders = []
		for path in _sources(".css"):
			if path == SHARED or "docs/" in path.as_posix() or "/scripts/" in path.as_posix():
				continue
			css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8", errors="ignore"), flags=re.S)
			for token in re.findall(r"\.((?:[a-z]{2,4}-)?seg(?:-opt|-inline)?)(?![\w-])", css):
				if token in ("seg", "seg-opt") or _is_copy(token):
					offenders.append(f"{path.relative_to(REPO)}: .{token}")
		self.assertEqual(offenders, [], "a module must not restyle or copy the shared segmented control")

	def test_no_screen_uses_a_legacy_or_module_copy_of_the_control(self):
		offenders = []
		attr = re.compile(r"""(?:\bclass(?:Name)?\s*[=:]\s*|:class\s*=\s*)["'`]([^"'`]*)["'`]""")
		for path in _sources(".vue", ".js"):
			if path.name.endswith(".spec.js") or "/tests/" in path.as_posix():
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
			for match in attr.finditer(text):
				for token in match.group(1).split():
					if _is_copy(token):
						offenders.append(f"{path.relative_to(REPO)}: {token}")
		self.assertEqual(offenders, [], "use the shared `seg` / `seg-opt`")
