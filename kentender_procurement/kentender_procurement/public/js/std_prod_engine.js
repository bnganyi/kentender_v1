(function () {
	"use strict";

	frappe.provide("kentender.std_prod");

	var API = "kentender_procurement.std_engine.api.read";
	var DEFAULT_FAMILY = "KE-PPRA-IT";
	var DEFAULT_PACKAGE = "KE-PPRA-IT-2022-04";

	function call_read(method, args) {
		return frappe.call({
			method: API + "." + method,
			type: "GET",
			args: args || {},
		});
	}

	var MODULE_ROW_ROUTES = {
		"Sections & Containers": "std-section-clauses",
		"Standard Clauses": "std-section-clauses",
		"Parameters & Rules": "std-parameter-dictionary",
		"Requirements Schema": "std-requirement-schema-manager",
		"Price Schedule Schema": "std-price-schedule-schema",
	};

	var SCHEMA_CROSS_LINKS = {
		"Parameter Dictionary": "std-parameter-dictionary",
		"Rule Dictionary": "std-rule-dictionary",
		"Form Schema Manager": "std-form-schema-manager",
		"Evaluation Schema": "std-evaluation-schema",
		"Render Blocks": "std-render-blocks",
	};

	// Frappe router registers DocType slugs before custom Pages; these collide.
	var PROCUREMENT_SIDEBAR_KEY = "Procurement";

	function preserve_procurement_sidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY);
		}
	}

	var DOCTYPE_ROUTE_CONFLICT_PAGES = [
		"std-price-schedule-schema",
		"std-evaluation-schema",
	];

	function claim_page_routes_over_doctype_conflicts() {
		if (!frappe.router || !frappe.router.routes) {
			return;
		}
		DOCTYPE_ROUTE_CONFLICT_PAGES.forEach(function (slug) {
			if (frappe.router.routes[slug]) {
				delete frappe.router.routes[slug];
			}
		});
	}

	function install_route_conflict_guard() {
		if (!frappe.router || frappe.router.__std_prod_route_guard) {
			return;
		}
		frappe.router.__std_prod_route_guard = true;
		var originalSetup = frappe.router.setup.bind(frappe.router);
		frappe.router.setup = function () {
			originalSetup();
			claim_page_routes_over_doctype_conflicts();
		};
		var originalParse = frappe.router.parse.bind(frappe.router);
		frappe.router.parse = async function (route) {
			claim_page_routes_over_doctype_conflicts();
			return originalParse(route);
		};
		claim_page_routes_over_doctype_conflicts();
	}

	function get_context() {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		var opts = root.frappe.route_options || {};
		return {
			family_code: opts.family_code || DEFAULT_FAMILY,
			package_id: opts.package_id || DEFAULT_PACKAGE,
			clause_key: opts.clause_key || "",
			parameter_key: opts.parameter_key || "",
			rule_key: opts.rule_key || "",
			form_key: opts.form_key || "",
			import_run_key: opts.import_run_key || "",
		};
	}

	function set_context(ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		root.frappe.route_options = Object.assign({}, root.frappe.route_options || {}, ctx || {});
	}

	function navigate(route, ctx) {
		var root = window.parent && window.parent.frappe ? window.parent : window;
		if (ctx) {
			set_context(ctx);
		}
		root.frappe.set_route(route);
	}

	function mark_hydrated(doc, ctx) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.setAttribute("data-std-prod-hydrated", "1");
		doc.body.setAttribute("data-std-package-id", ctx.package_id || "");
		doc.body.setAttribute("data-std-family-code", ctx.family_code || "");
	}

	function replace_mock_identities(doc, ctx) {
		var html = doc.body.innerHTML;
		var patterns = [
			/KE-PPRA-IT-2024-\d{2}(-[A-Z])?/g,
			/KE-PPRA-IT-2024-04/g,
			/KE-PPRA-IT-2024-01/g,
			/KE-PPRA-IT-2024-02-B/g,
		];
		patterns.forEach(function (pattern) {
			html = html.replace(pattern, ctx.package_id);
		});
		html = html.replace(/>\s*2024-04\s*</g, ">" + ctx.package_id + "<");
		html = html.replace(/v2024-04/g, "v" + ctx.package_id);
		doc.body.innerHTML = html;
	}

	function apply_read_only_banner(doc, ctx) {
		var banner_text =
			"DRAFT VERSION — READ ONLY INSPECTION. Editing, approval, and activation are disabled in Milestone 1.";
		doc.querySelectorAll("main *, header *").forEach(function (node) {
			if (!node.childNodes || node.childNodes.length !== 1) {
				return;
			}
			var text = (node.textContent || "").trim();
			if (text.indexOf("ACTIVE VERSION — READ ONLY") === 0) {
				node.textContent = banner_text;
			}
		});
		var lifecycle_nodes = doc.querySelectorAll("span, p, div");
		lifecycle_nodes.forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (text === "ACTIVE" && node.children.length === 0) {
				node.textContent = "DRAFT";
			}
		});
	}

	function hide_extra_rows(tbody, keep) {
		if (!tbody) {
			return null;
		}
		var rows = Array.from(tbody.querySelectorAll("tr"));
		rows.forEach(function (row, index) {
			row.style.display = index < keep ? "" : "none";
		});
		return rows[0] || null;
	}

	function detect_table_page_size(doc, fallback) {
		var select = doc.querySelector(
			".border-t select, .bg-surface-container-low select, .bg-surface-container-high select, table + div select, table ~ div select"
		);
		if (select && select.options && select.options.length) {
			var parsed = parseInt(
				select.options[select.selectedIndex].textContent ||
					select.options[0].textContent ||
					"",
				10
			);
			if (!isNaN(parsed) && parsed > 0) {
				return parsed;
			}
		}
		return fallback || 10;
	}

	function update_showing_label(node, start, end, total) {
		if (!node) {
			return false;
		}
		var spans = Array.from(node.querySelectorAll(":scope > span"));
		if (
			spans.length >= 4 &&
			(spans[0].textContent || "").trim() === "Showing" &&
			(spans[2].textContent || "").trim() === "of"
		) {
			spans[1].textContent = start + "-" + end;
			spans[3].textContent = String(total);
			return true;
		}
		var raw = (node.textContent || "").trim();
		if (raw.indexOf("Showing") !== 0) {
			return false;
		}
		var suffix_match = raw.match(/of\s+[\d,]+\s*(.*)$/i);
		var suffix = suffix_match ? suffix_match[1].trim() : "";
		if (node.querySelector("span.font-bold, span.text-primary.font-bold")) {
			var bold_class = "font-bold";
			if (node.querySelector("span.text-primary.font-bold")) {
				bold_class = "font-bold text-primary";
			}
			var html =
				"Showing <span class='" +
				bold_class +
				"'>" +
				start +
				"-" +
				end +
				"</span> of <span class='" +
				bold_class +
				"'>" +
				total +
				"</span>";
			if (suffix) {
				html += " " + suffix;
			}
			node.innerHTML = html;
			return true;
		}
		var plain = "Showing " + start + "-" + end + " of " + total;
		if (suffix) {
			plain += " " + suffix;
		}
		node.textContent = plain;
		return true;
	}

	function sync_page_of_labels(doc, total_pages) {
		doc.querySelectorAll("span, div").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (/^PAGE\s+\d+\s+OF\s+\d+/i.test(text)) {
				node.textContent = "PAGE 1 OF " + total_pages;
				return;
			}
			if (/^\d+\s+OF\s+\d+$/i.test(text)) {
				node.textContent = "1 OF " + total_pages;
			}
		});
		doc.querySelectorAll("div.flex.items-center.px-2, div.flex.items-center.gap-4").forEach(function (node) {
			var text = (node.textContent || "").trim();
			if (text.indexOf("PAGE") === 0 && text.indexOf("OF") > 0) {
				var page_spans = node.querySelectorAll("span");
				if (page_spans.length >= 2) {
					page_spans[page_spans.length - 1].textContent = String(total_pages);
				}
			}
		});
	}

	function sync_numbered_page_buttons(doc, total_pages) {
		doc.querySelectorAll("button").forEach(function (btn) {
			var label = (btn.textContent || "").trim();
			if (!/^\d+$/.test(label)) {
				return;
			}
			var page_num = parseInt(label, 10);
			if (page_num <= total_pages) {
				btn.style.display = "";
				btn.disabled = false;
				btn.removeAttribute("disabled");
				if (page_num === 1) {
					btn.classList.add("bg-primary", "text-white");
				} else {
					btn.classList.remove("bg-primary", "text-white");
				}
			} else {
				btn.style.display = "none";
			}
		});
	}

	function sync_pager_nav_buttons(doc, total_pages) {
		var nav_icons = {
			first_page: true,
			chevron_left: true,
			chevron_right: true,
			last_page: true,
		};
		doc.querySelectorAll("button").forEach(function (btn) {
			var icon = btn.querySelector(".material-symbols-outlined");
			if (!icon) {
				return;
			}
			var icon_name = (icon.textContent || "").trim();
			if (!nav_icons[icon_name]) {
				return;
			}
			var disable =
				total_pages <= 1 ||
				icon_name === "first_page" ||
				icon_name === "chevron_left";
			btn.disabled = disable;
			if (disable) {
				btn.setAttribute("disabled", "");
				btn.style.opacity = "0.3";
				btn.classList.add("disabled:opacity-30");
			} else {
				btn.removeAttribute("disabled");
				btn.style.opacity = "";
			}
		});
	}

	function is_table_footer_showing_node(node) {
		if (!node || node.querySelector("button, select, .material-symbols-outlined")) {
			return false;
		}
		var text = (node.textContent || "").trim();
		if (text.indexOf("Showing") !== 0) {
			return false;
		}
		var tag = (node.tagName || "").toUpperCase();
		return tag === "SPAN" || tag === "P" || tag === "DIV";
	}

	function hydrate_table_footer(doc, total, page_size) {
		var count = total || 0;
		var pageSize = page_size || detect_table_page_size(doc, 10);
		var start = count > 0 ? 1 : 0;
		var end = count > 0 ? Math.min(pageSize, count) : 0;
		var total_pages = count > 0 ? Math.ceil(count / pageSize) : 0;

		var showing_nodes = [];
		doc.querySelectorAll("span, p, div").forEach(function (node) {
			if (!is_table_footer_showing_node(node)) {
				return;
			}
			var dominated = showing_nodes.some(function (seen) {
				return seen !== node && seen.contains(node);
			});
			if (!dominated) {
				showing_nodes.push(node);
			}
		});
		showing_nodes.forEach(function (node) {
			var has_child_showing = showing_nodes.some(function (other) {
				return other !== node && node.contains(other);
			});
			if (!has_child_showing) {
				update_showing_label(node, start, end, count);
			}
		});

		sync_page_of_labels(doc, Math.max(total_pages, 1));
		sync_numbered_page_buttons(doc, total_pages);
		sync_pager_nav_buttons(doc, total_pages);
	}

	function disable_governance_actions(doc) {
		doc.querySelectorAll("button").forEach(function (btn) {
			var text = (btn.textContent || "").trim();
			if (
				text === "Suspend" ||
				text === "Supersede" ||
				text.indexOf("Approve") === 0 ||
				text === "Commit Import" ||
				text === "Reject Import" ||
				text === "Activate Version"
			) {
				btn.style.pointerEvents = "none";
				btn.style.opacity = "0.55";
				btn.setAttribute("aria-disabled", "true");
			}
		});
	}

	function update_headline_counters(doc, label, value) {
		doc.querySelectorAll(".text-headline-md, .font-headline-md").forEach(function (node) {
			var parent_text = node.parentElement ? node.parentElement.textContent || "" : "";
			if (parent_text.indexOf(label) >= 0) {
				node.textContent = String(value);
			}
		});
	}

	function render_identity_rows(items, row_class, data_attr) {
		return items
			.map(function (item) {
				return (
					"<tr class='" +
					row_class +
					" cursor-pointer hover:bg-surface-container-low transition-colors' " +
					data_attr +
					"='" +
					frappe.utils.escape_html(item.id) +
					"'><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(item.code || item.id) +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(item.name || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(item.validationStatus || "—") +
					"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
					frappe.utils.escape_html(item.sourceAnchorId || "—") +
					"</td></tr>"
				);
			})
			.join("");
	}

	function hydrate_parameters(doc, payload, ctx) {
		var data = payload.data || {};
		var params = data.parameters || [];
		update_headline_counters(doc, "Total Parameters", data.count || params.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && params.length) {
			tbody.innerHTML = params
				.slice(0, 60)
				.map(function (item) {
					return (
						"<tr class='bureau-table-row transition-colors std-prod-param-row cursor-pointer' data-parameter-key='" +
						frappe.utils.escape_html(item.id) +
						"'><td class='px-4 py-4 parameter-key text-primary font-medium'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='px-4 py-4'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>" +
						frappe.utils.escape_html(item.validationStatus || "—") +
						"</td><td class='px-4 py-4'>—</td><td class='px-4 py-4'>—</td><td class='px-4 py-4 font-mono text-[10px]'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || params.length);
	}

	function hydrate_parameter(doc, payload, ctx) {
		var data = payload.data || {};
		var title = doc.querySelector("h1.font-headline-lg");
		if (title) {
			title.innerHTML =
				frappe.utils.escape_html(data.name || data.code || "Parameter") +
				' <span class="text-on-surface-variant font-normal"> (' +
				frappe.utils.escape_html(data.code || data.id || "") +
				")</span>";
		}
		doc.querySelectorAll("nav span.text-primary.font-medium").forEach(function (node) {
			node.textContent = data.code || data.id || "";
		});
		doc.querySelectorAll("p.font-data-mono, .font-data-mono").forEach(function (node) {
			if ((node.textContent || "").indexOf("PKG-") === 0) {
				node.textContent = ctx.package_id;
			}
		});
	}

	function hydrate_rules(doc, payload, ctx) {
		var data = payload.data || {};
		var rules = data.rules || [];
		update_headline_counters(doc, "Total Rules", data.count || rules.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && rules.length) {
			tbody.innerHTML = render_identity_rows(rules.slice(0, 60), "std-prod-rule-row", "data-rule-key");
		}
		hydrate_table_footer(doc, data.count || rules.length);
	}

	function hydrate_rule(doc, payload, ctx) {
		var data = payload.data || {};
		var title = doc.querySelector("h1");
		if (title) {
			title.textContent = (data.name || data.code || "Rule") + " (" + (data.code || data.id || "") + ")";
		}
		var desc = doc.querySelector("section p, .font-body-md");
		if (desc && data.description) {
			desc.textContent = data.description;
		}
	}

	function hydrate_forms(doc, payload, ctx) {
		var data = payload.data || {};
		var forms = data.forms || [];
		update_headline_counters(doc, "Total Forms", data.count || forms.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && forms.length) {
			tbody.innerHTML = forms
				.slice(0, 40)
				.map(function (item) {
					return (
						"<tr class='hover:bg-surface-container-low transition-colors std-prod-form-row cursor-pointer' data-form-key='" +
						frappe.utils.escape_html(item.id) +
						"'><td class='p-4 font-data-mono text-primary'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='p-4 font-medium'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4 text-center'>—</td><td class='p-4 text-center'>—</td><td class='p-4 text-center'>—</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4'>—</td><td class='p-4 text-right'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || forms.length);
	}

	function hydrate_form(doc, payload, ctx) {
		var data = payload.data || {};
		var title = doc.querySelector("h1");
		if (title) {
			title.textContent = (data.name || data.code || "Form") + " — Field Builder";
		}
		var fields = data.formFields || [];
		var tbody = doc.querySelector("table tbody");
		if (tbody && fields.length) {
			tbody.innerHTML = fields
				.map(function (field) {
					return (
						"<tr><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(field.code || field.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(field.name || "") +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(field.fieldType || "") +
						"</td><td class='px-4 py-3'>" +
						(field.isRequired ? "Required" : "Optional") +
						"</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, fields.length);
	}

	function hydrate_requirements(doc, payload, ctx) {
		var data = payload.data || {};
		var items = data.requirements || [];
		update_headline_counters(doc, "Requirement", data.count || items.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && items.length) {
			tbody.innerHTML = render_identity_rows(items, "std-prod-req-row", "data-requirement-key");
		}
		hydrate_table_footer(doc, data.count || items.length);
	}

	function hydrate_price_schedules(doc, payload, ctx) {
		var data = payload.data || {};
		var items = data.priceSchedules || [];
		update_headline_counters(doc, "Price Schedule", data.count || items.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && items.length) {
			tbody.innerHTML = render_identity_rows(items, "std-prod-price-row", "data-price-key");
		}
		hydrate_table_footer(doc, data.count || items.length);
	}

	function hydrate_evaluation(doc, payload, ctx) {
		var data = payload.data || {};
		var schemas = data.schemas || [];
		var schema = schemas[0] || {};
		doc.querySelectorAll("h1, .font-headline-sm").forEach(function (node) {
			if ((node.textContent || "").indexOf("Evaluation Schema") >= 0 && schema.name) {
				node.textContent = schema.name;
			}
		});
		update_headline_counters(doc, "Criteria", data.count || schemas.length);
		hydrate_table_footer(doc, data.count || schemas.length);
	}

	function hydrate_render_blocks(doc, payload, ctx) {
		var data = payload.data || {};
		var blocks = data.renderBlocks || [];
		update_headline_counters(doc, "Render Block", data.count || blocks.length);
		var tbody = doc.querySelector("table tbody");
		if (tbody && blocks.length) {
			tbody.innerHTML = blocks
				.slice(0, 40)
				.map(function (item) {
					return (
						"<tr class='hover:bg-surface-container-low transition-colors'><td class='px-4 py-3 font-data-mono text-primary'>" +
						frappe.utils.escape_html(item.code || item.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(item.name || "") +
						"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(item.validationStatus || "—") +
						"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || blocks.length);
	}

	function hydrate_usage(doc, payload, ctx) {
		var data = payload.data || {};
		var bindings = data.bindings || [];
		var tbody = doc.querySelector("table tbody");
		if (!tbody) {
			hydrate_table_footer(doc, data.count || 0);
			return;
		}
		if (!bindings.length) {
			tbody.innerHTML =
				"<tr><td colspan='8' class='px-4 py-6 text-on-surface-variant'>No usage bindings for this package.</td></tr>";
			hydrate_table_footer(doc, data.count || 0);
			return;
		}
		tbody.innerHTML = bindings
			.map(function (binding) {
				return (
					"<tr><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(binding.code || binding.id) +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.name || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.tenderRef || "—") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(binding.bindingStatus || "—") +
					"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
					frappe.utils.escape_html(binding.fixtureSource || "—") +
					"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td></tr>"
				);
			})
			.join("");
		hydrate_table_footer(doc, data.count || bindings.length);
	}

	function hydrate_import_review(doc, payload, ctx) {
		var run = (payload.data && payload.data.importRun) || {};
		doc.querySelectorAll("h1").forEach(function (node) {
			if ((node.textContent || "").indexOf("Import Package Review") >= 0) {
				node.textContent = "Import Package Review — " + (run.import_run_key || ctx.package_id);
			}
		});
		var tbody = doc.querySelectorAll("table tbody")[0];
		if (tbody) {
			tbody.innerHTML =
				"<tr><td class='px-4 py-3 font-body-md text-[13px] font-semibold'>manifest.json</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
				frappe.utils.escape_html(run.manifest_hash || "—") +
				"</td><td class='px-4 py-3'>" +
				frappe.utils.escape_html(run.status || "—") +
				"</td><td class='px-4 py-3 font-data-mono text-[11px]'>" +
				frappe.utils.escape_html(run.package_sha256 || "—") +
				"</td></tr>";
		}
		hydrate_table_footer(doc, 1);
	}

	function hydrate_version_diff(doc, payload, ctx) {
		var data = payload.data || {};
		var panel = doc.querySelector("main");
		if (!panel) {
			return;
		}
		if (!data.compareAvailable) {
			var notice =
				"<div class='std-prod-diff-stub mx-container-padding my-6 p-6 border border-outline-variant rounded-lg bg-surface-container-low text-on-surface-variant'>" +
				frappe.utils.escape_html(data.message || "Version comparison unavailable.") +
				" <span class='font-data-mono text-primary'>" +
				frappe.utils.escape_html(data.reason || "SINGLE_VERSION_ONLY") +
				"</span></div>";
			var existing = doc.querySelector(".std-prod-diff-stub");
			if (existing) {
				existing.outerHTML = notice;
			} else {
				panel.insertAdjacentHTML("afterbegin", notice);
			}
		}
		var diff_count = (data.changes && data.changes.length) || (data.compareAvailable ? 1 : 0);
		hydrate_table_footer(doc, diff_count);
	}

	function hydrate_review(doc, results, ctx) {
		var version = (results.version && results.version.data) || {};
		var validation = (results.validation && results.validation.data) || {};
		var summary = validation.summary || {};
		doc.querySelectorAll("h1").forEach(function (node) {
			if ((node.textContent || "").indexOf("Review and Approval") >= 0) {
				node.textContent = "Review and Approval — " + (version.packageId || ctx.package_id);
			}
		});
		doc.querySelectorAll(".font-headline-lg, .font-headline-md").forEach(function (node) {
			var label = node.previousElementSibling ? node.previousElementSibling.textContent || "" : "";
			if (label.indexOf("Blockers") >= 0) {
				node.textContent = String(summary.blockers || 0);
			}
			if (label.indexOf("Warnings") >= 0) {
				node.textContent = String(summary.warnings || 0);
			}
		});
		disable_governance_actions(doc);
	}

	function resolve_module_route(row_label) {
		return MODULE_ROW_ROUTES[row_label] || null;
	}

	function hydrate_library_kpis(doc, kpis, health) {
		if (!kpis) {
			return;
		}
		function set_kpi_card(label, value, delta) {
			doc.querySelectorAll(".font-label-caps").forEach(function (node) {
				if ((node.textContent || "").trim() !== label) {
					return;
				}
				var card = node.parentElement;
				if (!card) {
					return;
				}
				var headline = card.querySelector(".font-headline-md");
				if (headline) {
					headline.textContent = String(value);
				}
				if (label === "STD FAMILIES") {
					var delta_node = card.querySelector(".text-status-available");
					if (delta_node) {
						if (delta > 0) {
							delta_node.textContent = "+" + delta + " New";
							delta_node.style.display = "";
						} else {
							delta_node.style.display = "none";
						}
					}
				}
			});
		}
		set_kpi_card("STD FAMILIES", kpis.stdFamilies || 0, kpis.newFamilies || 0);
		set_kpi_card("ACTIVE VERSIONS", kpis.activeVersions || 0);
		set_kpi_card("IN REVIEW", kpis.inReview || 0);
		set_kpi_card("DUE / OVERDUE", kpis.dueOverdue || 0);
		set_kpi_card("BLOCKERS", kpis.blockers || 0);

		if (!health) {
			return;
		}
		var health_rows = {
			"Unauthorized active versions": health.unauthorizedActiveVersions,
			"Pending approvals": health.pendingApprovals,
			"Due for review (30d)": health.dueForReview30d,
			"Superseded in active tenders": health.supersededInActiveTenders,
			"Blocked drafts": health.blockedDrafts,
		};
		doc.querySelectorAll(".space-y-2 > div").forEach(function (row) {
			var label_span = row.querySelector(".text-on-surface-variant");
			var value_span = row.querySelector(".font-bold");
			if (!label_span || !value_span) {
				return;
			}
			var label = (label_span.textContent || "").trim();
			if (Object.prototype.hasOwnProperty.call(health_rows, label)) {
				value_span.textContent = String(health_rows[label]);
			}
		});
	}

	function hydrate_library(doc, payload, ctx) {
		var data = payload.data || {};
		var families = data.families || [];
		var kpis = data.libraryKpis || {};
		var total_families = kpis.stdFamilies || families.length;
		hydrate_library_kpis(doc, kpis, data.libraryHealth);
		hydrate_table_footer(doc, total_families);
		var family = families[0];
		if (!family) {
			return;
		}
		var tbody = doc.querySelector("table tbody");
		var row = hide_extra_rows(tbody, 1);
		if (!row) {
			return;
		}
		var cells = row.querySelectorAll("td");
		if (cells[0]) {
			cells[0].innerHTML =
				'<div class="font-bold text-body-md text-primary">' +
				frappe.utils.escape_html(family.familyName || family.familyCode) +
				'</div><div class="text-[11px] text-on-surface-variant font-body-md">' +
				frappe.utils.escape_html(family.familyCode) +
				"</div>";
		}
		if (cells[1]) {
			cells[1].textContent = family.familyCode;
		}
		if (cells[2]) {
			cells[2].innerHTML =
				'<span class="bg-surface-container-highest text-secondary text-[10px] px-2 py-0.5 font-bold rounded">' +
				frappe.utils.escape_html(family.latestPackageId || ctx.package_id) +
				" (DRAFT)</span>";
		}
		if (cells[6]) {
			cells[6].innerHTML =
				'<span class="bg-surface-container-highest text-secondary text-[10px] px-2 py-0.5 font-bold border border-outline-variant rounded">DRAFT</span>';
		}
		var summary = payload.validationSummary || {};
		if (cells[10]) {
			var blockers = summary.blockers || 0;
			var warnings = summary.warnings || 0;
			if (blockers > 0) {
				cells[10].innerHTML =
					'<div class="flex items-center gap-1 text-error text-[10px] font-bold"><span class="material-symbols-outlined text-[14px]">error</span> ' +
					blockers +
					" BLOCKERS</div>";
			} else if (warnings > 0) {
				cells[10].innerHTML =
					'<div class="flex items-center gap-1 text-status-reserved text-[10px] font-bold"><span class="material-symbols-outlined text-[14px]">warning</span> ' +
					warnings +
					" WARNINGS</div>";
			}
		}
	}

	function hydrate_family(doc, payload, ctx) {
		var data = payload.data || {};
		var versions = data.versions || [];
		var version = versions[0];
		doc.querySelectorAll("h1, h2, .font-display-lg").forEach(function (node) {
			if ((node.textContent || "").indexOf("KE-PPRA-IT") >= 0) {
				node.textContent = data.familyName || data.familyCode || ctx.family_code;
			}
		});
		var tbody = doc.querySelector("table tbody");
		var row = hide_extra_rows(tbody, versions.length || 1);
		if (!row || !version) {
			hydrate_table_footer(doc, versions.length);
			return;
		}
		var cells = row.querySelectorAll("td");
		if (cells[0]) {
			cells[0].textContent = version.packageId;
		}
		if (cells[1]) {
			cells[1].textContent = version.versionCode || version.packageId;
		}
		if (cells[2]) {
			cells[2].innerHTML =
				'<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-surface-container-highest text-secondary border border-outline-variant/20">' +
				frappe.utils.escape_html(version.lifecycleState || "DRAFT") +
				"</span>";
		}
		if (cells[4]) {
			var blockers = (payload.validationSummary && payload.validationSummary.blockers) || 0;
			if (blockers > 0) {
				cells[4].innerHTML =
					'<div class="flex items-center gap-1.5 text-error"><span class="material-symbols-outlined text-[16px]">error</span><span class="text-body-sm">' +
					blockers +
					" Blockers</span></div>";
			}
		}
		hydrate_table_footer(doc, versions.length);
	}

	function hydrate_version(doc, version_payload, ctx) {
		var data = version_payload.data || {};
		var ctx_data = version_payload.packageContext || {};
		doc.querySelectorAll("h1.font-display-lg, nav span.text-primary.font-bold").forEach(function (node) {
			node.textContent = data.packageId || ctx.package_id;
		});
		var blockers = (version_payload.validationSummary && version_payload.validationSummary.blockers) || 0;
		var warnings = (version_payload.validationSummary && version_payload.validationSummary.warnings) || 0;
		doc.querySelectorAll(".font-label-caps").forEach(function (node) {
			if ((node.textContent || "").indexOf("Blockers /") >= 0) {
				node.textContent = blockers + " Blockers / " + warnings + " Warnings";
			}
		});
		var integrity = doc.querySelector(".bg-status-available\\/5");
		if (integrity) {
			integrity.classList.remove("bg-status-available/5", "border-status-available/20");
			integrity.classList.add("bg-surface-container-low", "border-outline-variant");
		}
	}

	function hydrate_source_doc(doc, payload, ctx) {
		var docs = (payload.data && payload.data.sourceDocuments) || [];
		var doc_row = docs[0];
		if (doc_row) {
			doc.querySelectorAll("h1").forEach(function (node) {
				node.textContent = ctx.package_id + " — Source Documents & Traceability";
			});
			doc.querySelectorAll("span.font-bold, .font-bold").forEach(function (node) {
				if ((node.textContent || "").indexOf(".pdf") >= 0) {
					node.textContent = doc_row.name;
				}
			});
			doc.querySelectorAll("code").forEach(function (node) {
				if ((node.textContent || "").indexOf("...") >= 0 && doc_row.hash) {
					node.textContent = doc_row.hash.slice(0, 8) + "..." + doc_row.hash.slice(-4);
					node.title = doc_row.hash;
				}
			});
		}
		var anchors = (payload.data && payload.data.anchors) || [];
		var anchor_panel = doc.querySelector("table tbody");
		if (anchor_panel && anchors.length) {
			anchor_panel.innerHTML = anchors
				.slice(0, 10)
				.map(function (anchor) {
					return (
						"<tr><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(anchor.code || anchor.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(anchor.name || anchor.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(String(anchor.pageFrom || "")) +
						"</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, anchors.length);
	}

	function hydrate_sections(doc, payload, ctx) {
		var sections = (payload.data && payload.data.sections) || [];
		var clauses = (payload.data && payload.data.clauses) || [];
		doc.querySelectorAll(".font-headline-sm.text-primary").forEach(function (node) {
			if ((node.textContent || "").trim() === "4") {
				node.textContent = String(sections.length);
			}
			if ((node.textContent || "").trim() === "28") {
				node.textContent = String(sections.length);
			}
			if ((node.textContent || "").trim() === "142") {
				node.textContent = String(clauses.length);
			}
		});
		var tree = doc.querySelector(".tree-container");
		if (tree) {
			tree.innerHTML = sections
				.map(function (section, index) {
					return (
						'<div class="p-2 rounded ' +
						(index === 0 ? "bg-primary/5 text-primary border-l-2 border-primary" : "hover:bg-surface-container-low text-on-surface-variant") +
						' text-body-md flex items-center gap-2 cursor-pointer std-prod-section-row" data-section-id="' +
						frappe.utils.escape_html(section.id) +
						'"><span class="material-symbols-outlined text-[16px]">description</span>' +
						frappe.utils.escape_html(section.name || section.code) +
						"</div>"
					);
				})
				.join("");
		}
		var clause_panel = doc.querySelector("table.w-full tbody");
		if (clause_panel && clauses.length) {
			clause_panel.innerHTML = clauses
				.slice(0, 15)
				.map(function (clause) {
					return (
						"<tr class='std-prod-clause-row hover:bg-surface-container-low cursor-pointer' data-clause-id='" +
						frappe.utils.escape_html(clause.id) +
						"'><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(clause.code || clause.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(clause.name || clause.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(clause.sectionId || "") +
						"</td></tr>"
					);
				})
				.join("");
			clause_panel.querySelectorAll(".std-prod-clause-row").forEach(function (row) {
				row.addEventListener("click", function () {
					kentender.std_prod.navigate("std-clause-detail", {
						package_id: ctx.package_id,
						family_code: ctx.family_code,
						clause_key: row.getAttribute("data-clause-id"),
					});
				});
			});
		}
		hydrate_table_footer(doc, clauses.length);
	}

	function hydrate_clause(doc, payload, ctx) {
		var data = payload.data || {};
		var title = doc.querySelector("h1.font-headline-lg");
		if (title) {
			title.textContent = data.name || data.code || "Clause Detail";
		}
		var badge = doc.querySelector("span.bg-primary.text-on-primary.text-\\[10px\\]");
		if (badge) {
			badge.textContent = data.code || data.id || "";
		}
		var desc = title && title.parentElement && title.parentElement.querySelector("p");
		if (desc) {
			desc.textContent = data.description || "";
		}
		var legal = doc.querySelector("section .font-body-md, section p.font-body-md");
		if (legal && data.clauseText) {
			legal.textContent = data.clauseText;
		}
	}

	function hydrate_validation(doc, payload, ctx) {
		var data = payload.data || {};
		var summary = data.summary || payload.validationSummary || {};
		doc.querySelectorAll(".font-headline-lg.text-primary").forEach(function (node) {
			var label = (node.previousElementSibling && node.previousElementSibling.textContent) || "";
			if (label.indexOf("Total Findings") >= 0) {
				node.textContent = String(data.count || 0);
			}
			if (label.indexOf("Blockers") >= 0) {
				node.textContent = String(summary.blockers || 0);
			}
			if (label.indexOf("Warnings") >= 0) {
				node.textContent = String(summary.warnings || 0);
			}
		});
		var run = data.validationRun || {};
		doc.querySelectorAll(".font-data-mono").forEach(function (node) {
			if ((node.textContent || "").indexOf("VR-") === 0 && run.runKey) {
				node.textContent = run.runKey;
			}
		});
		var tbody = doc.querySelector("table tbody");
		var findings = data.findings || [];
		if (tbody && findings.length) {
			tbody.innerHTML = findings
				.map(function (finding) {
					return (
						"<tr><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(finding.code || finding.id) +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(finding.severity || "") +
						"</td><td class='px-4 py-3'>" +
						frappe.utils.escape_html(finding.name || "") +
						"</td><td class='px-4 py-3 font-data-mono'>" +
						frappe.utils.escape_html(finding.objectId || "") +
						"</td></tr>"
					);
				})
				.join("");
		}
		hydrate_table_footer(doc, data.count || findings.length);
	}

	function hydrate_audit(doc, payload, ctx) {
		var events = (payload.data && payload.data.events) || [];
		var tbody = doc.querySelector("table tbody");
		if (!tbody) {
			return;
		}
		if (!events.length) {
			tbody.innerHTML =
				"<tr><td colspan='10' class='px-4 py-6 text-on-surface-variant'>No audit events recorded for this package.</td></tr>";
			hydrate_table_footer(doc, (payload.pagination && payload.pagination.total) || 0);
			return;
		}
		tbody.innerHTML = events
			.map(function (event) {
				return (
					"<tr><td class='px-4 py-3 font-data-mono whitespace-nowrap'>" +
					frappe.utils.escape_html(event.occurredAt || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.actor || "system") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.eventType || "") +
					"</td><td class='px-4 py-3'>" +
					frappe.utils.escape_html(event.objectType || "") +
					"</td><td class='px-4 py-3 font-data-mono text-primary'>" +
					frappe.utils.escape_html(event.objectId || "") +
					"</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3'>—</td><td class='px-4 py-3 font-data-mono'>—</td><td class='px-4 py-3 text-center'>—</td></tr>"
				);
			})
			.join("");
		hydrate_table_footer(doc, (payload.pagination && payload.pagination.total) || events.length);
	}

	var HYDRATORS = {
		library: function (doc, results, ctx) {
			hydrate_library(doc, results.families, ctx);
		},
		family: function (doc, results, ctx) {
			hydrate_family(doc, results.family, ctx);
		},
		version: function (doc, results, ctx) {
			hydrate_version(doc, results.version, ctx);
			var events = (results.audit && results.audit.data && results.audit.data.events) || [];
			var audit_tbody = doc.querySelectorAll("table tbody")[1];
			if (audit_tbody && events.length) {
				audit_tbody.innerHTML = events
					.slice(0, 3)
					.map(function (event) {
						return (
							"<tr class='text-body-sm'><td class='px-4 py-4 font-semibold text-on-surface'>" +
							frappe.utils.escape_html(event.eventType || "") +
							"</td><td class='px-4 py-4 text-on-surface-variant'>" +
							frappe.utils.escape_html(event.actor || "system") +
							"</td><td class='px-4 py-4 font-data-mono text-secondary'>" +
							frappe.utils.escape_html(event.occurredAt || "") +
							"</td><td class='px-4 py-4 font-data-mono text-[11px] text-secondary'>" +
							frappe.utils.escape_html(event.objectId || "") +
							"</td></tr>"
						);
					})
					.join("");
			}
		},
		source: function (doc, results, ctx) {
			hydrate_source_doc(doc, results.source, ctx);
		},
		sections: function (doc, results, ctx) {
			hydrate_sections(doc, results.sections, ctx);
		},
		clause: function (doc, results, ctx) {
			hydrate_clause(doc, results.clause, ctx);
		},
		validation: function (doc, results, ctx) {
			hydrate_validation(doc, results.validation, ctx);
		},
		audit: function (doc, results, ctx) {
			hydrate_audit(doc, results.audit, ctx);
		},
		parameters: function (doc, results, ctx) {
			hydrate_parameters(doc, results.parameters, ctx);
		},
		parameter: function (doc, results, ctx) {
			hydrate_parameter(doc, results.parameter, ctx);
		},
		rules: function (doc, results, ctx) {
			hydrate_rules(doc, results.rules, ctx);
		},
		rule: function (doc, results, ctx) {
			hydrate_rule(doc, results.rule, ctx);
		},
		forms: function (doc, results, ctx) {
			hydrate_forms(doc, results.forms, ctx);
		},
		form: function (doc, results, ctx) {
			hydrate_form(doc, results.form, ctx);
		},
		requirements: function (doc, results, ctx) {
			hydrate_requirements(doc, results.requirements, ctx);
		},
		priceSchedules: function (doc, results, ctx) {
			hydrate_price_schedules(doc, results.priceSchedules, ctx);
		},
		evaluation: function (doc, results, ctx) {
			hydrate_evaluation(doc, results.evaluation, ctx);
		},
		renderBlocks: function (doc, results, ctx) {
			hydrate_render_blocks(doc, results.renderBlocks, ctx);
		},
		usage: function (doc, results, ctx) {
			hydrate_usage(doc, results.usage, ctx);
		},
		importReview: function (doc, results, ctx) {
			hydrate_import_review(doc, results.importReview, ctx);
			disable_governance_actions(doc);
		},
		versionDiff: function (doc, results, ctx) {
			hydrate_version_diff(doc, results.versionDiff, ctx);
			disable_governance_actions(doc);
		},
		review: function (doc, results, ctx) {
			hydrate_review(doc, results, ctx);
		},
	};

	function fetch_screen_data(screen, ctx) {
		var package_id = ctx.package_id;
		if (screen === "library") {
			return call_read("get_std_families").then(function (r) {
				return { families: r.message };
			});
		}
		if (screen === "family") {
			return call_read("get_std_family", { family_code: ctx.family_code }).then(function (r) {
				return { family: r.message };
			});
		}
		if (screen === "version") {
			return Promise.all([
				call_read("get_std_version", { package_id: package_id }),
				call_read("get_std_version_audit_log", { package_id: package_id, limit: 3 }),
			]).then(function (responses) {
				return { version: responses[0].message, audit: responses[1].message };
			});
		}
		if (screen === "source") {
			return call_read("get_std_version_source_traceability", { package_id: package_id }).then(function (r) {
				return { source: r.message };
			});
		}
		if (screen === "sections") {
			return call_read("get_std_version_sections", { package_id: package_id }).then(function (r) {
				return { sections: r.message };
			});
		}
		if (screen === "clause") {
			var clause_key = ctx.clause_key;
			return call_read("get_std_version_sections", { package_id: package_id }).then(function (r) {
				var clauses = (r.message.data && r.message.data.clauses) || [];
				if (!clause_key && clauses.length) {
					clause_key = clauses[0].id;
				}
				if (!clause_key) {
					return { clause: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_clause", { clause_key: clause_key }).then(function (cr) {
					return { clause: cr.message };
				});
			});
		}
		if (screen === "validation") {
			return call_read("get_std_version_validation_report", { package_id: package_id }).then(function (r) {
				return { validation: r.message };
			});
		}
		if (screen === "audit") {
			return call_read("get_std_version_audit_log", { package_id: package_id }).then(function (r) {
				return { audit: r.message };
			});
		}
		if (screen === "parameters") {
			return call_read("get_std_version_parameters", { package_id: package_id }).then(function (r) {
				return { parameters: r.message };
			});
		}
		if (screen === "parameter") {
			return call_read("get_std_version_parameters", { package_id: package_id }).then(function (r) {
				var params = (r.message.data && r.message.data.parameters) || [];
				var key = ctx.parameter_key || (params[0] && params[0].id);
				if (!key) {
					return { parameter: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_parameter", { parameter_key: key }).then(function (pr) {
					return { parameter: pr.message };
				});
			});
		}
		if (screen === "rules") {
			return call_read("get_std_version_rules", { package_id: package_id }).then(function (r) {
				return { rules: r.message };
			});
		}
		if (screen === "rule") {
			return call_read("get_std_version_rules", { package_id: package_id }).then(function (r) {
				var rules = (r.message.data && r.message.data.rules) || [];
				var key = ctx.rule_key || (rules[0] && rules[0].id);
				if (!key) {
					return { rule: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_rule", { rule_key: key }).then(function (rr) {
					return { rule: rr.message };
				});
			});
		}
		if (screen === "forms") {
			return call_read("get_std_version_forms", { package_id: package_id }).then(function (r) {
				return { forms: r.message };
			});
		}
		if (screen === "form") {
			return call_read("get_std_version_forms", { package_id: package_id }).then(function (r) {
				var forms = (r.message.data && r.message.data.forms) || [];
				var key = ctx.form_key || (forms[0] && forms[0].id);
				if (!key) {
					return { form: { data: {}, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_form", { form_key: key }).then(function (fr) {
					return { form: fr.message };
				});
			});
		}
		if (screen === "requirements") {
			return call_read("get_std_version_requirements", { package_id: package_id }).then(function (r) {
				return { requirements: r.message };
			});
		}
		if (screen === "priceSchedules") {
			return call_read("get_std_version_price_schedules", { package_id: package_id }).then(function (r) {
				return { priceSchedules: r.message };
			});
		}
		if (screen === "evaluation") {
			return call_read("get_std_version_evaluation_schema", { package_id: package_id }).then(function (r) {
				return { evaluation: r.message };
			});
		}
		if (screen === "renderBlocks") {
			return call_read("get_std_version_render_blocks", { package_id: package_id }).then(function (r) {
				return { renderBlocks: r.message };
			});
		}
		if (screen === "usage") {
			return call_read("get_std_version_usage_bindings", { package_id: package_id }).then(function (r) {
				return { usage: r.message };
			});
		}
		if (screen === "importReview") {
			if (ctx.import_run_key) {
				return call_read("get_std_import_run", { import_run_key: ctx.import_run_key }).then(function (r) {
					return { importReview: r.message };
				});
			}
			return call_read("get_std_version_import_runs", { package_id: package_id }).then(function (r) {
				var runs = (r.message.data && r.message.data.importRuns) || [];
				var latest = runs[0];
				if (!latest || !latest.id) {
					return { importReview: { data: { importRun: {} }, packageContext: r.message.packageContext } };
				}
				return call_read("get_std_import_run", { import_run_key: latest.id }).then(function (ir) {
					return { importReview: ir.message };
				});
			});
		}
		if (screen === "versionDiff") {
			return call_read("get_std_version_diff", { package_id: package_id }).then(function (r) {
				return { versionDiff: r.message };
			});
		}
		if (screen === "review") {
			return Promise.all([
				call_read("get_std_version", { package_id: package_id }),
				call_read("get_std_version_validation_report", { package_id: package_id }),
				call_read("get_std_version_audit_log", { package_id: package_id, limit: 5 }),
			]).then(function (responses) {
				return {
					version: responses[0].message,
					validation: responses[1].message,
					audit: responses[2].message,
				};
			});
		}
		return Promise.resolve({});
	}

	function wire_navigation(screen, iframe, ctx) {
		function apply() {
			var doc = iframe.contentDocument;
			if (!doc) {
				return;
			}
			wire_navigation_doc(screen, doc, ctx);
		}
		iframe.addEventListener("load", apply);
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				apply();
			}
		} catch (err) {
			// Ignore until load event fires.
		}
	}

	function wire_navigation_doc(screen, doc, ctx) {
		if (!doc || !doc.body || doc.body.dataset.stdProdNavScreen === screen) {
			return;
		}
		doc.body.dataset.stdProdNavScreen = screen;
		doc.body.addEventListener(
			"click",
			function (event) {
				var target = event.target && event.target.closest ? event.target.closest("button, a, tr, span") : null;
				if (!target) {
					return;
				}
				var text = (target.textContent || "").trim();

				if (screen === "library") {
					var open_btn = target.closest("button");
					if (open_btn && text === "Open") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-family-detail", ctx);
					}
					return;
				}

				if (screen === "family") {
					var family_btn = target.closest("button");
					if (!family_btn) {
						return;
					}
					var icon = family_btn.querySelector(".material-symbols-outlined");
					if (icon) {
						var icon_name = (icon.textContent || "").trim();
						if (["open_in_new", "edit", "visibility"].indexOf(icon_name) !== -1) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-version-detail", ctx);
						}
					}
					return;
				}

				if (screen === "version") {
					if (target.tagName === "BUTTON" && (text === "View Audit Trail" || text === "Full Audit Log")) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-audit-log", ctx);
						return;
					}
					if (target.tagName === "BUTTON" && text === "View Usage") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-usage-and-tender-bindings", ctx);
						return;
					}
					if (text === "Validation") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-validation-report", ctx);
						return;
					}
					if (text === "Traceability") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-source-doc", ctx);
						return;
					}
					if (text === "Supersede") {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-version-diff-and-supersession", ctx);
						return;
					}
					var version_row = target.closest("tr");
					if (version_row) {
						var label = version_row.querySelector(".font-semibold, .font-body-md.font-semibold");
						var name = label ? (label.textContent || "").trim() : "";
						var route = resolve_module_route(name);
						if (route) {
							event.preventDefault();
							event.stopPropagation();
							navigate(route, ctx);
							return;
						}
						if (name === "Sections & Containers" || name === "Standard Clauses") {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-section-clauses", ctx);
						}
					}
					return;
				}

				if (screen === "parameters") {
					var param_row = target.closest(".std-prod-param-row");
					if (param_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-parameter-detail", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							parameter_key: param_row.getAttribute("data-parameter-key"),
						});
						return;
					}
					var open_btn = target.closest("button");
					if (open_btn && (text === "Open" || open_btn.querySelector(".material-symbols-outlined"))) {
						var row = open_btn.closest(".std-prod-param-row");
						if (row) {
							event.preventDefault();
							event.stopPropagation();
							navigate("std-parameter-detail", {
								package_id: ctx.package_id,
								family_code: ctx.family_code,
								parameter_key: row.getAttribute("data-parameter-key"),
							});
						}
						return;
					}
					if (text.indexOf("Rule Dictionary") >= 0 || target.closest('[title="View Rules"]')) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-rule-dictionary", ctx);
					}
					return;
				}

				if (screen === "rules") {
					var rule_row = target.closest(".std-prod-rule-row");
					if (rule_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-rule-detail", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							rule_key: rule_row.getAttribute("data-rule-key"),
						});
					}
					return;
				}

				if (screen === "forms") {
					var form_row = target.closest(".std-prod-form-row");
					if (form_row) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-form-detail-field-builder", {
							package_id: ctx.package_id,
							family_code: ctx.family_code,
							form_key: form_row.getAttribute("data-form-key"),
						});
					}
					return;
				}

				var cross_route = SCHEMA_CROSS_LINKS[text];
				if (cross_route && ["parameters", "rules", "forms", "requirements", "priceSchedules", "evaluation", "renderBlocks", "versionDiff", "importReview", "usage", "review"].indexOf(screen) !== -1) {
					event.preventDefault();
					event.stopPropagation();
					navigate(cross_route, ctx);
					return;
				}

				if (screen === "sections") {
					var sections_btn = target.closest("button");
					if (!sections_btn) {
						return;
					}
					if (text.indexOf("SOURCE TRACEABILITY") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-source-doc", ctx);
					} else if (text.indexOf("VIEW VALIDATION") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-validation-report", ctx);
					} else if (text.indexOf("AUDIT TRAIL") >= 0) {
						event.preventDefault();
						event.stopPropagation();
						navigate("std-audit-log", ctx);
					}
				}
			},
			true,
		);
	}

	function hydrate_iframe(screen, iframe, ctx) {
		var doc = iframe.contentDocument;
		if (!doc) {
			return;
		}
		fetch_screen_data(screen, ctx)
			.then(function (results) {
				replace_mock_identities(doc, ctx);
				apply_read_only_banner(doc, ctx);
				disable_governance_actions(doc);
				var hydrator = HYDRATORS[screen];
				if (hydrator) {
					hydrator(doc, results, ctx);
				}
				wire_navigation_doc(screen, doc, ctx);
				mark_hydrated(doc, ctx);
			})
			.catch(function (err) {
				frappe.msgprint({
					title: __("STD read API failed"),
					indicator: "red",
					message: (err && err.message) || __("Unable to load STD data."),
				});
			});
	}

	function mount_page(wrapper, config) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: config.title,
			single_column: true,
		});
		preserve_procurement_sidebar();
		var shell_class = config.shell_class;
		document.body.classList.add(shell_class);

		var root = page.main.get(0);
		if (!root) {
			return;
		}
		var testid = config.testid;
		root.className = config.root_class;
		root.setAttribute("data-testid", testid + "-root");
		root.innerHTML =
			'<section class="' +
			shell_class +
			'" data-testid="' +
			testid +
			'-shell">' +
			'<iframe class="' +
			config.iframe_class +
			'" data-testid="' +
			testid +
			'-iframe" src="' +
			config.asset +
			'" title="' +
			frappe.utils.escape_html(config.title) +
			'"></iframe></section>';

		var iframe = root.querySelector("iframe");
		var ctx = get_context();
		wire_navigation(config.screen, iframe, ctx);
		function run_hydration() {
			hydrate_iframe(config.screen, iframe, ctx);
		}
		iframe.addEventListener("load", run_hydration);
		try {
			if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
				run_hydration();
			}
		} catch (err) {
			// Cross-origin guard — load event will hydrate when ready.
		}

		frappe.pages[config.page].on_page_show = function () {
			document.body.classList.add(shell_class);
			preserve_procurement_sidebar();
		};
		frappe.pages[config.page].on_page_hide = function () {
			document.body.classList.remove(shell_class);
		};
	}

	kentender.std_prod.DEFAULT_FAMILY_CODE = DEFAULT_FAMILY;
	kentender.std_prod.DEFAULT_PACKAGE_ID = DEFAULT_PACKAGE;
	kentender.std_prod.get_context = get_context;
	kentender.std_prod.set_context = set_context;
	kentender.std_prod.navigate = navigate;
	kentender.std_prod.mount_page = mount_page;
	kentender.std_prod.hydrate_iframe = hydrate_iframe;
	kentender.std_prod.claim_page_routes_over_doctype_conflicts =
		claim_page_routes_over_doctype_conflicts;
	kentender.std_prod.install_route_conflict_guard = install_route_conflict_guard;
	kentender.std_prod.preserve_procurement_sidebar = preserve_procurement_sidebar;
	kentender.std_prod.hydrate_table_footer = hydrate_table_footer;

	install_route_conflict_guard();
	$(document).on("app_ready", claim_page_routes_over_doctype_conflicts);
})();
