// UI-M01 — Create Tender Configuration modal (C1-M2).
(function () {
	"use strict";

	frappe.provide("kentender_procurement.tender_configurations");

	var API_ELIGIBLE =
		"kentender_procurement.tender_configurations.get_eligible_procurement_packages";
	var API_CREATE =
		"kentender_procurement.tender_configurations.create_tender_configuration";

	var state = {
		open: false,
		packages: [],
		selected: null,
		preselectId: null,
		$listHost: null,
	};

	function comp() {
		return kentender_core.cl_components;
	}

	function optionLabel(pkg) {
		return (
			(pkg.planning_package_ref || "") +
			" — " +
			(pkg.procurement_title || "") +
			" · " +
			(pkg.std_family_label || "")
		);
	}

	function close() {
		state.open = false;
		state.selected = null;
		state.preselectId = null;
		$("body").find('[data-testid="kt-cl-uim01-overlay"]').remove();
	}

	function renderList($list) {
		var html = (state.packages || [])
			.map(function (pkg) {
				return (
					'<button type="button" class="w-full text-left px-3 py-2 hover:bg-surface-container-high border-b border-outline-variant/40 text-body-sm" data-package-id="' +
					frappe.utils.escape_html(pkg.package_id) +
					'" data-testid="kt-cl-uim01-option">' +
					frappe.utils.escape_html(optionLabel(pkg)) +
					"</button>"
				);
			})
			.join("");
		if (!html) {
			html =
				'<div class="px-3 py-4 text-body-sm text-on-surface-variant">' +
				__("No eligible packages found.") +
				"</div>";
		}
		$list.html(html);
	}

	function remount() {
		var c = comp();
		if (!c) {
			return;
		}
		var sel = state.selected;
		var html = c.createTenderConfigurationModal({
			hasSelection: !!sel,
			selectedLabel: sel ? optionLabel(sel) : "",
			canCreate: !!(sel && sel.can_create_configuration && sel.applicable_std_document_id),
			preview: sel || {},
		});
		$("body").find('[data-testid="kt-cl-uim01-overlay"]').remove();
		var $overlay = $(html).appendTo("body");
		bind($overlay);
		if (state.listOpen) {
			var $list = $overlay.find('[data-testid="kt-cl-uim01-package-list"]');
			$list.removeClass("hidden");
			renderList($list);
		}
	}

	function bind($overlay) {
		$overlay.on("click", '[data-action="close"], [data-action="cancel"]', function (e) {
			e.preventDefault();
			close();
		});
		$overlay.on("click", function (e) {
			if ($(e.target).is('[data-testid="kt-cl-uim01-overlay"]')) {
				close();
			}
		});
		$overlay.on("click", '[data-action="toggle-package"]', function (e) {
			e.preventDefault();
			e.stopPropagation();
			var $list = $overlay.find('[data-testid="kt-cl-uim01-package-list"]');
			state.listOpen = $list.hasClass("hidden");
			if (state.listOpen) {
				$list.removeClass("hidden");
				renderList($list);
			} else {
				$list.addClass("hidden");
			}
		});
		$overlay.on("click", "[data-package-id]", function (e) {
			e.preventDefault();
			var id = $(this).attr("data-package-id");
			state.selected =
				state.packages.find(function (p) {
					return p.package_id === id;
				}) || null;
			state.listOpen = false;
			remount();
		});
		$overlay.on("click", '[data-action="create"]', function (e) {
			e.preventDefault();
			if (!state.selected) {
				frappe.msgprint(__("Select an approved procurement package before creating a configuration."));
				return;
			}
			var $btn = $(this);
			$btn.prop("disabled", true);
			frappe.call({
				method: API_CREATE,
				args: {
					package_id: state.selected.package_id,
					std_document_id: state.selected.applicable_std_document_id,
				},
				callback: function (r) {
					var out = r.message || {};
					frappe.show_alert({
						message: __("Tender configuration created."),
						indicator: "green",
					});
					close();
					frappe.route_options = {
						configuration_id: out.configuration_id,
					};
					frappe.set_route("it-tender-configuration-overview");
				},
				error: function () {
					$btn.prop("disabled", false);
				},
			});
		});
	}

	function openModal(opts) {
		opts = opts || {};
		state.open = true;
		state.preselectId = opts.package_id || null;
		state.selected = null;
		state.listOpen = false;
		frappe.call({
			method: API_ELIGIBLE,
			args: { search: opts.search || null },
			callback: function (r) {
				state.packages = (r.message && r.message.packages) || [];
				if (state.preselectId) {
					state.selected =
						state.packages.find(function (p) {
							return p.package_id === state.preselectId;
						}) || null;
				}
				remount();
			},
		});
	}

	kentender_procurement.tender_configurations.openCreateModal = openModal;
	kentender_procurement.tender_configurations.closeCreateModal = close;
})();
