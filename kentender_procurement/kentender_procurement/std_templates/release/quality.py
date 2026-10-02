# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Template content quality gates (STD-TPL-001 v0.14 §13.9).

The structural checks of the compiler and `validate_release.py` prove a
template is well formed; none of them proves it says what the official form
says. These gates catch the defect classes found when a real Tender was
exercised on release 1.2:

- G-LABEL: a field whose label (or, with a wordless label, its help) is only
  an ordinal such as "Conflict of interest item 3";
- G-DUPLICATE: two always-visible fields of one rule that read identically;
- G-TABLE: an official-form table with no recorded treatment, or one still
  collapsed into text after the release that was meant to replace it;
- G-POLARITY: a Yes/No field whose evaluation reading is not declared, or
  disagrees with the rule kind;
- G-EVAL-COVERAGE: an evaluated field with no evaluation rule (always
  "Needs review"), or a rule for a not-evaluated mapping;
- G-EVALUATOR-TEXT: a result rule or reason that names an item by number only;
- G-LOCKED-NUMBERING: an ordered list in the master that loses its numbers in
  the locked declaration text;
- G-COMPOUND (advisory): a free-text field that asks for several things.

Pure Python, no Frappe import. Inputs are the loaded JSON documents; a
finding is a `Finding`. A finding covered by a dated owner decision in the
quality register's `deferred` list is reported as deferred, never silently
dropped.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, NamedTuple

LABEL, DUPLICATE, TABLE, POLARITY, EVAL_COVERAGE, EVALUATOR_TEXT, LOCKED_NUMBERING, COMPOUND = (
	"G-LABEL", "G-DUPLICATE", "G-TABLE", "G-POLARITY", "G-EVAL-COVERAGE", "G-EVALUATOR-TEXT", "G-LOCKED-NUMBERING", "G-COMPOUND")
ADVISORY = (COMPOUND,)
#: Treatments a table in the quality register may carry.
TREATMENTS = ("itemised", "row-group", "interim", "excluded", "deferred", "open")
#: What a Yes/No answer means to the evaluator.
POLARITIES = ("yes-discloses", "yes-reassures")
_ORDINAL = re.compile(r"\b(?:item|items|question|paragraph|clause|row|part)\s*(?:\([0-9a-z]{1,4}\)|[0-9]{1,3})\.?(?:\s*\([0-9a-z]{1,4}\))?", re.IGNORECASE)
_NAMED_BY_NUMBER = re.compile(r"\bitem\s*(?:\([0-9a-z]{1,4}\)|[0-9]{1,3})|\bthe item named\b", re.IGNORECASE)
#: Fewer words than this around an ordinal and the text identifies nothing.
_MIN_WORDS = 6
#: A label of fewer words than this says too little to stand without its help.
_LABEL_WORDS = 3


class Finding(NamedTuple):
	check: str
	where: str
	message: str

	@property
	def advisory(self) -> bool:
		return self.check in ADVISORY


def _words(text: str) -> int:
	return len(re.findall(r"[A-Za-z]{2,}", _ORDINAL.sub(" ", text or "")))


def _bare_ordinal(text: str) -> bool:
	return bool(text) and bool(_ORDINAL.search(text)) and _words(text) < _MIN_WORDS


def release_key(release: str) -> tuple[int, ...]:
	return tuple(int(p) for p in str(release).split("."))


# -- G-LABEL, G-DUPLICATE, G-COMPOUND ----------------------------------------
def check_labels(rules: list[dict], profile: dict) -> list[Finding]:
	repetition = {c["composition_id"]: c.get("repetition", "one") for c in profile.get("compositions", [])}
	out: list[Finding] = []
	for rule in rules:
		seen: dict[tuple[str, str], str] = {}
		for field in rule["field_definitions"]:
			where = f"{rule['rule_id']}.{field['field_key']}"
			label, help_text = field.get("label") or "", field.get("help_text") or ""
			if _bare_ordinal(label):
				out.append(Finding(LABEL, where, f"label {label!r} is an ordinal with no wording; the supplier cannot tell what is asked."))
			elif help_text and _bare_ordinal(help_text) and _words(label) < _LABEL_WORDS:
				out.append(Finding(LABEL, where, f"label {label!r} and help {help_text!r} carry no wording."))
			if repetition.get(rule["composition_id"], "one") == "one":
				key = (label, repr(field.get("visibility_rule")))
				if key in seen:
					out.append(Finding(DUPLICATE, where, f"label {label!r} repeats {seen[key]} with the same visibility."))
				seen[key] = field["field_key"]
			if field["control_id"] == "CTL-LONG-TEXT" and _compound(label):
				out.append(Finding(COMPOUND, where, f"long-text label {label!r} appears to ask for several things; confirm one answer is meant."))
	return out


