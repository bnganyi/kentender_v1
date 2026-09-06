"""The CFG-CHG-002 v0.6 §8 error contract for site configuration.

A closed set, mirroring `responsibility_errors`: `fail_cfg()` refuses any code
outside the contract, and the sanctioned user-facing messages never name an
internal table, hook or algorithm (KT-STD-001 §11).
"""

from __future__ import annotations

import frappe

ERROR_CODES: frozenset[str] = frozenset(
	{
		"CFG_PE_NOT_CONFIGURED",
		"CFG_PE_ALREADY_CONFIGURED",
		"CFG_PE_CODE_IMMUTABLE",
		"CFG_PE_INVALID",
		"CFG_ROOT_UNIT_MISSING",
		"CFG_FY_ALREADY_EXISTS",
		"CFG_FY_IN_USE",
		"CFG_INTAKE_CLOSE_INSTANT_INVALID",
		"CFG_INTAKE_NOT_OPEN",
		"CFG_AUTHORITY_REQUIRED",
		"CFG_VERSION_CONFLICT",
	}
)

DEFAULT_MESSAGES: dict[str, str] = {
	"CFG_PE_NOT_CONFIGURED": "This site has no Procuring Entity yet. Configure it before using KenTender.",
	"CFG_PE_ALREADY_CONFIGURED": "This site already has a Procuring Entity.",
	"CFG_PE_CODE_IMMUTABLE": "The Procuring Entity code cannot be changed after it is set.",
	"CFG_PE_INVALID": "Complete the required Procuring Entity information.",
	"CFG_ROOT_UNIT_MISSING": "The root organisation unit is missing. Run the governed repair before assigning responsibilities.",
	"CFG_FY_ALREADY_EXISTS": "This financial year already exists.",
	"CFG_FY_IN_USE": "This financial year cannot be disabled while the listed records reference it.",
	"CFG_INTAKE_CLOSE_INSTANT_INVALID": "The closing time must be in the future.",
	"CFG_INTAKE_NOT_OPEN": "Needs submission is not open for this financial year.",
	"CFG_AUTHORITY_REQUIRED": "You are not authorised to change site configuration.",
	"CFG_VERSION_CONFLICT": "This record changed after you opened it. Refresh and review the latest version.",
}


class ConfigurationError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail_cfg(code: str, message: str = "") -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the CFG-CHG-002 v0.6 §8 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	message = message or DEFAULT_MESSAGES[code]
	frappe.throw(message, exc=ConfigurationError(code, message))
