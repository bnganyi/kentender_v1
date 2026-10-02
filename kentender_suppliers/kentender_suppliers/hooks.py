from pathlib import Path


def _desk_asset_v(rel_path: str) -> int:
	try:
		base = Path(__file__).resolve().parent
		a = (base / rel_path).stat()
		h = (base / "hooks.py").stat()
		return int(
			(a.st_mtime_ns + h.st_mtime_ns + a.st_size + h.st_size) % 2_147_483_647
		)
	except OSError:
		return 1


app_name = "kentender_suppliers"
app_title = "Kentender Suppliers"
app_publisher = "KenTender Suppliers app"
app_description = "KenTender"
app_email = "dev@kentender.local"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext", "kentender_core"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender_suppliers",
# 		"logo": "/assets/kentender_suppliers/logo.png",
# 		"title": "Kentender Suppliers",
# 		"route": "/kentender_suppliers",
# 		"has_permission": "kentender_suppliers.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/kentender_suppliers/css/ktsm_supplier_workbench.css?v={_desk_asset_v('public/css/ktsm_supplier_workbench.css')}"
]
app_include_js = [
	f"/assets/kentender_suppliers/js/ktsm_supplier_workbench.js?v={_desk_asset_v('public/js/ktsm_supplier_workbench.js')}"
]

# include js, css files in header of web template
# web_include_css = "/assets/kentender_suppliers/css/kentender_suppliers.css"
# web_include_js = "/assets/kentender_suppliers/js/kentender_suppliers.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_suppliers/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"KTSM Supplier Profile": "public/js/ktsm_supplier_profile.js",
	# BDS-CHG-001 v0.8 plan OD-D — Suspend / Restore access with a reason.
	"Supplier Organisation": "public/js/supplier_organisation.js",
}

# BDS-CHG-001 v0.8 plan D1 — Supplier Accounts publishes the account
# provider Bid Submission reads (kentender_core supplier_account_contract).
kt_supplier_account_provider = ["kentender_suppliers.supplier_accounts.services.provider"]
# The canonical supplier account (BDS-CHG-001 v0.8 §10.1), seeded before the
# canonical Start bid (Bid Submission calls every hook entry).
kt_canonical_supplier_accounts = ["kentender_suppliers.supplier_accounts.seeds.canonical.ensure_canonical_supplier_accounts"]
# Any other seeded supplier account (browser-test worlds), same commands.
kt_seed_supplier_account = ["kentender_suppliers.supplier_accounts.seeds.canonical.ensure_supplier_account"]
# The complete business profile a seeded supplier is given (release 1.4): bids copy it.
kt_default_supplier_profile = ["kentender_suppliers.supplier_accounts.seeds.canonical.default_profile"]
kt_seed_supplier_account_removal = ["kentender_suppliers.supplier_accounts.seeds.canonical.remove_supplier_accounts"]

# BDS-CHG-001 v0.8 plan OD-B (slices 11.3–11.4): Supplier Accounts' portal
# surface — /account, /account/register, /account/verify. The page CSS is a
# static file because the esbuild pipeline discards <style scoped> CSS.
import os as _os


def _account_asset_version(rel: str) -> str:
	try:
		return str(int(_os.path.getmtime(_os.path.join(_os.path.dirname(__file__), rel))))
	except OSError:
		return "0"


kt_portal_surfaces = [
	{
		"key": "account",
		"prefix": "/account",
		"resolver": "kentender_suppliers.supplier_accounts.portal.resolve",
		"bundle": "supplier_account_portal.bundle.js",
		"css": [f"/assets/kentender_suppliers/css/supplier_account_portal.css?v={_account_asset_version('public/css/supplier_account_portal.css')}"],
	},
]

# The portal header names the organisation a signed-in supplier acts for.
kt_portal_identity_providers = ["kentender_suppliers.supplier_accounts.portal.identity_detail"]

# BDS-CHG-001 v0.8 §5.14 — suspended-access reviews in the shared My Work.
kt_my_work_providers = ["kentender_suppliers.supplier_accounts.services.my_work_provider.my_work_rows"]
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender_suppliers/public/icons.svg"

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
# 	"methods": "kentender_suppliers.utils.jinja_methods",
# 	"filters": "kentender_suppliers.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_suppliers.install.before_install"
# after_install = "kentender_suppliers.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender_suppliers.uninstall.before_uninstall"
# after_uninstall = "kentender_suppliers.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_suppliers.utils.before_app_install"
# after_app_install = "kentender_suppliers.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_suppliers.utils.before_app_uninstall"
# after_app_uninstall = "kentender_suppliers.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_suppliers.notifications.get_notification_config"

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
	"Supplier": {
		"validate": "kentender_suppliers.validators.supplier_hooks.validate_kentender_supplier",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kentender_suppliers.tasks.all"
# 	],
# 	"daily": [
# 		"kentender_suppliers.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender_suppliers.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender_suppliers.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender_suppliers.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender_suppliers.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender_suppliers.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_suppliers.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender_suppliers.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender_suppliers.utils.before_request"]
# after_request = ["kentender_suppliers.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender_suppliers.utils.before_job"]
# after_job = ["kentender_suppliers.utils.after_job"]

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
# 	"kentender_suppliers.auth.validate"
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

