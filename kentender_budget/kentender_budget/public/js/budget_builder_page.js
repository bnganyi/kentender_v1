(function () {
	function escapeHtml(v) {
		if (v === null || v === undefined) {
			return "";
		}
		return String(v)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function testIdPart(value) {
		if (value === null || value === undefined || value === "") {
			return "unknown";
		}
		return String(value).replace(/[^a-zA-Z0-9 _-]/g, "_");
	}

	function formatAmount(value, digits) {
		const n = Number(value);
		if (Number.isNaN(n)) {
			return "0";
		}
		const precision = Number.isInteger(digits) ? digits : 2;
		return n.toLocaleString("en-US", {
			minimumFractionDigits: precision,
			maximumFractionDigits: precision,
		});
	}

	function budgetFromRoute() {
		const r = frappe.get_route() || [];
		return r.length > 1 ? r[1] : null;
	}

	/** Match landing `budget_workspace.js` display normalization for test suffixes. */
	function displayBudgetLabel(raw) {
		const s = String(raw || "").trim();
		return s.replace(/\s+\d{10,}$/, "");
	}

	function statusKeyFromRaw(statusRaw) {
		const s = String(statusRaw || "")
			.toLowerCase()
			.trim();
		if (s === "approved") {
			return "approved";
		}
		if (s === "submitted") {
			return "submitted";
		}
		if (s === "rejected") {
			return "rejected";
		}
		return "draft";
	}

	function budgetBadgeClass(statusRaw) {
		const k = statusKeyFromRaw(statusRaw);
		return "kt-budget-badge kt-budget-badge--" + k;
	}

	function formatReferenceDisplay(label, code) {
		const cleanLabel = String(label || "").trim();
		const cleanCode = String(code || "").trim();
		if (!cleanLabel && !cleanCode) {
			return "—";
		}
		if (!cleanCode) {
			return cleanLabel || "—";
		}
		return `${cleanLabel} (${cleanCode})`;
	}

	function stripInternalIdFromDescription(description) {
		const raw = String(description || "").trim();
		if (!raw) {
			return raw;
		}
		// Frappe title-link suggestions prepend internal id in description. Remove it.
		return raw.replace(/^[a-z0-9]{8,}\s*,\s*/i, "");
	}

	/** Desk breadcrumb URLs — same pattern as `frappe.views.breadcrumbs`. */
	function builderBreadcrumbHrefs() {
		let desk = "/desk";
		let workspace = "/desk/Workspaces/Budget%20Management";
		try {
			if (frappe.router && typeof frappe.router.make_url === "function") {
				desk = frappe.router.make_url([]);
				workspace = frappe.router.make_url(["Workspaces", "Budget Management"]);
			}
		} catch (e) {
			/* ignore */
		}
		return { desk, workspace };
	}

	function builderMonitorIconHtml() {
		try {
			if (frappe.utils && typeof frappe.utils.icon === "function") {
				return frappe.utils.icon("monitor");
			}
		} catch (e) {
			/* ignore */
		}
		return "";
	}

	function renderBuilderBreadcrumbs() {
		const { desk, workspace } = builderBreadcrumbHrefs();
		const icon = builderMonitorIconHtml();
		return (
			`<nav class="kt-bb-page-nav" aria-label="${escapeHtml(__("Breadcrumb"))}">` +
			`<ul class="nav d-sm-flex navbar-breadcrumbs ellipsis" data-testid="budget-builder-nav">` +
			`<li><a href="${escapeHtml(desk)}">${icon}</a></li>` +
			`<li class="ellipsis"><a href="${escapeHtml(workspace)}" data-testid="budget-builder-back-to-landing">${escapeHtml(
				__("Budget Management")
			)}</a></li>` +
			`<li class="disabled ellipsis"><a href="javascript:void(0)">${escapeHtml(__("Budget Builder"))}</a></li>` +
			`</ul></nav>`
		);
	}

	/**
	 * Standard desk: full-width `.page-head` (breadcrumbs) + container body.
	 * Body uses `kt-budget-builder-shell` so `budget_workspace.css` tokens apply (same as landing).
	 */
	function deskPageLayout(headInnerHtml, bodyInnerHtml) {
		return (
			`<div class="kt-bb-builder-layout">` +
			`<header class="kt-bb-page-head">` +
			`<div class="container">` +
			headInnerHtml +
			`</div></header>` +
			`<div class="container kt-bb-page-body">` +
			`<div class="kt-budget-builder-shell" data-testid="budget-builder-page">` +
			bodyInnerHtml +
			`</div></div></div>`
		);
	}

	function renderWorkspaceHeaderBlock(opts) {
		opts = opts || {};
		const subtitle = opts.subtitle != null ? opts.subtitle : "";
		const title = opts.title != null ? opts.title : __("Budget Builder");
		return (
			`<div class="kt-budget-workspace-header mb-3">` +
			`<div class="kt-budget-header-row">` +
			`<h2 class="kt-budget-page-title h4 mb-2">${escapeHtml(title)}</h2>` +
			`<div class="kt-budget-header-cta" data-testid="budget-builder-header-cta">` +
			(opts.showBack === false
				? ""
				: `<button type="button" class="btn btn-default btn-sm" data-testid="budget-builder-back-button">${escapeHtml(
						__("Back to Budgets")
					)}</button>`) +
			`</div></div>` +
			`<p class="kt-budget-page-intro text-muted mb-0" data-testid="budget-builder-intro">${escapeHtml(subtitle)}</p>` +
			`</div>`
		);
	}

	class BudgetBuilderPage {
		constructor($wrapper) {
			this.$wrapper = $wrapper;
			this.budgetName = null;
			this.payload = null;
			this.selectedBudgetLineName = null;
			this.readOnly = false;
			/** @type {"active"|"inactive"|"all"} */
			this.linesFilter = "active";
		}

		init() {
			this.budgetName = budgetFromRoute();
			if (!this.budgetName) {
				const headHtml = renderBuilderBreadcrumbs();
				const bodyHtml =
					renderWorkspaceHeaderBlock({ subtitle: "", showBack: false }) +
					`<div class="alert alert-warning">${__("Open this page from a Budget (missing budget in URL).")}</div>`;
				this.$wrapper.html(deskPageLayout(headHtml, bodyHtml));
				this.applyDocumentTitle();
				return;
			}
			this.renderLoading();
			this.bindRouteChange();
			this.load();
		}

		bindRouteChange() {
			const me = this;
			$(document)
				.off("page-change.kt_budget_builder")
				.on("page-change.kt_budget_builder", function () {
					const r = frappe.get_route() || [];
					if (r[0] !== "budget-builder") {
						return;
					}
					const next = r[1] || null;
					if (next && next !== me.budgetName) {
						me.budgetName = next;
						me.renderLoading();
						me.load();
					}
				});
		}

		renderLoading() {
			const headHtml = renderBuilderBreadcrumbs();
			const bodyHtml =
				renderWorkspaceHeaderBlock({ subtitle: "" }) +
				`<div class="text-muted small">${__("Loading…")}</div>`;
			this.$wrapper.html(deskPageLayout(headHtml, bodyHtml));
			this.applyDocumentTitle();
		}

		load() {
			const me = this;
			return frappe
				.call({
					method: "kentender_budget.api.builder.get_budget_builder_data",
					args: { budget_name: me.budgetName, lines_filter: me.linesFilter },
				})
				.then((r) => {
					me.payload = r.message || {};
					const lines = me.payload.budget_lines || [];
					if (me.selectedBudgetLineName && !lines.some((p) => p.name === me.selectedBudgetLineName)) {
						me.selectedBudgetLineName = null;
					}
					me.render();
				})
				.catch(() => {
					const headHtml = renderBuilderBreadcrumbs();
					const bodyHtml =
						renderWorkspaceHeaderBlock({ subtitle: "" }) +
						`<div class="alert alert-danger">${__("Could not load Budget Builder data.")}</div>`;
					me.$wrapper.html(deskPageLayout(headHtml, bodyHtml));
					me.applyDocumentTitle();
				});
		}

		getSelectedBudgetLine() {
			const lines = (this.payload && this.payload.budget_lines) || [];
			if (!this.selectedBudgetLineName) {
				return null;
			}
			return lines.find((p) => p.name === this.selectedBudgetLineName) || null;
		}

		renderBudgetLineList(lines) {
			if (!lines || !lines.length) {
				return `<div class="text-muted small">${__("No budget lines in this view.")}</div>`;
			}
			return lines
				.map((p) => {
					const label = p.budget_line_name || p.name;
					const idPart = testIdPart(label);
					const active = p.name === this.selectedBudgetLineName ? " is-active" : "";
					const inactiveRow = !Number(p.is_active || 0) ? " kt-budget-row--inactive" : "";
					const amt = escapeHtml(formatAmount(p.amount_allocated, 2));
					const programLabel = p.program_label || p.program || __("No Program");
					let badgeHtml = "";
					if (Number(p.amount_allocated || 0) === 0) {
						badgeHtml = `<span class="kt-budget-line-mini-badge">${escapeHtml(__("Unallocated"))}</span>`;
					} else if (!Number(p.is_active || 0)) {
						badgeHtml = `<span class="kt-budget-line-mini-badge">${escapeHtml(__("Inactive"))}</span>`;
					}
					return `<button type="button" class="kt-budget-row${active}${inactiveRow}" data-budget-line="${escapeHtml(
						p.name
					)}" data-testid="budget-line-row-${escapeHtml(idPart)}">
						<span class="kt-budget-row__main">
							<span class="kt-budget-row__title">${escapeHtml(label)}</span>
							<span class="kt-budget-row__meta">${escapeHtml(p.budget_line_code || "")} · ${escapeHtml(programLabel)}</span>
						</span>
						<span class="text-muted small text-right" data-testid="budget-line-row-amount-${escapeHtml(idPart)}">KES ${amt}${badgeHtml ? `<br/>${badgeHtml}` : ""}</span>
					</button>`;
				})
				.join("");
		}

		renderEditor(selectedLine) {
			if (!selectedLine) {
				return `<div class="kt-budget-section kt-surface" data-testid="budget-allocation-editor">
					<h3 class="kt-budget-section__title" data-testid="budget-line-editor-title">${escapeHtml(
						__("Budget Line Editor")
					)}</h3>
					<div class="text-muted" data-testid="budget-builder-empty-selection">
						${escapeHtml(__("Select a budget line from the list to view or edit details."))}
					</div>
				</div>`;
			}
			const lineLocked = this.readOnly || !Number(selectedLine.is_active || 0);
			const disabledAttr = lineLocked ? ' disabled aria-disabled="true"' : "";
			const identityMeta = `${selectedLine.budget_line_code || ""} · ${formatReferenceDisplay(
				selectedLine.program_label || selectedLine.program || __("No Program"),
				selectedLine.program_code,
			)}`;
			const parentBudget = (this.payload && this.payload.budget) || {};
			const saveBtn =
				!lineLocked && !this.readOnly
					? `<button type="button" class="btn btn-primary btn-sm" data-testid="budget-allocation-save-button">${escapeHtml(__("Save Budget Line"))}</button>`
					: "";
			const removeBtn =
				!lineLocked && !this.readOnly && selectedLine.can_remove
					? `<button type="button" class="btn btn-default btn-sm kt-budget-line-remove-btn" data-testid="budget-line-remove-button">${escapeHtml(__("Remove"))}</button>`
					: "";
			const deleteBtn =
				!this.readOnly && selectedLine.can_hard_delete
					? `<button type="button" class="btn btn-default btn-sm kt-budget-line-hard-delete-btn" data-testid="budget-line-hard-delete-button">${escapeHtml(__("Delete"))}</button>`
					: "";
			const headerActions =
				saveBtn || removeBtn || deleteBtn
					? `<div class="kt-budget-line-editor-header__actions">${saveBtn}${removeBtn ? ` ${removeBtn}` : ""}${
							deleteBtn ? ` ${deleteBtn}` : ""
						}</div>`
					: "";
			return `<div class="kt-budget-section kt-surface" data-testid="budget-allocation-editor">
				<div class="kt-budget-line-editor-header">
					<div class="kt-budget-line-editor-header__identity">
						<h3 class="kt-budget-section__title mb-1" data-testid="budget-line-editor-title">${escapeHtml(
							selectedLine.budget_line_name || selectedLine.name
						)}</h3>
						<div class="text-muted small">${escapeHtml(identityMeta)}</div>
					</div>
					${headerActions}
				</div>

				<div class="small text-muted mb-2 mt-3">${escapeHtml(__("Budget Line Definition"))}</div>
				<div class="row">
					<div class="col-12 col-md-6">
						<div class="form-group mb-2">
							<label class="small text-muted">${escapeHtml(__("Budget Line Name"))}</label>
							<input type="text" class="form-control" data-testid="budget-line-name-input"${disabledAttr} value="${escapeHtml(selectedLine.budget_line_name || "")}" />
						</div>
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Budget Line Code"))}</div><div class="kt-budget-display-row__value">${escapeHtml(selectedLine.budget_line_code || "—")}</div></div>
					</div>
					<div class="col-12 col-md-6">
						<div class="form-group mb-2">
							<label class="small text-muted">${escapeHtml(__("Allocated Amount"))}</label>
							<input type="number" step="any" min="0" class="form-control" data-testid="budget-allocation-amount-input"${disabledAttr} value="${escapeHtml(
								String(selectedLine.amount_allocated || "")
							)}" />
						</div>
						<div class="form-group mb-2">
							<label class="small text-muted">${escapeHtml(__("Funding Source"))}</label>
							<input type="text" class="form-control" data-testid="budget-funding-source-input"${disabledAttr} value="${escapeHtml(selectedLine.funding_source || "")}" />
						</div>
					</div>
				</div>
				<div class="form-group mb-2">
					<label class="small text-muted">${escapeHtml(__("Notes"))}</label>
					<textarea rows="2" class="form-control kt-budget-notes-input" data-testid="budget-allocation-notes-input"${disabledAttr}>${escapeHtml(
						selectedLine.notes || ""
					)}</textarea>
				</div>

				<div class="small text-muted mb-2 mt-3">${escapeHtml(__("Strategic Context"))}</div>
				<div class="row">
					<div class="col-12 col-md-6">
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Program"))}</div><div class="kt-budget-display-row__value">${escapeHtml(formatReferenceDisplay(selectedLine.program_label || selectedLine.program, selectedLine.program_code))}</div></div>
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Sub-Program"))}</div><div class="kt-budget-display-row__value">${escapeHtml(formatReferenceDisplay(selectedLine.sub_program_label || selectedLine.sub_program, selectedLine.sub_program_code))}</div></div>
					</div>
					<div class="col-12 col-md-6">
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Output Indicator"))}</div><div class="kt-budget-display-row__value">${escapeHtml(formatReferenceDisplay(selectedLine.output_indicator_label || selectedLine.output_indicator, selectedLine.output_indicator_code))}</div></div>
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Performance Target"))}</div><div class="kt-budget-display-row__value">${escapeHtml(formatReferenceDisplay(selectedLine.performance_target_label || selectedLine.performance_target, selectedLine.performance_target_code))}</div></div>
					</div>
				</div>

				<div class="small text-muted mb-2 mt-3">${escapeHtml(__("Financial Context"))}</div>
				<div class="row">
					<div class="col-12 col-md-6">
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Reserved Amount"))}</div><div class="kt-budget-display-row__value">KES ${escapeHtml(formatAmount(selectedLine.amount_reserved, 2))}</div></div>
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Available Amount"))}</div><div class="kt-budget-display-row__value">KES ${escapeHtml(formatAmount(selectedLine.amount_available, 2))}</div></div>
					</div>
					<div class="col-12 col-md-6">
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Currency"))}</div><div class="kt-budget-display-row__value">${escapeHtml(parentBudget.currency || "—")}</div></div>
						<div class="kt-budget-display-row"><div class="kt-budget-display-row__label">${escapeHtml(__("Active"))}</div><div class="kt-budget-display-row__value">${Number(selectedLine.is_active || 0) ? escapeHtml(__("Yes")) : escapeHtml(__("No"))}</div></div>
					</div>
				</div>
			</div>`;
		}

		showAddBudgetLineModal() {
			const strategicPlan = ((this.payload || {}).budget || {}).strategic_plan;
			const d = new frappe.ui.Dialog({
				title: __("Add Budget Line"),
				fields: [
					{ fieldname: "budget_line_name", label: __("Budget Line Name"), fieldtype: "Data", reqd: 1 },
					{ fieldname: "amount_allocated", label: __("Allocated Amount"), fieldtype: "Currency", reqd: 1, default: 0 },
					{ fieldname: "funding_source", label: __("Funding Source"), fieldtype: "Link", options: "Funding Source" },
					{ fieldname: "program", label: __("Program"), fieldtype: "Link", options: "Strategy Program", reqd: 1 },
					{ fieldname: "sub_program", label: __("Sub-Program"), fieldtype: "Link", options: "Sub Program" },
					{ fieldname: "output_indicator", label: __("Output Indicator"), fieldtype: "Link", options: "Strategy Objective" },
					{ fieldname: "performance_target", label: __("Performance Target"), fieldtype: "Link", options: "Strategy Target" },
					{ fieldname: "notes", label: __("Notes"), fieldtype: "Text" },
				],
				primary_action_label: __("Create Budget Line"),
				primary_action: (values) => {
					const beforeNames = new Set(((this.payload || {}).budget_lines || []).map((x) => x.name));
					frappe.call({
						method: "kentender_budget.api.builder.upsert_budget_line",
						args: { budget_name: this.budgetName, lines_filter: this.linesFilter, ...values },
					}).then((r) => {
						this.payload = r.message || {};
						const lines = this.payload.budget_lines || [];
						let created = null;
						created = lines.find((x) => !beforeNames.has(x.name)) || null;
						this.selectedBudgetLineName = created ? created.name : null;
						this.render();
						d.hide();
					});
				},
			});
			const programField = d.get_field("program");
			const subProgramField = d.get_field("sub_program");
			const objectiveField = d.get_field("output_indicator");
			const targetField = d.get_field("performance_target");
			programField.get_query = () => ({
				filters: strategicPlan ? { strategic_plan: strategicPlan } : {},
			});
			subProgramField.get_query = () => {
				const program = d.get_value("program");
				return {
					filters: program ? { program } : { name: ["=", ""] },
				};
			};
			objectiveField.get_query = () => {
				const program = d.get_value("program");
				const filters = {};
				if (strategicPlan) {
					filters.strategic_plan = strategicPlan;
				}
				if (program) {
					filters.program = program;
				}
				return { filters };
			};
			targetField.get_query = () => {
				const program = d.get_value("program");
				const objective = d.get_value("output_indicator");
				const filters = {};
				if (strategicPlan) {
					filters.strategic_plan = strategicPlan;
				}
				if (program) {
					filters.program = program;
				}
				if (objective) {
					filters.objective = objective;
				}
				return Object.keys(filters).length ? { filters } : { filters: { name: ["=", ""] } };
			};
			programField.df.onchange = () => {
				d.set_value("sub_program", "");
				d.set_value("output_indicator", "");
				d.set_value("performance_target", "");
			};
			subProgramField.df.onchange = () => {
				d.set_value("output_indicator", "");
				d.set_value("performance_target", "");
			};
			objectiveField.df.onchange = () => {
				d.set_value("performance_target", "");
			};
			d.show();
			["program", "sub_program", "output_indicator", "performance_target"].forEach((fieldname) => {
				const control = d.fields_dict[fieldname];
				if (!control || !control.awesomplete || typeof control.awesomplete.get_item !== "function") {
					return;
				}
				const originalGetItem = control.awesomplete.get_item.bind(control.awesomplete);
				control.awesomplete.get_item = function (value) {
					const item = originalGetItem(value);
					if (!item || !item.description) {
						return item;
					}
					return {
						...item,
						description: stripInternalIdFromDescription(item.description),
					};
				};
			});
		}

		applyDocumentTitle() {
			if (!frappe.utils || typeof frappe.utils.set_title !== "function") {
				return;
			}
			const base = __("Budget Builder");
			const b = this.payload && this.payload.budget;
			if (b) {
				const raw = String(b.budget_name || b.name || "").trim();
				const plain = raw
					? typeof strip_html === "function"
						? strip_html(raw)
						: raw.replace(/<[^>]*>/g, "")
					: "";
				const label = plain ? displayBudgetLabel(plain) : "";
				if (label) {
					frappe.utils.set_title(`${label} · ${base}`);
					return;
				}
			}
			frappe.utils.set_title(base);
		}

		render() {
			const budget = (this.payload && this.payload.budget) || {};
			const totals = (this.payload && this.payload.totals) || {};
			const budgetLines = (this.payload && this.payload.budget_lines) || [];
			if (!this.selectedBudgetLineName && budgetLines.length) {
				this.selectedBudgetLineName = budgetLines[0].name;
			}
			const selectedLine = this.getSelectedBudgetLine();
			const intro = displayBudgetLabel(budget.budget_name || budget.name || "");
			const st = String(budget.status || "Draft").trim();
			this.readOnly = st === "Submitted" || st === "Approved";
			let lockBanner = "";
			if (this.readOnly) {
				lockBanner = `<div class="alert alert-info mb-3 kt-budget-builder-lock-banner" data-testid="budget-builder-readonly-banner" role="status">${escapeHtml(
					st === "Approved"
						? __("This budget is approved and locked.")
						: __("This budget is submitted and awaiting approval."),
				)}</div>`;
			} else if (st === "Rejected" && budget.rejection_reason) {
				lockBanner = `<div class="alert alert-danger mb-3 kt-budget-builder-rejected-banner" data-testid="budget-builder-rejected-banner" role="status">${escapeHtml(
					__("This budget was rejected. Revise allocations and re-submit."),
				)}<br/><span class="small">${escapeHtml(String(budget.rejection_reason))}</span></div>`;
			}
			const stKey = statusKeyFromRaw(st);
			const statusRow =
				`<div class="mb-2 d-flex align-items-center flex-wrap gap-2" data-testid="budget-builder-status-row">` +
				`<span class="${budgetBadgeClass(st)}" data-testid="budget-builder-status-badge" data-kt-status="${escapeHtml(stKey)}">${escapeHtml(
					__(st),
				)}</span>` +
				`</div>`;
			const headHtml = renderBuilderBreadcrumbs();
			const bodyHtml =
				renderWorkspaceHeaderBlock({ subtitle: intro }) +
				statusRow +
				lockBanner +
				`<div class="kt-budget-overview-metrics row g-3 mb-3">` +
				`<div class="col-12 col-md-4">` +
				`<div class="kt-budget-kpi-card kt-surface">` +
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Total Budget"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-total">${escapeHtml(formatAmount(totals.total_budget_amount, 2))}</div>` +
				`</div></div>` +
				`<div class="col-12 col-md-4">` +
				`<div class="kt-budget-kpi-card kt-surface">` +
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Line Allocated"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-allocated">${escapeHtml(formatAmount(totals.allocated_sum, 2))}</div>` +
				`</div></div>` +
				`<div class="col-12 col-md-4">` +
				`<div class="kt-budget-kpi-card kt-surface">` +
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Line Unallocated"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-remaining">${escapeHtml(formatAmount(totals.remaining_amount, 2))}</div>` +
				`</div></div>` +
				`<div class="col-12 col-md-4">` +
				`<div class="kt-budget-kpi-card kt-surface">` +
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Available for Reservation"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-available">${escapeHtml(formatAmount(totals.available_sum, 2))}</div>` +
				`<div class="small text-muted" data-testid="budget-builder-reserved">${escapeHtml(__("Reserved"))}: ${escapeHtml(formatAmount(totals.reserved_sum, 2))}</div>` +
				`</div></div>` +
				`</div>` +
				`<div class="row g-3 kt-budget-master-detail">` +
				`<div class="kt-budget-col-list">` +
				`<div class="kt-budget-section kt-surface">` +
				`<h3 class="kt-budget-section__title">${escapeHtml(__("Budget Lines"))}</h3>` +
				(() => {
					const lf = String(this.linesFilter || "active").toLowerCase();
					return (
						`<div class="d-flex flex-wrap align-items-center gap-2 mb-2 kt-budget-lines-filter" data-testid="budget-lines-filter">` +
						`<span class="text-muted small">${escapeHtml(__("Show"))}</span>` +
						`<div class="btn-group btn-group-sm" role="group">` +
						`<button type="button" class="btn btn-default${lf === "active" ? " active" : ""}" data-lines-filter="active" data-testid="budget-lines-filter-active">${escapeHtml(__("Active"))}</button>` +
						`<button type="button" class="btn btn-default${lf === "inactive" ? " active" : ""}" data-lines-filter="inactive" data-testid="budget-lines-filter-inactive">${escapeHtml(__("Inactive"))}</button>` +
						`<button type="button" class="btn btn-default${lf === "all" ? " active" : ""}" data-lines-filter="all" data-testid="budget-lines-filter-all">${escapeHtml(__("All"))}</button>` +
						`</div></div>`
					);
				})() +
				`${this.readOnly ? "" : `<button type="button" class="btn btn-default btn-sm mb-2" data-testid="budget-line-add-button">${escapeHtml(__("Add Budget Line"))}</button>`}` +
				`<div class="kt-budget-row-list" data-testid="budget-line-list">` +
				`${this.renderBudgetLineList(budgetLines)}` +
				`</div></div></div>` +
				`<div class="kt-budget-col-detail">` +
				`${this.renderEditor(selectedLine)}` +
				`</div></div>`;
			this.$wrapper.html(deskPageLayout(headHtml, bodyHtml));
			this.$wrapper
				.find('[data-testid="budget-builder-page"]')
				.toggleClass("kt-budget-builder-shell--locked", !!this.readOnly);
			this.applyDocumentTitle();
			this.bindHandlers();
		}

		confirmRemoveBudgetLine() {
			const sel = this.getSelectedBudgetLine();
			if (!sel || !sel.can_remove) {
				return;
			}
			const me = this;
			const msg =
				`<p><strong>${__("Remove Budget Line?")}</strong></p><p>${__(
					"This will deactivate the budget line. It will no longer be used for allocations or reservations.",
				)}</p>`;
			frappe.confirm(msg, () => {
				frappe
					.call({
						method: "kentender_budget.api.builder.remove_budget_line",
						args: {
							budget_name: me.budgetName,
							budget_line_id: sel.name,
							lines_filter: me.linesFilter,
						},
					})
					.then((r) => {
						me.payload = r.message || {};
						frappe.show_alert({ message: __("Budget line removed"), indicator: "green" });
						me.render();
					});
			});
		}

		confirmHardDeleteBudgetLine() {
			const sel = this.getSelectedBudgetLine();
			if (!sel || !sel.can_hard_delete) {
				return;
			}
			const me = this;
			frappe.warn(
				__("Delete Budget Line permanently?"),
				`<p>${__("This action cannot be undone.")}</p>`,
				() => {
					frappe
						.call({
							method: "kentender_budget.api.builder.delete_budget_line_permanent",
							args: {
								budget_name: me.budgetName,
								budget_line_id: sel.name,
								lines_filter: me.linesFilter,
							},
						})
						.then((r) => {
							me.payload = r.message || {};
							me.selectedBudgetLineName = null;
							frappe.show_alert({ message: __("Budget line deleted"), indicator: "green" });
							me.render();
						});
				},
				__("Delete"),
			);
		}

		bindHandlers() {
			const me = this;
			function bindBack(el) {
				$(el).on("click", function (e) {
					if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
						return;
					}
					e.preventDefault();
					frappe.set_route("Workspaces", "Budget Management");
				});
			}
			bindBack(this.$wrapper.find("[data-testid='budget-builder-back-to-landing']"));
			bindBack(this.$wrapper.find("[data-testid='budget-builder-back-button']"));
			this.$wrapper.find(".kt-budget-row[data-budget-line]").on("click", function () {
				me.selectedBudgetLineName = $(this).attr("data-budget-line") || null;
				me.render();
			});
			this.$wrapper.find("[data-testid='budget-line-add-button']").on("click", function () {
				me.showAddBudgetLineModal();
			});
			this.$wrapper.find("[data-testid='budget-allocation-save-button']").on("click", function () {
				me.saveSelectedAllocation();
			});
			this.$wrapper.find("[data-lines-filter]").on("click", function () {
				const v = String($(this).attr("data-lines-filter") || "active").toLowerCase();
				if (!["active", "inactive", "all"].includes(v) || v === me.linesFilter) {
					return;
				}
				me.linesFilter = v;
				me.load();
			});
			this.$wrapper.find("[data-testid='budget-line-remove-button']").on("click", function () {
				me.confirmRemoveBudgetLine();
			});
			this.$wrapper.find("[data-testid='budget-line-hard-delete-button']").on("click", function () {
				me.confirmHardDeleteBudgetLine();
			});
		}

		saveSelectedAllocation() {
			if (this.readOnly) {
				frappe.msgprint(__("You have read-only access to this budget."));
				return;
			}
			const selectedLine = this.getSelectedBudgetLine();
			if (!selectedLine) {
				return;
			}
			const amountRaw = this.$wrapper.find("[data-testid='budget-allocation-amount-input']").val();
			const budgetLineName = (this.$wrapper.find("[data-testid='budget-line-name-input']").val() || "").trim();
			const fundingSource = (this.$wrapper.find("[data-testid='budget-funding-source-input']").val() || "").trim();
			const notes = this.$wrapper.find("[data-testid='budget-allocation-notes-input']").val() || "";
			const amount = Number(amountRaw);
			if (!budgetLineName) {
				frappe.msgprint(__("Budget Line Name is required."));
				return;
			}
			if (amountRaw === "" || Number.isNaN(amount) || amount < 0) {
				frappe.msgprint(__("Enter a valid allocation amount zero or greater."));
				return;
			}
			frappe
				.call({
					method: "kentender_budget.api.builder.upsert_budget_line",
					args: {
						budget_name: this.budgetName,
						budget_line_id: selectedLine.name,
						budget_line_name: budgetLineName,
						amount_allocated: amount,
						funding_source: fundingSource,
						program: selectedLine.program,
						sub_program: selectedLine.sub_program,
						output_indicator: selectedLine.output_indicator,
						performance_target: selectedLine.performance_target,
						notes,
						lines_filter: this.linesFilter,
					},
				})
				.then((r) => {
					this.payload = r.message || this.payload || {};
					frappe.show_alert({ message: __("Budget Line saved"), indicator: "green" });
					this.render();
				});
		}
	}

	function bootBudgetBuilderPage() {
		const el = frappe.pages["budget-builder"];
		if (!el) {
			return false;
		}
		const $w = $(el);
		if ($w.data("kt_budget_builder")) {
			return true;
		}
		const bb = new BudgetBuilderPage($w);
		$w.data("kt_budget_builder", bb);
		bb.init();
		$w.off("show.kt_budget_builder").on("show.kt_budget_builder", function () {
			const state = $w.data("kt_budget_builder");
			if (state && typeof state.applyDocumentTitle === "function") {
				state.applyDocumentTitle();
			}
			if (state && state.budgetName) {
				state.load();
			}
		});
		return true;
	}

	function scheduleBoot() {
		const r = frappe.get_route() || [];
		if (r[0] !== "budget-builder") {
			return;
		}
		if (bootBudgetBuilderPage()) {
			return;
		}
		let tries = 0;
		const maxTries = 60;
		const timer = setInterval(function () {
			tries += 1;
			const rr = frappe.get_route() || [];
			if (rr[0] !== "budget-builder") {
				clearInterval(timer);
				return;
			}
			if (bootBudgetBuilderPage() || tries >= maxTries) {
				clearInterval(timer);
			}
		}, 50);
	}

	$(document).on("page-change", scheduleBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleBoot);
	}
	scheduleBoot();
})();
