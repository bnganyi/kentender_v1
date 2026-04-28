// Supplier Management workbench (queue-first): header, KPI, filters, list/detail, state actions.
(function () {
	if (typeof frappe === "undefined") {
		return;
	}

	function esc(v) {
		return frappe.utils.escape_html(String(v || ""));
	}

	function doctypeSlug(doctype) {
		return String(doctype || "")
			.toLowerCase()
			.replace(/\s+/g, "-");
	}

	function routeToForm(doctype, name) {
		if (!doctype || !name) return;
		if (window.location.pathname.indexOf("/desk") === 0) {
			window.location.href =
				"/desk/Form/" + encodeURIComponent(doctype) + "/" + encodeURIComponent(name);
			return;
		}
		if (typeof frappe !== "undefined" && typeof frappe.set_route === "function" && window.location.pathname.indexOf("/app") === 0) {
			frappe.set_route("Form", doctype, name);
			return;
		}
		window.location.href = "/app/" + doctypeSlug(doctype) + "/" + encodeURIComponent(name);
	}

	function routeToList(doctype, routeOptions) {
		if (!doctype) return;
		var query = "";
		if (routeOptions && typeof URLSearchParams !== "undefined") {
			query = "?" + new URLSearchParams(routeOptions).toString();
		}
		if (window.location.pathname.indexOf("/desk") === 0) {
			window.location.href =
				"/desk/List/" + encodeURIComponent(doctype) + "/List" + query;
			return;
		}
		window.location.href = "/app/" + doctypeSlug(doctype) + "/view/list" + query;
	}

	var state = {
		landing: null,
		rows: [],
		selectedCode: "",
		selectedDetail: null,
		activeKpi: "all",
		ownershipQueue: "all",
		stateQueue: "",
		query: "",
		secondary: {},
	};

	var KTSM_WS = "KTSM Supplier Registry";
	var bindScheduled = false;
	var hooksBound = false;
	var pollStarted = false;

	function workspaceNameMatchesKtsm(name) {
		if (name == null || name === "") return false;
		if (name === KTSM_WS) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(KTSM_WS);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "ktsm-supplier-registry";
	}

	function isKtsmWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				var r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					var workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesKtsm(workspaceName)) return true;
					if (workspaceName) return false;
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			var route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				var w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesKtsm(w)) return true;
				if (w) return false;
			}
		} catch (e2) {
			/* ignore */
		}
		var loc = window.location;
		var path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
		if (path.includes("ktsm-supplier-registry") || path.includes("ktsm%20supplier%20registry")) {
			return true;
		}
		var dr = (document.body && document.body.getAttribute("data-route")) || "";
		if (dr.indexOf("KTSM Supplier Registry") !== -1 || dr.toLowerCase().indexOf("ktsm-supplier-registry") !== -1) {
			return true;
		}
		return false;
	}

	function syncKtsmShellClass() {
		document.body.classList.toggle("kt-ktsm-shell", isKtsmWorkspaceRoute());
	}

	function getWorkspacesPageRoot() {
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]') ||
			document.querySelector('[data-page-route="Workspaces"]')
		);
	}

	function resolveWorkspaceEditorMount() {
		var root = getWorkspacesPageRoot();
		if (root) {
			var esc = root.querySelector(".layout-main-section .editor-js-container");
			if (!esc) esc = root.querySelector(".editor-js-container");
			if (!esc) {
				var ed = root.querySelector("#editorjs");
				if (ed && ed.parentElement) esc = ed.parentElement;
			}
			if (!esc) {
				var lms = root.querySelector(".layout-main-section");
				if (lms) esc = lms;
			}
			if (esc) return esc;
		}
		var directEsc =
			document.querySelector("#page-Workspaces .editor-js-container") ||
			document.querySelector("#page-Workspaces .layout-main-section");
		if (directEsc) return directEsc;
		var candidates = document.querySelectorAll(".editor-js-container");
		var fallback = null;
		for (var i = 0; i < candidates.length; i++) {
			var el = candidates[i];
			if (!el || !el.isConnected) continue;
			if (!fallback) fallback = el;
			if (el.getClientRects && el.getClientRects().length > 0) return el;
		}
		return fallback;
	}

	function removeKtsmShellIfWrongRoute() {
		var el = document.getElementById("kt-smw-landing");
		if (el && el.classList.contains("ktsm-injected-mount")) {
			el.remove();
		}
		document.body.classList.remove("kt-ktsm-shell");
		bindScheduled = false;
		state.rows = [];
		state.selectedCode = "";
		state.selectedDetail = null;
	}

	function queueBtn(label, value, kind, active) {
		return (
			'<button class="ktsm-queue-btn ' +
			(active ? "is-active" : "") +
			'" data-kind="' +
			esc(kind) +
			'" data-value="' +
			esc(value) +
			'">' +
			esc(label) +
			"</button>"
		);
	}

	function renderBase(data) {
		var k = (data && data.kpis) || {};
		var q = (data && data.queues) || {};
		return (
			'<div class="ktsm-landing" data-testid="ktsm-landing">' +
			'<div class="ktsm-header" data-testid="ktsm-header">' +
			'<div><h2>Supplier Management</h2><p class="text-muted">Review, approve, and manage supplier lifecycle.</p></div>' +
			'<div class="ktsm-header-actions"><button class="btn btn-primary btn-sm" data-action="new-supplier">New Supplier</button></div>' +
			"</div>" +
			'<div class="ktsm-kpi-row" data-testid="ktsm-kpi-row">' +
			'<button class="ktsm-kpi" data-kpi="all" data-testid="ktsm-kpi-registered">Registered<b>' +
			esc(k.registered || 0) +
			"</b></button>" +
			'<button class="ktsm-kpi" data-kpi="pending_review" data-testid="ktsm-kpi-pending">Pending Review<b>' +
			esc(k.pending_review || 0) +
			"</b></button>" +
			'<button class="ktsm-kpi" data-kpi="active" data-testid="ktsm-kpi-active-card">Active<b>' +
			esc(k.active || 0) +
			"</b></button>" +
			'<button class="ktsm-kpi" data-kpi="blocked" data-testid="ktsm-kpi-blocked-card">Blocked<b>' +
			esc(k.blocked || 0) +
			"</b></button>" +
			"</div>" +
			'<div class="ktsm-active-kpi text-muted" data-testid="ktsm-active-kpi">' +
			esc(state.activeKpi) +
			"</div>" +
			'<div class="ktsm-queue-row" data-testid="ktsm-queue-row-ownership">' +
			queueBtn("My Work", "my_work", "ownership", state.ownershipQueue === "my_work") +
			queueBtn("All", "all", "ownership", state.ownershipQueue === "all") +
			queueBtn("Approved", "approved", "ownership", state.ownershipQueue === "approved") +
			queueBtn("Blocked", "blocked", "ownership", state.ownershipQueue === "blocked") +
			"</div>" +
			'<div class="ktsm-queue-row" data-testid="ktsm-queue-row-state">' +
			queueBtn("Draft", "draft", "state", state.stateQueue === "draft") +
			queueBtn("Submitted", "submitted", "state", state.stateQueue === "submitted") +
			queueBtn("Under Review", "under_review", "state", state.stateQueue === "under_review") +
			queueBtn("Returned", "returned", "state", state.stateQueue === "returned") +
			queueBtn("Active", "active", "state", state.stateQueue === "active") +
			queueBtn("Suspended", "suspended", "state", state.stateQueue === "suspended") +
			queueBtn("Blacklisted", "blacklisted", "state", state.stateQueue === "blacklisted") +
			queueBtn("Expired", "expired", "state", state.stateQueue === "expired") +
			"</div>" +
			'<div class="ktsm-search-row"><input data-testid="ktsm-search-input" class="form-control input-xs" placeholder="Search suppliers..." value="' +
			esc(state.query) +
			'"/></div>' +
			'<div class="ktsm-workarea">' +
			'<div class="ktsm-list-panel" data-testid="ktsm-list-panel"></div>' +
			'<div class="ktsm-detail-panel" data-testid="ktsm-detail-panel"><div class="text-muted">Select a supplier.</div></div>' +
			"</div>" +
			'<div class="ktsm-meta text-muted">draft ' +
			esc(q.approval_draft || 0) +
			" · submitted " +
			esc(q.approval_submitted || 0) +
			" · under review " +
			esc(q.approval_in_review || 0) +
			" · returned " +
			esc(q.approval_returned || 0) +
			"</div>" +
			"</div>"
		);
	}

	function supplierCard(r) {
		var active = state.selectedCode === r.supplier_code;
		return (
			'<button class="ktsm-supplier-card ' +
			(active ? "is-selected" : "") +
			'" data-supplier-code="' +
			esc(r.supplier_code) +
			'" data-testid="ktsm-row-' +
			esc(r.supplier_code) +
			'">' +
			'<div class="ktsm-row-name">' +
			esc(r.supplier_name) +
			"</div>" +
			'<div class="ktsm-row-code text-muted">' +
			esc(r.supplier_code) +
			"</div>" +
			'<div class="ktsm-row-badges"><span class="ktsm-badge">' +
			esc(r.approval_status) +
			'</span><span class="ktsm-badge">' +
			esc(r.compliance_status) +
			"</span>" +
			(r.risk_level ? '<span class="ktsm-badge ktsm-risk">' + esc(r.risk_level) + " Risk</span>" : "") +
			"</div>" +
			'<div class="ktsm-row-categories text-muted">' +
			esc((r.categories || []).join(", ") || "No categories") +
			"</div>" +
			"</button>"
		);
	}

	function renderList() {
		var panel = document.querySelector('[data-testid="ktsm-list-panel"]');
		if (!panel) {
			return;
		}
		if (!state.rows.length) {
			panel.innerHTML = '<div class="text-muted">No suppliers match current filters.</div>';
			return;
		}
		panel.innerHTML = state.rows.map(supplierCard).join("");
	}

	function detailSection(title, content) {
		return '<div class="ktsm-detail-section"><h5>' + esc(title) + "</h5>" + content + "</div>";
	}

	function renderDetail(detail) {
		var panel = document.querySelector('[data-testid="ktsm-detail-panel"]');
		if (!panel || !detail) {
			return;
		}
		var actions = (detail.actions || [])
			.map(function (a) {
				return (
					'<button class="btn btn-xs btn-default" data-workflow-action="' +
					esc(a.id) +
					'" ' +
					(a.disabled ? "disabled" : "") +
					">" +
					esc(a.label) +
					"</button>"
				);
			})
			.join("");
		var docs = (detail.sections.documents || [])
			.map(function (d) {
				return (
					"<tr>" +
					"<td>" +
					esc(d.document_type) +
					"</td>" +
					"<td>" +
					esc(d.status) +
					"</td>" +
					"<td>" +
					esc(d.expiry || "-") +
					"</td>" +
					"<td>" +
					esc(d.verified_by || "-") +
					"</td>" +
					"</tr>"
				);
			})
			.join("");
		var cats = (detail.sections.categories || [])
			.map(function (c) {
				return "<li>" + esc(c.category) + " - " + esc(c.qualification_status) + "</li>";
			})
			.join("");
		var history = (detail.sections.activity_log || [])
			.map(function (h) {
				return "<li>" + esc(h.status_type) + ": " + esc(h.previous_status) + " -> " + esc(h.new_status) + "</li>";
			})
			.join("");
		panel.innerHTML =
			'<div class="ktsm-detail-head">' +
			"<h4>" +
			esc(detail.supplier_name) +
			"</h4>" +
			'<div class="text-muted">' +
			esc(detail.supplier_code) +
			"</div>" +
			'<div class="ktsm-row-badges"><span class="ktsm-badge">' +
			esc(detail.approval_status) +
			'</span><span class="ktsm-badge">' +
			esc(detail.compliance_status) +
			"</span>" +
			(detail.risk_level ? '<span class="ktsm-badge ktsm-risk">' + esc(detail.risk_level) + " Risk</span>" : "") +
			"</div>" +
			"</div>" +
			'<div class="ktsm-detail-links">' +
			'<button class="btn btn-xs btn-default" data-nav-action="open-profile" data-testid="ktsm-open-profile">Open Full Profile</button>' +
			'<button class="btn btn-xs btn-default" data-nav-action="open-documents" data-testid="ktsm-open-documents">Open Documents Register</button>' +
			"</div>" +
			'<div class="ktsm-action-bar" data-testid="ktsm-action-bar">' +
			actions +
			"</div>" +
			detailSection(
				"Supplier Profile",
				"<ul><li>ERPNext: " +
					esc(detail.sections.profile.erpnext_supplier) +
					"</li><li>Contact: " +
					esc(detail.sections.profile.contact_info) +
					"</li></ul>"
			).replace('<div class="ktsm-detail-section">', '<div class="ktsm-detail-section" data-testid="ktsm-detail-profile">') +
			detailSection(
				"Documents",
				'<div class="text-muted ktsm-doc-hint" data-testid="ktsm-doc-hint">Captured under DocType: KTSM Supplier Document</div>' +
				'<table class="ktsm-doc-table" data-testid="ktsm-documents-table"><thead><tr><th>Document Type</th><th>Status</th><th>Expiry</th><th>Verified By</th></tr></thead><tbody>' +
					(docs || "<tr><td colspan='4'>None</td></tr>") +
					"</tbody></table>"
			).replace(
				'<div class="ktsm-detail-section">',
				'<div class="ktsm-detail-section" id="ktsm-detail-documents-anchor" data-testid="ktsm-detail-documents">'
			) +
			detailSection("Category Qualification", "<ul>" + (cats || "<li>None</li>") + "</ul>").replace(
				'<div class="ktsm-detail-section">',
				'<div class="ktsm-detail-section" data-testid="ktsm-detail-category">'
			) +
			detailSection(
				"Compliance Status",
				"<ul><li>Overall: " +
					esc(detail.sections.compliance.overall_status) +
					"</li><li>Missing: " +
					esc((detail.sections.compliance.missing_documents || []).join(", ") || "None") +
					"</li></ul>"
			).replace('<div class="ktsm-detail-section">', '<div class="ktsm-detail-section" data-testid="ktsm-detail-compliance">') +
			detailSection("Risk Profile", "<div>" + esc(detail.sections.risk.risk_level || "N/A") + "</div>").replace(
				'<div class="ktsm-detail-section">',
				'<div class="ktsm-detail-section" data-testid="ktsm-detail-risk">'
			) +
			detailSection("Activity Log", "<ul>" + (history || "<li>No activity</li>") + "</ul>").replace(
				'<div class="ktsm-detail-section">',
				'<div class="ktsm-detail-section" data-testid="ktsm-detail-history">'
			);
	}

	function currentFilters() {
		return {
			kpi: state.activeKpi,
			ownership_queue: state.ownershipQueue,
			state_queue: state.stateQueue,
			q: state.query,
		};
	}

	function loadSuppliers() {
		frappe.call({
			method: "kentender_suppliers.api.ktsm_landing.get_suppliers",
			args: { filters: currentFilters() },
			callback: function (r) {
				state.rows = (r.message && r.message.rows) || [];
				if (state.selectedCode && !state.rows.some(function (x) { return x.supplier_code === state.selectedCode; })) {
					state.selectedCode = "";
				}
				renderList();
				if (state.selectedCode) {
					loadDetail(state.selectedCode);
				}
			},
		});
	}

	function loadDetail(code) {
		if (!code) {
			return;
		}
		frappe.call({
			method: "kentender_suppliers.api.ktsm_landing.get_supplier_detail",
			args: { supplier_code: code },
			callback: function (r) {
				var msg = r.message || {};
				if (!msg.ok || !msg.detail) {
					return;
				}
				state.selectedDetail = msg.detail;
				renderDetail(msg.detail);
			},
		});
	}

	function performAction(action, code) {
		if (!action || !code) {
			return;
		}
		var needsReason = action === "return" || action === "reject" || action === "suspend" || action === "blacklist" || action === "reactivate";
		var run = function (reason) {
			frappe.call({
				method: "kentender_suppliers.api.ktsm_landing.perform_action",
				args: {
					action: action,
					supplier_code: code,
					reason: reason || "",
				},
				callback: function () {
					loadSuppliers();
				},
			});
		};
		if (!needsReason) {
			run("");
			return;
		}
		frappe.prompt(
			[{ fieldname: "reason", fieldtype: "Small Text", reqd: 1, label: "Reason" }],
			function (v) {
				run(v.reason);
			},
			"Reason Required",
			"Submit"
		);
	}

	function wireSearchInput(root) {
		var input = root.querySelector('[data-testid="ktsm-search-input"]');
		if (!input) return;
		input.addEventListener(
			"input",
			frappe.utils.debounce(function (ev) {
				state.query = (ev.target.value || "").trim();
				loadSuppliers();
			}, 250)
		);
	}

	function onWorkbenchRootClick(ev) {
		var root = ev.currentTarget;
		if (!root || !root.id || root.id !== "kt-smw-landing") return;
		var kpi = ev.target.closest("[data-kpi]");
		if (kpi) {
			state.activeKpi = kpi.getAttribute("data-kpi") || "all";
			var activeEl = root.querySelector('[data-testid="ktsm-active-kpi"]');
			if (activeEl) activeEl.textContent = state.activeKpi;
			loadSuppliers();
			return;
		}
		var qbtn = ev.target.closest(".ktsm-queue-btn");
		if (qbtn) {
			var kind = qbtn.getAttribute("data-kind");
			var value = qbtn.getAttribute("data-value");
			if (kind === "ownership") {
				state.ownershipQueue = value || "all";
			} else if (kind === "state") {
				state.stateQueue = state.stateQueue === value ? "" : value;
			}
			root.innerHTML = renderBase(state.landing);
			wireSearchInput(root);
			renderList();
			loadSuppliers();
			return;
		}
		var row = ev.target.closest("[data-supplier-code]");
		if (row) {
			state.selectedCode = row.getAttribute("data-supplier-code") || "";
			renderList();
			loadDetail(state.selectedCode);
			return;
		}
		var act = ev.target.closest("[data-workflow-action]");
		if (act) {
			performAction(act.getAttribute("data-workflow-action"), state.selectedCode);
			return;
		}
		var navAction = ev.target.closest("[data-nav-action]");
		if (navAction) {
			var type = navAction.getAttribute("data-nav-action");
			if (type === "open-profile") {
				var pname = state.selectedDetail && state.selectedDetail.profile_name;
				routeToForm("KTSM Supplier Profile", pname);
			} else if (type === "open-documents") {
				var profileName = state.selectedDetail && state.selectedDetail.profile_name;
				routeToList("KTSM Supplier Document", profileName ? { supplier_profile: profileName } : null);
			}
			return;
		}
		var headerAction = ev.target.closest("[data-action='new-supplier']");
		if (headerAction) {
			frappe.prompt(
				[
					{ fieldname: "supplier_name", fieldtype: "Data", label: "Supplier Name", reqd: 1 },
					{
						fieldname: "supplier_type",
						fieldtype: "Select",
						label: "Supplier Type",
						options: "Company\nIndividual",
						default: "Company",
					},
				],
				function (v) {
					frappe.call({
						method: "kentender_suppliers.api.ktsm_landing.create_supplier_builder_profile",
						args: {
							supplier_name: v.supplier_name,
							supplier_type: v.supplier_type,
						},
						callback: function (r) {
							var msg = r.message || {};
							if (!msg.ok || !msg.profile_name) {
								frappe.msgprint({
									title: __("Could not create supplier"),
									message: (msg.error && String(msg.error)) || __("Unexpected response."),
									indicator: "orange",
								});
								return;
							}
							routeToForm("KTSM Supplier Profile", msg.profile_name);
						},
						error: function (xhr) {
							var msg = __("Request failed.");
							try {
								var j = xhr && xhr.responseJSON;
								if (j && j.message) msg = String(j.message);
								else if (j && j.exc) msg = String(j.exc);
							} catch (e) {
								/* ignore */
							}
							frappe.msgprint({
								title: __("Could not create supplier"),
								message: msg,
								indicator: "red",
							});
						},
					});
				},
				"Create Supplier",
				"Create"
			);
		}
	}

	function bindEvents(root) {
		if (!root.dataset.ktsmRootClickBound) {
			root.dataset.ktsmRootClickBound = "1";
			root.addEventListener("click", onWorkbenchRootClick);
		}
		wireSearchInput(root);
	}

	function loadLandingIntoRoot(root) {
		if (!root) return;
		frappe.call({
			method: "kentender_suppliers.api.ktsm_landing.get_landing",
			callback: function (r) {
				if (!isKtsmWorkspaceRoute()) return;
				if (!root || !root.isConnected) return;
				if (!r.message || !r.message.ok) {
					return;
				}
				state.landing = r.message;
				root.innerHTML = renderBase(r.message);
				bindEvents(root);
				loadSuppliers();
			},
		});
	}

	function tryBindKtsmWorkspace() {
		if (!isKtsmWorkspaceRoute()) {
			removeKtsmShellIfWrongRoute();
			return;
		}
		syncKtsmShellClass();
		var root = document.getElementById("kt-smw-landing");
		if (!root) {
			var esc = resolveWorkspaceEditorMount();
			if (!esc) return;
			root = document.createElement("div");
			root.id = "kt-smw-landing";
			root.className = "ktsm-workbench-root ktsm-injected-mount";
			root.setAttribute("data-testid", "ktsm-workbench-root");
			var ed = document.getElementById("editorjs");
			if (ed && esc.contains(ed)) esc.insertBefore(root, ed);
			else esc.insertBefore(root, esc.firstChild);
		}
		if (root.querySelector('[data-testid="ktsm-header"]')) {
			return;
		}
		loadLandingIntoRoot(root);
	}

	function requestKtsmBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindKtsmWorkspace();
		}, delayMs || 0);
	}

	function scheduleKtsmWorkspaceBind() {
		if (!isKtsmWorkspaceRoute()) {
			removeKtsmShellIfWrongRoute();
			return;
		}
		syncKtsmShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(function () {
				requestKtsmBind(0);
			});
		} else {
			requestKtsmBind(0);
		}
		requestKtsmBind(120);
	}

	function bindKtsmWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", scheduleKtsmWorkspaceBind);
				window.jQuery(document).on("app_ready", scheduleKtsmWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", scheduleKtsmWorkspaceBind);
			}
		}
		syncKtsmShellClass();
		scheduleKtsmWorkspaceBind();
	}

	function ensurePollKtsmWorkspace() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isKtsmWorkspaceRoute()) removeKtsmShellIfWrongRoute();
			else if (
				!document.getElementById("kt-smw-landing") ||
				!document.querySelector("#kt-smw-landing [data-testid=\"ktsm-header\"]")
			) {
				tryBindKtsmWorkspace();
			}
			setTimeout(tick, 400);
		}
		tick();
	}

	function kickKtsmWorkspace() {
		bindKtsmWorkspaceHooks();
		ensurePollKtsmWorkspace();
		setTimeout(scheduleKtsmWorkspaceBind, 400);
	}

	function bootstrapKtsmWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickKtsmWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickKtsmWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickKtsmWorkspace);
		setTimeout(kickKtsmWorkspace, 900);
	}

	bootstrapKtsmWorkspace();
})();
