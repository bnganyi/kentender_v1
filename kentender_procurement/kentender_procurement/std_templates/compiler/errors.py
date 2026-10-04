# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §12 — the closed STD template error vocabulary.

Pure Python (no Frappe import): the compiler, the release tooling and the
curation CLI raise these; the Frappe services translate them into service
results. An unknown code is a defect in the caller, not a new error type.
"""

from __future__ import annotations

from typing import Any

ERROR_CODES: frozenset[str] = frozenset(
	{
		"STD_RELEASE_NOT_FOUND",
		"STD_RELEASE_NOT_AVAILABLE",
		"STD_RELEASE_WITHDRAWN",
		"STD_RELEASE_INTEGRITY_FAILED",
		"STD_RELEASE_GATE_INCOMPLETE",
		"STD_RENDERER_UNSUPPORTED",
		"STD_INPUT_UNSUPPORTED",
		"STD_DEFINITION_INVALID",
		"STD_CONCERN_INVALID",
	}
)

MESSAGES: dict[str, str] = {
	"STD_RELEASE_NOT_FOUND": "STD Template not found.",
	"STD_RELEASE_NOT_AVAILABLE": "This Tender format is not available for new Tenders. Choose a currently available compatible format.",
	"STD_RELEASE_WITHDRAWN": "This Tender format has been withdrawn. Publication cannot continue.",
	"STD_RELEASE_INTEGRITY_FAILED": "The installed Tender format no longer matches its approved release. Contact the controlled template-release owner.",
	"STD_RELEASE_GATE_INCOMPLETE": "The release gate record does not list every mandatory gate.",
	"STD_RENDERER_UNSUPPORTED": "The renderer this Tender format needs is missing or incompatible.",
	"STD_INPUT_UNSUPPORTED": "This Tender uses a fact the Tender format does not support.",
	"STD_DEFINITION_INVALID": "The Bid definition could not be built from the released rules.",
	"STD_CONCERN_INVALID": "Check the highlighted concern details.",
}


class STDTemplateError(Exception):
	"""A typed STD template failure. `identity` names the stable rule, asset,
	gate or fact at fault; `detail` carries structured, non-secret context."""

	def __init__(self, code: str, message: str = "", *, identity: str = "", detail: dict[str, Any] | None = None):
		if code not in ERROR_CODES:
			raise ValueError(f"Unknown STD error code {code!r}")
		self.code = code
		self.identity = identity
		self.detail = dict(detail or {})
		self.message = message or MESSAGES[code]
		super().__init__(f"{code}: {self.message}" + (f" [{identity}]" if identity else ""))

	def as_dict(self) -> dict[str, Any]:
		return {"code": self.code, "message": self.message, "identity": self.identity, "detail": self.detail}


def fail(code: str, message: str = "", *, identity: str = "", detail: dict[str, Any] | None = None):
	raise STDTemplateError(code, message, identity=identity, detail=detail)
