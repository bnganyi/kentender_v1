from pathlib import Path


def _asset_version(rel_path: str) -> int:
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


def _desk_asset_v(rel_path: str) -> int:
	"""Cache-bust string for app_include: combine asset + hooks mtime so any edit rebusts; clear-cache + restart still required for Redis hook cache in prod."""
	try:
		base = Path(__file__).resolve().parent
		a = (base / rel_path).stat()
		h = (base / "hooks.py").stat()
		# Use nanosecond precision + file size to avoid same-second cache-bust collisions.
		return int((a.st_mtime_ns + h.st_mtime_ns + a.st_size + h.st_size) % 2_147_483_647)
	except OSError:
		return 1


app_name = "kentender_procurement"
app_title = "Kentender Procurement"
app_publisher = "KenTender"
app_description = "KenTender procurement lifecycle module."
app_email = "dev@kentender.local"
app_license = "mit"

# Apps
# ------------------

required_apps = ["kentender_core", "kentender_strategy", "kentender_budget"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender_procurement",
# 		"logo": "/assets/kentender_procurement/logo.png",
# 		"title": "Kentender Procurement",
# 		"route": "/kentender_procurement",
# 		"has_permission": "kentender_procurement.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/kentender_procurement/css/procurement_home_workspace.css?v={_desk_asset_v('public/css/procurement_home_workspace.css')}",
	f"/assets/kentender_procurement/css/procurement_journey_page.css?v={_desk_asset_v('public/css/procurement_journey_page.css')}",
	f"/assets/kentender_procurement/css/module_journey_context_header.css?v={_desk_asset_v('public/css/module_journey_context_header.css')}",
	f"/assets/kentender_procurement/css/pp2_planning_status_badge.css?v={_desk_asset_v('public/css/pp2_planning_status_badge.css')}",
	f"/assets/kentender_procurement/css/pp2_planning_handoff_card.css?v={_desk_asset_v('public/css/pp2_planning_handoff_card.css')}",
	f"/assets/kentender_procurement/css/tm2_tender_handoff_panel.css?v={_desk_asset_v('public/css/tm2_tender_handoff_panel.css')}",
	f"/assets/kentender_procurement/css/business_readiness_summary.css?v={_desk_asset_v('public/css/business_readiness_summary.css')}",
	f"/assets/kentender_procurement/css/procurement_package.css?v={_desk_asset_v('public/css/procurement_package.css')}",
	f"/assets/kentender_procurement/css/std_library_shell.css?v={_desk_asset_v('public/css/std_library_shell.css')}",
	f"/assets/kentender_procurement/css/tender_management_v2_workbench.css?v={_desk_asset_v('public/css/tender_management_v2_workbench.css')}",
	f"/assets/kentender_procurement/css/pp2_planning_page.css?v={_desk_asset_v('public/css/pp2_planning_page.css')}",
	f"/assets/kentender_procurement/css/pp3_planning_design_system.css?v={_desk_asset_v('public/css/pp3_planning_design_system.css')}",
]
app_include_js = [
	f"/assets/kentender_procurement/js/pp2_planning_status_badge.js?v={_desk_asset_v('public/js/pp2_planning_status_badge.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_handoff_card.js?v={_desk_asset_v('public/js/pp2_planning_handoff_card.js')}",
	f"/assets/kentender_procurement/js/module_journey_context_header.js?v={_desk_asset_v('public/js/module_journey_context_header.js')}",
	f"/assets/kentender_procurement/js/business_readiness_summary.js?v={_desk_asset_v('public/js/business_readiness_summary.js')}",
	f"/assets/kentender_procurement/js/tm2_tender_handoff_panel.js?v={_desk_asset_v('public/js/tm2_tender_handoff_panel.js')}",
	f"/assets/kentender_procurement/js/workspace_list_selection_utils.js?v={_desk_asset_v('public/js/workspace_list_selection_utils.js')}",
	f"/assets/kentender_procurement/js/pp_template_selector.js?v={_desk_asset_v('public/js/pp_template_selector.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_active_plan_banner.js?v={_desk_asset_v('public/js/pp3_planning_active_plan_banner.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_workbench_queue_tabs.js?v={_desk_asset_v('public/js/pp3_planning_workbench_queue_tabs.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_work_list.js?v={_desk_asset_v('public/js/pp3_planning_work_list.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_plan_list.js?v={_desk_asset_v('public/js/pp3_planning_plan_list.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_plan_summary.js?v={_desk_asset_v('public/js/pp3_planning_plan_summary.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_package_detail.js?v={_desk_asset_v('public/js/pp3_planning_package_detail.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_create_plan_modal.js?v={_desk_asset_v('public/js/pp3_planning_create_plan_modal.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_selected_work_summary.js?v={_desk_asset_v('public/js/pp3_planning_selected_work_summary.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_evidence_drawer.js?v={_desk_asset_v('public/js/pp3_planning_evidence_drawer.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_released_list.js?v={_desk_asset_v('public/js/pp3_planning_released_list.js')}",
	f"/assets/kentender_procurement/js/pp3_planning_release_summary.js?v={_desk_asset_v('public/js/pp3_planning_release_summary.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_page_header.js?v={_desk_asset_v('public/js/pp2_planning_page_header.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_queue_tabs.js?v={_desk_asset_v('public/js/pp2_planning_queue_tabs.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_work_list.js?v={_desk_asset_v('public/js/pp2_planning_work_list.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_blocker_summary.js?v={_desk_asset_v('public/js/pp2_planning_blocker_summary.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_empty_state.js?v={_desk_asset_v('public/js/pp2_planning_empty_state.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_advanced_filters.js?v={_desk_asset_v('public/js/pp2_planning_advanced_filters.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_evidence_drawer.js?v={_desk_asset_v('public/js/pp2_planning_evidence_drawer.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_selected_summary_panel.js?v={_desk_asset_v('public/js/pp2_planning_selected_summary_panel.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_include_plan_modal.js?v={_desk_asset_v('public/js/pp2_planning_include_plan_modal.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_create_package_modal.js?v={_desk_asset_v('public/js/pp2_planning_create_package_modal.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_summary.js?v={_desk_asset_v('public/js/pp2_planning_summary.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_home_item_card.js?v={_desk_asset_v('public/js/pp2_planning_home_item_card.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_home_queue_section.js?v={_desk_asset_v('public/js/pp2_planning_home_queue_section.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_home_queues.js?v={_desk_asset_v('public/js/pp2_planning_home_queues.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_home.js?v={_desk_asset_v('public/js/pp2_planning_home.js')}",
	f"/assets/kentender_procurement/js/pp2_planning_router.js?v={_desk_asset_v('public/js/pp2_planning_router.js')}",
	f"/assets/kentender_procurement/js/procurement_home_workspace.js?v={_desk_asset_v('public/js/procurement_home_workspace.js')}",
	f"/assets/kentender_procurement/js/tm2_workbench_lifecycle.js?v={_desk_asset_v('public/js/tm2_workbench_lifecycle.js')}",
	f"/assets/kentender_procurement/js/std_engine_desk_boot.js?v={_desk_asset_v('public/js/std_engine_desk_boot.js')}",
]

