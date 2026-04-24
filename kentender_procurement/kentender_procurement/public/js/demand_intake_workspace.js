// Demand Intake and Approval workspace — Desk shell (D1): header, KPIs, tabs, queues, filters, master–detail.

(function () {
	const DIA_WS = "Demand Intake and Approval";
	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let activeWorkTab = "mywork";
	let activeQueueId = null;
	let lastRoleKey = null;
	let lastQueueListPayload = null;
	let selectedDemandName = null;
	let diaSearchTimer = null;
	let detailLoadSeq = 0;
	let diaQueueListReqId = 0;
	/** v3: single-row queue line + overflow; keep primary for operational queues */
	const DIA_MAX_INLINE_QUEUES = 4;

	function userCanCreateDemand() {
		return (
			typeof frappe !== "undefined" &&
			frappe.model &&
			typeof frappe.model.can_create === "function" &&
			frappe.model.can_create("Demand")
		);
	}

	function focusDiaQueueToolbar() {
		const row = document.getElementById("kt-dia-queue-selector");
		const pills = document.getElementById("kt-dia-queue-pills");
		if (row && typeof row.scrollIntoView === "function") {
			row.scrollIntoView({ block: "nearest", behavior: "smooth" });
		}
		if (!pills) {
			return;
		}
		const t =
			pills.querySelector("[data-toggle=dropdown]") || pills.querySelector("button[data-dia-queue]");
		if (t && typeof t.focus === "function") {
			t.focus();
		}
	}

	function diaQueueListScrollHost(listRoot) {
		if (!listRoot) {
			return null;
		}
		return listRoot.querySelector(".kt-dia-queue-list");
	}

	function diaReadQueueListScrollTop(listRoot) {
		const host = diaQueueListScrollHost(listRoot);
		return host && typeof host.scrollTop === "number" ? host.scrollTop : 0;
	}

	function diaRestoreQueueListScrollTop(listRoot, top, selectedName) {
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

	const TAB_APPROVED_QUEUE_IDS = {
		requisitioner: ["my_approved"],
		hod: ["all_dept", "emergency"],
		finance: ["approved_today"],
		procurement: ["planning_ready", "approved_not_planned", "emergency_approved", "all_approved"],
		admin: ["planning_ready", "approved_not_planned", "emergency_approved", "all_approved"],
		auditor: ["planning_ready", "all_approved"],
	};

	const TAB_REJECTED_QUEUE_IDS = {
		requisitioner: ["rejected", "returned_to_me"],
		hod: ["returned_await", "hod_rejected"],
		finance: ["budget_exceptions", "dia_rejected"],
		procurement: ["dia_rejected"],
		admin: ["dia_rejected"],
		auditor: ["dia_rejected"],
	};

	const QUEUES_BY_ROLE = {
		requisitioner: [
			{ id: "my_drafts", label: __("My Drafts") },
			{ id: "submitted_by_me", label: __("Submitted by Me") },
			{ id: "returned_to_me", label: __("Returned to Me") },
			{ id: "rejected", label: __("Rejected") },
			{ id: "my_approved", label: __("My Approved") },
		],
		admin: [
			{ id: "my_drafts", label: __("My Drafts") },
			{ id: "all_demands", label: __("All Demands") },
			{ id: "planning_ready", label: __("Planning Ready") },
			{ id: "approved_not_planned", label: __("Approved Not Yet Planned") },
			{ id: "emergency_approved", label: __("Emergency Approved") },
			{ id: "all_approved", label: __("All Approved Demand") },
			{ id: "dia_rejected", label: __("Rejected demands") },
		],
		hod: [
			{ id: "pending_hod", label: __("Pending HoD Approval") },
			{ id: "returned_await", label: __("Returned Awaiting Resubmission") },
			{ id: "emergency", label: __("Emergency Requests") },
			{ id: "all_dept", label: __("All Department Requests") },
			{ id: "hod_rejected", label: __("Rejected (department)") },
		],
		finance: [
			{ id: "pending_finance", label: __("Pending Finance Approval") },
			{ id: "budget_exceptions", label: __("Budget Exceptions") },
			{ id: "emergency_fin", label: __("Emergency Requests") },
			{ id: "approved_today", label: __("Approved Today") },
			{ id: "dia_rejected", label: __("Rejected demands") },
		],
		procurement: [
			{ id: "my_drafts", label: __("My Drafts") },
			{ id: "all_demands", label: __("All Demands") },
			{ id: "planning_ready", label: __("Planning Ready") },
			{ id: "approved_not_planned", label: __("Approved Not Yet Planned") },
			{ id: "emergency_approved", label: __("Emergency Approved") },
			{ id: "all_approved", label: __("All Approved Demand") },
			{ id: "dia_rejected", label: __("Rejected demands") },
		],
		auditor: [
			{ id: "all_demands", label: __("All Demands (Read-only)") },
			{ id: "pending_hod", label: __("Pending HoD Approval") },
			{ id: "pending_finance", label: __("Pending Finance Approval") },
			{ id: "planning_ready", label: __("Planning Ready") },
			{ id: "all_approved", label: __("All Approved Demand") },
			{ id: "dia_rejected", label: __("Rejected demands") },
		],
	};

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
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
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesDia(workspaceName)) return true;
					/* Another workspace is active — do not use stale URL/hash heuristics (would mount DIA on e.g. Procurement Home). */
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
		const loc = window.location;
		const path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
		if (path.includes("demand-intake-and-approval") || path.includes("demand_intake_and_approval")) {
			return true;
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
		activeQueueId = null;
		lastRoleKey = null;
		lastQueueListPayload = null;
		selectedDemandName = null;
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

	function injectDiaLandingShell() {
		if (document.getElementById("kt-dia-list-root")) {
			return { ok: true, inserted: false };
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false, inserted: false };
		const wrap = document.createElement("div");
		wrap.id = "kt-dia-root";
		wrap.className = "kt-dia-injected-shell";
		wrap.setAttribute("data-testid", "dia-landing-page");
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
			'<div class="row g-1 align-items-stretch" data-testid="dia-kpi-row">' +
			'<div class="col-6 col-lg-3"><div class="kt-dia-kpi-card kt-surface">' +
			'<div class="kt-dia-kpi-label" data-testid="dia-kpi-0-label">—</div>' +
			'<div class="kt-dia-kpi-value" data-testid="dia-kpi-0-value">—</div></div></div>' +
			'<div class="col-6 col-lg-3"><div class="kt-dia-kpi-card kt-surface">' +
			'<div class="kt-dia-kpi-label" data-testid="dia-kpi-1-label">—</div>' +
			'<div class="kt-dia-kpi-value" data-testid="dia-kpi-1-value">—</div></div></div>' +
			'<div class="col-6 col-lg-3"><div class="kt-dia-kpi-card kt-surface">' +
			'<div class="kt-dia-kpi-label" data-testid="dia-kpi-2-label">—</div>' +
			'<div class="kt-dia-kpi-value" data-testid="dia-kpi-2-value">—</div></div></div>' +
			'<div class="col-6 col-lg-3"><div class="kt-dia-kpi-card kt-surface">' +
			'<div class="kt-dia-kpi-label" data-testid="dia-kpi-3-label">—</div>' +
			'<div class="kt-dia-kpi-value" data-testid="dia-kpi-3-value">—</div></div></div>' +
			"</div>" +
			'<p class="kt-dia-kpi-currency-note text-muted" id="kt-dia-kpi-currency-note" data-testid="dia-kpi-currency-context" hidden></p>' +
			'<div class="kt-dia-control-bar" data-testid="dia-control-bar">' +
			'<div class="kt-dia-control-bar__row kt-dia-control-bar__row--tabs" data-testid="dia-control-row-tabs">' +
			'<div class="kt-dia-work-tabs" role="tablist" id="kt-dia-work-tabs" data-testid="dia-work-tabs">' +
			'<div class="btn-group btn-group-sm flex-nowrap kt-dia-tab-group" role="group">' +
			'<button type="button" class="btn btn-default kt-dia-work-tab" data-testid="dia-tab-my-work" data-kt-dia-tab="mywork" role="tab">' +
			escapeHtml(__("My Work")) +
			"</button>" +
			'<button type="button" class="btn btn-default kt-dia-work-tab" data-testid="dia-tab-all" data-kt-dia-tab="all" role="tab">' +
			escapeHtml(__("All")) +
			"</button>" +
			'<button type="button" class="btn btn-default kt-dia-work-tab" data-testid="dia-tab-approved" data-kt-dia-tab="approved" role="tab">' +
			escapeHtml(__("Approved")) +
			"</button>" +
			'<button type="button" class="btn btn-default kt-dia-work-tab" data-testid="dia-tab-rejected" data-kt-dia-tab="rejected" role="tab">' +
			escapeHtml(__("Rejected")) +
			"</button></div></div>" +
			'<div class="kt-dia-search-compact-wrap">' +
			'<div class="kt-dia-search-compact">' +
			'<label class="kt-dia-sr-only" for="kt-dia-search-input">' +
			escapeHtml(__("Search")) +
			'</label><input type="search" class="form-control form-control-sm" id="kt-dia-search-input" data-testid="dia-search-input" placeholder="' +
			escapeHtml(__("Demand ID, title, requester, department…")) +
			'" />' +
			"</div></div></div>" +
			'<div class="kt-dia-control-bar__row kt-dia-control-bar__row--queues" data-testid="dia-control-row-queues" id="kt-dia-queue-selector">' +
			'<div class="kt-dia-queue-pills" id="kt-dia-queue-pills" data-testid="dia-queue-pills"></div>' +
			'<div class="kt-dia-toolbar-queues-right">' +
			'<button type="button" class="btn btn-default btn-sm kt-dia-filters-icon-btn" data-dia-action="toggle-filters" data-testid="dia-filters-toggle" id="kt-dia-filters-toggle" aria-expanded="false" aria-controls="kt-dia-filters-popover" title="' +
			escapeHtml(__("Refine (filters)")) +
			'">' +
			'<svg class="kt-dia-filters-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M0 1.25h16v1.2H0V1.25zM2.5 6.1h11v1.2h-11V6.1zM4.5 10.8h7v1.2h-7v-1.2z" /></svg>' +
			'<span class="kt-dia-sr-only">' +
			escapeHtml(__("Refine (filters)")) +
			"</span></button>" +
			'<button type="button" class="kt-dia-scope-hint-btn" id="kt-dia-scope-hint" data-testid="dia-scope-hint" hidden="">' +
			'<span class="kt-dia-scope-hint-glyph" aria-hidden="true">' +
			"\u2139" +
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
			'<div class="kt-dia-chip-row" data-testid="dia-active-filter-chips" hidden></div></div>' +
			'<div class="kt-dia-master-detail kt-dia-master-detail--tight">' +
			'<div class="kt-dia-col-list">' +
			'<div class="kt-dia-section kt-surface">' +
			'<h3 class="kt-dia-section__title" id="kt-dia-queue-list-title" data-testid="dia-list-title">' +
			escapeHtml(__("My Drafts")) +
			"</h3>" +
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

	function closeDiaFiltersPopover() {
		const p = document.getElementById("kt-dia-filters-popover");
		const b = document.getElementById("kt-dia-root")
			? document.querySelector("#kt-dia-root [data-dia-action=\"toggle-filters\"]")
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
		if (t && t.closest && t.closest("[data-dia-action=\"toggle-filters\"]")) {
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
				if (a === "empty-new-demand" && userCanCreateDemand() && typeof frappe !== "undefined" && frappe.new_doc) {
					frappe.new_doc("Demand");
					return;
				}
				if (a === "empty-focus-queues") {
					focusDiaQueueToolbar();
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
			const demRow = ev.target.closest("[data-dia-demand]");
			if (demRow && root.contains(demRow) && demRow.getAttribute("data-dia-demand")) {
				selectedDemandName = demRow.getAttribute("data-dia-demand");
				const listRoot = document.getElementById("kt-dia-list-root");
				if (listRoot) {
					syncDemandListSelection(listRoot, selectedDemandName, {
						ensureSelectedVisible: true,
					});
				}
				loadDiaDemandDetail();
				return;
			}
			const tabBtn = ev.target.closest("button[data-kt-dia-tab]");
			if (tabBtn && root.contains(tabBtn)) {
				activeWorkTab = tabBtn.getAttribute("data-kt-dia-tab");
				syncWorkTabButtons();
				syncActiveQueueForTab(lastRoleKey || "requisitioner");
				renderQueuePills(lastRoleKey || "requisitioner");
				loadDiaQueueList();
				return;
			}
			const qBtn = ev.target.closest("[data-dia-queue]");
			if (qBtn && root.contains(qBtn)) {
				if (qBtn.tagName === "A") {
					ev.preventDefault();
				}
				const qid = qBtn.getAttribute("data-dia-queue");
				if (qid) {
					activeQueueId = qid;
					renderQueuePills(lastRoleKey || "requisitioner");
					loadDiaQueueList();
				}
				return;
			}
			const kpiCard = ev.target.closest(".kt-dia-kpi-card--clickable");
			if (kpiCard && root.contains(kpiCard)) {
				const tab = kpiCard.getAttribute("data-dia-select-tab");
				const q = kpiCard.getAttribute("data-dia-select-queue");
				if (tab) activeWorkTab = tab;
				if (q) activeQueueId = q;
				syncWorkTabButtons();
				syncActiveQueueForTab(lastRoleKey || "requisitioner");
				renderQueuePills(lastRoleKey || "requisitioner");
				loadDiaQueueList();
			}
		});
		root.addEventListener("input", function (ev) {
			const t = ev.target;
			if (!t || !t.getAttribute || t.getAttribute("data-testid") !== "dia-search-input") {
				return;
			}
			if (!root.contains(t)) {
				return;
			}
			if (diaSearchTimer) {
				clearTimeout(diaSearchTimer);
			}
			diaSearchTimer = setTimeout(function () {
				diaSearchTimer = null;
				renderFilterChips();
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
			btn.className = "btn btn-primary btn-sm";
			btn.setAttribute("data-testid", "dia-new-demand-button");
			btn.textContent = __("New Demand");
			btn.addEventListener("click", function () {
				frappe.new_doc("Demand");
			});
			slot.appendChild(btn);
		}
	}

	function formatKpiValue(row, _currency) {
		if (!row) return "—";
		if (row.format === "currency") {
			const v = Number(row.value);
			if (Number.isNaN(v)) return "—";
			try {
				return Math.round(v).toLocaleString("en-US", {
					minimumFractionDigits: 0,
					maximumFractionDigits: 0,
				});
			} catch (e) {
				return String(v);
			}
		}
		return String(row.value != null ? row.value : "0");
	}

	function applyKpis(payload) {
		const kpis = (payload && payload.kpis) || [];
		const currency = (payload && payload.currency) || "KES";
		const rowWrap = document.querySelector('[data-testid="dia-kpi-row"]');
		const curNote = document.getElementById("kt-dia-kpi-currency-note");
		if (curNote) {
			const hasCurrency = kpis.some(function (k) {
				return k && k.format === "currency";
			});
			if (hasCurrency) {
				curNote.textContent = __("All monetary figures in {0}").replace("{0}", currency);
				curNote.hidden = false;
			} else {
				curNote.textContent = "";
				curNote.hidden = true;
			}
		}
		const cards = rowWrap ? rowWrap.querySelectorAll(".kt-dia-kpi-card") : [];
		for (let i = 0; i < 4; i++) {
			const row = kpis[i];
			const lb = document.querySelector('[data-testid="dia-kpi-' + i + '-label"]');
			const vl = document.querySelector('[data-testid="dia-kpi-' + i + '-value"]');
			if (lb) lb.textContent = row && row.label ? String(row.label) : "—";
			if (vl) vl.textContent = row ? formatKpiValue(row, currency) : "—";
			const card = cards[i];
			if (card) {
				card.removeAttribute("data-testid");
				if (row && row.testid) {
					card.setAttribute("data-testid", String(row.testid));
				}
				card.classList.remove("kt-dia-kpi-card--clickable");
				card.removeAttribute("data-dia-select-queue");
				card.removeAttribute("data-dia-select-tab");
				card.removeAttribute("role");
				card.removeAttribute("tabindex");
				card.removeAttribute("title");
				if (row && (row.select_queue_id || row.select_work_tab)) {
					card.classList.add("kt-dia-kpi-card--clickable");
					if (row.select_queue_id) card.setAttribute("data-dia-select-queue", row.select_queue_id);
					if (row.select_work_tab) card.setAttribute("data-dia-select-tab", row.select_work_tab);
					card.setAttribute("role", "button");
					card.setAttribute("tabindex", "0");
					card.setAttribute("title", __("Open this queue in the list below."));
				}
			}
		}
	}

	function queueLabel(roleKey, queueId) {
		const list = QUEUES_BY_ROLE[roleKey] || QUEUES_BY_ROLE.requisitioner;
		const hit = list.find(function (q) {
			return q.id === queueId;
		});
		return hit ? hit.label : list[0].label;
	}

	function queuesVisibleForTab(roleKey, tab) {
		const base = QUEUES_BY_ROLE[roleKey] || QUEUES_BY_ROLE.requisitioner;
		if (tab === "mywork" || tab === "all") {
			return base;
		}
		if (tab === "approved") {
			const ids = TAB_APPROVED_QUEUE_IDS[roleKey];
			if (!ids || !ids.length) {
				return base;
			}
			return base.filter(function (q) {
				return ids.indexOf(q.id) !== -1;
			});
		}
		if (tab === "rejected") {
			const ids = TAB_REJECTED_QUEUE_IDS[roleKey];
			if (!ids || !ids.length) {
				return base;
			}
			return base.filter(function (q) {
				return ids.indexOf(q.id) !== -1;
			});
		}
		return base;
	}

	function syncActiveQueueForTab(roleKey) {
		const list = queuesVisibleForTab(roleKey, activeWorkTab);
		if (!list.length) {
			return;
		}
		if (!activeQueueId || !list.some(function (q) { return q.id === activeQueueId; })) {
			activeQueueId = list[0].id;
		}
	}

	function updateDiaScopeHint() {
		const el = document.getElementById("kt-dia-scope-hint");
		if (!el) {
			return;
		}
		if (!lastRoleKey) {
			el.removeAttribute("title");
			el.setAttribute("aria-label", "");
			el.hidden = true;
			return;
		}
		const rk = lastRoleKey;
		const tab = activeWorkTab;
		const q = activeQueueId || "";
		let msg = "";
		if (tab === "mywork") {
			msg = __("My Work shows drafts, submissions, returns, rejections, and approvals tied to you.");
		} else if (tab === "all") {
			msg = __("All shows every queue for your role (not limited to your own requests).");
		} else if (tab === "approved") {
			if (rk === "procurement" || rk === "admin" || rk === "auditor") {
				if (q === "emergency_approved") {
					msg = __(
						"Emergency Approved: demands marked Emergency that are already Approved or Planning ready (not rejected)."
					);
				} else if (q === "planning_ready") {
					msg = __("Planning Ready: demands with status Planning ready.");
				} else if (q === "approved_not_planned") {
					msg = __("Approved Not Yet Planned: Approved demands still awaiting full planning.");
				} else if (q === "all_approved") {
					msg = __("All Approved Demand: Approved or Planning ready in one list.");
				} else {
					msg = __("Approved tab: post-approval / planning queues only.");
				}
			} else if (rk === "finance") {
				msg = __("Approved tab: finance-approved views (e.g. approved today).");
			} else if (rk === "hod") {
				msg = __("Approved tab: department demands that are already approved or planning-ready.");
			} else {
				msg = __("Approved tab: your approved or planning-ready demands.");
			}
		} else if (tab === "rejected") {
			if (rk === "procurement" || rk === "admin" || rk === "auditor") {
				msg = __(
					"Rejected tab: only demands with workflow status Rejected. “Emergency Approved” lives under the Approved tab."
				);
			} else if (rk === "finance") {
				if (q === "budget_exceptions") {
					msg = __("Budget Exceptions: budget reservation checks that failed (not necessarily status Rejected).");
				} else {
					msg = __("Rejected demands: workflow status Rejected at finance.");
				}
			} else if (rk === "hod") {
				if (q === "returned_await") {
					msg = __("Returned: Draft demands sent back for correction (return reason set).");
				} else {
					msg = __("Rejected (department): demands with status Rejected in your scope.");
				}
			} else {
				msg = __("Rejected / returned queues for your role.");
			}
		}
		if (!msg) {
			el.removeAttribute("title");
			el.setAttribute("aria-label", "");
			el.hidden = true;
			return;
		}
		el.setAttribute("title", msg);
		el.setAttribute("aria-label", msg);
		el.hidden = false;
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

	/** Main queue list: numbers only; currency is in the KPI “All monetary figures in …” line (Layout spec). */
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

	function diaStatusBadgeClass(status) {
		const s = (status || "").toLowerCase();
		if (s.indexOf("draft") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-draft";
		}
		if (s.indexOf("pending") >= 0 && s.indexOf("hod") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-pending-hod";
		}
		if (s.indexOf("pending") >= 0 && s.indexOf("finance") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-pending-fin";
		}
		if (s.indexOf("approved") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-approved";
		}
		if (s.indexOf("planning ready") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-planning";
		}
		if (s.indexOf("reject") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-rejected";
		}
		if (s.indexOf("cancel") >= 0) {
			return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-cancelled";
		}
		return "kt-dia-badge kt-dia-badge--status kt-dia-badge--st-neutral";
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

	function buildDiaListSecondaryLine(row, roleKey) {
		const parts = [];
		const who = row.requested_by_label || row.requested_by;
		if (who) {
			parts.push("<span>" + escapeHtml(who) + "</span>");
		}
		if (row.budget_line_label) {
			parts.push(
				"<span>" +
					escapeHtml(__("Budget line")) +
					": " +
					escapeHtml(row.budget_line_label) +
					"</span>"
			);
		}
		const rs = row.reservation_status;
		const showRes =
			rs &&
			(roleKey === "finance" ||
				roleKey === "admin" ||
				roleKey === "procurement" ||
				roleKey === "auditor" ||
				String(rs).toLowerCase().indexOf("fail") >= 0);
		if (showRes) {
			parts.push(
				"<span>" + escapeHtml(__("Reservation")) + ": " + escapeHtml(String(rs)) + "</span>"
			);
		}
		if (row.is_exception) {
			parts.push('<span class="kt-dia-queue-item__flag">' + escapeHtml(__("Exception")) + "</span>");
		}
		if (!parts.length) {
			return "";
		}
		const sep = ' <span class="kt-dia-queue-item__dot" aria-hidden="true">·</span> ';
		return '<div class="kt-dia-queue-item__secondary">' + parts.join(sep) + "</div>";
	}

	function paintDetailEmpty() {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		detailRoot.innerHTML =
			'<div class="kt-dia-empty" data-testid="dia-detail-empty">' +
			"<p>" +
			escapeHtml(__("Select a demand record to view details and take action.")) +
			"</p>" +
			'<p class="small text-muted mb-0">' +
			escapeHtml(__("Choose a row in the queue list to load summary sections A–F.")) +
			"</p>" +
			"</div>";
	}

	function diaDetailDash(v) {
		if (v === null || v === undefined || v === "") {
			return "—";
		}
		return escapeHtml(String(v));
	}

	function diaDetailSection(title, body, testId) {
		return (
			'<section class="kt-dia-detail__section" data-testid="' +
			testId +
			'">' +
			'<h4 class="kt-dia-detail__heading">' +
			escapeHtml(title) +
			"</h4>" +
			body +
			"</section>"
		);
	}

	function diaDetailDlRow(label, valueHtml, ddTestId) {
		const tid = ddTestId ? ' data-testid="' + escapeHtml(ddTestId) + '"' : "";
		return "<dt>" + escapeHtml(label) + "</dt><dd" + tid + ">" + valueHtml + "</dd>";
	}

	function diaDemandIdRowSlug(demandId) {
		return String(demandId || "row").replace(/[^a-zA-Z0-9_-]/g, "-");
	}

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
	};

	function buildDiaDetailActionsHtml(actions, nm) {
		if (!actions || !actions.length) {
			return '<p class="text-muted small mb-0">' + escapeHtml(__("No actions.")) + "</p>";
		}
		let h = '<div class="kt-dia-detail__actions btn-toolbar flex-wrap mb-1">';
		for (let i = 0; i < actions.length; i++) {
			const a = actions[i];
			const base =
				"btn btn-sm " +
				(a.danger ? "btn-danger" : a.primary ? "btn-primary" : "btn-default");
			const tid =
				a.client_action === "open_form"
					? DIA_LANDING_ACTION_TESTID.open_form
					: DIA_LANDING_ACTION_TESTID[a.id] || "dia-detail-action-" + escapeHtml(a.id);
			if (a.client_action === "open_form") {
				h +=
					'<button type="button" class="' +
					base +
					'" data-dia-detail-action="open_form" data-dia-detail-name="' +
					escapeHtml(nm) +
					'" data-testid="' +
					escapeHtml(tid) +
					'">' +
					escapeHtml(a.label || "") +
					"</button>";
			} else {
				h +=
					'<button type="button" class="' +
					base +
					'" data-dia-detail-action="' +
					escapeHtml(a.id) +
					'" data-dia-detail-method="' +
					escapeHtml(a.method || "") +
					'" data-dia-detail-reason="' +
					escapeHtml(a.reason || "") +
					'" data-dia-detail-name="' +
					escapeHtml(nm) +
					'" data-testid="' +
					escapeHtml(tid) +
					'">' +
					escapeHtml(a.label || "") +
					"</button>";
			}
		}
		h += "</div>";
		return h;
	}

	function runDiaDetailPanelAction(btn) {
		const action = btn.getAttribute("data-dia-detail-action");
		const nm = btn.getAttribute("data-dia-detail-name");
		if (!nm || !action) {
			return;
		}
		if (action === "open_form") {
			if (typeof frappe !== "undefined" && frappe.set_route) {
				frappe.set_route("Form", "Demand", nm);
			}
			return;
		}
		const method = btn.getAttribute("data-dia-detail-method");
		const reasonKind = (btn.getAttribute("data-dia-detail-reason") || "").trim();
		if (!method) {
			return;
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
					loadDiaQueueList();
					loadDiaDemandDetail();
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

	function buildDiaDetailItemsHtml(cur, dblock) {
		const rows = (dblock && dblock.rows) || [];
		const cnt = (dblock && dblock.line_count) || rows.length;
		if (!rows.length) {
			return (
				'<div data-testid="dia-detail-items-summary"><p class="text-muted small mb-0">' +
				escapeHtml(__("No line items on this demand.")) +
				"</p></div>"
			);
		}
		let h =
			'<p class="small text-muted mb-1">' +
			escapeHtml(__("Lines")) +
			": " +
			escapeHtml(String(cnt)) +
			"</p>";
		h += '<div class="table-responsive"><table class="table table-sm table-bordered kt-dia-detail-items mb-0">';
		h +=
			"<thead><tr>" +
			"<th>" +
			escapeHtml(__("Description")) +
			"</th><th>" +
			escapeHtml(__("Category")) +
			"</th><th>" +
			escapeHtml(__("UOM")) +
			'</th><th class="text-end">' +
			escapeHtml(__("Qty")) +
			'</th><th class="text-end">' +
			escapeHtml(__("Unit cost")) +
			'</th><th class="text-end">' +
			escapeHtml(__("Line total")) +
			"</th></tr></thead><tbody>";
		for (let i = 0; i < rows.length; i++) {
			const r = rows[i];
			h +=
				"<tr><td>" +
				diaDetailDash(r.item_description) +
				"</td><td>" +
				diaDetailDash(r.category) +
				"</td><td>" +
				diaDetailDash(r.uom) +
				'</td><td class="text-end">' +
				diaDetailDash(r.quantity) +
				'</td><td class="text-end">' +
				escapeHtml(formatListMoney(r.estimated_unit_cost, cur)) +
				'</td><td class="text-end">' +
				escapeHtml(formatListMoney(r.line_total, cur)) +
				"</td></tr>";
		}
		h += "</tbody></table></div>";
		return '<div data-testid="dia-detail-items-summary">' + h + "</div>";
	}

	function buildDiaDetailPanelHtml(payload) {
		const cur = payload.currency || "KES";
		const a = payload.a || {};
		const b = payload.b || {};
		const c = payload.c || {};
		const dblock = payload.d || {};
		const e = payload.e || {};
		const nm = payload.name || "";

		const priC = diaPriorityBadgeClass(a.priority_level);
		const stC = diaStatusBadgeClass(a.status);
		const dtC = diaDemandTypeBadgeClass(a.demand_type);
		const badges =
			(a.priority_level
				? '<span data-testid="dia-detail-priority" class="' + priC + '">' + escapeHtml(a.priority_level) + "</span> "
				: "") +
			(a.status
				? '<span data-testid="dia-detail-status" class="' + stC + '">' + escapeHtml(a.status) + "</span> "
				: "") +
			(a.demand_type
				? '<span data-testid="dia-detail-demand-type" class="' + dtC + '">' + escapeHtml(a.demand_type) + "</span>"
				: "");

		const aBody =
			'<div class="kt-dia-detail__badges mb-2">' +
			badges +
			"</div>" +
			'<h3 class="kt-dia-detail__title" data-testid="dia-detail-title">' +
			diaDetailDash(a.title) +
			"</h3>" +
			'<p class="text-muted small mb-2">' +
			escapeHtml(__("Demand ID")) +
			": " +
			'<span class="font-monospace">' +
			diaDetailDash(a.demand_id) +
			"</span></p>" +
			'<dl class="kt-dia-detail__dl">' +
			diaDetailDlRow(
				__("Department"),
				diaDetailDash(a.requesting_department_label || a.requesting_department)
			) +
			diaDetailDlRow(__("Requester"), diaDetailDash(a.requested_by_label || a.requested_by)) +
			diaDetailDlRow(
				__("Entity"),
				diaDetailDash(a.procuring_entity_label || a.procuring_entity)
			) +
			diaDetailDlRow(__("Demand category"), diaDetailDash(a.requisition_type)) +
			diaDetailDlRow(__("Request date"), diaDetailDash(a.request_date)) +
			diaDetailDlRow(__("Required by"), diaDetailDash(a.required_by_date)) +
			"</dl>";

		const bBody =
			'<dl class="kt-dia-detail__dl">' +
			diaDetailDlRow(__("Budget line"), diaDetailDash(b.budget_line_label || b.budget_line), "dia-detail-budget-line") +
			diaDetailDlRow(__("Budget"), diaDetailDash(b.budget_label || b.budget)) +
			diaDetailDlRow(
				__("Funding source"),
				diaDetailDash(b.funding_source_label || b.funding_source)
			) +
			diaDetailDlRow(__("Reservation status"), diaDetailDash(b.reservation_status), "dia-detail-reservation-status") +
			diaDetailDlRow(
				__("Strategic plan"),
				diaDetailDash(b.strategic_plan_label || b.strategic_plan),
				"dia-detail-strategy"
			) +
			diaDetailDlRow(__("Program"), diaDetailDash(b.program_label || b.program)) +
			diaDetailDlRow(__("Sub-program"), diaDetailDash(b.sub_program_label || b.sub_program)) +
			diaDetailDlRow(
				__("Output indicator"),
				diaDetailDash(b.output_indicator_label || b.output_indicator)
			) +
			diaDetailDlRow(
				__("Performance target"),
				diaDetailDash(b.performance_target_label || b.performance_target)
			) +
			"</dl>";

		const amtStr = formatListMoney(c.total_amount, cur);
		const snap =
			c.available_budget_at_check != null
				? escapeHtml(formatListMoney(c.available_budget_at_check, cur))
				: "—";
		const cBody =
			'<dl class="kt-dia-detail__dl">' +
			diaDetailDlRow(
				__("Total requested"),
				'<strong class="kt-dia-detail__amount" data-testid="dia-detail-total-amount">' + escapeHtml(amtStr) + "</strong>"
			) +
			diaDetailDlRow(__("Available budget snapshot"), snap) +
			diaDetailDlRow(
				__("Reservation ref"),
				diaDetailDash(c.reservation_reference),
				"dia-detail-reservation-reference"
			) +
			diaDetailDlRow(__("Budget check time"), diaDetailDash(c.budget_check_datetime)) +
			"</dl>";

		const rejParts = [];
		if (e.rejection_reason) {
			rejParts.push(
				'<p class="small mb-1"><strong>' +
					escapeHtml(__("Rejection")) +
					"</strong> — " +
					diaDetailDash(e.rejection_reason) +
					"</p>"
			);
		}
		if (e.return_reason) {
			rejParts.push(
				'<p class="small mb-1"><strong>' +
					escapeHtml(__("Return to draft")) +
					"</strong> — " +
					diaDetailDash(e.return_reason) +
					"</p>"
			);
		}
		if (e.cancellation_reason) {
			rejParts.push(
				'<p class="small mb-1"><strong>' +
					escapeHtml(__("Cancellation")) +
					"</strong> — " +
					diaDetailDash(e.cancellation_reason) +
					"</p>"
			);
		}
		let eBody = "";
		if (e.is_exception) {
			eBody +=
				'<p class="small kt-dia-detail__exception mb-2"><strong>' +
				escapeHtml(__("Exception demand")) +
				"</strong></p>";
		}
		eBody +=
			'<dl class="kt-dia-detail__dl">' +
			diaDetailDlRow(__("Current stage"), diaDetailDash(e.current_stage)) +
			diaDetailDlRow(__("Planning status"), diaDetailDash(e.planning_status), "dia-detail-planning-status") +
			diaDetailDlRow(__("Submitted by"), diaDetailDash(e.submitted_by_label || e.submitted_by)) +
			diaDetailDlRow(__("Submitted at"), diaDetailDash(e.submitted_at)) +
			diaDetailDlRow(
				__("HoD approved by"),
				diaDetailDash(e.hod_approved_by_label || e.hod_approved_by)
			) +
			diaDetailDlRow(__("HoD approved at"), diaDetailDash(e.hod_approved_at)) +
			diaDetailDlRow(
				__("Finance approved by"),
				diaDetailDash(e.finance_approved_by_label || e.finance_approved_by)
			) +
			diaDetailDlRow(__("Finance approved at"), diaDetailDash(e.finance_approved_at)) +
			diaDetailDlRow(__("Rejected by"), diaDetailDash(e.rejected_by_label || e.rejected_by)) +
			diaDetailDlRow(__("Rejected at"), diaDetailDash(e.rejected_at)) +
			diaDetailDlRow(__("Returned by"), diaDetailDash(e.returned_by_label || e.returned_by)) +
			diaDetailDlRow(__("Returned at"), diaDetailDash(e.returned_at)) +
			diaDetailDlRow(__("Cancelled by"), diaDetailDash(e.cancelled_by_label || e.cancelled_by)) +
			diaDetailDlRow(__("Cancelled at"), diaDetailDash(e.cancelled_at)) +
			"</dl>";
		const rejBlock = rejParts.join("");
		if (rejBlock) {
			eBody += '<div data-testid="dia-detail-rejection-summary">' + rejBlock + "</div>";
		}

		const dBody = buildDiaDetailItemsHtml(cur, dblock);

		const act = payload.actions || [];
		const fBody = buildDiaDetailActionsHtml(act, nm);
		const fTop = diaDetailSection(__("Actions"), fBody, "dia-detail-section-f");

		return (
			'<div class="kt-dia-detail" data-testid="dia-detail-panel" data-dia-detail-for="' +
			escapeHtml(nm) +
			'">' +
			fTop +
			diaDetailSection(__("A. Demand summary"), aBody, "dia-detail-section-a") +
			diaDetailSection(__("B. Budget and strategy"), bBody, "dia-detail-section-b") +
			diaDetailSection(__("C. Financial summary"), cBody, "dia-detail-section-c") +
			diaDetailSection(__("D. Items summary"), dBody, "dia-detail-section-d") +
			diaDetailSection(__("E. Workflow and audit"), eBody, "dia-detail-section-e") +
			"</div>"
		);
	}

	function paintDetailError(msg) {
		const detailRoot = document.getElementById("kt-dia-detail-root");
		if (!detailRoot) {
			return;
		}
		const m =
			msg && (msg.message || msg.error_code)
				? String(msg.message || msg.error_code)
				: __("Could not load demand details.");
		detailRoot.innerHTML =
			'<div class="kt-dia-detail kt-dia-detail--error" data-testid="dia-detail-error"><p class="text-danger small mb-0">' +
			escapeHtml(m) +
			"</p></div>";
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
		detailLoadSeq += 1;
		const mySeq = detailLoadSeq;
		const existingPanel = detailRoot.querySelector(".kt-dia-detail[data-dia-detail-for]");
		const keepVisibleDetail =
			existingPanel &&
			existingPanel.getAttribute("data-dia-detail-for") === selectedDemandName;
		if (!keepVisibleDetail) {
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
				detailRoot.innerHTML = buildDiaDetailPanelHtml(resp);
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
			const names = new Set(rows.map(function (r) { return r.name; }));
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
				__("This queue is empty.");
			const canC = userCanCreateDemand();
			const newBtn = canC
				? '<button type="button" class="btn btn-primary btn-sm" data-dia-action="empty-new-demand" data-testid="dia-empty-cta-new">' +
					escapeHtml(__("Create new demand")) +
					"</button>"
				: "";
			const switchBtn =
				'<button type="button" class="btn btn-default btn-sm" data-dia-action="empty-focus-queues" data-testid="dia-empty-cta-queues">' +
				escapeHtml(__("Switch queue")) +
				"</button>";
			const actions = '<div class="kt-dia-empty__actions mt-2 d-flex flex-wrap gap-2 justify-content-center align-items-center">' + newBtn + switchBtn + "</div>";
			listRoot.innerHTML =
				'<div class="kt-dia-empty kt-dia-empty--v3" data-testid="dia-list-empty">' +
				'<p class="mb-0 text-center">' +
				escapeHtml(cap) +
				"</p>" +
				actions +
				"</div>";
			return;
		}
		const roleKey = (payload && payload.role_key) || lastRoleKey || "requisitioner";
		let html =
			'<div class="kt-dia-queue-list" data-testid="dia-list" role="listbox" aria-label="' +
			escapeHtml(__("Demand queue")) +
			'">';
		for (let i = 0; i < rows.length; i++) {
			const row = rows[i];
			const isSel = row.name === selectedDemandName;
			const active = isSel ? " is-active" : "";
			const accent = diaDemandRowAccentClass(row.demand_type);
			const exc = row.is_exception ? " kt-dia-queue-item--exception" : "";
			const amt = formatDiaQueueListAmount(row.total_amount);
			const did = row.demand_id || row.name || "";
			const ttl = row.title || "";
			const dept = row.requesting_department_label || row.requesting_department || "";
			const due = formatDiaListDatePlain(row.required_by_date);
			const dueLabel = due
				? escapeHtml(__("Required")) + ": " + escapeHtml(due)
				: escapeHtml(__("Required")) + ": —";
			const sec = buildDiaListSecondaryLine(row, roleKey);
			const priC = diaPriorityBadgeClass(row.priority_level);
			const stC = diaStatusBadgeClass(row.status);
			const dtC = diaDemandTypeBadgeClass(row.demand_type);
			const rowTestSlug = diaDemandIdRowSlug(did);
			const priB = row.priority_level
				? '<span class="' + priC + '">' + escapeHtml(row.priority_level) + "</span>"
				: "";
			const stB = row.status
				? '<span data-testid="dia-row-status-' +
					escapeHtml(rowTestSlug) +
					'" class="' +
					stC +
					'">' +
					escapeHtml(row.status) +
					"</span>"
				: "";
			const dtB = row.demand_type
				? '<span data-testid="dia-row-type-' +
					escapeHtml(rowTestSlug) +
					'" class="' +
					dtC +
					'">' +
					escapeHtml(row.demand_type) +
					"</span>"
				: "";
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
				(dept
					? '<div class="kt-dia-queue-item__dept text-muted">' + escapeHtml(dept) + "</div>"
					: "") +
				'<div class="kt-dia-queue-item__badges">' +
				priB +
				stB +
				dtB +
				"</div>" +
				'<div class="kt-dia-queue-item__amount-row">' +
				'<span class="kt-dia-queue-item__amount" data-testid="dia-row-amount-' +
				escapeHtml(rowTestSlug) +
				'">' +
				escapeHtml(amt) +
				"</span>" +
				'<span class="kt-dia-queue-item__due text-muted small">' +
				dueLabel +
				"</span>" +
				"</div>" +
				sec +
				"</div>";
		}
		html += "</div>";
		listRoot.innerHTML = html;
		// Full list DOM rebuild resets scroll; restore after paint (see diaRestoreQueueListScrollTop).
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
		const se = document.querySelector('[data-testid="dia-search-input"]');
		if (se) {
			se.value = "";
		}
	}

	function clearOneDiaRefineField(key) {
		if (key === "search") {
			const se = document.querySelector('[data-testid="dia-search-input"]');
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
		const se = document.querySelector('[data-testid="dia-search-input"]');
		const q = se && se.value ? String(se.value).trim() : "";
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
		const visible = queuesVisibleForTab(lastRoleKey, activeWorkTab);
		if (!visible.length) {
			listRoot.innerHTML =
				'<div class="kt-dia-empty text-muted small" data-testid="dia-list-no-queues">' +
				escapeHtml(__("No queues match this tab for your role.")) +
				"</div>";
			renderDetailForSelection();
			return;
		}
		const hadQueueListDom = !!listRoot.querySelector(".kt-dia-queue-list");
		if (hadQueueListDom) {
			listRoot.classList.add("kt-dia-list-root--refreshing");
			listRoot.setAttribute("aria-busy", "true");
		} else {
			listRoot.innerHTML =
				'<div class="text-muted small py-3" data-testid="dia-list-loading">' +
				escapeHtml(__("Loading…")) +
				"</div>";
		}
		const searchEl = document.querySelector('[data-testid="dia-search-input"]');
		const search = searchEl && searchEl.value ? String(searchEl.value).trim() : "";
		const rf = collectRefineFilters();
		const filtersJson = Object.keys(rf).length ? JSON.stringify(rf) : null;
		frappe.call({
			method: "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_list",
			args: {
				work_tab: activeWorkTab,
				queue_id: activeQueueId,
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
				const nameSet = new Set(demands.map(function (row) { return row.name; }));
				const sel = selectedDemandName;
				if (
					prevSig &&
					prevSig === newSig &&
					sel &&
					nameSet.has(sel)
				) {
					lastQueueListPayload = p;
					syncDemandListSelection(listRoot, sel);
					renderDetailForSelection();
					return;
				}
				renderDemandList(p);
				renderDetailForSelection();
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

	function renderQueuePills(roleKey) {
		const host = document.getElementById("kt-dia-queue-pills");
		if (!host) return;
		const list = queuesVisibleForTab(roleKey, activeWorkTab);
		if (!list.length) {
			host.innerHTML =
				'<span class="text-muted small">' + escapeHtml(__("No queues for this tab.")) + "</span>";
			const titleEl = document.getElementById("kt-dia-queue-list-title");
			if (titleEl) {
				titleEl.textContent = __("Demand list");
			}
			updateDiaScopeHint();
			return;
		}
		if (!activeQueueId || !list.some(function (q) { return q.id === activeQueueId; })) {
			activeQueueId = list[0].id;
		}
		const inline = list.slice(0, DIA_MAX_INLINE_QUEUES);
		const overflow = list.slice(DIA_MAX_INLINE_QUEUES);
		const parts = inline.map(function (q) {
			const cls =
				"btn btn-sm kt-dia-queue-pill " + (q.id === activeQueueId ? "btn-primary is-active" : "btn-default");
			return (
				'<button type="button" class="' +
				cls +
				'" data-dia-queue="' +
				escapeHtml(q.id) +
				'" data-testid="dia-queue-' +
				escapeHtml(q.id) +
				'">' +
				escapeHtml(String(q.label)) +
				"</button>"
			);
		});
		if (overflow.length) {
			const moreOn = overflow.some(function (q) { return q.id === activeQueueId; });
			const moreItems = overflow
				.map(function (q) {
					const on = q.id === activeQueueId;
					return (
						'<li><button type="button" class="kt-dia-queue-more__item' +
						(on ? " is-active" : "") +
						'" data-dia-queue="' +
						escapeHtml(q.id) +
						'" data-testid="dia-queue-' +
						escapeHtml(q.id) +
						'" role="menuitem">' +
						escapeHtml(String(q.label)) +
						"</button></li>"
					);
				})
				.join("");
			parts.push(
				'<div class="btn-group kt-dia-queue-more' +
				(moreOn ? " kt-dia-queue-more--open" : "") +
				'">' +
				'<button type="button" class="btn btn-sm btn-default dropdown-toggle' +
				(moreOn ? " is-active" : "") +
				'" data-toggle="dropdown" data-testid="dia-queue-more-toggle" aria-haspopup="true" aria-expanded="false" aria-label="' +
				escapeHtml(__("More queues")) +
				'">' +
				escapeHtml(__("More")) +
				' <span class="caret"></span></button>' +
				'<ul class="dropdown-menu kt-dia-queue-more__menu" role="menu">' +
				moreItems +
				"</ul></div>"
			);
		}
		host.innerHTML = parts.join("");
		const titleEl = document.getElementById("kt-dia-queue-list-title");
		if (titleEl) titleEl.textContent = String(queueLabel(roleKey, activeQueueId));
		updateDiaScopeHint();
	}

	function syncWorkTabButtons() {
		const wrap = document.getElementById("kt-dia-work-tabs");
		if (!wrap) return;
		wrap.querySelectorAll("[data-kt-dia-tab]").forEach(function (btn) {
			const t = btn.getAttribute("data-kt-dia-tab");
			const on = t === activeWorkTab;
			btn.classList.remove("btn-primary");
			btn.classList.add("btn", "btn-default", "kt-dia-work-tab");
			btn.classList.toggle("kt-dia-work-tab--active", on);
			btn.setAttribute("aria-selected", on ? "true" : "false");
		});
	}

	function renderLandingBlocked(payload) {
		lastQueueListPayload = null;
		selectedDemandName = null;
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
		applyKpis({ kpis: [] });
	}

	function loadDiaLandingData() {
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
				if (payload.ok === false) {
					lastRoleKey = payload.role_key || "requisitioner";
					renderQueuePills(lastRoleKey);
					renderLandingBlocked(payload);
					return;
				}
				lastRoleKey = payload.role_key || "requisitioner";
				if (lastRoleKey === "auditor" && activeWorkTab === "mywork") {
					activeWorkTab = "all";
				}
				applyKpis(payload);
				loadDiaFilterMeta(function () {
					renderQueuePills(lastRoleKey);
					renderFilterChips();
					loadDiaQueueList();
				});
			},
			error: function () {
				if (listRoot)
					listRoot.innerHTML =
						'<p class="text-danger small">' + escapeHtml(__("Could not load landing data.")) + "</p>";
				applyKpis({ kpis: [] });
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
			activeWorkTab = "mywork";
			activeQueueId = null;
			syncWorkTabButtons();
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
