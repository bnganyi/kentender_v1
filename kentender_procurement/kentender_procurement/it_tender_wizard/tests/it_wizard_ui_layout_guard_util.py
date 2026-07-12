# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared helpers for IT Tender Wizard static UI layout guards."""

from __future__ import annotations

from pathlib import Path


def _kentender_v1_root() -> Path:
	return Path(__file__).resolve().parents[4]


def _procurement_public_root() -> Path:
	return Path(__file__).resolve().parents[2] / "public"


def design_source_path(ui_folder: str) -> Path:
	return (
		_kentender_v1_root()
		/ "docs"
		/ "std-prod-impl"
		/ "IT-STD-Wizard"
		/ "ui-designs"
		/ ui_folder
		/ "code.html"
	)


def deployed_asset_path(filename: str) -> Path:
	return _procurement_public_root() / "it_tender_wizard_impl" / filename


def normalize_eof_newline(text: str) -> str:
	"""Allow a single trailing newline difference at EOF only."""
	return text.rstrip("\n")


def read_text(path: Path) -> str:
	return path.read_text(encoding="utf-8", errors="replace")


def assert_verbatim_deploy(design_path: Path, deployed_path: Path) -> None:
	assert design_path.exists(), f"missing design source: {design_path}"
	assert deployed_path.exists(), f"missing deployed asset: {deployed_path}"

	design_html = normalize_eof_newline(read_text(design_path))
	deployed_html = normalize_eof_newline(read_text(deployed_path))

	assert design_html == deployed_html, (
		f"deployed asset must match design verbatim: {deployed_path.name} "
		f"(len design={len(design_html)}, len deployed={len(deployed_html)})"
	)
