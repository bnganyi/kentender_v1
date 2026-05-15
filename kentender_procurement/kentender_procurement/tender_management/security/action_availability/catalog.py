# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Action code catalogue — SEC-0400.

Keeps the Action Availability minimum action list aligned with
``ACTION_AUTHORIZATION_REGISTRY``.
"""

from __future__ import annotations

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	registered_action_codes,
	tm2_doc9_section_74_action_codes,
)

REQUIRED_ACTION_CODES: frozenset[str] = frozenset(
	{
		"IMPORT_OFFICIAL_STD_PACKAGE",
		"VALIDATE_STD_TEMPLATE",
		"ACTIVATE_STD_TEMPLATE",
		"RELEASE_PACKAGE_TO_TENDER",
		"CREATE_STD_INSTANCE_FROM_TENDER",
		"EDIT_STD_INSTANCE_PARAMETERS",
		"UPLOAD_STD_SECTION_ATTACHMENT",
		"CONFIGURE_WORKS_BOQ",
		"GENERATE_STD_OUTPUTS",
		"RUN_PUBLICATION_READINESS",
		"SUBMIT_TENDER_FOR_APPROVAL",
		"APPROVE_TENDER_PUBLICATION",
		"RETURN_TENDER_FOR_CORRECTION",
		"PUBLISH_TENDER",
		"CREATE_ADDENDUM",
		"CONSUME_DSM",
		"CONSUME_DOM",
		"CONSUME_DEM",
		"CONSUME_DCM",
		"EXPORT_EVIDENCE_PACKAGE",
	}
)

# Doc 9 §7.4 — same keys as ``_TM2_DOC9_SECTION_74_REGISTRY`` (single source of truth).
PACK_SECTION_7_4_ACTION_CODES: frozenset[str] = tm2_doc9_section_74_action_codes()

_EXPECTED_PACK_74_CODE_COUNT = 59


def assert_required_action_codes_registered() -> None:
	"""Fail fast if SEC-0400 required actions are not registered for authorization."""
	registered = registered_action_codes()
	missing = REQUIRED_ACTION_CODES - registered
	if missing:
		raise AssertionError(f"SEC-0400 required action codes missing from registry: {sorted(missing)!r}")


def assert_pack_section_74_action_codes_registered() -> None:
	"""Fail fast if doc 9 §7.4 actions are missing from ``ACTION_AUTHORIZATION_REGISTRY``."""
	registered = registered_action_codes()
	pack = PACK_SECTION_7_4_ACTION_CODES
	missing = pack - registered
	if missing:
		raise AssertionError(f"Doc 9 §7.4 action codes missing from registry: {sorted(missing)!r}")
	if len(pack) != _EXPECTED_PACK_74_CODE_COUNT:
		raise AssertionError(
			f"Expected {_EXPECTED_PACK_74_CODE_COUNT} doc 9 §7.4 codes, registry has {len(pack)} "
			"(update _EXPECTED_PACK_74_CODE_COUNT if the pack list changed)."
		)


assert_required_action_codes_registered()
assert_pack_section_74_action_codes_registered()
