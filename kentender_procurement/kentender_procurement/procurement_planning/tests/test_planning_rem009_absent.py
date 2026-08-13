# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-REM-009 — no active Submission / contribution / OU_SIGNOFF writers."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase

PLANNING_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_WRITERS = (
	"submit_departmental_contribution",
	"get_departmental_contribution",
	"Departmental Submission",
	"OU_SIGNOFF",
	"contribution_drawer",
)

# Absence tests, layout forbids, and DTO stub keys may mention removed terms.
ALLOW_PATH_PARTS = (
	"test_planning_contribution_absent.py",
	"test_planning_rem009_absent.py",
	"test_planning_ui_stitch_layout_guard.py",
	"test_planning_mvp_seed_contract.py",
	"c02_drop_departmental_submission",
)


def _allowed(path: Path) -> bool:
	text = str(path)
	return any(part in text for part in ALLOW_PATH_PARTS)


class TestPlanningRem009Absent(UnitTestCase):
	def test_no_active_contribution_writers(self) -> None:
		hits: list[str] = []
		for path in PLANNING_ROOT.rglob("*"):
			if not path.is_file():
				continue
			if path.suffix not in {".py", ".js", ".json", ".html", ".css"}:
				continue
			if _allowed(path):
				continue
			try:
				body = path.read_text(encoding="utf-8")
			except OSError:
				continue
			for token in FORBIDDEN_WRITERS:
				if token not in body:
					continue
				# DTO stub / comment-only mentions are allowed.
				if token == "Departmental Submission" and any(
					marker in body.lower()
					for marker in (
						"not exist",
						"removed",
						"no departmental",
						"c02:",
					)
				):
					continue
				rel = path.relative_to(PLANNING_ROOT)
				hits.append(f"{rel}: {token}")
		self.assertEqual(hits, [], msg="Active contribution/OU_SIGNOFF writers:\n" + "\n".join(hits))
