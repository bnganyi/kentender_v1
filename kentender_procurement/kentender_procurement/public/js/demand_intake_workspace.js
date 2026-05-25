// Demand Intake and Approval workspace — compact lifecycle bar + tabbed detail panels (Phase 0–2).

(function () {
	const DIA_WS = "Demand Intake and Approval";

	const DETAIL_TABS = [
		{ id: "overview", label: __("Overview"), testId: "dia-tab-overview" },
		{ id: "items", label: __("Items & Value"), testId: "dia-tab-items" },
		{ id: "review", label: __("Review"), testId: "dia-tab-review" },
		{ id: "planning", label: __("Planning"), testId: "dia-tab-planning" },
		{ id: "audit", label: __("Audit"), testId: "dia-tab-audit" },
	];

	const QUEUE_CHIPS = [
		{ id: "all", label: __("All"), testId: "dia-tab-all", countKey: "total", workScope: "all", lifecycle: "all", group: "scope" },
		{ id: "mywork", label: __("My Work"), testId: "dia-tab-my-work", countKey: null, workScope: "mywork", lifecycle: "all", group: "scope" },
		{ id: "draft", label: __("Draft"), testId: "dia-tab-draft", countKey: "draft_count", workScope: "all", lifecycle: "draft", group: "intake" },
		{
			id: "submitted",
			label: __("HoD"),
			testId: "dia-tab-hod",
			countKey: "submitted_count",
			workScope: "all",
			lifecycle: "submitted",
			group: "approval",
		},
		{
			id: "under_review",
			label: __("Finance"),
			testId: "dia-tab-finance",
			countKey: "under_review_count",
			workScope: "all",
			lifecycle: "under_review",
			group: "approval",
		},
		{
			id: "approved",
			label: __("Approved"),
			testId: "dia-tab-approved",
			countKey: "approved_count",
			workScope: "all",
			lifecycle: "approved",
			group: "approval",
		},
		{
			id: "planning_ready",
			label: __("Planning Ready"),
			testId: "dia-tab-planning-ready",
			countKey: "planning_ready_count",
			workScope: "all",
			lifecycle: "planning_ready",
			group: "handoff",
		},
		{
			id: "rejected",
			label: __("Rejected"),
			testId: "dia-tab-rejected",
			countKey: "rejected_count",
			workScope: "all",
			lifecycle: "rejected",
			group: "exceptions",
		},
		{
			id: "cancelled",
			label: __("Cancelled"),
			testId: "dia-tab-cancelled",
			countKey: "cancelled_count",
			workScope: "all",
			lifecycle: "cancelled",
			group: "exceptions",
		},
		{
			id: "emergency",
			label: __("Emergency"),
			testId: "dia-tab-emergency",
			countKey: "emergency_count",
			workScope: "all",
			lifecycle: "emergency",
			group: "exceptions",
		},
	];

	const QUEUE_CHIP_GROUPS = [
		{ id: "scope", label: null },
		{ id: "intake", label: __("Intake") },
		{ id: "approval", label: __("Approval") },
		{ id: "handoff", label: __("Handoff") },
		{ id: "exceptions", label: __("Exceptions") },
	];

	const QUEUE_CHIP_IDS = {};
	for (let qi = 0; qi < QUEUE_CHIPS.length; qi++) {
		QUEUE_CHIP_IDS[QUEUE_CHIPS[qi].id] = true;
	}

	const QUEUE_TO_LIFECYCLE = {
		my_drafts: "draft",
		submitted_by_me: "submitted",
		pending_hod: "under_review",
		pending_finance: "under_review",
		planning_ready: "planning_ready",
		approved_not_planned: "approved",
		emergency_approved: "emergency",
		emergency: "emergency",
		emergency_fin: "emergency",
		dia_rejected: "rejected",
		rejected: "rejected",
		hod_rejected: "rejected",
		returned_to_me: "draft",
		returned_await: "draft",
		my_approved: "approved",
		all_approved: "approved",
		approved_today: "approved",
		budget_exceptions: "under_review",
		all_demands: "all",
		all_dept: "all",
	};

	const DIA_LANDING_ACTION_TESTID = {
		open_form: "dia-action-edit",
		submit_demand: "dia-action-submit",
		approve_hod: "dia-action-approve-hod",
		approve_finance: "dia-action-approve-finance",
		return_from_hod: "dia-action-return",
		return_from_finance: "dia-action-return",
		reject_from_hod: "dia-action-reject",
		reject_from_finance: "dia-action-reject",
		cancel_demand: "dia-action-cancel",
		mark_planning_ready: "dia-action-mark-planning-ready",
		return_approved_to_finance: "dia-action-return-to-finance",
	};

	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let activeQueueFilter = "mywork";
	let activeDetailTab = "overview";
	let searchQuery = "";
	let lastPortfolio = null;
	let lastRoleKey = null;
	let lastQueueListPayload = null;
	let selectedDemandName = null;
	let currentDetailPayload = null;
	let diaSearchTimer = null;
	let detailLoadSeq = 0;
	let diaQueueListReqId = 0;
	let explicitQueueFilterRestored = false;
	let diaPanelsDirty = false;
	const DIA_WORKBENCH_BUILD = "20260523-flicker4";

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function userCanCreateDemand() {
		return (
			typeof frappe !== "undefined" &&
			frappe.model &&
			typeof frappe.model.can_create === "function" &&
			frappe.model.can_create("Demand")
		);
	}

	function defaultQueueFilter(roleKey) {
		if (roleKey === "auditor") {
			return "all";
		}
		return "mywork";
	}

	function resolveQueueApiParams() {
		const chip = QUEUE_CHIPS.find(function (c) {
			return c.id === activeQueueFilter;
		});
		if (!chip) {
			return { work_scope: "mywork", lifecycle_filter: "all" };
		}
		return { work_scope: chip.workScope, lifecycle_filter: chip.lifecycle };
	}

	function migrateQueueFilterFromState(st) {
		if (!st) {
			return null;
		}
		if (st.queueFilter && QUEUE_CHIP_IDS[st.queueFilter]) {
			return st.queueFilter;
		}
		if (st.queueFilter === "not_yet_planned") {
			return "approved";
		}
		const lifecycle = st.lifecycleFilter ? String(st.lifecycleFilter) : "";
		const scope = st.workScope ? String(st.workScope) : st.workTab ? String(st.workTab) : "";
		if (scope === "mywork" && (!lifecycle || lifecycle === "all")) {
			return "mywork";
		}
		if (scope === "all" && (!lifecycle || lifecycle === "all")) {
			return "all";
		}
		if (lifecycle && lifecycle !== "all" && QUEUE_CHIP_IDS[lifecycle]) {
			return lifecycle;
		}
		if (st.queueId && QUEUE_TO_LIFECYCLE[st.queueId]) {
			const mapped = QUEUE_TO_LIFECYCLE[st.queueId];
			if (mapped !== "all" && QUEUE_CHIP_IDS[mapped]) {
				return mapped;
			}
		}
		return null;
	}

	function saveDiaWorkbenchState() {
		if (typeof kentender_core === "undefined" || !kentender_core.kt_state) {
			return;
		}
		const api = resolveQueueApiParams();
		kentender_core.kt_state.save("dia", {
			queueFilter: activeQueueFilter,
			workScope: api.work_scope,
			lifecycleFilter: api.lifecycle_filter,
			detailTab: activeDetailTab,
			searchQuery: searchQuery,
			selectedRecord: selectedDemandName,
		});
		if (selectedDemandName) {
			kentender_core.kt_state.setSelectedRecord("dia", selectedDemandName);
		}
	}

	function restoreDiaWorkbenchState() {
		explicitQueueFilterRestored = false;
		if (typeof kentender_core === "undefined" || !kentender_core.kt_state) {
			return;
		}
		const stored = kentender_core.kt_state.consumeSelectedRecord("dia");
		if (stored) {
			selectedDemandName = stored;
		}
		const st = kentender_core.kt_state.restore("dia");
		if (!st) {
			return;
		}
		const migrated = migrateQueueFilterFromState(st);
		if (migrated) {
			activeQueueFilter = migrated;
			explicitQueueFilterRestored = true;
		}
		if (st.detailTab) {
			activeDetailTab = st.detailTab;
		}
		if (st.searchQuery != null && st.searchQuery !== "") {
			searchQuery = String(st.searchQuery);
		}
		if (!selectedDemandName && st.selectedRecord) {
			selectedDemandName = st.selectedRecord;
		}
	}

	function focusDiaStatusChips() {
		const host = document.querySelector('[data-testid="dia-status-chips"]');
		if (host && typeof host.scrollIntoView === "function") {
			host.scrollIntoView({ block: "nearest", behavior: "smooth" });
		}
		const first = host && host.querySelector(".kt-status-filter");
		if (first && typeof first.focus === "function") {
			first.focus();
		}
	}

	function diaQueueListScrollHost(listRoot) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.listHost === "function") {
			return helper.listHost(listRoot, ".kt-dia-row-list");
		}
		if (!listRoot) {
			return null;
		}
		return listRoot.querySelector(".kt-dia-row-list");
	}

	function diaReadQueueListScrollTop(listRoot) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.readScrollTop === "function") {
			return helper.readScrollTop(listRoot, ".kt-dia-row-list");
		}
		const host = diaQueueListScrollHost(listRoot);
		return host && typeof host.scrollTop === "number" ? host.scrollTop : 0;
	}

	function diaRestoreQueueListScrollTop(listRoot, top, selectedName) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.restoreScrollTop === "function") {
			helper.restoreScrollTop(
				listRoot,
				".kt-dia-row-list",
				top,
				selectedName,
				"[data-dia-demand]",
				"data-dia-demand"
			);
			return;
		}
		const host = diaQueueListScrollHost(listRoot);
		if (!host) {
			return;
		}
		host.scrollTop = typeof top === "number" ? top : 0;
		if (!selectedName) {
			return;
		}
		let sel = null;
		host.querySelectorAll("[data-dia-demand]").forEach(function (el) {
			if (el.getAttribute("data-dia-demand") === selectedName) {
				sel = el;
			}
		});
		if (!sel || typeof sel.getBoundingClientRect !== "function") {
			return;
		}
		const rowRect = sel.getBoundingClientRect();
		const listRect = host.getBoundingClientRect();
		if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
			sel.scrollIntoView({ block: "nearest" });
		}
	}

	function detailPayloadSignature(payload) {
		if (!payload || !payload.name) {
			return "";
		}
		const a = payload.a || {};
		const e = payload.e || {};
		const c = payload.c || {};
		return [
			payload.name,
			a.status || "",
			a.title || "",
			a.demand_id || "",
			e.planning_status || "",
			e.current_stage || "",
			String(c.total_amount != null ? c.total_amount : ""),
			nextStepLabel(payload),
			String((payload.actions || []).length),
		].join("#");
	}

	function queueListSignature(payload) {
		if (!payload || !Array.isArray(payload.demands)) {
			return "";
		}
		const cur = payload.currency || "";
		const rk = payload.role_key || "";
		const rows = payload.demands
			.map(function (r) {
				return (
					(r.name || "") +
					"#" +
					(r.status || "") +
					"#" +
					String(r.total_amount != null ? r.total_amount : "") +
					"#" +
					(r.demand_id || "") +
					"#" +
					(r.title || "") +
					"#" +
					(r.reservation_status || "")
				);
			})
			.join("|");
		return rk + "|" + cur + "|" + rows;
	}

	function syncDemandListSelection(listRoot, selectedName, opts) {
		opts = opts || {};
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.syncSelection === "function") {
			helper.syncSelection(
				listRoot,
				".kt-dia-row-list",
				".kt-dia-queue-item[data-dia-demand]",
				"data-dia-demand",
				selectedName,
				"is-active"
			);
			if (opts.ensureSelectedVisible) {
				diaRestoreQueueListScrollTop(listRoot, diaReadQueueListScrollTop(listRoot), selectedName);
			}
			return;
		}
		const host = diaQueueListScrollHost(listRoot);
		if (!host) {
			return;
		}
		host.querySelectorAll(".kt-dia-queue-item[data-dia-demand]").forEach(function (el) {
			const nm = el.getAttribute("data-dia-demand");
			const on = nm && nm === selectedName;
			el.classList.toggle("is-active", !!on);
			el.setAttribute("aria-selected", on ? "true" : "false");
		});
		if (opts.ensureSelectedVisible) {
			diaRestoreQueueListScrollTop(listRoot, diaReadQueueListScrollTop(listRoot), selectedName);
		}
	}

	function workspaceNameMatchesDia(name) {
		if (name == null || name === "") return false;
		if (name === DIA_WS) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(DIA_WS);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "demand-intake-and-approval";
	}

	function isDiaWorkspaceRoute() {
		try {
			const loc = window.location;
			const path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
			if (path.includes("demand-intake-and-approval") || path.includes("demand_intake_and_approval")) {
				return true;
			}
		} catch (e) {
			/* ignore */
		}
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesDia(workspaceName)) return true;
					if (workspaceName) return false;
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesDia(w)) return true;
				if (w) return false;
			}
		} catch (e2) {
			/* ignore */
		}
		const dr = (document.body && document.body.getAttribute("data-route")) || "";
		if (dr.includes(DIA_WS) || dr.toLowerCase().includes("demand-intake")) {
			return true;
		}
		return false;
	}

	function syncDiaShellClass() {
		document.body.classList.toggle("kt-dia-shell", isDiaWorkspaceRoute());
	}

	function removeDiaLandingIfWrongRoute() {
		document.querySelectorAll(".kt-dia-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-dia-shell");
		bindScheduled = false;
		lastRoleKey = null;
		lastPortfolio = null;
		lastQueueListPayload = null;
		selectedDemandName = null;
		currentDetailPayload = null;
		activeQueueFilter = "mywork";
		activeDetailTab = "overview";
		searchQuery = "";
		explicitQueueFilterRestored = false;
		if (diaSearchTimer) {
			clearTimeout(diaSearchTimer);
			diaSearchTimer = null;
		}
		detailLoadSeq += 1;
	}

	function getWorkspacesPageRoot() {
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	function resolveWorkspaceEditorMount() {
		const root = getWorkspacesPageRoot();
		if (root) {
			let esc = root.querySelector(".layout-main-section .editor-js-container");
			if (!esc) esc = root.querySelector(".editor-js-container");
			if (!esc) {
				const lms = root.querySelector(".layout-main-section");
				if (lms) esc = lms;
			}
			if (esc) return esc;
		}
		const candidates = document.querySelectorAll(".editor-js-container");
		let fallback = null;
		for (let i = 0; i < candidates.length; i++) {
			const el = candidates[i];
			if (!el || !el.isConnected) continue;
			if (!fallback) fallback = el;
			if (el.getClientRects && el.getClientRects().length > 0) return el;
		}
		return fallback;
	}

	function portfolioCount(portfolio, countKey) {
		const p = portfolio || {};
		if (!countKey) {
			return null;
		}
		const v = p[countKey];
		return v != null ? Number(v) : 0;
	}

	function renderStatusChipsHtml(portfolio) {
		let html =
			'<div class="kt-status-filter-row kt-dia-status-filter-row" data-testid="dia-status-filter-row">';
		let lastGroup = null;
		for (let i = 0; i < QUEUE_CHIPS.length; i++) {
			const chip = QUEUE_CHIPS[i];
			if (chip.group !== lastGroup) {
				const groupMeta = QUEUE_CHIP_GROUPS.find(function (g) {
					return g.id === chip.group;
				});
				if (lastGroup !== null) {
					html += '<span class="kt-dia-status-filter-sep" aria-hidden="true"></span>';
				}
				if (groupMeta && groupMeta.label) {
					html +=
						'<span class="kt-dia-status-filter-sep kt-dia-status-filter-sep--label text-muted small">' +
						escapeHtml(groupMeta.label) +
						"</span>";
				}
				lastGroup = chip.group;
			}
			const on = activeQueueFilter === chip.id;
			const count = portfolioCount(portfolio, chip.countKey);
			const isZero = count != null && Number(count) === 0;
			html +=
				'<button type="button" class="kt-status-filter kt-dia-status-chip' +
				(on ? " is-active kt-status-filter-active" : "") +
				(isZero ? " is-zero" : "") +
				'" data-kt-dia-queue-filter="' +
				escapeHtml(chip.id) +
				'" data-testid="' +
				escapeHtml(chip.testId) +
				'" aria-selected="' +
				(on ? "true" : "false") +
				'"><span class="kt-status-filter__label">' +
				escapeHtml(chip.label) +
				"</span>";
			if (count != null) {
				html += ' <span class="kt-status-filter__count">' + escapeHtml(String(count)) + "</span>";
			}
			html += "</button>";
		}
		html += "</div>";
		return html;
	}

	function paintPortfolioChips(portfolio) {
		lastPortfolio = portfolio || lastPortfolio || {};
		const host = document.querySelector('[data-testid="dia-status-chips"]');
		if (!host) {
			return;
		}
		host.innerHTML = renderStatusChipsHtml(lastPortfolio);
	}

	function removeStaleDiaShellIfNeeded() {
		const root = document.getElementById("kt-dia-root");
		if (!root) {
			return false;
		}
		const build = root.getAttribute("data-dia-workbench-build");
		if (build === DIA_WORKBENCH_BUILD) {
			return false;
		}
		root.remove();
		bindScheduled = false;
		currentDetailPayload = null;
		diaPanelsDirty = false;
		detailLoadSeq += 1;
		return true;
	}

	function injectDiaLandingShell() {
		removeStaleDiaShellIfNeeded();
		if (document.getElementById("kt-dia-list-root")) {
			return { ok: true, inserted: false };
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false, inserted: false };
		const wrap = document.createElement("div");
		wrap.id = "kt-dia-root";
		wrap.className = "kt-dia-injected-shell";
		wrap.setAttribute("data-testid", "dia-landing-page");
		wrap.setAttribute("data-dia-workbench-build", DIA_WORKBENCH_BUILD);
		wrap.innerHTML =
			'<div class="kt-dia-workspace-header kt-dia-workspace-header--compact mb-1">' +
			'<div class="kt-dia-header-row">' +
			'<div>' +
			'<h2 class="kt-dia-page-title h5 mb-1" data-testid="dia-page-title">' +
			escapeHtml(__("Demand Intake and Approval")) +
			"</h2>" +
			'<p class="kt-dia-page-intro text-muted small mb-0" data-testid="dia-page-intro">' +
			escapeHtml(__("Capture, approve, and prepare procurement demand for planning.")) +
			"</p></div>" +
			'<div class="kt-dia-header-cta" data-testid="dia-header-cta"></div>' +
			"</div></div>" +
			'<div class="kt-dia-status-chips" data-testid="dia-status-chips"></div>' +
			'<div class="kt-dia-master-detail kt-dia-master-detail--tight">' +
			'<div class="kt-dia-col-list">' +
			'<div class="kt-dia-section kt-surface">' +
			'<div class="kt-dia-list-head" data-testid="dia-list-head">' +
			'<div class="kt-dia-list-head__tools">' +
			'<label class="kt-dia-sr-only" for="kt-dia-search-input">' +
			escapeHtml(__("Search")) +
			'</label><input type="search" class="form-control form-control-sm kt-dia-list-search" id="kt-dia-search-input" data-testid="dia-search" placeholder="' +
			escapeHtml(__("Demand ID, title, requester, department…")) +
			'" value="' +
			escapeHtml(searchQuery) +
			'" />' +
			'<button type="button" class="btn btn-default btn-sm kt-dia-filters-icon-btn" data-dia-action="toggle-filters" data-testid="dia-filters-toggle" id="kt-dia-filters-toggle" aria-expanded="false" aria-controls="kt-dia-filters-popover" title="' +
			escapeHtml(__("Refine (filters)")) +
			'">' +
			'<svg class="kt-dia-filters-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M0 1.25h16v1.2H0V1.25zM2.5 6.1h11v1.2h-11V6.1zM4.5 10.8h7v1.2h-7v-1.2z" /></svg>' +
			'<span class="kt-dia-sr-only">' +
			escapeHtml(__("Refine (filters)")) +
			"</span></button></div></div>" +
			'<div id="kt-dia-filters-popover" class="kt-dia-filters-popover" data-testid="dia-filters-panel" hidden data-kt-dia-filters="1">' +
			'<div class="kt-dia-filter-grid">' +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Demand Type")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-demand-type"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Department")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-department"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Budget Line")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-budget-line"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Priority")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-priority"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Requisition Type")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-requisition-type"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group kt-dia-filter-date-range" data-testid="dia-filter-date-range">' +
			'<label class="small text-muted d-block">' +
			escapeHtml(__("Request date range")) +
			"</label>" +
			'<div class="d-flex gap-2 align-items-center flex-wrap">' +
			'<input type="date" class="form-control form-control-sm" data-testid="dia-filter-date-from" aria-label="' +
			escapeHtml(__("Request date from")) +
			'" />' +
			'<span class="text-muted small">—</span>' +
			'<input type="date" class="form-control form-control-sm" data-testid="dia-filter-date-to" aria-label="' +
			escapeHtml(__("Request date to")) +
			'" /></div></div>' +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Amount min")) +
			'</label><input type="number" step="any" min="0" class="form-control form-control-sm" data-testid="dia-filter-amount-min" /></div>' +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Amount max")) +
			'</label><input type="number" step="any" min="0" class="form-control form-control-sm" data-testid="dia-filter-amount-max" /></div>' +
			'<div class="form-group"><label class="small text-muted">' +
			escapeHtml(__("Status")) +
			'</label><select class="form-control form-control-sm" data-testid="dia-filter-status"><option value="">' +
			escapeHtml(__("All")) +
			"</option></select></div>" +
			'<div class="form-group d-flex align-items-end gap-2">' +
			'<button type="button" class="btn btn-primary btn-sm" data-dia-action="apply-filters" data-testid="dia-filter-apply">' +
			escapeHtml(__("Apply")) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm" data-dia-action="clear-filters" data-testid="dia-filter-clear">' +
			escapeHtml(__("Clear")) +
			"</button></div></div></div>" +
			'<div class="kt-dia-chip-row" data-testid="dia-active-filter-chips" hidden></div>' +
			'<div id="kt-dia-list-root" data-testid="dia-list-root"></div></div></div>' +
			'<div class="kt-dia-col-detail">' +
			'<div class="kt-dia-section kt-surface">' +
			'<div id="kt-dia-detail-root" data-testid="dia-detail-root"></div></div></div></div>';

		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) esc.insertBefore(wrap, ed);
		else esc.insertBefore(wrap, esc.firstChild);

		syncNewDemandButton();
		ensureDiaDelegatedClicks();
		return { ok: true, inserted: true };
	}

	function openNewDemandForm() {
		saveDiaWorkbenchState();
		if (
			typeof kentender_procurement !== "undefined" &&
			kentender_procurement.dia_demand_drawer &&
			typeof kentender_procurement.dia_demand_drawer.openCreate === "function"
		) {
			kentender_procurement.dia_demand_drawer.openCreate(
				function () {
					refreshDiaPortfolio();
					loadDiaQueueList();
					loadDiaDemandDetail();
				},
				function () {
					loadDiaDemandDetail();
				}
			);
			return;
		}
		if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
			kentender_core.kt_nav.toForm("dia", null, true);
			return;
		}
		if (typeof frappe !== "undefined" && frappe.new_doc) {
			frappe.new_doc("Demand");
		}
	}

	function closeDiaFiltersPopover() {
		const p = document.getElementById("kt-dia-filters-popover");
		const b = document.getElementById("kt-dia-root")
			? document.querySelector('#kt-dia-root [data-dia-action="toggle-filters"]')
			: null;
		if (p) {
			p.hidden = true;
		}
		if (b) {
			b.setAttribute("aria-expanded", "false");
		}
		document.removeEventListener("mousedown", onDiaFiltersDocMouseDown, true);
		document.removeEventListener("keydown", onDiaFiltersEscape, true);
	}

	function onDiaFiltersDocMouseDown(ev) {
		const p = document.getElementById("kt-dia-filters-popover");
		if (!p || p.hidden) {
			return;
		}
		const t = ev.target;
		if (p.contains(t) || (t && t.closest && t.closest("#kt-dia-filters-popover"))) {
			return;
		}
		if (t && t.closest && t.closest('[data-dia-action="toggle-filters"]')) {
			return;
		}
		closeDiaFiltersPopover();
	}

	function onDiaFiltersEscape(ev) {
		if (ev.key === "Escape") {
			closeDiaFiltersPopover();
		}
	}

	function ensureDiaDelegatedClicks() {
		const root = document.getElementById("kt-dia-root");
		if (!root || root.dataset.diaDelegated === "1") return;
		root.dataset.diaDelegated = "1";
		root.addEventListener("click", function (ev) {
			const chipX = ev.target.closest("[data-dia-chip-remove]");
			if (chipX && root.contains(chipX)) {
				const key = chipX.getAttribute("data-dia-chip-remove");
				clearOneDiaRefineField(key);
				renderFilterChips();
				loadDiaQueueList();
				return;
			}
			const act = ev.target.closest("[data-dia-action]");
			if (act && root.contains(act)) {
				const a = act.getAttribute("data-dia-action");
				if (a === "empty-new-demand" && userCanCreateDemand()) {
					openNewDemandForm();
					return;
				}
				if (a === "empty-focus-filters") {
					focusDiaStatusChips();
					return;
				}
				if (a === "toggle-filters") {
					const p = document.getElementById("kt-dia-filters-popover");
					if (!p) {
						return;
					}
					if (p.hidden) {
						p.hidden = false;
						act.setAttribute("aria-expanded", "true");
						document.addEventListener("mousedown", onDiaFiltersDocMouseDown, true);
						document.addEventListener("keydown", onDiaFiltersEscape, true);
					} else {
						closeDiaFiltersPopover();
					}
					return;
				}
				if (a === "apply-filters") {
					renderFilterChips();
					loadDiaQueueList();
					closeDiaFiltersPopover();
					return;
				}
				if (a === "clear-filters") {
					clearDiaRefineUi();
					renderFilterChips();
					loadDiaQueueList();
					return;
				}
			}
			const dAct = ev.target.closest("[data-dia-detail-action]");
			if (dAct && root.contains(dAct)) {
				runDiaDetailPanelAction(dAct);
				return;
			}
			const openForm = ev.target.closest("[data-dia-hero-action=\"open_form\"]");
			if (openForm && root.contains(openForm)) {
				runDiaDetailPanelAction(openForm);
				return;
			}
			const demRow = ev.target.closest("[data-dia-demand]");
			if (demRow && root.contains(demRow) && demRow.getAttribute("data-dia-demand")) {
				const nextName = demRow.getAttribute("data-dia-demand");
				if (
					nextName === selectedDemandName &&
					currentDetailPayload &&
					currentDetailPayload.name === nextName &&
					!diaPanelsDirty
				) {
					const listRoot = document.getElementById("kt-dia-list-root");
					if (listRoot) {
						syncDemandListSelection(listRoot, selectedDemandName, {
							ensureSelectedVisible: true,
						});
					}
					saveDiaWorkbenchState();
					return;
				}
				selectedDemandName = nextName;
				const listRoot = document.getElementById("kt-dia-list-root");
				if (listRoot) {
					syncDemandListSelection(listRoot, selectedDemandName, {
						ensureSelectedVisible: true,
					});
				}
				saveDiaWorkbenchState();
				loadDiaDemandDetail();
				return;
			}
			const queueChip = ev.target.closest("[data-kt-dia-queue-filter]");
			if (queueChip && root.contains(queueChip)) {
				activeQueueFilter = queueChip.getAttribute("data-kt-dia-queue-filter") || "all";
				if (!QUEUE_CHIP_IDS[activeQueueFilter]) {
					activeQueueFilter = "all";
				}
				explicitQueueFilterRestored = true;
				paintPortfolioChips(lastPortfolio);
				saveDiaWorkbenchState();
				loadDiaQueueList();
				return;
			}
			const detailTabBtn = ev.target.closest("[data-kt-dia-detail-tab]");
			if (detailTabBtn && root.contains(detailTabBtn)) {
				switchDetailTab(detailTabBtn.getAttribute("data-kt-dia-detail-tab") || "overview");
			}
		});
		root.addEventListener("input", function (ev) {
			const t = ev.target;
			if (!t || !t.getAttribute || t.getAttribute("data-testid") !== "dia-search") {
				return;
			}
			if (!root.contains(t)) {
				return;
			}
			searchQuery = t.value ? String(t.value) : "";
			if (diaSearchTimer) {
				clearTimeout(diaSearchTimer);
			}
			diaSearchTimer = setTimeout(function () {
				diaSearchTimer = null;
				renderFilterChips();
				saveDiaWorkbenchState();
				loadDiaQueueList();
			}, 400);
		});
	}

	function syncNewDemandButton() {
		const slot = document.querySelector('[data-testid="dia-header-cta"]');
		if (!slot) return;
		slot.innerHTML = "";
		if (userCanCreateDemand()) {
			const btn = document.createElement("button");
			btn.type = "button";
			btn.className = "btn btn-primary btn-sm kt-page-action-primary";
			btn.setAttribute("data-testid", "dia-new-demand-button");
			btn.innerHTML = '<span aria-hidden="true">+</span> ' + escapeHtml(__("New Demand"));
			btn.addEventListener("click", openNewDemandForm);
			slot.appendChild(btn);
		}
	}

	function formatListMoney(value, currency) {
		if (value == null || value === undefined || Number.isNaN(Number(value))) {
			return "—";
		}
		const cur = currency || "KES";
		const v = Number(value);
		try {
			return (
				cur +
				" " +
				Math.round(v).toLocaleString("en-US", {
					minimumFractionDigits: 0,
					maximumFractionDigits: 0,
				})
			);
		} catch (e) {
			return String(v);
		}
	}

	function formatDiaQueueListAmount(value) {
		if (value == null || value === undefined || Number.isNaN(Number(value))) {
			return "—";
		}
		const v = Number(value);
		try {
			return Math.round(v).toLocaleString("en-US", {
				minimumFractionDigits: 0,
				maximumFractionDigits: 0,
			});
		} catch (e) {
			return String(v);
		}
	}

	function formatDiaListDatePlain(val) {
		if (!val) {
			return "";
		}
		const raw = typeof val === "string" ? val.split(" ")[0] : val;
		try {
			if (typeof frappe !== "undefined" && frappe.datetime && frappe.datetime.str_to_user) {
				return String(frappe.datetime.str_to_user(raw, false, true) || "");
			}
		} catch (e1) {
			/* fall through */
		}
		try {
			const d = new Date(raw);
			if (!Number.isNaN(d.getTime())) {
				return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
			}
		} catch (e2) {
			/* fall through */
		}
		return String(val);
	}

	function diaPriorityBadgeClass(priority) {
		const p = (priority || "").toLowerCase();
		if (p.indexOf("high") >= 0 || p.indexOf("urgent") >= 0 || p.indexOf("critical") >= 0) {
			return "kt-dia-badge kt-dia-badge--priority kt-dia-badge--pri-high";
		}
		if (p.indexOf("low") >= 0) {
			return "kt-dia-badge kt-dia-badge--priority kt-dia-badge--pri-low";
		}
		return "kt-dia-badge kt-dia-badge--priority kt-dia-badge--pri-normal";
	}

	function diaInlineStatusClass(status) {
		const s = (status || "").toLowerCase();
		if (s.indexOf("draft") >= 0) return "kt-dia-inline-status kt-dia-inline-status--draft";
		if (s.indexOf("pending") >= 0 && s.indexOf("hod") >= 0) return "kt-dia-inline-status kt-dia-inline-status--pending-hod";
		if (s.indexOf("pending") >= 0 && s.indexOf("finance") >= 0) return "kt-dia-inline-status kt-dia-inline-status--pending-fin";
		if (s.indexOf("approved") >= 0) return "kt-dia-inline-status kt-dia-inline-status--approved";
		if (s.indexOf("planning ready") >= 0) return "kt-dia-inline-status kt-dia-inline-status--planning";
		if (s.indexOf("reject") >= 0) return "kt-dia-inline-status kt-dia-inline-status--rejected";
		if (s.indexOf("cancel") >= 0) return "kt-dia-inline-status kt-dia-inline-status--cancelled";
		return "kt-dia-inline-status kt-dia-inline-status--neutral";
	}

	function diaDemandTypeBadgeClass(dt) {
		if (dt === "Emergency") {
			return "kt-dia-badge kt-dia-badge--dtype kt-dia-badge--dtype-emergency";
		}
		if (dt === "Unplanned") {
			return "kt-dia-badge kt-dia-badge--dtype kt-dia-badge--dtype-unplanned";
		}
		return "kt-dia-badge kt-dia-badge--dtype kt-dia-badge--dtype-planned";
	}

	function diaDemandRowAccentClass(dt) {
		if (dt === "Emergency") {
			return " kt-dia-queue-item--emergency";
		}
		if (dt === "Unplanned") {
			return " kt-dia-queue-item--unplanned";
		}
		return "";
	}

	function diaDemandIdRowSlug(demandId) {
		return String(demandId || "row").replace(/[^a-zA-Z0-9_-]/g, "-");
	}

	function formatDiaListPlanningHint(row) {
		const st = String(row.status || "").trim();
		if (st === "Approved" || st === "Planning Ready") {
			const ps = String(row.planning_status || "").trim();
			if (!ps || ps === "Not Planned" || ps === "Partially Planned") {
				return __("Not yet planned");
			}
			if (ps === "Planning Ready") {
				return __("Planning ready");
			}
			return ps;
		}
		return "";
	}

	function buildDiaListMetaLine(row) {
		const parts = [];
		if (row.status) {
			parts.push(String(row.status));
		}
		const planningHint = formatDiaListPlanningHint(row);
		if (planningHint) {
			parts.push(planningHint);
		}
		if (row.requisition_type) {
			parts.push(String(row.requisition_type));
		}
		if (row.priority_level) {
			parts.push(String(row.priority_level));
		}
		if (!parts.length) {
			return "";
		}
		return (
			'<div class="kt-dia-queue-item__meta text-muted small">' +
			escapeHtml(parts.join(" · ")) +
			"</div>"
		);
	}

	function buildDiaListContextLine(row, currency) {
		const st = String(row.status || "").trim();
		const due = formatDiaListDatePlain(row.required_by_date);
		return (
			'<div class="kt-dia-queue-item__context text-muted small">' +
			escapeHtml(formatListMoney(row.total_amount, currency)) +
			(st !== "Approved" && st !== "Planning Ready" && due
				? " · " + escapeHtml(__("Required by")) + " " + escapeHtml(due)
				: "") +
			"</div>"
		);
	}

	function buildDiaListOptionalBadges(row) {
		const badges = [];
		if (row.demand_type === "Emergency") {
			badges.push(
				'<span class="kt-dia-badge kt-dia-badge--dtype kt-dia-badge--dtype-emergency">' +
					escapeHtml(__("Emergency")) +
					"</span>"
			);
		}
		if (row.is_exception) {
			badges.push(
				'<span class="kt-dia-badge kt-dia-badge--flag">' + escapeHtml(__("Exception")) + "</span>"
			);
		}
		if (String(row.status || "").trim() === "Planning Ready") {
			badges.push(
				'<span class="kt-dia-badge kt-dia-badge--planning-ready">' +
					escapeHtml(__("Planning Ready")) +
					"</span>"
			);
		}
		const rs = String(row.reservation_status || "").toLowerCase();
		if (rs.indexOf("fail") >= 0 || rs.indexOf("block") >= 0) {
			badges.push(
				'<span class="kt-dia-badge kt-dia-badge--blocked">' + escapeHtml(__("Blocked")) + "</span>"
			);
		}
		if (!badges.length) {
			return "";
		}
		return '<div class="kt-dia-queue-item__badges">' + badges.join("") + "</div>";
	}

	function nextStepLabel(payload) {
		const a = (payload && payload.a) || {};
		const e = (payload && payload.e) || {};
		const st = String(a.status || e.status || "").trim();
		const blockerCount = Number(payload && payload.integrity_blocker_count) || 0;
		const integrityBlocked = !!(payload && payload.integrity_blocked);
		if (st === "Draft") {
			if ((e.return_reason || "").trim()) {
				return __("Next step: revise and resubmit this demand.");
			}
			return __("Next step: complete the demand and submit for approval.");
		}
		if (st === "Pending HoD Approval") {
			return __("Next step: HoD review and approval.");
		}
		if (st === "Pending Finance Approval") {
			return __("Next step: finance validation and budget reservation.");
		}
		if (st === "Approved") {
			if (integrityBlocked && blockerCount > 0) {
				return __("Next step: resolve {0} planning blocker(s) — Finance action required.", [blockerCount]);
			}
			return __("Next step: confirm Planning Ready on the Planning tab.");
		}
		if (st === "Planning Ready") {
			return __("Next step: include in procurement planning.");
		}
		if (st === "Rejected") {
			return __("Next step: review rejection reason and revise if allowed.");
		}
		if (st === "Cancelled") {
			return __("This demand is cancelled.");
		}
		return __("Next step: review demand readiness.");
	}

	function renderPrimaryTabs() {
		let html = '<div class="kt-primary-tabs kt-dia-detail-tabs" role="tablist">';
		for (let i = 0; i < DETAIL_TABS.length; i++) {
			const tab = DETAIL_TABS[i];
			const on = tab.id === activeDetailTab;
			html +=
				'<button type="button" class="kt-primary-tab kt-dia-tab' +
				(on ? " is-active kt-primary-tab-active" : "") +
				'" data-kt-dia-detail-tab="' +
				escapeHtml(tab.id) +
				'" data-testid="' +
				escapeHtml(tab.testId) +
				'" role="tab" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				escapeHtml(tab.label) +
				"</button>";
		}
		html += "</div>";
		return html;
	}

	function renderActiveTabPanelHtml() {
		const tab =
			DETAIL_TABS.find(function (row) {
				return row.id === activeDetailTab;
			}) || DETAIL_TABS[0];
		return (
			'<div class="kt-dia-tab-panel-wrap">' +
			'<section class="kt-dia-tab-panel is-active" data-kt-dia-panel="' +
			escapeHtml(tab.id) +
			'" data-testid="dia-tab-panel-' +
			escapeHtml(tab.id) +
			'"><div data-testid="dia-panel-host-' +
			escapeHtml(tab.id) +
			'"></div></section></div>'
		);
	}

	function renderTabPanels() {
		return renderActiveTabPanelHtml();
	}

	function updateDetailTabButtons() {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		detailRoot.querySelectorAll("[data-kt-dia-detail-tab]").forEach(function (btn) {
			const on = btn.getAttribute("data-kt-dia-detail-tab") === activeDetailTab;
			btn.classList.toggle("is-active", on);
			btn.classList.toggle("kt-primary-tab-active", on);
			btn.setAttribute("aria-selected", on ? "true" : "false");
		});
	}

	function prefetchDetailPanelData(payload) {
		const nm = payload && payload.name;
		if (!nm) {
			return;
		}
		if (
			kentender_procurement.dia_review_panel &&
			typeof kentender_procurement.dia_review_panel.prefetch === "function"
		) {
			kentender_procurement.dia_review_panel.prefetch(nm);
		}
		if (
			kentender_procurement.dia_planning_panel &&
			typeof kentender_procurement.dia_planning_panel.prefetch === "function"
		) {
			kentender_procurement.dia_planning_panel.prefetch(nm, payload);
		}
		if (
			kentender_procurement.dia_audit_panel &&
			typeof kentender_procurement.dia_audit_panel.prefetch === "function"
		) {
			kentender_procurement.dia_audit_panel.prefetch(nm);
		}
	}

	function paintActiveDetailTabPanel(payload, forceRemount) {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot || !payload) {
			return;
		}
		const currentPanel = detailRoot.querySelector(".kt-dia-tab-panel.is-active");
		const currentTabId =
			currentPanel && currentPanel.getAttribute ? currentPanel.getAttribute("data-kt-dia-panel") : null;
		let host =
			currentTabId === activeDetailTab
				? detailRoot.querySelector('[data-testid="dia-panel-host-' + activeDetailTab + '"]')
				: null;
		if (!host) {
			const existingWrap = detailRoot.querySelector(".kt-dia-tab-panel-wrap");
			if (existingWrap) {
				existingWrap.outerHTML = renderActiveTabPanelHtml();
			}
			host = detailRoot.querySelector('[data-testid="dia-panel-host-' + activeDetailTab + '"]');
		}
		if (host) {
			mountPanel(activeDetailTab, host, payload, !!forceRemount);
		}
	}

	function switchDetailTab(tabId) {
		activeDetailTab = tabId || "overview";
		updateDetailTabButtons();
		if (currentDetailPayload) {
			paintActiveDetailTabPanel(currentDetailPayload, false);
		}
		saveDiaWorkbenchState();
	}

	function heroOpenFormAction(payload) {
		const actions = (payload && payload.actions) || [];
		for (let i = 0; i < actions.length; i++) {
			const a = actions[i];
			if (a && a.client_action === "open_form") {
				const st = String((payload.a && payload.a.status) || "").trim();
				const label =
					st === "Draft" || st === "Rejected"
						? __("Edit Demand")
						: __("View Demand");
				return (
					'<button type="button" class="btn btn-default btn-sm kt-context-action" data-dia-hero-action="open_form" data-dia-detail-action="open_form" data-dia-detail-name="' +
					escapeHtml(payload.name || "") +
					'" data-dia-detail-view-only="' +
					(st === "Draft" || st === "Rejected" ? "0" : "1") +
					'" data-testid="' +
					escapeHtml(DIA_LANDING_ACTION_TESTID.open_form) +
					'">' +
					escapeHtml(a.label || label) +
					"</button>"
				);
			}
		}
		return "";
	}

	function renderDetailShell(payload) {
		const a = payload.a || {};
		const c = payload.c || {};
		const cur = payload.currency || "KES";
		const metaParts = [];
		if (a.demand_id) {
			metaParts.push(escapeHtml(String(a.demand_id)));
		}
		if (a.requesting_department_label || a.requesting_department) {
			metaParts.push(escapeHtml(String(a.requesting_department_label || a.requesting_department)));
		}
		if (c.total_amount != null) {
			metaParts.push(escapeHtml(formatListMoney(c.total_amount, cur)));
		}
		return (
			'<div class="kt-dia-detail" data-testid="dia-detail-panel" data-dia-detail-for="' +
			escapeHtml(payload.name || "") +
			'" data-dia-workbench-build="' +
			escapeHtml(DIA_WORKBENCH_BUILD) +
			'">' +
			'<section class="kt-dia-detail-section kt-surface" data-testid="selected-demand-panel">' +
			'<header class="kt-dia-detail__hero">' +
			'<div class="kt-dia-detail__hero-main">' +
			'<h2 class="kt-dia-detail__title" data-testid="selected-demand-title">' +
			escapeHtml(a.title || payload.name || "—") +
			"</h2>" +
			'<div class="text-muted small" data-testid="selected-demand-meta">' +
			(metaParts.length ? metaParts.join(" · ") : "—") +
			"</div>" +
			'<div class="kt-dia-status-guidance mt-2">' +
			(a.status
				? '<span class="' +
					diaInlineStatusClass(a.status) +
					'" data-testid="dia-detail-status">' +
					escapeHtml(a.status) +
					"</span> "
				: "") +
			'<span class="kt-dia-next-step text-muted small" data-testid="dia-next-step">' +
			escapeHtml(nextStepLabel(payload)) +
			"</span></div></div>" +
			'<div class="kt-dia-detail__hero-actions">' +
			heroOpenFormAction(payload) +
			"</div></header>" +
			renderPrimaryTabs() +
			renderTabPanels() +
			"</section></div>"
		);
	}

	function mountPanel(panelId, host, payload, forceRemount) {
		if (!host || !payload) {
			return;
		}
		const nm = payload.name || "";
		if (
			!forceRemount &&
			host.getAttribute("data-dia-panel-mounted") === "1" &&
			host.getAttribute("data-dia-panel-for") === nm &&
			host.childElementCount > 0
		) {
			return;
		}
		host.setAttribute("data-dia-panel-mounted", "1");
		host.setAttribute("data-dia-panel-for", nm);
		const ctx = {
			payload: payload,
			roleKey: lastRoleKey,
			formatListMoney: formatListMoney,
		};
		if (panelId === "overview" && kentender_procurement.dia_overview_panel) {
			kentender_procurement.dia_overview_panel.mount(host, ctx);
			return;
		}
		if (panelId === "items" && kentender_procurement.dia_items_panel) {
			kentender_procurement.dia_items_panel.mount(host, ctx);
			return;
		}
		if (panelId === "review" && kentender_procurement.dia_review_panel) {
			kentender_procurement.dia_review_panel.mount(host, ctx);
			return;
		}
		if (panelId === "planning" && kentender_procurement.dia_planning_panel) {
			kentender_procurement.dia_planning_panel.mount(host, ctx);
			return;
		}
		if (panelId === "audit" && kentender_procurement.dia_audit_panel) {
			kentender_procurement.dia_audit_panel.mount(host, ctx);
			return;
		}
		host.innerHTML =
			'<div class="text-muted small py-2">' + escapeHtml(__("Loading…")) + "</div>";
	}

	function setTabVisibility() {
		updateDetailTabButtons();
	}

	function refreshMountedDetailPanels(payload) {
		paintActiveDetailTabPanel(payload, true);
		prefetchDetailPanelData(payload);
	}

	function updateDetailHeroInPlace(detailRoot, payload) {
		if (!detailRoot || !payload) {
			return;
		}
		const a = payload.a || {};
		const c = payload.c || {};
		const cur = payload.currency || "KES";
		const titleEl = detailRoot.querySelector('[data-testid="selected-demand-title"]');
		if (titleEl) {
			titleEl.textContent = a.title || payload.name || "—";
		}
		const metaEl = detailRoot.querySelector('[data-testid="selected-demand-meta"]');
		if (metaEl) {
			const metaParts = [];
			if (a.demand_id) {
				metaParts.push(String(a.demand_id));
			}
			if (a.requesting_department_label || a.requesting_department) {
				metaParts.push(String(a.requesting_department_label || a.requesting_department));
			}
			if (c.total_amount != null) {
				metaParts.push(formatListMoney(c.total_amount, cur));
			}
			metaEl.textContent = metaParts.length ? metaParts.join(" · ") : "—";
		}
		const statusEl = detailRoot.querySelector('[data-testid="dia-detail-status"]');
		if (statusEl && a.status) {
			statusEl.textContent = a.status;
			statusEl.className = diaInlineStatusClass(a.status);
		}
		const nextEl = detailRoot.querySelector('[data-testid="dia-next-step"]');
		if (nextEl) {
			nextEl.textContent = nextStepLabel(payload);
		}
	}

	function updateDetailShellInPlace(detailRoot, payload) {
		if (!detailRoot || !payload) {
			return;
		}
		const panelEl = detailRoot.querySelector('[data-testid="dia-detail-panel"]');
		if (panelEl) {
			panelEl.setAttribute("data-dia-detail-for", payload.name || "");
			panelEl.setAttribute("data-dia-workbench-build", DIA_WORKBENCH_BUILD);
		}
		const heroActions = detailRoot.querySelector(".kt-dia-detail__hero-actions");
		if (heroActions) {
			heroActions.innerHTML = heroOpenFormAction(payload);
		}
		updateDetailHeroInPlace(detailRoot, payload);
		updateDetailTabButtons();
	}

	function mountActiveDetailPanel(payload) {
		paintActiveDetailTabPanel(payload, false);
		prefetchDetailPanelData(payload);
	}

	function invalidateDiaPanels(demandName) {
		diaPanelsDirty = true;
		if (
			kentender_procurement.dia_review_panel &&
			typeof kentender_procurement.dia_review_panel.invalidate === "function"
		) {
			kentender_procurement.dia_review_panel.invalidate(demandName);
		}
		if (
			kentender_procurement.dia_planning_panel &&
			typeof kentender_procurement.dia_planning_panel.invalidate === "function"
		) {
			kentender_procurement.dia_planning_panel.invalidate(demandName);
		}
		if (
			kentender_procurement.dia_audit_panel &&
			typeof kentender_procurement.dia_audit_panel.invalidate === "function"
		) {
			kentender_procurement.dia_audit_panel.invalidate(demandName);
		}
	}

	function paintDetailEmpty() {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		currentDetailPayload = null;
		detailRoot.innerHTML =
			'<div class="kt-dia-empty" data-testid="dia-detail-empty">' +
			"<p>" +
			escapeHtml(__("Select a demand record to view details and take action.")) +
			"</p>" +
			'<p class="small text-muted mb-0">' +
			escapeHtml(__("Choose a row in the demand list to load overview, items, review, planning, and audit tabs.")) +
			"</p>" +
			"</div>";
	}

	function paintDetailError(msg) {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		currentDetailPayload = null;
		const m =
			msg && (msg.message || msg.error_code)
				? String(msg.message || msg.error_code)
				: __("Could not load demand details.");
		detailRoot.innerHTML =
			'<div class="kt-dia-detail kt-dia-detail--error" data-testid="dia-detail-error"><p class="text-danger small mb-0">' +
			escapeHtml(m) +
			"</p></div>";
	}

	function runDiaDetailPanelAction(btn) {
		const action = btn.getAttribute("data-dia-detail-action");
		const nm = btn.getAttribute("data-dia-detail-name");
		if (!nm || !action) {
			return;
		}
		if (action === "open_form") {
			saveDiaWorkbenchState();
			const viewOnly = btn.getAttribute("data-dia-detail-view-only") === "1";
			if (
				typeof kentender_procurement !== "undefined" &&
				kentender_procurement.dia_demand_drawer &&
				typeof kentender_procurement.dia_demand_drawer.openEdit === "function"
			) {
				kentender_procurement.dia_demand_drawer.openEdit(
					nm,
					function () {
						invalidateDiaPanels(nm);
						refreshDiaPortfolio();
						loadDiaQueueList();
						loadDiaDemandDetail();
					},
					function () {
						loadDiaDemandDetail();
					},
					{ viewOnly: viewOnly }
				);
				return;
			}
			if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
				kentender_core.kt_nav.toForm("dia", nm);
			} else if (typeof frappe !== "undefined" && frappe.set_route) {
				frappe.set_route("Form", "Demand", nm);
			}
			return;
		}
		const method = btn.getAttribute("data-dia-detail-method");
		const reasonKind = (btn.getAttribute("data-dia-detail-reason") || "").trim();
		if (!method) {
			return;
		}
		function onWorkflowSuccess() {
			invalidateDiaPanels(nm);
			refreshDiaPortfolio();
			loadDiaQueueList();
			loadDiaDemandDetail();
		}
		function callWith(extra) {
			frappe.call({
				method: method,
				args: Object.assign({ demand_name: nm }, extra || {}),
				callback: function (r) {
					if (!r || r.exc) {
						return;
					}
					frappe.show_alert({ message: __("Updated"), indicator: "green" });
					onWorkflowSuccess();
				},
				error: function (r) {
					let msg = __("Request failed");
					try {
						if (r && r._server_messages) {
							const arr = JSON.parse(r._server_messages);
							if (arr && arr.length) {
								const row = JSON.parse(arr[0]);
								if (row && row.message) {
									msg = row.message;
								}
							}
						} else if (r && r.message) {
							msg = r.message;
						}
					} catch (e1) {
						/* ignore */
					}
					frappe.msgprint({ title: __("Could not complete action"), message: msg, indicator: "red" });
				},
			});
		}
		if (reasonKind === "cancellation") {
			frappe.prompt(
				[
					{
						fieldname: "cancellation_reason",
						fieldtype: "Small Text",
						label: __("Cancellation reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ cancellation_reason: vals.cancellation_reason });
				},
				__("Cancel demand"),
				__("Cancel")
			);
			return;
		}
		if (reasonKind === "return") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Return reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ reason: vals.reason });
				},
				__("Return to draft"),
				__("Return")
			);
			return;
		}
		if (reasonKind === "rejection") {
			frappe.prompt(
				[
					{
						fieldname: "rejection_reason",
						fieldtype: "Small Text",
						label: __("Rejection reason"),
						reqd: 1,
					},
				],
				function (vals) {
					callWith({ rejection_reason: vals.rejection_reason });
				},
				__("Reject demand"),
				__("Reject")
			);
			return;
		}
		callWith();
	}

	function loadDiaDemandDetail() {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		if (!selectedDemandName) {
			paintDetailEmpty();
			return;
		}
		const existingPanel = detailRoot.querySelector(".kt-dia-detail[data-dia-detail-for]");
		const hasDetailShell = !!existingPanel;
		const sameDemand =
			existingPanel &&
			existingPanel.getAttribute("data-dia-detail-for") === selectedDemandName;
		if (
			sameDemand &&
			!diaPanelsDirty &&
			currentDetailPayload &&
			currentDetailPayload.name === selectedDemandName
		) {
			setTabVisibility();
			return;
		}
		detailLoadSeq += 1;
		const mySeq = detailLoadSeq;
		if (!sameDemand && !hasDetailShell) {
			detailRoot.innerHTML =
				'<div class="text-muted small py-3" data-testid="dia-detail-loading">' +
				escapeHtml(__("Loading details…")) +
				"</div>";
		}
		frappe.call({
			method: "kentender_procurement.demand_intake.api.dia_detail.get_dia_demand_detail",
			args: { name: selectedDemandName },
			callback: function (r) {
				if (mySeq !== detailLoadSeq) {
					return;
				}
				if (!r || !r.message) {
					paintDetailError(null);
					return;
				}
				const resp = r.message;
				if (resp.ok === false) {
					paintDetailError(resp);
					return;
				}
				const prevSig =
					currentDetailPayload && currentDetailPayload.name === selectedDemandName
						? detailPayloadSignature(currentDetailPayload)
						: "";
				const nextSig = detailPayloadSignature(resp);
				currentDetailPayload = resp;
				if (sameDemand && !diaPanelsDirty && prevSig && prevSig === nextSig) {
					setTabVisibility();
					return;
				}
				if (sameDemand && !diaPanelsDirty) {
					updateDetailHeroInPlace(detailRoot, resp);
					setTabVisibility();
					return;
				}
				if (sameDemand && diaPanelsDirty) {
					updateDetailHeroInPlace(detailRoot, resp);
					refreshMountedDetailPanels(resp);
					diaPanelsDirty = false;
					return;
				}
				if (!sameDemand && hasDetailShell) {
					updateDetailShellInPlace(detailRoot, resp);
					mountActiveDetailPanel(resp);
					diaPanelsDirty = false;
					return;
				}
				detailRoot.innerHTML = renderDetailShell(resp);
				mountActiveDetailPanel(resp);
				diaPanelsDirty = false;
			},
			error: function () {
				if (mySeq !== detailLoadSeq) {
					return;
				}
				paintDetailError(null);
			},
		});
	}

	function renderDetailForSelection() {
		if (!selectedDemandName) {
			paintDetailEmpty();
			return;
		}
		loadDiaDemandDetail();
	}

	function renderDemandList(payload) {
		lastQueueListPayload = payload;
		const listRoot = document.getElementById("kt-dia-list-root");
		if (!listRoot) {
			return;
		}
		const prevScrollTop = diaReadQueueListScrollTop(listRoot);
		const rows = (payload && payload.demands) || [];
		if (selectedDemandName && rows.length) {
			const names = new Set(rows.map(function (r) {
				return r.name;
			}));
			if (!names.has(selectedDemandName)) {
				selectedDemandName = null;
				detailLoadSeq += 1;
			}
		} else if (!rows.length && selectedDemandName) {
			selectedDemandName = null;
			detailLoadSeq += 1;
			paintDetailEmpty();
		}
		if (!rows.length) {
			const cap =
				(payload && payload.empty_caption) ||
				__("No demands match the current filters.");
			const canC = userCanCreateDemand();
			const newBtn = canC
				? '<button type="button" class="btn btn-primary btn-sm" data-dia-action="empty-new-demand" data-testid="dia-empty-cta-new">' +
					escapeHtml(__("Create new demand")) +
					"</button>"
				: "";
			const switchBtn =
				'<button type="button" class="btn btn-default btn-sm" data-dia-action="empty-focus-filters" data-testid="dia-empty-cta-filters">' +
				escapeHtml(__("Change filters")) +
				"</button>";
			const actions =
				'<div class="kt-dia-empty__actions mt-2 d-flex flex-wrap gap-2 justify-content-center align-items-center">' +
				newBtn +
				switchBtn +
				"</div>";
			listRoot.innerHTML =
				'<div class="kt-dia-empty kt-dia-empty--v3" data-testid="dia-list-empty">' +
				'<p class="mb-0 text-center">' +
				escapeHtml(cap) +
				"</p>" +
				actions +
				"</div>";
			return;
		}
		const currency = (payload && payload.currency) || "KES";
		let html =
			'<div class="kt-dia-row-list" data-testid="dia-list" role="listbox" aria-label="' +
			escapeHtml(__("Demand list")) +
			'">';
		for (let i = 0; i < rows.length; i++) {
			const row = rows[i];
			const isSel = row.name === selectedDemandName;
			const active = isSel ? " is-active" : "";
			const accent = diaDemandRowAccentClass(row.demand_type);
			const exc = row.is_exception ? " kt-dia-queue-item--exception" : "";
			const did = row.demand_id || row.name || "";
			const ttl = row.title || "";
			const rowTestSlug = diaDemandIdRowSlug(did);
			const metaLine = buildDiaListMetaLine(row);
			const contextLine = buildDiaListContextLine(row, currency);
			const optBadges = buildDiaListOptionalBadges(row);
			html +=
				'<div class="kt-dia-queue-item kt-dia-list-row' +
				active +
				accent +
				exc +
				'" data-dia-demand="' +
				escapeHtml(row.name) +
				'" tabindex="0" role="option" aria-selected="' +
				(isSel ? "true" : "false") +
				'" data-testid="dia-row-' +
				escapeHtml(rowTestSlug) +
				'">' +
				'<div class="kt-dia-queue-item__id">' +
				escapeHtml(did) +
				"</div>" +
				'<div class="kt-dia-queue-item__title" data-testid="dia-row-title-' +
				escapeHtml(rowTestSlug) +
				'">' +
				escapeHtml(ttl) +
				"</div>" +
				metaLine +
				contextLine +
				optBadges +
				"</div>";
		}
		html += "</div>";
		listRoot.innerHTML = html;
		requestAnimationFrame(function () {
			diaRestoreQueueListScrollTop(listRoot, prevScrollTop, selectedDemandName);
		});
	}

	function fillDiaSelectOptions(testId, values, useObjects) {
		const sel = document.querySelector('[data-testid="' + testId + '"]');
		if (!sel) {
			return;
		}
		const first = sel.options[0];
		sel.innerHTML = "";
		sel.appendChild(first);
		if (useObjects) {
			(values || []).forEach(function (o) {
				const opt = document.createElement("option");
				opt.value = o.value;
				opt.textContent = o.label || o.value;
				sel.appendChild(opt);
			});
		} else {
			(values || []).forEach(function (v) {
				const opt = document.createElement("option");
				opt.value = v;
				opt.textContent = v;
				sel.appendChild(opt);
			});
		}
	}

	function populateDiaFilterForm(meta) {
		fillDiaSelectOptions("dia-filter-demand-type", meta.demand_types || [], false);
		fillDiaSelectOptions("dia-filter-priority", meta.priorities || [], false);
		fillDiaSelectOptions("dia-filter-requisition-type", meta.requisition_types || [], false);
		fillDiaSelectOptions("dia-filter-status", meta.statuses || [], false);
		fillDiaSelectOptions("dia-filter-department", meta.departments || [], true);
		fillDiaSelectOptions("dia-filter-budget-line", meta.budget_lines || [], true);
	}

	function loadDiaFilterMeta(done) {
		frappe.call({
			method: "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_filter_meta",
			callback: function (r) {
				if (r && r.message && r.message.ok) {
					populateDiaFilterForm(r.message);
				}
				if (typeof done === "function") {
					done();
				}
			},
			error: function () {
				if (typeof done === "function") {
					done();
				}
			},
		});
	}

	function collectRefineFilters() {
		const out = {};
		function s(testId) {
			const el = document.querySelector('[data-testid="' + testId + '"]');
			if (!el || !el.value) {
				return "";
			}
			return String(el.value).trim();
		}
		function n(testId) {
			const el = document.querySelector('[data-testid="' + testId + '"]');
			if (!el || el.value === "" || el.value == null) {
				return null;
			}
			const v = Number(el.value);
			return Number.isFinite(v) ? v : null;
		}
		const dt = s("dia-filter-demand-type");
		if (dt) {
			out.demand_type = dt;
		}
		const pr = s("dia-filter-priority");
		if (pr) {
			out.priority_level = pr;
		}
		const rt = s("dia-filter-requisition-type");
		if (rt) {
			out.requisition_type = rt;
		}
		const st = s("dia-filter-status");
		if (st) {
			out.status = st;
		}
		const dep = s("dia-filter-department");
		if (dep) {
			out.requesting_department = dep;
		}
		const bl = s("dia-filter-budget-line");
		if (bl) {
			out.budget_line = bl;
		}
		const df = s("dia-filter-date-from");
		if (df) {
			out.date_from = df;
		}
		const dto = s("dia-filter-date-to");
		if (dto) {
			out.date_to = dto;
		}
		const amin = n("dia-filter-amount-min");
		if (amin !== null) {
			out.amount_min = amin;
		}
		const amax = n("dia-filter-amount-max");
		if (amax !== null) {
			out.amount_max = amax;
		}
		return out;
	}

	function clearDiaRefineUi() {
		[
			"dia-filter-demand-type",
			"dia-filter-department",
			"dia-filter-budget-line",
			"dia-filter-priority",
			"dia-filter-requisition-type",
			"dia-filter-status",
		].forEach(function (id) {
			const el = document.querySelector('[data-testid="' + id + '"]');
			if (el) {
				el.value = "";
			}
		});
		["dia-filter-date-from", "dia-filter-date-to", "dia-filter-amount-min", "dia-filter-amount-max"].forEach(
			function (id) {
				const el = document.querySelector('[data-testid="' + id + '"]');
				if (el) {
					el.value = "";
				}
			}
		);
		searchQuery = "";
		const se = document.querySelector('[data-testid="dia-search"]');
		if (se) {
			se.value = "";
		}
	}

	function clearOneDiaRefineField(key) {
		if (key === "search") {
			searchQuery = "";
			const se = document.querySelector('[data-testid="dia-search"]');
			if (se) {
				se.value = "";
			}
			return;
		}
		const map = {
			demand_type: "dia-filter-demand-type",
			priority_level: "dia-filter-priority",
			requisition_type: "dia-filter-requisition-type",
			status: "dia-filter-status",
			requesting_department: "dia-filter-department",
			budget_line: "dia-filter-budget-line",
			date_from: "dia-filter-date-from",
			date_to: "dia-filter-date-to",
			amount_min: "dia-filter-amount-min",
			amount_max: "dia-filter-amount-max",
		};
		const tid = map[key];
		if (!tid) {
			return;
		}
		const el = document.querySelector('[data-testid="' + tid + '"]');
		if (el) {
			el.value = "";
		}
	}

	function renderFilterChips() {
		const host = document.querySelector('[data-testid="dia-active-filter-chips"]');
		if (!host) {
			return;
		}
		const f = collectRefineFilters();
		const q = String(searchQuery || "").trim();
		const chips = [];
		function add(key, label) {
			chips.push(
				'<span class="kt-dia-chip">' +
					'<span class="kt-dia-chip__text">' +
					escapeHtml(label) +
					'</span><button type="button" class="kt-dia-chip__x" data-dia-chip-remove="' +
					escapeHtml(key) +
					'" title="' +
					escapeHtml(__("Remove")) +
					'">&times;</button></span>'
			);
		}
		if (f.demand_type) {
			add("demand_type", f.demand_type);
		}
		if (f.priority_level) {
			add("priority_level", f.priority_level);
		}
		if (f.requisition_type) {
			add("requisition_type", f.requisition_type);
		}
		if (f.status) {
			add("status", f.status);
		}
		if (f.requesting_department) {
			add("requesting_department", f.requesting_department);
		}
		if (f.budget_line) {
			add("budget_line", f.budget_line);
		}
		if (f.date_from) {
			add("date_from", f.date_from);
		}
		if (f.date_to) {
			add("date_to", f.date_to);
		}
		if ("amount_min" in f) {
			add("amount_min", String(f.amount_min));
		}
		if ("amount_max" in f) {
			add("amount_max", String(f.amount_max));
		}
		if (q) {
			chips.push(
				'<span class="kt-dia-chip">' +
					'<span class="kt-dia-chip__text">' +
					escapeHtml(__("Search")) +
					": " +
					escapeHtml(q) +
					'</span><button type="button" class="kt-dia-chip__x" data-dia-chip-remove="search" title="' +
					escapeHtml(__("Remove")) +
					'">&times;</button></span>'
			);
		}
		host.innerHTML = chips.length ? chips.join(" ") : "";
		const has = chips.length > 0;
		host.hidden = !has;
		const fbtn = document.getElementById("kt-dia-filters-toggle");
		if (fbtn) {
			fbtn.classList.toggle("is-active", has);
		}
	}

	function loadDiaQueueList() {
		const listRoot = document.getElementById("kt-dia-list-root");
		if (!listRoot || !lastRoleKey) {
			return;
		}
		diaQueueListReqId += 1;
		const myReq = diaQueueListReqId;
		listRoot.classList.remove("kt-dia-list-root--refreshing");
		listRoot.removeAttribute("aria-busy");
		const hadQueueListDom = !!listRoot.querySelector(".kt-dia-row-list");
		if (hadQueueListDom) {
			listRoot.classList.add("kt-dia-list-root--refreshing");
			listRoot.setAttribute("aria-busy", "true");
		} else {
			listRoot.innerHTML =
				'<div class="text-muted small py-3" data-testid="dia-list-loading">' +
				escapeHtml(__("Loading…")) +
				"</div>";
		}
		const search = String(searchQuery || "").trim();
		const rf = collectRefineFilters();
		const filtersJson = Object.keys(rf).length ? JSON.stringify(rf) : null;
		const api = resolveQueueApiParams();
		frappe.call({
			method: "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_list",
			args: {
				work_scope: api.work_scope,
				lifecycle_filter: api.lifecycle_filter,
				limit: 50,
				start: 0,
				search: search || null,
				filters: filtersJson,
			},
			callback: function (r) {
				if (myReq !== diaQueueListReqId) {
					return;
				}
				listRoot.classList.remove("kt-dia-list-root--refreshing");
				listRoot.removeAttribute("aria-busy");
				if (!r || !r.message) {
					return;
				}
				const p = r.message;
				if (p.ok === false) {
					renderLandingBlocked(p);
					return;
				}
				const prevSig = lastQueueListPayload ? queueListSignature(lastQueueListPayload) : "";
				const newSig = queueListSignature(p);
				const demands = (p && p.demands) || [];
				const nameSet = new Set(
					demands.map(function (row) {
						return row.name;
					})
				);
				const sel = selectedDemandName;
				if (prevSig && prevSig === newSig && sel && nameSet.has(sel)) {
					lastQueueListPayload = p;
					syncDemandListSelection(listRoot, sel);
					return;
				}
				renderDemandList(p);
				if (!selectedDemandName) {
					/* paintDetailEmpty handled inside renderDemandList when needed */
				} else if (
					!currentDetailPayload ||
					currentDetailPayload.name !== selectedDemandName ||
					diaPanelsDirty
				) {
					renderDetailForSelection();
				} else {
					syncDemandListSelection(listRoot, selectedDemandName);
				}
				saveDiaWorkbenchState();
			},
			error: function () {
				if (myReq !== diaQueueListReqId) {
					return;
				}
				listRoot.classList.remove("kt-dia-list-root--refreshing");
				listRoot.removeAttribute("aria-busy");
				if (hadQueueListDom) {
					frappe.show_alert({
						message: __("Could not refresh the list. Showing the last loaded rows."),
						indicator: "orange",
					});
					return;
				}
				listRoot.innerHTML =
					'<p class="text-danger small" data-testid="dia-list-error">' +
					escapeHtml(__("Could not load list.")) +
					"</p>";
			},
		});
	}

	function renderLandingBlocked(payload) {
		lastQueueListPayload = null;
		selectedDemandName = null;
		currentDetailPayload = null;
		const listRoot = document.getElementById("kt-dia-list-root");
		const detailRoot = document.getElementById("kt-dia-detail-root");
		const msg = (payload && payload.message) || __("Demand landing data is not available.");
		const code = (payload && payload.error_code) || "UNKNOWN";
		const hint =
			code === "DEMAND_NOT_INSTALLED"
				? __("After migrate, hard-refresh this page (Ctrl+Shift+R).")
				: code === "DIA_ACCESS_DENIED"
					? __(
							"Ask an administrator to assign a Demand Intake role (Requisitioner, HoD, Finance, Procurement, or Auditor)."
					  )
					: "";
		const migrateLine =
			code === "DEMAND_NOT_INSTALLED"
				? '<p class="mb-0 small text-muted"><code>bench --site &lt;site&gt; migrate</code></p>'
				: "";
		if (listRoot) {
			listRoot.innerHTML =
				'<div class="alert alert-warning mb-0" data-testid="dia-landing-blocked" role="status">' +
				"<strong>" +
				escapeHtml(__("Demand Intake cannot load yet")) +
				"</strong><p class=\"mb-1 small\">" +
				escapeHtml(msg) +
				"</p>" +
				(hint ? '<p class="mb-0 small text-muted">' + escapeHtml(hint) + "</p>" : "") +
				migrateLine +
				"</div>";
		}
		if (detailRoot) {
			detailRoot.innerHTML =
				'<div class="kt-dia-empty text-muted small" data-testid="dia-detail-blocked">' +
				escapeHtml(__("Fix the issue above, then reload. No demand row can be selected until the DocType exists.")) +
				"</div>";
		}
		paintPortfolioChips((payload && payload.portfolio) || {});
	}

	function applyAuditorScopeDefault() {
		if (lastRoleKey === "auditor" && !explicitQueueFilterRestored) {
			activeQueueFilter = "all";
		}
	}

	function refreshDiaPortfolio(done) {
		frappe.call({
			method: "kentender_procurement.demand_intake.api.landing.get_dia_landing_shell_data",
			callback: function (r) {
				if (r && r.message && r.message.portfolio) {
					paintPortfolioChips(r.message.portfolio);
				}
				if (typeof done === "function") {
					done(r && r.message);
				}
			},
			error: function () {
				if (typeof done === "function") {
					done(null);
				}
			},
		});
	}

	function loadDiaLandingData() {
		restoreDiaWorkbenchState();
		const listRoot = document.getElementById("kt-dia-list-root");
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!listRoot || !detailRoot) return;
		listRoot.innerHTML =
			'<div class="text-muted small py-3">' + escapeHtml(__("Loading…")) + "</div>";
		detailRoot.innerHTML = "";

		frappe.call({
			method: "kentender_procurement.demand_intake.api.landing.get_dia_landing_shell_data",
			callback: function (r) {
				if (!r || !r.message) return;
				const payload = r.message;
				lastRoleKey = payload.role_key || "requisitioner";
				applyAuditorScopeDefault();
				if (!explicitQueueFilterRestored) {
					activeQueueFilter = defaultQueueFilter(lastRoleKey);
				}
				if (payload.ok === false) {
					renderLandingBlocked(payload);
					return;
				}
				paintPortfolioChips(payload.portfolio || {});
				const searchEl = document.querySelector('[data-testid="dia-search"]');
				if (searchEl && searchQuery) {
					searchEl.value = searchQuery;
				}
				loadDiaFilterMeta(function () {
					renderFilterChips();
					loadDiaQueueList();
				});
			},
			error: function () {
				if (listRoot)
					listRoot.innerHTML =
						'<p class="text-danger small">' + escapeHtml(__("Could not load landing data.")) + "</p>";
				paintPortfolioChips({});
			},
		});
	}

	function tryBindDiaWorkspace() {
		if (!isDiaWorkspaceRoute()) return;
		const inj = injectDiaLandingShell();
		if (!inj || !inj.ok) return;
		const listRoot = document.getElementById("kt-dia-list-root");
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!listRoot || !detailRoot) return;
		if (inj.inserted) {
			restoreDiaWorkbenchState();
			if (!activeQueueFilter || !QUEUE_CHIP_IDS[activeQueueFilter]) {
				activeQueueFilter = defaultQueueFilter(lastRoleKey);
			}
			if (!activeDetailTab) activeDetailTab = "overview";
			loadDiaLandingData();
		}
	}

	function requestDiaBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindDiaWorkspace();
		}, delayMs || 0);
	}

	function scheduleDiaWorkspaceBind() {
		if (!isDiaWorkspaceRoute()) {
			removeDiaLandingIfWrongRoute();
			return;
		}
		syncDiaShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => requestDiaBind(0));
		} else {
			requestDiaBind(0);
		}
		requestDiaBind(120);
	}

	function ensureWorkspaceDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		workspaceDomObserver = new MutationObserver(function () {
			if (!isDiaWorkspaceRoute() || document.getElementById("kt-dia-list-root")) return;
			tryBindDiaWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindDiaWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleDiaWorkspaceBind);
				window.jQuery(document).on("app_ready", scheduleDiaWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleDiaWorkspaceBind);
			}
			ensureWorkspaceDomObserver();
		}
		syncDiaShellClass();
		scheduleDiaWorkspaceBind();
	}

	function ensurePollDiaWorkspace() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isDiaWorkspaceRoute()) removeDiaLandingIfWrongRoute();
			else if (!document.getElementById("kt-dia-list-root")) tryBindDiaWorkspace();
			setTimeout(tick, 400);
		}
		tick();
	}

	function kickDiaWorkspace() {
		removeStaleDiaShellIfNeeded();
		bindDiaWorkspaceHooks();
		ensurePollDiaWorkspace();
		setTimeout(scheduleDiaWorkspaceBind, 400);
	}

	function bootstrapDiaWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickDiaWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickDiaWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickDiaWorkspace);
		setTimeout(kickDiaWorkspace, 900);
	}

	bootstrapDiaWorkspace();
})();
