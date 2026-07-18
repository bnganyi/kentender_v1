// UI-01 — Tender Configuration Home (thin stub for post-create / Continue).
(function () {
	"use strict";

	var SURFACE_ID = "UI-01";
	var API = "kentender_procurement.tender_configurations.get_tender_configuration";

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function configurationId() {
		if (frappe.route_options && frappe.route_options.configuration_id) {
			return frappe.route_options.configuration_id;
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			if (params.get("configuration_id")) {
				return params.get("configuration_id");
			}
		} catch (e) {
			/* ignore */
		}
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return route[1];
		}
		return null;
	}

	function stubHtml(data) {
		if (!data) {
			return (
				'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6" data-testid="kt-cl-ui01-stub">' +
				'<p class="text-body-md text-on-surface-variant">' +
				__("Select a tender configuration from the dashboard.") +
				"</p>" +
				'<button type="button" class="mt-4 h-8 px-4 rounded bg-primary text-on-primary text-label-sm" data-action="back">' +
				__("Back to Tender Configurations") +
				"</button></div>"
			);
		}
		return (
			'<div class="rounded border border-outline-variant bg-surface-container-lowest p-6 space-y-4" data-testid="kt-cl-ui01-stub">' +
			'<p class="text-label-md text-on-surface-variant uppercase">' +
			__("Tender Configuration Home") +
			"</p>" +
			'<h2 class="text-headline-lg font-bold text-primary" data-testid="kt-cl-ui01-title">' +
			frappe.utils.escape_html(data.tender_title || "") +
			"</h2>" +
			'<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-body-md">' +
			"<div><span class=\"text-label-sm text-on-surface-variant uppercase block\">" +
			__("Configuration Ref") +
			'</span><span data-testid="kt-cl-ui01-ref">' +
			frappe.utils.escape_html(data.configuration_ref || "") +
			"</span></div>" +
			"<div><span class=\"text-label-sm text-on-surface-variant uppercase block\">" +
			__("Status") +
			"</span><span data-testid=\"kt-cl-ui01-status\">" +
			frappe.utils.escape_html(data.status || "") +
			"</span></div>" +
			"<div><span class=\"text-label-sm text-on-surface-variant uppercase block\">" +
			__("Procurement Package Ref") +
			"</span>" +
			frappe.utils.escape_html(data.procurement_package_ref || "") +
			"</div>" +
			"<div><span class=\"text-label-sm text-on-surface-variant uppercase block\">" +
			__("STD Family") +
			"</span>" +
			frappe.utils.escape_html(data.std_family_label || "") +
			"</div></div>" +
			'<p class="text-body-sm text-on-surface-variant">' +
			__("Configuration steps (CFG-01…CFG-09) will appear here in a follow-on ticket.") +
			"</p>" +
			'<button type="button" class="h-8 px-4 rounded border border-primary text-primary text-label-sm" data-action="back" data-testid="kt-cl-ui01-back">' +
			__("Back to Tender Configurations") +
			"</button></div>"
		);
	}

	function mount(page) {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		var pageHeader =
			(surf && surf.chrome && surf.chrome.pageHeader) || {
				title: __("Tender Configuration Home"),
				hideBreadcrumbs: true,
			};
		if (surf && surf.chrome && surf.chrome.toolbar) {
			sh.updateChrome({ toolbar: surf.chrome.toolbar });
		}

		var id = configurationId();
		if (!id) {
			sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: stubHtml(null) });
			$(page.main)
				.find("[data-action='back']")
				.on("click", function () {
					frappe.set_route("it-tender-configuration-dashboard");
				});
			return;
		}

		frappe.call({
			method: API,
			args: { configuration_id: id },
			callback: function (r) {
				sh.mountContent(page.main, {
					pageHeader: pageHeader,
					mainHtml: stubHtml(r.message || null),
				});
				$(page.main)
					.find("[data-action='back']")
					.on("click", function () {
						frappe.set_route("it-tender-configuration-dashboard");
					});
			},
			error: function () {
				sh.mountContent(page.main, { pageHeader: pageHeader, mainHtml: stubHtml(null) });
			},
		});
	}

	frappe.pages["it-tender-configuration-overview"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Tender Configuration Home"),
			single_column: true,
		});
		wrapper.page = page;
		mount(page);
	};

	frappe.pages["it-tender-configuration-overview"].on_page_show = function (wrapper) {
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
})();
