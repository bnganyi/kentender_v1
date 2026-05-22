// Strategic Plan form — guided creation UX. No extra fields.
frappe.ui.form.on("Strategic Plan", {
	refresh(frm) {
		$(frm.wrapper).find(".kt-sp-intro, .kt-sp-footer, .kt-sp-back-bar, .kt-sp-module-shell-host").remove();

		// Single primary action: hide toolbar Save; bottom button calls frm.save() (save() still works).
		frm.disable_save();

		const $page = $(frm.wrapper).find(".form-layout .form-page").first();
		if (!$page.length) {
			return;
		}

		if (
			typeof kentender_core !== "undefined" &&
			kentender_core.kt_shell &&
			kentender_core.kt_nav
		) {
			const $host = $('<div class="kt-sp-module-shell-host mb-2"></div>');
			$page.prepend($host);
			if (typeof kentender_core.kt_nav.ensureSidebar === "function") {
				kentender_core.kt_nav.ensureSidebar("strategy");
			}
			kentender_core.kt_shell.mountHeader($host, {
				moduleId: "strategy",
				recordTitle: frm.is_new()
					? __("New Strategic Plan")
					: frm.doc.strategic_plan_name || frm.doc.name,
				taskLabel: frm.is_new()
					? __("Create Plan")
					: kentender_core.kt_nav.taskLabel("strategy", "form"),
			});
		}

		const intro = $(
			`<div class="kt-sp-intro alert alert-info mb-3" role="status">
				<p class="mb-2">${__(
					"Create a strategic plan to define programs, objectives, and targets.",
				)}</p>
				<p class="kt-sp-hierarchy-hint small mb-0">${__(
					"You will define programs, objectives, and targets in a structured hierarchy.",
				)}</p>
				${
					frm.is_new()
						? `<p class="small mb-0 mt-2">${__(
								"After you save, you will open Manage Structure to add programs, objectives, and targets.",
						  )}</p>`
						: ""
				}
			</div>`,
		);
		$page.prepend(intro);

		// Align with input column: offset matches standard label (4) + field (8) split.
		const $footer = $(`<div class="kt-sp-footer">
			<div class="row">
				<div class="col-12 col-md-8 offset-md-4">
					<button type="button" class="btn btn-primary kt-sp-save-continue">${__(
						"Save and Continue",
					)}</button>
					<button type="button" class="btn btn-default kt-sp-open-builder ml-2" style="display:none;">${__(
						"Manage Structure",
					)}</button>
					<p class="text-muted small mt-3 mb-0">${__(
						"Next: Add programs first, then objectives nested under each program (hierarchy — not a single flat list).",
					)}</p>
				</div>
			</div>
		</div>`);

		if (!frm.is_new()) {
			$footer.find("button.kt-sp-open-builder").show().on("click", () => {
				if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
					kentender_core.kt_nav.toBuilder("strategy", frm.doc.name);
				} else {
					frappe.set_route("strategy-builder", frm.doc.name);
				}
			});
		}

		$footer.find("button.kt-sp-save-continue").on("click", () => {
			frm
				.save()
				.then(() => {
					frappe.show_alert({
						message: __("Strategic Plan saved"),
						indicator: "green",
					});
					if (frm.doc && frm.doc.name) {
						if (typeof kentender_core !== "undefined" && kentender_core.kt_nav) {
							kentender_core.kt_nav.toBuilder("strategy", frm.doc.name);
						} else {
							frappe.set_route("strategy-builder", frm.doc.name);
						}
					}
				})
				.catch(() => {});
		});

		$page.append($footer);
	},
});
