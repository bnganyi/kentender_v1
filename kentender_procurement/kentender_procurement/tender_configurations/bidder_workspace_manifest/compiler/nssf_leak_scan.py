# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Test utility: forbid NSSF calibration literals outside fixture/test paths."""

from __future__ import annotations

import re
from pathlib import Path

# Literals that must not appear in compiler production code (fixture-only).
_FORBIDDEN = re.compile(
	r"("
	r"BWMF-CAL-NSSF-ERP-001-V1|"
	r"NSSFSPS/ICT/ERP|"
	r"CAL-NSSF-NSSFSPS|"
	r"461ffc824759f767|"
	r"b3bbc3f304563832|"
	r"Professional Indemnity|"
	r"National Social Security Fund Staff Pension"
	r")"
)

_ALLOWED_PATH_PARTS = (
	"/fixtures/",
	"/tests/",
	"nssf_fixture_errata.py",
	"nssf_leak_scan.py",
	"test_bwmf_",
)


def scan_tree_for_nssf_leaks(root: Path) -> list[str]:
	"""Return list of ``path:line:match`` for forbidden literals outside allowlist paths."""
	hits: list[str] = []
	for path in sorted(root.rglob("*.py")):
		text_path = str(path)
		if any(p in text_path for p in _ALLOWED_PATH_PARTS):
			continue
		try:
			content = path.read_text(encoding="utf-8")
		except OSError:
			continue
		for i, line in enumerate(content.splitlines(), start=1):
			m = _FORBIDDEN.search(line)
			if m:
				hits.append(f"{path}:{i}:{m.group(1)}")
	return hits
