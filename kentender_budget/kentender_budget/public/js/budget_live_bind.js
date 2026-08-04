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
				frappe.msgprint({
					title: __("Not permitted"),
					message: __("Only a Budget Officer can register an approved budget."),
					indicator: "red",
				});
				throw err;
			});
	}

	kentender_budget.live.bindPortfolio = bindPortfolio;
	kentender_budget.live.bindRegister = bindRegister;
})();
