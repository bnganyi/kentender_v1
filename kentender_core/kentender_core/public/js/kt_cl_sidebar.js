// Civic Ledger sidebar — curated, config-driven Sidenav.
// Reproduces the mock IA (code.html 166-307) exactly from an `items` config so
// the POC proves faithful porting, while staying reusable: any page can pass its
// own `items` array. Item schema:
//   link:  { kind: "link",  label, icon, route: [...] | url: "..", active? }
//   group: { kind: "group", label, icon, keepClosed?, children: [ childItem ] }
//   child: { label, route: [...] | url: "..", active? }
frappe.provide("kentender_core.cl_sidebar");

(function () {
	"use strict";

	var SIDENAV_ID = "kt-cl-sidenav";
	var STORAGE_KEY = "kt-cl-sidenav-sections";

	function spec() {
		return kentender_core.cl_code_spec || {};
	}

	function components() {
		return kentender_core.cl_components || {};
	}

	function escapeHtml(value) {
		if (components().escapeHtml) return components().escapeHtml(value);
		return String(value == null ? "" : value);
	}

	function msIcon(name, sizePx, extraClass) {
		var size = sizePx || 20;
		return (
			'<span class="material-symbols-outlined' +
			(extraClass ? " " + extraClass : "") +
			'" style="font-size: ' +
			size +
			'px;" aria-hidden="true">' +
			escapeHtml(name) +
			"</span>"
		);
	}

	// ---- Routing helpers ------------------------------------------------
	function routeToHref(route) {
		if (!route) return "#";
		if (typeof route === "string") return route;
		if (route.length) return "/app/" + route.map(encodeURIComponent).join("/");
		return "#";
	}

	function routesMatch(a, b) {
		if (!a || !b || a.length !== b.length) return false;
		for (var i = 0; i < a.length; i += 1) {
			if (String(a[i]) !== String(b[i])) return false;
		}
		return true;
	}

	function isActive(item) {
		if (item.active === true) return true;
		if (item.active === false) return false;
		var route = item.route;
		if (!route || typeof route === "string") return false;
		try {
			return routesMatch(route, frappe.get_route() || []);
		} catch (e) {
			return false;
		}
	}

	// ---- Collapse persistence ------------------------------------------
	function readSectionState(workspaceKey) {
		try {
			var all = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
			return all[workspaceKey] || {};
		} catch (e) {
			return {};
		}
	}

	function writeSectionState(workspaceKey, label, collapsed) {
		try {
			var all = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
			if (!all[workspaceKey]) all[workspaceKey] = {};
			all[workspaceKey][label] = collapsed;
			localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
		} catch (e2) {
			/* ignore */
		}
	}

	// ---- Renderers (code.html 167-305) ----------------------------------
	function renderBrandBlock(opts) {
		opts = opts || {};
		var avatarInner = opts.avatarUrl
			? '<img alt="" class="w-full h-full object-cover" src="' + escapeHtml(opts.avatarUrl) + '" />'
			: escapeHtml(opts.avatarInitials || "KT");

		return (
			'<div class="p-4 border-b border-outline-variant flex flex-col gap-2" data-testid="kt-cl-sidebar-brand">' +
			'<div class="flex items-center gap-2 mb-1">' +
			'<span class="font-headline-md text-headline-md font-bold text-primary">KenTender</span>' +
			"</div>" +
			'<div class="flex items-center gap-3">' +
			'<div class="w-8 h-8 rounded-full overflow-hidden border border-outline-variant">' +
			avatarInner +
			"</div>" +
			"<div>" +
			'<h2 class="font-body-md text-body-md font-bold text-on-surface leading-tight">' +
			escapeHtml(opts.portalTitle || __("Procurement Portal")) +
			"</h2>" +
			'<p class="font-label-sm text-label-sm text-on-surface-variant">' +
			escapeHtml(opts.portalSubtitle || __("Public Sector")) +
			"</p>" +
			"</div></div></div>"
		);
	}

	function routeAttr(item) {
		if (item.url) return ' data-kt-cl-route="' + escapeHtml(JSON.stringify(item.url)) + '"';
		if (item.route) return ' data-kt-cl-route="' + escapeHtml(JSON.stringify(item.route)) + '"';
		return "";
	}

	function renderNavLink(item) {
		var active = isActive(item);
		var cls = active ? spec().NAV_LINK_ACTIVE : spec().NAV_LINK;
		var href = item.url || routeToHref(item.route);
		return (
			'<li data-testid="kt-cl-nav-item">' +
			'<a class="' +
			cls +
			'" href="' +
			escapeHtml(href) +
			'"' +
			routeAttr(item) +
			(active ? ' aria-current="page"' : "") +
			">" +
			msIcon(item.icon || "circle", 20) +
			'<span class="font-body-md text-body-md">' +
			escapeHtml(__(item.label)) +
			"</span></a></li>"
		);
	}

	function renderNavChild(item) {
		var active = isActive(item);
		var cls = active ? spec().NAV_CHILD_ACTIVE : spec().NAV_CHILD;
		var href = item.url || routeToHref(item.route);
		return (
			'<li data-testid="kt-cl-nav-child">' +
			'<a class="' +
			cls +
			'" href="' +
			escapeHtml(href) +
			'"' +
			routeAttr(item) +
			(active ? ' aria-current="page"' : "") +
			">" +
			escapeHtml(__(item.label)) +
			"</a></li>"
		);
	}

	function renderNavGroup(group, collapsed) {
		var chevron = collapsed ? "expand_more" : "expand_less";
		return (
			'<li data-testid="kt-cl-nav-group">' +
			'<div class="' +
			spec().NAV_PARENT +
			'" data-kt-cl-section="' +
			escapeHtml(group.label) +
			'" role="button" tabindex="0" aria-expanded="' +
			(collapsed ? "false" : "true") +
			'">' +
			'<div class="flex items-center gap-3">' +
			msIcon(group.icon || "folder", 20) +
			'<span class="font-body-md text-body-md">' +
			escapeHtml(__(group.label)) +
			"</span></div>" +
			msIcon(chevron, 16, "text-outline") +
			"</div>" +
			'<ul class="' +
			spec().NAV_CHILDREN_LIST +
			(collapsed ? " cl-nested-hidden" : "") +
			'" data-kt-cl-nested="' +
			escapeHtml(group.label) +
			'">' +
			(group.children || [])
				.map(function (child) {
					return renderNavChild(child);
				})
				.join("") +
			"</ul></li>"
		);
	}

	function renderFooter(footerItems) {
		var items =
			footerItems ||
			[
				{
					label: "Settings",
					icon: "settings",
					url: "/app/user-profile",
					testid: "kt-cl-sidebar-settings",
				},
				{
					label: "Support",
					icon: "contact_support",
					url: "https://docs.frappe.io",
					external: true,
					testid: "kt-cl-sidebar-support",
				},
			];

		var links = items
			.map(function (it) {
				var target = it.external ? ' target="_blank" rel="noopener noreferrer"' : "";
				return (
					"<li>" +
					'<a class="' +
					spec().NAV_FOOTER_LINK +
					'" href="' +
					escapeHtml(it.url || "#") +
					'"' +
					target +
					routeAttr(it) +
					(it.testid ? ' data-testid="' + escapeHtml(it.testid) + '"' : "") +
					">" +
					msIcon(it.icon || "circle", 20) +
					'<span class="font-body-md text-body-md">' +
					escapeHtml(__(it.label)) +
					"</span></a></li>"
				);
			})
			.join("");

		return (
			'<div class="p-3 border-t border-outline-variant flex flex-col gap-0.5" data-testid="kt-cl-sidebar-footer">' +
			'<ul class="flex flex-col gap-0.5 cl-list-reset">' +
			links +
			"</ul></div>"
		);
	}

	function renderSidenav(opts) {
		opts = opts || {};
		var items = opts.items || [];
		var workspaceKey = opts.workspaceKey || "default";
		var sectionState = readSectionState(workspaceKey);

		var navItems = items
			.map(function (item) {
				if (item.kind === "group" || item.children) {
					var collapsed = sectionState[item.label];
					if (collapsed === undefined) collapsed = !!item.keepClosed;
					return renderNavGroup(item, collapsed);
				}
				return renderNavLink(item);
			})
			.join("");

		return (
			'<nav class="kt-cl-sidenav ' +
			spec().SIDENAV_ROOT +
			'" id="' +
			SIDENAV_ID +
			'" data-testid="kt-cl-sidenav" aria-label="' +
			escapeHtml(__("Primary navigation")) +
			'">' +
			renderBrandBlock(opts) +
			'<div class="flex-1 py-2 overflow-y-auto flex flex-col gap-0.5">' +
			'<ul class="flex flex-col cl-list-reset">' +
			navItems +
			"</ul></div>" +
			renderFooter(opts.footerItems) +
			"</nav>"
		);
	}

	function bindNavEvents(workspaceKey) {
		var $nav = $("#" + SIDENAV_ID);
		if (!$nav.length) return;

		$nav.find("[data-kt-cl-route]").on("click", function (e) {
			var raw = $(this).attr("data-kt-cl-route");
			if (!raw) return;
			e.preventDefault();
			try {
				var route = JSON.parse(raw);
				if (typeof route === "string") {
					if (route.indexOf("http") === 0) {
						window.open(route, "_blank", "noopener,noreferrer");
					} else {
						window.location.href = route;
					}
					return;
				}
				if (route && route.length) {
					frappe.set_route.apply(frappe, route);
				}
			} catch (err) {
				/* ignore */
			}
		});

		function toggleSection($header) {
			var label = $header.attr("data-kt-cl-section");
			var $nested = $nav.find('[data-kt-cl-nested="' + label + '"]');
			var collapsed = !$nested.hasClass("cl-nested-hidden");
			if (collapsed) {
				$nested.addClass("cl-nested-hidden");
				$header.attr("aria-expanded", "false");
				$header.find(".material-symbols-outlined").last().text("expand_more");
			} else {
				$nested.removeClass("cl-nested-hidden");
				$header.attr("aria-expanded", "true");
				$header.find(".material-symbols-outlined").last().text("expand_less");
			}
			writeSectionState(workspaceKey, label, collapsed);
		}

		$nav.find("[data-kt-cl-section]").on("click", function () {
			toggleSection($(this));
		});
		$nav.find("[data-kt-cl-section]").on("keydown", function (e) {
			if (e.key === "Enter" || e.key === " " || e.keyCode === 13 || e.keyCode === 32) {
				e.preventDefault();
				toggleSection($(this));
			}
		});
	}

	function mount(workspaceKey, opts) {
		if (!document.body.classList.contains("kt-cl-shell")) return;
		opts = opts || {};
		opts.workspaceKey = workspaceKey || opts.workspaceKey || "default";
		$("#" + SIDENAV_ID).remove();
		var html = renderSidenav(opts);
		if (!html) return;
		$("body").append(html);
		bindNavEvents(opts.workspaceKey);
	}

	function unmount() {
		$("#" + SIDENAV_ID).remove();
	}

	kentender_core.cl_sidebar = {
		mount: mount,
		unmount: unmount,
		renderSidenav: renderSidenav,
		isActive: isActive,
		routeToHref: routeToHref,
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.sidenav = kentender_core.cl_sidebar;
})();
