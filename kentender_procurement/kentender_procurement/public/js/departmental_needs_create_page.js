// NDS-UI-02A (Create) / NDS-UI-02B (Returned correction) — high-fidelity hand-port
// of docs/mvp-1-r1/01_departmental_needs/NDS-UI-02A.html and NDS-UI-02B.html.
// One controller serves both `/desk/departmental-needs-new` and
// `/desk/departmental-needs-edit` — they share the same form shape; 02B adds
// only the return notice and a different footer action set. Built against the
// MD spec's §7.1/§7.2 tables where they disagree with the HTML mockups (02B's
// own HTML is missing its footer entirely).
frappe.provide("kentender_procurement.departmental_needs");

(function () {
	"use strict";

	var API = "kentender_procurement.departmental_needs.api";
	var UNIT_CODES = ["Each", "Set", "Lot", "Person", "Staff", "Month", "Day", "Service", "Programme", "Other"];

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
		if (!isFinite(n)) return "";
		return n.toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	}

	function fmtBytes(n) {
		if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + " MB";
		return Math.max(1, Math.round(n / 1024)) + " KB";
	}

	function uid() {
		return "r" + Math.random().toString(36).slice(2, 10);
	}

	// ---- state ----------------------------------------------------------

	function newItemRow() {
		return { key: uid(), description: "", indicative_quantity: "", unit_code: "", other_unit: "" };
	}

	function initState(mode) {
		return {
			mode: mode, // "create" | "edit"
			need: null, // existing Departmental Need name, edit mode only
			token: "",
			context: {}, // {procuring_entity, organisation_unit, target_financial_year, ...labels}
			status: "Draft",
			revision_no: null,
			returnNotice: null, // {reason, actor, occurred_at} when status is Returned
			fields: { title: "", business_justification: "", required_by_date: "", delivery_or_use_location: "", indicative_cost: "" },
			items: [newItemRow()],
			attachments: [],
			saving: false,
		};
	}

	// ---- markup -----------------------------------------------------------

	function unitOptions(selected) {
		return UNIT_CODES.map(function (code) {
			return '<option value="' + esc(code) + '"' + (code === selected ? " selected" : "") + ">" + esc(code) + "</option>";
		}).join("");
	}

	function itemRowHtml(row, index) {
		var showOther = row.unit_code === "Other";
		return (
			'<tr data-item-row="' + esc(row.key) + '">' +
			'<td class="kt-nds-td-line">' + (index + 1) + "</td>" +
			"<td>" +
			'<input type="text" class="kt-nds-cell-input" data-item-field="description" value="' + esc(row.description) + '" placeholder="' + esc(__("Describe what is needed")) + '">' +
			"</td>" +
			"<td>" +
			'<input type="number" min="0" step="any" class="kt-nds-cell-input kt-nds-cell-input--qty" data-item-field="indicative_quantity" value="' + esc(row.indicative_quantity) + '">' +
			"</td>" +
			"<td>" +
			'<select class="kt-nds-cell-input" data-item-field="unit_code"><option value="">' + esc(__("Unit")) + "</option>" + unitOptions(row.unit_code) + "</select>" +
			(showOther
				? '<div class="kt-nds-item-other-unit"><input type="text" class="kt-nds-cell-input" data-item-field="other_unit" value="' + esc(row.other_unit) + '" placeholder="' + esc(__("Specify unit")) + '"></div>'
				: "") +
			"</td>" +
			'<td class="kt-nds-td-action">' +
			'<button type="button" class="kt-nds-row-remove" data-item-remove="' + esc(row.key) + '" aria-label="' + esc(__("Remove item")) + '"><span class="material-symbols-outlined" aria-hidden="true">delete</span></button>' +
			"</td>" +
			"</tr>"
		);
	}

	function attachmentRowHtml(att) {
		var scanLabel = att.scan_status === "Clean" ? "" : ' <span class="kt-nds-attachment-scan--' + esc((att.scan_status || "").toLowerCase()) + '">(' + esc(att.scan_status) + ")</span>";
		return (
			'<div class="kt-nds-attachment-row" data-attachment-row="' + esc(att.name) + '">' +
			'<div class="kt-nds-attachment-info">' +
			'<div class="kt-nds-attachment-icon"><span class="material-symbols-outlined" aria-hidden="true">description</span></div>' +
			"<div>" +
			'<p class="kt-nds-attachment-name" title="' + esc(att.original_filename) + '">' + esc(att.original_filename) + "</p>" +
			'<p class="kt-nds-attachment-meta">' + esc(fmtBytes(att.file_size)) + scanLabel + "</p>" +
			"</div></div>" +
			'<button type="button" class="kt-nds-attachment-remove" data-attachment-remove="' + esc(att.name) + '" aria-label="' + esc(__("Remove")) + '"><span class="material-symbols-outlined" aria-hidden="true">close</span></button>' +
			"</div>"
		);
	}

	function fieldError(state, field) {
		return state.errors && state.errors[field] ? '<p class="kt-nds-field-error">' + esc(state.errors[field]) + "</p>" : "";
	}

	function returnNoticeHtml(notice) {
		if (!notice) return "";
		return (
			'<div class="kt-nds-return-notice">' +
			'<span class="material-symbols-outlined" aria-hidden="true" style="font-variation-settings:\'FILL\' 1">error</span>' +
			"<div>" +
			'<h3 class="kt-nds-return-notice-title">' + esc(__("Returned for correction")) + "</h3>" +
			'<p class="kt-nds-return-notice-reason">&ldquo;' + esc(notice.reason) + '&rdquo;</p>' +
			'<div class="kt-nds-return-notice-audit"><span class="material-symbols-outlined" aria-hidden="true">history</span><span>' +
			esc(__("Returned by {0} on {1}", [notice.actor_label, notice.occurred_label])) +
			"</span></div></div></div>"
		);
	}

	function formMarkup(state) {
		var f = state.fields;
		var isEdit = state.mode === "edit";
		var c = state.context;
		return (
			'<div class="kt-nds-root kt-stitch-canvas" data-testid="' + (isEdit ? "departmental-needs-edit" : "departmental-needs-new") + '">' +
			'<div class="kt-nds-form-page">' +
			'<div class="kt-nds-page-header">' +
			(isEdit
				? '<div class="kt-nds-title-row"><h1 class="kt-nds-title">' + esc(f.title || __("Departmental need")) + "</h1>" +
					'<span class="kt-nds-status-pill kt-nds-status-pill--reserved">' + esc(state.status) + "</span></div>" +
					'<p class="kt-nds-meta-line"><span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">corporate_fare</span>' +
					esc(c.procuring_entity_label) + " | " + esc(c.organisation_unit_label) + " | " + esc(__("Planning year")) + " " + esc(c.financial_year) + "</p>"
				: '<h1 class="kt-nds-title">' + esc(__("Create departmental need")) + "</h1>" +
					'<p class="kt-nds-subtitle">' + esc(__("Describe what your department expects to require for the selected planning year.")) + "</p>" +
					'<div class="kt-nds-context">' +
					"<span><span class=\"kt-nds-context-label\">" + esc(__("Procuring Entity:")) + "</span> " + esc(c.procuring_entity_label) + "</span>" +
					'<span class="kt-nds-context-sep" aria-hidden="true">|</span>' +
					"<span><span class=\"kt-nds-context-label\">" + esc(__("Department:")) + "</span> " + esc(c.organisation_unit_label) + "</span>" +
					'<span class="kt-nds-context-sep" aria-hidden="true">|</span>' +
					"<span><span class=\"kt-nds-context-label\">" + esc(__("Planning year:")) + "</span> " + esc(c.financial_year) + "</span>" +
					"</div>") +
			"</div>" +
			(isEdit ? returnNoticeHtml(state.returnNotice) : "") +
			'<section class="kt-nds-block">' +
			'<div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">description</span><h3 class="kt-nds-block-title">1. ' + esc(__("Need Summary")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div class="kt-nds-field"><label class="kt-nds-field-label" for="kt-nds-f-title">' + esc(__("Need Title")) + '</label>' +
			'<input type="text" id="kt-nds-f-title" class="kt-nds-input" data-field="title" value="' + esc(f.title) + '" placeholder="' + esc(__("E.g., Office Supplies Q1")) + '">' + fieldError(state, "title") + "</div>" +
			'<div class="kt-nds-field"><label class="kt-nds-field-label" for="kt-nds-f-justification">' + esc(__("Business Justification")) + '</label>' +
			'<textarea id="kt-nds-f-justification" class="kt-nds-input" rows="3" data-field="business_justification">' + esc(f.business_justification) + "</textarea>" + fieldError(state, "business_justification") + "</div>" +
			"</div>" +
			'<p class="kt-nds-block-helper"><span class="material-symbols-outlined" aria-hidden="true">info</span>' +
			esc(__("Use plain language. Detailed procurement specifications will be prepared later if the need is included in the approved Plan.")) +
			"</p></section>" +
			'<section class="kt-nds-block">' +
			'<div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">list_alt</span><h3 class="kt-nds-block-title">2. ' + esc(__("Items Needed")) + "</h3></div>" +
			'<div class="kt-nds-items-table-wrap"><table class="kt-nds-items-table"><thead><tr>' +
			'<th class="kt-nds-th-line">' + esc(__("Line")) + "</th><th>" + esc(__("Description")) + '</th><th class="kt-nds-th-qty">' + esc(__("Indicative Qty")) + '</th><th class="kt-nds-th-unit">' + esc(__("Unit")) + '</th><th class="kt-nds-th-action">' + esc(__("Action")) + "</th>" +
			"</tr></thead><tbody data-items-tbody>" + state.items.map(itemRowHtml).join("") + "</tbody></table></div>" +
			fieldError(state, "items") +
			'<div class="kt-nds-items-footer"><button type="button" class="kt-nds-add-item" data-add-item><span class="material-symbols-outlined" aria-hidden="true">add</span>' + esc(__("Add item")) + "</button></div>" +
			"</section>" +
			'<div class="kt-nds-grid-2">' +
			'<section class="kt-nds-block"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">event_available</span><h3 class="kt-nds-block-title">3. ' + esc(__("Timing & Location")) + "</h3></div>" +
			'<div class="kt-nds-block-body">' +
			'<div class="kt-nds-field"><label class="kt-nds-field-label">' + esc(__("Required by")) + '</label><div class="kt-nds-date-field">' +
			'<input type="date" class="kt-nds-input" data-field="required_by_date" value="' + esc(f.required_by_date) + '"><span class="material-symbols-outlined" aria-hidden="true">calendar_today</span></div>' + fieldError(state, "required_by_date") + "</div>" +
			'<div class="kt-nds-field"><label class="kt-nds-field-label">' + esc(__("Delivery or use location")) + '</label>' +
			'<textarea class="kt-nds-input" rows="2" data-field="delivery_or_use_location">' + esc(f.delivery_or_use_location) + "</textarea>" + fieldError(state, "delivery_or_use_location") + "</div>" +
			"</div></section>" +
			'<div class="kt-nds-grid-2-stack">' +
			'<section class="kt-nds-block kt-nds-cost-block"><div class="kt-nds-block-body kt-nds-block-body--tight">' +
			'<label class="kt-nds-field-label kt-nds-cost-label">' + esc(__("Estimated total cost")) + ' <span class="kt-nds-cost-optional">(' + esc(__("optional")) + ")</span></label>" +
			'<div class="kt-nds-cost-input-row"><span class="kt-nds-cost-currency">KES</span><input type="text" inputmode="decimal" class="kt-nds-cost-input" data-field="indicative_cost" value="' + esc(f.indicative_cost) + '" placeholder="0.00"></div>' +
			fieldError(state, "indicative_cost") +
			"</div></section>" +
			'<section class="kt-nds-block" style="flex:1"><div class="kt-nds-block-head"><span class="material-symbols-outlined" aria-hidden="true">folder</span><h3 class="kt-nds-block-title">5. ' + esc(__("Supporting Documents")) + "</h3></div>" +
			'<div class="kt-nds-block-body kt-nds-block-body--tight" data-attachments-list>' + state.attachments.map(attachmentRowHtml).join("") +
			'<button type="button" class="kt-nds-attachment-upload" data-attachment-upload-btn><span class="material-symbols-outlined" aria-hidden="true">upload</span>' + esc(__("Upload another document")) + "</button>" +
			'<input type="file" class="kt-nds-attachment-upload-input" data-attachment-upload-input accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg">' +
			fieldError(state, "attachments") +
			"</div></section>" +
			"</div></div>" +
			"</div>" +
			footerMarkup(state) +
			"</div>"
		);
	}

	function footerMarkup(state) {
		var isEdit = state.mode === "edit";
		return (
			'<footer class="kt-nds-form-footer">' +
			(isEdit
				? '<button type="button" class="kt-nds-btn-danger-outline" data-action="withdraw">' + esc(__("Withdraw need")) + "</button>"
				: '<button type="button" class="kt-nds-btn-danger-outline" data-action="cancel">' + esc(__("Cancel")) + "</button>") +
			'<div class="kt-nds-form-footer-right">' +
			'<button type="button" class="kt-nds-btn-outline" data-action="save">' + esc(isEdit ? __("Save changes") : __("Save draft")) + "</button>" +
			'<button type="button" class="kt-nds-btn-primary" data-action="submit">' +
			esc(isEdit ? __("Resubmit for departmental review") : __("Submit for departmental review")) +
			'<span class="material-symbols-outlined" aria-hidden="true">send</span></button>' +
			"</div></footer>"
		);
	}

	// ---- data plumbing ------------------------------------------------

	function itemsPayload(state) {
		return state.items
			.filter(function (row) {
				return row.description || row.indicative_quantity || row.unit_code;
			})
			.map(function (row) {
				return {
					description: row.description || "",
					indicative_quantity: row.indicative_quantity === "" ? 0 : parseFloat(row.indicative_quantity) || 0,
					unit_code: row.unit_code || "",
					other_unit: row.other_unit || "",
				};
			});
	}

	function fieldsFromNeed(need) {
		return {
			title: need.title || "",
			business_justification: need.business_justification || "",
			required_by_date: need.required_by_date || "",
			delivery_or_use_location: need.delivery_or_use_location || "",
			indicative_cost: need.indicative_cost ? String(need.indicative_cost) : "",
		};
	}

	function itemsFromRows(rows) {
		return (rows && rows.length ? rows : [{}]).map(function (row) {
			return {
				key: uid(),
				description: row.description || "",
				indicative_quantity: row.indicative_quantity != null ? String(row.indicative_quantity) : "",
				unit_code: row.unit_code || "",
				other_unit: row.other_unit || "",
			};
		});
	}

	function loadCreate(state, query) {
		return call("resolve_creation_context").then(function (ctx) {
			if (!ctx || !ctx.ok) throw new Error(__("No active Departmental Needs assignment."));
			var pick = ctx.contexts[0] || {};
			if (query.procuring_entity && query.organisation_unit) {
				pick = ctx.contexts.find(function (row) {
					return row.procuring_entity === query.procuring_entity && row.organisation_unit === query.organisation_unit;
				}) || pick;
			}
			var fy = query.financial_year || ((ctx.financial_years[0] || {}).id || "");
			state.context = {
				procuring_entity: pick.procuring_entity, procuring_entity_label: pick.procuring_entity_label,
				organisation_unit: pick.organisation_unit, organisation_unit_label: pick.organisation_unit_label,
				financial_year: fy,
			};
		});
	}

	function loadEdit(state, needRef) {
		return call("get_need", { need: needRef }).then(function (data) {
			if (!data || !data.ok) throw new Error(__("Departmental Need not found."));
			var need = data.need;
			state.need = need.name;
			state.token = need.concurrency_token;
			state.status = need.status;
			state.revision_no = need.revision_no;
			state.fields = fieldsFromNeed(need);
			state.items = itemsFromRows(data.items);
			state.attachments = data.attachments || [];
			state.context = {
				procuring_entity_label: need.procuring_entity, organisation_unit_label: need.organisation_unit, financial_year: need.target_financial_year,
			};
			if (need.status === "Returned") {
				var latest = (data.latest_return || null);
				state.returnNotice = latest;
			}
			if (!(need.status === "Draft" || need.status === "Returned")) {
				throw new Error(__("Only a Draft or Returned Departmental Need may be edited."));
			}
		});
	}

	// ---- interactivity --------------------------------------------------

	function readField($body, el) {
		return { field: el.getAttribute("data-field"), value: el.value };
	}

	function syncFieldsFromDom(state, $body) {
		$body.find("[data-field]").each(function () {
			state.fields[this.getAttribute("data-field")] = this.value;
		});
		$body.find("[data-item-row]").each(function () {
			var key = this.getAttribute("data-item-row");
			var row = state.items.find(function (r) { return r.key === key; });
			if (!row) return;
			jQuery(this).find("[data-item-field]").each(function () {
				row[this.getAttribute("data-item-field")] = this.value;
			});
		});
	}

	function repaintForm(state, $body) {
		// formMarkup() returns ONE root element (data-testid="departmental-needs-{new,edit}").
		// jQuery(formMarkup(state)).html() would parse that string into an element and
		// read back only ITS children, discarding the root — silently stripping the
		// testid/kt-nds-root wrapper (and its styling scope) from the live DOM on every
		// repaint (add/remove item, unit change). Setting .html() directly on $body with
		// the markup string keeps the root element intact.
		$body.html(formMarkup(state));
		bindInteractions(state, $body);
	}

	function idempotencyKey(prefix) {
		return prefix + ":" + frappe.session.user + ":" + Date.now() + ":" + Math.random().toString(36).slice(2, 8);
	}

	function doSave(state, $body, { thenSubmit } = {}) {
		if (state.saving) return;
		syncFieldsFromDom(state, $body);
		state.saving = true;
		state.errors = {};
		var payload = {
			title: state.fields.title, business_justification: state.fields.business_justification,
			required_by_date: state.fields.required_by_date, delivery_or_use_location: state.fields.delivery_or_use_location,
			indicative_cost: state.fields.indicative_cost ? parseFloat(state.fields.indicative_cost) : null,
			items: itemsPayload(state), idempotency_key: idempotencyKey("nds-save"),
		};
		var promise;
		if (state.mode === "create" && !state.need) {
			promise = call("create_need", Object.assign({}, payload, {
				procuring_entity: state.context.procuring_entity, organisation_unit: state.context.organisation_unit,
				target_financial_year: state.context.financial_year,
			}));
		} else {
			promise = call("update_need", Object.assign({}, payload, { need: state.need, expected_token: state.token }));
		}
		return promise
			.then(function (result) {
				var wasCreate = state.mode === "create";
				state.need = result.need;
				state.token = result.concurrency_token;
				state.status = result.status;
				if (thenSubmit) return doSubmit(state, $body, { skipSync: true });
				frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
				if (wasCreate) {
					// First save of a new draft — move to the edit page's route.
					// Once there, state.mode becomes "edit" and further saves stay
					// put: re-navigating here on every save would silently drop the
					// need from the URL (frappe.set_route() only carries it through
					// frappe.route_options, not the URL — see routeNeed() above), so
					// a page reload afterward would have nothing to reload against.
					return frappe.set_route("departmental-needs-edit", { need: result.need });
				}
				state.mode = "edit";
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not save"), indicator: "red" });
			})
			.finally(function () {
				state.saving = false;
			});
	}

	function doSubmit(state, $body, opts) {
		opts = opts || {};
		if (!opts.skipSync) {
			// Persist any unsaved DOM edits first — submit_need validates the
			// server's stored record, not the form's current field values.
			return doSave(state, $body, { thenSubmit: true });
		}
		state.saving = true;
		return call("submit_need", { need: state.need, expected_token: state.token, idempotency_key: idempotencyKey("nds-submit") })
			.then(function (result) {
				frappe.show_alert({ message: __("Submitted for departmental review"), indicator: "green" });
				return frappe.set_route("departmental-needs-detail", { need: result.need });
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not submit"), indicator: "red" });
			})
			.finally(function () {
				state.saving = false;
			});
	}

	function doWithdraw(state) {
		return call("withdraw_need", { need: state.need, expected_token: state.token, idempotency_key: idempotencyKey("nds-withdraw"), reason: "" })
			.then(function () {
				frappe.show_alert({ message: __("Departmental Need withdrawn"), indicator: "green" });
				return frappe.set_route("departmental-needs");
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not withdraw"), indicator: "red" });
			});
	}

	function uploadFile(state, $body, file) {
		if (!state.need) {
			frappe.show_alert({ message: __("Save the draft before adding attachments."), indicator: "orange" });
			return;
		}
		return new Promise(function (resolve, reject) {
			var fd = new FormData();
			fd.append("file", file, file.name);
			fd.append("need", state.need);
			fd.append("expected_token", state.token);
			fd.append("idempotency_key", idempotencyKey("nds-attach"));
			var xhr = new XMLHttpRequest();
			xhr.open("POST", "/api/method/" + API + ".upload_attachment", true);
			xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token || "");
			xhr.setRequestHeader("Accept", "application/json");
			xhr.onload = function () {
				var body = null;
				try {
					body = JSON.parse(xhr.responseText || "{}");
				} catch (e) {
					reject(new Error("Upload failed"));
					return;
				}
				if (xhr.status >= 400 || (body && body.exc)) {
					reject(extractMessage(body));
					return;
				}
				resolve((body && body.message) || {});
			};
			xhr.onerror = function () {
				reject(new Error(__("Upload network error")));
			};
			xhr.send(fd);
		})
			.then(function (result) {
				state.attachments.push({
					name: result.attachment, original_filename: result.original_filename,
					file_size: result.file_size, mime_type: result.mime_type, scan_status: result.scan_status,
				});
				repaintForm(state, $body);
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not upload document"), indicator: "red" });
			});
	}

	function removeAttachment(state, $body, name) {
		return call("remove_attachment", { need: state.need, attachment: name, expected_token: state.token, idempotency_key: idempotencyKey("nds-detach") })
			.then(function () {
				state.attachments = state.attachments.filter(function (a) { return a.name !== name; });
				repaintForm(state, $body);
			})
			.catch(function (err) {
				frappe.show_alert({ message: err.message || __("Could not remove document"), indicator: "red" });
			});
	}

	function bindInteractions(state, $body) {
		$body.off(".ktNdsForm");
		$body.on("click.ktNdsForm", "[data-add-item]", function () {
			syncFieldsFromDom(state, $body);
			state.items.push(newItemRow());
			repaintForm(state, $body);
		});
		$body.on("click.ktNdsForm", "[data-item-remove]", function () {
			syncFieldsFromDom(state, $body);
			var key = this.getAttribute("data-item-remove");
			if (state.items.length <= 1) {
				state.items = [newItemRow()];
			} else {
				state.items = state.items.filter(function (r) { return r.key !== key; });
			}
			repaintForm(state, $body);
		});
		$body.on("change.ktNdsForm", '[data-item-field="unit_code"]', function () {
			syncFieldsFromDom(state, $body);
			repaintForm(state, $body);
		});
		$body.on("click.ktNdsForm", "[data-attachment-upload-btn]", function () {
			$body.find("[data-attachment-upload-input]").trigger("click");
		});
		$body.on("change.ktNdsForm", "[data-attachment-upload-input]", function () {
			var file = this.files && this.files[0];
			this.value = "";
			if (file) uploadFile(state, $body, file);
		});
		$body.on("click.ktNdsForm", "[data-attachment-remove]", function () {
			removeAttachment(state, $body, this.getAttribute("data-attachment-remove"));
		});
		$body.on("click.ktNdsForm", '[data-action="save"]', function () {
			doSave(state, $body);
		});
		$body.on("click.ktNdsForm", '[data-action="submit"]', function () {
			doSubmit(state, $body);
		});
		$body.on("click.ktNdsForm", '[data-action="cancel"]', function () {
			frappe.set_route("departmental-needs");
		});
		$body.on("click.ktNdsForm", '[data-action="withdraw"]', function () {
			frappe.confirm(__("Withdraw this Departmental Need? This cannot be undone."), function () {
				doWithdraw(state);
			});
		});
	}

	// ---- shell lifecycle --------------------------------------------------

	function activateSurface() {
		document.body.classList.add("kt-nds-surface");
	}
	function deactivateSurface() {
		document.body.classList.remove("kt-nds-surface");
	}

	function enterShell(state) {
		activateSurface();
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.enterNative !== "function") return;
		var crumbs = [
			{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
			{ label: __("Departmental Needs"), route: ["departmental-needs"] },
		];
		crumbs.push({ label: state.mode === "edit" ? __(state.fields.title || "Edit need") : __("Create need") });
		sh.enterNative({ sidebarWorkspaceKey: "procurement", toolbar: { breadcrumbs: crumbs, showSearch: false, showUserMeta: true } });
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

	function query() {
		var params = new URLSearchParams(window.location.search);
		return {
			procuring_entity: params.get("procuring_entity") || "", organisation_unit: params.get("organisation_unit") || "",
			financial_year: params.get("financial_year") || "", need: routeNeed(),
		};
	}

	function load(wrapper) {
		var route = frappe.get_route();
		var mode = route[0] === "departmental-needs-edit" ? "edit" : "create";
		var state = initState(mode);
		wrapper.ktNdsForm = { page: wrapper.ktNdsForm.page, state: state };
		var q = query();
		render(wrapper.ktNdsForm.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-loading">' + esc(__("Loading…")) + "</div></div>");
		var ready = mode === "edit" ? loadEdit(state, q.need) : loadCreate(state, q);
		return ready
			.then(function () {
				enterShell(state);
				var body = jQuery(render(wrapper.ktNdsForm.page, formMarkup(state)));
				bindInteractions(state, body);
			})
			.catch(function (err) {
				enterShell(state);
				render(wrapper.ktNdsForm.page, '<div class="kt-nds-root kt-stitch-canvas"><div class="kt-nds-empty">' + esc(err.message || __("This Departmental Need could not be opened.")) + "</div></div>");
			});
	}

	["departmental-needs-new", "departmental-needs-edit"].forEach(function (name) {
		// Both page names share this one script — Frappe's Page constructor sets
		// frappe.pages[name] to the real wrapper element BEFORE eval'ing the page's
		// script (see frappe.views.container.add_page()), but only for the name
		// currently being loaded. A blind `frappe.pages[name] = frappe.pages[name] || {}`
		// here would stub out the *other* (not-yet-visited) name with a plain object;
		// frappe.views.pageview.show() then sees that stub as "already registered" and
		// skips `new frappe.views.Page(name)` on the real first visit, so that page's
		// wrapper/container is never created and the route renders blank. Only attach
		// handlers onto a name that Frappe has already resolved to a real wrapper.
		if (!frappe.pages[name]) return;
		frappe.pages[name].on_page_load = function (wrapper) {
			var page = frappe.ui.make_app_page({ parent: wrapper, title: __("Departmental Needs"), single_column: true });
			wrapper.ktNdsForm = { page: page };
		};
		frappe.pages[name].on_page_show = function (wrapper) {
			return load(wrapper);
		};
		frappe.pages[name].on_page_hide = function () {
			deactivateSurface();
			var sh = kentender_core.cl_shell;
			if (sh && typeof sh.leaveNative === "function") sh.leaveNative();
		};
	});
})();