# include js, css files in header of web template
# web_include_css = "/assets/kentender_procurement/css/kentender_procurement.css"
# web_include_js = "/assets/kentender_procurement/js/kentender_procurement.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_procurement/public/scss/website"

# Doc 9 §18.1 — supplier portal URLs (`/supplier/tenders`, `/supplier/tenders/<tender_code>`).
# Resolves dynamic detail paths to ``www/supplier/tenders`` (same shell as list).
website_route_rules = [
	{"from_route": "/supplier/tenders/<tender_code>", "to_route": "supplier/tenders"},
]

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in doctype views
doctype_js = {
	"Procurement Package": "public/js/procurement_package.js",
}

# Never append ?v= to page_js values — Frappe resolves them as disk paths (meta.py get_code_files_via_hooks).
page_js = {
	"plc-procurement-journey": "public/js/procurement_journey_page.js",
	"plc-module-journey-context": "public/js/plc_module_journey_context_page.js",
	"tender-management-v2": "public/js/tender_management_v2_workbench_page.js",
	"std-engine": [
		"public/js/std_library/action_availability.js",
		"public/js/std_library/summary_data.js",
		"public/js/std_library/templates_data.js",
		"public/js/std_library/import_wizard_data.js",
		"public/js/std_library/std_library_api.js",
		"public/js/std_library/std_library_user_messages.js",
		"public/js/std_library/std_library_import_wizard_shell.js",
		"public/js/std_library/std_library_shell_detail_renderers.js",
		"public/js/std_library/std_library_shell.js",
		"public/js/std_engine_page.js",
	],
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender_procurement/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kentender_procurement.utils.jinja_methods",
# 	"filters": "kentender_procurement.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_procurement.install.before_install"
# after_install = "kentender_procurement.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender_procurement.uninstall.before_uninstall"
# after_uninstall = "kentender_procurement.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_procurement.utils.before_app_install"
# after_app_install = "kentender_procurement.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_procurement.utils.before_app_uninstall"
# after_app_uninstall = "kentender_procurement.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_procurement.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Demand": "kentender_procurement.demand_intake.permissions.demand_permissions.get_permission_query_conditions_for_demand",
	"Procurement Plan": "kentender_procurement.procurement_planning.permissions.pp_record_permissions.get_permission_query_conditions_for_procurement_plan",
	"Procurement Package": "kentender_procurement.procurement_planning.permissions.pp_record_permissions.get_permission_query_conditions_for_procurement_package",
	"Package Review Decision": "kentender_procurement.procurement_planning.permissions.pp_scope.get_permission_query_conditions_for_package_review_decision",
}