def _compound(label: str) -> bool:
	inner = re.search(r"\(([^)]*)\)", label)
	listed = (inner.group(1) if inner else label)
	return len(re.split(r",|\band\b", listed)) >= 3


# -- G-TABLE -----------------------------------------------------------------
def check_tables(register: dict, rules: list[dict], template_release: str) -> tuple[list[Finding], list[Finding]]:
	"""(findings, deferred). Every table in the register carries a treatment."""
	by_rule = {r["rule_id"]: {f["field_key"]: f for f in r["field_definitions"]} for r in rules}
	deferred_ids = {d["where"] for d in register.get("deferred", []) if d["check"] == TABLE}
	out: list[Finding] = []
	deferred: list[Finding] = []
	for table in register.get("tables", []):
		where, treatment = table["id"], table.get("treatment")
		if treatment not in TREATMENTS:
			out.append(Finding(TABLE, where, f"{where} has no recorded treatment (one of {', '.join(TREATMENTS)})."))
			continue
		for ref in table.get("fields", []):
			rule_id, _, key = ref.partition(".")
			field = by_rule.get(rule_id, {}).get(key)
			if field is None:
				out.append(Finding(TABLE, where, f"{where} names {ref}, which the template does not publish."))
			elif treatment == "row-group" and field["control_id"] != "CTL-ROW-GROUP":
				out.append(Finding(TABLE, where, f"{where} is a row-group but {ref} uses {field['control_id']}."))
		if treatment in ("excluded", "deferred") and not (table.get("reason") and table.get("decided")):
			out.append(Finding(TABLE, where, f"{where} is {treatment} without a recorded reason and owner decision date."))
		if treatment == "interim" and release_key(template_release) >= release_key(table["until_release"]):
			out.append(Finding(TABLE, where, f"{where} is still collapsed into text; it was due as a table in release {table['until_release']}."))
		if treatment == "open" and not table.get("reason"):
			out.append(Finding(TABLE, where, f"{where} is open without stating the question for the owner."))
		if treatment in ("deferred", "open"):
			deferred.append(Finding(TABLE, where, ("OPEN: " if treatment == "open" else "") + table.get("reason", "")))
	return [f for f in out if f.where not in deferred_ids], deferred


# -- G-POLARITY, G-EVAL-COVERAGE, G-EVALUATOR-TEXT ---------------------------
def entries_for(evaluation: dict, template_release: str) -> list[dict]:
	"""The evaluation entries in force for one release: an entry with a
	`releases` list applies only to those releases."""
	return [r for r in evaluation.get("rules", []) if not r.get("releases") or template_release in r["releases"]]


