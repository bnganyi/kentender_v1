/**
 * Desk list scroll + selection helpers for workspace shells.
 * Mirror: `kentender_strategy/.../public/js/workspace_list_selection_utils.js` — keep APIs identical
 * until a shared package exists (second script on Desk is a no-op if `KTWorkspaceListSelection` already set).
 */
(function () {
	function listHost(root, selector) {
		if (!root || !selector || typeof root.querySelector !== "function") {
			return null;
		}
		return root.querySelector(selector);
	}

	function readScrollTop(root, selector) {
		const host = listHost(root, selector);
		return host && typeof host.scrollTop === "number" ? host.scrollTop : 0;
	}

	function restoreScrollTop(root, selector, top, selectedValue, rowSelector, attrName) {
		const host = listHost(root, selector);
		if (!host) {
			return;
		}
		host.scrollTop = typeof top === "number" ? top : 0;
		if (!selectedValue || !rowSelector || !attrName) {
			return;
		}
		let selectedRow = null;
		host.querySelectorAll(rowSelector).forEach(function (el) {
			if (el.getAttribute(attrName) === selectedValue) {
				selectedRow = el;
			}
		});
		if (!selectedRow || typeof selectedRow.getBoundingClientRect !== "function") {
			return;
		}
		const rowRect = selectedRow.getBoundingClientRect();
		const listRect = host.getBoundingClientRect();
		if (rowRect.top < listRect.top || rowRect.bottom > listRect.bottom) {
			selectedRow.scrollIntoView({ block: "nearest" });
		}
	}

	function syncSelection(root, selector, rowSelector, attrName, selectedValue, activeClass) {
		const host = listHost(root, selector);
		if (!host || !rowSelector || !attrName) {
			return;
		}
		const cls = activeClass || "is-active";
		host.querySelectorAll(rowSelector).forEach(function (el) {
			const value = el.getAttribute(attrName);
			const isActive = !!selectedValue && value === selectedValue;
			el.classList.toggle(cls, isActive);
			el.setAttribute("aria-selected", isActive ? "true" : "false");
		});
	}

	window.KTWorkspaceListSelection = window.KTWorkspaceListSelection || {
		listHost: listHost,
		readScrollTop: readScrollTop,
		restoreScrollTop: restoreScrollTop,
		syncSelection: syncSelection,
	};
})();
