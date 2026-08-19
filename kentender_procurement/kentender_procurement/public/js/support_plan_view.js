(function () {
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  frappe.pages["support-plan-view"] = frappe.pages["support-plan-view"] || {};
  frappe.pages["support-plan-view"].on_page_load = async (wrapper) => {
    frappe.ui.make_app_page({ parent: wrapper, title: __("Support read-only Plan"), single_column: true });
    const plan = decodeURIComponent(frappe.get_route()[2] || "");
    try {
      const response = await frappe.call({method:"kentender_procurement.procurement_planning.api.get_support_plan",args:{plan,purpose:"Access diagnostic support"}});
      const d = response.message;
      const summary = [["Approved value",d.approved_value],["Draft value",d.draft_value],["Finance confirmed",d.finance_confirmed],["Validation",d.validation]].map(([k,v])=>`<div class="kt-auth-card"><span class="kt-auth-label">${__(k)}</span><span class="kt-auth-value">${esc(v)}</span></div>`).join("");
      $(wrapper).find(".layout-main-section").html(`<main class="kt-auth-surface"><div class="kt-auth-banner"><strong>${esc(d.access_label)}</strong>${esc(d.access_copy)}</div><div class="kt-auth-header"><div><div class="kt-auth-breadcrumb">${esc(d.plan)}</div><h1>${esc(d.title)}</h1><p>${esc(d.lifecycle)} · ${esc(d.approved_version)} · ${esc(d.draft_version)}</p></div></div><div class="kt-auth-grid">${summary}</div><section class="kt-auth-panel"><h2>${__("Plan identifiers")}</h2><dl class="kt-auth-dl"><div><dt class="kt-auth-label">${__("Procuring Entity")}</dt><dd>${esc(d.procuring_entity)}</dd></div><div><dt class="kt-auth-label">${__("Financial year")}</dt><dd>${esc(d.financial_year)}</dd></div><div><dt class="kt-auth-label">${__("Current Approved Version reference")}</dt><dd>${esc(d.approved_version)}</dd></div><div><dt class="kt-auth-label">${__("Open Draft Version reference")}</dt><dd>${esc(d.draft_version)}</dd></div></dl></section><button class="kt-auth-btn" data-action="back">← ${__("Back to access diagnostic")}</button></main>`);
      $(wrapper).on("click","[data-action=back]",()=>frappe.set_route("access-diagnostic"));
    } catch (e) { frappe.msgprint({title:e.exc_type||__("Support access denied"),message:e.message||String(e),indicator:"red"}); }
  };
})();
