"""Extract page-marked layout text from the official IT STD PDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.std_extraction.constants import DATA_DIR, PDF_FILENAME
from scripts.std_extraction.verbatim.text_normalize import normalize_pdf_text


@dataclass
class LayoutPage:
	number: int
	text: str


@dataclass
class LayoutDocument:
	pages: list[LayoutPage]
	source_path: Path

	def page_text(self, page_number: int) -> str:
		for page in self.pages:
			if page.number == page_number:
				return page.text
		return ""

	def combined_text(self, start_page: int, end_page: int) -> tuple[str, list[tuple[int, int, int]]]:
		"""Return combined text and spans as (page_number, start_offset, end_offset)."""
		chunks: list[str] = []
		spans: list[tuple[int, int, int]] = []
		offset = 0
		for page in self.pages:
			if page.number < start_page or page.number > end_page:
				continue
			start = offset
			chunks.append(page.text)
			offset += len(page.text) + 1
			spans.append((page.number, start, offset - 1))
		return "\n".join(chunks), spans

	def page_for_offset(self, spans: list[tuple[int, int, int]], position: int) -> int:
		for page_number, start, end in spans:
			if start <= position <= end:
				return page_number
		if spans:
			return spans[-1][0]
		return 1


def extract_layout(pdf_path: Path | None = None) -> LayoutDocument:
	try:
		import fitz
	except ImportError as exc:
		raise RuntimeError("PyMuPDF (pymupdf) is required for verbatim extraction") from exc

	path = pdf_path or (DATA_DIR / PDF_FILENAME)
	doc = fitz.open(path)
	pages = [
		LayoutPage(number=index + 1, text=normalize_pdf_text(doc[index].get_text()))
		for index in range(doc.page_count)
	]
	doc.close()
	return LayoutDocument(pages=pages, source_path=path)


def write_layout_file(layout: LayoutDocument, output_path: Path) -> None:
	lines: list[str] = []
	for page in layout.pages:
		lines.append(f"--- PAGE {page.number} ---")
		lines.append(page.text)
		lines.append("")
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text("\n".join(lines), encoding="utf-8")
