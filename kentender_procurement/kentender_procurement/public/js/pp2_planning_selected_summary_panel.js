/**
 * P5B-004 — Shared Planning selected summary panel (right panel).
 */
(function () {
	frappe.provide("kentender_procurement");

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function statusHtml(statusLabel) {
		const label = String(statusLabel || "").trim();
		if (!label) return esc("—");
		const badgeApi =
			kentender_procurement &&
			kentender_procurement.PlanningStatusBadge &&
			typeof kentender_procurement.PlanningStatusBadge.html === "function"
				? kentender_procurement.PlanningStatusBadge
				: null;
		if (badgeApi) {
			return badgeApi.html(label, { context: "package", scope: "header" });
		}
		return esc(label);
	}

	function blockersHtml(summary) {
		const s = summary || {};
		const blockerApi =
			kentender_procurement &&
			kentender_procurement.PlanningBlockerSummary &&
			typeof kentender_procurement.PlanningBlockerSummary.html === "function"
				? kentender_procurement.PlanningBlockerSummary
				: null;
		const inner = blockerApi
			? blockerApi.html({ blockers: s.blockers, blocker_count: s.blocker_count })
			: esc(__("No blockers"));
		return (
			'<div class="pp2-selected-summary-panel__blockers text-muted small mb-1" data-testid="pp2-selected-summary-blockers">' +
			esc(__("Blockers")) +
			": " +
			inner +
			"</div>"
		);
	}

	function summaryFromWorkItem(item) {
		const it = item || {};
		const blockers = Array.isArray(it.blockers) ? it.blockers : [];
		const count = blockers.length ? blockers.length : Number(it.blocker_count || 0);
		return {
			title: String(it.title || "").trim(),
			status_label: String(it.status_label || "").trim(),
			key_facts: String(it.subtitle || it.key_facts || "").trim(),
			funding_label: String(it.funding_label || "").trim(),
			blockers: blockers,
			blocker_count: count,
			next_action_label: String(it.next_action_label || "").trim(),
			primary_action: it.primary_action || null,
			secondary_actions: Array.isArray(it.secondary_actions) ? it.secondary_actions : [],
			show_evidence_action: it.show_evidence_action !== false,
		};
	}

	function actionsHtml(summary) {
		const s = summary || {};
		let html = "";
		const primary = s.primary_action || null;
		if (primary && primary.label) {
			html +=
				'<button type="button" class="btn btn-primary btn-sm pp2-selected-summary-panel__primary"' +
				' data-testid="pp2-selected-summary-primary-action">' +
				esc(primary.label) +
				"</button>";
		}
		const secondary = Array.isArray(s.secondary_actions) ? s.secondary_actions : [];
		for (let i = 0; i < secondary.length; i += 1) {
			const action = secondary[i] || {};
			if (!action.label) continue;
			if (String(action.action || "") === "open_evidence") continue;
			html +=
				'<button type="button" class="btn btn-default btn-sm pp2-selected-summary-panel__secondary"' +
				' data-testid="pp2-selected-summary-secondary-action">' +
				esc(action.label) +
				"</button>";
		}
		if (s.show_evidence_action !== false) {
			html +=
				'<button type="button" class="btn btn-default btn-sm pp2-selected-summary-panel__evidence"' +
				' data-testid="pp2-view-evidence-button">' +
				esc(__("View Evidence")) +
				"</button>";
		}
		if (!html) return "";
		return '<div class="pp2-selected-summary-panel__actions">' + html + "</div>";
	}

	function idleHtml(opts) {
		const o = opts || {};
		const message = String(o.idleMessage || __("Select an item to view summary.")).trim();
		return (
			'<section class="pp2-selected-summary-panel is-idle" data-testid="pp2-selected-summary-panel">' +
			'<p class="text-muted small mb-0" data-testid="pp2-selected-summary-idle">' +
			esc(message) +
			"</p></section>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const summary = o.summary || {};
		const title = String(summary.title || "").trim();
		const keyFacts = String(summary.key_facts || "").trim();
		const funding = String(summary.funding_label || "").trim();
		const nextAction = String(summary.next_action_label || "").trim();
		let body =
			'<section class="pp2-selected-summary-panel" data-testid="pp2-selected-summary-panel">' +
			'<h3 class="h6 pp2-selected-summary-panel__title mb-2" data-testid="pp2-selected-summary-title">' +
			esc(title) +
			"</h3>" +
			'<div class="pp2-selected-summary-panel__status small mb-1" data-testid="pp2-selected-summary-status">' +
			esc(__("Status")) +
			": " +
			statusHtml(summary.status_label) +
			"</div>";
		if (keyFacts) {
			body +=
				'<div class="pp2-selected-summary-panel__facts text-muted small mb-1" data-testid="pp2-selected-summary-facts">' +
				esc(keyFacts) +
				"</div>";
		}
		if (funding) {
			body +=
				'<div class="pp2-selected-summary-panel__funding text-muted small mb-1" data-testid="pp2-selected-summary-funding">' +
				esc(__("Funding")) +
				": " +
				esc(funding) +
				"</div>";
		}
		body += blockersHtml(summary);
		if (nextAction) {
			body +=
				'<div class="pp2-selected-summary-panel__next-action small mb-2" data-testid="pp2-selected-summary-next-action">' +
				esc(__("Next")) +
				": " +
				esc(nextAction) +
				"</div>";
		}
		body += actionsHtml(summary) + "</section>";
		return body;
	}

	function bindActions(host, summary) {
		if (!host) return;
		const evidenceBtn = host.querySelector('[data-testid="pp2-view-evidence-button"]');
		if (evidenceBtn && evidenceBtn.getAttribute("data-bound") !== "1") {
			evidenceBtn.setAttribute("data-bound", "1");
			evidenceBtn.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") {
					event.preventDefault();
				}
				const drawerApi =
					kentender_procurement &&
					kentender_procurement.PlanningEvidenceDrawer &&
					typeof kentender_procurement.PlanningEvidenceDrawer.open === "function"
						? kentender_procurement.PlanningEvidenceDrawer
						: null;
				const s = summary || {};
				if (drawerApi) {
					drawerApi.open({ title: String(s.title || "").trim() });
				}
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const o = opts || {};
		if (!o.summary || !String(o.summary.title || "").trim()) {
			renderIdle(target, o);
			return;
		}
		target.innerHTML = html(o);
		bindActions(target, o.summary);
		const blockerApi =
			kentender_procurement &&
			kentender_procurement.PlanningBlockerSummary &&
			typeof kentender_procurement.PlanningBlockerSummary.bindActions === "function"
				? kentender_procurement.PlanningBlockerSummary
				: null;
		if (blockerApi) {
			const blockerHost = target.querySelector('[data-testid="pp2-blocker-summary"]');
			if (blockerHost) blockerApi.bindActions(blockerHost);
		}
	}

	function renderIdle(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		target.innerHTML = idleHtml(opts || {});
	}

	kentender_procurement.PlanningSelectedSummaryPanel = {
		html: html,
		idleHtml: idleHtml,
		render: render,
		renderIdle: renderIdle,
		summaryFromWorkItem: summaryFromWorkItem,
	};
})();
