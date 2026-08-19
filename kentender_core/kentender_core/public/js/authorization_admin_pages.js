(function () {
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const call = (method, args) => frappe.call({ method, args }).then((r) => r.message);
  const routeArg = (index, fallback = "") => decodeURIComponent((frappe.get_route()[index] || fallback));
  const shell = (wrapper, html) => { $(wrapper).find(".layout-main-section").html(`<div class="kt-auth-surface">${html}</div>`); };
  const status = (value, denied = false) => `<span class="kt-auth-status${denied ? " denied" : ""}">${esc(value)}</span>`;

  function mount(name, renderer) {
    frappe.pages[name] = frappe.pages[name] || {};
    frappe.pages[name].on_page_load = (wrapper) => {
      frappe.ui.make_app_page({ parent: wrapper, title: __("Access management"), single_column: true });
      renderer(wrapper).catch((e) => frappe.msgprint({ title: e.exc_type || __("Access unavailable"), message: e.message || String(e), indicator: "red" }));
    };
  }

  mount("user-operational-acc", async (wrapper) => {
    const target = routeArg(2, frappe.session.user);
    const d = await call("kentender_core.authorization_api.user_access", { target_user: target });
    const rows = d.assignments.map((a) => `<tr><td><strong>${esc(a.role)}</strong></td><td>${esc(a.procuring_entity)}</td><td>${esc(a.organisation_scope)}</td><td>${esc(a.resource_scope)}</td><td>${esc(a.effective_period)}</td><td>${status(a.status)}</td><td><a href="/app/operational-scope-assignment/${encodeURIComponent(a.name)}">${__("View assignment")} →</a></td></tr>`).join("") || `<tr><td colspan="7">${__("No operational assignments")}</td></tr>`;
    shell(wrapper, `<div class="kt-auth-breadcrumb">${__("Access management / Users / ")}${esc(d.full_name)}</div><div class="kt-auth-header"><div><h1>${esc(d.full_name)}</h1><p>${__("Operational roles and the Procuring Entity, Organisation Unit or governed resource scopes in which they apply.")}</p></div><button class="kt-auth-btn primary" data-action="add">+ ${__("Add operational assignment")}</button></div><div class="kt-auth-grid"><div class="kt-auth-card"><span class="kt-auth-label">${__("Account status")}</span>${status(d.account_status)}</div><div class="kt-auth-card"><span class="kt-auth-label">${__("Active assignments")}</span><span class="kt-auth-value">${d.active_assignments}</span></div><div class="kt-auth-card"><span class="kt-auth-label">${__("Current open tasks")}</span><span class="kt-auth-value">${d.open_tasks}</span></div><div class="kt-auth-card"><span class="kt-auth-label">${__("Separation-of-duties issues")}</span><span class="kt-auth-value">${d.sod_issues}</span></div></div><section class="kt-auth-panel"><h2>${__("Operational assignments")}</h2><div class="kt-auth-table-wrap"><table class="kt-auth-table"><thead><tr><th>${__("Role")}</th><th>${__("Procuring Entity")}</th><th>${__("Organisation scope")}</th><th>${__("Resource scope")}</th><th>${__("Effective period")}</th><th>${__("Status")}</th><th>${__("Action")}</th></tr></thead><tbody>${rows}</tbody></table></div></section><div class="kt-auth-note">ⓘ ${__("Assignments grant scope and capabilities. Workflow tasks are assigned separately through routing rules.")}</div>`);
    $(wrapper).on("click", "[data-action=add]", () => frappe.prompt([{fieldname:"capability_profile_id",label:__("Capability Profile"),fieldtype:"Link",options:"Capability Profile",reqd:1},{fieldname:"procuring_entity_id",label:__("Procuring Entity"),fieldtype:"Link",options:"Procuring Entity",reqd:1},{fieldname:"effective_from",label:__("Effective From"),fieldtype:"Datetime",reqd:1}], (values) => call("kentender_core.authorization_api.add_assignment", {values:JSON.stringify({...values,user_id:target})}).then(() => frappe.set_route(frappe.get_route())), __("Add operational assignment")));
  });

  mount("workflow-routing-rul", async (wrapper) => {
    const name = routeArg(2);
    const d = await call("kentender_core.authorization_api.routing_rule", { name });
    const values = [["Module",d.module_name],["Task type",d.task_type],["Procuring Entity",d.procuring_entity],["Organisation scope",d.organisation_unit_id || "All assigned entity units"],["Resource scope",d.resource_scope_type ? `${d.resource_scope_type}: ${d.resource_scope_id}` : "All admitted resources"],["Required capability",d.required_capability],["Assignment method",d.assignee_strategy],["Assigned user or queue",d.assignee],["Effective from",d.effective_from],["Effective to",d.effective_to || "No end date"],["Priority",d.priority],["Fallback",d.fallback_rule_id || "None"]].map(([k,v])=>`<div><dt class="kt-auth-label">${__(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
    shell(wrapper, `<div class="kt-auth-breadcrumb">${__("Workflow routing / ")}${esc(d.task_type)} / ${esc(d.routing_rule_id)}</div><div class="kt-auth-header"><div><h1>${esc(d.task_type)} — ${esc(d.procuring_entity)}</h1>${status(d.status)}</div><div><button class="kt-auth-btn">${__("View routing history")}</button> <button class="kt-auth-btn primary" data-action="revise">${__("Create revised rule")}</button></div></div><section class="kt-auth-panel"><h2>${esc(d.routing_rule_id)} · ${__("Version")} ${d.version}</h2><dl class="kt-auth-dl">${values}</dl></section><div class="kt-auth-note"><strong>${d.eligible ? "✓ Eligible" : "Not eligible"}</strong><br>${esc(d.eligibility_copy)}</div>`);
    $(wrapper).on("click", "[data-action=revise]", () => call("kentender_core.authorization_api.revise_routing_rule", {name}).then((next)=>frappe.set_route("workflow-routing-rul",next.name)));
  });

  mount("access-diagnostic", async (wrapper) => {
    const task = routeArg(2), tested = routeArg(3, frappe.session.user), capability = routeArg(4, "support.record.view");
    const taskMeta = task ? await frappe.db.get_value("Workflow Task", task, ["subject_type","subject_id","procuring_entity_id","financial_year_id","organisation_unit_id"]) : null;
    const m = taskMeta && taskMeta.message;
    const d = await call("kentender_core.authorization_api.diagnostic", {tested_user:tested,capability,resource_type:m?.subject_type||"Procuring Entity",resource_id:m?.subject_id||"diagnostic",procuring_entity_id:m?.procuring_entity_id||routeArg(5),financial_year_id:m?.financial_year_id||"",organisation_unit_id:m?.organisation_unit_id||"",task_id:task});
    const rows = d.checks.map((r)=>`<tr class="${r.passed?"":"failed"}"><td><strong>${esc(r.check)}</strong></td><td>${esc(r.required)}</td><td>${esc(r.actual)}</td><td>${status(r.passed?"Passed":"Failed",!r.passed)}</td></tr>`).join("");
    shell(wrapper, `<div class="kt-auth-header"><div><h1>${__("Access diagnostic")}</h1><p>${__("Read-only evaluation of the current authorization and task assignment.")}</p></div>${status(d.status,!d.allowed)}</div><section class="kt-auth-panel"><h2>${__("Evaluation details")}</h2><div class="kt-auth-table-wrap"><table class="kt-auth-table"><thead><tr><th>${__("Check")}</th><th>${__("Required")}</th><th>${__("Actual")}</th><th>${__("Result")}</th></tr></thead><tbody>${rows}</tbody></table></div></section><div class="kt-auth-banner"><strong>${d.allowed?__("Authorization allowed"):__("Authorization denied")}</strong>${esc(d.conclusion)}</div><div class="kt-auth-links"><a href="/app/user-operational-acc/${encodeURIComponent(tested)}">${__("View user assignments")}</a>${d.routing_rule_id?`<a href="/app/workflow-routing-rul/${encodeURIComponent(d.routing_rule_id)}">${__("View routing rule")} ${esc(d.routing_rule_id)}</a>`:""}<a href="/app/workflow-task/${encodeURIComponent(task)}">${__("View task history")}</a></div>`);
  });
})();
