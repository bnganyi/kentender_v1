// ANL-CHG-001 v0.8 §9, §9.1 — Procurement Analytics at /desk/analytics[/<tab>]. Roles gate empty in the
// Page doctype (KT-STD-001 §3A.3): one server read returns the verdict and the data, and the screen shows
// the denied / no-area state in place. One desk_page.register call (AGENTS.md §6.1); not registered in
// cl_surface_registry (§6.5). The tab is a path segment and the applied filters live in the query string;
// the page writes its own history entries (docs/mvp-1-r1/19_analytics/reconciliation/route_spike.md).
// The two CSS bundles load only here, never app-wide: the design system's rules for the classes the
// Analytics boards use (generated, scoped under .kt-industry.kt-analytics), then the page layout.

/* global frappe */

kentender_core.desk_page.register("analytics", {
	title: __("Procurement Analytics"),
	bundles: ["analytics.bundle.js", "kt_analytics_ds.bundle.css", "analytics_page.bundle.css"],
	mount: (el) => frappe.kt_mount_analytics(el),
	sidebarWorkspaceKey: "procurement",
});
