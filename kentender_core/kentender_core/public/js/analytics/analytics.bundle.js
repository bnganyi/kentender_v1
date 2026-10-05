import { createApp } from "vue";
import Analytics from "./Analytics.vue";

frappe.kt_mount_analytics = function (el) {
	const app = createApp(Analytics);
	// AGENTS.md §6.1 — SFC templates compile `__("…")` into `_ctx.__(…)`, so the
	// translation helper and frappe itself must be bound onto globalProperties;
	// without them every template render throws and the page stays blank.
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
