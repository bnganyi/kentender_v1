from pathlib import Path


def _asset_version(rel_path: str) -> int:
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


def _desk_asset_v(rel_path: str) -> int:
	"""Cache-bust string for app_include: combine asset + hooks mtime so any edit rebusts.

	Editing only JS/CSS does not reload this module — touch hooks.py (or restart)
	so Desk boot emits a new ?v= and browsers drop stale fixture functions.
	clear-cache alone is not enough while the worker still holds the old import.
	Touched: PLN-UI-07 Finance confirmation drawer overlay (flex dim + panel).
	"""
	try:
		base = Path(__file__).resolve().parent
		a = (base / rel_path).stat()
		h = (base / "hooks.py").stat()
		# Use nanosecond precision + file size to avoid same-second cache-bust collisions.
		return int((a.st_mtime_ns + h.st_mtime_ns + a.st_size + h.st_size) % 2_147_483_647)
	except OSError:
		return 1


app_name = "kentender_procurement"
app_title = "KenTender"
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
	# authorization_surfaces.css and kt_industry_tokens.css are already loaded
	# globally by kentender_core/hooks.py — this app depends on kentender_core
	# (required_apps above), so re-declaring them here was a pure duplicate
	# download, not a second real inclusion.
	f"/assets/kentender_procurement/css/procurement_home_workspace.css?v={_desk_asset_v('public/css/procurement_home_workspace.css')}",
	f"/assets/kentender_procurement/css/procurement_home_page.css?v={_desk_asset_v('public/css/procurement_home_page.css')}",
	f"/assets/kentender_procurement/css/procurement_journey_page.css?v={_desk_asset_v('public/css/procurement_journey_page.css')}",
	f"/assets/kentender_procurement/css/module_journey_context_header.css?v={_desk_asset_v('public/css/module_journey_context_header.css')}",
	f"/assets/kentender_procurement/css/tm2_tender_handoff_panel.css?v={_desk_asset_v('public/css/tm2_tender_handoff_panel.css')}",
	f"/assets/kentender_procurement/css/business_readiness_summary.css?v={_desk_asset_v('public/css/business_readiness_summary.css')}",
	f"/assets/kentender_procurement/css/tender_management_v2_workbench.css?v={_desk_asset_v('public/css/tender_management_v2_workbench.css')}",
	# The legacy std-* "std_prod" route family's own CSS is now lazy-loaded by
	# each of its page_js controllers alongside std_prod_engine.js (see below).
	# coming_soon_page.css: now lazy-loaded by coming_soon_page.js's own
	# on_page_load. bid_submissions_page.css: bid_submissions_page.js already
	# had its own ensureCss() fallback link-injection for exactly this case.
	f"/assets/kentender_procurement/css/departmental_needs.css?v={_desk_asset_v('public/css/departmental_needs.css')}",
	f"/assets/kentender_procurement/css/departmental_needs_forms.css?v={_desk_asset_v('public/css/departmental_needs_forms.css')}",
	f"/assets/kentender_procurement/css/planning_workspace.css?v={_desk_asset_v('public/css/planning_workspace.css')}",
]
app_include_js = [
	f"/assets/kentender_procurement/js/procurement_sidebar_header.js?v={_desk_asset_v('public/js/procurement_sidebar_header.js')}",
	# The whole "planning" route family's fixtures/binds/dialogs used to load
	# here globally (every Desk page, not just planning ones) — each is now
	# lazy-loaded by its own page_js controller via frappe.require() instead
	# (planning_workspace_page.js, planning_register_page.js,
	# planning_builder_page.js, planning_item_editor_page.js,
	# planning_review_page.js, planning_approved_page.js).
	f"/assets/kentender_procurement/js/planning_workspace_redirect.js?v={_desk_asset_v('public/js/planning_workspace_redirect.js')}",
	f"/assets/kentender_procurement/js/module_journey_context_header.js?v={_desk_asset_v('public/js/module_journey_context_header.js')}",
	# std_prod_engine.js (the legacy std-* route family's shared engine, ~4900
	# lines) is now lazy-loaded by each of its 7 page_js controllers instead.
	f"/assets/kentender_procurement/js/business_readiness_summary.js?v={_desk_asset_v('public/js/business_readiness_summary.js')}",
	f"/assets/kentender_procurement/js/tm2_tender_handoff_panel.js?v={_desk_asset_v('public/js/tm2_tender_handoff_panel.js')}",
	f"/assets/kentender_procurement/js/workspace_list_selection_utils.js?v={_desk_asset_v('public/js/workspace_list_selection_utils.js')}",
	f"/assets/kentender_procurement/js/procurement_home_workspace.js?v={_desk_asset_v('public/js/procurement_home_workspace.js')}",
	f"/assets/kentender_procurement/js/tm2_workbench_lifecycle.js?v={_desk_asset_v('public/js/tm2_workbench_lifecycle.js')}",
	f"/assets/kentender_procurement/js/it_tender_configuration_create_modal.js?v={_desk_asset_v('public/js/it_tender_configuration_create_modal.js')}",
	f"/assets/kentender_procurement/js/electronic_bid/bidder_workspace_renderer.js?v={_desk_asset_v('public/js/electronic_bid/bidder_workspace_renderer.js')}",
	# support_plan_view.js is already the page_js controller for route
	# "support-plan-view" (Frappe lazy-loads it on navigation) — this was a
	# pure duplicate global load with zero benefit.
]

