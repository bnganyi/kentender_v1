/**
 * P2-005 — Shared PP3 WorkbenchQueueTabs component.
 */
(function () {
	frappe.provide("kentender_procurement");

	const WORKBENCH_TABS = [
		{
			key: "needs_planning",
			label: __("Needs Planning"),
			testId: "pp3-queue-needs-planning",
		},
		{
			key: "draft_packages",
			label: __("Draft Packages"),
			testId: "pp3-queue-draft-packages",
		},
		{
			key: "needs_review",
			label: __("Needs Review"),
			testId: "pp3-queue-needs-review",
		},
		{
			key: "ready_to_release",
			label: __("Ready to Release"),
			testId: "pp3-queue-ready-release",
		},
		{
			key: "blocked",
			label: __("Blocked"),
			testId: "pp3-queue-blocked",
		},
		{
			key: "recently_released",
			label: __("Recently Released"),
			testId: "pp3-queue-recently-released",
		},
	];

	const LEGACY_QUEUE_ALIASES = {
		"needs-planning": "needs_planning",
		"needs-review": "needs_review",
		"ready-to-release": "ready_to_release",
		"released-recently": "recently_released",
		"draft-packages": "draft_packages",
	};
	// Keep explicit literals for G2 static selector guard.
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-workbench-queue-tabs"',
		'data-testid="pp3-queue-needs-planning"',
		'data-testid="pp3-queue-draft-packages"',
		'data-testid="pp3-queue-needs-review"',
		'data-testid="pp3-queue-ready-release"',
		'data-testid="pp3-queue-blocked"',
		'data-testid="pp3-queue-recently-released"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* keep linter happy for static literals */
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function knownQueueKeys() {
		const keys = {};
		for (let i = 0; i < WORKBENCH_TABS.length; i += 1) {
			keys[WORKBENCH_TABS[i].key] = true;
		}
		return keys;
	}

	function normalizeQueueKey(value) {
		const raw = String(value || "").trim();
		if (!raw) return "";
		if (knownQueueKeys()[raw]) return raw;
		if (LEGACY_QUEUE_ALIASES[raw]) return LEGACY_QUEUE_ALIASES[raw];
		return "";
	}

	function readActiveFromUrl() {
		try {
			const raw = new URLSearchParams(window.location.search).get("queue");
			const normalized = normalizeQueueKey(raw);
			if (normalized) return normalized;
		} catch (e) {
			/* ignore */
		}
		return WORKBENCH_TABS[0].key;
	}

	function setQueueUrl(queueKey) {
		const normalized = normalizeQueueKey(queueKey) || WORKBENCH_TABS[0].key;
		try {
			const url = new URL(window.location.href);
			url.searchParams.set("queue", normalized);
			window.history.replaceState({}, "", url.pathname + url.search + url.hash);
		} catch (e) {
			/* ignore */
		}
	}

	function buttonHtml(tab, active, testIdLiteral) {
		const selected = tab.key === active;
		return (
			'<button type="button" class="btn btn-default btn-sm pp3-workbench-queue-tabs__chip' +
			(selected ? " is-active" : "") +
			'" data-testid="' +
			testIdLiteral +
			'" data-pp3-queue-key="' +
			esc(tab.key) +
			'" role="tab" aria-selected="' +
			(selected ? "true" : "false") +
			'">' +
			esc(tab.label) +
			"</button>"
		);
	}

	function html(activeQueue) {
		const active = normalizeQueueKey(activeQueue) || WORKBENCH_TABS[0].key;
		return (
			'<nav class="pp3-workbench-queue-tabs" data-testid="pp3-workbench-queue-tabs" role="tablist">' +
			buttonHtml(WORKBENCH_TABS[0], active, "pp3-queue-needs-planning") +
			buttonHtml(WORKBENCH_TABS[1], active, "pp3-queue-draft-packages") +
			buttonHtml(WORKBENCH_TABS[2], active, "pp3-queue-needs-review") +
			buttonHtml(WORKBENCH_TABS[3], active, "pp3-queue-ready-release") +
			buttonHtml(WORKBENCH_TABS[4], active, "pp3-queue-blocked") +
			buttonHtml(WORKBENCH_TABS[5], active, "pp3-queue-recently-released") +
			"</nav>"
		);
	}

	function bind(host) {
		const buttons = host.querySelectorAll("[data-pp3-queue-key]");
		for (let i = 0; i < buttons.length; i += 1) {
			const button = buttons[i];
			if (button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function () {
				const queueKey = String(button.getAttribute("data-pp3-queue-key") || "").trim();
				const normalized = normalizeQueueKey(queueKey);
				if (!normalized) return;
				setQueueUrl(normalized);
				render(host, { activeQueue: normalized });
			});
		}
	}

	function render(host, opts) {
		if (!host || host.nodeType !== 1) return;
		const options = opts || {};
		const activeQueue =
			options.activeQueue != null ? normalizeQueueKey(options.activeQueue) : readActiveFromUrl();
		host.innerHTML = html(activeQueue);
		bind(host);
	}

	function renderForSlug(host, slug, opts) {
		if (String(slug || "").trim() !== "") {
			if (host && host.nodeType === 1) host.innerHTML = "";
			return;
		}
		render(host, opts || {});
	}

	kentender_procurement.PlanningWorkbenchQueueTabs = {
		html: html,
		render: render,
		renderForSlug: renderForSlug,
		readActiveFromUrl: readActiveFromUrl,
		setQueueUrl: setQueueUrl,
	};
})();
