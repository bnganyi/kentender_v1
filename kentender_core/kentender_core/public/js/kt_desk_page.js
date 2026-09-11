// KenTender Vue-in-Desk page runtime — the one page lifecycle every Vue-owned
// Desk page uses (AGENTS.md §6.1, §6.4, §6.5).
//
// Frappe keeps every page container alive in the DOM: `frappe.views.Container
// .change_to()` only show()s the destination and hide()s the origin. Before
// this runtime existed, eleven hand-copied page controllers unmounted their
// Vue app on every hide and rebuilt it on every show (empty the container,
// re-require the bundle, createApp, loading=true, refetch) — including hops
// between the four Planning pages that share one bundle — while
// kt_cl_shell_router stripped the shell body classes after each route change
// and the page re-added them on the next. Every navigation therefore painted
// a blank container, a skeleton and a layout reflow before the content.
//
// Contract:
//   register(pageName, opts)   — wires on_page_load/show/hide. The app is
//                                mounted once per `group` and kept alive; pages
//                                in the same group share one live app whose
//                                root element moves between their containers.
//   useRoute(vue, pageSlug)    — route state for the consuming bundle's own Vue
//                                (pass its ref/onMounted/...): one router
//                                listener per app, paused while the page is
//                                hidden or the component deactivated, re-synced
//                                on resume; `epoch` ticks when the page resumes
//                                on the same route so screens revalidate quietly.
//   createScreenCache()        — per-screen payload cache so a revisited screen
//                                renders instantly and refreshes in place.
//   ownsRoute(route)           — true for a registered page: the shell router
//                                must not tear this page's chrome down.
frappe.provide("kentender_core.desk_page");

