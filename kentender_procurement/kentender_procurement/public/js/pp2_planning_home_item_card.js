/**
 * P5C-003 — Planning Home queue item card (reset addendum §7.1).
 */
(function () {
	frappe.provide("kentender_procurement");

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function html(item) {
		const it = item || {};
		const title = String(it.title || "").trim();
		const subtitle = String(it.subtitle || "").trim();
		const nextAction = String(it.next_action_label || "").trim();
		const primary = it.primary_action || {};
		const primaryLabel = String(primary.label || __("Open")).trim() || __("Open");
		const secondaryActions = Array.isArray(it.secondary_actions) ? it.secondary_actions : [];
		const secondary = secondaryActions.length ? secondaryActions[0] || {} : null;
		const secondaryLabel = secondary
			? String(secondary.label || __("Open")).trim() || __("Open")
			: "";
		const nextLine = nextAction
			? __("Next: {0}", [nextAction])
			: "";
		return (
			'<article class="pp2-home-item-card" data-testid="pp2-home-item-card"' +
			(it.id ? ' data-pp2-home-item-id="' + esc(it.id) + '"' : "") +
			">" +
			'<div class="pp2-home-item-card__title">' +
			esc(title) +
			"</div>" +
			(subtitle
				? '<div class="pp2-home-item-card__subtitle text-muted">' + esc(subtitle) + "</div>"
				: "") +
			(nextLine
				? '<div class="pp2-home-item-card__next text-muted">' + esc(nextLine) + "</div>"
				: "") +
			'<div class="pp2-home-item-card__actions">' +
			'<button type="button" class="btn btn-primary btn-sm pp2-home-item-card__primary"' +
			' data-testid="pp2-home-primary-action">' +
			esc(primaryLabel) +
			"</button>" +
			(secondary
				? '<button type="button" class="btn btn-default btn-sm pp2-home-item-card__secondary"' +
					' data-testid="pp2-home-secondary-action" data-pp2-action-index="0">' +
					esc(secondaryLabel) +
					"</button>"
				: "") +
			"</div>" +
			"</article>"
		);
	}

	function bindActions(host, handlers) {
		const root = host && host.nodeType === 1 ? host : null;
		if (!root) return;
		const onPrimary = typeof handlers === "function" ? handlers : handlers && handlers.onPrimary;
		const onSecondary = handlers && typeof handlers === "object" ? handlers.onSecondary : null;
		if (typeof onPrimary !== "function" && typeof onSecondary !== "function") return;
		const primaryButtons = root.querySelectorAll('[data-testid="pp2-home-primary-action"]');
		for (let i = 0; i < primaryButtons.length; i += 1) {
			const btn = primaryButtons[i];
			const card = btn.closest('[data-testid="pp2-home-item-card"]');
			const itemId = card ? card.getAttribute("data-pp2-home-item-id") : "";
			btn.addEventListener("click", function (event) {
				event.preventDefault();
				if (typeof onPrimary === "function") {
					onPrimary({ id: itemId, card: card });
				}
			});
		}
		const secondaryButtons = root.querySelectorAll('[data-testid="pp2-home-secondary-action"]');
		for (let j = 0; j < secondaryButtons.length; j += 1) {
			const btn = secondaryButtons[j];
			const card = btn.closest('[data-testid="pp2-home-item-card"]');
			const itemId = card ? card.getAttribute("data-pp2-home-item-id") : "";
			const actionIndex = Number(btn.getAttribute("data-pp2-action-index") || 0);
			btn.addEventListener("click", function (event) {
				event.preventDefault();
				if (typeof onSecondary === "function") {
					onSecondary({ id: itemId, card: card, actionIndex: Number.isFinite(actionIndex) ? actionIndex : 0 });
				}
			});
		}
	}

	kentender_procurement.PlanningHomeItemCard = {
		html: html,
		bindActions: bindActions,
	};
})();
