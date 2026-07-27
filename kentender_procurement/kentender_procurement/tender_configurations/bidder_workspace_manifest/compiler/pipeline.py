# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ordered C01–C22 stage registry."""

from __future__ import annotations

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages.impl import (
	STAGE_FUNCS,
	_assemble_payload,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	CompileContext,
	CompileRequestDTO,
	CompileResult,
	SourceSet,
)


def run(request: CompileRequestDTO, sources: SourceSet) -> CompileResult:
	ctx = CompileContext(request=request, sources=sources)
	for _stage_id, fn in STAGE_FUNCS:
		ctx = fn(ctx)
	# Ensure payload assembled on success path if C20 skipped unexpectedly
	if not ctx.payload and not ctx.failed:
		_assemble_payload(ctx)
	report = {
		"ok": not ctx.failed,
		"error_count": sum(1 for d in ctx.diagnostics if d.severity == "error"),
		"warning_count": sum(1 for d in ctx.diagnostics if d.severity == "warning"),
		"information_count": sum(1 for d in ctx.diagnostics if d.severity == "information"),
		"payload_digest": ctx.payload_digest,
		"projection_digest": ctx.projection_digest,
		"diagnostic_digest": ctx.diagnostic_digest,
		"publication_readiness": (ctx.payload or {}).get("publication_readiness") or {},
		"stage_count": len(ctx.traces),
	}
	return CompileResult(
		ok=not ctx.failed,
		envelope=ctx.envelope,
		payload=ctx.payload,
		payload_digest=ctx.payload_digest,
		projection_digest=ctx.projection_digest,
		diagnostic_digest=ctx.diagnostic_digest,
		diagnostics=[d.as_dict() for d in ctx.diagnostics],
		traces=[t.as_dict() for t in ctx.traces],
		logical_resources=list(ctx.logical_resources),
		golden_projection=ctx.golden_projection,
		validation_report=report,
		addendum_impact=dict(ctx.addendum_impact or {}),
		digest_label=ctx.digest_label or "unmaterialized_preview_payload",
		fail_code=ctx.fail_code,
	)
