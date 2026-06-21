/**
 * P5B-002 — Shared Planning queue tabs (compact chip bar, max six default chips).
 */
(function () {
	frappe.provide("kentender_procurement");

	const SURFACE_QUEUE_CONFIG = {
		"": {
			tabs: [
				{ id: "needs-planning", label: __("Needs Planning"), testId: "pp2-queue-tab-needs-planning" },
				{ id: "needs-review", label: __("Needs Review"), testId: "pp2-queue-tab-needs-review" },
				{ id: "ready-to-release", label: __("Ready to Release"), testId: "pp2-queue-tab-ready-to-release" },
				{
					id: "released-recently",
					label: __("Released Recently"),
					testId: "pp2-queue-tab-released-recently",
				},
				{ id: "blocked", label: __("Blocked"), testId: "pp2-queue-tab-blocked" },
			],
		},
		"approved-demands": {
			tabs: [
				{ id: "ready-to-plan", label: __("Ready to Plan"), testId: "pp2-queue-tab-ready-to-plan" },
				{ id: "blocked", label: __("Blocked"), testId: "pp2-queue-tab-blocked" },
				{ id: "already-planned", label: __("Already Planned"), testId: "pp2-queue-tab-already-planned" },
			],
		},
		plans: {
			tabs: [
				{ id: "active-plans", label: __("Active Plans"), testId: "pp2-queue-tab-active-plans" },
				{ id: "draft-plans", label: __("Draft Plans"), testId: "pp2-queue-tab-draft-plans" },
				{ id: "closed-plans", label: __("Closed Plans"), testId: "pp2-queue-tab-closed-plans" },
			],
		},
		packages: {
			tabs: [
				{ id: "all", label: __("All"), testId: "pp2-queue-tab-all" },
				{ id: "my-work", label: __("My Work"), testId: "pp2-queue-tab-my-work" },
				{ id: "needs-review", label: __("Needs Review"), testId: "pp2-queue-tab-needs-review" },
				{ id: "ready-to-release", label: __("Ready to Release"), testId: "pp2-queue-tab-ready-to-release" },
				{ id: "released", label: __("Released"), testId: "pp2-queue-tab-released" },
				{ id: "blocked", label: __("Blocked"), testId: "pp2-queue-tab-blocked" },
			],
		},
		releases: {
			tabs: [
				{ id: "all", label: __("All"), testId: "pp2-queue-tab-all" },
				{ id: "released", label: __("Released"), testId: "pp2-queue-tab-released" },
			],
		},
	};

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function normalizeSlug(slug) {
		const key = slug == null ? "" : String(slug);
		return Object.prototype.hasOwnProperty.call(SURFACE_QUEUE_CONFIG, key) ? key : "";
	}

	function configForSlug(slug) {
		const key = normalizeSlug(slug);
		return SURFACE_QUEUE_CONFIG[key] || SURFACE_QUEUE_CONFIG[""];
	}

	function tabIdsForSlug(slug) {
		const tabs = (configForSlug(slug).tabs || []).slice();
		const ids = {};
		for (let i = 0; i < tabs.length; i += 1) {
			ids[tabs[i].id] = true;
		}
		return ids;
	}

	function readActiveFromUrl(slug) {
		const ids = tabIdsForSlug(slug);
		try {
			const raw = new URLSearchParams(window.location.search).get("queue");
			if (raw && ids[raw]) {
				return raw;
			}
		} catch (e) {
			/* ignore */
		}
		const tabs = configForSlug(slug).tabs || [];
		return tabs.length ? tabs[0].id : "";
	}

	function setQueueUrl(queueId) {
		const id = String(queueId || "").trim();
		try {
			const u = new URL(window.location.href);
			if (id) {
				u.searchParams.set("queue", id);
			} else {
				u.searchParams.delete("queue");
			}
			window.history.replaceState({}, "", u.pathname + u.search + u.hash);
		} catch (e) {
			/* ignore */
		}
	}

	function html(opts) {
		const o = opts || {};
		const tabs = Array.isArray(o.tabs) ? o.tabs : [];
		const activeId = String(o.activeId || (tabs[0] && tabs[0].id) || "");
		let chips = "";
		for (let i = 0; i < tabs.length; i += 1) {
			const tab = tabs[i];
			const id = String(tab.id || "");
			const on = id === activeId;
			chips +=
				'<button type="button" class="btn btn-default btn-sm pp2-queue-tabs__chip' +
				(on ? " is-active" : "") +
				'" data-testid="' +
				esc(tab.testId || "pp2-queue-tab-" + id) +
				'" data-pp2-queue-id="' +
				esc(id) +
				'" role="tab" aria-selected="' +
				(on ? "true" : "false") +
				'">' +
				esc(tab.label || id) +
				"</button>";
		}
		return (
			'<nav class="pp2-queue-tabs" data-testid="pp2-queue-tabs" role="tablist">' + chips + "</nav>"
		);
	}

	function bindQueueTabs(host, slug) {
		if (!host) return;
		const buttons = host.querySelectorAll("[data-pp2-queue-id]");
		for (let i = 0; i < buttons.length; i += 1) {
			const button = buttons[i];
			if (button.getAttribute("data-bound") === "1") continue;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function () {
				const queueId = String(button.getAttribute("data-pp2-queue-id") || "").trim();
				if (!queueId) return;
				setQueueUrl(queueId);
				renderForSlug(host, slug, queueId);
			});
		}
	}

	function render(host, opts) {
		const target = host && host.nodeType === 1 ? host : null;
		if (!target) return;
		const o = opts || {};
		const tabs = Array.isArray(o.tabs) ? o.tabs : [];
		const activeId = o.activeId != null ? String(o.activeId) : readActiveFromUrl(o.slug);
		target.innerHTML = html({ tabs: tabs, activeId: activeId });
		bindQueueTabs(target, o.slug != null ? o.slug : "");
	}

	function renderForSlug(host, slug, activeId) {
		const key = normalizeSlug(slug);
		const cfg = configForSlug(key);
		const resolvedActive =
			activeId != null && tabIdsForSlug(key)[String(activeId)]
				? String(activeId)
				: readActiveFromUrl(key);
		render(host, { tabs: cfg.tabs, activeId: resolvedActive, slug: key });
	}

	kentender_procurement.PlanningQueueTabs = {
		html: html,
		render: render,
		configForSlug: configForSlug,
		renderForSlug: renderForSlug,
		readActiveFromUrl: readActiveFromUrl,
		setQueueUrl: setQueueUrl,
	};
})();
