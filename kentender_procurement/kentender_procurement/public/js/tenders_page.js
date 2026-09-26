// TPR-CHG-001 v0.12 §9 — one Page ("tenders") owning the /app/tenders prefix;
// every route (workspace, Start, the record's tasks and decision screens,
// publication, addenda, clarifications, cancellation, history) is a path
// segment under it, exactly like Procurement Requisitions' single-page model.
// The shared guidance bundle draws the §10.17 journey and next step.
kentender_core.desk_page.register("tenders", {
	title: __("Tenders"),
	bundles: ["kt_industry_page_rail.bundle.js", "kt_industry_guidance.bundle.js", "tenders.bundle.js"],
	mount: (el) => frappe.kt_mount_tenders(el),
	sidebarWorkspaceKey: "procurement",
});
