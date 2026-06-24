/**
 * P2-007 — Shared PP3 SelectedWorkSummary component.
 */
(function () {
	frappe.provide("kentender_procurement");

	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-selected-work-summary"',
		'data-testid="pp3-primary-action"',
		'data-testid="pp3-secondary-actions"',
		'data-testid="pp3-view-evidence-button"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* static literals kept for G2 selector guard */
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function normalizeSummary(summary) {
		const s = summary || {};
		return {
			title: String(s.title || "").trim(),
			stateLabel: String(s.status_label || s.state_label || s.stateLabel || "").trim(),
			facts: String(s.key_facts || s.subtitle || s.facts || "").trim(),
			nextAction: String(s.next_action_label || s.nextAction || "").trim(),
			includeSuccess: s.include_success === true || s.includeSuccess === true,
			includeSuccessMessage: String(
				s.include_success_message || s.includeSuccessMessage || "",
			).trim(),
			createPackageSuccess:
				s.create_package_success === true || s.createPackageSuccess === true,
			createPackageSuccessMessage: String(
				s.create_package_success_message || s.createPackageSuccessMessage || "",
			).trim(),
			underlyingObjectType: String(
				s.underlying_object_type || s.underlyingObjectType || "",
			).trim(),
			underlyingObjectCode: String(
				s.underlying_object_code || s.underlyingObjectCode || "",
			).trim(),
			packageCode: String(s.package_code || s.packageCode || "").trim(),
			blockers: Array.isArray(s.blockers) ? s.blockers : [],
			primaryAction:
				s.primary_action && s.primary_action.label
					? s.primary_action
					: s.primaryAction && s.primaryAction.label
						? s.primaryAction
						: null,
			secondaryActions: Array.isArray(s.secondary_actions)
				? s.secondary_actions
				: Array.isArray(s.secondaryActions)
					? s.secondaryActions
					: [],
			showEvidenceAction:
				s.show_evidence_action !== false && s.showEvidenceAction !== false,
		};
	}

	function summaryFromWorkItem(item) {
		const it = item || {};
		return normalizeSummary({
			title: it.title,
			state_label: it.state_label,
			subtitle: it.subtitle,
			next_action_label: it.next_action_label,
			underlying_object_type: it.underlying_object_type,
			underlying_object_code: it.underlying_object_code,
			package_code: it.package_code,
			blockers: it.blockers,
			primary_action: it.primary_action,
			secondary_actions: it.secondary_actions,
			show_evidence_action: it.show_evidence_action,
		});
	}

	function blockersHtml(summary) {
		const blockers = Array.isArray(summary.blockers) ? summary.blockers : [];
		if (!blockers.length) {
			return (
				'<div class="pp3-selected-work-summary__blockers text-muted small mb-2">' +
				esc(__("Blockers")) +
				": " +
				esc(__("No blockers")) +
				"</div>"
			);
		}
		const labels = [];
		for (let i = 0; i < blockers.length; i += 1) {
			const value = blockers[i];
			const label = String(value && value.label ? value.label : value || "").trim();
			if (label) labels.push(label);
		}
		const display = labels.length ? labels.join(", ") : __("Has blockers");
		return (
			'<div class="pp3-selected-work-summary__blockers text-muted small mb-2">' +
			esc(__("Blockers")) +
			": " +
			esc(display) +
			"</div>"
		);
	}

	function primaryActionHtml(summary) {
		const action = summary.primaryAction;
		if (!action || !action.label) return "";
		return (
			'<button type="button" class="btn btn-primary btn-sm pp3-selected-work-summary__primary" data-testid="pp3-primary-action" data-pp3-summary-primary-action="' +
			esc(action.action || "") +
			'">' +
			esc(action.label) +
			"</button>"
		);
	}

	function secondaryActionTestIdAttr(action) {
		const testId = String((action && action.testid) || "").trim();
		if (testId === "pp3-back-to-workbench") return ' data-testid="pp3-back-to-workbench"';
		if (testId) return ' data-testid="' + esc(testId) + '"';
		return "";
	}

	function successActionsHtml(summary, primaryTestId) {
		let html = "";
		const primary = summary.primaryAction;
		if (primary && primary.label) {
			const testId = String(primary.testid || "").trim();
			let testIdAttr = ' data-testid="pp3-primary-action"';
			if (testId === "pp2-create-package-next-action") {
				testIdAttr = ' data-testid="pp2-create-package-next-action"';
			} else if (testId === "pp2-open-package-next-action") {
				testIdAttr = ' data-testid="pp2-open-package-next-action"';
			} else if (primaryTestId) {
				testIdAttr = ' data-testid="' + esc(primaryTestId) + '"';
			}
			html +=
				'<button type="button" class="btn btn-primary btn-sm pp3-selected-work-summary__primary"' +
				testIdAttr +
				' data-pp3-summary-primary-action="' +
				esc(primary.action || "") +
				'">' +
				esc(primary.label) +
				"</button>";
		}
		const secondary = Array.isArray(summary.secondaryActions) ? summary.secondaryActions : [];
		let secondaryButtons = "";
		for (let i = 0; i < secondary.length; i += 1) {
			const action = secondary[i] || {};
			const label = String(action.label || "").trim();
			if (!label) continue;
			secondaryButtons +=
				'<button type="button" class="btn btn-default btn-sm pp3-selected-work-summary__secondary"' +
				secondaryActionTestIdAttr(action) +
				' data-pp3-summary-secondary-index="' +
				String(i) +
				'">' +
				esc(label) +
				"</button>";
		}
		if (secondaryButtons) {
			html +=
				'<div class="pp3-selected-work-summary__secondary-actions" data-testid="pp3-secondary-actions">' +
				secondaryButtons +
				"</div>";
		}
		return html ? '<div class="pp3-selected-work-summary__actions">' + html + "</div>" : "";
	}

	function includeSuccessActionsHtml(summary) {
		return successActionsHtml(summary, "");
	}

	function createPackageSuccessHtml(summary) {
		const message = String(summary.createPackageSuccessMessage || summary.title || "").trim();
		const nextAction = String(summary.nextAction || "").trim();
		return (
			'<section class="pp3-selected-work-summary pp2-create-package-success" data-testid="pp3-selected-work-summary">' +
			'<div class="pp2-create-package-success" data-testid="pp2-create-package-success">' +
			'<div class="pp2-create-package-success__message" data-testid="pp2-create-package-success-message">' +
			esc(message || __("Package created.")) +
			"</div>" +
			'<div class="pp2-create-package-success__next small text-muted mt-1 mb-2" data-testid="pp2-create-package-success-next">' +
			esc(__("Next")) +
			": " +
			esc(nextAction || __("Complete readiness and submit for review.")) +
			"</div>" +
			successActionsHtml(summary, "pp2-open-package-next-action") +
			"</div></section>"
		);
	}

	function includeSuccessHtml(summary) {
		const message = String(summary.includeSuccessMessage || summary.title || "").trim();
		const nextAction = String(summary.nextAction || "").trim();
		return (
			'<section class="pp3-selected-work-summary pp2-include-plan-success" data-testid="pp3-selected-work-summary">' +
			'<div class="pp2-include-plan-success" data-testid="pp2-include-plan-success">' +
			'<div class="pp2-include-plan-success__message" data-testid="pp2-include-plan-success-message">' +
			esc(message || __("Demand added to the active procurement plan.")) +
			"</div>" +
			'<div class="pp2-include-plan-success__next small text-muted mt-1 mb-2" data-testid="pp2-include-plan-success-next">' +
			esc(__("Next")) +
			": " +
			esc(nextAction || __("Create package.")) +
			"</div>" +
			includeSuccessActionsHtml(summary) +
			"</div></section>"
		);
	}

	function secondaryActionsHtml(summary) {
		const actions = Array.isArray(summary.secondaryActions) ? summary.secondaryActions : [];
		let buttons = "";
		for (let i = 0; i < actions.length; i += 1) {
			const action = actions[i] || {};
			const label = String(action.label || "").trim();
			if (!label || String(action.action || "") === "open_evidence") continue;
			buttons +=
				'<button type="button" class="btn btn-default btn-sm pp3-selected-work-summary__secondary" data-pp3-summary-secondary-index="' +
				String(i) +
				'">' +
				esc(label) +
				"</button>";
		}
		if (!buttons) return "";
		return '<div class="pp3-selected-work-summary__secondary-actions" data-testid="pp3-secondary-actions">' + buttons + "</div>";
	}

	function evidenceActionHtml(summary) {
		if (!summary.showEvidenceAction) return "";
		return (
			'<button type="button" class="btn btn-default btn-sm pp3-selected-work-summary__evidence" data-testid="pp3-view-evidence-button">' +
			esc(__("View Evidence")) +
			"</button>"
		);
	}

	function idleHtml() {
		return (
			'<section class="pp3-selected-work-summary is-idle" data-testid="pp3-selected-work-summary">' +
			'<p class="text-muted small mb-0">' +
			esc(__("Select an item to view summary.")) +
			"</p></section>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const summary = normalizeSummary(o.summary || {});
		if (summary.createPackageSuccess) {
			return createPackageSuccessHtml(summary);
		}
		if (summary.includeSuccess) {
			return includeSuccessHtml(summary);
		}
		if (!summary.title) return idleHtml();
		let body =
			'<section class="pp3-selected-work-summary" data-testid="pp3-selected-work-summary">' +
			'<h3 class="h6 mb-2">' +
			esc(summary.title) +
			"</h3>";
		if (summary.stateLabel) {
			body +=
				'<div class="text-muted small mb-1">' +
				esc(__("State")) +
				": " +
				esc(summary.stateLabel) +
				"</div>";
		}
		if (summary.facts) {
			body += '<div class="text-muted small mb-1">' + esc(summary.facts) + "</div>";
		}
		body += blockersHtml(summary);
		if (summary.nextAction) {
			body +=
				'<div class="small mb-2">' +
				esc(__("Next")) +
				": " +
				esc(summary.nextAction) +
				"</div>";
		}
		body += '<div class="pp3-selected-work-summary__actions">';
		body += primaryActionHtml(summary);
		body += secondaryActionsHtml(summary);
		body += evidenceActionHtml(summary);
		body += "</div></section>";
		return body;
	}

	function bindActions(host, summary, opts) {
		const o = opts || {};
		const primary = host.querySelector("[data-pp3-summary-primary-action]");
		if (primary && primary.getAttribute("data-bound") !== "1") {
			primary.setAttribute("data-bound", "1");
			primary.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") event.preventDefault();
				if (typeof o.onPrimaryAction === "function") {
					o.onPrimaryAction(summary.primaryAction || null, summary);
				}
			});
		}
		const secondaries = host.querySelectorAll("[data-pp3-summary-secondary-index]");
		for (let i = 0; i < secondaries.length; i += 1) {
			const button = secondaries[i];
			if (!button || button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") event.preventDefault();
				const index = Number(button.getAttribute("data-pp3-summary-secondary-index") || -1);
				const action = index >= 0 ? summary.secondaryActions[index] || null : null;
				if (typeof o.onSecondaryAction === "function") {
					o.onSecondaryAction(action, summary);
				}
			});
		}
		const evidence = host.querySelector('[data-testid="pp3-view-evidence-button"]');
		if (evidence && evidence.getAttribute("data-bound") !== "1") {
			evidence.setAttribute("data-bound", "1");
			evidence.addEventListener("click", function (event) {
				if (event && typeof event.preventDefault === "function") event.preventDefault();
				if (typeof o.onEvidenceAction === "function") {
					o.onEvidenceAction(summary);
				}
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const o = opts || {};
		const summary = normalizeSummary(o.summary || {});
		target.innerHTML = html({ summary: summary });
		bindActions(target, summary, o);
	}

	function renderIdle(host) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		target.innerHTML = idleHtml();
	}

	kentender_procurement.PlanningWorkbenchSelectedSummary = {
		html: html,
		idleHtml: idleHtml,
		render: render,
		renderIdle: renderIdle,
		summaryFromWorkItem: summaryFromWorkItem,
	};
})();
