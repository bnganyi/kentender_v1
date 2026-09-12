import { createApp } from "vue";
import TechnicalSearch from "./TechnicalSearch.vue";

frappe.kt_mount_technical_search = function (el) {
	const app = createApp(TechnicalSearch);
	// AGENTS.md §6.1 — SFC templates compile `__("…")` into `_ctx.__(…)`, so
	// the translation helper and frappe itself must be bound onto
	// globalProperties; without them every template render throws and the page
	// stays blank with only a console error to show for it.
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
