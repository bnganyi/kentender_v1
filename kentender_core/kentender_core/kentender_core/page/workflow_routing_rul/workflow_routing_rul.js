// Real controller lives in public/js/authorization_admin_pages.js, wired via
// hooks.py's page_js override. This file is only Frappe's required Page
// doctype script asset — it must exist, but must stay empty: assigning
// frappe.pages['workflow-routing-rul'].on_page_load here as well raced the
// page_js override (both call make_app_page() on the same route) and threw
// on the second call.
