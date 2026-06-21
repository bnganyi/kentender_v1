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
		"": __("Planning Home"),
		"approved-demands": __("Approved Demands"),
		plans: __("Plans"),
		packages: __("Packages"),
		releases: __("Released to Tender"),
	};

	const SURFACES = {
		"": {
			testId: "pp2-planning-home",
			title: __("Procurement Planning"),
			subtitle: __("Planning Home"),
		},
		"approved-demands": {
			testId: "pp2-approved-demands-page",
			title: __("Procurement Planning"),
			subtitle: __("Approved Demands"),
		},
		plans: {
			testId: "pp2-plans-page",
			title: __("Procurement Planning"),
			subtitle: __("Plans"),
		},
		packages: {
			testId: "pp2-packages-page",
			title: __("Procurement Planning"),
			subtitle: __("Packages"),
		},
		releases: {
			testId: "pp2-released-to-tender-page",
			title: __("Procurement Planning"),
			subtitle: __("Released to Tender"),
		},
	};

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
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
		if (path.endsWith("/approved-demands")) return "approved-demands";
		if (path.endsWith("/plans")) return "plans";
		if (path.endsWith("/packages")) return "packages";
		if (path.endsWith("/releases")) return "releases";
		return "";
	}

	const CANONICAL_PLANNING_SLUGS = {
		"approved-demands": true,
		plans: true,
		packages: true,
		releases: true,
	};

	const INTERNAL_PLANNING_LEGACY_SLUGS = {
		evidence: true,
		inclusions: true,
		readiness: true,
		review: true,
		lines: true,
		technical: true,
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

	function buildPackagesRedirectUrl(packageCode) {
		const url = new URL(window.location.origin + ROOT_PATH + "/packages");
		const code = String(packageCode || "").trim();
		if (code) {
			url.searchParams.set("package_code", decodeURIComponent(code));
		}
		return url.pathname + url.search;
	}

	function resolvePlanningRoute(pathname) {
		const segments = parsePlanningPathname(pathname);
		const rawSegments = readPlanningRawSegments(pathname);
		if (!segments.length) {
			return { action: "canonical", slug: "" };
		}

		const head = segments[0];
		if (CANONICAL_PLANNING_SLUGS[head] && segments.length === 1) {
			return { action: "canonical", slug: head };
		}

		const requiresInternalAccess =
			INTERNAL_PLANNING_LEGACY_SLUGS[head] ||
			(head === "packages" && segments.length > 1) ||
			(head === "plans" && segments.length > 1) ||
			(head === "releases" && segments.length > 1);
		if (requiresInternalAccess && !mayAccessInternalPlanningLegacyRoute()) {
			return { action: "not_found", reason: "denied" };
		}

		if (head === "evidence") {
			return {
				action: "redirect",
				slug: "packages",
				redirectUrl: buildPackagesRedirectUrl(rawSegments[1] || ""),
			};
		}
		if (head === "inclusions") {
			return {
				action: "redirect",
				slug: "approved-demands",
				redirectUrl: `${ROOT_PATH}/approved-demands`,
			};
		}
		if (head === "readiness" || head === "review" || head === "lines" || head === "technical" || head === "audit") {
			return {
				action: "redirect",
				slug: "packages",
				redirectUrl: `${ROOT_PATH}/packages`,
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
				slug: "packages",
				redirectUrl: buildPackagesRedirectUrl(rawSegments[1] || ""),
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
			esc(__("This planning page is not available or you do not have access.")) +
			"</p>" +
			"</section>";
	}

	function surfaceForSlug(slug) {
		return SURFACES[slug] || SURFACES[""];
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
		plans: __("Which plan owns this procurement work?"),
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
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningQueueTabs &&
			typeof kentender_procurement.PlanningQueueTabs.renderForSlug === "function"
				? kentender_procurement.PlanningQueueTabs
				: null;
		if (api) {
			api.renderForSlug(queueHost, slug);
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
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningSelectedSummaryPanel &&
			typeof kentender_procurement.PlanningSelectedSummaryPanel.renderIdle === "function"
				? kentender_procurement.PlanningSelectedSummaryPanel
				: null;
		if (!api) {
			summaryHost.innerHTML = "";
			return;
		}
		const o = opts || {};
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
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningWorkList &&
			typeof kentender_procurement.PlanningWorkList.renderForSlug === "function"
				? kentender_procurement.PlanningWorkList
				: null;
		const onSelect = function (_itemId, item) {
			if (!shell) return;
			const summaryApi =
				kentender_procurement &&
				kentender_procurement.PlanningSelectedSummaryPanel &&
				typeof kentender_procurement.PlanningSelectedSummaryPanel.summaryFromWorkItem === "function"
					? kentender_procurement.PlanningSelectedSummaryPanel
					: null;
			if (summaryApi && item) {
				mountPlanningSelectedSummary(shell, { summary: summaryApi.summaryFromWorkItem(item) });
			}
		};
		if (api) {
			api.renderForSlug(workListHost, slug, { items: [], onSelect: onSelect });
			return;
		}
		workListHost.innerHTML = "";
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
				'<div class="pp2-primary-workspace-shell__header">' +
				'<div class="pp2-primary-workspace-shell__breadcrumb text-muted small" data-testid="pp2-primary-breadcrumb"></div>' +
				'<div class="pp2-primary-workspace-shell__context" data-testid="pp2-primary-context-host"></div>' +
				"</div>" +
				'<div class="pp2-primary-workspace-shell__layout">' +
				'<div class="pp2-primary-workspace-shell__main" data-testid="pp2-primary-main-host"></div>' +
				'<aside class="pp2-primary-workspace-shell__right" data-testid="pp2-primary-right-panel">' +
				'<button type="button" class="btn btn-xs btn-default pp2-primary-workspace-shell__toggle" data-testid="pp2-primary-right-panel-toggle"></button>' +
				'<div class="pp2-primary-summary-host" data-testid="pp2-primary-summary-host"></div>' +
				'<div class="pp2-primary-workspace-shell__next-action text-muted small" data-testid="pp2-primary-next-action-panel"></div>' +
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
		pruneDuplicatePrimaryShells(shell);

		const breadcrumb = shell.querySelector('[data-testid="pp2-primary-breadcrumb"]');
		if (breadcrumb) {
			breadcrumb.textContent = __("Procurement Planning") + " / " + surface.subtitle;
		}
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost) {
			mountPlanningPageHeader(contextHost, slug);
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
			});
		}
		if (toggle) {
			const collapsed = shell.getAttribute("data-right-panel-collapsed") === "1";
			toggle.textContent = collapsed ? __("Expand panel") : __("Collapse panel");
		}
		ensureSummaryHost(shell);
		mountPlanningSelectedSummary(shell, {});

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

	function enhanceSidebarVisualHierarchy(slug, parentActive) {
		const parent = document.querySelector('.section-item[title="Procurement Planning"]');
		if (!parent) return false;
		parent.classList.add("kt-pp2-sidebar-parent");
		parent.classList.toggle("kt-pp2-sidebar-parent-active", !!parentActive);
		if (!parentActive) {
			const nested = parent.querySelector(".nested-container");
			const dropIcon = parent.querySelector(".drop-icon");
			const expanded = !!(
				nested &&
				window.getComputedStyle(nested).display !== "none" &&
				nested.querySelector(".item-anchor")
			);
			if (expanded && dropIcon && typeof dropIcon.click === "function") {
				dropIcon.click();
			}
		}
		const sectionBreak = parent.querySelector(".section-break");
		if (sectionBreak && !sectionBreak.querySelector(".kt-pp2-parent-icon")) {
			const icon = document.createElement("span");
			icon.className = "kt-pp2-parent-icon sidebar-item-icon text-ink-gray-7";
			let iconHtml = "";
			try {
				if (frappe.utils && typeof frappe.utils.icon === "function") {
					iconHtml = frappe.utils.icon("kanban", "sm");
				}
			} catch (e) {
				/* ignore */
			}
			icon.innerHTML = iconHtml || '<span aria-hidden="true">▦</span>';
			sectionBreak.insertBefore(icon, sectionBreak.firstChild);
		}
		const anchors = parent.querySelectorAll(".nested-container .item-anchor");
		for (let i = 0; i < anchors.length; i += 1) {
			anchors[i].classList.add("kt-pp2-sidebar-child");
			const labelEl = anchors[i].querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "")
				.trim()
				.toLowerCase();
			const targetLabel = parentActive ? String(SURFACE_LABELS[slug || ""] || "").trim().toLowerCase() : "";
			const isActive = !!targetLabel && label === targetLabel;
			anchors[i].classList.toggle("kt-pp2-sidebar-child-active", isActive);
		}
		return true;
	}

	const FORBIDDEN_PLANNING_NAV_LABELS = {
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
		const section = document.querySelector('.section-item[title="Procurement Planning"]');
		if (!section) return [];
		const nested = section.querySelector(".nested-container");
		const scope = nested || section;
		return Array.from(scope.querySelectorAll(".item-anchor"));
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
		const routeByLabel = {
			"planning home": ROOT_PATH,
			"approved demands": `${ROOT_PATH}/approved-demands`,
			plans: `${ROOT_PATH}/plans`,
			packages: `${ROOT_PATH}/packages`,
			"released to tender": `${ROOT_PATH}/releases`,
		};
		const anchors = document.querySelectorAll(".sidebar-items .item-anchor");
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "").trim().toLowerCase();
			const targetPath = routeByLabel[label];
			if (!targetPath) continue;
			anchor.setAttribute("href", targetPath);
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
		const drawerApi =
			kentender_procurement &&
			kentender_procurement.PlanningEvidenceDrawer &&
			typeof kentender_procurement.PlanningEvidenceDrawer.close === "function"
				? kentender_procurement.PlanningEvidenceDrawer
				: null;
		if (drawerApi) {
			drawerApi.close();
		}
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
			const shell = ensurePrimaryWorkspaceShell(root, "");
			if (!shell) return false;
			root.setAttribute("data-testid", "pp2-planning-home");
			renderRouteNotFound(root);
			document.body.classList.add("kt-pp2-shell");
			syncSidebarActive("");
			return hierarchyReady;
		}

		const hasDeepLinkQuery = String(window.location.search || "").indexOf("package_code=") !== -1;
		syncSurfaceUrl(slug, { preserveSearch: slug === "packages" && hasDeepLinkQuery });
		const shell = ensurePrimaryWorkspaceShell(root, slug);
		if (!shell) return false;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (mainHost) {
			const queueHost = mainHost.querySelector('[data-testid="pp2-primary-queue-host"]');
			const filtersHost = mainHost.querySelector('[data-testid="pp2-primary-filters-host"]');
			const workListHost = mainHost.querySelector('[data-testid="pp2-primary-work-list-host"]');
			const children = Array.from(mainHost.children);
			for (let i = 0; i < children.length; i += 1) {
				if (
					children[i] !== root &&
					children[i] !== queueHost &&
					children[i] !== filtersHost &&
					children[i] !== workListHost
				) {
					mainHost.removeChild(children[i]);
				}
			}
			mountPlanningQueueTabs(mainHost, slug);
			const queueApi =
				kentender_procurement &&
				kentender_procurement.PlanningQueueTabs &&
				typeof kentender_procurement.PlanningQueueTabs.readActiveFromUrl === "function"
					? kentender_procurement.PlanningQueueTabs
					: null;
			if (queueApi) {
				try {
					const raw = new URLSearchParams(window.location.search).get("queue");
					if (raw) {
						const activeQueue = queueApi.readActiveFromUrl(slug);
						if (raw !== activeQueue) {
							queueApi.setQueueUrl(activeQueue);
						}
					}
				} catch (e) {
					/* ignore */
				}
			}
			mountPlanningAdvancedFilters(mainHost, slug);
			mountPlanningWorkList(mainHost, slug, shell);
			const workListApi =
				kentender_procurement &&
				kentender_procurement.PlanningWorkList &&
				typeof kentender_procurement.PlanningWorkList.readSelectedFromUrl === "function"
					? kentender_procurement.PlanningWorkList
					: null;
			if (workListApi) {
				try {
					const rawItem = new URLSearchParams(window.location.search).get("item");
					if (rawItem && !workListApi.readSelectedFromUrl([])) {
						workListApi.setSelectedUrl("");
					}
				} catch (e) {
					/* ignore */
				}
			}
		}
		const markerId = surfaceForSlug(slug).testId;
		root.setAttribute("data-testid", markerId);
		renderSurfaceEmptyState(root, slug);
		document.body.classList.add("kt-pp2-shell");
		syncSidebarActive(slug);
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
