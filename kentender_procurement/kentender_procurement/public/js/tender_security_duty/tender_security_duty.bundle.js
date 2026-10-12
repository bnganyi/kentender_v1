import { createApp } from "vue";
import TenderSecurityDuty from "./TenderSecurityDuty.vue";

// Tender-security intake duty (Project Owner, 10 October 2026). The shared rail
// bundle and tender_security_receipts.bundle.css (the page layout it shares
// with the receipts page) load alongside this bundle from
// tender_security_duty_page.js.
frappe.kt_mount_tender_security_duty = function (el) {
	const app = createApp(TenderSecurityDuty);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
