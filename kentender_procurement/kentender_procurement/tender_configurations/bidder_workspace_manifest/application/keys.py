# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Server-derived composite identity keys (structured JCS digests)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)

RESOURCE_KEY_ALGORITHM = "bwmf-resource-key-v1"
ARTIFACT_BINDING_KEY_ALGORITHM = "bwmf-artifact-binding-key-v1"
MANIFEST_BINDING_KEY_ALGORITHM = "bwmf-manifest-binding-key-v1"


def _hex_digest(structured: dict[str, Any]) -> str:
	"""Return bare 64-char hex (no sha256: prefix) for Data(140) unique keys."""
	full = jcs_sha256_digest(structured)
	return full.removeprefix("sha256:")


def resource_version_key(
	resource_id: str,
	resource_digest: str,
	schema_ref: str,
	schema_version: str,
) -> str:
	"""Composite unique key for an exact Manifest Resource version."""
	return _hex_digest(
		{
			"algorithm_version": RESOURCE_KEY_ALGORITHM,
			"resource_id": resource_id,
			"resource_digest": resource_digest,
			"schema_ref": schema_ref,
			"schema_version": schema_version,
		}
	)


def artifact_resource_key(compile_artifact: str, resource_id: str) -> str:
	return _hex_digest(
		{
			"algorithm_version": ARTIFACT_BINDING_KEY_ALGORITHM,
			"compile_artifact": compile_artifact,
			"resource_id": resource_id,
		}
	)


def manifest_resource_binding_key(manifest_version: str, resource_id: str) -> str:
	return _hex_digest(
		{
			"algorithm_version": MANIFEST_BINDING_KEY_ALGORITHM,
			"manifest_version": manifest_version,
			"resource_id": resource_id,
		}
	)


def assert_server_key(field_name: str, provided: str | None, expected: str) -> None:
	"""Reject client-supplied composite keys that differ from the server derivation."""
	if provided and provided != expected:
		import frappe
		from frappe import _

		frappe.throw(
			_("Client-supplied {0} does not match server-derived value.").format(field_name),
			title="BWMF_COMPOSITE_KEY",
		)
