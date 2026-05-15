# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X-03 — doc 9 §23.4 acceptance sequence documentation gate."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


def _bench_root() -> Path:
	return Path(__file__).resolve().parents[6]


class TestX03Doc9Section234AcceptanceSequenceGate(unittest.TestCase):
	def test_x_03_audit_script_passes(self) -> None:
		root = _bench_root()
		script = root / "scripts" / "audit_x_03_doc9_section_23_4_acceptance_sequence.py"
		self.assertTrue(script.is_file(), msg=f"missing audit script: {script}")
		proc = subprocess.run(
			[sys.executable, str(script)],
			capture_output=True,
			text=True,
			check=False,
			cwd=str(root),
		)
		self.assertEqual(proc.returncode, 0, msg=(proc.stdout or "") + (proc.stderr or ""))

