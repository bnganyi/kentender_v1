"""Extract verbatim locked ITT/GCC clause text from the official PDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from scripts.std_extraction.hash_utils import normalize_text, sha256_text
from scripts.std_extraction.parse_passes import LockedClauseRegister, _page_range, load_locked_clauses
from scripts.std_extraction.verbatim.extract_layout import LayoutDocument, extract_layout
from scripts.std_extraction.verbatim.text_normalize import normalize_pdf_text, title_search_pattern


SYNTHETIC_MARKER = (
	"This clause forms part of the Instructions to Tenderers for procurement of information technology "
	"under the Standard Tender Document issued by the Public Procurement Regulatory Authority."
)

ITT_PAGE_START = 17
ITT_PAGE_END = 36
GCC_PAGE_START = 107
GCC_PAGE_END = 141

_HEADING_RE = re.compile(
	r"(?:^|\n)\s*(?:[A-Z]\.\s*)?(\d{1,2})\s*(?:\.\s*)?\n\s*([A-Za-z][^\n]{4,160}?)(?=\s*\n)",
	re.MULTILINE,
)


@dataclass
class VerbatimClause:
	clause_code: str
	section: str
	visible_number: str
	display_title: str
	full_clause_text: str
	source_page_start: int
	source_page_end: int
	paragraph_start_hint: str | None
	paragraph_end_hint: str | None
	source_text_hash: str
	normalized_text_hash: str
	extraction_status: str
	verification_status: str
	confidence: str
	register_page_start: int
	register_page_end: int


def _clause_region(layout: LayoutDocument, section: str) -> tuple[str, list[tuple[int, int, int]]]:
	if section == "ITT":
		return layout.combined_text(ITT_PAGE_START, ITT_PAGE_END)
	return layout.combined_text(GCC_PAGE_START, GCC_PAGE_END)


def _section_page_start(section: str) -> int:
	return ITT_PAGE_START if section == "ITT" else GCC_PAGE_START


def _title_fragments(title: str) -> list[str]:
	parts = re.split(r"[,/]|\band\b", title, flags=re.IGNORECASE)
	fragments = [part.strip() for part in parts if len(part.strip()) >= 5]
	words = re.findall(r"[A-Za-z0-9]+", title)
	if len(words) >= 4:
		fragments.append(" ".join(words[:4]))
	if len(words) >= 3:
		fragments.append(" ".join(words[:3]))
	seen: set[str] = set()
	unique: list[str] = []
	for fragment in fragments:
		key = fragment.lower()
		if key in seen:
			continue
		seen.add(key)
		unique.append(fragment)
	return unique or [title.strip()]


def _looks_like_clause_heading(title: str) -> bool:
	title = title.strip()
	if len(title) > 90:
		return False
	if re.search(r"\.\s+[A-Za-z]", title):
		return False
	if re.search(r"\b(shall|will|must|means|including|pursuant|accordance)\b", title, re.IGNORECASE):
		return False
	return True


def _printed_page_number(pdf_page: int, section_start: int) -> int:
	return pdf_page - section_start + 1


def _is_page_chrome(
	position: int,
	number: int,
	title: str,
	page: int,
	spans: list[tuple[int, int, int]],
	section_start: int,
) -> bool:
	if not _looks_like_clause_heading(title):
		return True
	printed = _printed_page_number(page, section_start)
	if number != printed:
		return False
	for _page, start, _end in spans:
		if _page == page and start <= position <= start + 12:
			return True
	return False


def _discover_headings(
	layout: LayoutDocument,
	text: str,
	spans: list[tuple[int, int, int]],
	section: str,
) -> list[tuple[int, int, str, int]]:
	section_start = _section_page_start(section)
	headings: list[tuple[int, int, str, int]] = []
	for match in _HEADING_RE.finditer(text):
		number = int(match.group(1))
		title = match.group(2).strip()
		position = match.start()
		page = layout.page_for_offset(spans, position)
		if _is_page_chrome(position, number, title, page, spans, section_start):
			continue
		headings.append((position, number, title, page))
	headings.sort(key=lambda row: row[0])
	return headings


def _normalize_match_text(text: str) -> str:
	return re.sub(r"[^a-z0-9]", "", text.lower())


def _title_match_score(register_title: str, candidate_title: str) -> float:
	candidate = _normalize_match_text(candidate_title)
	scores: list[float] = []
	for fragment in _title_fragments(register_title):
		normalized_fragment = _normalize_match_text(fragment)
		if normalized_fragment and normalized_fragment in candidate:
			scores.append(1.0)
			continue
		pattern = title_search_pattern(fragment)
		if re.search(pattern, candidate_title, flags=re.IGNORECASE):
			scores.append(1.0)
			continue
		words = [word for word in re.findall(r"[a-z0-9]+", normalized_fragment) if len(word) > 2]
		if not words:
			continue
		hits = sum(1 for word in words if word in candidate.split())
		scores.append(hits / len(words))
	full_pattern = title_search_pattern(register_title)
	if re.search(full_pattern, candidate_title, flags=re.IGNORECASE):
		scores.append(0.95)
	return max(scores) if scores else 0.0


def _score_heading(
	clause: LockedClauseRegister,
	heading: tuple[int, int, str, int],
	section_start: int,
) -> float:
	position, number, title, page = heading
	reg_start, reg_end = _page_range(clause.page_anchor)
	title_score = _title_match_score(clause.title, title)
	if title_score < 0.5:
		return 0.0
	page_distance = min(abs(page - reg_start), abs(page - reg_end))
	page_score = max(0.0, 1.0 - (page_distance / 8.0))
	number_bonus = 0.1 if str(number) == clause.visible_number.strip() else 0.0
	return (title_score * 0.75) + (page_score * 0.25) + number_bonus


def _find_clause_positions(
	layout: LayoutDocument,
	text: str,
	spans: list[tuple[int, int, int]],
	clause: LockedClauseRegister,
	headings: list[tuple[int, int, str, int]],
) -> list[tuple[int, re.Match[str]]]:
	section_start = _section_page_start(clause.section)
	scored: list[tuple[float, int, tuple[int, int, str, int]]] = []
	for heading in headings:
		score = _score_heading(clause, heading, section_start)
		if score >= 0.55:
			scored.append((score, heading[0], heading))
	if not scored:
		visible = re.escape(clause.visible_number.strip())
		title_pattern = title_search_pattern(clause.title)
		patterns = [
			rf"(?:^|\n)\s*{visible}\s*\.\s*{title_pattern}",
			rf"(?:^|\n)\s*{visible}\s*\n\s*{title_pattern}",
		]
		reg_start, reg_end = _page_range(clause.page_anchor)
		candidates: list[tuple[int, int, re.Match[str]]] = []
		for pattern in patterns:
			for match in re.finditer(pattern, text, flags=re.IGNORECASE):
				page_guess = layout.page_for_offset(spans, match.start())
				distance = min(abs(page_guess - reg_start), abs(page_guess - reg_end))
				candidates.append((distance, match.start(), match))
		if not candidates:
			return []
		candidates.sort(key=lambda row: (row[0], row[1]))
		best_distance = candidates[0][0]
		return [(pos, match) for dist, pos, match in candidates if dist == best_distance]

	scored.sort(key=lambda row: (-row[0], row[1]))
	best_score = scored[0][0]
	best_positions = [row[1] for row in scored if row[0] >= best_score - 0.05]
	start = min(best_positions)
	class _HeadingMatch:
		def __init__(self, pos: int) -> None:
			self._pos = pos

		def start(self) -> int:
			return self._pos

	return [(start, _HeadingMatch(start))]


def _assign_clause_starts(
	registers: list[LockedClauseRegister],
	headings: list[tuple[int, int, str, int]],
	section: str,
) -> list[tuple[LockedClauseRegister, int]]:
	section_start = _section_page_start(section)
	used_positions: set[int] = set()
	starts: list[tuple[LockedClauseRegister, int]] = []
	for clause in registers:
		scored: list[tuple[float, int]] = []
		for heading in headings:
			position = heading[0]
			if position in used_positions:
				continue
			score = _score_heading(clause, heading, section_start)
			if score >= 0.55:
				scored.append((score, position))
		if not scored:
			continue
		scored.sort(key=lambda row: (-row[0], row[1]))
		best_position = scored[0][1]
		used_positions.add(best_position)
		starts.append((clause, best_position))
	return starts


def extract_verbatim_clauses(layout: LayoutDocument | None = None) -> list[VerbatimClause]:
	layout = layout or extract_layout()
	clauses_by_section: dict[str, list[LockedClauseRegister]] = {"ITT": [], "GCC": []}
	for clause in load_locked_clauses():
		clauses_by_section[clause.section].append(clause)

	results: list[VerbatimClause] = []
	for section, registers in clauses_by_section.items():
		region_text, spans = _clause_region(layout, section)
		headings = _discover_headings(layout, region_text, spans, section)
		starts = _assign_clause_starts(registers, headings, section)
		position_sorted = sorted(starts, key=lambda row: row[1])

		section_results: list[VerbatimClause] = []
		for index, (clause, start) in enumerate(position_sorted):
			end = position_sorted[index + 1][1] if index + 1 < len(position_sorted) else len(region_text)
			body = normalize_pdf_text(region_text[start:end])
			page_start = layout.page_for_offset(spans, start)
			page_end = layout.page_for_offset(spans, max(start, end - 1))
			reg_start, reg_end = _page_range(clause.page_anchor)
			confidence = "HIGH" if body and len(body) > 40 else "LOW"
			extraction_status = "EXTRACTED" if body else "EXTRACTION_LOW_CONFIDENCE"
			section_results.append(
				VerbatimClause(
					clause_code=clause.internal_id,
					section=section,
					visible_number=clause.visible_number.strip(),
					display_title=clause.title.strip(),
					full_clause_text=body,
					source_page_start=page_start,
					source_page_end=page_end,
					paragraph_start_hint=f"{clause.visible_number.strip()}.1",
					paragraph_end_hint=f"{clause.visible_number.strip()}.n",
					source_text_hash=sha256_text(body) if body else "",
					normalized_text_hash=sha256_text(normalize_text(body)) if body else "",
					extraction_status=extraction_status,
					verification_status="PENDING_LEGAL_REVIEW",
					confidence=confidence,
					register_page_start=reg_start,
					register_page_end=reg_end,
				)
			)

		found_codes = {row.clause_code for row in section_results}
		for clause in registers:
			if clause.internal_id in found_codes:
				continue
			reg_start, reg_end = _page_range(clause.page_anchor)
			section_results.append(
				VerbatimClause(
					clause_code=clause.internal_id,
					section=section,
					visible_number=clause.visible_number.strip(),
					display_title=clause.title.strip(),
					full_clause_text="",
					source_page_start=reg_start,
					source_page_end=reg_end,
					paragraph_start_hint=None,
					paragraph_end_hint=None,
					source_text_hash="",
					normalized_text_hash="",
					extraction_status="EXTRACTION_LOW_CONFIDENCE",
					verification_status="PENDING_LEGAL_REVIEW",
					confidence="LOW",
					register_page_start=reg_start,
					register_page_end=reg_end,
				)
			)
		results.extend(section_results)
	return sorted(results, key=lambda row: (row.section, row.clause_code))


def verbatim_clause_to_package_record(
	clause: VerbatimClause,
	*,
	clause_key: str,
	section_key: str,
	anchor_key: str,
	source_document_id: str,
) -> dict[str, Any]:
	return {
		"clause_key": clause_key,
		"clause_code": clause.clause_code,
		"section_key": section_key,
		"clause_number": clause.visible_number,
		"display_title": clause.display_title,
		"full_clause_text": clause.full_clause_text,
		"clause_text_source": "PDF_VERBATIM",
		"mutability_type": "LOCKED_LEGAL_TEXT",
		"source_anchor_key": anchor_key,
		"source_document_id": source_document_id,
		"source_section_ref": clause.section,
		"source_clause_ref": clause.clause_code,
		"source_page_start": clause.source_page_start,
		"source_page_end": clause.source_page_end,
		"paragraph_start_hint": clause.paragraph_start_hint,
		"paragraph_end_hint": clause.paragraph_end_hint,
		"source_anchor": anchor_key,
		"source_text_hash": clause.source_text_hash,
		"normalized_text_hash": clause.normalized_text_hash,
		"text_status": clause.extraction_status,
		"extraction_status": clause.extraction_status,
		"verification_status": clause.verification_status,
		"extraction_confidence": clause.confidence,
		"register_page_start": clause.register_page_start,
		"register_page_end": clause.register_page_end,
	}
