# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared helpers for IT Tender Wizard static UI layout guards."""

from __future__ import annotations

import re
from pathlib import Path

# Font <link> tags differ between the standalone design mockup (Google Fonts CDN)
# and the deployed asset (self-hosted kt_fonts.css). That swap is a deliberate
# app-wide infra change, not a layout change, so the verbatim guard normalizes
# both away before comparing — everything else must still match byte-for-byte.
_FONT_LINK_RE = re.compile(
	r"<link\b[^>]*?(?:fonts\.googleapis\.com|fonts\.gstatic\.com|kt_fonts\.css)[^>]*?>",
	re.IGNORECASE,
)

_TAILWIND_CDN_SCRIPT_RE = re.compile(
	r'<script\b[^>]*?\bsrc=["\'][^"\']*cdn\.tailwindcss\.com[^"\']*["\'][^>]*>\s*</script>',
	re.IGNORECASE,
)

_TAILWIND_CONFIG_SCRIPT_RE = re.compile(
	r'<script\b[^>]*?\bid=["\']tailwind-config["\'][^>]*>.*?</script>',
	re.IGNORECASE | re.DOTALL,
)


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


def design_source_path_v2_screen(screen_folder: str) -> Path:
	"""IT-STD-Wizard-v2 screen artefacts (e.g. screen-01/code.html)."""
	return (
		_kentender_v1_root()
		/ "docs"
		/ "std-prod-impl"
		/ "IT-STD-Wizard-v2"
		/ screen_folder
		/ "code.html"
	)


def dashboard_design_source_path() -> Path:
	"""Screen 01 dashboard design lives under IT-STD-Wizard-v2."""
	return design_source_path_v2_screen("screen-01")


def overview_design_source_path() -> Path:
	"""Screen 02 Tender Configuration Home design lives under IT-STD-Wizard-v2."""
	return design_source_path_v2_screen("screen-02")


def it_requirements_design_source_path() -> Path:
	"""Screen 03 IT Requirements design lives under IT-STD-Wizard-v2."""
	return design_source_path_v2_screen("screen-03")


def deployed_asset_path(filename: str) -> Path:
	return _procurement_public_root() / "it_tender_wizard_impl" / filename


def normalize_eof_newline(text: str) -> str:
	"""Allow a single trailing newline difference at EOF only."""
	return text.rstrip("\n")


def normalize_font_links(text: str) -> str:
	"""Strip Google-Fonts CDN and self-hosted kt_fonts.css <link> tags so the
	verbatim guard tolerates the CDN -> self-host font swap."""
	return _FONT_LINK_RE.sub("", text)


def normalize_tailwind_cdn(text: str) -> str:
	"""Strip Tailwind CDN/config scripts — native screens use kt_it_wizard.css."""
	text = _TAILWIND_CDN_SCRIPT_RE.sub("", text)
	return _TAILWIND_CONFIG_SCRIPT_RE.sub("", text)


def normalize_design_html(text: str) -> str:
	return normalize_tailwind_cdn(normalize_font_links(normalize_eof_newline(text)))


_DATA_ITW_ATTR_RE = re.compile(r'\s+data-itw-[a-z0-9_-]+(?:="[^"]*")?', re.IGNORECASE)


def normalize_data_itw_hooks(text: str) -> str:
	return _DATA_ITW_ATTR_RE.sub("", text)


def prepare_it_requirements_reference_html(html: str) -> str:
	"""Apply native reference transforms (hooks + spec fixes) before layout compare."""
	html = normalize_design_html(html)
	html = html.replace(
		'<section class="bg-surface-container-lowest border border-border-subtle rounded-xl p-card-padding shadow-sm overflow-x-auto">',
		'<section class="bg-surface-container-lowest border border-border-subtle rounded-xl p-card-padding shadow-sm overflow-x-auto" data-itw-req-context="1">',
	)
	html = html.replace(
		'<div class="flex flex-col gap-4">',
		'<div class="flex flex-col gap-4" data-itw-req-composer="1">',
		1,
	)
	html = html.replace(
		'<div class="overflow-x-auto">',
		'<div class="overflow-x-auto" data-itw-req-table-host="1">',
		1,
	)
	html = html.replace(
		'<aside class="flex flex-col gap-6 sticky top-24">',
		'<aside class="flex flex-col gap-6 sticky top-24" data-itw-req-guidance="1">',
		1,
	)
	html = html.replace(
		'<footer class="fixed bottom-0 w-full bg-surface-container-lowest border-t border-outline-variant px-container-padding py-4 z-40">',
		'<footer class="fixed bottom-0 w-full bg-surface-container-lowest border-t border-outline-variant px-container-padding py-4 z-40" data-itw-req-actions="1">',
		1,
	)
	html = html.replace(
		'id="edit-requirement-drawer"',
		'id="edit-requirement-drawer" data-itw-req-drawer="1" data-itw-req-drawer-hidden="1"',
	)
	html = re.sub(
		r'<div class="flex items-center gap-2"><span class="material-symbols-outlined text-\[18px\] text-on-surface-variant">verified_user</span>.*?</div>',
		'<div class="flex items-center gap-2"><span class="material-symbols-outlined text-[18px] text-on-surface-variant">description</span><span class="text-[13px] text-on-surface-variant">Forms &amp; Evidence: <span class="font-bold text-on-surface">Evidence item will be configured in Forms &amp; Evidence</span></span></div>',
		html,
		flags=re.DOTALL,
	)
	html = html.replace(
		'<label class="block text-[12px] font-bold text-on-surface mb-1">Acceptance Criteria</label>\n<textarea class="w-full px-3 py-2 border border-outline-variant rounded-lg text-body-md focus:border-primary outline-none h-20" placeholder="Define the criteria for acceptance..."></textarea>',
		'<label class="block text-[12px] font-bold text-on-surface mb-1">Acceptance Description</label>\n<textarea class="w-full px-3 py-2 border border-outline-variant rounded-lg text-body-md focus:border-primary outline-none h-20" placeholder="Define the criteria for acceptance..."></textarea>',
		1,
	)
	html = html.replace(
		'<label class="block text-[12px] font-bold text-on-surface mb-1">Acceptance Criteria</label>\n<select',
		'<label class="block text-[12px] font-bold text-on-surface mb-1">Acceptance Expectation</label>\n<select',
		1,
	)
	return html


def assert_it_requirements_reference_deploy(design_path: Path, deployed_path: Path) -> None:
	assert design_path.exists(), f"missing design source: {design_path}"
	assert deployed_path.exists(), f"missing deployed asset: {deployed_path}"
	design_html = prepare_it_requirements_reference_html(read_text(design_path))
	# Deployed asset is already prepared (hooks + spec fixes applied at sync time).
	deployed_html = normalize_design_html(read_text(deployed_path))
	assert design_html == deployed_html, (
		f"deployed asset must match v2 Screen 03 reference: {deployed_path.name} "
		f"(len design={len(design_html)}, len deployed={len(deployed_html)})"
	)


def read_text(path: Path) -> str:
	return path.read_text(encoding="utf-8", errors="replace")


def assert_verbatim_deploy(design_path: Path, deployed_path: Path) -> None:
	assert design_path.exists(), f"missing design source: {design_path}"
	assert deployed_path.exists(), f"missing deployed asset: {deployed_path}"

	design_html = normalize_design_html(read_text(design_path))
	deployed_html = normalize_design_html(read_text(deployed_path))

	assert design_html == deployed_html, (
		f"deployed asset must match design verbatim: {deployed_path.name} "
		f"(len design={len(design_html)}, len deployed={len(deployed_html)})"
	)
