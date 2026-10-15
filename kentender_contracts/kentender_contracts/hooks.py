app_name = "kentender_contracts"
app_title = "Kentender Contracts"
app_publisher = "KenTender"
app_description = "KenTender Contract Management."
app_email = "dev@kentender.local"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext", "kentender_core"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender_contracts",
# 		"logo": "/assets/kentender_contracts/logo.png",
# 		"title": "Kentender Contracts",
# 		"route": "/kentender_contracts",
# 		"has_permission": "kentender_contracts.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kentender_contracts/css/kentender_contracts.css"
# app_include_js = "/assets/kentender_contracts/js/kentender_contracts.js"

# include js, css files in header of web template
# web_include_css = "/assets/kentender_contracts/css/kentender_contracts.css"
# web_include_js = "/assets/kentender_contracts/js/kentender_contracts.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_contracts/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender_contracts/public/icons.svg"

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
# 	"methods": "kentender_contracts.utils.jinja_methods",
# 	"filters": "kentender_contracts.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_contracts.install.before_install"
# after_install = "kentender_contracts.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender_contracts.uninstall.before_uninstall"
# after_uninstall = "kentender_contracts.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_contracts.utils.before_app_install"
# after_app_install = "kentender_contracts.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_contracts.utils.before_app_uninstall"
# after_app_uninstall = "kentender_contracts.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_contracts.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": ["kentender_contracts.services.formation_end.sweep_signing_windows"],
	"daily": ["kentender_contracts.services.reporting.generate_scheduled"],
}

# scheduler_events = {
# 	"all": [
# 		"kentender_contracts.tasks.all"
# 	],
# 	"daily": [
# 		"kentender_contracts.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender_contracts.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender_contracts.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender_contracts.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender_contracts.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender_contracts.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_contracts.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender_contracts.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender_contracts.utils.before_request"]
# after_request = ["kentender_contracts.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender_contracts.utils.before_job"]
# after_job = ["kentender_contracts.utils.after_job"]

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
# 	"kentender_contracts.auth.validate"
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

# Native payment guards and unit references (plan D7, tracker CM8-306/307). The guard sits on the documents' own events because every
# route (desk, API, Journal Entry, reconciliation, import, background job) reaches them.
_guard = "kentender_contracts.native.payment_guard.on_event"
doc_events = {
	"Payment Entry": {**{event: _guard for event in ("validate", "before_submit", "before_update_after_submit")}, "on_cancel": "kentender_contracts.native.finance_events.on_payment_entry_cancel"},
	"Journal Entry": {event: _guard for event in ("before_submit", "before_update_after_submit")},
	"Purchase Receipt": {"on_submit": "kentender_contracts.native.adapter.assign_unit_references"},
	"Purchase Invoice": {"on_submit": "kentender_contracts.native.finance_events.on_purchase_invoice_submit"},
}

# The extra fields on ERPNext's own documents (plan D7, FU-CM-48): installed and kept present.
after_install = "kentender_contracts.native.fields.ensure"
after_migrate = ["kentender_contracts.native.fields.ensure"]

# Signing (plan D8): the simulation provider answers only on a simulation site and only for the consumer "contracts".
kt_trust_signing_services = ["kentender_contracts.simulation.signing.service"]

# The one Desk Page (plan Phase 3, tracker CM8-315). Never append ?v= to page_js values: Frappe resolves them as disk paths.
page_js = {"contracts": "public/js/contracts_page.js"}

# The slot Procurement's shared rail reserves for this module (kentender_core.services.navigation_overrides).
kt_navigation_overrides = ["kentender_contracts.navigation.overrides"]

# The synthetic contract-source provider (development only; answers only on a simulation site): kentender_core.services.contract_source_contract.
kt_contract_source_provider = ["kentender_contracts.simulation.sources.service"]
kt_contract_funding_provider = ["kentender_contracts.simulation.funding.service"]

# The contract screens' choices of one person or one native record (AGENTS.md section 6.12): kentender_core.services.record_picker.
kt_record_picker_sources = ["kentender_contracts.services.picker_sources.sources"]

# Contract Management is the Contracting receiver of Award's package, decision events and updates (AWD-IF-05; FU-CM-33: it declines where another receiver answers, unless named by `kt_award_contracting_receiver`).
kt_award_contracting_receivers = ["kentender_contracts.award_receiver.receiver"]

# Contract work on the Home page (HOME-CHG-001 v0.6 section 7; CM-CHG-001 v0.8 section 5.10, FU-CM-68): one function that answers for one actor and only reads.
kt_home_providers = ["kentender_contracts.services.home_provider.entries"]

# The supplier's side (CM-CHG-001 v0.8 section 9): `/supplier/contracts` and `/supplier/contracts/<contract>/...` on the shared supplier portal (kentender_core's `kt_portal`). The resolver answers the verdict;
# the bundle mounts the same screens the Desk page hosts, fed by the portal's route and transport.
website_route_rules = [
	{"from_route": "/supplier/contracts", "to_route": "kt_portal"},
	{"from_route": "/supplier/contracts/<path:portal_path>", "to_route": "kt_portal"},
]
kt_portal_surfaces = [
	{"key": "contracts", "prefix": "/supplier/contracts", "resolver": "kentender_contracts.portal.resolve", "bundle": "contracts_portal.bundle.js", "css": []},
]
