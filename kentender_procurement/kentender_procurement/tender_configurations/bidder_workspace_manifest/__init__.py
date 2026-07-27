# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder Workspace Manifest contract schemas and NSSF fixture errata (G1 Phase 1)."""

from __future__ import annotations

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compatibility import (
	LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY,
	LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT,
	LEGACY_PACK10_SCHEMA_DIGEST,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.registry import (
	MANIFEST_SCHEMA_VERSION,
	list_schema_ids,
	load_schema,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.validate import (
	ManifestSchemaError,
	validate_against_schema,
)

__all__ = [
	"LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY",
	"LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT",
	"LEGACY_PACK10_SCHEMA_DIGEST",
	"MANIFEST_SCHEMA_VERSION",
	"ManifestSchemaError",
	"list_schema_ids",
	"load_schema",
	"validate_against_schema",
]
