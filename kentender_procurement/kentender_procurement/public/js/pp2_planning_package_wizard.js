/** PW7–PW11 — Planning Package Creation Wizard.
 *
 * Replaces `pp2_planning_create_package_modal.js`'s single-field dialog
 * with the full multi-demand flow from `Planning Package Creation Wizard.md`
 * (Select Demands -> Configure Package -> Review and Create -> Success).
 *
 * Implementation note: built as a sequence of `frappe.ui.Dialog` steps
 * driven by the real PW2–PW6 backend APIs, rather than the iframe-embedded
 * 4 static mockups under `public/workbench_design/package_wizard_step*.html`
 * (kept on disk as design references). This trades pixel-for-pixel fidelity
 * to those mockups for a much faster, fully-wired implementation, per
 * explicit direction to prioritize speed over pixel precision — see
 * "Frontend implementation approach" in PACKAGE_WIZARD_WIRING_TRACKER.md.
 * No technical codes/handoff IDs are rendered as user-facing labels
 * (§15/§17); `inclusion_code`/`package_code` are opaque handles only.
 */
(function () {
	frappe.provide("kentender_procurement");

	const ELIGIBLE_DEMANDS_API =
		"kentender_procurement.procurement_planning.api.package_wizard.list_pp_wizard_eligible_demands";
	const COMPATIBILITY_API =
		"kentender_procurement.procurement_planning.api.package_wizard.check_pp_package_compatibility";
	const CONFIG_PREVIEW_API =
		"kentender_procurement.procurement_planning.api.package_wizard.get_pp_package_wizard_configuration_preview";
	const DOC_PATH_API =
		"kentender_procurement.procurement_planning.api.package_wizard.get_pp_package_wizard_document_path_preview";
	const READINESS_API =
		"kentender_procurement.procurement_planning.api.package_wizard.get_pp_package_wizard_readiness";
	const CREATE_API =
		"kentender_procurement.procurement_planning.api.package_wizard.create_pp_package_from_wizard";

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function money(amount, currency) {
		const n = Number(amount) || 0;
		return esc(currency || "KES") + " " + Math.round(n).toLocaleString("en-US");
	}

	function row(label, valueHtml, testid) {
		return (
			'<div style="display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-bottom:1px solid var(--border-color, #e0e3e5);"' +
			(testid ? ' data-testid="' + esc(testid) + '"' : "") +
			'><span class="text-muted small">' +
			esc(label) +
			'</span><span class="small" style="text-align:right;font-weight:600;">' +
			valueHtml +
			"</span></div>"
		);
	}

	// ---- Wizard state (session-scoped, in-memory only — no server draft;
	// Save Draft is explicitly deferred per the tracker's scope decisions) ----

	function WizardCtx(opts) {
		this.opts = opts || {};
		this.plan_code = String(this.opts.plan_code || "").trim();
		this.plan_name = String(this.opts.plan_name || "").trim();
		this.selected = new Map(); // inclusion_code -> demand row from eligibility list
		this.config = {
			package_title: "",
			package_description: "",
			package_owner: frappe.session.user,
			target_release_date: "",
			package_priority: "Normal",
			procurement_method: "",
			method_override_reason: "",
			line_overrides: {},
		};
		this.dialog = null;
		this._blocked = false;
	}

	WizardCtx.prototype.inclusionCodes = function () {
		return Array.from(this.selected.keys());
	};

	WizardCtx.prototype.destroyDialog = function () {
		if (this.dialog) {
			const $wrapper = this.dialog.$wrapper;
			try {
				this.dialog.hide();
			} catch (e) {
				/* noop */
			}
			if ($wrapper && $wrapper.remove) $wrapper.remove();
			this.dialog = null;
		}
	};

	function cancelWizard(ctx) {
		ctx.destroyDialog();
		if (typeof ctx.opts.onCancel === "function") ctx.opts.onCancel();
	}

	// ---------------------------------------------------------------------
	// Step 1 — Select Demands (§8)
	// ---------------------------------------------------------------------

	function demandCardHtml(demand, selected) {
		const d = demand || {};
		const code = String(d.inclusion_code || "");
		const name = String((d.demand || {}).name || d.ref || "");
		const category = String(d.category || "").trim();
		const value = money(d.estimated_value, d.currency);
		const funding = String(d.funding_label || "");
		const dept = String(d.department || "");
		return (
			'<div class="pp2-wizard-demand-card" data-inclusion-code="' +
			esc(code) +
			'" data-testid="pp2-wizard-demand-card" style="border:1px solid var(--border-color,#d1d8dd);border-radius:8px;padding:14px 16px;margin-bottom:10px;' +
			(selected ? "background:var(--control-bg,#f0f4ff);border-color:var(--primary,#485f84);" : "") +
			'">' +
			'<label style="display:flex;align-items:flex-start;gap:12px;cursor:pointer;margin:0;">' +
			'<input type="checkbox" class="pp2-wizard-demand-checkbox" data-testid="pp2-wizard-demand-checkbox"' +
			(selected ? " checked" : "") +
			' style="margin-top:4px;"/>' +
			'<span style="flex:1;">' +
			'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">' +
			(category
				? '<span class="indicator-pill blue" style="font-size:11px;">' + esc(category) + "</span>"
				: "") +
			'<strong style="font-size:14px;">' +
			esc(name) +
			"</strong>" +
			"</div>" +
			'<div class="text-muted small" style="margin-top:4px;">' +
			esc(dept) +
			(dept ? " · " : "") +
			value +
			(funding ? " · " + esc(funding) : "") +
			"</div>" +
			"</span>" +
			"</label>" +
			"</div>"
		);
	}

	function renderDemandList(ctx, dialog, rows) {
		const listEl = dialog.fields_dict.demand_list.$wrapper[0];
		if (!rows.length) {
			listEl.innerHTML =
				'<div class="text-muted small" data-testid="pp2-wizard-empty-state" style="padding:24px;text-align:center;">' +
				esc(
					__(
						"No eligible demands found. Add approved, funded demands to the active plan first."
					)
				) +
				"</div>";
			return;
		}
		rows.forEach(function (d) {
			// Keep pre-selected rows (e.g. arriving from a bulk "Add to Plan +
			// Create Package" action) in sync with the freshly-fetched fields
			// once the real list has loaded, since callers may have only
			// passed minimal placeholder data when opening the wizard.
			if (ctx.selected.has(d.inclusion_code)) ctx.selected.set(d.inclusion_code, d);
		});
		listEl.innerHTML = rows
			.map(function (d) {
				return demandCardHtml(d, ctx.selected.has(d.inclusion_code));
			})
			.join("");
		Array.prototype.forEach.call(
			listEl.querySelectorAll(".pp2-wizard-demand-card"),
			function (card) {
				const code = card.getAttribute("data-inclusion-code");
				const checkbox = card.querySelector(".pp2-wizard-demand-checkbox");
				const row = rows.filter(function (r) {
					return r.inclusion_code === code;
				})[0];
				checkbox.addEventListener("change", function () {
					if (checkbox.checked) {
						ctx.selected.set(code, row);
						card.style.background = "var(--control-bg,#f0f4ff)";
						card.style.borderColor = "var(--primary,#485f84)";
					} else {
						ctx.selected.delete(code);
						card.style.background = "";
						card.style.borderColor = "";
					}
					refreshSelectionSummary(ctx, dialog);
				});
			}
		);
	}

	function fetchAndRenderDemandList(ctx, dialog, search) {
		frappe.call({
			method: ELIGIBLE_DEMANDS_API,
			args: { plan_code: ctx.plan_code, search: search || "" },
			freeze: false,
			callback: function (r) {
				const msg = (r && r.message) || {};
				renderDemandList(ctx, dialog, msg.demands || []);
				refreshSelectionSummary(ctx, dialog);
			},
		});
	}

	function refreshSelectionSummary(ctx, dialog) {
		const summaryEl = dialog.fields_dict.summary.$wrapper[0];
		const codes = ctx.inclusionCodes();
		if (!codes.length) {
			ctx._blocked = false;
			summaryEl.innerHTML =
				'<p class="text-muted small" data-testid="pp2-wizard-selection-empty">' +
				esc(__("No demands selected yet.")) +
				"</p>";
			return;
		}
		const items = Array.from(ctx.selected.values());
		const total = items.reduce(function (sum, i) {
			return sum + (Number(i.estimated_value) || 0);
		}, 0);
		const currency = (items[0] && items[0].currency) || "KES";
		const categories = Array.from(
			new Set(
				items
					.map(function (i) {
						return i.category;
					})
					.filter(Boolean)
			)
		);
		const renderResult = function (compatible, reasons) {
			ctx._blocked = !compatible;
			summaryEl.innerHTML =
				'<div data-testid="pp2-wizard-selection-summary" style="border:1px solid var(--border-color,#d1d8dd);border-radius:8px;padding:14px 16px;">' +
				'<div style="font-weight:700;margin-bottom:8px;">' +
				esc(__("Package Selection Summary")) +
				"</div>" +
				row(__("Selected Demands"), String(items.length)) +
				row(__("Total Estimated Value"), money(total, currency)) +
				row(__("Category"), esc(categories.join(", ") || "—")) +
				(compatible
					? '<div class="text-success small" data-testid="pp2-wizard-compatible" style="margin-top:10px;">✓ ' +
						esc(__("Compatible — ready to configure.")) +
						"</div>"
					: '<div class="text-danger small" data-testid="pp2-wizard-incompatible" style="margin-top:10px;"><b>' +
						esc(__("Not compatible:")) +
						"</b><ul style=\"margin:4px 0 0 18px;padding:0;\">" +
						reasons
							.map(function (r) {
								return "<li>" + esc(r) + "</li>";
							})
							.join("") +
						"</ul></div>") +
				"</div>";
		};
		if (codes.length <= 1) {
			renderResult(true, []);
			return;
		}
		frappe.call({
			method: COMPATIBILITY_API,
			args: { inclusion_codes: codes },
			freeze: false,
			callback: function (r) {
				const msg = (r && r.message) || {};
				renderResult(msg.compatible !== false, msg.reasons || []);
			},
		});
	}

	function openStep1(ctx) {
		ctx.destroyDialog();
		const dialog = new frappe.ui.Dialog({
			title: __("Create Package — Step 1 of 3: Select Demands"),
			size: "large",
			fields: [
				{
					fieldtype: "Data",
					fieldname: "search",
					label: __("Search"),
					placeholder: __("Search by demand title or reference..."),
				},
				{ fieldtype: "Section Break" },
				{
					fieldtype: "HTML",
					fieldname: "demand_list",
					options: '<div data-testid="pp2-wizard-step1-list"></div>',
				},
				{ fieldtype: "Section Break" },
				{
					fieldtype: "HTML",
					fieldname: "summary",
					options: '<div data-testid="pp2-wizard-step1-summary"></div>',
				},
			],
			primary_action_label: __("Next"),
			primary_action: function () {
				if (!ctx.selected.size) {
					frappe.show_alert({ indicator: "orange", message: __("Select at least one demand.") });
					return;
				}
				if (ctx._blocked) {
					frappe.show_alert({
						indicator: "orange",
						message: __("Resolve compatibility issues before continuing."),
					});
					return;
				}
				ctx.destroyDialog();
				openStep2(ctx);
			},
			secondary_action_label: __("Cancel"),
			secondary_action: function () {
				cancelWizard(ctx);
			},
		});
		ctx.dialog = dialog;
		dialog.show();
		dialog.$wrapper.attr("data-testid", "pp2-package-wizard-step1");
		if (ctx.plan_name) {
			dialog.set_title(
				__("Create Package — Step 1 of 3: Select Demands") + " · " + ctx.plan_name
			);
		}
		fetchAndRenderDemandList(ctx, dialog, "");
		refreshSelectionSummary(ctx, dialog);
		dialog.fields_dict.search.$input.on(
			"input",
			frappe.utils.debounce(function () {
				fetchAndRenderDemandList(ctx, dialog, dialog.get_value("search"));
			}, 300)
		);
	}

	// ---------------------------------------------------------------------
	// Step 2 — Configure Package (§9)
	// ---------------------------------------------------------------------

	function linesTableHtml(lines, lineOverrides) {
		if (!lines || !lines.length) return "";
		const rows = lines
			.map(function (line) {
				const code = line.inclusion_code;
				const override = lineOverrides[code] || {};
				return (
					'<tr data-testid="pp2-wizard-line-row" data-inclusion-code="' +
					esc(code) +
					'">' +
					'<td style="padding:6px 8px;">' +
					esc(line.line_title) +
					"</td>" +
					'<td style="padding:6px 8px;" class="text-muted small">' +
					esc(line.scope_quantity) +
					"</td>" +
					'<td style="padding:6px 8px;">' +
					esc(Math.round(Number(line.estimated_value) || 0).toLocaleString("en-US")) +
					"</td>" +
					'<td style="padding:6px 8px;"><input type="text" class="form-control input-xs pp2-wizard-lot-input" data-testid="pp2-wizard-lot-input" placeholder="' +
					esc(__("Lot / group label")) +
					'" value="' +
					esc(override.lot_group || line.lot_group || "") +
					'"/></td>' +
					'<td style="padding:6px 8px;"><input type="text" class="form-control input-xs pp2-wizard-delivery-input" data-testid="pp2-wizard-delivery-input" placeholder="' +
					esc(__("Delivery location")) +
					'" value="' +
					esc(override.delivery_location || line.delivery_location || "") +
					'"/></td>' +
					"</tr>"
				);
			})
			.join("");
		return (
			'<table class="table table-condensed" data-testid="pp2-wizard-lines-table" style="margin-bottom:0;">' +
			"<thead><tr>" +
			"<th>" +
			esc(__("Line")) +
			"</th><th>" +
			esc(__("Scope")) +
			"</th><th>" +
			esc(__("Value")) +
			"</th><th>" +
			esc(__("Lot / Group")) +
			"</th><th>" +
			esc(__("Delivery Location")) +
			"</th></tr></thead><tbody>" +
			rows +
			"</tbody></table>"
		);
	}

	function fundingSummaryHtml(funding) {
		const f = funding || {};
		const toneClass =
			f.funding_status === "Insufficient" || f.funding_status === "Blocked"
				? "text-danger"
				: "text-success";
		return (
			'<div data-testid="pp2-wizard-funding-summary">' +
			row(__("Package Estimated Value"), money(f.package_estimated_value, f.currency)) +
			row(__("Reserved Amount"), money(f.reserved_amount, f.currency)) +
			row(
				__("Funding Status"),
				'<span class="' + toneClass + '">' + esc(f.funding_status || "—") + "</span>"
			) +
			((f.funding_blockers || []).length
				? '<div class="text-danger small" style="margin-top:8px;">' +
					(f.funding_blockers || [])
						.map(function (m) {
							return esc(m);
						})
						.join("<br/>") +
					"</div>"
				: "") +
			"</div>"
		);
	}

	function docPathSummaryHtml(doc) {
		const d = doc || {};
		return (
			'<div data-testid="pp2-wizard-doc-path-summary">' +
			row(__("Required Document Family"), esc(d.required_document_family || "—")) +
			row(
				__("Tender Document Path"),
				d.std_path_resolved
					? esc(d.std_path_label || "—")
					: '<span class="text-warning">' + esc(__("Not resolved")) + "</span>"
			) +
			row(__("Specification Attachments"), String(d.specification_attachments_count || 0)) +
			"</div>"
		);
	}

	function warningsHtml(warnings) {
		const list = warnings || [];
		if (!list.length) return "";
		return (
			'<div class="text-warning small" data-testid="pp2-wizard-warnings" style="margin-top:8px;">' +
			list
				.map(function (w) {
					return "⚠ " + esc(w);
				})
				.join("<br/>") +
			"</div>"
		);
	}

	function collectLineOverridesFromDom(dialog, ctx) {
		const rows = dialog.$wrapper[0].querySelectorAll('[data-testid="pp2-wizard-line-row"]');
		Array.prototype.forEach.call(rows, function (tr) {
			const code = tr.getAttribute("data-inclusion-code");
			const lot = tr.querySelector(".pp2-wizard-lot-input");
			const delivery = tr.querySelector(".pp2-wizard-delivery-input");
			ctx.config.line_overrides[code] = {
				lot_group: lot ? lot.value.trim() : "",
				delivery_location: delivery ? delivery.value.trim() : "",
			};
		});
	}

	function refreshStep2Preview(ctx, dialog, preview) {
		if (dialog.fields_dict.lines_table) {
			dialog.fields_dict.lines_table.$wrapper[0].innerHTML = linesTableHtml(
				preview.lines,
				ctx.config.line_overrides
			);
			bindLineInputListeners(dialog, ctx);
		}
		if (dialog.fields_dict.funding_summary) {
			dialog.fields_dict.funding_summary.$wrapper[0].innerHTML = fundingSummaryHtml(preview.funding);
		}
		if (dialog.fields_dict.warnings) {
			dialog.fields_dict.warnings.$wrapper[0].innerHTML = warningsHtml(preview.warnings);
		}
	}

	function bindLineInputListeners(dialog, ctx) {
		const inputs = dialog.$wrapper[0].querySelectorAll(
			".pp2-wizard-lot-input, .pp2-wizard-delivery-input"
		);
		Array.prototype.forEach.call(inputs, function (input) {
			input.addEventListener("change", function () {
				collectLineOverridesFromDom(dialog, ctx);
			});
		});
	}

	function fetchStep2Preview(ctx, dialog, opts) {
		const o = opts || {};
		frappe.call({
			method: CONFIG_PREVIEW_API,
			args: { inclusion_codes: ctx.inclusionCodes(), config: ctx.config },
			freeze: false,
			callback: function (r) {
				const preview = (r && r.message) || {};
				if (!preview.ok) {
					frappe.show_alert({
						indicator: "red",
						message: preview.message || __("Could not load package configuration."),
					});
					return;
				}
				if (o.applyDefaults) {
					const identity = preview.package_identity || {};
					const cm = preview.category_method || {};
					if (!ctx.config.package_title) ctx.config.package_title = identity.package_title || "";
					if (!ctx.config.package_owner) ctx.config.package_owner = identity.package_owner || frappe.session.user;
					if (!ctx.config.package_priority) ctx.config.package_priority = identity.package_priority || "Normal";
					if (!ctx.config.procurement_method)
						ctx.config.procurement_method = cm.procurement_method || cm.recommended_method || "";
					dialog.set_value("package_title", ctx.config.package_title);
					dialog.set_value("package_owner", ctx.config.package_owner);
					dialog.set_value("package_priority", ctx.config.package_priority);
					dialog.set_value("procurement_method", ctx.config.procurement_method);
					if (dialog.fields_dict.recommended_method_hint) {
						dialog.fields_dict.recommended_method_hint.$wrapper[0].innerHTML = cm.recommended_method
							? '<span class="text-muted small">' +
								esc(__("Recommended: {0}", [cm.recommended_method])) +
								"</span>"
							: "";
					}
				}
				ctx._lastPreview = preview;
				refreshStep2Preview(ctx, dialog, preview);
				frappe.call({
					method: DOC_PATH_API,
					args: { inclusion_codes: ctx.inclusionCodes(), config: ctx.config },
					freeze: false,
					callback: function (docR) {
						const docPreview = (docR && docR.message) || {};
						if (dialog.fields_dict.doc_path_summary) {
							dialog.fields_dict.doc_path_summary.$wrapper[0].innerHTML = docPathSummaryHtml(
								docPreview
							);
						}
					},
				});
			},
		});
	}

	function openStep2(ctx) {
		const dialog = new frappe.ui.Dialog({
			title: __("Create Package — Step 2 of 3: Configure Package"),
			size: "large",
			fields: [
				{
					fieldtype: "Data",
					fieldname: "package_title",
					label: __("Package Title"),
					reqd: 1,
					default: ctx.config.package_title,
				},
				{
					fieldtype: "Small Text",
					fieldname: "package_description",
					label: __("Description"),
					default: ctx.config.package_description,
				},
				{ fieldtype: "Column Break" },
				{
					fieldtype: "Link",
					fieldname: "package_owner",
					label: __("Package Owner"),
					options: "User",
					default: ctx.config.package_owner,
				},
				{
					fieldtype: "Date",
					fieldname: "target_release_date",
					label: __("Target Release Date"),
					default: ctx.config.target_release_date,
				},
				{
					fieldtype: "Select",
					fieldname: "package_priority",
					label: __("Priority"),
					options: "Normal\nHigh\nEmergency",
					default: ctx.config.package_priority,
				},
				{ fieldtype: "Section Break", label: __("Category & Method") },
				{
					fieldtype: "Data",
					fieldname: "procurement_method",
					label: __("Procurement Method"),
					default: ctx.config.procurement_method,
				},
				{
					fieldtype: "HTML",
					fieldname: "recommended_method_hint",
					options: "<div></div>",
				},
				{ fieldtype: "Column Break" },
				{
					fieldtype: "Small Text",
					fieldname: "method_override_reason",
					label: __("Override Justification (required if method changed)"),
					default: ctx.config.method_override_reason,
				},
				{ fieldtype: "Section Break", label: __("Lines & Lots") },
				{
					fieldtype: "HTML",
					fieldname: "lines_table",
					options: '<div data-testid="pp2-wizard-lines-host"></div>',
				},
				{ fieldtype: "Section Break", label: __("Funding") },
				{
					fieldtype: "HTML",
					fieldname: "funding_summary",
					options: '<div data-testid="pp2-wizard-funding-host"></div>',
				},
				{ fieldtype: "Section Break", label: __("Document / Tender Path") },
				{
					fieldtype: "HTML",
					fieldname: "doc_path_summary",
					options: '<div data-testid="pp2-wizard-doc-path-host"></div>',
				},
				{ fieldtype: "Section Break" },
				{
					fieldtype: "HTML",
					fieldname: "warnings",
					options: '<div data-testid="pp2-wizard-warnings-host"></div>',
				},
			],
			primary_action_label: __("Next"),
			primary_action: function () {
				readStep2Values(ctx, dialog);
				if (!ctx.config.package_title) {
					frappe.show_alert({ indicator: "orange", message: __("Enter a package title.") });
					return;
				}
				ctx.destroyDialog();
				openStep3(ctx);
			},
			secondary_action_label: __("Back"),
			secondary_action: function () {
				readStep2Values(ctx, dialog);
				ctx.destroyDialog();
				openStep1(ctx);
			},
		});
		ctx.dialog = dialog;
		dialog.show();
		dialog.$wrapper.attr("data-testid", "pp2-package-wizard-step2");

		["package_title", "package_description", "package_owner", "target_release_date", "package_priority", "procurement_method", "method_override_reason"].forEach(
			function (fieldname) {
				const field = dialog.fields_dict[fieldname];
				if (field && field.df) {
					field.df.onchange = function () {
						readStep2Values(ctx, dialog);
						if (fieldname === "procurement_method" || fieldname === "method_override_reason") {
							fetchStep2Preview(ctx, dialog, { applyDefaults: false });
						}
					};
				}
			}
		);

		fetchStep2Preview(ctx, dialog, { applyDefaults: !ctx.config.package_title });
	}

	function readStep2Values(ctx, dialog) {
		ctx.config.package_title = String(dialog.get_value("package_title") || "").trim();
		ctx.config.package_description = String(dialog.get_value("package_description") || "").trim();
		ctx.config.package_owner = String(dialog.get_value("package_owner") || "").trim();
		ctx.config.target_release_date = dialog.get_value("target_release_date") || "";
		ctx.config.package_priority = dialog.get_value("package_priority") || "Normal";
		ctx.config.procurement_method = String(dialog.get_value("procurement_method") || "").trim();
		ctx.config.method_override_reason = String(dialog.get_value("method_override_reason") || "").trim();
		collectLineOverridesFromDom(dialog, ctx);
	}

	// ---------------------------------------------------------------------
	// Step 3 — Review and Create (§10)
	// ---------------------------------------------------------------------

	const READINESS_ICON = { Ready: "✓", Warning: "⚠", Blocked: "✕" };
	const READINESS_CLASS = { Ready: "text-success", Warning: "text-warning", Blocked: "text-danger" };

	function readinessChecklistHtml(checks) {
		return (
			'<ul style="list-style:none;padding:0;margin:0;" data-testid="pp2-wizard-readiness-list">' +
			(checks || [])
				.map(function (c) {
					return (
						'<li data-testid="pp2-wizard-readiness-row" data-status="' +
						esc(c.status) +
						'" style="padding:6px 0;border-bottom:1px solid var(--border-color,#e0e3e5);">' +
						'<span class="' +
						(READINESS_CLASS[c.status] || "") +
						'" style="font-weight:700;margin-right:8px;">' +
						(READINESS_ICON[c.status] || "•") +
						"</span>" +
						"<span>" +
						esc(c.label) +
						"</span>" +
						(c.message
							? '<div class="text-muted small" style="margin-left:22px;">' + esc(c.message) + "</div>"
							: "") +
						"</li>"
					);
				})
				.join("") +
			"</ul>"
		);
	}

	function reviewSummaryHtml(ctx, preview) {
		const identity = preview.package_identity || {};
		const cm = preview.category_method || {};
		const items = Array.from(ctx.selected.values());
		return (
			'<div data-testid="pp2-wizard-review-summary">' +
			row(__("Package Title"), esc(identity.package_title || "—")) +
			row(__("Owner"), esc(identity.package_owner || "—")) +
			row(__("Priority"), esc(identity.package_priority || "—")) +
			row(__("Category"), esc(cm.category || "—")) +
			row(__("Method"), esc(cm.procurement_method || "—")) +
			row(__("Selected Demands"), String(items.length)) +
			"</div>"
		);
	}

	function openStep3(ctx) {
		const dialog = new frappe.ui.Dialog({
			title: __("Create Package — Step 3 of 3: Review and Create"),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "review_summary",
					options: '<div data-testid="pp2-wizard-review-summary-host"></div>',
				},
				{ fieldtype: "Section Break", label: __("Readiness") },
				{
					fieldtype: "HTML",
					fieldname: "readiness",
					options: '<div data-testid="pp2-wizard-readiness-host"></div>',
				},
				{ fieldtype: "Section Break" },
				{
					fieldtype: "HTML",
					fieldname: "blocking_reasons",
					options: '<div data-testid="pp2-wizard-blocking-host"></div>',
				},
			],
			primary_action_label: __("Create Package"),
			primary_action: function () {
				dialog.set_primary_action(__("Creating..."), function () {});
				frappe.call({
					method: CREATE_API,
					args: { inclusion_codes: ctx.inclusionCodes(), config: ctx.config },
					freeze: true,
					callback: function (r) {
						const result = (r && r.message) || {};
						if (!result.ok) {
							frappe.msgprint({
								title: __("Unable to create package"),
								indicator: "orange",
								message:
									esc(result.message || __("The package could not be created.")) +
									((result.blocking_reasons || []).length
										? "<ul>" +
											result.blocking_reasons
												.map(function (b) {
													return "<li>" + esc(b) + "</li>";
												})
												.join("") +
											"</ul>"
										: ""),
							});
							dialog.set_primary_action(__("Create Package"), dialog.primary_action);
							return;
						}
						ctx.destroyDialog();
						openStep4Success(ctx, result);
					},
					error: function () {
						dialog.set_primary_action(__("Create Package"), dialog.primary_action);
					},
				});
			},
			secondary_action_label: __("Back"),
			secondary_action: function () {
				ctx.destroyDialog();
				openStep2(ctx);
			},
		});
		ctx.dialog = dialog;
		dialog.show();
		dialog.$wrapper.attr("data-testid", "pp2-package-wizard-step3");

		frappe.call({
			method: READINESS_API,
			args: { inclusion_codes: ctx.inclusionCodes(), config: ctx.config },
			freeze: false,
			callback: function (r) {
				const readiness = (r && r.message) || {};
				dialog.fields_dict.readiness.$wrapper[0].innerHTML = readinessChecklistHtml(readiness.checks);
				const blockers = readiness.blocking_reasons || [];
				dialog.fields_dict.blocking_reasons.$wrapper[0].innerHTML = blockers.length
					? '<div class="text-danger small" data-testid="pp2-wizard-blocking-reasons">' +
						blockers
							.map(function (b) {
								return "⚠ " + esc(b);
							})
							.join("<br/>") +
						"</div>"
					: "";
				const primaryBtn = dialog.get_primary_btn();
				if (readiness.create_allowed === false && primaryBtn && primaryBtn.prop) {
					primaryBtn.prop("disabled", true);
				} else if (primaryBtn && primaryBtn.prop) {
					primaryBtn.prop("disabled", false);
				}
			},
		});

		frappe.call({
			method: CONFIG_PREVIEW_API,
			args: { inclusion_codes: ctx.inclusionCodes(), config: ctx.config },
			freeze: false,
			callback: function (r) {
				const preview = (r && r.message) || {};
				if (preview.ok) {
					dialog.fields_dict.review_summary.$wrapper[0].innerHTML = reviewSummaryHtml(ctx, preview);
				}
			},
		});
	}

	// ---------------------------------------------------------------------
	// Step 4 — Success (§11)
	// ---------------------------------------------------------------------

	function openStep4Success(ctx, result) {
		const pkg = result.package || {};
		const demandTitles = result.demand_titles || [];
		const dialog = new frappe.ui.Dialog({
			title: __("Package Created"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "success",
					options:
						'<div data-testid="pp2-wizard-success" style="text-align:center;padding:12px 0;">' +
						'<div class="text-success" style="font-size:40px;">✓</div>' +
						'<h4 style="margin-top:8px;">' +
						esc(__("{0} has been created.", [pkg.package_name || __("Package")])) +
						"</h4>" +
						'<p class="text-muted small">' +
						esc(
							__("{0} demand(s) included: {1}", [
								String(demandTitles.length),
								demandTitles.join(", "),
							])
						) +
						"</p>" +
						"</div>",
				},
			],
			primary_action_label: __("Open Package"),
			primary_action: function () {
				dialog.hide();
				dialog.$wrapper.remove();
				if (typeof ctx.opts.onSuccess === "function") {
					ctx.opts.onSuccess(Object.assign({ action: "open_package" }, result));
				}
			},
			secondary_action_label: __("Back to Workbench"),
			secondary_action: function () {
				dialog.hide();
				dialog.$wrapper.remove();
				if (typeof ctx.opts.onSuccess === "function") {
					ctx.opts.onSuccess(Object.assign({ action: "back_to_workbench" }, result));
				}
			},
		});
		dialog.show();
		dialog.$wrapper.attr("data-testid", "pp2-package-wizard-step4");
	}

	// ---------------------------------------------------------------------
	// Public entry point
	// ---------------------------------------------------------------------

	function open(opts) {
		const o = opts || {};
		if (!String(o.plan_code || "").trim()) {
			frappe.show_alert({ indicator: "orange", message: __("No active procurement plan found.") });
			return { opened: false };
		}
		const ctx = new WizardCtx(o);
		if (Array.isArray(o.initial_demand_rows)) {
			o.initial_demand_rows.forEach(function (r) {
				if (r && r.inclusion_code) ctx.selected.set(r.inclusion_code, r);
			});
		}
		openStep1(ctx);
		return { opened: true, ctx: ctx };
	}

	kentender_procurement.PlanningPackageWizard = { open: open };
})();
