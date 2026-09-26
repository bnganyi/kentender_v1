import { createApp } from "vue";
import StdTemplates from "./StdTemplates.vue";

// STD-TPL-001 v0.10 §11 — STD Templates. kt_industry_page_rail.bundle.js
// (kentender_core) and std_templates.bundle.css are required alongside this
// bundle by std_templates_page.js; the rail mounts imperatively as its own
// isolated Vue app (AGENTS.md §6.6).
frappe.kt_mount_std_templates = function (el) {
	const app = createApp(StdTemplates);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
