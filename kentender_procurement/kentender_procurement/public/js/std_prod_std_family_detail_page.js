(function () {
	"use strict";

	var STD_FAMILY_DETAIL_ASSET =
		"/assets/kentender_procurement/std_prod_impl/std_family_detail.html";

	frappe.pages["std-family-detail"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("STD Family Detail"),
			single_column: true,
		});

		document.body.classList.add("std-prod-std-family-detail-shell");

		var root = page.main.get(0);
		if (!root) {
			return;
		}

		root.className = "std-prod-std-family-detail-root";
		root.setAttribute("data-testid", "std-prod-std-family-detail-root");
		root.innerHTML =
			'<section class="std-prod-std-family-detail-shell" data-testid="std-prod-std-family-detail-shell">' +
			'<iframe class="std-prod-std-family-detail-iframe" data-testid="std-prod-std-family-detail-iframe" src="' +
			STD_FAMILY_DETAIL_ASSET +
			'" title="STD Family Detail"></iframe>' +
			"</section>";

		var iframe = root.querySelector(".std-prod-std-family-detail-iframe");
		if (iframe) {
			wire_std_family_version_actions(iframe);
		}
	};

	var VERSION_ACTION_ICONS = ["open_in_new", "edit", "visibility"];

	function wire_std_family_version_actions(iframe) {
		iframe.addEventListener("load", function () {
			var doc = iframe.contentDocument;
			if (!doc) {
				return;
			}

			doc.querySelectorAll("tbody tr").forEach(function (row) {
				row.querySelectorAll("button").forEach(function (btn) {
					var icon = btn.querySelector(".material-symbols-outlined");
					if (!icon || btn.dataset.stdProdWired === "1") {
						return;
					}
					var icon_name = (icon.textContent || "").trim();
					if (VERSION_ACTION_ICONS.indexOf(icon_name) === -1) {
						return;
					}
					btn.dataset.stdProdWired = "1";
					btn.addEventListener("click", function (event) {
						event.preventDefault();
						frappe.set_route("std-version-detail");
					});
				});
			});
		});
	}

	frappe.pages["std-family-detail"].on_page_show = function () {
		document.body.classList.add("std-prod-std-family-detail-shell");
	};

	frappe.pages["std-family-detail"].on_page_hide = function () {
		document.body.classList.remove("std-prod-std-family-detail-shell");
	};
})();
