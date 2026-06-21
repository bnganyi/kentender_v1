/**
 * R5-001 / LV-R5-001-01 — Shared **Module Journey Context** header for source objects.
 *
 * Calls ``get_journey_by_object`` (pack §9.2) and renders a compact card with
 * ``data-testid="plc-module-journey-context-header"``. Other modules (e.g. TM2 Tender
 * R5-010) mount the same component by invoking ``render`` on a container element.
 */
(function () {
	frappe.provide("kentender_procurement");

	function textOrDash(value) {
		var raw = String(value == null ? "" : value).trim();
		return raw || "—";
	}

	function normalizeDeskRoute(routeValue) {
		var raw = String(routeValue || "").trim();
		if (!raw) return [];
		if (raw.indexOf("/desk/") === 0) {
			raw = raw.slice("/desk/".length);
		}
		return raw
			.split("/")
			.map(function (part) {
				return String(part || "").trim();
			})
			.filter(Boolean);
	}

	function pickPlanningStep(payload, requestedStepKey) {
		var steps = (payload && payload.planning_steps) || [];
		if (!steps.length) return null;
		var targetKey = String(requestedStepKey || "").trim();
		if (!targetKey) return steps[0];
		for (var i = 0; i < steps.length; i += 1) {
			if (String(steps[i].step_key || "").trim() === targetKey) {
				return steps[i];
			}
		}
		return steps[0];
	}

	function stripTechnicalTokens(value) {
		var raw = String(value == null ? "" : value).trim();
		if (!raw) return "";
		return raw
			.replace(/\b(?:PLANINCL|PKGREL|PKGCONSUME|PKG|DEM|BUD|OBJ|JRN)-[A-Z0-9-]+\b/g, "")
			.replace(/\b(?:source_object_code|target_object_code|package_release|technical_refs_json)\b/gi, "")
			.replace(/\s{2,}/g, " ")
			.trim();
	}

	function resolvePp2StateLine(payload) {
		var packageStatus = String((payload && payload.package_status) || "").trim();
		var release = (payload && payload.planning_release) || {};
		var releaseStatus = String(release.status || "").trim().toLowerCase();
		var releaseConsumed =
			releaseStatus === "consumed" || String(release.consumed_at || "").trim().length > 0;

		if (packageStatus === "Consumed by Tender Management") {
			return __("Procurement planned · Continue in Tender Management");
		}
		if (packageStatus === "Released to Tender") {
			if (releaseConsumed) {
				return __("Procurement planned · Tender Management has consumed the released package");
			}
			return __("Released to Tender · Awaiting Tender Management consumption");
		}
		if (packageStatus === "Ready for Release") {
			return __("Ready for release · Release package to Tender Management");
		}
		if (packageStatus === "In Review") {
			return __("Package in review · Waiting for planning approval");
		}
		if (packageStatus === "Draft" || packageStatus === "Returned for Correction") {
			return __("Package draft · Complete package details");
		}
		if (packageStatus === "Approved") {
			return __("Included in plan · Package not created yet");
		}
		return __("Procurement planned · No action required in Planning");
	}

	function syncTechnicalDetailsToggle($details, $summary) {
		if ($details.prop("open")) {
			$summary.text(__("Hide technical details"));
			return;
		}
		$summary.text(__("Show technical details"));
	}

	function renderPp2($host, opts) {
		var packageCode = String((opts && opts.package_code) || "").trim();
		var stepKey = String((opts && opts.step_key) || "").trim();
		$host.empty();
		if (!packageCode) {
			$host.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "pp2-module-journey-missing-params")
					.text(__("Journey context is unavailable because package_code is missing.")),
			);
			return;
		}

		var requestToken = String(Date.now()) + ":" + String(Math.random()).slice(2);
		var $card = $('<div class="card plc-module-journey-context-header pp2-module-journey-context-header mb-0">')
			.attr("data-testid", "pp2-module-journey-context-header")
			.attr("data-package-code", packageCode)
			.attr("data-request-token", requestToken);
		var $body = $('<div class="card-body py-2 px-3">');
		$body.append(
			$("<div>")
				.addClass("text-muted small")
				.attr("data-testid", "pp2-module-journey-loading")
				.text(__("Loading planning journey context…")),
		);
		$card.append($body);
		$host.append($card);

		function renderPayload(payload) {
			if (!$card.closest("body").length) return;
			if ($card.attr("data-request-token") !== requestToken) return;
			$body.empty();
			var journey = (payload && payload.journey) || {};
			var inclusion = (payload && payload.planning_inclusion) || {};
			var release = (payload && payload.planning_release) || {};
			var step = pickPlanningStep(payload || {}, stepKey) || {};
			var title =
				stripTechnicalTokens(journey.journey_title || journey.title) ||
				__("Procurement planning progress");
			var stateLine = resolvePp2StateLine(payload);
			var openRoute = String(journey.open_route || "").trim();
			var tenderOpenRoute = String(release.tender_open_route || "").trim();

			var $titleRow = $('<div class="pp2-module-journey-title-row d-flex flex-wrap align-items-start justify-content-between gap-2">');
			$titleRow.append(
				$("<div>")
					.addClass("fw-semibold plc-module-journey-context-title min-w-0 flex-grow-1")
					.attr("data-testid", "pp2-module-journey-title")
					.text(title),
			);

			var $actions = $('<div class="pp2-module-journey-actions d-flex flex-wrap align-items-center gap-2 flex-shrink-0">');
			if (tenderOpenRoute) {
				$actions.append(
					$('<a href="#" class="btn btn-sm btn-default">')
						.attr("data-testid", "pp2-module-journey-open-tender")
						.attr("data-open-route", tenderOpenRoute)
						.text(__("Open Tender"))
						.on("click", function (ev) {
							ev.preventDefault();
							var deskParts = normalizeDeskRoute(tenderOpenRoute);
							if (deskParts.length) {
								frappe.set_route(deskParts);
							}
						}),
				);
			}
			$actions.append(
				$('<a href="#" class="btn btn-sm btn-primary">')
					.attr("data-testid", "pp2-module-journey-open")
					.attr("data-open-route", openRoute || "")
					.text(__("Open Procurement Journey"))
					.on("click", function (ev) {
						ev.preventDefault();
						var deskParts = normalizeDeskRoute(openRoute);
						if (deskParts.length) {
							frappe.set_route(deskParts);
							return;
						}
						if (journey.journey_code) {
							frappe.set_route("plc-procurement-journey", journey.journey_code);
							return;
						}
						frappe.set_route("plc-procurement-journey");
					}),
			);
			$titleRow.append($actions);

			var $stateLine = $("<div>")
				.addClass("pp2-module-journey-state-line text-muted small mt-1")
				.attr("data-testid", "pp2-module-journey-state-line")
				.text(stateLine);

			var $summary = $("<summary>")
				.addClass("pp2-module-journey-technical-toggle")
				.attr("data-testid", "pp2-module-journey-technical-toggle")
				.text(__("Show technical details"));
			var $technicalDetails = $("<details>")
				.addClass("pp2-module-journey-technical-details text-muted small mt-1")
				.attr("data-testid", "pp2-module-journey-technical-details")
				.append($summary)
				.append(
					$("<div>")
						.addClass("pp2-module-journey-technical-body mt-1")
						.append(
							$("<div>").text(__("Technical details")),
						)
						.append(
							$("<div>").text(
								__("Stage key") +
									": " +
									textOrDash(step.step_key) +
									" | " +
									__("Journey code") +
									": " +
									textOrDash(journey.journey_code) +
									" | " +
									__("Inclusion handoff") +
									": " +
									textOrDash(inclusion.handoff_code) +
									" | " +
									__("Release handoff") +
									": " +
									textOrDash(release.handoff_code),
							),
						),
				);
			$technicalDetails.on("toggle", function () {
				syncTechnicalDetailsToggle($technicalDetails, $summary);
			});
			syncTechnicalDetailsToggle($technicalDetails, $summary);

			$body.append($titleRow, $stateLine, $technicalDetails);
		}

		frappe.call({
			method: "kentender_procurement.procurement_planning.api.planning_journey.get_pp_planning_journey_handoffs",
			args: { package_code: packageCode },
			freeze: false,
			callback: function (r) {
				var payload = (r && r.message) || {};
				if (r.exc || !payload || payload.ok === false) {
					renderPayload({});
					return;
				}
				renderPayload(payload);
			},
			error: function () {
				renderPayload({});
			},
		});
	}

	function render($host, opts) {
		if (opts && opts.variant === "pp2") {
			renderPp2($host, opts);
			return;
		}
		var ot = String((opts && opts.object_type) || "").trim();
		var oc = String((opts && opts.object_code) || "").trim();
		$host.empty();

		if (!ot || !oc) {
			$host.append(
				$("<p>")
					.addClass("text-muted small mb-0")
					.attr("data-testid", "plc-module-journey-context-missing-params")
					.text(
						__(
							"Provide object_type and object_code (e.g. query string on the smoke page).",
						),
					),
			);
			return;
		}

		var $card = $('<div class="card plc-module-journey-context-header mb-0">')
			.attr("data-testid", "plc-module-journey-context-header")
			.attr("data-object-type", ot)
			.attr("data-object-code", oc);

		var $body = $('<div class="card-body py-2 px-3">');
		$body.append(
			$("<div>")
				.addClass("text-muted small")
				.attr("data-testid", "plc-module-journey-context-loading")
				.text(__("Loading journey context…")),
		);
		$card.append($body);
		$host.append($card);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.journey_api.get_journey_by_object",
			args: { object_type: ot, object_code: oc },
			freeze: false,
			callback: function (r) {
				var payload = r && r.message;
				$body.empty();
				if (!payload || r.exc) {
					$body.append(
						$("<div>")
							.addClass("text-muted small")
							.attr("data-testid", "plc-module-journey-context-empty")
							.text(
								__(
									"No Procurement Journey is linked to this object, or you do not have access.",
								),
							),
					);
					return;
				}
				var jcode = String(payload.journey_code || "").trim();
				var title = String(payload.title || "").trim() || jcode;
				var stage = String(payload.current_stage || "").trim();
				var entity = String(payload.procuring_entity_code || "").trim();

				var $row = $('<div class="d-flex flex-wrap align-items-start justify-content-between gap-2">');
				var $left = $('<div class="min-w-0 flex-grow-1">');
				$left.append(
					$("<div>")
						.addClass("fw-semibold plc-module-journey-context-title")
						.attr("data-testid", "plc-module-journey-context-title")
						.text(title),
				);
				if (jcode) {
					$left.append(
						$("<div>")
							.addClass("text-muted small font-monospace")
							.attr("data-testid", "plc-module-journey-context-code")
							.text(jcode),
					);
				}
				if (entity) {
					$left.append(
						$("<div>")
							.addClass("text-muted small")
							.attr("data-testid", "plc-module-journey-context-entity")
							.text(entity),
					);
				}
				if (stage) {
					$left.append(
						$("<div>")
							.addClass("text-muted small mt-1")
							.attr("data-testid", "plc-module-journey-context-stage")
							.text(__("Current stage") + ": " + stage),
					);
				}

				var $btn = $('<a href="#" class="btn btn-sm btn-primary flex-shrink-0">')
					.attr("data-testid", "plc-module-journey-context-open")
					.text(__("Open journey"))
					.on("click", function (ev) {
						ev.preventDefault();
						if (jcode) {
							frappe.set_route("plc-procurement-journey", jcode);
						}
					});

				$row.append($left, $btn);
				$body.append($row);
			},
			error: function () {
				$body.empty().append(
					$("<div>")
						.addClass("alert alert-warning py-2 px-3 mb-0 small")
						.attr("data-testid", "plc-module-journey-context-error")
						.text(
							__(
								"Unable to load journey context. Check permissions or try again.",
							),
						),
				);
			},
		});
	}

	kentender_procurement.ModuleJourneyContextHeader = { render: render };
})();
