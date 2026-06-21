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

	function renderSurfaceShellPlaceholder(root, slug) {
		if (!root) return;
		const surface = surfaceForSlug(slug);
		root.innerHTML =
			'<section class="pp2-canonical-surface" data-testid="pp2-canonical-surface">' +
			'<h3 class="h6 mb-1">' +
			esc(surface.subtitle || __("Procurement Planning")) +
			"</h3>" +
			'<p class="text-muted small mb-0">' +
			esc(__("Choose a planning workspace action from the navigation menu.")) +
			"</p>" +
			"</section>";
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
			contextHost.innerHTML = "";
		}
		const nextActionPanel = shell.querySelector('[data-testid="pp2-primary-next-action-panel"]');
		if (nextActionPanel) {
			nextActionPanel.innerHTML =
				'<strong class="d-block mb-1">' +
				esc(__("Next action")) +
				"</strong>" +
				esc(__("Open a planning queue from the sidebar to continue."));
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

	function pruneForbiddenPlanningNavLinks() {
		const anchors = document.querySelectorAll(".sidebar-items .item-anchor");
		for (let i = 0; i < anchors.length; i += 1) {
			const anchor = anchors[i];
			const labelEl = anchor.querySelector(".sidebar-item-label");
			const label = String(labelEl ? labelEl.textContent || "" : "")
				.trim()
				.toLowerCase();
			const href = String(anchor.getAttribute("href") || "").toLowerCase();
			const isEvidenceNav =
				label === "planning evidence" || href.endsWith("/procurement-planning/evidence");
			if (!isEvidenceNav) continue;
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

	function mount() {
		const planningRoute = isPlanningWorkspaceRoute();
		const slug = planningRoute ? readSurfaceSlug() : "";
		normalizeChildLinkRoutes();
		const hierarchyReady = enhanceSidebarVisualHierarchy(slug, planningRoute);
		if (!planningRoute) {
			document.body.classList.remove("kt-pp2-shell");
			return hierarchyReady;
		}
		const root = ensureWorkspaceRoot();
		if (!root) return false;
		syncSurfaceUrl(slug);
		const shell = ensurePrimaryWorkspaceShell(root, slug);
		if (!shell) return false;
		const mainHost = shell.querySelector('[data-testid="pp2-primary-main-host"]');
		if (mainHost) {
			const children = Array.from(mainHost.children);
			for (let i = 0; i < children.length; i += 1) {
				if (children[i] !== root) {
					mainHost.removeChild(children[i]);
				}
			}
		}
		const markerId = surfaceForSlug(slug).testId;
		root.setAttribute("data-testid", markerId);
		renderSurfaceShellPlaceholder(root, slug);
		document.body.classList.add("kt-pp2-shell");
		syncSidebarActive(slug);
		return true;
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
