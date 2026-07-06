/* global frappe */
// STD-CFG-0230 — Configurator shell (mockup-faithful chrome from 2. overview/code.html).
frappe.provide("kentender_procurement.std_configurator_shell");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const cfgApi = kentender_procurement.std_configurator_api;
	const ui = kentender_procurement.std_configurator_ui;
	const shell = kentender_procurement.std_configurator_shell;

	shell.CONFIGURATOR_TABS = Object.freeze([
		{ slug: "overview", label: __("Overview"), tabLabel: __("Overview"), section: "metadata" },
		{ slug: "applicability", label: __("Applicability"), tabLabel: __("Applicability"), section: "applicability" },
		{ slug: "tender-fields", label: __("Tender Fields"), tabLabel: __("Tender Fields"), section: "tender_fields" },
		{
			slug: "supplier-requirements",
			label: __("Supplier Requirements"),
			tabLabel: __("Supplier Req"),
			section: "supplier_requirements",
		},
		{
			slug: "forms-attachments",
			label: __("Forms & Attachments"),
			tabLabel: __("Forms & Attachments"),
			section: "forms_and_attachments",
		},
		{ slug: "evaluation-setup", label: __("Evaluation Setup"), tabLabel: __("Evaluation Setup"), section: "evaluation_setup" },
		{ slug: "contract-terms", label: __("Contract Terms"), tabLabel: __("Contract Terms"), section: "contract_terms" },
		{
			slug: "rules-validations",
			label: __("Rules & Validations"),
			tabLabel: __("Rules & Validations"),
			sections: ["rules", "validations"],
		},
		{ slug: "preview", label: __("Preview"), tabLabel: __("Preview"), readOnly: true },
		{ slug: "approval", label: __("Approval"), tabLabel: __("Approval"), readOnly: true },
		{ slug: "evidence", label: __("Evidence"), tabLabel: __("Evidence"), readOnly: true },
		{
			slug: "technical-json",
			label: __("Technical JSON"),
			tabLabel: __("Technical JSON"),
			readOnly: true,
			privileged: true,
		},
	]);

	let _panelToken = 0;
	let _context = null;
	let _templateCode = "";
	let _activeTab = "overview";
	let _root = null;

	function _visibleTabs(context) {
		const canTechnical = !!(context && context.can_view_technical_json);
		return shell.CONFIGURATOR_TABS.filter(function (tab) {
			if (tab.privileged && !canTechnical) return false;
			return true;
		});
	}

	function _tabBySlug(slug, context) {
		return _visibleTabs(context).find(function (tab) {
			return tab.slug === slug;
		});
	}

	function _tabDisplayLabel(tab) {
		return String(tab.tabLabel || tab.label || tab.slug).toUpperCase();
	}

	function _tabsHtml(activeSlug, context) {
		return _visibleTabs(context)
			.map(function (tab) {
				const active = tab.slug === activeSlug ? " is-active" : "";
				return `<button type="button" class="kt-std-cfg-tab${active}" data-kt-std-tab="${tab.slug}" data-testid="kt-std-cfg-tab-${tab.slug}">${_tabDisplayLabel(
					tab,
				)}</button>`;
			})
			.join("");
	}

	function _shellHtml(context, activeTab) {
		const title = shared._escapeHtml((context && context.title) || _templateCode || __("STD Configurator"));
		const lifecycle = (context && context.lifecycle_status) || "Draft";
		const badge = ui.lifecycleBadge(lifecycle);
		const initials = ui.userInitials();
		const user = (frappe.boot && frappe.boot.user) || {};
		const userName = shared._escapeHtml(user.full_name || user.name || __("Administrator"));
		return `
<div class="kt-std-cfg-root" data-testid="kt-std-cfg-root">
	<header class="kt-std-cfg-topbar" data-testid="kt-std-cfg-topbar">
		<h2 class="kt-std-cfg-topbar__brand">${__("STD Configurator")}</h2>
		<div class="kt-std-cfg-topbar__actions">
			<button type="button" class="kt-std-cfg-topbar__icon-btn" aria-label="${__("Notifications")}"><span class="material-symbols-outlined kt-std-icon">notifications</span></button>
			<button type="button" class="kt-std-cfg-topbar__icon-btn" aria-label="${__("History")}"><span class="material-symbols-outlined kt-std-icon">history</span></button>
			<button type="button" class="kt-std-cfg-topbar__icon-btn" aria-label="${__("Help")}"><span class="material-symbols-outlined kt-std-icon">help</span></button>
			<div class="kt-std-cfg-topbar__user">
				<div class="kt-std-cfg-topbar__user-meta">
					<p class="kt-std-cfg-topbar__user-name">${userName}</p>
					<p class="kt-std-cfg-topbar__user-role">${__("STD Configuration")}</p>
				</div>
				<div class="kt-std-cfg-topbar__avatar">${initials}</div>
			</div>
		</div>
	</header>
	<div class="kt-std-cfg-canvas">
		<nav class="kt-std-cfg-breadcrumbs" data-testid="kt-std-cfg-breadcrumbs">
			<a data-kt-std-breadcrumb-library>${__("STD Library")}</a>
			<span class="material-symbols-outlined kt-std-icon">chevron_right</span>
			<span class="kt-std-cfg-breadcrumbs__current">${__("Configurator")}</span>
		</nav>
		<div class="kt-std-cfg-page-head" data-testid="kt-std-cfg-doc-header">
			<div class="kt-std-cfg-title-row">
				<h1 class="kt-std-cfg-title" data-testid="kt-std-cfg-title">${title}</h1>
				<span class="kt-std-cfg-draft-badge">${badge}</span>
			</div>
			<p class="kt-std-cfg-subtitle">${__(
				"Configure the structural definitions and rules for this standard document. This version will serve as the master template for entity-level procurement.",
			)}</p>
		</div>
		<div class="kt-std-cfg-tabbar" data-testid="kt-std-cfg-tabs">${_tabsHtml(activeTab, context)}</div>
		<div class="kt-std-cfg-panel-host" data-testid="kt-std-cfg-panel-host"></div>
	</div>
</div>`;
	}

	function _getTabRenderer(slug) {
		const reg = window.kentender_procurement && kentender_procurement.std_configurator_tab_registry;
		if (reg && typeof reg.get === "function") {
			const fromReg = reg.get(slug);
			if (fromReg) return fromReg;
		}
		const tabs = window.kentender_procurement && kentender_procurement.std_configurator_tabs;
		return tabs && tabs[slug];
	}

	shell.renderTabPanel = function renderTabPanel(host, slug, options) {
		if (!host) return;
		const token = ++_panelToken;
		const tab = _tabBySlug(slug, _context) || _tabBySlug("overview", _context);
		if (!tab) return;
		host.innerHTML = `<div class="kt-std-cfg-tab-panel" data-testid="kt-std-cfg-tab-panel-${tab.slug}"><div class="kt-std-cfg-empty">${__(
			"Loading…",
		)}</div></div>`;
		const panel = host.querySelector(`[data-testid="kt-std-cfg-tab-panel-${tab.slug}"]`);

		const renderer = _getTabRenderer(tab.slug);
		if (!renderer || typeof renderer.render !== "function") {
			if (panel) {
				panel.innerHTML = `<div class="kt-std-cfg-empty">${__(
					"No renderer registered for tab {0}.",
					[tab.slug],
				)}</div>`;
			}
			return;
		}

		Promise.resolve(
			renderer.render({
				host: panel,
				templateCode: _templateCode,
				tab: tab,
				context: _context,
				root: _root,
				options: options || {},
			}),
		)
			.then(function (result) {
				if (token !== _panelToken) return;
				if (typeof renderer.bind === "function") {
					renderer.bind({
						host: panel,
						root: _root,
						templateCode: _templateCode,
						tab: tab,
						context: _context,
						result: result,
					});
				}
			})
			.catch(function (err) {
				if (token !== _panelToken) return;
				const message = (err && err.message) || String(err || __("Unable to load tab."));
				if (panel) {
					panel.innerHTML = `<div class="kt-std-cfg-empty">${shared._escapeHtml(message)}</div>`;
				}
			});
	};

	function _setActiveTab(slug, options) {
		const nextTab = _tabBySlug(slug, _context);
		const next = nextTab ? slug : "overview";
		_activeTab = next;
		if (_root) {
			const tabsEl = _root.querySelector("[data-testid='kt-std-cfg-tabs']");
			if (tabsEl) tabsEl.innerHTML = _tabsHtml(next, _context);
		}
		const host = _root && _root.querySelector("[data-testid='kt-std-cfg-panel-host']");
		shell.renderTabPanel(host, next, options);
	}

	function _bindChrome() {
		if (!_root) return;
		_root.addEventListener("click", function (event) {
			const libraryLink = event.target.closest("[data-kt-std-breadcrumb-library]");
			if (libraryLink) {
				frappe.set_route("std-library");
				return;
			}
			const btn = event.target.closest("[data-kt-std-tab]");
			if (!btn) return;
			const slug = btn.getAttribute("data-kt-std-tab");
			if (!slug || slug === _activeTab) return;
			frappe.set_route("std-configurator", _templateCode, slug);
		});
	}

	shell.bindTabFooter = function bindTabFooter(panelHost, editable, handlers) {
		const base = {
			onCancel: function () {
				frappe.set_route("std-library");
			},
			onSave: function () {
				frappe.show_alert({ message: __("Draft saved."), indicator: "green" });
			},
			onPreview: function () {
				frappe.set_route("std-configurator", _templateCode, "preview");
			},
			onSubmit: function () {
				cfgApi.submitForReview(_templateCode).then(function () {
					frappe.show_alert({ message: __("Submitted for review."), indicator: "green" });
				});
			},
		};
		const merged = Object.assign(base, handlers || {});
		ui.bindFooter(panelHost, merged);
		if (!editable) {
			panelHost.querySelectorAll("[data-kt-std-footer-cancel], [data-kt-std-footer-save], [data-kt-std-footer-submit]").forEach(
				function (el) {
					el.disabled = true;
				},
			);
		}
	};

	shell.mount = function mount(wrapper, templateCode, tabSlug) {
		shared._ensureFonts();
		if (!wrapper || !templateCode) return;
		_templateCode = String(templateCode).trim();
		_activeTab = tabSlug || "overview";

		wrapper.innerHTML = _shellHtml(_context, _activeTab);
		_root = wrapper.querySelector("[data-testid='kt-std-cfg-root']");
		_bindChrome();

		return cfgApi.getContext(_templateCode).then(function (context) {
			_context = context || {};
			const titleEl = _root && _root.querySelector("[data-testid='kt-std-cfg-title']");
			if (titleEl) titleEl.textContent = _context.title || _templateCode;
			const badgeEl = _root && _root.querySelector(".kt-std-cfg-draft-badge");
			if (badgeEl) badgeEl.textContent = ui.lifecycleBadge(_context.lifecycle_status);
			const tabsEl = _root && _root.querySelector("[data-testid='kt-std-cfg-tabs']");
			if (tabsEl) tabsEl.innerHTML = _tabsHtml(_activeTab, _context);
			_setActiveTab(_activeTab, { refreshContext: true });
			return _context;
		});
	};

	shell.getContext = function getContext() {
		return _context;
	};

	shell.getTemplateCode = function getTemplateCode() {
		return _templateCode;
	};
})();
