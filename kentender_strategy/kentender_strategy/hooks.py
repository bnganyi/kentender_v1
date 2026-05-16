# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from pathlib import Path


def _asset_version(rel_path: str) -> int:
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


app_name = "kentender_strategy"
app_title = "Kentender Strategy"
app_publisher = "KenTender"
app_description = "KenTender strategy and planning module."
app_email = "dev@kentender.local"
app_license = "mit"

# Apps
# ------------------

required_apps = ["kentender_core"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/kentender_strategy/css/strategy_workspace.css?v={_asset_version('public/css/strategy_workspace.css')}",
	f"/assets/kentender_strategy/css/strategic_plan_form.css?v={_asset_version('public/css/strategic_plan_form.css')}",
	f"/assets/kentender_strategy/css/strategy_builder_page.css?v={_asset_version('public/css/strategy_builder_page.css')}",
	f"/assets/kentender_strategy/css/procurement_journey_impact_panel.css?v={_asset_version('public/css/procurement_journey_impact_panel.css')}",
]
app_include_js = [
	f"/assets/kentender_strategy/js/workspace_list_selection_utils.js?v={_asset_version('public/js/workspace_list_selection_utils.js')}",
	f"/assets/kentender_strategy/js/strategy_workspace.js?v={_asset_version('public/js/strategy_workspace.js')}",
	f"/assets/kentender_strategy/js/strategic_plan.js?v={_asset_version('public/js/strategic_plan.js')}",
]

# include js in page
page_js = {"strategy-builder": "public/js/strategy_builder_page.js"}

# include js in doctype views
doctype_js = {
	"Strategic Plan": "public/js/strategic_plan.js",
	"Strategy Objective": "public/js/procurement_journey_impact_panel.js",
	"Strategy Target": "public/js/procurement_journey_impact_panel.js",
}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender_strategy/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kentender_strategy.utils.jinja_methods",
# 	"filters": "kentender_strategy.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_strategy.install.before_install"
# after_install = "kentender_strategy.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender_strategy.install.before_uninstall"
# after_uninstall = "kentender_strategy.install.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_strategy.utils.before_app_install"
# after_app_install = "kentender_strategy.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_strategy.utils.before_app_uninstall"
# after_app_uninstall = "kentender_strategy.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_strategy.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Strategic Plan": "kentender_strategy.permissions.get_strategic_plan_permission_query_conditions",
	"Strategy Program": "kentender_strategy.permissions.get_strategy_program_permission_query_conditions",
	"Strategy Objective": "kentender_strategy.permissions.get_strategy_objective_permission_query_conditions",
	"Strategy Target": "kentender_strategy.permissions.get_strategy_target_permission_query_conditions",
}

has_permission = {
	"Strategic Plan": "kentender_strategy.permissions.has_strategic_plan_permission",
	"Strategy Program": "kentender_strategy.permissions.has_strategy_program_permission",
	"Strategy Objective": "kentender_strategy.permissions.has_strategy_objective_permission",
	"Strategy Target": "kentender_strategy.permissions.has_strategy_target_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kentender_strategy.tasks.all"
# 	],
# 	"daily": [
# 		"kentender_strategy.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender_strategy.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender_strategy.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender_strategy.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender_strategy.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_strategy.event.get_events"
# }

# Fixtures
# --------

fixtures = [
	{
		"dt": "DocType",
		"filters": [
			[
				"name",
				"in",
				[
					"Strategic Plan",
					"Strategy Program",
					"Strategy Objective",
					"Strategy Target",
					"Strategy Node",
					"Sub Program",
					"Strategy Navigation",
				],
			]
		],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", ["Strategy Management"]]],
	},
	{
		"dt": "Page",
		"filters": [["name", "in", ["strategy-builder"]]],
	},
	{
		"dt": "Workspace Sidebar",
		"filters": [["name", "in", ["Strategy"]]],
	},
	{
		"dt": "Desktop Icon",
		"filters": [["name", "in", ["Strategy"]]],
	},
]
