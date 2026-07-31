// Strategy Builder — two-pane hierarchy editor for one Strategic Plan.
frappe.provide("kentender_strategy.strategy_builder");

(function () {
	/** Preset units for Numeric measurement (stored as target_unit string). */
	const NUMERIC_UNIT_PRESETS = ["Facilities", "Staff", "People", "Sites", "Index", "Unit"];
	const CURRENCY_UNITS = ["KES", "USD", "EUR", "GBP"];
	const UNIT_OTHER_VALUE = "__other__";
	function planFromRoute() {
		const r = frappe.get_route() || [];
		return r.length > 1 ? r[1] : null;
	}

	function nestNodes(flat) {
		const byParent = {};
		flat.forEach((n) => {
			const p = n.parent || "";
			if (!byParent[p]) {
				byParent[p] = [];
			}
			byParent[p].push(n);
		});
		function walk(parentId) {
			return (byParent[parentId] || []).map((n) => ({
				...n,
				children: walk(n.name),
			}));
		}
		return walk("");
	}

	function typeIconClass(nodeType) {
		if (nodeType === "Program") {
			return "kt-sb-type--program";
		}
		if (nodeType === "Objective") {
			return "kt-sb-type--objective";
		}
		return "kt-sb-type--target";
	}

	function typeIconLetter(nodeType) {
		if (nodeType === "Program") {
			return "P";
		}
		if (nodeType === "Objective") {
			return "O";
		}
		return "T";
	}

	function readinessMarkup(counts) {
		const p = counts.programs || 0;
		const o = counts.objectives || 0;
		const t = counts.targets || 0;

		let statusClass = "kt-swb-readiness--ok";
		let statusIcon = "check_circle";
		let statusLabel = __("Ready");
		let statusColor = "#2e7d32";

		if (p === 0 || o === 0) {
			statusClass = "kt-swb-readiness--bad";
			statusIcon = "cancel";
			statusLabel = __("Incomplete — add programs and indicators");
			statusColor = "#ba1a1a";
		} else if (t === 0) {
			statusClass = "kt-swb-readiness--warn";
			statusIcon = "warning";
			statusLabel = __("Missing performance targets");
			statusColor = "#c77700";
		}

		const esc = (s) => {
			const d = document.createElement("div");
			d.textContent = String(s == null ? "" : s);
			return d.innerHTML;
		};

		return `<div class="kt-swb-readiness ${statusClass}" data-testid="strategy-readiness">
			<span class="material-symbols-outlined" style="font-size:16px;color:${statusColor};flex-shrink:0">${statusIcon}</span>
			<span class="kt-swb-readiness-label">${esc(__("Plan Readiness"))}:</span>
			<span class="kt-swb-readiness-status" style="color:${statusColor}">${esc(statusLabel)}</span>
			<span class="kt-swb-readiness-counts">${esc(p)} ${esc(__("Programs"))} · ${esc(o)} ${esc(__("Indicators"))} · ${esc(t)} ${esc(__("Targets"))}</span>
		</div>`;
	}

	class StrategyBuilder {
		constructor($wrapper) {
			this.$wrapper = $wrapper;
			this.planName = null;
			this.flatNodes = [];
			this.nodeByName = {};
			this.selectedName = null;
			this.creatingMode = null;
			/** @type {Set<string>} Node names whose child rows are visible */
			this.expanded = new Set();
			this._didInitExpanded = false;
			/** @type {string|null} After create, focus this node once tree reloads */
			this._focusAfterLoad = null;
			this.lastCounts = { programs: 0, objectives: 0, targets: 0 };
			/** Plan years from tree API (for End of Plan hint). */
			this.planMeta = { start_year: null, end_year: null };
			/** Planning Authority v1: read-only builder (no create/write on hierarchy DocTypes). */
			this.readOnly =
				typeof frappe !== "undefined" &&
				frappe.model &&
				!frappe.model.can_write("Strategic Plan");
		}

	init() {
		this.planName = planFromRoute();
		if (!this.planName) {
			this.$wrapper.html(
				`<div class="alert alert-warning">${__("Open this page from a Strategic Plan (missing plan in the URL).")}</div>`,
			);
			return;
		}

		/* Set a plain background immediately so the page is never blank-white while
		   waiting for the first 'show' event (Frappe fires it after its own lifecycle). */
		this.$wrapper.css({ background: "#f7f9fb", minHeight: "100vh" });

		const me = this;
		/* Re-render on plan change via SPA navigation.
		   (The 'show' event may not fire again when only the route param changes.) */
		$(document).off("page-change.kt_sb_plan").on("page-change.kt_sb_plan", () => {
			const r = frappe.get_route() || [];
			if (r[0] !== "strategy-builder") return;
			const next = r[1] || null;
		if (next && next !== me.planName) {				me.planName = next;
				me.renderShell();
			}
		});
	}

		mountModuleShellHeader(planTitle) {
			if (
				typeof kentender_core === "undefined" ||
				!kentender_core.kt_shell
			) {
				return;
			}
			const title = planTitle || this.planName || "";
			kentender_core.kt_shell.mountHeader(this.$wrapper.find(".kt-sb-module-shell-host"), {
				moduleId: "strategy",
				recordTitle: title,
				taskLabel:
					kentender_core.kt_nav && typeof kentender_core.kt_nav.taskLabel === "function"
						? kentender_core.kt_nav.taskLabel("strategy", "builder")
						: __("Manage Structure"),
			});
		}

	renderShell() {
		const wbHtml = typeof window._ktStaticWorkbenchHtml === "function"
			? window._ktStaticWorkbenchHtml()
			: `<p class="text-muted p-4">${__("Workbench loading\u2026")}</p>`;

		this.$wrapper.html(
			`<div class="kt-swb-shell" data-testid="strategy-builder-page">${wbHtml}</div>`,
		);

		/* Wire static interactions immediately, then hydrate from API */
		this._wireStaticActions();
		this.loadPlanMeta();
		this.loadTree();
		this.loadPlanActivity();
	}

	/* ── Header wiring ─────────────────────────────────────────────── */

	loadPlanMeta() {
		const me = this;
		if (!me.planName) return;
		frappe.call({
			method: "kentender_strategy.api.strategy_builder.get_plan_meta",
			args: { plan_name: me.planName },
			callback(r) {
				if (r && r.message) {
					me.planMeta = r.message;
					me.applyPlanMeta(r.message);
				}
			},
		});
	}

	applyPlanMeta(meta) {
		const $w = this.$wrapper;

		/* Breadcrumb */
		$w.find("[data-swb='crumb-entity']").text(
			meta.procuring_entity_name || meta.procuring_entity || __("Strategic Plans"),
		);
		$w.find("[data-swb='crumb-plan']").text(meta.plan_title || meta.plan_name || "");

		/* Title + subtitle */
		$w.find("[data-swb='page-title']").text(meta.plan_title || meta.plan_name || "");
		$w.find("[data-swb='page-sub']").text(meta.description || "");

		/* Status chip */
		const statusColors = {
			Active: "green",
			Approved: "green",
			Submitted: "blue",
			Draft: "blue",
			Archived: "amber",
		};
		const chipColor = statusColors[meta.status] || "blue";
		$w.find("[data-swb='status-chip']")
			.attr("class", `kt-swb-pill kt-swb-pill--${chipColor}`)
			.text(meta.status || "Draft");

		/* KPI 1 – Overall Completion (success_rate) */
		const sr = Number(meta.success_rate || 0).toFixed(1);
		const dc = Number(meta.data_coverage || 0).toFixed(0);
		$w.find("[data-swb='kpi-completion-val']").text(`${sr}%`);
		$w.find("[data-swb='kpi-completion-bar']").css("width", `${Math.min(sr, 100)}%`);
		$w.find("[data-swb='kpi-completion-sub'] span:last-child").text(
			`Coverage: ${dc}%`,
		);

		/* KPI 2 – Programs */
		const prog = meta.programs || 0;
		const obj = meta.objectives || 0;
		const tgt = meta.targets || 0;
		$w.find("[data-swb='kpi-programs-val']").text(prog);
		$w.find("[data-swb='kpi-programs-sub'] span:last-child").text(
			`${obj} Indicators · ${tgt} Targets`,
		);

		/* KPI 3 – Indicators / Targets */
		$w.find("[data-swb='kpi-indicators-val']").text(obj);
		$w.find("[data-swb='kpi-indicators-sub'] span:last-child").text(
			`${tgt} Performance Target${tgt !== 1 ? "s" : ""}`,
		);

		/* Readiness bar */
		const $rb = $w.find("[data-swb='readiness-bar']");
		if ($rb.length) {
			$rb.html(readinessMarkup({ programs: prog, objectives: obj, targets: tgt }));
		}

		/* KPI 4 – Next Milestone */
		const ms = meta.next_milestone || "";
		if (ms) {
			const label = frappe.datetime && frappe.datetime.str_to_user
				? frappe.datetime.str_to_user(ms)
				: ms;
			$w.find("[data-swb='kpi-milestone-date']").text(label);
			$w.find("[data-swb='kpi-milestone-note']").text("");
		} else {
			$w.find("[data-swb='kpi-milestone-date']").text("—");
			$w.find("[data-swb='kpi-milestone-note']").text(__("No upcoming milestones"));
		}

		/* Store description for _showPlanModal pre-fill */
		this._planDescription = meta.description || "";

		/* Locked-status gating — Active and Archived plans are read-only in the hierarchy */
		const LOCKED_STATUSES = ["Active", "Archived"];
		const isLocked = LOCKED_STATUSES.includes(meta.status);
		if (isLocked !== this._statusLocked) {
			this._statusLocked = isLocked;
			if (isLocked) this.readOnly = true;
			this._applyLockState(isLocked, meta.status);
		}

		/* Workflow action buttons (role-gated) */
		this._renderWorkflowActions(meta.status);
	}

	/**
	 * Show / hide the lock banner and disable / re-enable the Edit Plan button
	 * based on plan status. Called whenever applyPlanMeta detects a status change.
	 */
	_applyLockState(isLocked, status) {
		const $w = this.$wrapper;

		/* Remove any existing banner */
		$w.find("[data-swb='lock-banner']").remove();

		if (isLocked) {
			const msg = status === "Archived"
				? __("This plan is archived and cannot be modified.")
				: __("This plan is active. Hierarchy changes are locked. Contact a Strategy Manager to revert to Draft.");

			const banner = `<div data-swb="lock-banner" class="kt-swb-lock-banner"
				data-testid="swb-lock-banner">
				<span class="material-symbols-outlined" style="font-size:16px;flex-shrink:0">lock</span>
				<span>${msg}</span>
			</div>`;

			/* Insert before tree toolbar */
			const $tree = $w.find("[data-testid='swb-tree-body']").closest(".kt-swb-tree-panel, [data-testid='strategy-builder-page']");
			const $toolbar = $w.find("[data-testid='swb-tree-search']").closest("[class*='toolbar'], .kt-swb-tree-toolbar, .kt-swb-toolbar");
			if ($toolbar.length) {
				$toolbar.before(banner);
			} else {
				/* Fallback: prepend to the tree panel */
				($tree.length ? $tree : $w.find("[data-testid='strategy-builder-page']")).prepend(banner);
			}

			/* Disable Edit Plan button — swap icon + tooltip */
			$w.find("[data-swb='edit-plan-btn']")
				.prop("disabled", true)
				.attr("title", __("Plan is locked — revert to Draft to edit"))
				.addClass("kt-swb-btn--locked");

			/* Disable the static Add Program toolbar button */
			$w.find("[data-testid='swb-add-program-btn']")
				.prop("disabled", true)
				.addClass("kt-swb-btn--locked");
		} else {
			/* Re-enable if unlocked (e.g. status refreshed to Draft) */
			$w.find("[data-swb='edit-plan-btn']")
				.prop("disabled", false)
				.removeAttr("title")
				.removeClass("kt-swb-btn--locked");
			$w.find("[data-testid='swb-add-program-btn']")
				.prop("disabled", false)
				.removeClass("kt-swb-btn--locked");
		}

		/* Re-render tree so add/edit/more buttons pick up the updated readOnly flag */
		if (this._treeLoaded) this.renderTree();
	}

	// ── Workflow actions ────────────────────────────────────────────────────────

	/**
	 * Render contextual workflow action buttons in [data-swb="workflow-actions"].
	 *
	 * Transition rules (mirrors kentender_strategy/api/strategy_workflow.py):
	 *   Draft     → Submit (Strategy Manager)
	 *   Submitted → Approve | Return for Correction (Planning Authority)
	 *   Approved  → Activate | Archive (Planning Authority or Strategy Manager)
	 *   Active    → Archive (Planning Authority or Strategy Manager)
	 *   Archived  → (no actions)
	 */
	_renderWorkflowActions(status) {
		const me = this;
		const $slot = me.$wrapper.find("[data-swb='workflow-actions']");
		if (!$slot.length) return;

		/* Role helpers — System Manager / Administrator can do everything */
		const isSM  = frappe.user.has_role("System Manager") || frappe.session.user === "Administrator";
		const isMgr = isSM || frappe.user.has_role("Strategy Manager");
		const isPA  = isSM || frappe.user.has_role("Planning Authority");

		/* Build button descriptors for this status */
		const actions = [];

		if (status === "Draft" && isMgr) {
			actions.push({
				label: __("Submit for Review"),
				css: "kt-swb-btn-primary kt-swb-wf-btn--submit",
				testid: "swb-wf-submit",
				confirm: false,
				api: "kentender_strategy.api.strategy_workflow.submit_plan",
			});
		}

		if (status === "Submitted" && isPA) {
			actions.push({
				label: __("Approve"),
				css: "kt-swb-btn-primary kt-swb-wf-btn--approve",
				testid: "swb-wf-approve",
				confirm: false,
				api: "kentender_strategy.api.strategy_workflow.approve_plan",
			});
			actions.push({
				label: __("Return for Correction"),
				css: "kt-swb-btn-outline kt-swb-wf-btn--return",
				testid: "swb-wf-return",
				confirm: true,
				confirmMsg: __("Return this plan to the Strategy Manager for corrections?"),
				api: "kentender_strategy.api.strategy_workflow.return_for_correction",
			});
		}

		if (status === "Approved" && (isMgr || isPA)) {
			actions.push({
				label: __("Activate"),
				css: "kt-swb-btn-primary kt-swb-wf-btn--activate",
				testid: "swb-wf-activate",
				confirm: true,
				confirmMsg: __("Activate this plan? Once active, the hierarchy will be locked."),
				api: "kentender_strategy.api.strategy_workflow.activate_plan",
			});
		}

		if ((status === "Approved" || status === "Active") && (isMgr || isPA)) {
			actions.push({
				label: __("Archive"),
				css: "kt-swb-btn-outline kt-swb-wf-btn--archive",
				testid: "swb-wf-archive",
				confirm: true,
				confirmMsg: __("Archive this plan? It will become read-only."),
				api: "kentender_strategy.api.strategy_workflow.archive_plan",
			});
		}

		/* Render */
		if (!actions.length) {
			$slot.empty();
			return;
		}

		const html = actions.map((a) =>
			`<button type="button"
				class="${a.css}"
				data-testid="${a.testid}"
				data-api="${a.api}"
				data-confirm="${a.confirm ? "1" : ""}"
				data-confirm-msg="${frappe.utils.escape_html(a.confirmMsg || "")}">
				${frappe.utils.escape_html(a.label)}
			</button>`,
		).join("");

		$slot.html(html);

		/* Wire clicks */
		$slot.find("button[data-api]").off("click.wf").on("click.wf", function () {
			const $btn = $(this);
			const api  = $btn.data("api");
			const needConfirm = $btn.data("confirm") === "1" || $btn.data("confirm") === 1;
			const msg  = $btn.data("confirm-msg") || __("Are you sure?");

			function doTransition() {
				$btn.prop("disabled", true);
				frappe.call({
					method: api,
					args: { plan_name: me.planName },
					callback(r) {
						if (r && r.message) {
							const newStatus = r.message.status;
							frappe.show_alert({
								message: __("Plan status updated to: {0}", [newStatus]),
								indicator: "green",
							});
							/* Refresh header meta + tree lock state */
							me.loadPlanMeta();
							me._realLoadTree();
							me.loadPlanActivity();
						}
					},
					error() {
						$btn.prop("disabled", false);
					},
				});
			}

			if (needConfirm) {
				frappe.confirm(msg, doTransition);
			} else {
				doTransition();
			}
		});
	}

	// ── Activity feed ─────────────────────────────────────────────────────────

	loadPlanActivity() {
		const me = this;
		if (!me.planName) return;
		const $list = me.$wrapper.find("[data-testid='swb-activity-list']");
		if (!$list.length) return;

		$list.html(`<div class="kt-swb-feed-loading" data-testid="swb-activity-loading">
			<span class="material-symbols-outlined" style="font-size:18px;opacity:.4;animation:kt-spin 1s linear infinite">progress_activity</span>
			<span>${__("Loading activity\u2026")}</span>
		</div>`);

		frappe.call({
			method: "kentender_strategy.api.strategy_builder.get_plan_activity",
			args: { plan_name: me.planName, limit: 15 },
			callback(r) {
				const events = (r && r.message) || [];
				me.renderActivityFeed($list, events);
			},
		});
	}

	_refreshReadiness() {
		const nodes = this.flatNodes || [];
		const prog = nodes.filter((n) => n.node_type === "Program").length;
		const obj  = nodes.filter((n) => n.node_type === "Indicator").length;
		const tgt  = nodes.filter((n) => n.node_type === "Target").length;
		const $rb  = this.$wrapper.find("[data-swb='readiness-bar']");
		if ($rb.length) {
			$rb.html(readinessMarkup({ programs: prog, objectives: obj, targets: tgt }));
		}
	}

	renderActivityFeed($list, events) {
		if (!events || !events.length) {
			$list.html(`<div class="kt-swb-feed-empty" data-testid="swb-activity-empty">${__("No activity recorded yet.")}</div>`);
			return;
		}

		function esc(s) {
			const d = document.createElement("div");
			d.textContent = s == null ? "" : String(s);
			return d.innerHTML;
		}

		function relTime(isoStr) {
			if (!isoStr) return "";
			const d = new Date(isoStr.replace(" ", "T"));
			if (isNaN(d)) return isoStr;
			const diff = Date.now() - d.getTime();
			const mins = Math.floor(diff / 60000);
			if (mins < 2) return __("Just now");
			if (mins < 60) return `${mins} ${__("min ago")}`;
			const hrs = Math.floor(mins / 60);
			if (hrs < 24) return `${hrs} ${hrs === 1 ? __("hr ago") : __("hrs ago")}`;
			const days = Math.floor(hrs / 24);
			if (days === 1) return __("Yesterday");
			if (days < 7) return `${days} ${__("days ago")}`;
			return frappe.datetime && frappe.datetime.str_to_user
				? frappe.datetime.str_to_user(isoStr.split(" ")[0])
				: isoStr.split(" ")[0];
		}

		const iconMap = {
			Plan:       { icon: "flag",          cls: "" },
			Program:    { icon: "account_tree",   cls: "" },
			"Sub-program": { icon: "account_tree", cls: "" },
			Indicator:  { icon: "analytics",      cls: "" },
			Target:     { icon: "track_changes",  cls: "" },
		};
		const errDot = "is-err";

		let html = "";
		events.forEach((ev, i) => {
			const isLast = i === events.length - 1;
			const m = iconMap[ev.node_type] || { icon: "edit", cls: "" };
			const isErr = ev.dot_class === "error" || ev.dot_class === "danger";
			const iconCls = isErr ? errDot : m.cls;
			const iconName = isErr ? "report" : m.icon;
			const user = esc(ev.user || __("System"));
			const action = esc(ev.action || "");
			const nodeTitle = esc(ev.node_title || "");
			const time = esc(relTime(ev.time));

			html += `<div class="kt-swb-feed-item" data-testid="swb-activity-item">
				<div class="kt-swb-feed-icon-wrap">
					<div class="kt-swb-feed-icon ${iconCls}">
						<span class="material-symbols-outlined">${iconName}</span>
					</div>
					${!isLast ? `<div class="kt-swb-feed-line"></div>` : ""}
				</div>
				<div class="kt-swb-feed-copy">
					<p><strong>${user}</strong> — ${action}${nodeTitle ? `: <span class="ref">${nodeTitle}</span>` : ""}</p>
					<small>${time}</small>
				</div>
			</div>`;
		});
		$list.html(html);
	}

	_wireStaticActions() {
		const $w = this.$wrapper;
		const me = this;

		/* Back to Strategy Hub */
		$w.find("[data-swb='back-link']").off("click.kb_back").on("click.kb_back", function (e) {
			e.preventDefault();
			frappe.set_route("strategy-management");
		});

		/* Edit Plan — inline modal */
		$w.find("[data-swb='edit-plan-btn']").off("click.kb_edit").on("click.kb_edit", function () {
			if (me.planName) me._showPlanModal();
		});

		/* Activity feed — refresh button */
		$w.find("[data-testid='swb-activity-refresh']").off("click.kb_act").on("click.kb_act", function () {
			me.loadPlanActivity();
		});

		/* Tree toolbar — Add Program */
		$w.find("[data-testid='swb-add-program-btn']").off("click.kb_ap").on("click.kb_ap", function () {
			me.promptCreate("Program", null);
		});

		/* Tree toolbar — Search */
		$w.find("[data-testid='swb-tree-search']").off("input.kb_search").on("input.kb_search", function () {
			me.renderTree();
		});

		/* Tree toolbar — Expand / Collapse all toggle */
		$w.find("[data-testid='swb-expand-all-btn']").off("click.kb_exp").on("click.kb_exp", function () {
			const $btn = $(this);
			const allExpanded = $btn.data("expanded") === true;
			if (allExpanded) {
				me.expanded.clear();
				$btn.data("expanded", false).attr("title", "Expand All");
				$btn.find(".material-symbols-outlined").text("unfold_more");
			} else {
				(me.flatNodes || []).forEach((n) => {
					if (n.node_type !== "Target") me.expanded.add(n.name);
				});
				$btn.data("expanded", true).attr("title", "Collapse All");
				$btn.find(".material-symbols-outlined").text("unfold_less");
			}
			me.renderTree();
		});
	}

	/* Stub — tree wiring is a follow-on task */
	loadTree() {
		this._realLoadTree();
	}

	// ── Tree: load ───────────────────────────────────────────────────────────

	_realLoadTree() {
		const me = this;
		if (!me.planName) return;
		frappe.call({
			method: "kentender_strategy.api.strategy_builder.get_strategy_tree",
			args: { plan_name: me.planName },
			callback(r) {
				if (!r || !r.message) return;
				/* build_tree returns { plan, nodes: [...], counts } */
				const nodes = Array.isArray(r.message) ? r.message
					: (r.message.nodes || []);
				me.flatNodes = nodes;
				me.nodeByName = {};
				nodes.forEach((n) => { me.nodeByName[n.name] = n; });
				// Auto-expand Programs on first load
				if (!me._didInitExpanded) {
					nodes
						.filter((n) => n.node_type === "Program")
						.forEach((n) => me.expanded.add(n.name));
					me._didInitExpanded = true;
				}
			me.renderTree();
			me._treeLoaded = true;
			me._refreshReadiness();
			},
		});
	}

	// ── Tree: render ─────────────────────────────────────────────────────────

	renderTree() {
		const $body = this.$wrapper.find("[data-testid='swb-tree-body']");
		if (!$body.length) return;
		const nodes = this.flatNodes;
		const search = (
			this.$wrapper.find("[data-testid='swb-tree-search']").val() || ""
		).toLowerCase().trim();

		if (!nodes || !nodes.length) {
			$body.html(
				`<div class="kt-swb-empty-tree">
					<span class="material-symbols-outlined" style="font-size:48px;color:#c6c6cd;display:block;margin-bottom:8px">account_tree</span>
					<p style="font-size:14px">No programs yet. Click <strong>+ Program</strong> to start.</p>
				</div>`,
			);
			return;
		}

		const programs = nodes.filter((n) => n.node_type === "Program");
		let html = "";
		for (const prog of programs) {
			if (
				search &&
				!(prog.title || "").toLowerCase().includes(search) &&
				!nodes.some(
					(n) => n.program === prog.name && (
						(n.title || "").toLowerCase().includes(search) ||
						(n.code || "").toLowerCase().includes(search)
					),
				)
			) continue;
			html += this._progHtml(prog, nodes);
		}

		$body.html(html);
		this._bindTreeEvents();
		this._applyFocusAfterLoad();
	}

	_progHtml(prog, nodes) {
		const e = frappe.utils.escape_html;
		const sps = nodes.filter((n) => n.node_type === "SubProgram" && n.parent === prog.name);
		const allInds = nodes.filter((n) => n.node_type === "Indicator" && n.program === prog.name);
		const allTgts = nodes.filter((n) => n.node_type === "Target" && n.program === prog.name);
		const pct = this._pct("Program", prog.name, nodes);
		const exp = this.expanded.has(prog.name);
		const sel = this.selectedName === prog.name ? " kt-swb-selected" : "";

		let h = `<div class="kt-swb-prog-wrap" data-node-wrap="${e(prog.name)}">
			<div class="kt-swb-prog-row${sel}" data-name="${e(prog.name)}" data-ntype="Program">
				<button class="kt-swb-expand" data-expand="${e(prog.name)}" type="button">
					<span class="material-symbols-outlined">${exp ? "keyboard_arrow_down" : "keyboard_arrow_right"}</span>
				</button>
				<div class="kt-swb-prog-icon"><span class="material-symbols-outlined">business_center</span></div>
				<div class="kt-swb-prog-body">
					<div class="kt-swb-prog-title-row">
						<span class="kt-swb-node-code">${e(prog.code || "")}</span>
						<h4 class="kt-swb-prog-name">${e(prog.title)}</h4>
					</div>
					<div class="kt-swb-prog-meta">
						<div class="kt-swb-pbar-wrap kt-swb-pbar-wrap--prog">
							<div class="kt-swb-pbar-track kt-swb-pbar-track--prog">
								<div class="kt-swb-pbar-fill" style="width:${pct}%"></div>
							</div>
							<span class="kt-swb-pbar-pct">${pct}%</span>
						</div>
						<span class="kt-swb-meta-txt">${sps.length} Sub-prog · ${allInds.length} Ind. · ${allTgts.length} Targets</span>
					</div>
				</div>
				<div class="kt-swb-row-actions">
					<button class="kt-swb-btn-sm" data-act="add" data-ntype="SubProgram" data-parent="${e(prog.name)}" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">add</span> Sub-program
					</button>
					<button class="kt-swb-btn-more" data-act="more" data-name="${e(prog.name)}" data-ntype="Program" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">more_vert</span>
					</button>
				</div>
			</div>`;

		if (exp) {
			h += `<div class="kt-swb-children" data-ch="${e(prog.name)}">
				<div class="kt-swb-tree-v"></div>`;
			for (const sp of sps) h += this._spHtml(sp, nodes);
			if (!this.readOnly) h += this._addRowHtml("SubProgram", prog.name);
			h += `</div>`;
		}
		return h + `</div>`;
	}

	_spHtml(sp, nodes) {
		const e = frappe.utils.escape_html;
		const inds = nodes.filter((n) => n.node_type === "Indicator" && n.parent === sp.name);
		const spTgts = nodes.filter((n) => n.node_type === "Target" && n.sub_program === sp.name);
		const pct = this._pct("SubProgram", sp.name, nodes);
		const exp = this.expanded.has(sp.name);
		const sel = this.selectedName === sp.name ? " kt-swb-selected" : "";

		let h = `<div class="kt-swb-branch" data-node-wrap="${e(sp.name)}">
			<div class="kt-swb-tree-h"></div>
			<div class="kt-swb-obj-row${sel}" data-name="${e(sp.name)}" data-ntype="SubProgram" style="background:#f8fafc">
				<button class="kt-swb-expand" data-expand="${e(sp.name)}" type="button">
					<span class="material-symbols-outlined">${exp ? "keyboard_arrow_down" : "keyboard_arrow_right"}</span>
				</button>
				<div class="kt-swb-obj-body">
					<div class="kt-swb-obj-title-row">
						<span class="kt-swb-node-code" style="color:#57657b">${e(sp.code || "")}</span>
						<h5 class="kt-swb-obj-name" style="font-size:13px">${e(sp.title)}</h5>
					</div>
					<div class="kt-swb-obj-meta">
						<div class="kt-swb-pbar-wrap kt-swb-pbar-wrap--obj">
							<div class="kt-swb-pbar-track kt-swb-pbar-track--obj">
								<div class="kt-swb-pbar-fill" style="width:${pct}%"></div>
							</div>
							<span class="kt-swb-pbar-pct">${pct}%</span>
						</div>
						<span class="kt-swb-meta-txt">${inds.length} Ind. · ${spTgts.length} Targets</span>
					</div>
				</div>
				<div class="kt-swb-row-actions">
					<button class="kt-swb-btn-xs" data-act="add" data-ntype="Indicator" data-parent="${e(sp.name)}" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">add</span> Indicator
					</button>
					<button class="kt-swb-btn-more" data-act="more" data-name="${e(sp.name)}" data-ntype="SubProgram" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">more_vert</span>
					</button>
				</div>
			</div>`;

		if (exp) {
			h += `<div class="kt-swb-children" data-ch="${e(sp.name)}" style="margin-left:32px">
				<div class="kt-swb-tree-v"></div>`;
			for (const ind of inds) h += this._indHtml(ind, nodes);
			if (!this.readOnly) h += this._addRowHtml("Indicator", sp.name);
			h += `</div>`;
		}
		return h + `</div>`;
	}

	_indHtml(ind, nodes) {
		const e = frappe.utils.escape_html;
		const tgts = nodes.filter((n) => n.node_type === "Target" && n.parent === ind.name);
		const pct = this._pct("Indicator", ind.name, nodes);
		const exp = this.expanded.has(ind.name);
		const sel = this.selectedName === ind.name ? " kt-swb-selected" : "";
		const barCls = pct < 50 ? "kt-swb-pbar-fill--amber" : "kt-swb-obj-fill--green";

		let h = `<div class="kt-swb-branch" data-node-wrap="${e(ind.name)}">
			<div class="kt-swb-tree-h"></div>
			<div class="kt-swb-obj-row${sel}" data-name="${e(ind.name)}" data-ntype="Indicator">
				<button class="kt-swb-expand" data-expand="${e(ind.name)}" type="button">
					<span class="material-symbols-outlined">${exp ? "keyboard_arrow_down" : "keyboard_arrow_right"}</span>
				</button>
				<div class="kt-swb-obj-body">
					<div class="kt-swb-obj-title-row">
						<span class="kt-swb-node-code">${e(ind.code || "")}</span>
						<h5 class="kt-swb-obj-name">${e(ind.title)}</h5>
					</div>
					<div class="kt-swb-obj-meta">
						<div class="kt-swb-pbar-wrap kt-swb-pbar-wrap--obj">
							<div class="kt-swb-pbar-track kt-swb-pbar-track--obj">
								<div class="kt-swb-pbar-fill ${barCls}" style="width:${pct}%"></div>
							</div>
							<span class="kt-swb-pbar-pct">${pct}%</span>
						</div>
						<span class="kt-swb-meta-txt">${tgts.length} Target${tgts.length !== 1 ? "s" : ""}</span>
					</div>
				</div>
				<div class="kt-swb-row-actions">
					<button class="kt-swb-btn-xs" data-act="add" data-ntype="Target" data-parent="${e(ind.name)}" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">add</span> Target
					</button>
					<button class="kt-swb-btn-more" data-act="more" data-name="${e(ind.name)}" data-ntype="Indicator" type="button" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">more_vert</span>
					</button>
				</div>
			</div>`;

		if (exp) {
			h += `<div class="kt-swb-targets" data-ch="${e(ind.name)}" style="margin-left:32px">
				<div class="kt-swb-tree-v"></div>`;
			for (const tgt of tgts) h += this._tgtHtml(tgt);
			if (!this.readOnly) h += this._addRowHtml("Target", ind.name);
			h += `</div>`;
		}
		return h + `</div>`;
	}

	_tgtHtml(tgt) {
		const e = frappe.utils.escape_html;
		const pct = this._tgtPct(tgt);
		let due = "";
		if (tgt.target_due_date) {
			due = `Due: ${frappe.datetime && frappe.datetime.str_to_user
				? frappe.datetime.str_to_user(tgt.target_due_date)
				: tgt.target_due_date}`;
		} else if (tgt.target_year) {
			due = `FY ${tgt.target_year}`;
		}
		let display = "";
		if (tgt.measurement_type === "Numeric" || tgt.measurement_type === "Percentage") {
			const unit = tgt.target_unit
				? ` ${tgt.target_unit}`
				: tgt.measurement_type === "Percentage" ? "%" : "";
			const actual = tgt.actual_value_numeric != null ? tgt.actual_value_numeric : "—";
			const target = tgt.target_value_numeric != null ? tgt.target_value_numeric : "—";
			display = `${actual}${unit} / ${target}${unit}`;
		} else if (tgt.measurement_type === "Milestone" || tgt.measurement_type === "Boolean") {
			display = tgt.actual_is_complete ? "Complete ✓" : "Pending";
		}
		const sel = this.selectedName === tgt.name ? " kt-swb-selected" : "";

		return `<div class="kt-swb-tgt-branch" data-node-wrap="${e(tgt.name)}">
			<div class="kt-swb-tree-h"></div>
			<div class="kt-swb-tgt-row${sel}" data-name="${e(tgt.name)}" data-ntype="Target">
				<div class="kt-swb-tgt-body">
					<div class="kt-swb-tgt-head">
						<span class="kt-swb-tgt-code">${e(tgt.code || "")}</span>
						${due ? `<span class="kt-swb-tgt-due">${e(due)}</span>` : ""}
					</div>
					<p class="kt-swb-tgt-title">${e(tgt.title)}</p>
					${display || pct > 0 ? `<div class="kt-swb-tgt-progress">
						<div class="kt-swb-tgt-track"><div class="kt-swb-tgt-fill" style="width:${pct}%"></div></div>
						${display ? `<span class="kt-swb-tgt-count">${e(display)}</span>` : ""}
					</div>` : ""}
				</div>
				<div style="display:flex;gap:4px;flex-shrink:0;align-self:center">
					<button class="kt-swb-btn-edit" data-act="edit" data-name="${e(tgt.name)}" data-ntype="Target" type="button" title="${__("Edit")}" ${this.readOnly ? "disabled" : ""}>
						<span class="material-symbols-outlined">edit_note</span>
					</button>
					${!this.readOnly ? `<button class="kt-swb-btn-more" data-act="more" data-name="${e(tgt.name)}" data-ntype="Target" type="button">
						<span class="material-symbols-outlined">more_vert</span>
					</button>` : ""}
				</div>
			</div>
		</div>`;
	}

	_addRowHtml(nodeType, parentName) {
		const e = frappe.utils.escape_html;
		const label = nodeType === "SubProgram" ? "Sub-program" : nodeType;
		const isTarget = nodeType === "Target";
		const cls = isTarget ? "kt-swb-tgt-branch" : "kt-swb-branch";
		return `<div class="${cls} kt-swb-add-row">
			<div class="${isTarget ? "kt-swb-tree-h" : "kt-swb-tree-h"}"></div>
			<button class="kt-swb-btn-xs" data-act="add" data-ntype="${e(nodeType)}" data-parent="${e(parentName)}"
				type="button" style="${isTarget ? "margin-left:24px;" : ""}margin-top:4px">
				<span class="material-symbols-outlined">add</span> ${e(label)}
			</button>
		</div>`;
	}

	// ── Tree: progress ───────────────────────────────────────────────────────

	_tgtPct(tgt) {
		if (!tgt) return 0;
		if (tgt.measurement_type === "Milestone" || tgt.measurement_type === "Boolean") {
			return tgt.actual_is_complete ? 100 : 0;
		}
		const a = parseFloat(tgt.actual_value_numeric) || 0;
		const t = parseFloat(tgt.target_value_numeric) || 0;
		if (t === 0) return 0;
		return Math.min(100, Math.round((a / t) * 100));
	}

	_pct(nodeType, name, nodes) {
		if (nodeType === "Target") return this._tgtPct(this.nodeByName[name]);
		const childType = nodeType === "Program" ? "SubProgram"
			: nodeType === "SubProgram" ? "Indicator" : "Target";
		const children = nodes.filter((n) => n.node_type === childType && n.parent === name);
		if (!children.length) return 0;
		const sum = children.reduce((s, c) => s + this._pct(childType, c.name, nodes), 0);
		return Math.round(sum / children.length);
	}

	// ── Post-create focus: scroll to and flash newly created node ────────────

	_applyFocusAfterLoad() {
		const name = this._focusAfterLoad;
		if (!name) return;
		this._focusAfterLoad = null;

		const me = this;

		/* Ensure all ancestors are expanded so the row is in the DOM */
		const node = me.nodeByName[name];
		if (node) {
			/* Walk up the parent chain and expand every ancestor */
			let cur = node;
			while (cur && cur.parent_name) {
				me.expanded.add(cur.parent_name);
				cur = me.nodeByName[cur.parent_name];
			}
			/* If any expansion happened, re-render synchronously before scrolling */
			if (cur !== node) {
				const $body = me.$wrapper.find("[data-testid='swb-tree-body']");
				const programs = me.flatNodes.filter((n) => n.node_type === "Program");
				let html = "";
				for (const prog of programs) {
					html += me._progHtml(prog, me.flatNodes);
				}
				$body.html(html);
				me._bindTreeEvents();
			}
		}

		/* Find the rendered row */
		const $row = me.$wrapper.find(`[data-node-wrap="${CSS.escape(name)}"], [data-ntype][data-name="${CSS.escape(name)}"]`).first();
		if (!$row.length) return;

		/* Scroll into view */
		const el = $row[0];
		el.scrollIntoView({ behavior: "smooth", block: "center" });

		/* Select it */
		me.$wrapper.find(".kt-swb-selected").removeClass("kt-swb-selected");
		$row.addClass("kt-swb-selected");
		me.selectedName = name;

		/* Flash highlight */
		$row.addClass("kt-swb-row--flash");
		setTimeout(() => $row.removeClass("kt-swb-row--flash"), 1400);
	}

	// ── Tree: event binding ──────────────────────────────────────────────────

	_bindTreeEvents() {
		const me = this;
		const $w = this.$wrapper;

		$w.find("[data-expand]").off("click.kt_t").on("click.kt_t", function (ev) {
			ev.stopPropagation();
			const n = $(this).data("expand");
			if (me.expanded.has(n)) me.expanded.delete(n);
			else me.expanded.add(n);
			me.renderTree();
		});

		$w.find("[data-ntype]").off("click.kt_t").on("click.kt_t", function (ev) {
			if ($(ev.target).closest("[data-expand],[data-act]").length) return;
			me.selectNode($(this).data("name"), $(this).data("ntype"));
		});

		$w.find("[data-act='add']").off("click.kt_t").on("click.kt_t", function (ev) {
			ev.stopPropagation();
			me.promptCreate($(this).data("ntype"), $(this).data("parent") || null);
		});

		$w.find("[data-act='edit']").off("click.kt_t").on("click.kt_t", function (ev) {
			ev.stopPropagation();
			me.editNode($(this).data("name"), $(this).data("ntype"));
		});

		$w.find("[data-act='more']").off("click.kt_t").on("click.kt_t", function (ev) {
			ev.stopPropagation();
			me._showNodeMenu($(this).data("name"), $(this).data("ntype"), this);
		});
	}

	// ── Tree: selection ──────────────────────────────────────────────────────

	selectNode(name) {
		this.selectedName = name;
		this.creatingMode = null;
		this.$wrapper.find(".kt-swb-prog-row,.kt-swb-obj-row,.kt-swb-tgt-row")
			.removeClass("kt-swb-selected");
		this.$wrapper.find(`[data-name="${CSS.escape(name)}"]`).addClass("kt-swb-selected");
	}

	updateAddButtons() {
		/* Tree uses inline add buttons; no toolbar buttons to gate. */
	}

	// ── Tree: create dialog ──────────────────────────────────────────────────

	promptCreate(nodeType, parentName) {
		const me = this;
		if (me.readOnly) {
			frappe.msgprint(__("You have read-only access to this plan."));
			return;
		}
		const labels = {
			Program: __("Add Program"),
			SubProgram: __("Add Sub-program"),
			Indicator: __("Add Indicator"),
			Target: __("Add Target / KPI"),
		};
		const parentNode = parentName ? me.nodeByName[parentName] : null;
		const parentLabel = parentNode ? parentNode.title : null;

		const onSubmit = (values) => {
			frappe.call({
				method: "kentender_strategy.api.strategy_builder.create_strategy_node",
				args: {
					plan_name: me.planName,
					parent_name: parentName || null,
					node_type: nodeType,
					initial_data: JSON.stringify(values),
				},
				callback(r) {
					if (r && r.message && r.message.name) {
						me._focusAfterLoad = r.message.name;
					}
					me._realLoadTree();
					me.loadPlanActivity();
					frappe.show_alert({
						message: (labels[nodeType] || nodeType) + " " + __("created"),
						indicator: "green",
					});
				},
			});
		};

		const ctxIcons = {
			Program: "account_tree",
			SubProgram: "account_tree",
			Indicator: "account_tree",
			Target: "lock",
		};

		if (nodeType === "Target") {
			me._showTargetModal({
				title: labels.Target,
				contextIcon: ctxIcons.Target,
				contextLabel: parentLabel,
				primaryLabel: __("Add Target"),
				onSubmit,
			});
		} else {
			const fields = [
				{ name: "node_title", label: __("Title"), type: "text", required: true,
					placeholder: `${__("Enter")} ${(nodeType === "SubProgram" ? __("sub-program") : nodeType.toLowerCase())} ${__("title")}` },
			];
			if (nodeType !== "SubProgram") {
				fields.push({ name: "node_description", label: __("Description"), type: "textarea",
					placeholder: __("Optional description") });
			}
			me._showModal({
				title: labels[nodeType],
				contextIcon: ctxIcons[nodeType],
				contextLabel: parentLabel,
				fields,
				primaryLabel: labels[nodeType],
				onSubmit,
			});
		}
	}

	// ── Tree: edit dialog ────────────────────────────────────────────────────

	editNode(name, nodeType) {
		const me = this;
		const n = me.nodeByName[name];
		if (!n) return;

		const parentNode = n.parent ? me.nodeByName[n.parent] : null;
		const parentLabel = parentNode ? parentNode.title : null;

		const onSubmit = (values) => {
			frappe.call({
				method: "kentender_strategy.api.strategy_builder.update_strategy_node",
				args: { node_name: name, data: JSON.stringify(values) },
				callback() {
					me._realLoadTree();
					me.loadPlanActivity();
					frappe.show_alert({ message: __("Saved"), indicator: "green" });
				},
			});
		};

		if (nodeType === "Target") {
			me._showTargetModal({
				title: `${__("Edit Target")}: ${n.title || ""}`,
				contextIcon: "lock",
				contextLabel: parentLabel,
				primaryLabel: __("Save Changes"),
				defaults: n,
				onSubmit,
			});
		} else {
			const fields = [
				{ name: "node_title", label: __("Title"), type: "text", required: true,
					value: n.title || "" },
			];
			if (nodeType !== "SubProgram") {
				fields.push({ name: "node_description", label: __("Description"), type: "textarea",
					value: n.description || "" });
			}
			me._showModal({
				title: `${__("Edit")}: ${n.title || ""}`,
				contextIcon: "account_tree",
				contextLabel: parentLabel,
				fields,
				primaryLabel: __("Save Changes"),
				onSubmit,
			});
		}
	}

	// ── Tree: context menu ───────────────────────────────────────────────────

	_showNodeMenu(name, nodeType, btnEl) {
		const me = this;
		$(".kt-swb-ctx-menu").remove();
		const $menu = $(`<div class="kt-swb-ctx-menu"
			style="position:fixed;background:#fff;border:1px solid #c6c6cd;border-radius:4px;
			       box-shadow:0 4px 16px rgba(0,0,0,.12);z-index:2000;min-width:130px;padding:4px 0">
			<button class="kt-swb-ctx-item" data-act2="edit"
				style="display:flex;align-items:center;gap:6px;width:100%;text-align:left;
				       padding:8px 16px;background:none;border:none;font-size:13px;
				       cursor:pointer;font-family:inherit">
				<span class="material-symbols-outlined" style="font-size:16px">edit</span>${__("Edit")}
			</button>
			<button class="kt-swb-ctx-item" data-act2="delete"
				style="display:flex;align-items:center;gap:6px;width:100%;text-align:left;
				       padding:8px 16px;background:none;border:none;font-size:13px;
				       cursor:pointer;color:#ba1a1a;font-family:inherit">
				<span class="material-symbols-outlined" style="font-size:16px">delete</span>${__("Delete")}
			</button>
		</div>`);

		const rect = btnEl.getBoundingClientRect();
		$menu.css({ top: rect.bottom + 2, left: rect.left });
		$("body").append($menu);

		$menu.find("[data-act2='edit']").on("click", () => {
			$menu.remove();
			me.editNode(name, nodeType);
		});
		$menu.find("[data-act2='delete']").on("click", () => {
			$menu.remove();
			frappe.confirm(
				__("Delete this {0}? All child nodes will also be removed.", [nodeType]),
				() => {
					frappe.call({
						method: "kentender_strategy.api.strategy_builder.delete_strategy_node",
						args: { node_name: name },
					callback() {
						if (me.selectedName === name) me.selectedName = null;
						me._realLoadTree();
						me.loadPlanActivity();
						frappe.show_alert({ message: __("Deleted"), indicator: "green" });
					},
					});
				},
			);
		});

		setTimeout(() => {
			$(document).one("click.kt_ctx", () => $(".kt-swb-ctx-menu").remove());
		}, 0);
	}



	// ── Modal helpers ─────────────────────────────────────────────────────────

	/**
	 * Base modal portal — appended directly to document.body.
	 * @param {object} opts
	 * @param {string}   opts.title
	 * @param {string}   [opts.contextIcon]   material symbol name
	 * @param {string}   [opts.contextLabel]  read-only context row text
	 * @param {Array}    opts.fields          [{name, label, type, required, value, placeholder, options}]
	 * @param {string}   opts.primaryLabel
	 * @param {Function} opts.onSubmit        called with values plain object
	 * @param {string}   [opts.hint]          optional hint callout text
	 * @returns {{ overlay: HTMLElement, close: Function, getValues: Function }}
	 */
	_showModal({ title, contextIcon, contextLabel, fields = [], primaryLabel, onSubmit, hint }) {
		function esc(s) {
			const d = document.createElement("div");
			d.textContent = s == null ? "" : String(s);
			return d.innerHTML;
		}

		const ctxRow = (contextLabel)
			? `<div class="kt-swb-modal-ctx">
				<span class="material-symbols-outlined">${esc(contextIcon || "account_tree")}</span>
				<span>${esc(contextLabel)}</span>
			</div>` : "";

		const hintRow = hint
			? `<div class="kt-swb-modal-hint">
				<span class="material-symbols-outlined">info</span>
				<span>${esc(hint)}</span>
			</div>` : "";

		function buildField(f) {
			const id = `ktm_${f.name}`;
			const req = f.required ? `<span style="color:#ba1a1a">*</span>` : "";
			const val = f.value != null ? esc(f.value) : "";
			if (f.type === "textarea") {
				return `<div class="kt-swb-modal-field" data-field="${f.name}">
					<label class="kt-swb-modal-lbl" for="${id}">${esc(f.label)}${req}</label>
					<textarea id="${id}" name="${f.name}" class="kt-swb-modal-textarea"
						placeholder="${esc(f.placeholder || "")}">${val}</textarea>
				</div>`;
			}
			if (f.type === "select") {
				const opts = (f.options || []).map((o) =>
					`<option value="${esc(o)}"${o === f.value ? " selected" : ""}>${esc(o)}</option>`
				).join("");
				return `<div class="kt-swb-modal-field" data-field="${f.name}">
					<label class="kt-swb-modal-lbl" for="${id}">${esc(f.label)}${req}</label>
					<select id="${id}" name="${f.name}" class="kt-swb-modal-select">${opts}</select>
				</div>`;
			}
			return `<div class="kt-swb-modal-field" data-field="${f.name}">
				<label class="kt-swb-modal-lbl" for="${id}">${esc(f.label)}${req}</label>
				<input id="${id}" name="${f.name}" type="${f.type || "text"}"
					class="kt-swb-modal-input" value="${val}"
					placeholder="${esc(f.placeholder || "")}">
			</div>`;
		}

		const fieldsHtml = fields.map(buildField).join("");

		const html = `
		<div class="kt-swb-modal-overlay" data-testid="kt-modal-overlay">
			<div class="kt-swb-modal-backdrop" data-testid="kt-modal-backdrop"></div>
			<div class="kt-swb-modal-box" data-testid="kt-modal-box" role="dialog" aria-modal="true">
				<div class="kt-swb-modal-hdr">
					<span class="kt-swb-modal-title" data-testid="kt-modal-title">${esc(title)}</span>
					<button class="kt-swb-modal-close" data-testid="kt-modal-close" aria-label="Close">
						<span class="material-symbols-outlined" style="font-size:20px">close</span>
					</button>
				</div>
				<div class="kt-swb-modal-body">
					${ctxRow}
					${fieldsHtml}
					${hintRow}
				</div>
				<div class="kt-swb-modal-ftr">
					<button class="kt-swb-modal-cancel" data-testid="kt-modal-cancel">${esc(__("Cancel"))}</button>
					<button class="kt-swb-modal-submit" data-testid="kt-modal-submit">${esc(primaryLabel)}</button>
				</div>
			</div>
		</div>`;

		const el = document.createElement("div");
		el.innerHTML = html;
		const overlay = el.firstElementChild;
		document.body.appendChild(overlay);

		const focusFirst = () => {
			const first = overlay.querySelector(".kt-swb-modal-input, .kt-swb-modal-textarea, .kt-swb-modal-select");
			if (first) first.focus();
		};
		setTimeout(focusFirst, 50);

		// Focus label on input focus
		overlay.querySelectorAll(".kt-swb-modal-input, .kt-swb-modal-textarea, .kt-swb-modal-select").forEach((inp) => {
			inp.addEventListener("focus", () => {
				const lbl = overlay.querySelector(`label[for="${inp.id}"]`);
				if (lbl) lbl.classList.add("active");
			});
			inp.addEventListener("blur", () => {
				const lbl = overlay.querySelector(`label[for="${inp.id}"]`);
				if (lbl) lbl.classList.remove("active");
			});
		});

		const getValues = () => {
			const vals = {};
			overlay.querySelectorAll("[name]").forEach((el) => {
				vals[el.name] = el.tagName === "SELECT" ? el.value : (el.value || "").trim();
			});
			return vals;
		};

		const close = () => {
			if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
			document.removeEventListener("keydown", onKey);
		};

		const onKey = (e) => { if (e.key === "Escape") close(); };
		document.addEventListener("keydown", onKey);

		overlay.querySelector("[data-testid='kt-modal-backdrop']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-modal-close']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-modal-cancel']").addEventListener("click", close);

		overlay.querySelector("[data-testid='kt-modal-submit']").addEventListener("click", () => {
			const vals = getValues();
			const missing = fields.filter((f) => f.required && !vals[f.name]);
			if (missing.length) {
				const inp = overlay.querySelector(`[name="${missing[0].name}"]`);
				if (inp) { inp.focus(); inp.style.borderColor = "#ba1a1a"; }
				return;
			}
			close();
			onSubmit(vals);
		});

		// Enter key submits (except textarea)
		overlay.addEventListener("keydown", (e) => {
			if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
				overlay.querySelector("[data-testid='kt-modal-submit']").click();
			}
		});

		return { overlay, close, getValues };
	}

	/**
	 * Target-specific modal — extends _showModal with measurement_type and
	 * period_type conditional field toggling.
	 */
	_showTargetModal({ title, contextLabel, primaryLabel, defaults = {}, onSubmit }) {
		const me = this;
		function esc(s) {
			const d = document.createElement("div");
			d.textContent = s == null ? "" : String(s);
			return d.innerHTML;
		}

		const ctxRow = contextLabel
			? `<div class="kt-swb-modal-ctx">
				<span class="material-symbols-outlined">lock</span>
				<span>${esc(contextLabel)}</span>
			</div>` : "";

		const mt = defaults.measurement_type || "Numeric";
		const ptype = defaults.target_period_type || "Annual";
		const isNumeric = mt === "Numeric" || mt === "Percentage";

		const unitOptions = ["Facilities", "Staff", "People", "Sites", "Index", "Unit", "KES", "USD", "EUR", "%", "Other"].map((u) =>
			`<option value="${esc(u)}"${u === (defaults.target_unit || "") ? " selected" : ""}>${esc(u)}</option>`
		).join("");

		const html = `
		<div class="kt-swb-modal-overlay" data-testid="kt-modal-overlay">
			<div class="kt-swb-modal-backdrop" data-testid="kt-modal-backdrop"></div>
			<div class="kt-swb-modal-box" data-testid="kt-modal-box" role="dialog" aria-modal="true">
				<div class="kt-swb-modal-hdr">
					<span class="kt-swb-modal-title" data-testid="kt-modal-title">${esc(title)}</span>
					<button class="kt-swb-modal-close" data-testid="kt-modal-close" aria-label="Close">
						<span class="material-symbols-outlined" style="font-size:20px">close</span>
					</button>
				</div>
				<div class="kt-swb-modal-body">
					${ctxRow}
					<!-- Metric Name -->
					<div class="kt-swb-modal-field">
						<label class="kt-swb-modal-lbl" for="ktm_node_title">${esc(__("Metric Name"))} <span style="color:#ba1a1a">*</span></label>
						<input id="ktm_node_title" name="node_title" type="text" class="kt-swb-modal-input"
							value="${esc(defaults.title || "")}" placeholder="${esc(__("Enter metric name"))}">
					</div>
					<!-- Measurement Type -->
					<div class="kt-swb-modal-field">
						<label class="kt-swb-modal-lbl" for="ktm_measurement_type">${esc(__("Measurement Type"))}</label>
						<select id="ktm_measurement_type" name="measurement_type" class="kt-swb-modal-select">
							${["Numeric","Percentage","Milestone","Boolean"].map((o) =>
								`<option value="${o}"${o === mt ? " selected" : ""}>${o}</option>`
							).join("")}
						</select>
					</div>
					<!-- Numeric fields group -->
					<div class="kt-swb-mt-numeric${isNumeric ? "" : " kt-swb-modal-hidden"}">
						<div class="kt-swb-modal-grid2">
							<div class="kt-swb-modal-field">
								<label class="kt-swb-modal-lbl" for="ktm_target_unit">${esc(__("Unit of Measure"))}</label>
								<select id="ktm_target_unit" name="target_unit" class="kt-swb-modal-select">${unitOptions}</select>
							</div>
							<div class="kt-swb-modal-field kt-swb-period-annual${ptype === "Annual" ? "" : " kt-swb-modal-hidden"}">
								<label class="kt-swb-modal-lbl" for="ktm_target_year">${esc(__("Target Year"))}</label>
								<input id="ktm_target_year" name="target_year" type="number" class="kt-swb-modal-input"
									value="${esc(defaults.target_year || "")}" placeholder="e.g. 2030">
							</div>
							<div class="kt-swb-modal-field kt-swb-period-date${ptype === "Milestone Date" ? "" : " kt-swb-modal-hidden"}">
								<label class="kt-swb-modal-lbl" for="ktm_target_due_date">${esc(__("Due Date"))}</label>
								<input id="ktm_target_due_date" name="target_due_date" type="date" class="kt-swb-modal-input"
									value="${esc((defaults.target_due_date || "").split(" ")[0])}">
							</div>
						</div>
						<div class="kt-swb-modal-grid2">
							<div class="kt-swb-modal-field">
								<label class="kt-swb-modal-lbl" for="ktm_baseline_value_numeric">${esc(__("Baseline Value"))}</label>
								<input id="ktm_baseline_value_numeric" name="baseline_value_numeric" type="number" class="kt-swb-modal-input"
									value="${esc(defaults.baseline_value_numeric != null ? defaults.baseline_value_numeric : "")}">
							</div>
							<div class="kt-swb-modal-field">
								<label class="kt-swb-modal-lbl" for="ktm_target_value_numeric">${esc(__("Target Value"))}</label>
								<input id="ktm_target_value_numeric" name="target_value_numeric" type="number" class="kt-swb-modal-input"
									value="${esc(defaults.target_value_numeric != null ? defaults.target_value_numeric : "")}">
							</div>
						</div>
					</div>
					<!-- Text/Milestone fields group -->
					<div class="kt-swb-mt-text${isNumeric ? " kt-swb-modal-hidden" : ""}">
						<div class="kt-swb-modal-field">
							<label class="kt-swb-modal-lbl" for="ktm_target_value_text">${esc(__("Target Description"))}</label>
							<textarea id="ktm_target_value_text" name="target_value_text" class="kt-swb-modal-textarea"
								placeholder="${esc(__("Describe the target outcome"))}">${esc(defaults.target_value_text || "")}</textarea>
						</div>
					</div>
					<!-- Period Type -->
					<div class="kt-swb-modal-field">
						<label class="kt-swb-modal-lbl" for="ktm_target_period_type">${esc(__("Period Type"))}</label>
						<select id="ktm_target_period_type" name="target_period_type" class="kt-swb-modal-select">
							${["Annual","Milestone Date","End of Plan"].map((o) =>
								`<option value="${o}"${o === ptype ? " selected" : ""}>${o}</option>`
							).join("")}
						</select>
					</div>
					<div class="kt-swb-modal-hint">
						<span class="material-symbols-outlined">info</span>
						<span>${esc(__("Numeric and Percentage types support baseline and target values. Milestone and Boolean types use descriptive targets."))}</span>
					</div>
				</div>
				<div class="kt-swb-modal-ftr">
					<button class="kt-swb-modal-cancel" data-testid="kt-modal-cancel">${esc(__("Cancel"))}</button>
					<button class="kt-swb-modal-submit" data-testid="kt-modal-submit">${esc(primaryLabel)}</button>
				</div>
			</div>
		</div>`;

		const el = document.createElement("div");
		el.innerHTML = html;
		const overlay = el.firstElementChild;
		document.body.appendChild(overlay);

		setTimeout(() => {
			const first = overlay.querySelector(".kt-swb-modal-input");
			if (first) first.focus();
		}, 50);

		const close = () => {
			if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
			document.removeEventListener("keydown", onKey);
		};
		const onKey = (e) => { if (e.key === "Escape") close(); };
		document.addEventListener("keydown", onKey);

		// Measurement type toggling
		const mtSel = overlay.querySelector("[name='measurement_type']");
		const toggleMtype = (val) => {
			const numeric = val === "Numeric" || val === "Percentage";
			overlay.querySelectorAll(".kt-swb-mt-numeric").forEach((el) =>
				el.classList.toggle("kt-swb-modal-hidden", !numeric));
			overlay.querySelectorAll(".kt-swb-mt-text").forEach((el) =>
				el.classList.toggle("kt-swb-modal-hidden", numeric));
		};
		mtSel.addEventListener("change", (e) => toggleMtype(e.target.value));

		// Period type toggling
		const ptSel = overlay.querySelector("[name='target_period_type']");
		const togglePtype = (val) => {
			overlay.querySelectorAll(".kt-swb-period-annual").forEach((el) =>
				el.classList.toggle("kt-swb-modal-hidden", val !== "Annual"));
			overlay.querySelectorAll(".kt-swb-period-date").forEach((el) =>
				el.classList.toggle("kt-swb-modal-hidden", val !== "Milestone Date"));
		};
		ptSel.addEventListener("change", (e) => togglePtype(e.target.value));

		overlay.querySelector("[data-testid='kt-modal-backdrop']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-modal-close']").addEventListener("click", close);
		overlay.querySelector("[data-testid='kt-modal-cancel']").addEventListener("click", close);

		const getValues = () => {
			const vals = {};
			overlay.querySelectorAll("[name]").forEach((inp) => {
				vals[inp.name] = inp.tagName === "SELECT" ? inp.value : (inp.value || "").trim();
			});
			return vals;
		};

		overlay.querySelector("[data-testid='kt-modal-submit']").addEventListener("click", () => {
			const vals = getValues();
			if (!vals.node_title) {
				const inp = overlay.querySelector("[name='node_title']");
				if (inp) { inp.focus(); inp.style.borderColor = "#ba1a1a"; }
				return;
			}
			close();
			onSubmit(vals);
		});

		return { overlay, close, getValues };
	}

	/** Edit Strategic Plan inline modal (title + description). */
	_showPlanModal() {
		const me = this;
		const planTitle = me.$wrapper.find("[data-testid='swb-plan-title']").text().trim()
			|| me.planName || "";
		const planDesc = me._planDescription || "";

		me._showModal({
			title: __("Edit Plan"),
			fields: [
				{ name: "plan_title", label: __("Plan Title"), type: "text", required: true,
					value: planTitle, placeholder: __("Enter plan title") },
				{ name: "description", label: __("Description"), type: "textarea",
					value: planDesc, placeholder: __("Optional description") },
			],
			primaryLabel: __("Save Changes"),
			onSubmit(values) {
				frappe.call({
					method: "kentender_strategy.api.strategy_builder.update_plan",
					args: { plan_name: me.planName, data: JSON.stringify(values) },
					callback() {
						me.loadPlanMeta();
						frappe.show_alert({ message: __("Plan updated"), indicator: "green" });
					},
				});
			},
		});
	}

	loadProcurementJourneyImpact(nodeName, nodeDoctype) {
		const $section = this.$procurementImpactSection;
		if (!$section || !$section.length) return;

		const $body = $section.find('[data-testid="plc-strategy-procurement-journey-impact-body"]');
		$body.html(`<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-loading">${__("Loading\u2026")}</p>`);

		function esc(s) {
			const t = String(s == null ? "" : s);
			return frappe.utils && frappe.utils.escape_html ? frappe.utils.escape_html(t) : t;
		}

		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.get_procurement_journeys_for_strategy_node",
			args: { strategy_node_doctype: nodeDoctype, name: nodeName },
			callback: function (r) {
				if (!$body.length) return;
				if (r.exc) {
					$body.html(`<p class="text-danger small mb-0" data-testid="plc-strategy-procurement-journey-impact-error">${esc(r.exc)}</p>`);
					return;
				}
				const d = r.message;
				if (!d || !d.ok) {
					const msg = (d && d.message) || __("Unable to load procurement links.");
					$body.html(`<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-empty">${esc(msg)}</p>`);
					return;
				}

				const journeys = d.journeys || [];
				const lines = d.budget_lines || [];

				if (!journeys.length && !lines.length) {
					$body.html(`<p class="text-muted small mb-0" data-testid="plc-strategy-procurement-journey-impact-none">${__("No linked procurement journeys or budget lines.")}</p>`);
					return;
				}

				let html = "";

				if (journeys.length) {
					html += `<div class="mb-2" data-testid="plc-strategy-procurement-journey-impact-journeys"><div class="small font-weight-bold mb-1">${__("Linked procurement journeys")}</div><ul class="list-unstyled mb-0 pl-0">`;
					journeys.forEach(function (j) {
						const title = esc(j.journey_title || j.journey_code || "");
						const code = esc(j.journey_code || "");
						const stage = esc(j.current_stage_label || "");
						const href = esc(j.open_route || "#");
						html += `<li class="mb-1" data-testid="plc-strategy-procurement-journey-impact-journey-row"><a href="${href}"><span data-testid="plc-strategy-procurement-journey-impact-journey-title">${title}</span></a> <span class="text-muted small">(${code})</span>${stage ? `<span class="text-muted small"> — ${stage}</span>` : ""}</li>`;
					});
					html += `</ul></div>`;
				}

				if (lines.length) {
					html += `<div data-testid="plc-strategy-procurement-journey-impact-budget-lines"><div class="small font-weight-bold mb-1">${__("Linked budget lines")}</div><ul class="list-unstyled mb-0 pl-0">`;
					lines.forEach(function (line) {
						const nm = esc(line.name || "");
						const code = esc(line.code || "");
						const href = esc(line.list_route || "#");
						html += `<li class="mb-1" data-testid="plc-strategy-procurement-journey-impact-budget-row"><a href="${href}"><span data-testid="plc-strategy-procurement-journey-impact-budget-name">${nm}</span></a> <span class="text-muted small">(${code})</span></li>`;
					});
					html += `</ul></div>`;
				}

				$body.html(html);
			},
			error: function (err) {
				$body.html(`<p class="text-danger small mb-0" data-testid="plc-strategy-procurement-journey-impact-error">${esc(err && err.message)}</p>`);
			},
		});
	}



	deleteSelected() {
			if (this.readOnly) {
				frappe.msgprint(__("You have read-only access to this plan."));
				return;
			}
			const me = this;
			if (!me.selectedName) {
				return;
			}
			frappe.confirm(__("Delete this node?"), () => {
				frappe.call({
					method: "kentender_strategy.api.strategy_builder.delete_strategy_node",
					args: { node_name: me.selectedName },
					callback() {
						me.selectedName = null;
						me.loadTree();
						frappe.show_alert({ message: __("Deleted"), indicator: "green" });
					},
				});
			});
		}
	}

	function _doRenderShell($w, setupSidebar) {
		const s = $w.data("kt_sb");
		if (!s || (frappe.get_route() || [])[0] !== "strategy-builder") return;
		const next = (frappe.get_route() || [])[1] || null;
		if (next && next !== s.planName) s.planName = next;
		/* Only render if the shell hasn't been injected yet (avoid double-render). */
		const hasShell = !!$w.find("[data-testid='strategy-builder-page']").length;
		if (!hasShell) {
			s.renderShell();
		}
		/* Re-establish the Strategy Management sidebar on the first real show.
		   The class-name conflict that previously caused DOM wipes is fixed, so
		   this is now safe to call here. */
		if (setupSidebar && frappe.app && frappe.app.sidebar) {
			frappe.app.sidebar.setup("Procurement");
		}
	}

	function bootStrategyBuilderPage() {
		const el = frappe.pages["strategy-builder"];
		if (!el) {
			return false;
		}
		const $w = $(el);
		if ($w.data("kt_sb")) {
			/* Already booted — re-render if shell is missing (show fired before handler). */
			if ((frappe.get_route() || [])[0] === "strategy-builder") {
				setTimeout(() => _doRenderShell($w, false), 0);
			}
			return true;
		}
		const sb = new StrategyBuilder($w);
		$w.data("kt_sb", sb);
		sb.init();
		/* 'show' fires AFTER Frappe completes its own page-show lifecycle.
		   This is the only safe place to inject content. Pass setupSidebar=true
		   so the Strategy Management sidebar is restored on direct load / refresh. */
		$w.off("show.kt_sb_boot").on("show.kt_sb_boot", function () {
			setTimeout(function () { _doRenderShell($w, true); }, 0);
		});
		/* If we booted AFTER 'show' already fired (retry-loop race), render now.
		   No sidebar setup here — it would navigate away on cold retry paths. */
		if ((frappe.get_route() || [])[0] === "strategy-builder") {
			setTimeout(() => _doRenderShell($w, false), 0);
		}
		return true;
	}

	function scheduleStrategyBuilderBoot() {
		const r = frappe.get_route() || [];
		if (r[0] !== "strategy-builder") {
			return;
		}
		if (bootStrategyBuilderPage()) {
			return;
		}
		// Page container can appear several seconds after route change on slow loads.
		let n = 0;
		const max = 600;  // 600 × 50 ms = 30 s
		const t = setInterval(function () {
			n += 1;
			const r2 = frappe.get_route() || [];
			if (r2[0] !== "strategy-builder") {
				clearInterval(t);
				return;
			}
			if (bootStrategyBuilderPage()) {
				clearInterval(t);
			} else if (n >= max) {
				clearInterval(t);
				// eslint-disable-next-line no-console
				console.warn(
					"Strategy Builder: page container not ready after 30 s. If the main area stays blank, check Page \"strategy-builder\" roles (Planning Authority / Strategy Manager) and reload.",
				);
			}
		}, 50);
	}

	// Desk may eval this script before `frappe.pages["strategy-builder"]` exists; SPA navigation
	// can fire page-change before listeners run. Cover router + delayed retries.
	$(document).on("page-change", scheduleStrategyBuilderBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleStrategyBuilderBoot);
	}

	scheduleStrategyBuilderBoot();
})();
