/**
 * IT Wizard ITW-08..15 Desk hydration (Price → Publication).
 * Registers into kentender.it_wizard via register_downstream after engine loads.
 */
(function () {
	"use strict";

	if (!window.kentender) {
		window.kentender = {};
	}
	if (!kentender.it_wizard) {
		kentender.it_wizard = {};
	}

	var caches = {};

	function envelope_data(source) {
		var envelope = (source && source.message) || source || {};
		if (envelope.data !== undefined) {
			return envelope.data || {};
		}
		return envelope || {};
	}

	function ref_label(ref) {
		if (!ref) {
			return "—";
		}
		if (typeof ref === "string") {
			return ref;
		}
		return ref.name || ref.code || "—";
	}

	function fill_context_strip(doc, data) {
		var strip =
			doc.querySelector("[data-itw-context]") ||
			doc.querySelector("header + div.grid") ||
			doc.querySelector("div.grid.grid-cols-2, div.grid.grid-cols-7, div[class*='grid-cols-7']");
		if (!strip) {
			var candidates = doc.querySelectorAll("div.grid");
			for (var i = 0; i < candidates.length; i++) {
				if ((candidates[i].textContent || "").indexOf("Tender Ref") >= 0) {
					strip = candidates[i];
					break;
				}
			}
		}
		if (!strip) {
			return;
		}
		strip.setAttribute("data-itw-context", "1");
		var values = {
			"Tender Ref": data.tender_number || data.configuration_id || "—",
			"Tender Title": data.title || "—",
			"Planning Package Ref": ref_label(data.planning_package),
			"Procuring Entity": ref_label(data.procuring_entity),
			Method: ref_label(data.method),
			"Wizard State": data.state_label || "—",
		};
		strip.querySelectorAll(":scope > div").forEach(function (cell) {
			var label = (cell.querySelector("p, span") || {}).textContent || "";
			label = label.trim();
			Object.keys(values).forEach(function (key) {
				if (label.indexOf(key) < 0) {
					return;
				}
				var valueNode =
					cell.querySelector("p.font-data-mono, p.font-body-md, p.text-body-md, span.inline-flex") ||
					cell.querySelectorAll("p")[1];
				if (valueNode && key !== "Validation") {
					valueNode.textContent = values[key];
				}
			});
			if (label.indexOf("Validation") >= 0) {
				var blockers = (data.validation && data.validation.blockers) || 0;
				var warnings = (data.validation && data.validation.warnings) || 0;
				cell.innerHTML =
					'<p class="text-label-caps font-label-caps text-on-surface-variant uppercase mb-1">Validation</p>' +
					'<div class="flex items-center gap-2">' +
					'<span class="flex items-center gap-1 text-xs font-bold">' +
					blockers +
					" Blockers</span>" +
					'<span class="flex items-center gap-1 text-xs font-bold">' +
					warnings +
					" Warnings</span></div>";
			}
		});
	}

	function find_main_tbody(doc) {
		var marked = doc.querySelector("[data-itw-table-body]");
		if (marked) {
			return marked;
		}
		var tbody = doc.querySelector("main table tbody") || doc.querySelector("table tbody");
		if (tbody) {
			tbody.setAttribute("data-itw-table-body", "1");
		}
		return tbody;
	}

	function update_completion(doc, completion) {
		completion = completion || {};
		var label = doc.querySelector("aside .font-data-mono.font-bold, aside span.font-data-mono");
		if (label && (label.textContent || "").indexOf("/") >= 0) {
			label.textContent =
				String(completion.completed || 0) + "/" + String(completion.total || 0);
		}
		var bar = doc.querySelector("aside .bg-primary.h-full, aside [class*='bg-primary'][class*='h-full']");
		if (bar) {
			bar.style.width = String(completion.percent || 0) + "%";
		}
	}

	function button_by_text(doc, snippet) {
		var buttons = doc.querySelectorAll("button");
		for (var i = 0; i < buttons.length; i++) {
			if ((buttons[i].textContent || "").toUpperCase().indexOf(snippet.toUpperCase()) >= 0) {
				return buttons[i];
			}
		}
		return null;
	}

	function build_price_rows(items) {
		if (!items || !items.length) {
			return (
				'<tr><td class="p-8 text-center text-on-surface-variant" colspan="8">' +
				__("Not configured — no price items defined.") +
				"</td></tr>"
			);
		}
		return items
			.map(function (item) {
				var code = item.line_code || item.line_id || "";
				return (
					'<tr data-itw-row="1" data-itw-code="' +
					frappe.utils.escape_html(code) +
					'">' +
					'<td class="p-4"><p class="font-semibold">' +
					frappe.utils.escape_html(item.title || code) +
					'</p><p class="text-xs text-on-surface-variant">' +
					frappe.utils.escape_html(code) +
					"</p></td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(item.inventory_item_code || "—") +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(item.pricing_basis || "—") +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(
						String(item.quantity != null ? item.quantity : "—") +
							" " +
							(item.unit_of_measure || ""),
					) +
					"</td>" +
					'<td class="p-4 text-center">' +
					frappe.utils.escape_html(item.mandatory_optional || "—") +
					"</td>" +
					'<td class="p-4 max-w-xs">' +
					frappe.utils.escape_html(item.bidder_instruction || "—") +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(item.review_status || "—") +
					"</td>" +
					'<td class="p-4 text-right"><button type="button" class="text-primary text-xs font-bold" data-itw-edit="1">' +
					__("Edit") +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function build_eval_rows(items) {
		if (!items || !items.length) {
			return (
				'<tr><td class="p-8 text-center text-on-surface-variant" colspan="8">' +
				__("Not configured — no evaluation criteria defined.") +
				"</td></tr>"
			);
		}
		return items
			.map(function (item) {
				var code = item.criterion_code || item.criterion_id || "";
				return (
					'<tr data-itw-row="1" data-itw-code="' +
					frappe.utils.escape_html(code) +
					'">' +
					'<td class="p-4 font-semibold">' +
					frappe.utils.escape_html(item.title || code) +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(item.criterion_type || "—") +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(
						item.weight_marks != null ? String(item.weight_marks) + " marks" : "—",
					) +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(
						item.pass_mark != null ? String(item.pass_mark) : "—",
					) +
					"</td>" +
					'<td class="p-4">' +
					frappe.utils.escape_html(item.linked_requirement_code || "—") +
					"</td>" +
					'<td class="p-4 text-right"><button type="button" class="text-primary text-xs font-bold" data-itw-edit="1">' +
					__("Edit") +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function build_generic_rows(items, emptyMsg) {
		if (!items || !items.length) {
			return (
				'<tr><td class="p-8 text-center text-on-surface-variant" colspan="6">' +
				frappe.utils.escape_html(emptyMsg) +
				"</td></tr>"
			);
		}
		return items
			.map(function (item) {
				var code =
					item.item_code ||
					item.finding_code ||
					item.stage_code ||
					item.line_code ||
					item.criterion_code ||
					"";
				var title = item.title || item.stage_title || item.message || code;
				var meta =
					item.submission_rule ||
					item.severity ||
					item.decision ||
					item.carry_forward ||
					item.status ||
					"";
				return (
					'<tr data-itw-row="1" data-itw-code="' +
					frappe.utils.escape_html(code) +
					'">' +
					'<td class="p-4 font-semibold">' +
					frappe.utils.escape_html(title) +
					'</td><td class="p-4 text-on-surface-variant">' +
					frappe.utils.escape_html(code) +
					'</td><td class="p-4">' +
					frappe.utils.escape_html(meta || "—") +
					'</td><td class="p-4 text-right"><button type="button" class="text-primary text-xs font-bold" data-itw-edit="1">' +
					__("Edit") +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function build_checklist_html(items) {
		if (!items || !items.length) {
			return (
				'<p class="p-6 text-on-surface-variant">' + __("Not configured") + "</p>"
			);
		}
		return (
			'<ul class="space-y-2 p-4">' +
			items
				.map(function (item) {
					var label = item.label || item.title || item.code || "—";
					var done = item.complete || item.confirmed || item.status === "COMPLETE";
					return (
						'<li class="flex items-center gap-2"><span class="material-symbols-outlined text-sm">' +
						(done ? "check_circle" : "radio_button_unchecked") +
						"</span>" +
						frappe.utils.escape_html(label) +
						"</li>"
					);
				})
				.join("") +
			"</ul>"
		);
	}

	function open_item_dialog(screen, item, onSave) {
		var fields = [];
		if (screen === "price_schedule") {
			fields = [
				{ fieldname: "title", label: __("Title"), fieldtype: "Data", reqd: 1, default: item.title || "" },
				{
					fieldname: "pricing_basis",
					label: __("Pricing Basis"),
					fieldtype: "Select",
					options: "SUPPLY\nINSTALL\nRECURRENT\nOTHER",
					default: item.pricing_basis || "SUPPLY",
				},
				{
					fieldname: "quantity",
					label: __("Quantity"),
					fieldtype: "Float",
					default: item.quantity != null ? item.quantity : 1,
				},
				{
					fieldname: "unit_of_measure",
					label: __("Unit"),
					fieldtype: "Data",
					default: item.unit_of_measure || "LOT",
				},
				{
					fieldname: "mandatory_optional",
					label: __("Mandatory / Optional"),
					fieldtype: "Select",
					options: "MANDATORY\nOPTIONAL",
					default: item.mandatory_optional || "MANDATORY",
				},
				{
					fieldname: "bidder_instruction",
					label: __("Bidder Instruction"),
					fieldtype: "Small Text",
					default: item.bidder_instruction || "",
				},
				{
					fieldname: "evaluated_price_included",
					label: __("Include in Evaluated Price"),
					fieldtype: "Check",
					default: item.evaluated_price_included ? 1 : 0,
				},
			];
		} else if (screen === "evaluation_setup") {
			fields = [
				{ fieldname: "title", label: __("Criterion"), fieldtype: "Data", reqd: 1, default: item.title || "" },
				{
					fieldname: "criterion_type",
					label: __("Type"),
					fieldtype: "Select",
					options: "MANDATORY\nSCORED\nINFORMATIONAL",
					default: item.criterion_type || "SCORED",
				},
				{
					fieldname: "weight_marks",
					label: __("Marks / Weight"),
					fieldtype: "Float",
					default: item.weight_marks != null ? item.weight_marks : 0,
				},
				{
					fieldname: "pass_mark",
					label: __("Pass Mark"),
					fieldtype: "Float",
					default: item.pass_mark != null ? item.pass_mark : 0,
				},
				{
					fieldname: "linked_requirement_code",
					label: __("Linked Requirement"),
					fieldtype: "Data",
					default: item.linked_requirement_code || "",
				},
			];
		} else {
			fields = [
				{ fieldname: "title", label: __("Title"), fieldtype: "Data", reqd: 1, default: item.title || item.message || "" },
				{
					fieldname: "notes",
					label: __("Notes"),
					fieldtype: "Small Text",
					default: item.bidder_instruction || item.obligation_text || item.comment || "",
				},
			];
		}
		var dialog = new frappe.ui.Dialog({
			title: __("Edit item"),
			fields: fields,
			primary_action_label: __("Apply"),
			primary_action: function (values) {
				onSave(values);
				dialog.hide();
			},
		});
		dialog.show();
	}

	function screen_config(screen) {
		return {
			price_schedule: {
				get: "get_price_schedule_api",
				save: "save_price_schedule_api",
				json: "price_schedule_json",
				key: "price_schedule",
				items: "items",
				next: "it-tender-configuration-evaluation-setup",
				continueText: "CONTINUE TO EVALUATION",
				saveText: "SAVE PRICE SCHEDULE",
				addText: "ADD PRICE ITEM",
				empty: __("Not configured — no price items defined."),
				build: build_price_rows,
				newItem: function () {
					return {
						line_code: "PL-NEW-" + String(Date.now()).slice(-6),
						title: __("New price line"),
						pricing_basis: "SUPPLY",
						quantity: 1,
						unit_of_measure: "LOT",
						tax_treatment: "STANDARD_VAT",
						evaluated_price_included: 1,
						mandatory_optional: "MANDATORY",
						bidder_instruction: "",
						review_status: "DRAFT",
						display_order: 99,
					};
				},
			},
			evaluation_setup: {
				get: "get_evaluation_setup_api",
				save: "save_evaluation_setup_api",
				json: "evaluation_setup_json",
				key: "evaluation_setup",
				items: "criteria",
				next: "it-tender-configuration-forms-and-evidence",
				continueText: "CONTINUE TO FORMS",
				saveText: "SAVE",
				addText: "ADD",
				empty: __("Not configured — no evaluation criteria defined."),
				build: build_eval_rows,
				newItem: function () {
					return {
						criterion_code: "EV-NEW-" + String(Date.now()).slice(-6),
						title: __("New criterion"),
						criterion_type: "SCORED",
						weight_marks: 10,
						pass_mark: 0,
						review_status: "DRAFT",
						display_order: 99,
					};
				},
			},
			forms_and_evidence: {
				get: "get_forms_and_evidence_api",
				save: "save_forms_and_evidence_api",
				json: "forms_and_evidence_json",
				key: "forms_and_evidence",
				items: "items",
				next: "it-tender-configuration-scc",
				continueText: "CONTINUE TO SCC",
				saveText: "SAVE",
				addText: "ADD",
				empty: __("Not configured — no submission items defined."),
				build: function (items) {
					return build_generic_rows(items, __("Not configured — no submission items defined."));
				},
				newItem: function () {
					return {
						item_code: "FE-NEW-" + String(Date.now()).slice(-6),
						title: __("New submission item"),
						submission_rule: "MANDATORY",
						accepted_format: "PDF",
						display_order: 99,
					};
				},
			},
			scc: {
				get: "get_scc_api",
				save: "save_scc_api",
				json: "scc_json",
				key: "scc",
				items: "items",
				next: "it-tender-configuration-validation-report",
				continueText: "CONTINUE TO VALIDATION",
				saveText: "SAVE",
				addText: "ADD",
				empty: __("Not configured — no SCC carry-forward items."),
				build: function (items) {
					return build_generic_rows(items, __("Not configured — no SCC carry-forward items."));
				},
				newItem: function () {
					return {
						item_code: "SCC-NEW-" + String(Date.now()).slice(-6),
						title: __("New SCC item"),
						carry_forward: "YES",
						obligation_text: "",
						display_order: 99,
					};
				},
			},
			validation_report: {
				get: "get_validation_report_api",
				save: "save_validation_report_api",
				json: "validation_report_json",
				key: "validation_report",
				items: "findings",
				next: "it-tender-configuration-review-and-approval",
				continueText: "CONTINUE TO REVIEW",
				saveText: "RUN VALIDATION",
				addText: null,
				empty: __("No validation findings."),
				build: function (items) {
					return build_generic_rows(items, __("No validation findings."));
				},
				readonly: true,
			},
			review_and_approval: {
				get: "get_review_and_approval_api",
				save: "save_review_and_approval_api",
				json: "review_and_approval_json",
				key: "review_and_approval",
				items: "decisions",
				next: "it-tender-configuration-render-preview",
				continueText: "CONTINUE TO PREVIEW",
				saveText: "SAVE",
				addText: null,
				empty: __("No review stages configured."),
				build: function (items) {
					return build_generic_rows(items, __("No review stages configured."));
				},
			},
			render_preview: {
				get: "get_render_preview_api",
				save: "save_render_preview_api",
				json: "render_preview_json",
				key: "render_preview",
				items: "confirmation_checklist",
				next: "it-tender-configuration-publication-readiness",
				continueText: "CONTINUE TO PUBLICATION",
				saveText: "CONFIRM PREVIEW",
				addText: null,
				empty: __("Preview not generated."),
				checklist: true,
			},
			publication_readiness: {
				get: "get_publication_readiness_api",
				save: "save_publication_readiness_api",
				json: "publication_readiness_json",
				key: "publication_readiness",
				items: "confirmation_checklist",
				next: null,
				continueText: "MARK AS PUBLICATION READY",
				saveText: "SAVE READINESS",
				addText: null,
				empty: __("Publication readiness not configured."),
				checklist: true,
				markReady: true,
			},
		}[screen];
	}

	function apply_downstream(doc, screen, data, ctx) {
		var cfg = screen_config(screen);
		if (!cfg) {
			return;
		}
		caches[screen] = data || {};
		fill_context_strip(doc, data || {});
		update_completion(doc, (data && data.completion) || {});
		var host = find_main_tbody(doc);
		var items = (data && data[cfg.items]) || [];
		if (cfg.checklist) {
			var checklistHost =
				doc.querySelector("[data-itw-checklist]") ||
				doc.querySelector("main section .space-y-2") ||
				doc.querySelector("main ul");
			if (!checklistHost) {
				var section = doc.querySelector("main section") || doc.querySelector("main");
				if (section) {
					checklistHost = doc.createElement("div");
					checklistHost.setAttribute("data-itw-checklist", "1");
					section.appendChild(checklistHost);
				}
			}
			if (checklistHost) {
				checklistHost.setAttribute("data-itw-checklist", "1");
				var list = items;
				if ((!list || !list.length) && data && data.confirmation_checklist) {
					list = data.confirmation_checklist;
				}
				checklistHost.innerHTML = build_checklist_html(list);
			}
		} else if (host) {
			host.innerHTML = cfg.build(items);
		}
		wire_downstream(doc, screen, ctx);
	}

	function wire_downstream(doc, screen, ctx) {
		var cfg = screen_config(screen);
		if (!cfg || doc.body.getAttribute("data-itw-downstream-wired-" + screen) === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-downstream-wired-" + screen, "1");

		function persist(extra) {
			var payload = Object.assign({}, caches[screen] || {}, extra || {});
			var body = {};
			body[cfg.json] = JSON.stringify(payload);
			body.configuration_id = ctx.configuration_id;
			return frappe
				.call({
					method:
						"kentender_procurement.it_tender_wizard.api.instance_api." + cfg.save,
					args: body,
					freeze: true,
					freeze_message: __("Saving…"),
				})
				.then(function (result) {
					var data = envelope_data(result);
					caches[screen] = data;
					apply_downstream(doc, screen, data, ctx);
					frappe.show_alert({ message: __("Saved"), indicator: "green" });
					return data;
				});
		}

		doc.addEventListener("click", function (event) {
			var editBtn = event.target.closest("[data-itw-edit]");
			if (editBtn) {
				var row = editBtn.closest("[data-itw-row]");
				var code = row ? row.getAttribute("data-itw-code") : "";
				var items = (caches[screen] && caches[screen][cfg.items]) || [];
				var item =
					items.find(function (candidate) {
						return (
							(candidate.line_code ||
								candidate.criterion_code ||
								candidate.item_code ||
								candidate.finding_code ||
								candidate.stage_code) === code
						);
					}) || {};
				if (cfg.readonly) {
					var route = item.owner_screen_route;
					if (route && kentender.it_wizard.navigate) {
						kentender.it_wizard.navigate(route, {
							configuration_id: ctx.configuration_id,
						});
					}
					return;
				}
				open_item_dialog(screen, item, function (values) {
					Object.assign(item, values);
					if (!item.line_code && !item.criterion_code && !item.item_code) {
						items.push(Object.assign(cfg.newItem ? cfg.newItem() : {}, values));
					}
					caches[screen][cfg.items] = items;
					apply_downstream(doc, screen, caches[screen], ctx);
				});
				return;
			}
		});

		var saveBtn = button_by_text(doc, cfg.saveText || "SAVE");
		if (saveBtn) {
			saveBtn.addEventListener("click", function (event) {
				event.preventDefault();
				var extra = {};
				if (cfg.markReady && (saveBtn.textContent || "").toUpperCase().indexOf("PUBLICATION READY") >= 0) {
					extra.mark_ready = 1;
				}
				if (screen === "validation_report") {
					extra.run_validation = 1;
				}
				persist(extra);
			});
		}

		if (cfg.addText) {
			var addBtn = button_by_text(doc, cfg.addText);
			if (addBtn && cfg.newItem) {
				addBtn.addEventListener("click", function (event) {
					event.preventDefault();
					var items = (caches[screen][cfg.items] = caches[screen][cfg.items] || []);
					var created = cfg.newItem();
					open_item_dialog(screen, created, function (values) {
						items.push(Object.assign(created, values));
						apply_downstream(doc, screen, caches[screen], ctx);
					});
				});
			}
		}

		var continueBtn = button_by_text(doc, cfg.continueText || "CONTINUE");
		if (continueBtn) {
			continueBtn.disabled = false;
			continueBtn.classList.remove("opacity-55", "cursor-not-allowed");
			continueBtn.removeAttribute("aria-disabled");
			continueBtn.addEventListener("click", function (event) {
				event.preventDefault();
				var go = function () {
					if (cfg.markReady) {
						persist({ mark_ready: 1 }).then(function () {
							frappe.show_alert({
								message: __("Marked as Publication Ready"),
								indicator: "green",
							});
						});
						return;
					}
					if (cfg.next && kentender.it_wizard.navigate) {
						kentender.it_wizard.navigate(cfg.next, {
							configuration_id: ctx.configuration_id,
						});
					}
				};
				persist({}).then(go).catch(go);
			});
		}
	}

	function make_fetcher(screen) {
		var cfg = screen_config(screen);
		return function (ctx) {
			return frappe
				.call({
					method:
						"kentender_procurement.it_tender_wizard.api.instance_api." + cfg.get,
					args: { configuration_id: ctx.configuration_id },
				})
				.then(function (result) {
					var payload = {};
					payload[cfg.key] = result;
					return payload;
				});
		};
	}

	function make_hydrator(screen) {
		var cfg = screen_config(screen);
		return function (doc, payload, ctx) {
			var raw = (payload && payload[cfg.key]) || {};
			apply_downstream(doc, screen, envelope_data(raw), ctx);
		};
	}

	var SCREENS = [
		"price_schedule",
		"evaluation_setup",
		"forms_and_evidence",
		"scc",
		"validation_report",
		"review_and_approval",
		"render_preview",
		"publication_readiness",
	];

	var STEP_ROUTE_MAP = {
		PRICE_SCHEDULE: "it-tender-configuration-price-schedule",
		EVALUATION_SETUP: "it-tender-configuration-evaluation-setup",
		FORMS_AND_EVIDENCE: "it-tender-configuration-forms-and-evidence",
		SCC: "it-tender-configuration-scc",
		VALIDATION_REPORT: "it-tender-configuration-validation-report",
		REVIEW_AND_APPROVAL: "it-tender-configuration-review-and-approval",
		RENDER_PREVIEW: "it-tender-configuration-render-preview",
		PUBLICATION_READINESS: "it-tender-configuration-publication-readiness",
	};

	var ROUTES = Object.keys(STEP_ROUTE_MAP).map(function (k) {
		return STEP_ROUTE_MAP[k];
	});

	var fetchers = {};
	var hydrators = {};
	SCREENS.forEach(function (screen) {
		fetchers[screen] = make_fetcher(screen);
		hydrators[screen] = make_hydrator(screen);
	});

	function try_register() {
		if (typeof kentender.it_wizard.register_downstream === "function") {
			kentender.it_wizard.register_downstream({
				routes: ROUTES,
				step_route_map: STEP_ROUTE_MAP,
				fetchers: fetchers,
				hydrators: hydrators,
				context_routes: ROUTES,
			});
			return true;
		}
		return false;
	}

	if (!try_register()) {
		var attempts = 0;
		var timer = setInterval(function () {
			attempts += 1;
			if (try_register() || attempts > 40) {
				clearInterval(timer);
			}
		}, 50);
	}
})();
