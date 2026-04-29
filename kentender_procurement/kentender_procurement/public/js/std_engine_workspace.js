// STD Engine workbench shell — STD-CURSOR-1001 (route + layout scaffold only).

(function () {
	const WS_NAME = "STD Engine";
	const HIGH_RISK_KPI_IDS = new Set(["validation_blocked", "generation_failures", "addendum_impact_pending"]);
	let bindScheduled = false;
	let hooksBound = false;
	let domObserver = null;
	let activeKpiId = null;
	let activeQueueId = null;
	let activeWorkTab = null;
	let kpiRows = [];
	let scopeTabs = [];
	let queueRows = [];
	let searchQuery = "";
	let searchResults = [];
	let activeFilters = {};
	let searchDebounceTimer = null;
	let selectedObjectCode = "";
	let selectedObjectType = "";
	let filtersCollapsed = true;
	let detailReqId = 0;
	let detailLastPayload = null;
	let detailLastListRow = null;
	let detailTabMode = "generic";
	let detailActiveTab = "overview";
	let templateVersionSummary = null;
	let templateVersionSummaryError = null;
	let templateVersionStructure = null;
	let templateVersionStructureError = null;
	let templateVersionStructureLoading = false;
	let templateVersionParameters = null;
	let templateVersionParametersError = null;
	let templateVersionParametersLoading = false;
	let templateVersionForms = null;
	let templateVersionFormsError = null;
	let templateVersionFormsLoading = false;
	let activeFormsCategoryId = "";
	let selectedFormCode = "";
	let templateVersionWorks = null;
	let templateVersionWorksError = null;
	let templateVersionWorksLoading = false;
	let templateVersionMappings = null;
	let templateVersionMappingsError = null;
	let templateVersionMappingsLoading = false;
	let templateVersionReviews = null;
	let templateVersionReviewsError = null;
	let templateVersionReviewsLoading = false;
	let templateVersionAudit = null;
	let templateVersionAuditError = null;
	let templateVersionAuditLoading = false;
	let activeMappingsTargetModel = "Bundle";
	let selectedStructureKind = "";
	let selectedStructureCode = "";
	let stdInstanceWorkbenchShell = null;
	let stdInstanceWorkbenchShellError = null;
	let stdInstanceParameters = null;
	let stdInstanceParametersError = null;
	let stdInstanceParametersLoading = false;
	let stdInstanceWorks = null;
	let stdInstanceWorksError = null;
	let stdInstanceWorksLoading = false;
	let stdInstanceBoq = null;
	let stdInstanceBoqError = null;
	let stdInstanceBoqLoading = false;
	let stdInstanceOutputs = null;
	let stdInstanceOutputsError = null;
	let stdInstanceOutputsLoading = false;
	let stdInstanceReadiness = null;
	let stdInstanceReadinessError = null;
	let stdInstanceReadinessLoading = false;
	let stdInstanceReadinessRunning = false;
	let stdInstanceAddendum = null;
	let stdInstanceAddendumError = null;
	let stdInstanceAddendumLoading = false;
	let stdInstanceDownstream = null;
	let stdInstanceDownstreamError = null;
	let stdInstanceDownstreamLoading = false;
	let stdInstanceAudit = null;
	let stdInstanceAuditError = null;
	let stdInstanceAuditLoading = false;
	const STRUCTURE_LOCKED_SECTION_WARNING = __(
		"This section is locked standard text and cannot be edited in a tender-specific STD instance."
	);

	function esc(v) {
		if (v == null) return "";
		return String(v)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function routeLooksLikeStdEngine() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route.map((x) => String(x || "").toLowerCase());
				if (r[0] === "std-engine") return true;
				if (r[0] === "workspaces" && r.length >= 2) {
					const w = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (w === "std-engine" || w === "std engine") return true;
				}
			}
		} catch (e) { }
		try {
			const dr = (document.body && document.body.getAttribute("data-route")) || "";
			if (/std-engine|std%20engine|std engine/i.test(dr)) return true;
		} catch (e) { }
		try {
			const loc = decodeURIComponent(String(window.location.pathname + window.location.hash + window.location.search).toLowerCase());
			if (loc.includes('/std-engine') || loc.includes('std%20engine') || loc.includes('std engine')) return true;
		} catch (e) { }
		return false;
	}

	function syncBodyClass() {
		document.body.classList.toggle('kt-std-shell', routeLooksLikeStdEngine());
	}

	function pageRoot() {
		try {
			if (typeof frappe !== "undefined" && frappe.container && frappe.container.page) {
				const p = frappe.container.page;
				const route = p && p.getAttribute && p.getAttribute("data-page-route");
				if (p && p.isConnected && (route === "Workspaces" || route === "std-engine")) return p;
			}
		} catch (e) { }
		const pages = document.querySelectorAll('.page-container');
		let fallback = null;
		for (let i = 0; i < pages.length; i++) {
			const p = pages[i];
			if (!p || !p.isConnected) continue;
			if (!fallback) fallback = p;
			const route = p.getAttribute && p.getAttribute("data-page-route");
			const isVisible = p.getClientRects && p.getClientRects().length > 0;
			if (route === "Workspaces" && isVisible) return p;
			if (route === "std-engine" && isVisible) return p;
		}
		return fallback || document.querySelector('.page-container');
	}

	function resolveMount() {
		const root = pageRoot();
		if (root) {
			const local =
				root.querySelector('.layout-main-section .editor-js-container') ||
				root.querySelector('.editor-js-container') ||
				root.querySelector('.layout-main-section');
			if (local) return local;
		}
		const candidates = document.querySelectorAll('.layout-main-section .editor-js-container, .editor-js-container, .layout-main-section');
		let fallback = null;
		for (let i = 0; i < candidates.length; i++) {
			const el = candidates[i];
			if (!el || !el.isConnected) continue;
			if (!fallback) fallback = el;
			if (el.getClientRects && el.getClientRects().length > 0) return el;
		}
		return fallback;
	}

	function shellPresent() {
		const root = pageRoot();
		return !!(root && root.querySelector('.kt-std-injected-shell'));
	}

	function getActiveStdShellRoot() {
		const root = pageRoot();
		if (root) {
			const shell = root.querySelector(".kt-std-injected-shell");
			if (shell) return shell;
		}
		return document.querySelector(".kt-std-injected-shell");
	}

	function fallbackKpis() {
		return [
			{ id: "draft_versions", label: __("Draft Versions"), value: 0, testid: "std-kpi-draft-versions", select_queue_id: "draft_versions", select_work_tab: "templates" },
			{ id: "validation_blocked", label: __("Validation Blocked"), value: 0, testid: "std-kpi-validation-blocked", select_queue_id: "validation_blocked", select_work_tab: "mywork", risk_level: "high" },
			{ id: "legal_review_pending", label: __("Legal Review Pending"), value: 0, testid: "std-kpi-legal-review-pending", select_queue_id: "legal_review", select_work_tab: "templates" },
			{ id: "policy_review_pending", label: __("Policy Review Pending"), value: 0, testid: "std-kpi-policy-review-pending", select_queue_id: "policy_review", select_work_tab: "templates" },
			{ id: "active_versions", label: __("Active Versions"), value: 0, testid: "std-kpi-active-versions", select_queue_id: "active_versions", select_work_tab: "active_versions" },
			{ id: "instances_blocked", label: __("Instances Blocked"), value: 0, testid: "std-kpi-instances-blocked", select_queue_id: "instance_blocked", select_work_tab: "instances" },
			{ id: "generation_failures", label: __("Generation Failures"), value: 0, testid: "std-kpi-generation-failures", select_queue_id: "generation_failed", select_work_tab: "generation_jobs", risk_level: "high" },
			{ id: "addendum_impact_pending", label: __("Addendum Impact Pending"), value: 0, testid: "std-kpi-addendum-impact-pending", select_queue_id: "addendum_impact", select_work_tab: "addendum_impacts", risk_level: "high" },
		];
	}

	function fallbackScopeTabs() {
		return [
			{ id: "mywork", label: __("My Work"), testid: "std-scope-my-work" },
			{ id: "templates", label: __("Templates"), testid: "std-scope-templates" },
			{ id: "active_versions", label: __("Active Versions"), testid: "std-scope-active-versions" },
			{ id: "instances", label: __("STD Instances"), testid: "std-scope-std-instances" },
			{ id: "generation_jobs", label: __("Generation Jobs"), testid: "std-scope-generation-jobs" },
			{ id: "addendum_impacts", label: __("Addendum Impacts"), testid: "std-scope-addendum-impacts" },
			{ id: "audit_view", label: __("Audit View"), testid: "std-scope-audit-view" },
		];
	}

	function fallbackQueues() {
		return [
			{ id: "draft_versions", label: __("Draft Versions"), scope_tab_id: "templates", testid: "std-queue-draft-versions" },
			{ id: "structure_in_progress", label: __("Structure In Progress"), scope_tab_id: "templates", testid: "std-queue-structure-in-progress" },
			{ id: "validation_blocked", label: __("Validation Blocked"), scope_tab_id: "mywork", testid: "std-queue-validation-blocked" },
			{ id: "validation_passed", label: __("Validation Passed"), scope_tab_id: "templates", testid: "std-queue-validation-passed" },
			{ id: "legal_review", label: __("Legal Review"), scope_tab_id: "templates", testid: "std-queue-legal-review" },
			{ id: "policy_review", label: __("Policy Review"), scope_tab_id: "templates", testid: "std-queue-policy-review" },
			{ id: "approved", label: __("Approved"), scope_tab_id: "templates", testid: "std-queue-approved" },
			{ id: "active_versions", label: __("Active"), scope_tab_id: "active_versions", testid: "std-queue-active" },
			{ id: "suspended", label: __("Suspended"), scope_tab_id: "active_versions", testid: "std-queue-suspended" },
			{ id: "superseded", label: __("Superseded"), scope_tab_id: "active_versions", testid: "std-queue-superseded" },
			{ id: "draft_instances", label: __("Draft Instances"), scope_tab_id: "instances", testid: "std-queue-draft-instances" },
			{ id: "instance_blocked", label: __("Instance Blocked"), scope_tab_id: "instances", testid: "std-queue-instance-blocked" },
			{ id: "instance_ready", label: __("Instance Ready"), scope_tab_id: "instances", testid: "std-queue-instance-ready" },
			{ id: "published_locked", label: __("Published Locked"), scope_tab_id: "instances", testid: "std-queue-published-locked" },
			{ id: "generation_failed", label: __("Generation Failed"), scope_tab_id: "generation_jobs", testid: "std-queue-generation-failed" },
			{ id: "addendum_impact", label: __("Addendum Impact"), scope_tab_id: "addendum_impacts", testid: "std-queue-addendum-impact" },
			{ id: "archived", label: __("Archived"), scope_tab_id: "audit_view", testid: "std-queue-archived" },
		];
	}

	function renderQueueStateHint() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const indicator = root.querySelector('[data-testid="std-active-queue-state"]');
		if (!indicator) return;
		const queueText = activeQueueId ? __("Queue") + ": " + activeQueueId : __("No queue selected yet.");
		const tabText = activeWorkTab ? __("Scope") + ": " + activeWorkTab : "";
		indicator.textContent = queueText + (tabText ? " · " + tabText : "");
	}

	function renderScopeTabs() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector("#kt-std-scope-host");
		if (!host) return;
		const tabs = scopeTabs.length ? scopeTabs : fallbackScopeTabs();
		let html = "";
		for (let i = 0; i < tabs.length; i++) {
			const tab = tabs[i] || {};
			const id = String(tab.id || "scope_" + i);
			const label = String(tab.label || "");
			const isActive = activeWorkTab === id;
			html +=
				'<button type="button" class="kt-std-scope-tab btn btn-xs ' +
				(isActive ? "btn-primary is-active" : "btn-default") +
				'" data-std-scope-tab="' +
				esc(id) +
				'" data-testid="' +
				esc(String(tab.testid || "std-scope-" + id.replace(/_/g, "-"))) +
				'">' +
				esc(label) +
				"</button>";
		}
		host.innerHTML = html;
	}

	function renderQueueBar() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector("#kt-std-queue-host");
		if (!host) return;
		const queues = queueRows.length ? queueRows : fallbackQueues();
		let html = "";
		for (let i = 0; i < queues.length; i++) {
			const q = queues[i] || {};
			const id = String(q.id || "queue_" + i);
			const label = String(q.label || "");
			const scopeId = String(q.scope_tab_id || "");
			const isVisible = !activeWorkTab || !scopeId || scopeId === activeWorkTab;
			const isActive = activeQueueId === id;
			html +=
				'<button type="button" class="kt-std-queue-chip btn btn-xs ' +
				(isActive ? "btn-primary is-active" : "btn-default") +
				'" data-std-queue="' +
				esc(id) +
				'" data-std-queue-scope="' +
				esc(scopeId) +
				'" data-testid="' +
				esc(String(q.testid || "std-queue-" + id.replace(/_/g, "-"))) +
				'"' +
				(isVisible ? "" : ' hidden="hidden"') +
				">" +
				esc(label) +
				"</button>";
		}
		host.innerHTML = html;
	}

	function filterFields() {
		return [
			{ id: "object_type", label: __("Object Type"), type: "select", options: ["", "Template Version", "Applicability Profile", "STD Instance", "Generation Job", "Generated Output", "Addendum Impact", "Readiness Run"] },
			{ id: "procurement_category", label: __("Procurement Category"), type: "select", options: ["", "Works", "Goods", "Services"] },
			{ id: "works_profile_type", label: __("Works Profile Type"), type: "text" },
			{ id: "template_version_status", label: __("Template Version Status"), type: "text" },
			{ id: "profile_status", label: __("Profile Status"), type: "text" },
			{ id: "instance_status", label: __("Instance Status"), type: "text" },
			{ id: "readiness_status", label: __("Readiness Status"), type: "text" },
			{ id: "generation_status", label: __("Generation Status"), type: "text" },
			{ id: "output_status", label: __("Output Status"), type: "text" },
			{ id: "legal_review_status", label: __("Legal Review Status"), type: "text" },
			{ id: "policy_review_status", label: __("Policy Review Status"), type: "text" },
			{ id: "has_critical_blockers", label: __("Has Critical Blockers"), type: "check" },
			{ id: "has_failed_generation", label: __("Has Failed Generation"), type: "check" },
			{ id: "used_by_published_tender", label: __("Used by Published Tender"), type: "check" },
			{ id: "created_from", label: __("Created/Updated From"), type: "date" },
			{ id: "created_to", label: __("Created/Updated To"), type: "date" },
			{ id: "assigned_to_me", label: __("Assigned To Me"), type: "check" },
		];
	}

	function renderFilterPanel() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector('[data-testid="std-filter-panel"]');
		if (!host) return;
		const fields = filterFields();
		let html =
			'<div class="kt-std-filter-header">' +
			'<span class="kt-std-filter-title">' +
			esc(__("Filters")) +
			"</span>" +
			'<button type="button" class="btn btn-xs btn-default" data-std-filter-toggle data-testid="std-filter-toggle">' +
			esc(filtersCollapsed ? __("Show Filters") : __("Hide Filters")) +
			"</button>" +
			"</div>" +
			'<div class="kt-std-filter-controls">';
		for (let i = 0; i < fields.length; i++) {
			const f = fields[i];
			if (f.type === "select") {
				html += '<label class="kt-std-filter-item"><span>' + esc(f.label) + '</span><select class="form-control form-control-xs" data-std-filter="' + esc(f.id) + '">';
				for (let j = 0; j < f.options.length; j++) {
					const o = String(f.options[j] || "");
					html += '<option value="' + esc(o) + '">' + esc(o || "Any") + "</option>";
				}
				html += "</select></label>";
			} else if (f.type === "check") {
				html += '<label class="kt-std-filter-item kt-std-filter-item--check"><input type="checkbox" data-std-filter="' + esc(f.id) + '" /> ' + esc(f.label) + "</label>";
			} else {
				html += '<label class="kt-std-filter-item"><span>' + esc(f.label) + '</span><input class="form-control form-control-xs" type="' + esc(f.type) + '" data-std-filter="' + esc(f.id) + '" /></label>';
			}
		}
		html += '</div><div class="kt-std-filter-chips" data-testid="std-active-filter-chips"></div>';
		host.innerHTML = html;
		renderFilterCollapsedState();
	}

	function renderFilterCollapsedState() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector('[data-testid="std-filter-panel"]');
		if (!host) return;
		host.classList.toggle("is-collapsed", !!filtersCollapsed);
		const btn = host.querySelector("[data-std-filter-toggle]");
		if (btn) {
			btn.textContent = filtersCollapsed ? __("Show Filters") : __("Hide Filters");
		}
	}

	function collectFiltersFromUi() {
		const root = getActiveStdShellRoot();
		if (!root) return {};
		const out = {};
		const controls = root.querySelectorAll("[data-std-filter]");
		for (let i = 0; i < controls.length; i++) {
			const c = controls[i];
			const key = c.getAttribute("data-std-filter");
			if (!key) continue;
			if (c.type === "checkbox") {
				if (c.checked) out[key] = 1;
			} else {
				const v = String(c.value || "").trim();
				if (v) out[key] = v;
			}
		}
		return out;
	}

	function renderFilterChips() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector('[data-testid="std-active-filter-chips"]');
		if (!host) return;
		const keys = Object.keys(activeFilters || {});
		if (!keys.length) {
			host.innerHTML = '<span class="text-muted">' + esc(__("No active filters")) + "</span>";
			return;
		}
		let html = "";
		for (let i = 0; i < keys.length; i++) {
			const k = keys[i];
			html += '<span class="kt-std-filter-chip" data-testid="std-filter-chip-' + esc(k.replace(/_/g, "-")) + '">' + esc(k + ": " + activeFilters[k]) + "</span>";
		}
		host.innerHTML = html;
	}

	function renderObjectListResults() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector('[data-testid="std-object-list"]');
		if (!host) return;
		const rows = searchResults || [];
		let html = '<h3 class="h6 mb-1">' + esc(__("Object List")) + '</h3>';
		if (!rows.length) {
			html += '<p class="small text-muted mb-0" data-testid="std-search-results-empty">' + esc(__("No objects match current search and filters.")) + "</p>";
			host.innerHTML = html;
			return;
		}
		html += '<div class="small text-muted mb-1" data-testid="std-search-results-count">' + esc(__("Results")) + ": " + esc(String(rows.length)) + "</div>";
		html += '<ul class="kt-std-results-list">';
		for (let i = 0; i < rows.length; i++) {
			const r = rows[i];
			const isActive = selectedObjectCode && selectedObjectCode === String(r.code || "");
			const badgeA =
				r.procurement_category
					? '<span class="kt-std-row-badge">' + esc(String(r.procurement_category || "")) + "</span>"
					: "";
			const badgeB =
				r.readiness_status
					? '<span class="kt-std-row-badge">' + esc(String(r.readiness_status || "")) + "</span>"
					: "";
			const subtitle = (() => {
				if (r.object_type === "Template Version") {
					return __("Family") + ": " + String(r.template_code || "—");
				}
				if (r.object_type === "Applicability Profile") {
					return __("Version") + ": " + String(r.version_code || "—");
				}
				if (r.object_type === "STD Instance") {
					return __("Tender") + ": " + String(r.tender_code || "—");
				}
				if (r.object_type === "Generated Output") {
					return __("Output") + ": " + String(r.output_type || "—");
				}
				if (r.object_type === "Generation Job") {
					return __("Job") + ": " + String(r.job_type || "—");
				}
				if (r.object_type === "Addendum Impact") {
					return __("Addendum") + ": " + String(r.addendum_code || "—");
				}
				return __("Status") + ": " + String(r.status || "—");
			})();
			html +=
				'<li class="kt-std-results-list__item' +
				(isActive ? " is-active" : "") +
				'" data-std-object-code="' +
				esc(String(r.code || "")) +
				'" data-std-object-type="' +
				esc(String(r.object_type || "")) +
				'" data-testid="std-row-' +
				esc(String(r.object_type || "").toLowerCase().replace(/[^a-z0-9]+/g, "-")) +
				'">' +
				'<div class="kt-std-row-line-1"><span class="kt-std-results-list__code">' +
				esc(String(r.code || "")) +
				"</span> · " +
				esc(String(r.title || "")) +
				"</div>" +
				'<div class="kt-std-row-line-2 text-muted">' +
				esc(subtitle) +
				"</div>" +
				'<div class="kt-std-row-line-3 text-muted">' +
				esc(String(r.object_type || "")) +
				" · " +
				esc(String(r.status || "")) +
				"</div>" +
				'<div class="kt-std-row-badges">' +
				badgeA +
				badgeB +
				"</div>" +
				"</li>";
		}
		html += "</ul>";
		host.innerHTML = html;
	}

	function stdListScrollHost(root) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.listHost === "function") {
			return helper.listHost(root, ".kt-std-results-list");
		}
		if (!root) return null;
		return root.querySelector(".kt-std-results-list");
	}

	function stdReadListScrollTop(root) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.readScrollTop === "function") {
			return helper.readScrollTop(root, ".kt-std-results-list");
		}
		const host = stdListScrollHost(root);
		return host && typeof host.scrollTop === "number" ? host.scrollTop : 0;
	}

	function stdRestoreListScrollTop(root, top, selectedCode) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.restoreScrollTop === "function") {
			helper.restoreScrollTop(
				root,
				".kt-std-results-list",
				top,
				selectedCode,
				"[data-std-object-code]",
				"data-std-object-code"
			);
			return;
		}
		const host = stdListScrollHost(root);
		if (!host) return;
		host.scrollTop = typeof top === "number" ? top : 0;
		if (!selectedCode) return;
		let sel = null;
		host.querySelectorAll("[data-std-object-code]").forEach(function (el) {
			if (el.getAttribute("data-std-object-code") === selectedCode) sel = el;
		});
		if (!sel || typeof sel.getBoundingClientRect !== "function") return;
		const rowRect = sel.getBoundingClientRect();
		const listRect = host.getBoundingClientRect();
		if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
			sel.scrollIntoView({ block: "nearest" });
		}
	}

	function syncStdListSelection(root, selectedCode) {
		const helper = window.KTWorkspaceListSelection;
		if (helper && typeof helper.syncSelection === "function") {
			helper.syncSelection(
				root,
				".kt-std-results-list",
				"[data-std-object-code]",
				"data-std-object-code",
				selectedCode,
				"is-active"
			);
			return;
		}
		const host = stdListScrollHost(root);
		if (!host) return;
		host.querySelectorAll("[data-std-object-code]").forEach(function (el) {
			const code = el.getAttribute("data-std-object-code");
			const on = !!selectedCode && code === selectedCode;
			el.classList.toggle("is-active", on);
			el.setAttribute("aria-selected", on ? "true" : "false");
		});
	}

	function actionTestId(actionId) {
		return "std-action-" + String(actionId || "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "unknown";
	}

	function injectGenericDetailTabs(tabsHost) {
		if (!tabsHost) return;
		tabsHost.classList.remove("kt-std-detail-tabs--template");
		tabsHost.classList.remove("kt-std-detail-tabs--instance");
		tabsHost.innerHTML =
			'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab is-active" data-std-detail-tab="overview" data-testid="std-detail-tab-overview" aria-selected="true">' +
			esc(__("Overview")) +
			'</button>' +
			'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab" data-std-detail-tab="audit" data-testid="std-detail-tab-audit" aria-selected="false">' +
			esc(__("Audit")) +
			"</button>";
	}

	function injectTemplateVersionDetailTabs(tabsHost) {
		if (!tabsHost) return;
		tabsHost.classList.remove("kt-std-detail-tabs--instance");
		tabsHost.classList.add("kt-std-detail-tabs--template");
		const tabs = [
			{ key: "tpl-overview", tid: "std-tab-template-overview", lab: __("Overview") },
			{ key: "tpl-structure", tid: "std-tab-template-structure", lab: __("Structure") },
			{ key: "tpl-parameters", tid: "std-tab-template-parameters", lab: __("Parameters") },
			{ key: "tpl-forms", tid: "std-tab-template-forms", lab: __("Forms") },
			{ key: "tpl-works", tid: "std-tab-works-configuration", lab: __("Works Configuration") },
			{ key: "tpl-mappings", tid: "std-tab-mappings", lab: __("Mappings") },
			{ key: "tpl-readiness", tid: "std-tab-readiness-rules", lab: __("Readiness Rules") },
			{ key: "tpl-reviews", tid: "std-tab-reviews-approval", lab: __("Reviews & Approval") },
			{ key: "tpl-usage", tid: "std-tab-usage", lab: __("Usage") },
			{ key: "tpl-audit-evidence", tid: "std-tab-template-audit-evidence", lab: __("Audit & Evidence") },
		];
		let h = "";
		for (let i = 0; i < tabs.length; i++) {
			const t = tabs[i];
			const active = i === 0;
			h +=
				'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab' +
				(active ? " is-active" : "") +
				'" data-std-detail-tab="' +
				esc(t.key) +
				'" data-testid="' +
				esc(t.tid) +
				'" aria-selected="' +
				(active ? "true" : "false") +
				'">' +
				esc(t.lab) +
				"</button>";
		}
		tabsHost.innerHTML = h;
	}

	function injectStdInstanceDetailTabs(tabsHost) {
		if (!tabsHost) return;
		tabsHost.classList.remove("kt-std-detail-tabs--template");
		tabsHost.classList.add("kt-std-detail-tabs--instance");
		const tabs = [
			{ key: "inst-overview", tid: "std-tab-instance-overview", lab: __("Overview") },
			{ key: "inst-parameters", tid: "std-tab-instance-parameters", lab: __("Parameters") },
			{ key: "inst-works", tid: "std-tab-instance-works-requirements", lab: __("Works Requirements") },
			{ key: "inst-boq", tid: "std-tab-instance-boq", lab: __("BOQ") },
			{ key: "inst-outputs", tid: "std-tab-generated-outputs", lab: __("Generated Outputs") },
			{ key: "inst-readiness", tid: "std-tab-instance-readiness", lab: __("Readiness") },
			{ key: "inst-addendum", tid: "std-tab-addendum-impact", lab: __("Addendum Impact") },
			{ key: "inst-downstream", tid: "std-tab-downstream-contracts", lab: __("Usage / Downstream Contracts") },
			{ key: "inst-audit", tid: "std-tab-instance-audit-evidence", lab: __("Audit & Evidence") },
		];
		let h = "";
		for (let i = 0; i < tabs.length; i++) {
			const t = tabs[i];
			const active = i === 0;
			h +=
				'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab' +
				(active ? " is-active" : "") +
				'" data-std-detail-tab="' +
				esc(t.key) +
				'" data-testid="' +
				esc(t.tid) +
				'" aria-selected="' +
				(active ? "true" : "false") +
				'">' +
				esc(t.lab) +
				"</button>";
		}
		tabsHost.innerHTML = h;
	}

	function ensureTemplateStructureFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionStructureLoading) return;
		if (templateVersionStructure && templateVersionStructure.ok) return;
		if (templateVersionStructureError) return;
		templateVersionStructureLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_structure_tree",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionStructureLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionStructure = msg;
					templateVersionStructureError = null;
				} else {
					templateVersionStructure = null;
					templateVersionStructureError = String(
						(msg && msg.message) || __("Could not load structure tree.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-structure") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionStructureLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionStructure = null;
				templateVersionStructureError = __("Could not load structure tree.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-structure") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function buildStructureTreeHtml(parts) {
		if (!parts || !parts.length) {
			return (
				'<p class="small text-muted mb-0" data-testid="std-structure-tree-empty">' +
				esc(__("No parts for this version.")) +
				"</p>"
			);
		}
		let h = '<ul class="kt-std-structure-tree-ul list-unstyled mb-0">';
		for (let pi = 0; pi < parts.length; pi++) {
			const p = parts[pi] || {};
			const pc = String(p.part_code || "");
			const pActive = selectedStructureKind === "part" && selectedStructureCode === pc;
			const pTitle = String(p.part_title || "");
			const pNum = String(p.part_number || "");
			const pLabel = pTitle ? esc(pTitle) + " (" + esc(pNum) + " · " + esc(pc) + ")" : esc(pc);
			h += '<li class="kt-std-structure-tree-li kt-std-structure-tree-li--part">';
			h +=
				'<button type="button" class="btn btn-link btn-sm text-left p-0 kt-std-structure-node' +
				(pActive ? " is-active" : "") +
				'" data-std-structure-select="1" data-testid="std-structure-node-part" data-std-structure-kind="part" data-std-structure-code="' +
				esc(pc) +
				'">' +
				pLabel +
				"</button>";
			const secs = p.sections || [];
			if (secs.length) {
				h += '<ul class="kt-std-structure-tree-ul kt-std-structure-tree-ul--nested list-unstyled mb-0">';
				for (let si = 0; si < secs.length; si++) {
					const s = secs[si] || {};
					const sc = String(s.section_code || "");
					const sActive = selectedStructureKind === "section" && selectedStructureCode === sc;
					const st = String(s.section_title || "");
					const sn = String(s.section_number || "");
					const sLabel = st ? esc(st) + " (" + esc(sn) + " · " + esc(sc) + ")" : esc(sc);
					let badges = "";
					if (s.itt_locked_hint) {
						badges += '<span class="badge badge-secondary ml-1">' + esc(__("ITT")) + "</span>";
					}
					if (s.gcc_locked_hint) {
						badges += '<span class="badge badge-secondary ml-1">' + esc(__("GCC")) + "</span>";
					}
					h += '<li class="kt-std-structure-tree-li">';
					h +=
						'<button type="button" class="btn btn-link btn-sm text-left p-0 kt-std-structure-node' +
						(sActive ? " is-active" : "") +
						'" data-std-structure-select="1" data-testid="std-structure-node-section" data-std-structure-kind="section" data-std-structure-code="' +
						esc(sc) +
						'">' +
						sLabel +
						badges +
						"</button>";
					const cls = s.clauses || [];
					if (cls.length) {
						h += '<ul class="kt-std-structure-tree-ul kt-std-structure-tree-ul--nested list-unstyled mb-0">';
						for (let ci = 0; ci < cls.length; ci++) {
							const c = cls[ci] || {};
							const cc = String(c.clause_code || "");
							const cActive = selectedStructureKind === "clause" && selectedStructureCode === cc;
							const ct = String(c.clause_title || "");
							const cn = String(c.clause_number || "");
							const cLabel = ct ? esc(ct) + " (" + esc(cn) + " · " + esc(cc) + ")" : esc(cc);
							h += '<li class="kt-std-structure-tree-li">';
							h +=
								'<button type="button" class="btn btn-link btn-sm text-left p-0 kt-std-structure-node' +
								(cActive ? " is-active" : "") +
								'" data-std-structure-select="1" data-testid="std-structure-node-clause" data-std-structure-kind="clause" data-std-structure-code="' +
								esc(cc) +
								'">' +
								cLabel +
								"</button></li>";
						}
						h += "</ul>";
					}
					h += "</li>";
				}
				h += "</ul>";
			}
			h += "</li>";
		}
		h += "</ul>";
		return h;
	}

	function paintStructureDetailInto(panel) {
		const body = panel.querySelector("#kt-std-structure-detail-body");
		if (!body) return;
		if (!selectedStructureKind || !selectedStructureCode) {
			body.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-structure-detail-empty">' +
				esc(__("Select a part, section, or clause in the tree.")) +
				"</p>";
			return;
		}
		const tree = templateVersionStructure;
		if (!tree || !tree.parts) {
			body.innerHTML = "";
			return;
		}
		if (selectedStructureKind === "part") {
			let p = null;
			for (let i = 0; i < tree.parts.length; i++) {
				if (String(tree.parts[i].part_code || "") === selectedStructureCode) {
					p = tree.parts[i];
					break;
				}
			}
			if (!p) {
				body.innerHTML = "";
				return;
			}
			body.innerHTML =
				'<h4 class="h6 mb-2" data-testid="std-structure-detail-title">' +
				esc(String(p.part_title || "")) +
				" (" +
				esc(String(p.part_number || "")) +
				" · " +
				esc(String(p.part_code || "")) +
				")</h4>" +
				'<p class="small text-muted mb-0" data-testid="std-structure-detail-part-meta">' +
				esc(__("Part overview: use sections for clause-level detail.")) +
				"</p>";
			return;
		}
		if (selectedStructureKind === "section") {
			let sec = null;
			for (let i = 0; i < tree.parts.length; i++) {
				const secs = tree.parts[i].sections || [];
				for (let j = 0; j < secs.length; j++) {
					if (String(secs[j].section_code || "") === selectedStructureCode) {
						sec = secs[j];
						break;
					}
				}
				if (sec) break;
			}
			if (!sec) {
				body.innerHTML = "";
				return;
			}
			const ed = String(sec.editability || "");
			let warn = "";
			if (ed === "Locked") {
				warn =
					'<div class="alert alert-warning py-2 px-2 small mb-2" data-testid="std-structure-locked-section-warning">' +
					esc(STRUCTURE_LOCKED_SECTION_WARNING) +
					"</div>";
			}
			const srcLine =
				sec.source_document_title || sec.source_document_code
					? '<dt class="col-sm-4 text-muted">' +
					  esc(__("Source")) +
					  '</dt><dd class="col-sm-8" data-testid="std-structure-detail-source">' +
					  esc(String(sec.source_document_title || sec.source_document_code || "—")) +
					  (sec.source_page_start != null
					  	? " · " +
						  esc(__("pages")) +
						  " " +
						  esc(String(sec.source_page_start)) +
						  "–" +
						  esc(String(sec.source_page_end != null ? sec.source_page_end : sec.source_page_start))
					  	: "") +
					  "</dd>"
					: "";
			body.innerHTML =
				warn +
				'<h4 class="h6 mb-2" data-testid="std-structure-detail-title">' +
				esc(String(sec.section_title || "")) +
				" (" +
				esc(String(sec.section_number || "")) +
				" · " +
				esc(String(sec.section_code || "")) +
				")</h4>" +
				'<p class="mb-2"><span class="badge badge-secondary" data-testid="std-structure-detail-editability">' +
				esc(ed || "—") +
				"</span></p>" +
				'<dl class="row mb-0 small">' +
				srcLine +
				"</dl>";
			return;
		}
		if (selectedStructureKind === "clause") {
			let cl = null;
			for (let i = 0; i < tree.parts.length; i++) {
				const secs = tree.parts[i].sections || [];
				for (let j = 0; j < secs.length; j++) {
					const cls = secs[j].clauses || [];
					for (let k = 0; k < cls.length; k++) {
						if (String(cls[k].clause_code || "") === selectedStructureCode) {
							cl = cls[k];
							break;
						}
					}
					if (cl) break;
				}
				if (cl) break;
			}
			if (!cl) {
				body.innerHTML = "";
				return;
			}
			const ed = String(cl.editability || "");
			const imp = cl.impact || {};
			const labels = [];
			if (imp.drives_bundle) labels.push(__("Drives bundle"));
			if (imp.drives_dsm) labels.push(__("Drives DSM"));
			if (imp.drives_dom) labels.push(__("Drives DOM"));
			if (imp.drives_dem) labels.push(__("Drives DEM"));
			if (imp.drives_dcm) labels.push(__("Drives DCM"));
			if (imp.drives_addendum) labels.push(__("Drives addendum"));
			let impactHtml = "";
			if (labels.length) {
				impactHtml =
					'<dt class="col-sm-4 text-muted">' +
					esc(__("Model impact")) +
					'</dt><dd class="col-sm-8" data-testid="std-structure-detail-impacts">' +
					esc(labels.join(", ")) +
					"</dd>";
			}
			const srcLine =
				cl.source_document_title || cl.source_document_code
					? '<dt class="col-sm-4 text-muted">' +
					  esc(__("Source")) +
					  '</dt><dd class="col-sm-8" data-testid="std-structure-detail-source">' +
					  esc(String(cl.source_document_title || cl.source_document_code || "—")) +
					  (cl.source_page_start != null
					  	? " · " +
						  esc(__("pages")) +
						  " " +
						  esc(String(cl.source_page_start)) +
						  "–" +
						  esc(String(cl.source_page_end != null ? cl.source_page_end : cl.source_page_start))
					  	: "") +
					  "</dd>"
					: "";
			body.innerHTML =
				'<h4 class="h6 mb-2" data-testid="std-structure-detail-title">' +
				esc(String(cl.clause_title || "")) +
				" (" +
				esc(String(cl.clause_number || "")) +
				" · " +
				esc(String(cl.clause_code || "")) +
				")</h4>" +
				'<p class="mb-2"><span class="badge badge-secondary" data-testid="std-structure-detail-editability">' +
				esc(ed || "—") +
				"</span></p>" +
				'<dl class="row mb-0 small">' +
				impactHtml +
				srcLine +
				"</dl>";
		}
	}

	function syncStructureTreeActive(panel) {
		panel.querySelectorAll("[data-std-structure-select]").forEach(function (btn) {
			const k = String(btn.getAttribute("data-std-structure-kind") || "");
			const c = String(btn.getAttribute("data-std-structure-code") || "");
			const on = k === selectedStructureKind && c === selectedStructureCode;
			btn.classList.toggle("is-active", on);
		});
	}

	function renderTemplateStructurePanel(panel) {
		panel.innerHTML =
			'<div class="kt-std-structure-layout" data-testid="std-template-panel-structure">' +
			'<div class="kt-std-structure-tree-wrap">' +
			'<div class="small text-muted mb-1">' +
			esc(__("Parts, sections, and clauses")) +
			"</div>" +
			'<div class="kt-std-structure-tree" data-testid="std-structure-tree"></div></div>' +
			'<div class="kt-std-structure-detail" data-testid="std-structure-detail">' +
			'<div id="kt-std-structure-detail-body" data-testid="std-structure-detail-body"></div></div></div>';

		const treeHost = panel.querySelector('[data-testid="std-structure-tree"]');
		if (templateVersionStructureError) {
			treeHost.innerHTML =
				'<p class="text-warning small mb-0" data-testid="std-structure-tree-error">' +
				esc(String(templateVersionStructureError)) +
				"</p>";
			paintStructureDetailInto(panel);
			return;
		}
		if (templateVersionStructureLoading && !templateVersionStructure) {
			treeHost.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-structure-tree-loading">' +
				esc(__("Loading structure…")) +
				"</p>";
			paintStructureDetailInto(panel);
			return;
		}
		if (!templateVersionStructure || !templateVersionStructure.ok) {
			treeHost.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-structure-tree-loading">' +
				esc(__("Loading structure…")) +
				"</p>";
			paintStructureDetailInto(panel);
			ensureTemplateStructureFetched();
			return;
		}
		treeHost.innerHTML = buildStructureTreeHtml(templateVersionStructure.parts || []);
		paintStructureDetailInto(panel);
		syncStructureTreeActive(panel);
	}

	function slugForTestId(s) {
		const t = String(s || "")
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
		return t || "x";
	}

	function ensureTemplateParametersFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionParametersLoading) return;
		if (templateVersionParameters && templateVersionParameters.ok) return;
		if (templateVersionParametersError) return;
		templateVersionParametersLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_parameter_catalogue",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionParametersLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionParameters = msg;
					templateVersionParametersError = null;
				} else {
					templateVersionParameters = null;
					templateVersionParametersError = String(
						(msg && msg.message) || __("Could not load parameter catalogue.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-parameters") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionParametersLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionParameters = null;
				templateVersionParametersError = __("Could not load parameter catalogue.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-parameters") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function impactChipsHtml(impact) {
		const im = impact || {};
		let h = "";
		if (im.drives_bundle) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives bundle")) + "</span>";
		if (im.drives_dsm) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DSM")) + "</span>";
		if (im.drives_dom) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DOM")) + "</span>";
		if (im.drives_dem) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DEM")) + "</span>";
		if (im.drives_dcm) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DCM")) + "</span>";
		if (im.addendum_change_requires_acknowledgement) {
			h += '<span class="badge badge-light border mr-1">' + esc(__("Addendum acknowledgement")) + "</span>";
		}
		if (im.addendum_change_requires_deadline_review) {
			h += '<span class="badge badge-light border mr-1">' + esc(__("Addendum deadline review")) + "</span>";
		}
		return h;
	}

	function renderTemplateParametersPanel(panel) {
		let h =
			'<div class="kt-std-parameters-panel" data-testid="std-template-panel-parameters">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Parameter catalogue (read-only).")) +
			"</div>";
		if (templateVersionParameters && templateVersionParameters.read_only) {
			h +=
				'<div class="alert alert-warning py-2 px-2 small mb-2" data-testid="std-parameters-read-only">' +
				esc(__("Read-only (active & immutable template version).")) +
				"</div>";
		}
		if (templateVersionParametersError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-parameters-catalogue-error">' +
				esc(String(templateVersionParametersError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionParametersLoading && !templateVersionParameters) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-parameters-catalogue-loading">' +
				esc(__("Loading parameters…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionParameters || !templateVersionParameters.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-parameters-catalogue-loading">' +
				esc(__("Loading parameters…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateParametersFetched();
			return;
		}
		const groups = templateVersionParameters.groups || [];
		if (!groups.length) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-parameters-catalogue-empty">' +
				esc(__("No parameters for this version.")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		for (let gi = 0; gi < groups.length; gi++) {
			const g = groups[gi] || {};
			const gname = String(g.group_name || "");
			const gslug = slugForTestId(gname);
			h += '<section class="kt-std-param-group mb-2" data-testid="std-param-group-' + esc(gslug) + '">';
			h += '<h4 class="h6 mb-1 kt-std-param-group__title">' + esc(gname) + "</h4>";
			const params = g.parameters || [];
			for (let pi = 0; pi < params.length; pi++) {
				const p = params[pi] || {};
				const pcode = String(p.parameter_code || "");
				const pslug = slugForTestId(pcode);
				const lab = String(p.label || "");
				const titleLine = esc(lab) + " (" + esc(pcode) + ")";
				const req = p.required ? __("Yes") : __("No");
				const stage = String(p.value_resolution_stage || "—");
				const dtype = String(p.data_type || "—");
				let secLine = "";
				if (p.section_title || p.section_code) {
					secLine =
						'<div class="small text-muted" data-testid="std-param-section-line-' +
						esc(pslug) +
						'">' +
						esc(String(p.section_title || "")) +
						(p.section_code ? " (" + esc(String(p.section_code)) + ")" : "") +
						"</div>";
				}
				const inc = p.incoming_dependencies || [];
				const out = p.outgoing_dependencies || [];
				const allDeps = ([]).concat(inc, out);
				let depBlock = "";
				if (allDeps.length) {
					depBlock = '<ul class="list-unstyled small mb-0 mt-1 kt-std-param-deps">';
					for (let di = 0; di < allDeps.length; di++) {
						depBlock +=
							'<li data-testid="std-param-dependency-line-' +
							esc(pslug) +
							"-" +
							String(di) +
							'">' +
							esc(String(allDeps[di])) +
							"</li>";
					}
					depBlock += "</ul>";
				}
				const chips = impactChipsHtml(p.impact);
				h +=
					'<div class="kt-std-param-row kt-std-surface mb-1 p-2" data-testid="std-param-row-' +
					esc(pslug) +
					'">' +
					'<div class="font-weight-bold small" data-testid="std-param-title-' +
					esc(pslug) +
					'">' +
					titleLine +
					"</div>" +
					'<div class="small text-muted">' +
					esc(__("Type")) +
					": " +
					esc(dtype) +
					" · " +
					esc(__("Required")) +
					": " +
					esc(req) +
					" · " +
					esc(__("Resolution")) +
					": " +
					esc(stage) +
					"</div>" +
					secLine +
					(chips ? '<div class="mt-1" data-testid="std-param-impacts-' + esc(pslug) + '">' + chips + "</div>" : "") +
					depBlock +
					"</div>";
			}
			h += "</section>";
		}
		h += "</div>";
		panel.innerHTML = h;
	}

	function ensureTemplateFormsFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionFormsLoading) return;
		if (templateVersionForms && templateVersionForms.ok) return;
		if (templateVersionFormsError) return;
		templateVersionFormsLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_forms_catalogue",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionFormsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionForms = msg;
					templateVersionFormsError = null;
				} else {
					templateVersionForms = null;
					templateVersionFormsError = String(
						(msg && msg.message) || __("Could not load forms catalogue.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-forms") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionFormsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionForms = null;
				templateVersionFormsError = __("Could not load forms catalogue.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-forms") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function formsImpactChipsHtml(impact) {
		const im = impact || {};
		let h = "";
		if (im.drives_dsm) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DSM")) + "</span>";
		if (im.drives_dem) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DEM")) + "</span>";
		if (im.drives_dcm) h += '<span class="badge badge-light border mr-1">' + esc(__("Drives DCM")) + "</span>";
		return h;
	}

	function renderTemplateFormsPanel(panel) {
		let h =
			'<div class="kt-std-forms-panel" data-testid="std-template-panel-forms">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Section IV and X forms with generated model impacts.")) +
			"</div>";
		if (templateVersionFormsError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-forms-catalogue-error">' +
				esc(String(templateVersionFormsError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionFormsLoading && !templateVersionForms) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-forms-catalogue-loading">' +
				esc(__("Loading forms…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionForms || !templateVersionForms.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-forms-catalogue-loading">' +
				esc(__("Loading forms…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateFormsFetched();
			return;
		}
		const forms = templateVersionForms.forms || [];
		const categories = templateVersionForms.categories || [];
		if (!forms.length) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-forms-catalogue-empty">' +
				esc(__("No forms for this version.")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!activeFormsCategoryId && categories.length) {
			activeFormsCategoryId = String(categories[0].id || "");
		}
		const visibleForms = forms.filter(function (row) {
			return !activeFormsCategoryId || String(row.category_id || "") === activeFormsCategoryId;
		});
		if (
			!selectedFormCode ||
			!visibleForms.find(function (row) {
				return String(row.form_code || "") === selectedFormCode;
			})
		) {
			selectedFormCode = visibleForms.length ? String(visibleForms[0].form_code || "") : "";
		}
		const selectedForm =
			visibleForms.find(function (row) {
				return String(row.form_code || "") === selectedFormCode;
			}) || null;

		h += '<div class="kt-std-forms-layout">';
		h += '<aside class="kt-std-forms-sidebar" data-testid="std-forms-category-sidebar">';
		for (let ci = 0; ci < categories.length; ci++) {
			const cat = categories[ci] || {};
			const cid = String(cat.id || "");
			const on = cid === activeFormsCategoryId;
			h +=
				'<button type="button" class="btn btn-xs btn-default kt-std-forms-category' +
				(on ? " is-active" : "") +
				'" data-std-forms-category="' +
				esc(cid) +
				'" data-testid="std-forms-category-' +
				esc(slugForTestId(cid)) +
				'">' +
				esc(String(cat.label || cid)) +
				" (" +
				esc(String(cat.count || 0)) +
				")</button>";
		}
		h += "</aside>";

		h += '<section class="kt-std-forms-table-wrap">';
		h += '<table class="table table-sm table-bordered mb-0" data-testid="std-forms-table">';
		h +=
			"<thead><tr>" +
			"<th>" +
			esc(__("Form")) +
			"</th><th>" +
			esc(__("Section")) +
			"</th><th>" +
			esc(__("Completed By")) +
			"</th><th>" +
			esc(__("Required")) +
			"</th><th>" +
			esc(__("Impact")) +
			"</th></tr></thead><tbody>";
		for (let fi = 0; fi < visibleForms.length; fi++) {
			const f = visibleForms[fi] || {};
			const code = String(f.form_code || "");
			const on = code === selectedFormCode;
			const sec = (f.section_number ? String(f.section_number) + " · " : "") + String(f.section_title || "—");
			const chips = formsImpactChipsHtml(f.impact);
			h +=
				'<tr class="kt-std-forms-row' +
				(on ? " is-active" : "") +
				'" data-std-form-code="' +
				esc(code) +
				'" data-testid="std-form-row-' +
				esc(slugForTestId(code)) +
				'">' +
				"<td><div class='font-weight-bold'>" +
				esc(String(f.title || "")) +
				"</div><div class='small text-muted'>" +
				esc(code) +
				"</div></td>" +
				"<td>" +
				esc(sec) +
				"</td>" +
				"<td>" +
				esc(String(f.completed_by || "—")) +
				"</td>" +
				"<td>" +
				esc(f.is_required ? __("Yes") : __("No")) +
				"</td>" +
				"<td>" +
				(chips || "—") +
				"</td></tr>";
		}
		h += "</tbody></table></section>";

		h += '<aside class="kt-std-forms-detail-drawer" data-testid="std-forms-detail-drawer">';
		if (selectedForm) {
			const reqSupplier = selectedForm.supplier_submission_requirement && selectedForm.is_required;
			h +=
				'<h4 class="h6 mb-1" data-testid="std-forms-detail-title">' +
				esc(String(selectedForm.title || "")) +
				"</h4>" +
				'<div class="small text-muted mb-1">' +
				esc(String(selectedForm.form_code || "")) +
				" · " +
				esc(String(selectedForm.form_type || "—")) +
				"</div>" +
				'<div class="small mb-1">' +
				esc(__("Supplier submission requirement")) +
				": " +
				esc(selectedForm.supplier_submission_requirement ? __("Yes") : __("No")) +
				"</div>" +
				'<div class="small mb-1">' +
				esc(__("Contract carry-forward")) +
				": " +
				esc(selectedForm.contract_carry_forward ? __("Yes") : __("No")) +
				"</div>" +
				'<div class="mb-1" data-testid="std-forms-detail-impacts">' +
				(formsImpactChipsHtml(selectedForm.impact) || "—") +
				"</div>";
			if (reqSupplier && selectedForm.impact && selectedForm.impact.drives_dsm) {
				h +=
					'<div class="alert alert-warning py-1 px-2 small mb-1" data-testid="std-forms-required-supplier-dsm-impact">' +
					esc(__("Required supplier form drives DSM output obligations.")) +
					"</div>";
			}
			h += '<div class="kt-std-forms-field-builder mt-2" data-testid="std-forms-field-builder">';
			if (templateVersionForms.draft_editable) {
				h +=
					'<div class="small text-muted mb-1">' +
					esc(__("Field builder (draft only).")) +
					"</div>" +
					'<label class="small d-block mb-1">' +
					esc(__("Field label")) +
					'<input type="text" class="form-control form-control-xs" value="' +
					esc(String(selectedForm.title || "")) +
					'" /></label>' +
					'<label class="small d-block mb-0">' +
					esc(__("Field type")) +
					'<select class="form-control form-control-xs"><option>' +
					esc(String(selectedForm.form_type || "Text")) +
					"</option></select></label>";
			} else {
				h +=
					'<div class="small text-muted" data-testid="std-forms-field-builder-readonly">' +
					esc(__("Field builder is available on draft template versions only.")) +
					"</div>";
			}
			h += "</div>";
		} else {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-forms-detail-empty">' +
				esc(__("Select a form row to view details.")) +
				"</p>";
		}
		h += "</aside>";
		h += "</div>";

		const preview = templateVersionForms.model_preview || {};
		h +=
			'<div class="kt-std-forms-model-preview mt-2" data-testid="std-forms-model-preview-readonly">' +
			'<div class="small text-muted mb-1">' +
			esc(__("Generated model preview (read-only).")) +
			"</div>" +
			'<div class="small">' +
			esc(__("DSM forms")) +
			": " +
			esc(String(preview.dsm_form_count || 0)) +
			" · " +
			esc(__("DEM forms")) +
			": " +
			esc(String(preview.dem_form_count || 0)) +
			" · " +
			esc(__("DCM forms")) +
			": " +
			esc(String(preview.dcm_form_count || 0)) +
			"</div></div>";

		h += "</div>";
		panel.innerHTML = h;
	}

	function ensureTemplateWorksFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionWorksLoading) return;
		if (templateVersionWorks && templateVersionWorks.ok) return;
		if (templateVersionWorksError) return;
		templateVersionWorksLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_works_configuration",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionWorksLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionWorks = msg;
					templateVersionWorksError = null;
				} else {
					templateVersionWorks = null;
					templateVersionWorksError = String(
						(msg && msg.message) || __("Could not load works configuration.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-works") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionWorksLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionWorks = null;
				templateVersionWorksError = __("Could not load works configuration.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-works") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function renderTemplateWorksPanel(panel) {
		let h =
			'<div class="kt-std-works-panel" data-testid="std-template-panel-works-configuration">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Works profile rules, BOQ configuration, and readiness context.")) +
			"</div>";
		if (templateVersionWorksError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-works-config-error">' +
				esc(String(templateVersionWorksError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionWorksLoading && !templateVersionWorks) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-works-config-loading">' +
				esc(__("Loading works configuration…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionWorks || !templateVersionWorks.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-works-config-loading">' +
				esc(__("Loading works configuration…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateWorksFetched();
			return;
		}
		const wp = templateVersionWorks.works_profile || {};
		const boq = templateVersionWorks.boq_definition || {};
		const warnings = templateVersionWorks.warnings || {};
		const components = templateVersionWorks.works_components || [];
		const evalRules = templateVersionWorks.evaluation_rule_templates || [];
		const carry = templateVersionWorks.contract_carry_forward_templates || [];
		const readiness = templateVersionWorks.readiness_rules || [];

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-works-profile-selector">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Works profile")) +
			"</h4>" +
			'<div class="small"><strong>' +
			esc(String(wp.profile_title || "—")) +
			"</strong> (" +
			esc(String(wp.profile_code || "—")) +
			")</div>" +
			'<div class="small text-muted" data-testid="std-works-profile-details">' +
			esc(__("Type")) +
			": " +
			esc(String(wp.works_profile_type || "—")) +
			" · " +
			esc(__("Status")) +
			": " +
			esc(String(wp.profile_status || "—")) +
			"</div></section>";

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-works-components">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Works requirement components")) +
			"</h4>";
		if (!components.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No components configured.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < components.length; i++) {
				const c = components[i] || {};
				h += "<li>" + esc(String(c.component_title || c.component_code || "—")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-works-boq-definition">' +
			'<h4 class="h6 mb-1">' +
			esc(__("BOQ configuration")) +
			"</h4>" +
			'<div class="small">' +
			esc(__("Definition")) +
			": " +
			esc(String(boq.boq_definition_code || "—")) +
			"</div>" +
			'<div class="small">' +
			esc(__("Arithmetic correction stage")) +
			': <strong data-testid="std-works-arithmetic-correction-stage">' +
			esc(String(boq.arithmetic_correction_stage || "—")) +
			"</strong></div>" +
			'<div class="alert alert-warning py-1 px-2 small mb-1 mt-1" data-testid="std-works-boq-warning">' +
			esc(String(warnings.boq_warning || "")) +
			"</div>" +
			'<div class="alert alert-warning py-1 px-2 small mb-0" data-testid="std-works-contract-price-warning">' +
			esc(String(warnings.contract_price_warning || "")) +
			"</div></section>";

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-works-evaluation-rule-templates">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Evaluation rule templates")) +
			"</h4>";
		if (!evalRules.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No evaluation templates found.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < evalRules.length; i++) {
				const r = evalRules[i] || {};
				h += "<li>" + esc(String(r.source_object_code || r.mapping_code || "—")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-works-contract-carry-forward-templates">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Contract carry-forward templates")) +
			"</h4>";
		if (!carry.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No carry-forward templates found.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < carry.length; i++) {
				const r = carry[i] || {};
				h += "<li>" + esc(String(r.target_component_type || r.mapping_code || "—")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";

		h +=
			'<section class="kt-std-surface p-2" data-testid="std-works-readiness-rules">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Works readiness rules")) +
			"</h4>";
		if (!readiness.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No readiness rules available.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < readiness.length; i++) {
				const rr = readiness[i] || {};
				h += "<li>" + esc(String(rr.label || rr.id || "")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";
		h += "</div>";
		panel.innerHTML = h;
	}

	function ensureTemplateMappingsFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionMappingsLoading) return;
		if (templateVersionMappings && templateVersionMappings.ok) return;
		if (templateVersionMappingsError) return;
		templateVersionMappingsLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_mappings_catalogue",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionMappingsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionMappings = msg;
					templateVersionMappingsError = null;
				} else {
					templateVersionMappings = null;
					templateVersionMappingsError = String(
						(msg && msg.message) || __("Could not load extraction mappings.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-mappings") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionMappingsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionMappings = null;
				templateVersionMappingsError = __("Could not load extraction mappings.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-mappings") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function renderTemplateMappingsPanel(panel) {
		const models = ["Bundle", "DSM", "DOM", "DEM", "DCM"];
		let h =
			'<div class="kt-std-mappings-panel" data-testid="std-template-panel-mappings">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Extraction mappings by target model (Bundle, DSM, DOM, DEM, DCM) plus coverage gaps.")) +
			"</div>";
		if (templateVersionMappingsError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-mappings-catalogue-error">' +
				esc(String(templateVersionMappingsError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionMappingsLoading && !templateVersionMappings) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-mappings-catalogue-loading">' +
				esc(__("Loading extraction mappings…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionMappings || !templateVersionMappings.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-mappings-catalogue-loading">' +
				esc(__("Loading extraction mappings…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateMappingsFetched();
			return;
		}
		const cat = templateVersionMappings;
		const tabs = cat.tabs || {};
		if (cat.read_only) {
			h +=
				'<div class="alert alert-warning py-1 px-2 small mb-2" data-testid="std-mappings-read-only-banner">' +
				esc(__("Mappings are read-only while this template version is active and immutable.")) +
				"</div>";
		}
		h += '<div class="kt-std-mappings-target-tabs d-flex flex-wrap gap-1 mb-2" data-testid="std-mappings-target-tabs">';
		for (let mi = 0; mi < models.length; mi++) {
			const m = models[mi];
			const tid = "std-mappings-target-" + String(m).toLowerCase();
			const on = activeMappingsTargetModel === m;
			const nrows = (tabs[m] && tabs[m].length) || 0;
			h +=
				'<button type="button" class="btn btn-xs ' +
				(on ? "btn-primary" : "btn-default") +
				'" data-std-mappings-target="' +
				esc(m) +
				'" data-testid="' +
				esc(tid) +
				'">' +
				esc(m) +
				" (" +
				esc(String(nrows)) +
				")</button>";
		}
		h += "</div>";
		const rows = tabs[activeMappingsTargetModel] || [];
		h += '<div class="kt-std-mappings-table-wrap mb-2" data-testid="std-mappings-table-wrap">';
		if (!rows.length) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-mappings-tab-empty">' +
				esc(__("No mappings for this target model.")) +
				"</p>";
		} else {
			h +=
				'<table class="table table-bordered table-sm table-condensed mb-0" data-testid="std-mappings-table"><thead><tr>' +
				"<th>" +
				esc(__("Mapping")) +
				"</th><th>" +
				esc(__("Source type")) +
				"</th><th>" +
				esc(__("Source code")) +
				"</th><th>" +
				esc(__("Target component")) +
				"</th><th>" +
				esc(__("Mandatory")) +
				"</th><th>" +
				esc(__("Validation")) +
				"</th></tr></thead><tbody>";
			for (let ri = 0; ri < rows.length; ri++) {
				const row = rows[ri] || {};
				h +=
					"<tr><td>" +
					esc(String(row.mapping_code || "")) +
					"</td><td>" +
					esc(String(row.source_object_type || "")) +
					"</td><td>" +
					esc(String(row.source_object_code || "")) +
					"</td><td>" +
					esc(String(row.target_component_type || "")) +
					"</td><td>" +
					esc(row.mandatory ? __("Yes") : __("No")) +
					"</td><td data-testid=\"std-mappings-validation-cell\">" +
					esc(String(row.validation_status || "")) +
					"</td></tr>";
			}
			h += "</tbody></table>";
		}
		h += "</div>";
		const miss = cat.missing_coverage || [];
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-mappings-missing">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Missing or flagged coverage")) +
			"</h4>";
		if (!miss.length) {
			h += '<p class="small text-muted mb-0" data-testid="std-mappings-missing-empty">' + esc(__("None detected.")) + "</p>";
		} else {
			h += '<ul class="small mb-0" data-testid="std-mappings-missing-list">';
			for (let i = 0; i < miss.length; i++) {
				const g = miss[i] || {};
				h += "<li>" + esc(String(g.label || g.mapping_code || "")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";
		const hi = cat.highlights || {};
		const iv = hi.section_iv_dsm || [];
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-mappings-highlight-iv-dsm">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Section IV → DSM (tender forms)")) +
			"</h4>";
		if (!iv.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No DSM mappings from Section IV forms.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < iv.length; i++) {
				const r = iv[i] || {};
				h +=
					"<li>" +
					esc(String(r.mapping_code || "")) +
					" · " +
					esc(String(r.source_object_code || "")) +
					"</li>";
			}
			h += "</ul>";
		}
		h += "</section>";
		const iii = hi.section_iii_dem || [];
		h +=
			'<section class="kt-std-surface p-2" data-testid="std-mappings-highlight-iii-dem">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Section III → DEM (evaluation)")) +
			"</h4>";
		if (!iii.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("No DEM highlights for Section III or evaluation rules.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < iii.length; i++) {
				const r = iii[i] || {};
				h +=
					"<li>" +
					esc(String(r.mapping_code || "")) +
					" · " +
					esc(String(r.source_object_type || "")) +
					"</li>";
			}
			h += "</ul>";
		}
		h += "</section></div>";
		panel.innerHTML = h;
	}

	function ensureTemplateReviewsFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionReviewsLoading) return;
		if (templateVersionReviews && templateVersionReviews.ok) return;
		if (templateVersionReviewsError) return;
		templateVersionReviewsLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_reviews_approval",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionReviewsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionReviews = msg;
					templateVersionReviewsError = null;
				} else {
					templateVersionReviews = null;
					templateVersionReviewsError = String(
						(msg && msg.message) || __("Could not load reviews and approval data.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-reviews") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionReviewsLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionReviews = null;
				templateVersionReviewsError = __("Could not load reviews and approval data.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-reviews") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function renderTemplateReviewsPanel(panel) {
		let h =
			'<div class="kt-std-reviews-panel" data-testid="std-template-panel-reviews-approval">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Legal, policy, and structure review status with activation checklist (read-only).")) +
			"</div>";
		if (templateVersionReviewsError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-reviews-catalogue-error">' +
				esc(String(templateVersionReviewsError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionReviewsLoading && !templateVersionReviews) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-reviews-catalogue-loading">' +
				esc(__("Loading reviews…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionReviews || !templateVersionReviews.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-reviews-catalogue-loading">' +
				esc(__("Loading reviews…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateReviewsFetched();
			return;
		}
		const rev = templateVersionReviews;
		if (rev.read_only) {
			h +=
				'<div class="alert alert-warning py-1 px-2 small mb-2" data-testid="std-reviews-read-only-banner">' +
				esc(__("This version is active and immutable; activation and checklist edits run through controlled Desk workflows.")) +
				"</div>";
		}
		const rs = rev.review_summary || {};
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-reviews-summary">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Review summary")) +
			"</h4>" +
			'<dl class="row mb-0 small">' +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Version status")) +
			'</dt><dd class="col-sm-8" data-testid="std-reviews-version-status">' +
			esc(String(rs.version_status || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Legal review")) +
			'</dt><dd class="col-sm-8" data-testid="std-reviews-legal-status">' +
			esc(String(rs.legal_review_status || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Policy review")) +
			'</dt><dd class="col-sm-8" data-testid="std-reviews-policy-status">' +
			esc(String(rs.policy_review_status || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Structure validation")) +
			'</dt><dd class="col-sm-8" data-testid="std-reviews-structure-status">' +
			esc(String(rs.structure_validation_status || "—")) +
			"</dd></dl></section>";

		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-reviews-governance">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Governance")) +
			"</h4>" +
			'<p class="small text-muted mb-0">' +
			esc(String(rev.governance_note || "")) +
			"</p></section>";

		const ret = rev.returned_corrections || [];
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-reviews-returned">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Returned corrections")) +
			"</h4>";
		if (!ret.length) {
			h += '<p class="small text-muted mb-0">' + esc(__("None recorded on this version.")) + "</p>";
		} else {
			h += '<ul class="small mb-0">';
			for (let i = 0; i < ret.length; i++) {
				const x = ret[i] || {};
				h += "<li>" + esc(String(x.detail || "")) + "</li>";
			}
			h += "</ul>";
		}
		h += "</section>";

		const items = rev.activation_checklist || [];
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-reviews-checklist">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Activation checklist")) +
			"</h4>" +
			'<div class="kt-std-reviews-checklist-wrap" data-testid="std-reviews-checklist-table-wrap">' +
			'<table class="table table-bordered table-sm table-condensed mb-0" data-testid="std-reviews-checklist-table"><thead><tr>' +
			"<th>" +
			esc(__("Item")) +
			"</th><th>" +
			esc(__("OK")) +
			"</th><th>" +
			esc(__("Detail")) +
			"</th></tr></thead><tbody>";
		for (let ci = 0; ci < items.length; ci++) {
			const it = items[ci] || {};
			const ok = !!it.pass;
			h +=
				'<tr data-testid="std-reviews-checklist-row-' +
				esc(String(it.id || ci)) +
				'"><td>' +
				esc(String(it.label || "")) +
				'</td><td data-testid="std-reviews-checklist-pass-cell">' +
				(ok ? esc(__("Yes")) : esc(__("No"))) +
				"</td><td class=\"small\">" +
				esc(String(it.detail || "")) +
				"</td></tr>";
		}
		h += "</tbody></table></div></section>";

		const warnText = String(rev.activation_legal_immutability_text || "");
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-reviews-activation-confirmation">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Activation — legal immutability")) +
			"</h4>" +
			'<blockquote class="small border-left pl-2 mb-2 text-muted" data-testid="std-reviews-activation-legal-warning">' +
			esc(warnText) +
			"</blockquote>" +
			'<p class="small text-muted mb-0" data-testid="std-reviews-activation-hint">' +
			esc(String(rev.activation_hint || "")) +
			"</p></section>";

		const gates = rev.activation_gates || {};
		const canGo = !!gates.can_activate_transition;
		const blockReason = String(rev.activation_ui_block_reason || "");
		h +=
			'<div class="d-flex flex-wrap align-items-center gap-2 mb-0" data-testid="std-reviews-activation-actions">' +
			'<button type="button" class="btn btn-sm btn-primary" disabled data-testid="std-reviews-activate-version" title="' +
			esc(canGo ? __("Activation is performed in Desk (state transitions).") : blockReason) +
			'">' +
			esc(__("Activate version (Desk)")) +
			"</button>" +
			'<span class="small text-muted" data-testid="std-reviews-activate-note">' +
			esc(__("Workbench shows readiness only; use Desk to run STD_VERSION_ACTIVATE when allowed.")) +
			"</span></div>";

		h += "</div>";
		panel.innerHTML = h;
	}

	function runStdTemplateAuditExportCsv() {
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.export_std_template_version_audit_evidence_csv",
			args: { version_code: vcode },
			callback: function (r) {
				const msg = (r && r.message) || {};
				if (!msg || !msg.ok) {
					if (typeof frappe !== "undefined" && frappe.show_alert) {
						frappe.show_alert({
							message: String((msg && msg.message) || __("Export not permitted.")),
							indicator: "orange",
						});
					}
					return;
				}
				const csv = String(msg.csv_text || "");
				const fn = String(msg.filename || "std-audit-export.csv");
				try {
					const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
					const url = URL.createObjectURL(blob);
					const a = document.createElement("a");
					a.href = url;
					a.download = fn;
					a.rel = "noopener";
					document.body.appendChild(a);
					a.click();
					a.remove();
					setTimeout(function () {
						URL.revokeObjectURL(url);
					}, 2500);
				} catch (e) {
					if (typeof frappe !== "undefined" && frappe.show_alert) {
						frappe.show_alert({ message: __("Could not start download."), indicator: "red" });
					}
				}
			},
			error: function () {
				if (typeof frappe !== "undefined" && frappe.show_alert) {
					frappe.show_alert({ message: __("Export failed."), indicator: "red" });
				}
			},
		});
	}

	function ensureTemplateAuditFetched() {
		const myReq = detailReqId;
		const payload = detailLastPayload;
		if (!payload || !payload.ok || detailTabMode !== "template") return;
		const vcode = String(payload.code || selectedObjectCode || "").trim();
		if (!vcode || typeof frappe === "undefined" || !frappe.call) return;
		if (templateVersionAuditLoading) return;
		if (templateVersionAudit && templateVersionAudit.ok) return;
		if (templateVersionAuditError) return;
		templateVersionAuditLoading = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_audit_evidence",
			args: { version_code: vcode },
			callback: function (r) {
				templateVersionAuditLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const msg = (r && r.message) || {};
				if (msg && msg.ok) {
					templateVersionAudit = msg;
					templateVersionAuditError = null;
				} else {
					templateVersionAudit = null;
					templateVersionAuditError = String(
						(msg && msg.message) || __("Could not load audit evidence.")
					);
				}
				if (detailTabMode === "template" && detailActiveTab === "tpl-audit-evidence") {
					renderDetailTabPanel();
				}
			},
			error: function () {
				templateVersionAuditLoading = false;
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				templateVersionAudit = null;
				templateVersionAuditError = __("Could not load audit evidence.");
				if (detailTabMode === "template" && detailActiveTab === "tpl-audit-evidence") {
					renderDetailTabPanel();
				}
			},
		});
	}

	function renderTemplateAuditPanel(panel) {
		const sectionOrder = [
			["general_evidence", __("Lifecycle & transitions")],
			["template_evidence", __("Template evidence")],
			["source_trace_evidence", __("Source trace evidence")],
			["configuration_evidence", __("Configuration evidence")],
			["works_evidence", __("Works evidence")],
			["generation_evidence", __("Generation evidence")],
			["readiness_evidence", __("Readiness evidence")],
			["addendum_evidence", __("Addendum evidence")],
			["downstream_evidence", __("Downstream evidence")],
			["denied_events", __("Denied events")],
		];
		let h =
			'<div class="kt-std-audit-panel" data-testid="std-template-panel-audit-evidence">' +
			'<div class="small text-muted mb-2">' +
			esc(__("Audit timeline and evidence slices for this template version and linked STD instances.")) +
			"</div>";
		if (templateVersionAuditError) {
			h +=
				'<p class="text-warning small mb-0" data-testid="std-audit-catalogue-error">' +
				esc(String(templateVersionAuditError)) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (templateVersionAuditLoading && !templateVersionAudit) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-audit-catalogue-loading">' +
				esc(__("Loading audit evidence…")) +
				"</p></div>";
			panel.innerHTML = h;
			return;
		}
		if (!templateVersionAudit || !templateVersionAudit.ok) {
			h +=
				'<p class="small text-muted mb-0" data-testid="std-audit-catalogue-loading">' +
				esc(__("Loading audit evidence…")) +
				"</p></div>";
			panel.innerHTML = h;
			ensureTemplateAuditFetched();
			return;
		}
		const aud = templateVersionAudit;
		if (aud.read_only) {
			h +=
				'<div class="alert alert-warning py-1 px-2 small mb-2" data-testid="std-audit-read-only-banner">' +
				esc(__("This template version is active; audit stream is append-only.")) +
				"</div>";
		}
		if (aud.privacy_note) {
			h +=
				'<div class="alert alert-info py-1 px-2 small mb-2" data-testid="std-audit-privacy-note">' +
				esc(String(aud.privacy_note)) +
				"</div>";
		}
		const perm = aud.permissions || {};
		const canExport = !!perm.can_export_evidence;
		h +=
			'<div class="d-flex flex-wrap align-items-center gap-2 mb-2" data-testid="std-audit-export-row">' +
			'<button type="button" class="btn btn-sm btn-default"' +
			(canExport ? "" : ' disabled="disabled"') +
			' data-testid="std-audit-export-csv" data-std-audit-export-csv="1" title="' +
			esc(
				canExport
					? __("Download CSV (Auditor / Administrator / System Manager)")
					: __("CSV export requires Auditor, System Manager, or Administrator.")
			) +
			'">' +
			esc(__("Export evidence (CSV)")) +
			"</button>" +
			'<span class="small text-muted" data-testid="std-audit-event-counts">' +
			esc(__("Events")) +
			": " +
			esc(String((aud.event_counts && aud.event_counts.total) || 0)) +
			"</span></div>";

		const tl = aud.lifecycle_timeline || [];
		h +=
			'<section class="kt-std-surface p-2 mb-2" data-testid="std-audit-timeline-section">' +
			'<h4 class="h6 mb-1">' +
			esc(__("Lifecycle timeline")) +
			"</h4>";
		if (!tl.length) {
			h += '<p class="small text-muted mb-0" data-testid="std-audit-timeline-empty">' + esc(__("No audit events yet.")) + "</p>";
		} else {
			h +=
				'<div class="kt-std-audit-table-wrap" data-testid="std-audit-timeline-table-wrap">' +
				'<table class="table table-bordered table-sm table-condensed mb-0" data-testid="std-audit-timeline-table"><thead><tr>' +
				"<th>" +
				esc(__("Time")) +
				"</th><th>" +
				esc(__("Event")) +
				"</th><th>" +
				esc(__("Object")) +
				"</th><th>" +
				esc(__("Actor")) +
				"</th>";
			if (perm.can_view_denied_events) {
				h += "<th>" + esc(__("Denial")) + "</th>";
			}
			h += "</tr></thead><tbody>";
			const start = Math.max(0, tl.length - 80);
			for (let ti = start; ti < tl.length; ti++) {
				const ev = tl[ti] || {};
				h +=
					"<tr><td class=\"small\">" +
					esc(String(ev.timestamp || "")) +
					"</td><td class=\"small\">" +
					esc(String(ev.event_type || "")) +
					"</td><td class=\"small\">" +
					esc(String(ev.object_type || "") + " · " + String(ev.object_code || "")) +
					"</td><td class=\"small\">" +
					esc(String(ev.actor || "")) +
					"</td>";
				if (perm.can_view_denied_events) {
					h += '<td class="small">' + esc(String(ev.denial_code || "")) + "</td>";
				}
				h += "</tr>";
			}
			h += "</tbody></table></div>";
		}
		h += "</section>";

		const secs = aud.evidence_sections || {};
		for (let si = 0; si < sectionOrder.length; si++) {
			const sk = sectionOrder[si][0];
			const lab = sectionOrder[si][1];
			const rows = secs[sk] || [];
			h +=
				'<section class="kt-std-surface p-2 mb-2" data-testid="std-audit-section-' +
				esc(sk) +
				'">' +
				'<h4 class="h6 mb-1">' +
				esc(String(lab)) +
				"</h4>";
			if (!rows.length) {
				h += '<p class="small text-muted mb-0">' + esc(__("No events in this slice.")) + "</p>";
			} else {
				h += '<ul class="small mb-0">';
				for (let ri = 0; ri < rows.length; ri++) {
					const ev = rows[ri] || {};
					h +=
						"<li><strong>" +
						esc(String(ev.event_type || "")) +
						"</strong> · " +
						esc(String(ev.object_code || "")) +
						" · " +
						esc(String(ev.timestamp || "")) +
						"</li>";
				}
				h += "</ul>";
			}
			h += "</section>";
		}

		h += "</div>";
		panel.innerHTML = h;
	}

	function renderInstanceOverviewPanel(panel, lr, payload) {
		if (!stdInstanceWorkbenchShell && !stdInstanceWorkbenchShellError) {
			panel.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-instance-summary-loading">' +
				esc(__("Loading instance summary…")) +
				"</p>";
			return;
		}
		const sh = stdInstanceWorkbenchShell || {};
		let badges = '<div class="d-flex flex-wrap gap-1 mb-2" data-testid="std-instance-overview-badges">';
		if (sh.read_only) {
			badges +=
				'<span class="badge badge-warning" data-testid="std-instance-read-only">' +
				esc(__("Read-only (locked or closed instance)")) +
				"</span>";
		}
		badges += "</div>";
		let guidance = "";
		const g = String(sh.addendum_guidance || "").trim();
		if (g) {
			guidance =
				'<div class="alert alert-info small mb-2" data-testid="std-instance-addendum-path" role="status">' +
				esc(g) +
				"</div>";
		}
		let errLine = "";
		if (stdInstanceWorkbenchShellError) {
			errLine =
				'<p class="text-warning small mb-2" data-testid="std-instance-summary-error">' +
				esc(String(stdInstanceWorkbenchShellError)) +
				"</p>";
		}
		panel.innerHTML =
			errLine +
			badges +
			guidance +
			'<dl class="row mb-0 small kt-std-overview-dl">' +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Object type")) +
			'</dt><dd class="col-sm-8" data-testid="std-overview-object-type">' +
			esc(String(lr.object_type || payload.object_type || "")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("DocType")) +
			'</dt><dd class="col-sm-8" data-testid="std-overview-doctype">' +
			esc(String(payload.doctype || "")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Instance status")) +
			'</dt><dd class="col-sm-8" data-testid="std-instance-status">' +
			esc(String(sh.instance_status || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Readiness")) +
			'</dt><dd class="col-sm-8" data-testid="std-instance-readiness-status">' +
			esc(String(sh.readiness_status || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Tender")) +
			'</dt><dd class="col-sm-8" data-testid="std-instance-tender-code">' +
			esc(String(sh.tender_code || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Template version")) +
			'</dt><dd class="col-sm-8" data-testid="std-instance-template-version-code">' +
			esc(String(sh.template_version_code || "—")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Applicability profile")) +
			'</dt><dd class="col-sm-8" data-testid="std-instance-profile-code">' +
			esc(String(sh.profile_code || "—")) +
			"</dd></dl>";
	}


	function resetStdInstancePanelCaches() {
		stdInstanceParameters = null;
		stdInstanceParametersError = null;
		stdInstanceParametersLoading = false;
		stdInstanceWorks = null;
		stdInstanceWorksError = null;
		stdInstanceWorksLoading = false;
		stdInstanceBoq = null;
		stdInstanceBoqError = null;
		stdInstanceBoqLoading = false;
		stdInstanceOutputs = null;
		stdInstanceOutputsError = null;
		stdInstanceOutputsLoading = false;
		stdInstanceReadiness = null;
		stdInstanceReadinessError = null;
		stdInstanceReadinessLoading = false;
		stdInstanceReadinessRunning = false;
		stdInstanceAddendum = null;
		stdInstanceAddendumError = null;
		stdInstanceAddendumLoading = false;
		stdInstanceDownstream = null;
		stdInstanceDownstreamError = null;
		stdInstanceDownstreamLoading = false;
		stdInstanceAudit = null;
		stdInstanceAuditError = null;
		stdInstanceAuditLoading = false;
	}

	function stdInstanceCodeFromPayload() {
		const payload = detailLastPayload;
		return String((payload && payload.code) || selectedObjectCode || "").trim();
	}

	function ensureStdInstanceTabFetched(tabId) {
		const myReq = detailReqId;
		const icode = stdInstanceCodeFromPayload();
		if (!icode || typeof frappe === "undefined" || !frappe.call) return;
		if (tabId === "inst-parameters") {
			if (stdInstanceParametersLoading) return;
			if (stdInstanceParameters && stdInstanceParameters.ok) return;
			if (stdInstanceParametersError) return;
			stdInstanceParametersLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_parameter_catalogue",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceParametersLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceParameters = msg;
						stdInstanceParametersError = null;
					} else {
						stdInstanceParameters = null;
						stdInstanceParametersError = String((msg && msg.message) || __("Could not load parameters."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-parameters") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceParametersLoading = false;
					stdInstanceParameters = null;
					stdInstanceParametersError = __("Could not load parameters.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-parameters") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-works") {
			if (stdInstanceWorksLoading) return;
			if (stdInstanceWorks && stdInstanceWorks.ok) return;
			if (stdInstanceWorksError) return;
			stdInstanceWorksLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_works_requirements_panel",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceWorksLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceWorks = msg;
						stdInstanceWorksError = null;
					} else {
						stdInstanceWorks = null;
						stdInstanceWorksError = String((msg && msg.message) || __("Could not load works requirements."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-works") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceWorksLoading = false;
					stdInstanceWorks = null;
					stdInstanceWorksError = __("Could not load works requirements.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-works") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-boq") {
			if (stdInstanceBoqLoading) return;
			if (stdInstanceBoq && stdInstanceBoq.ok) return;
			if (stdInstanceBoqError) return;
			stdInstanceBoqLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_boq_workbench_panel",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceBoqLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceBoq = msg;
						stdInstanceBoqError = null;
					} else {
						stdInstanceBoq = null;
						stdInstanceBoqError = String((msg && msg.message) || __("Could not load BOQ."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-boq") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceBoqLoading = false;
					stdInstanceBoq = null;
					stdInstanceBoqError = __("Could not load BOQ.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-boq") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-outputs") {
			if (stdInstanceOutputsLoading) return;
			if (stdInstanceOutputs && stdInstanceOutputs.ok) return;
			if (stdInstanceOutputsError) return;
			stdInstanceOutputsLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_outputs_preview",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceOutputsLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceOutputs = msg;
						stdInstanceOutputsError = null;
					} else {
						stdInstanceOutputs = null;
						stdInstanceOutputsError = String((msg && msg.message) || __("Could not load outputs."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-outputs") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceOutputsLoading = false;
					stdInstanceOutputs = null;
					stdInstanceOutputsError = __("Could not load outputs.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-outputs") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-readiness") {
			if (stdInstanceReadinessLoading) return;
			if (stdInstanceReadiness && stdInstanceReadiness.ok) return;
			if (stdInstanceReadinessError) return;
			stdInstanceReadinessLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_readiness_panel",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceReadinessLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceReadiness = msg;
						stdInstanceReadinessError = null;
					} else {
						stdInstanceReadiness = null;
						stdInstanceReadinessError = String((msg && msg.message) || __("Could not load readiness."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-readiness") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceReadinessLoading = false;
					stdInstanceReadiness = null;
					stdInstanceReadinessError = __("Could not load readiness.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-readiness") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-addendum") {
			if (stdInstanceAddendumLoading) return;
			if (stdInstanceAddendum && stdInstanceAddendum.ok) return;
			if (stdInstanceAddendumError) return;
			stdInstanceAddendumLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_addendum_impact_panel",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceAddendumLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceAddendum = msg;
						stdInstanceAddendumError = null;
					} else {
						stdInstanceAddendum = null;
						stdInstanceAddendumError = String((msg && msg.message) || __("Could not load addendum impact."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-addendum") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceAddendumLoading = false;
					stdInstanceAddendum = null;
					stdInstanceAddendumError = __("Could not load addendum impact.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-addendum") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-downstream") {
			const sh = stdInstanceWorkbenchShell || {};
			const tc = String(sh.tender_code || "").trim();
			if (!tc) {
				stdInstanceDownstreamLoading = false;
				stdInstanceDownstream = {
					ok: true,
					tender_code: "",
					binding: null,
					message: __("No tender code on instance."),
				};
				stdInstanceDownstreamError = null;
				return;
			}
			if (stdInstanceDownstreamLoading) return;
			if (stdInstanceDownstream && stdInstanceDownstream.ok) return;
			if (stdInstanceDownstreamError) return;
			stdInstanceDownstreamLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.tender_std_panel.get_tender_std_panel_data",
				args: { tender_code: tc },
				callback: function (r) {
					stdInstanceDownstreamLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceDownstream = msg;
						stdInstanceDownstreamError = null;
					} else {
						stdInstanceDownstream = null;
						stdInstanceDownstreamError = String((msg && msg.message) || __("Could not load tender STD panel."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-downstream") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceDownstreamLoading = false;
					stdInstanceDownstream = null;
					stdInstanceDownstreamError = __("Could not load tender STD panel.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-downstream") renderDetailTabPanel();
				},
			});
			return;
		}
		if (tabId === "inst-audit") {
			if (stdInstanceAuditLoading) return;
			if (stdInstanceAudit && stdInstanceAudit.ok) return;
			if (stdInstanceAuditError) return;
			stdInstanceAuditLoading = true;
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_audit_trail",
				args: { instance_code: icode },
				callback: function (r) {
					stdInstanceAuditLoading = false;
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceAudit = msg;
						stdInstanceAuditError = null;
					} else {
						stdInstanceAudit = null;
						stdInstanceAuditError = String((msg && msg.message) || __("Could not load audit trail."));
					}
					if (detailTabMode === "instance" && detailActiveTab === "inst-audit") renderDetailTabPanel();
				},
				error: function () {
					stdInstanceAuditLoading = false;
					stdInstanceAudit = null;
					stdInstanceAuditError = __("Could not load audit trail.");
					if (detailTabMode === "instance" && detailActiveTab === "inst-audit") renderDetailTabPanel();
				},
			});
		}
	}

	function saveStdInstanceParameterFromRow(btn) {
		const pcode = String(btn.getAttribute("data-parameter-code") || "").trim();
		const icode = stdInstanceCodeFromPayload();
		if (!pcode || !icode) return;
		const row = btn.closest("[data-std-inst-param-row]");
		const input = row && row.querySelector("[data-std-inst-param-input]");
		const val = input ? input.value : "";
		frappe.call({
			method: "kentender_procurement.std_engine.services.parameter_value_service.set_std_parameter_value",
			args: { instance_code: icode, parameter_code: pcode, value: val },
			callback: function (r) {
				if (!r || r.exc) return;
				frappe.show_alert({ message: __("Parameter saved"), indicator: "green" });
				stdInstanceParameters = null;
				stdInstanceParametersError = null;
				stdInstanceParametersLoading = false;
				renderDetailTabPanel();
			},
		});
	}

	function runStdInstanceReadinessNow() {
		const icode = stdInstanceCodeFromPayload();
		if (!icode || stdInstanceReadinessRunning) return;
		stdInstanceReadinessRunning = true;
		frappe.call({
			method: "kentender_procurement.std_engine.api.instance_workbench.run_std_instance_readiness_now",
			args: { instance_code: icode },
			callback: function (r) {
				stdInstanceReadinessRunning = false;
				if (!r || r.exc) return;
				stdInstanceReadiness = null;
				stdInstanceReadinessError = null;
				stdInstanceReadinessLoading = false;
				stdInstanceWorkbenchShell = null;
				stdInstanceWorkbenchShellError = null;
				frappe.show_alert({ message: __("Readiness run complete"), indicator: "green" });
				const myReq = detailReqId;
				frappe.call({
					method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_workbench_shell",
					args: { instance_code: icode },
					callback: function (r2) {
						if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
						const m2 = (r2 && r2.message) || {};
						if (m2 && m2.ok) stdInstanceWorkbenchShell = m2;
						if (detailTabMode === "instance") renderDetailTabPanel();
					},
				});
			},
			error: function () {
				stdInstanceReadinessRunning = false;
			},
		});
	}

	function saveStdInstanceWorksText(btn) {
		const cc = String(btn.getAttribute("data-component-code") || "").trim();
		const icode = stdInstanceCodeFromPayload();
		const wrap = btn.closest("[data-std-inst-works-editor]");
		const ta = wrap && wrap.querySelector("textarea");
		if (!cc || !icode || !ta) return;
		frappe.call({
			method: "kentender_procurement.std_engine.services.works_requirements_service.update_works_requirement_component",
			args: { instance_code: icode, component_code: cc, payload: { structured_text: ta.value } },
			callback: function () {
				frappe.show_alert({ message: __("Works requirement updated"), indicator: "green" });
				stdInstanceWorks = null;
				renderDetailTabPanel();
			},
		});
	}

	function promptStdInstanceAttachment(classification, label) {
		const icode = stdInstanceCodeFromPayload();
		const w = stdInstanceWorks || {};
		const sec = String(w.section_vii_section_code || "").trim();
		if (!icode) return;
		const fileRef = window.prompt(label + "\n" + __("File reference (business id / URL):"));
		if (!fileRef) return;
		frappe.call({
			method: "kentender_procurement.std_engine.services.section_attachment_service.add_std_section_attachment",
			args: {
				instance_code: icode,
				section_code: sec,
				file_reference: fileRef,
				classification: classification,
				component_code: null,
			},
			callback: function () {
				frappe.show_alert({ message: __("Attachment recorded"), indicator: "green" });
				stdInstanceWorks = null;
				stdInstanceWorksLoading = false;
				renderDetailTabPanel();
			},
		});
	}

	function renderInstanceSubTabPanel(panel) {
		const tid = detailActiveTab;
		if (tid === "inst-parameters") {
			let h = '<div class="kt-std-surface p-2" data-testid="std-instance-panel-parameters">';
			if (stdInstanceParametersError) {
				h += '<p class="text-warning small" data-testid="std-instance-parameters-error">' + esc(String(stdInstanceParametersError)) + "</p></div>";
				panel.innerHTML = h;
				return;
			}
			if (stdInstanceParametersLoading && !stdInstanceParameters) {
				h += '<p class="small text-muted" data-testid="std-instance-parameters-loading">' + esc(__("Loading…")) + "</p></div>";
				panel.innerHTML = h;
				return;
			}
			const cat = stdInstanceParameters || {};
			if (!cat.ok) {
				h += '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				panel.innerHTML = h;
				return;
			}
			if (cat.read_only) {
				h +=
					'<div class="alert alert-warning py-2 px-2 small mb-2" data-testid="std-instance-parameters-read-only">' +
					esc(__("Published / locked instance — use addendum path to change parameters.")) +
					"</div>";
			}
			if (String(cat.addendum_guidance || "").trim()) {
				h +=
					'<div class="alert alert-info py-2 px-2 small mb-2" data-testid="std-instance-parameters-addendum">' +
					esc(String(cat.addendum_guidance)) +
					"</div>";
			}
			const groups = cat.groups || [];
			for (let gi = 0; gi < groups.length; gi++) {
				const g = groups[gi] || {};
				const gslug = slugForTestId(g.group_name || "g");
				h += '<section class="mb-2" data-testid="std-param-group-' + esc(gslug) + '"><h4 class="h6">' + esc(String(g.group_name || "")) + "</h4>";
				const params = g.parameters || [];
				for (let pi = 0; pi < params.length; pi++) {
					const p = params[pi] || {};
					const pcode = String(p.parameter_code || "");
					const pslug = slugForTestId(pcode);
					h += '<div class="kt-std-surface p-2 mb-1" data-testid="std-param-row-' + esc(pslug) + '" data-std-inst-param-row="1">';
					h += '<div class="small font-weight-bold" data-testid="std-param-title-' + esc(pslug) + '">' + esc(String(p.label || "")) + " (" + esc(pcode) + ")</div>";
					if (p.tender_security_dependency) {
						h +=
							'<div class="small text-muted mb-1" data-testid="std-instance-param-tender-security-' +
							esc(pslug) +
							'">' +
							esc(__("Tender security dependency")) +
							"</div>";
					}
					h += '<div class="small">' + impactChipsHtml(p.impact) + "</div>";
					if (p.value_is_stale) {
						h += '<span class="badge badge-warning" data-testid="std-instance-param-stale-' + esc(pslug) + '">' + esc(__("Stale outputs")) + "</span> ";
					}
					const ro = cat.read_only;
					h +=
						'<div class="mt-1"><label class="small d-block">' +
						esc(__("Value")) +
						'<input class="form-control form-control-sm" data-std-inst-param-input="1" value="' +
						esc(String(p.current_value_display || "")) +
						'" ' +
						(ro ? "disabled" : "") +
						"/></label>";
					if (!ro) {
						h +=
							'<button type="button" class="btn btn-xs btn-primary mt-1" data-std-inst-param-save="1" data-parameter-code="' +
							esc(pcode) +
							'">' +
							esc(__("Save")) +
							"</button>";
					}
					h += "</div></div>";
				}
				h += "</section>";
			}
			h += "</div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-works") {
			let h = '<div data-testid="std-instance-panel-works-requirements">';
			if (stdInstanceWorksError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceWorksError)) + "</p></div>";
				return;
			}
			if (stdInstanceWorksLoading && !stdInstanceWorks) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const w = stdInstanceWorks || {};
			if (!w.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const labels = w.attachment_action_labels || {};
			h += '<div class="d-flex flex-wrap gap-1 mb-2">';
			h +=
				'<button type="button" class="btn btn-xs btn-default" data-std-inst-attachment-action="1" data-act="spec">' +
				esc(labels.specification || __("Add Specification Attachment")) +
				"</button>";
			h +=
				'<button type="button" class="btn btn-xs btn-default" data-std-inst-attachment-action="1" data-act="draw">' +
				esc(labels.drawing_register || __("Add Drawing to Register")) +
				"</button>";
			h +=
				'<button type="button" class="btn btn-xs btn-default" data-std-inst-attachment-action="1" data-act="sup">' +
				esc(labels.supersede || __("Supersede Attachment by Addendum")) +
				"</button>";
			h += "</div>";
			if (w.read_only) {
				h += '<div class="alert alert-warning small">' + esc(__("Read-only instance.")) + "</div>";
			}
			h += '<div class="small mb-2" data-testid="std-instance-works-derived">' + esc(__("Derived impacts (DSM/DEM/DCM drivers):")) + " ";
			const di = w.derived_impacts || [];
			h += esc(String(di.length)) + "</div>";
			const comps = w.components || [];
			for (let i = 0; i < comps.length; i++) {
				const c = comps[i] || {};
				const cc = String(c.component_code || "");
				h +=
					'<div class="kt-std-surface p-2 mb-2" data-testid="std-instance-works-component" data-std-inst-works-editor="1"><div class="small font-weight-bold">' +
					esc(String(c.component_title || cc)) +
					" (" +
					esc(cc) +
					")</div>";
				h +=
					'<textarea class="form-control form-control-sm mt-1" rows="3" ' +
					(w.read_only ? "disabled" : "") +
					">" +
					esc(String(c.structured_text || "")) +
					"</textarea>";
				if (!w.read_only && intOr0(c.supports_structured_text)) {
					h +=
						'<button type="button" class="btn btn-xs btn-primary mt-1" data-std-inst-works-save="1" data-component-code="' +
						esc(cc) +
						'">' +
						esc(__("Save")) +
						"</button>";
				}
				h += "</div>";
			}
			h += "</div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-boq") {
			let h = '<div data-testid="std-instance-panel-boq">';
			if (stdInstanceBoqError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceBoqError)) + "</p></div>";
				return;
			}
			if (stdInstanceBoqLoading && !stdInstanceBoq) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const bq = stdInstanceBoq || {};
			if (!bq.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const boq = bq.boq;
			if (!boq) {
				h += '<p class="small text-muted" data-testid="std-boq-validation-panel">' + esc(__("No BOQ instance.")) + "</p></div>";
				panel.innerHTML = h;
				return;
			}
			const defn = boq.definition || {};
			h += '<div class="kt-std-surface p-2 mb-2 small" data-testid="std-boq-summary-bar">';
			h += esc(__("BOQ")) + ": " + esc(String(boq.boq_instance_code)) + " · ";
			h += esc(__("Status")) + ": " + esc(String(boq.status)) + " · ";
			h += esc(__("Pricing")) + ": " + esc(String(defn.pricing_model || "—")) + " · ";
			h += esc(__("Currency")) + ": " + esc(String(boq.currency || "KES")) + " · ";
			h += esc(__("Quantity owner")) + ": " + esc(String(bq.quantity_owner_label || "")) + " · ";
			h += esc(__("Items")) + ": " + esc(String(boq.item_count || 0)) + "</div>";
			h += '<p class="small text-muted" data-testid="std-boq-owner-hint">' + esc(String(bq.rate_owner_note || "")) + "</p>";
			h += '<div class="mb-2" data-testid="std-boq-bill-list">';
			const bills = boq.bills || [];
			for (let bi = 0; bi < bills.length; bi++) {
				const bill = bills[bi] || {};
				h += '<div class="small font-weight-bold mb-1">' + esc(String(bill.bill_title || bill.bill_instance_code)) + "</div>";
				h += '<div class="table-responsive" data-testid="std-boq-item-grid"><table class="table table-sm table-bordered"><thead><tr>';
				h += "<th>" + esc(__("Item")) + "</th><th>" + esc(__("Description")) + "</th><th>" + esc(__("Unit")) + "</th>";
				h += "<th>" + esc(__("Qty (PE)")) + "</th><th>" + esc(__("Rate (supplier)")) + "</th><th>" + esc(__("Amount")) + "</th></tr></thead><tbody>";
				const items = bill.items || [];
				for (let ii = 0; ii < items.length; ii++) {
					const it = items[ii] || {};
					h += "<tr><td>" + esc(String(it.item_number || "")) + "</td><td>" + esc(String(it.description || "")) + "</td><td>" + esc(String(it.unit || "")) + "</td>";
					h += "<td>" + esc(String(it.quantity != null ? it.quantity : "")) + "</td><td>" + esc(String(it.rate != null ? it.rate : "—")) + "</td><td>" + esc(String(it.amount != null ? it.amount : "—")) + "</td></tr>";
				}
				h += "</tbody></table></div>";
			}
			h += "</div>";
			const val = bq.validation || {};
			h += '<div class="kt-std-surface p-2 small" data-testid="std-boq-validation-panel">';
			h += esc(__("Validation")) + ": " + esc(String(val.validation_status || "")) + "<ul class=\"mb-0\">";
			const errs = val.errors || [];
			for (let ei = 0; ei < errs.length; ei++) {
				h += "<li>" + esc(String(errs[ei])) + "</li>";
			}
			h += "</ul></div>";
			h +=
				'<button type="button" class="btn btn-xs btn-default mt-1" disabled data-testid="std-action-boq-import">' +
				esc(__("Import (preview in later ticket)")) +
				"</button>";
			h += '<div class="small text-muted mt-1" data-testid="std-boq-import-preview">' + esc(__("Import preview not saved until structured records exist.")) + "</div>";
			h += '<div class="small mt-2" data-testid="std-boq-dsm-impact">' + esc(__("BOQ changes mark DSM/DEM/DCM stale via generation rules.")) + "</div>";
			h += "</div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-outputs") {
			let h = '<div data-testid="std-instance-panel-generated-outputs">';
			if (stdInstanceOutputsError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceOutputsError)) + "</p></div>";
				return;
			}
			const o = stdInstanceOutputs || {};
			if (!o.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const warn = o.warnings || {};
			const by = o.outputs_by_type || {};
			function panelBlock(testid, title, typeKey) {
				const rows = by[typeKey] || [];
				let s = '<section class="kt-std-surface p-2 mb-2" data-testid="' + testid + '"><h4 class="h6">' + esc(title) + "</h4>";
				if (typeKey === "DEM" && warn.dem) s += '<p class="small text-warning" data-testid="std-preview-dem-warning">' + esc(String(warn.dem)) + "</p>";
				if (typeKey === "DOM" && warn.dom) s += '<p class="small text-warning" data-testid="std-preview-dom-warning">' + esc(String(warn.dom)) + "</p>";
				if (typeKey === "DCM" && warn.dcm) s += '<p class="small text-warning" data-testid="std-preview-dcm-warning">' + esc(String(warn.dcm)) + "</p>";
				if (!rows.length) s += '<p class="small text-muted">' + esc(__("No rows.")) + "</p>";
				for (let i = 0; i < rows.length; i++) {
					const r = rows[i] || {};
					s += '<div class="small">' + esc(String(r.output_code || "")) + " · " + esc(String(r.status || "")) + " ";
					if (intOr0(r.is_stale)) s += '<span class="badge badge-warning">' + esc(__("Stale")) + "</span>";
					s += "</div>";
				}
				s += "</section>";
				return s;
			}
			h += panelBlock("std-preview-bundle", __("Bundle"), "Bundle");
			h += panelBlock("std-preview-dsm", __("DSM"), "DSM");
			h += panelBlock("std-preview-dom", __("DOM"), "DOM");
			h += panelBlock("std-preview-dem", __("DEM"), "DEM");
			h += panelBlock("std-preview-dcm", __("DCM"), "DCM");
			h += '<section class="kt-std-surface p-2 small" data-testid="std-instance-output-jobs"><h4 class="h6">' + esc(__("Generation jobs")) + "</h4>";
			const jobs = o.generation_jobs || [];
			for (let j = 0; j < jobs.length; j++) {
				const jj = jobs[j] || {};
				h += "<div>" + esc(String(jj.generation_job_code || "")) + " · " + esc(String(jj.status || "")) + "</div>";
			}
			const fj = o.failed_jobs || [];
			if (fj.length) {
				h += '<p class="text-danger small mb-0" data-testid="std-instance-failed-job">' + esc(String(fj[0].error_message || __("Job failed"))) + "</p>";
			}
			h += "</section></div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-readiness") {
			let h = '<div data-testid="std-instance-panel-readiness">';
			if (stdInstanceReadinessError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceReadinessError)) + "</p></div>";
				return;
			}
			const rd = stdInstanceReadiness || {};
			if (!rd.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			h += '<div class="mb-2 small" data-testid="std-instance-readiness-summary">' + esc(__("Instance readiness:")) + " " + esc(String(rd.instance_readiness_status || "")) + "</div>";
			h +=
				'<button type="button" class="btn btn-xs btn-primary mb-2" data-std-inst-readiness-run="1" data-testid="std-instance-readiness-run">' +
				esc(__("Run readiness")) +
				"</button>";
			h += '<p class="small text-muted" data-testid="std-instance-readiness-manual-forbidden">' + esc(String(rd.manual_ready_message || "")) + "</p>";
			h += '<table class="table table-sm table-bordered" data-testid="std-instance-readiness-findings"><thead><tr>';
			h += "<th>" + esc(__("Severity")) + "</th><th>" + esc(__("Rule")) + "</th><th>" + esc(__("Message")) + "</th></tr></thead><tbody>";
			const finds = rd.findings || [];
			for (let i = 0; i < finds.length; i++) {
				const f = finds[i] || {};
				h += "<tr><td>" + esc(String(f.severity || "")) + "</td><td>" + esc(String(f.rule_code || "")) + "</td><td>" + esc(String(f.message || "")) + "</td></tr>";
			}
			h += "</tbody></table></div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-addendum") {
			let h = '<div data-testid="std-instance-panel-addendum-impact">';
			if (stdInstanceAddendumError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceAddendumError)) + "</p></div>";
				return;
			}
			const ad = stdInstanceAddendum || {};
			if (!ad.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			const hints = ad.regeneration_hints || {};
			h += '<div class="small mb-2" data-testid="std-instance-addendum-regen-hint">' + esc(String(hints.boq || "")) + " " + esc(String(hints.deadline || "")) + "</div>";
			h += "<table class=\"table table-sm\"><thead><tr><th>Code</th><th>Status</th><th>Regen</th></tr></thead><tbody>";
			const rows = ad.impact_analyses || [];
			for (let i = 0; i < rows.length; i++) {
				const r = rows[i] || {};
				h += "<tr><td>" + esc(String(r.impact_analysis_code || "")) + "</td><td>" + esc(String(r.status || "")) + "</td><td>" + esc(String(r.requires_regeneration || "")) + "</td></tr>";
			}
			h += "</tbody></table>";
			h += '<div class="small mt-2" data-testid="std-instance-supersession">' + esc(__("Related instances (tender):")) + " ";
			const sup = ad.supersession_chain || [];
			h += esc(String(sup.length)) + "</div></div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-downstream") {
			let h = '<div data-testid="std-instance-panel-downstream-contracts">';
			if (stdInstanceDownstreamError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceDownstreamError)) + "</p></div>";
				return;
			}
			const d = stdInstanceDownstream || {};
			if (!d.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			h += '<p class="small" data-testid="std-instance-downstream-tender">' + esc(__("Tender")) + ": " + esc(String(d.tender_code || "")) + "</p>";
			if (d.message) {
				h += '<p class="small text-muted" data-testid="std-instance-downstream-message">' + esc(String(d.message)) + "</p>";
			}
			const bind = d.binding;
			h += '<pre class="small" data-testid="std-instance-downstream-binding">' + esc(JSON.stringify(bind || {}, null, 0).slice(0, 2000)) + "</pre>";
			h +=
				'<a class="small" href="/app/std-engine" data-testid="std-instance-open-std-engine">' +
				esc(__("Open STD Engine")) +
				"</a></div>";
			panel.innerHTML = h;
			return;
		}
		if (tid === "inst-audit") {
			let h = '<div data-testid="std-instance-panel-audit-evidence">';
			if (stdInstanceAuditError) {
				panel.innerHTML = h + '<p class="text-warning small">' + esc(String(stdInstanceAuditError)) + "</p></div>";
				return;
			}
			const a = stdInstanceAudit || {};
			if (!a.ok) {
				panel.innerHTML = h + '<p class="small text-muted">' + esc(__("Loading…")) + "</p></div>";
				return;
			}
			h += "<table class=\"table table-sm\"><thead><tr><th>Type</th><th>Actor</th><th>When</th></tr></thead><tbody>";
			const evs = a.events || [];
			for (let i = 0; i < evs.length; i++) {
				const e = evs[i] || {};
				h +=
					"<tr><td>" +
					esc(String(e.event_type || "")) +
					"</td><td>" +
					esc(String(e.actor || "")) +
					"</td><td>" +
					esc(String(e.timestamp || "")) +
					"</td></tr>";
			}
			h += "</tbody></table></div>";
			panel.innerHTML = h;
			return;
		}
		panel.innerHTML = '<p class="small text-muted">' + esc(__("Unknown tab.")) + "</p>";
	}

	function intOr0(v) {
		const n = parseInt(String(v || 0), 10);
		return isNaN(n) ? 0 : n;
	}

	function renderDetailTabPanel() {
		const root = getActiveStdShellRoot();
		const panel = root && root.querySelector("#kt-std-detail-tab-panel");
		if (!panel) return;
		const payload = detailLastPayload;
		if (!payload) {
			panel.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-detail-tab-empty">' +
				esc(__("Select an object from the list.")) +
				"</p>";
			return;
		}
		if (!payload.ok) {
			panel.innerHTML =
				'<p class="text-danger small mb-0" data-testid="std-detail-availability-error">' +
				esc(String(payload.message || __("Could not load detail context."))) +
				"</p>";
			return;
		}
		const lr = detailLastListRow || {};
		if (detailTabMode === "generic") {
			if (detailActiveTab === "audit") {
				panel.innerHTML =
					'<div class="kt-std-surface p-2 small text-muted" data-testid="std-detail-audit-panel">' +
					esc(__("Audit trail and evidence for this object will appear here.")) +
					"</div>";
				return;
			}
			panel.innerHTML =
				'<dl class="row mb-0 small kt-std-overview-dl">' +
				'<dt class="col-sm-4 text-muted">' +
				esc(__("Object type")) +
				'</dt><dd class="col-sm-8" data-testid="std-overview-object-type">' +
				esc(String(lr.object_type || payload.object_type || "")) +
				"</dd>" +
				'<dt class="col-sm-4 text-muted">' +
				esc(__("DocType")) +
				'</dt><dd class="col-sm-8" data-testid="std-overview-doctype">' +
				esc(String(payload.doctype || "")) +
				"</dd></dl>" +
				'<p class="small text-muted mb-0 mt-2" data-testid="std-detail-tab-placeholder">' +
				esc(__("Type-specific configuration tabs follow in STD-CURSOR-1007+.")) +
				"</p>";
			return;
		}
		if (detailTabMode === "instance") {
			if (detailActiveTab === "inst-overview") {
				renderInstanceOverviewPanel(panel, lr, payload);
				return;
			}
			ensureStdInstanceTabFetched(detailActiveTab);
			renderInstanceSubTabPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-structure") {
			renderTemplateStructurePanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-parameters") {
			renderTemplateParametersPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-forms") {
			renderTemplateFormsPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-works") {
			renderTemplateWorksPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-mappings") {
			renderTemplateMappingsPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-reviews") {
			renderTemplateReviewsPanel(panel);
			return;
		}
		if (detailActiveTab === "tpl-audit-evidence") {
			renderTemplateAuditPanel(panel);
			return;
		}
		const tplPanels = {
			"tpl-forms": "std-template-panel-forms",
			"tpl-works": "std-template-panel-works-configuration",
			"tpl-mappings": "std-template-panel-mappings",
			"tpl-readiness": "std-template-panel-readiness-rules",
			"tpl-reviews": "std-template-panel-reviews-approval",
			"tpl-usage": "std-template-panel-usage",
			"tpl-audit-evidence": "std-template-panel-audit-evidence",
		};
		if (detailActiveTab !== "tpl-overview") {
			const tid = tplPanels[detailActiveTab] || "std-template-panel-unknown";
			panel.innerHTML =
				'<div class="kt-std-surface p-2 small text-muted" data-testid="' +
				esc(tid) +
				'">' +
				esc(__("This tab will be implemented in a later STD ticket (1010+).")) +
				"</div>";
			return;
		}
		if (!templateVersionSummary && !templateVersionSummaryError) {
			panel.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-template-summary-loading">' +
				esc(__("Loading template summary…")) +
				"</p>";
			return;
		}
		let badges = '<div class="d-flex flex-wrap gap-1 mb-2" data-testid="std-template-overview-badges">';
		const sum = templateVersionSummary || {};
		if (sum.read_only) {
			badges +=
				'<span class="badge badge-warning" data-testid="std-template-read-only">' +
				esc(__("Read-only (active & immutable)")) +
				"</span>";
		}
		if (sum.itt_locked) {
			badges +=
				'<span class="badge badge-secondary" data-testid="std-template-itt-locked">' +
				esc(__("ITT section locked")) +
				"</span>";
		}
		if (sum.gcc_locked) {
			badges +=
				'<span class="badge badge-secondary" data-testid="std-template-gcc-locked">' +
				esc(__("GCC section locked")) +
				"</span>";
		}
		badges += "</div>";
		let lockLine = "";
		const n = parseInt(String(sum.locked_section_count || 0), 10) || 0;
		if (n > 0 && !sum.itt_locked && !sum.gcc_locked) {
			lockLine =
				'<p class="small text-muted mb-2" data-testid="std-template-locked-sections-neutral">' +
				esc(__("Locked standard sections:")) +
				" " +
				esc(String(n)) +
				"</p>";
		}
		let errLine = "";
		if (templateVersionSummaryError) {
			errLine =
				'<p class="text-warning small mb-2" data-testid="std-template-summary-error">' +
				esc(String(templateVersionSummaryError)) +
				"</p>";
		}
		panel.innerHTML =
			errLine +
			badges +
			lockLine +
			'<dl class="row mb-0 small kt-std-overview-dl">' +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Object type")) +
			'</dt><dd class="col-sm-8" data-testid="std-overview-object-type">' +
			esc(String(lr.object_type || payload.object_type || "")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("DocType")) +
			'</dt><dd class="col-sm-8" data-testid="std-overview-doctype">' +
			esc(String(payload.doctype || "")) +
			"</dd>" +
			'<dt class="col-sm-4 text-muted">' +
			esc(__("Version status")) +
			'</dt><dd class="col-sm-8" data-testid="std-template-version-status">' +
			esc(String(sum.version_status || "—")) +
			"</dd></dl>";
	}

	function applyDetailTabsAfterPayload(payload, listRow, myReq) {
		const root = getActiveStdShellRoot();
		const tabsHost = root && root.querySelector('[data-testid="std-detail-tabs"]');
		if (!tabsHost) return;
		const ot = String((payload && payload.object_type) || (listRow && listRow.object_type) || selectedObjectType || "").trim();
		const ok = payload && payload.ok;
		if (!ok) {
			detailTabMode = "generic";
			detailActiveTab = "overview";
			templateVersionSummary = null;
			templateVersionSummaryError = null;
			templateVersionStructure = null;
			templateVersionStructureError = null;
			templateVersionStructureLoading = false;
			templateVersionParameters = null;
			templateVersionParametersError = null;
			templateVersionParametersLoading = false;
			templateVersionForms = null;
			templateVersionFormsError = null;
			templateVersionFormsLoading = false;
			activeFormsCategoryId = "";
			selectedFormCode = "";
			templateVersionWorks = null;
			templateVersionWorksError = null;
			templateVersionWorksLoading = false;
			templateVersionMappings = null;
			templateVersionMappingsError = null;
			templateVersionMappingsLoading = false;
			templateVersionReviews = null;
			templateVersionReviewsError = null;
			templateVersionReviewsLoading = false;
			templateVersionAudit = null;
			templateVersionAuditError = null;
			templateVersionAuditLoading = false;
			stdInstanceWorkbenchShell = null;
			stdInstanceWorkbenchShellError = null;
			resetStdInstancePanelCaches();
			activeMappingsTargetModel = "Bundle";
			selectedStructureKind = "";
			selectedStructureCode = "";
			injectGenericDetailTabs(tabsHost);
			syncStdDetailTabs("overview");
			return;
		}
		if (ot === "Template Version") {
			detailTabMode = "template";
			detailActiveTab = "tpl-overview";
			stdInstanceWorkbenchShell = null;
			stdInstanceWorkbenchShellError = null;
			resetStdInstancePanelCaches();
			templateVersionSummary = null;
			templateVersionSummaryError = null;
			templateVersionStructure = null;
			templateVersionStructureError = null;
			templateVersionStructureLoading = false;
			templateVersionParameters = null;
			templateVersionParametersError = null;
			templateVersionParametersLoading = false;
			templateVersionForms = null;
			templateVersionFormsError = null;
			templateVersionFormsLoading = false;
			activeFormsCategoryId = "";
			selectedFormCode = "";
			templateVersionWorks = null;
			templateVersionWorksError = null;
			templateVersionWorksLoading = false;
			templateVersionMappings = null;
			templateVersionMappingsError = null;
			templateVersionMappingsLoading = false;
			templateVersionReviews = null;
			templateVersionReviewsError = null;
			templateVersionReviewsLoading = false;
			templateVersionAudit = null;
			templateVersionAuditError = null;
			templateVersionAuditLoading = false;
			activeMappingsTargetModel = "Bundle";
			selectedStructureKind = "";
			selectedStructureCode = "";
			injectTemplateVersionDetailTabs(tabsHost);
			syncStdDetailTabs("tpl-overview");
			const vcode = String((payload && payload.code) || selectedObjectCode || "").trim();
			if (!vcode || typeof frappe === "undefined" || !frappe.call) {
				templateVersionSummaryError = __("Could not load summary.");
				renderDetailTabPanel();
				return;
			}
			frappe.call({
				method: "kentender_procurement.std_engine.api.template_version_workbench.get_std_template_version_workbench_summary",
				args: { version_code: vcode },
				callback: function (r) {
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						templateVersionSummary = msg;
						templateVersionSummaryError = null;
					} else {
						templateVersionSummary = null;
						templateVersionSummaryError = String(
							(msg && msg.message) || __("Could not load template version summary.")
						);
					}
					if (detailTabMode === "template") {
						renderDetailTabPanel();
					}
				},
				error: function () {
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					templateVersionSummary = null;
					templateVersionSummaryError = __("Could not load template version summary.");
					if (detailTabMode === "template") {
						renderDetailTabPanel();
					}
				},
			});
			return;
		}
		if (ot === "STD Instance") {
			detailTabMode = "instance";
			detailActiveTab = "inst-overview";
			templateVersionSummary = null;
			templateVersionSummaryError = null;
			templateVersionStructure = null;
			templateVersionStructureError = null;
			templateVersionStructureLoading = false;
			templateVersionParameters = null;
			templateVersionParametersError = null;
			templateVersionParametersLoading = false;
			templateVersionForms = null;
			templateVersionFormsError = null;
			templateVersionFormsLoading = false;
			activeFormsCategoryId = "";
			selectedFormCode = "";
			templateVersionWorks = null;
			templateVersionWorksError = null;
			templateVersionWorksLoading = false;
			templateVersionMappings = null;
			templateVersionMappingsError = null;
			templateVersionMappingsLoading = false;
			templateVersionReviews = null;
			templateVersionReviewsError = null;
			templateVersionReviewsLoading = false;
			templateVersionAudit = null;
			templateVersionAuditError = null;
			templateVersionAuditLoading = false;
			activeMappingsTargetModel = "Bundle";
			selectedStructureKind = "";
			selectedStructureCode = "";
			resetStdInstancePanelCaches();
			stdInstanceWorkbenchShell = null;
			stdInstanceWorkbenchShellError = null;
			injectStdInstanceDetailTabs(tabsHost);
			syncStdDetailTabs("inst-overview");
			const icode = String((payload && payload.code) || selectedObjectCode || "").trim();
			if (!icode || typeof frappe === "undefined" || !frappe.call) {
				stdInstanceWorkbenchShellError = __("Could not load instance summary.");
				renderDetailTabPanel();
				return;
			}
			frappe.call({
				method: "kentender_procurement.std_engine.api.instance_workbench.get_std_instance_workbench_shell",
				args: { instance_code: icode },
				callback: function (r) {
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					const msg = (r && r.message) || {};
					if (msg && msg.ok) {
						stdInstanceWorkbenchShell = msg;
						stdInstanceWorkbenchShellError = null;
					} else {
						stdInstanceWorkbenchShell = null;
						stdInstanceWorkbenchShellError = String(
							(msg && msg.message) || __("Could not load STD instance summary.")
						);
					}
					if (detailTabMode === "instance") {
						renderDetailTabPanel();
					}
				},
				error: function () {
					if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
					stdInstanceWorkbenchShell = null;
					stdInstanceWorkbenchShellError = __("Could not load STD instance summary.");
					if (detailTabMode === "instance") {
						renderDetailTabPanel();
					}
				},
			});
			return;
		}
		detailTabMode = "generic";
		detailActiveTab = "overview";
		templateVersionSummary = null;
		templateVersionSummaryError = null;
		templateVersionStructure = null;
		templateVersionStructureError = null;
		templateVersionStructureLoading = false;
		templateVersionParameters = null;
		templateVersionParametersError = null;
		templateVersionParametersLoading = false;
		templateVersionForms = null;
		templateVersionFormsError = null;
		templateVersionFormsLoading = false;
		activeFormsCategoryId = "";
		selectedFormCode = "";
		templateVersionWorks = null;
		templateVersionWorksError = null;
		templateVersionWorksLoading = false;
		templateVersionMappings = null;
		templateVersionMappingsError = null;
		templateVersionMappingsLoading = false;
		templateVersionReviews = null;
		templateVersionReviewsError = null;
		templateVersionReviewsLoading = false;
		templateVersionAudit = null;
		templateVersionAuditError = null;
		templateVersionAuditLoading = false;
		stdInstanceWorkbenchShell = null;
		stdInstanceWorkbenchShellError = null;
		resetStdInstancePanelCaches();
		activeMappingsTargetModel = "Bundle";
		selectedStructureKind = "";
		selectedStructureCode = "";
		injectGenericDetailTabs(tabsHost);
		syncStdDetailTabs("overview");
	}

	function clearStdDetailUi() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		detailLastPayload = null;
		detailLastListRow = null;
		detailTabMode = "generic";
		detailActiveTab = "overview";
		templateVersionSummary = null;
		templateVersionSummaryError = null;
		templateVersionStructure = null;
		templateVersionStructureError = null;
		templateVersionStructureLoading = false;
		templateVersionParameters = null;
		templateVersionParametersError = null;
		templateVersionParametersLoading = false;
		templateVersionForms = null;
		templateVersionFormsError = null;
		templateVersionFormsLoading = false;
		activeFormsCategoryId = "";
		selectedFormCode = "";
		templateVersionWorks = null;
		templateVersionWorksError = null;
		templateVersionWorksLoading = false;
		templateVersionMappings = null;
		templateVersionMappingsError = null;
		templateVersionMappingsLoading = false;
		templateVersionReviews = null;
		templateVersionReviewsError = null;
		templateVersionReviewsLoading = false;
		templateVersionAudit = null;
		templateVersionAuditError = null;
		templateVersionAuditLoading = false;
		stdInstanceWorkbenchShell = null;
		stdInstanceWorkbenchShellError = null;
		resetStdInstancePanelCaches();
		activeMappingsTargetModel = "Bundle";
		selectedStructureKind = "";
		selectedStructureCode = "";
		const tabsHost = root.querySelector('[data-testid="std-detail-tabs"]');
		if (tabsHost) injectGenericDetailTabs(tabsHost);
		const hdr = root.querySelector("#kt-std-detail-header");
		if (hdr) {
			hdr.innerHTML =
				'<p class="small text-muted mb-0" data-testid="std-detail-empty-hint">' + esc(__("Select an object from the list.")) + "</p>";
		}
		const cards = root.querySelector("#kt-std-detail-state-cards");
		if (cards) cards.innerHTML = "";
		const panel = root.querySelector("#kt-std-detail-tab-panel");
		if (panel) panel.innerHTML = "";
		const blk = root.querySelector("#kt-std-detail-blockers");
		if (blk) {
			blk.innerHTML = '<span class="text-muted small">' + esc(__("No blockers for current selection.")) + "</span>";
		}
		const act = root.querySelector("#kt-std-action-host");
		if (act) {
			act.innerHTML = '<span class="text-muted small">' + esc(__("Select an object to see actions.")) + "</span>";
		}
		syncStdDetailTabs("overview");
	}

	function syncStdDetailTabs(activeId) {
		const root = getActiveStdShellRoot();
		if (!root) return;
		let id = activeId || "";
		if (!id) {
			if (detailTabMode === "template") {
				id = "tpl-overview";
			} else if (detailTabMode === "instance") {
				id = "inst-overview";
			} else {
				id = "overview";
			}
		}
		detailActiveTab = id;
		root.querySelectorAll("[data-std-detail-tab]").forEach(function (btn) {
			const on = String(btn.getAttribute("data-std-detail-tab") || "") === id;
			btn.classList.toggle("is-active", on);
			btn.setAttribute("aria-selected", on ? "true" : "false");
		});
		renderDetailTabPanel();
	}

	function renderDetailHeaderFromListRow(selected) {
		const root = getActiveStdShellRoot();
		const hdr = root && root.querySelector("#kt-std-detail-header");
		if (!hdr || !selected) return;
		hdr.innerHTML =
			'<div class="kt-std-detail-title-line" data-testid="std-detail-title-line">' +
			'<span class="kt-std-detail-name" data-testid="std-detail-selected-title">' +
			esc(String(selected.title || "")) +
			"</span>" +
			"</div>" +
			'<div class="small text-muted kt-std-detail-code-line" data-testid="std-detail-code-line">' +
			esc(String(selected.object_type || "")) +
			" · " +
			'<span data-testid="std-selected-object-code">' +
			esc(String(selected.code || "")) +
			"</span> · " +
			esc(String(selected.status || "")) +
			"</div>";
	}

	function renderActionBarFromPayload(payload) {
		const root = getActiveStdShellRoot();
		const host = root && root.querySelector("#kt-std-action-host");
		if (!host) return;
		if (!payload || !payload.ok || !Array.isArray(payload.actions)) {
			host.innerHTML = '<span class="text-muted small">' + esc(__("Select an object to see actions.")) + "</span>";
			return;
		}
		let html = "";
		for (let i = 0; i < payload.actions.length; i++) {
			const a = payload.actions[i] || {};
			if (!a.visible) continue;
			const disAttr = a.disabled ? " disabled" : "";
			const reason = a.reason ? ' title="' + esc(String(a.reason)) + '"' : "";
			const cls =
				"btn btn-sm " + (String(a.id) === "open_in_desk" && !a.disabled ? "btn-primary" : "btn-default");
			html +=
				'<button type="button" class="' +
				cls +
				'" data-std-desk-action="' +
				esc(String(a.id || "")) +
				'" data-testid="' +
				esc(actionTestId(a.id)) +
				'"' +
				disAttr +
				reason +
				">" +
				esc(String(a.label || a.id || "")) +
				"</button>";
		}
		host.innerHTML = html || '<span class="text-muted small">' + esc(__("No actions for this object.")) + "</span>";
	}

	function renderDetailFromAvailability(payload, listRow, myReq) {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const cardsHost = root.querySelector("#kt-std-detail-state-cards");
		const blk = root.querySelector("#kt-std-detail-blockers");
		detailLastListRow = listRow || null;
		if (!payload || !payload.ok) {
			renderActionBarFromPayload({ ok: false });
			applyDetailTabsAfterPayload(payload || { ok: false }, listRow, myReq);
			return;
		}
		if (listRow && payload.title) {
			const hdr = root.querySelector("#kt-std-detail-header");
			if (hdr) {
				const merged = Object.assign({}, listRow, { title: payload.title });
				renderDetailHeaderFromListRow(merged);
			}
		}
		if (cardsHost) {
			const cards = payload.state_cards || [];
			if (!cards.length) {
				cardsHost.innerHTML = '<span class="text-muted small">' + esc(__("No state summary.")) + "</span>";
			} else {
				let chtml = '<div class="kt-std-state-cards-grid">';
				for (let j = 0; j < cards.length; j++) {
					const c = cards[j] || {};
					chtml +=
						'<div class="kt-std-state-card kt-std-surface" data-testid="std-state-card-' +
						esc(String(c.id || j).replace(/[^a-z0-9-]+/gi, "-")) +
						'">' +
						'<div class="kt-std-state-card__label small text-muted">' +
						esc(String(c.label || "")) +
						"</div>" +
						'<div class="kt-std-state-card__value">' +
						esc(String(c.value || "—")) +
						"</div></div>";
				}
				chtml += "</div>";
				cardsHost.innerHTML = chtml;
			}
		}
		const blocks = (payload.blockers || []).concat(payload.warnings || []);
		if (blk) {
			if (!blocks.length) {
				blk.innerHTML = '<span class="text-muted small" data-testid="std-blockers-empty">' + esc(__("No blockers for current selection.")) + "</span>";
			} else {
				let bhtml = '<ul class="list-unstyled mb-0 small">';
				for (let k = 0; k < blocks.length; k++) {
					const b = blocks[k] || {};
					const sev = String(b.severity || "warning").toLowerCase() === "danger" ? "danger" : "warning";
					bhtml +=
						'<li class="mb-1 kt-std-blocker-line kt-std-blocker-line--' +
						esc(sev) +
						'" data-testid="std-blocker-line-' +
						String(k) +
						'">' +
						esc(String(b.text || "")) +
						"</li>";
				}
				bhtml += "</ul>";
				blk.innerHTML = bhtml;
			}
		}
		renderActionBarFromPayload(payload);
		applyDetailTabsAfterPayload(payload, listRow, myReq);
	}

	function runStdDeskAction(actionId) {
		if (!detailLastPayload || !detailLastPayload.ok || !Array.isArray(detailLastPayload.actions)) return;
		const a = detailLastPayload.actions.find(function (x) {
			return String(x.id || "") === String(actionId);
		});
		if (!a || a.disabled || !a.allowed) return;
		const go = function () {
			if (a.id === "create_std_instance" && a.meta && a.meta.template_version_code) {
				if (typeof frappe === "undefined" || !frappe.model || typeof frappe.model.get_new_doc !== "function") {
					return;
				}
				const d = frappe.model.get_new_doc("STD Instance");
				d.template_version_code = String(a.meta.template_version_code || "");
				frappe.set_route("Form", d.doctype, d.name);
				return;
			}
			if (Array.isArray(a.route) && a.route.length) {
				frappe.set_route.apply(null, a.route);
			}
		};
		if (a.requires_confirmation) {
			const msg = String(a.confirmation_message || __("Proceed with this action?"));
			if (typeof frappe !== "undefined" && frappe.confirm) {
				frappe.confirm(msg, go, function () {});
			} else {
				go();
			}
		} else {
			go();
		}
	}

	function loadStdDetailContext(listRow) {
		if (!routeLooksLikeStdEngine()) return;
		const ot = String(selectedObjectType || "").trim();
		const code = String(selectedObjectCode || "").trim();
		if (!ot || !code) {
			clearStdDetailUi();
			return;
		}
		detailReqId += 1;
		const myReq = detailReqId;
		templateVersionStructure = null;
		templateVersionStructureError = null;
		templateVersionStructureLoading = false;
		templateVersionParameters = null;
		templateVersionParametersError = null;
		templateVersionParametersLoading = false;
		templateVersionForms = null;
		templateVersionFormsError = null;
		templateVersionFormsLoading = false;
		activeFormsCategoryId = "";
		selectedFormCode = "";
		templateVersionWorks = null;
		templateVersionWorksError = null;
		templateVersionWorksLoading = false;
		templateVersionMappings = null;
		templateVersionMappingsError = null;
		templateVersionMappingsLoading = false;
		templateVersionReviews = null;
		templateVersionReviewsError = null;
		templateVersionReviewsLoading = false;
		templateVersionAudit = null;
		templateVersionAuditError = null;
		templateVersionAuditLoading = false;
		activeMappingsTargetModel = "Bundle";
		selectedStructureKind = "";
		selectedStructureCode = "";
		frappe.call({
			method: "kentender_procurement.std_engine.api.landing.get_std_action_availability",
			args: { object_type: ot, object_code: code },
			callback: function (r) {
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				const payload = (r && r.message) || {};
				detailLastPayload = payload;
				const sel =
					listRow ||
					(searchResults || []).find(function (row) {
						return String(row.code || "") === code && String(row.object_type || "") === ot;
					}) ||
					null;
				renderDetailFromAvailability(payload, sel, myReq);
			},
			error: function () {
				if (!routeLooksLikeStdEngine() || myReq !== detailReqId) return;
				detailLastPayload = { ok: false, message: __("Could not load action availability.") };
				renderDetailFromAvailability(detailLastPayload, listRow, myReq);
			},
		});
	}

	function renderDetailSelection() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector('[data-testid="std-object-detail"]');
		if (!host || !root.querySelector("#kt-std-detail-header")) {
			return;
		}
		const selected = (searchResults || []).find(function (r) {
			return String(r.code || "") === String(selectedObjectCode || "");
		});
		if (!selected || !selectedObjectCode) {
			clearStdDetailUi();
			return;
		}
		selectedObjectType = String(selected.object_type || selectedObjectType || "");
		renderDetailHeaderFromListRow(selected);
		loadStdDetailContext(selected);
	}

	function loadSearchResults() {
		if (!routeLooksLikeStdEngine()) return;
		frappe.call({
			method: "kentender_procurement.std_engine.api.landing.search_std_workbench_objects",
			args: {
				query: searchQuery,
				queue_id: activeQueueId,
				scope_tab_id: activeWorkTab,
				filters: activeFilters,
				limit: 50,
			},
			callback: function (r) {
				if (!routeLooksLikeStdEngine()) return;
				const root = getActiveStdShellRoot();
				const prevScrollTop = stdReadListScrollTop(root);
				const payload = (r && r.message) || {};
				searchResults = Array.isArray(payload.results) ? payload.results : [];
				if (!selectedObjectCode && searchResults.length) {
					selectedObjectCode = String(searchResults[0].code || "");
					selectedObjectType = String(searchResults[0].object_type || "");
				} else if (selectedObjectCode) {
					const m = searchResults.find(function (row) {
						return String(row.code || "") === String(selectedObjectCode);
					});
					if (m) {
						selectedObjectType = String(m.object_type || "");
					} else {
						selectedObjectCode = "";
						selectedObjectType = "";
					}
				}
				renderObjectListResults();
				syncStdListSelection(root, selectedObjectCode);
				stdRestoreListScrollTop(root, prevScrollTop, selectedObjectCode);
				renderDetailSelection();
			},
			error: function () {
				if (!routeLooksLikeStdEngine()) return;
				searchResults = [];
				selectedObjectCode = "";
				selectedObjectType = "";
				renderObjectListResults();
				clearStdDetailUi();
			},
		});
	}

	function applyKpiSelection(row) {
		if (!row) return;
		activeKpiId = String(row.id || "");
		activeQueueId = String(row.select_queue_id || "");
		activeWorkTab = String(row.select_work_tab || "");
		const shell = getActiveStdShellRoot();
		if (shell) {
			shell.setAttribute("data-active-kpi-id", activeKpiId);
			shell.setAttribute("data-active-queue-id", activeQueueId);
			shell.setAttribute("data-active-work-tab", activeWorkTab);
		}
		renderKpiStrip();
		renderScopeTabs();
		renderQueueBar();
		renderQueueStateHint();
		document.dispatchEvent(
			new CustomEvent("std-workbench:kpi-selected", {
				detail: {
					kpi_id: activeKpiId,
					queue_id: activeQueueId,
					work_tab: activeWorkTab,
				},
			})
		);
	}

	function renderKpiStrip() {
		const root = getActiveStdShellRoot();
		if (!root) return;
		const host = root.querySelector("#kt-std-kpi-host");
		if (!host) return;
		const rows = kpiRows.length ? kpiRows : fallbackKpis();
		let html = "";
		for (let i = 0; i < rows.length; i++) {
			const row = rows[i] || {};
			const id = String(row.id || "kpi_" + i);
			const label = String(row.label || "");
			const value = Number(row.value) || 0;
			const testid = String(row.testid || "std-kpi-" + id.replace(/_/g, "-"));
			const isHighRisk = String(row.risk_level || "").toLowerCase() === "high" || HIGH_RISK_KPI_IDS.has(id);
			const isActive = activeKpiId === id;
			const classes = [
				"kt-std-kpi-card",
				"kt-std-surface",
				isHighRisk ? "kt-std-kpi-card--high-risk" : "",
				isActive ? "is-active" : "",
			]
				.join(" ")
				.trim();
			html +=
				'<button type="button" class="' +
				esc(classes) +
				'" data-std-kpi="' +
				esc(id) +
				'" data-testid="' +
				esc(testid) +
				'" aria-pressed="' +
				(isActive ? "true" : "false") +
				'">' +
				'<span class="kt-std-kpi-card__label">' +
				esc(label) +
				"</span>" +
				'<span class="kt-std-kpi-card__value">' +
				esc(value.toLocaleString()) +
				"</span>" +
				"</button>";
		}
		host.innerHTML = html;
	}

	function ensureStdDelegatedClicks() {
		const root = getActiveStdShellRoot();
		if (!root || root.getAttribute("data-std-kpi-delegated") === "1") return;
		root.setAttribute("data-std-kpi-delegated", "1");
		root.addEventListener("click", function (ev) {
			const target = ev.target;
			if (!target || !target.closest) return;
			const card = target.closest("[data-std-kpi]");
			if (!card) return;
			const kpiId = card.getAttribute("data-std-kpi") || "";
			const row = kpiRows.find((x) => String(x.id || "") === String(kpiId));
			if (row) applyKpiSelection(row);
		});
		root.addEventListener("click", function (ev) {
			const target = ev.target;
			if (!target || !target.closest) return;
			const tab = target.closest("[data-std-scope-tab]");
			if (tab) {
				activeWorkTab = String(tab.getAttribute("data-std-scope-tab") || "");
				if (activeWorkTab) {
					const first = (queueRows.length ? queueRows : fallbackQueues()).find(
						(q) => String(q.scope_tab_id || "") === activeWorkTab
					);
					if (first) activeQueueId = String(first.id || "");
				}
				renderScopeTabs();
				renderQueueBar();
				renderQueueStateHint();
				loadSearchResults();
				return;
			}
			const queue = target.closest("[data-std-queue]");
			if (queue) {
				activeQueueId = String(queue.getAttribute("data-std-queue") || "");
				const scopeId = String(queue.getAttribute("data-std-queue-scope") || "");
				if (scopeId) activeWorkTab = scopeId;
				renderScopeTabs();
				renderQueueBar();
				renderQueueStateHint();
				loadSearchResults();
			}
			const actBtn = target.closest("[data-std-desk-action]");
			if (actBtn && root.contains(actBtn)) {
				ev.preventDefault();
				runStdDeskAction(String(actBtn.getAttribute("data-std-desk-action") || ""));
				return;
			}
			const detTab = target.closest("[data-std-detail-tab]");
			if (detTab && root.contains(detTab)) {
				ev.preventDefault();
				syncStdDetailTabs(String(detTab.getAttribute("data-std-detail-tab") || "overview"));
				return;
			}
			const strBtn = target.closest("[data-std-structure-select]");
			if (strBtn && root.contains(strBtn)) {
				ev.preventDefault();
				selectedStructureKind = String(strBtn.getAttribute("data-std-structure-kind") || "");
				selectedStructureCode = String(strBtn.getAttribute("data-std-structure-code") || "");
				const panel = root.querySelector("#kt-std-detail-tab-panel");
				if (panel) {
					paintStructureDetailInto(panel);
					syncStructureTreeActive(panel);
				}
				return;
			}
			const catBtn = target.closest("[data-std-forms-category]");
			if (catBtn && root.contains(catBtn)) {
				ev.preventDefault();
				activeFormsCategoryId = String(catBtn.getAttribute("data-std-forms-category") || "");
				selectedFormCode = "";
				renderDetailTabPanel();
				return;
			}
			const formRow = target.closest("[data-std-form-code]");
			if (formRow && root.contains(formRow)) {
				ev.preventDefault();
				selectedFormCode = String(formRow.getAttribute("data-std-form-code") || "");
				renderDetailTabPanel();
				return;
			}
			const mapTgt = target.closest("[data-std-mappings-target]");
			if (mapTgt && root.contains(mapTgt)) {
				ev.preventDefault();
				activeMappingsTargetModel = String(mapTgt.getAttribute("data-std-mappings-target") || "Bundle");
				renderDetailTabPanel();
				return;
			}
			const auditExport = target.closest("[data-std-audit-export-csv]");
			if (auditExport && root.contains(auditExport) && !auditExport.disabled) {
				ev.preventDefault();
				runStdTemplateAuditExportCsv();
				return;
			}
			const instParamSave = target.closest("[data-std-inst-param-save]");
			if (instParamSave && root.contains(instParamSave)) {
				ev.preventDefault();
				saveStdInstanceParameterFromRow(instParamSave);
				return;
			}
			const instReadRun = target.closest("[data-std-inst-readiness-run]");
			if (instReadRun && root.contains(instReadRun)) {
				ev.preventDefault();
				runStdInstanceReadinessNow();
				return;
			}
			const instWorksSave = target.closest("[data-std-inst-works-save]");
			if (instWorksSave && root.contains(instWorksSave)) {
				ev.preventDefault();
				saveStdInstanceWorksText(instWorksSave);
				return;
			}
			const instAtt = target.closest("[data-std-inst-attachment-action]");
			if (instAtt && root.contains(instAtt)) {
				ev.preventDefault();
				const act = String(instAtt.getAttribute("data-act") || "");
				if (act === "spec") {
					promptStdInstanceAttachment("Specification", __("Add Specification Attachment"));
				} else if (act === "draw") {
					promptStdInstanceAttachment("Drawing", __("Add Drawing to Register"));
				} else if (act === "sup") {
					frappe.show_alert({ message: __("Supersede via addendum workflow in Desk."), indicator: "orange" });
				}
				return;
			}
			const row = target.closest("[data-std-object-code]");
			if (row) {
				selectedObjectCode = String(row.getAttribute("data-std-object-code") || "");
				selectedObjectType = String(row.getAttribute("data-std-object-type") || "");
				syncStdListSelection(root, selectedObjectCode);
				renderDetailSelection();
				return;
			}
			const toggle = target.closest("[data-std-filter-toggle]");
			if (toggle) {
				filtersCollapsed = !filtersCollapsed;
				renderFilterCollapsedState();
			}
		});
		root.addEventListener("change", function (ev) {
			const target = ev.target;
			if (!target || !target.getAttribute) return;
			if (!target.getAttribute("data-std-filter")) return;
			activeFilters = collectFiltersFromUi();
			renderFilterChips();
			loadSearchResults();
		});
		const search = root.querySelector('[data-testid="std-search-input"]');
		if (search) {
			search.addEventListener("input", function () {
				searchQuery = String(search.value || "").trim();
				if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
				searchDebounceTimer = setTimeout(loadSearchResults, 200);
			});
		}
	}

	function loadStdKpiStripData() {
		if (!routeLooksLikeStdEngine()) return;
		frappe.call({
			method: "kentender_procurement.std_engine.api.landing.get_std_workbench_kpi_strip",
			callback: function (r) {
				if (!routeLooksLikeStdEngine()) return;
				const payload = (r && r.message) || {};
				kpiRows = Array.isArray(payload.kpis) && payload.kpis.length ? payload.kpis : fallbackKpis();
				scopeTabs = Array.isArray(payload.scope_tabs) && payload.scope_tabs.length ? payload.scope_tabs : fallbackScopeTabs();
				queueRows = Array.isArray(payload.queues) && payload.queues.length ? payload.queues : fallbackQueues();
				if (!activeWorkTab) activeWorkTab = String(payload.default_scope_tab_id || "mywork");
				if (!activeQueueId) activeQueueId = String(payload.default_queue_id || "");
				renderKpiStrip();
				renderScopeTabs();
				renderQueueBar();
				if (!activeKpiId && kpiRows.length) {
					applyKpiSelection(kpiRows[0]);
				} else {
					renderQueueStateHint();
				}
				activeFilters = collectFiltersFromUi();
				renderFilterChips();
				loadSearchResults();
			},
			error: function () {
				if (!routeLooksLikeStdEngine()) return;
				kpiRows = fallbackKpis();
				scopeTabs = fallbackScopeTabs();
				queueRows = fallbackQueues();
				if (!activeWorkTab) activeWorkTab = "mywork";
				if (!activeQueueId) activeQueueId = "validation_blocked";
				renderKpiStrip();
				renderScopeTabs();
				renderQueueBar();
				if (!activeKpiId && kpiRows.length) {
					applyKpiSelection(kpiRows[0]);
				} else {
					renderQueueStateHint();
				}
				activeFilters = collectFiltersFromUi();
				renderFilterChips();
				loadSearchResults();
			},
		});
	}

	function injectShell() {
		if (shellPresent()) return { ok: true, inserted: false };
		const mount = resolveMount();
		if (!mount) return { ok: false, inserted: false };

		const shell = document.createElement('section');
		shell.className = 'kt-std-injected-shell';
		shell.setAttribute('data-testid', 'std-workbench-page');
		shell.innerHTML =
			'<header class="kt-std-header kt-std-surface">' +
			'<div>' +
			'<h2 class="h5 mb-1" data-testid="std-page-title">' + esc(__(WS_NAME)) + '</h2>' +
			'<p class="small text-muted mb-0">' + esc(__("STD Engine workbench shell (Phase 10 ticket 1001).")) + '</p>' +
			'</div>' +
			'<div class="kt-std-header-actions" data-testid="std-action-bar">' +
			'<div id="kt-std-action-host" class="kt-std-action-host d-flex flex-wrap gap-1 justify-content-end" data-testid="std-action-host">' +
			'<span class="text-muted small">' + esc(__("Select an object to see actions.")) + "</span></div></div>" +
			'</header>' +
			'<section class="kt-std-surface" data-testid="std-kpi-strip"><div id="kt-std-kpi-host" class="kt-std-kpi-grid"></div></section>' +
			'<section class="kt-std-surface" data-testid="std-scope-tabs"><div id="kt-std-scope-host" class="kt-std-scope-tabs"></div></section>' +
			'<section class="kt-std-surface" data-testid="std-queue-bar"><div id="kt-std-queue-host" class="kt-std-queue-row"></div><div class="small text-muted mt-1" data-testid="std-active-queue-state">' + esc(__("No queue selected yet.")) + '</div></section>' +
			'<section class="kt-std-surface kt-std-search-row">' +
			'<input class="form-control form-control-sm" type="search" placeholder="' + esc(__("Search")) + '" data-testid="std-search-input" />' +
			'<div class="small text-muted" data-testid="std-filter-panel">' + esc(__("Filters placeholder")) + '</div>' +
			'</section>' +
			'<section class="kt-std-main">' +
			'<div class="kt-std-surface" data-testid="std-object-list"><h3 class="h6 mb-1">' + esc(__("Object List")) + '</h3><p class="small text-muted mb-0">' + esc(__("List panel placeholder")) + '</p></div>' +
			'<div class="kt-std-surface kt-std-detail" data-testid="std-object-detail">' +
			'<h3 class="h6 mb-2">' + esc(__("Object Detail")) + "</h3>" +
			'<div class="kt-std-detail-header mb-2" data-testid="std-detail-header" id="kt-std-detail-header">' +
			'<p class="small text-muted mb-0" data-testid="std-detail-empty-hint">' +
			esc(__("Select an object from the list.")) +
			"</p></div>" +
			'<div class="kt-std-state-cards mb-2" data-testid="std-detail-state-cards" id="kt-std-detail-state-cards"></div>' +
			'<div class="kt-std-detail-tabs mb-2" data-testid="std-detail-tabs" role="tablist" aria-label="' +
			esc(__("Detail tabs")) +
			'">' +
			'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab is-active" data-std-detail-tab="overview" data-testid="std-detail-tab-overview" aria-selected="true">' +
			esc(__("Overview")) +
			'</button>' +
			'<button type="button" class="btn btn-xs btn-default kt-std-detail-tab" data-std-detail-tab="audit" data-testid="std-detail-tab-audit" aria-selected="false">' +
			esc(__("Audit")) +
			"</button></div>" +
			'<div class="kt-std-detail-tab-panel mb-2" data-testid="std-detail-tab-panel" id="kt-std-detail-tab-panel"></div>' +
			'<div data-testid="std-blockers-panel" class="kt-std-blockers-panel small" id="kt-std-detail-blockers">' +
			'<span class="text-muted small">' + esc(__("No blockers for current selection.")) + "</span></div></div>" +
			'</section>';

		const editor = mount.querySelector && mount.querySelector('#editorjs');
		if (editor && mount.contains(editor)) {
			mount.insertBefore(shell, editor);
		} else {
			mount.insertBefore(shell, mount.firstChild);
		}
		renderFilterPanel();
		ensureStdDelegatedClicks();
		return { ok: true, inserted: true };
	}

	function removeShellIfOffRoute() {
		if (routeLooksLikeStdEngine()) return;
		document.querySelectorAll('.kt-std-injected-shell').forEach((n) => n.remove());
		document.body.classList.remove('kt-std-shell');
		bindScheduled = false;
	}

	function bindShell() {
		if (!routeLooksLikeStdEngine()) {
			removeShellIfOffRoute();
			return;
		}
		syncBodyClass();
		const result = injectShell();
		if (!result.ok) {
			setTimeout(scheduleBind, 250);
			return;
		}
		ensureStdDelegatedClicks();
		loadStdKpiStripData();
	}

	function scheduleBind() {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			bindShell();
		}, 0);
	}

	function bindHooks() {
		if (hooksBound) return;
		hooksBound = true;
		if (typeof MutationObserver !== 'undefined' && !domObserver) {
			domObserver = new MutationObserver(function () {
				if (routeLooksLikeStdEngine() && !shellPresent()) scheduleBind();
			});
			domObserver.observe(document.body, { childList: true, subtree: true });
		}
		document.addEventListener('page-change', scheduleBind);
		document.addEventListener('app_ready', scheduleBind);
		if (typeof frappe !== 'undefined' && frappe.router && frappe.router.on) {
			frappe.router.on('change', scheduleBind);
		}
	}

	bindHooks();
	scheduleBind();
})();
