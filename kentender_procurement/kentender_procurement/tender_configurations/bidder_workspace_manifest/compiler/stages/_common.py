# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	CompileContext,
	StageTrace,
)


def digest_of(obj: Any) -> str:
	raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
	return "sha256:" + hashlib.sha256(raw).hexdigest()


def ok(ctx: CompileContext, stage: str, detail: str = "") -> CompileContext:
	ctx.traces.append(StageTrace(stage=stage, state="ok", detail=detail))
	return ctx


def err(ctx: CompileContext, stage: str, detail: str) -> CompileContext:
	ctx.traces.append(StageTrace(stage=stage, state="error", detail=detail))
	return ctx


def skipped(ctx: CompileContext, stage: str, detail: str = "") -> CompileContext:
	ctx.traces.append(StageTrace(stage=stage, state="skipped", detail=detail))
	return ctx


def deep_copy(obj: Any) -> Any:
	return copy.deepcopy(obj)
