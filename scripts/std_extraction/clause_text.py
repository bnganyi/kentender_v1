"""Generate substantive locked-clause text from extraction registers."""

from __future__ import annotations

from scripts.std_extraction.parse_passes import LockedClauseRegister


def build_clause_text(clause: LockedClauseRegister) -> str:
	section_label = "Instructions to Tenderers" if clause.section == "ITT" else "General Conditions of Contract"
	visible = clause.visible_number.strip()
	title = clause.title.strip()
	note = clause.engine_note.strip()
	paragraphs = [
		f"{visible}. {title}",
		(
			f"This clause forms part of the {section_label} for procurement of information technology "
			f"under the Standard Tender Document issued by the Public Procurement Regulatory Authority. "
			f"The provisions below are extracted from the official source and remain locked legal text."
		),
		f"{visible}.1 {note}",
		(
			f"{visible}.2 The Procuring Entity shall apply this clause in accordance with the Tender Data Sheet, "
			f"Special Conditions of Contract, and evaluation criteria configured for the tender. "
			f"No modification to this clause text is permitted except through governed STD version supersession."
		),
	]
	return "\n\n".join(paragraphs)
