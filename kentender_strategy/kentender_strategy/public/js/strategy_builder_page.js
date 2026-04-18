// Strategy Builder — two-pane hierarchy editor for one Strategic Plan.
frappe.provide("kentender_strategy.strategy_builder");

(function () {
	function planFromRoute() {
		const r = frappe.get_route() || [];
		return r.length > 1 ? r[1] : null;
	}

	function nestNodes(flat) {
		const byParent = {};
		flat.forEach((n) => {
			const p = n.parent || "";
			if (!byParent[p]) {
				byParent[p] = [];
			}
			byParent[p].push(n);
		});
		function walk(parentId) {
			return (byParent[parentId] || []).map((n) => ({
				...n,
				children: walk(n.name),
			}));
		}
		return walk("");
	}

	function typeIconClass(nodeType) {
		if (nodeType === "Program") {
			return "kt-sb-type--program";
		}
		if (nodeType === "Objective") {
			return "kt-sb-type--objective";
		}
		return "kt-sb-type--target";
	}

	function typeIconLetter(nodeType) {
		if (nodeType === "Program") {
			return "P";
		}
		if (nodeType === "Objective") {
			return "O";
		}
		return "T";
	}

	function readinessMarkup(counts) {
		const p = counts.programs || 0;
		const o = counts.objectives || 0;
		const t = counts.targets || 0;
		const countsLine = `${__("Programs")}: ${p} · ${__("Objectives")}: ${o} · ${__("Targets")}: ${t}`;
		let statusClass = "kt-sb-readiness--ok";
		let statusIcon = "✅";
		let statusLabel = __("Ready");
		if (p === 0 || o === 0) {
			statusClass = "kt-sb-readiness--bad";
			statusIcon = "❌";
			statusLabel = __("Incomplete");
		} else if (t === 0) {
			statusClass = "kt-sb-readiness--warn";
			statusIcon = "⚠️";
			statusLabel = __("Missing targets");
		}
		return `<div class="kt-sb-readiness card py-2 px-3 mb-0 ${statusClass}" data-testid="strategy-readiness">
			<div class="d-flex flex-wrap align-items-center justify-content-between gap-2">
				<span class="small text-muted mb-0">${frappe.utils.escape_html(countsLine)}</span>
				<span class="font-weight-bold mb-0">${frappe.utils.escape_html(statusIcon + " " + statusLabel)}</span>
			</div>
		</div>`;
	}

	class StrategyBuilder {
		constructor($wrapper) {
			this.$wrapper = $wrapper;
			this.planName = null;
			this.flatNodes = [];
			this.nodeByName = {};
			this.selectedName = null;
			this.creatingMode = null;
			/** @type {Set<string>} Node names whose child rows are visible */
			this.expanded = new Set();
			this._didInitExpanded = false;
			/** @type {string|null} After create, focus this node once tree reloads */
			this._focusAfterLoad = null;
			this.lastCounts = { programs: 0, objectives: 0, targets: 0 };
		}

		init() {
			this.planName = planFromRoute();
			if (!this.planName) {
				this.$wrapper.html(
					`<div class="alert alert-warning">${__("Open this page from a Strategic Plan (missing plan in the URL).")}</div>`,
				);
				return;
			}
			this.renderShell();
			const me = this;
			$(document).off("page-change.kt_sb_plan").on("page-change.kt_sb_plan", () => {
				const r = frappe.get_route() || [];
				if (r[0] !== "strategy-builder") {
					return;
				}
				const next = r[1] || null;
				if (next && next !== me.planName) {
					me.planName = next;
					me.selectedName = null;
					me._focusAfterLoad = null;
					me._didInitExpanded = false;
					me.expanded = new Set();
					me.loadTree();
				}
			});
			this.loadTree();
		}

		renderShell() {
			this.$wrapper.html(`
				<div class="kt-strategy-builder" data-testid="strategy-builder-page">
					<div class="page-head-content pb-2">
						<div class="kt-sb-readiness-host small mb-2"></div>
					</div>
					<div class="row kt-sb-row">
						<div class="col-md-4 border-end">
							<div class="kt-sb-tree-pane" data-testid="strategy-tree-pane">
								<div class="btn-group mb-3 flex-wrap" role="group">
									<button type="button" class="btn btn-xs btn-primary" data-testid="add-program-button">${__("Add Program")}</button>
									<button type="button" class="btn btn-xs btn-default" data-testid="add-objective-button" disabled>${__("Add Objective")}</button>
									<button type="button" class="btn btn-xs btn-default" data-testid="add-target-button" disabled>${__("Add Target")}</button>
								</div>
								<div class="kt-sb-tree-scroll">
									<div class="kt-sb-tree-list"></div>
								</div>
							</div>
						</div>
						<div class="col-md-8">
							<div class="kt-sb-editor-pane" data-testid="strategy-editor-pane">
								<div class="kt-sb-empty-editor text-muted" data-testid="empty-editor-hint">${__(
									"Select a node from the left, or create a new Program to begin.",
								)}</div>
								<div class="kt-sb-editor-form" style="display:none;">
									<div class="mb-2"><span class="badge" data-testid="selected-node-type"></span></div>
									<div class="form-group">
										<label>${__("Title")}</label>
										<input type="text" class="form-control" data-testid="node-title-input" />
									</div>
									<div class="form-group">
										<label>${__("Description")}</label>
										<textarea class="form-control" rows="3" data-testid="node-description-input"></textarea>
									</div>
									<div class="kt-sb-target-fields" style="display:none;">
										<div class="form-group">
											<label>${__("Measurement Type")}</label>
											<select class="form-control" data-testid="measurement-type-input">
												<option value="Numeric">${__("Numeric")}</option>
												<option value="Percentage">${__("Percentage")}</option>
												<option value="Currency">${__("Currency")}</option>
												<option value="Milestone">${__("Milestone")}</option>
												<option value="Boolean">${__("Boolean")}</option>
											</select>
										</div>
										<div class="form-group">
											<label>${__("Target Period Type")}</label>
											<select class="form-control" data-testid="target-period-type-input">
												<option value="Annual">${__("Annual")}</option>
												<option value="End of Plan">${__("End of Plan")}</option>
												<option value="Quarterly">${__("Quarterly")}</option>
												<option value="Milestone Date">${__("Milestone Date")}</option>
											</select>
										</div>
										<div class="form-group">
											<label>${__("Period Value")}</label>
											<input type="text" class="form-control" data-testid="target-period-value-input" />
										</div>
										<div class="kt-sb-target-numeric-fields">
											<div class="form-group">
												<label>${__("Target Year")}</label>
												<input type="number" class="form-control" data-testid="target-year-input" />
											</div>
											<div class="form-group">
												<label>${__("Target Value (numeric)")}</label>
												<input type="number" step="any" class="form-control" data-testid="target-value-input" />
											</div>
											<div class="form-group">
												<label>${__("Target Unit")}</label>
												<input type="text" class="form-control" data-testid="target-unit-input" />
											</div>
										</div>
										<div class="kt-sb-target-text-fields" style="display:none;">
											<div class="form-group">
												<label>${__("Target Value (text)")}</label>
												<textarea class="form-control" rows="2" data-testid="target-value-text-input"></textarea>
											</div>
										</div>
										<div class="form-group kt-sb-baseline-fields">
											<label>${__("Baseline (numeric, optional)")}</label>
											<input type="number" step="any" class="form-control" data-testid="baseline-value-numeric-input" />
										</div>
										<div class="form-group">
											<label>${__("Baseline (text, optional)")}</label>
											<textarea class="form-control" rows="2" data-testid="baseline-value-text-input"></textarea>
										</div>
										<div class="form-group">
											<label>${__("Baseline Year")}</label>
											<input type="number" class="form-control" data-testid="baseline-year-input" />
										</div>
									</div>
									<button type="button" class="btn btn-primary" data-testid="save-node-button">${__("Save")}</button>
									<button type="button" class="btn btn-default ml-2" data-testid="delete-node-button">${__("Delete")}</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			`);

			this.$treeList = this.$wrapper.find(".kt-sb-tree-list");
			this.$readinessHost = this.$wrapper.find(".kt-sb-readiness-host");
			this.$emptyHint = this.$wrapper.find("[data-testid='empty-editor-hint']");
			this.$editorForm = this.$wrapper.find(".kt-sb-editor-form");
			this.$targetFields = this.$wrapper.find(".kt-sb-target-fields");

			const me = this;
			this.$wrapper.find("[data-testid='add-program-button']").on("click", () => me.promptCreate("Program"));
			this.$wrapper.find("[data-testid='add-objective-button']").on("click", () => me.promptCreate("Objective"));
			this.$wrapper.find("[data-testid='add-target-button']").on("click", () => me.promptCreate("Target"));
			this.$wrapper.find("[data-testid='save-node-button']").on("click", () => me.saveSelected());
			this.$wrapper.find("[data-testid='delete-node-button']").on("click", () => me.deleteSelected());
			this.$wrapper.on("change", "[data-testid='measurement-type-input']", function () {
				me.toggleTargetEditorMode($(this).val());
			});
		}

		toggleTargetEditorMode(mt) {
			const numeric = ["Numeric", "Percentage", "Currency"].includes(mt);
			this.$wrapper.find(".kt-sb-target-numeric-fields").toggle(numeric);
			this.$wrapper.find(".kt-sb-target-text-fields").toggle(!numeric);
			this.$wrapper.find(".kt-sb-baseline-fields").toggle(numeric);
		}

		defaultExpandAllParents() {
			if (this._didInitExpanded || !this.flatNodes.length) {
				return;
			}
			this.flatNodes.forEach((n) => {
				const hasKids = this.flatNodes.some((c) => c.parent === n.name);
				if (hasKids) {
					this.expanded.add(n.name);
				}
			});
			this._didInitExpanded = true;
		}

		expandPathTo(name) {
			let id = name;
			while (id) {
				const n = this.nodeByName[id];
				if (!n) {
					break;
				}
				const p = n.parent;
				if (p) {
					this.expanded.add(p);
				}
				id = p || "";
			}
		}

		toggleExpanded(name, e) {
			if (e) {
				e.preventDefault();
				e.stopPropagation();
			}
			if (this.expanded.has(name)) {
				this.expanded.delete(name);
			} else {
				this.expanded.add(name);
			}
			this.renderTree();
		}

		isExpanded(name) {
			return this.expanded.has(name);
		}

		scrollNodeIntoView(name) {
			const el = this.$treeList
				.find(".kt-sb-tree-row")
				.filter(function () {
					return $(this).attr("data-node") === name;
				})
				.get(0);
			if (el && el.scrollIntoView) {
				el.scrollIntoView({ block: "nearest", behavior: "smooth" });
			}
		}

		loadTree() {
			const me = this;
			return frappe
				.call({
					method: "kentender_strategy.api.strategy_builder.get_strategy_tree",
					args: { plan_name: me.planName },
				})
				.then((r) => {
					me.flatNodes = (r.message && r.message.nodes) || [];
					me.nodeByName = {};
					me.flatNodes.forEach((n) => {
						me.nodeByName[n.name] = n;
					});
					if (!me.flatNodes.length) {
						me._didInitExpanded = false;
						me.expanded = new Set();
					}
					const counts = (r.message && r.message.counts) || {};
					me.lastCounts = {
						programs: counts.programs || 0,
						objectives: counts.objectives || 0,
						targets: counts.targets || 0,
					};
					me.$readinessHost.html(readinessMarkup(me.lastCounts));
					me.defaultExpandAllParents();
					const pendingFocus = me._focusAfterLoad;
					if (pendingFocus && me.nodeByName[pendingFocus]) {
						me._focusAfterLoad = null;
						me.expandPathTo(pendingFocus);
						me.selectedName = pendingFocus;
						me.creatingMode = null;
					} else {
						if (pendingFocus) {
							me._focusAfterLoad = null;
						}
						me.expandPathTo(me.selectedName || "");
					}
					me.renderTree();
					me.updateAddButtons();

					if (me.selectedName && me.nodeByName[me.selectedName]) {
						me.fillEditor(me.nodeByName[me.selectedName]);
						if (pendingFocus && me.nodeByName[pendingFocus]) {
							setTimeout(() => me.scrollNodeIntoView(pendingFocus), 150);
						}
					} else if (me.selectedName) {
						me.selectedName = null;
						me.showEmptyEditor();
					} else {
						me.showEmptyEditor();
					}
				});
		}

		labelForNode(n) {
			const kind = n.node_type;
			const t = n.title || "";
			if (kind === "Target" && n.target_period_value) {
				return `${kind} — ${n.target_period_value}: ${t}`;
			}
			return `${kind} — ${t}`;
		}

		renderTreeNode(n, depth) {
			const me = this;
			const kids = n.children || [];
			const hasKids = kids.length > 0;
			const expanded = !hasKids || me.isExpanded(n.name);
			const selected = me.selectedName === n.name;
			const label = me.labelForNode(n);
			const esc = frappe.utils.escape_html;
			const chevron = hasKids
				? `<button type="button" class="kt-sb-chevron btn btn-xs btn-link p-0" tabindex="0" aria-expanded="${expanded}" data-chevron-for="${esc(
						n.name,
					)}" title="${expanded ? __("Collapse") : __("Expand")}">${expanded ? "▼" : "▶"}</button>`
				: `<span class="kt-sb-chevron-placeholder"></span>`;

			const rowClass = `kt-sb-tree-row d-flex align-items-start ${selected ? "kt-sb-tree-row--selected" : ""}`;
			let html = `<li class="kt-sb-tree-node" data-depth="${depth}" data-testid="tree-node-${esc(n.name)}">
				<div class="${rowClass}" data-node="${esc(n.name)}">
					${chevron}
					<span class="kt-sb-type-icon ${typeIconClass(n.node_type)}" title="${esc(n.node_type)}">${typeIconLetter(n.node_type)}</span>
					<button type="button" class="btn btn-link btn-sm text-left flex-grow-1 kt-sb-node-btn p-1" data-node="${esc(n.name)}">${esc(label)}</button>
				</div>`;

			if (hasKids && expanded) {
				html += `<ul class="kt-sb-tree-children list-unstyled">`;
				kids.forEach((ch) => {
					html += me.renderTreeNode(ch, depth + 1);
				});
				html += `</ul>`;
			} else if (hasKids && !expanded) {
				html += `<ul class="kt-sb-tree-children list-unstyled kt-sb-tree-children--collapsed" aria-hidden="true"></ul>`;
			}
			html += `</li>`;
			return html;
		}

		renderTree() {
			const me = this;
			const tree = nestNodes(me.flatNodes);
			if (!me.flatNodes.length) {
				this.$treeList.html(
					`<div class="kt-sb-empty-tree alert alert-secondary" data-testid="empty-tree-message" role="region">
						<p class="font-weight-bold mb-2">${__("Build your strategy tree")}</p>
						<ol class="mb-0 pl-3 small text-left">
							<li>${__("Step 1: Add Program")}</li>
							<li>${__("Step 2: Add Objectives under each Program")}</li>
							<li>${__("Step 3: Add Targets under each Objective")}</li>
						</ol>
					</div>`,
				);
				return;
			}
			let html = `<ul class="kt-sb-tree list-unstyled mb-0">`;
			tree.forEach((n) => {
				html += me.renderTreeNode(n, 0);
			});
			html += `</ul>`;
			me.$treeList.html(html);

			me.$treeList.find(".kt-sb-node-btn").on("click", function () {
				const name = $(this).attr("data-node");
				me.selectNode(name);
			});
			me.$treeList.find(".kt-sb-chevron").on("click", function (e) {
				const name = $(this).attr("data-chevron-for");
				me.toggleExpanded(name, e);
			});
			me.$treeList.find(".kt-sb-tree-row").on("click", function (e) {
				if ($(e.target).closest(".kt-sb-chevron, .kt-sb-node-btn").length) {
					return;
				}
				const name = $(this).attr("data-node");
				if (name) {
					me.selectNode(name);
				}
			});
		}

		selectNode(name) {
			this.selectedName = name;
			this.creatingMode = null;
			this.renderTree();
			const n = this.nodeByName[name];
			if (n) {
				this.fillEditor(n);
			}
			this.updateAddButtons();
		}

		selectedNodeType() {
			if (!this.selectedName) {
				return null;
			}
			const n = this.nodeByName[this.selectedName];
			return n ? n.node_type : null;
		}

		updateAddButtons() {
			const $obj = this.$wrapper.find("[data-testid='add-objective-button']");
			const $tar = this.$wrapper.find("[data-testid='add-target-button']");
			const t = this.selectedNodeType();
			$obj.prop("disabled", t !== "Program");
			$tar.prop("disabled", t !== "Objective");
		}

		showEmptyEditor() {
			this.$emptyHint.show();
			this.$editorForm.hide();
		}

		fillEditor(n) {
			this.$emptyHint.hide();
			this.$editorForm.show();
			this.$wrapper.find("[data-testid='selected-node-type']").text(n.node_type);
			this.$wrapper.find("[data-testid='node-title-input']").val(n.title || "");
			this.$wrapper.find("[data-testid='node-description-input']").val(n.description || "");
			if (n.node_type === "Target") {
				this.$targetFields.show();
				const mt = n.measurement_type || "Numeric";
				this.$wrapper.find("[data-testid='measurement-type-input']").val(mt);
				this.$wrapper.find("[data-testid='target-period-type-input']").val(n.target_period_type || "Annual");
				this.$wrapper.find("[data-testid='target-period-value-input']").val(n.target_period_value || "");
				const py =
					n.target_period_type === "Annual" && n.target_period_value
						? parseInt(n.target_period_value, 10)
						: "";
				this.$wrapper.find("[data-testid='target-year-input']").val(py || "");
				this.$wrapper.find("[data-testid='target-value-input']").val(
					n.target_value_numeric !== null && n.target_value_numeric !== undefined
						? n.target_value_numeric
						: "",
				);
				this.$wrapper.find("[data-testid='target-unit-input']").val(n.target_unit || "");
				this.$wrapper.find("[data-testid='target-value-text-input']").val(n.target_value_text || "");
				this.$wrapper.find("[data-testid='baseline-value-numeric-input']").val(
					n.baseline_value_numeric !== null && n.baseline_value_numeric !== undefined
						? n.baseline_value_numeric
						: "",
				);
				this.$wrapper.find("[data-testid='baseline-value-text-input']").val(n.baseline_value_text || "");
				this.$wrapper.find("[data-testid='baseline-year-input']").val(n.baseline_year || "");
				this.toggleTargetEditorMode(mt);
			} else {
				this.$targetFields.hide();
			}
		}

		promptCreate(nodeType) {
			const me = this;
			let parent = null;
			if (nodeType === "Objective") {
				if (me.selectedNodeType() !== "Program") {
					return;
				}
				parent = me.selectedName;
			} else if (nodeType === "Target") {
				if (me.selectedNodeType() !== "Objective") {
					return;
				}
				parent = me.selectedName;
			}

			const fields = [
				{ fieldname: "node_title", fieldtype: "Data", label: __("Title"), reqd: 1 },
				{ fieldname: "node_description", fieldtype: "Small Text", label: __("Description") },
			];
			if (nodeType === "Target") {
				fields.push(
					{
						fieldname: "measurement_type",
						fieldtype: "Select",
						label: __("Measurement Type"),
						options: ["Numeric", "Percentage", "Currency", "Milestone", "Boolean"].join("\n"),
						default: "Numeric",
					},
					{
						fieldname: "target_period_type",
						fieldtype: "Select",
						label: __("Target Period Type"),
						options: ["Annual", "End of Plan", "Quarterly", "Milestone Date"].join("\n"),
						default: "Annual",
					},
					{
						fieldname: "target_period_value",
						fieldtype: "Data",
						label: __("Period Value"),
						description: __("For Annual, enter the year (e.g. 2026)."),
					},
					{ fieldname: "target_value", fieldtype: "Float", label: __("Target Value (numeric)") },
					{ fieldname: "target_unit", fieldtype: "Data", label: __("Target Unit") },
					{ fieldname: "target_value_text", fieldtype: "Small Text", label: __("Target Value (text)") },
				);
			}

			const d = new frappe.ui.Dialog({
				title:
					nodeType === "Program"
						? __("New Program")
						: nodeType === "Objective"
							? __("New Objective")
							: __("New Target"),
				fields,
				primary_action_label: __("Create"),
				primary_action(values) {
					const data = {
						node_title: values.node_title,
						node_description: values.node_description || "",
					};
					if (nodeType === "Target") {
						data.measurement_type = values.measurement_type || "Numeric";
						data.target_period_type = values.target_period_type || "Annual";
						data.target_period_value =
							values.target_period_value || String(new Date().getFullYear());
						data.target_value_numeric = values.target_value;
						data.target_value_text = values.target_value_text || "";
						data.target_unit = values.target_unit || "";
						if (["Milestone", "Boolean"].includes(data.measurement_type)) {
							data.target_value_numeric = null;
						} else {
							data.target_value_text = "";
						}
					}
					frappe.call({
						method: "kentender_strategy.api.strategy_builder.create_strategy_node",
						args: {
							plan_name: me.planName,
							parent_name: parent,
							node_type: nodeType,
							initial_data: data,
						},
						callback(r) {
							d.hide();
							const newName = r.message && r.message.name;
							if (newName) {
								me._focusAfterLoad = newName;
							}
							me.loadTree();
							frappe.show_alert({
								message:
									nodeType === "Program"
										? __("Program saved")
										: nodeType === "Objective"
											? __("Objective saved")
											: __("Target saved"),
								indicator: "green",
							});
						},
					});
				},
			});
			d.show();
		}

		saveSelected() {
			const me = this;
			if (!me.selectedName) {
				return;
			}
			const n = me.nodeByName[me.selectedName];
			if (!n) {
				return;
			}
			const data = {
				node_title: me.$wrapper.find("[data-testid='node-title-input']").val(),
				node_description: me.$wrapper.find("[data-testid='node-description-input']").val(),
			};
			if (n.node_type === "Target") {
				const ptype = me.$wrapper.find("[data-testid='target-period-type-input']").val();
				let periodVal = me.$wrapper.find("[data-testid='target-period-value-input']").val();
				if (ptype === "Annual") {
					const y = me.$wrapper.find("[data-testid='target-year-input']").val();
					if (y) {
						periodVal = String(y);
					}
				}
				data.measurement_type = me.$wrapper.find("[data-testid='measurement-type-input']").val();
				data.target_period_type = ptype;
				data.target_period_value = periodVal || "";
				data.target_value_numeric = me.$wrapper.find("[data-testid='target-value-input']").val();
				data.target_value_text = me.$wrapper.find("[data-testid='target-value-text-input']").val();
				data.target_unit = me.$wrapper.find("[data-testid='target-unit-input']").val();
				data.baseline_value_numeric = me.$wrapper.find("[data-testid='baseline-value-numeric-input']").val();
				data.baseline_value_text = me.$wrapper.find("[data-testid='baseline-value-text-input']").val();
				data.baseline_year = me.$wrapper.find("[data-testid='baseline-year-input']").val();
			}
			frappe.call({
				method: "kentender_strategy.api.strategy_builder.update_strategy_node",
				args: { node_name: me.selectedName, data },
				callback() {
					me.loadTree();
					const label =
						n.node_type === "Program"
							? __("Program saved")
							: n.node_type === "Objective"
								? __("Objective saved")
								: __("Target saved");
					frappe.show_alert({ message: label, indicator: "green" });
				},
			});
		}

		deleteSelected() {
			const me = this;
			if (!me.selectedName) {
				return;
			}
			frappe.confirm(__("Delete this node?"), () => {
				frappe.call({
					method: "kentender_strategy.api.strategy_builder.delete_strategy_node",
					args: { node_name: me.selectedName },
					callback() {
						me.selectedName = null;
						me.loadTree();
						frappe.show_alert({ message: __("Deleted"), indicator: "green" });
					},
				});
			});
		}
	}

	function bootStrategyBuilderPage() {
		const el = frappe.pages["strategy-builder"];
		if (!el) {
			return;
		}
		const $w = $(el);
		if ($w.data("kt_sb")) {
			return;
		}
		const sb = new StrategyBuilder($w);
		$w.data("kt_sb", sb);
		sb.init();
		$w.on("show", function () {
			const s = $w.data("kt_sb");
			if (s && s.planName) {
				s.loadTree();
			}
		});
	}

	bootStrategyBuilderPage();
})();
