# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable codes for governance errors and UI hints (spec §21 alignment)."""


class PlanSubmit:
	NOT_ALL_PACKAGES_APPROVED = "PP_PLAN_SUBMIT_NOT_ALL_APPROVED"
	NO_ACTIVE_PACKAGES = "PP_PLAN_SUBMIT_NO_ACTIVE_PACKAGES"


class PackageRelease:
	PLAN_NOT_APPROVED = "PP_RELEASE_PLAN_NOT_APPROVED"
	MUST_USE_WORKFLOW = "PP_RELEASE_MUST_USE_WORKFLOW"
