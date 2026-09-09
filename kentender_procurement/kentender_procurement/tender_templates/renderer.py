# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.5/§10.1 and STD-TPL-IMP-001 §10 — the one server-side
renderer for `IT-EQUIPMENT-OPEN-V1`.

Masters are loaded only from the installed code bundle; Jinja runs with
`StrictUndefined`, autoescape and no custom filters (STD-TPL-001 v0.5 §4.1);
the render context is built by Tender Preparation's canonical serializer,
never from a user-editable database field; the Invitation renders separately
from the issued Tender (STD-STD-001 §7); HTML is the authoritative output
and the PDF a convenience rendering of the same content (plan D4).
"""

from __future__ import annotations

import hashlib
from typing import Any

from jinja2 import Environment, FunctionLoader, StrictUndefined, select_autoescape

from kentender_procurement.tender_templates import checks, loader

INVITATION_TEMPLATE = "invitation_to_tender.html"
ISSUED_TENDER_TEMPLATE = "complete_tender.html"
PRINT_CSS = "print.css"


def _sha256(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def environment(bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> Environment:
	def _load(name: str) -> str:
		return loader.read_text(f"templates/{name}", bundle_root)

	return Environment(
		loader=FunctionLoader(_load),
		autoescape=select_autoescape(enabled_extensions=("html",)),
		undefined=StrictUndefined,
		keep_trailing_newline=True,
	)


def render_invitation(context: dict[str, Any], bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> str:
	return environment(bundle_root).get_template(INVITATION_TEMPLATE).render(**_public(context))


def render_issued_tender(context: dict[str, Any], bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> str:
	return environment(bundle_root).get_template(ISSUED_TENDER_TEMPLATE).render(**_public(context))


def _public(context: dict[str, Any]) -> dict[str, Any]:
	"""The template never sees internal-only context (TPR-AC-044): the
	serializer keeps those under `_internal`, stripped here as a second
	guard, and `StrictUndefined` means no master can reach them anyway."""
	return {k: v for k, v in context.items() if not k.startswith("_")}


def render_both(context: dict[str, Any], bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> dict[str, Any]:
	"""Both outputs plus their digests and the release checks that gate
	readiness (STD-TPL-001 v0.5 §11.3). `problems` is empty on a clean render."""
	invitation = render_invitation(context, bundle_root)
	issued = render_issued_tender(context, bundle_root)
	problems: list[str] = []
	problems += [f"invitation: {hit}" for hit in checks.unresolved_content(invitation)]
	problems += [f"issued tender: {hit}" for hit in checks.unresolved_content(issued)]
	if not checks.invitation_absent_from_issued_tender(issued):
		problems.append("the Invitation notice is inside the issued Tender")
	problems += [f"cross-output: {p}" for p in checks.cross_output_inconsistencies(context, invitation, issued)]
	problems += [f"internal-only leak (invitation): {leak}" for leak in checks.internal_only_leaks(invitation, context)]
	problems += [f"internal-only leak (issued tender): {leak}" for leak in checks.internal_only_leaks(issued, context)]
	return {
		"invitation_html": invitation, "issued_tender_html": issued,
		"invitation_digest": _sha256(invitation), "issued_tender_digest": _sha256(issued),
		"problems": problems,
	}


def with_inline_print_css(html: str, bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> str:
	"""The masters link `print.css` relatively; a PDF renderer has no base
	path, so the same stylesheet is inlined for the convenience PDF only —
	the authoritative HTML (and its digest) is untouched."""
	css = loader.read_text(f"templates/{PRINT_CSS}", bundle_root)
	return html.replace('<link rel="stylesheet" href="print.css">', f"<style>\n{css}\n</style>", 1)


def to_pdf(html: str, *, footer_center: str = "", bundle_root: str = loader.DEFAULT_BUNDLE_ROOT) -> bytes:
	"""Convenience PDF via Frappe's wkhtmltopdf wrapper (plan D4): content is
	inspected in tests, never byte-compared."""
	from frappe.utils.pdf import get_pdf

	options: dict[str, Any] = {"page-size": "A4", "margin-top": "25mm", "margin-bottom": "25mm", "margin-left": "20mm", "margin-right": "20mm"}
	if footer_center:
		options["footer-center"] = footer_center
		options["footer-font-size"] = "8"
	return get_pdf(with_inline_print_css(html, bundle_root), options=options)
