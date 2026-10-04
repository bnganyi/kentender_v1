# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The document-renderer adapter (STD-TPL-IMP-001 v1.0 §8; STD-TPL-001
v0.10 §13.4) for renderer profile `BDS-GOODS-IT-V1` version `1.0.0`.

HTML is rendered from the release's own master bytes with Jinja
auto-escaping, `StrictUndefined` and no custom filters; the HTML is the
authoritative output. The convenience PDF is produced by the one pinned
engine this adapter declares — wkhtmltopdf 0.12.6.1 (with patched qt) —
through fixed options. A different engine or version is a new adapter
version with new regression evidence, never a silent substitution.
Pure Python (Jinja + subprocess): no Frappe import.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

from jinja2 import DictLoader, Environment, StrictUndefined, select_autoescape

from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.renderers import checks

INVITATION = "invitation_to_tender.html"
ISSUED_TENDER = "complete_tender.html"
PRINT_CSS = "print.css"
MASTER_PATHS = {
	INVITATION: "02_master/invitation_to_tender.html",
	ISSUED_TENDER: "02_master/complete_tender.html",
	PRINT_CSS: "02_master/print.css",
}


@dataclass(frozen=True)
class DocumentAdapter:
	renderer_profile_id: str
	supported_renderer_version: str
	engine: str
	engine_version: str
	page_options: tuple[tuple[str, str], ...]
	sanitisation: str = "Jinja auto-escaping; StrictUndefined; no custom filters; no JavaScript in masters; no network resources"
	fonts_and_print_css: str = "Release print.css inlined for the PDF; system serif fonts; A4 portrait"
	regression_procedure: str = "pdftotext -layout text extraction compared with the authoritative HTML for required sections and anchors"

	def describe(self) -> dict[str, Any]:
		return {
			"renderer_profile_id": self.renderer_profile_id,
			"supported_renderer_version": self.supported_renderer_version,
			"kind": "document",
			"engine": self.engine,
			"engine_version": self.engine_version,
			"page_options": dict(self.page_options),
			"sanitisation": self.sanitisation,
			"fonts_and_print_css": self.fonts_and_print_css,
			"regression_procedure": self.regression_procedure,
		}

	# ------------------------------------------------------------------
	# health
	# ------------------------------------------------------------------

	def health(self) -> dict[str, Any]:
		binary = shutil.which(self.engine)
		if not binary:
			return {"ok": False, "engine": self.engine, "problem": f"{self.engine} is not installed"}
		try:
			result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30, check=False)
		except (OSError, subprocess.SubprocessError) as exc:
			return {"ok": False, "engine": self.engine, "problem": f"{self.engine} could not run: {exc}"}
		found = (result.stdout or result.stderr).strip()
		ok = found == self.engine_version
		return {"ok": ok, "engine": self.engine, "found_version": found, "expected_version": self.engine_version, "problem": "" if ok else "engine version differs from the registered adapter"}

	def require_healthy(self) -> None:
		state = self.health()
		if not state["ok"]:
			fail("STD_RENDERER_UNSUPPORTED", f"Document renderer unavailable: {state['problem']}.", identity=f"{self.renderer_profile_id}@{self.supported_renderer_version}")

	# ------------------------------------------------------------------
	# HTML
	# ------------------------------------------------------------------

	def environment(self, masters: dict[str, str]) -> Environment:
		missing = [name for name in (INVITATION, ISSUED_TENDER) if name not in masters]
		if missing:
			fail("STD_RELEASE_INTEGRITY_FAILED", f"Release master {missing[0]} is missing.", identity=missing[0])
		return Environment(
			loader=DictLoader(dict(masters)),
			autoescape=select_autoescape(enabled_extensions=("html",)),
			undefined=StrictUndefined,
			keep_trailing_newline=True,
		)

	def render_html(self, masters: dict[str, str], context: dict[str, Any]) -> dict[str, Any]:
		public = {k: v for k, v in context.items() if not k.startswith("_")}
		env = self.environment(masters)
		invitation = env.get_template(INVITATION).render(**public)
		issued = env.get_template(ISSUED_TENDER).render(**public)
		problems: list[str] = []
		problems += [f"invitation: {hit}" for hit in checks.unresolved_content(invitation)]
		problems += [f"issued tender: {hit}" for hit in checks.unresolved_content(issued)]
		if not checks.invitation_absent_from_issued_tender(issued):
			problems.append("the Invitation notice is inside the issued Tender")
		problems += [f"cross-output: {p}" for p in checks.cross_output_inconsistencies(context, invitation, issued)]
		problems += [f"internal-only leak (invitation): {leak}" for leak in checks.internal_only_leaks(invitation, context)]
		problems += [f"internal-only leak (issued tender): {leak}" for leak in checks.internal_only_leaks(issued, context)]
		return {
			"invitation_html": invitation,
			"issued_tender_html": issued,
			"invitation_digest": hashlib.sha256(invitation.encode("utf-8")).hexdigest(),
			"issued_tender_digest": hashlib.sha256(issued.encode("utf-8")).hexdigest(),
			"problems": problems,
		}

	# ------------------------------------------------------------------
	# PDF (convenience rendering of the authoritative HTML)
	# ------------------------------------------------------------------

	@staticmethod
	def inline_print_css(html: str, print_css: str) -> str:
		return html.replace('<link rel="stylesheet" href="print.css">', f"<style>\n{print_css}\n</style>", 1)

	def render_pdf(self, html: str, print_css: str, *, footer_center: str = "") -> bytes:
		self.require_healthy()
		args = [shutil.which(self.engine) or self.engine, "--quiet", "--encoding", "UTF-8", "--disable-javascript", "--disable-local-file-access"]
		for name, value in self.page_options:
			args += [f"--{name}", value]
		if footer_center:
			args += ["--footer-center", footer_center, "--footer-font-size", "8"]
		args += ["-", "-"]
		result = subprocess.run(args, input=self.inline_print_css(html, print_css).encode("utf-8"), capture_output=True, timeout=180, check=False)
		if result.returncode != 0 or not result.stdout.startswith(b"%PDF"):
			fail("STD_RENDERER_UNSUPPORTED", "The document renderer failed to produce a PDF.", identity=self.engine, detail={"stderr": result.stderr.decode("utf-8", "replace")[-500:]})
		return result.stdout

	@staticmethod
	def extract_text(pdf: bytes) -> str:
		binary = shutil.which("pdftotext")
		if not binary:
			fail("STD_RENDERER_UNSUPPORTED", "pdftotext is required for renderer regression checks.", identity="pdftotext")
		result = subprocess.run([binary, "-layout", "-", "-"], input=pdf, capture_output=True, timeout=120, check=False)
		if result.returncode != 0:
			fail("STD_RENDERER_UNSUPPORTED", "The PDF text could not be extracted.", identity="pdftotext")
		return result.stdout.decode("utf-8", "replace")
