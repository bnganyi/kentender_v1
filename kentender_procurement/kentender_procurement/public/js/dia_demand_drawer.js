// DIA demand create/edit drawer — wide modal; Form loads in iframe with drawer chrome stripped in demand_form.js.

frappe.provide("kentender_procurement.dia_demand_drawer");

(function () {
	let activeDialog = null;

	function destroyDrawer() {
		if (activeDialog) {
			try {
				activeDialog.hide();
			} catch (e) {
				/* ignore */
			}
			activeDialog = null;
		}
	}

	function formUrl(demandName, isNew) {
		let name = demandName;
		if (isNew) {
			name = frappe.model.make_new_doc_and_get_name("Demand", true);
		}
		const url = frappe.router.make_url(["Form", "Demand", name]);
		return url + (url.indexOf("?") >= 0 ? "&" : "?") + "dia_drawer=1";
	}

	function openDrawer(opts) {
		opts = opts || {};
		destroyDrawer();
		const isNew = !opts.demandName;
		const viewOnly = !!opts.viewOnly;
		const title = opts.title
			? opts.title
			: isNew
				? __("New Demand")
				: viewOnly
					? __("View Demand")
					: __("Edit Demand");
		const d = new frappe.ui.Dialog({
			title: title,
			size: "extra-large",
			no_submit_on_enter: true,
		});
		d.$wrapper.addClass("modal-dialog-scrollable kt-dia-demand-drawer");
		d.$wrapper.attr("data-testid", "dia-demand-drawer");

		function mountFrame(url) {
			const $frame = $(
				'<iframe class="kt-dia-demand-drawer__iframe" data-testid="dia-demand-drawer-frame" title="' +
					frappe.utils.escape_html(title) +
					'"></iframe>'
			);
			$frame.css("visibility", "hidden");
			$frame.on("load", function () {
				// Keep iframe hidden until first paint completes to prevent sidebar/chrome flash.
				requestAnimationFrame(function () {
					$frame.css("visibility", "visible");
				});
			});
			$frame.attr("src", url);
			$frame.appendTo(d.body);
		}

		if (d.get_primary_btn) {
			d.get_primary_btn().hide();
		}
		if (d.get_secondary_btn) {
			d.get_secondary_btn().hide();
		}
		const closeBtn = d.$wrapper.find(".btn-modal-close");
		closeBtn.attr("data-testid", "dia-demand-drawer-close");

		frappe.model.with_doctype("Demand", function () {
			mountFrame(formUrl(opts.demandName, isNew));
		});

		d.onhide = function () {
			destroyDrawer();
			if (typeof opts.onClose === "function") {
				opts.onClose();
			}
		};

		activeDialog = d;
		d.show();
		return d;
	}

	kentender_procurement.dia_demand_drawer = {
		openCreate(onSaved, onClose) {
			return openDrawer({ onSaved: onSaved, onClose: onClose });
		},
		openEdit(demandName, onSaved, onClose, drawerOpts) {
			drawerOpts = drawerOpts || {};
			return openDrawer(
				Object.assign({ demandName: demandName, onSaved: onSaved, onClose: onClose }, drawerOpts)
			);
		},
		close() {
			destroyDrawer();
		},
		isOpen() {
			return !!activeDialog;
		},
	};
})();
