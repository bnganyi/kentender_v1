/** TM2 workbench — compact lifecycle queue bar + queue URL sync (UI refactor). */
(function () {
	frappe.provide("kentender_procurement.Tm2Lifecycle");

	const QUEUE_SLUGS = new Set([
		"draft",
		"std-incomplete",
		"ready-review",
		"returned",
		"approved",
		"published",
		"clarifications",
		"addenda",
		"closing-soon",
		"closed",
		"opening-ready",
		"evaluation-ready",
		"cancelled",
	]);

	const SLUG_LABELS = {
		draft: __("Draft"),
		"std-incomplete": __("Doc incomplete"),
		"ready-review": __("Review"),
		returned: __("Returned"),
		approved: __("Approved"),
		published: __("Published"),
		clarifications: __("Clarifications"),
		addenda: __("Addenda"),
		"closing-soon": __("Closing soon"),
		closed: __("Closed"),
		"opening-ready": __("Opening ready"),
		"evaluation-ready": __("Evaluation ready"),
		cancelled: __("Cancelled"),
	};

	const SLUG_TOOLTIPS = {
		"std-incomplete": __("Tender document setup or STD binding is incomplete."),
	};

	const LIFECYCLE_GROUPS = [
		{
			id: "preparation",
			title: __("Preparation"),
			slugs: ["draft", "std-incomplete"],
		},
		{
			id: "review",
			title: __("Review"),
			slugs: ["ready-review", "returned", "approved"],
		},
		{
			id: "live_tender",
			title: __("Live Tender"),
			slugs: ["published", "clarifications", "addenda"],
		},
		{
			id: "closing",
			title: __("Closing"),
			slugs: ["closing-soon", "opening-ready", "closed", "evaluation-ready", "cancelled"],
		},
	];

	const PRIMARY_STAGE_GROUPS = LIFECYCLE_GROUPS.slice(0, 3);
	const CLOSING_STAGE_GROUP = LIFECYCLE_GROUPS[3];

	function queueLabelForSlug(slug) {
		return SLUG_LABELS[slug] || slug || "";
	}

	function queueTooltipForSlug(slug) {
		return SLUG_TOOLTIPS[slug] || "";
	}

	function formatChipLabel(base, count) {
		return String(base || "").trim() + " " + String(count != null ? count : 0);
	}

	function parseChipBase(text) {
		return String(text || "")
			.trim()
			.replace(/\s+\d+\s*$/, "");
	}

	function setWorkbenchQueueUrl(slug) {
		if (slug && !QUEUE_SLUGS.has(slug)) {
			return;
		}
		const u = new URL(window.location.href);
		if (slug) {
			u.searchParams.set("queue", slug);
		} else {
			u.searchParams.delete("queue");
		}
		window.history.replaceState({}, "", u.pathname + u.search + u.hash);
	}

	function readQueueSlugFromUrl() {
		const raw = new URLSearchParams(window.location.search).get("queue");
		if (raw && QUEUE_SLUGS.has(raw)) {
			return raw;
		}
		return null;
	}

	function esc(s) {
		return frappe.utils.escape_html(s);
	}

	function buildQueueChipHtml(slug) {
		const tid = "tm2-queue-" + slug;
		const lab = queueLabelForSlug(slug);
		const tip = queueTooltipForSlug(slug);
		const titleAttr = tip ? ' title="' + esc(tip) + '"' : "";
		return (
			'<button type="button" class="btn btn-default btn-sm tm2-lifecycle-chip" data-testid="' +
			esc(tid) +
			'" data-tm2-queue-slug="' +
			esc(slug) +
			'"' +
			titleAttr +
			">" +
			esc(formatChipLabel(lab, 0)) +
			"</button>"
		);
	}

	function buildStageInlineHtml(group) {
		let chips = "";
		for (let s = 0; s < group.slugs.length; s += 1) {
			chips += buildQueueChipHtml(group.slugs[s]);
		}
		return (
			'<div class="tm2-lifecycle-stage" data-lifecycle-group="' +
			esc(group.id) +
			'" data-testid="tm2-lifecycle-stage-' +
			esc(group.id) +
			'">' +
			'<span class="tm2-lifecycle-stage-label">' +
			esc(group.title) +
			"</span>" +
			'<span class="tm2-lifecycle-stage-chips">' +
			chips +
			"</span></div>"
		);
	}

	function buildLifecycleBarHtml() {
		let primaryStages = "";
		for (let g = 0; g < PRIMARY_STAGE_GROUPS.length; g += 1) {
			primaryStages += buildStageInlineHtml(PRIMARY_STAGE_GROUPS[g]);
		}

		let html =
			'<div class="tm2-lifecycle-stage-row tm2-lifecycle-stage-row--primary" data-testid="tm2-lifecycle-stage-row-primary">' +
			'<div class="tm2-lifecycle-scope-inline">' +
			'<button type="button" class="btn btn-default btn-sm tm2-lifecycle-chip" data-testid="tm2-lifecycle-all" data-tm2-queue-slug="">' +
			esc(formatChipLabel(__("All"), 0)) +
			"</button>" +
			'<button type="button" class="btn btn-default btn-sm tm2-lifecycle-scope-chip" data-testid="tm2-lifecycle-my-work" title="' +
			esc(__("Show tenders assigned to you")) +
			'">' +
			esc(__("My Work")) +
			"</button></div>" +
			primaryStages +
			"</div>";

		html +=
			'<div class="tm2-lifecycle-stage-row tm2-lifecycle-stage-row--closing" data-testid="tm2-lifecycle-stage-row-closing">' +
			buildStageInlineHtml(CLOSING_STAGE_GROUP) +
			"</div>";
		return html;
	}

	function applyQueueSelection($w, slug) {
		const s = slug && QUEUE_SLUGS.has(slug) ? slug : null;
		$w.find(".tm2-lifecycle-chip").removeClass("tm2-lifecycle-chip--active btn-primary");
		if (s) {
			$w.find('.tm2-lifecycle-chip[data-tm2-queue-slug="' + s + '"]').addClass("tm2-lifecycle-chip--active btn-primary");
		} else {
			$w.find('[data-testid="tm2-lifecycle-all"]').addClass("tm2-lifecycle-chip--active btn-primary");
		}
		refreshLifecycleChipEmphasis($w);
	}

	function applyMyWorkScope($w, on) {
		const $btn = $w.find('[data-testid="tm2-lifecycle-my-work"]');
		if (!$btn.length) {
			return;
		}
		$btn.toggleClass("tm2-lifecycle-chip--active btn-primary", !!on);
	}

	function refreshLifecycleChipEmphasis($w) {
		$w.find(".tm2-lifecycle-chip[data-tm2-queue-slug]").each(function () {
			const $b = $(this);
			const slug = $b.attr("data-tm2-queue-slug");
			if (!slug) {
				return;
			}
			const text = $.trim($b.text());
			const count = parseInt(text.replace(/^.*\s(\d+)\s*$/, "$1"), 10);
			const isZero = !Number.isNaN(count) && count === 0;
			$b.toggleClass("tm2-lifecycle-chip--zero", isZero && !$b.hasClass("tm2-lifecycle-chip--active"));
		});
		const $all = $w.find('[data-testid="tm2-lifecycle-all"]');
		if ($all.length) {
			const allText = $.trim($all.text());
			const allCount = parseInt(allText.replace(/^.*\s(\d+)\s*$/, "$1"), 10);
			const allZero = !Number.isNaN(allCount) && allCount === 0;
			$all.toggleClass("tm2-lifecycle-chip--zero", allZero && !$all.hasClass("tm2-lifecycle-chip--active"));
		}
	}

	function refreshLifecycleCounts($w) {
		frappe.call({
			method: "kentender_procurement.tender_management.api.tm2_workbench.get_workbench_kpi_counts",
			callback(r) {
				const msg = r.message || {};
				if (!msg.ok) {
					return;
				}
				const queueCounts = msg.queue_counts || {};
				const total = typeof msg.total_accessible === "number" ? msg.total_accessible : 0;
				const $all = $w.find('[data-testid="tm2-lifecycle-all"]');
				if ($all.length) {
					const base = $all.data("tm2LifecycleBase") || __("All");
					$all.text(formatChipLabel(base, total));
				}
				$w.find(".tm2-lifecycle-chip[data-tm2-queue-slug]").each(function () {
					const $b = $(this);
					const slug = $b.attr("data-tm2-queue-slug");
					if (!slug) {
						return;
					}
					const base = $b.data("tm2LifecycleBase") || queueLabelForSlug(slug);
					const c = typeof queueCounts[slug] === "number" ? queueCounts[slug] : 0;
					$b.text(formatChipLabel(base, c));
					const risk = c > 0 && (slug === "std-incomplete" || slug === "addenda");
					$b.toggleClass("tm2-lifecycle-chip--risk border-warning", risk);
				});
				refreshLifecycleChipEmphasis($w);
			},
		});
	}

	function initLifecycleChipBases($w) {
		$w.find(".tm2-lifecycle-chip").each(function () {
			const $b = $(this);
			if (!$b.data("tm2LifecycleBase")) {
				$b.data("tm2LifecycleBase", parseChipBase($b.text()));
			}
		});
	}

	kentender_procurement.Tm2Lifecycle = {
		QUEUE_SLUGS: QUEUE_SLUGS,
		LIFECYCLE_GROUPS: LIFECYCLE_GROUPS,
		queueLabelForSlug: queueLabelForSlug,
		formatChipLabel: formatChipLabel,
		setWorkbenchQueueUrl: setWorkbenchQueueUrl,
		readQueueSlugFromUrl: readQueueSlugFromUrl,
		buildLifecycleBarHtml: buildLifecycleBarHtml,
		applyQueueSelection: applyQueueSelection,
		applyMyWorkScope: applyMyWorkScope,
		refreshLifecycleCounts: refreshLifecycleCounts,
		initLifecycleChipBases: initLifecycleChipBases,
	};
})();
