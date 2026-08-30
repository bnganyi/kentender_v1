import { createApp } from "vue";
import ProcurementPlanning from "./ProcurementPlanning.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by procurement_planning_page.js — the rail mounts imperatively (its
// own isolated Vue app), never as a child component across bundle boundaries
// (AGENTS.md §6.6).
frappe.kt_mount_procurement_planning = function (el) {
	const app = createApp(ProcurementPlanning);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
