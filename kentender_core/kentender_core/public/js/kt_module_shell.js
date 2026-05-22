// KenTender context-preserving module shell — nav, state, header (requires kt_module_registry.js)
frappe.provide("kentender_core.kt_nav");
frappe.provide("kentender_core.kt_state");
frappe.provide("kentender_core.kt_shell");

(function () {
	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function registry() {
		return (typeof kentender_core !== "undefined" && kentender_core.module_registry) || null;
	}

	function getModule(moduleId) {
		const reg = registry();
		return reg ? reg.get(moduleId) : null;
	}

	function readJson(key) {
		try {
			const raw = sessionStorage.getItem(key);
			if (!raw) return null;
			return JSON.parse(raw);
		} catch (e) {
			return null;
		}
	}

	function writeJson(key, value) {
		try {
			if (value == null) {
				sessionStorage.removeItem(key);
				return;
			}
			sessionStorage.setItem(key, JSON.stringify(value));
		} catch (e2) {
			/* ignore */
		}
	}

	kentender_core.kt_state = {
		save(moduleId, partial) {
			const mod = getModule(moduleId);
			if (!mod || !mod.stateKey) return;
			const prev = readJson(mod.stateKey) || {};
			writeJson(mod.stateKey, Object.assign({}, prev, partial || {}));
		},
		restore(moduleId) {
			const mod = getModule(moduleId);
			if (!mod || !mod.stateKey) return null;
			return readJson(mod.stateKey);
		},
		clear(moduleId) {
			const mod = getModule(moduleId);
			if (!mod || !mod.stateKey) return;
			writeJson(mod.stateKey, null);
		},
		setSelectedRecord(moduleId, recordName) {
			const mod = getModule(moduleId);
			if (!mod) return;
			if (mod.selectKey && recordName) {
				try {
					sessionStorage.setItem(mod.selectKey, recordName);
				} catch (e) {
					/* ignore */
				}
			}
			this.save(moduleId, { selectedRecord: recordName });
		},
		consumeSelectedRecord(moduleId) {
			const mod = getModule(moduleId);
			if (!mod) return null;
			let name = null;
			if (mod.selectKey) {
				try {
					name = sessionStorage.getItem(mod.selectKey);
					if (name) sessionStorage.removeItem(mod.selectKey);
				} catch (e) {
					/* ignore */
				}
			}
			if (!name) {
				const st = this.restore(moduleId);
				name = st && st.selectedRecord ? st.selectedRecord : null;
			}
			return name;
		},
	};

	kentender_core.kt_nav = {
		getModule: getModule,
		resolveFromRoute(route) {
			const reg = registry();
			return reg ? reg.resolveFromRoute(route) : null;
		},
		toWorkbench(moduleId, opts) {
			opts = opts || {};
			const mod = getModule(moduleId);
			if (!mod) return;
			if (opts.restore !== false) {
				/* selection restored by workbench on load via consumeSelectedRecord */
			}
			if (mod.workspaceSlug) {
				frappe.set_route(mod.workspaceSlug);
			} else if (mod.workspaceRoute) {
				frappe.set_route.apply(frappe, mod.workspaceRoute);
			}
		},
		ensureSidebar(moduleId) {
			const mod = getModule(moduleId);
			if (!mod) return;
			const sidebarKey = mod.sidebarWorkspaceKey || (mod.workbenchLabel || "").toLowerCase();
			try {
				if (
					sidebarKey &&
					frappe.app &&
					frappe.app.sidebar &&
					typeof frappe.app.sidebar.setup === "function"
				) {
					frappe.app.sidebar.setup(sidebarKey);
				}
			} catch (e) {
				/* ignore */
			}
		},
		toBuilder(moduleId, recordName) {
			const mod = getModule(moduleId);
			if (!mod || !mod.builderPage || !recordName) return;
			if (moduleId) {
				kentender_core.kt_state.setSelectedRecord(moduleId, recordName);
			}
			try {
				frappe.route_options = Object.assign({}, frappe.route_options || {}, {
					sidebar: mod.sidebarWorkspaceKey || mod.workbenchLabel,
				});
			} catch (e) {
				/* ignore */
			}
			frappe.set_route(mod.builderPage, recordName);
		},
		toForm(moduleId, docname, isNew) {
			const mod = getModule(moduleId);
			if (!mod || !mod.formDoctype) return;
			if (docname && !isNew) {
				kentender_core.kt_state.setSelectedRecord(moduleId, docname);
			}
			try {
				frappe.route_options = Object.assign({}, frappe.route_options || {}, {
					sidebar: mod.sidebarWorkspaceKey || mod.workbenchLabel,
				});
			} catch (e) {
				/* ignore */
			}
			if (isNew) {
				frappe.set_route("Form", mod.formDoctype, "new-" + mod.formDoctype.toLowerCase().replace(/ /g, "-"));
			} else if (docname) {
				frappe.set_route("Form", mod.formDoctype, docname);
			}
		},
		taskLabel(moduleId, taskKey) {
			const mod = getModule(moduleId);
			if (!mod || !mod.taskLabels) return "";
			return mod.taskLabels[taskKey] || "";
		},
	};

	function makeUrl(routeParts) {
		try {
			if (frappe.router && typeof frappe.router.make_url === "function") {
				return frappe.router.make_url(routeParts);
			}
		} catch (e) {
			/* ignore */
		}
		return "/desk";
	}

	kentender_core.kt_shell = {
		renderHeaderHtml(opts) {
			opts = opts || {};
			const moduleId = opts.moduleId;
			const mod = getModule(moduleId);
			if (!mod) return "";

			const recordTitle = opts.recordTitle || "";
			const taskLabel = opts.taskLabel || "";
			const metaLine = opts.metaLine || "";
			const statusHtml = opts.statusHtml || "";
			const actionsHtml = opts.actionsHtml || "";
			const backLabel = opts.backLabel || mod.backLabel || mod.workbenchLabel;

			const wsHref = escapeHtml(makeUrl(mod.workspaceRoute));
			const moduleLabel = escapeHtml(mod.workbenchLabel);
			const crumbTask = taskLabel ? " / " + escapeHtml(taskLabel) : "";

			let icon = "";
			try {
				if (frappe.utils && typeof frappe.utils.icon === "function") {
					icon = frappe.utils.icon("monitor");
				}
			} catch (e2) {
				/* ignore */
			}

			return (
				'<div class="kt-module-shell-header" data-testid="kt-module-shell-header">' +
				'<nav class="kt-module-shell-nav" aria-label="' +
				escapeHtml(__("Breadcrumb")) +
				'">' +
				'<ul class="nav d-sm-flex navbar-breadcrumbs ellipsis kt-module-shell-breadcrumbs">' +
				'<li><a href="' +
				escapeHtml(makeUrl([])) +
				'">' +
				icon +
				"</a></li>" +
				'<li class="ellipsis"><a href="' +
				wsHref +
				'" data-testid="kt-module-shell-breadcrumb-workbench">' +
				moduleLabel +
				"</a></li>" +
				(recordTitle
					? '<li class="ellipsis"><span class="text-muted">' +
						escapeHtml(recordTitle) +
						crumbTask +
						"</span></li>"
					: "") +
				"</ul></nav>" +
				'<div class="kt-module-shell-heading-row d-flex flex-wrap align-items-start justify-content-between gap-2">' +
				'<div class="kt-module-shell-heading min-w-0">' +
				(recordTitle
					? '<h2 class="h5 mb-1 kt-module-shell-title" data-testid="kt-module-shell-title">' +
						escapeHtml(recordTitle) +
						"</h2>"
					: "") +
				(metaLine || statusHtml
					? '<div class="kt-module-shell-meta text-muted small d-flex flex-wrap align-items-center gap-2">' +
						(statusHtml ? '<span data-testid="kt-module-shell-status">' + statusHtml + "</span>" : "") +
						(metaLine ? '<span data-testid="kt-module-shell-meta">' + escapeHtml(metaLine) + "</span>" : "") +
						"</div>"
					: "") +
				"</div>" +
				'<div class="kt-module-shell-actions d-flex flex-wrap align-items-center gap-2">' +
				'<button type="button" class="btn btn-default btn-sm" data-testid="back-to-workbench">' +
				escapeHtml(backLabel) +
				"</button>" +
				(actionsHtml || "") +
				"</div></div></div>"
			);
		},

		mountHeader(container, opts) {
			const $host = container && container.jquery ? container : $(container);
			if (!$host || !$host.length) return $host;
			const html = this.renderHeaderHtml(opts);
			$host.html(html);
			this.bindBack($host.find('[data-testid="back-to-workbench"]'), opts.moduleId);
			return $host;
		},

		bindBack($el, moduleId) {
			const mod = getModule(moduleId);
			if (!$el || !$el.length || !mod) return;
			$el.off("click.ktBack").on("click.ktBack", function (e) {
				if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
				e.preventDefault();
				kentender_core.kt_nav.toWorkbench(moduleId, { restore: true });
			});
		},

		bindBackSelector(root, selector, moduleId) {
			const $root = root && root.jquery ? root : $(root);
			this.bindBack($root.find(selector), moduleId);
		},
	};
})();
