// Procurement Home workbench — Desk shell (IA v1.0 §5.1, pack §11.1).

(function () {
	const HOME_WS = "Procurement Home";
	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function workspaceNameMatchesHome(name) {
		if (name == null || name === "") return false;
		if (name === HOME_WS) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(HOME_WS);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "procurement-home";
	}

	function isHomeWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesHome(workspaceName)) return true;
					if (workspaceName) return false;
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const dr = (document.body && document.body.getAttribute("data-route")) || "";
			const parts = dr.split("/").filter(Boolean);
			if (parts[0] === "Workspaces" && parts.length >= 2) {
				const w = parts[1] === "private" && parts.length >= 3 ? parts[2] : parts[1];
				if (workspaceNameMatchesHome(w)) return true;
				if (w) return false;
			}
		} catch (e1) {
			/* ignore */
		}
		try {
			const loc = window.location;
			const raw = (loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "";
			const path = decodeURIComponent(String(raw).toLowerCase());
			if (
				path.includes("procurement-home") ||
				path.includes("procurement%20home") ||
				path.includes("procurement home")
			) {
				return true;
			}
		} catch (e2) {
			/* ignore */
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesHome(w)) return true;
				if (w) return false;
			}
		} catch (e3) {
			return false;
		}
		return false;
	}

	function syncHomeShellClass() {
		document.body.classList.toggle("kt-ph-shell", isHomeWorkspaceRoute());
	}

	function removeHomeLandingIfWrongRoute() {
		document.querySelectorAll(".kt-ph-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-ph-shell");
		bindScheduled = false;
	}

	function getVisibleWorkspacesPageRoot() {
		try {
			if (typeof frappe !== "undefined" && frappe.container && frappe.container.page) {
				const p = frappe.container.page;
				const route = p.getAttribute && p.getAttribute("data-page-route");
				if (route === "Workspaces" && p.isConnected) {
					return p;
				}
			}
		} catch (e) {
			/* ignore */
		}
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	function homeShellPresentOnActiveWsPage() {
		const root = getVisibleWorkspacesPageRoot();
		if (!root) return false;
		return root.querySelector(".kt-ph-injected-shell") != null;
	}

	function resolveWorkspaceEditorMount() {
		const root = getVisibleWorkspacesPageRoot();
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

	function injectHomeLandingShell() {
		if (homeShellPresentOnActiveWsPage()) {
			return { ok: true, inserted: false };
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false, inserted: false };
		const wrap = document.createElement("div");
		wrap.id = "kt-ph-root";
		wrap.className = "kt-ph-injected-shell";
		wrap.setAttribute("data-testid", "ph-landing-page");
		wrap.innerHTML =
			'<div id="kt-ph-active-journeys" class="kt-ph-section kt-surface plc-procurement-home-active-journeys" data-testid="plc-procurement-home-active-journeys">' +
			'<h3 class="kt-ph-section-title h6 mb-2">' +
			escapeHtml(__("Active Procurement Journeys")) +
			"</h3>" +
			'<div id="kt-ph-active-journeys-host" class="kt-ph-active-journeys-host">' +
			'<p class="text-muted small mb-0 kt-ph-active-journeys-loading">' +
			escapeHtml(__("Loading journeys…")) +
			"</p>" +
			"</div>" +
			"</div>" +
			'<div id="kt-ph-needs-action" class="kt-ph-section kt-surface plc-procurement-home-needs-action">' +
			'<h3 class="kt-ph-section-title h6 mb-2">' +
			escapeHtml(__("Needs My Action")) +
			"</h3>" +
			'<div id="kt-ph-needs-action-host" class="kt-ph-journey-panel-host">' +
			'<p class="text-muted small mb-0 kt-ph-panel-loading">' +
			escapeHtml(__("Loading journeys…")) +
			"</p>" +
			"</div>" +
			"</div>" +
			'<div id="kt-ph-blocked-journeys" class="kt-ph-section kt-surface plc-procurement-home-blocked-journeys">' +
			'<h3 class="kt-ph-section-title h6 mb-2">' +
			escapeHtml(__("Blocked Journeys")) +
			"</h3>" +
			'<div id="kt-ph-blocked-journeys-host" class="kt-ph-journey-panel-host">' +
			'<p class="text-muted small mb-0 kt-ph-panel-loading">' +
			escapeHtml(__("Loading journeys…")) +
			"</p>" +
			"</div>" +
			"</div>" +
			'<div id="kt-ph-ready-for-handoff" class="kt-ph-section kt-surface plc-procurement-home-ready-for-handoff">' +
			'<h3 class="kt-ph-section-title h6 mb-2">' +
			escapeHtml(__("Ready for Handoff")) +
			"</h3>" +
			'<div id="kt-ph-ready-for-handoff-host" class="kt-ph-journey-panel-host">' +
			'<p class="text-muted small mb-0 kt-ph-panel-loading">' +
			escapeHtml(__("Loading journeys…")) +
			"</p>" +
			"</div>" +
			"</div>";

		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) {
			esc.insertBefore(wrap, ed);
			ed.style.display = "none";
		} else {
			esc.insertBefore(wrap, esc.firstChild);
		}

		ensureHomeDelegatedClicks();
		return { ok: true, inserted: true };
	}

	function formatBlockersLabel(item) {
		const bc = Number(item && item.blocker_count) || 0;
		const cc = Number(item && item.critical_blocker_count) || 0;
		if (bc === 0 && cc === 0) {
			return __("None");
		}
		const parts = [];
		if (cc > 0) {
			parts.push(cc + " " + __("critical"));
		}
		if (bc > 0) {
			parts.push(bc + " " + __("total"));
		}
		return parts.join(", ");
	}

	function renderHomeJourneyCard(item) {
		const title = (item && item.journey_title) || "";
		const code = (item && item.journey_code) || "";
		const stage = (item && item.current_stage_label) || "";
		const next = (item && item.next_action) || __("—");
		const blockers = formatBlockersLabel(item);
		const tenderCode = (item && item.primary_object_code) || "";
		let actions =
			'<button type="button" class="btn btn-primary btn-sm plc-home-open-journey" data-testid="plc-home-open-journey" data-journey-code="' +
			escapeHtml(code) +
			'">' +
			escapeHtml(__("Open Journey")) +
			"</button>";
		if (tenderCode) {
			actions +=
				'<button type="button" class="btn btn-default btn-sm plc-home-open-tender" data-tender-code="' +
				escapeHtml(tenderCode) +
				'">' +
				escapeHtml(__("Open Tender")) +
				"</button>";
		}
		actions +=
			'<button type="button" class="btn btn-default btn-sm plc-home-view-evidence" data-journey-code="' +
			escapeHtml(code) +
			'">' +
			escapeHtml(__("View Evidence")) +
			"</button>";
		return (
			'<div class="kt-ph-journey-card kt-surface">' +
			'<div class="kt-ph-journey-card-title fw-semibold">' +
			escapeHtml(title) +
			"</div>" +
			'<div class="kt-ph-journey-card-meta small text-muted">' +
			"<div><strong>" +
			escapeHtml(__("Current stage")) +
			":</strong> " +
			escapeHtml(stage) +
			"</div>" +
			"<div><strong>" +
			escapeHtml(__("Next action")) +
			":</strong> " +
			escapeHtml(next) +
			"</div>" +
			"<div><strong>" +
			escapeHtml(__("Blockers")) +
			":</strong> " +
			escapeHtml(blockers) +
			"</div>" +
			"</div>" +
			'<div class="kt-ph-journey-card-actions">' +
			actions +
			"</div>" +
			"</div>"
		);
	}

	function applyActiveJourneys(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host =
			(root && root.querySelector("#kt-ph-active-journeys-host")) ||
			document.getElementById("kt-ph-active-journeys-host");
		if (!host) return;
		const items = (payload && payload.items) || [];
		if (!items.length) {
			host.innerHTML =
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("No active procurement journeys.")) +
				"</p>";
			return;
		}
		let html = "";
		for (let i = 0; i < items.length; i++) {
			html += renderHomeJourneyCard(items[i]);
		}
		host.innerHTML = html;
	}

	function loadActiveJourneys() {
		if (!isHomeWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.list_journeys",
			args: { status: "active", limit: 20 },
			callback: function (r) {
				if (!isHomeWorkspaceRoute()) return;
				const payload = r && r.message;
				if (!payload || !Array.isArray(payload.items)) {
					applyActiveJourneys({ items: [] });
					return;
				}
				applyActiveJourneys(payload);
			},
			error: function () {
				if (!isHomeWorkspaceRoute()) return;
				const root = getVisibleWorkspacesPageRoot();
				const host =
					(root && root.querySelector("#kt-ph-active-journeys-host")) ||
					document.getElementById("kt-ph-active-journeys-host");
				if (!host) return;
				host.innerHTML =
					'<p class="text-muted small mb-0 text-danger">' +
					escapeHtml(__("Unable to load active journeys.")) +
					"</p>";
			},
		});
	}

	function applyNeedsActionJourneys(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host =
			(root && root.querySelector("#kt-ph-needs-action-host")) ||
			document.getElementById("kt-ph-needs-action-host");
		if (!host) return;
		const items = (payload && payload.items) || [];
		if (!items.length) {
			host.innerHTML =
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("No journeys need your action.")) +
				"</p>";
			return;
		}
		let html = "";
		for (let i = 0; i < items.length; i++) {
			html += renderHomeJourneyCard(items[i]);
		}
		host.innerHTML = html;
	}

	function loadNeedsActionJourneys() {
		if (!isHomeWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.list_journeys",
			args: { status: "needs_action", scope: "my-work", limit: 20 },
			callback: function (r) {
				if (!isHomeWorkspaceRoute()) return;
				const payload = r && r.message;
				if (!payload || !Array.isArray(payload.items)) {
					applyNeedsActionJourneys({ items: [] });
					return;
				}
				applyNeedsActionJourneys(payload);
			},
			error: function () {
				if (!isHomeWorkspaceRoute()) return;
				const root = getVisibleWorkspacesPageRoot();
				const host =
					(root && root.querySelector("#kt-ph-needs-action-host")) ||
					document.getElementById("kt-ph-needs-action-host");
				if (!host) return;
				host.innerHTML =
					'<p class="text-muted small mb-0 text-danger">' +
					escapeHtml(__("Unable to load journeys that need your action.")) +
					"</p>";
			},
		});
	}

	function applyBlockedJourneys(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host =
			(root && root.querySelector("#kt-ph-blocked-journeys-host")) ||
			document.getElementById("kt-ph-blocked-journeys-host");
		if (!host) return;
		const items = (payload && payload.items) || [];
		if (!items.length) {
			host.innerHTML =
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("No critical blockers.")) +
				"</p>";
			return;
		}
		let html = "";
		for (let i = 0; i < items.length; i++) {
			html += renderHomeJourneyCard(items[i]);
		}
		host.innerHTML = html;
	}

	function loadBlockedJourneys() {
		if (!isHomeWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.list_journeys",
			args: { status: "blocked", limit: 20 },
			callback: function (r) {
				if (!isHomeWorkspaceRoute()) return;
				const payload = r && r.message;
				if (!payload || !Array.isArray(payload.items)) {
					applyBlockedJourneys({ items: [] });
					return;
				}
				applyBlockedJourneys(payload);
			},
			error: function () {
				if (!isHomeWorkspaceRoute()) return;
				const root = getVisibleWorkspacesPageRoot();
				const host =
					(root && root.querySelector("#kt-ph-blocked-journeys-host")) ||
					document.getElementById("kt-ph-blocked-journeys-host");
				if (!host) return;
				host.innerHTML =
					'<p class="text-muted small mb-0 text-danger">' +
					escapeHtml(__("Unable to load blocked journeys.")) +
					"</p>";
			},
		});
	}

	function applyReadyForHandoffJourneys(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host =
			(root && root.querySelector("#kt-ph-ready-for-handoff-host")) ||
			document.getElementById("kt-ph-ready-for-handoff-host");
		if (!host) return;
		const items = (payload && payload.items) || [];
		if (!items.length) {
			host.innerHTML =
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("No journeys ready for handoff.")) +
				"</p>";
			return;
		}
		let html = "";
		for (let i = 0; i < items.length; i++) {
			html += renderHomeJourneyCard(items[i]);
		}
		host.innerHTML = html;
	}

	function loadReadyForHandoffJourneys() {
		if (!isHomeWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.list_journeys",
			args: { status: "ready_for_handoff", limit: 20 },
			callback: function (r) {
				if (!isHomeWorkspaceRoute()) return;
				const payload = r && r.message;
				if (!payload || !Array.isArray(payload.items)) {
					applyReadyForHandoffJourneys({ items: [] });
					return;
				}
				applyReadyForHandoffJourneys(payload);
			},
			error: function () {
				if (!isHomeWorkspaceRoute()) return;
				const root = getVisibleWorkspacesPageRoot();
				const host =
					(root && root.querySelector("#kt-ph-ready-for-handoff-host")) ||
					document.getElementById("kt-ph-ready-for-handoff-host");
				if (!host) return;
				host.innerHTML =
					'<p class="text-muted small mb-0 text-danger">' +
					escapeHtml(__("Unable to load journeys ready for handoff.")) +
					"</p>";
			},
		});
	}

	function navigateToProcurementJourney(journeyCode, focusEvidence) {
		if (!journeyCode || typeof frappe === "undefined" || !frappe.set_route) return;
		frappe.route_options = {};
		if (focusEvidence) {
			frappe.route_options.plc_focus = "evidence";
		}
		frappe.set_route("plc-procurement-journey", journeyCode);
	}

	function ensureHomeDelegatedClicks() {
		const page = getVisibleWorkspacesPageRoot();
		const root = (page && page.querySelector("#kt-ph-root")) || document.getElementById("kt-ph-root");
		if (!root || root.getAttribute("data-ph-delegated") === "1") return;
		root.setAttribute("data-ph-delegated", "1");
		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;
			const openJourney = t.closest(".plc-home-open-journey");
			if (openJourney) {
				const jc = openJourney.getAttribute("data-journey-code");
				if (jc) navigateToProcurementJourney(jc, false);
				return;
			}
			const viewEvidence = t.closest(".plc-home-view-evidence");
			if (viewEvidence) {
				const jc = viewEvidence.getAttribute("data-journey-code");
				if (jc) navigateToProcurementJourney(jc, true);
				return;
			}
			const openTender = t.closest(".plc-home-open-tender");
			if (openTender) {
				const tc = openTender.getAttribute("data-tender-code");
				if (tc) frappe.set_route("Form", "TM2 Tender", tc);
				return;
			}
		});
	}

	function tryBindHomeWorkspace() {
		if (!isHomeWorkspaceRoute()) {
			removeHomeLandingIfWrongRoute();
			return;
		}
		syncHomeShellClass();
		const inj = injectHomeLandingShell();
		if (inj && inj.ok) {
			loadActiveJourneys();
			loadNeedsActionJourneys();
			loadBlockedJourneys();
			loadReadyForHandoffJourneys();
		}
	}

	function requestHomeBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindHomeWorkspace();
		}, delayMs || 0);
	}

	function scheduleHomeWorkspaceBind() {
		if (!isHomeWorkspaceRoute()) {
			removeHomeLandingIfWrongRoute();
			return;
		}
		syncHomeShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => requestHomeBind(0));
		} else {
			requestHomeBind(0);
		}
		requestHomeBind(120);
		requestHomeBind(450);
		requestHomeBind(950);
	}

	function ensureWorkspaceDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		workspaceDomObserver = new MutationObserver(function () {
			if (!isHomeWorkspaceRoute() || homeShellPresentOnActiveWsPage()) return;
			tryBindHomeWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindHomeWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleHomeWorkspaceBind);
				window.jQuery(document).on("app_ready", scheduleHomeWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleHomeWorkspaceBind);
			}
			ensureWorkspaceDomObserver();
		}
		syncHomeShellClass();
		scheduleHomeWorkspaceBind();
	}

	function ensurePollHomeWorkspace() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isHomeWorkspaceRoute()) removeHomeLandingIfWrongRoute();
			else if (!homeShellPresentOnActiveWsPage()) tryBindHomeWorkspace();
			setTimeout(tick, 400);
		}
		tick();
	}

	function kickHomeWorkspace() {
		bindHomeWorkspaceHooks();
		ensurePollHomeWorkspace();
		setTimeout(scheduleHomeWorkspaceBind, 400);
	}

	function bootstrapHomeWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickHomeWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickHomeWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickHomeWorkspace);
		setTimeout(kickHomeWorkspace, 900);
	}

	bootstrapHomeWorkspace();
})();
