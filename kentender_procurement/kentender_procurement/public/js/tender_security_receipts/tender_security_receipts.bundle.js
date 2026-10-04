import { createApp } from "vue";
import TenderSecurityReceipts from "./TenderSecurityReceipts.vue";

// Blind physical tender-security intake (BDS-CHG-001 v0.8 OD-G/OD-H).
// kt_industry_page_rail.bundle.js (kentender_core) and
// tender_security_receipts.bundle.css load alongside this bundle from
// tender_security_receipts_page.js; the rail mounts as its own Vue app.
frappe.kt_mount_tender_security_receipts = function (el) {
	const app = createApp(TenderSecurityReceipts);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
