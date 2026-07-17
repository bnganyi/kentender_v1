/* @deprecated — iframe hydrator for Screen 02. Replaced by native
 * screens/configuration_home.js. Kept temporarily for reference only; not
 * loaded in hooks.py app_include_js.
 */
(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.overview");

	var API = "kentender_procurement.it_tender_wizard.api.instance_api";

	var STATUS_BADGE_CLASS = {
		Complete: "bg-emerald-available/10 text-emerald-available",
		"In progress": "bg-secondary/10 text-secondary",
		"Needs attention": "bg-error-container/30 text-error",
		"Not started": "bg-surface-variant text-on-surface-variant",
		"Available later": "bg-surface-variant text-on-surface-variant",
	};

	function call_api(method, args) {
		return frappe.call({
			method: API + "." + method,
			args: args || {},
		});
	}

	function navigate(route, ctx) {
		if (kentender.it_wizard && typeof kentender.it_wizard.navigate === "function") {
			kentender.it_wizard.navigate(route, ctx);
		}
	}

	function escape_html(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function install_operating_styles(doc) {
		if (!doc || !doc.head || doc.getElementById("it-wizard-overview-v2-styles")) {
			return;
		}
		var style = doc.createElement("style");
		style.id = "it-wizard-overview-v2-styles";
		style.textContent =
			"[data-itw-home-drawer-overlay].hidden," +
			"[data-itw-home-drawer-overlay][hidden] { display: none !important; }" +
			"[data-itw-home-drawer].translate-x-full { transform: translateX(100%); }" +
			"[data-itw-home-drawer]:not(.translate-x-full) { transform: translateX(0); }" +
			"[data-itw-home-stub-action] { opacity: 0.55; pointer-events: none; }";
		doc.head.appendChild(style);
	}

	function prepare(doc) {
		if (!doc || !doc.body) {
			return;
		}
		doc.body.classList.add("it-wizard-overview-v2");
		install_operating_styles(doc);

		doc.querySelectorAll("main > section").forEach(function (section) {
			if (section.querySelector("h1") && (section.textContent || "").indexOf("Tender Configuration Home") >= 0) {
				section.setAttribute("data-itw-home-header", "1");
			}
			if ((section.textContent || "").indexOf("TENDER REF") >= 0) {
				section.setAttribute("data-itw-home-context", "1");
			}
			if (section.classList.contains("bg-secondary-fixed")) {
				section.setAttribute("data-itw-next-action", "1");
			}
		});

		doc.querySelectorAll("h3").forEach(function (heading) {
			if ((heading.textContent || "").indexOf("Configuration Steps") >= 0 && heading.nextElementSibling) {
				heading.nextElementSibling.setAttribute("data-itw-step-grid", "1");
			}
		});

		var overlay = doc.querySelector("main + div.fixed.inset-0, body > div.fixed.inset-0.bg-on-background");
		if (!overlay) {
			doc.querySelectorAll("div.fixed.inset-0").forEach(function (node) {
				if ((node.className || "").indexOf("bg-on-background") >= 0) {
					overlay = node;
				}
			});
		}
		if (overlay) {
			overlay.setAttribute("data-itw-home-drawer-overlay", "1");
			overlay.classList.add("hidden");
		}

		var drawer = doc.querySelector("aside.fixed.top-0.right-0");
		if (drawer) {
			drawer.setAttribute("data-itw-home-drawer", "1");
			drawer.classList.add("translate-x-full");
			drawer.classList.remove("translate-x-0");
		}

		disable_stub_actions(doc);
	}

	function disable_stub_actions(doc) {
		var header = doc.querySelector("[data-itw-home-header]");
		if (header) {
			header.querySelectorAll("button").forEach(function (btn) {
				var text = (btn.textContent || "").trim();
				if (text.indexOf("Finalize") >= 0 || text.indexOf("Discard") >= 0) {
					btn.disabled = true;
					btn.setAttribute("data-itw-home-stub-action", "1");
				}
			});
		}
	}

	function fetch(ctx) {
		return call_api("get_configuration_summary_api", {
			configuration_id: ctx.configuration_id,
		}).then(function (result) {
			return {
				overview: (result && result.message) || {},
			};
		});
	}

	function set_context_value(section, label, value) {
		if (!section) {
			return;
		}
		section.querySelectorAll(".flex.flex-col").forEach(function (cell) {
			var labelNode = cell.querySelector(".text-label-caps");
			if (!labelNode) {
				return;
			}
			if ((labelNode.textContent || "").trim().toUpperCase() !== label.toUpperCase()) {
				return;
			}
			var valueNode = labelNode.nextElementSibling;
			if (!valueNode) {
				valueNode = cell.querySelector(".text-data-mono, .inline-flex, span.text-body-md");
			}
			if (valueNode && valueNode !== labelNode) {
				valueNode.textContent = value || "—";
			}
		});
	}

	function hydrate_context_strip(doc, data) {
		var section = doc.querySelector("[data-itw-home-context]");
		if (!section || !data) {
			return;
		}
		set_context_value(section, "TENDER REF", data.tender_ref || data.configuration_id);
		set_context_value(section, "TENDER TITLE", data.tender_title || data.title);
		set_context_value(section, "PLANNING PKG REF", data.planning_package_ref);
		set_context_value(section, "PROCURING ENTITY", data.procuring_entity_name);
		set_context_value(section, "PROCUREMENT METHOD", data.procurement_method_label);
		set_context_value(section, "WIZARD STATE", data.wizard_state_label || data.state_label);
		var issuesText = data.issues_summary || "No issues";
		if (issuesText === "No issues") {
			issuesText = __("No issues");
		}
		set_context_value(section, "ISSUES", issuesText);
	}

	function hydrate_next_action(doc, data) {
		var panel = doc.querySelector("[data-itw-next-action]");
		var next = (data && data.next_action) || {};
		if (!panel) {
			return;
		}
		var heading = panel.querySelector("h2");
		if (heading) {
			heading.textContent = __("Next step: {0}", [next.label || ""]);
		}
		var reason = panel.querySelector("p.text-body-md");
		if (reason) {
			reason.textContent = __("Reason: {0}", [next.reason || ""]);
		}
		var button = panel.querySelector("button");
		if (button) {
			button.textContent = next.button_label || __("Continue");
			button.setAttribute("data-itw-next-action-route", next.route || "");
		}
	}

	function format_issue_line(step) {
		var blockers = step.blocker_count || 0;
		var warnings = step.warning_count || 0;
		if (!blockers && !warnings) {
			return "";
		}
		var parts = [];
		if (blockers) {
			parts.push(blockers + " " + (blockers === 1 ? __("Blocker") : __("Blockers")));
		}
		if (warnings) {
			parts.push(warnings + " " + (warnings === 1 ? __("Warning") : __("Warnings")));
		}
		return parts.join(" / ");
	}

	function build_step_card_html(step) {
		var status = step.status_label || "Not started";
		var badgeClass = STATUS_BADGE_CLASS[status] || STATUS_BADGE_CLASS["Not started"];
		var isCurrent = step.is_current ? "1" : "0";
		var isAvailableLater = status === "Available later";
		var isInProgress = status === "In progress";
		var cardClass =
			"bg-surface-container-lowest border rounded-xl p-card-padding flex flex-col h-full shadow-sm ";
		if (isInProgress) {
			cardClass += "border-2 border-secondary ";
		} else if (isAvailableLater) {
			cardClass += "bg-surface-container-low border-border-subtle opacity-75 ";
		} else {
			cardClass += "border-border-subtle hover:shadow-md transition-shadow ";
		}
		var stepNum = String(step.step_number || 0).padStart(2, "0");
		var statusHtml =
			'<span class="inline-flex items-center gap-1 px-2 py-1 rounded ' +
			badgeClass +
			' text-[10px] font-bold uppercase">' +
			(isAvailableLater
				? '<span class="material-symbols-outlined text-[14px]">lock</span>'
				: "") +
			escape_html(status === "Available later" ? "Available Later" : status) +
			"</span>";
		var issueLine = format_issue_line(step);
		var issueHtml = issueLine
			? '<div class="flex items-center gap-1 text-error text-label-caps font-label-caps mb-4">' +
				'<span class="material-symbols-outlined text-[14px]">error</span>' +
				escape_html(issueLine) +
				"</div>"
			: '<div class="mb-6"></div>';
		if (!issueLine && !isAvailableLater) {
			issueHtml = '<div class="mb-6 flex-grow"></div>';
		} else if (!issueLine && isAvailableLater) {
			issueHtml = '<div class="mb-6 flex-grow"></div>';
		}
		var prereqHtml = "";
		if (isAvailableLater && step.availability_reason) {
			prereqHtml =
				'<div class="pt-4 border-t border-outline-variant">' +
				'<span class="text-label-caps font-label-caps text-on-surface-variant opacity-60">' +
				escape_html(step.availability_reason.toUpperCase()) +
				"</span></div>";
		}
		var actionClass = isInProgress
			? "self-start px-4 py-2 bg-primary-container text-on-primary rounded font-label-caps text-label-caps hover:bg-primary-container/90 transition-colors"
			: isAvailableLater
				? "self-start px-4 py-2 border border-outline text-on-surface-variant rounded font-label-caps text-label-caps opacity-60"
				: "self-start px-4 py-2 border border-outline text-on-surface rounded font-label-caps text-label-caps hover:bg-surface-container-low transition-colors";
		var actionBtn = isAvailableLater
			? ""
			: '<button type="button" class="' +
				actionClass +
				'" data-itw-step-action="1">' +
				escape_html(step.action_label || "Start") +
				"</button>";
		return (
			'<div class="' +
			cardClass +
			'" data-itw-step-card="1" data-itw-step-code="' +
			escape_html(step.step_code || "") +
			'" data-itw-step-route="' +
			escape_html(step.route || "") +
			'" data-itw-step-current="' +
			isCurrent +
			'">' +
			'<div class="flex flex-col gap-1 mb-4">' +
			'<span class="text-label-caps font-label-caps ' +
			(isInProgress ? "text-secondary" : "text-on-surface-variant") +
			'">STEP ' +
			stepNum +
			"</span>" +
			'<div class="flex justify-between items-start gap-2">' +
			'<h4 class="text-body-lg font-body-lg font-semibold ' +
			(isAvailableLater ? "text-on-surface-variant" : "text-on-surface") +
			'">' +
			escape_html(step.step_label || "") +
			"</h4>" +
			statusHtml +
			"</div></div>" +
			'<p class="text-body-md font-body-md text-on-surface-variant mb-2 flex-grow">' +
			escape_html(step.card_description || "") +
			"</p>" +
			(issueLine
				? '<div class="flex items-center gap-1 text-error text-label-caps font-label-caps mb-4">' +
					'<span class="material-symbols-outlined text-[14px]">error</span>' +
					escape_html(issueLine) +
					"</div>"
				: "") +
			actionBtn +
			prereqHtml +
			"</div>"
		);
	}

	function hydrate_step_grid(doc, steps) {
		var grid = doc.querySelector("[data-itw-step-grid]");
		if (!grid) {
			return;
		}
		if (!steps || !steps.length) {
			grid.innerHTML =
				'<div class="col-span-full text-center text-on-surface-variant py-8">' +
				__("No configuration steps found.") +
				"</div>";
			return;
		}
		grid.innerHTML = steps.map(build_step_card_html).join("");
	}

	function hydrate_drawer(doc, step) {
		var drawer = doc.querySelector("[data-itw-home-drawer]");
		if (!drawer || !step) {
			return;
		}
		var stepNum = String(step.step_number || 0).padStart(2, "0");
		var stepLabel = drawer.querySelector("[data-itw-home-drawer] .text-label-caps");
		var title = drawer.querySelector("[data-itw-home-drawer] h2");
		drawer.querySelectorAll(".text-label-caps").forEach(function (node) {
			if ((node.textContent || "").indexOf("STEP") >= 0) {
				node.textContent = "STEP " + stepNum;
			}
		});
		if (title) {
			title.textContent = step.step_label || "";
		}
		drawer.querySelectorAll(".flex.flex-col.gap-1").forEach(function (block) {
			var label = block.querySelector(".text-label-caps");
			if (!label) {
				return;
			}
			var text = (label.textContent || "").trim().toUpperCase();
			var valueNode = block.querySelector(".inline-flex, span.inline-flex, span.font-bold, span.text-error");
			if (text === "STATUS" && valueNode) {
				valueNode.textContent = step.status_label || "";
			}
			if (text === "ISSUES" && valueNode) {
				var issueText = format_issue_line(step);
				valueNode.innerHTML = issueText
					? '<span class="material-symbols-outlined text-[14px]">error</span> ' + escape_html(issueText)
					: __("None");
			}
		});
		var purpose = drawer.querySelector('[data-itw-home-drawer] p.text-body-md, aside p.text-body-md');
		drawer.querySelectorAll("p.text-body-md").forEach(function (node) {
			var parent = node.closest("div.flex.flex-col.gap-2");
			if (parent && (parent.textContent || "").indexOf("Purpose") >= 0) {
				node.textContent = step.drawer_purpose || "";
			}
		});
		var listHost = drawer.querySelector("ul.list-disc");
		if (listHost && step.configure_there) {
			listHost.innerHTML = step.configure_there
				.map(function (item) {
					return "<li>" + escape_html(item) + "</li>";
				})
				.join("");
		}
		var metadata = drawer.querySelector(".flex.flex-col.gap-6.pt-4");
		if (metadata) {
			metadata.style.display = step.last_updated_at ? "" : "none";
		}
		var progressBlock = drawer.querySelector(".flex.flex-col.gap-1");
		drawer.querySelectorAll(".flex.flex-col.gap-1").forEach(function (block) {
			if ((block.textContent || "").indexOf("Progress") >= 0) {
				block.style.display = "none";
			}
		});
		var primaryBtn = drawer.querySelector(".p-6.border-t button");
		if (primaryBtn) {
			primaryBtn.textContent = step.action_label || __("Continue");
			primaryBtn.setAttribute("data-itw-drawer-route", step.route || "");
		}
	}

	function open_drawer(doc, step) {
		hydrate_drawer(doc, step);
		var overlay = doc.querySelector("[data-itw-home-drawer-overlay]");
		var drawer = doc.querySelector("[data-itw-home-drawer]");
		if (overlay) {
			overlay.classList.remove("hidden");
		}
		if (drawer) {
			drawer.classList.remove("translate-x-full");
		}
	}

	function close_drawer(doc) {
		var overlay = doc.querySelector("[data-itw-home-drawer-overlay]");
		var drawer = doc.querySelector("[data-itw-home-drawer]");
		if (overlay) {
			overlay.classList.add("hidden");
		}
		if (drawer) {
			drawer.classList.add("translate-x-full");
		}
	}

	function wire_interactions(doc, ctx, steps) {
		if (!doc || !doc.body || doc.body.getAttribute("data-itw-home-wired") === "1") {
			return;
		}
		doc.body.setAttribute("data-itw-home-wired", "1");
		var stepByCode = {};
		(steps || []).forEach(function (step) {
			stepByCode[step.step_code] = step;
		});

		doc.addEventListener(
			"click",
			function (event) {
				var closeBtn = event.target.closest("[data-itw-home-drawer] button");
				if (closeBtn && (closeBtn.textContent || "").indexOf("close") >= 0) {
					event.preventDefault();
					close_drawer(doc);
					return;
				}
				if (event.target.closest("[data-itw-home-drawer-overlay]")) {
					close_drawer(doc);
					return;
				}
				var nextBtn = event.target.closest("[data-itw-next-action] button");
				if (nextBtn) {
					event.preventDefault();
					var route = nextBtn.getAttribute("data-itw-next-action-route");
					if (route) {
						navigate(route, { configuration_id: ctx.configuration_id });
					}
					return;
				}
				var drawerBtn = event.target.closest("[data-itw-home-drawer] .p-6.border-t button");
				if (drawerBtn) {
					event.preventDefault();
					var drawerRoute = drawerBtn.getAttribute("data-itw-drawer-route");
					if (drawerRoute) {
						navigate(drawerRoute, { configuration_id: ctx.configuration_id });
					}
					return;
				}
				var actionBtn = event.target.closest("[data-itw-step-action]");
				var card = event.target.closest("[data-itw-step-card]");
				if (actionBtn && card) {
					event.preventDefault();
					var route = card.getAttribute("data-itw-step-route");
					if (route) {
						navigate(route, { configuration_id: ctx.configuration_id });
					}
					return;
				}
				if (card && !actionBtn) {
					var code = card.getAttribute("data-itw-step-code");
					if (code && stepByCode[code]) {
						event.preventDefault();
						open_drawer(doc, stepByCode[code]);
					}
				}
			},
			true,
		);

		var drawer = doc.querySelector("[data-itw-home-drawer]");
		if (drawer) {
			drawer.querySelectorAll("button").forEach(function (btn) {
				if ((btn.textContent || "").indexOf("close") >= 0) {
					btn.addEventListener("click", function (event) {
						event.preventDefault();
						close_drawer(doc);
					});
				}
			});
		}
	}

	function hydrate(doc, payload, ctx) {
		var data = (payload.overview && payload.overview.data) || {};
		var steps = data.steps || [];
		prepare(doc);
		hydrate_context_strip(doc, data);
		hydrate_next_action(doc, data);
		hydrate_step_grid(doc, steps);
		disable_stub_actions(doc);
		close_drawer(doc);
		wire_interactions(doc, ctx, steps);
	}

	kentender.it_wizard.overview.prepare = prepare;
	kentender.it_wizard.overview.fetch = fetch;
	kentender.it_wizard.overview.hydrate = hydrate;
})();
