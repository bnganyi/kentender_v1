"""Parse extraction pass markdown tables into structured registers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.std_extraction.constants import DOCS_STD_PROD


@dataclass(frozen=True)
class LockedClauseRegister:
	internal_id: str
	visible_number: str
	title: str
	page_anchor: str
	engine_note: str
	section: str  # ITT or GCC


def _parse_locked_clause_table(content: str, section: str) -> list[LockedClauseRegister]:
	rows: list[LockedClauseRegister] = []
	in_table = False
	for line in content.splitlines():
		if line.startswith("| Internal ID |"):
			in_table = True
			continue
		if not in_table:
			continue
		if not line.startswith("|"):
			if rows:
				break
			continue
		if line.startswith("| ---") or line.startswith("|---"):
			continue
		cells = [cell.strip() for cell in line.strip("|").split("|")]
		if len(cells) < 6:
			continue
		internal_id, visible_no, title, page_anchor, _treatment, note = cells[:6]
		if not internal_id or internal_id == "Internal ID":
			continue
		rows.append(
			LockedClauseRegister(
				internal_id=internal_id,
				visible_number=visible_no,
				title=title,
				page_anchor=page_anchor,
				engine_note=note,
				section=section,
			)
		)
	return rows


def load_locked_clauses() -> list[LockedClauseRegister]:
	pass1 = (DOCS_STD_PROD / "STD_IT_Full_Source_Extraction_Pass_1.md").read_text(encoding="utf-8")
	itt_section = pass1.split("## 5. Locked ITT clause register", 1)[1].split("## 6.", 1)[0]
	gcc_section = pass1.split("## 6. Locked GCC clause register", 1)[1].split("## 7.", 1)[0]
	return _parse_locked_clause_table(itt_section, "ITT") + _parse_locked_clause_table(gcc_section, "GCC")


@dataclass(frozen=True)
class SectionRegister:
	engine_id: str
	source_section: str
	mutability: str
	page_anchor: str


def load_sections() -> list[SectionRegister]:
	pass1 = (DOCS_STD_PROD / "STD_IT_Full_Source_Extraction_Pass_1.md").read_text(encoding="utf-8")
	section_block = pass1.split("## 4. Section/source anchor map", 1)[1].split("## 5.", 1)[0]
	rows: list[SectionRegister] = []
	for line in section_block.splitlines():
		if not line.startswith("|"):
			continue
		if line.startswith("| ---") or "Engine section ID" in line:
			continue
		cells = [cell.strip() for cell in line.strip("|").split("|")]
		if len(cells) < 5:
			continue
		engine_id, source_section, _role, mutability, page_anchor = cells[:5]
		if not engine_id.startswith("IT-STD-"):
			continue
		rows.append(
			SectionRegister(
				engine_id=engine_id,
				source_section=source_section,
				mutability=mutability,
				page_anchor=page_anchor,
			)
		)
	return rows


@dataclass(frozen=True)
class TdsParameterRegister:
	code: str
	source_ref: str
	label: str
	data_type: str
	required: bool
	engine_note: str


def _parse_bool_required(value: str) -> bool:
	normalized = value.strip().lower()
	return normalized in {"yes", "true", "mandatory"}


def load_tds_parameters() -> list[TdsParameterRegister]:
	pass2 = (DOCS_STD_PROD / "STD_IT_Full_Source_Extraction_Pass_2.md").read_text(encoding="utf-8")
	block = pass2.split("### 4.2 TDS parameter register", 1)[1].split("### 4.3", 1)[0]
	rows: list[TdsParameterRegister] = []
	for line in block.splitlines():
		if not line.startswith("| IT-TDS-"):
			continue
		cells = [cell.strip() for cell in line.strip("|").split("|")]
		if len(cells) < 7:
			continue
		code, source_ref, label, data_type, required, _allowed, note = cells[:7]
		rows.append(
			TdsParameterRegister(
				code=code,
				source_ref=source_ref,
				label=label,
				data_type=data_type,
				required=_parse_bool_required(required),
				engine_note=note,
			)
		)
	return rows


def load_scc_parameters() -> list[TdsParameterRegister]:
	pass2 = (DOCS_STD_PROD / "STD_IT_Full_Source_Extraction_Pass_2.md").read_text(encoding="utf-8")
	block = pass2.split("### 5.2 SCC parameter register", 1)[1].split("### 5.3", 1)[0]
	rows: list[TdsParameterRegister] = []
	for line in block.splitlines():
		if not line.startswith("| IT-SCC-"):
			continue
		cells = [cell.strip() for cell in line.strip("|").split("|")]
		if len(cells) < 7:
			continue
		code, gcc_ref, label, data_type, required, _allowed, note = cells[:7]
		rows.append(
			TdsParameterRegister(
				code=code,
				source_ref=gcc_ref,
				label=label,
				data_type=data_type,
				required=_parse_bool_required(required),
				engine_note=note,
			)
		)
	return rows


@dataclass(frozen=True)
class FormRegister:
	form_code: str
	title: str
	stage: str
	respondent: str


def load_forms() -> list[FormRegister]:
	pass3 = (DOCS_STD_PROD / "STD_IT_Full_Source_Extraction_Pass_3.md").read_text(encoding="utf-8")
	block = pass3.split("## 7. Tendering forms extraction register", 1)[1].split("## 8.", 1)[0]
	rows: list[FormRegister] = []
	for line in block.splitlines():
		if "IT-FORM-" not in line:
			continue
		cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
		if len(cells) < 5:
			continue
		form_code, title, stage, respondent, _notes = cells[:5]
		rows.append(FormRegister(form_code=form_code, title=title, stage=stage, respondent=respondent))
	return rows


def _page_range(page_anchor: str) -> tuple[int, int]:
	match = re.match(r"(\d+)(?:-(\d+))?", page_anchor.strip())
	if not match:
		return 1, 1
	start = int(match.group(1))
	end = int(match.group(2) or start)
	return start, end
