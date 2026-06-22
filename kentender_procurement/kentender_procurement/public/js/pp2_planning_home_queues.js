/**
 * P5C-003 / P5C-004 / P5C-005 / P5C-006 / P5C-007 — Planning Home queue orchestrator.
 */
(function () {
	frappe.provide("kentender_procurement");

	const NEEDS_PLANNING_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_needs_planning_queue";
	const NEEDS_REVIEW_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_needs_review_queue";
	const READY_RELEASE_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_ready_to_release_queue";
	const RELEASED_RECENTLY_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_released_recently_queue";
	const BLOCKED_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_blocked_queue";

	const WORKBENCH_PATH = "/desk/procurement-planning";
	const TENDER_MANAGEMENT_PATH = "/desk/tender-management-v2";
	const NEEDS_REVIEW_QUEUE = "needs-review";
	const READY_RELEASE_QUEUE = "ready-to-release";
	const RELEASED_RECENTLY_QUEUE = "released-recently";
	const BLOCKED_QUEUE = "blocked";

	function sectionApi() {
		return (
			kentender_procurement &&
			kentender_procurement.PlanningHomeQueueSection &&
			typeof kentender_procurement.PlanningHomeQueueSection.fetchAndRender === "function"
				? kentender_procurement.PlanningHomeQueueSection
				: null
		);
	}

	function emptyMessageForQueueKey(queueKey) {
		const key = String(queueKey || "").trim();
		const emptyApi =
			kentender_procurement &&
			kentender_procurement.PlanningEmptyState &&
			kentender_procurement.PlanningEmptyState.HOME_QUEUE_MESSAGES
				? kentender_procurement.PlanningEmptyState
				: null;
		if (emptyApi && emptyApi.HOME_QUEUE_MESSAGES && emptyApi.HOME_QUEUE_MESSAGES[key]) {
			return emptyApi.HOME_QUEUE_MESSAGES[key];
		}
		if (key === "needs_planning") {
			return __("No approved demands need planning.");
		}
		if (key === "needs_review") {
			return __("No packages are waiting for review.");
		}
		return __("No items need your attention right now.");
	}

	function buildWorkbenchHref(params) {
		const q = params || {};
		const url = new URL(window.location.origin + WORKBENCH_PATH);
		Object.keys(q).forEach((key) => {
			const value = String(q[key] || "").trim();
			if (!value) return;
			url.searchParams.set(key, value);
		});
		return url.pathname + url.search;
	}

	function openDemandItem(item) {
		const it = item || {};
		const primary = it.primary_action || {};
		const target = String(primary.target || it.id || "").trim();
		if (!target) {
			window.location.href = buildWorkbenchHref({ queue: "needs-planning" });
			return;
		}
		window.location.href = buildWorkbenchHref({
			queue: "needs-planning",
			item: target,
		});
	}

	function openPackageItem(item) {
		const it = item || {};
		const primary = it.primary_action || {};
		const target = String(primary.target || it.id || "").trim();
		const base = buildWorkbenchHref({ queue: NEEDS_REVIEW_QUEUE });
		if (!target) {
			window.location.href = base;
			return;
		}
		window.location.href = buildWorkbenchHref({ queue: NEEDS_REVIEW_QUEUE, item: target });
	}

	function openReadyReleaseItem(item) {
		const it = item || {};
		const primary = it.primary_action || {};
		const target = String(primary.target || it.id || "").trim();
		const base = buildWorkbenchHref({ queue: READY_RELEASE_QUEUE });
		if (!target) {
			window.location.href = base;
			return;
		}
		window.location.href = buildWorkbenchHref({ queue: READY_RELEASE_QUEUE, item: target });
	}

	function openReleasedTender(item) {
		const it = item || {};
		const primary = it.primary_action || {};
		const target = String(primary.target || "").trim();
		if (!target) {
			window.location.href = TENDER_MANAGEMENT_PATH;
			return;
		}
		window.location.href =
			TENDER_MANAGEMENT_PATH + "?tender_code=" + encodeURIComponent(target);
	}

	function openReleasedPackage(item, selectedSecondaryAction) {
		const it = item || {};
		const secondary = selectedSecondaryAction || {};
		const fallbackPrimary = it.primary_action || {};
		const target = String(secondary.target || it.id || fallbackPrimary.target || "").trim();
		const base = buildWorkbenchHref({ queue: RELEASED_RECENTLY_QUEUE });
		if (!target) {
			window.location.href = base;
			return;
		}
		window.location.href = buildWorkbenchHref({ queue: RELEASED_RECENTLY_QUEUE, item: target });
	}

	function openBlockedItem(item) {
		const it = item || {};
		const primary = it.primary_action || {};
		const action = String(primary.action || "").trim();
		const target = String(primary.target || it.id || "").trim();
		if (action === "open_demand") {
			const demandBase = buildWorkbenchHref({ queue: BLOCKED_QUEUE });
			if (!target) {
				window.location.href = demandBase;
				return;
			}
			window.location.href = buildWorkbenchHref({ queue: BLOCKED_QUEUE, item: target });
			return;
		}
		const packageBase = buildWorkbenchHref({ queue: BLOCKED_QUEUE });
		if (!target) {
			window.location.href = packageBase;
			return;
		}
		window.location.href = buildWorkbenchHref({ queue: BLOCKED_QUEUE, item: target });
	}

	function mountQueueSection(host, config) {
		const api = sectionApi();
		if (!api || !host || !config) return;
		const sectionHost = document.createElement("div");
		sectionHost.className = "pp2-planning-home__queue-slot";
		host.appendChild(sectionHost);
		api.fetchAndRender(sectionHost, config);
	}

	function needsPlanningConfig() {
		return {
			queueKey: "needs_planning",
			sectionTestId: "pp2-queue-needs-planning",
			title: __("Needs Planning"),
			emptyMessage: emptyMessageForQueueKey("needs_planning"),
			apiMethod: NEEDS_PLANNING_API,
			viewAllHref: buildWorkbenchHref({ queue: "needs-planning" }),
			onOpen: openDemandItem,
		};
	}

	function needsReviewConfig() {
		return {
			queueKey: "needs_review",
			sectionTestId: "pp2-queue-needs-review",
			title: __("Needs Review"),
			emptyMessage: emptyMessageForQueueKey("needs_review"),
			apiMethod: NEEDS_REVIEW_API,
			viewAllHref: buildWorkbenchHref({ queue: NEEDS_REVIEW_QUEUE }),
			onOpen: openPackageItem,
		};
	}

	function readyToReleaseConfig() {
		return {
			queueKey: "ready_to_release",
			sectionTestId: "pp2-queue-ready-release",
			title: __("Ready to Release"),
			emptyMessage: emptyMessageForQueueKey("ready_to_release"),
			apiMethod: READY_RELEASE_API,
			viewAllHref: buildWorkbenchHref({ queue: READY_RELEASE_QUEUE }),
			onOpen: openReadyReleaseItem,
		};
	}

	function releasedRecentlyConfig() {
		return {
			queueKey: "released_recently",
			sectionTestId: "pp2-queue-released-recently",
			title: __("Released Recently"),
			emptyMessage: emptyMessageForQueueKey("released_recently"),
			apiMethod: RELEASED_RECENTLY_API,
			viewAllHref: buildWorkbenchHref({ queue: RELEASED_RECENTLY_QUEUE }),
			onOpen: openReleasedTender,
			onSecondary: openReleasedPackage,
		};
	}

	function blockedConfig() {
		return {
			queueKey: "blocked",
			sectionTestId: "pp2-queue-blocked",
			title: __("Blocked"),
			emptyMessage: emptyMessageForQueueKey("blocked"),
			apiMethod: BLOCKED_API,
			viewAllHref: buildWorkbenchHref({ queue: BLOCKED_QUEUE }),
			onOpen: openBlockedItem,
		};
	}

	function mountNeedsPlanning(host) {
		mountQueueSection(host, needsPlanningConfig());
	}

	function mountNeedsReview(host) {
		mountQueueSection(host, needsReviewConfig());
	}

	function mountReadyToRelease(host) {
		mountQueueSection(host, readyToReleaseConfig());
	}

	function mountReleasedRecently(host) {
		mountQueueSection(host, releasedRecentlyConfig());
	}

	function mountBlocked(host) {
		mountQueueSection(host, blockedConfig());
	}

	function fetchAndRender(host) {
		if (!host) return;
		host.innerHTML = "";
		mountNeedsPlanning(host);
		mountNeedsReview(host);
		mountReadyToRelease(host);
		mountReleasedRecently(host);
		mountBlocked(host);
	}

	kentender_procurement.PlanningHomeQueues = {
		emptyMessageForQueueKey: emptyMessageForQueueKey,
		needsPlanningConfig: needsPlanningConfig,
		needsReviewConfig: needsReviewConfig,
		readyToReleaseConfig: readyToReleaseConfig,
		releasedRecentlyConfig: releasedRecentlyConfig,
		blockedConfig: blockedConfig,
		mountNeedsPlanning: mountNeedsPlanning,
		mountNeedsReview: mountNeedsReview,
		mountReadyToRelease: mountReadyToRelease,
		mountReleasedRecently: mountReleasedRecently,
		mountBlocked: mountBlocked,
		fetchAndRender: fetchAndRender,
		openDemandItem: openDemandItem,
		openPackageItem: openPackageItem,
		openReadyReleaseItem: openReadyReleaseItem,
		openReleasedTender: openReleasedTender,
		openReleasedPackage: openReleasedPackage,
		openBlockedItem: openBlockedItem,
	};
})();
