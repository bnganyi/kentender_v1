# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_budget — MVP-1 Budget & Funding (BUD-CHG-001 v1.2 clean rebuild)."""

app_name = "kentender_budget"
app_title = "Kentender Budget"
app_publisher = "KenTender"
app_description = "KenTender budget module (MVP-1 UI-first rebuild)."
app_email = "dev@kentender.local"
app_license = "mit"

required_apps = ["kentender_core", "kentender_strategy"]

# Empty pending the Phase 5 Vue-in-Desk rebuild (BUD-CHG-001 v1.2). Kept as an
# explicit dict, not removed, so callers that read kentender_budget.hooks.page_js
# directly (e.g. kentender_core's module-registry tests) see "zero routes",
# not an AttributeError.
page_js: dict[str, str] = {}

after_migrate = "kentender_budget.install.after_migrate"
before_tests = "kentender_budget.install.before_tests"