# include js, css files in header of web template
# web_include_css = "/assets/kentender_procurement/css/kentender_procurement.css"
# web_include_js = "/assets/kentender_procurement/js/kentender_procurement.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_procurement/public/scss/website"

# Doc 9 §18.1 — supplier portal URLs (`/supplier/tenders`, `/supplier/tenders/<tender_code>`).
# Resolves dynamic detail paths to ``www/supplier/tenders`` (same shell as list).
website_route_rules = [
	# Prompt canonical alias → thin Website page that redirects into Desk.
	{"from_route": "/procurement/home", "to_route": "procurement/home"},
	{"from_route": "/supplier/tenders/<tender_code>", "to_route": "supplier/tenders"},
	{
		"from_route": "/tenders/<publication_ref>/review-and-validate",
		"to_route": "tenders/review_and_validate",
	},
	{
		"from_route": "/tenders/<publication_ref>/final-bid-review",
		"to_route": "tenders/final_bid_review",
	},
	{
		"from_route": "/tenders/<publication_ref>/submit-bid",
		"to_route": "tenders/submit_bid",
	},
	{
		"from_route": "/tenders/<publication_ref>/submission-receipt",
		"to_route": "tenders/submission_receipt",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/form_of_tender",
		"to_route": "tenders/form_of_tender",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/confidential_business_questionnaire",
		"to_route": "tenders/confidential_business_questionnaire",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/statutory_declarations",
		"to_route": "tenders/statutory_declarations",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/tender_security",
		"to_route": "tenders/tender_security",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/preliminary_requirements_and_evidence",
		"to_route": "tenders/preliminary_requirements",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/qualification_and_capability/<category_key>",
		"to_route": "tenders/qualification_category",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/qualification_and_capability",
		"to_route": "tenders/qualification_and_capability",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan/review",
		"to_route": "tenders/technical_proposal_review",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan/<subsection_key>",
		"to_route": "tenders/technical_proposal_subsection",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan",
		"to_route": "tenders/technical_proposal_and_implementation_plan",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/requirements_compliance/review",
		"to_route": "tenders/requirements_compliance_review",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/requirements_compliance",
		"to_route": "tenders/requirements_compliance",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/price_schedule/review",
		"to_route": "tenders/price_schedule_review",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/price_schedule/schedules/<schedule_key>",
		"to_route": "tenders/price_schedule_schedule",
	},
	{
		"from_route": "/tenders/<publication_ref>/sections/price_schedule",
		"to_route": "tenders/price_schedule",
	},
	{"from_route": "/tenders/<publication_ref>/sections/<section_key>", "to_route": "tenders/section"},
	{"from_route": "/tenders/<publication_ref>/documents", "to_route": "tenders/documents"},
	{"from_route": "/tenders/<publication_ref>/evidence", "to_route": "tenders/evidence"},
	{"from_route": "/tenders/<publication_ref>/issues", "to_route": "tenders/issues"},
	{"from_route": "/tenders/<publication_ref>/workspace", "to_route": "tenders/workspace"},
	{"from_route": "/tenders/<publication_ref>", "to_route": "tenders/overview"},
]

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in doctype views
doctype_js = {
}