def check_evaluation(rules: list[dict], mappings: list[dict], evaluation: dict, template_release: str = "") -> list[Finding]:
	out: list[Finding] = []
	entries = entries_for(evaluation, template_release)
	index = {(r["mapping_id"], r["field_key"]): r for r in entries}
	evaluated = {m["mapping_id"] for m in mappings if m["evaluation_treatment"] == "Evaluated"}
	not_evaluated = {m["mapping_id"] for m in mappings} - evaluated
	if sorted(set(evaluation.get("not_evaluated", []))) != sorted(not_evaluated):
		out.append(Finding(EVAL_COVERAGE, "not_evaluated", "the evaluation file's not_evaluated list differs from the mappings' not-evaluated treatments."))
	for rule in rules:
		mapping_id = rule["evaluation_mapping_id"]
		for field in rule["field_definitions"]:
			entry = index.get((mapping_id, field["field_key"]))
			where = f"{mapping_id}.{field['field_key']}"
			if mapping_id in evaluated and entry is None:
				out.append(Finding(EVAL_COVERAGE, where, "evaluated field has no evaluation rule; every bid reads Needs review."))
			if mapping_id in not_evaluated and entry is not None:
				out.append(Finding(EVAL_COVERAGE, where, "a rule exists for a not-evaluated mapping (a hidden criterion)."))
			if mapping_id in evaluated and field["control_id"] == "CTL-YES-NO" and entry is not None:
				out += _polarity(where, entry)
	for entry in entries:
		for key, value in entry.items():
			if isinstance(value, str) and _NAMED_BY_NUMBER.search(value):
				out.append(Finding(EVALUATOR_TEXT, f"{entry['mapping_id']}.{entry['field_key']}", f"{key} names an item by number only: {value!r}."))
	for mapping in mappings:
		text = mapping.get("evaluation_result_rule") or ""
		if _NAMED_BY_NUMBER.search(text):
			out.append(Finding(EVALUATOR_TEXT, mapping["mapping_id"], f"result rule names an item by number only: {text!r}."))
	return out


def _polarity(where: str, entry: dict) -> list[Finding]:
	polarity, kind = entry.get("polarity"), entry.get("kind")
	if polarity not in POLARITIES:
		return [Finding(POLARITY, where, f"Yes/No field in an evaluated mapping declares no polarity (one of {', '.join(POLARITIES)}).")]
	if kind == "review-if-yes" and polarity != "yes-discloses":
		return [Finding(POLARITY, where, "rule kind review-if-yes reads Yes as a disclosure but polarity says Yes reassures.")]
	if kind == "review-unless" and polarity == "yes-discloses" and entry.get("accepted_value") == "Yes":
		return [Finding(POLARITY, where, "rule kind review-unless accepts Yes but polarity says Yes discloses.")]
	return []


# -- G-LOCKED-NUMBERING ------------------------------------------------------
class _OrderedLists(HTMLParser):
	def __init__(self, anchor: str):
		super().__init__(convert_charrefs=True)
		self.anchor, self.depth, self.ordered = anchor, 0, False

	def handle_starttag(self, tag, attrs):
		if self.depth:
			self.depth += tag not in ("br", "hr", "img", "input")
			self.ordered = self.ordered or tag == "ol"
		elif dict(attrs).get("id") == self.anchor:
			self.depth = 1

	def handle_endtag(self, tag):
		if self.depth and tag not in ("br", "hr", "img", "input"):
			self.depth -= 1


def check_locked_numbering(rules: list[dict], master_html: str) -> list[Finding]:
	out = []
	for rule in rules:
		if "locked_text" not in rule:
			continue
		anchor = rule["document_anchor"].split("#", 1)[1]
		parser = _OrderedLists(anchor)
		parser.feed(master_html)
		if parser.ordered and not re.search(r"(?:^|\s)1[.)]\s", rule["locked_text"]):
			out.append(Finding(LOCKED_NUMBERING, rule["rule_id"], f"master anchor {anchor} holds an ordered list but the locked text carries no numbers."))
	return out


# -- everything --------------------------------------------------------------
def run(*, rules: list[dict], mappings: list[dict], profile: dict, evaluation: dict, register: dict, master_html: str,
		template_release: str) -> dict[str, list[Finding]]:
	"""{'failures': [...], 'advisories': [...], 'deferred': [...]}. A finding
	named by a deferred register entry (same check and `where`) moves to
	'deferred'."""
	table_findings, deferred_tables = check_tables(register, rules, template_release)
	found = check_labels(rules, profile) + table_findings + check_evaluation(rules, mappings, evaluation, template_release) + check_locked_numbering(rules, master_html)
	waived = {(d["check"], d["where"]) for d in register.get("deferred", [])}
	failures = [f for f in found if not f.advisory and (f.check, f.where) not in waived]
	deferred = deferred_tables + [f for f in found if (f.check, f.where) in waived]
	return {"failures": failures, "advisories": [f for f in found if f.advisory], "deferred": deferred}
