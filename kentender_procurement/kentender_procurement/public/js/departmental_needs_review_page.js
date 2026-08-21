// NDS-UI-02C (Departmental review) — high-fidelity hand-port of
// docs/mvp-1-r1/01_departmental_needs/NDS-UI-02C.html.
frappe.provide("kentender_procurement.departmental_needs");

(function () {
	"use strict";

	var API = "kentender_procurement.departmental_needs.api";
	var PAGE = "departmental-needs-review";

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

	function fmtMoney(value) {
		var n = parseFloat(value);
		if (!isFinite(n)) return __("Unavailable");
		return "KES " + n.toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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

	function idempotencyKey(prefix) {
		return prefix + ":" + frappe.session.user + ":" + Date.now() + ":" + Math.random().toString(36).slice(2, 8);
	}

	function itemsHtml(items) {
		if (!items.length) return "";
		return items
			.map(function (row, index) {
				return (
					'<tr><td class="kt-nds-td-line">' + String(index + 1).padStart(2, "0") + "</td>" +
					"<td>" + esc(row.description) + "</td>" +
					'<td class="kt-nds-th-qty" style="text-align:right">' + esc(row.indicative_quantity) + "</td>" +
					"<td>" + esc(unitLabel(row)) + "</td></tr>"
				);
			})
			.join("");
	}

	function attachmentsHtml(attachments) {
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

	function reviewMarkup(data) {
		var need = data.need, items = data.items || [], attachments = data.attachments || [];
		var actionCodes = (data.actions || []).map(function (a) { return a.code; });
		var canReview = actionCodes.indexOf("review") !== -1;
		return (
			'<div class="kt-nds-root kt-stitch-canvas" data-testid="departmental-needs-review">' +
			'<div class="kt-nds-form-page">' +
			'<div class="kt-nds-page-header">' +
			'<div class="kt-nds-title-row"><h2 class="kt-nds-title" style="font-size:30px">' + esc(__("Review departmental need")) + "</h2>" +
			'<span class="kt-nds-status-pill kt-nds-status-pill--primary">' + esc(need.status) + "</span></div>" +
			'<p class="kt-nds-meta-line"><span>' + esc(__("Submitted by:")) + " <strong>" + esc(data.submitted_by_label) + '</strong></span><span class="kt-nds-meta-sep" aria-hidden="true"></span>' +
			"<span>" + esc(__("Submitted:")) + " <strong>" + esc(data.submitted_label) + '</strong></span><span class="kt-nds-meta-sep" aria-hidden="true"></span>' +
			"<span>" + esc(__("Revision:")) + " <strong>" + esc(need.revision_no) + "</strong></span></p>" +
			'<p class="kt-nds-meta-line"><span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">account_balance</span>' +
			esc(__("Procuring Entity:")) + " " + esc(need.procuring_entity) +
			'<span class="kt-nds-meta-sep" aria-hidden="true"></span><span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">corporate_fare</span>' +
			esc(__("Department:")) + " " + esc(need.organisation_unit) +
			'<span class="kt-nds-meta-sep" aria-hidden="true"></span><span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">calendar_today</span>' +
			esc(__("Planning year:")) + " " + esc(need.target_financial_year) + "</p>" +
			"</div>" +
			'<div class="kt-nds-review-banner"><span class="material-symbols-outlined" aria-hidden="true">info</span>' +
			"<p>" + esc(__("Confirm whether this need should be taken forward for departmental procurement planning")) + "</p></div>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">description</span><h3 class="kt-nds-block-title">1. ' + esc(__("Need Summary")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Need Title")) + '</p><p class="kt-nds-ro-value">' + esc(need.title) + "</p></div>" +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Business Justification")) + '</p><p class="kt-nds-ro-justification">' + esc(need.business_justification) + "</p></div>" +
			"</div></section>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">list_alt</span><h3 class="kt-nds-block-title">2. ' + esc(__("Items")) + "</h3></div>" +
			'<div class="kt-nds-items-table-wrap"><table class="kt-nds-items-table"><thead><tr>' +
			'<th class="kt-nds-th-line">' + esc(__("Line")) + "</th><th>" + esc(__("Description")) + '</th><th class="kt-nds-th-qty">' + esc(__("Indicative Quantity")) + '</th><th class="kt-nds-th-unit">' + esc(__("Unit")) + "</th>" +
			"</tr></thead><tbody>" + itemsHtml(items) + "</tbody></table></div></section>" +
			'<div class="kt-nds-grid-2">' +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">pin_drop</span><h3 class="kt-nds-block-title">3. ' + esc(__("Timing and Location")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div class="kt-nds-ro-timing-row"><div class="kt-nds-ro-timing-icon"><span class="material-symbols-outlined" aria-hidden="true">event</span></div>' +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Required By")) + '</p><p class="kt-nds-ro-value">' + esc(data.required_by_label) + "</p></div></div>" +
			'<div class="kt-nds-ro-timing-divider"></div>' +
			'<div class="kt-nds-ro-timing-row"><div class="kt-nds-ro-timing-icon"><span class="material-symbols-outlined" aria-hidden="true">location_on</span></div>' +
			'<div><p class="kt-nds-ro-field-label">' + esc(__("Delivery / Use Location")) + '</p><p class="kt-nds-ro-value">' + esc(need.delivery_or_use_location) + "</p></div></div>" +
			"</div></section>" +
			'<div class="kt-nds-grid-2-stack">' +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">payments</span><h3 class="kt-nds-block-title">4. ' + esc(__("Indicative Cost")) + "</h3></div>" +
			'<div class="kt-nds-ro-cost"><p class="kt-nds-ro-field-label">' + esc(__("Total Value")) + '</p><div class="kt-nds-ro-cost-value"><span>KES</span><span class="kt-nds-ro-cost-amount">' +
			(need.indicative_cost ? esc(parseFloat(need.indicative_cost).toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })) : esc(__("Unavailable"))) +
			"</span></div></div></section>" +
			'<section class="kt-nds-ro-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">attach_file</span><h3 class="kt-nds-block-title">5. ' + esc(__("Supporting Documents")) + "</h3></div>" +
			'<div class="kt-nds-block-body kt-nds-block-body--tight">' + attachmentsHtml(attachments) + "</div></section>" +
			"</div></div>" +
			"</div>" +
			(canReview ? decisionFooterHtml() : "") +
			reasonDialogTemplate() +
			"</div>"
		);
	}

	function decisionFooterHtml() {
		return (
			'<div class="kt-nds-decision-footer"><div class="kt-nds-decision-footer-inner">' +
			'<button type="button" class="kt-nds-decision-btn kt-nds-decision-btn--return" data-decision="return">' + esc(__("Return for correction")) + "</button>" +
			'<button type="button" class="kt-nds-decision-btn kt-nds-decision-btn--decline" data-decision="decline">' + esc(__("Do not take forward")) + "</button>" +
			'<button type="button" class="kt-nds-decision-btn kt-nds-decision-btn--accept" data-decision="accept">' + esc(__("Accept for planning")) + "</button>" +
			"</div></div>"
		);
	}

	function reasonDialogTemplate() {
		return (
			'<div class="kt-nds-reason-dialog" data-reason-dialog hidden>' +
			'<div class="kt-nds-reason-dialog-backdrop" data-reason-dialog-backdrop></div>' +
			'<div class="kt-nds-reason-dialog-card">' +
			'<div class="kt-nds-reason-dialog-header"><h3 class="kt-nds-reason-dialog-title" data-reason-dialog-title></h3>' +
			'<button type="button" class="kt-nds-reason-dialog-close" data-reason-dialog-cancel aria-label="' + esc(__("Close")) + '"><span class="material-symbols-outlined" aria-hidden="true">close</span></button></div>' +
			'<div class="kt-nds-reason-dialog-body"><label class="kt-nds-field-label" for="kt-nds-reason-text" data-reason-dialog-label></label>' +
			'<textarea id="kt-nds-reason-text" class="kt-nds-input" rows="4" data-reason-text minlength="20" maxlength="1000"></textarea>' +
			'<p class="kt-nds-reason-dialog-hint">' + esc(__("20-1,000 characters.")) + "</p></div>" +
			'<div class="kt-nds-reason-dialog-footer"><button type="button" class="kt-nds-btn-outline" data-reason-dialog-cancel>' + esc(__("Cancel")) + "</button>" +
			'<button type="button" class="kt-nds-btn-primary" data-reason-dialog-confirm>' + esc(__("Confirm")) + "</button></div>" +
			"</div></div>"
		);
	}

	function openReasonDialog($body, decision) {
		var $dialog = $body.find("[data-reason-dialog]");
		var titles = { return: __("Return for correction"), decline: __("Do not take forward") };
		var labels = { return: __("Reason for return"), decline: __("Reason for declining") };
		$dialog.find("[data-reason-dialog-title]").text(titles[decision]);
		$dialog.find("[data-reason-dialog-label]").text(labels[decision]);
		$dialog.find("[data-reason-text]").val("");
		$dialog.attr("data-decision-pending", decision).removeAttr("hidden");
		$dialog.find("[data-reason-text]").trigger("focus");
	}

	function closeReasonDialog($body) {
		$body.find("[data-reason-dialog]").attr("hidden", "hidden").removeAttr("data-decision-pending");
	}

	function submitDecision(state, $body, decision, reason) {
		return call("review_need", {
			need: state.need, decision: decision, task: state.task, expected_token: state.token,
			task_token: state.taskToken, idempotency_key: idempotencyKey("nds-review-" + decision), reason: reason || "",
		})
			.then(function () {
				frappe.show_alert({ message: __("Decision recorded"), indicator: "green" });
				return frappe.set_route("departmental-needs");
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not record decision"), indicator: "red" });
			});
	}

	function bind(state, $body) {
		$body.off(".ktNdsReview");
		$body.on("click.ktNdsReview", "[data-decision]", function () {
			var decision = this.getAttribute("data-decision");
			if (decision === "accept") {
				frappe.confirm(__("Accept this Departmental Need for planning?"), function () {
					submitDecision(state, $body, "accept");
				});
				return;
			}
			openReasonDialog($body, decision);
		});
		$body.on("click.ktNdsReview", "[data-reason-dialog-cancel], [data-reason-dialog-backdrop]", function () {
			closeReasonDialog($body);
		});
		$body.on("click.ktNdsReview", "[data-reason-dialog-confirm]", function () {
			var $dialog = $body.find("[data-reason-dialog]");
			var decision = $dialog.attr("data-decision-pending");
			var reason = ($dialog.find("[data-reason-text]").val() || "").trim();
			if (reason.length < 20) {
				frappe.show_alert({ message: __("Reason must be at least 20 characters."), indicator: "orange" });
				return;
			}
			closeReasonDialog($body);
			submitDecision(state, $body, decision, reason);
		});
		$body.on("keydown.ktNdsReview", "[data-reason-dialog]", function (event) {
			if (event.key === "Escape") closeReasonDialog($body);
		});
		$body.on("click.ktNdsReview", "[data-download-attachment]", function () {
			var name = this.getAttribute("data-download-attachment");
			window.open(
				frappe.urllib.get_full_url(
					"/api/method/" + API + ".download_attachment?need=" + encodeURIComponent(state.need) + "&attachment=" + encodeURIComponent(name)
				),
				"_blank"
			);
		});
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
					{ label: __("Review") },
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
		render(wrapper.ktNdsReview.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-loading">' + esc(__("Loading…")) + "</div></div>");
		return call("get_need", { need: need })
			.then(function (data) {
				if (!data || !data.ok) throw new Error(__("Departmental Need not found."));
				var n = data.need;
				var reviewAction = (data.actions || []).find(function (a) { return a.code === "review"; }) || {};
				var state = { need: n.name, token: n.concurrency_token, task: reviewAction.task || "", taskToken: reviewAction.task_token || "" };
				wrapper.ktNdsReview.state = state;
				enterShell(n.title);
				var body = jQuery(render(wrapper.ktNdsReview.page, reviewMarkup(Object.assign({}, data, {
					required_by_label: n.required_by_date ? dateLabel(n.required_by_date) : __("Unavailable"),
				}))));
				bind(state, body);
			})
			.catch(function (err) {
				enterShell(__("Review"));
				render(wrapper.ktNdsReview.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-empty">' + esc(err.message || __("This Departmental Need could not be opened.")) + "</div></div>");
			});
	}

	frappe.pages[PAGE] = frappe.pages[PAGE] || {};
	frappe.pages[PAGE].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({ parent: wrapper, title: __("Review departmental need"), single_column: true });
		wrapper.ktNdsReview = { page: page };
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
