import { createApp } from "vue";
import Award from "./Award.vue";

// AWD-CHG-001 v0.4 §9 / plan D13: the Award Page (/app/award and
// /app/award/{award_id}). kt_industry_page_rail.bundle.js and
// kt_industry_guidance.bundle.js load alongside from award_page.js
// (AGENTS.md §6.6: an isolated app with its own Vue runtime).
frappe.kt_mount_award = function (el) {
	const app = createApp(Award);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
