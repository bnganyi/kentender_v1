// Budget & Funding MVP-1 — live API binders (Stitch shells + frappe.call).
frappe.provide("kentender_budget.live");

(function () {
	"use strict";

	var API = "kentender_budget.api.budget_api";

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: API + "." + method,
				args: args || {},
				freeze: false,
				callback: function (r) {
					if (r && r.exc) {
						reject(r.exc);
						return;
					}
					resolve(r && r.message);
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function esc(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}

	function statusDotClass(status) {
		if (status === "Active") {
			return "bg-status-available";
		}
		if (status === "Submitted") {
			return "bg-status-reserved";
		}
		return "bg-outline";
	}

	function statusTextClass(status) {
		if (status === "Active") {
			return "text-status-available";
		}
		if (status === "Submitted") {
			return "text-status-reserved";
		}
		return "text-on-surface-variant";
	}

	function availableClass(row) {
		if (row.status === "Active") {
			return "text-status-available font-bold";
		}
		if (row.status === "Closed") {
			return "text-on-surface";
		}
		return "text-on-surface-variant";
	}

	function attentionHtml(row) {
		var note = (row.attention || "None").trim();
		if (!note || note === "None") {
			return '<td class="px-4 py-3 align-top text-on-surface-variant text-sm italic">None</td>';
		}
		var icon = row.attention_kind === "info" ? "info" : "warning";
		return (
			'<td class="px-4 py-3 align-top">' +
			'<div class="flex items-start gap-2 text-status-reserved bg-status-reserved/10 px-2 py-1 rounded text-xs">' +
			'<span class="material-symbols-outlined text-[16px] shrink-0">' +
			icon +
			"</span>" +
			"<span>" +
			esc(note) +
			"</span></div></td>"
		);
	}

	function actionIcon(action) {
		if (action === "review") {
			return "rule";
		}
		if (action === "view") {
			return "visibility";
		}
		return "arrow_forward";
	}

	function renderBudgetRows(rows) {
		if (!rows || !rows.length) {
			return "";
		}
		return rows
			.map(function (row) {
				var muted = row.status === "Closed" ? " opacity-70" : "";
				var highlight = row.status === "Submitted" ? " bg-surface-container-low/30" : "";
				return (
					'<tr class="hover:bg-surface-container/50 transition-colors group' +
					muted +
					highlight +
					'" data-budget-code="' +
					esc(row.code) +
					'" data-budget-id="' +
					esc(row.id) +
					'">' +
					'<td class="px-4 py-3 align-top">' +
					'<div class="font-medium text-on-surface" title="' +
					esc(row.title) +
					'">' +
					esc(row.title) +
					"</div>" +
					'<div class="text-xs text-on-surface-variant mt-1 flex items-center gap-1 font-data-mono" data-kt-bud-ref="' +
					esc(row.code) +
					'">' +
					esc(row.code) +
					"</div></td>" +
					'<td class="px-4 py-3 align-top whitespace-nowrap font-data-mono text-data-mono text-on-surface-variant">' +
					esc(row.fiscal_period) +
					"</td>" +
					'<td class="px-4 py-3 align-top whitespace-nowrap text-on-surface-variant">' +
					esc(row.registration_source_label || row.registration_source || "") +
					"</td>" +
					'<td class="px-4 py-3 align-top whitespace-nowrap text-right font-data-mono text-data-mono text-on-surface">' +
					esc(row.approved_display) +
					"</td>" +
					'<td class="px-4 py-3 align-top whitespace-nowrap text-right font-data-mono text-data-mono ' +
					availableClass(row) +
					'">' +
					esc(row.available_display) +
					"</td>" +
					'<td class="px-4 py-3 align-top whitespace-nowrap">' +
					'<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-surface-container-highest ' +
					statusTextClass(row.status) +
					' text-xs font-bold uppercase tracking-wide">' +
					'<div class="w-1.5 h-1.5 rounded-full ' +
					statusDotClass(row.status) +
					'"></div>' +
					esc(row.status_label || row.status) +
					"</span></td>" +
					attentionHtml(row) +
					'<td class="px-4 py-3 align-top text-right">' +
					'<button type="button" class="' +
					(row.action_muted || row.action === "view"
						? "text-on-surface-variant hover:text-on-surface"
						: "text-primary hover:text-secondary") +
					' font-medium text-sm flex items-center justify-end gap-1 ml-auto" data-kt-bud-action="' +
					esc(row.action) +
					'" data-kt-bud-route="' +
					esc(row.action === "review" ? "budget-review/" : "budget-overview/") +
					esc(row.code) +
					'" data-budget-code="' +
					esc(row.code) +
					'">' +
					esc(row.action_label || "Open") +
					' <span class="material-symbols-outlined text-[16px]">' +
					actionIcon(row.action) +
					"</span></button></td></tr>"
				);
			})
			.join("");
	}

	function applyStrip($root, counts) {
		counts = counts || {};
		["active", "awaiting_review", "returned", "funding_exceptions"].forEach(function (key) {
			$root.find('[data-kt-bud-count="' + key + '"]').text(
				counts[key] != null ? String(counts[key]) : "0"
			);
		});
	}

	function showEmpty($root, empty) {
		var $wrap = $root.find("[data-kt-bud-table-wrap]");
		var $empty = $root.find("[data-kt-bud-empty]");
		if (empty) {
			$wrap.addClass("hidden");
			$empty.removeClass("hidden");
		} else {
			$wrap.removeClass("hidden");
			$empty.addClass("hidden");
		}
	}

	function readFilters($root) {
		return {
			search: ($root.find('[data-kt-bud-filter="search"]').val() || "").trim(),
			fiscal_period: $root.find('[data-kt-bud-filter="fiscal_period"]').val() || "",
			status: $root.find('[data-kt-bud-filter="status"]').val() || "",
			registration_source: $root.find('[data-kt-bud-filter="registration_source"]').val() || "",
		};
	}

	function renderTable($root, rows) {
		var $tbody = $root.find("[data-kt-bud-budgets-tbody]");
		if (!rows || !rows.length) {
			showEmpty($root, true);
			$tbody.html("");
			if (
				window.kentender_core &&
				kentender_core.table &&
				typeof kentender_core.table.attachPagination === "function"
			) {
				kentender_core.table
					.attachPagination($root, {
						renderPage: function () {
							$tbody.html("");
						},
					})
					.setRows([], true);
			}
			return;
		}
		showEmpty($root, false);
		if (
			window.kentender_core &&
			kentender_core.table &&
			typeof kentender_core.table.attachPagination === "function"
		) {
			kentender_core.table
				.attachPagination($root, {
					renderPage: function (pageRows) {
						$tbody.html(renderBudgetRows(pageRows));
					},
				})
				.setRows(rows, true);
			return;
		}
		$tbody.html(renderBudgetRows(rows));
	}

	function bindPortfolio($root) {
		var token = Number($root.attr("data-kt-bud-bind-token") || 0) + 1;
		$root.attr("data-kt-bud-bind-token", String(token));
		$root.attr("data-kt-bud-live", "0");

		function reloadTable() {
			var filters = readFilters($root);
			return call("list_budgets", filters).then(function (rows) {
				if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
					return;
				}
				renderTable($root, rows || []);
			});
		}

		return call("get_budget_portfolio")
			.then(function (data) {
				if (!data) {
					throw new Error("Empty portfolio payload");
				}
				if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
					return data;
				}
				$root.attr("data-kt-bud-live", "1");
				applyStrip($root, data.counts);
				renderTable($root, data.budgets || []);

				var canRegister = !!(data.capabilities && data.capabilities.register_budget);
				var $reg = $root.find('[data-kt-bud-action="register-budget"]');
				if (!canRegister) {
					$reg.addClass("hidden").attr("disabled", "disabled").attr("aria-hidden", "true");
				} else {
					$reg.removeClass("hidden").removeAttr("disabled").attr("aria-hidden", "false");
				}

				var debounce = null;
				$root.off(".ktBudPfLive");
				$root.on("input.ktBudPfLive", '[data-kt-bud-filter="search"]', function () {
					clearTimeout(debounce);
					debounce = setTimeout(function () {
						reloadTable().catch(function (err) {
							console.warn("Budget portfolio filter failed", err);
						});
					}, 250);
				});
				$root.on(
					"change.ktBudPfLive",
					'[data-kt-bud-filter="fiscal_period"], [data-kt-bud-filter="status"], [data-kt-bud-filter="registration_source"]',
					function () {
						reloadTable().catch(function (err) {
							console.warn("Budget portfolio filter failed", err);
						});
					}
				);
				return data;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				$root.find("[data-kt-bud-budgets-tbody]").html(
					'<tr data-kt-bud-error-row="1"><td class="py-6 px-4 text-body-md text-error" colspan="8">' +
						esc(__("Could not load budgets. Refresh and try again.")) +
						"</td></tr>"
				);
				console.warn("Budget portfolio bind failed", err);
			});
	}

	function clearRegisterErrors($root) {
		$root.find("[data-kt-bud-error]").addClass("hidden").text("");
	}

	function showRegisterErrors($root, errors) {
		errors = errors || {};
		Object.keys(errors).forEach(function (key) {
			var $el = $root.find('[data-kt-bud-error="' + key + '"]');
			if ($el.length) {
				$el.text(errors[key] || "").removeClass("hidden");
			}
		});
	}

	function formatMoneyInput(raw) {
		var cleaned = String(raw == null ? "" : raw).replace(/[^\d.]/g, "");
		if (!cleaned) {
			return "";
		}
		var parts = cleaned.split(".");
		var whole = parts[0] || "0";
		var frac = parts.length > 1 ? parts.slice(1).join("").slice(0, 2) : "";
		var withCommas = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
		return frac ? withCommas + "." + frac : withCommas;
	}

	function readRegisterPayload($root) {
		return {
			title: ($root.find('[data-kt-bud-field="title"]').val() || "").trim(),
			fiscal_period: ($root.find('[data-kt-bud-field="fiscal_period"]').val() || "").trim(),
			currency: ($root.find('[data-kt-bud-field="currency"]').val() || "").trim(),
			budget_owner: ($root.find('[data-kt-bud-field="budget_owner"]').val() || "").trim(),
			authoritative_reference: (
				$root.find('[data-kt-bud-field="authoritative_reference"]').val() || ""
			).trim(),
			approval_date: ($root.find('[data-kt-bud-field="approval_date"]').val() || "").trim(),
			external_approved_total: (
				$root.find('[data-kt-bud-field="external_approved_total"]').val() || ""
			).trim(),
			approval_evidence: ($root.find('[data-kt-bud-field="approval_evidence"]').val() || "").trim(),
		};
	}

	function setEvidence($root, fileUrl, fileName) {
		$root.find('[data-kt-bud-field="approval_evidence"]').val(fileUrl || "");
		var $chip = $root.find("[data-kt-bud-evidence-chip]");
		var $drop = $root.find('[data-testid="kt-bud-evidence-dropzone"]');
		if (fileUrl) {
			$root.find("[data-kt-bud-evidence-name]").text(fileName || fileUrl);
			$chip.removeClass("hidden");
			$drop.addClass("hidden");
		} else {
			$root.find("[data-kt-bud-evidence-name]").text("");
			$chip.addClass("hidden");
			$drop.removeClass("hidden");
			var $file = $root.find('[data-kt-bud-field="approval_evidence_file"]');
			if ($file.length) {
				$file.val("");
			}
		}
	}

	function uploadEvidenceFile($root, file) {
		if (!file) {
			return Promise.resolve();
		}
		var maxBytes = 10 * 1024 * 1024;
		if (file.size > maxBytes) {
			showRegisterErrors($root, {
				approval_evidence: __("File must be 10MB or smaller"),
			});
			return Promise.reject(new Error("file too large"));
		}
		return new Promise(function (resolve, reject) {
			var fd = new FormData();
			fd.append("file", file, file.name);
			fd.append("is_private", "1");
			fd.append("folder", "Home/Attachments");
			var xhr = new XMLHttpRequest();
			xhr.open("POST", "/api/method/upload_file", true);
			xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token || "");
			xhr.setRequestHeader("Accept", "application/json");
			xhr.onload = function () {
				var body = null;
				try {
					body = JSON.parse(xhr.responseText || "{}");
				} catch (err) {
					reject(err);
					return;
				}
				if (xhr.status >= 400 || (body && body.exc)) {
					reject(body || new Error("Upload failed"));
					return;
				}
				var fileDoc = (body && body.message) || body || {};
				var url = fileDoc.file_url || "";
				var name = fileDoc.file_name || file.name;
				if (!url) {
					reject(new Error("Upload returned no file_url"));
					return;
				}
				setEvidence($root, url, name);
				$root.find('[data-kt-bud-error="approval_evidence"]').addClass("hidden").text("");
				resolve(fileDoc);
			};
			xhr.onerror = function () {
				reject(new Error("Upload network error"));
			};
			xhr.send(fd);
		});
	}

	function bindRegister($root) {
		$root.attr("data-kt-bud-live", "0");
		clearRegisterErrors($root);
		setEvidence($root, "", "");

		return call("get_register_form_context")
			.then(function (ctx) {
				if (!ctx) {
					throw new Error("Empty register context");
				}
				$root.attr("data-kt-bud-live", "1");
				var pe = ctx.procuring_entity || {};
				$root
					.find('[data-kt-bud-field="procuring_entity_label"]')
					.val(pe.name || pe.code || "");

				var periods = ctx.fiscal_periods || [];
				var $fy = $root.find('[data-kt-bud-field="fiscal_period"]');
				if (periods.length) {
					var html = periods
						.map(function (p) {
							return (
								'<option value="' +
								esc(p.value) +
								'">' +
								esc(p.label || p.value) +
								"</option>"
							);
						})
						.join("");
					$fy.html(html);
				}
				var defaults = ctx.defaults || {};
				if (defaults.fiscal_period) {
					$fy.val(defaults.fiscal_period);
				}
				var $cur = $root.find('[data-kt-bud-field="currency"]');
				var currencies = ctx.currencies || ["KES", "USD"];
				$cur.html(
					currencies
						.map(function (c) {
							return '<option value="' + esc(c) + '">' + esc(c) + "</option>";
						})
						.join("")
				);
				$cur.val(defaults.currency || "KES");
				$root.find("[data-kt-bud-currency-prefix]").text($cur.val() || "KES");
				if (defaults.budget_owner) {
					$root.find('[data-kt-bud-field="budget_owner"]').val(defaults.budget_owner);
				}
				if (defaults.title) {
					$root.find('[data-kt-bud-field="title"]').val(defaults.title);
				}

				$root.off(".ktBudReg");
				$root.on("change.ktBudReg", '[data-kt-bud-field="currency"]', function () {
					$root.find("[data-kt-bud-currency-prefix]").text($(this).val() || "KES");
				});
				$root.on("blur.ktBudReg", '[data-kt-bud-field="external_approved_total"]', function () {
					var $inp = $(this);
					$inp.val(formatMoneyInput($inp.val()));
				});
				$root.on("click.ktBudReg", '[data-kt-bud-action="cancel"]', function (e) {
					e.preventDefault();
					frappe.set_route("budget-funding");
				});
				$root.on("click.ktBudReg", '[data-kt-bud-action="clear-evidence"]', function (e) {
					e.preventDefault();
					setEvidence($root, "", "");
				});
				$root.on(
					"click.ktBudReg keydown.ktBudReg",
					'[data-kt-bud-action="pick-evidence"]',
					function (e) {
						if (e.type === "keydown" && e.key !== "Enter" && e.key !== " ") {
							return;
						}
						e.preventDefault();
						var $file = $root.find('[data-kt-bud-field="approval_evidence_file"]');
						if ($file.length) {
							$file.trigger("click");
						}
					}
				);
				$root.on("change.ktBudReg", '[data-kt-bud-field="approval_evidence_file"]', function () {
					var file = this.files && this.files[0];
					if (!file) {
						return;
					}
					uploadEvidenceFile($root, file).catch(function (err) {
						console.warn("Evidence upload failed", err);
						frappe.show_alert({
							message: __("Could not upload evidence"),
							indicator: "red",
						});
					});
				});
				$root.on("dragover.ktBudReg drop.ktBudReg", '[data-testid="kt-bud-evidence-dropzone"]', function (e) {
					e.preventDefault();
					e.stopPropagation();
					if (e.type !== "drop") {
						return;
					}
					var dt = e.originalEvent && e.originalEvent.dataTransfer;
					var file = dt && dt.files && dt.files[0];
					if (!file) {
						return;
					}
					uploadEvidenceFile($root, file).catch(function (err) {
						console.warn("Evidence upload failed", err);
					});
				});
				$root.on("click.ktBudReg", '[data-kt-bud-action="create-draft"]', function (e) {
					e.preventDefault();
					clearRegisterErrors($root);
					var payload = readRegisterPayload($root);
					var $btn = $root.find('[data-kt-bud-action="create-draft"]');
					$btn.prop("disabled", true);
					call("register_budget", { payload: payload })
						.then(function (result) {
							if (!result || !result.ok) {
								showRegisterErrors($root, (result && result.errors) || {});
								$btn.prop("disabled", false);
								return;
							}
							var code = (result.budget && result.budget.code) || "";
							frappe.show_alert({
								message: __("Draft budget created"),
								indicator: "green",
							});
							frappe.set_route("budget-overview", code);
						})
						.catch(function (err) {
							console.warn("Register budget failed", err);
							$btn.prop("disabled", false);
							frappe.show_alert({
								message: __("Could not create draft budget"),
								indicator: "red",
							});
						});
				});
				return ctx;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				// In-canvas form notice — never Frappe Message dialog.
				var $notice = $root.find('[data-testid="kt-bud-register-notice"]');
				if ($notice.length) {
					$notice
						.find("[data-kt-bud-register-notice-msg]")
						.text(__("Only a Budget Officer can register an approved budget."));
					$notice.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
				} else if (window.ktFormErrors) {
					window.ktFormErrors.show(
						$root,
						{ form: __("Only a Budget Officer can register an approved budget.") },
						{ errorAttr: "data-kt-bud-error", errorAttrAliases: [] }
					);
				} else {
					frappe.show_alert({
						message: __("Only a Budget Officer can register an approved budget."),
						indicator: "orange",
					});
				}
				throw err;
			});
	}

	function setOv($root, key, text) {
		$root.find('[data-kt-bud-ov="' + key + '"]').text(text == null ? "" : String(text));
	}

	function paintStatusPill($root, status, label) {
		var $pill = $root.find("[data-kt-bud-status-pill]");
		var $icon = $root.find("[data-kt-bud-status-icon]");
		var $label = $root.find("[data-kt-bud-budget-status]");
		$label.text(label || status || "—");
		$pill
			.removeClass(
				"bg-status-available/10 text-status-available border-status-available/20 bg-status-reserved/10 text-status-reserved border-status-reserved/20 bg-surface-variant text-on-surface-variant border-outline-variant/20"
			)
			.addClass("border");
		if (status === "Active") {
			$pill.addClass(
				"bg-status-available/10 text-status-available border-status-available/20"
			);
			$icon.text("check_circle");
		} else if (status === "Submitted") {
			$pill.addClass("bg-status-reserved/10 text-status-reserved border-status-reserved/20");
			$icon.text("pending");
		} else {
			$pill.addClass("bg-surface-variant text-on-surface-variant border-outline-variant/20");
			$icon.text("radio_button_unchecked");
		}
	}

	/** Seed sibling-tab chrome cache so soft-nav never flashes placeholder title. */
	function rememberPaintedBudgetChrome(budget) {
		if (
			kentender_budget.workspace &&
			typeof kentender_budget.workspace.rememberBudgetChrome === "function"
		) {
			kentender_budget.workspace.rememberBudgetChrome(budget);
		}
	}

	function paintBudgetWorkspaceChrome($root, budget, caps) {
		budget = budget || {};
		$root.find("[data-kt-bud-budget-code]").text(budget.code || "");
		$root.find("[data-kt-bud-budget-title]").text(budget.title || budget.name || "—");
		paintStatusPill($root, budget.status, budget.status_label);
		if (caps !== undefined) {
			paintChromeActions($root, caps);
		}
		rememberPaintedBudgetChrome(budget);
	}

	function paintChromeActions($root, caps) {
		caps = caps || {};
		var action = String(caps.primary_action || "").trim();
		var label = String(caps.primary_label || "").trim();
		// Known actions get a proper label when the DTO omits primary_label.
		// Never invent a bare "Open" fallback.
		if (!label && action) {
			var defaults = {
				request_revision: __("Request revision"),
				open_lines: __("Budget lines"),
				add_line: __("Add budget line"),
				view_funding_performance: __("View funding performance"),
				apply_revision: __("Apply revision"),
			};
			label = defaults[action] || "";
		}
		$root.attr("data-kt-bud-primary-action", action);
		var $primary = $root.find('[data-testid="kt-bud-overview-primary"]');
		if (!$primary.length) {
			return;
		}
		if (!action || !label) {
			$primary.addClass("hidden").attr("hidden", "hidden").text("");
			return;
		}
		$primary.removeClass("hidden").removeAttr("hidden").text(label);
	}

	function bindOverview($root, budgetCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = $root.attr("data-kt-bud-mount-gen") || "0";
		return call("get_budget_overview", { budget: budgetCode })
			.then(function (ov) {
				if (($root.attr("data-kt-bud-mount-gen") || "0") !== gen) {
					return ov;
				}
				if (!ov) {
					$root.attr("data-kt-bud-live", "0");
					return ov;
				}
				var pe = ov.procuring_entity || {};
				var totals = ov.totals || {};
				var bar = ov.utilization_bar || {};
				var strategy = ov.strategy || {};
				var attn = ov.attention || {};

				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, ov, { code: ov.code || budgetCode || "" }),
					ov.capabilities
				);

				setOv($root, "entity", pe.name || pe.code || "—");
				setOv($root, "fiscal_period", ov.fiscal_period_label || ov.fiscal_period || "—");
				setOv($root, "currency", ov.currency || "KES");
				setOv($root, "source", ov.registration_source_label || ov.registration_source || "—");
				setOv($root, "external_ref", ov.authoritative_reference || "—");
				setOv($root, "last_sync_text", ov.last_synchronised || "Not applicable");
				setOv($root, "approved", totals.approved_display || "—");
				setOv($root, "reserved", totals.reserved_display || "—");
				setOv($root, "committed", totals.committed_display || "—");
				setOv($root, "available", totals.available_display || "—");
				setOv($root, "actual", totals.actual_display || "—");
				setOv($root, "outstanding", totals.outstanding_display || "—");
				setOv(
					$root,
					"bar_total",
					"100% (" + (bar.total_display || totals.approved_display || "—") + ")"
				);
				$root
					.find('[data-kt-bud-ov-bar="reserved"]')
					.css("width", (bar.reserved_pct || 0) + "%")
					.attr("title", "Reserved: " + (totals.reserved_display || ""));
				$root
					.find('[data-kt-bud-ov-bar="committed"]')
					.css("width", (bar.committed_pct || 0) + "%")
					.attr("title", "Committed: " + (totals.committed_display || ""));
				$root
					.find('[data-kt-bud-ov-bar="available"]')
					.css("width", (bar.available_pct || 0) + "%")
					.attr("title", "Available: " + (totals.available_display || ""));

				setOv($root, "strategy_lines", strategy.lines_summary || "—");
				setOv($root, "definition", ov.definitional_note || "");

				var $attn = $root.find('[data-testid="kt-bud-overview-attention"]');
				if (attn.has_exception && attn.text) {
					setOv($root, "attention_text", attn.text);
					$attn.removeAttr("hidden");
				} else {
					$attn.attr("hidden", "hidden");
				}

				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return ov;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				throw err;
			});
	}

	function parseMoneyInput(raw) {
		var s = String(raw == null ? "" : raw).replace(/[^\d.-]/g, "");
		var n = parseFloat(s);
		return isNaN(n) ? 0 : n;
	}

	function formatMoneyInput(n) {
		var v = Number(n) || 0;
		return "KES " + Math.round(v).toLocaleString("en-US");
	}

	function lineRowHtml(row) {
		var statusKind = row.status_kind === "attention" ? "attention" : "complete";
		var actualExtra = "";
		if (row.actual_freshness === "Stale") {
			actualExtra =
				'<div class="text-[11px] text-error font-medium flex items-center justify-end gap-1">' +
				'<span class="material-symbols-outlined text-[12px]">warning</span> Stale</div>';
		} else if (row.actual_freshness === "Unknown") {
			actualExtra = "";
		}
		var actualClass =
			row.actual_freshness === "Unknown"
				? "font-data-mono text-outline italic"
				: "font-data-mono text-on-surface mb-1";
		var icon = row.action_icon || "visibility";
		var actionLabel = row.action_label || "View line";
		return (
			'<tr class="hover:bg-surface-container-low/50 transition-colors" data-testid="kt-bud-line-row" data-line-code="' +
			esc(row.code) +
			'" data-funding-source="' +
			esc(row.funding_source_type || "") +
			'" data-primary-target="' +
			esc(row.primary_target_code || "") +
			'">' +
			'<td class="px-4 py-4 align-top">' +
			'<div class="font-medium text-primary mb-1 leading-snug">' +
			esc(row.title) +
			"</div>" +
			'<div class="font-data-mono text-xs text-outline mb-2">' +
			esc(row.code) +
			"</div>" +
			'<span class="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-surface-container text-on-surface-variant border border-outline-variant/30">' +
			esc(row.funding_source_type || "") +
			"</span></td>" +
			'<td class="px-4 py-4 align-top">' +
			'<div class="text-on-surface mb-1">' +
			esc(row.primary_target_label || "—") +
			"</div>" +
			'<div class="font-data-mono text-xs text-outline">' +
			esc(row.primary_target_code || "") +
			"</div></td>" +
			'<td class="px-4 py-4 align-top text-right font-data-mono font-medium text-on-surface" data-kt-bud-line-money>' +
			esc(row.approved_display) +
			"</td>" +
			'<td class="px-4 py-4 align-top text-right font-data-mono text-status-reserved" data-kt-bud-line-money>' +
			esc(row.reserved_display) +
			"</td>" +
			'<td class="px-4 py-4 align-top text-right font-data-mono text-status-committed" data-kt-bud-line-money>' +
			esc(row.committed_display) +
			"</td>" +
			'<td class="px-4 py-4 align-top text-right font-data-mono text-status-available font-semibold" data-kt-bud-line-money>' +
			esc(row.available_display) +
			"</td>" +
			'<td class="px-4 py-4 align-top text-right">' +
			'<div class="' +
			actualClass +
			'">' +
			esc(row.actual_display) +
			"</div>" +
			actualExtra +
			"</td>" +
			'<td class="px-4 py-4 align-top">' +
			'<div data-kt-bud-line-status="' +
			statusKind +
			'" class="mb-2">' +
			'<div class="w-1.5 h-1.5 rounded-full ' +
			(statusKind === "attention" ? "bg-error" : "bg-status-available") +
			'"></div>' +
			esc(row.status_label || "") +
			"</div>" +
			'<div class="text-[11px] text-on-surface-variant leading-tight">' +
			esc(row.attention || "") +
			"</div></td>" +
			'<td class="px-4 py-4 align-top text-right">' +
			'<button type="button" class="text-primary hover:text-secondary font-medium text-sm inline-flex items-center justify-end gap-1 ml-auto" data-kt-bud-line-action="' +
			esc(row.action || "view") +
			'" data-line-code="' +
			esc(row.code) +
			'" title="' +
			esc(actionLabel) +
			'" data-testid="kt-bud-line-action">' +
			'<span class="kt-bud-line-action-label">' +
			esc(actionLabel) +
			"</span>" +
			'<span class="material-symbols-outlined text-[16px]" aria-hidden="true">' +
			esc(icon) +
			"</span></button></td></tr>"
		);
	}

	function supportingCardHtml(st, readOnly) {
		return (
			'<div class="bg-surface border border-outline-variant rounded-lg p-4 flex flex-col gap-2" data-kt-bud-supporting-card data-target-code="' +
			esc(st.code) +
			'">' +
			'<div class="flex justify-between items-start"><div class="space-y-1">' +
			'<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase">Supporting strategic target</label>' +
			'<div class="font-body-md text-on-surface font-medium">' +
			esc(st.name) +
			'</div><div class="font-data-mono text-[12px] text-on-surface-variant">' +
			esc(st.code) +
			"</div></div>" +
			(readOnly
				? ""
				: '<button type="button" class="p-1 text-on-surface-variant hover:bg-surface-container rounded-full" data-kt-bud-supporting-remove="' +
					esc(st.code) +
					'"><span class="material-symbols-outlined text-[20px]">close</span></button>') +
			"</div>" +
			'<div class="font-body-md text-on-surface-variant text-[13px] italic flex gap-1 items-start mt-1">' +
			'<span class="material-symbols-outlined text-[16px]">info</span><span>Reason: ' +
			esc(st.reason || "") +
			"</span></div></div>"
		);
	}

	function closeLineDrawer($root) {
		var $drawer = $root.find("[data-kt-bud-line-drawer]");
		var $scrim = $root.find("[data-kt-bud-line-drawer-scrim]");
		$drawer.attr("hidden", "hidden").attr("aria-hidden", "true");
		$scrim.attr("hidden", "hidden");
	}

	function openLineDrawer($root, lineDto, opts) {
		opts = opts || {};
		var readOnly = !!(lineDto.capabilities && lineDto.capabilities.read_only);
		var $drawer = $root.find("[data-kt-bud-line-drawer]");
		var $scrim = $root.find("[data-kt-bud-line-drawer-scrim]");
		clearLineDrawerFieldErrors($drawer);
		$drawer.attr("data-kt-bud-line-readonly", readOnly ? "1" : "0");
		$drawer.attr("data-line-code", lineDto.code || "");
		$drawer.find("[data-kt-bud-line-drawer-title]").text(
			opts.isNew ? __("Add Budget Line") : __("Edit Budget Line")
		);
		$drawer.find('[data-kt-bud-line-field="code"]').text(lineDto.code || (opts.isNew ? "(assigned on save)" : "—"));
		$drawer.find('[data-kt-bud-line-input="title"]').val(lineDto.title || "");
		$drawer
			.find('[data-kt-bud-line-input="approved_amount"]')
			.val(lineDto.approved != null ? formatMoneyInput(lineDto.approved) : "");
		$drawer
			.find('[data-kt-bud-line-input="funding_source_type"]')
			.val(lineDto.funding_source_type || "Exchequer");
		$drawer
			.find('[data-kt-bud-line-input="external_financial_line_reference"]')
			.val(lineDto.external_financial_line_reference || "");
		$drawer
			.find('[data-kt-bud-line-input="classification"]')
			.val(lineDto.classification || "Capital expenditure");
		$drawer
			.find('[data-kt-bud-line-input="organisational_owner"]')
			.val(lineDto.organisational_owner || "");
		var ownershipPath = lineDto.ownership_path || "";
		var $ownPath = $drawer.find("[data-kt-bud-line-ownership-path]");
		if ($ownPath.length) {
			$ownPath.text(ownershipPath || "—");
			$ownPath.toggleClass("hidden", !ownershipPath);
		}

		var primary = lineDto.primary_target || {};
		var $primary = $drawer.find('[data-kt-bud-line-input="primary_target"]');
		if (primary.code && !$primary.find('option[value="' + primary.code + '"]').length) {
			$primary.append(
				$("<option></option>").attr("value", primary.code).text(primary.name || primary.code)
			);
		}
		$primary.val(primary.code || "");
		$drawer.find('[data-kt-bud-line-field="primary_target_code"]').text(primary.code || "—");

		var $sup = $drawer.find("[data-kt-bud-line-supporting-list]");
		$sup.empty();
		(lineDto.supporting_targets || []).forEach(function (st) {
			$sup.append(supportingCardHtml(st, readOnly));
		});

		$drawer.find('[data-kt-bud-line-field="approved_compact"]').text(
			lineDto.approved_compact_display || formatMoneyInput(lineDto.approved).replace(/,000,000$/, "M")
		);

		var $save = $drawer.find("[data-kt-bud-line-save]");
		var $rev = $drawer.find("[data-kt-bud-line-request-revision]");
		if (readOnly) {
			$save.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
			if (lineDto.capabilities && lineDto.capabilities.show_request_revision) {
				$rev.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
			} else {
				$rev.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
			}
			$drawer.find("[data-kt-bud-line-add-supporting]").addClass("hidden").attr("hidden", "hidden");
		} else {
			$save.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
			$rev.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
			$drawer.find("[data-kt-bud-line-add-supporting]").removeClass("hidden").removeAttr("hidden");
		}

		$drawer.data("ktLineDto", lineDto);
		$drawer.removeAttr("hidden").attr("aria-hidden", "false");
		$scrim.removeAttr("hidden");
	}

	function collectDrawerPayload($root, budgetCode) {
		var $drawer = $root.find("[data-kt-bud-line-drawer]");
		var dto = $drawer.data("ktLineDto") || {};
		var primaryCode = $drawer.find('[data-kt-bud-line-input="primary_target"]').val() || "";
		var primaryOpt = $drawer.find('[data-kt-bud-line-input="primary_target"] option:selected');
		var primaryMeta = (dto._targetOptions || []).find(function (t) {
			return t.node_code === primaryCode || t.code === primaryCode;
		}) || {};
		var supporting = [];
		$drawer.find("[data-kt-bud-supporting-card]").each(function () {
			var $c = $(this);
			supporting.push({
				code: $c.attr("data-target-code"),
				name: $c.find(".font-medium").first().text().trim(),
				reason: ($c.text().match(/Reason:\s*(.*)/) || [])[1] || "",
			});
		});
		return {
			budget: budgetCode,
			line: $drawer.attr("data-line-code") || "",
			title: $drawer.find('[data-kt-bud-line-input="title"]').val(),
			organisational_owner: $drawer.find('[data-kt-bud-line-input="organisational_owner"]').val(),
			classification: $drawer.find('[data-kt-bud-line-input="classification"]').val(),
			funding_source_type: $drawer.find('[data-kt-bud-line-input="funding_source_type"]').val(),
			funding_source_name: dto.funding_source_name || "Government of Kenya Development Budget",
			external_financial_line_reference: $drawer
				.find('[data-kt-bud-line-input="external_financial_line_reference"]')
				.val(),
			approved_amount: parseMoneyInput(
				$drawer.find('[data-kt-bud-line-input="approved_amount"]').val()
			),
			primary_target: {
				id: primaryMeta.node_id || primaryMeta.id || "",
				code: primaryCode,
				name: primaryOpt.text() || primaryMeta.node_name || primaryCode,
				plan_version_id: primaryMeta.plan_version_id || "",
				snapshot_label: primaryMeta.snapshot_label || "",
			},
			supporting_targets: supporting,
		};
	}

	function bindLineDrawer($root, budgetCode) {
		$root.off("click.ktBudLineDrawer");
		$root.on(
			"click.ktBudLineDrawer",
			"[data-kt-bud-line-drawer-close], [data-kt-bud-line-cancel], [data-kt-bud-line-drawer-scrim]",
			function (e) {
				e.preventDefault();
				closeLineDrawer($root);
			}
		);
		$root.on("click.ktBudLineDrawer", "[data-kt-bud-line-save]", function (e) {
			e.preventDefault();
			var $drawer = $root.find("[data-kt-bud-line-drawer]");
			clearLineDrawerFieldErrors($drawer);
			var payload = collectDrawerPayload($root, budgetCode);
			call("save_budget_line", { payload: payload })
				.then(function (res) {
					if (!res || !res.ok) {
						var errs = (res && res.errors) || {};
						showLineDrawerFieldErrors($drawer, errs);
						var msg = Object.keys(errs)
							.map(function (k) {
								return errs[k];
							})
							.join("; ");
						frappe.show_alert({ message: msg || __("Could not save budget line"), indicator: "red" });
						return;
					}
					closeLineDrawer($root);
					frappe.show_alert({ message: __("Budget line saved"), indicator: "green" });
					return bindLines($root, budgetCode);
				})
				.catch(function (err) {
					console.warn("save_budget_line failed", err);
					frappe.show_alert({ message: __("Could not save budget line"), indicator: "red" });
				});
		});
		$root.on("click.ktBudLineDrawer", "[data-kt-bud-line-request-revision]", function (e) {
			e.preventDefault();
			frappe.set_route("budget-revision-create", budgetCode);
		});
		$root.on("change.ktBudLineDrawer", '[data-kt-bud-line-input="primary_target"]', function () {
			$root
				.find('[data-kt-bud-line-field="primary_target_code"]')
				.text($(this).val() || "—");
			clearLineDrawerFieldErrors($root.find("[data-kt-bud-line-drawer]"));
		});
	}

	function clearLineDrawerFieldErrors($drawer) {
		if (!$drawer || !$drawer.length) {
			return;
		}
		$drawer.find("[data-kt-bud-error]").addClass("hidden").text("");
		$drawer.find(".kt-field-invalid").removeClass("kt-field-invalid");
		if (window.ktFormErrors && typeof window.ktFormErrors.clear === "function") {
			window.ktFormErrors.clear($drawer, {
				errorAttr: "data-kt-bud-error",
				fieldAttr: "data-kt-bud-field",
				invalidClass: "kt-field-invalid",
			});
		}
	}

	function showLineDrawerFieldErrors($drawer, errors) {
		if (!$drawer || !$drawer.length || !errors) {
			return;
		}
		Object.keys(errors).forEach(function (key) {
			var $el = $drawer.find('[data-kt-bud-error="' + key + '"]');
			if ($el.length) {
				$el.text(errors[key] || "").removeClass("hidden");
			}
		});
		if (window.ktFormErrors) {
			window.ktFormErrors.show($drawer, errors, {
				errorAttr: "data-kt-bud-error",
				errorAttrAliases: [],
				fieldAttr: "data-kt-bud-field",
				fieldAttrAliases: [],
				invalidClass: "kt-field-invalid",
			});
		}
	}

	function hideLinesNotice($root) {
		var $n = $root.find("[data-kt-bud-lines-notice], [data-testid='kt-bud-lines-notice']");
		if (!$n.length) {
			return;
		}
		$n.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
	}

	function showLinesNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-lines-notice], [data-testid='kt-bud-lines-notice']");
		if (!$n.length) {
			return;
		}
		if (opts.title) {
			$n.find("[data-kt-bud-lines-notice-title]").text(opts.title);
		}
		if (opts.message) {
			$n.find("[data-kt-bud-lines-notice-msg]").text(opts.message);
		}
		$n.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
		try {
			var el = $n.get(0);
			if (el && typeof el.scrollIntoView === "function") {
				el.scrollIntoView({ block: "nearest", behavior: "smooth" });
			}
		} catch (e) {
			/* ignore */
		}
	}

	function bindLines($root, budgetCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = $root.attr("data-kt-bud-mount-gen") || "0";
		bindLineDrawer($root, budgetCode);
		hideLinesNotice($root);
		return call("list_budget_lines", { budget: budgetCode })
			.then(function (dto) {
				if (($root.attr("data-kt-bud-mount-gen") || "0") !== gen) {
					return dto;
				}
				if (!dto) {
					$root.attr("data-kt-bud-live", "0");
					return dto;
				}
				var budget = dto.budget || {};
				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, budget, { code: budget.code || budgetCode || "" }),
					dto.capabilities
				);

				// New Line stays visible (Stitch toolbar); Active blocks create with guidance.
				var $newBtn = $root.find("[data-kt-bud-lines-new]");
				$newBtn.removeClass("hidden").removeAttr("hidden");
				$newBtn.attr(
					"data-kt-bud-can-add",
					dto.capabilities && dto.capabilities.can_add_line ? "1" : "0"
				);

				var lines = dto.lines || [];
				$root.data("ktBudLinesCache", lines);

				// Populate Strategic Target filter from live rows (code + name).
				var $targetFilter = $root.find('[data-kt-bud-lines-filter="primary_target"]');
				var prevTarget = $targetFilter.val() || "";
				var targetOpts = {};
				lines.forEach(function (r) {
					if (r.primary_target_code) {
						targetOpts[r.primary_target_code] =
							r.primary_target_label || r.primary_target_code;
					}
				});
				$targetFilter.empty().append('<option value="">All targets</option>');
				Object.keys(targetOpts)
					.sort()
					.forEach(function (code) {
						$targetFilter.append(
							$("<option></option>").attr("value", code).text(targetOpts[code] + " (" + code + ")")
						);
					});
				if (prevTarget && targetOpts[prevTarget]) {
					$targetFilter.val(prevTarget);
				}

				function filteredLines() {
					var query = ($root.find("[data-kt-bud-lines-search]").val() || "")
						.toLowerCase()
						.trim();
					var source = $root.find('[data-kt-bud-lines-filter="funding_source"]').val() || "";
					var target = $root.find('[data-kt-bud-lines-filter="primary_target"]').val() || "";
					return lines.filter(function (r) {
						if (source && (r.funding_source_type || "") !== source) {
							return false;
						}
						if (target && (r.primary_target_code || "") !== target) {
							return false;
						}
						if (!query) {
							return true;
						}
						return (
							(r.title || "").toLowerCase().indexOf(query) >= 0 ||
							(r.code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.primary_target_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.primary_target_label || "").toLowerCase().indexOf(query) >= 0
						);
					});
				}

				function paintLinesTable(filtered) {
					var $tbody = $root.find("[data-kt-bud-lines-tbody]");
					if (
						window.kentender_core &&
						kentender_core.table &&
						typeof kentender_core.table.attachPagination === "function"
					) {
						kentender_core.table
							.attachPagination($root, {
								footerSelector: '[data-testid="kt-bud-lines-table-footer"]',
								renderPage: function (pageRows) {
									if (!pageRows || !pageRows.length) {
										$tbody.html(
											'<tr><td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">No budget lines match.</td></tr>'
										);
										return;
									}
									$tbody.html(pageRows.map(lineRowHtml).join(""));
								},
							})
							.setRows(filtered, true);
						return;
					}
					if (!filtered.length) {
						$tbody.html(
							'<tr><td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">No budget lines match.</td></tr>'
						);
					} else {
						$tbody.html(filtered.map(lineRowHtml).join(""));
					}
				}

				function renderFiltered() {
					paintLinesTable(filteredLines());
				}

				renderFiltered();

				$root
					.off("input.ktBudLinesSearch change.ktBudLinesFilter")
					.on(
						"input.ktBudLinesSearch change.ktBudLinesFilter",
						"[data-kt-bud-lines-search], [data-kt-bud-lines-filter]",
						function () {
							renderFiltered();
						}
					);

				$root.off("click.ktBudLinesRow").on("click.ktBudLinesRow", "[data-kt-bud-line-action]", function (e) {
					e.preventDefault();
					var code = $(this).attr("data-line-code");
					openLineByCode($root, budgetCode, code, budget);
				});

				$root.off("click.ktBudLinesNew").on("click.ktBudLinesNew", "[data-kt-bud-lines-new]", function (e) {
					e.preventDefault();
					if ($(this).attr("data-kt-bud-can-add") !== "1") {
						// In-canvas notice — never Frappe Message dialog for governance locks.
						showLinesNotice($root, {
							title: __("Revision required"),
							message: __(
								"Active budgets cannot add lines directly. Request a revision to change the baseline."
							),
						});
						return;
					}
					hideLinesNotice($root);
					openNewLine($root, budgetCode, budget);
				});

				$root
					.off("click.ktBudLinesNotice")
					.on("click.ktBudLinesNotice", "[data-kt-bud-lines-notice-dismiss]", function (e) {
						e.preventDefault();
						hideLinesNotice($root);
					})
					.on("click.ktBudLinesNotice", "[data-kt-bud-lines-notice-cta]", function (e) {
						e.preventDefault();
						hideLinesNotice($root);
						frappe.set_route("budget-revision-create", budgetCode);
					});

				// Chrome primary "Add budget line" on Draft
				$root.off("click.ktBudLinesPrimary").on("click.ktBudLinesPrimary", function () {
					/* noop — shell handles; hook add_line below via data attr listener */
				});
				$root.attr("data-kt-bud-primary-action", (dto.capabilities || {}).primary_action || "");
				if ((dto.capabilities || {}).primary_action === "add_line") {
					$root
						.off("click.ktBudAddLineChrome")
						.on("click.ktBudAddLineChrome", '[data-testid="kt-bud-overview-primary"]', function (e) {
							e.preventDefault();
							e.stopPropagation();
							openNewLine($root, budgetCode, budget);
						});
				}

				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				throw err;
			});
	}

	function loadTargetOptions($root, pe) {
		return new Promise(function (resolve) {
			frappe.call({
				method: "kentender_strategy.api.strategy_api.list_active_targets",
				args: { procuring_entity: pe || "" },
				callback: function (r) {
					resolve((r && r.message) || []);
				},
				error: function () {
					resolve([]);
				},
			});
		});
	}

	function populatePrimaryOptions($root, targets, selectedCode) {
		var $sel = $root.find('[data-kt-bud-line-input="primary_target"]');
		$sel.empty().append('<option value="">Select Active target…</option>');
		(targets || []).forEach(function (t) {
			var code = t.node_code || t.code;
			var name = t.node_name || t.name || code;
			$sel.append(
				$("<option></option>")
					.attr("value", code)
					.prop("selected", code === selectedCode)
					.text(name)
			);
		});
	}

	function openLineByCode($root, budgetCode, lineCode, budget) {
		return call("get_budget_line", { line: lineCode }).then(function (line) {
			return loadTargetOptions($root, budget && budget.procuring_entity).then(function (targets) {
				line._targetOptions = targets;
				populatePrimaryOptions($root, targets, (line.primary_target || {}).code);
				openLineDrawer($root, line, { isNew: false });
				return line;
			});
		});
	}

	function openNewLine($root, budgetCode, budget) {
		return loadTargetOptions($root, budget && budget.procuring_entity).then(function (targets) {
			var blank = {
				code: "",
				title: "",
				approved: 0,
				classification: "Capital expenditure",
				funding_source_type: "Exchequer",
				funding_source_name: "Government of Kenya Development Budget",
				organisational_owner: "",
				external_financial_line_reference: "",
				primary_target: {},
				supporting_targets: [],
				approved_compact_display: "KES 0",
				capabilities: { read_only: false, can_save: true, show_request_revision: false },
				_targetOptions: targets,
			};
			populatePrimaryOptions($root, targets, "");
			openLineDrawer($root, blank, { isNew: true });
		});
	}

	function hideActivityNotice($root) {
		var $n = $root.find("[data-kt-bud-activity-notice], [data-testid='kt-bud-activity-notice']");
		if (!$n.length) {
			return;
		}
		$n.addClass("hidden").attr("hidden", "hidden").attr("aria-hidden", "true");
	}

	function showActivityNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-activity-notice], [data-testid='kt-bud-activity-notice']");
		if (!$n.length) {
			return;
		}
		$n.find("[data-kt-bud-activity-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-activity-notice-msg]").text(opts.message || "");
		$n.removeClass("hidden").removeAttr("hidden").attr("aria-hidden", "false");
	}

	function activityStatusKind(row) {
		return (row.status_kind || "neutral").toLowerCase();
	}

	function activityRowHtml(row) {
		var amountClass = "";
		if (row.amount_kind === "committed") {
			amountClass = " text-status-committed";
		} else if (row.amount_kind === "actual") {
			amountClass = " text-status-available";
		}
		var relatedHtml = "—";
		if (row.related_label && row.related_value) {
			relatedHtml =
				'<span class="text-status-reserved">' +
				esc(row.related_label) +
				"</span> " +
				esc(row.related_value);
		} else if (row.related_value && row.related_value !== "—") {
			relatedHtml = esc(row.related_value);
		}
		var sourceLine = esc(row.source_name || "—");
		if (row.source_code) {
			sourceLine +=
				'<div class="font-data-mono text-[12px] text-on-surface-variant mt-0.5">' +
				esc(row.source_code) +
				"</div>";
		}
		return (
			'<tr data-testid="kt-bud-activity-row" data-activity-code="' +
			esc(row.code) +
			'" data-activity-type="' +
			esc(row.activity_type || "") +
			'">' +
			'<td class="px-4 py-4 font-semibold">' +
			esc(row.activity_label || "") +
			"</td>" +
			'<td class="px-4 py-4 text-on-surface-variant max-w-xs">' +
			sourceLine +
			"</td>" +
			'<td class="px-4 py-4 font-data-mono text-right' +
			amountClass +
			'">' +
			esc(row.amount_display || "—") +
			"</td>" +
			'<td class="px-4 py-4"><span data-kt-bud-activity-status="' +
			esc(activityStatusKind(row)) +
			'">' +
			esc(row.status || "") +
			"</span></td>" +
			'<td class="px-4 py-4 text-on-surface-variant">' +
			esc(row.event_date || "—") +
			"</td>" +
			'<td class="px-4 py-4 text-sm">' +
			relatedHtml +
			"</td>" +
			'<td class="px-4 py-4 text-right">' +
			'<button type="button" class="text-secondary font-medium text-sm inline-flex items-center justify-end gap-1" data-testid="kt-bud-activity-action" data-kt-bud-activity-action="' +
			esc(row.action || "view") +
			'" data-activity-code="' +
			esc(row.code) +
			'">' +
			'<span class="kt-bud-activity-action-label">' +
			esc(row.action_label || "View") +
			"</span>" +
			'<span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>' +
			"</button></td></tr>"
		);
	}

	function bindFundingActivity($root, budgetCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = $root.attr("data-kt-bud-mount-gen") || "0";
		hideActivityNotice($root);
		return call("list_funding_activity", { budget: budgetCode })
			.then(function (dto) {
				if (($root.attr("data-kt-bud-mount-gen") || "0") !== gen) {
					return dto;
				}
				if (!dto) {
					$root.attr("data-kt-bud-live", "0");
					return dto;
				}
				var budget = dto.budget || {};
				var bal = dto.balances || {};
				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, budget, { code: budget.code || budgetCode || "" }),
					dto.capabilities
				);

				$root.find('[data-kt-bud-activity-bal="reserved"]').text(bal.reserved_display || "—");
				$root.find('[data-kt-bud-activity-bal="committed"]').text(bal.committed_display || "—");
				$root.find('[data-kt-bud-activity-bal="actual"]').text(bal.actual_display || "—");
				$root.find('[data-kt-bud-activity-bal="outstanding"]').text(bal.outstanding_display || "—");

				var rows = dto.rows || [];
				$root.data("ktBudActivityCache", rows);
				$root.data("ktBudActivityDetail", {});
				rows.forEach(function (r) {
					$root.data("ktBudActivityDetail")[r.code] = r.detail || r;
				});

				function filteredRows() {
					var query = ($root.find("[data-kt-bud-activity-search]").val() || "")
						.toLowerCase()
						.trim();
					var type = $root.find('[data-kt-bud-activity-filter="activity_type"]').val() || "";
					var status = $root.find('[data-kt-bud-activity-filter="status"]').val() || "";
					var dateFrom = $root.find('[data-kt-bud-activity-filter="date_from"]').val() || "";
					return rows.filter(function (r) {
						if (type && (r.activity_type || "") !== type) {
							return false;
						}
						if (status && (r.status || "") !== status) {
							return false;
						}
						if (dateFrom && (r.event_date_sort || "") < dateFrom) {
							return false;
						}
						if (!query) {
							return true;
						}
						return (
							(r.activity_label || "").toLowerCase().indexOf(query) >= 0 ||
							(r.source_name || "").toLowerCase().indexOf(query) >= 0 ||
							(r.source_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.status || "").toLowerCase().indexOf(query) >= 0
						);
					});
				}

				function paintTable(filtered) {
					var $tbody = $root.find("[data-kt-bud-activity-tbody]");
					if (
						window.kentender_core &&
						kentender_core.table &&
						typeof kentender_core.table.attachPagination === "function"
					) {
						kentender_core.table
							.attachPagination($root, {
								footerSelector: '[data-testid="kt-bud-activity-table-footer"]',
								renderPage: function (pageRows) {
									if (!pageRows || !pageRows.length) {
										$tbody.html(
											'<tr><td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">No funding activity matches.</td></tr>'
										);
										return;
									}
									$tbody.html(pageRows.map(activityRowHtml).join(""));
								},
							})
							.setRows(filtered, true);
						return;
					}
					if (!filtered.length) {
						$tbody.html(
							'<tr><td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">No funding activity matches.</td></tr>'
						);
					} else {
						$tbody.html(filtered.map(activityRowHtml).join(""));
					}
				}

				function renderFiltered() {
					paintTable(filteredRows());
				}

				renderFiltered();

				$root
					.off("input.ktBudActSearch change.ktBudActFilter")
					.on(
						"input.ktBudActSearch change.ktBudActFilter",
						"[data-kt-bud-activity-search], [data-kt-bud-activity-filter]",
						function () {
							renderFiltered();
						}
					);

				$root
					.off("click.ktBudActRow")
					.on("click.ktBudActRow", "[data-kt-bud-activity-action]", function (e) {
						e.preventDefault();
						var code = $(this).attr("data-activity-code");
						var detailMap = $root.data("ktBudActivityDetail") || {};
						var detail = detailMap[code] || {};
						var lines = [
							detail.code ? __("Reference") + ": " + detail.code : "",
							detail.demand_code ? __("Demand") + ": " + detail.demand_code : "",
							detail.contract_code ? __("Contract") + ": " + detail.contract_code : "",
							detail.original_amount_display
								? __("Original") + ": " + detail.original_amount_display
								: "",
							detail.amount_display ? __("Amount") + ": " + detail.amount_display : "",
							detail.remaining_display
								? __("Reserved balance") + ": " + detail.remaining_display
								: "",
							detail.outstanding_display
								? __("Outstanding") + ": " + detail.outstanding_display
								: "",
							detail.status ? __("Status") + ": " + detail.status : "",
							detail.source_as_at ? __("Source as at") + ": " + detail.source_as_at : "",
							detail.downstream ? __("Downstream") + ": " + detail.downstream : "",
						].filter(Boolean);
						showActivityNotice($root, {
							title: detail.title || code || __("Activity detail"),
							message: lines.join("\n") || __("Read-only funding activity record."),
						});
					});

				$root
					.off("click.ktBudActNotice")
					.on("click.ktBudActNotice", "[data-kt-bud-activity-notice-dismiss]", function (e) {
						e.preventDefault();
						hideActivityNotice($root);
					});

				$root.attr("data-kt-bud-primary-action", (dto.capabilities || {}).primary_action || "");
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showActivityNotice($root, {
					title: __("Could not load funding activity"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function showRevNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-rev-notice]");
		if (!$n.length) {
			return;
		}
		$n.find("[data-kt-bud-rev-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-rev-notice-msg]").text(opts.message || "");
		$n.removeClass("hidden").removeAttr("hidden");
	}

	function hideRevNotice($root) {
		var $n = $root.find("[data-kt-bud-rev-notice]");
		$n.addClass("hidden").attr("hidden", "hidden");
	}

	function clearRevErrors($root) {
		$root.find("[data-kt-bud-error]").addClass("hidden").text("");
		$root.find(".kt-bud-rev-change-input").removeClass("is-error");
		$root.find("[data-kt-bud-field]").removeClass("kt-field-invalid is-error");
		hideCreateFooterError($root);
		var $cn = $root.find("[data-kt-bud-rev-create-notice]");
		if ($cn.length) {
			$cn.addClass("hidden").attr("hidden", "hidden").removeClass("is-error is-info");
		}
	}

	function hideCreateFooterError($root) {
		var $fe = $root.find("[data-kt-bud-rev-footer-error]");
		if ($fe.length) {
			$fe.addClass("hidden").attr("hidden", "hidden");
			$fe.find("[data-kt-bud-rev-footer-error-msg]").text("");
		}
	}

	function showCreateFooterError($root, message) {
		var $fe = $root.find("[data-kt-bud-rev-footer-error]");
		if (!$fe.length) {
			return;
		}
		$fe.find("[data-kt-bud-rev-footer-error-msg]").text(message || "");
		$fe.removeClass("hidden").removeAttr("hidden");
	}

	function showCreateErrorNotice($root, title, message) {
		var $cn = $root.find("[data-kt-bud-rev-create-notice]");
		if (!$cn.length) {
			return;
		}
		$cn.find("[data-kt-bud-rev-create-notice-title]").text(title || "");
		$cn.find("[data-kt-bud-rev-create-notice-msg]").text(message || "");
		$cn
			.removeClass("hidden is-info")
			.addClass("is-error")
			.removeAttr("hidden")
			.attr("role", "alert");
		try {
			var el = $cn.get(0);
			if (el && typeof el.scrollIntoView === "function") {
				el.scrollIntoView({ block: "start", behavior: "smooth" });
			}
		} catch (e) {
			/* ignore */
		}
	}

	function showRevErrors($root, errors) {
		errors = errors || {};
		Object.keys(errors).forEach(function (key) {
			var $el = $root.find('[data-kt-bud-error="' + key + '"]');
			if ($el.length) {
				$el.text(errors[key] || "").removeClass("hidden");
			} else if (key.indexOf("line:") === 0) {
				var code = key.slice(5);
				$root
					.find('tr[data-line-code="' + code + '"] .kt-bud-rev-change-input')
					.addClass("is-error");
			}
		});
		if (window.ktFormErrors) {
			window.ktFormErrors.show($root, errors, {
				errorAttr: "data-kt-bud-error",
				errorAttrAliases: [],
				fieldAttr: "data-kt-bud-field",
				fieldAttrAliases: [],
				invalidClass: "kt-field-invalid",
			});
		}
		var keys = Object.keys(errors);
		var summary =
			keys.length === 1
				? errors[keys[0]]
				: __("Fix {0} issues above, then try again.").replace("{0}", String(keys.length));
		showCreateFooterError($root, summary);
		showCreateErrorNotice($root, __("Could not save revision"), summary);
	}

	function parseChangeInput(raw) {
		var s = String(raw == null ? "" : raw)
			.replace(/,/g, "")
			.trim();
		if (!s) {
			return 0;
		}
		s = s.replace(/^\+/, "");
		var n = Number(s);
		return isNaN(n) ? 0 : n;
	}

	function formatKesFullClient(amount, currency) {
		currency = currency || "KES";
		var n = Math.round(Number(amount) || 0);
		var abs = Math.abs(n).toLocaleString("en-US");
		return currency + " " + abs;
	}

	function signedKes(amount, currency) {
		var n = Number(amount) || 0;
		if (n > 0) {
			return "+ " + formatKesFullClient(n, currency);
		}
		if (n < 0) {
			return "- " + formatKesFullClient(Math.abs(n), currency);
		}
		return formatKesFullClient(0, currency);
	}

	function revisionListRowHtml(r) {
		var openAction = r.open_action || "";
		var actionLabel = r.action_label || "";
		var clickable =
			openAction === "review" || openAction === "edit" || openAction === "view";
		var actionCell = "—";
		if (clickable && actionLabel) {
			actionCell =
				'<button type="button" class="kt-bud-rev-list-action text-secondary font-medium text-sm inline-flex items-center justify-end gap-1 ml-auto" data-testid="kt-bud-rev-list-action" data-kt-bud-rev-list-action="' +
				esc(openAction) +
				'" data-revision-code="' +
				esc(r.code) +
				'">' +
				'<span class="kt-bud-rev-list-action-label">' +
				esc(actionLabel) +
				"</span>" +
				'<span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>' +
				"</button>";
		}
		return (
			'<tr data-revision-code="' +
			esc(r.code) +
			'" data-open-action="' +
			esc(openAction) +
			'"' +
			(clickable
				? ' class="kt-bud-rev-row-clickable" data-testid="kt-bud-rev-row"'
				: "") +
			">" +
			'<td class="px-4 py-3 align-top">' +
			'<div class="font-medium text-on-surface">' +
			esc(r.code) +
			"</div>" +
			'<div class="font-label-caps text-label-caps text-outline mt-0.5">' +
			esc(r.revision_type || "Line amendment") +
			"</div></td>" +
			'<td class="px-4 py-3 align-top">' +
			esc(r.external_approval_reference || "—") +
			"</td>" +
			'<td class="px-4 py-3 align-top">' +
			esc(r.status_label || r.status || "") +
			"</td>" +
			'<td class="px-4 py-3 align-top text-right font-data-mono">' +
			esc(r.change_total_display || "—") +
			"</td>" +
			'<td class="px-4 py-3 align-top">' +
			esc(r.effective_date || "—") +
			"</td>" +
			'<td class="px-4 py-3 align-top text-on-surface-variant">' +
			esc(r.reason || "—") +
			"</td>" +
			'<td class="px-4 py-3 align-top text-right text-sm">' +
			actionCell +
			"</td></tr>"
		);
	}

	function revLineRowHtml(line, currency) {
		var change = Number(line.change_amount) || 0;
		var after = Number(line.after_amount != null ? line.after_amount : line.before_amount) || 0;
		var floor = Number(line.floor) || Number(line.reserved || 0) + Number(line.committed || 0);
		var below = after < floor;
		var impact = below
			? "Below floor"
			: change > 0
				? "Increase"
				: change < 0
					? "Decrease"
					: "Balanced";
		var pillClass = below ? "is-bad" : "is-ok";
		var icon = below ? "error" : "check_circle";
		var changeVal = change === 0 ? "0" : change > 0 ? "+ " + change : String(change);
		return (
			'<tr data-line-code="' +
			esc(line.code) +
			'" data-line-id="' +
			esc(line.id) +
			'" data-before="' +
			esc(line.before_amount) +
			'" data-reserved="' +
			esc(line.reserved) +
			'" data-committed="' +
			esc(line.committed) +
			'" data-floor="' +
			esc(floor) +
			'">' +
			'<td class="px-3 py-2">' +
			'<div class="font-medium">' +
			esc(line.name || line.title) +
			"</div>" +
			'<div class="font-label-caps text-label-caps text-outline mt-0.5">' +
			esc(line.code) +
			"</div></td>" +
			'<td class="px-3 py-2 text-right font-data-mono">' +
			esc(line.before_display || formatKesFullClient(line.before_amount, currency)) +
			"</td>" +
			'<td class="px-3 py-2 text-right">' +
			'<input type="text" class="kt-bud-rev-change-input" data-kt-bud-rev-change inputmode="decimal" value="' +
			esc(changeVal) +
			'" aria-label="Change for ' +
			esc(line.code) +
			'">' +
			"</td>" +
			'<td class="px-3 py-2 text-right font-data-mono font-bold" data-kt-bud-rev-after>' +
			esc(formatKesFullClient(after, currency)) +
			"</td>" +
			'<td class="px-3 py-2 text-right font-data-mono text-on-surface-variant">' +
			esc(line.reserved_display || formatKesFullClient(line.reserved, currency)) +
			"</td>" +
			'<td class="px-3 py-2 text-right font-data-mono text-on-surface-variant">' +
			esc(line.committed_display || formatKesFullClient(line.committed, currency)) +
			"</td>" +
			'<td class="px-3 py-2 text-center">' +
			'<span class="kt-bud-rev-impact-pill ' +
			pillClass +
			'" data-kt-bud-rev-impact-status>' +
			'<span class="material-symbols-outlined text-[14px]" aria-hidden="true">' +
			icon +
			"</span> " +
			esc(impact) +
			"</span></td></tr>"
		);
	}

	function recomputeRevImpact($root) {
		var currency = $root.data("ktBudRevCurrency") || "KES";
		var beforeTotal = 0;
		var changeTotal = 0;
		var afterTotal = 0;
		$root.find("[data-kt-bud-rev-lines-tbody] tr[data-line-code]").each(function () {
			var $tr = $(this);
			var before = Number($tr.attr("data-before")) || 0;
			var floor = Number($tr.attr("data-floor")) || 0;
			var change = parseChangeInput($tr.find("[data-kt-bud-rev-change]").val());
			var after = before + change;
			beforeTotal += before;
			changeTotal += change;
			afterTotal += after;
			var below = after < floor;
			var impact = below
				? "Below floor"
				: change > 0
					? "Increase"
					: change < 0
						? "Decrease"
						: "Balanced";
			$tr.find("[data-kt-bud-rev-after]").text(formatKesFullClient(after, currency));
			var $pill = $tr.find("[data-kt-bud-rev-impact-status]");
			$pill
				.toggleClass("is-bad", below)
				.toggleClass("is-ok", !below)
				.html(
					'<span class="material-symbols-outlined text-[14px]" aria-hidden="true">' +
						(below ? "error" : "check_circle") +
						"</span> " +
						esc(impact)
				);
			$tr.find("[data-kt-bud-rev-change]").toggleClass("is-error", below);
		});
		$root.find("[data-kt-bud-rev-impact-before]").text(formatKesFullClient(beforeTotal, currency));
		$root.find("[data-kt-bud-rev-impact-change]").text(signedKes(changeTotal, currency));
		$root.find("[data-kt-bud-rev-impact-after]").text(formatKesFullClient(afterTotal, currency));
	}

	function readRevisionPayload($root, budgetCode) {
		var lines = [];
		$root.find("[data-kt-bud-rev-lines-tbody] tr[data-line-code]").each(function () {
			var $tr = $(this);
			lines.push({
				budget_line: $tr.attr("data-line-id") || $tr.attr("data-line-code"),
				change_amount: parseChangeInput($tr.find("[data-kt-bud-rev-change]").val()),
			});
		});
		return {
			budget: budgetCode,
			revision: ($root.find('[data-kt-bud-field="revision"]').val() || "").trim(),
			external_approval_reference: (
				$root.find('[data-kt-bud-field="external_approval_reference"]').val() || ""
			).trim(),
			approval_date: ($root.find('[data-kt-bud-field="approval_date"]').val() || "").trim(),
			effective_date: ($root.find('[data-kt-bud-field="effective_date"]').val() || "").trim(),
			reason: ($root.find('[data-kt-bud-field="reason"]').val() || "").trim(),
			approval_evidence: ($root.find('[data-kt-bud-field="approval_evidence"]').val() || "").trim(),
			lines: lines,
		};
	}

	function paintCreateContext($root, ctx) {
		var currency = (ctx.budget && ctx.budget.currency) || "KES";
		$root.data("ktBudRevCurrency", currency);
		var impact = ctx.impact || {};
		$root.find("[data-kt-bud-rev-impact-before]").text(impact.before_display || "—");
		$root.find("[data-kt-bud-rev-impact-change]").text(impact.change_display || "—");
		$root.find("[data-kt-bud-rev-impact-after]").text(impact.after_display || "—");
		$root.find("[data-kt-bud-rev-impact-demands]").text(String(impact.affected_demands || 0));
		$root.find("[data-kt-bud-rev-impact-tenders]").text(String(impact.affected_tenders || 0));
		var lines = ctx.lines || [];
		var $tbody = $root.find("[data-kt-bud-rev-lines-tbody]");
		if (!lines.length) {
			$tbody.html(
				'<tr><td colspan="7" class="px-4 py-6 text-center text-on-surface-variant">No active budget lines.</td></tr>'
			);
		} else {
			$tbody.html(
				lines
					.map(function (l) {
						return revLineRowHtml(l, currency);
					})
					.join("")
			);
		}
		recomputeRevImpact($root);
	}

	function bindRevisions($root, budgetCode) {
		// Revisions tab = list only. Create is /desk/budget-revision-create/<code>.
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = $root.attr("data-kt-bud-mount-gen") || "0";
		hideRevNotice($root);

		return call("list_budget_revisions", { budget: budgetCode })
			.then(function (dto) {
				if (($root.attr("data-kt-bud-mount-gen") || "0") !== gen) {
					return dto;
				}
				if (!dto) {
					$root.attr("data-kt-bud-live", "0");
					return dto;
				}
				var budget = dto.budget || {};
				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, budget, { code: budget.code || budgetCode || "" }),
					dto.capabilities
				);

				var rows = dto.rows || [];
				var $tbody = $root.find("[data-kt-bud-revisions-tbody]");
				function paintRows(pageRows) {
					if (!pageRows || !pageRows.length) {
						$tbody.html(
							'<tr><td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">No revisions yet. Use Request revision to record an externally approved change.</td></tr>'
						);
						return;
					}
					$tbody.html(pageRows.map(revisionListRowHtml).join(""));
				}
				if (
					window.kentender_core &&
					kentender_core.table &&
					typeof kentender_core.table.attachPagination === "function"
				) {
					kentender_core.table
						.attachPagination($root, {
							footerSelector: '[data-testid="kt-bud-revisions-table-footer"]',
							renderPage: paintRows,
						})
						.setRows(rows, true);
				} else {
					paintRows(rows);
				}

				function openRevisionFromList(code, action) {
					if (!code || !action) {
						return;
					}
					if (action === "review" || action === "view") {
						frappe.set_route("budget-revision-review", code);
					} else if (action === "edit") {
						frappe.set_route("budget-revision-create", budgetCode, code);
					}
				}

				$root.off(".ktBudRev");
				$root.on("click.ktBudRev", "[data-kt-bud-rev-notice-dismiss]", function (e) {
					e.preventDefault();
					hideRevNotice($root);
				});
				$root.on("click.ktBudRev", "[data-kt-bud-rev-list-action]", function (e) {
					e.preventDefault();
					e.stopPropagation();
					var $btn = $(this);
					openRevisionFromList(
						String($btn.attr("data-revision-code") || "").trim(),
						String($btn.attr("data-kt-bud-rev-list-action") || "").trim()
					);
				});
				$root.on("click.ktBudRev", "tr[data-revision-code]", function (e) {
					if ($(e.target).closest("[data-kt-bud-rev-list-action]").length) {
						return;
					}
					var $tr = $(this);
					openRevisionFromList(
						String($tr.attr("data-revision-code") || "").trim(),
						String($tr.attr("data-open-action") || "").trim()
					);
				});

				$root.attr("data-kt-bud-primary-action", (dto.capabilities || {}).primary_action || "");
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showRevNotice($root, {
					title: __("Could not load revisions"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function bindRevisionCreate($root, budgetCode, revisionCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		clearRevErrors($root);
		$root.find('[data-kt-bud-field="revision"]').val("");
		$root.find('[data-kt-bud-field="external_approval_reference"]').val("");
		$root.find('[data-kt-bud-field="approval_date"]').val("");
		$root.find('[data-kt-bud-field="effective_date"]').val("");
		$root.find('[data-kt-bud-field="reason"]').val("");
		setEvidence($root, "", "");
		$root.find("[data-kt-bud-rev-saved-code-wrap]").addClass("hidden");
		$root.find("[data-kt-bud-rev-saved-code]").text("");
		$root.find("[data-kt-bud-rev-create-notice]").addClass("hidden").attr("hidden", "hidden");

		$root.off(".ktBudRevCreate");
		$root.on("click.ktBudRevCreate", '[data-kt-bud-rev-action="add-line"]', function (e) {
			e.preventDefault();
			var $cn = $root.find("[data-kt-bud-rev-create-notice]");
			if ($cn.length) {
				$cn.find("[data-kt-bud-rev-create-notice-title]").text(__("Add line"));
				$cn.find("[data-kt-bud-rev-create-notice-msg]").text(
					__(
						"Amend existing lines below. Adding a new budget line through revision apply lands with Revision Review (BUD-UI-09)."
					)
				);
				$cn
					.removeClass("hidden is-error")
					.addClass("is-info")
					.removeAttr("hidden")
					.attr("role", "status");
			}
		});
		$root.on("click.ktBudRevCreate", '[data-kt-bud-rev-action="cancel"]', function (e) {
			e.preventDefault();
			frappe.set_route("budget-revisions", budgetCode);
		});
		$root.on("input.ktBudRevCreate change.ktBudRevCreate", "[data-kt-bud-rev-change]", function () {
			recomputeRevImpact($root);
		});
		$root.on("click.ktBudRevCreate", '[data-kt-bud-action="clear-evidence"]', function (e) {
			e.preventDefault();
			setEvidence($root, "", "");
		});
		$root.on(
			"click.ktBudRevCreate keydown.ktBudRevCreate",
			'[data-kt-bud-action="pick-evidence"]',
			function (e) {
				if (e.type === "keydown" && e.key !== "Enter" && e.key !== " ") {
					return;
				}
				e.preventDefault();
				var $file = $root.find('[data-kt-bud-field="approval_evidence_file"]');
				if ($file.length) {
					$file.trigger("click");
				}
			}
		);
		$root.on(
			"change.ktBudRevCreate",
			'[data-kt-bud-field="approval_evidence_file"]',
			function () {
				var file = this.files && this.files[0];
				if (!file) {
					return;
				}
				uploadEvidenceFile($root, file).catch(function (err) {
					console.warn("Revision evidence upload failed", err);
					showCreateErrorNotice(
						$root,
						__("Evidence upload failed"),
						__("The file was not attached. You can submit without evidence, or try again.")
					);
					showCreateFooterError(
						$root,
						__("Evidence upload failed — you can still submit without it.")
					);
				});
			}
		);
		$root.on(
			"dragover.ktBudRevCreate drop.ktBudRevCreate",
			'[data-testid="kt-bud-evidence-dropzone"]',
			function (e) {
				e.preventDefault();
				e.stopPropagation();
				if (e.type !== "drop") {
					return;
				}
				var dt = e.originalEvent && e.originalEvent.dataTransfer;
				var file = dt && dt.files && dt.files[0];
				if (!file) {
					return;
				}
				uploadEvidenceFile($root, file).catch(function () {
					showCreateErrorNotice(
						$root,
						__("Evidence upload failed"),
						__("The file was not attached. You can submit without evidence, or try again.")
					);
				});
			}
		);

		function persist(action) {
			clearRevErrors($root);
			var payload = readRevisionPayload($root, budgetCode);
			var method = action === "submit" ? "submit_budget_revision" : "create_budget_revision";
			var $btn = $root.find(
				action === "submit"
					? '[data-kt-bud-rev-action="submit"]'
					: '[data-kt-bud-rev-action="save-draft"]'
			);
			$btn.prop("disabled", true);
			return call(method, { payload: payload })
				.then(function (result) {
					$btn.prop("disabled", false);
					if (!result || !result.ok) {
						showRevErrors($root, (result && result.errors) || {});
						return result;
					}
					var rev = result.revision || {};
					$root.find('[data-kt-bud-field="revision"]').val(rev.code || "");
					$root.find("[data-kt-bud-rev-saved-code]").text(rev.code || "");
					$root.find("[data-kt-bud-rev-saved-code-wrap]").removeClass("hidden");
					hideCreateFooterError($root);
					if (action === "submit") {
						frappe.show_alert({
							message: __("Revision submitted for review"),
							indicator: "green",
						});
						frappe.set_route("budget-revisions", budgetCode);
						return result;
					}
					frappe.show_alert({
						message: __("Draft revision saved"),
						indicator: "green",
					});
					return result;
				})
				.catch(function (err) {
					$btn.prop("disabled", false);
					console.warn("Revision persist failed", err);
					showCreateErrorNotice(
						$root,
						__("Could not save revision"),
						__("Refresh and try again.")
					);
					showCreateFooterError($root, __("Could not save revision. Refresh and try again."));
					throw err;
				});
		}

		$root.on("click.ktBudRevCreate", '[data-kt-bud-rev-action="save-draft"]', function (e) {
			e.preventDefault();
			persist("draft");
		});
		$root.on("click.ktBudRevCreate", '[data-kt-bud-rev-action="submit"]', function (e) {
			e.preventDefault();
			persist("submit");
		});

		var ctxArgs = { budget: budgetCode };
		if (revisionCode) {
			ctxArgs.revision = revisionCode;
		}
		return call("get_budget_revision_create_context", ctxArgs)
			.then(function (ctx) {
				paintCreateContext($root, ctx || {});
				if (ctx && ctx.revision) {
					$root.find('[data-kt-bud-field="revision"]').val(ctx.revision.code || "");
					$root
						.find('[data-kt-bud-field="external_approval_reference"]')
						.val(ctx.revision.external_approval_reference || "");
					$root
						.find('[data-kt-bud-field="approval_date"]')
						.val(ctx.revision.approval_date || "");
					$root
						.find('[data-kt-bud-field="effective_date"]')
						.val(ctx.revision.effective_date || "");
					$root.find('[data-kt-bud-field="reason"]').val(ctx.revision.reason || "");
					if (ctx.revision.approval_evidence) {
						setEvidence($root, ctx.revision.approval_evidence, ctx.revision.approval_evidence);
					}
					$root.find("[data-kt-bud-rev-saved-code-wrap]").removeClass("hidden");
					$root.find("[data-kt-bud-rev-saved-code]").text(ctx.revision.code || "");
				}
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return ctx;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				var $cn = $root.find("[data-kt-bud-rev-create-notice]");
				if ($cn.length) {
					$cn.find("[data-kt-bud-rev-create-notice-title]").text(
						__("Cannot create revision")
					);
					$cn.find("[data-kt-bud-rev-create-notice-msg]").text(
						__("Revisions can only be created for Active budgets by a Budget Officer.")
					);
					$cn.removeClass("is-info").addClass("is-error").attr("role", "alert");
					$cn.removeClass("hidden").removeAttr("hidden");
				}
				throw err;
			});
	}

	function bindRevisionReview($root, revisionCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = String(Date.now());
		$root.attr("data-kt-bud-mount-gen", gen);
		$root.find("[data-kt-bud-error]").addClass("hidden").text("");
		$root.find("[data-kt-bud-rev-review-notice]").addClass("hidden").attr("hidden", "hidden");

		function showReviewNotice(title, message) {
			var $n = $root.find("[data-kt-bud-rev-review-notice]");
			$n.find("[data-kt-bud-rev-review-notice-title]").text(title || "");
			$n.find("[data-kt-bud-rev-review-notice-msg]").text(message || "");
			$n.removeClass("hidden").removeAttr("hidden");
		}

		function paintReview(dto) {
			var rev = (dto && dto.revision) || {};
			var budget = (dto && dto.budget) || {};
			var caps = (dto && dto.capabilities) || {};
			$root.attr("data-kt-bud-task-id", caps.task_id || "");
			$root.attr("data-kt-bud-task-token", caps.concurrency_token || "");
			var financial = (dto && dto.financial) || {};
			var blockers = (dto && dto.blockers) || [];
			$root.attr("data-kt-bud-budget-code", budget.code || "");
			$root.find("[data-kt-bud-rev-review-code]").text(rev.code || "—");
			$root
				.find("[data-kt-bud-rev-review-status-label]")
				.text(rev.status_label || rev.status || "");
			$root.find("[data-kt-bud-rev-review-submitted-by]").text(rev.submitted_by || "—");
			$root
				.find("[data-kt-bud-rev-review-submitted-at]")
				.text(rev.submitted_at_display || rev.submitted_at || "—");
			$root.find("[data-kt-bud-rev-review-fiscal]").text(budget.fiscal_period || "—");
			$root
				.find("[data-kt-bud-rev-review-ext-ref]")
				.text(rev.external_approval_reference || "—");
			$root.find("[data-kt-bud-rev-review-approval-date]").text(rev.approval_date || "—");
			$root.find("[data-kt-bud-rev-review-effective-date]").text(rev.effective_date || "—");
			$root.find("[data-kt-bud-rev-review-reason]").text(rev.reason || "—");
			$root.find("[data-kt-bud-rev-review-evidence]").text(rev.approval_evidence || "—");
			$root.find("[data-kt-bud-rev-review-net]").text(financial.net_change_display || "—");
			$root
				.find("[data-kt-bud-rev-review-balance-label]")
				.text(financial.balance_label || "BALANCED");
			$root
				.find("[data-kt-bud-rev-review-deductions]")
				.text(financial.deductions_display || "—");
			$root
				.find("[data-kt-bud-rev-review-additions]")
				.text(financial.additions_display || "—");

			var $blocker = $root.find("[data-kt-bud-rev-review-blocker]");
			if (blockers.length) {
				$blocker.removeClass("hidden").removeAttr("hidden");
				$root
					.find("[data-kt-bud-rev-review-blocker-msg]")
					.html(frappe.utils.escape_html(blockers[0].message || ""));
				$root.attr("data-kt-bud-rev-blocker-line", blockers[0].line_code || "");
			} else {
				$blocker.addClass("hidden").attr("hidden", "hidden");
				$root.attr("data-kt-bud-rev-blocker-line", "");
			}

			var strategyHtml = ((dto.strategy && dto.strategy.items) || [])
				.map(function (item) {
					var icon = item.severity === "warning" ? "warning" : "check_circle";
					var cls =
						item.severity === "warning"
							? "kt-bud-rev-review-item is-warn"
							: "kt-bud-rev-review-item is-ok";
					return (
						'<div class="' +
						cls +
						'">' +
						'<span class="material-symbols-outlined" aria-hidden="true">' +
						icon +
						'</span><div><span class="kt-bud-rev-review-item-title">' +
						esc(item.title || "") +
						'</span><span class="kt-bud-rev-review-item-msg">' +
						esc(item.message || "") +
						"</span></div></div>"
					);
				})
				.join("");
			$root.find("[data-kt-bud-rev-review-strategy-items]").html(strategyHtml || "");

			var cards = (dto.downstream && dto.downstream.cards) || [];
			var $down = $root.find("[data-kt-bud-rev-review-downstream-cards]");
			if (cards.length) {
				$down.html(
					cards
						.map(function (c) {
							return (
								'<div class="kt-bud-rev-review-down-card">' +
								'<div class="kt-bud-rev-review-down-top">' +
								'<span class="kt-bud-rev-review-label">Linked reservation</span>' +
								'<span class="font-data-mono">' +
								esc(c.code || "") +
								"</span></div>" +
								'<span class="kt-bud-rev-review-value">' +
								esc(c.name || "") +
								"</span>" +
								'<div class="kt-bud-rev-review-down-risk">' +
								'<span class="material-symbols-outlined" aria-hidden="true">link_off</span>' +
								"<span>" +
								esc(c.risk_message || "") +
								"</span></div></div>"
							);
						})
						.join("")
				);
			} else {
				$down.html(
					'<p class="kt-bud-rev-review-empty">' +
						esc(
							(dto.downstream && dto.downstream.empty_message) ||
								__("No linked reservations or commitments on this budget.")
						) +
						"</p>"
				);
			}

			var $apply = $root.find('[data-kt-bud-rev-review-action="apply"]');
			var $lock = $root.find("[data-kt-bud-rev-review-apply-lock]");
			if (caps.can_apply) {
				$apply.prop("disabled", false).removeAttr("aria-disabled").removeClass("is-locked");
				$lock.addClass("hidden");
			} else {
				$apply.prop("disabled", true).attr("aria-disabled", "true").addClass("is-locked");
				$lock.removeClass("hidden");
				if (caps.apply_locked_reason) {
					$apply.attr("title", caps.apply_locked_reason);
				}
			}
			$root
				.find('[data-kt-bud-rev-review-action="return"]')
				.prop("disabled", !caps.can_return);
			$root
				.find('[data-kt-bud-rev-review-action="reject"]')
				.prop("disabled", !caps.can_reject);
		}

		function closeReasonModal() {
			var $m = $root.find("[data-kt-bud-rev-reason-modal]");
			$m.addClass("hidden").attr("hidden", "hidden").attr("data-kt-bud-rev-reason-action", "");
			$m.find("[data-kt-bud-rev-reason-comment]").val("");
			$m.find('[data-kt-bud-error="comment"]').addClass("hidden").text("");
		}

		function openReasonModal(action) {
			var $m = $root.find("[data-kt-bud-rev-reason-modal]");
			if (!$m.length) {
				return;
			}
			var initiator =
				String($root.find("[data-kt-bud-rev-review-submitted-by]").text() || "").trim() ||
				__("the initiator");
			var isReject = action === "reject";
			$m.attr("data-kt-bud-rev-reason-action", action);
			$m.find("[data-kt-bud-rev-reason-title]").text(
				isReject ? __("Reject budget revision") : __("Return budget revision")
			);
			$m.find("[data-kt-bud-rev-reason-lead]").text(
				isReject
					? __(
							"Provide a mandatory reason for rejection. This feedback will be sent to the initiator ({0})."
					  ).replace("{0}", initiator)
					: __(
							"Provide a mandatory reason for returning this revision. This feedback will be sent to the initiator ({0})."
					  ).replace("{0}", initiator)
			);
			$m.find("[data-kt-bud-rev-reason-comment]")
				.val("")
				.attr(
					"placeholder",
					isReject
						? __(
								"e.g., The proposed reduction is not permitted at this stage."
						  )
						: __("e.g., Please correct the line change and resubmit.")
				);
			var $confirm = $m.find("[data-kt-bud-rev-reason-confirm]");
			$confirm
				.text(isReject ? __("Confirm rejection") : __("Confirm return"))
				.toggleClass("is-reject", isReject)
				.toggleClass("is-return", !isReject);
			$m.find('[data-kt-bud-error="comment"]').addClass("hidden").text("");
			$m.removeClass("hidden").removeAttr("hidden");
			try {
				$m.find("[data-kt-bud-rev-reason-comment]").trigger("focus");
			} catch (e) {
				/* ignore */
			}
		}

		function runAction(action, comment) {
			$root.find("[data-kt-bud-error]").addClass("hidden").text("");
			var method =
				action === "return"
					? "return_budget_revision"
					: action === "reject"
						? "reject_budget_revision"
						: "apply_budget_revision";
			var payload = {
				revision: revisionCode,
				task_id: $root.attr("data-kt-bud-task-id") || "",
				concurrency_token: $root.attr("data-kt-bud-task-token") || "",
			};
			if (action === "return" || action === "reject") {
				payload.comment = comment || "";
			}
			return call(method, { payload: payload })
				.then(function (result) {
					if (!result || result.ok === false) {
						var errors = (result && result.errors) || {};
						if (errors.comment) {
							$root
								.find('[data-kt-bud-error="comment"]')
								.removeClass("hidden")
								.text(errors.comment);
							showReviewNotice(__("Comment required"), errors.comment);
						} else if (errors.blockers) {
							closeReasonModal();
							showReviewNotice(__("Cannot apply"), errors.blockers);
						} else if (errors.status) {
							closeReasonModal();
							showReviewNotice(__("Action not allowed"), errors.status);
						} else {
							Object.keys(errors).forEach(function (k) {
								$root
									.find('[data-kt-bud-error="' + k + '"]')
									.removeClass("hidden")
									.text(errors[k]);
							});
						}
						return result;
					}
					closeReasonModal();
					var msg =
						action === "return"
							? __("Revision returned for correction")
							: action === "reject"
								? __("Revision rejected")
								: __("Revision applied");
					frappe.show_alert({ message: msg, indicator: "green" });
					var budgetCode = $root.attr("data-kt-bud-budget-code") || "MOH-BUD-2027-2028";
					frappe.set_route("budget-revisions", budgetCode);
					return result;
				})
				.catch(function (err) {
					showReviewNotice(__("Action failed"), __("Refresh and try again."));
					throw err;
				});
		}

		$root.off(".ktBudRevReview");
		$root.on("click.ktBudRevReview", "[data-kt-bud-rev-review-back]", function (e) {
			e.preventDefault();
			var budgetCode = $root.attr("data-kt-bud-budget-code") || "MOH-BUD-2027-2028";
			frappe.set_route("budget-revisions", budgetCode);
		});
		$root.on("click.ktBudRevReview", "[data-kt-bud-rev-review-view-line]", function (e) {
			e.preventDefault();
			var budgetCode = $root.attr("data-kt-bud-budget-code") || "MOH-BUD-2027-2028";
			frappe.set_route("budget-lines", budgetCode);
		});
		$root.on("click.ktBudRevReview", "[data-kt-bud-rev-review-action]", function (e) {
			e.preventDefault();
			var action = $(this).attr("data-kt-bud-rev-review-action");
			if (!action || $(this).prop("disabled")) {
				return;
			}
			if (action === "return" || action === "reject") {
				openReasonModal(action);
				return;
			}
			runAction(action);
		});
		$root.on(
			"click.ktBudRevReview",
			"[data-kt-bud-rev-reason-close], [data-kt-bud-rev-reason-cancel]",
			function (e) {
				e.preventDefault();
				closeReasonModal();
			}
		);
		$root.on("click.ktBudRevReview", "[data-kt-bud-rev-reason-modal]", function (e) {
			if (e.target === this) {
				closeReasonModal();
			}
		});
		$root.on("click.ktBudRevReview", "[data-kt-bud-rev-reason-confirm]", function (e) {
			e.preventDefault();
			var $m = $root.find("[data-kt-bud-rev-reason-modal]");
			var action = String($m.attr("data-kt-bud-rev-reason-action") || "").trim();
			var comment = String($m.find("[data-kt-bud-rev-reason-comment]").val() || "").trim();
			if (!action) {
				return;
			}
			if (!comment) {
				$m.find('[data-kt-bud-error="comment"]')
					.removeClass("hidden")
					.text(__("A comment is required"));
				return;
			}
			var $btn = $(this);
			$btn.prop("disabled", true);
			Promise.resolve(runAction(action, comment)).finally(function () {
				$btn.prop("disabled", false);
			});
		});

		return call("get_budget_revision_review_context", { revision: revisionCode })
			.then(function (dto) {
				if ($root.attr("data-kt-bud-mount-gen") !== gen) {
					return dto;
				}
				paintReview(dto || {});
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showReviewNotice(
					__("Could not load revision"),
					__("Refresh and try again. If the problem continues, contact support.")
				);
				throw err;
			});
	}

	function showDownstreamNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-downstream-notice]");
		if (!$n.length) {
			return;
		}
		$n.find("[data-kt-bud-downstream-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-downstream-notice-msg]").text(opts.message || "");
		$n.removeClass("hidden").removeAttr("hidden");
	}

	function hideDownstreamNotice($root) {
		var $n = $root.find("[data-kt-bud-downstream-notice]");
		$n.addClass("hidden").attr("hidden", "hidden");
	}

	function downstreamRowHtml(r) {
		var statusKind = r.status_kind || "ok";
		var contractCell =
			r.contract_code
				? '<span class="kt-bud-downstream-code">' + esc(r.contract_code) + "</span>"
				: '<span class="kt-bud-downstream-muted">' +
					esc(r.contract_display || "—") +
					"</span>";
		return (
			'<tr data-testid="kt-bud-downstream-row" data-reservation-code="' +
			esc(r.code) +
			'">' +
			'<td class="px-4 py-3 font-medium">' +
			esc(r.requirement || "—") +
			"</td>" +
			'<td class="px-4 py-3 kt-bud-down-phase">' +
			'<span class="kt-bud-downstream-code">' +
			esc(r.demand_code || "—") +
			"</span></td>" +
			'<td class="px-4 py-3">' +
			'<span class="kt-bud-downstream-code">' +
			esc(r.plan_item_code || "—") +
			"</span></td>" +
			'<td class="px-4 py-3 kt-bud-down-phase">' +
			'<span class="kt-bud-downstream-code">' +
			esc(r.tender_code || "—") +
			"</span></td>" +
			'<td class="px-4 py-3">' +
			contractCell +
			"</td>" +
			'<td class="px-4 py-3 text-right font-data-mono kt-bud-down-phase">' +
			esc(r.reserved_balance_display || "—") +
			"</td>" +
			'<td class="px-4 py-3 text-right font-data-mono">' +
			esc(r.commitment_display || "—") +
			"</td>" +
			'<td class="px-4 py-3 kt-bud-down-phase">' +
			'<span data-kt-bud-downstream-status="' +
			esc(statusKind) +
			'">' +
			esc(r.status || "") +
			"</span></td>" +
			'<td class="px-4 py-3 text-right">' +
			'<button type="button" class="kt-bud-downstream-action" data-testid="kt-bud-downstream-action" data-kt-bud-downstream-action="view" data-reservation-code="' +
			esc(r.code) +
			'">' +
			'<span class="kt-bud-downstream-action-label">' +
			esc(r.action_label || "View reservation") +
			"</span>" +
			'<span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>' +
			"</button></td></tr>"
		);
	}

	function bindDownstream($root, budgetCode) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var gen = $root.attr("data-kt-bud-mount-gen") || "0";
		hideDownstreamNotice($root);
		return call("get_funding_lineage", { budget: budgetCode })
			.then(function (dto) {
				if (($root.attr("data-kt-bud-mount-gen") || "0") !== gen) {
					return dto;
				}
				if (!dto) {
					$root.attr("data-kt-bud-live", "0");
					return dto;
				}
				var budget = dto.budget || {};
				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, budget, { code: budget.code || budgetCode || "" }),
					dto.capabilities
				);

				var rows = dto.rows || [];
				$root.data("ktBudDownstreamCache", rows);

				function filteredRows() {
					var query = ($root.find("[data-kt-bud-downstream-search]").val() || "")
						.toLowerCase()
						.trim();
					var status = $root.find('[data-kt-bud-downstream-filter="status"]').val() || "";
					return rows.filter(function (r) {
						if (status && (r.status || "") !== status) {
							return false;
						}
						if (!query) {
							return true;
						}
						return (
							(r.requirement || "").toLowerCase().indexOf(query) >= 0 ||
							(r.demand_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.plan_item_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.tender_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.contract_code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.code || "").toLowerCase().indexOf(query) >= 0 ||
							(r.status || "").toLowerCase().indexOf(query) >= 0
						);
					});
				}

				function paintTable(filtered) {
					var $tbody = $root.find("[data-kt-bud-downstream-tbody]");
					if (
						window.kentender_core &&
						kentender_core.table &&
						typeof kentender_core.table.attachPagination === "function"
					) {
						kentender_core.table
							.attachPagination($root, {
								footerSelector: '[data-testid="kt-bud-downstream-table-footer"]',
								renderPage: function (pageRows) {
									if (!pageRows || !pageRows.length) {
										$tbody.html(
											'<tr><td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">No downstream usage matches.</td></tr>'
										);
										return;
									}
									$tbody.html(pageRows.map(downstreamRowHtml).join(""));
								},
							})
							.setRows(filtered, true);
						return;
					}
					if (!filtered.length) {
						$tbody.html(
							'<tr><td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">No downstream usage matches.</td></tr>'
						);
					} else {
						$tbody.html(filtered.map(downstreamRowHtml).join(""));
					}
				}

				function renderFiltered() {
					paintTable(filteredRows());
				}

				renderFiltered();

				$root
					.off("input.ktBudDownSearch change.ktBudDownFilter")
					.on(
						"input.ktBudDownSearch change.ktBudDownFilter",
						"[data-kt-bud-downstream-search], [data-kt-bud-downstream-filter]",
						function () {
							renderFiltered();
						}
					);

				$root
					.off("click.ktBudDownRow")
					.on("click.ktBudDownRow", "[data-kt-bud-downstream-action]", function (e) {
						e.preventDefault();
						var code = $(this).attr("data-reservation-code");
						var cache = $root.data("ktBudDownstreamCache") || [];
						var row = null;
						for (var i = 0; i < cache.length; i++) {
							if (cache[i].code === code) {
								row = cache[i];
								break;
							}
						}
						row = row || {};
						var lines = [
							row.code ? __("Reservation") + ": " + row.code : "",
							row.requirement ? __("Requirement") + ": " + row.requirement : "",
							row.demand_code ? __("Demand") + ": " + row.demand_code : "",
							row.plan_item_code ? __("Plan item") + ": " + row.plan_item_code : "",
							row.tender_code ? __("Tender") + ": " + row.tender_code : "",
							row.contract_code ? __("Contract") + ": " + row.contract_code : "",
							row.reserved_balance_display
								? __("Reserved balance") + ": " + row.reserved_balance_display
								: "",
							row.commitment_display
								? __("Commitment") + ": " + row.commitment_display
								: "",
							row.status ? __("Status") + ": " + row.status : "",
						].filter(Boolean);
						showDownstreamNotice($root, {
							title: row.requirement || code || __("Downstream usage"),
							message:
								lines.join("\n") ||
								__("Read-only downstream lineage for this reservation."),
						});
					});

				$root
					.off("click.ktBudDownNotice")
					.on(
						"click.ktBudDownNotice",
						"[data-kt-bud-downstream-notice-dismiss]",
						function (e) {
							e.preventDefault();
							hideDownstreamNotice($root);
						}
					);

				$root.attr("data-kt-bud-primary-action", (dto.capabilities || {}).primary_action || "");
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showDownstreamNotice($root, {
					title: __("Could not load downstream usage"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function showReviewNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-review-notice]");
		$n.removeClass("hidden").removeAttr("hidden");
		$n.find("[data-kt-bud-review-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-review-notice-msg]").text(opts.message || "");
	}

	function hideReviewNotice($root) {
		$root
			.find("[data-kt-bud-review-notice]")
			.addClass("hidden")
			.attr("hidden", "hidden");
	}

	function showReviewFooterError($root, message) {
		var $e = $root.find("[data-kt-bud-review-footer-error]");
		if (!message) {
			$e.addClass("hidden").attr("hidden", "hidden").text("");
			return;
		}
		$e.removeClass("hidden").removeAttr("hidden").text(message);
		try {
			$e[0].scrollIntoView({ block: "nearest", behavior: "smooth" });
		} catch (err) {
			/* ignore */
		}
	}

	function reviewGroupCardHtml(g) {
		var isIssue = g.status === "issue";
		var issue = (g.issues && g.issues[0]) || null;
		var icon = isIssue ? "warning" : "check_circle";
		var body = isIssue
			? '<div class="kt-bud-review-issue-box"><span class="material-symbols-outlined text-sm mt-0.5" aria-hidden="true">error</span><span class="font-body-md text-body-md">' +
				esc(issue.message || g.summary || "") +
				"</span></div>" +
				(issue
					? '<button type="button" class="kt-bud-review-action" data-testid="kt-bud-review-group-action" data-kt-bud-review-group-action="' +
						esc(issue.action_route || "") +
						'"><span class="kt-bud-review-action-label">' +
						esc(issue.action_label || __("Review")) +
						'</span><span class="material-symbols-outlined text-sm" aria-hidden="true">arrow_forward</span></button>'
					: "")
			: '<p class="kt-bud-review-ok-msg font-body-md text-body-md">' +
				esc(g.summary || __("All requirements met.")) +
				"</p>";
		return (
			'<div class="kt-bud-review-card' +
			(isIssue ? " is-issue" : "") +
			'" data-testid="kt-bud-review-group" data-kt-bud-review-group="' +
			esc(g.key || "") +
			'" data-status="' +
			esc(g.status || "") +
			'">' +
			'<div class="kt-bud-review-card-rail" aria-hidden="true"></div>' +
			'<div class="kt-bud-review-card-top">' +
			'<div class="kt-bud-review-card-title-wrap">' +
			'<div class="kt-bud-review-card-icon"><span class="material-symbols-outlined' +
			(isIssue ? "" : " icon-fill") +
			'" aria-hidden="true">' +
			icon +
			"</span></div>" +
			'<h3 class="font-headline-sm text-headline-sm text-on-surface">' +
			esc(g.title || "") +
			"</h3></div>" +
			'<div class="kt-bud-review-card-count"><span data-kt-bud-review-group-count>' +
			esc(String(g.complete_count || 0) + "/" + String(g.total_count || 0)) +
			'</span><div class="kt-bud-review-card-count-label">COMPLETE</div></div></div>' +
			body +
			"</div>"
		);
	}

	function applyReviewDto($root, dto) {
		var budget = dto.budget || {};
		var caps = dto.capabilities || {};
		var gov = dto.governance || {};
		var status = budget.status || "";
		$root.attr("data-kt-bud-task-id", caps.task_id || "");
		$root.attr("data-kt-bud-task-token", caps.concurrency_token || "");

		paintBudgetWorkspaceChrome(
			$root,
			Object.assign({}, budget, { status: status }),
			caps
		);

		$root
			.find("[data-kt-bud-review-status-chip]")
			.attr("data-status", status);
		$root
			.find("[data-kt-bud-review-status-label]")
			.text(budget.status_label || status || "—");
		$root
			.find("[data-kt-bud-review-disclaimer]")
			.text(dto.disclaimer || "");

		var $groups = $root.find("[data-kt-bud-review-groups]");
		$groups.html((dto.groups || []).map(reviewGroupCardHtml).join(""));

		var $act = $root.find("[data-kt-bud-review-activation]");
		if (caps.show_activation_record) {
			var summary =
				__("Activated by {0} on {1}")
					.replace("{0}", gov.activated_by || "—")
					.replace("{1}", gov.activated_at_display || gov.activated_at || "—") +
				(gov.authoritative_reference
					? " · " + gov.authoritative_reference
					: "");
			$act.removeClass("hidden").removeAttr("hidden");
			$root.find("[data-kt-bud-review-activation-summary]").text(summary);
		} else {
			$act.addClass("hidden").attr("hidden", "hidden");
		}

		var $run = $root.find('[data-kt-bud-review-action="run"]');
		var $submit = $root.find('[data-kt-bud-review-action="submit"]');
		var $ret = $root.find('[data-kt-bud-review-action="return"]');
		var $mark = $root.find('[data-kt-bud-review-action="mark"]');
		var $activate = $root.find('[data-kt-bud-review-action="activate"]');
		var $lock = $root.find("[data-kt-bud-review-activate-lock]");

		var draftLike = status === "Draft" || status === "Returned";
		var submitted = status === "Submitted";
		var activeLike = status === "Active" || status === "Closed" || status === "Cancelled";

		$run.prop("disabled", !caps.can_run_check);
		if (draftLike) {
			$submit.removeAttr("hidden").prop("disabled", !caps.can_submit);
			$ret.attr("hidden", "hidden");
			$mark.attr("hidden", "hidden");
			$activate.attr("hidden", "hidden");
		} else if (submitted) {
			$submit.attr("hidden", "hidden");
			$ret.removeAttr("hidden").prop("disabled", !caps.can_return);
			$mark
				.removeAttr("hidden")
				.prop("disabled", !caps.can_mark_reviewed)
				.toggleClass("hidden", !caps.can_mark_reviewed && !!gov.reviewed_by);
			if (gov.reviewed_by && !caps.can_mark_reviewed) {
				$mark.attr("hidden", "hidden");
			}
			$activate.removeAttr("hidden").prop("disabled", !caps.can_activate);
			if (caps.activate_lock_reason && !caps.can_activate) {
				$lock.removeClass("hidden");
				$activate.attr("title", caps.activate_lock_reason);
			} else {
				$lock.addClass("hidden");
				$activate.removeAttr("title");
			}
		} else {
			$submit.attr("hidden", "hidden");
			$ret.attr("hidden", "hidden");
			$mark.attr("hidden", "hidden");
			$activate.attr("hidden", "hidden");
			if (activeLike) {
				$run.prop("disabled", false);
			}
		}

		$root.attr("data-kt-bud-primary-action", caps.primary_action || "");
	}

	function openReviewReturnModal($root) {
		var $m = $root.find("[data-kt-bud-review-reason-modal]");
		$m.removeClass("hidden").removeAttr("hidden");
		$root.find("[data-kt-bud-review-reason-comment]").val("");
		$root.find('[data-kt-bud-error="comment"]').addClass("hidden").text("");
	}

	function closeReviewReturnModal($root) {
		$root
			.find("[data-kt-bud-review-reason-modal]")
			.addClass("hidden")
			.attr("hidden", "hidden");
	}

	function bindReview($root, budgetCode) {
		var token = Number($root.attr("data-kt-bud-bind-token") || 0) + 1;
		$root.attr("data-kt-bud-bind-token", String(token));
		$root.attr("data-kt-bud-live", "0");
		hideReviewNotice($root);
		showReviewFooterError($root, "");

		function reload() {
			var routeTask =
				(frappe.route_options && frappe.route_options.task_id) ||
				$root.attr("data-kt-bud-task-id") ||
				"";
			return call("get_budget_readiness", { budget: budgetCode, task_id: routeTask }).then(function (dto) {
				if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
					return dto;
				}
				if (!dto) {
					throw new Error("Empty readiness payload");
				}
				applyReviewDto($root, dto);
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			});
		}

		function mutate(method, payload) {
			showReviewFooterError($root, "");
			var body = payload || { budget: budgetCode };
			body.task_id = body.task_id || $root.attr("data-kt-bud-task-id") || "";
			body.concurrency_token =
				body.concurrency_token || $root.attr("data-kt-bud-task-token") || "";
			return call(method, { payload: body })
				.then(function (res) {
					if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
						return res;
					}
					if (res && res.ok === false) {
						var errors = res.errors || {};
						var msg =
							errors.blockers ||
							errors.comment ||
							errors.status ||
							errors.reviewed_by ||
							errors.approval_evidence ||
							__("Action failed. Resolve issues and try again.");
						showReviewFooterError($root, msg);
						if (errors.comment) {
							$root
								.find('[data-kt-bud-error="comment"]')
								.text(errors.comment)
								.removeClass("hidden");
						}
						if (res.readiness) {
							applyReviewDto($root, res.readiness);
						}
						return res;
					}
					closeReviewReturnModal($root);
					if (res && res.readiness) {
						applyReviewDto($root, res.readiness);
					} else {
						return reload().then(function () {
							return res;
						});
					}
					showReviewNotice($root, {
						title: __("Updated"),
						message: __("Budget readiness and workflow state refreshed."),
					});
					return res;
				})
				.catch(function (err) {
					showReviewFooterError(
						$root,
						__("Action failed. Refresh and try again.")
					);
					throw err;
				});
		}

		return reload()
			.then(function (dto) {
				$root.off(".ktBudReview");
				$root.on("click.ktBudReview", "[data-kt-bud-review-notice-dismiss]", function (e) {
					e.preventDefault();
					hideReviewNotice($root);
				});
				$root.on("click.ktBudReview", "[data-kt-bud-review-group-action]", function (e) {
					e.preventDefault();
					var route = ($(this).attr("data-kt-bud-review-group-action") || "").trim();
					if (!route) {
						return;
					}
					var parts = route.split("/").filter(Boolean);
					if (parts.length) {
						frappe.set_route.apply(frappe, parts);
					}
				});
				$root.on("click.ktBudReview", "[data-kt-bud-review-action]", function (e) {
					e.preventDefault();
					var action = $(this).attr("data-kt-bud-review-action");
					if (action === "run") {
						showReviewFooterError($root, "");
						reload().then(function () {
							showReviewNotice($root, {
								title: __("Readiness check complete"),
								message: __("Checklist counts refreshed from the current baseline."),
							});
						});
						return;
					}
					if (action === "submit") {
						mutate("submit_budget", { budget: budgetCode });
						return;
					}
					if (action === "return") {
						openReviewReturnModal($root);
						return;
					}
					if (action === "mark") {
						mutate("mark_budget_reviewed", { budget: budgetCode });
						return;
					}
					if (action === "activate") {
						mutate("activate_budget", { budget: budgetCode });
					}
				});
				$root.on(
					"click.ktBudReview",
					"[data-kt-bud-review-reason-close], [data-kt-bud-review-reason-cancel]",
					function (e) {
						e.preventDefault();
						closeReviewReturnModal($root);
					}
				);
				$root.on("click.ktBudReview", "[data-kt-bud-review-reason-confirm]", function (e) {
					e.preventDefault();
					var comment = (
						$root.find("[data-kt-bud-review-reason-comment]").val() || ""
					).trim();
					if (!comment) {
						$root
							.find('[data-kt-bud-error="comment"]')
							.text(__("Comment is required when returning a Budget"))
							.removeClass("hidden");
						return;
					}
					mutate("return_budget", { budget: budgetCode, comment: comment });
				});
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showReviewNotice($root, {
					title: __("Could not load readiness"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function showAuditNotice($root, opts) {
		opts = opts || {};
		var $n = $root.find("[data-kt-bud-audit-notice]");
		$n.removeClass("hidden").removeAttr("hidden");
		$n.find("[data-kt-bud-audit-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-audit-notice-msg]").text(opts.message || "");
	}

	function hideAuditNotice($root) {
		$root.find("[data-kt-bud-audit-notice]").addClass("hidden").attr("hidden", "hidden");
	}

	function csvEscape(val) {
		var s = String(val == null ? "" : val);
		if (/^[=+\-@]/.test(s)) {
			s = "'" + s;
		}
		if (/[",\n\r]/.test(s)) {
			return '"' + s.replace(/"/g, '""') + '"';
		}
		return s;
	}

	function auditEventIcon(eventType) {
		if (eventType === "Budget activated") {
			return "check_circle";
		}
		if (eventType === "Funding reserved" || eventType === "Reservation partially converted") {
			return "lock";
		}
		if (eventType === "Baseline registered") {
			return "dataset";
		}
		if (eventType === "Revision applied") {
			return "edit_note";
		}
		if (eventType === "Contract commitment recorded") {
			return "gavel";
		}
		if (eventType === "Expenditure snapshot recorded") {
			return "payments";
		}
		return "history";
	}

	function auditActorInitials(name) {
		var parts = String(name || "")
			.trim()
			.split(/\s+/)
			.filter(Boolean);
		if (!parts.length) {
			return "?";
		}
		if (parts.length === 1) {
			return parts[0].slice(0, 2).toUpperCase();
		}
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function auditActorHtml(r) {
		var kind = r.actor_kind || "user";
		var name = r.actor || "—";
		var badgeInner =
			kind === "integration"
				? '<span class="material-symbols-outlined" aria-hidden="true">api</span>'
				: kind === "system"
					? '<span class="material-symbols-outlined" aria-hidden="true">settings</span>'
					: esc(auditActorInitials(name));
		return (
			'<span class="kt-bud-audit-actor">' +
			'<span class="kt-bud-audit-actor-badge" data-kind="' +
			esc(kind) +
			'">' +
			badgeInner +
			"</span>" +
			"<span>" +
			esc(name) +
			"</span></span>"
		);
	}

	function auditRowHtml(r) {
		return (
			'<tr data-testid="kt-bud-audit-row" data-audit-id="' +
			esc(r.id || "") +
			'" data-record-code="' +
			esc(r.record_code || "") +
			'">' +
			'<td class="kt-bud-audit-mono whitespace-nowrap">' +
			'<span class="inline-flex items-center gap-2"><span class="material-symbols-outlined text-[16px] text-on-surface-variant" aria-hidden="true">schedule</span>' +
			esc(r.event_at_display || "—") +
			"</span></td>" +
			'<td><span class="kt-bud-audit-event-pill" data-event="' +
			esc(r.event_type || "") +
			'"><span class="material-symbols-outlined" aria-hidden="true">' +
			auditEventIcon(r.event_type) +
			"</span>" +
			esc(r.event_type || "—") +
			"</span></td>" +
			'<td class="kt-bud-audit-mono whitespace-nowrap">' +
			esc(r.record_code || "—") +
			"</td>" +
			"<td>" +
			auditActorHtml(r) +
			"</td>" +
			'<td class="min-w-[200px]">' +
			esc(r.change_summary_display || r.change_summary || "—") +
			"</td>" +
			'<td class="kt-bud-audit-mono text-on-surface-variant whitespace-nowrap">' +
			esc(r.source_reference || "—") +
			"</td>" +
			'<td class="text-right">' +
			'<button type="button" class="kt-bud-audit-action" data-testid="kt-bud-audit-action" data-kt-bud-audit-action="view" data-audit-id="' +
			esc(r.id || "") +
			'"><span class="kt-bud-audit-action-label">' +
			esc(r.action_label || __("View")) +
			"</span></button>" +
			"</td></tr>"
		);
	}

	function fillAuditSelect($sel, values, allLabel) {
		var cur = $sel.val() || "";
		var opts = ['<option value="">' + esc(allLabel) + "</option>"];
		(values || []).forEach(function (v) {
			if (!v) {
				return;
			}
			opts.push(
				'<option value="' +
					esc(v) +
					'"' +
					(v === cur ? " selected" : "") +
					">" +
					esc(v) +
					"</option>"
			);
		});
		$sel.html(opts.join(""));
		if (cur) {
			$sel.val(cur);
		}
	}

	function bindAudit($root, budgetCode) {
		var token = Number($root.attr("data-kt-bud-bind-token") || 0) + 1;
		$root.attr("data-kt-bud-bind-token", String(token));
		$root.attr("data-kt-bud-live", "0");
		hideAuditNotice($root);
		var lastRows = [];

		function readFilters() {
			return {
				budget: budgetCode,
				event_type: $root.find('[data-kt-bud-audit-filter="event_type"]').val() || "",
				actor: $root.find('[data-kt-bud-audit-filter="actor"]').val() || "",
				date_from: $root.find('[data-kt-bud-audit-filter="date_from"]').val() || "",
				date_to: $root.find('[data-kt-bud-audit-filter="date_to"]').val() || "",
			};
		}

		function renderRows(rows) {
			lastRows = rows || [];
			var $tbody = $root.find("[data-kt-bud-audit-tbody]");
			if (
				window.kentender_core &&
				kentender_core.table &&
				typeof kentender_core.table.attachPagination === "function"
			) {
				kentender_core.table
					.attachPagination($root, {
						footerSelector: '[data-testid="kt-bud-audit-table-footer"]',
						renderPage: function (pageRows) {
							if (!pageRows.length) {
								$tbody.html(
									'<tr><td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">No audit events match.</td></tr>'
								);
								return;
							}
							$tbody.html(pageRows.map(auditRowHtml).join(""));
						},
					})
					.setRows(lastRows, true);
				return;
			}
			if (!lastRows.length) {
				$tbody.html(
					'<tr><td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">No audit events match.</td></tr>'
				);
				return;
			}
			$tbody.html(lastRows.map(auditRowHtml).join(""));
		}

		function reload() {
			return call("get_budget_audit", readFilters()).then(function (dto) {
				if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
					return dto;
				}
				if (!dto) {
					throw new Error("Empty audit payload");
				}
				var budget = dto.budget || {};
				paintBudgetWorkspaceChrome(
					$root,
					Object.assign({}, budget, { code: budget.code || budgetCode || "" }),
					dto.capabilities
				);

				var filters = dto.filters || {};
				fillAuditSelect(
					$root.find('[data-kt-bud-audit-filter="event_type"]'),
					filters.event_types || [],
					__("All Events")
				);
				fillAuditSelect(
					$root.find('[data-kt-bud-audit-filter="actor"]'),
					filters.actors || [],
					__("All Sources")
				);
				renderRows(dto.rows || []);
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			});
		}

		return reload()
			.then(function (dto) {
				$root.off(".ktBudAudit");
				$root.on(
					"change.ktBudAudit",
					"[data-kt-bud-audit-filter]",
					function () {
						reload().catch(function (err) {
							console.warn("Budget audit filter failed", err);
						});
					}
				);
				$root.on("click.ktBudAudit", "[data-kt-bud-audit-notice-dismiss]", function (e) {
					e.preventDefault();
					hideAuditNotice($root);
				});
				$root.on("click.ktBudAudit", "[data-kt-bud-audit-action]", function (e) {
					e.preventDefault();
					var id = $(this).attr("data-audit-id");
					var row = lastRows.find(function (r) {
						return r.id === id;
					});
					if (!row) {
						return;
					}
					showAuditNotice($root, {
						title: (row.event_type || __("Audit event")) + " · " + (row.record_code || ""),
						message: [
							__("When") + ": " + (row.event_at_display || "—"),
							__("Actor") + ": " + (row.actor || "—"),
							__("Change") + ": " + (row.change_summary_display || "—"),
							__("Source") + ": " + (row.source_reference || "—"),
							row.reason ? __("Reason") + ": " + row.reason : "",
						]
							.filter(Boolean)
							.join("\n"),
					});
				});
				$root.on("click.ktBudAudit", "[data-kt-bud-audit-export]", function (e) {
					e.preventDefault();
					var headers = [
						"Date and time",
						"Event",
						"Record",
						"User or integration",
						"Before and after summary",
						"Source reference",
					];
					var lines = [headers.map(csvEscape).join(",")];
					lastRows.forEach(function (r) {
						lines.push(
							[
								r.event_at_display,
								r.event_type,
								r.record_code,
								r.actor,
								r.change_summary_display,
								r.source_reference,
							]
								.map(csvEscape)
								.join(",")
						);
					});
					var blob = new Blob([lines.join("\n")], {
						type: "text/csv;charset=utf-8",
					});
					var url = URL.createObjectURL(blob);
					var a = document.createElement("a");
					a.href = url;
					a.download = "budget-audit-" + budgetCode + ".csv";
					document.body.appendChild(a);
					a.click();
					a.remove();
					URL.revokeObjectURL(url);
					showAuditNotice($root, {
						title: __("Export ready"),
						message: __("Downloaded {0} audit rows for the current filters.").replace(
							"{0}",
							String(lastRows.length)
						),
					});
				});
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showAuditNotice($root, {
					title: __("Could not load audit history"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function showPerfNotice($root, opts) {
		var $n = $root.find("[data-kt-bud-perf-notice]");
		$n.removeClass("hidden").removeAttr("hidden");
		$n.find("[data-kt-bud-perf-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-perf-notice-msg]").text(opts.message || "");
	}

	function hidePerfNotice($root) {
		$root.find("[data-kt-bud-perf-notice]").addClass("hidden").attr("hidden", "hidden");
	}

	function fillPerfSelect($sel, values, allLabel, mapLabel) {
		var cur = $sel.val() || "";
		var opts = ['<option value="">' + esc(allLabel) + "</option>"];
		(values || []).forEach(function (v) {
			var value = typeof v === "object" ? v.code || v.id || "" : v;
			var label =
				typeof mapLabel === "function"
					? mapLabel(v)
					: typeof v === "object"
						? v.name
							? v.name + (v.code ? " (" + v.code + ")" : "")
							: value
						: v;
			if (!value && typeof v !== "object") {
				return;
			}
			if (!value) {
				return;
			}
			opts.push(
				'<option value="' +
					esc(value) +
					'"' +
					(value === cur ? " selected" : "") +
					">" +
					esc(label) +
					"</option>"
			);
		});
		$sel.html(opts.join(""));
		if (cur) {
			$sel.val(cur);
		}
	}

	function coverageRowHtml(r) {
		return (
			'<tr data-testid="kt-bud-performance-coverage-row" data-target-code="' +
			esc(r.target_code || "") +
			'" data-budget-code="' +
			esc(r.budget_code || "") +
			'">' +
			"<td><div class=\"kt-bud-perf-target-name\">" +
			esc(r.target_name || "—") +
			'</div><div class="kt-bud-perf-target-code">' +
			esc(r.target_code || "") +
			"</div></td>" +
			'<td class="text-right kt-bud-perf-mono">' +
			esc(String(r.line_count || 0)) +
			"</td>" +
			'<td class="text-right kt-bud-perf-mono">' +
			esc(r.approved_display || "—") +
			"</td>" +
			'<td class="text-right kt-bud-perf-mono text-status-reserved">' +
			esc(r.reserved_display || "—") +
			"</td>" +
			'<td class="text-right kt-bud-perf-mono text-status-committed">' +
			esc(r.committed_display || "—") +
			"</td>" +
			'<td class="text-right kt-bud-perf-mono text-status-available">' +
			esc(r.available_display || "—") +
			"</td>" +
			'<td class="text-center">' +
			esc(r.attention_label || "—") +
			"</td>" +
			'<td class="text-right">' +
			'<button type="button" class="kt-bud-perf-action" data-testid="kt-bud-performance-coverage-action" data-kt-bud-perf-action="view_details" data-budget-code="' +
			esc(r.budget_code || "") +
			'">' +
			esc(r.action_label || __("View Details")) +
			"</button></td></tr>"
		);
	}

	function exceptionRowHtml(r) {
		return (
			'<tr data-testid="kt-bud-performance-exception-row" data-exception-kind="' +
			esc(r.exception_kind || "") +
			'">' +
			"<td><span class=\"inline-flex items-center gap-2\"><span class=\"material-symbols-outlined text-status-exhausted text-sm\" aria-hidden=\"true\">error</span>" +
			esc(r.exception || "—") +
			"</span></td>" +
			"<td>" +
			esc(r.budget_line || "—") +
			"</td>" +
			"<td>" +
			esc(r.owner || "—") +
			"</td>" +
			"<td>" +
			esc(r.age_label || "—") +
			"</td>" +
			'<td class="text-right">' +
			'<button type="button" class="kt-bud-perf-exc-action" data-testid="kt-bud-performance-exception-action" data-kt-bud-perf-action="review_finance_sync" data-line-code="' +
			esc(r.budget_line_code || "") +
			'">' +
			esc(r.action_label || __("Review finance sync")) +
			"</button></td></tr>"
		);
	}

	function bindPerformance($root) {
		if (!$root || !$root.length) {
			return Promise.resolve(null);
		}
		var token = Number($root.attr("data-kt-bud-bind-token") || 0) + 1;
		$root.attr("data-kt-bud-bind-token", String(token));
		$root.attr("data-kt-bud-live", "0");
		hidePerfNotice($root);
		var lastExport = null;

		function readFilters() {
			return {
				fiscal_period: $root.find('[data-kt-bud-perf-filter="fiscal_period"]').val() || "",
				programme: $root.find('[data-kt-bud-perf-filter="programme"]').val() || "",
				primary_target: $root.find('[data-kt-bud-perf-filter="primary_target"]').val() || "",
				funding_status: $root.find('[data-kt-bud-perf-filter="funding_status"]').val() || "",
			};
		}

		function paintDto(dto) {
			var entity = dto.entity || {};
			var kpis = dto.kpis || {};
			var filters = dto.filters || {};
			$root.find("[data-kt-bud-perf-entity]").text(entity.name || entity.code || "—");
			$root.find("[data-kt-bud-perf-as-at]").text(
				dto.as_at_display ? __("As at") + " " + dto.as_at_display : "—"
			);
			$root.find('[data-kt-bud-perf-kpi-value="approved"]').text(kpis.approved_display || "—");
			$root.find('[data-kt-bud-perf-kpi-value="reserved"]').text(kpis.reserved_display || "—");
			$root.find('[data-kt-bud-perf-kpi-value="committed"]').text(kpis.committed_display || "—");
			$root.find('[data-kt-bud-perf-kpi-value="available"]').text(kpis.available_display || "—");
			$root.find('[data-kt-bud-perf-kpi-value="actual"]').text(kpis.actual_display || "—");
			$root.find('[data-kt-bud-perf-kpi-value="attention"]').text(kpis.attention_display || "0");
			$root.find("[data-kt-bud-perf-disclaimer-text]").text(dto.disclaimer || "");

			fillPerfSelect(
				$root.find('[data-kt-bud-perf-filter="fiscal_period"]'),
				filters.fiscal_periods || [],
				__("All fiscal periods"),
				function (v) {
					return "FY " + v;
				}
			);
			fillPerfSelect(
				$root.find('[data-kt-bud-perf-filter="programme"]'),
				filters.programmes || [],
				__("All programmes")
			);
			fillPerfSelect(
				$root.find('[data-kt-bud-perf-filter="primary_target"]'),
				filters.targets || [],
				__("All strategic targets")
			);
			fillPerfSelect(
				$root.find('[data-kt-bud-perf-filter="funding_status"]'),
				filters.funding_statuses || [],
				__("All funding statuses")
			);

			var $ct = $root.find("[data-kt-bud-perf-coverage-tbody]");
			var coverage = dto.coverage_rows || [];
			if (!coverage.length) {
				$ct.html(
					'<tr><td colspan="8" class="px-4 py-8 text-center text-on-surface-variant">No strategy funding coverage for the current filters.</td></tr>'
				);
			} else {
				$ct.html(coverage.map(coverageRowHtml).join(""));
			}

			var $et = $root.find("[data-kt-bud-perf-exceptions-tbody]");
			var exceptions = dto.exception_rows || [];
			if (!exceptions.length) {
				$et.html(
					'<tr><td colspan="5" class="px-4 py-8 text-center text-on-surface-variant">No funding exceptions.</td></tr>'
				);
			} else {
				$et.html(exceptions.map(exceptionRowHtml).join(""));
			}

			var caps = dto.capabilities || {};
			var $exportBtn = $root.find("[data-kt-bud-perf-export]");
			if (caps.can_export) {
				$exportBtn.removeClass("hidden").prop("disabled", false).attr("aria-hidden", "false");
			} else {
				$exportBtn.addClass("hidden").prop("disabled", true).attr("aria-hidden", "true");
			}
		}

		function reload() {
			return call("get_funding_performance", readFilters()).then(function (dto) {
				if (String($root.attr("data-kt-bud-bind-token")) !== String(token)) {
					return dto;
				}
				if (!dto) {
					throw new Error("Empty performance payload");
				}
				paintDto(dto);
				lastExport = null;
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-error", "0");
				return dto;
			});
		}

		function downloadExport() {
			return call("export_funding_performance", readFilters()).then(function (payload) {
				lastExport = payload;
				var lineage = (payload && payload.lineage) || {};
				var headers = [
					"Section",
					"Strategic target",
					"Target code",
					"Budget lines",
					"Approved",
					"Reserved",
					"Committed",
					"Available",
					"Attention",
					"Exception",
					"Budget line",
					"Owner",
					"Age",
				];
				function csvEscape(val) {
					var s = val == null ? "" : String(val);
					if (/^[=+\-@]/.test(s)) {
						s = "'" + s;
					}
					if (/[",\n\r]/.test(s)) {
						return '"' + s.replace(/"/g, '""') + '"';
					}
					return s;
				}
				var lines = [
					["Lineage", "Entity", lineage.entity_name || "", lineage.entity_code || ""]
						.map(csvEscape)
						.join(","),
					["Lineage", "As at", lineage.as_at_display || "", ""]
						.map(csvEscape)
						.join(","),
					["Lineage", "Source coverage", lineage.source_coverage || "", ""]
						.map(csvEscape)
						.join(","),
					["Lineage", "Disclaimer", lineage.disclaimer || "", ""]
						.map(csvEscape)
						.join(","),
					headers.map(csvEscape).join(","),
				];
				(payload.coverage_rows || []).forEach(function (r) {
					lines.push(
						[
							"Coverage",
							r.target_name,
							r.target_code,
							r.line_count,
							r.approved_display,
							r.reserved_display,
							r.committed_display,
							r.available_display,
							r.attention_label,
							"",
							"",
							"",
							"",
						]
							.map(csvEscape)
							.join(",")
					);
				});
				(payload.exception_rows || []).forEach(function (r) {
					lines.push(
						[
							"Exception",
							"",
							"",
							"",
							"",
							"",
							"",
							"",
							"",
							r.exception,
							r.budget_line,
							r.owner,
							r.age_label,
						]
							.map(csvEscape)
							.join(",")
					);
				});
				var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
				var url = URL.createObjectURL(blob);
				var a = document.createElement("a");
				a.href = url;
				a.download = "funding-performance-export.csv";
				document.body.appendChild(a);
				a.click();
				a.remove();
				URL.revokeObjectURL(url);
				showPerfNotice($root, {
					title: __("Export ready"),
					message: __("Downloaded the filtered Funding Performance report with lineage metadata."),
				});
				return payload;
			});
		}

		return reload()
			.then(function (dto) {
				$root.off(".ktBudPerf");
				$root.on("change.ktBudPerf", "[data-kt-bud-perf-filter]", function () {
					reload().catch(function (err) {
						console.warn("Funding performance filter failed", err);
					});
				});
				$root.on("click.ktBudPerf", "[data-kt-bud-perf-notice-dismiss]", function (e) {
					e.preventDefault();
					hidePerfNotice($root);
				});
				$root.on("click.ktBudPerf", "[data-kt-bud-perf-export]", function (e) {
					e.preventDefault();
					downloadExport().catch(function (err) {
						showPerfNotice($root, {
							title: __("Export failed"),
							message: __("Could not export the current view. Refresh and try again."),
						});
						console.warn("Funding performance export failed", err);
					});
				});
				$root.on("click.ktBudPerf", "[data-kt-bud-perf-action]", function (e) {
					e.preventDefault();
					var action = $(this).attr("data-kt-bud-perf-action");
					if (action === "view_details") {
						var code = $(this).attr("data-budget-code");
						if (code) {
							frappe.set_route("budget-lines", code);
							return;
						}
						showPerfNotice($root, {
							title: __("View details"),
							message: __("Open a Budget from the portfolio to inspect line-level funding."),
						});
						return;
					}
					if (action === "review_finance_sync") {
						showPerfNotice($root, {
							title: __("Review finance sync"),
							message: __(
								"Actual expenditure on this line is stale. Ask Finance Integration to re-sync expenditure; live sync is not available from this screen."
							),
						});
					}
				});
				return dto;
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				$root.attr("data-kt-bud-error", "1");
				showPerfNotice($root, {
					title: __("Could not load Funding Performance"),
					message: __("Refresh and try again. If the problem continues, contact support."),
				});
				throw err;
			});
	}

	function ensureCheckReserveHost() {
		var $host = $("body > [data-testid='kt-bud-check-reserve-host']");
		if ($host.length) {
			return $host;
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.check_reserve === "function"
				? kentender_budget.ui_fixtures.check_reserve()
				: "";
		if (!html) {
			return $();
		}
		$host = $(html);
		$("body").append($host);
		return $host;
	}

	function showCrNotice($root, opts) {
		var $n = $root.find("[data-kt-bud-cr-notice]");
		$n.removeClass("hidden").removeAttr("hidden");
		$n.find("[data-kt-bud-cr-notice-title]").text(opts.title || "");
		$n.find("[data-kt-bud-cr-notice-msg]").text(opts.message || "");
	}

	function hideCrNotice($root) {
		$root.find("[data-kt-bud-cr-notice]").addClass("hidden").attr("hidden", "hidden");
	}

	function closeCheckReserve() {
		var $host = $("body > [data-testid='kt-bud-check-reserve-host']");
		if ($host.length) {
			$host.attr("hidden", "hidden");
			$host.find("[data-testid='kt-bud-check-reserve']").attr("data-kt-bud-live", "0");
		}
	}

	function openCheckReserve(opts) {
		opts = opts || {};
		var $host = ensureCheckReserveHost();
		if (!$host.length) {
			return Promise.reject(new Error("Check/Reserve fixture missing"));
		}
		var $root = $host.find("[data-testid='kt-bud-check-reserve']");
		$host.removeAttr("hidden");
		hideCrNotice($root);
		$root.data("ktBudCrOpts", opts);
		$root.attr("data-kt-bud-live", "0");

		var state = {
			demand: opts.demandName || opts.demandCode || "",
			demandTitle: opts.demandTitle || "",
			department: opts.department || "",
			requested: Number(opts.requestedAmount || 0),
			budgetLine: opts.budgetLine || opts.budgetLineCode || "",
			lines: [],
			dto: null,
		};

		function paintContext(dto) {
			var demand = (dto && dto.demand) || {};
			var line = (dto && dto.budget_line) || {};
			$root
				.find("[data-kt-bud-cr-demand-title]")
				.text(state.demandTitle || demand.demand_title || state.demand || "—");
			$root
				.find("[data-kt-bud-cr-demand-code]")
				.text(demand.demand_code || state.demand || "");
			$root
				.find("[data-kt-bud-cr-department]")
				.text(state.department || demand.department || "—");
			$root
				.find("[data-kt-bud-cr-requested]")
				.text((dto && dto.requested_display) || "—");
			$root
				.find("[data-kt-bud-cr-target-name]")
				.text(line.primary_target_name || "—");
			$root
				.find("[data-kt-bud-cr-target-code]")
				.text(line.primary_target_code || "");
		}

		function paintDecision(dto) {
			var available = dto && dto.decision_kind === "available";
			var $ok = $root.find('[data-kt-bud-cr-decision="available"]');
			var $bad = $root.find('[data-kt-bud-cr-decision="insufficient"]');
			if (available) {
				$ok.removeClass("hidden").removeAttr("hidden");
				$bad.addClass("hidden").attr("hidden", "hidden");
				$root.find("[data-kt-bud-cr-available-before]").text(dto.available_before_display || "—");
				$root
					.find("[data-kt-bud-cr-requested-row]")
					.text("- " + (dto.requested_display || "—"));
				$root.find("[data-kt-bud-cr-available-after]").text(dto.available_after_display || "—");
				$root.find("[data-kt-bud-cr-lineage]").text(dto.lineage_note || "");
				var before = Number(dto.available_before || 0);
				var req = Number(dto.requested_amount || 0);
				var usedPct = before > 0 ? Math.min(100, Math.round((req / before) * 100)) : 0;
				$root.find("[data-kt-bud-cr-bar-available] .kt-bud-cr-bar-used").css("width", usedPct + "%");
				$root
					.find("[data-kt-bud-cr-bar-available] .kt-bud-cr-bar-free")
					.css("width", Math.max(0, 100 - usedPct) + "%");
			} else {
				$bad.removeClass("hidden").removeAttr("hidden");
				$ok.addClass("hidden").attr("hidden", "hidden");
				$root.find("[data-kt-bud-cr-insuff-requested]").text(dto.requested_display || "—");
				$root.find("[data-kt-bud-cr-insuff-before]").text(dto.available_before_display || "—");
				$root.find("[data-kt-bud-cr-shortfall]").text(dto.shortfall_display || "—");
				var before2 = Number(dto.available_before || 0);
				var req2 = Number(dto.requested_amount || 0);
				var used2 = req2 > 0 ? Math.min(100, Math.round((before2 / req2) * 100)) : 0;
				$root.find("[data-kt-bud-cr-bar-insufficient] .kt-bud-cr-bar-used").css("width", used2 + "%");
				$root
					.find("[data-kt-bud-cr-bar-insufficient] .kt-bud-cr-bar-short")
					.css("width", Math.max(0, 100 - used2) + "%");
			}
		}

		function fillLines(rows) {
			state.lines = rows || [];
			var $sel = $root.find("[data-kt-bud-cr-line]");
			var cur = state.budgetLine || $sel.val() || "";
			var optsHtml = ['<option value="">' + esc(__("Select a budget line")) + "</option>"];
			state.lines.forEach(function (r) {
				var value = r.code || r.id;
				var label = (r.name || value) + (r.code ? " (" + r.code + ")" : "");
				var selected = value === cur || r.id === cur || r.code === cur;
				optsHtml.push(
					'<option value="' +
						esc(value) +
						'" data-line-id="' +
						esc(r.id || "") +
						'"' +
						(selected ? " selected" : "") +
						">" +
						esc(label) +
						"</option>"
				);
				if (selected) {
					cur = value;
					state.budgetLine = value;
				}
			});
			$sel.html(optsHtml.join(""));
			if (cur) {
				$sel.val(cur);
			}
			var selectedRow = state.lines.find(function (r) {
				return r.code === cur || r.id === cur;
			});
			$root
				.find("[data-kt-bud-cr-line-available]")
				.text((selectedRow && selectedRow.available_before_display) || "—");
		}

		function runCheck() {
			if (!state.budgetLine || !state.requested) {
				return Promise.resolve(null);
			}
			return call("check_funding", {
				budget_line: state.budgetLine,
				requested_amount: state.requested,
				demand: state.demand,
			}).then(function (dto) {
				state.dto = dto;
				paintContext(dto);
				paintDecision(dto);
				$root.find("[data-kt-bud-cr-line-available]").text(dto.available_before_display || "—");
				$root.attr("data-kt-bud-live", "1");
				$root.attr("data-kt-bud-decision", dto.decision_kind || "");
				return dto;
			});
		}

		function doReserve() {
			var mode = opts.mode || "standalone";
			if (mode === "approve_finance" && typeof opts.onConfirmApprove === "function") {
				return Promise.resolve(opts.onConfirmApprove(state.dto)).then(function (result) {
					closeCheckReserve();
					if (typeof opts.onReserved === "function") {
						opts.onReserved(result);
					}
					return result;
				});
			}
			return call("reserve_funding", {
				budget_line: state.budgetLine,
				demand_name: state.demand,
				requested_amount: state.requested,
				idempotency_key: opts.idempotencyKey || "",
			}).then(function (result) {
				showCrNotice($root, {
					title: __("Funding reserved"),
					message:
						__("Reservation") +
						" " +
						((result && result.reservation_code) || "") +
						" " +
						__("created for") +
						" " +
						((result && result.original_amount_display) || "") +
						".",
				});
				if (typeof opts.onReserved === "function") {
					opts.onReserved(result);
				}
				return result;
			});
		}

		$root.off(".ktBudCr");
		$root.on("click.ktBudCr", "[data-kt-bud-cr-close], [data-kt-bud-cr-cancel], [data-kt-bud-cr-return]", function (e) {
			e.preventDefault();
			closeCheckReserve();
			if (typeof opts.onCancel === "function") {
				opts.onCancel();
			}
		});
		$host.off("click.ktBudCrScrim").on("click.ktBudCrScrim", "[data-kt-bud-cr-scrim]", function () {
			closeCheckReserve();
			if (typeof opts.onCancel === "function") {
				opts.onCancel();
			}
		});
		$root.on("click.ktBudCr", "[data-kt-bud-cr-notice-dismiss]", function (e) {
			e.preventDefault();
			hideCrNotice($root);
		});
		$root.on("click.ktBudCr", "[data-kt-bud-cr-select-line]", function (e) {
			e.preventDefault();
			$root.find("[data-kt-bud-cr-line]").trigger("focus");
		});
		$root.on("change.ktBudCr", "[data-kt-bud-cr-line]", function () {
			state.budgetLine = $(this).val() || "";
			runCheck().catch(function (err) {
				console.warn("Check funding failed", err);
				showCrNotice($root, {
					title: __("Could not check funding"),
					message: __("Refresh and try again."),
				});
			});
		});
		$root.on("click.ktBudCr", "[data-kt-bud-cr-reserve]", function (e) {
			e.preventDefault();
			if (!state.dto || !state.dto.sufficient) {
				return;
			}
			doReserve().catch(function (err) {
				showCrNotice($root, {
					title: __("Reservation failed"),
					message: __("Could not reserve funding. Refresh and try again."),
				});
				console.warn("Reserve funding failed", err);
			});
		});

		return call("list_eligible_budget_lines", {})
			.then(function (rows) {
				fillLines(rows || []);
				if (!state.budgetLine && state.lines.length) {
					state.budgetLine = state.lines[0].code || state.lines[0].id;
					$root.find("[data-kt-bud-cr-line]").val(state.budgetLine);
				}
				return runCheck();
			})
			.catch(function (err) {
				$root.attr("data-kt-bud-live", "0");
				showCrNotice($root, {
					title: __("Could not load funding check"),
					message: __("Refresh and try again."),
				});
				throw err;
			});
	}

	kentender_budget.live.bindPortfolio = bindPortfolio;
	kentender_budget.live.bindRegister = bindRegister;
	kentender_budget.live.bindOverview = bindOverview;
	kentender_budget.live.bindLines = bindLines;
	kentender_budget.live.bindFundingActivity = bindFundingActivity;
	kentender_budget.live.bindDownstream = bindDownstream;
	kentender_budget.live.bindReview = bindReview;
	kentender_budget.live.bindAudit = bindAudit;
	kentender_budget.live.bindPerformance = bindPerformance;
	kentender_budget.live.openCheckReserve = openCheckReserve;
	kentender_budget.live.closeCheckReserve = closeCheckReserve;
	kentender_budget.live.bindRevisions = bindRevisions;
	kentender_budget.live.bindRevisionCreate = bindRevisionCreate;
	kentender_budget.live.bindRevisionReview = bindRevisionReview;
	kentender_budget.live.bindLineDrawer = bindLineDrawer;
	kentender_budget.live.openLineDrawer = openLineDrawer;
	kentender_budget.live.closeLineDrawer = closeLineDrawer;
})();
