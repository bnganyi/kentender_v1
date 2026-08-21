# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deprecated shim — use kentender_core.seeds.kentender_mvp_v1.orchestrator."""

from __future__ import annotations

from kentender_core.seeds.kentender_mvp_v1.orchestrator import (  # noqa: F401
	run_kentender_mvp_v1,
	run_moh_mvp_v1,
	validate_kentender_mvp_v1,
	validate_moh_mvp_v1,
)
