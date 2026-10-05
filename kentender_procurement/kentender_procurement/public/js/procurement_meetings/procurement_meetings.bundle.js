import { createApp } from "vue";
import ProcurementMeetings from "./ProcurementMeetings.vue";

// OVS-CHG-001 v0.6 §11: the Procurement meetings register Page (/app/procurement-meetings).
// kt_industry_page_rail.bundle.js and kt_industry_guidance.bundle.js load alongside from
// procurement_meetings_page.js.
frappe.kt_mount_procurement_meetings = function (el) {
	const app = createApp(ProcurementMeetings);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
