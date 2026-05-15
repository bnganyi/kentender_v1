# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X-02 — gate test for tender-management docs + KenTender v1 Makefile (no plain bench build).

Canonical scanner: ``frappe-bench/scripts/audit_x_02_tender_management_no_plain_bench_build.py``.
Shell wrapper: ``frappe-bench/scripts/x_02_tender_management_docs_no_plain_bench_build_gate.sh``.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


def _bench_root() -> Path:
	# .../kentender_procurement/tender_management/tests/<this file>
	return Path(__file__).resolve().parents[6]


class TestX02TenderManagementNoPlainBenchBuildGate(unittest.TestCase):
	def test_x_02_audit_script_passes(self) -> None:
		root = _bench_root()
		script = root / "scripts" / "audit_x_02_tender_management_no_plain_bench_build.py"
		self.assertTrue(script.is_file(), msg=f"missing audit script: {script}")
		proc = subprocess.run(
			[sys.executable, str(script)],
			capture_output=True,
			text=True,
			check=False,
			cwd=str(root),
		)
		self.assertEqual(
			proc.returncode,
			0,
			msg=(proc.stdout or "") + (proc.stderr or ""),
		)
