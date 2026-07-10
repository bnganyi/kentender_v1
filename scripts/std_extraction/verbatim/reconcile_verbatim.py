"""Reconcile verbatim extraction against pass registers and v1_0 synthetic package."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.std_extraction.constants import DATA_DIR, PACKAGE_ROOT_NAME
from scripts.std_extraction.verbatim.extract_clauses import SYNTHETIC_MARKER, VerbatimClause, extract_verbatim_clauses
from scripts.std_extraction.verbatim.extract_layout import extract_layout, write_layout_file
from scripts.std_extraction.verbatim.extract_parameters import VerbatimParameter, extract_verbatim_parameters


def _load_v1_clauses() -> dict[str, dict[str, Any]]:
	path = DATA_DIR / PACKAGE_ROOT_NAME / "template" / "clauses.json"
	if not path.exists():
		return {}
	payload = json.loads(path.read_text(encoding="utf-8"))
	return {row["clause_code"]: row for row in payload.get("records", [])}


def build_reconciliation(
	clauses: list[VerbatimClause] | None = None,
	parameters: list[VerbatimParameter] | None = None,
) -> dict[str, Any]:
	clauses = clauses or extract_verbatim_clauses()
	parameters = parameters or extract_verbatim_parameters()
	v1_clauses = _load_v1_clauses()
	findings: list[dict[str, Any]] = []

	for clause in clauses:
		if not clause.full_clause_text:
			findings.append(
				{
					"finding_code": "CLAUSE_TEXT_MISSING",
					"severity": "BLOCKER",
					"object_type": "STD Clause",
					"object_id": clause.clause_code,
					"description": f"No verbatim clause text extracted for {clause.clause_code}",
				}
			)
		if clause.extraction_status == "EXTRACTION_LOW_CONFIDENCE":
			findings.append(
				{
					"finding_code": "EXTRACTION_LOW_CONFIDENCE",
					"severity": "BLOCKER",
					"object_type": "STD Clause",
					"object_id": clause.clause_code,
					"description": f"Low-confidence extraction for {clause.clause_code}",
				}
			)
		if clause.register_page_start != clause.source_page_start and clause.full_clause_text:
			findings.append(
				{
					"finding_code": "ANCHOR_DRIFT",
					"severity": "WARNING",
					"object_type": "STD Clause",
					"object_id": clause.clause_code,
					"description": (
						f"Register page {clause.register_page_start} differs from PDF page "
						f"{clause.source_page_start} for {clause.clause_code}"
					),
				}
			)
		v1_row = v1_clauses.get(clause.clause_code)
		if v1_row and clause.full_clause_text and v1_row.get("full_clause_text") != clause.full_clause_text:
			if SYNTHETIC_MARKER in (v1_row.get("full_clause_text") or ""):
				findings.append(
					{
						"finding_code": "SOURCE_TEXT_MISMATCH",
						"severity": "INFO",
						"object_type": "STD Clause",
						"object_id": clause.clause_code,
						"description": f"v1_0 synthetic text replaced by PDF verbatim for {clause.clause_code}",
					}
				)
			else:
				findings.append(
					{
						"finding_code": "SOURCE_TEXT_MISMATCH",
						"severity": "WARNING",
						"object_type": "STD Clause",
						"object_id": clause.clause_code,
						"description": f"Pass-register package text differs from PDF verbatim for {clause.clause_code}",
					}
				)
		if clause.verification_status == "PENDING_LEGAL_REVIEW":
			findings.append(
				{
					"finding_code": "LEGAL_REVIEW_PENDING",
					"severity": "BLOCKER",
					"object_type": "STD Clause",
					"object_id": clause.clause_code,
					"description": f"Legal reviewer verification pending for {clause.clause_code}",
					"lifecycle_gate": "ACTIVATION",
				}
			)

	for param in parameters:
		if not param.source_text:
			findings.append(
				{
					"finding_code": "PARAMETER_SOURCE_TEXT_MISSING",
					"severity": "BLOCKER",
					"object_type": "STD Parameter",
					"object_id": param.parameter_code,
					"description": f"No verbatim parameter source text for {param.parameter_code}",
				}
			)
		if param.extraction_status == "EXTRACTION_LOW_CONFIDENCE":
			findings.append(
				{
					"finding_code": "EXTRACTION_LOW_CONFIDENCE",
					"severity": "WARNING",
					"object_type": "STD Parameter",
					"object_id": param.parameter_code,
					"description": f"Low-confidence parameter extraction for {param.parameter_code}",
				}
			)
		if param.verification_status == "PENDING_LEGAL_REVIEW":
			findings.append(
				{
					"finding_code": "LEGAL_REVIEW_PENDING",
					"severity": "BLOCKER",
					"object_type": "STD Parameter",
					"object_id": param.parameter_code,
					"description": f"Legal reviewer verification pending for {param.parameter_code}",
					"lifecycle_gate": "ACTIVATION",
				}
			)

	blockers = [row for row in findings if row.get("severity") == "BLOCKER"]
	return {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"package_version": "v1_1",
		"summary": {
			"clauses": len(clauses),
			"parameters": len(parameters),
			"findings": len(findings),
			"blockers": len(blockers),
			"activation_allowed": len(blockers) == 0,
		},
		"clauses": [clause.__dict__ for clause in clauses],
		"parameters": [param.__dict__ for param in parameters],
		"findings": findings,
	}


def write_reconciliation_report(payload: dict[str, Any], output_dir: Path | None = None) -> tuple[Path, Path]:
	output_dir = output_dir or DATA_DIR
	json_path = output_dir / "verbatim_reconciliation.json"
	md_path = output_dir / "KE-PPRA-IT-2022-04_Verbatim_Reconciliation_Report_v1_1.md"
	json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

	lines = [
		"# KE-PPRA-IT-2022-04 Verbatim Reconciliation Report v1.1",
		"",
		f"**Generated:** {payload['generated_at']}",
		"",
		"## Summary",
		"",
		f"- Clauses extracted: {payload['summary']['clauses']}",
		f"- Parameters extracted: {payload['summary']['parameters']}",
		f"- Findings: {payload['summary']['findings']}",
		f"- Blockers: {payload['summary']['blockers']}",
		f"- Activation allowed: {payload['summary']['activation_allowed']}",
		"",
		"## Blocker findings",
		"",
	]
	blockers = [row for row in payload["findings"] if row.get("severity") == "BLOCKER"]
	if not blockers:
		lines.append("- None")
	else:
		for row in blockers[:50]:
			lines.append(f"- **{row['finding_code']}** — {row['object_id']}: {row['description']}")
		if len(blockers) > 50:
			lines.append(f"- ... and {len(blockers) - 50} more")
	lines.append("")
	md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
	return json_path, md_path


def run_reconciliation(layout_output: Path | None = None) -> dict[str, Any]:
	layout = extract_layout()
	if layout_output:
		write_layout_file(layout, layout_output)
	payload = build_reconciliation(
		extract_verbatim_clauses(layout),
		extract_verbatim_parameters(layout),
	)
	write_reconciliation_report(payload)
	return payload
