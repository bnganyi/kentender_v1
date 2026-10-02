# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-001 v0.10 §13.4 — locked declaration text is one text, not two.

A locked declaration rule repeats the official wording the supplier affirms.
Its `locked_text` is the normalized text of the anchored block in the
released master: tags removed, entities decoded, whitespace collapsed, and
descendant `<table>` content excluded (schedules inside a form are data, not
declaration wording). The only template syntax that may remain is
`{{ dotted.key }}` or `{{ dotted.key | lower }}`; `resolve()` fills those from
the document context. The release validator proves the resolved text equals
the same anchor's normalized text in the rendered issued Tender. Pure
Python: no Frappe import.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from kentender_procurement.std_templates.compiler.canonical import sha256_text
from kentender_procurement.std_templates.compiler.errors import fail

_EXPRESSION = re.compile(r"\{\{\s*([a-z_][a-z0-9_.]*)\s*(\|\s*lower\s*)?\}\}")
_STATEMENT = re.compile(r"\{%")
_VOID = {"br", "hr", "img", "input", "link", "meta", "col", "area", "base", "wbr", "source", "track", "param", "embed"}


class _AnchorText(HTMLParser):
	def __init__(self, anchor: str):
		super().__init__(convert_charrefs=True)
		self.anchor = anchor
		self.depth = 0  # >0 while inside the anchored element
		self.table_depth = 0
		self.found = 0
		self.parts: list[str] = []
		self.lists: list[list] = []  # one [marker kind, count] per open <ol>/<ul>; kind None = unordered

	def handle_starttag(self, tag, attrs):
		if self.depth:
			if tag not in _VOID:
				self.depth += 1
			if tag == "table":
				self.table_depth += 1
			if tag in ("ol", "ul"):
				self.lists.append([(dict(attrs).get("type") or "1") if tag == "ol" else None, 0])
			elif tag == "li" and self.lists and self.lists[-1][0] and not self.table_depth:
				self.lists[-1][1] += 1
				self.parts.append(" " + _marker(*self.lists[-1]) + " ")
			if tag in ("p", "li", "div", "h1", "h2", "h3", "h4", "ol", "ul", "br", "tr"):
				self.parts.append(" ")
			return
		if dict(attrs).get("id") == self.anchor and tag not in _VOID:
			self.found += 1
			self.depth = 1

	def handle_endtag(self, tag):
		if not self.depth:
			return
		if tag in ("ol", "ul") and self.lists:
			self.lists.pop()
		if tag == "table" and self.table_depth:
			self.table_depth -= 1
		if tag not in _VOID:
			self.depth -= 1
		if self.depth:
			self.parts.append(" ")

	def handle_data(self, data):
		if self.depth and not self.table_depth:
			self.parts.append(data)


def _marker(kind: str, count: int) -> str:
	"""The marker a browser draws for the `count`th item of an ordered list: 1., a., A., i., I."""
	if kind in ("a", "A"):
		return f"{chr(ord(kind) + (count - 1) % 26)}."
	if kind in ("i", "I"):
		numerals, out = (("m", 1000), ("cm", 900), ("d", 500), ("cd", 400), ("c", 100), ("xc", 90), ("l", 50), ("xl", 40), ("x", 10), ("ix", 9), ("v", 5), ("iv", 4), ("i", 1)), ""
		for symbol, value in numerals:
			out += symbol * (count // value)
			count %= value
		return (out if kind == "i" else out.upper()) + "."
	return f"{count}."


def normalize(text: str) -> str:
	return " ".join(text.split())


def anchored_text(html: str, anchor: str) -> str | None:
	"""Normalized text of the first element with `id=anchor`, or None."""
	parser = _AnchorText(anchor)
	parser.feed(html)
	parser.close()
	if not parser.found:
		return None
	return normalize("".join(parser.parts))


def anchor_count(html: str, anchor: str) -> int:
	return len(re.findall(r'\bid="' + re.escape(anchor) + r'"', html))


def text_digest(locked_text: str) -> str:
	return sha256_text(locked_text)


def _lookup(context: dict[str, Any], dotted: str) -> Any:
	value: Any = context
	for part in dotted.split("."):
		if not isinstance(value, dict) or part not in value:
			fail("STD_DEFINITION_INVALID", f"Locked text refers to an unknown value {dotted!r}.", identity=dotted)
		value = value[part]
	if isinstance(value, (dict, list)):
		fail("STD_DEFINITION_INVALID", f"Locked text value {dotted!r} is not a scalar.", identity=dotted)
	return value


def check_template(locked_text: str, identity: str) -> None:
	if _STATEMENT.search(locked_text):
		fail("STD_DEFINITION_INVALID", "Locked text contains a template statement.", identity=identity)
	leftover = _EXPRESSION.sub("", locked_text)
	if "{{" in leftover or "}}" in leftover:
		fail("STD_DEFINITION_INVALID", "Locked text contains an unsupported template expression.", identity=identity)


def resolve(locked_text: str, context: dict[str, Any], identity: str) -> str:
	check_template(locked_text, identity)

	def _sub(match: re.Match) -> str:
		value = "" if (v := _lookup(context, match.group(1))) is None else str(v)
		return value.lower() if match.group(2) else value

	return normalize(_EXPRESSION.sub(_sub, locked_text))
