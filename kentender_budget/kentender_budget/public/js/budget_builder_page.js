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
			this.selectedProgramName = null;
			this.readOnly = false;
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
					args: { budget_name: me.budgetName },
				})
				.then((r) => {
					me.payload = r.message || {};
					const programs = me.payload.programs || [];
					if (me.selectedProgramName && !programs.some((p) => p.name === me.selectedProgramName)) {
						me.selectedProgramName = null;
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

		getSelectedProgram() {
			const programs = (this.payload && this.payload.programs) || [];
			if (!this.selectedProgramName) {
				return null;
			}
			return programs.find((p) => p.name === this.selectedProgramName) || null;
		}

		renderProgramList(programs) {
			if (!programs || !programs.length) {
				return `<div class="text-muted small">${__("No programs found for this strategic plan.")}</div>`;
			}
			return programs
				.map((p) => {
					const label = p.program_title || p.name;
					const idPart = testIdPart(label);
					const active = p.name === this.selectedProgramName ? " is-active" : "";
					const amt = p.is_allocated
						? escapeHtml(formatAmount(p.allocated_amount, 2))
						: escapeHtml(__("Not allocated"));
					return `<button type="button" class="kt-budget-row${active}" data-program="${escapeHtml(
						p.name
					)}" data-testid="budget-program-row-${escapeHtml(idPart)}">
						<span class="kt-budget-row__main">
							<span class="kt-budget-row__title">${escapeHtml(label)}</span>
						</span>
						<span class="text-muted small" data-testid="budget-program-row-amount-${escapeHtml(idPart)}">${amt}</span>
					</button>`;
				})
				.join("");
		}

		renderEditor(selectedProgram) {
			if (!selectedProgram) {
				return `<div class="kt-budget-section kt-surface" data-testid="budget-allocation-editor">
					<h3 class="kt-budget-section__title" data-testid="budget-allocation-program-title">${escapeHtml(
						__("Allocation Editor")
					)}</h3>
					<div class="text-muted" data-testid="budget-builder-empty-selection">
						${escapeHtml(__("Select a program from the list to view or edit allocation details."))}
					</div>
				</div>`;
			}
			const disabledAttr = this.readOnly ? ' disabled aria-disabled="true"' : "";
			return `<div class="kt-budget-section kt-surface" data-testid="budget-allocation-editor">
				<h3 class="kt-budget-section__title" data-testid="budget-allocation-program-title">${escapeHtml(
					selectedProgram.program_title || selectedProgram.name
				)}</h3>
				<div class="form-group mb-2">
					<label class="small text-muted">${escapeHtml(__("Program"))}</label>
					<input type="text" class="form-control" value="${escapeHtml(
						selectedProgram.program_title || selectedProgram.name
					)}" readonly />
				</div>
				<div class="form-group mb-2">
					<label class="small text-muted">${escapeHtml(__("Allocation Amount"))}</label>
					<input type="number" step="any" min="0" class="form-control" data-testid="budget-allocation-amount-input"${disabledAttr} value="${escapeHtml(
						selectedProgram.is_allocated ? String(selectedProgram.allocated_amount || "") : ""
					)}" />
				</div>
				<div class="form-group mb-3">
					<label class="small text-muted">${escapeHtml(__("Notes"))}</label>
					<textarea rows="3" class="form-control" data-testid="budget-allocation-notes-input"${disabledAttr}>${escapeHtml(
						selectedProgram.notes || ""
					)}</textarea>
				</div>
				${
					this.readOnly
						? ""
						: `<button type="button" class="btn btn-primary btn-sm" data-testid="budget-allocation-save-button">${escapeHtml(
								__("Save Allocation")
							)}</button>`
				}
			</div>`;
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
			const programs = (this.payload && this.payload.programs) || [];
			const selectedProgram = this.getSelectedProgram();
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
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Allocated"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-allocated">${escapeHtml(formatAmount(totals.allocated_sum, 2))}</div>` +
				`</div></div>` +
				`<div class="col-12 col-md-4">` +
				`<div class="kt-budget-kpi-card kt-surface">` +
				`<div class="kt-budget-kpi-label">${escapeHtml(__("Remaining"))}</div>` +
				`<div class="kt-budget-kpi-value" data-testid="budget-builder-remaining">${escapeHtml(formatAmount(totals.remaining_amount, 2))}</div>` +
				`</div></div>` +
				`</div>` +
				`<div class="row g-3 kt-budget-master-detail">` +
				`<div class="kt-budget-col-list">` +
				`<div class="kt-budget-section kt-surface">` +
				`<h3 class="kt-budget-section__title">${escapeHtml(__("Programs"))}</h3>` +
				`<div class="kt-budget-row-list" data-testid="budget-program-list">` +
				`${this.renderProgramList(programs)}` +
				`</div></div></div>` +
				`<div class="kt-budget-col-detail">` +
				`${this.renderEditor(selectedProgram)}` +
				`</div></div>`;
			this.$wrapper.html(deskPageLayout(headHtml, bodyHtml));
			this.$wrapper
				.find('[data-testid="budget-builder-page"]')
				.toggleClass("kt-budget-builder-shell--locked", !!this.readOnly);
			this.applyDocumentTitle();
			this.bindHandlers();
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
			this.$wrapper.find(".kt-budget-row[data-program]").on("click", function () {
				me.selectedProgramName = $(this).attr("data-program") || null;
				me.render();
			});
			this.$wrapper.find("[data-testid='budget-allocation-save-button']").on("click", function () {
				me.saveSelectedAllocation();
			});
		}

		saveSelectedAllocation() {
			if (this.readOnly) {
				frappe.msgprint(__("You have read-only access to this budget."));
				return;
			}
			const selectedProgram = this.getSelectedProgram();
			if (!selectedProgram) {
				return;
			}
			const amountRaw = this.$wrapper.find("[data-testid='budget-allocation-amount-input']").val();
			const notes = this.$wrapper.find("[data-testid='budget-allocation-notes-input']").val() || "";
			const amount = Number(amountRaw);
			if (amountRaw === "" || Number.isNaN(amount) || amount <= 0) {
				frappe.msgprint(__("Enter a valid allocation amount greater than zero."));
				return;
			}
			frappe
				.call({
					method: "kentender_budget.api.builder.upsert_budget_allocation",
					args: {
						budget_name: this.budgetName,
						program_name: selectedProgram.name,
						amount,
						notes,
					},
				})
				.then((r) => {
					this.payload = r.message || this.payload || {};
					frappe.show_alert({ message: __("Allocation saved"), indicator: "green" });
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
