/* ── Tender Configuration Home — Screen 02 (native screen module) ─────────── */
(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.screens.configuration_home");

	var api = kentender.it_wizard.api;
	var routes = kentender.it_wizard.routes;
	var components = kentender.it_wizard.components;
	var shell = kentender.it_wizard.shell;

	var SCREEN_SHELL = "it-wizard-overview-shell";
	var DRAWER_PORTAL_ID = "kt-itw-home-drawer-portal";

	var _state = {
		wrapper: null,
		drawerPortal: null,
		loading: false,
		configurationId: "",
		summary: null,
		steps: [],
		drawerOpen: false,
		drawerStepCode: "",
	};

	function _q(sel) {
		return _state.wrapper ? _state.wrapper.querySelector(sel) : null;
	}

	function _drawerQ(sel) {
		return _state.drawerPortal ? _state.drawerPortal.querySelector(sel) : null;
	}

	function _contextFields(data) {
		data = data || {};
		var blockers = data.blocker_count || 0;
		var warnings = data.warning_count || 0;
		var issuesTone = blockers ? "danger" : warnings ? "warn" : undefined;
		return [
			{ label: "TENDER REF", value: data.tender_ref || data.configuration_id, mono: true },
			{ label: "TENDER TITLE", value: data.tender_title || data.title },
			{ label: "PLANNING PKG REF", value: data.planning_package_ref, mono: true },
			{ label: "PROCURING ENTITY", value: data.procuring_entity_name },
			{ label: "PROCUREMENT METHOD", value: data.procurement_method_label },
			{
				label: "WIZARD STATE",
				value: data.wizard_state_label || data.state_label,
				tone: "state",
			},
			{
				label: "ISSUES",
				value: data.issues_summary || __("No issues"),
				tone: issuesTone,
			},
		];
	}

	function _stepProgressPercent(step, summary) {
		var status = step.status_label || "";
		if (status === "Complete") {
			return 100;
		}
		if (status === "Not started" || status === "Available later") {
			return 0;
		}
		if (summary && summary.completion_percent != null) {
			return summary.completion_percent;
		}
		return 0;
	}

	function _formatLastUpdated(value) {
		if (!value) {
			return "";
		}
		if (frappe.datetime && frappe.datetime.str_to_user) {
			return frappe.datetime.str_to_user(value);
		}
		return String(value).replace("T", " ").slice(0, 16);
	}

	function _drawerRouteLabel(step) {
		var action = step.action_label || "";
		if (action === "Continue" || action === "Start") {
			return __("Continue Configuration");
		}
		if (action === "Review") {
			return __("Review");
		}
		return action || __("Continue Configuration");
	}

	function _shellHtml() {
		var user = (frappe.session && (frappe.session.user_fullname || frappe.session.user)) || "User";
		return (
			'<div class="kt-itw-root" data-testid="it-wizard-overview" data-itw-native-loaded="0">' +
			components.appbar({ user: user, title: "IT Tender Configurations" }) +
			'<main class="kt-itw-canvas kt-itw-canvas--home">' +
			components.page_header({
				title: "Tender Configuration Home",
				subtitle: "Complete the required setup steps for this IT tender configuration.",
				actions: [
					{ label: "Discard", variant: "ghost", stub: true },
					{ label: "Finalize Configuration", variant: "primary", stub: true },
				],
			}) +
			'<div data-itw-home-loading="1" class="kt-itw-loading">' +
			components.escape_html(__("Loading configuration summary…")) +
			"</div>" +
			'<div data-itw-home-content="1" class="kt-itw-home-stack" hidden>' +
			components.context_strip([]) +
			components.hero_panel({}) +
			'<section class="kt-itw-steps-section">' +
			'<h3 class="kt-itw-section-title">Configuration Steps</h3>' +
			components.step_grid([]) +
			"</section></div></main></div>"
		);
	}

	function _drawerPortalHtml() {
		return (
			'<div class="kt-itw-drawer-backdrop kt-itw-drawer-backdrop--home" data-itw-home-drawer-overlay="1"></div>' +
			'<aside class="kt-itw-drawer-panel--home" data-itw-home-drawer="1" data-testid="it-wizard-overview-drawer">' +
			'<div class="kt-itw-drawer-head">' +
			'<div>' +
			'<p class="kt-itw-step-num" data-itw-drawer-step-num="1"></p>' +
			'<h2 class="kt-itw-drawer-title" data-itw-drawer-title="1"></h2>' +
			"</div>" +
			'<button type="button" class="kt-itw-icon-btn kt-itw-icon-btn--round" data-itw-drawer-close="1" aria-label="Close">' +
			components.icon("close") +
			"</button>" +
			"</div>" +
			'<div class="kt-itw-drawer-body" data-itw-drawer-body="1"></div>' +
			'<div class="kt-itw-drawer-foot">' +
			'<button type="button" class="kt-itw-btn kt-itw-btn--primary" data-itw-drawer-route="1">' +
			components.escape_html(__("Continue Configuration")) +
			"</button>" +
			'<button type="button" class="kt-itw-btn kt-itw-btn--outline" data-itw-drawer-fix="1" hidden>' +
			components.escape_html(__("Fix Issues")) +
			"</button>" +
			"</div>" +
			"</aside>"
		);
	}

	function _ensureDrawerPortal() {
		var existing = document.getElementById(DRAWER_PORTAL_ID);
		if (existing) {
			existing.parentNode.removeChild(existing);
		}
		var portal = document.createElement("div");
		portal.id = DRAWER_PORTAL_ID;
		portal.className = "kt-itw-home-drawer-portal";
		portal.hidden = true;
		portal.setAttribute("data-itw-home-drawer-open", "0");
		portal.innerHTML = _drawerPortalHtml();
		document.body.appendChild(portal);
		_state.drawerPortal = portal;
	}

	function _teardownDrawerPortal() {
		_closeDrawer();
		if (_state.drawerPortal && _state.drawerPortal.parentNode) {
			_state.drawerPortal.parentNode.removeChild(_state.drawerPortal);
		}
		_state.drawerPortal = null;
	}

	function _syncDrawerSelection() {
		if (!_state.wrapper) {
			return;
		}
		_state.wrapper.querySelectorAll("[data-itw-step-card]").forEach(function (card) {
			var code = card.getAttribute("data-itw-step-code") || "";
			var selected = _state.drawerOpen && code === _state.drawerStepCode;
			card.classList.toggle("kt-itw-step-card--drawer-open", selected);
		});
	}

	function _hydrateDrawer(step) {
		if (!step) {
			return;
		}
		var stepNum = String(step.step_number || 0).padStart(2, "0");
		var stepNumNode = _drawerQ("[data-itw-drawer-step-num]");
		if (stepNumNode) {
			stepNumNode.textContent = "STEP " + stepNum;
		}
		var titleNode = _drawerQ("[data-itw-drawer-title]");
		if (titleNode) {
			titleNode.textContent = step.step_label || "";
		}
		var body = _drawerQ("[data-itw-drawer-body]");
		if (body) {
			var issueText = components.format_issue_line(step);
			var progress = _stepProgressPercent(step, _state.summary || {});
			var lastUpdated = _formatLastUpdated(step.last_updated_at);
			body.innerHTML =
				'<div class="kt-itw-drawer-meta">' +
				'<div class="kt-itw-drawer-meta-row"><span class="kt-itw-context-label">Status</span>' +
				components.status_chip(step.status_label || "Not started", { pill: true }) +
				"</div>" +
				'<div class="kt-itw-drawer-meta-row"><span class="kt-itw-context-label">Issues</span>' +
				'<span class="kt-itw-drawer-issues' +
				(issueText ? "" : " kt-itw-drawer-issues--none") +
				'">' +
				(issueText
					? components.icon("error", "kt-itw-ico--sm") + " " + components.escape_html(issueText)
					: components.escape_html(__("None"))) +
				"</span></div></div>" +
				(step.drawer_purpose
					? '<div class="kt-itw-drawer-block"><h4 class="kt-itw-drawer-block-title">Purpose</h4><p class="kt-itw-drawer-block-text">' +
						components.escape_html(step.drawer_purpose) +
						"</p></div>"
					: "") +
				(step.configure_there && step.configure_there.length
					? '<div class="kt-itw-drawer-block"><h4 class="kt-itw-drawer-block-title">What is configured</h4><ul class="kt-itw-drawer-list">' +
						step.configure_there
							.map(function (item) {
								return "<li>" + components.escape_html(item) + "</li>";
							})
							.join("") +
						"</ul></div>"
					: "") +
				'<div class="kt-itw-drawer-meta-section">' +
				(lastUpdated
					? '<div class="kt-itw-drawer-meta-row"><span class="kt-itw-context-label">Last Updated</span>' +
						'<span class="kt-itw-mono">' +
						components.escape_html(lastUpdated) +
						"</span></div>"
					: "") +
				'<div class="kt-itw-drawer-meta-row"><span class="kt-itw-context-label">Progress</span>' +
				'<div class="kt-itw-drawer-progress">' +
				'<div class="kt-itw-drawer-progress-track"><div class="kt-itw-drawer-progress-fill" style="width:' +
				String(progress) +
				'%"></div></div>' +
				'<span class="kt-itw-drawer-progress-value">' +
				String(progress) +
				"%</span></div></div></div>";
		}
		var routeBtn = _drawerQ("[data-itw-drawer-route]");
		if (routeBtn) {
			routeBtn.textContent = _drawerRouteLabel(step);
			routeBtn.setAttribute("data-itw-drawer-route", step.route || "");
		}
		var fixBtn = _drawerQ("[data-itw-drawer-fix]");
		if (fixBtn) {
			var hasIssues = (step.blocker_count || 0) + (step.warning_count || 0) > 0;
			fixBtn.hidden = !hasIssues;
			fixBtn.setAttribute("data-itw-drawer-fix-route", step.route || "");
		}
	}

	function _openDrawer(step) {
		if (!step || !_state.drawerPortal) {
			return;
		}
		_state.drawerStepCode = step.step_code || "";
		_hydrateDrawer(step);
		_state.drawerPortal.removeAttribute("hidden");
		_state.drawerPortal.setAttribute("data-itw-home-drawer-open", "1");
		document.body.classList.add("kt-itw-home-drawer-open");
		_state.drawerOpen = true;
		_syncDrawerSelection();
	}

	function _closeDrawer() {
		if (_state.drawerPortal) {
			_state.drawerPortal.setAttribute("data-itw-home-drawer-open", "0");
			_state.drawerPortal.setAttribute("hidden", "hidden");
		}
		document.body.classList.remove("kt-itw-home-drawer-open");
		_state.drawerOpen = false;
		_state.drawerStepCode = "";
		_syncDrawerSelection();
	}

	function _stepByCode() {
		var map = {};
		(_state.steps || []).forEach(function (step) {
			map[step.step_code] = step;
		});
		return map;
	}

	function _paintSummary(data) {
		data = data || {};
		var contextHost = _q("[data-itw-home-context]");
		if (contextHost) {
			contextHost.outerHTML = components.context_strip(_contextFields(data));
		}
		var heroHost = _q("[data-itw-next-action]");
		if (heroHost) {
			heroHost.outerHTML = components.hero_panel(data.next_action || {});
		}
		var gridHost = _q("[data-itw-step-grid]");
		if (gridHost) {
			gridHost.outerHTML = components.step_grid(data.steps || []);
		}
		_state.steps = data.steps || [];
		_syncDrawerSelection();
		var root = _q('[data-testid="it-wizard-overview"]');
		if (root) {
			root.setAttribute("data-itw-native-loaded", "1");
		}
	}

	function _fetchSummary() {
		_state.loading = true;
		var loading = _q("[data-itw-home-loading]");
		var content = _q("[data-itw-home-content]");
		if (loading) {
			loading.hidden = false;
		}
		if (content) {
			content.hidden = true;
		}
		return api
			.call("get_configuration_summary_api", { configuration_id: _state.configurationId })
			.then(function (result) {
				var data = (result && result.message && result.message.data) || {};
				_state.summary = data;
				_state.steps = data.steps || [];
				_paintSummary(data);
				if (loading) {
					loading.hidden = true;
				}
				if (content) {
					content.hidden = false;
				}
				_state.loading = false;
			})
			.catch(function (err) {
				_state.loading = false;
				frappe.show_alert({
					indicator: "red",
					message: (err && err.message) || __("Unable to load configuration overview."),
				});
			});
	}

	function _requireConfigurationId() {
		var ctx = routes.read_route_context();
		var configurationId = ctx.configuration_id;
		if (!configurationId) {
			frappe.show_alert({
				message: __("Open a tender configuration from the dashboard to view this screen."),
				indicator: "orange",
			});
			routes.navigate(routes.ROUTES.DASHBOARD);
			return "";
		}
		return configurationId;
	}

	function _handleDrawerInteraction(target) {
		if (target.closest("[data-itw-home-drawer-overlay]") || target.closest("[data-itw-drawer-close]")) {
			_closeDrawer();
			return true;
		}
		var drawerBtn = target.closest("[data-itw-drawer-route]");
		if (drawerBtn) {
			var drawerRoute = drawerBtn.getAttribute("data-itw-drawer-route");
			if (drawerRoute) {
				routes.navigate(drawerRoute, { configuration_id: _state.configurationId });
			}
			return true;
		}
		var fixBtn = target.closest("[data-itw-drawer-fix]");
		if (fixBtn && !fixBtn.hidden) {
			var fixRoute = fixBtn.getAttribute("data-itw-drawer-fix-route");
			if (fixRoute) {
				routes.navigate(fixRoute, { configuration_id: _state.configurationId });
			}
			return true;
		}
		return false;
	}

	function _bind() {
		var root = _q('[data-testid="it-wizard-overview"]');
		if (!root) {
			return;
		}
		if (_state.drawerPortal) {
			_state.drawerPortal.onclick = function (event) {
				if (_handleDrawerInteraction(event.target)) {
					event.preventDefault();
				}
			};
		}
		root.onclick = function (event) {
			var target = event.target;
			if (target.closest("[data-itw-back]")) {
				event.preventDefault();
				_teardownDrawerPortal();
				routes.go_back_to_desk();
				return;
			}
			var nextBtn = target.closest("[data-itw-next-action] button, [data-itw-next-action-route]");
			if (nextBtn) {
				event.preventDefault();
				var route = nextBtn.getAttribute("data-itw-next-action-route");
				if (route) {
					routes.navigate(route, { configuration_id: _state.configurationId });
				}
				return;
			}
			var actionBtn = target.closest("[data-itw-step-action]");
			var card = target.closest("[data-itw-step-card]");
			if (actionBtn && card) {
				event.preventDefault();
				event.stopPropagation();
				var stepRoute = card.getAttribute("data-itw-step-route");
				if (stepRoute) {
					routes.navigate(stepRoute, { configuration_id: _state.configurationId });
				}
				return;
			}
			if (card) {
				event.preventDefault();
				var code = card.getAttribute("data-itw-step-code");
				var stepMap = _stepByCode();
				if (code && stepMap[code]) {
					if (_state.drawerOpen && _state.drawerStepCode === code) {
						_closeDrawer();
					} else {
						_openDrawer(stepMap[code]);
					}
				}
			}
		};
	}

	function render(wrapper) {
		_state.wrapper = wrapper;
		_closeDrawer();
		_ensureDrawerPortal();
		shell.mount_wrapper(wrapper, _shellHtml());
		_bind();
		if (!_state._keyHandler) {
			_state._keyHandler = function (event) {
				if (event.key === "Escape" && _state.drawerOpen) {
					event.preventDefault();
					_closeDrawer();
				}
			};
			document.addEventListener("keydown", _state._keyHandler);
		}
	}

	function show(wrapper) {
		shell.show({ screen_shell_class: SCREEN_SHELL });
		_state.drawerOpen = false;
		_state.drawerStepCode = "";
		_state.configurationId = _requireConfigurationId();
		if (!_state.configurationId) {
			return Promise.resolve();
		}
		render(wrapper);
		return _fetchSummary();
	}

	kentender.it_wizard.screens.configuration_home = {
		init: function (wrapper) {
			_state.wrapper = wrapper;
			shell.show({ screen_shell_class: SCREEN_SHELL });
		},
		show: show,
		teardown: _teardownDrawerPortal,
	};
})();
