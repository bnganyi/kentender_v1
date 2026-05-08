// STD-LIB-0001 — Desk-wide hook so Page std-engine-advanced redirects without relying on page_js registration timing.
(function () {
	function redirectAdvancedCatalogue() {
		const r = frappe.get_route() || [];
		if (r[0] !== "std-engine-advanced") {
			return;
		}
		frappe.show_alert({
			message: __("Advanced Technical View — opening the STD Template catalogue."),
			indicator: "blue",
		});
		frappe.set_route("List", "STD Template");
	}

	function schedule() {
		setTimeout(redirectAdvancedCatalogue, 200);
	}

	$(document).on("page-change", schedule);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", schedule);
	}
})();
