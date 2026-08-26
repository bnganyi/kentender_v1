// Planned capability overview — hand-port of docs/misc/coming_soon_code.html
(function () {
	"use strict";

	var DEFAULT_FEATURE = "Home";

	function resolveFeatureName() {
		var opts = frappe.route_options || {};
		if (opts.feature) {
			return String(opts.feature);
		}
		try {
			var params = new URLSearchParams(window.location.search || "");
			var q = params.get("feature");
			if (q) {
				return decodeURIComponent(q);
			}
		} catch (e) {
			/* ignore */
		}
		var route = frappe.get_route_str ? frappe.get_route_str() : "";
		if (route && route.indexOf("?") >= 0) {
			try {
				var qs = route.split("?")[1] || "";
				var fromRoute = new URLSearchParams(qs).get("feature");
				if (fromRoute) {
					return decodeURIComponent(fromRoute);
				}
			} catch (e2) {
				/* ignore */
			}
		}
		return DEFAULT_FEATURE;
	}

	function escapeHtml(value) {
		return frappe.utils.escape_html(String(value || ""));
	}

	function render(wrapper, featureName) {
		var safe = escapeHtml(featureName);
		wrapper.innerHTML =
			'<div class="kt-coming-soon" data-testid="kt-coming-soon" data-feature="' +
			safe +
			'">' +
			'<div class="kt-coming-soon__glow" aria-hidden="true"></div>' +
			'<span class="kt-coming-soon__watermark material-symbols-outlined" aria-hidden="true">precision_manufacturing</span>' +
			'<div class="kt-coming-soon__card">' +
			'<div class="kt-coming-soon__icon-wrap">' +
			'<div class="kt-coming-soon__icon-main">' +
			'<span class="material-symbols-outlined" aria-hidden="true">architecture</span>' +
			"</div>" +
			'<div class="kt-coming-soon__icon-gear" aria-hidden="true">' +
			'<span class="material-symbols-outlined">settings</span>' +
			"</div>" +
			"</div>" +
			'<h1 class="kt-coming-soon__title" data-testid="kt-coming-soon-title">' +
			safe +
			"</h1>" +
			'<h2 class="kt-coming-soon__subtitle">' +
			__("Coming Soon") +
			"</h2>" +
			'<div class="kt-coming-soon__body">' +
			"<p>" +
			__(
				"{0} is planned for a future KenTender release. Our engineering and compliance teams are preparing this module for production use.",
				[safe]
			) +
			"</p>" +
			'<div class="kt-coming-soon__status" aria-hidden="true">' +
			'<div class="kt-coming-soon__dot kt-coming-soon__dot--available"></div>' +
			'<div class="kt-coming-soon__dot kt-coming-soon__dot--reserved"></div>' +
			"</div>" +
			"</div>" +
			'<div class="kt-coming-soon__actions">' +
			'<button type="button" class="kt-coming-soon__btn kt-coming-soon__btn--primary" data-action="notify">' +
			'<span class="material-symbols-outlined" aria-hidden="true">mail</span>' +
			__("Notify Me On Launch") +
			"</button>" +
			'<button type="button" class="kt-coming-soon__btn kt-coming-soon__btn--ghost" data-action="roadmap">' +
			__("View Development Roadmap") +
			"</button>" +
			"</div>" +
			"</div>" +
			"</div>";

		wrapper.querySelectorAll("[data-action]").forEach(function (btn) {
			btn.addEventListener("click", function () {
				frappe.show_alert({
					message: __("This capability overview will be updated when {0} ships.", [featureName]),
					indicator: "blue",
				});
			});
		});
	}

	function ensureProcurementRail() {
		var sh = window.kentender_core && kentender_core.cl_shell;
		if (sh && typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: { showSearch: false, showUserMeta: true },
			});
		}
	}

	frappe.pages["coming-soon"].on_page_load = function (wrapper) {
		frappe.require("/assets/kentender_procurement/css/coming_soon_page.css");
		ensureProcurementRail();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Coming Soon"),
			single_column: true,
		});
		page.main.addClass("kt-coming-soon-host");
		wrapper._kt_coming_soon_page = page;
		render(page.main.get(0), resolveFeatureName());
	};

	frappe.pages["coming-soon"].on_page_show = function (wrapper) {
		ensureProcurementRail();
		var page = wrapper._kt_coming_soon_page;
		if (!page) {
			return;
		}
		var feature = resolveFeatureName();
		page.set_title(feature);
		render(page.main.get(0), feature);
	};
})();