# Never append ?v= to page_js values — Frappe resolves them as disk paths (meta.py get_code_files_via_hooks).
page_js = {
	"support-plan-view": "public/js/support_plan_view.js",
	"departmental-needs": "public/js/departmental_needs_page.js",
	"departmental-needs-new": "public/js/departmental_needs_create_page.js",
	"departmental-needs-edit": "public/js/departmental_needs_create_page.js",
	"departmental-needs-review": "public/js/departmental_needs_review_page.js",
	"departmental-needs-detail": "public/js/departmental_needs_detail_page.js",
	"kt-procurement-home": "public/js/procurement_home_page.js",
	"plc-procurement-journey": "public/js/procurement_journey_page.js",
	"plc-module-journey-context": "public/js/plc_module_journey_context_page.js",
	"tender-management-v2": "public/js/tender_management_v2_workbench_page.js",
	"it-std-wizard-retired": "public/js/it_std_wizard_retired_page.js",
	"kt-cl-shell-poc": "public/js/kt_cl_shell_poc_page.js",
	"it-tender-configuration-dashboard": "public/js/it_tender_configurations_dashboard_page.js",
	"it-tender-configuration-overview": "public/js/it_tender_configuration_overview_page.js",
	"it-tender-configuration-tender-profile": "public/js/it_tender_configuration_tender_profile_page.js",
	"it-tender-configuration-tds": "public/js/it_tender_configuration_tds_page.js",
	"it-tender-configuration-it-requirements": "public/js/it_tender_configuration_it_requirements_page.js",
	"it-tender-configuration-implementation-schedule": "public/js/it_tender_configuration_implementation_schedule_page.js",
	"it-tender-configuration-system-inventory": "public/js/it_tender_configuration_system_inventory_page.js",
	"it-tender-configuration-price-schedule": "public/js/it_tender_configuration_price_schedule_page.js",
	"it-tender-configuration-evaluation-setup": "public/js/it_tender_configuration_evaluation_setup_page.js",
	"it-tender-configuration-forms-and-evidence": "public/js/it_tender_configuration_forms_and_evidence_page.js",
	"it-tender-configuration-scc": "public/js/it_tender_configuration_scc_page.js",
	"it-tender-configuration-validation-report": "public/js/it_tender_configuration_validation_report_page.js",
	"it-tender-configuration-review-and-approval": "public/js/it_tender_configuration_review_and_approval_page.js",
	"it-tender-configuration-render-preview": "public/js/it_tender_configuration_render_preview_page.js",
	"it-tender-configuration-publication-readiness": "public/js/it_tender_configuration_render_preview_page.js",
	"it-tender-package-review": "public/js/it_tender_package_review_page.js",
	"coming-soon": "public/js/coming_soon_page.js",
	"publications": "public/js/publications_page.js",
	"planning-workspace": "public/js/planning_workspace_page.js",
	"procurement-plan-register": "public/js/planning_register_page.js",
	"procurement-plan-builder": "public/js/planning_builder_page.js",
	"procurement-plan-item-editor": "public/js/planning_item_editor_page.js",
	"procurement-plan-review": "public/js/planning_review_page.js",
	"procurement-plan-approved": "public/js/planning_approved_page.js",
	"publication-setup": "public/js/publication_setup_page.js",
	"published-tender-overview": "public/js/published_tender_overview_page.js",
	"bid-submissions": "public/js/bid_submissions_page.js",
	"it-electronic-bidder-workspace": "public/js/it_electronic_bidder_workspace_page.js",
	# STD-CHG-001 v1.3 Phase 11 — new Vue-in-Desk STD Configuration surfaces
	# (STD-UI-*/PCFG-*/STD-WF-*). Distinct route names from the "std-*" legacy
	# std_engine pages below, which remain live pending Phase 12 retirement.
	"std-cfg-documents": "public/js/std_cfg_documents_page.js",
	# "std-cfg-package" (unsuffixed) collides with the auto-generated Desk
	# route for the "STD Cfg Package" DocType — confirmed live: it opened the
	# DocType's form view instead of this Vue page. "-home" avoids every
	# current and future "STD Cfg *" DocType's own auto-slug.
	"std-cfg-package-home": "public/js/std_cfg_package_page.js",
	"std-cfg-area": "public/js/std_cfg_area_page.js",
	"std-cfg-readiness": "public/js/std_cfg_readiness_page.js",
	"std-cfg-review": "public/js/std_cfg_review_page.js",
	"std-cfg-comparison": "public/js/std_cfg_comparison_page.js",
	"std-library": "public/js/std_prod_std_library_page.js",
	"std-family-detail": "public/js/std_prod_std_family_detail_page.js",
	"std-version-detail": "public/js/std_prod_std_version_detail_page.js",
	"std-source-doc": "public/js/std_prod_vertical_slice_pages.js",
	"std-section-clauses": "public/js/std_prod_vertical_slice_pages.js",
	"std-clause-detail": "public/js/std_prod_vertical_slice_pages.js",
	"std-validation-report": "public/js/std_prod_vertical_slice_pages.js",
	"std-audit-log": "public/js/std_prod_vertical_slice_pages.js",
	"std-parameter-dictionary": "public/js/std_prod_schema_pages.js",
	"std-parameter-detail": "public/js/std_prod_schema_pages.js",
	"std-rule-dictionary": "public/js/std_prod_schema_pages.js",
	"std-rule-detail": "public/js/std_prod_schema_pages.js",
	"std-form-schema-manager": "public/js/std_prod_schema_pages.js",
	"std-form-detail-field-builder": "public/js/std_prod_schema_pages.js",
	"std-requirement-schema-manager": "public/js/std_prod_schema_pages.js",
	"std-price-schedule-schema": "public/js/std_prod_schema_pages.js",
	"std-evaluation-schema": "public/js/std_prod_schema_pages.js",
	"std-render-blocks": "public/js/std_prod_schema_pages.js",
	"std-review-and-approval": "public/js/std_prod_governance_pages.js",
	"std-usage-and-tender-bindings": "public/js/std_prod_governance_pages.js",
	"std-import-package-review": "public/js/std_prod_governance_pages.js",
	"std-version-diff-and-supersession": "public/js/std_prod_governance_pages.js",
	"std-module-retired": "public/js/std_module_retired_page.js",
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
}

has_permission = {
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"File": {
		"on_trash": "kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas.prevent_cas_file_trash",
	},
}

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
]

boot_session = [
	"kentender_procurement.setup.workspace_permissions.patch_bootinfo",
]

# Optional hooks for downstream tendering implementations (v2+). Each path: dotted ``callable(payload: dict)``.
# PP2 retired: release_procurement_package_to_tender removed

fixtures = [
	{"dt": "DocType", "filters": [["name", "=", "Procurement Navigation"]]},
	{
		"dt": "Workspace",
		"filters": [
			[
				"name",
				"in",
				[
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
				["Procurement", "Planning module navigation"],
			]
		],
	},
	{
		"dt": "Desktop Icon",
		"filters": [["name", "in", ["Procurement", "Tenders"]]],
	},
]









