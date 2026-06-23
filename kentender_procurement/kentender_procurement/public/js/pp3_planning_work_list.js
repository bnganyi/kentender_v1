/**
 * P2-006 — Shared PP3 WorkList component.
 */
(function () {
	frappe.provide("kentender_procurement");

	const WORKBENCH_ITEMS_API =
		"kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model";
	const WORKBENCH_QUEUE_KEYS = {
		needs_planning: true,
		draft_packages: true,
		needs_review: true,
		ready_to_release: true,
		blocked: true,
		recently_released: true,
	};
	const API_QUEUE_BY_UI_QUEUE = {
		needs_planning: "needs_planning",
		draft_packages: "draft_packages",
		needs_review: "needs_review",
		ready_to_release: "ready_release",
		blocked: "blocked",
		recently_released: "recently_released",
	};
	const renderTokens = new WeakMap();
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-work-list"',
		'data-testid="pp3-work-item-row"',
		'data-testid="pp3-work-item-title"',
		'data-testid="pp3-work-item-state"',
		'data-testid="pp3-work-item-next-action"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* keep linter happy for static literals */
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function normalizeQueueKey(value) {
		const key = String(value || "").trim();
		return WORKBENCH_QUEUE_KEYS[key] ? key : "needs_planning";
	}

	function queueFromUrl() {
		try {
			const raw = new URLSearchParams(window.location.search).get("queue");
			return normalizeQueueKey(raw);
		} catch (e) {
			return "needs_planning";
		}
	}

	function itemId(item) {
		return String(item.work_item_id || item.underlying_object_code || item.title || "").trim();
	}

	const EMPTY_MESSAGE_KEY_BY_QUEUE = {
		recently_released: "released_recently",
	};

	function emptyMessageForQueue(queueKey) {
		const key = normalizeQueueKey(queueKey);
		const messageKey = EMPTY_MESSAGE_KEY_BY_QUEUE[key] || key;
		const emptyState =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			kentender_procurement.PlanningEmptyState.HOME_QUEUE_MESSAGES;
		if (emptyState && emptyState[messageKey]) {
			return emptyState[messageKey];
		}
		return __("No planning work items found for this queue.");
	}

	function rowHtml(item, selectedId) {
		const id = itemId(item);
		const active = id && id === selectedId;
		return (
			'<button type="button" class="pp3-work-list__row' +
			(active ? " is-active" : "") +
			'" data-testid="pp3-work-item-row" data-pp3-work-item-id="' +
			esc(id) +
			'" aria-selected="' +
			(active ? "true" : "false") +
			'">' +
			'<div class="pp3-work-list__title" data-testid="pp3-work-item-title">' +
			esc(item.title || "") +
			"</div>" +
			'<div class="pp3-work-list__meta text-muted small">' +
			esc(item.subtitle || "") +
			"</div>" +
			'<div class="pp3-work-list__state" data-testid="pp3-work-item-state">' +
			esc(item.state_label || "") +
			"</div>" +
			'<div class="pp3-work-list__next text-muted small" data-testid="pp3-work-item-next-action">' +
			esc(item.next_action_label || "") +
			"</div>" +
			"</button>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const items = Array.isArray(o.items) ? o.items : [];
		const selectedId = String(o.selectedId || "").trim();
		if (!items.length) {
			const emptyMessage = String(o.emptyMessage || __("No planning work items found for this queue.")).trim();
			return (
				'<div class="pp3-work-list" data-testid="pp3-work-list">' +
				'<div class="pp3-work-list__empty text-muted small">' +
				esc(emptyMessage) +
				"</div></div>"
			);
		}
		let rows = "";
		for (let i = 0; i < items.length; i += 1) {
			rows += rowHtml(items[i], selectedId);
		}
		return (
			'<div class="pp3-work-list" data-testid="pp3-work-list">' +
			'<div class="pp3-work-list__rows" role="listbox">' +
			rows +
			"</div></div>"
		);
	}

	function render(host, opts) {
		if (!host || host.nodeType !== 1) return;
		host.innerHTML = html(opts || {});
	}

	function bindSelection(host, opts) {
		if (!host) return;
		const o = opts || {};
		const items = Array.isArray(o.items) ? o.items : [];
		const buttons = host.querySelectorAll("[data-pp3-work-item-id]");
		for (let i = 0; i < buttons.length; i += 1) {
			const button = buttons[i];
			if (button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function () {
				const selectedId = String(button.getAttribute("data-pp3-work-item-id") || "").trim();
				let selectedItem = null;
				for (let j = 0; j < items.length; j += 1) {
					if (itemId(items[j]) === selectedId) {
						selectedItem = items[j];
						break;
					}
				}
				render(host, {
					items: items,
					selectedId: selectedId,
					emptyMessage: o.emptyMessage,
				});
				bindSelection(host, {
					items: items,
					selectedId: selectedId,
					emptyMessage: o.emptyMessage,
					onSelect: o.onSelect,
				});
				if (typeof o.onSelect === "function" && selectedItem) {
					o.onSelect(selectedId, selectedItem);
				}
			});
		}
	}

	function callWorkbenchItems(queueKey) {
		const uiQueue = normalizeQueueKey(queueKey);
		const apiQueue = API_QUEUE_BY_UI_QUEUE[uiQueue] || "needs_planning";
		return new Promise(function (resolve) {
			frappe.call({
				method: WORKBENCH_ITEMS_API,
				args: { queue: apiQueue, start: 0, limit: 50 },
				callback: function (response) {
					resolve((response && response.message) || {});
				},
				error: function () {
					resolve({ ok: false, items: [] });
				},
			});
		});
	}

	function fetchAndRender(host, opts) {
		if (!host || host.nodeType !== 1) return Promise.resolve();
		const token = (renderTokens.get(host) || 0) + 1;
		renderTokens.set(host, token);
		const o = opts || {};
		const queueKey = normalizeQueueKey(o.queue || queueFromUrl());
		render(host, { items: [], emptyMessage: __("Loading planning work...") });
		const queueEmptyMessage = emptyMessageForQueue(queueKey);
		return callWorkbenchItems(queueKey).then(function (payload) {
			if (renderTokens.get(host) !== token) return;
			const items = payload && payload.ok && Array.isArray(payload.items) ? payload.items : [];
			const selectedId = items.length ? itemId(items[0]) : "";
			render(host, {
				items: items,
				selectedId: selectedId,
				emptyMessage: queueEmptyMessage,
			});
			bindSelection(host, {
				items: items,
				selectedId: selectedId,
				emptyMessage: queueEmptyMessage,
				onSelect: o.onSelect,
			});
			if (selectedId && typeof o.onSelect === "function") {
				o.onSelect(selectedId, items[0]);
			}
		});
	}

	function renderForSlug(host, slug, opts) {
		if (String(slug || "").trim() !== "") {
			if (host && host.nodeType === 1) host.innerHTML = "";
			return Promise.resolve();
		}
		return fetchAndRender(host, opts || {});
	}

	kentender_procurement.PlanningWorkbenchWorkList = {
		html: html,
		render: render,
		renderForSlug: renderForSlug,
		fetchAndRender: fetchAndRender,
		queueFromUrl: queueFromUrl,
	};
})();
