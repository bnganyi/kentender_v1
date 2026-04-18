"""Workflow guard hook for KenTender (Phase H — placeholder).

Future implementations may inspect *action* and *document* and return ``(False, reason)``.
Phase H does not enforce rules; callers receive a successful pass-through so the API is stable.
"""

from __future__ import annotations

from frappe.model.document import Document


def run_workflow_guard(action: str, document: Document) -> tuple[bool, str]:
	"""Run pre-conditions before a critical workflow *action* on *document*.

	Returns ``(ok, message)`` where *message* explains failure when *ok* is false.
	"""
	return True, ""
