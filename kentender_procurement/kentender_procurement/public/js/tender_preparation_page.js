// TPR-CHG-001 v0.6 §12 — one Page ("tender-preparation") owning the
// /app/tender-preparation prefix; every §12 route (workspace, Start
// {handoff_id}, editor {tender_id}, approval task {task_id}, approved view)
// is a path segment under it, exactly like Requisitions' single-page model.
kentender_core.desk_page.register("tender-preparation", {
	title: __("Tender Preparation"),
	bundles: ["kt_industry_page_rail.bundle.js", "tender_preparation.bundle.js"],
	mount: (el) => frappe.kt_mount_tender_preparation(el),
	sidebarWorkspaceKey: "procurement",
});
