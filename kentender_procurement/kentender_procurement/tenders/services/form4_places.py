# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The places of Form No. 4 that the agreement fills (CM-CHG-001 v0.11 section 19.4 "Form No. 4 insertion or output"; CM-TPL-01; follow-up FU-CM-70).

The issued Form No. 4 is the template's own text with blanks (a run of underscores) and a few places the tender already filled with its own facts (the entity, its address, the goods). Nothing in it says which blank
is the agreement day, the supplier's name or the signatory, and Contract Management does not guess legal prose. This module is the template owner's declaration: for each template release it lists the places the
agreement may fill, each found by the fixed words that surround it, so the issued prose is **never edited**; a place is only wrapped in `<span data-insertion="key">…</span>` around what the form already holds
there. Contract Management fills the declared places and nothing else (`source_package.render`).

A release with no declaration here declares no place, and Contract Management names that as the gap. A declaration that does not match the form it is applied to (a tender issued from a form that reads differently
from the reviewed one) is refused by name, never applied loosely: every pattern must find its place **exactly once**.

The declaration for release 1.5 was written from the Form No. 4 that release 1.5 issues (the PPRA goods form, "Form No. 4 - Contract Agreement"). It is **new content for the Project Owner's review**: it adds no
word to the form and removes none."""

from __future__ import annotations

import re
from typing import Any

BLANK = r"_{5,}"

#: release -> patterns; each named group is one place, and its name is the insertion key Contract Management fills.
RELEASES: dict[str, tuple[str, ...]] = {
	"1.5": (
		# THIS AGREEMENT made the ___ day of ___, ___.
		rf"THIS AGREEMENT made the (?P<agreement_day>{BLANK}) day of (?P<agreement_month>{BLANK}), (?P<agreement_year>{BLANK})\. BETWEEN",
		# BETWEEN (1) <entity>, having its principal place of business at <address> (hereinafter called “the Procuring Entity”) … and (2) ___, a corporation incorporated under the laws of ___ and having its principal place of business at ___ (…“the Supplier”)
		r"BETWEEN \(1\) (?P<entity_name>[^<]+?), having its principal place of business at (?P<entity_address>[^<]+?) \(hereinafter called &ldquo;the Procuring Entity&rdquo;\), of the one part; and "
		rf"\(2\) (?P<supplier_name>{BLANK}), a corporation incorporated under the laws of (?P<supplier_country>{BLANK}) and having its principal place of business at (?P<supplier_address>{BLANK}) "
		r"\(hereinafter called &ldquo;the Supplier&rdquo;\)",
		# viz. <the tender's own description of the goods>, and has accepted a Tender
		r"viz\. (?P<goods>[^<]+?), and has accepted a Tender by the Supplier",
		# c) the Addenda Nos. ___ (if any)
		rf"the Addenda Nos\. (?P<addenda>{BLANK}) \(if any\)",
		# SIGNED ON ___ on behalf of <entity> / By ___ in the capacity of ___
		rf"<p>SIGNED ON {BLANK} on behalf of (?!the Supplier)[^<]+</p>\s*<p>By (?P<entity_signatory>{BLANK}) in the capacity of (?P<entity_capacity>{BLANK})</p>",
		# SIGNED ON ___ on behalf of the Supplier / By ___ in the capacity of ___
		rf"<p>SIGNED ON {BLANK} on behalf of the Supplier</p>\s*<p>By (?P<supplier_signatory>{BLANK}) in the capacity of (?P<supplier_capacity>{BLANK})</p>",
	),
}


class Undeclared(Exception):
	"""The form cannot be given places: the release declares none, or the form does not read as the reviewed one."""


def declared(release: str) -> bool:
	return str(release) in RELEASES


def mark(fragment: str, release: str) -> tuple[str, list[str]]:
	"""`fragment` with each declared place wrapped, and the keys in the order they appear. The words of the form are not changed."""
	patterns = RELEASES.get(str(release))
	if patterns is None:
		raise Undeclared(f"No reviewed declaration of the places of Form No. 4 exists for template release {release}, so the form declares no place to fill.")
	spans: list[tuple[int, int, str]] = []
	for pattern in patterns:
		found = list(re.finditer(pattern, fragment, re.S))
		names = list(re.compile(pattern, re.S).groupindex)
		if len(found) != 1:
			raise Undeclared(f"Form No. 4 of template release {release} does not read as the reviewed declaration expects: the passage holding {', '.join(names)} was found {len(found)} times, not once.")
		for name in names:
			start, end = found[0].span(name)
			spans.append((start, end, name))
	spans.sort()
	for earlier, later in zip(spans, spans[1:]):
		if earlier[1] > later[0]:
			raise Undeclared(f"Form No. 4 of template release {release}: the places {earlier[2]!r} and {later[2]!r} overlap.")
	out, last = [], 0
	for start, end, name in spans:
		out.append(fragment[last:start])
		out.append(f'<span data-insertion="{name}">{fragment[start:end]}</span>')
		last = end
	out.append(fragment[last:])
	return "".join(out), [name for _s, _e, name in spans]


def unmark(marked: str) -> str:
	"""The form as issued: the wrapping removed again (what a reader of the issued document sees, byte for byte)."""
	return re.sub(r'<span data-insertion="[a-z_]+">(.*?)</span>', r"\1", marked, flags=re.S)


def describe(release: str) -> dict[str, Any]:
	return {"release": str(release), "declared": declared(release), "places": [n for p in RELEASES.get(str(release), ()) for n in re.compile(p, re.S).groupindex]}
