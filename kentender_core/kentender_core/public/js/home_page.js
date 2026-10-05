// HOME-CHG-001 v0.6 §9 — Home at /app/home. Roles gate empty in the Page doctype
// (KT-STD-001 §3A.3): one server read returns the verdict and the data, and the screen
// shows the denied state in place for anyone who is not an internal user. One
// desk_page.register call (AGENTS.md §6.1); not registered in cl_surface_registry (§6.5).
// The two CSS bundles load only here, never app-wide: the design system's rules for the
// classes the Home board uses (generated, scoped under .kt-industry.kt-home), then the
// page layout.

/* global frappe */

kentender_core.desk_page.register("home", {
	title: __("Home"),
	bundles: ["home.bundle.js", "kt_home_ds.bundle.css", "home_page.bundle.css"],
	mount: (el) => frappe.kt_mount_home(el),
	sidebarWorkspaceKey: "procurement",
});
