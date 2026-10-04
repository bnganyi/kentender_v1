// STD-TPL-001 v0.10 §11 / STD-TPL-IMP-001 v1.0 §11 — one Page
// ("std-templates") owning /app/std-templates and /app/std-templates/{release_id}.
// Access is decided on the server for every read (inline Forbidden state);
// the page CSS loads here, never globally (AGENTS.md §6.9).
kentender_core.desk_page.register("std-templates", {
	title: __("STD Templates"),
	bundles: ["kt_industry_page_rail.bundle.js", "std_templates.bundle.js", "std_templates.bundle.css"],
	mount: (el) => frappe.kt_mount_std_templates(el),
	sidebarWorkspaceKey: "procurement",
});
