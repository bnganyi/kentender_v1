/**
 * Desk PoC host for the electronic bidder workspace (Administrator demo).
 * Route: /app/it-electronic-bidder-workspace/<configuration_id>
 * Core UI: kentender_procurement.electronic_bid.mount (host-agnostic).
 */
frappe.pages["it-electronic-bidder-workspace"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Electronic Bidder Workspace (PoC)",
		single_column: true,
	});
	wrapper.page = page;
	page.main.html(
		'<div class="kt-eb-desk-host" data-testid="kt-eb-desk-host">' +
			'<div class="text-muted" style="padding:12px">Loading bidder workspace…</div>' +
			"</div>"
	);
};

frappe.pages["it-electronic-bidder-workspace"].on_page_show = function (wrapper) {
	var host = wrapper.querySelector("[data-testid='kt-eb-desk-host']") || wrapper.querySelector(".kt-eb-desk-host");
	if (!host) return;

	function configurationId() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) return String(route[1]).trim();
		return "TCFG-E1-NSSF-ERP";
	}

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					if (r.exc) reject(r.exc);
					else resolve(r.message);
				},
				error: reject,
			});
		});
	}

	var cfgId = configurationId();
	host.innerHTML = '<div class="text-muted" style="padding:12px">Loading ' + frappe.utils.escape_html(cfgId) + "…</div>";

	call("kentender_procurement.tender_configurations.get_electronic_bidder_workspace", {
		configuration_id: cfgId,
	})
		.then(function (workspace) {
			return call("kentender_procurement.tender_configurations.create_electronic_bid_draft", {
				configuration_id: cfgId,
				bidder_label: "PoC Demo Bidder",
			}).then(function (draft) {
				return { workspace: workspace, draft: draft };
			});
		})
		.then(function (ctx) {
			var workspace = ctx.workspace;
			var draft = ctx.draft;
			host.innerHTML = "";
			var header = document.createElement("div");
			header.style.padding = "8px 12px";
			header.innerHTML =
				"<div><strong data-testid='kt-eb-config-ref'>" +
				frappe.utils.escape_html(workspace.configuration_ref || cfgId) +
				"</strong> · STD " +
				frappe.utils.escape_html(workspace.std_version || "") +
				"</div>" +
				"<div class='text-muted' style='font-size:12px'>Administrator PoC demo — schema-driven bidder workspace (not part of CFG wizard)</div>";
			host.appendChild(header);
			var mountEl = document.createElement("div");
			host.appendChild(mountEl);

			var renderer = kentender_procurement.electronic_bid;
			if (!renderer || typeof renderer.mount !== "function") {
				host.innerHTML =
					"<div class='text-danger' style='padding:12px'>Bidder renderer not loaded. Ensure electronic_bid/bidder_workspace_renderer.js is included.</div>";
				return;
			}

			var bidId = draft.bid_id;
			renderer.mount(mountEl, {
				schema: workspace.schema,
				responses: draft.responses || workspace.responses || {},
				readOnly: !!draft.read_only,
				bidId: bidId,
				receipt: draft.receipt_code
					? { receipt_code: draft.receipt_code, seal_hash: draft.seal_hash, sealed_at: draft.sealed_at }
					: null,
				api: {
					saveSection: function (sectionKey, payload) {
						return call("kentender_procurement.tender_configurations.save_electronic_bid_section", {
							bid_id: bidId,
							section_key: sectionKey,
							payload: payload,
						});
					},
					validate: function () {
						return call("kentender_procurement.tender_configurations.validate_electronic_bid", {
							bid_id: bidId,
						});
					},
					submit: function () {
						return call("kentender_procurement.tender_configurations.submit_and_seal_electronic_bid", {
							bid_id: bidId,
						});
					},
					fillForTests: function () {
						return call("kentender_procurement.tender_configurations.fill_electronic_bid_draft_for_tests", {
							bid_id: bidId,
						});
					},
				},
			});
		})
		.catch(function (err) {
			host.innerHTML =
				"<div class='text-danger' style='padding:12px' data-testid='kt-eb-load-error'>Failed to load bidder workspace. " +
				frappe.utils.escape_html(String(err || "")) +
				"</div>";
		});
};
