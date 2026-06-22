/**
 * P5B-003 — Shared Planning work list (title, metadata, status, optional blocker).
 */
(function () {
	frappe.provide("kentender_procurement");

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function statusHtml(item) {
		const label = String(item.status_label || "").trim();
		if (!label) return "";
		const badgeApi =
			kentender_procurement &&
			kentender_procurement.PlanningStatusBadge &&
			typeof kentender_procurement.PlanningStatusBadge.html === "function"
				? kentender_procurement.PlanningStatusBadge
				: null;
		if (badgeApi) {
			return badgeApi.html(label, { context: "package", scope: "list" });
		}
		return esc(label);
	}

	function blockerHtml(blockerCount) {
		const count = Number(blockerCount || 0);
		if (!count || count < 1) return "";
		const label = count === 1 ? __("1 blocker") : __("{0} blockers", [count]);
		return (
			'<div class="pp2-work-list-row__blocker text-muted small" data-testid="pp2-work-list-row-blocker">' +
			esc(label) +
			"</div>"
		);
	}

	function approvedDemandBlockerHtml(item) {
		const count = Number(item.blocker_count || 0);
		if (!count || count < 1) return "";
		const label = String(item.blocker_label || "").trim() || (count === 1 ? __("1 blocker") : __("{0} blockers", [count]));
		return (
			'<div class="pp2-approved-demand-row__blocker text-muted small" data-testid="pp2-approved-demand-row-blocker">' +
			esc(label) +
			"</div>"
		);
	}

	function approvedDemandRowHtml(item, opts) {
		const o = opts || {};
		const id = String(item.id || "").trim();
		const selectedId = String(o.selectedId || "").trim();
		const on = !!id && id === selectedId;
		return (
			'<button type="button" class="pp2-work-list-row pp2-approved-demand-row' +
			(on ? " is-active" : "") +
			'" data-testid="pp2-approved-demand-row" data-pp2-work-item-id="' +
			esc(id) +
			'" role="option" aria-selected="' +
			(on ? "true" : "false") +
			'">' +
			'<div class="pp2-approved-demand-row__title" data-testid="pp2-approved-demand-row-title">' +
			esc(item.title || "") +
			"</div>" +
			'<div class="pp2-approved-demand-row__category-value text-muted small" data-testid="pp2-approved-demand-row-category-value">' +
			esc(item.category_value || item.subtitle || "") +
			"</div>" +
			'<div class="pp2-approved-demand-row__funding text-muted small" data-testid="pp2-approved-demand-row-funding-status">' +
			esc(item.funding_status || "") +
			"</div>" +
			'<div class="pp2-approved-demand-row__planning-status" data-testid="pp2-approved-demand-row-planning-status">' +
			statusHtml({ status_label: item.planning_status || item.status_label }) +
			"</div>" +
			approvedDemandBlockerHtml(item) +
			"</button>"
		);
	}

	function rowSelectorForSlug(slug) {
		return String(slug || "") === "approved-demands"
			? '[data-testid="pp2-approved-demand-row"]'
			: '[data-testid="pp2-work-list-row"]';
	}

	function rowHtml(item, opts) {
		const o = opts || {};
		if (String(o.slug || "") === "approved-demands") {
			return approvedDemandRowHtml(item, o);
		}
		const id = String(item.id || "").trim();
		const selectedId = String(o.selectedId || "").trim();
		const on = !!id && id === selectedId;
		return (
			'<button type="button" class="pp2-work-list-row' +
			(on ? " is-active" : "") +
			'" data-testid="pp2-work-list-row" data-pp2-work-item-id="' +
			esc(id) +
			'" role="option" aria-selected="' +
			(on ? "true" : "false") +
			'">' +
			'<div class="pp2-work-list-row__title" data-testid="pp2-work-list-row-title">' +
			esc(item.title || "") +
			"</div>" +
			'<div class="pp2-work-list-row__meta text-muted small" data-testid="pp2-work-list-row-meta">' +
			esc(item.subtitle || "") +
			"</div>" +
			'<div class="pp2-work-list-row__status" data-testid="pp2-work-list-row-status">' +
			statusHtml(item) +
			"</div>" +
			blockerHtml(item.blocker_count) +
			"</button>"
		);
	}

	function readSelectedFromUrl(items) {
		const ids = {};
		const list = Array.isArray(items) ? items : [];
		for (let i = 0; i < list.length; i += 1) {
			const id = String(list[i].id || "").trim();
			if (id) ids[id] = true;
		}
		try {
			const raw = new URLSearchParams(window.location.search).get("item");
			if (raw && ids[raw]) return raw;
		} catch (e) {
			/* ignore */
		}
		return "";
	}

	function setSelectedUrl(itemId) {
		const id = String(itemId || "").trim();
		try {
			const u = new URL(window.location.href);
			if (id) {
				u.searchParams.set("item", id);
			} else {
				u.searchParams.delete("item");
			}
			window.history.replaceState({}, "", u.pathname + u.search + u.hash);
		} catch (e) {
			/* ignore */
		}
	}

	function html(opts) {
		const o = opts || {};
		const items = Array.isArray(o.items) ? o.items : [];
		const selectedId =
			o.selectedId != null ? String(o.selectedId) : readSelectedFromUrl(items);
		if (!items.length) {
			const emptyMessage = String(o.emptyMessage || __("No items in this queue yet.")).trim();
			return (
				'<div class="pp2-work-list" data-testid="pp2-work-list">' +
				'<div class="pp2-work-list-empty text-muted small" data-testid="pp2-work-list-empty">' +
				esc(emptyMessage) +
				"</div></div>"
			);
		}
		let rows = "";
		for (let i = 0; i < items.length; i += 1) {
			rows += rowHtml(items[i], { selectedId: selectedId, slug: o.slug });
		}
		return (
			'<div class="pp2-work-list" data-testid="pp2-work-list">' +
			'<div class="pp2-work-list__rows" data-testid="pp2-work-list-rows" role="listbox">' +
			rows +
			"</div></div>"
		);
	}

	function bindRows(host, opts) {
		if (!host) return;
		const o = opts || {};
		const slug = o.slug != null ? String(o.slug) : "";
		const items = Array.isArray(o.items) ? o.items : [];
		const buttons = host.querySelectorAll("[data-pp2-work-item-id]");
		for (let i = 0; i < buttons.length; i += 1) {
			const button = buttons[i];
			if (button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function () {
				const itemId = String(button.getAttribute("data-pp2-work-item-id") || "").trim();
				if (!itemId) return;
				setSelectedUrl(itemId);
				let matched = null;
				for (let j = 0; j < items.length; j += 1) {
					if (String(items[j].id || "").trim() === itemId) {
						matched = items[j];
						break;
					}
				}
				if (typeof o.onSelect === "function") {
					o.onSelect(itemId, matched);
				}
				render(host, {
					items: items,
					selectedId: itemId,
					slug: slug,
					emptyMessage: o.emptyMessage,
					onSelect: o.onSelect,
				});
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const o = opts || {};
		const items = Array.isArray(o.items) ? o.items : [];
		const selectedId =
			o.selectedId != null ? String(o.selectedId) : readSelectedFromUrl(items);
		target.innerHTML = html({
			items: items,
			selectedId: selectedId,
			slug: o.slug,
			emptyMessage: o.emptyMessage,
		});
		bindRows(target, {
			items: items,
			selectedId: selectedId,
			slug: o.slug,
			emptyMessage: o.emptyMessage,
			onSelect: o.onSelect,
		});
		if (window.KTWorkspaceListSelection && items.length) {
			window.KTWorkspaceListSelection.syncSelection(
				target,
				'[data-testid="pp2-work-list-rows"]',
				rowSelectorForSlug(o.slug),
				"data-pp2-work-item-id",
				selectedId,
				"is-active"
			);
		}
	}

	function renderForSlug(host, slug, opts) {
		const o = opts || {};
		render(host, {
			items: Array.isArray(o.items) ? o.items : [],
			selectedId: o.selectedId,
			slug: slug,
			emptyMessage: o.emptyMessage,
			onSelect: o.onSelect,
		});
	}

	kentender_procurement.PlanningWorkList = {
		html: html,
		rowHtml: rowHtml,
		render: render,
		renderForSlug: renderForSlug,
		readSelectedFromUrl: readSelectedFromUrl,
		setSelectedUrl: setSelectedUrl,
	};
})();
