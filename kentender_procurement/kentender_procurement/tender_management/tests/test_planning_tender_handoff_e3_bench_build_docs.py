# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""§E E3 — planning-to-tender-handoff docs must not instruct plain ``bench build``.

Implements **IMPLEMENTATION_TRACKER §E** row E3 (repo rule / ``frappe-bench-node``).

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_e3_bench_build_docs
"""

from __future__ import annotations

import re
from pathlib import Path

from frappe.tests import IntegrationTestCase

_HANDOFF_DIR = (
	Path(__file__).resolve().parents[4]
	/ "docs"
	/ "prompts"
	/ "planning-to-tender-handoff"
)
_BENCH_BUILD = re.compile(r"\bbench\s+build\b", re.IGNORECASE)
_BENCH_WATCH = re.compile(r"\bbench\s+watch\b", re.IGNORECASE)


class TestPlanningTenderHandoffE3BenchBuildDocs(IntegrationTestCase):
	def test_e3_planning_handoff_markdown_has_no_plain_bench_build_lines(self) -> None:
		self.assertTrue(
			_HANDOFF_DIR.is_dir(),
			f"expected handoff doc dir {_HANDOFF_DIR}",
		)
		violations: list[str] = []
		for path in sorted(_HANDOFF_DIR.glob("*.md")):
			text = path.read_text(encoding="utf-8")
			for lineno, line in enumerate(text.splitlines(), 1):
				if not _BENCH_BUILD.search(line) and not _BENCH_WATCH.search(line):
					continue
				lower = line.lower()
				if "bench-with-node" in lower or "bench_with_node" in lower:
					continue
				if path.name == "IMPLEMENTATION_TRACKER.md" and line.strip().startswith("| E3 "):
					continue
				violations.append(f"{path.name}:{lineno}:{line.strip()}")
		self.assertEqual(
			violations,
			[],
			"plain bench build/watch instructions must use ./scripts/bench-with-node.sh; violations:\n"
			+ "\n".join(violations),
		)
