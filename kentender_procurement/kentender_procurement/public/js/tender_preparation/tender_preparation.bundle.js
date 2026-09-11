import { createApp } from "vue";
import TenderPreparation from "./TenderPreparation.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by tender_preparation_page.js — the rail mounts imperatively.
frappe.kt_mount_tender_preparation = function (el) {
	const app = createApp(TenderPreparation);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
