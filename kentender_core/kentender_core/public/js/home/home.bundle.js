import { createApp } from "vue";
import Home from "./Home.vue";

frappe.kt_mount_home = function (el) {
	const app = createApp(Home);
	// AGENTS.md §6.1 — SFC templates compile `__("…")` into `_ctx.__(…)`, so the
	// translation helper and frappe itself must be bound onto globalProperties;
	// without them every template render throws and the page stays blank.
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
