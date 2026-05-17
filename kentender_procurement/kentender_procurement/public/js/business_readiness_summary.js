/**
 * R6-001 / LV-R6-001-01 — **BusinessReadinessSummary** — business labels before technical refs.
 * R6-004 / NEG-TND-MISSING-DEM-001 — DEM **FAIL** rows prefer ``user_blocker_message`` (server)
 * for `plc-br-dem-blocker`; machine ``blocker_code`` is not used as primary copy.
 *
 * Renders `data-testid="plc-business-readiness-summary"` with business-first rows; technical
 * block uses `plc-tm2-readiness-technical-drawer` and pack-aligned `plc-technical-evidence-body`.
 *
 * API: `kentender_procurement.procurement_lifecycle.api.readiness_api.read_business_readiness_summary`
 */
(function () {
	frappe.provide("kentender_procurement");

	function esc(s) {
		if (s == null || s === undefined) {
			return "";
		}
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function _statusBadgeClass(status) {
		const st = String(status || "").trim();
		if (st === "Ready") {
			return "badge-success";
		}
		if (st === "Blocked") {
			return "badge-danger";
		}
		return "badge-secondary";
	}

	function _resultLabel(result) {
		const r = String(result || "").toUpperCase();
		if (r === "PASS") {
			return __("Pass");
		}
		if (r === "FAIL") {
			return __("Not met");
		}
		return String(result || "—");
	}

	/**
	 * Build the summary UI from an R3-016 payload (already authorized server-side).
	 *
	 * @param {JQuery} $host
	 * @param {object} payload
	 */
	function render($host, payload) {
		$host.empty();
		if (!payload || typeof payload !== "object") {
			$host.append(
				$("<div>")
					.addClass("text-muted small")
					.attr("data-testid", "plc-br-empty")
					.text(__("No readiness data.")),
			);
			return;
		}

		const summaryLabel = String(payload.summary_label || "").trim() || __("Readiness");
		const status = String(payload.status || "").trim() || __("—");
		const checks = Array.isArray(payload.checks) ? payload.checks : [];
		const snap = String(payload.snapshot_ref || "").trim();
		const techAvail = Boolean(payload.technical_details_available);
		const canViewTechnical =
			payload.can_view_technical_output_codes === undefined
				? true
				: Boolean(payload.can_view_technical_output_codes);

		const $root = $("<div>")
			.addClass("card plc-business-readiness-summary border")
			.attr("data-testid", "plc-business-readiness-summary");

		const $body = $('<div class="card-body py-3 px-3">');

		const $head = $('<div class="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">');
		const $title = $('<div class="min-w-0">').append(
			$("<div>")
				.addClass("h6 mb-0")
				.attr("data-testid", "plc-br-summary-label")
				.text(summaryLabel),
		);
		const $badge = $("<span>")
			.addClass(`badge ${_statusBadgeClass(status)}`)
			.attr("data-testid", "plc-br-status")
			.text(__(status));
		$head.append($title, $badge);
		$body.append($head);

		const $checks = $("<div>")
			.addClass("plc-br-checks")
			.attr("data-testid", "plc-br-business-checks");

		for (let i = 0; i < checks.length; i += 1) {
			const c = checks[i] || {};
			const bl = String(c.business_label || "").trim();
			const res = String(c.result || "").trim();
			const pass = String(res).toUpperCase() === "PASS";

			const $row = $("<div>")
				.addClass("d-flex justify-content-between align-items-start border-bottom py-2 plc-br-check-row")
				.attr("data-testid", "plc-br-check-row")
				.attr("data-technical-label", esc(String(c.technical_label || "").trim()));

			const $left = $("<div>").addClass("pr-2 min-w-0 flex-grow-1");
			$left.append(
				$("<div>")
					.addClass("font-weight-bold small")
					.attr("data-testid", "plc-br-business-label")
					.text(bl || __("—")),
			);
			if (!pass) {
				const um =
					c.user_blocker_message != null && String(c.user_blocker_message).trim()
						? String(c.user_blocker_message).trim()
						: "";
				const ra =
					c.required_action != null && String(c.required_action).trim()
						? String(c.required_action).trim()
						: "";
				const blockerText = um || ra;
				if (blockerText) {
					const isDem = String(c.technical_label || "").toUpperCase() === "DEM";
					$left.append(
						$("<div>")
							.addClass("text-muted small mt-1")
							.attr(
								"data-testid",
								isDem ? "plc-br-dem-blocker" : "plc-br-blocker-hint",
							)
							.text(blockerText),
					);
				}
			}

			const $right = $("<div>").addClass("text-nowrap small flex-shrink-0");
			const passCls = pass ? "text-success" : "text-danger";
			$right.append(
				$("<span>")
					.addClass(passCls)
					.attr("data-testid", "plc-br-result")
					.text(_resultLabel(res)),
			);

			$row.append($left, $right);
			$checks.append($row);
		}
		$body.append($checks);

		if (!canViewTechnical) {
			$body.append(
				$("<div>")
					.addClass("text-muted small border rounded px-3 py-2 mt-3")
					.attr("data-testid", "plc-br-technical-restricted")
					.text(
						__(
							"STD technical output codes are not shown for this user type. Contact procurement administration if you need Bundle / DSM / DOM / DEM / DCM references.",
						),
					),
			);
			$root.append($body);
			$host.append($root);
			return;
		}

		let techInner = "";
		for (let j = 0; j < checks.length; j += 1) {
			const c = checks[j] || {};
			const tl = String(c.technical_label || "").trim();
			const tr = String(c.technical_ref || "").trim();
			if (!tl) {
				continue;
			}
			techInner += `<div class="small plc-br-tech-line" data-testid="plc-br-technical-line"><span class="text-muted">${esc(
				tl,
			)}</span> · <span class="font-monospace plc-technical-output-code">${esc(tr || "—")}</span></div>`;
		}
		if (snap) {
			techInner += `<div class="small mt-2" data-testid="plc-br-snapshot-line"><span class="text-muted">${esc(
				__("Publication snapshot"),
			)}</span> · <span class="font-monospace">${esc(snap)}</span></div>`;
		}
		if (!techInner) {
			techInner = `<div class="text-muted small" data-testid="plc-br-no-tech">${esc(
				 __("No technical output codes recorded yet."),
			)}</div>`;
		}

		const $details = $("<details>")
			.addClass("border rounded mt-3 plc-br-technical-wrap plc-tm2-readiness-technical-drawer")
			.attr("data-testid", "plc-br-technical-collapsed");
		if (!techAvail) {
			$details.attr("data-technical-pending", "1");
		}
		$details.append(
			$("<summary>")
				.addClass("px-3 py-2 small font-weight-bold text-muted")
				.attr("data-testid", "plc-br-technical-summary")
				.text(__("Technical output codes (advanced)")),
		);
		$details.append(
			$("<div>")
				.addClass("px-3 pb-3")
				.attr("data-testid", "plc-technical-evidence-body")
				.html(techInner),
		);
		$body.append($details);

		$root.append($body);
		$host.append($root);
	}

	/**
	 * Load summary via Frappe and render into host.
	 *
	 * @param {JQuery} $host
	 * @param {{ object_type: string, object_code: string }} opts
	 */
	function mount($host, opts) {
		var ot = String((opts && opts.object_type) || "").trim();
		var oc = String((opts && opts.object_code) || "").trim();
		$host.empty();
		if (!ot || !oc) {
			return;
		}

		$host.append(
			$("<div>")
				.addClass("text-muted small py-2")
				.attr("data-testid", "plc-br-loading")
				.text(__("Loading readiness summary…")),
		);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.readiness_api.read_business_readiness_summary",
			args: { object_type: ot, object_code: oc },
			freeze: false,
			callback: function (r) {
				$host.empty();
				if (r.exc) {
					$host.append(
						$("<div>")
							.addClass("alert alert-warning py-2 px-3 mb-0 small")
							.attr("data-testid", "plc-br-error")
							.attr("data-plc-br-error-kind", "server")
							.text(
								__(
									"Unable to load business readiness. Check permissions or try again.",
								),
							),
					);
					return;
				}
				if (!r.message || typeof r.message !== "object") {
					$host.append(
						$("<div>")
							.addClass("alert alert-warning py-2 px-3 mb-0 small")
							.attr("data-testid", "plc-br-error")
							.attr("data-plc-br-error-kind", "empty")
							.text(
								__(
									"No readiness data returned. Try again or contact support.",
								),
							),
					);
					return;
				}
				render($host, r.message);
			},
			error: function () {
				$host.empty().append(
					$("<div>")
						.addClass("alert alert-warning py-2 px-3 mb-0 small")
						.attr("data-testid", "plc-br-error")
						.attr("data-plc-br-error-kind", "network")
						.text(
							__(
								"Unable to load business readiness. Check permissions or try again.",
							),
						),
				);
			},
		});
	}

	kentender_procurement.BusinessReadinessSummary = {
		render: render,
		mount: mount,
	};
})();
