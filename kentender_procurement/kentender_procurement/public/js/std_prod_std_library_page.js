(function () {
	"use strict";

	var STD_LIBRARY_ASSET =
		"/assets/kentender_procurement/std_prod_impl/std_library.html";

	frappe.pages["std-library"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Official STD Library"),
			single_column: true,
		});

		document.body.classList.add("std-prod-std-library-shell");

		var root = page.main.get(0);
		if (!root) {
			return;
		}

		root.className = "std-prod-std-library-root";
		root.setAttribute("data-testid", "std-prod-std-library-root");
		root.innerHTML =
			'<section class="std-prod-std-library-shell" data-testid="std-prod-std-library-shell">' +
			'<iframe class="std-prod-std-library-iframe" data-testid="std-prod-std-library-iframe" src="' +
			STD_LIBRARY_ASSET +
			'" title="STD Library"></iframe>' +
			"</section>";

		var iframe = root.querySelector(".std-prod-std-library-iframe");
		if (iframe) {
			wire_std_library_open_actions(iframe);
		}
	};

	function wire_std_library_open_actions(iframe) {
		iframe.addEventListener("load", function () {
			var doc = iframe.contentDocument;
			if (!doc) {
				return;
			}

			doc.querySelectorAll("tbody tr").forEach(function (row) {
				var open_btn = Array.from(row.querySelectorAll("button")).find(function (btn) {
					return (btn.textContent || "").trim() === "Open";
				});
				if (!open_btn || open_btn.dataset.stdProdWired === "1") {
					return;
				}
				open_btn.dataset.stdProdWired = "1";
				open_btn.addEventListener("click", function (event) {
					event.preventDefault();
					frappe.set_route("std-family-detail");
				});
			});
		});
	}

	frappe.pages["std-library"].on_page_show = function () {
		document.body.classList.add("std-prod-std-library-shell");
	};

	frappe.pages["std-library"].on_page_hide = function () {
		document.body.classList.remove("std-prod-std-library-shell");
	};
})();
