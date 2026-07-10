"""Extract verbatim TDS/SCC parameter source text from the official PDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from scripts.std_extraction.hash_utils import normalize_text, sha256_text
from scripts.std_extraction.parse_passes import TdsParameterRegister, load_scc_parameters, load_tds_parameters
from scripts.std_extraction.verbatim.extract_layout import LayoutDocument, extract_layout
from scripts.std_extraction.verbatim.text_normalize import normalize_pdf_text


TDS_PAGE_START = 37
TDS_PAGE_END = 42
SCC_PAGE_START = 142
SCC_PAGE_END = 151


@dataclass
class VerbatimParameter:
	parameter_code: str
	section: str
	source_ref: str
	display_label: str
	source_text: str
	source_page_start: int
	source_page_end: int
	paragraph_hint: str | None
	source_text_hash: str
	normalized_text_hash: str
	extraction_status: str
	verification_status: str
	confidence: str


def _region_text(layout: LayoutDocument, section: str) -> tuple[str, list[tuple[int, int, int]]]:
	if section == "TDS":
		return layout.combined_text(TDS_PAGE_START, TDS_PAGE_END)
	return layout.combined_text(SCC_PAGE_START, SCC_PAGE_END)


def _normalize_ref(source_ref: str) -> str:
	return re.sub(r"\s+", " ", source_ref.strip())


def _find_ref_positions(text: str, source_ref: str) -> list[int]:
	ref = _normalize_ref(source_ref)
	positions: list[int] = []
	for match in re.finditer(re.escape(ref), text, flags=re.IGNORECASE):
		positions.append(match.start())
	if positions:
		return positions
	short = ref.split("(")[0].strip()
	for match in re.finditer(re.escape(short), text, flags=re.IGNORECASE):
		positions.append(match.start())
	return positions


def _extract_block(text: str, start: int, next_start: int | None) -> str:
	end = next_start if next_start is not None else len(text)
	block = normalize_pdf_text(text[start:end])
	return block.strip()


def _extract_parameters_for_section(
	layout: LayoutDocument,
	section: str,
	registers: list[TdsParameterRegister],
) -> list[VerbatimParameter]:
	region_text, spans = _region_text(layout, section)
	ref_positions: list[tuple[TdsParameterRegister, int]] = []
	for param in registers:
		positions = _find_ref_positions(region_text, param.source_ref)
		if positions:
			ref_positions.append((param, positions[0]))

	ref_positions.sort(key=lambda item: item[1])
	results: list[VerbatimParameter] = []
	for index, (param, start) in enumerate(ref_positions):
		next_start = ref_positions[index + 1][1] if index + 1 < len(ref_positions) else None
		block = _extract_block(region_text, start, next_start)
		if param.label.lower() not in block.lower() and param.label:
			block = f"{param.label}\n{block}".strip()
		page_start = layout.page_for_offset(spans, start)
		page_end = layout.page_for_offset(spans, max(start, (next_start or len(region_text)) - 1))
		confidence = "HIGH" if len(block) > 20 else "LOW"
		extraction_status = "EXTRACTED" if block else "EXTRACTION_LOW_CONFIDENCE"
		results.append(
			VerbatimParameter(
				parameter_code=param.code,
				section=section,
				source_ref=param.source_ref,
				display_label=param.label,
				source_text=block,
				source_page_start=page_start,
				source_page_end=page_end,
				paragraph_hint=param.source_ref,
				source_text_hash=sha256_text(block) if block else "",
				normalized_text_hash=sha256_text(normalize_text(block)) if block else "",
				extraction_status=extraction_status,
				verification_status="PENDING_LEGAL_REVIEW",
				confidence=confidence,
			)
		)

	found_codes = {row.parameter_code for row in results}
	for param in registers:
		if param.code in found_codes:
			continue
		fallback = normalize_pdf_text(param.label)
		results.append(
			VerbatimParameter(
				parameter_code=param.code,
				section=section,
				source_ref=param.source_ref,
				display_label=param.label,
				source_text=fallback,
				source_page_start=TDS_PAGE_START if section == "TDS" else SCC_PAGE_START,
				source_page_end=TDS_PAGE_END if section == "TDS" else SCC_PAGE_END,
				paragraph_hint=param.source_ref,
				source_text_hash=sha256_text(fallback) if fallback else "",
				normalized_text_hash=sha256_text(normalize_text(fallback)) if fallback else "",
				extraction_status="EXTRACTION_LOW_CONFIDENCE",
				verification_status="PENDING_LEGAL_REVIEW",
				confidence="LOW",
			)
		)
	return sorted(results, key=lambda row: row.parameter_code)


def extract_verbatim_parameters(layout: LayoutDocument | None = None) -> list[VerbatimParameter]:
	layout = layout or extract_layout()
	return _extract_parameters_for_section(layout, "TDS", load_tds_parameters()) + _extract_parameters_for_section(
		layout, "SCC", load_scc_parameters()
	)


def verbatim_parameter_to_package_fields(param: VerbatimParameter) -> dict[str, Any]:
	return {
		"source_text": param.source_text,
		"source_page_start": param.source_page_start,
		"source_page_end": param.source_page_end,
		"paragraph_hint": param.paragraph_hint,
		"source_text_hash": param.source_text_hash,
		"normalized_text_hash": param.normalized_text_hash,
		"verification_status": param.verification_status,
		"extraction_status": param.extraction_status,
		"extraction_confidence": param.confidence,
		"source_reference": param.source_ref,
	}
