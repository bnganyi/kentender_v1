# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Checksum verification for STD seed package files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ChecksumFailure:
	relative_path: str
	expected: str
	actual: str


def sha256_hex(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def verify_package_checksums(
	*,
	checksums: dict[str, Any],
	read_file: Callable[[str], bytes],
) -> tuple[str, list[ChecksumFailure]]:
	"""Verify files listed in checksum manifest using ``read_file(relative_path) -> bytes``."""
	files = checksums.get("files") if isinstance(checksums, dict) else None
	if not isinstance(files, dict) or not files:
		return "SKIPPED", []

	failures: list[ChecksumFailure] = []
	for relative_path, expected in files.items():
		if not isinstance(relative_path, str) or not isinstance(expected, str):
			continue
		try:
			actual = sha256_hex(read_file(relative_path))
		except KeyError:
			failures.append(ChecksumFailure(relative_path, expected, "<missing>"))
			continue
		if actual.lower() != expected.lower():
			failures.append(ChecksumFailure(relative_path, expected, actual))

	status = "PASSED" if not failures else "FAILED"
	return status, failures
