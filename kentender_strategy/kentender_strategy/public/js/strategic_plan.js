// Strategic Plan form — guided creation UX. No extra fields.
frappe.ui.form.on("Strategic Plan", {
	refresh(frm) {
		$(frm.wrapper).find(".kt-sp-intro, .kt-sp-footer").remove();

		// Single primary action: hide toolbar Save; bottom button calls frm.save() (save() still works).
		frm.disable_save();

		const $page = $(frm.wrapper).find(".form-layout .form-page").first();
		if (!$page.length) {
			return;
		}

		const intro = $(
			`<div class="kt-sp-intro alert alert-info mb-3" role="status">
				<p class="mb-2">${__(
					"Create a strategic plan to define programs, objectives, and targets.",
				)}</p>
				<p class="kt-sp-hierarchy-hint small mb-0">${__(
					"You will define programs, objectives, and targets in a structured hierarchy.",
				)}</p>
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
					<p class="text-muted small mt-3 mb-0">${__(
						"Next: Add programs first, then objectives nested under each program (hierarchy — not a single flat list).",
					)}</p>
				</div>
			</div>
		</div>`);

		$footer.find("button.kt-sp-save-continue").on("click", () => {
			frm
				.save()
				.then(() => {
					frappe.show_alert({
						message: __("Strategic Plan saved"),
						indicator: "green",
					});
				})
				.catch(() => {});
		});

		$page.append($footer);
	},
});
