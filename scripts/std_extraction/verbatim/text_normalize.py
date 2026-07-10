"""PDF text normalization for search and hashing."""

from __future__ import annotations

import re
import unicodedata


def normalize_pdf_text(text: str) -> str:
	"""Normalize ligatures and whitespace from PDF text extraction."""
	if not text:
		return ""
	normalized = unicodedata.normalize("NFKC", text)
	normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
	normalized = re.sub(r"[ \t]+", " ", normalized)
	normalized = re.sub(r"\n{3,}", "\n\n", normalized)
	return normalized.strip()


def title_search_pattern(title: str) -> str:
	"""Build a forgiving regex fragment for clause title matching."""
	words = re.findall(r"[A-Za-z0-9]+", title)
	if not words:
		return re.escape(title)
	if len(words) >= 3:
		words = words[: min(6, len(words))]
	return r"\s+".join(re.escape(word) for word in words)
