"""Providers the record-picker tests register in place of an app's own.

Not a test module: `test_record_picker` points the registry at `sources()` here so the
mechanics (search, ranking, sections, clamping) are tested without any app's data."""

from __future__ import annotations

from typing import Any

#: What the last provider call received, so a test can see what core passed on.
calls: list[dict[str, Any]] = []

PEOPLE = [
	{"id": "amina.hassan", "label": "Amina Hassan", "detail": "Accounting Officer · Ministry of Health", "keywords": "amina.hassan@moh.example", "near": True},
	{"id": "amos.kamau", "label": "Amos Kamau", "detail": "Budget Officer · Finance", "keywords": "amos.kamau@moh.example"},
	{"id": "brian.wafula", "label": "Brian Wafula", "detail": "Procurement Officer · Supply Chain Management", "keywords": "brian.wafula@moh.example", "near": True},
	{"id": "beatrice.kamau", "label": "Beatrice Kamau", "detail": "Budget Approver · Finance", "keywords": "beatrice.kamau@moh.example"},
	{"id": "daniel.rotich", "label": "Daniel Rotich", "detail": "Plan Statutory Approver · Planning", "keywords": "daniel.rotich@moh.example"},
	{"id": "esther.njeri", "label": "Esther Njeri", "detail": "Evaluation Technical Support · ICT", "keywords": "esther.njeri@moh.example",
		"disabled_reason": "Was involved in processing this Tender"},
	{"id": "zoe.mwangi", "label": "Zoë Mwangi", "detail": "Auditor · Internal Audit", "keywords": "zoe.mwangi@moh.example",
		"extra": {"designation": "Auditor", "department": "Internal Audit"}},
	{"id": "hamina.ali", "label": "Hamina Ali", "detail": "Aminata Desk · Registry", "keywords": "hamina.ali@moh.example"},
	# Two people a typed login can confuse: both match the words "pw", "tnd" and "officer"; only one has this login.
	{"id": "pw.tnd.both@example.test", "label": "Playwright Tenders Both", "detail": "Procurement Officer", "keywords": "pw.tnd.both@example.test"},
	{"id": "pw.tnd.officer@example.test", "label": "Playwright Tenders Officer", "detail": "Procurement Officer", "keywords": "pw.tnd.officer@example.test"},
]


def _rows(extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	return [{**row, **(extra or {})} for row in PEOPLE]


def everyone(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""Core mode: every row the actor may see; core matches and ranks."""
	calls.append({"query": query, "context": context, "actor": actor, "limit": limit})
	return _rows({"secret": "must not reach the browser"})


def many(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""Core mode, 120 people in one department, to prove the caps."""
	calls.append({"query": query, "context": context, "actor": actor, "limit": limit})
	return [{"id": f"p{i:03d}", "label": f"Person {i:03d}", "detail": "Finance", "near": True} for i in range(120)]


def forbidden(*, query: str, context: dict, actor: str, limit: int):
	import frappe

	raise frappe.PermissionError("no")


def messy(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""Rows with no id, no label, and a repeated id."""
	return [
		{"id": "a", "label": "First A", "detail": ""},
		{"id": "a", "label": "Second A", "detail": ""},
		{"label": "No id", "detail": ""},
		{"id": "c", "label": "", "detail": ""},
		{"id": "d", "label": "Dee"},
	]


def by_provider(*, query: str, context: dict, actor: str, limit: int):
	"""Provider mode: the provider filters and says how many matched."""
	calls.append({"query": query, "context": context, "actor": actor, "limit": limit})
	rows = [row for row in PEOPLE if query.lower() in row["label"].lower()][:limit]
	return rows, 143


def by_provider_resolver(*, ids: list[str], context: dict, actor: str) -> list[dict[str, Any]]:
	return [row for row in PEOPLE if row["id"] in ids]


def sources() -> list[dict[str, Any]]:
	base = "kentender_core.tests.picker_test_sources."
	return [
		{"key": "test.everyone", "noun": "person", "match": "core", "provider": base + "everyone"},
		{"key": "test.many", "noun": "unit", "plural": "units", "near_title": "Your directorate", "rest_title": "Other units", "hint": "Only active units are listed.", "match": "core", "provider": base + "many"},
		{"key": "test.forbidden", "noun": "person", "match": "core", "provider": base + "forbidden"},
		{"key": "test.messy", "noun": "record", "match": "core", "provider": base + "messy"},
		{"key": "test.by_provider", "noun": "person", "match": "provider", "provider": base + "by_provider", "resolver": base + "by_provider_resolver"},
	]
