/**
 * P5B-005 — Shared Planning blocker summary (none / single / multiple).
 */
(function () {
	frappe.provide("kentender_procurement");

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function blockerLabel(blocker) {
		if (blocker == null) return "";
		if (typeof blocker === "string") return String(blocker).trim();
		return String(blocker.label || blocker.message || "").trim();
	}

	function normalizeBlockers(opts) {
		const o = opts || {};
		const raw = Array.isArray(o.blockers) ? o.blockers : [];
		const labels = [];
		for (let i = 0; i < raw.length; i += 1) {
			const label = blockerLabel(raw[i]);
			if (label) labels.push({ label: label, action: raw[i] && raw[i].action ? raw[i].action : null });
		}
		if (labels.length) return labels;
		const count = Number(o.blocker_count || 0);
		if (!count || count < 1) return [];
		if (count === 1) {
			return [{ label: __("1 blocker"), action: null }];
		}
		for (let j = 0; j < count; j += 1) {
			labels.push({ label: __("Blocker {0}", [j + 1]), action: null });
		}
		return labels;
	}

	function resolveState(blockers) {
		const list = Array.isArray(blockers) ? blockers : [];
		if (!list.length) return "none";
		if (list.length === 1) return "single";
		return "multiple";
	}

	function itemActionHtml(action) {
		const a = action || {};
		const label = String(a.label || "").trim();
		if (!label) return "";
		return (
			' <button type="button" class="btn btn-default btn-xs pp2-blocker-summary__action"' +
			' data-testid="pp2-blocker-summary-action">' +
			esc(label) +
			"</button>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const blockers = normalizeBlockers(o);
		const state = resolveState(blockers);
		let body =
			'<div class="pp2-blocker-summary" data-testid="pp2-blocker-summary" data-blocker-state="' +
			esc(state) +
			'">';
		if (state === "none") {
			body +=
				'<span class="pp2-blocker-summary__empty text-muted" data-testid="pp2-blocker-summary-empty">' +
				esc(__("No blockers")) +
				"</span>";
		} else if (state === "single") {
			const item = blockers[0] || {};
			body +=
				'<span class="pp2-blocker-summary__item" data-testid="pp2-blocker-summary-item">' +
				esc(item.label) +
				itemActionHtml(item.action) +
				"</span>";
		} else {
			body += '<ul class="pp2-blocker-summary__list mb-0 ps-3">';
			for (let i = 0; i < blockers.length; i += 1) {
				const item = blockers[i] || {};
				body +=
					'<li class="pp2-blocker-summary__item" data-testid="pp2-blocker-summary-item">' +
					esc(item.label) +
					itemActionHtml(item.action) +
					"</li>";
			}
			body += "</ul>";
		}
		body += "</div>";
		return body;
	}

	function bindActions(host) {
		if (!host) return;
		const buttons = host.querySelectorAll('[data-testid="pp2-blocker-summary-action"]');
		for (let i = 0; i < buttons.length; i += 1) {
			const button = buttons[i];
			if (button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") {
					event.preventDefault();
				}
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		target.innerHTML = html(opts || {});
		bindActions(target);
	}

	kentender_procurement.PlanningBlockerSummary = {
		normalizeBlockers: normalizeBlockers,
		resolveState: resolveState,
		html: html,
		render: render,
		bindActions: bindActions,
	};
})();
