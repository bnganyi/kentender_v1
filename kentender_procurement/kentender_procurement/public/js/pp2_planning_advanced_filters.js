/**
 * P5B-007 — Shared Planning advanced filters (collapsed by default).
 */
(function () {
	frappe.provide("kentender_procurement");

	const FILTER_SURFACES = {
		"approved-demands": true,
		plans: true,
		packages: true,
		releases: true,
	};

	const FILTER_FIELDS = {
		"approved-demands": [
			{ id: "category", label: __("Category") },
			{ id: "funding-status", label: __("Funding status") },
			{ id: "fiscal-year", label: __("Fiscal year") },
			{ id: "procuring-entity", label: __("Procuring entity") },
			{ id: "planning-status", label: __("Planning status") },
		],
		plans: [
			{ id: "fiscal-year", label: __("Fiscal year") },
			{ id: "procuring-entity", label: __("Procuring entity") },
			{ id: "status", label: __("Status") },
		],
		packages: [
			{ id: "fiscal-year", label: __("Fiscal year") },
			{ id: "procuring-entity", label: __("Procuring entity") },
			{ id: "method", label: __("Method") },
			{ id: "category", label: __("Category") },
			{ id: "risk", label: __("Risk") },
			{ id: "emergency", label: __("Emergency") },
			{ id: "readiness-status", label: __("Readiness status") },
			{ id: "handoff-status", label: __("Handoff status") },
			{ id: "approval-status", label: __("Approval status") },
			{ id: "draft-packages", label: __("Draft Packages") },
			{ id: "in-review-packages", label: __("In Review Packages") },
			{ id: "high-risk-packages", label: __("High-Risk Packages") },
			{ id: "emergency-packages", label: __("Emergency Packages") },
			{ id: "pending-approval", label: __("Pending Approval") },
			{ id: "high-risk-escalation", label: __("High-Risk Requiring Escalation") },
			{ id: "method-override", label: __("Method Override Cases") },
			{ id: "approved-not-handed-off", label: __("Approved Not Yet Handed Off") },
			{ id: "procurement-method", label: __("Procurement Method") },
			{ id: "procurement-category", label: __("Procurement Category") },
		],
		releases: [
			{ id: "fiscal-year", label: __("Fiscal year") },
			{ id: "procuring-entity", label: __("Procuring entity") },
			{ id: "method", label: __("Method") },
			{ id: "tender-status", label: __("Tender status") },
			{ id: "handoff-status", label: __("Handoff status") },
		],
	};

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function isAvailableForSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return Boolean(FILTER_SURFACES[key]);
	}

	function filtersForSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return FILTER_FIELDS[key] ? FILTER_FIELDS[key].slice() : [];
	}

	function fieldHtml(field) {
		const f = field || {};
		const id = String(f.id || "").trim();
		const label = String(f.label || id).trim();
		return (
			'<div class="pp2-advanced-filters__field" data-testid="pp2-advanced-filter-' +
			esc(id) +
			'">' +
			'<label class="pp2-advanced-filters__label text-muted small mb-0">' +
			esc(label) +
			"</label>" +
			'<select class="form-control input-sm pp2-advanced-filters__control" disabled aria-label="' +
			esc(label) +
			'">' +
			'<option value="">' +
			esc(__("Any")) +
			"</option>" +
			"</select>" +
			"</div>"
		);
	}

	function html(opts) {
		const o = opts || {};
		const slug = o.slug == null ? "" : String(o.slug);
		const fields = Array.isArray(o.fields) ? o.fields : filtersForSlug(slug);
		if (!fields.length) return "";
		let rows = "";
		for (let i = 0; i < fields.length; i += 1) {
			rows += fieldHtml(fields[i]);
		}
		return (
			'<details class="pp2-advanced-filters" data-testid="pp2-advanced-filters">' +
			'<summary class="pp2-advanced-filters__toggle" data-testid="pp2-advanced-filters-toggle">' +
			esc(__("Advanced Filters")) +
			"</summary>" +
			'<div class="pp2-advanced-filters__panel" data-testid="pp2-advanced-filters-panel">' +
			rows +
			"</div>" +
			"</details>"
		);
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const o = opts || {};
		const slug = o.slug == null ? "" : String(o.slug);
		if (!isAvailableForSlug(slug)) {
			target.innerHTML = "";
			return;
		}
		target.innerHTML = html(o);
	}

	function renderForSlug(host, slug) {
		render(host, { slug: slug });
	}

	kentender_procurement.PlanningAdvancedFilters = {
		FILTER_FIELDS: FILTER_FIELDS,
		isAvailableForSlug: isAvailableForSlug,
		filtersForSlug: filtersForSlug,
		html: html,
		render: render,
		renderForSlug: renderForSlug,
	};
})();
