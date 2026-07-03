/** PP2 P5-001 — Procurement Planning nested surfaces inside main Procurement shell. */
(function () {
	const WORKSPACE_NAME = "Procurement Planning";
	const ROOT_PATH = "/desk/procurement-planning";
	const RIGHT_PANEL_STATE_KEY = "kt-pp2-right-panel-collapsed";
	let sidebarObserver = null;
	let sidebarRefreshQueued = false;
	let bootRetryTimer = null;
	let bootRunToken = 0;
	let sidebarFastpathPatched = false;
	let sidebarLookupPatched = false;
	let sidebarSetupListenerBound = false;

	const SURFACE_LABELS = {
		"": __("Planning Workbench"),
		plans: __("Planning Workbench"),
		releases: __("Planning Workbench"),
	};

	const SURFACES = {
		"": {
			testId: "pp4-workbench",
			title: __("Planning Workbench"),
			subtitle: __("Planning Workbench"),
		},
		"package-detail": {
			testId: "pp3-package-detail-surface",
			title: __("Procurement Planning"),
			subtitle: __("Package Detail"),
		},
	};
	const APPROVED_DEMANDS_QUEUE_API =
		"kentender_procurement.procurement_planning.api.approved_demands.get_pp_approved_demands_awaiting_planning";
	const APPROVED_DEMANDS_DRAWER_API =
		"kentender_procurement.procurement_planning.api.approved_demands.get_pp_approved_demand_planning_drawer";
	const ACTIVE_PLAN_API =
		"kentender_procurement.procurement_planning.api.active_plan.get_pp_active_plan_view_model";
	const CREATE_PACKAGE_DRAWER_API =
		"kentender_procurement.procurement_planning.api.planning_inclusion.get_pp_create_package_modal_drawer";
	const PP_LANDING_SHELL_API =
		"kentender_procurement.procurement_planning.api.landing.get_pp_landing_shell_data";
	const WORKBENCH_QUEUE_COUNTS_API =
		"kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts";
	const WORKBENCH_ITEM_VIEW_MODEL_API =
		"kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model";
	const WORKBENCH_QUEUE_BY_UI_QUEUE = {
		needs_planning: true,
		draft_packages: true,
		needs_review: true,
		ready_to_release: true,
		blocked: true,
		recently_released: true,
	};
	const approvedDemandFetchTokens = new WeakMap();
	const approvedDemandSummaryTokens = new WeakMap();
	const pp4PackageFetchTokens = new WeakMap();
	const pp4KpiPayloadByRoot = new WeakMap();
	const pp4QueueCountsByRoot = new WeakMap();
	const pp4MountSignatureByRoot = new WeakMap();
	const pp4PackageItemsByRoot = new WeakMap();
	const pp4QueueItemsByRoot = new WeakMap();
	const pp4SearchTermByRoot = new WeakMap();
	const pp4SortModeByRoot = new WeakMap();
	const pp4SortMenuOpenByRoot = new WeakMap();
	const pp4FilterDrawerOpenByRoot = new WeakMap();
	const pp4FilterDraftByRoot = new WeakMap();
	const pp4FilterAppliedByRoot = new WeakMap();
	const PP4_TAB_TO_QUEUE = {
		"all-packages": "all-packages",
		"in-creation": "draft_packages",
		"awaiting-review": "needs_review",
		"ready-for-release": "ready_release",
	};
	const PP4_ALL_PACKAGES_QUEUES = ["draft_packages", "needs_review", "ready_release"];
	const PP4_SORT_MODES = [
		{ key: "newest", label: "Newest" },
		{ key: "value_high_low", label: "Value High-Low" },
		{ key: "value_low_high", label: "Value Low-High" },
	];
	const PP4_DEPARTMENT_ALL = "all_departments";
	const PP4_VALUE_RANGE_ALL = "all";
	const PP4_STATUS_FILTERS = [
		{ key: "in_creation", label: "In Creation" },
		{ key: "awaiting_review", label: "Awaiting Review" },
		{ key: "ready_for_release", label: "Ready for Release" },
	];
	const PP4_VALUE_RANGES = [
		{ key: "under_kes_100m", label: "Under KES 100M" },
		{ key: "kes_100m_500m", label: "KES 100M - 500M" },
		{ key: "over_kes_500m", label: "Over KES 500M" },
	];
	const WORKBENCH_STATE_QUERY_KEYS = [
		"queue",
		"item",
		"plan",
		"search",
		"department",
		"category",
		"value_range",
		"created_from",
		"created_to",
		"sort",
		"page",
	];
	const WORKBENCH_ALLOWED_QUEUES = {
		needs_planning: true,
		draft_packages: true,
		needs_review: true,
		ready_to_release: true,
		blocked: true,
		recently_released: true,
		"all-packages": true,
	};
	const WORKBENCH_QUEUE_ALIASES = {
		"needs-planning": "needs_planning",
		"draft-packages": "draft_packages",
		"needs-review": "needs_review",
		"ready-to-release": "ready_to_release",
		"released-recently": "recently_released",
	};
	const WORKBENCH_SORT_OPTIONS = {
		newest: true,
		oldest: true,
		value_high_low: true,
		value_low_high: true,
		title_asc: true,
		title_desc: true,
	};

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
	}

	function normalizeWorkbenchQueueValue(rawValue) {
		const raw = String(rawValue || "").trim();
		if (!raw) return "needs_planning";
		const mapped = WORKBENCH_QUEUE_ALIASES[raw] || raw;
		return WORKBENCH_ALLOWED_QUEUES[mapped] ? mapped : "needs_planning";
	}

	function normalizePositiveIntValue(rawValue, fallback) {
		const n = Number(rawValue);
		if (!Number.isFinite(n) || n < 1) return String(fallback || 1);
		return String(Math.floor(n));
	}

	function readWorkbenchStateFromUrl(urlLike) {
		const url = urlLike ? new URL(urlLike, window.location.origin) : new URL(window.location.href);
		const search = url.searchParams;
		const state = {
			queue: normalizeWorkbenchQueueValue(search.get("queue")),
			item: String(search.get("item") || "").trim(),
			plan: String(search.get("plan") || "").trim(),
			search: String(search.get("search") || "").trim(),
			department: String(search.get("department") || "").trim(),
			category: String(search.get("category") || "").trim(),
			value_range: String(search.get("value_range") || "").trim(),
			created_from: String(search.get("created_from") || "").trim(),
			created_to: String(search.get("created_to") || "").trim(),
			sort: String(search.get("sort") || "").trim(),
			page: normalizePositiveIntValue(search.get("page"), 1),
		};
		if (!WORKBENCH_SORT_OPTIONS[state.sort]) {
			state.sort = "newest";
		}
		return state;
	}

	function hasWorkbenchStateQuery(searchParams) {
		const params = searchParams || new URLSearchParams(window.location.search || "");
		for (let i = 0; i < WORKBENCH_STATE_QUERY_KEYS.length; i += 1) {
			if (params.has(WORKBENCH_STATE_QUERY_KEYS[i])) return true;
		}
		return false;
	}

	function writeWorkbenchStateToUrl(partialState, options) {
		const opts = options || {};
		const url = new URL(window.location.href);
		const current = readWorkbenchStateFromUrl(url.toString());
		const next = Object.assign({}, current, partialState || {});
		next.queue = normalizeWorkbenchQueueValue(next.queue);
		next.page = normalizePositiveIntValue(next.page, 1);
		next.sort = WORKBENCH_SORT_OPTIONS[String(next.sort || "").trim()] ? String(next.sort || "").trim() : "newest";
		WORKBENCH_STATE_QUERY_KEYS.forEach(function (key) {
			const value = String(next[key] || "").trim();
			if (!value) {
				url.searchParams.delete(key);
				return;
			}
			url.searchParams.set(key, value);
		});
		const target = url.pathname + url.search + url.hash;
		if (opts.replace !== false) {
			window.history.replaceState({}, "", target);
		} else {
			window.history.pushState({}, "", target);
		}
		return next;
	}

	function canonicalizeWorkbenchStateQuery() {
		if (!isPlanningWorkspaceRoute()) return;
		if (readSurfaceSlug() !== "") return;
		const params = new URLSearchParams(window.location.search || "");
		if (!hasWorkbenchStateQuery(params)) return;
		const currentUrl = window.location.pathname + window.location.search + window.location.hash;
		writeWorkbenchStateToUrl({}, { replace: true });
		const nextUrl = window.location.pathname + window.location.search + window.location.hash;
		return nextUrl !== currentUrl;
	}

	function renderPlanningWorkbenchV4(root) {
		if (!root) return;
		root.setAttribute("data-testid", "pp4-workbench-root");
		root.className = "kt-pp-injected-shell pp4-workbench-root";
		root.innerHTML =
			'<section class="pp4-workbench" data-testid="pp4-workbench">' +
			'<iframe class="pp4-workbench-design-iframe" data-testid="pp4-workbench-design-iframe" src="/assets/kentender_procurement/workbench_design/needs_planning_default.html" title="Planning Workbench Needs Planning Default"></iframe>' +
			"</section>";
	}

	function renderPP4QueueCounts(root, counts) {
		if (!root || !counts || typeof counts !== "object") return;
		pp4QueueCountsByRoot.set(root, counts);
		const safeCount = function (key) {
			const value = Number(counts[key] || 0);
			return Number.isFinite(value) && value > 0 ? value : 0;
		};
		const inCreation = safeCount("draft_packages");
		const awaitingReview = safeCount("needs_review");
		const readyForRelease = safeCount("ready_to_release");
		const allPackages = inCreation + awaitingReview + readyForRelease;
		const setCount = function (testId, value) {
			const node = root.querySelector('[data-testid="' + testId + '"]');
			if (!node) return;
			node.textContent = String(value);
		};
		setCount("pp4-count-all-packages", allPackages);
		setCount("pp4-count-in-creation", inCreation);
		setCount("pp4-count-awaiting-review", awaitingReview);
		setCount("pp4-count-ready-for-release", readyForRelease);
		renderPP4PendingActionKpi(root, counts);
		renderPP4KpisFromState(root);
	}

	function pp4SetTabBadgeCounts(root, inCreation, awaitingReview, readyForRelease) {
		if (!root) return;
		const allPackages = Math.max(0, inCreation) + Math.max(0, awaitingReview) + Math.max(0, readyForRelease);
		const setCount = function (testId, value) {
			const node = root.querySelector('[data-testid="' + testId + '"]');
			if (!node) return;
			node.textContent = String(Math.max(0, Number(value || 0)));
		};
		setCount("pp4-count-all-packages", allPackages);
		setCount("pp4-count-in-creation", inCreation);
		setCount("pp4-count-awaiting-review", awaitingReview);
		setCount("pp4-count-ready-for-release", readyForRelease);
	}

	function pp4KpiNode(root, testId) {
		if (!root) return null;
		return root.querySelector('[data-testid="' + testId + '"]');
	}

	function pp4SetKpiText(root, testId, value) {
		const node = pp4KpiNode(root, testId);
		if (!node) return;
		node.textContent = String(value == null ? "" : value);
	}

	function pp4CompactKes(value) {
		const n = Number(value || 0);
		if (!Number.isFinite(n) || n <= 0) return "KES 0";
		const abs = Math.abs(n);
		if (abs >= 1000000000) {
			return "KES " + (abs / 1000000000).toFixed(1).replace(/\.0$/, "") + "B";
		}
		if (abs >= 1000000) {
			return "KES " + (abs / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
		}
		return "KES " + abs.toLocaleString();
	}

	function renderPP4PendingActionKpi(root, counts) {
		const c = counts && typeof counts === "object" ? counts : {};
		const needsReview = Number(c.needs_review || 0);
		const readyForRelease = Number(c.ready_to_release || 0);
		const pendingAction = (Number.isFinite(needsReview) ? needsReview : 0) + (Number.isFinite(readyForRelease) ? readyForRelease : 0);
		pp4SetKpiText(root, "pp4-kpi-pending-action-value", String(Math.max(0, pendingAction)) + " Items");
	}

	function pp4ReadNumericKpi(byId, key) {
		const value = Number((byId[key] && byId[key].value) || 0);
		return Number.isFinite(value) ? Math.max(0, value) : 0;
	}

	function renderPP4KpisFromState(root) {
		if (!root) return;
		const payload = pp4KpiPayloadByRoot.get(root) || null;
		if (!payload || payload.ok === false) return;
		const kpis = Array.isArray(payload.kpis) ? payload.kpis : [];
		const byId = {};
		for (let i = 0; i < kpis.length; i += 1) {
			const row = kpis[i] || {};
			const id = String(row.id || "").trim();
			if (!id) continue;
			byId[id] = row;
		}
		const queueCounts = pp4QueueCountsByRoot.get(root) || null;
		const safeTotalPackages = pp4ReadNumericKpi(byId, "total_packages");
		const safeTotalValue = pp4ReadNumericKpi(byId, "total_planned_value");
		const safeApproved = pp4ReadNumericKpi(byId, "approved_packages");
		const safeReadyForTender = pp4ReadNumericKpi(byId, "ready_for_tender");
		let activePackages = safeTotalPackages;
		if (queueCounts && typeof queueCounts === "object") {
			const inCreation = Number(queueCounts.draft_packages || 0);
			const awaitingReview = Number(queueCounts.needs_review || 0);
			const readyForRelease = Number(queueCounts.ready_to_release || 0);
			const queueActive =
				(Number.isFinite(inCreation) ? Math.max(0, inCreation) : 0) +
				(Number.isFinite(awaitingReview) ? Math.max(0, awaitingReview) : 0) +
				(Number.isFinite(readyForRelease) ? Math.max(0, readyForRelease) : 0);
			if (queueActive > 0) activePackages = queueActive;
		}
		const effectiveApproved = safeApproved + safeReadyForTender;
		const approvalRate = activePackages > 0 ? Math.round((effectiveApproved / activePackages) * 100) : 0;
		const boundedApprovalRate = Math.max(0, Math.min(100, approvalRate));
		pp4SetKpiText(root, "pp4-kpi-total-estimate-value", pp4CompactKes(safeTotalValue));
		pp4SetKpiText(root, "pp4-kpi-active-packages-value", String(activePackages));
		pp4SetKpiText(root, "pp4-kpi-approval-rate-value", String(boundedApprovalRate) + "%");
		const meter = pp4KpiNode(root, "pp4-kpi-approval-rate-meter");
		if (meter) {
			meter.style.width = String(boundedApprovalRate) + "%";
		}
	}

	function renderPP4Kpis(root, payload) {
		if (!root || !payload || payload.ok === false) return;
		pp4KpiPayloadByRoot.set(root, payload);
		renderPP4KpisFromState(root);
	}

	function fetchAndRenderPP4Kpis(root) {
		if (!root || !frappe || typeof frappe.call !== "function") return;
		frappe.call({
			method: PP_LANDING_SHELL_API,
			args: {},
			callback: function (response) {
				const message = (response && response.message) || {};
				renderPP4Kpis(root, message);
			},
		});
	}

	function fetchAndRenderPP4QueueCounts(root) {
		if (!root || !frappe || typeof frappe.call !== "function") return;
		frappe.call({
			method: WORKBENCH_QUEUE_COUNTS_API,
			args: {},
			callback: function (response) {
				const message = (response && response.message) || {};
				if (!message || message.ok === false) return;
				renderPP4QueueCounts(root, message.counts || {});
			},
		});
	}

	function pp4StatusToneClass(statusLabel) {
		const status = String(statusLabel || "").toLowerCase();
		if (status.indexOf("review") >= 0) return "pp4-package-card--review";
		if (status.indexOf("draft") >= 0) return "pp4-package-card--draft";
		if (status.indexOf("ready") >= 0 || status.indexOf("approved") >= 0) {
			return "pp4-package-card--approved";
		}
		return "pp4-package-card--draft";
	}

	function pp4ExtractValueLabel(item) {
		const hay = String((item && (item.meta_line || item.subtitle || item.summary_detail_line)) || "");
		const matched = hay.match(/KES\s+[0-9,]+(?:\.[0-9]+)?/i);
		return matched ? matched[0].toUpperCase() : "KES 0";
	}

	function pp4ProgressModel(item) {
		const data = item && typeof item === "object" ? item : {};
		const statusHay = String(
			data.status_pill_label || data.state_label || data.status_headline || "",
		).toLowerCase();
		if (
			statusHay.indexOf("ready for release") >= 0 ||
			statusHay.indexOf("approved") >= 0 ||
			statusHay.indexOf("released") >= 0
		) {
			return {
				percent: 100,
				label: "100% Complete",
				selection: true,
				validation: true,
				signoff: true,
			};
		}
		if (statusHay.indexOf("review") >= 0 || statusHay.indexOf("validation") >= 0) {
			return {
				percent: 65,
				label: "65% Progress",
				selection: true,
				validation: true,
				signoff: false,
			};
		}
		return {
			percent: 15,
			label: "15% Progress",
			selection: true,
			validation: false,
			signoff: false,
		};
	}

	function pp4CardHtmlForItem(item) {
		const data = item && typeof item === "object" ? item : {};
		const code = esc(String(data.underlying_object_code || "").trim());
		const title = esc(String(data.title || "").trim() || __("Untitled Package"));
		const status = esc(String(data.status_pill_label || data.state_label || "").trim() || __("Draft"));
		const desc = esc(
			String(
				data.package_description ||
					(data.package && data.package.description) ||
					data.status_detail ||
					data.next_step_detail ||
					data.subtitle ||
					"",
			)
				.trim()
				.slice(0, 180),
		);
		const valueLabel = esc(pp4ExtractValueLabel(data));
		const consolidatedDemandCount = Number(data.consolidated_demand_count || 0);
		const consolidatedLabel = esc(
			Number.isFinite(consolidatedDemandCount) && consolidatedDemandCount > 0
				? String(consolidatedDemandCount) + " Demands"
				: "0 Demands",
		);
		const progress = pp4ProgressModel(data);
		const actionLabel = esc(
			String((data.primary_action && data.primary_action.label) || data.next_action_label || __("Open Package")).trim(),
		);
		const actionKey = esc(
			String((data.primary_action && data.primary_action.action) || "open_package").trim(),
		);
		const actionTarget = esc(
			String(
				(data.primary_action && data.primary_action.target) || data.underlying_object_code || "",
			).trim(),
		);
		const packageCode = esc(String(data.underlying_object_code || "").trim());
		const tenderTarget = esc(String(((data.tender && data.tender.code) || "")).trim());
		const secondaryActions = Array.isArray(data.secondary_actions) ? data.secondary_actions : [];
		const secondary = secondaryActions.length ? secondaryActions[0] || {} : {};
		const secondaryActionKey = esc(String(secondary.action || "view_package").trim());
		const secondaryActionTarget = esc(
			String(secondary.target || data.underlying_object_code || "").trim(),
		);
		return (
			'<article class="pp4-package-card ' +
			pp4StatusToneClass(status) +
			'" data-testid="pp4-package-card">' +
			'<div class="pp4-package-card__header"><span class="pp4-package-card__code" data-testid="pp4-package-code">' +
			code +
			'</span><span class="pp4-package-card__status" data-testid="pp4-package-status-chip">' +
			status +
			"</span></div>" +
			'<h3 class="pp4-package-card__title">' +
			title +
			"</h3>" +
			'<p class="pp4-package-card__desc">' +
			desc +
			"</p>" +
			'<div class="pp4-package-card__meta"><span>EST. VALUE<br><strong class="pp4-meta-value">' +
			valueLabel +
			'</strong></span><span>CONSOLIDATED<br><strong class="pp4-meta-value">' +
			consolidatedLabel +
			"</strong></span></div>" +
			'<div class="pp4-package-card__workflow"><p class="pp4-package-card__progress" data-testid="pp4-package-workflow-progress"><span>Workflow Progress</span><strong>' +
			esc(progress.label) +
			'</strong></p><div class="pp4-progress"><span style="width:' +
			esc(String(progress.percent)) +
			'%"></span></div><p class="pp4-stage-row"><span class="' +
			(progress.selection ? "is-active" : "") +
			'">Selection</span><span class="' +
			(progress.validation ? "is-active" : "") +
			'">Validation</span><span class="' +
			(progress.signoff ? "is-active" : "") +
			'">Sign-off</span></p></div>' +
			'<div class="pp4-package-card__actions"><button class="pp4-package-card__primary" type="button" data-testid="pp4-package-primary-action" data-pp4-action="' +
			actionKey +
			'" data-pp4-target="' +
			actionTarget +
			'" data-pp4-package-code="' +
			packageCode +
			'" data-pp4-tender-code="' +
			tenderTarget +
			'">' +
			actionLabel +
			"</button><button class=\"pp4-package-card__icon-btn\" type=\"button\" data-testid=\"pp4-package-secondary-action\" data-pp4-action=\"" +
			secondaryActionKey +
			'" data-pp4-target="' +
			secondaryActionTarget +
			'" data-pp4-package-code="' +
			packageCode +
			'" data-pp4-tender-code="' +
			tenderTarget +
			"\"><span class=\"material-symbols-outlined\">more_vert</span></button></div>" +
			"</article>"
		);
	}

	function pp4CreatePackageCardHtml() {
		return (
			'<article class="pp4-package-card pp4-package-card--create" data-testid="pp4-create-package-card">' +
			'<div class="pp4-package-card__create-icon"><span class="material-symbols-outlined">add_task</span></div>' +
			'<h3 class="pp4-package-card__title">Create New Package</h3>' +
			'<p class="pp4-package-card__desc">Start the planning wizard to consolidate unassigned demands into a strategic package.</p>' +
			'<button class="pp4-package-card__primary" type="button" data-testid="pp4-new-planning-run">New Planning Run <span class="material-symbols-outlined">arrow_forward</span></button>' +
			"</article>"
		);
	}

	function pp4SearchHaystack(item) {
		const data = item && typeof item === "object" ? item : {};
		const fields = [
			data.underlying_object_code,
			data.title,
			data.package_description,
			data.status_detail,
			data.state_label,
			data.status_pill_label,
			data.meta_line,
			data.subtitle,
			data.next_step_detail,
		];
		return fields
			.map(function (v) {
				return String(v || "").toLowerCase();
			})
			.join(" ");
	}

	function pp4ValueNumber(item) {
		const normalized = String(pp4ExtractValueLabel(item) || "")
			.replace(/[^0-9.]/g, "")
			.trim();
		const value = Number(normalized || 0);
		return Number.isFinite(value) ? value : 0;
	}

	function pp4SortModeMeta(key) {
		for (let i = 0; i < PP4_SORT_MODES.length; i += 1) {
			if (PP4_SORT_MODES[i].key === key) return PP4_SORT_MODES[i];
		}
		return PP4_SORT_MODES[0];
	}

	function pp4DefaultFilterState() {
		return {
			search: "",
			status: "",
			department: PP4_DEPARTMENT_ALL,
			value_range: PP4_VALUE_RANGE_ALL,
			created_from: "",
			created_to: "",
		};
	}

	function pp4CloneFilterState(state) {
		const src = state && typeof state === "object" ? state : pp4DefaultFilterState();
		return {
			search: String(src.search || ""),
			status: String(src.status || ""),
			department: String(src.department || PP4_DEPARTMENT_ALL),
			value_range: String(src.value_range || PP4_VALUE_RANGE_ALL),
			created_from: String(src.created_from || ""),
			created_to: String(src.created_to || ""),
		};
	}

	function pp4StatusFilterKey(item) {
		const data = item && typeof item === "object" ? item : {};
		const statusHay = String(data.status_pill_label || data.state_label || "").toLowerCase();
		if (statusHay.indexOf("review") >= 0 || statusHay.indexOf("validation") >= 0) return "awaiting_review";
		if (statusHay.indexOf("ready") >= 0 || statusHay.indexOf("approved") >= 0) return "ready_for_release";
		return "in_creation";
	}

	function pp4DepartmentValue(item) {
		const data = item && typeof item === "object" ? item : {};
		return String(
			data.department_label || data.department || data.procuring_entity_label || data.procuring_entity || "",
		).trim();
	}

	function pp4CreatedDateValue(item) {
		const data = item && typeof item === "object" ? item : {};
		const raw = String(data.created_on || data.creation || data.modified || "").trim();
		if (!raw) return "";
		const m = raw.match(/\d{4}-\d{2}-\d{2}/);
		return m ? m[0] : "";
	}

	function pp4ValueRangeMatches(value, rangeKey) {
		if (rangeKey === PP4_VALUE_RANGE_ALL || !rangeKey) return true;
		const n = Number(value || 0);
		if (!Number.isFinite(n)) return false;
		if (rangeKey === "under_kes_100m") return n < 100000000;
		if (rangeKey === "kes_100m_500m") return n >= 100000000 && n <= 500000000;
		if (rangeKey === "over_kes_500m") return n > 500000000;
		return true;
	}

	function pp4HasActiveAppliedFilters(filters) {
		const f = filters && typeof filters === "object" ? filters : pp4DefaultFilterState();
		return Boolean(
			String(f.search || "").trim() ||
				String(f.status || "").trim() ||
				(String(f.department || PP4_DEPARTMENT_ALL) !== PP4_DEPARTMENT_ALL &&
					String(f.department || "").trim()) ||
				(String(f.value_range || PP4_VALUE_RANGE_ALL) !== PP4_VALUE_RANGE_ALL &&
					String(f.value_range || "").trim()) ||
				String(f.created_from || "").trim() ||
				String(f.created_to || "").trim(),
		);
	}

	function pp4ItemMatchesDrawerFilters(item, filters) {
		const data = item && typeof item === "object" ? item : {};
		const f = filters && typeof filters === "object" ? filters : pp4DefaultFilterState();
		const drawerTerm = String(f.search || "")
			.toLowerCase()
			.trim();
		if (drawerTerm && pp4SearchHaystack(data).indexOf(drawerTerm) === -1) return false;
		if (f.status && pp4StatusFilterKey(data) !== f.status) return false;
		const dept = String(pp4DepartmentValue(data) || "").toLowerCase();
		if (
			f.department &&
			f.department !== PP4_DEPARTMENT_ALL &&
			dept &&
			dept !== String(f.department || "").toLowerCase()
		) {
			return false;
		}
		if (
			f.department &&
			f.department !== PP4_DEPARTMENT_ALL &&
			!dept &&
			String(f.department || "").trim()
		) {
			return false;
		}
		if (!pp4ValueRangeMatches(pp4ValueNumber(data), String(f.value_range || PP4_VALUE_RANGE_ALL))) {
			return false;
		}
		const created = pp4CreatedDateValue(data);
		const from = String(f.created_from || "").trim();
		const to = String(f.created_to || "").trim();
		if (from && created && created < from) return false;
		if (to && created && created > to) return false;
		if ((from || to) && !created) return false;
		return true;
	}

	function renderPP4TabCountsForCurrentFilters(root) {
		if (!root) return;
		const applied = pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState();
		const topSearchTerm = String(pp4SearchTermByRoot.get(root) || "")
			.toLowerCase()
			.trim();
		const hasDynamicFiltering = pp4HasActiveAppliedFilters(applied) || Boolean(topSearchTerm);
		if (!hasDynamicFiltering) {
			const counts = pp4QueueCountsByRoot.get(root) || {};
			const inCreation = Number(counts.draft_packages || 0);
			const awaitingReview = Number(counts.needs_review || 0);
			const readyForRelease = Number(counts.ready_to_release || 0);
			pp4SetTabBadgeCounts(root, inCreation, awaitingReview, readyForRelease);
			return;
		}
		const byQueue = pp4QueueItemsByRoot.get(root) || {};
		const queues = {
			draft_packages: Array.isArray(byQueue.draft_packages) ? byQueue.draft_packages : [],
			needs_review: Array.isArray(byQueue.needs_review) ? byQueue.needs_review : [],
			ready_release: Array.isArray(byQueue.ready_release) ? byQueue.ready_release : [],
		};
		const countFor = function (rows) {
			let c = 0;
			for (let i = 0; i < rows.length; i += 1) {
				const row = rows[i];
				if (topSearchTerm && pp4SearchHaystack(row).indexOf(topSearchTerm) === -1) continue;
				if (!pp4ItemMatchesDrawerFilters(row, applied)) continue;
				c += 1;
			}
			return c;
		};
		pp4SetTabBadgeCounts(
			root,
			countFor(queues.draft_packages),
			countFor(queues.needs_review),
			countFor(queues.ready_release),
		);
	}

	function pp4AvailableDepartments(rows) {
		const options = [
			"Ministry of Health (MOH)",
			"IT Infrastructure",
			"Facilities Management",
		];
		const seen = {};
		const all = [];
		for (let i = 0; i < options.length; i += 1) {
			const label = String(options[i] || "").trim();
			if (!label) continue;
			const key = label.toLowerCase();
			if (seen[key]) continue;
			seen[key] = true;
			all.push(label);
		}
		for (let j = 0; j < rows.length; j += 1) {
			const label = String(pp4DepartmentValue(rows[j]) || "").trim();
			if (!label) continue;
			const key = label.toLowerCase();
			if (seen[key]) continue;
			seen[key] = true;
			all.push(label);
		}
		return all;
	}

	function renderPP4ControlLabels(root) {
		if (!root) return;
		const sortLabel = root.querySelector('[data-testid="pp4-sort-label"]');
		const filterLabel = root.querySelector('[data-testid="pp4-filters-label"]');
		const filterButton = root.querySelector('[data-testid="pp4-filters"]');
		const sortMode = pp4SortModeMeta(String(pp4SortModeByRoot.get(root) || "newest"));
		const applied = pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState();
		if (sortLabel) {
			sortLabel.textContent = "Sort: " + sortMode.label;
		}
		if (filterLabel) {
			filterLabel.textContent = "Filters";
		}
		if (filterButton) {
			filterButton.classList.toggle("is-active", pp4HasActiveAppliedFilters(applied));
		}
	}

	function renderPP4SortMenuState(root) {
		if (!root) return;
		const menu = root.querySelector('[data-testid="pp4-sort-menu"]');
		if (!menu) return;
		const open = pp4SortMenuOpenByRoot.get(root) === true;
		menu.hidden = !open;
		const selected = String(pp4SortModeByRoot.get(root) || "newest");
		const options = menu.querySelectorAll(".pp4-sort-menu__option");
		for (let i = 0; i < options.length; i += 1) {
			const opt = options[i];
			if (!opt) continue;
			const testId = String(opt.getAttribute("data-testid") || "");
			const selectedForOption =
				(selected === "newest" && testId === "pp4-sort-option-newest") ||
				(selected === "value_high_low" && testId === "pp4-sort-option-value-high-low") ||
				(selected === "value_low_high" && testId === "pp4-sort-option-value-low-high");
			opt.classList.toggle("is-selected", selectedForOption);
		}
	}

	function renderPP4FilterDrawerState(root) {
		if (!root) return;
		const backdrop = root.querySelector('[data-testid="pp4-filter-backdrop"]');
		const drawer = root.querySelector('[data-testid="pp4-filter-drawer"]');
		const open = pp4FilterDrawerOpenByRoot.get(root) === true;
		if (backdrop) backdrop.hidden = !open;
		if (drawer) drawer.hidden = !open;
		const draft = pp4FilterDraftByRoot.get(root) || pp4DefaultFilterState();
		const searchInput = root.querySelector('[data-testid="pp4-filter-search"]');
		const departmentSelect = root.querySelector('[data-testid="pp4-filter-department"]');
		const createdFrom = root.querySelector('[data-testid="pp4-filter-created-from"]');
		const createdTo = root.querySelector('[data-testid="pp4-filter-created-to"]');
		if (searchInput) searchInput.value = String(draft.search || "");
		if (createdFrom) createdFrom.value = String(draft.created_from || "");
		if (createdTo) createdTo.value = String(draft.created_to || "");
		if (departmentSelect) {
			const rows = Array.isArray(pp4PackageItemsByRoot.get(root)) ? pp4PackageItemsByRoot.get(root) : [];
			const departments = pp4AvailableDepartments(rows);
			const options = ['<option value="' + PP4_DEPARTMENT_ALL + '">All Departments</option>'];
			for (let i = 0; i < departments.length; i += 1) {
				const label = departments[i];
				options.push('<option value="' + esc(label) + '">' + esc(label) + "</option>");
			}
			departmentSelect.innerHTML = options.join("");
			departmentSelect.value = String(draft.department || PP4_DEPARTMENT_ALL);
		}
		for (let i = 0; i < PP4_STATUS_FILTERS.length; i += 1) {
			const status = PP4_STATUS_FILTERS[i];
			const chip = root.querySelector(
				'[data-testid="pp4-filter-status-' + status.key.replace(/_/g, "-") + '"]',
			);
			if (!chip) continue;
			chip.classList.toggle("is-active", String(draft.status || "") === status.key);
		}
		const radios = root.querySelectorAll('input[name="pp4-filter-value-range"]');
		for (let j = 0; j < radios.length; j += 1) {
			const radio = radios[j];
			radio.checked = String(radio.value || "") === String(draft.value_range || PP4_VALUE_RANGE_ALL);
		}
	}

	function renderPP4PackageCardsFromState(root) {
		if (!root) return;
		const grid = root.querySelector('[data-testid="pp4-package-grid"]');
		if (!grid) return;
		const rows = Array.isArray(pp4PackageItemsByRoot.get(root)) ? pp4PackageItemsByRoot.get(root) : [];
		const appliedFilters = pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState();
		const sortKey = String(pp4SortModeByRoot.get(root) || "newest").trim() || "newest";
		const term = String(pp4SearchTermByRoot.get(root) || "")
			.toLowerCase()
			.trim();
		const filteredRows = rows.filter(function (row) {
			if (term && pp4SearchHaystack(row).indexOf(term) === -1) return false;
			return pp4ItemMatchesDrawerFilters(row, appliedFilters);
		});
		const visibleRows = filteredRows.slice();
		if (sortKey === "value_high_low") {
			visibleRows.sort(function (a, b) {
				return pp4ValueNumber(b) - pp4ValueNumber(a);
			});
		} else if (sortKey === "value_low_high") {
			visibleRows.sort(function (a, b) {
				return pp4ValueNumber(a) - pp4ValueNumber(b);
			});
		}
		renderPP4ControlLabels(root);
		renderPP4SortMenuState(root);
		renderPP4FilterDrawerState(root);
		renderPP4TabCountsForCurrentFilters(root);
		const cards = [];
		for (let i = 0; i < visibleRows.length; i += 1) {
			cards.push(pp4CardHtmlForItem(visibleRows[i]));
		}
		if (!cards.length) {
			cards.push(
				'<article class="pp4-package-card pp4-package-card--draft" data-testid="pp4-package-card">' +
					'<h3 class="pp4-package-card__title">' +
					esc(__("No packages found")) +
					"</h3>" +
					'<p class="pp4-package-card__desc">' +
					esc(
						term || pp4HasActiveAppliedFilters(appliedFilters)
							? __("No packages match your search.")
							: __("There are no packages for this tab yet."),
					) +
					"</p>" +
					"</article>",
			);
		}
		cards.push(pp4CreatePackageCardHtml());
		grid.innerHTML = cards.join("");
		bindPP4CardActions(root);
	}

	function renderPP4PackageCards(root, items) {
		if (!root) return;
		pp4PackageItemsByRoot.set(root, Array.isArray(items) ? items : []);
		renderPP4PackageCardsFromState(root);
	}

	function buildPp4OpenTenderUrl(tenderCode) {
		const code = String(tenderCode || "").trim();
		if (!code) return "";
		return "/desk/tm2-tender/" + encodeURIComponent(code);
	}

	function handlePp4CardAction(action, target, packageCode, tenderCode) {
		if (action === "open_tender" || action === "view_tender") {
			const tenderUrl = buildPp4OpenTenderUrl(target || tenderCode);
			if (tenderUrl) {
				window.location.href = tenderUrl;
				return;
			}
		}
		const openPackageActions = {
			open_package: true,
			view_package: true,
			complete_package: true,
			review_package: true,
			mark_ready_for_release: true,
			release_to_tender: true,
			view_release: true,
			"": true,
		};
		if (openPackageActions[action]) {
			const code = target || packageCode;
			if (code) {
				window.location.href = buildWorkbenchOpenPackageUrl(code);
			}
		}
	}

	function handlePp4PrimaryCardAction(button) {
		if (!button) return;
		const action = String(button.getAttribute("data-pp4-action") || "").trim();
		const target = String(button.getAttribute("data-pp4-target") || "").trim();
		const packageCode = String(button.getAttribute("data-pp4-package-code") || "").trim();
		const tenderCode = String(button.getAttribute("data-pp4-tender-code") || "").trim();
		handlePp4CardAction(action, target, packageCode, tenderCode);
	}

	function handlePp4SecondaryCardAction(button) {
		if (!button) return;
		const action = String(button.getAttribute("data-pp4-action") || "").trim();
		const target = String(button.getAttribute("data-pp4-target") || "").trim();
		const packageCode = String(button.getAttribute("data-pp4-package-code") || "").trim();
		const tenderCode = String(button.getAttribute("data-pp4-tender-code") || "").trim();
		handlePp4CardAction(action, target, packageCode, tenderCode);
	}

	function bindPP4CardActions(root) {
		if (!root) return;
		const buttons = root.querySelectorAll('[data-testid="pp4-package-primary-action"]');
		for (let i = 0; i < buttons.length; i += 1) {
			const btn = buttons[i];
			if (!btn || btn.getAttribute("data-pp4-bound") === "1") continue;
			btn.setAttribute("data-pp4-bound", "1");
			btn.addEventListener("click", function () {
				handlePp4PrimaryCardAction(btn);
			});
		}
		const secondaryButtons = root.querySelectorAll('[data-testid="pp4-package-secondary-action"]');
		for (let j = 0; j < secondaryButtons.length; j += 1) {
			const btn = secondaryButtons[j];
			if (!btn || btn.getAttribute("data-pp4-bound") === "1") continue;
			btn.setAttribute("data-pp4-bound", "1");
			btn.addEventListener("click", function () {
				handlePp4SecondaryCardAction(btn);
			});
		}
	}

	function fetchPP4ItemsForQueue(queueKey, onDone) {
		if (!frappe || typeof frappe.call !== "function") {
			onDone([]);
			return;
		}
		frappe.call({
			method: WORKBENCH_ITEM_VIEW_MODEL_API,
			args: {
				queue: queueKey,
				limit: 24,
				start: 0,
			},
			callback: function (response) {
				const message = (response && response.message) || {};
				if (!message || message.ok === false) {
					onDone([]);
					return;
				}
				onDone(Array.isArray(message.items) ? message.items : []);
			},
			error: function () {
				onDone([]);
			},
		});
	}

	function fetchAndRenderPP4PackageCards(root, tabKey) {
		if (!root) return;
		const token = (pp4PackageFetchTokens.get(root) || 0) + 1;
		pp4PackageFetchTokens.set(root, token);
		const resolvedTab = String(tabKey || "all-packages").trim() || "all-packages";
		const queueKey = PP4_TAB_TO_QUEUE[resolvedTab] || "all-packages";
		if (queueKey !== "all-packages") {
			fetchPP4ItemsForQueue(queueKey, function (items) {
				if ((pp4PackageFetchTokens.get(root) || 0) !== token) return;
				const byQueue = pp4QueueItemsByRoot.get(root) || {};
				byQueue[queueKey] = Array.isArray(items) ? items.slice() : [];
				pp4QueueItemsByRoot.set(root, byQueue);
				renderPP4PackageCards(root, items);
			});
			return;
		}
		const collected = [];
		const seenByCode = {};
		const byQueue = {};
		let pending = PP4_ALL_PACKAGES_QUEUES.length;
		for (let i = 0; i < PP4_ALL_PACKAGES_QUEUES.length; i += 1) {
			const queue = PP4_ALL_PACKAGES_QUEUES[i];
			fetchPP4ItemsForQueue(queue, function (items) {
				if ((pp4PackageFetchTokens.get(root) || 0) !== token) return;
				byQueue[queue] = Array.isArray(items) ? items.slice() : [];
				for (let j = 0; j < items.length; j += 1) {
					const row = items[j];
					const code = String((row && row.underlying_object_code) || "").trim();
					if (code && seenByCode[code]) continue;
					if (code) seenByCode[code] = true;
					collected.push(row);
				}
				pending -= 1;
				if (pending <= 0) {
					pp4QueueItemsByRoot.set(root, byQueue);
					renderPP4PackageCards(root, collected);
				}
			});
		}
	}

	function setPP4ActiveTab(root, tabKey) {
		if (!root) return;
		const buttons = [
			{ testId: "pp4-tab-all-packages", key: "all-packages" },
			{ testId: "pp4-tab-in-creation", key: "in-creation" },
			{ testId: "pp4-tab-awaiting-review", key: "awaiting-review" },
			{ testId: "pp4-tab-ready-for-release", key: "ready-for-release" },
		];
		for (let i = 0; i < buttons.length; i += 1) {
			const cfg = buttons[i];
			const node = root.querySelector('[data-testid="' + cfg.testId + '"]');
			if (!node) continue;
			const active = cfg.key === tabKey;
			node.classList.toggle("is-active", active);
			node.setAttribute("aria-selected", active ? "true" : "false");
		}
	}

	function bindPP4TabPackageList(root) {
		if (!root) return;
		const tabBindings = [
			{ testId: "pp4-tab-all-packages", key: "all-packages" },
			{ testId: "pp4-tab-in-creation", key: "in-creation" },
			{ testId: "pp4-tab-awaiting-review", key: "awaiting-review" },
			{ testId: "pp4-tab-ready-for-release", key: "ready-for-release" },
		];
		for (let i = 0; i < tabBindings.length; i += 1) {
			const cfg = tabBindings[i];
			const node = root.querySelector('[data-testid="' + cfg.testId + '"]');
			if (!node) continue;
			if (node.getAttribute("data-pp4-tab-bound") === "1") continue;
			node.setAttribute("data-pp4-tab-bound", "1");
			node.addEventListener("click", function () {
				setPP4ActiveTab(root, cfg.key);
				fetchAndRenderPP4PackageCards(root, cfg.key);
			});
		}
	}

	function bindPP4Search(root) {
		if (!root) return;
		const input = root.querySelector('[data-testid="pp4-search-input"]');
		if (!input) return;
		if (input.getAttribute("data-pp4-search-bound") === "1") return;
		input.setAttribute("data-pp4-search-bound", "1");
		if (!pp4SearchTermByRoot.has(root)) {
			pp4SearchTermByRoot.set(root, "");
		}
		input.addEventListener("input", function () {
			pp4SearchTermByRoot.set(root, String(input.value || ""));
			renderPP4PackageCardsFromState(root);
		});
	}

	function bindPP4SortAndFilters(root) {
		if (!root) return;
		const sortButton = root.querySelector('[data-testid="pp4-sort"]');
		const filterButton = root.querySelector('[data-testid="pp4-filters"]');
		const sortMenu = root.querySelector('[data-testid="pp4-sort-menu"]');
		const backdrop = root.querySelector('[data-testid="pp4-filter-backdrop"]');
		const closeDrawerBtn = root.querySelector('[data-testid="pp4-filter-close"]');
		const filterSearch = root.querySelector('[data-testid="pp4-filter-search"]');
		const statusInCreation = root.querySelector('[data-testid="pp4-filter-status-in-creation"]');
		const statusAwaitingReview = root.querySelector('[data-testid="pp4-filter-status-awaiting-review"]');
		const statusReadyForRelease = root.querySelector('[data-testid="pp4-filter-status-ready-for-release"]');
		const department = root.querySelector('[data-testid="pp4-filter-department"]');
		const createdFrom = root.querySelector('[data-testid="pp4-filter-created-from"]');
		const createdTo = root.querySelector('[data-testid="pp4-filter-created-to"]');
		const applyButton = root.querySelector('[data-testid="pp4-filter-apply"]');
		const clearAllButton = root.querySelector('[data-testid="pp4-filter-clear-all"]');
		renderPP4ControlLabels(root);
		if (sortButton && sortButton.getAttribute("data-pp4-sort-bound") !== "1") {
			sortButton.setAttribute("data-pp4-sort-bound", "1");
			sortButton.addEventListener("click", function () {
				pp4SortMenuOpenByRoot.set(root, !(pp4SortMenuOpenByRoot.get(root) === true));
				renderPP4PackageCardsFromState(root);
			});
		}
		if (sortMenu && sortMenu.getAttribute("data-pp4-sort-options-bound") !== "1") {
			sortMenu.setAttribute("data-pp4-sort-options-bound", "1");
			const bindSortOption = function (testId, sortKey) {
				const node = root.querySelector('[data-testid="' + testId + '"]');
				if (!node) return;
				node.addEventListener("click", function () {
					pp4SortModeByRoot.set(root, sortKey);
					pp4SortMenuOpenByRoot.set(root, false);
					renderPP4PackageCardsFromState(root);
				});
			};
			bindSortOption("pp4-sort-option-newest", "newest");
			bindSortOption("pp4-sort-option-value-high-low", "value_high_low");
			bindSortOption("pp4-sort-option-value-low-high", "value_low_high");
		}
		if (filterButton && filterButton.getAttribute("data-pp4-filter-bound") !== "1") {
			filterButton.setAttribute("data-pp4-filter-bound", "1");
			filterButton.addEventListener("click", function () {
				pp4SortMenuOpenByRoot.set(root, false);
				const applied = pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState();
				pp4FilterDraftByRoot.set(root, pp4CloneFilterState(applied));
				pp4FilterDrawerOpenByRoot.set(root, true);
				renderPP4FilterDrawerState(root);
				renderPP4SortMenuState(root);
			});
		}
		if (backdrop && backdrop.getAttribute("data-pp4-filter-backdrop-bound") !== "1") {
			backdrop.setAttribute("data-pp4-filter-backdrop-bound", "1");
			backdrop.addEventListener("click", function () {
				pp4FilterDrawerOpenByRoot.set(root, false);
				pp4FilterDraftByRoot.set(
					root,
					pp4CloneFilterState(pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState()),
				);
				renderPP4FilterDrawerState(root);
			});
		}
		if (closeDrawerBtn && closeDrawerBtn.getAttribute("data-pp4-filter-close-bound") !== "1") {
			closeDrawerBtn.setAttribute("data-pp4-filter-close-bound", "1");
			closeDrawerBtn.addEventListener("click", function () {
				pp4FilterDrawerOpenByRoot.set(root, false);
				pp4FilterDraftByRoot.set(
					root,
					pp4CloneFilterState(pp4FilterAppliedByRoot.get(root) || pp4DefaultFilterState()),
				);
				renderPP4FilterDrawerState(root);
			});
		}
		const updateDraft = function (updater) {
			const current = pp4CloneFilterState(pp4FilterDraftByRoot.get(root) || pp4DefaultFilterState());
			updater(current);
			pp4FilterDraftByRoot.set(root, current);
			renderPP4FilterDrawerState(root);
		};
		if (filterSearch && filterSearch.getAttribute("data-pp4-filter-search-bound") !== "1") {
			filterSearch.setAttribute("data-pp4-filter-search-bound", "1");
			filterSearch.addEventListener("input", function () {
				updateDraft(function (next) {
					next.search = String(filterSearch.value || "");
				});
			});
		}
		const bindStatus = function (node, key) {
			if (!node || node.getAttribute("data-pp4-filter-status-bound") === "1") return;
			node.setAttribute("data-pp4-filter-status-bound", "1");
			node.addEventListener("click", function () {
				updateDraft(function (next) {
					next.status = key;
				});
			});
		};
		bindStatus(statusInCreation, "in_creation");
		bindStatus(statusAwaitingReview, "awaiting_review");
		bindStatus(statusReadyForRelease, "ready_for_release");
		if (department && department.getAttribute("data-pp4-filter-department-bound") !== "1") {
			department.setAttribute("data-pp4-filter-department-bound", "1");
			department.addEventListener("change", function () {
				updateDraft(function (next) {
					next.department = String(department.value || PP4_DEPARTMENT_ALL);
				});
			});
		}
		const rangeRadios = root.querySelectorAll('input[name="pp4-filter-value-range"]');
		for (let i = 0; i < rangeRadios.length; i += 1) {
			const radio = rangeRadios[i];
			if (!radio || radio.getAttribute("data-pp4-filter-range-bound") === "1") continue;
			radio.setAttribute("data-pp4-filter-range-bound", "1");
			radio.addEventListener("change", function () {
				if (!radio.checked) return;
				updateDraft(function (next) {
					next.value_range = String(radio.value || PP4_VALUE_RANGE_ALL);
				});
			});
		}
		if (createdFrom && createdFrom.getAttribute("data-pp4-filter-created-from-bound") !== "1") {
			createdFrom.setAttribute("data-pp4-filter-created-from-bound", "1");
			createdFrom.addEventListener("change", function () {
				updateDraft(function (next) {
					next.created_from = String(createdFrom.value || "");
				});
			});
		}
		if (createdTo && createdTo.getAttribute("data-pp4-filter-created-to-bound") !== "1") {
			createdTo.setAttribute("data-pp4-filter-created-to-bound", "1");
			createdTo.addEventListener("change", function () {
				updateDraft(function (next) {
					next.created_to = String(createdTo.value || "");
				});
			});
		}
		if (applyButton && applyButton.getAttribute("data-pp4-filter-apply-bound") !== "1") {
			applyButton.setAttribute("data-pp4-filter-apply-bound", "1");
			applyButton.addEventListener("click", function () {
				pp4FilterAppliedByRoot.set(
					root,
					pp4CloneFilterState(pp4FilterDraftByRoot.get(root) || pp4DefaultFilterState()),
				);
				pp4FilterDrawerOpenByRoot.set(root, false);
				renderPP4PackageCardsFromState(root);
			});
		}
		if (clearAllButton && clearAllButton.getAttribute("data-pp4-filter-clear-bound") !== "1") {
			clearAllButton.setAttribute("data-pp4-filter-clear-bound", "1");
			clearAllButton.addEventListener("click", function () {
				const defaults = pp4DefaultFilterState();
				pp4FilterDraftByRoot.set(root, pp4CloneFilterState(defaults));
				pp4FilterAppliedByRoot.set(root, pp4CloneFilterState(defaults));
				pp4FilterDrawerOpenByRoot.set(root, false);
				renderPP4PackageCardsFromState(root);
			});
		}
		if (document && !document.__pp4SortDismissBound) {
			document.__pp4SortDismissBound = true;
			document.addEventListener("click", function (ev) {
				if (!root || !root.contains(ev.target)) return;
				const host = root.querySelector(".pp4-sort-host");
				if (host && host.contains(ev.target)) return;
				if (pp4SortMenuOpenByRoot.get(root) === true) {
					pp4SortMenuOpenByRoot.set(root, false);
					renderPP4SortMenuState(root);
				}
			});
		}
	}

	function workspaceNameMatches(name) {
		if (!name) return false;
		if (name === WORKSPACE_NAME) return true;
		try {
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(WORKSPACE_NAME);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "procurement-planning";
	}

	function isPlanningWorkspaceRoute() {
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const workspaceName = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceName) {
					return workspaceNameMatches(workspaceName);
				}
			}
		} catch (e) {
			/* ignore */
		}
		const path = String(window.location.pathname || "").toLowerCase();
		return path.includes("/procurement-planning");
	}

	function readSurfaceSlug() {
		const path = String(window.location.pathname || "").toLowerCase();
		if (path.endsWith("/plans")) return "plans";
		if (path.endsWith("/releases")) return "releases";
		return "";
	}

	const CANONICAL_PLANNING_SLUGS = {
		plans: true,
		releases: true,
	};

	const INTERNAL_PLANNING_LEGACY_SLUGS = {
		"approved-demands": true,
		packages: true,
		home: true,
		evidence: true,
		inclusions: true,
		readiness: true,
		review: true,
		lines: true,
		technical: true,
		"release-package": true,
		"technical-details": true,
		audit: true,
	};

	const INTERNAL_PLANNING_ACCESS_ROLES = [
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Auditor",
		"Administrator",
		"System Manager",
		"Procurement Officer",
		"Tender Manager",
		"Budget Officer",
	];

	const INTERNAL_PLANNING_DENIED_ROLES = ["Supplier"];

	function readUserRoles() {
		try {
			const testRoles = window.__kt_pp2_test_roles;
			if (Array.isArray(testRoles)) {
				return testRoles.slice();
			}
		} catch (e) {
			/* ignore */
		}
		try {
			if (frappe.boot && frappe.boot.user && frappe.boot.user.roles) {
				return frappe.boot.user.roles.slice();
			}
			if (frappe.user_roles) {
				return frappe.user_roles.slice();
			}
		} catch (e) {
			/* ignore */
		}
		return [];
	}

	function mayAccessInternalPlanningLegacyRoute() {
		const roles = readUserRoles();
		for (let i = 0; i < INTERNAL_PLANNING_DENIED_ROLES.length; i += 1) {
			if (roles.indexOf(INTERNAL_PLANNING_DENIED_ROLES[i]) === -1) continue;
			for (let j = 0; j < INTERNAL_PLANNING_ACCESS_ROLES.length; j += 1) {
				if (roles.indexOf(INTERNAL_PLANNING_ACCESS_ROLES[j]) !== -1) {
					return true;
				}
			}
			return false;
		}
		return true;
	}

	function parsePlanningPathname(pathname) {
		const path = String(pathname || "").toLowerCase();
		const prefix = ROOT_PATH.toLowerCase();
		if (!path.startsWith(prefix)) return [];
		const rest = path.slice(prefix.length).replace(/^\/+/, "");
		if (!rest) return [];
		return rest.split("/").filter(Boolean);
	}

	function readPlanningRawSegments(pathname) {
		const path = String(pathname || "");
		const prefix = ROOT_PATH.toLowerCase();
		if (!path.toLowerCase().startsWith(prefix)) return [];
		const rest = path.slice(ROOT_PATH.length).replace(/^\/+/, "");
		if (!rest) return [];
		return rest.split("/").filter(Boolean);
	}

	function buildWorkbenchRedirectUrl(query) {
		const url = new URL(window.location.origin + ROOT_PATH);
		const q = query || {};
		Object.keys(q).forEach(function (key) {
			let value = String(q[key] || "").trim();
			if (!value) return;
			if (key === "queue") value = normalizeWorkbenchQueueValue(value);
			if (key === "page") value = normalizePositiveIntValue(value, 1);
			if (key === "sort") {
				value = WORKBENCH_SORT_OPTIONS[value] ? value : "newest";
			}
			url.searchParams.set(key, value);
		});
		return url.pathname + url.search;
	}

	function buildWorkbenchPackageRedirectUrl(packageCode) {
		const code = String(packageCode || "").trim();
		const state = readWorkbenchStateFromUrl();
		const queue = String(state.queue || "").trim();
		const item = String(state.item || "").trim();
		const params = {};
		if (code) {
			params.package_code = decodeURIComponent(code);
		}
		if (queue) {
			params.queue = queue;
		}
		if (item) {
			params.item = item;
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function buildWorkbenchApprovedDemandsRedirectUrl() {
		const state = readWorkbenchStateFromUrl();
		const params = {};
		const queue = String(state.queue || "").trim();
		const item = String(state.item || "").trim();
		if (queue) {
			params.queue = queue;
		}
		if (item) {
			params.item = item;
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function buildPackageDetailUrl(packageCode) {
		const code = String(packageCode || "").trim();
		if (!code) return ROOT_PATH;
		return `${ROOT_PATH}/packages/${encodeURIComponent(code)}`;
	}

	function buildPackagesRedirectUrl(packageCode) {
		return buildPackageDetailUrl(packageCode);
	}

	function resolvePlanningRoute(pathname) {
		const segments = parsePlanningPathname(pathname);
		const rawSegments = readPlanningRawSegments(pathname);
		if (!segments.length) {
			return { action: "canonical", slug: "" };
		}

		const head = segments[0];
		if (CANONICAL_PLANNING_SLUGS[head] && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
		}

		const requiresInternalAccess =
			INTERNAL_PLANNING_LEGACY_SLUGS[head] ||
			(head === "packages" && segments.length > 1) ||
			(head === "plans" && segments.length > 1) ||
			(head === "releases" && segments.length > 1);
		if (requiresInternalAccess && !mayAccessInternalPlanningLegacyRoute()) {
			return { action: "not_found", reason: "denied" };
		}

		if (head === "home" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
		}
		if (head === "approved-demands" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchApprovedDemandsRedirectUrl(),
			};
		}
		if (head === "packages" && segments.length === 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchPackageRedirectUrl(),
			};
		}

		if (head === "evidence") {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildPackagesRedirectUrl(rawSegments[1] || ""),
			};
		}
		if (head === "inclusions") {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchApprovedDemandsRedirectUrl(),
			};
		}
		if (
			head === "readiness" ||
			head === "review" ||
			head === "lines" ||
			head === "technical" ||
			head === "technical-details" ||
			head === "audit" ||
			head === "release-package"
		) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchRedirectUrl(),
			};
		}
		if (head === "releases" && segments.length > 1) {
			return {
				action: "redirect",
				slug: "releases",
				redirectUrl: `${ROOT_PATH}/releases`,
			};
		}
		if (head === "plans" && segments.length > 1) {
			return {
				action: "redirect",
				slug: "plans",
				redirectUrl: `${ROOT_PATH}/plans`,
			};
		}
		if (head === "packages" && segments.length > 1) {
			return {
				action: "redirect",
				slug: "",
				redirectUrl: buildWorkbenchPackageRedirectUrl(rawSegments[1] || ""),
			};
		}

		if (!CANONICAL_PLANNING_SLUGS[head]) {
			return { action: "not_found", reason: "unknown" };
		}

		return { action: "canonical", slug: head };
	}

	function applyPlanningRouteRedirect(redirectUrl) {
		const target = String(redirectUrl || "").trim();
		if (!target) return false;
		const url = new URL(target, window.location.origin);
		const next = url.pathname + url.search + url.hash;
		const curr = window.location.pathname + window.location.search + window.location.hash;
		if (next === curr) return false;
		window.history.replaceState({}, "", next);
		return true;
	}

	function renderRouteNotFound(root) {
		if (!root) return;
		root.innerHTML =
			'<section class="pp2-route-not-found" data-testid="pp2-route-not-found">' +
			'<h3 class="h6 mb-1">' +
			esc(__("Planning page unavailable")) +
			"</h3>" +
			'<p class="text-muted small mb-0">' +
			esc(__("You do not have access to this planning information.")) +
			"</p>" +
			"</section>";
	}

	function surfaceForSlug(slug) {
		return SURFACES[slug] || SURFACES[""];
	}

	function isPlanningHomeSlug(slug) {
		return String(slug == null ? "" : slug) === "";
	}

	function isProcurementPlansSlug(slug) {
		return String(slug || "").trim() === "plans";
	}

	function isReleasedToTenderSlug(slug) {
		return String(slug || "").trim() === "releases";
	}

	function isPackageDetailSlug(slug) {
		return String(slug || "").trim() === "package-detail";
	}

	function clearWorkbenchHosts(mainHost) {
		if (!mainHost) return;
		const testIds = [
			"pp2-primary-queue-host",
			"pp2-primary-filters-host",
			"pp2-primary-work-list-host",
		];
		for (let i = 0; i < testIds.length; i += 1) {
			const el = mainHost.querySelector('[data-testid="' + testIds[i] + '"]');
			if (el && el.parentNode) {
				el.parentNode.removeChild(el);
			}
		}
	}

	function formatMoneyValue(value, currency) {
		const amount = Number(value || 0);
		const curr = String(currency || "KES").trim() || "KES";
		const safeAmount = Number.isFinite(amount) ? amount : 0;
		return safeAmount.toLocaleString() + " " + curr;
	}

	function approvedDemandEmptyMessage(queueId) {
		const key = String(queueId || "").trim();
		if (key === "blocked") {
			return __("No blocked approved demands match this queue.");
		}
		if (key === "already-planned") {
			return __("No fully planned approved demands match this queue.");
		}
		return __("No approved demands match this queue.");
	}

	function mapApprovedDemandQueueRow(row, queueId) {
		const data = row || {};
		const demand = data.demand || {};
		const demandId = String(demand.id || "").trim();
		const title = String(demand.name || demand.code || demandId).trim();
		const category = String(data.category || "").trim();
		const valueLabel = formatMoneyValue(data.estimated_value, data.currency);
		const blockerLabel = String((data.blocker_summary && data.blocker_summary.label) || "").trim();
		const budgetLine = data.budget_line || {};
		const budgetLinked = String(budgetLine.id || budgetLine.code || "").trim().length > 0;
		const planningStatus = String(data.planning_status || "").trim() || (String(queueId || "").trim() === "already-planned" ? __("Fully Planned") : __("Ready for Planning"));
		return {
			id: demandId,
			title: title,
			subtitle: [category, valueLabel].filter(Boolean).join(" · "),
			category_value: [category, valueLabel].filter(Boolean).join(" · "),
			funding_status: budgetLinked ? __("Budget linked") : __("Budget not linked"),
			planning_status: planningStatus,
			status_label: planningStatus,
			blocker_label: blockerLabel,
			blocker_count: Number((data.blocker_summary && data.blocker_summary.count) || 0),
			raw: data,
		};
	}

	function approvedDemandSummaryFacts(item, drawerMessage) {
		const raw = (item && item.raw) || {};
		const drawer = drawerMessage || {};
		const demand = drawer.demand || {};
		const category = String(demand.category || raw.category || "").trim();
		const value = formatMoneyValue(
			demand.estimated_value != null ? demand.estimated_value : raw.estimated_value,
			demand.currency || raw.currency
		);
		return [category, value].filter(Boolean).join(" · ");
	}

	function approvedDemandSummaryFromDrawer(item, queueId, drawerMessage) {
		const raw = (item && item.raw) || {};
		const drawer = drawerMessage || {};
		const demand = drawer.demand || {};
		const demandTitle = String(demand.name || (item && item.title) || "").trim();
		const categoryLabel = String(demand.category || raw.category || "").trim();
		const valueLabel = formatMoneyValue(
			demand.estimated_value != null ? demand.estimated_value : raw.estimated_value,
			demand.currency || raw.currency
		);
		const budgetLine = (drawer.budget_context && drawer.budget_context.budget_line) || {};
		const budgetLinked = String(budgetLine.id || budgetLine.code || "").trim().length > 0;
		const eligibility = drawer.eligibility || {};
		const includeAllowed = eligibility.allowed !== false;
		const blockers = Array.isArray(eligibility.blockers)
			? eligibility.blockers
					.map(function (row) {
						return String((row && row.message) || "").trim();
					})
					.filter(Boolean)
			: [];
		const demandStatus = String(demand.planning_status || (item && item.planning_status) || "").trim();
		const fallbackNextAction = String(queueId || "").trim() === "blocked"
			? __("Resolve blockers before including in plan")
			: __("Include in plan");
		const evidenceRoute = String(
			(drawer.actions && drawer.actions.approval_certificate_route) ||
				(drawer.evidence && drawer.evidence.view_route) ||
				""
		).trim();
		const demandItems = Array.isArray(drawer.demand_items) ? drawer.demand_items : [];
		const demandItemCodes = demandItems
			.map(function (row) {
				if (!row || typeof row !== "object") return "";
				return String(row.code || row.demand_item_code || row.item_code || "").trim();
			})
			.filter(Boolean);
		const targetPlan = drawer.target_plan || {};
		return {
			context_slug: "approved-demands",
			demand_code: String(demand.code || (raw.demand && raw.demand.code) || "").trim(),
			title: demandTitle,
			status_label: demandStatus,
			key_facts: [categoryLabel, valueLabel].filter(Boolean).join(" · "),
			value_label: valueLabel,
			funding_label: budgetLinked ? __("Budget linked") : __("Budget not linked"),
			blockers: blockers,
			blocker_count: blockers.length,
			include_allowed: includeAllowed,
			include_blocker_message: blockers[0] || "",
			demand_item_codes: demandItemCodes,
			target_plan_code: String(targetPlan.code || targetPlan.id || targetPlan.name || "").trim(),
			target_plan_name: String(targetPlan.name || "").trim(),
			next_action_label: blockers.length ? __("Resolve blockers before including in plan") : fallbackNextAction,
			primary_action: {
				label: __("Add to Active Plan"),
				action: "include_in_plan",
				testid: "pp2-include-in-plan-button",
			},
			secondary_actions: [
				{
					label: __("View Demand"),
					action: "view_demand",
					route: evidenceRoute,
					testid: "pp2-view-demand-button",
				},
			],
			show_evidence_action: true,
			evidence_testid: "pp2-view-demand-evidence",
		};
	}

	function buildWorkbenchOpenPackageUrl(packageCode) {
		const code = String(packageCode || "").trim();
		const params = { queue: "draft-packages" };
		if (code) {
			params.package_code = decodeURIComponent(code);
		}
		return buildWorkbenchRedirectUrl(params);
	}

	function refreshWorkbenchWorkList(shell, slug, queueKey, refreshOpts) {
		if (!shell || !isPlanningHomeSlug(slug)) return;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (!mainHost) return;
		const normalizedQueue = String(queueKey || "").trim();
		const ro = refreshOpts || {};
		if (normalizedQueue) {
			const queueTabsApi =
				kentender_procurement &&
				kentender_procurement.PlanningWorkbenchQueueTabs &&
				typeof kentender_procurement.PlanningWorkbenchQueueTabs.setQueueUrl === "function"
					? kentender_procurement.PlanningWorkbenchQueueTabs
					: null;
			if (queueTabsApi) {
				queueTabsApi.setQueueUrl(normalizedQueue);
				const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
				if (queueHost && typeof queueTabsApi.fetchAndRender === "function") {
					queueTabsApi.fetchAndRender(queueHost, { activeQueue: normalizedQueue });
				} else if (queueHost && typeof queueTabsApi.render === "function") {
					queueTabsApi.render(queueHost, { activeQueue: normalizedQueue });
				}
			}
		}
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		const workListApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchWorkList &&
			typeof kentender_procurement.PlanningWorkbenchWorkList.fetchAndRender === "function"
				? kentender_procurement.PlanningWorkbenchWorkList
				: null;
		if (workListHost && workListApi && ro.suppressAutoSelect === true) {
			workListApi.fetchAndRender(workListHost, {
				queue: normalizedQueue || "needs_planning",
				suppressAutoSelect: true,
			});
			return;
		}
		mountPlanningWorkList(mainHost, slug, shell);
	}

	function createPackageSuccessSummary(payloadSummary, createResult, contextOpts) {
		const summaryData = payloadSummary || {};
		const result = createResult || {};
		const ctx = contextOpts || {};
		const workbench = ctx.workbench === true;
		const pkgRow = result.package && typeof result.package === "object" ? result.package : {};
		const packageCode = String(result.package_code || pkgRow.package_code || "").trim();
		const packageName = String(pkgRow.package_name || summaryData.title || "").trim();
		const message = __("Package created.");
		return {
			context_slug: workbench ? "workbench" : "approved-demands",
			create_package_success: true,
			title: message,
			create_package_success_message: message,
			next_action_label: __("Complete readiness and submit for review."),
			package_code: packageCode,
			package_name: packageName,
			primary_action: {
				label: __("Open Package"),
				action: "open_package_next",
				testid: "pp2-open-package-next-action",
			},
			secondary_actions: workbench
				? [
						{
							label: __("Back to Workbench"),
							action: "back_to_workbench",
							testid: "pp3-back-to-workbench",
						},
					]
				: [
						{
							label: __("Back to Approved Demands"),
							action: "back_to_approved_demands",
							testid: "pp2-back-to-approved-demands",
						},
					],
			show_evidence_action: false,
			demand_code: String(result.demand_code || summaryData.demand_code || "").trim(),
			target_plan_code: String(
				result.procurement_plan_code || summaryData.target_plan_code || "",
			).trim(),
			inclusion_code: String(result.inclusion_code || summaryData.inclusion_code || "").trim(),
		};
	}

	function mountCreatePackageSuccessSummary(shell, payloadSummary, createResult, opts) {
		const o = opts || {};
		const slug = String(o.slug || readSurfaceSlug() || "").trim();
		const workbench = isPlanningHomeSlug(slug);
		const successSummary = createPackageSuccessSummary(payloadSummary, createResult, {
			workbench: workbench,
		});
		mountPlanningSelectedSummary(shell, {
			summary: successSummary,
			slug: slug,
			onPrimaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey !== "open_package_next") return;
				const packageCode = String(successSummary.package_code || "").trim();
				if (!packageCode) {
					frappe.show_alert({
						indicator: "orange",
						message: __("Package reference is missing."),
					});
					return;
				}
				window.location.href = buildWorkbenchOpenPackageUrl(packageCode);
			},
			onSecondaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey === "back_to_workbench") {
					const packageCode = String(successSummary.package_code || "").trim();
					if (packageCode) {
						window.location.href = buildWorkbenchOpenPackageUrl(packageCode);
						return;
					}
					refreshWorkbenchWorkList(shell, slug, "draft_packages");
					return;
				}
				if (actionKey === "back_to_approved_demands") {
					window.location.href = ROOT_PATH + "?queue=needs-planning";
				}
			},
		});
	}

	function includePlanSuccessSummary(payloadSummary, includeResult, contextOpts) {
		const summaryData = payloadSummary || {};
		const result = includeResult || {};
		const ctx = contextOpts || {};
		const workbench = ctx.workbench === true;
		const planName = String(summaryData.target_plan_name || summaryData.active_plan_name || "").trim();
		const demandCode = String(result.demand_code || summaryData.demand_code || "").trim();
		const legacyMessage = __("Demand added to the procurement plan.");
		const message = workbench
			? planName
				? __("This demand has been added to:") + " " + planName
				: __("Demand added to the active procurement plan.")
			: legacyMessage;
		return {
			context_slug: workbench ? "workbench" : "approved-demands",
			include_success: true,
			title: String(summaryData.title || "").trim(),
			include_success_message: message,
			status_headline: workbench ? __("Added to active plan") : "",
			target_plan_name: planName,
			next_step_detail: workbench
				? __("Create a procurement package for this demand.")
				: "",
			next_action_label: __("Create Package"),
			primary_action: {
				label: __("Create Package"),
				action: "create_package_next",
				testid: "pp2-create-package-next-action",
			},
			secondary_actions: workbench
				? [
						{
							label: __("View Demand"),
							action: "view_demand",
							testid: "pp3-view-demand-button",
						},
					]
				: [
						{
							label: __("Back to Approved Demands"),
							action: "back_to_approved_demands",
							testid: "pp2-back-to-approved-demands",
						},
					],
			show_evidence_action: workbench,
			underlying_object_type: "approved_demand",
			underlying_object_code: demandCode,
			demand_code: demandCode,
			target_plan_code: String(
				result.procurement_plan_code || summaryData.target_plan_code || "",
			).trim(),
			inclusion_code: String(result.inclusion_code || "").trim(),
		};
	}

	function openCreatePackageModalForShell(shell, summaryData, opts) {
		const o = opts || {};
		const createApi =
			kentender_procurement &&
			kentender_procurement.PlanningCreatePackageModal &&
			typeof kentender_procurement.PlanningCreatePackageModal.open === "function"
				? kentender_procurement.PlanningCreatePackageModal
				: null;
		const payload = summaryData || {};
		if (!createApi) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Create Package modal is unavailable."),
			});
			return;
		}
		const launch = function (drawerMessage) {
			const drawer = drawerMessage || {};
			if (!drawer.ok) {
				frappe.show_alert({
					indicator: "orange",
					message:
						String(drawer.message || "").trim() ||
						__("Create Package context is unavailable."),
				});
				return;
			}
			createApi.open({
				demand_name: String(drawer.demand_name || payload.title || "").trim(),
				active_plan_name: String(drawer.active_plan_name || payload.target_plan_name || "").trim(),
				category_label: String(drawer.category_label || "").trim(),
				method_label: String(drawer.method_label || "").trim(),
				value_label: String(drawer.value_label || payload.value_label || "").trim(),
				funding_label: String(drawer.funding_label || payload.funding_label || "").trim(),
				package_title_default: String(drawer.package_title_default || drawer.demand_name || "").trim(),
				inclusion_code: String(drawer.inclusion_code || payload.inclusion_code || "").trim(),
				create_allowed: drawer.create_allowed !== false,
				blocker_code: String(drawer.blocker_code || "").trim(),
				blocker_message: String(drawer.blocker_message || "").trim(),
				duplicate_package: drawer.duplicate_package === true,
				existing_package_name: String(drawer.existing_package_name || "").trim(),
				existing_package_code: String(drawer.existing_package_code || "").trim(),
				onSuccess: function (createResult) {
					if (typeof o.onCreateSuccess === "function") {
						o.onCreateSuccess(createResult || {});
						return;
					}
					mountCreatePackageSuccessSummary(shell, payload, createResult || {}, {
						slug: o.slug,
					});
				},
				onOpenExistingPackage: function () {
					window.location.href = buildWorkbenchOpenPackageUrl(
						String(drawer.existing_package_code || "").trim(),
					);
				},
			});
		};
		frappe.call({
			method: CREATE_PACKAGE_DRAWER_API,
			args: {
				demand_code: String(payload.demand_code || "").trim(),
				plan_code: String(payload.target_plan_code || "").trim(),
				inclusion_code: String(payload.inclusion_code || "").trim(),
			},
			callback: function (response) {
				launch((response && response.message) || {});
			},
			error: function () {
				frappe.show_alert({
					indicator: "orange",
					message: __("Create Package context could not be loaded."),
				});
			},
		});
	}

	function mountIncludePlanSuccessSummary(shell, payloadSummary, includeResult, opts) {
		const o = opts || {};
		const slug = String(o.slug || readSurfaceSlug() || "").trim();
		const workbench = isPlanningHomeSlug(slug);
		const successSummary = includePlanSuccessSummary(payloadSummary, includeResult, {
			workbench: workbench,
		});
		mountPlanningSelectedSummary(shell, {
			summary: successSummary,
			slug: slug,
			onPrimaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey !== "create_package_next") return;
				if (workbench) {
					openCreatePackageModalForShell(shell, successSummary, { slug: slug });
					return;
				}
				window.location.href = ROOT_PATH + "/packages";
			},
			onSecondaryAction: function (action) {
				const actionKey = String((action && action.action) || "").trim();
				if (actionKey === "view_demand") {
					const demandCode = String(successSummary.demand_code || "").trim();
					if (!demandCode) return;
					frappe.call({
						method: APPROVED_DEMANDS_DRAWER_API,
						args: { demand_code: demandCode },
						callback: function (response) {
							const message = (response && response.message) || {};
							const route = String(
								(message.actions && message.actions.approval_certificate_route) ||
									(message.evidence && message.evidence.view_route) ||
									"",
							).trim();
							if (route) {
								window.location.href = route;
							}
						},
					});
					return;
				}
				if (actionKey === "back_to_workbench") {
					mountPlanningSelectedSummary(shell, { slug: slug });
					const mainHost = shell && shell.querySelector
						? shell.querySelector('[data-testid="pp2-primary-main-host"]')
						: null;
					if (mainHost) {
						mountPlanningWorkList(mainHost, slug, shell);
					}
					return;
				}
				if (actionKey === "back_to_approved_demands") {
					window.location.href = ROOT_PATH + "?queue=needs-planning";
				}
			},
			onEvidenceAction: function () {
				openWorkbenchEvidenceDrawer({
					title: String(successSummary.title || payloadSummary.title || "").trim(),
					underlying_object_type: "approved_demand",
					underlying_object_code: String(successSummary.demand_code || "").trim(),
				});
			},
		});
		if (workbench) {
			const queueKey =
				kentender_procurement &&
				kentender_procurement.PlanningWorkbenchWorkList &&
				typeof kentender_procurement.PlanningWorkbenchWorkList.queueFromUrl === "function"
					? kentender_procurement.PlanningWorkbenchWorkList.queueFromUrl()
					: "needs_planning";
			refreshWorkbenchWorkList(shell, slug, queueKey, { suppressAutoSelect: true });
		}
	}

	function openIncludePlanModalForShell(shell, summaryPayload, opts) {
		const o = opts || {};
		const includeApi =
			kentender_procurement &&
			kentender_procurement.PlanningIncludePlanModal &&
			typeof kentender_procurement.PlanningIncludePlanModal.open === "function"
				? kentender_procurement.PlanningIncludePlanModal
				: null;
		const summaryData = summaryPayload || {};
		if (!includeApi) {
			frappe.show_alert({
				indicator: "orange",
				message: __("Add to Active Plan modal is unavailable."),
			});
			return;
		}
		includeApi.open({
			demand_code: String(summaryData.demand_code || "").trim(),
			demand_name: String(summaryData.title || "").trim(),
			value_label: String(summaryData.value_label || "").trim(),
			funding_label: String(summaryData.funding_label || "").trim(),
			target_plan_code: String(summaryData.target_plan_code || "").trim(),
			target_plan_name: String(summaryData.target_plan_name || "").trim(),
			target_plan_locked: o.target_plan_locked === true,
			demand_item_codes: Array.isArray(summaryData.demand_item_codes) ? summaryData.demand_item_codes : [],
			include_allowed: summaryData.include_allowed !== false,
			blocker_message: String(summaryData.include_blocker_message || "").trim(),
			onBlocked: function (message) {
				const withAlert = Object.assign({}, summaryData, {
					include_alert_message: String(message || "").trim(),
				});
				mountPlanningSelectedSummary(shell, {
					summary: withAlert,
					slug: o.slug,
					onPrimaryAction: function () {
						openIncludePlanModalForShell(shell, withAlert, o);
					},
					onSecondaryAction: o.onSecondaryAction,
					onEvidenceAction: o.onEvidenceAction,
				});
			},
			onSuccess: function (includeResult) {
				if (typeof o.onIncludeSuccess === "function") {
					o.onIncludeSuccess(includeResult || {}, summaryData);
					return;
				}
				mountIncludePlanSuccessSummary(shell, summaryData, includeResult || {}, o);
			},
		});
	}

	function requestIncludePlanModalForShell(shell, summaryPayload, opts) {
		const summaryData = summaryPayload || {};
		const demandCode = String(summaryData.demand_code || "").trim();
		const launch = function (payload) {
			openIncludePlanModalForShell(shell, payload, opts);
		};
		const fetchDrawer = function (planCode) {
			if (!demandCode) {
				launch(summaryData);
				return;
			}
			const args = { demand_code: demandCode };
			if (planCode) args.plan_code = planCode;
			frappe.call({
				method: APPROVED_DEMANDS_DRAWER_API,
				args: args,
				callback: function (response) {
					const message = response && response.message ? response.message : {};
					if (message && message.ok && typeof opts.refreshSummaryFromDrawer === "function") {
						launch(opts.refreshSummaryFromDrawer(message) || summaryData);
						return;
					}
					launch(summaryData);
				},
				error: function () {
					launch(summaryData);
				},
			});
		};
		if (opts.useActivePlanContext) {
			frappe.call({
				method: ACTIVE_PLAN_API,
				args: {},
				callback: function (response) {
					const message = response && response.message ? response.message : {};
					const planCode = message && message.has_active_plan ? String(message.plan_code || "").trim() : "";
					fetchDrawer(planCode);
				},
				error: function () {
					fetchDrawer("");
				},
			});
			return;
		}
		fetchDrawer("");
	}

	function workbenchPseudoItemFromWorkItem(workItem) {
		const it = workItem || {};
		const subtitle = String(it.subtitle || "").trim();
		const parts = subtitle
			.split(" · ")
			.map(function (part) {
				return String(part || "").trim();
			})
			.filter(Boolean);
		const budgetLinked = /budget linked/i.test(subtitle);
		let valuePart = "";
		if (parts.length >= 3) {
			valuePart = parts[1];
		} else if (parts.length === 2 && !budgetLinked) {
			valuePart = parts[1];
		}
		return {
			title: String(it.title || "").trim(),
			raw: {
				demand: { code: String(it.underlying_object_code || "").trim() },
				category: parts[0] || "",
				estimated_value: valuePart,
				currency: "KES",
			},
		};
	}

	function openWorkbenchIncludePlanModal(shell, workItem, slug) {
		const pseudoItem = workbenchPseudoItemFromWorkItem(workItem);
		const baseSummary = approvedDemandSummaryFromDrawer(pseudoItem, "needs_planning", {});
		requestIncludePlanModalForShell(shell, baseSummary, {
			slug: slug,
			useActivePlanContext: true,
			target_plan_locked: true,
			refreshSummaryFromDrawer: function (drawerMessage) {
				return approvedDemandSummaryFromDrawer(pseudoItem, "needs_planning", drawerMessage || {});
			},
		});
	}

	function renderApprovedDemandSummary(shell, item, queueId) {
		if (!shell || !item) return;
		const summaryHost = ensureSummaryHost(shell);
		if (!summaryHost) return;
		const demandCode = String((((item || {}).raw || {}).demand || {}).code || "").trim();
		const token = (approvedDemandSummaryTokens.get(summaryHost) || 0) + 1;
		approvedDemandSummaryTokens.set(summaryHost, token);
		const baseSummary = approvedDemandSummaryFromDrawer(item, queueId, {});
		const includeModalOpts = {
			slug: "approved-demands",
			refreshSummaryFromDrawer: function (drawerMessage) {
				return approvedDemandSummaryFromDrawer(item, queueId, drawerMessage || {});
			},
			onSecondaryAction: function (action) {
				const route = String((action && action.route) || "").trim();
				if (!route) return;
				window.location.href = route;
			},
		};
		mountPlanningSelectedSummary(shell, {
			summary: baseSummary,
			slug: "approved-demands",
			onPrimaryAction: function () {
				requestIncludePlanModalForShell(shell, baseSummary, includeModalOpts);
			},
			onSecondaryAction: includeModalOpts.onSecondaryAction,
		});
		if (!demandCode) return;
		frappe.call({
			method: APPROVED_DEMANDS_DRAWER_API,
			args: { demand_code: demandCode },
			callback: function (response) {
				if (approvedDemandSummaryTokens.get(summaryHost) !== token) return;
				const message = response && response.message ? response.message : {};
				if (!message || !message.ok) return;
				const refreshedSummary = approvedDemandSummaryFromDrawer(item, queueId, message);
				mountPlanningSelectedSummary(shell, {
					summary: refreshedSummary,
					slug: "approved-demands",
					onPrimaryAction: function () {
						requestIncludePlanModalForShell(shell, refreshedSummary, includeModalOpts);
					},
					onSecondaryAction: includeModalOpts.onSecondaryAction,
				});
			},
		});
	}

	function renderApprovedDemandsQueue(mainHost, shell) {
		if (!mainHost || !shell) return;
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!workListHost) return;
		const queueApi =
			kentender_procurement &&
			kentender_procurement.PlanningQueueTabs &&
			typeof kentender_procurement.PlanningQueueTabs.readActiveFromUrl === "function"
				? kentender_procurement.PlanningQueueTabs
				: null;
		const workListApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkList &&
			typeof kentender_procurement.PlanningWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkList
				: null;
		if (!queueApi || !workListApi) return;
		const queueId = queueApi.readActiveFromUrl("approved-demands");
		const token = (approvedDemandFetchTokens.get(workListHost) || 0) + 1;
		approvedDemandFetchTokens.set(workListHost, token);
		workListApi.renderForSlug(workListHost, "approved-demands", {
			items: [],
			emptyMessage: __("Loading approved demands..."),
		});

		frappe.call({
			method: APPROVED_DEMANDS_QUEUE_API,
			args: { queue: queueId, start: 0, limit: 50 },
			callback: function (response) {
				if (approvedDemandFetchTokens.get(workListHost) !== token) return;
				const message = response && response.message ? response.message : {};
				if (!message || !message.ok) {
					workListApi.renderForSlug(workListHost, "approved-demands", {
						items: [],
						emptyMessage: approvedDemandEmptyMessage(queueId),
					});
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				const rows = Array.isArray(message.rows) ? message.rows : [];
				const items = rows.map(function (row) {
					return mapApprovedDemandQueueRow(row, queueId);
				});
				let selectedId = "";
				if (typeof workListApi.readSelectedFromUrl === "function") {
					selectedId = workListApi.readSelectedFromUrl(items);
					try {
						const rawItem = new URLSearchParams(window.location.search).get("item");
						if (rawItem && !selectedId && typeof workListApi.setSelectedUrl === "function") {
							workListApi.setSelectedUrl("");
						}
					} catch (e) {
						/* ignore */
					}
				}

				workListApi.renderForSlug(workListHost, "approved-demands", {
					items: items,
					selectedId: selectedId,
					emptyMessage: approvedDemandEmptyMessage(queueId),
					onSelect: function (_itemId, item) {
						if (!item) {
							mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
							return;
						}
						renderApprovedDemandSummary(shell, item, queueId);
					},
				});

				if (!selectedId) {
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				let selectedItem = null;
				for (let i = 0; i < items.length; i += 1) {
					if (String(items[i].id || "") === String(selectedId || "")) {
						selectedItem = items[i];
						break;
					}
				}
				if (!selectedItem) {
					mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
					return;
				}
				renderApprovedDemandSummary(shell, selectedItem, queueId);
			},
			error: function () {
				if (approvedDemandFetchTokens.get(workListHost) !== token) return;
				workListApi.renderForSlug(workListHost, "approved-demands", {
					items: [],
					emptyMessage: approvedDemandEmptyMessage(queueId),
				});
				mountPlanningSelectedSummary(shell, { slug: "approved-demands" });
			},
		});
	}

	function bindApprovedDemandsQueueRefresh(mainHost, shell) {
		if (!mainHost || !shell) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost || queueHost.getAttribute("data-pp2-approved-bound") === "1") return;
		queueHost.setAttribute("data-pp2-approved-bound", "1");
		queueHost.addEventListener("click", function (event) {
			const target = event.target && event.target.closest ? event.target.closest("[data-pp2-queue-id]") : null;
			if (!target) return;
			window.setTimeout(function () {
				renderApprovedDemandsQueue(mainHost, shell);
			}, 0);
		});
	}

	function mountPlanningHome(root) {
		if (!root) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningHome &&
			typeof kentender_procurement.PlanningHome.render === "function"
				? kentender_procurement.PlanningHome
				: null;
		if (api) {
			api.render(root);
			return;
		}
		root.innerHTML =
			'<article class="pp2-planning-home" data-testid="pp2-planning-home-surface">' +
			'<div class="pp2-planning-home__body" data-testid="pp2-planning-home-body">' +
			'<div class="pp2-planning-home__summary-host"></div>' +
			'<div class="pp2-planning-home__queues" data-testid="pp2-planning-home-queues"></div>' +
			"</div></article>";
	}

	function readRightPanelCollapsed() {
		try {
			const raw = window.localStorage.getItem(RIGHT_PANEL_STATE_KEY);
			if (raw === null) return true;
			return raw === "1";
		} catch (e) {
			return true;
		}
	}

	function writeRightPanelCollapsed(collapsed) {
		try {
			window.localStorage.setItem(RIGHT_PANEL_STATE_KEY, collapsed ? "1" : "0");
		} catch (e) {
			/* ignore */
		}
	}

	function syncSurfaceUrl(slug, options) {
		const opts = options || {};
		const url = new URL(window.location.href);
		const preserveSearch = opts.preserveSearch !== false;
		url.pathname = slug ? `${ROOT_PATH}/${slug}` : ROOT_PATH;
		if (!preserveSearch) {
			url.search = "";
		}
		const next = url.pathname + url.search + url.hash;
		const curr = window.location.pathname + window.location.search + window.location.hash;
		if (next !== curr) {
			window.history.replaceState({}, "", next);
		}
	}

	function resolveWorkspaceRoot() {
		return (
			document.getElementById("kt-pp-root") ||
			document.querySelector(".kt-pp-injected-shell")
		);
	}

	function ensureWorkspaceRoot() {
		let root = resolveWorkspaceRoot();
		if (root) return root;
		const mountPoint =
			document.querySelector(".layout-main-section .editor-js-container") ||
			document.querySelector(".layout-main-section") ||
			document.querySelector(".page-content");
		if (!mountPoint) return null;
		root = document.createElement("div");
		root.id = "kt-pp-root";
		root.className = "kt-pp-injected-shell";
		mountPoint.innerHTML = "";
		mountPoint.appendChild(root);
		return root;
	}

	const SURFACE_PURPOSE = {
		"": __("Convert approved demand into tender-ready procurement packages."),
		"approved-demands": __("Which approved demands can be planned now?"),
		plans: __("Create, activate, and review procurement plans."),
		packages: __("Which packages need work, review, release, or follow-up?"),
		releases: __("Which packages have left Planning, and where did they go?"),
	};

	function surfacePurposeForSlug(slug) {
		const emptyApi =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			typeof kentender_procurement.PlanningEmptyState.purposeForSlug === "function"
				? kentender_procurement.PlanningEmptyState
				: null;
		if (emptyApi) return emptyApi.purposeForSlug(slug);
		const key = slug == null ? "" : String(slug);
		return SURFACE_PURPOSE[key] || SURFACE_PURPOSE[""];
	}

	function renderSurfaceEmptyState(root, slug) {
		if (!root) return;
		const emptyApi =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			typeof kentender_procurement.PlanningEmptyState.renderForSlug === "function"
				? kentender_procurement.PlanningEmptyState
				: null;
		root.innerHTML =
			'<section class="pp2-surface-empty-state" data-testid="pp2-surface-empty-state"></section>';
		const wrapper = root.querySelector('[data-testid="pp2-surface-empty-state"]');
		if (!wrapper) return;
		if (emptyApi) {
			emptyApi.renderForSlug(wrapper, slug);
			return;
		}
		wrapper.innerHTML =
			'<div class="pp2-empty-state" data-testid="pp2-empty-state">' +
			'<p class="text-muted small mb-0" data-testid="pp2-empty-state-message">' +
			esc(__("No items need your attention right now.")) +
			"</p></div>";
	}

	function mountPlanningPageHeader(contextHost, slug) {
		if (!contextHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningPageHeader &&
			typeof kentender_procurement.PlanningPageHeader.renderForSlug === "function"
				? kentender_procurement.PlanningPageHeader
				: null;
		if (api) {
			api.renderForSlug(contextHost, slug);
			return;
		}
		const copy = surfacePurposeForSlug(slug);
		const surface = surfaceForSlug(slug);
		contextHost.innerHTML =
			'<header class="pp2-page-header" data-testid="pp2-page-header">' +
			'<h2 class="h5 mb-1" data-testid="pp2-page-title">' +
			esc(surface.subtitle || __("Procurement Planning")) +
			"</h2>" +
			'<p class="text-muted small mb-0" data-testid="pp2-page-purpose">' +
			esc(copy) +
			"</p></header>";
	}

	function clearPlanningWorkUnavailable(mainHost) {
		if (!mainHost) return;
		const panel = mainHost.querySelector('[data-testid="pp3-planning-work-unavailable"]');
		if (panel && panel.parentNode) {
			panel.parentNode.removeChild(panel);
		}
	}

	function mountPlanningWorkUnavailable(mainHost) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		let panel = mainHost.querySelector('[data-testid="pp3-planning-work-unavailable"]');
		if (!panel) {
			panel = document.createElement("section");
			panel.className = "pp3-planning-work-unavailable";
			panel.setAttribute("data-testid", "pp3-planning-work-unavailable");
			mainHost.appendChild(panel);
		}
		panel.innerHTML =
			'<p class="pp3-planning-work-unavailable__message text-muted mb-0">' +
			esc(__("Planning work is unavailable until an active procurement plan is selected.")) +
			"</p>";
	}

	function fetchActivePlanPayload() {
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.fetchPayload === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (!api) {
			return Promise.resolve({ has_active_plan: true });
		}
		return api.fetchPayload({});
	}

	function mountPlanningContextWithPayload(contextHost, slug, payload) {
		if (!contextHost) return;
		contextHost.innerHTML =
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>' +
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>';
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
		const bannerApi =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.render === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (bannerApi && activePlanHost) {
			bannerApi.render(activePlanHost, payload || {});
		} else if (activePlanHost) {
			activePlanHost.innerHTML = "";
		}
		mountPlanningPageHeader(pageHeaderHost, slug);
	}

	function mountWorkbenchRootWork(mainHost, shell, slug, activePlanPayload) {
		if (!mainHost || !shell) return;
		const payload = activePlanPayload || {};
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost) {
			mountPlanningContextWithPayload(contextHost, slug, payload);
		}
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		if (!payload.has_active_plan) {
			shell.setAttribute("data-pp3-planning-blocked", "1");
			mountPlanningWorkUnavailable(mainHost);
			mountPlanningSelectedSummary(shell, { slug: slug });
			return;
		}
		shell.removeAttribute("data-pp3-planning-blocked");
		mountPlanningQueueTabs(mainHost, slug);
		mountPlanningWorkList(mainHost, slug, shell);
		bindWorkbenchQueueRefresh(mainHost, slug, shell);
	}

	function mountActivePlanBanner(host) {
		if (!host) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningActivePlanBanner &&
			typeof kentender_procurement.PlanningActivePlanBanner.fetchAndRender === "function"
				? kentender_procurement.PlanningActivePlanBanner
				: null;
		if (!api) {
			host.innerHTML = "";
			return;
		}
		api.fetchAndRender(host, {});
	}

	function mountPlanningContext(contextHost, slug) {
		if (!contextHost) return;
		contextHost.innerHTML =
			'<div class="pp2-primary-context-page-header" data-testid="pp2-page-header-host"></div>' +
			'<div class="pp2-primary-context-active-plan" data-testid="pp3-active-plan-host"></div>';
		const pageHeaderHost = contextHost.querySelector('[data-testid="pp2-page-header-host"]');
		const activePlanHost = contextHost.querySelector('[data-testid="pp3-active-plan-host"]');
		if (isProcurementPlansSlug(slug)) {
			if (activePlanHost) activePlanHost.innerHTML = "";
		} else if (isReleasedToTenderSlug(slug) || isPackageDetailSlug(slug)) {
			if (activePlanHost) activePlanHost.innerHTML = "";
		} else {
			mountActivePlanBanner(activePlanHost);
		}
		mountPlanningPageHeader(pageHeaderHost, slug);
	}

	function mountProcurementPlansSurface(mainHost, slug, root) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		const children = Array.from(mainHost.children);
		for (let i = 0; i < children.length; i += 1) {
			if (children[i] !== root) {
				mainHost.removeChild(children[i]);
			}
		}
		const markerId = surfaceForSlug(slug).testId;
		if (root) {
			root.innerHTML =
				'<article class="pp3-procurement-plans-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-procurement-plans-surface__body" data-testid="pp3-procurement-plans-body"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-procurement-plans-body"]');
			if (bodyHost) {
				bodyHost.innerHTML =
					'<div class="pp3-procurement-plans-layout"><div class="pp3-procurement-plans-layout__list" data-testid="pp3-procurement-plans-list-host"></div><div class="pp3-procurement-plans-layout__summary" data-testid="pp3-procurement-plans-summary-host"></div></div>';
				const listHost = bodyHost.querySelector('[data-testid="pp3-procurement-plans-list-host"]');
				const planListApi =
					kentender_procurement &&
					kentender_procurement.PlanningPlanList &&
					typeof kentender_procurement.PlanningPlanList.render === "function"
						? kentender_procurement.PlanningPlanList
						: null;
				if (planListApi && listHost) {
					const summaryHost = bodyHost.querySelector(
						'[data-testid="pp3-procurement-plans-summary-host"]',
					);
					const summaryApi =
						kentender_procurement &&
						kentender_procurement.PlanningPlanSummary &&
						typeof kentender_procurement.PlanningPlanSummary.render === "function"
							? kentender_procurement.PlanningPlanSummary
							: null;
					function renderSummary(plan) {
						if (!summaryApi || !summaryHost || !plan) return;
						summaryApi.render(summaryHost, {
							plan: plan,
							onRefresh: function () {
								if (typeof window.__kt_pp_refresh_procurement_plans === "function") {
									window.__kt_pp_refresh_procurement_plans();
								}
							},
						});
					}
					function selectPlan(plan) {
						const planId = String((plan && plan.plan_id) || "").trim();
						if (!planId) return;
						try {
							const url = new URL(window.location.href);
							url.searchParams.set("plan", planId);
							window.history.replaceState({}, "", url.pathname + url.search);
						} catch (e) {
							/* ignore */
						}
						renderSummary(plan);
						const rows = listHost.querySelectorAll('[data-testid="pp3-plan-row"]');
						for (let i = 0; i < rows.length; i += 1) {
							const row = rows[i];
							const active = String(row.getAttribute("data-pp3-plan-id") || "").trim() === planId;
							row.classList.toggle("is-active", active);
							row.setAttribute("aria-selected", active ? "true" : "false");
						}
					}
					planListApi.render(listHost, {
						onSelect: selectPlan,
						onLoaded: function (_payload, plans) {
							if (!Array.isArray(plans) || !plans.length) return;
							let selectedId = "";
							try {
								selectedId = String(
									new URLSearchParams(window.location.search).get("plan") || "",
								).trim();
							} catch (e) {
								selectedId = "";
							}
							const match =
								plans.find(function (row) {
									return String(row.plan_id || row.plan_code || "").trim() === selectedId;
								}) || plans[0];
							if (match) selectPlan(match);
						},
						selectedPlanId: (function () {
							try {
								return new URLSearchParams(window.location.search).get("plan") || "";
							} catch (e) {
								return "";
							}
						})(),
					});
					window.__kt_pp_refresh_procurement_plans = function () {
						planListApi.render(listHost, {
							onSelect: selectPlan,
							selectedPlanId: (function () {
								try {
									return new URLSearchParams(window.location.search).get("plan") || "";
								} catch (e) {
									return "";
								}
							})(),
						});
					};
				}
			}
		}
	}

	function mountReleasedToTenderSurface(mainHost, slug, root) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		const children = Array.from(mainHost.children);
		for (let i = 0; i < children.length; i += 1) {
			if (children[i] !== root) {
				mainHost.removeChild(children[i]);
			}
		}
		const markerId = surfaceForSlug(slug).testId;
		if (root) {
			root.innerHTML =
				'<article class="pp3-released-to-tender-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-released-to-tender-surface__body" data-testid="pp3-released-to-tender-body"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-released-to-tender-body"]');
			const listApi =
				kentender_procurement &&
				kentender_procurement.PlanningReleasedList &&
				typeof kentender_procurement.PlanningReleasedList.render === "function"
					? kentender_procurement.PlanningReleasedList
					: null;
			if (listApi && bodyHost) {
				let selectedCode = "";
				try {
					selectedCode = String(
						new URLSearchParams(window.location.search).get("package") || "",
					).trim();
				} catch (e) {
					selectedCode = "";
				}
				function selectRow(row) {
					const code = String(((row && row.package) || {}).code || "").trim();
					if (!code) return;
					try {
						const url = new URL(window.location.href);
						url.searchParams.set("package", code);
						window.history.replaceState({}, "", url.pathname + url.search);
					} catch (err) {
						/* ignore */
					}
					const rows = bodyHost.querySelectorAll('[data-testid="pp3-released-row"]');
					for (let i = 0; i < rows.length; i += 1) {
						const rowEl = rows[i];
						const active =
							String(rowEl.getAttribute("data-pp3-package-code") || "").trim() === code;
						rowEl.classList.toggle("is-active", active);
						rowEl.setAttribute("aria-selected", active ? "true" : "false");
					}
					const summaryHost = bodyHost.querySelector(
						'[data-testid="pp3-released-summary-host"]',
					);
					const summaryApi =
						kentender_procurement &&
						kentender_procurement.PlanningReleasedSummary &&
						typeof kentender_procurement.PlanningReleasedSummary.render === "function"
							? kentender_procurement.PlanningReleasedSummary
							: null;
					if (summaryApi && summaryHost) {
						summaryApi.render(summaryHost, {
							packageCode: code,
							onViewEvidence: function (ctx) {
								openWorkbenchEvidenceDrawer({
									title: (ctx && ctx.title) || "",
									package_code: (ctx && ctx.package_code) || code,
								});
							},
						});
					}
				}
				listApi.render(bodyHost, {
					selectedPackageCode: selectedCode,
					onSelect: selectRow,
					onViewEvidence: function (ctx) {
						openWorkbenchEvidenceDrawer({
							title: (ctx && ctx.title) || "",
							package_code: (ctx && ctx.package_code) || "",
						});
					},
				});
			}
		}
	}

	function mountPackageDetailSurface(mainHost, packageCode, root) {
		if (!mainHost) return;
		clearWorkbenchHosts(mainHost);
		clearPlanningWorkUnavailable(mainHost);
		const children = Array.from(mainHost.children);
		for (let i = 0; i < children.length; i += 1) {
			if (children[i] !== root) {
				mainHost.removeChild(children[i]);
			}
		}
		const markerId = surfaceForSlug("package-detail").testId;
		if (root) {
			root.innerHTML =
				'<article class="pp3-package-detail-surface" data-testid="' +
				esc(markerId) +
				'"><div class="pp3-package-detail-surface__body" data-testid="pp3-package-detail-host"></div></article>';
			const bodyHost = root.querySelector('[data-testid="pp3-package-detail-host"]');
			const detailApi =
				kentender_procurement &&
				kentender_procurement.PlanningPackageDetail &&
				typeof kentender_procurement.PlanningPackageDetail.render === "function"
					? kentender_procurement.PlanningPackageDetail
					: null;
			if (detailApi && bodyHost) {
				detailApi.render(bodyHost, { packageCode: packageCode });
			}
		}
	}

	function mountPlanningQueueTabs(mainHost, slug) {
		if (!mainHost) return;
		let queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost) {
			queueHost = document.createElement("div");
			queueHost.className = "pp2-primary-queue-host";
			queueHost.setAttribute("data-testid", "pp2-primary-queue-host");
			mainHost.insertBefore(queueHost, mainHost.firstChild);
		} else if (mainHost.firstChild !== queueHost) {
			mainHost.insertBefore(queueHost, mainHost.firstChild);
		}
		const isWorkbenchRoot = isPlanningHomeSlug(slug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchQueueTabs &&
			typeof kentender_procurement.PlanningWorkbenchQueueTabs.renderForSlug === "function"
				? kentender_procurement.PlanningWorkbenchQueueTabs
				: null;
		const pp2Api =
			kentender_procurement &&
			kentender_procurement.PlanningQueueTabs &&
			typeof kentender_procurement.PlanningQueueTabs.renderForSlug === "function"
				? kentender_procurement.PlanningQueueTabs
				: null;
		const api = isWorkbenchRoot ? pp3Api : pp2Api;
		if (api) {
			if (
				isWorkbenchRoot &&
				typeof kentender_procurement.PlanningWorkbenchQueueTabs.fetchAndRender === "function"
			) {
				kentender_procurement.PlanningWorkbenchQueueTabs.fetchAndRender(queueHost, { slug: slug });
				return;
			}
			api.renderForSlug(queueHost, slug);
			return;
		}
		if (isWorkbenchRoot) {
			const fallbackQueueKeys = {
				needs_planning: true,
				draft_packages: true,
				needs_review: true,
				ready_to_release: true,
				blocked: true,
				recently_released: true,
			};
			let activeQueue = "needs_planning";
			try {
				const rawQueue = new URLSearchParams(window.location.search).get("queue");
				if (rawQueue && fallbackQueueKeys[rawQueue]) {
					activeQueue = rawQueue;
				}
			} catch (e) {
				/* ignore */
			}
			const queueChipHtml = function (queueKey, label, testId) {
				const active = queueKey === activeQueue;
				return (
					'<button type="button" class="btn btn-default btn-sm pp3-workbench-queue-tabs__chip' +
					(active ? " is-active" : "") +
					'" data-testid="' +
					testId +
					'" data-pp3-queue-key="' +
					queueKey +
					'" role="tab" aria-selected="' +
					(active ? "true" : "false") +
					'">' +
					esc(label) +
					"</button>"
				);
			};
			queueHost.innerHTML =
				'<nav class="pp3-workbench-queue-tabs" data-testid="pp3-workbench-queue-tabs" role="tablist">' +
				queueChipHtml("needs_planning", __("Needs Planning"), "pp3-queue-needs-planning") +
				queueChipHtml("draft_packages", __("Draft Packages"), "pp3-queue-draft-packages") +
				queueChipHtml("needs_review", __("Needs Review"), "pp3-queue-needs-review") +
				queueChipHtml("ready_to_release", __("Ready to Release"), "pp3-queue-ready-release") +
				queueChipHtml("blocked", __("Blocked"), "pp3-queue-blocked") +
				queueChipHtml("recently_released", __("Recently Released"), "pp3-queue-recently-released") +
				"</nav>";
			const fallbackButtons = queueHost.querySelectorAll("[data-pp3-queue-key]");
			for (let i = 0; i < fallbackButtons.length; i += 1) {
				const button = fallbackButtons[i];
				if (button.getAttribute("data-bound") === "1") continue;
				button.setAttribute("data-bound", "1");
				button.addEventListener("click", function () {
					const queueKey = String(button.getAttribute("data-pp3-queue-key") || "").trim();
					if (!fallbackQueueKeys[queueKey]) return;
					try {
						const url = new URL(window.location.href);
						url.searchParams.set("queue", queueKey);
						window.history.replaceState({}, "", url.pathname + url.search + url.hash);
					} catch (e) {
						/* ignore */
					}
					mountPlanningQueueTabs(mainHost, slug);
				});
			}
			return;
		}
		queueHost.innerHTML = "";
	}

	function mountPlanningAdvancedFilters(mainHost, slug) {
		if (!mainHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningAdvancedFilters &&
			typeof kentender_procurement.PlanningAdvancedFilters.renderForSlug === "function"
				? kentender_procurement.PlanningAdvancedFilters
				: null;
		let filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
		if (!api || !api.isAvailableForSlug(slug)) {
			if (filtersHost) filtersHost.remove();
			return;
		}
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!filtersHost) {
			filtersHost = document.createElement("div");
			filtersHost.className = "pp2-primary-filters-host";
			filtersHost.setAttribute("data-testid", "pp2-primary-filters-host");
		}
		if (workListHost) {
			mainHost.insertBefore(filtersHost, workListHost);
		} else if (queueHost && queueHost.nextSibling) {
			mainHost.insertBefore(filtersHost, queueHost.nextSibling);
		} else if (queueHost) {
			if (queueHost.nextSibling) {
				mainHost.insertBefore(filtersHost, queueHost.nextSibling);
			} else {
				mainHost.appendChild(filtersHost);
			}
		} else {
			mainHost.insertBefore(filtersHost, mainHost.firstChild);
		}
		api.renderForSlug(filtersHost, slug);
	}

	function ensureSummaryHost(shell) {
		if (!shell) return null;
		const rightPanel = shell.querySelector('[data-testid="pp2-primary-right-panel"]');
		if (!rightPanel) return null;
		let summaryHost = rightPanel.querySelector('[data-testid="pp2-primary-summary-host"]');
		if (!summaryHost) {
			summaryHost = document.createElement("div");
			summaryHost.className = "pp2-primary-summary-host";
			summaryHost.setAttribute("data-testid", "pp2-primary-summary-host");
			const nextAction = rightPanel.querySelector('[data-testid="pp2-primary-next-action-panel"]');
			if (nextAction) {
				rightPanel.insertBefore(summaryHost, nextAction);
			} else {
				rightPanel.appendChild(summaryHost);
			}
		}
		return summaryHost;
	}

	function mountPlanningSelectedSummary(shell, opts) {
		if (!shell) return;
		const summaryHost = ensureSummaryHost(shell);
		if (!summaryHost) return;
		const o = opts || {};
		const summarySlug = String((o.summary && o.summary.context_slug) || "").trim();
		const resolvedSlug = String(
			o.slug != null ? o.slug : summarySlug || readSurfaceSlug(),
		).trim();
		const isWorkbenchRoot = isPlanningHomeSlug(resolvedSlug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchSelectedSummary &&
			typeof kentender_procurement.PlanningWorkbenchSelectedSummary.renderIdle === "function"
				? kentender_procurement.PlanningWorkbenchSelectedSummary
				: null;
		const api =
			isWorkbenchRoot && pp3Api
				? pp3Api
				: kentender_procurement &&
					kentender_procurement.PlanningSelectedSummaryPanel &&
					typeof kentender_procurement.PlanningSelectedSummaryPanel.renderIdle === "function"
					? kentender_procurement.PlanningSelectedSummaryPanel
				: null;
		if (!api) {
			summaryHost.innerHTML = "";
			return;
		}
		if (o.summary && String(o.summary.title || "").trim()) {
			api.render(summaryHost, o);
			return;
		}
		api.renderIdle(summaryHost, o);
	}

	function mountPlanningWorkList(mainHost, slug, shell) {
		if (!mainHost) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		const filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
		const insertAfter = filtersHost || queueHost;
		let workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
		if (!workListHost) {
			workListHost = document.createElement("div");
			workListHost.className = "pp2-primary-work-list-host";
			workListHost.setAttribute("data-testid", "pp2-primary-work-list-host");
			if (insertAfter && insertAfter.nextSibling) {
				mainHost.insertBefore(workListHost, insertAfter.nextSibling);
			} else if (insertAfter) {
				mainHost.appendChild(workListHost);
			} else {
				mainHost.insertBefore(workListHost, mainHost.firstChild);
			}
		} else {
			const desiredNext = insertAfter ? insertAfter.nextSibling : mainHost.firstChild;
			if (insertAfter && workListHost.previousSibling !== insertAfter) {
				mainHost.insertBefore(workListHost, desiredNext);
			} else if (!insertAfter && mainHost.firstChild !== workListHost) {
				mainHost.insertBefore(workListHost, mainHost.firstChild);
			}
		}
		const isWorkbenchRoot = isPlanningHomeSlug(slug);
		const pp3Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchWorkList &&
			typeof kentender_procurement.PlanningWorkbenchWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkbenchWorkList
				: null;
		const pp2Api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkList &&
			typeof kentender_procurement.PlanningWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkList
				: null;
		const api = isWorkbenchRoot ? pp3Api : pp2Api;
		const onSelect = function (_itemId, item) {
			if (!shell) return;
			const summaryApi =
				isWorkbenchRoot
					? kentender_procurement &&
						kentender_procurement.PlanningWorkbenchSelectedSummary &&
						typeof kentender_procurement.PlanningWorkbenchSelectedSummary.summaryFromWorkItem === "function"
						? kentender_procurement.PlanningWorkbenchSelectedSummary
						: null
					: kentender_procurement &&
						kentender_procurement.PlanningSelectedSummaryPanel &&
						typeof kentender_procurement.PlanningSelectedSummaryPanel.summaryFromWorkItem === "function"
						? kentender_procurement.PlanningSelectedSummaryPanel
					: null;
			if (summaryApi && item) {
				const summary = summaryApi.summaryFromWorkItem(item);
				mountPlanningSelectedSummary(shell, {
					slug: slug,
					summary: summary,
					onPrimaryAction: function (action) {
						if (String((action && action.action) || "").trim() === "include_in_plan") {
							openWorkbenchIncludePlanModal(shell, item, slug);
						}
					},
					onEvidenceAction: isWorkbenchRoot
						? function (selectedSummary) {
							openWorkbenchEvidenceDrawer(selectedSummary || summary);
						}
						: null,
				});
			}
		};
		if (api) {
			let queueKey = "needs_planning";
			if (isWorkbenchRoot) {
				const queueTabsApi =
					kentender_procurement &&
					kentender_procurement.PlanningWorkbenchQueueTabs &&
					typeof kentender_procurement.PlanningWorkbenchQueueTabs.readActiveFromUrl === "function"
						? kentender_procurement.PlanningWorkbenchQueueTabs
						: null;
				if (queueTabsApi) {
					queueKey = String(queueTabsApi.readActiveFromUrl() || "").trim() || "needs_planning";
				}
				if (!WORKBENCH_QUEUE_BY_UI_QUEUE[queueKey]) {
					queueKey = "needs_planning";
				}
				api.renderForSlug(workListHost, slug, { queue: queueKey, onSelect: onSelect });
				return;
			}
			api.renderForSlug(workListHost, slug, { items: [], onSelect: onSelect });
			return;
		}
		workListHost.innerHTML = "";
	}

	function bindWorkbenchQueueRefresh(mainHost, slug, shell) {
		if (!mainHost || !isPlanningHomeSlug(slug)) return;
		const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
		if (!queueHost || queueHost.getAttribute("data-pp3-work-list-bound") === "1") return;
		queueHost.setAttribute("data-pp3-work-list-bound", "1");
		queueHost.addEventListener("click", function () {
			window.requestAnimationFrame(function () {
				mountPlanningWorkList(mainHost, slug, shell);
			});
		});
	}

	function slugifySidebarKey(value) {
		const raw = String(value || "").trim();
		if (!raw) return "";
		try {
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(raw);
			}
		} catch (e) {
			/* ignore */
		}
		return raw.toLowerCase().replace(/\s+/g, "-");
	}

	function resolveRouteSidebarPayload() {
		try {
			const route = (frappe.get_route && frappe.get_route()) || [];
			if (!route.length) return null;
			let entity = "";
			if (route[0] === "Workspaces") {
				entity = route[1] === "private" ? route[2] : route[1];
			} else if (route.length === 1) {
				entity = route[0];
			} else {
				entity = route[1];
			}
			const keyRaw = String(entity || "").trim();
			if (!keyRaw) return null;
			const bag = (frappe.boot && frappe.boot.workspace_sidebar_item) || {};
			return bag[keyRaw.toLowerCase()] || bag[slugifySidebarKey(keyRaw)] || null;
		} catch (e) {
			return null;
		}
	}

	function patchSidebarSingleSegmentFastpath() {
		if (sidebarFastpathPatched) return;
		try {
			if (!frappe.ui || !frappe.ui.Sidebar || !frappe.ui.Sidebar.prototype) {
				return;
			}
			const proto = frappe.ui.Sidebar.prototype;
			const original = proto.set_workspace_sidebar;
			if (typeof original !== "function" || original.__ktSingleSegmentFastpathPatched) {
				sidebarFastpathPatched = true;
				return;
			}
			const patched = function (router) {
				try {
					const mapped = resolveRouteSidebarPayload();
					if (mapped && mapped.label) {
						this.setup(mapped.label);
						return;
					}
				} catch (e) {
					/* ignore */
				}
				return original.call(this, router);
			};
			patched.__ktSingleSegmentFastpathPatched = true;
			proto.set_workspace_sidebar = patched;
			sidebarFastpathPatched = true;
		} catch (e2) {
			/* ignore */
		}
	}

	function patchSidebarLookupBySlug() {
		if (sidebarLookupPatched) return;
		try {
			if (!frappe.ui || !frappe.ui.Sidebar || !frappe.ui.Sidebar.prototype) {
				return;
			}
			const proto = frappe.ui.Sidebar.prototype;
			const original = proto.get_workspace_sidebars;
			if (typeof original !== "function" || original.__ktSlugLookupPatched) {
				sidebarLookupPatched = true;
				return;
			}
			const patched = function (link_to) {
				const requested = slugifySidebarKey(link_to);
				let sidebars = [];
				try {
					Object.entries(this.all_sidebar_items || {}).forEach(function (pair) {
						const sidebar = pair[1] || {};
						const items = sidebar.items || [];
						const label = sidebar.label || pair[0];
						for (let i = 0; i < items.length; i += 1) {
							const itemLink = items[i] && items[i].link_to;
							if (!itemLink) continue;
							if (String(itemLink) === String(link_to) || slugifySidebarKey(itemLink) === requested) {
								sidebars.push(label);
								break;
							}
						}
					});
				} catch (e) {
					/* ignore */
				}
				return sidebars;
			};
			patched.__ktSlugLookupPatched = true;
			proto.get_workspace_sidebars = patched;
			sidebarLookupPatched = true;
		} catch (e2) {
			/* ignore */
		}
	}

	function pruneDuplicatePrimaryShells(activeShell) {
		if (!activeShell || !activeShell.parentNode) return;
		const shells = document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]');
		for (let i = 0; i < shells.length; i += 1) {
			const shell = shells[i];
			if (shell === activeShell) continue;
			if (shell.parentNode) {
				shell.parentNode.removeChild(shell);
			}
		}
	}

	function ensurePrimaryWorkspaceShell(root, slug) {
		if (!root) return null;
		const surface = surfaceForSlug(slug);
		let shell =
			root.closest('[data-testid="pp2-primary-workspace-shell"]') ||
			document.querySelector('[data-testid="pp2-primary-workspace-shell"]');
		if (shell && !shell.isConnected) {
			shell = null;
		}
		if (!shell) {
			shell = document.createElement("section");
			shell.className = "pp2-primary-workspace-shell";
			shell.setAttribute("data-testid", "pp2-primary-workspace-shell");
			const collapsed = readRightPanelCollapsed();
			shell.setAttribute("data-right-panel-collapsed", collapsed ? "1" : "0");
			shell.innerHTML =
				'<div class="pp2-primary-workspace-shell__marker" data-testid="pp3-procurement-planning-shell" aria-hidden="true"></div>' +
				'<div class="pp2-primary-workspace-shell__header">' +
				'<div class="pp2-primary-workspace-shell__breadcrumb text-muted small" data-testid="pp2-primary-breadcrumb"></div>' +
				'<div class="pp2-primary-workspace-shell__context" data-testid="pp2-primary-context-host"></div>' +
				"</div>" +
				'<div class="pp2-primary-workspace-shell__layout">' +
				'<div class="pp2-primary-workspace-shell__main" data-testid="pp2-primary-main-host"></div>' +
				'<aside class="pp2-primary-workspace-shell__right" data-testid="pp2-primary-right-panel">' +
				'<div class="pp2-primary-workspace-shell__right-body" data-testid="pp2-primary-right-panel-body">' +
				'<div class="pp2-primary-summary-host" data-testid="pp2-primary-summary-host"></div>' +
				'<div class="pp2-primary-workspace-shell__next-action text-muted small" data-testid="pp2-primary-next-action-panel"></div>' +
				"</div>" +
				'<div class="pp2-primary-workspace-shell__right-footer" data-testid="pp2-primary-right-panel-footer">' +
				'<button type="button" class="btn btn-xs btn-link pp2-primary-workspace-shell__toggle text-muted" data-testid="pp2-primary-right-panel-toggle" aria-label="' +
				esc(__("Collapse panel")) +
				'"></button>' +
				"</div>" +
				"</aside>" +
				"</div>";
			root.parentNode.insertBefore(shell, root);
		}

		let mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (!mainHost) {
			if (shell.parentNode) {
				shell.parentNode.removeChild(shell);
			}
			return ensurePrimaryWorkspaceShell(root, slug);
		}

		if (mainHost && root.parentNode !== mainHost) {
			mainHost.appendChild(root);
		}
		shell.setAttribute("data-surface", String(slug || "workbench").trim() || "workbench");
		pruneDuplicatePrimaryShells(shell);

		const breadcrumb = shell.querySelector('[data-testid="pp2-primary-breadcrumb"]');
		if (breadcrumb) {
			breadcrumb.textContent = __("Procurement Planning") + " / " + surface.subtitle;
		}
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost && !isPlanningHomeSlug(slug)) {
			mountPlanningContext(contextHost, slug);
		}
		const nextActionPanel = shell.querySelector('[data-testid="pp2-primary-next-action-panel"]');
		if (nextActionPanel) {
			nextActionPanel.innerHTML = "";
		}

		const toggle = shell.querySelector('[data-testid="pp2-primary-right-panel-toggle"]');
		if (toggle && toggle.getAttribute("data-bound") !== "1") {
			toggle.setAttribute("data-bound", "1");
			toggle.addEventListener("click", function () {
				const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
				shell.setAttribute("data-right-panel-collapsed", collapsed ? "0" : "1");
				writeRightPanelCollapsed(!collapsed);
				toggle.textContent = collapsed ? __("Collapse panel") : __("Expand panel");
				toggle.setAttribute(
					"aria-label",
					collapsed ? __("Collapse panel") : __("Expand panel"),
				);
			});
		}
		if (toggle) {
			const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
			toggle.textContent = collapsed ? __("Expand panel") : __("Collapse panel");
			toggle.setAttribute(
				"aria-label",
				collapsed ? __("Expand panel") : __("Collapse panel"),
			);
		}
		if (isPlanningHomeSlug(slug)) {
			shell.removeAttribute("data-pp2-home-layout");
			ensureSummaryHost(shell);
			mountPlanningSelectedSummary(shell, { slug: slug });
		} else {
			shell.removeAttribute("data-pp2-home-layout");
			ensureSummaryHost(shell);
			mountPlanningSelectedSummary(shell, { slug: slug });
		}

		return shell;
	}

	function syncSidebarActive(slug) {
		try {
			const target = String(SURFACE_LABELS[slug || ""] || SURFACE_LABELS[""]).trim().toLowerCase();
			const items = document.querySelectorAll(".standard-sidebar-item");
			for (let i = 0; i < items.length; i += 1) {
				const label = String(items[i].textContent || "")
					.trim()
					.toLowerCase();
				items[i].classList.toggle("active-sidebar", label === target);
			}
		} catch (e) {
			/* ignore */
		}
	}

	function collapsePlanningSidebarParent(parent, attempt) {
		if (!parent || isPlanningWorkspaceRoute()) return;
		const nested = parent.querySelector(".nested-container");
		const dropIcon = parent.querySelector(".drop-icon");
		if (!nested || !dropIcon || typeof dropIcon.click !== "function") return;
		if (window.getComputedStyle(nested).display === "none") return;
		dropIcon.click();
		if ((attempt || 0) < 3) {
			window.setTimeout(function () {
				collapsePlanningSidebarParent(parent, (attempt || 0) + 1);
			}, 60);
		}
	}

	function enhanceSidebarVisualHierarchy(slug, parentActive) {
		return false;
	}

	const FORBIDDEN_PLANNING_NAV_LABELS = {
		"approved demands": true,
		packages: true,
		"planning evidence": true,
		"planning inclusion detail": true,
		"release package detail": true,
		"readiness review": true,
		"review & approval": true,
		"package lines": true,
		"technical details": true,
		"audit trail": true,
		"planning release package": true,
		"planning release package view": true,
		"release to tender review": true,
		"advanced / technical details": true,
	};

	const FORBIDDEN_PLANNING_HREF_SUBSTRINGS = [
		"/procurement-planning/approved-demands",
		"/procurement-planning/packages",
		"/procurement-planning/evidence",
		"/procurement-planning/inclusions",
		"/procurement-planning/readiness",
		"/procurement-planning/review",
		"/procurement-planning/lines",
		"/procurement-planning/technical",
		"/procurement-planning/audit",
		"/procurement-planning/releases/",
	];

	function planningNestedNavAnchors() {
		return Array.from(document.querySelectorAll(".item-anchor"));
	}

	function isForbiddenPlanningNavLink(label, href) {
		const normalizedLabel = String(label || "")
			.trim()
			.toLowerCase();
		const normalizedHref = String(href || "").toLowerCase();
		if (FORBIDDEN_PLANNING_NAV_LABELS[normalizedLabel]) return true;
		for (let i = 0; i < FORBIDDEN_PLANNING_HREF_SUBSTRINGS.length; i += 1) {
			if (normalizedHref.indexOf(FORBIDDEN_PLANNING_HREF_SUBSTRINGS[i]) !== -1) return true;
		}
		return false;
	}

	function pruneForbiddenPlanningNavLinks() {
		const anchors = planningNestedNavAnchors();
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "");
			const href = String(anchor.getAttribute("href") || "");
			if (!isForbiddenPlanningNavLink(label, href)) continue;
			const item = anchor.closest(".sidebar-item-container");
			if (item) {
				item.remove();
			} else {
				anchor.remove();
			}
		}
	}

	function normalizeChildLinkRoutes() {
		pruneForbiddenPlanningNavLinks();
		const anchors = planningNestedNavAnchors();
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			if (!(anchor instanceof HTMLAnchorElement)) continue;
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const rawLabel = String(labelEl ? labelEl.textContent || "" : "").trim().toLowerCase();
			if (rawLabel !== "planning workbench" && rawLabel !== "procurement planning" && rawLabel !== "workbench") {
				continue;
			}
			if (labelEl) {
				labelEl.textContent = __("Planning Workbench");
			}
			anchor.setAttribute("href", ROOT_PATH);
			anchor.setAttribute("data-testid", "pp4-nav-planning-workbench");
		}
	}

	function queueSidebarRefresh() {
		if (sidebarRefreshQueued) return;
		sidebarRefreshQueued = true;
		window.requestAnimationFrame(function () {
			sidebarRefreshQueued = false;
			scheduleBoot();
		});
	}

	function elementTouchesSidebar(el) {
		if (!el || !el.matches) return false;
		if (el.matches(".layout-side-section, .layout-side-section *")) return true;
		return !!(el.querySelector && el.querySelector(".layout-side-section"));
	}

	function ensureSidebarObserver() {
		if (sidebarObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		sidebarObserver = new MutationObserver(function (mutations) {
			for (let i = 0; i < mutations.length; i += 1) {
				const m = mutations[i];
				if (elementTouchesSidebar(m.target)) {
					queueSidebarRefresh();
					return;
				}
				if (m.addedNodes && m.addedNodes.length) {
					for (let j = 0; j < m.addedNodes.length; j += 1) {
						if (elementTouchesSidebar(m.addedNodes[j])) {
							queueSidebarRefresh();
							return;
						}
					}
				}
				if (m.removedNodes && m.removedNodes.length) {
					for (let k = 0; k < m.removedNodes.length; k += 1) {
						if (elementTouchesSidebar(m.removedNodes[k])) {
							queueSidebarRefresh();
							return;
						}
					}
				}
			}
		});
		sidebarObserver.observe(target, { childList: true, subtree: true });
	}

	function ensureSidebarSetupListener() {
		if (sidebarSetupListenerBound) return;
		sidebarSetupListenerBound = true;
		$(document).on("sidebar_setup.kt_pp2_hierarchy", function () {
			// Frappe emits sidebar_setup before the new sidebar DOM is fully painted.
			// Defer one frame so the enhancer can find and decorate the parent node.
			window.requestAnimationFrame(function () {
				scheduleBoot();
			});
		});
	}

	function closePlanningEvidenceDrawer() {
		const pp2DrawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningEvidenceDrawer &&
			typeof kentender_procurement.PlanningEvidenceDrawer.close === "function"
				? kentender_procurement.PlanningEvidenceDrawer
				: null;
		if (pp2DrawerApi) {
			pp2DrawerApi.close();
		}
		const pp3DrawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
			typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.close === "function"
				? kentender_procurement.PlanningWorkbenchEvidenceDrawer
				: null;
		if (pp3DrawerApi) {
			pp3DrawerApi.close();
		}
	}

	function openWorkbenchEvidenceDrawer(summary) {
		const drawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
			typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.open === "function"
				? kentender_procurement.PlanningWorkbenchEvidenceDrawer
				: null;
		if (!drawerApi) return;
		const s = summary || {};
		const title = String(s.title || "").trim();
		const packageCode = String(s.packageCode || s.package_code || "").trim();
		const underlyingObjectType = String(s.underlyingObjectType || s.underlying_object_type || "").trim();
		const underlyingObjectCode = String(s.underlyingObjectCode || s.underlying_object_code || "").trim();
		drawerApi.open({
			title: title,
			package_code: packageCode,
			underlying_object_type: underlyingObjectType,
			underlying_object_code: underlyingObjectCode,
		});
	}

	function removePp2PlanningShellIfWrongRoute() {
		closePlanningEvidenceDrawer();
		document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]').forEach(function (el) {
			el.remove();
		});
		document.querySelectorAll("#kt-pp-root, .kt-pp-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-pp2-shell");
		document.body.classList.remove("kt-pp4-shell");
	}

	function mount() {
		closePlanningEvidenceDrawer();
		const planningRoute = isPlanningWorkspaceRoute();
		normalizeChildLinkRoutes();
		if (!planningRoute) {
			removePp2PlanningShellIfWrongRoute();
			return enhanceSidebarVisualHierarchy("", false);
		}

		const resolution = resolvePlanningRoute(window.location.pathname);
		if (resolution.action === "redirect" && applyPlanningRouteRedirect(resolution.redirectUrl)) {
			window.requestAnimationFrame(function () {
				scheduleBoot();
			});
			return true;
		}

		const slug =
			resolution.action === "canonical"
				? resolution.slug != null
					? resolution.slug
					: readSurfaceSlug()
				: readSurfaceSlug();
		const hierarchyReady = enhanceSidebarVisualHierarchy(slug, planningRoute);
		const root = ensureWorkspaceRoot();
		if (!root) return false;

		if (resolution.action === "not_found") {
			renderRouteNotFound(root);
			document.body.classList.remove("kt-pp2-shell");
			document.body.classList.add("kt-pp4-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}

		const searchParams = new URLSearchParams(window.location.search || "");
		const hasPackageCode = searchParams.has("package_code");
		const hasWorkbenchState = hasWorkbenchStateQuery(searchParams);
		const hasApprovedDemandQuery = searchParams.has("queue") || searchParams.has("item");
		const hasPlanCode = searchParams.has("plan");
		syncSurfaceUrl(slug, {
			preserveSearch: slug === "" && (hasPackageCode || hasWorkbenchState || hasApprovedDemandQuery || hasPlanCode),
		});
		canonicalizeWorkbenchStateQuery();
		const routeSignature = String(window.location.pathname || "") + "|" + String(window.location.search || "");
		document.querySelectorAll('[data-testid="pp2-primary-workspace-shell"]').forEach(function (el) {
			el.remove();
		});
		const alreadyMounted = root.getAttribute("data-pp4-mounted") === "1";
		const lastSignature = pp4MountSignatureByRoot.get(root) || "";
		if (alreadyMounted && lastSignature === routeSignature) {
			document.body.classList.remove("kt-pp2-shell");
			document.body.classList.add("kt-pp4-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}
		renderPlanningWorkbenchV4(root);
		root.setAttribute("data-pp4-mounted", "1");
		pp4MountSignatureByRoot.set(root, routeSignature);
		pp4PackageItemsByRoot.set(root, []);
		pp4QueueItemsByRoot.set(root, {});
		pp4SearchTermByRoot.set(root, "");
		pp4SortModeByRoot.set(root, "newest");
		pp4SortMenuOpenByRoot.set(root, false);
		pp4FilterDrawerOpenByRoot.set(root, false);
		pp4FilterDraftByRoot.set(root, pp4DefaultFilterState());
		pp4FilterAppliedByRoot.set(root, pp4DefaultFilterState());
		// Design pass only: keep this screen static (no backend wiring yet).
		document.body.classList.remove("kt-pp2-shell");
		document.body.classList.add("kt-pp4-shell");
		syncSidebarActive("");
		return hierarchyReady;
	}

	function scheduleBoot() {
		patchSidebarSingleSegmentFastpath();
		patchSidebarLookupBySlug();
		ensureSidebarObserver();
		ensureSidebarSetupListener();
		bootRunToken += 1;
		const token = bootRunToken;
		if (bootRetryTimer) {
			clearTimeout(bootRetryTimer);
			bootRetryTimer = null;
		}
		if (mount()) return;
		let retries = 0;
		const retry = function () {
			if (token !== bootRunToken) return;
			retries += 1;
			if (mount() || retries >= 10) {
				bootRetryTimer = null;
				return;
			}
			bootRetryTimer = window.setTimeout(retry, 70);
		};
		bootRetryTimer = window.setTimeout(retry, 70);
	}

	$(document).on("page-change", scheduleBoot);
	$(document).on("app_ready", scheduleBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleBoot);
	}
	patchSidebarSingleSegmentFastpath();
	patchSidebarLookupBySlug();
	scheduleBoot();
})();
