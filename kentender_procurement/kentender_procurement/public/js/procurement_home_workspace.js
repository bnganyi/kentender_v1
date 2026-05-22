// Procurement Home workbench — Desk shell (IA v1.0 §5.1).

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
		/* Do not use global getElementById — a hidden #page-Workspaces can retain a shell and block the visible page. */
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
			'<div class="kt-ph-workspace-header kt-ph-workspace-header--compact mb-2">' +
			'<div class="kt-ph-header-row">' +
			"<div>" +
			'<h2 class="kt-ph-page-title h5 mb-1" data-testid="ph-page-title">' +
			escapeHtml(__("Procurement Home")) +
			"</h2>" +
			'<p class="kt-ph-page-intro text-muted small mb-0">' +
			escapeHtml(
				__(
					"Role-aware entry point: demand intake, planning, and settings — without raw configuration clutter in the main rail."
				)
			) +
			"</p>" +
			"</div>" +
			"</div>" +
			'<div id="kt-ph-hints" class="small text-muted mb-1"></div>' +
			'<div class="mb-1"><div class="row g-2 align-items-stretch" id="kt-ph-kpi-host"></div>' +
			'<p class="kt-ph-kpi-currency-note text-muted" id="kt-ph-kpi-currency-note" data-testid="ph-kpi-currency-context" hidden></p></div>' +
			'<div class="kt-ph-section kt-surface kt-ph-actions">' +
			'<div class="fw-bold small text-muted text-uppercase mb-1">' +
			escapeHtml(__("Quick links")) +
			"</div>" +
			'<button type="button" class="btn btn-primary btn-sm" data-ph-action="new-demand">' +
			escapeHtml(__("New Demand")) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm" data-ph-action="open-dia">' +
			escapeHtml(__("Open Demand Intake & Approval")) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm" data-ph-action="open-pp">' +
			escapeHtml(__("Open Procurement Planning")) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm" data-ph-action="open-pending">' +
			escapeHtml(__("Open Pending Approvals")) +
			"</button>" +
			"</div>" +
			"</div>";

		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) esc.insertBefore(wrap, ed);
		else esc.insertBefore(wrap, esc.firstChild);

		ensureHomeDelegatedClicks();
		return { ok: true, inserted: true };
	}

	function formatKpiValue(row, _fallbackCurrency) {
		const fmt = row.format || "int";
		const v = Number(row.value) || 0;
		if (fmt === "currency") {
			const n = Math.round(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
			return escapeHtml(n);
		}
		return escapeHtml(String(Math.round(v)));
	}

	function applyKpis(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host = (root && root.querySelector("#kt-ph-kpi-host")) || document.getElementById("kt-ph-kpi-host");
		if (!host) return;
		const curNote = document.getElementById("kt-ph-kpi-currency-note");
		const cur = (payload && payload.currency) || "KES";
		const kpis = (payload && payload.kpis) || [];
		if (curNote) {
			const hasCurrency = kpis.some(function (k) {
				return k && (k.format || "int") === "currency";
			});
			if (hasCurrency) {
				curNote.textContent = __("All monetary figures in {0}").replace("{0}", cur);
				curNote.hidden = false;
			} else {
				curNote.textContent = "";
				curNote.hidden = true;
			}
		}
		if (!kpis.length) {
			if (curNote) {
				curNote.textContent = "";
				curNote.hidden = true;
			}
			host.innerHTML =
				'<div class="col-12"><p class="text-muted small mb-0">' +
				escapeHtml(
					__(
						"No summary metrics yet — open Demand Intake or Procurement Planning when you have access."
					)
				) +
				"</p></div>";
			return;
		}
		let html = "";
		for (let i = 0; i < kpis.length; i++) {
			const k = kpis[i];
			const tid = k.testid || "ph-kpi-" + (k.id || i);
			html +=
				'<div class="col-6 col-md-3">' +
				'<div class="kt-ph-kpi-card kt-ph-kpi-card--static kt-surface" data-testid="' +
				escapeHtml(tid) +
				'">' +
				'<div class="kt-ph-kpi-label">' +
				escapeHtml(k.label || "") +
				"</div>" +
				'<div class="kt-ph-kpi-value">' +
				formatKpiValue(k, cur) +
				"</div></div></div>";
		}
		host.innerHTML = html;
	}

	function applyHints(payload) {
		const root = getVisibleWorkspacesPageRoot();
		const host = (root && root.querySelector("#kt-ph-hints")) || document.getElementById("kt-ph-hints");
		if (!host) return;
		const parts = [];
		if (payload && !payload.dia_ok && payload.dia_message) {
			parts.push("<span>" + escapeHtml(String(payload.dia_message)) + "</span>");
		}
		if (payload && !payload.pp_ok && payload.pp_message) {
			parts.push("<span>" + escapeHtml(String(payload.pp_message)) + "</span>");
		}
		host.innerHTML = parts.join(" · ");
	}

	function navigateToWorkspace(wsName) {
		if (!wsName || typeof frappe === "undefined" || !frappe.set_route) return;
		frappe.set_route("Workspaces", wsName);
	}

	function ensureHomeDelegatedClicks() {
		const page = getVisibleWorkspacesPageRoot();
		const root = (page && page.querySelector("#kt-ph-root")) || document.getElementById("kt-ph-root");
		if (!root || root.getAttribute("data-ph-delegated") === "1") return;
		root.setAttribute("data-ph-delegated", "1");
		root.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) return;
			const btn = t.closest("[data-ph-action]");
			if (!btn) return;
			const act = btn.getAttribute("data-ph-action");
			if (act === "new-demand") {
				frappe.new_doc("Demand");
			} else if (act === "open-dia") {
				navigateToWorkspace("Demand Intake and Approval");
			} else if (act === "open-pp") {
				navigateToWorkspace("Procurement Planning");
			} else if (act === "open-pending") {
				navigateToWorkspace("Demand Intake and Approval");
			}
		});
	}

	function loadHomeLandingData() {
		if (!isHomeWorkspaceRoute()) return;
		frappe.call({
			method: "kentender_procurement.procurement_home.api.landing.get_procurement_home_landing_data",
			callback: function (r) {
				if (!isHomeWorkspaceRoute()) return;
				const payload = r && r.message;
				if (!payload || !payload.ok) {
					applyKpis({ kpis: [] });
					return;
				}
				applyHints(payload);
				applyKpis(payload);
			},
			error: function () {
				if (!isHomeWorkspaceRoute()) return;
				applyKpis({ kpis: [] });
			},
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
			loadHomeLandingData();
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
