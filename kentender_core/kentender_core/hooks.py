from pathlib import Path


def _asset_version(rel_path: str) -> int:
	# mtime-based cache bust; touch this file after CSS edits so workers re-import hooks.
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


app_name = "kentender_core"
app_title = "Kentender Core"
app_publisher = "KenTender"
app_description = "KenTender core platform foundation."
app_email = "dev@kentender.local"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender_core",
# 		"logo": "/assets/kentender_core/logo.png",
# 		"title": "Kentender Core",
# 		"route": "/kentender_core",
# 		"has_permission": "kentender_core.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/kentender_core/css/authorization_surfaces.css?v={_asset_version('public/css/authorization_surfaces.css')}",
	"/assets/kentender_core/css/kentender_desk_builder_layout.css",
	f"/assets/kentender_core/css/kt_module_shell.css?v={_asset_version('public/css/kt_module_shell.css')}",
	f"/assets/kentender_core/css/kt_workbench_typography.css?v={_asset_version('public/css/kt_workbench_typography.css')}",
	f"/assets/kentender_core/css/kt_cl_fonts.css?v={_asset_version('public/css/kt_cl_fonts.css')}",
	f"/assets/kentender_core/css/civic_ledger.css?v={_asset_version('public/css/civic_ledger.css')}",
	f"/assets/kentender_core/css/kt_cl_code_layout.css?v={_asset_version('public/css/kt_cl_code_layout.css')}",
	f"/assets/kentender_core/css/kt_native_sidebar_civic.css?v={_asset_version('public/css/kt_native_sidebar_civic.css')}",
	# Stitch Desk chrome baseline — Desk bleed defeat (Win98 buttons, select chevron, Espresso 400).
	f"/assets/kentender_core/css/kt_stitch_desk_chrome.css?v={_asset_version('public/css/kt_stitch_desk_chrome.css')}",
	# Shared Stitch list-table footer (Showing X of Y + Rows per page + pager).
	f"/assets/kentender_core/css/kt_stitch_table_footer.css?v={_asset_version('public/css/kt_stitch_table_footer.css')}",
	# Shared "Industry" design-system tokens (CFG-CHG-002 and future Vue-in-Desk-page
	# modules) — scoped under .kt-industry, never :root; safe to load globally.
	f"/assets/kentender_core/css/kt_industry_tokens.css?v={_asset_version('public/css/kt_industry_tokens.css')}",
	# AUTH-ADR-001 v1.3 §12 — page compositions for the two Configuration and
	# Governance surfaces, in a static file because the esbuild pipeline
	# discards <style scoped> CSS (no dist/css output, no assets.json entry).
	# Same delivery as NDS/Planning's *_industry.css; every rule is scoped
	# under .kt-industry with page-unique class names.
	f"/assets/kentender_core/css/kt_admin_configuration.css?v={_asset_version('public/css/kt_admin_configuration.css')}",
]
boot_session = ["kentender_core.services.my_work.patch_bootinfo_home"]

app_include_js = [
	f"/assets/kentender_core/js/kt_desk_document_title.js?v={_asset_version('public/js/kt_desk_document_title.js')}",
	# Field-error helper — load early so Strategy / workbench binders can use ktFormErrors.
	f"/assets/kentender_core/js/kt_form_errors.js?v={_asset_version('public/js/kt_form_errors.js')}",
	f"/assets/kentender_core/js/kt_module_registry.js?v={_asset_version('public/js/kt_module_registry.js')}",
	f"/assets/kentender_core/js/kt_module_shell.js?v={_asset_version('public/js/kt_module_shell.js')}",
	f"/assets/kentender_core/js/kt_cl_code_spec.js?v={_asset_version('public/js/kt_cl_code_spec.js')}",
	f"/assets/kentender_core/js/kt_cl_components.js?v={_asset_version('public/js/kt_cl_components.js')}",
	f"/assets/kentender_core/js/kt_cl_sidebar.js?v={_asset_version('public/js/kt_cl_sidebar.js')}",
	f"/assets/kentender_core/js/kt_cl_shell.js?v={_asset_version('public/js/kt_cl_shell.js')}",
	f"/assets/kentender_core/js/kt_desk_page.js?v={_asset_version('public/js/kt_desk_page.js')}",
	f"/assets/kentender_core/js/kt_page_lifecycle.js?v={_asset_version('public/js/kt_page_lifecycle.js')}",
	f"/assets/kentender_core/js/kt_cl_surface_registry.js?v={_asset_version('public/js/kt_cl_surface_registry.js')}",
	f"/assets/kentender_core/js/kt_cl_shell_router.js?v={_asset_version('public/js/kt_cl_shell_router.js')}",
	f"/assets/kentender_core/js/kt_stitch_table_footer.js?v={_asset_version('public/js/kt_stitch_table_footer.js')}",
	f"/assets/kentender_core/js/kt_stitch_table_pager.js?v={_asset_version('public/js/kt_stitch_table_pager.js')}",
	f"/assets/kentender_core/js/kt_ds_recipes.js?v={_asset_version('public/js/kt_ds_recipes.js')}",
]

