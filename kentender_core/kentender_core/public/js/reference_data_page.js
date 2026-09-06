// CFG-PEFY — Reference Data (Procuring Entities, Financial Years, PE/FY
// contexts) under one Page ("reference-data"); ReferenceData.vue branches on
// the tab/view segments.
kentender_core.desk_page.register("reference-data", {
	title: __("Reference Data"),
	bundles: ["reference_data.bundle.js"],
	mount: (el) => frappe.kt_mount_reference_data(el),
	sidebarWorkspaceKey: "procurement",
});
