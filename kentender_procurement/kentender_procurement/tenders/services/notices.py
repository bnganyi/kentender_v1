# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 `GetTenderDocument` "addendum or cancellation
notice" — the two Tenders-owned notice templates (plan D5). Rendered with
the same discipline as the bundle masters: `StrictUndefined`, autoescape,
no custom filters, digest of the exact HTML. The 1.1 template release
carries no notice masters (FOLLOW_UPS FU-11)."""

from __future__ import annotations

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from kentender_procurement.tenders.services import digest

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
ADDENDUM_TEMPLATE = "addendum_notice.html"
CANCELLATION_TEMPLATE = "cancellation_notice.html"


def environment() -> Environment:
	return Environment(
		loader=FileSystemLoader(TEMPLATES_DIR),
		autoescape=select_autoescape(enabled_extensions=("html",)),
		undefined=StrictUndefined,
		keep_trailing_newline=True,
	)


def render_addendum_notice(context: dict[str, Any]) -> dict[str, str]:
	html = environment().get_template(ADDENDUM_TEMPLATE).render(**context)
	return {"html": html, "digest": digest.sha256_text(html)}


def render_cancellation_notice(context: dict[str, Any]) -> dict[str, str]:
	html = environment().get_template(CANCELLATION_TEMPLATE).render(**context)
	return {"html": html, "digest": digest.sha256_text(html)}
