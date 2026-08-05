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
					'" data-kt-bud-route="budget-overview/' +
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

	function paintChromeActions($root, caps) {
		caps = caps || {};
		$root.attr("data-kt-bud-primary-action", caps.primary_action || "");
		var $primary = $root.find('[data-testid="kt-bud-overview-primary"]');
		if ($primary.length) {
			$primary.text(caps.primary_label || __("Open"));
		}
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

				$root.find("[data-kt-bud-budget-code]").text(ov.code || budgetCode || "");
				$root.find("[data-kt-bud-budget-title]").text(ov.title || ov.name || "—");
				paintStatusPill($root, ov.status, ov.status_label);
				paintChromeActions($root, ov.capabilities);

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
				setOv($root, "strategy_pvc", strategy.pvc_summary || "—");
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

	function pvcCardHtml(tr, readOnly) {
		var level = (tr.requirement_level || "").toLowerCase().indexOf("recommend") >= 0
			? "Recommended"
			: "Required";
		var badgeClass =
			level === "Recommended"
				? "bg-secondary-fixed text-on-secondary-fixed-variant border-secondary-fixed-dim"
				: "bg-primary-fixed/20 text-primary border-primary/20";
		var amount =
			tr.treatment === "Dedicated allocation" && tr.dedicated_amount
				? '<div class="text-right"><div class="font-label-caps text-[10px] text-on-surface-variant uppercase">Dedicated Amount</div>' +
					'<div class="font-data-mono text-primary font-bold">' +
					esc(tr.dedicated_display || formatMoneyInput(tr.dedicated_amount)) +
					"</div></div>"
				: "";
		var rationale =
			tr.rationale &&
			(tr.treatment === "No direct allocation required" || tr.treatment === "Not applicable")
				? '<div class="font-body-md text-on-surface-variant text-[13px] italic flex gap-1 items-start bg-surface-container-low p-2 rounded">' +
					'<span class="material-symbols-outlined text-[16px] mt-0.5">info</span><span>Rationale: ' +
					esc(tr.rationale) +
					"</span></div>"
				: "";
		var treatmentControl = readOnly
			? '<span class="text-on-surface">' + esc(tr.treatment || "—") + "</span>"
			: '<div class="relative flex-1"><select class="w-full bg-surface border border-outline-variant rounded-lg py-1.5 px-2 text-sm appearance-none" data-kt-bud-pvc-treatment="' +
				esc(tr.code) +
				'">' +
				["Dedicated allocation", "Embedded in line", "No direct allocation required", "Not applicable"]
					.map(function (opt) {
						return (
							'<option value="' +
							esc(opt) +
							'"' +
							(opt === tr.treatment ? " selected" : "") +
							">" +
							esc(opt) +
							"</option>"
						);
					})
					.join("") +
				'</select><span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant text-[18px]">expand_more</span></div>';
		return (
			'<div class="bg-surface border border-outline-variant rounded-lg p-4 flex flex-col gap-3" data-kt-bud-pvc-card data-pvc-code="' +
			esc(tr.code) +
			'">' +
			'<div class="flex justify-between items-start"><div class="space-y-1"><div class="flex items-center gap-2">' +
			'<span class="font-body-md text-on-surface font-semibold">' +
			esc(tr.name) +
			'</span><span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold tracking-wide uppercase border ' +
			badgeClass +
			'">' +
			esc(level) +
			"</span></div>" +
			'<div class="font-data-mono text-[11px] text-on-surface-variant">' +
			esc(tr.code) +
			"</div></div>" +
			amount +
			"</div>" +
			'<div class="flex items-center gap-2 text-body-md"><span class="text-on-surface-variant font-label-caps text-[11px] uppercase">Treatment:</span>' +
			treatmentControl +
			"</div>" +
			rationale +
			"</div>"
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

		var $pvc = $drawer.find("[data-kt-bud-line-pvc-list]");
		$pvc.empty();
		(lineDto.value_treatments || []).forEach(function (tr) {
			$pvc.append(pvcCardHtml(tr, readOnly));
		});

		$drawer.find('[data-kt-bud-line-field="approved_compact"]').text(
			lineDto.approved_compact_display || formatMoneyInput(lineDto.approved).replace(/,000,000$/, "M")
		);
		$drawer
			.find('[data-kt-bud-line-field="dedicated_compact"]')
			.text(lineDto.dedicated_total_display || "KES 0");
		$drawer
			.find('[data-kt-bud-line-field="not_dedicated_compact"]')
			.text(lineDto.not_dedicated_display || "KES 0");

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
		var treatments = [];
		$drawer.find("[data-kt-bud-pvc-card]").each(function () {
			var $c = $(this);
			var code = $c.attr("data-pvc-code");
			var prev = (dto.value_treatments || []).find(function (t) {
				return t.code === code;
			}) || {};
			var treatment =
				$c.find("[data-kt-bud-pvc-treatment]").val() || prev.treatment || "Embedded in line";
			treatments.push({
				id: prev.id || "",
				code: code,
				name: prev.name || $c.find(".font-semibold").first().text().trim(),
				requirement_level: prev.requirement_level || "Required",
				treatment: treatment,
				dedicated_amount: prev.dedicated_amount || 0,
				rationale: prev.rationale || "",
				reviewer_accepted: prev.reviewer_accepted || 0,
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
			value_treatments: treatments,
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
			var payload = collectDrawerPayload($root, budgetCode);
			call("save_budget_line", { payload: payload })
				.then(function (res) {
					if (!res || !res.ok) {
						var errs = (res && res.errors) || {};
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
			frappe.set_route("budget-revisions", budgetCode);
		});
		$root.on("change.ktBudLineDrawer", '[data-kt-bud-line-input="primary_target"]', function () {
			$root
				.find('[data-kt-bud-line-field="primary_target_code"]')
				.text($(this).val() || "—");
		});
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
				$root.find("[data-kt-bud-budget-code]").text(budget.code || budgetCode || "");
				$root.find("[data-kt-bud-budget-title]").text(budget.title || budget.name || "—");
				paintStatusPill($root, budget.status, budget.status_label);
				paintChromeActions($root, dto.capabilities);

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
						frappe.set_route("budget-revisions", budgetCode);
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
				value_treatments: [],
				dedicated_total: 0,
				not_dedicated: 0,
				approved_compact_display: "KES 0",
				dedicated_total_display: "KES 0",
				not_dedicated_display: "KES 0",
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
				$root.find("[data-kt-bud-budget-code]").text(budget.code || budgetCode || "");
				$root.find("[data-kt-bud-budget-title]").text(budget.title || budget.name || "—");
				paintStatusPill($root, budget.status, budget.status_label);
				paintChromeActions($root, dto.capabilities);

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

	kentender_budget.live.bindPortfolio = bindPortfolio;
	kentender_budget.live.bindRegister = bindRegister;
	kentender_budget.live.bindOverview = bindOverview;
	kentender_budget.live.bindLines = bindLines;
	kentender_budget.live.bindFundingActivity = bindFundingActivity;
	kentender_budget.live.bindLineDrawer = bindLineDrawer;
	kentender_budget.live.openLineDrawer = openLineDrawer;
	kentender_budget.live.closeLineDrawer = closeLineDrawer;
})();
