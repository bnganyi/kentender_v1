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

	function actionTestIdAttr(testId, fallback) {
		const value = String(testId || "").trim();
		if (!value) return fallback;
		if (value === "pp2-include-in-plan-button") return ' data-testid="pp2-include-in-plan-button"';
		if (value === "pp2-view-demand-button") return ' data-testid="pp2-view-demand-button"';
		if (value === "pp2-create-package-next-action") return ' data-testid="pp2-create-package-next-action"';
		if (value === "pp2-back-to-approved-demands") return ' data-testid="pp2-back-to-approved-demands"';
		return ' data-testid="' + esc(value) + '"';
	}

	function evidenceTestIdAttr(summary) {
		const s = summary || {};
		const value = String(s.evidence_testid || "").trim();
		if (value === "pp2-view-demand-evidence") return ' data-testid="pp2-view-demand-evidence"';
		if (!value) return ' data-testid="pp2-view-evidence-button"';
		return ' data-testid="' + esc(value) + '"';
	}

	function actionsHtml(summary) {
		const s = summary || {};
		let html = "";
		const primary = s.primary_action || null;
		if (primary && primary.label) {
			html +=
				'<button type="button" class="btn btn-primary btn-sm pp2-selected-summary-panel__primary"' +
				actionTestIdAttr(primary.testid, ' data-testid="pp2-selected-summary-primary-action"') +
				' data-pp2-summary-primary-action="' +
				esc(primary.action || "") +
				'">' +
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
				actionTestIdAttr(action.testid, ' data-testid="pp2-selected-summary-secondary-action"') +
				' data-pp2-summary-secondary-index="' +
				String(i) +
				'">' +
				esc(action.label) +
				"</button>";
		}
		if (s.show_evidence_action !== false) {
			html +=
				'<button type="button" class="btn btn-default btn-sm pp2-selected-summary-panel__evidence"' +
				evidenceTestIdAttr(summary) +
				esc(__("View Evidence")) +
				"</button>";
		}
		if (!html) return "";
		return '<div class="pp2-selected-summary-panel__actions">' + html + "</div>";
	}

	function includeAlertHtml(summary) {
		const s = summary || {};
		const message = String(s.include_alert_message || "").trim();
		if (!message) return "";
		return (
			'<div class="pp2-selected-summary-panel__include-alert alert alert-warning mt-2 mb-0 py-2 px-2" data-testid="pp2-approved-demand-include-alert">' +
			esc(message) +
			"</div>"
		);
	}

	function includeSuccessHtml(summary) {
		const s = summary || {};
		const message = String(s.include_success_message || "").trim();
		const nextAction = String(s.next_action_label || "").trim();
		return (
			'<section class="pp2-include-plan-success" data-testid="pp2-include-plan-success">' +
			'<div class="pp2-include-plan-success__message" data-testid="pp2-include-plan-success-message">' +
			esc(message || __("Demand added to the procurement plan.")) +
			"</div>" +
			'<div class="pp2-include-plan-success__next small text-muted mt-1 mb-2" data-testid="pp2-include-plan-success-next">' +
			esc(__("Next")) +
			": " +
			esc(nextAction || __("Create package.")) +
			"</div>" +
			actionsHtml(summary) +
			"</section>"
		);
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
		if (summary && summary.include_success) {
			return (
				'<div data-testid="pp2-approved-demand-summary">' +
				includeSuccessHtml(summary) +
				"</div>"
			);
		}
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
		body += actionsHtml(summary);
		if (String(summary.context_slug || "").trim() === "approved-demands") {
			body += includeAlertHtml(summary);
		}
		body += "</section>";
		if (String(summary.context_slug || "").trim() === "approved-demands") {
			return '<div data-testid="pp2-approved-demand-summary">' + body + "</div>";
		}
		return body;
	}

	function bindActions(host, summary, opts) {
		if (!host) return;
		const o = opts || {};
		const primaryBtn = host.querySelector("[data-pp2-summary-primary-action]");
		if (primaryBtn && primaryBtn.getAttribute("data-bound") !== "1") {
			primaryBtn.setAttribute("data-bound", "1");
			primaryBtn.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") {
					event.preventDefault();
				}
				if (typeof o.onPrimaryAction === "function") {
					o.onPrimaryAction(summary && summary.primary_action ? summary.primary_action : null, summary || {});
				}
			});
		}
		const secondaryBtns = host.querySelectorAll("[data-pp2-summary-secondary-index]");
		for (let i = 0; i < secondaryBtns.length; i += 1) {
			const button = secondaryBtns[i];
			if (!button || button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") {
					event.preventDefault();
				}
				const idx = Number(button.getAttribute("data-pp2-summary-secondary-index") || -1);
				const secondaryActions = Array.isArray(summary && summary.secondary_actions)
					? summary.secondary_actions
					: [];
				const action = idx >= 0 ? secondaryActions[idx] || null : null;
				if (typeof o.onSecondaryAction === "function") {
					o.onSecondaryAction(action, summary || {});
				}
			});
		}
		const evidenceBtn = host.querySelector('[data-testid="pp2-view-evidence-button"]');
		const demandEvidenceBtn = host.querySelector('[data-testid="pp2-view-demand-evidence"]');
		const evidenceButtons = [evidenceBtn, demandEvidenceBtn];
		for (let i = 0; i < evidenceButtons.length; i += 1) {
			const button = evidenceButtons[i];
			if (!button || button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function (event) {
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
		bindActions(target, o.summary, o);
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
