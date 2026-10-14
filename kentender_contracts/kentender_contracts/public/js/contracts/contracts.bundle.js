import { createApp } from "vue";
import Contracts from "./Contracts.vue";

// CM-CHG-001 v0.8 §9.0: the Contracts Page (/app/contracts). kt_industry_page_rail.bundle.js loads alongside from contracts_page.js
// (AGENTS.md §6.6: an isolated app with its own Vue runtime).
frappe.kt_mount_contracts = function (el) {
	const app = createApp(Contracts);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
