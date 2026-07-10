#!/usr/bin/env python3
"""Run FULL_VERBATIM_SOURCE_EXTRACTION_V1_1 pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.std_extraction.constants import DATA_DIR, LAYOUT_FILENAME
from scripts.std_extraction.verbatim.extract_clauses import extract_verbatim_clauses
from scripts.std_extraction.verbatim.extract_layout import extract_layout, write_layout_file
from scripts.std_extraction.verbatim.extract_parameters import extract_verbatim_parameters
from scripts.std_extraction.verbatim.reconcile_verbatim import build_reconciliation, write_reconciliation_report


def run_verbatim_pipeline(*, layout_output: Path | None = None) -> dict:
	layout = extract_layout()
	if layout_output:
		write_layout_file(layout, layout_output)
	clauses = extract_verbatim_clauses(layout)
	parameters = extract_verbatim_parameters(layout)
	payload = build_reconciliation(clauses, parameters)
	write_reconciliation_report(payload, DATA_DIR)
	return {
		"clauses": len(clauses),
		"clauses_with_text": sum(1 for row in clauses if row.full_clause_text),
		"parameters": len(parameters),
		"parameters_with_text": sum(1 for row in parameters if row.source_text),
		"blockers": payload["summary"]["blockers"],
		"reconciliation": str(DATA_DIR / "verbatim_reconciliation.json"),
	}


if __name__ == "__main__":
	result = run_verbatim_pipeline(layout_output=DATA_DIR / LAYOUT_FILENAME)
	print(json.dumps({"status": "extracted", **result}, indent=2))
