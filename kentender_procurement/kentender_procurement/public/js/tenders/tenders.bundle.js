import { createApp } from "vue";
import Tenders from "./Tenders.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by tenders_page.js — the rail mounts imperatively (its own isolated
// Vue app), never as a child component across bundle boundaries (AGENTS.md §6.6).
frappe.kt_mount_tenders = function (el) {
	const app = createApp(Tenders);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
