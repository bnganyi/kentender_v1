/**
 * P5-005 — Shared PlanningHandoffCard for Inclusion / Release / Consumption.
 */
(function () {
	frappe.provide("kentender_procurement");

	const TECHNICAL_ROLES = {
		Auditor: true,
		"Planning Authority": true,
		Administrator: true,
		"System Manager": true,
	};

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function textOrDash(value) {
		const raw = String(value == null ? "" : value).trim();
		return raw || "—";
	}

	function stripTechnicalCodes(value) {
		const raw = String(value == null ? "" : value).trim();
		if (!raw) return "";
		return raw
			.replace(/\s*\(([A-Z]{2,}(?:-[A-Z0-9]+){1,})\)\s*/g, " ")
			.replace(/\b(?:PLANINCL|PKGREL|PKGCONSUME|JRN|TND|DEM|PKG)-[A-Z0-9-]+\b/g, "")
			.replace(/\s{2,}/g, " ")
			.trim();
	}

	function normalizeHandoffStatus(status, kind) {
		const raw = String(status || "").trim();
		const key = raw.toLowerCase();
		if (kind === "release") {
			if (key === "consumed") return __("Consumed by Tender Management");
			if (key === "handed off") return __("Sent to Tender Management");
		}
		if (kind === "consumption" && key === "consumed") {
			return __("Consumed");
		}
		if (kind === "inclusion" && key === "packaged") {
			return __("Packaged");
		}
		return raw || "—";
	}

	function summarizeProtectedText(card) {
		const kind = String((card && card.kind) || "").trim().toLowerCase();
		if (kind === "release") {
			return __(
				"Method, category, scope, funding, estimated value, and package lines are locked.",
			);
		}
		if (kind === "inclusion") {
			return __("Demand details and procurement plan linkage are locked.");
		}
		if (kind === "consumption") {
			return __("Planning release record is consumed and locked for audit.");
		}
		return __("Protected planning values are locked.");
	}

	function buildWhatHappened(card) {
		const kind = String((card && card.kind) || "").trim().toLowerCase();
		if (kind === "inclusion") {
			return __("Approved demand was included in the procurement plan.");
		}
		if (kind === "release") {
			return __("Planning released this package to Tender Management.");
		}
		if (kind === "consumption") {
			return __("Tender Management consumed the planning release package.");
		}
		const sourceLabel = stripTechnicalCodes(card.source_label || "") || stripTechnicalCodes(card.source_object_type);
		const targetLabel = stripTechnicalCodes(card.target_label || "") || stripTechnicalCodes(card.target_object_type);
		return textOrDash(sourceLabel || targetLabel);
	}

	function buildWhatNext(card) {
		const kind = String((card && card.kind) || "").trim().toLowerCase();
		const targetLabel = stripTechnicalCodes(card.target_label || "") || stripTechnicalCodes(card.target_object_type);
		if (kind === "inclusion") {
			return __("Continue package preparation and readiness checks.");
		}
		if (kind === "release") {
			return __("Continue in Tender Management.") + (targetLabel ? " " + targetLabel : "");
		}
		if (kind === "consumption") {
			return __("Open the tender to continue procurement execution.") + (targetLabel ? " " + targetLabel : "");
		}
		return textOrDash(targetLabel);
	}

	function statusClass(kind, status) {
		const s = String(status || "").trim().toLowerCase();
		if (kind === "consumption") return "is-consumed";
		if (s.indexOf("consumed") >= 0) return "is-consumed";
		if (s.indexOf("returned") >= 0 || s.indexOf("stale") >= 0) return "is-warning";
		if (s.indexOf("included") >= 0 || s.indexOf("packaged") >= 0 || s.indexOf("handed off") >= 0) {
			return "is-info";
		}
		return "is-neutral";
	}

	function summaryLines(raw) {
		if (!raw || typeof raw !== "object") return [];
		return Object.keys(raw).map(function (key) {
			return textOrDash(key) + ": " + textOrDash(raw[key]);
		});
	}

	function resolveMayViewTechnical(opts) {
		if (opts && typeof opts.may_view_technical === "boolean") {
			return opts.may_view_technical;
		}
		try {
			const roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
			for (let i = 0; i < roles.length; i += 1) {
				if (TECHNICAL_ROLES[roles[i]]) return true;
			}
		} catch (e) {
			/* ignore */
		}
		return false;
	}

	function normalizeDeskRoute(routeValue) {
		const raw = String(routeValue || "").trim();
		if (!raw) return [];
		if (raw.indexOf("/desk/") === 0) {
			return raw
				.slice("/desk/".length)
				.split("/")
				.map(function (part) {
					return String(part || "").trim();
				})
				.filter(Boolean);
		}
		return raw
			.split("/")
			.map(function (part) {
				return String(part || "").trim();
			})
			.filter(Boolean);
	}

	function render(card, opts) {
		const c = card || {};
		const o = opts || {};
		const kind = String(c.kind || "release").trim().toLowerCase();
		const kindTitle = {
			inclusion: __("Approved demand included in procurement plan"),
			release: __("Package released to Tender Management"),
			consumption: __("Tender Management consumed the package"),
		};
		const title = textOrDash(kindTitle[kind] || c.title || c.handoff_title);
		const status = normalizeHandoffStatus(c.status, kind);
		const whatHappened = buildWhatHappened(c);
		const whatProtected = summarizeProtectedText(c);
		const whatNext = buildWhatNext(c);
		const openRoute = String(c.open_route || "").trim();
		const actionText = String(o.action_text || (kind === "release" ? __("Open Tender") : __("Open"))).trim();
		const packageCode = String(o.package_code || c.package_code || "").trim();
		const evidenceHref =
			"/desk/procurement-planning" +
			(packageCode ? "?package_code=" + encodeURIComponent(packageCode) : "");
		const mayViewTechnical = resolveMayViewTechnical(o);

		let actionHtml = "";
		if (openRoute) {
			actionHtml =
				'<a href="#" class="btn btn-xs btn-default pp2-handoff-card-open-link" data-testid="pp2-handoff-card-open" data-open-route="' +
				esc(openRoute) +
				'">' +
				esc(actionText) +
				"</a>";
		}

		let technicalHtml = "";
		if (mayViewTechnical) {
			const lockedLines = summaryLines(c.locked_summary);
			const passedLines = summaryLines(c.passed_forward_summary);
			technicalHtml =
				'<details class="pp2-planning-handoff-card__meta text-muted" data-testid="pp2-handoff-card-technical-details">' +
				'<summary data-testid="pp2-planning-handoff-technical-toggle">' +
				esc(__("Technical details")) +
				"</summary>" +
				(c.handoff_code
					? '<div data-testid="pp2-handoff-card-handoff-code">' +
						esc(__("Handoff code")) +
						": " +
						esc(c.handoff_code) +
						"</div>"
					: "") +
				(c.source_object_code
					? '<div data-testid="pp2-handoff-card-source-code">' +
						esc(__("Source object")) +
						": " +
						esc(c.source_object_code) +
						"</div>"
					: "") +
				(c.target_object_code
					? '<div data-testid="pp2-handoff-card-target-code">' +
						esc(__("Target object")) +
						": " +
						esc(c.target_object_code) +
						"</div>"
					: "") +
				(lockedLines.length
					? '<div data-testid="pp2-handoff-card-locked-summary">' +
						esc(__("Locked")) +
						": " +
						esc(lockedLines.join(" | ")) +
						"</div>"
					: "") +
				(passedLines.length
					? '<div data-testid="pp2-handoff-card-passed-summary">' +
						esc(__("Passed forward")) +
						": " +
						esc(passedLines.join(" | ")) +
						"</div>"
					: "") +
				"</details>";
		}

		return (
			'<article class="pp2-planning-handoff-card ' +
			statusClass(kind, status) +
			'" data-testid="pp2-planning-handoff-card" data-handoff-kind="' +
			esc(kind) +
			'" data-handoff-view-mode="business">' +
			'<div data-testid="pp2-planning-handoff-business-mode">' +
			'<div class="pp2-planning-handoff-card__head">' +
			'<div class="pp2-planning-handoff-card__title" data-testid="pp2-handoff-card-title">' +
			esc(title) +
			"</div>" +
			'<span class="pp2-planning-handoff-card__status" data-testid="pp2-handoff-card-status">' +
			esc(status) +
			"</span>" +
			"</div>" +
			'<div class="pp2-planning-handoff-card__line" data-testid="pp2-handoff-what-happened">' +
			'<span class="text-muted">' +
			esc(__("What happened")) +
			": </span>" +
			esc(whatHappened) +
			"</div>" +
			'<div class="pp2-planning-handoff-card__line" data-testid="pp2-handoff-what-protected">' +
			'<span class="text-muted">' +
			esc(__("What is protected")) +
			": </span>" +
			esc(whatProtected) +
			"</div>" +
			'<div class="pp2-planning-handoff-card__line" data-testid="pp2-handoff-what-next">' +
			'<span class="text-muted">' +
			esc(__("What happens next")) +
			": </span>" +
			esc(whatNext) +
			"</div>" +
			(actionHtml
				? '<div class="pp2-planning-handoff-card__actions" data-testid="pp2-handoff-card-actions">' +
					esc(__("Action")) +
					": " +
					actionHtml +
					"</div>"
				: "") +
			'<div class="pp2-planning-handoff-card__evidence" data-testid="pp2-handoff-evidence-link">' +
			'<span class="text-muted">' +
			esc(__("Evidence")) +
			": </span>" +
			'<a href="' +
			esc(evidenceHref) +
			'" data-testid="pp2-handoff-view-evidence">' +
			esc(__("View Evidence")) +
			"</a>" +
			"</div>" +
			"</div>" +
			technicalHtml +
			"</article>"
		);
	}

	function renderTo($host, card, opts) {
		const $target = $host && $host.jquery ? $host : $(String($host || ""));
		if (!$target || !$target.length) return;
		$target.html(render(card, opts));
		const openLink = $target.find('[data-testid="pp2-handoff-card-open"]');
		if (openLink.length) {
			openLink.on("click", function (ev) {
				ev.preventDefault();
				const route = String(openLink.attr("data-open-route") || "").trim();
				const deskParts = normalizeDeskRoute(route);
				if (deskParts.length && frappe.set_route) {
					frappe.set_route(deskParts);
				}
			});
		}
	}

	kentender_procurement.PlanningHandoffCard = {
		render: render,
		renderTo: renderTo,
		normalizeHandoffStatus: normalizeHandoffStatus,
	};
})();
