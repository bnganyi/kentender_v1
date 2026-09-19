// TPR-CHG-001 v0.8 §11 — one Page ("tenders") owning the /app/tenders prefix;
// every route (workspace, Start, the record's tasks and decision screens,
// publication, addenda, inquiries, cancellation, history) is a path segment
// under it, exactly like Procurement Requisitions' single-page model.
kentender_core.desk_page.register("tenders", {
	title: __("Tenders"),
	bundles: ["kt_industry_page_rail.bundle.js", "tenders.bundle.js"],
	mount: (el) => frappe.kt_mount_tenders(el),
	sidebarWorkspaceKey: "procurement",
});
