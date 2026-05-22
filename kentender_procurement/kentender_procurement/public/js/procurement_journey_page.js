/** G0-007 / R4-005 … R4-013 — Desk Page `plc-procurement-journey` (header … handoffs, evidence timeline, safe open-module links, technical evidence drawer). */
(function () {
	frappe.provide("frappe.pages");
	const PAGE_NAME = "plc-procurement-journey";
	frappe.pages[PAGE_NAME] = frappe.pages[PAGE_NAME] || {};

	/** R4-012 — must stay aligned with ``journey_aggregate._OPEN_MODULE_ROUTE_ALLOWED_DOCTYPES``. */
	const _OPEN_MODULE_ALLOWED_DOCTYPES = {
		"TM2 Tender": true,
		"Tender STD Instance": true,
		Demand: true,
		"Procurement Package": true,
		"Procurement Plan": true,
		"Strategy Objective": true,
		"Budget Line": true,
	};

	const _SPINE_CLASSES = {
		strategy: "plc-journey-step-strategy",
		budget: "plc-journey-step-budget",
		demand: "plc-journey-step-demand",
		planning_inclusion: "plc-journey-step-planning",
		package_release: "plc-journey-step-planning",
		std_readiness: "plc-journey-step-std-readiness",
		tender_publication: "plc-journey-step-tender",
		tender_closing: "plc-journey-step-tender",
		opening_readiness: "plc-journey-step-opening",
		bid_opening: "plc-journey-step-opening",
		evaluation_award: "plc-journey-step-evaluation plc-journey-step-award",
		contract: "plc-journey-step-contract",
	};

	function spineClassesForStepKey(stepKey) {
		const k = String(stepKey || "").trim();
		return _SPINE_CLASSES[k] || "";
	}

	function statusVisualClass(statusCategory) {
		const s = String(statusCategory || "").trim().toLowerCase();
		if (!s) {
			return "plc-journey-step--not-started";
		}
		if (s.indexOf("block") >= 0) {
			return "plc-journey-step--blocked";
		}
		if (s === "not started") {
			return "plc-journey-step--not-started";
		}
		if (
			s === "completed" ||
			s === "handed off" ||
			s.indexOf("handoff") >= 0 ||
			s === "consumed"
		) {
			return "plc-journey-step--done";
		}
		if (s === "in progress" || s === "needs action" || s.indexOf("returned") >= 0) {
			return "plc-journey-step--active";
		}
		return "plc-journey-step--active";
	}

	function renderTimelineSection(steps) {
		const $section = $('<section class="card plc-journey-timeline mb-3">').attr(
			"data-testid",
			"plc-journey-timeline",
		);
		const $body = $('<div class="card-body pt-3 pb-2">');
		$body.append(
			$("<h5>")
				.attr("data-testid", "plc-journey-timeline-title")
				.addClass("h6 text-muted mb-3")
				.text(__("Lifecycle spine")),
		);
		const list = ((steps && steps.slice()) || []).sort(function (a, b) {
			return (Number(a && a.step_order) || 0) - (Number(b && b.step_order) || 0);
		});
		if (!list.length) {
			$body.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-journey-timeline-empty")
					.text(__("No journey steps are available for this journey.")),
			);
			$section.append($body);
			return $section;
		}
		const $track = $('<div class="plc-journey-timeline-track">');
		for (let i = 0; i < list.length; i++) {
			const step = list[i];
			const key = String((step && step.step_key) || "").trim();
			const label = String((step && step.label) || key);
			const st = String((step && step.status_category) || "");
			const spine = spineClassesForStepKey(key);
			const $node = $('<div class="plc-journey-timeline-node">').attr("data-step-key", key);
			const $pill = $('<div class="plc-journey-step-pill">').addClass(statusVisualClass(st));
			if (spine) {
				const parts = spine.split(/\s+/).filter(Boolean);
				for (let p = 0; p < parts.length; p++) {
					$pill.addClass(parts[p]);
				}
			}
			$pill.append(
				$('<div class="plc-journey-step-label">').text(label),
				$('<div class="plc-journey-step-status">').text(st),
			);
			$node.append($pill);
			$track.append($node);
		}
		$body.append($track);
		$section.append($body);
		return $section;
	}

	function parseOpenModuleRoute(raw) {
		if (raw == null || raw === "") {
			return null;
		}
		var s = String(raw).trim();
		if (!s) {
			return null;
		}
		try {
			var arr = JSON.parse(s);
			if (Array.isArray(arr) && arr.length) {
				var out = [];
				for (var i = 0; i < arr.length; i++) {
					out.push(String(arr[i]));
				}
				return out.length ? out : null;
			}
		} catch (e) {
			return null;
		}
		return null;
	}

	function deskFormOpenRouteAllowed(segments) {
		if (!segments || segments.length !== 3) {
			return false;
		}
		if (String(segments[0] || "").trim() !== "Form") {
			return false;
		}
		var dt = String(segments[1] || "").trim();
		if (!dt || !_OPEN_MODULE_ALLOWED_DOCTYPES[dt]) {
			return false;
		}
		return Boolean(String(segments[2] || "").trim());
	}

	function wireOpenModuleLink($a, routeRaw) {
		var segs = parseOpenModuleRoute(routeRaw);
		if (!segs || !deskFormOpenRouteAllowed(segs)) {
			return;
		}
		$a.attr("href", "#");
		$a.on("click", function (ev) {
			ev.preventDefault();
			frappe.set_route.apply(null, segs);
		});
	}

	function isDoneStatusCategory(cat) {
		var s = String(cat || "")
			.trim()
			.toLowerCase();
		if (!s) {
			return false;
		}
		return (
			s === "completed" ||
			s === "handed off" ||
			s === "superseded" ||
			s === "cancelled" ||
			s === "audit only"
		);
	}

	function pickFocusStep(steps) {
		var list = ((steps && steps.slice()) || []).sort(function (a, b) {
			return (Number(a && a.step_order) || 0) - (Number(b && b.step_order) || 0);
		});
		if (!list.length) {
			return null;
		}
		for (var i = 0; i < list.length; i++) {
			if (!isDoneStatusCategory(list[i] && list[i].status_category)) {
				return list[i];
			}
		}
		return list[list.length - 1];
	}

	function renderCurrentFocusSection(j) {
		var steps = (j && j.steps) || [];
		var focus = pickFocusStep(steps);
		var nextAction = String((j && j.next_action) || "").trim();
		var ownerMod = String((j && j.current_owner_module) || "").trim();
		var ownerRole = String((j && j.current_owner_role) || "").trim();
		var journeyStatus = String((j && j.current_status) || "").trim();
		var bcTotal = Number((j && j.blocker_count) || 0) || 0;
		var bcCrit = Number((j && j.critical_blocker_count) || 0) || 0;

		var $section = $('<section class="card plc-current-focus mb-3">').attr(
			"data-testid",
			"plc-current-focus",
		);
		var $body = $('<div class="card-body pt-3 pb-2">');
		$body.append(
			$("<h5>")
				.addClass("h6 text-muted mb-3")
				.attr("data-testid", "plc-current-focus-title")
				.text(__("Current focus")),
		);

		if (focus) {
			var fk = String((focus.step_key || "").trim());
			var flabel = String((focus.label || fk || __("Step")).trim());
			var fst = String((focus.status_category || "").trim());
			$body.append(
				$("<div>")
					.addClass("plc-current-focus-milestone mb-2")
					.attr("data-step-key", fk)
					.append(
						$("<div>")
							.addClass("fw-semibold plc-current-focus-step-label")
							.attr("data-testid", "plc-current-focus-step-label")
							.text(flabel),
						$("<div>")
							.addClass("text-muted small plc-current-focus-step-status")
							.attr("data-testid", "plc-current-focus-step-status")
							.text(fst),
					),
			);
		}

		if (nextAction) {
			$body.append(
				$("<div>")
					.addClass("plc-current-focus-next-action mt-1")
					.attr("data-testid", "plc-current-focus-next-action")
					.text(__("Next action") + ": " + nextAction),
			);
		}

		var ownerLine = "";
		if (ownerMod && ownerRole) {
			ownerLine = ownerMod + " · " + ownerRole;
		} else if (ownerMod) {
			ownerLine = ownerMod;
		} else if (ownerRole) {
			ownerLine = ownerRole;
		}
		if (ownerLine) {
			$body.append(
				$("<div>")
					.addClass("text-muted small mt-2 plc-current-focus-owner")
					.attr("data-testid", "plc-current-focus-owner")
					.text(__("Owner") + ": " + ownerLine),
			);
		}
		if (journeyStatus) {
			$body.append(
				$("<div>")
					.addClass("text-muted small mt-1 plc-current-focus-journey-status")
					.attr("data-testid", "plc-current-focus-journey-status")
					.text(__("Journey status") + ": " + journeyStatus),
			);
		}

		var $blk = $('<div class="plc-current-focus-blockers mt-3 pt-2 border-top">').attr(
			"data-testid",
			"plc-current-focus-blockers",
		);
		$blk.append(
			$("<div>")
				.addClass("d-flex flex-wrap gap-3 align-items-center small mb-2")
				.append(
					$("<span>")
						.addClass("plc-current-focus-blocker-total")
						.attr("data-testid", "plc-current-focus-blocker-total")
						.attr("data-count", String(bcTotal))
						.text(__("Open blockers") + ": " + String(bcTotal)),
					$("<span>")
						.addClass("plc-current-focus-blocker-critical")
						.attr("data-testid", "plc-current-focus-blocker-critical")
						.attr("data-count", String(bcCrit))
						.text(__("Critical steps") + ": " + String(bcCrit)),
				),
		);

		var blockerSteps = [];
		for (var bi = 0; bi < steps.length; bi++) {
			var st = steps[bi];
			var bcn = Number((st && st.blocker_count) || 0) || 0;
			var scat = String((st && st.status_category) || "")
				.trim()
				.toLowerCase();
			if (bcn > 0 || scat === "blocked") {
				blockerSteps.push(st);
			}
		}
		if (!blockerSteps.length) {
			$blk.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-current-focus-blockers-empty")
					.text(__("No step-level blockers recorded for this journey.")),
			);
		} else {
			var $list = $('<div class="plc-current-focus-blocker-list">');
			for (var bj = 0; bj < blockerSteps.length; bj++) {
				var row = blockerSteps[bj];
				var rk = String((row.step_key || "").trim());
				var rlabel = String((row.label || rk).trim());
				var rbc = Number((row.blocker_count || 0) || 0) || 0;
				var rowText = rlabel;
				if (rbc > 0) {
					rowText +=
						" · " +
						(rbc === 1 ? __("1 blocker") : String(rbc) + " " + __("blockers"));
				}
				if (String(row.status_category || "")
					.trim()
					.toLowerCase() === "blocked") {
					rowText += " (" + __("Blocked") + ")";
				}
				$list.append(
					$("<div>")
						.addClass("small plc-current-focus-blocker-row py-1")
						.attr("data-testid", "plc-current-focus-blocker-row")
						.attr("data-step-key", rk)
						.text(rowText),
				);
			}
			$blk.append($list);
		}
		$body.append($blk);
		$section.append($body);
		return $section;
	}

	function summaryPreviewFromObject(obj) {
		if (!obj || typeof obj !== "object") {
			return "";
		}
		var parts = [];
		var keys = Object.keys(obj);
		for (var i = 0; i < keys.length && parts.length < 2; i++) {
			var v = obj[keys[i]];
			if (typeof v === "string" && v.trim()) {
				parts.push(
					String(keys[i])
						.replace(/_/g, " ")
						.replace(/\b\w/g, function (ch) {
							return ch.toUpperCase();
						}) +
						": " +
						v.trim(),
				);
			}
		}
		return parts.join(" · ");
	}

	function handoffSummaryBlurb(card) {
		var s = summaryPreviewFromObject(card && card.passed_forward_summary);
		if (s) {
			return s;
		}
		return summaryPreviewFromObject(card && card.locked_summary);
	}

	function canViewTechnicalEvidence() {
		return Boolean(frappe.session && frappe.session.user && frappe.session.user !== "Guest");
	}

	function technicalRefsNonempty(refs) {
		if (!refs || typeof refs !== "object" || Array.isArray(refs)) {
			return false;
		}
		return Object.keys(refs).length > 0;
	}

	function ensurePlcTechnicalEvidenceDrawer() {
		var id = "plc-technical-evidence-drawer-root";
		var $existing = $("#" + id);
		if ($existing.length) {
			return $existing;
		}
		var $m = $("<div>")
			.attr("id", id)
			.addClass("modal fade kt-plc-tech-evidence-drawer")
			.attr("data-testid", "plc-technical-evidence-drawer")
			.attr("tabindex", -1)
			.attr("role", "dialog")
			.attr("aria-hidden", "true");
		$m.append(
			$('<div class="modal-dialog modal-lg modal-dialog-scrollable" role="document">').append(
				$('<div class="modal-content">').append(
					$('<div class="modal-header">').append(
						$("<h5>")
							.addClass("modal-title")
							.attr("data-testid", "plc-technical-evidence-drawer-title")
							.text(__("Technical references")),
						$("<button>")
							.attr("type", "button")
							.addClass("close")
							.attr("data-dismiss", "modal")
							.attr("aria-label", "Close")
							.html("&times;"),
					),
					$('<div class="modal-body">').append(
						$("<p>")
							.addClass("text-muted small font-monospace mb-2")
							.attr("data-testid", "plc-technical-evidence-handoff-code"),
						$("<pre>")
							.addClass("plc-technical-evidence-json mb-0")
							.attr("data-testid", "plc-technical-evidence-body"),
					),
				),
			),
		);
		$("body").append($m);
		return $m;
	}

	function showPlcTechnicalEvidenceDrawer(handoffTitle, handoffCode, refs) {
		var $m = ensurePlcTechnicalEvidenceDrawer();
		var subtitle = __("Technical references");
		if (handoffTitle) {
			subtitle = subtitle + " — " + handoffTitle;
		}
		$m.find('[data-testid="plc-technical-evidence-drawer-title"]').text(subtitle);
		var codeLine = handoffCode ? __("Handoff") + " · " + handoffCode : "";
		$m.find('[data-testid="plc-technical-evidence-handoff-code"]').text(codeLine);
		var body =
			refs && typeof refs === "object"
				? JSON.stringify(refs, null, 2)
				: "{}";
		$m.find('[data-testid="plc-technical-evidence-body"]').text(body);
		$m.modal("show");
	}

	function wireTechnicalEvidenceDrawer($section) {
		$section
			.off("click.plcTechEv")
			.on("click.plcTechEv", '[data-testid="plc-open-evidence"]', function (ev) {
				ev.preventDefault();
				if (!canViewTechnicalEvidence()) {
					return;
				}
				var $card = $(this).closest(".plc-handoff-card");
				var refs = $card.data("plcTechnicalRefs");
				var code = String($card.attr("data-handoff-code") || "").trim();
				var htitle = String($card.data("plcHandoffTitle") || "").trim();
				showPlcTechnicalEvidenceDrawer(htitle, code, refs);
			});
	}

	function formatHandoffEvidenceLine(card) {
		var links = (card && card.evidence_links) || [];
		if (!links.length) {
			return "";
		}
		var first = links[0];
		var code = first && first.object_code ? String(first.object_code).trim() : "";
		var lab = first && first.label ? String(first.label).trim() : "";
		if (lab && code) {
			return lab + " · " + code;
		}
		if (code) {
			return code;
		}
		if (links.length === 1) {
			return __("1 evidence link");
		}
		return String(links.length) + " " + __("evidence links");
	}

	function renderHandoffPanelSection(j) {
		var cards = (j && j.handoff_cards) || [];
		var $section = $('<section class="card plc-handoff-panel mb-3">').attr(
			"data-testid",
			"plc-handoff-panel",
		);
		var $body = $('<div class="card-body pt-3 pb-2">');
		$body.append(
			$("<h5>")
				.addClass("h6 text-muted mb-3")
				.attr("data-testid", "plc-handoff-panel-title")
				.text(__("Handoffs & evidence")),
		);
		if (!cards.length) {
			$body.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-handoff-panel-empty")
					.text(__("No handoff certificates are linked to this journey yet.")),
			);
			$section.append($body);
			return $section;
		}
		var $list = $('<div class="plc-handoff-panel-list">');
		for (var i = 0; i < cards.length; i++) {
			var c = cards[i] || {};
			var code = String(c.handoff_code || "").trim();
			var title = String(c.handoff_title || code || __("Handoff")).trim();
			var st = String(c.status || "").trim();
			var srcM = String(c.source_module || "").trim();
			var tgtM = String(c.target_module || "").trim();
			var soType = String(c.source_object_type || "").trim();
			var soCode = String(c.source_object_code || "").trim();
			var toType = String(c.target_object_type || "").trim();
			var toCode = String(c.target_object_code || "").trim();
			var stale = String(c.stale_reason || "").trim();

			var $card = $('<article class="card plc-handoff-card mb-2">')
				.attr("data-handoff-code", code)
				.attr("data-testid", "plc-handoff-card");
			$card.data(
				"plcTechnicalRefs",
				c.technical_refs && typeof c.technical_refs === "object" ? c.technical_refs : {},
			);
			$card.data("plcHandoffTitle", title);
			var $inner = $('<div class="card-body py-2 px-3">');
			var $head = $('<div class="d-flex justify-content-between align-items-start gap-2 mb-1">');
			$head.append(
				$("<div>")
					.addClass("fw-semibold plc-handoff-card-title")
					.attr("data-testid", "plc-handoff-card-title")
					.text(title),
			);
			if (st) {
				$head.append(
					$("<span>")
						.addClass("badge rounded-pill bg-light text-dark border plc-handoff-card-status")
						.attr("data-testid", "plc-handoff-card-status")
						.text(st),
				);
			}
			$inner.append($head);

			if (srcM || tgtM) {
				var route =
					(srcM ? srcM : "") +
					(srcM && tgtM ? " → " : "") +
					(tgtM ? tgtM : "");
				$inner.append(
					$("<div>")
						.addClass("text-muted small plc-handoff-card-route")
						.attr("data-testid", "plc-handoff-card-route")
						.text(route),
				);
			}

			var srcLine = "";
			if (soType && soCode) {
				srcLine = soType + " · " + soCode;
			} else if (soType) {
				srcLine = soType;
			} else if (soCode) {
				srcLine = soCode;
			}
			if (srcLine) {
				$inner.append(
					$("<div>")
						.addClass("small plc-handoff-card-source")
						.attr("data-testid", "plc-handoff-card-source")
						.text(srcLine),
				);
			}
			var tgtLine = "";
			if (toType && toCode) {
				tgtLine = toType + " · " + toCode;
			} else if (toType) {
				tgtLine = toType;
			} else if (toCode) {
				tgtLine = toCode;
			}
			if (tgtLine) {
				$inner.append(
					$("<div>")
						.addClass("small text-muted plc-handoff-card-target")
						.attr("data-testid", "plc-handoff-card-target")
						.text(__("Target") + ": " + tgtLine),
				);
			}

			var blurb = handoffSummaryBlurb(c);
			if (blurb) {
				$inner.append(
					$("<div>")
						.addClass("text-muted small mt-1 plc-handoff-card-preview")
						.attr("data-testid", "plc-handoff-card-preview")
						.text(blurb),
				);
			}

			var evLine = formatHandoffEvidenceLine(c);
			if (evLine) {
				$inner.append(
					$("<div>")
						.addClass("text-muted small mt-1 plc-handoff-card-evidence")
						.attr("data-testid", "plc-handoff-card-evidence")
						.text(__("Evidence") + ": " + evLine),
				);
			}

			if (stale) {
				$inner.append(
					$("<div>")
						.addClass("alert alert-warning py-1 px-2 small mb-0 mt-2 plc-handoff-card-stale")
						.attr("data-testid", "plc-handoff-card-stale")
						.text(stale),
				);
			}

			if (canViewTechnicalEvidence() && technicalRefsNonempty(c.technical_refs)) {
				$inner.append(
					$("<div>")
						.addClass("mt-2")
						.append(
							$("<button>")
								.attr("type", "button")
								.addClass("btn btn-sm btn-outline-secondary")
								.attr("data-testid", "plc-open-evidence")
								.text(__("Technical details")),
						),
				);
			}

			$card.append($inner);
			$list.append($card);
		}
		$body.append($list);
		$section.append($body);
		wireTechnicalEvidenceDrawer($section);
		return $section;
	}

	function renderEvidenceTimelineSection(j) {
		var events = (j && j.evidence_summary) || [];
		var $section = $('<section class="card plc-evidence-timeline mb-3">').attr(
			"data-testid",
			"plc-evidence-timeline",
		);
		var $body = $('<div class="card-body pt-3 pb-2">');
		$body.append(
			$("<h5>")
				.addClass("h6 text-muted mb-3")
				.attr("data-testid", "plc-evidence-timeline-title")
				.text(__("Evidence timeline")),
		);
		if (!events.length) {
			$body.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-evidence-timeline-empty")
					.text(__("No evidence events are recorded for this journey yet.")),
			);
			$section.append($body);
			return $section;
		}
		var $track = $('<div class="plc-evidence-timeline-track">');
		for (var ti = 0; ti < events.length; ti++) {
			var e = events[ti] || {};
			var hc = String(e.handoff_code || "").trim();
			var when = String(e.occurred_at || "").trim();
			var mod = String(e.module || "").trim();
			var evType = String(e.event_type || "").trim();
			var biz = String(e.business_label || "").trim();
			var ot = String(e.object_type || "").trim();
			var oc = String(e.object_code || "").trim();
			var refs = e.evidence_refs;
			var refParts = [];
			if (refs && refs.length) {
				for (var ri = 0; ri < refs.length; ri++) {
					if (refs[ri]) {
						refParts.push(String(refs[ri]));
					}
				}
			}
			var refStr = refParts.join(", ");

			var $ev = $('<div class="plc-evidence-timeline-event">')
				.attr("data-handoff-code", hc)
				.attr("data-testid", "plc-evidence-timeline-event");
			var $row = $('<div class="d-flex gap-2 align-items-start">');
			$row.append(
				$("<div>")
					.addClass("text-muted small plc-evidence-timeline-date flex-shrink-0")
					.attr("data-testid", "plc-evidence-timeline-date")
					.text(when || "—"),
			);
			var $main = $('<div class="flex-grow-1 min-w-0">');
			$main.append(
				$("<div>")
					.addClass("fw-semibold plc-evidence-timeline-event-title")
					.attr("data-testid", "plc-evidence-timeline-event-title")
					.text(evType || __("Event")),
			);
			if (biz) {
				$main.append(
					$("<div>")
						.addClass("text-muted small plc-evidence-timeline-business-label")
						.attr("data-testid", "plc-evidence-timeline-business-label")
						.text(biz),
				);
			}
			if (mod) {
				$main.append(
					$("<div>")
						.addClass("text-muted small plc-evidence-timeline-module")
						.attr("data-testid", "plc-evidence-timeline-module")
						.text(mod),
				);
			}
			var objLine = "";
			if (ot && oc) {
				objLine = ot + " · " + oc;
			} else if (ot) {
				objLine = ot;
			} else if (oc) {
				objLine = oc;
			}
			if (objLine) {
				$main.append(
					$("<div>")
						.addClass("small plc-evidence-timeline-object")
						.attr("data-testid", "plc-evidence-timeline-object")
						.text(objLine),
				);
			}
			if (hc) {
				$main.append(
					$("<div>")
						.addClass("small text-muted plc-evidence-timeline-handoff-code font-monospace")
						.attr("data-testid", "plc-evidence-timeline-handoff-code")
						.text(hc),
				);
			}
			if (refStr) {
				$main.append(
					$("<div>")
						.addClass("small text-muted plc-evidence-timeline-refs")
						.attr("data-testid", "plc-evidence-timeline-refs")
						.text(__("Refs") + ": " + refStr),
				);
			}
			if (e.stale_warning) {
				const sr = String(e.stale_reason || "").trim();
				var staleText = __("Stale handoff");
				if (sr) {
					staleText = staleText + ": " + sr;
				}
				$main.append(
					$("<div>")
						.addClass("alert alert-warning small py-1 px-2 mt-2 mb-0 plc-evidence-timeline-stale")
						.attr("data-testid", "plc-evidence-timeline-stale-warning")
						.attr("role", "alert")
						.text(staleText),
				);
			}
			$row.append($main);
			$ev.append($row);
			$track.append($ev);
		}
		$body.append($track);
		$section.append($body);
		return $section;
	}

	function renderStepCardsSection(steps) {
		var $section = $('<section class="card plc-journey-step-cards mb-3">').attr(
			"data-testid",
			"plc-journey-step-cards",
		);
		var $body = $('<div class="card-body pt-3 pb-2">');
		$body.append(
			$("<h5>")
				.attr("data-testid", "plc-journey-step-cards-title")
				.addClass("h6 text-muted mb-3")
				.text(__("Step details")),
		);
		var list = ((steps && steps.slice()) || []).sort(function (a, b) {
			return (Number(a && a.step_order) || 0) - (Number(b && b.step_order) || 0);
		});
		if (!list.length) {
			$body.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-journey-step-cards-empty")
					.text(__("No journey steps are available for this journey.")),
			);
			$section.append($body);
			return $section;
		}
		var $grid = $('<div class="row g-2 plc-journey-step-cards-grid">');
		for (var i = 0; i < list.length; i++) {
			var step = list[i];
			var key = String((step && step.step_key) || "").trim();
			var label = String((step && step.label) || key || __("Step"));
			var st = String((step && step.status_category) || "");
			var ownerMod = String((step && step.owner_module) || "").trim();
			var objType = String((step && step.source_object_type) || "").trim();
			var objCode = String((step && step.source_object_code) || "").trim();
			var nextAct = String((step && step.next_action) || "").trim();
			var routeRaw = step && step.open_module_route;
			var bc = Number((step && step.blocker_count) || 0) || 0;

			var spine = spineClassesForStepKey(key);
			var $col = $('<div class="col-12 col-md-6 col-xl-4">');
			var $card = $('<article class="card plc-journey-step-card h-100">')
				.attr("data-step-key", key)
				.attr("data-testid", "plc-journey-step-card");
			if (spine) {
				var parts = spine.split(/\s+/).filter(Boolean);
				for (var p = 0; p < parts.length; p++) {
					$card.addClass(parts[p]);
				}
			}
			var $cb = $('<div class="card-body py-2 px-3 d-flex flex-column">');
			var $row = $('<div class="d-flex justify-content-between align-items-start gap-2 mb-1">');
			$row.append(
				$("<h6>").addClass("mb-0 plc-journey-step-card-title flex-grow-1").text(label),
			);
			if (bc > 0) {
				var blockLabel =
					bc === 1 ? __("1 blocker") : String(bc) + " " + __("blockers");
				$row.append(
					$('<span class="badge bg-danger plc-journey-step-blocker-badge">')
						.attr("data-testid", "plc-journey-step-blocker-badge")
						.attr("data-blocker-count", String(bc))
						.text(blockLabel),
				);
			}
			$cb.append($row);

			var $status = $('<div class="plc-journey-step-card-status mb-2">');
			var $chip = $('<span class="plc-journey-step-card-status-chip">').addClass(statusVisualClass(st));
			$chip.append($("<span>").addClass("plc-journey-step-card-status-label").text(st || __("—")));
			$status.append($chip);
			$cb.append($status);

			if (ownerMod) {
				$cb.append(
					$("<div>")
						.addClass("text-muted small plc-journey-step-card-owner")
						.text(ownerMod),
				);
			}
			var refLine = "";
			if (objType && objCode) {
				refLine = objType + " · " + objCode;
			} else if (objType) {
				refLine = objType;
			} else if (objCode) {
				refLine = objCode;
			}
			if (refLine) {
				$cb.append(
					$("<div>")
						.addClass("small plc-journey-step-card-ref text-break")
						.text(refLine),
				);
			}
			if (nextAct) {
				$cb.append(
					$("<div>")
						.addClass("text-muted small mt-1 plc-journey-step-card-next")
						.text(__("Next") + ": " + nextAct),
				);
			}

			var segs = parseOpenModuleRoute(routeRaw);
			if (segs && deskFormOpenRouteAllowed(segs)) {
				var $actions = $('<div class="mt-auto pt-2">');
				var $open = $('<a role="button" class="btn btn-sm btn-outline-primary plc-open-current-module">')
					.attr("data-testid", "plc-open-current-module")
					.text(__("Open module"));
				wireOpenModuleLink($open, routeRaw);
				$actions.append($open);
				$cb.append($actions);
			}

			$card.append($cb);
			$col.append($card);
			$grid.append($col);
		}
		$body.append($grid);
		$section.append($body);
		return $section;
	}

	function optionValue(val) {
		if (val == null || val === "") return "";
		try {
			return String(JSON.parse(val)).trim();
		} catch (e) {
			return String(val).trim();
		}
	}

	function escapeHtml(s) {
		if (s == null || s === undefined) {
			return "";
		}
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function formatBlockersLabel(item) {
		const bc = Number(item && item.blocker_count) || 0;
		const cc = Number(item && item.critical_blocker_count) || 0;
		if (bc === 0 && cc === 0) {
			return __("None");
		}
		const parts = [];
		if (cc > 0) {
			parts.push(cc + " " + __("critical"));
		}
		if (bc > 0) {
			parts.push(bc + " " + __("total"));
		}
		return parts.join(", ");
	}

	function renderJourneyListCard(item) {
		const title = (item && item.journey_title) || "";
		const code = (item && item.journey_code) || "";
		const stage = (item && item.current_stage_label) || "";
		const next = (item && item.next_action) || __("—");
		const blockers = formatBlockersLabel(item);
		const tenderCode = (item && item.primary_object_code) || "";
		let actions =
			'<button type="button" class="btn btn-primary btn-sm plc-journey-list-open-journey" data-testid="plc-journey-list-open-journey" data-journey-code="' +
			escapeHtml(code) +
			'">' +
			escapeHtml(__("Open Journey")) +
			"</button>";
		if (tenderCode) {
			actions +=
				'<button type="button" class="btn btn-default btn-sm plc-journey-list-open-tender" data-tender-code="' +
				escapeHtml(tenderCode) +
				'">' +
				escapeHtml(__("Open Tender")) +
				"</button>";
		}
		actions +=
			'<button type="button" class="btn btn-default btn-sm plc-journey-list-view-evidence" data-journey-code="' +
			escapeHtml(code) +
			'">' +
			escapeHtml(__("View Evidence")) +
			"</button>";
		return (
			'<div class="plc-journey-list-card kt-surface">' +
			'<div class="plc-journey-list-card-title fw-semibold">' +
			escapeHtml(title) +
			"</div>" +
			'<div class="plc-journey-list-card-meta small text-muted">' +
			"<div><strong>" +
			escapeHtml(__("Current stage")) +
			":</strong> " +
			escapeHtml(stage) +
			"</div>" +
			"<div><strong>" +
			escapeHtml(__("Next action")) +
			":</strong> " +
			escapeHtml(next) +
			"</div>" +
			"<div><strong>" +
			escapeHtml(__("Blockers")) +
			":</strong> " +
			escapeHtml(blockers) +
			"</div>" +
			"</div>" +
			'<div class="plc-journey-list-card-actions">' +
			actions +
			"</div>" +
			"</div>"
		);
	}

	function applyJourneyListPanel($host, payload, emptyMessage) {
		if (!$host || !$host.length) {
			return;
		}
		const items = (payload && payload.items) || [];
		if (!items.length) {
			$host.html('<p class="text-muted small mb-0">' + escapeHtml(emptyMessage) + "</p>");
			return;
		}
		let html = "";
		for (let i = 0; i < items.length; i += 1) {
			html += renderJourneyListCard(items[i]);
		}
		$host.html(html);
	}

	function loadJourneyListPanel($page, hostTestId, apiArgs, emptyMessage) {
		const $host = $page.find('[data-testid="' + hostTestId + '"]');
		if (!$host.length) {
			return;
		}
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.list_journeys",
			args: apiArgs,
			callback: function (r) {
				if (journeyCodeFromRoute()) {
					return;
				}
				const payload = r && r.message;
				if (!payload || !Array.isArray(payload.items)) {
					applyJourneyListPanel($host, { items: [] }, emptyMessage);
					return;
				}
				applyJourneyListPanel($host, payload, emptyMessage);
			},
			error: function () {
				if (journeyCodeFromRoute()) {
					return;
				}
				$host.html(
					'<p class="text-muted small mb-0 text-danger">' +
						escapeHtml(__("Unable to load journeys.")) +
						"</p>",
				);
			},
		});
	}

	function navigateToProcurementJourney(journeyCode, focusEvidence) {
		if (!journeyCode || typeof frappe === "undefined" || !frappe.set_route) {
			return;
		}
		frappe.route_options = {};
		if (focusEvidence) {
			frappe.route_options.plc_focus = "evidence";
		}
		frappe.set_route(PAGE_NAME, journeyCode);
	}

	function ensureJourneyListDelegatedClicks($page) {
		if (!$page.length || $page.data("plcJourneyListClicks")) {
			return;
		}
		$page.data("plcJourneyListClicks", 1);
		$page.on("click.plcJourneyList", function (ev) {
			const t = ev.target;
			if (!t || !t.closest) {
				return;
			}
			const openJourney = t.closest(".plc-journey-list-open-journey");
			if (openJourney) {
				const jc = openJourney.getAttribute("data-journey-code");
				if (jc) {
					navigateToProcurementJourney(jc, false);
				}
				return;
			}
			const viewEvidence = t.closest(".plc-journey-list-view-evidence");
			if (viewEvidence) {
				const jc = viewEvidence.getAttribute("data-journey-code");
				if (jc) {
					navigateToProcurementJourney(jc, true);
				}
				return;
			}
			const openTender = t.closest(".plc-journey-list-open-tender");
			if (openTender) {
				const tc = openTender.getAttribute("data-tender-code");
				if (tc) {
					frappe.set_route("Form", "TM2 Tender", tc);
				}
			}
		});
	}

	function loadJourneyListSections($page) {
		loadJourneyListPanel($page, "plc-journeys-active-host", { status: "active", limit: 20 }, __("No active procurement journeys."));
		loadJourneyListPanel(
			$page,
			"plc-journeys-needs-action-host",
			{ status: "needs_action", scope: "my-work", limit: 20 },
			__("No journeys need your action."),
		);
		loadJourneyListPanel($page, "plc-journeys-blocked-host", { status: "blocked", limit: 20 }, __("No critical blockers."));
		loadJourneyListPanel(
			$page,
			"plc-journeys-ready-for-handoff-host",
			{ status: "ready_for_handoff", limit: 20 },
			__("No journeys ready for handoff."),
		);
	}

	function journeyCodeFromRoute() {
		try {
			const r = frappe.get_route && frappe.get_route();
			if (r && r.length >= 2) {
				const head = String(r[0] || "").toLowerCase();
				if (head === "plc-procurement-journey" && r[1]) {
					return String(r[1]).trim();
				}
			}
		} catch (e0) {
			/* ignore */
		}
		try {
			const opts = frappe.route_options || {};
			if (opts.journey_code) {
				return optionValue(opts.journey_code);
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const params = new URLSearchParams(window.location.search || "");
			if (params.has("journey_code")) {
				return optionValue(params.get("journey_code"));
			}
		} catch (e2) {
			/* ignore */
		}
		return "";
	}

	function renderNoJourneyCode(wrapper) {
		const $w = $(wrapper);
		const $outer = $('<div class="kt-plc-journey">');
		const $page = $('<div class="container py-4 plc-journey-page plc-journey-list-page">')
			.attr("data-testid", "plc-journey-page")
			.addClass("plc-journey-page--list");
		$page.append(
			$("<h4>").attr("data-testid", "plc-journeys-page-title").text(__("Procurement Journeys")),
			$("<p class='text-muted small mb-3'>")
				.attr("data-testid", "plc-journeys-page-intro")
				.text(__("Browse active procurement journeys, open a journey detail view, or jump to related tender work.")),
		);

		const section = function (title, sectionTestId, hostTestId) {
			return (
				'<section class="card plc-journey-list-section mb-3" data-testid="' +
				sectionTestId +
				'">' +
				'<div class="card-body">' +
				'<h5 class="h6 text-muted mb-2">' +
				escapeHtml(title) +
				"</h5>" +
				'<div class="plc-journey-list-host" data-testid="' +
				hostTestId +
				'">' +
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("Loading journeys…")) +
				"</p>" +
				"</div></div></section>"
			);
		};

		$page.append(
			section(__("Active Procurement Journeys"), "plc-procurement-journeys-active", "plc-journeys-active-host"),
			section(__("Needs My Action"), "plc-procurement-journeys-needs-action", "plc-journeys-needs-action-host"),
			section(__("Blocked Journeys"), "plc-procurement-journeys-blocked", "plc-journeys-blocked-host"),
			section(__("Ready for Handoff"), "plc-procurement-journeys-ready-for-handoff", "plc-journeys-ready-for-handoff-host"),
		);

		$outer.append($page);
		$w.empty().append($outer);
		ensureJourneyListDelegatedClicks($page);
		loadJourneyListSections($page);
	}

	function renderLoading(wrapper, journeyCode) {
		const $w = $(wrapper);
		const $outer = $('<div class="kt-plc-journey plc-procurement-journey-placeholder-inner">').attr(
			"data-testid",
			"plc-procurement-journey-placeholder",
		);
		const $page = $('<div class="container py-4 plc-journey-page">').attr("data-testid", "plc-journey-page");
		$page.append(
			$("<p>")
				.addClass("text-muted small mb-2")
				.attr("data-testid", "plc-journey-route-code")
				.text(journeyCode),
			$("<div>")
				.attr("data-testid", "plc-journey-header-loading")
				.addClass("py-4 text-muted")
				.text(__("Loading journey…")),
		);
		$outer.append($page);
		$w.empty().append($outer);
	}

	function renderError(wrapper, journeyCode) {
		const $w = $(wrapper);
		const $outer = $('<div class="kt-plc-journey plc-procurement-journey-placeholder-inner">').attr(
			"data-testid",
			"plc-procurement-journey-placeholder",
		);
		const $page = $('<div class="container py-4 plc-journey-page">').attr("data-testid", "plc-journey-page");
		$page.append(
			$("<p>")
				.addClass("text-muted small mb-2")
				.attr("data-testid", "plc-journey-route-code")
				.text(journeyCode),
			$("<div>")
				.attr("data-testid", "plc-journey-header-error")
				.addClass("alert alert-danger")
				.text(__("Unable to load this journey. Check permissions or try again.")),
		);
		$outer.append($page);
		$w.empty().append($outer);
	}

	function renderJourneyShell(wrapper, journeyCode, j) {
		const $w = $(wrapper);
		const title = (j && j.title) || "";
		const entity = (j && j.procuring_entity_code) || "";
		const category = (j && j.category) || "";
		const method = (j && j.method) || "";
		const stage = (j && j.current_stage) || "";
		const nextAction = (j && j.next_action) || "";

		const $outer = $('<div class="kt-plc-journey plc-procurement-journey-placeholder-inner">').attr(
			"data-testid",
			"plc-procurement-journey-placeholder",
		);
		const $page = $('<div class="container py-4 plc-journey-page">').attr("data-testid", "plc-journey-page");

		const $header = $('<div class="card plc-journey-header mb-3">').attr("data-testid", "plc-journey-header");
		const $body = $('<div class="card-body">');
		$body.append(
			$("<p>")
				.addClass("text-muted small mb-2 font-monospace")
				.attr("data-testid", "plc-journey-route-code")
				.text(journeyCode),
		);
		$body.append($("<h3>").addClass("plc-journey-title mb-3").attr("data-testid", "plc-journey-title").text(title));

		const $metaRow = $('<div class="row g-2 small mb-2">');
		const metaCell = function (label, testId, cssClass, value) {
			return $('<div class="col-md-4">')
				.append(
					$("<span>").addClass("plc-journey-meta-label").text(label),
					$("<span>")
						.addClass(cssClass)
						.attr("data-testid", testId)
						.text(value),
				);
		};
		$metaRow.append(
			metaCell(__("Procuring entity") + " ", "plc-journey-entity", "plc-journey-entity", entity),
			metaCell(__("Category") + " ", "plc-journey-category", "plc-journey-category", category),
			metaCell(__("Method") + " ", "plc-journey-method", "plc-journey-method", method),
		);
		$body.append($metaRow);

		$body.append(
			$("<div>")
				.addClass("plc-journey-current-stage mt-2")
				.attr("data-testid", "plc-journey-current-stage")
				.text(stage ? __("Current stage") + ": " + stage : ""),
		);
		$body.append(
			$("<div>")
				.addClass("plc-journey-next-action text-muted mt-2")
				.attr("data-testid", "plc-journey-next-action")
				.text(nextAction ? __("Next action") + ": " + nextAction : ""),
		);
		$header.append($body);
		$page.append($header);

		$page.append(renderCurrentFocusSection(j));

		$page.append(renderTimelineSection((j && j.steps) || []));
		$page.append(renderStepCardsSection((j && j.steps) || []));
		$page.append(renderHandoffPanelSection(j));
		$page.append(renderEvidenceTimelineSection(j));

		$outer.append($page);
		$w.empty().append($outer);
	}

	function loadAndRender(wrapper) {
		const journeyCode = journeyCodeFromRoute();
		if (!journeyCode) {
			renderNoJourneyCode(wrapper);
			return;
		}
		renderLoading(wrapper, journeyCode);
		frappe.call({
			method: "kentender_procurement.procurement_lifecycle.api.journey_api.get_journey",
			args: { journey_code: journeyCode },
			freeze: false,
			callback: function (r) {
				if (!isStillCurrentRoute(journeyCode)) {
					return;
				}
				const payload = r && r.message;
				if (!payload || r.exc) {
					renderError(wrapper, journeyCode);
					return;
				}
				renderJourneyShell(wrapper, journeyCode, payload);
			},
			error: function () {
				if (!isStillCurrentRoute(journeyCode)) {
					return;
				}
				renderError(wrapper, journeyCode);
			},
		});
	}

	function isStillCurrentRoute(expectedCode) {
		return journeyCodeFromRoute() === expectedCode;
	}

	frappe.pages[PAGE_NAME].on_page_load = function (wrapper) {
		loadAndRender(wrapper);
	};

	frappe.pages[PAGE_NAME].on_page_show = function (wrapper) {
		loadAndRender(wrapper);
	};
})();
