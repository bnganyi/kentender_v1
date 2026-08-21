// Read-only Departmental Need detail — required by §8.1's route table
// (`/departmental-needs/{need_reference}`) but not itself an exact Stitch
// fixture in NDS-CHG-002 §7; reuses the review screen's `.kt-nds-ro-*`
// read-only component styles for visual consistency, with no decision footer.
frappe.provide("kentender_procurement.departmental_needs");

(function () {
	"use strict";

	var API = "kentender_procurement.departmental_needs.api";
	var PAGE = "departmental-needs-detail";

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: API + "." + method,
				args: args || {},
				freeze: false,
				error_handlers: {},
				callback: function (r) {
					if (r && r.exc) {
						reject(extractMessage(r));
						return;
					}
					resolve(r && r.message);
				},
				error: function (err) {
					reject(extractMessage(err));
				},
			});
		});
	}

	function extractMessage(payload) {
		var msg = "Request failed";
		try {
			if (payload && payload.message) msg = payload.message;
			var raw = payload && (payload._server_messages || (payload.responseJSON && payload.responseJSON._server_messages));
			if (raw) {
				var parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
				if (parsed && parsed.length) {
					var first = typeof parsed[0] === "string" ? JSON.parse(parsed[0]) : parsed[0];
					msg = (first && (first.message || first.title)) || msg;
				}
			}
		} catch (e) {
			/* keep best-effort msg */
		}
		return new Error(msg);
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function fmtBytes(n) {
		if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + " MB";
		return Math.max(1, Math.round(n / 1024)) + " KB";
	}

	var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
	function dateLabel(iso) {
		if (!iso) return "";
		var d = new Date(iso + "T00:00:00");
		if (isNaN(d.getTime())) return esc(iso);
		return d.getDate() + " " + MONTHS[d.getMonth()] + " " + d.getFullYear();
	}

	function unitLabel(row) {
		return row.unit_code === "Other" ? row.other_unit : row.unit_code;
	}

	function statusToneClass(status) {
		if (status === "Accepted for planning") return "kt-nds-pill--accepted";
		if (status === "Submitted") return "kt-nds-pill--reserved";
		if (status === "Returned" || status === "Not taken forward") return "kt-nds-pill--error";
		return "kt-nds-pill--neutral";
	}

	function itemsHtml(items) {
		if (!items.length) return '<p class="kt-nds-empty">' + esc(__("No items recorded.")) + "</p>";
		return (
			'<table class="kt-nds-items-table"><thead><tr><th class="kt-nds-th-line">' + esc(__("Line")) + "</th><th>" + esc(__("Description")) +
			'</th><th class="kt-nds-th-qty">' + esc(__("Indicative Quantity")) + '</th><th class="kt-nds-th-unit">' + esc(__("Unit")) + "</th></tr></thead><tbody>" +
			items
				.map(function (row, index) {
					return (
						'<tr><td class="kt-nds-td-line">' + String(index + 1).padStart(2, "0") + "</td><td>" + esc(row.description) +
						'</td><td class="kt-nds-th-qty" style="text-align:right">' + esc(row.indicative_quantity) + "</td><td>" + esc(unitLabel(row)) + "</td></tr>"
					);
				})
				.join("") +
			"</tbody></table>"
		);
	}

	function attachmentsHtml(attachments, need) {
		if (!attachments.length) return '<p class="kt-nds-empty">' + esc(__("No supporting documents.")) + "</p>";
		return attachments
			.map(function (att) {
				return (
					'<div class="kt-nds-ro-attachment" data-download-attachment="' + esc(att.name) + '">' +
					'<div class="kt-nds-attachment-info"><div class="kt-nds-attachment-icon"><span class="material-symbols-outlined" aria-hidden="true">description</span></div>' +
					"<div><span class=\"kt-nds-attachment-name\">" + esc(att.original_filename) + '</span><br><span class="kt-nds-attachment-meta">' + esc(fmtBytes(att.file_size)) + "</span></div></div>" +
					'<button type="button" class="kt-nds-ro-attachment-download" aria-label="' + esc(__("Download")) + '"><span class="material-symbols-outlined" aria-hidden="true">download</span></button>' +
					"</div>"
				);
			})
			.join("");
	}

	function detailMarkup(data) {
		var need = data.need, items = data.items || [], attachments = data.attachments || [];
		var canEdit = (data.actions || []).some(function (a) { return a.code === "edit"; });
		return (
			'<div class="kt-nds-root kt-stitch-canvas" data-testid="departmental-needs-detail">' +
			'<div class="kt-nds-form-page">' +
			'<div class="kt-nds-page-header"><div class="kt-nds-title-row"><h1 class="kt-nds-title" style="font-size:30px">' + esc(need.title) + "</h1>" +
			'<span class="kt-nds-status-pill ' + statusToneClass(need.status) + '">' + esc(need.status) + "</span></div>" +
			'<p class="kt-nds-meta-line">' + esc(need.need_reference) + '<span class="kt-nds-meta-sep" aria-hidden="true"></span>' +
			esc(need.procuring_entity) + " | " + esc(need.organisation_unit) + " | " + esc(need.target_financial_year) + "</p></div>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">description</span><h3 class="kt-nds-block-title">' + esc(__("Need Summary")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Business Justification")) + '</p><p class="kt-nds-ro-justification">' + esc(need.business_justification || __("Unavailable")) + "</p></div>" +
			"</div></section>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">list_alt</span><h3 class="kt-nds-block-title">' + esc(__("Items")) + "</h3></div>" +
			'<div class="kt-nds-block-body kt-nds-block-body--tight">' + itemsHtml(items) + "</div></section>" +
			'<div class="kt-nds-grid-2">' +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">pin_drop</span><h3 class="kt-nds-block-title">' + esc(__("Timing and Location")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Required By")) + '</p><p class="kt-nds-ro-value">' + esc(need.required_by_date ? dateLabel(need.required_by_date) : __("Unavailable")) + "</p></div>" +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Delivery / Use Location")) + '</p><p class="kt-nds-ro-value">' + esc(need.delivery_or_use_location || __("Unavailable")) + "</p></div>" +
			"</div></section>" +
			'<div class="kt-nds-grid-2-stack">' +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">payments</span><h3 class="kt-nds-block-title">' + esc(__("Indicative Cost")) + "</h3></div>" +
			'<div class="kt-nds-ro-cost"><p class="kt-nds-ro-field-label">' + esc(__("Total Value")) + '</p><div class="kt-nds-ro-cost-value"><span>KES</span><span class="kt-nds-ro-cost-amount">' +
			(need.indicative_cost ? esc(parseFloat(need.indicative_cost).toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })) : esc(__("Unavailable"))) +
			"</span></div></div></section>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">attach_file</span><h3 class="kt-nds-block-title">' + esc(__("Supporting Documents")) + "</h3></div>" +
			'<div class="kt-nds-block-body kt-nds-block-body--tight">' + attachmentsHtml(attachments) + "</div></section>" +
			"</div></div>" +
			(canEdit ? '<div class="kt-nds-detail-actions"><button type="button" class="kt-nds-btn-primary" data-edit>' + esc(__("Edit")) + "</button></div>" : "") +
			"</div></div>"
		);
	}

	function activateSurface() {
		document.body.classList.add("kt-nds-surface");
	}
	function deactivateSurface() {
		document.body.classList.remove("kt-nds-surface");
	}

	function enterShell(title) {
		activateSurface();
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.enterNative !== "function") return;
		sh.enterNative({
			sidebarWorkspaceKey: "procurement",
			toolbar: {
				breadcrumbs: [
					{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
					{ label: __("Departmental Needs"), route: ["departmental-needs"] },
					{ label: title },
				],
				showSearch: false, showUserMeta: true,
			},
		});
	}

	function render(page, html) {
		var sh = kentender_core.cl_shell;
		if (sh && typeof sh.mountContent === "function") {
			sh.mountContent(page.main, { mainHtml: html, pageHeader: { title: "", hidden: true } });
			return page.main.find('[data-testid="kt-cl-page-body"]').get(0) || page.main.get(0);
		}
		page.main.html(html);
		return page.main.get(0);
	}

	function routeNeed() {
		// frappe.set_route(name, {need}) stashes the value on frappe.route_options
		// rather than the URL query string (Frappe core's push_state() never
		// appends it) — direct navigation (bookmark, page.goto) still relies on
		// the URL, so fall back to that.
		if (frappe.route_options && frappe.route_options.need) {
			var value = frappe.route_options.need;
			delete frappe.route_options.need;
			return value;
		}
		return new URLSearchParams(window.location.search).get("need") || "";
	}

	function load(wrapper) {
		var need = routeNeed();
		render(wrapper.ktNdsDetail.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-loading">' + esc(__("Loading…")) + "</div></div>");
		return call("get_need", { need: need })
			.then(function (data) {
				if (!data || !data.ok) throw new Error(__("Departmental Need not found."));
				enterShell(data.need.title);
				var body = jQuery(render(wrapper.ktNdsDetail.page, detailMarkup(data)));
				body.on("click.ktNdsDetail", "[data-edit]", function () {
					frappe.set_route("departmental-needs-edit", { need: data.need.name });
				});
				body.on("click.ktNdsDetail", "[data-download-attachment]", function () {
					window.open(
						frappe.urllib.get_full_url(
							"/api/method/" + API + ".download_attachment?need=" + encodeURIComponent(data.need.name) + "&attachment=" + encodeURIComponent(this.getAttribute("data-download-attachment"))
						),
						"_blank"
					);
				});
			})
			.catch(function (err) {
				enterShell(__("Departmental need"));
				render(wrapper.ktNdsDetail.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-empty">' + esc(err.message || __("This Departmental Need could not be opened.")) + "</div></div>");
			});
	}

	frappe.pages[PAGE] = frappe.pages[PAGE] || {};
	frappe.pages[PAGE].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: __("Departmental need"), single_column: true });
		wrapper.ktNdsDetail = { page: page };
	};
	frappe.pages[PAGE].on_page_show = function (wrapper) {
		return load(wrapper);
	};
	frappe.pages[PAGE].on_page_hide = function () {
		deactivateSurface();
		var sh = kentender_core.cl_shell;
		if (sh && typeof sh.leaveNative === "function") sh.leaveNative();
	};
})();
