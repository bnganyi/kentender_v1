// KenTender custom Page lifecycle adapter.
// Frappe emits a jQuery `hide` event for a departing page container but does
// not dispatch the custom Page object's `on_page_hide` callback.
frappe.provide("kentender_core.page_lifecycle");

(function () {
	"use strict";

	var BOUND_FLAG = "ktPageLifecycleBound";
	var observer = null;
	var started = false;

	function isSurfaceBodyClass(name) {
		return (
			/^kt-(str|bud|dem|pln)-/.test(name) ||
			name === "kt-ph-page-shell" ||
			(/^std-prod-/.test(name) && /-shell$/.test(name))
		);
	}

	function clearSurfaceBodyClasses() {
		if (!document.body) return;
		Array.prototype.slice.call(document.body.classList).forEach(function (name) {
			if (isSurfaceBodyClass(name)) {
				document.body.classList.remove(name);
			}
		});
	}

	function dispatchPageHide(wrapper) {
		try {
			if (typeof wrapper.on_page_hide === "function") {
				wrapper.on_page_hide(wrapper);
			}
		} finally {
			// Surface classes control global Desk layout. Clear the whole departing
			// family before Frappe shows the destination; its on_page_show restores
			// only the classes valid for the new route.
			clearSurfaceBodyClasses();
		}
	}

	function bindPage(wrapper) {
		if (!wrapper || !wrapper.classList || !wrapper.classList.contains("page-container")) {
			return;
		}
		if (wrapper.dataset[BOUND_FLAG] === "1") return;
		wrapper.dataset[BOUND_FLAG] = "1";
		$(wrapper).on("hide.ktPageLifecycle", function (event) {
			if (event.target === wrapper) {
				dispatchPageHide(wrapper);
			}
		});
	}

	function bindPagesWithin(root) {
		if (!root) return;
		if (root.matches && root.matches(".page-container")) {
			bindPage(root);
		}
		if (root.querySelectorAll) {
			root.querySelectorAll(".page-container").forEach(bindPage);
		}
	}

	function start() {
		if (started || !document.body) return;
		started = true;
		bindPagesWithin(document);
		observer = new MutationObserver(function (mutations) {
			mutations.forEach(function (mutation) {
				mutation.addedNodes.forEach(bindPagesWithin);
			});
		});
		observer.observe(document.body, { childList: true, subtree: true });
	}

	kentender_core.page_lifecycle = {
		start: start,
		bindPage: bindPage,
		bindPagesWithin: bindPagesWithin,
		clearSurfaceBodyClasses: clearSurfaceBodyClasses,
	};

	if (document.readyState === "loading") {
		$(start);
	} else {
		start();
	}
})();
