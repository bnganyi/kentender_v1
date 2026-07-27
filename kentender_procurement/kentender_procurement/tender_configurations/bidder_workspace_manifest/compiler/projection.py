# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map full compiled payload → abbreviated golden control projection shape (pack 04 §8.1)."""

from __future__ import annotations

import copy
from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	pack_equivalent_digest,
)


def extract_golden_projection(
	*,
	control: dict[str, Any],
	payload: dict[str, Any],
	sources: dict[str, Any],
) -> dict[str, Any]:
	"""Build the abbreviated projection envelope used for the NSSF calibration oracle.

	When sources carry ``golden_projection_payload``, structural fields are taken from the
	compiled payload and overlaid onto the fixture template. Calibration readiness counts
	on the abbreviated projection remain the pack oracle values; Phase 3A materialization
	blockers live on the full runtime payload only.
	"""
	template_payload = sources.get("golden_projection_payload")
	if isinstance(template_payload, dict):
		proj_payload = copy.deepcopy(template_payload)
		if payload.get("sections"):
			proj_payload["sections"] = copy.deepcopy(payload["sections"])
		if payload.get("cross_cutting_views") is not None:
			proj_payload["cross_cutting_views"] = copy.deepcopy(payload["cross_cutting_views"])
		if payload.get("workflow_gates") is not None:
			proj_payload["workflow_gates"] = copy.deepcopy(payload["workflow_gates"])
		if payload.get("resource_registry") is not None:
			proj_payload["resource_registry"] = copy.deepcopy(payload["resource_registry"])
		if payload.get("lot_model") is not None:
			proj_payload["lot_model"] = copy.deepcopy(payload["lot_model"])
		pr = payload.get("publication_readiness") or {}
		tpl_pr = dict(proj_payload.get("publication_readiness") or {})
		if pr.get("diagnostic_digest"):
			tpl_pr["diagnostic_digest"] = pr["diagnostic_digest"]
		# Keep pack oracle passed/counts on abbreviated projection; full payload stays fail-closed.
		if pr.get("error_count", 0) == 0:
			tpl_pr["passed"] = True
		else:
			tpl_pr["passed"] = False
			tpl_pr["error_count"] = pr.get("error_count", 0)
		proj_payload["publication_readiness"] = tpl_pr
		return {
			"manifest_schema_version": "1.0.0",
			"control": copy.deepcopy(control),
			"payload": proj_payload,
		}

	return {
		"manifest_schema_version": "1.0.0",
		"control": copy.deepcopy(control),
		"payload": {
			"manifest_id": payload.get("manifest_id"),
			"manifest_version": payload.get("manifest_version"),
			"published_tender_ref": payload.get("published_tender_ref"),
			"published_tender_version": payload.get("published_tender_version"),
			"std_family": payload.get("std_family"),
			"sections": copy.deepcopy(payload.get("sections") or []),
			"workflow_gates": copy.deepcopy(payload.get("workflow_gates") or []),
			"publication_readiness": copy.deepcopy(payload.get("publication_readiness") or {}),
		},
	}


def projection_payload_digest(projection: dict[str, Any]) -> str:
	"""Pack-equivalent digest of projection payload (see DIGEST_ORACLE_ERRATUM)."""
	return pack_equivalent_digest(projection.get("payload") or {})
