# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deprecated shim package — use kentender_core.seeds.kentender_mvp_v1."""

from kentender_core.seeds.moh_mvp_v1.orchestrator import (
	run_moh_mvp_v1,
	validate_moh_mvp_v1,
)

__all__ = ["run_moh_mvp_v1", "validate_moh_mvp_v1"]
