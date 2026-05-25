/** PP2 P5-001 — Procurement Planning nested surfaces inside main Procurement shell. */
(function () {
	const WORKSPACE_NAME = "Procurement Planning";
	const ROOT_PATH = "/desk/procurement-planning";
	const RIGHT_PANEL_STATE_KEY = "kt-pp2-right-panel-collapsed";
	let sidebarObserver = null;
	let sidebarRefreshQueued = false;
	let passiveSidebarPollStarted = false;

	const SURFACE_LABELS = {
		"": __("Planning Home"),
		"approved-demands": __("Approved Demands"),
		packages: __("Packages"),
		releases: __("Released to Tender"),
		evidence: __("Planning Evidence"),
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
		packages: {
			testId: "pp2-package-workbench",
			title: __("Procurement Planning"),
			subtitle: __("Packages"),
		},
		releases: {
			testId: "pp2-released-to-tender-page",
			title: __("Procurement Planning"),
			subtitle: __("Released to Tender"),
		},
		evidence: {
			testId: "pp2-planning-evidence-index",
			title: __("Procurement Planning"),
			subtitle: __("Planning Evidence"),
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
		if (path.endsWith("/packages")) return "packages";
		if (path.endsWith("/releases")) return "releases";
		if (path.endsWith("/evidence")) return "evidence";
		return "";
	}

	function surfaceForSlug(slug) {
		return SURFACES[slug] || SURFACES[""];
	}

	function readRightPanelCollapsed() {
		try {
			return window.localStorage.getItem(RIGHT_PANEL_STATE_KEY) === "1";
		} catch (e) {
			return false;
		}
	}

	function writeRightPanelCollapsed(collapsed) {
		try {
			window.localStorage.setItem(RIGHT_PANEL_STATE_KEY, collapsed ? "1" : "0");
		} catch (e) {
			/* ignore */
		}
	}

	function syncSurfaceUrl(slug) {
		const url = new URL(window.location.href);
		url.pathname = slug ? `${ROOT_PATH}/${slug}` : ROOT_PATH;
		const next = url.pathname + url.search + url.hash;
		const curr = window.location.pathname + window.location.search + window.location.hash;
		if (next !== curr) {
			window.history.replaceState({}, "", next);
		}
	}

	function buildShellHtml(slug) {
		const surface = surfaceForSlug(slug);
		return (
			'<div class="pp2-planning-page kt-pp2-shell" data-testid="' +
			esc(surface.testId) +
			'">' +
			'<div class="pp2-planning-page__header">' +
			"<h3 class=\"mb-1\">" +
			esc(surface.title) +
			"</h3>" +
			'<p class="text-muted mb-0">' +
			esc(surface.subtitle) +
			"</p>" +
			"</div>" +
			'<div class="pp2-planning-page__body text-muted small">' +
			esc(__("Surface content will be implemented in subsequent P5 tickets.")) +
			"</div>" +
			"</div>"
		);
	}

	function resolveWorkspaceRoot() {
		return (
			document.getElementById("kt-pp-root") ||
			document.querySelector(".kt-pp-injected-shell") ||
			document.querySelector('[data-testid="pp-landing-page"]')
		);
	}

	function ensurePrimaryWorkspaceShell(root, slug) {
		if (!root) return null;
		const surface = surfaceForSlug(slug);
		let shell = root.closest('[data-testid="pp2-primary-workspace-shell"]');
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
				'<div class="pp2-primary-workspace-shell__next-action text-muted small" data-testid="pp2-primary-next-action-panel"></div>' +
				"</aside>" +
				"</div>";
			root.parentNode.insertBefore(shell, root);
		}

		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (mainHost && root.parentNode !== mainHost) {
			mainHost.appendChild(root);
		}

		const breadcrumb = shell.querySelector('[data-testid="pp2-primary-breadcrumb"]');
		if (breadcrumb) {
			breadcrumb.textContent = __("Procurement Planning") + " / " + surface.subtitle;
		}
		const contextHost = shell.querySelector('[data-testid="pp2-primary-context-host"]');
		if (contextHost) {
			contextHost.textContent = __("Primary workspace shell") + " - " + surface.subtitle;
		}
		const nextActionPanel = shell.querySelector('[data-testid="pp2-primary-next-action-panel"]');
		if (nextActionPanel) {
			nextActionPanel.innerHTML =
				'<strong class="d-block mb-1">' +
				esc(__("Next action")) +
				"</strong>" +
				esc(__("Continue in ")) +
				esc(surface.subtitle) +
				". " +
				esc(__("Blockers and evidence will appear here as P5 surfaces are completed."));
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

	function normalizeChildLinkRoutes() {
		const routeByLabel = {
			"planning home": ROOT_PATH,
			"approved demands": `${ROOT_PATH}/approved-demands`,
			packages: `${ROOT_PATH}/packages`,
			"released to tender": `${ROOT_PATH}/releases`,
			"planning evidence": `${ROOT_PATH}/evidence`,
		};
		const anchors = document.querySelectorAll(".sidebar-items .item-anchor");
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "").trim().toLowerCase();
			const targetPath = routeByLabel[label];
			if (!targetPath) continue;
			anchor.setAttribute("href", targetPath);
			anchor.onclick = function (ev) {
				ev.preventDefault();
				window.history.pushState({}, "", targetPath);
				scheduleBoot();
			};
		}
	}

	function queueSidebarRefresh() {
		if (sidebarRefreshQueued) return;
		sidebarRefreshQueued = true;
		window.setTimeout(function () {
			sidebarRefreshQueued = false;
			scheduleBoot();
		}, 40);
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
				for (let j = 0; j < m.addedNodes.length; j += 1) {
					if (elementTouchesSidebar(m.addedNodes[j])) {
						queueSidebarRefresh();
						return;
					}
				}
				for (let k = 0; k < m.removedNodes.length; k += 1) {
					if (elementTouchesSidebar(m.removedNodes[k])) {
						queueSidebarRefresh();
						return;
					}
				}
			}
		});
		sidebarObserver.observe(target, { childList: true, subtree: true });
	}

	function ensurePassiveSidebarPoll() {
		if (passiveSidebarPollStarted) return;
		passiveSidebarPollStarted = true;
		window.setInterval(function () {
			if (document.hidden) return;
			mount();
		}, 900);
	}

	function mount() {
		const planningRoute = isPlanningWorkspaceRoute();
		const slug = planningRoute ? readSurfaceSlug() : "";
		normalizeChildLinkRoutes();
		const hierarchyReady = enhanceSidebarVisualHierarchy(slug, planningRoute);
		if (!planningRoute) {
			document.body.classList.remove("kt-pp2-shell");
			return hierarchyReady;
		}
		const root = resolveWorkspaceRoot();
		if (!root) return false;
		syncSurfaceUrl(slug);
		ensurePrimaryWorkspaceShell(root, slug);
		const markerId = surfaceForSlug(slug).testId;
		root.setAttribute("data-testid", markerId);
		const existingMarker = root.querySelector(".pp2-route-marker");
		if (existingMarker) existingMarker.remove();
		const marker = document.createElement("div");
		marker.className = "pp2-route-marker text-muted small mt-2";
		marker.textContent = surfaceForSlug(slug).subtitle;
		root.appendChild(marker);
		document.body.classList.add("kt-pp2-shell");
		syncSidebarActive(slug);
		return true;
	}

	function scheduleBoot() {
		ensureSidebarObserver();
		ensurePassiveSidebarPoll();
		if (mount()) return;
		let retries = 0;
		const timer = setInterval(function () {
			retries += 1;
			if (mount() || retries >= 60) {
				clearInterval(timer);
			}
		}, 50);
	}

	$(document).on("page-change", scheduleBoot);
	$(document).on("app_ready", scheduleBoot);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", scheduleBoot);
	}
	scheduleBoot();
})();