has_permission = {
	"Demand": "kentender_procurement.demand_intake.permissions.demand_permissions.demand_has_permission",
	"Procurement Plan": "kentender_procurement.procurement_planning.permissions.pp_record_permissions.procurement_plan_has_permission",
	"Procurement Package": "kentender_procurement.procurement_planning.permissions.pp_record_permissions.procurement_package_has_permission",
	"Package Review Decision": "kentender_procurement.procurement_planning.permissions.pp_scope.package_review_decision_has_permission",
}

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
# 		"kentender_procurement.tasks.all"
# 	],
# 	"daily": [
# 		"kentender_procurement.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender_procurement.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender_procurement.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender_procurement.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender_procurement.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender_procurement.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_procurement.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender_procurement.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender_procurement.utils.before_request"]
# after_request = ["kentender_procurement.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender_procurement.utils.before_job"]
# after_job = ["kentender_procurement.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kentender_procurement.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

after_migrate = [
	"kentender_procurement.setup.after_migrate_navigation.run",
	"kentender_procurement.tender_management.seeds.std_template_governance_roles.run_after_migrate",
	"kentender_procurement.tender_management.seeds.std_template_governance_seed.run_after_migrate",
]

boot_session = [
	"kentender_procurement.setup.workspace_permissions.patch_bootinfo",
]

# Optional hooks for downstream tendering implementations (v2+). Each path: dotted ``callable(payload: dict)``.
release_procurement_package_to_tender = [
	"kentender_procurement.tender_management.services.release_procurement_package_to_tender.hook_release_procurement_package_to_tender",
]

fixtures = [
	{"dt": "DocType", "filters": [["name", "=", "Procurement Navigation"]]},
	{
		"dt": "Workspace",
		"filters": [
			[
				"name",
				"in",
				[
					"Demand Intake and Approval",
					"Governance & Configuration",
					"Procurement Home",
					"Procurement Planning",
				],
			]
		],
	},
	{
		"dt": "Workspace Sidebar",
		"filters": [
			[
				"name",
				"in",
				["Procurement", "Demand Intake", "Planning module navigation"],
			]
		],
	},
]

