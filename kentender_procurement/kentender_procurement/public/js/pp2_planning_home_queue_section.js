/**
 * P5C-003 — Reusable Planning Home queue section (reset addendum §8.4).
 */
(function () {
	frappe.provide("kentender_procurement");

	const fetchTokens = new WeakMap();

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function cardApi() {
		return (
			kentender_procurement &&
			kentender_procurement.PlanningHomeItemCard &&
			typeof kentender_procurement.PlanningHomeItemCard.html === "function"
				? kentender_procurement.PlanningHomeItemCard
				: null
		);
	}

	function emptyApi() {
		return (
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			typeof kentender_procurement.PlanningEmptyState.html === "function"
				? kentender_procurement.PlanningEmptyState
				: null
		);
	}

	function itemsHtml(items) {
		const list = Array.isArray(items) ? items : [];
		const api = cardApi();
		if (!api) return "";
		let out = "";
		for (let i = 0; i < list.length; i += 1) {
			out += api.html(list[i]);
		}
		return out;
	}

	function viewAllHtml(config, payload) {
		const total = Number(payload && payload.total);
		const limit = Number(payload && payload.limit);
		if (!Number.isFinite(total) || !Number.isFinite(limit) || total <= limit) return "";
		const href = String(
			(payload && payload.view_all_href) || config.viewAllHref || ""
		).trim();
		if (!href) return "";
		const testId = String(config.sectionTestId || "pp2-queue-section") + "-view-all";
		return (
			'<div class="pp2-planning-home-queue__view-all">' +
			'<a href="' +
			esc(href) +
			'" class="pp2-planning-home-queue__view-all-link" data-testid="' +
			esc(testId) +
			'">' +
			esc(__("View all")) +
			"</a></div>"
		);
	}

	function html(config, payload) {
		const cfg = config || {};
		const data = payload || {};
		const title = String(cfg.title || "").trim();
		const sectionTestId = String(cfg.sectionTestId || "pp2-queue-section").trim();
		const items = Array.isArray(data.items) ? data.items : [];
		const emptyMessage = String(cfg.emptyMessage || "").trim();
		let bodyHtml = "";
		if (items.length) {
			bodyHtml =
				'<div class="pp2-planning-home-queue__items">' + itemsHtml(items) + "</div>" + viewAllHtml(cfg, data);
		} else if (emptyMessage) {
			const empty = emptyApi();
			bodyHtml = empty ? empty.html({ message: emptyMessage }) : "";
		}
		return (
			'<section class="pp2-planning-home-queue" data-testid="' +
			esc(sectionTestId) +
			'">' +
			(title
				? '<header class="pp2-planning-home-queue__header"><h3 class="pp2-planning-home-queue__title">' +
					esc(title) +
					"</h3></header>"
				: "") +
			'<div class="pp2-planning-home-queue__body">' +
			bodyHtml +
			"</div></section>"
		);
	}

	function render(host, config, payload) {
		if (!host) return;
		host.innerHTML = html(config, payload);
		const card = cardApi();
		if (!card || typeof card.bindActions !== "function") return;
		if (typeof config.onOpen !== "function" && typeof config.onSecondary !== "function") return;
		const resolveItem = function (itemId) {
			const items = (payload && payload.items) || [];
			for (let i = 0; i < items.length; i += 1) {
				if (String(items[i].id || "") === String(itemId || "")) {
					return items[i];
				}
			}
			return { id: itemId };
		};
		card.bindActions(host, {
			onPrimary: function (ctx) {
				const itemId = ctx && ctx.id ? ctx.id : "";
				if (typeof config.onOpen === "function") {
					config.onOpen(resolveItem(itemId));
				}
			},
			onSecondary: function (ctx) {
				const itemId = ctx && ctx.id ? ctx.id : "";
				const actionIndex = Number(ctx && ctx.actionIndex);
				const item = resolveItem(itemId);
				const secondaryActions = Array.isArray(item.secondary_actions) ? item.secondary_actions : [];
				const selectedSecondary =
					actionIndex >= 0 && actionIndex < secondaryActions.length ? secondaryActions[actionIndex] : null;
				if (typeof config.onSecondary === "function") {
					config.onSecondary(item, selectedSecondary || null);
				}
			},
		});
	}

	function fetchAndRender(host, config) {
		if (!host || !config || !config.apiMethod) return;
		const token = (fetchTokens.get(host) || 0) + 1;
		fetchTokens.set(host, token);
		render(host, config, { total: 0, limit: 5, items: [] });
		frappe.call({
			method: config.apiMethod,
			callback: function (response) {
				const latestToken = fetchTokens.get(host);
				if (token !== latestToken) return;
				const message = response && response.message ? response.message : {};
				if (message && message.ok) {
					render(host, config, message);
					return;
				}
				render(host, config, { total: 0, limit: 5, items: [] });
			},
			error: function () {
				if (token !== fetchTokens.get(host)) return;
				render(host, config, { total: 0, limit: 5, items: [] });
			},
		});
	}

	kentender_procurement.PlanningHomeQueueSection = {
		html: html,
		render: render,
		fetchAndRender: fetchAndRender,
	};
})();
