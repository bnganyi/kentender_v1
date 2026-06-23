/**
 * P5B-006 — Shared Planning empty state (surface + future queue copy).
 */
(function () {
	frappe.provide("kentender_procurement");

	const SURFACE_MESSAGES = {
		"": __("No items need your attention right now."),
		"approved-demands": __("No approved demands match this queue."),
		plans: __("No procurement plans match this queue."),
		packages: __("No packages match this queue."),
		releases: __("No released packages match this queue."),
	};

	const SURFACE_PURPOSE = {
		"": __("Convert approved demand into tender-ready procurement packages."),
		"approved-demands": __("Which approved demands can be planned now?"),
		plans: __("Which plan owns this procurement work?"),
		packages: __("Which packages need work, review, release, or follow-up?"),
		releases: __("Which packages have left Planning, and where did they go?"),
	};

	const HOME_QUEUE_MESSAGES = {
		needs_planning: __("No approved demands need planning."),
		draft_packages: __("No draft packages are waiting."),
		needs_review: __("No packages are waiting for review."),
		ready_to_release: __("No packages are ready for release."),
		released_recently: __("No packages have been released recently."),
		blocked: __("No planning blockers found."),
	};

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function messageForSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return SURFACE_MESSAGES[key] || SURFACE_MESSAGES[""];
	}

	function purposeForSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return SURFACE_PURPOSE[key] || SURFACE_PURPOSE[""];
	}

	function html(opts) {
		const o = opts || {};
		const message = String(o.message != null ? o.message : messageForSlug(o.slug)).trim();
		return (
			'<div class="pp2-empty-state" data-testid="pp2-empty-state">' +
			'<p class="text-muted small mb-0" data-testid="pp2-empty-state-message">' +
			esc(message) +
			"</p></div>"
		);
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		target.innerHTML = html(opts || {});
	}

	function renderForSlug(host, slug) {
		render(host, { slug: slug });
	}

	kentender_procurement.PlanningEmptyState = {
		SURFACE_MESSAGES: SURFACE_MESSAGES,
		SURFACE_PURPOSE: SURFACE_PURPOSE,
		HOME_QUEUE_MESSAGES: HOME_QUEUE_MESSAGES,
		messageForSlug: messageForSlug,
		purposeForSlug: purposeForSlug,
		html: html,
		render: render,
		renderForSlug: renderForSlug,
	};
})();
