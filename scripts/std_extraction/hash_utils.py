"""Text normalization and SHA-256 hashing for STD extraction."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_text(text: str) -> str:
	"""Normalize whitespace and ligatures for canonical hashing."""
	if not text:
		return ""
	normalized = unicodedata.normalize("NFKC", text)
	normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
	normalized = re.sub(r"[ \t]+", " ", normalized)
	normalized = re.sub(r"\n{3,}", "\n\n", normalized)
	return normalized.strip()


def sha256_text(text: str) -> str:
	return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
	with open(path, "rb") as handle:
		return hashlib.sha256(handle.read()).hexdigest()
