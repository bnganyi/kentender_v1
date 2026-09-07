import { createApp } from "vue";
import ProcurementRequisitions from "./ProcurementRequisitions.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by procurement_requisitions_page.js — the rail mounts imperatively
// (its own isolated Vue app), never as a child component across bundle
// boundaries (AGENTS.md §6.6).
frappe.kt_mount_procurement_requisitions = function (el) {
	const app = createApp(ProcurementRequisitions);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