# include js, css files in header of web template
# web_include_css = "/assets/kentender_core/css/kentender_core.css"
# web_include_js = "/assets/kentender_core/js/kentender_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# Never append ?v= to page_js values — Frappe resolves them as disk paths.
page_js = {
	"kt-cl-components": "public/js/kt_cl_components_gallery_page.js",
	# CFG-CHG-002 v0.6 §9 / AUTH-ADR-001 v1.6 §12 — the one System setup page.
	# page_js is Frappe's own lazy mechanism: the controller loads only when
	# the user navigates to that exact route, and pulls its Vue bundle with
	# frappe.require() (AGENTS.md §6.9). The former organisation-structure and
	# user-responsibilities pages are removed without an alias (§12).
	"system-setup": "public/js/system_setup_page.js",
	"user-operational-acc": "public/js/authorization_admin_pages.js",
	"workflow-routing-rul": "public/js/authorization_admin_pages.js",
	"access-diagnostic": "public/js/authorization_admin_pages.js",
	"reference-data": "public/js/reference_data_page.js",
}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender_core/public/icons.svg"

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
# 	"methods": "kentender_core.utils.jinja_methods",
# 	"filters": "kentender_core.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_core.install.before_install"
after_install = "kentender_core.install.after_install"

after_migrate = "kentender_core.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "kentender_core.uninstall.before_uninstall"
# after_uninstall = "kentender_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_core.utils.before_app_install"
# after_app_install = "kentender_core.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_core.utils.before_app_uninstall"
# after_app_uninstall = "kentender_core.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_core.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Capability Profile": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Operational Scope Assignment": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Workflow Queue": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Workflow Queue Membership": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Workflow Routing Rule": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Workflow Task": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Authorization Delegation": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
	"Separation of Duties Rule": {
		"validate": "kentender_core.services.authorization_records.validate_authorization_record",
		"on_update": "kentender_core.services.authorization_records.invalidate_authorization_cache",
	},
}

# Scheduled Tasks
# ---------------

# CFG-CHG-002 §6.3 — automated PE/FY Context activation (active_from reached)
# and closure (active_to reached), each with its own scheduler audit event.
scheduler_events = {
	"cron": {
		"*/5 * * * *": [
			"kentender_core.services.reference_data_transitions.run_scheduled_context_transitions"
		],
	},
	"hourly": [
		# CFG-CHG-002 v0.6 CFG-BR-008 — close needs submission when the
		# configured instant passes, audited with System as actor. A
		# convenience, never the security control (§11.3).
		"kentender_core.services.site_configuration.close_due_needs_submissions",
		# CFG-CHG-002 v0.9 §4.2 — the same closure for departmental-plan intake.
		"kentender_core.services.site_configuration.close_due_dpp_submissions",
	],
	"daily": [
		# AUTH-ADR-001 v1.6 §5.7 — remove Frappe Role projections left behind
		# by time-expired assignments. A lingering Role grants no business
		# authority on its own; this only prevents false orphan diagnostics.
		"kentender_core.services.responsibility_administration.reconcile_role_projections",
	],
}

# AUTH-ADR-001 v1.6 §5.3 — the declarative scope map. Each app declares which
# field carries the Organisation Unit on which of its DocTypes; the generic
# hook implementation in services/authorization.py reads the merged hook.
# Deliberately empty of production DocTypes here: §11.3 step 4 registers the
# predicate with no production caller switched — each module's cutover slice
# adds its own entries (and the matching permission_query_conditions /
# has_permission rows below) in that module's hooks.py.
kentender_scope_map: dict[str, str] = {}

# Testing
# -------

# before_tests = "kentender_core.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender_core.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_core.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender_core.utils.before_request"]
# after_request = ["kentender_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender_core.utils.before_job"]
# after_job = ["kentender_core.utils.after_job"]

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
# 	"kentender_core.auth.validate"
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