(function () {
	"use strict";

	var groups = {};
	var pageToGroup = {};
	var chromeHidden = false;
	var SHOW_EVENT = "kt:desk-page:show";
	var HIDE_EVENT = "kt:desk-page:hide";
	var CHROME_SELECTOR = ".navbar, .page-head";

	function shell() {
		return (window.kentender_core && kentender_core.cl_shell) || null;
	}

	function groupFor(pageSlug) {
		var id = pageToGroup[pageSlug];
		return id ? groups[id] : null;
	}

	function hideFrappeChrome() {
		document.querySelectorAll(CHROME_SELECTOR).forEach(function (el) {
			if (el.style.getPropertyValue("display") !== "none") {
				el.style.setProperty("display", "none", "important");
			}
		});
		chromeHidden = true;
	}

	function restoreFrappeChrome() {
		if (!chromeHidden) return;
		document.querySelectorAll(CHROME_SELECTOR).forEach(function (el) {
			el.style.removeProperty("display");
		});
		chromeHidden = false;
	}

	function applyChrome(opts) {
		var sh = shell();
		var key = (opts && opts.sidebarWorkspaceKey) || "procurement";
		if (sh) {
			if (!sh.isNativeActive()) {
				sh.enterNative({ sidebarWorkspaceKey: key });
			} else {
				sh.ensureNativeSidebar(key);
			}
			var host = document.getElementById("kt-cl-chrome-host");
			if (host && host.childNodes.length) host.innerHTML = "";
		}
		hideFrappeChrome();
	}

	function releaseChrome() {
		restoreFrappeChrome();
	}

	function placeholderHtml() {
		return '<div class="kt-industry kt-desk-page-placeholder"><div class="kt-rail-placeholder"></div></div>';
	}

	function mountElement(group) {
		if (group.el) return group.el;
		var el = document.createElement("div");
		el.className = "kt-desk-page-mount";
		el.setAttribute("data-kt-desk-page-group", group.id);
		el.innerHTML = placeholderHtml();
		group.el = el;
		return el;
	}

	function ensureMounted(group, wrapper) {
		var section = wrapper.querySelector(".layout-main-section") || wrapper;
		var el = mountElement(group);
		if (el.parentNode !== section) {
			section.appendChild(el);
		}
		if (group.app || group.pending) return;
		group.pending = true;
		frappe.require(group.bundles).then(function () {
			group.pending = false;
			if (group.app) return;
			group.app = group.mount(el);
		});
	}

	function setActive(group, active) {
		var was = group.active;
		group.active = active;
		if (!group.el) return;
		group.el.dispatchEvent(
			new CustomEvent(active ? SHOW_EVENT : HIDE_EVENT, {
				detail: { group: group.id, resumed: active && !was, route: frappe.get_route() },
			})
		);
	}

	function register(pageName, opts) {
		opts = opts || {};
		if (typeof opts.mount !== "function") {
			throw new Error("kentender_core.desk_page.register(" + pageName + "): opts.mount is required");
		}
		var page = frappe.pages[pageName];
		if (!page) {
			throw new Error("kentender_core.desk_page.register(" + pageName + "): frappe.pages entry missing");
		}
		var id = opts.group || pageName;
		var group = groups[id];
		if (!group) {
			group = groups[id] = { id: id, el: null, app: null, pending: false, active: false };
		}
		group.bundles = [].concat(opts.bundles || []);
		group.mount = opts.mount;
		group.sidebarWorkspaceKey = opts.sidebarWorkspaceKey || "procurement";
		pageToGroup[pageName] = id;
		[].concat(opts.pages || []).forEach(function (slug) {
			pageToGroup[slug] = id;
		});

		page.on_page_load = function (wrapper) {
			wrapper.page = frappe.ui.make_app_page({
				parent: wrapper,
				title: opts.title || pageName,
				single_column: true,
			});
		};
		page.on_page_show = function (wrapper) {
			applyChrome(group);
			ensureMounted(group, wrapper);
			setActive(group, true);
		};
		page.on_page_hide = function () {
			setActive(group, false);
		};
	}

	function ownsRoute(route) {
		var r = route || frappe.get_route() || [];
		return !!(r.length && pageToGroup[String(r[0])]);
	}

	function useRoute(vue, pageSlug) {
		var route = vue.ref(currentRoute());
		var epoch = vue.ref(0);
		var active = true;
		var paused = false;
		var keptAlive = false;

		function currentRoute() {
			var r = frappe.get_route();
			return r && r.length ? r.slice() : [pageSlug];
		}
		function shown() {
			var group = groupFor(pageSlug);
			return group ? group.active : true;
		}
		function sync() {
			var next = currentRoute();
			if (next.join("/") === route.value.join("/")) return false;
			route.value = next;
			return true;
		}
		function applyRouteChange() {
			if (!active || paused || !shown()) return;
			sync();
		}
		function onRouteChange() {
			// A KeepAlive-kept screen hears the outgoing route before its root
			// re-renders and deactivates it; applying that route would clobber
			// the screen's own record id (a Budget detail screen would fetch
			// "review" as a budget id, and Frappe's 404 handler then pops a
			// "Not found" modal), and the next activation would read as a new
			// record and cold-load it. The root syncs synchronously and queues
			// Vue's flush; deferring behind that flush lets a screen that just
			// got deactivated ignore the change. A microtask is not enough:
			// children mount before their parent, so the screen a page was
			// opened on binds its listener *before* the root and its microtask
			// ran ahead of the root's flush (confirmed live 2026-09-06 — direct
			// load on a record screen, then navigate to a sibling screen). A
			// macrotask always runs after every pending microtask, including
			// the flush that deactivates this screen, whatever the bind order.
			if (keptAlive) {
				setTimeout(applyRouteChange, 0);
			} else {
				applyRouteChange();
			}
		}
		function onResume() {
			if (!active) return;
			if (!sync()) epoch.value += 1;
		}
		function onShow(event) {
			if (event.detail && event.detail.resumed && !paused) onResume();
		}
		function element() {
			var group = groupFor(pageSlug);
			return group ? group.el : null;
		}

		vue.onMounted(function () {
			frappe.router.on("change", onRouteChange);
			var el = element();
			if (el) el.addEventListener(SHOW_EVENT, onShow);
		});
		vue.onUnmounted(function () {
			active = false;
			var el = element();
			if (el) el.removeEventListener(SHOW_EVENT, onShow);
		});
		if (vue.onDeactivated) {
			vue.onDeactivated(function () {
				paused = true;
			});
		}
		if (vue.onActivated) {
			vue.onActivated(function () {
				keptAlive = true;
				if (!paused) return;
				paused = false;
				onResume();
			});
		}

		function go() {
			frappe.set_route.apply(frappe, [pageSlug].concat(Array.prototype.slice.call(arguments)));
		}

		return { route: route, go: go, epoch: epoch, isShown: shown };
	}

	function createScreenCache() {
		var store = new Map();
		return {
			get: function (key) {
				return store.get(key);
			},
			has: function (key) {
				return store.has(key);
			},
			set: function (key, value) {
				store.set(key, value);
			},
			remove: function (key) {
				store.delete(key);
			},
			clear: function () {
				store.clear();
			},
		};
	}

	// Frappe fires "page-change" from Container.change_to for every page —
	// Desk-native views included — after the destination's own script has run,
	// so a registered page is already known here and only foreign pages get
	// the navbar back.
	$(document).on("page-change", function () {
		if (!ownsRoute(frappe.get_route())) releaseChrome();
	});

	kentender_core.desk_page = {
		register: register,
		ownsRoute: ownsRoute,
		applyChrome: function (route) {
			var r = route || frappe.get_route() || [];
			applyChrome(groupFor(String(r[0] || "")) || {});
		},
		releaseChrome: releaseChrome,
		useRoute: useRoute,
		createScreenCache: createScreenCache,
		isActive: function (pageSlug) {
			var group = groupFor(pageSlug);
			return group ? group.active : false;
		},
	};
})();
