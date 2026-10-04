<script setup>
// STD-UI-M01 — Create new package version (§15.4). Shell mirrors
// kentender_strategy's ConfirmDialog.vue/AddTargetDialog.vue pattern
// (kt-dialog-backdrop/kt-dialog, Escape-to-cancel, kt-field/kt-input).
import { reactive, ref, watch, nextTick } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	basedOnLabel: { type: String, default: "" },
	saving: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({ official_issue_label: "", official_source_file_id: "", official_source_file_name: "" });
const issueInput = ref(null);

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		Object.assign(form, { official_issue_label: "", official_source_file_id: "", official_source_file_name: "" });
		await nextTick();
		issueInput.value?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}

function pickSourceFile() {
	new frappe.ui.FileUploader({
		folder: "Home",
		on_success: (file) => {
			form.official_source_file_id = file.name;
			form.official_source_file_name = file.file_name;
		},
	});
}

function onConfirm() {
	emit("confirm", {
		official_issue_label: form.official_issue_label,
		official_source_file_id: form.official_source_file_id || null,
	});
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" @keydown="onKeydown" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 520px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Create new package version") }}</h2>
			<p class="kt-muted" style="font-size: 14px; margin: 0 0 16px">
				{{ __("Start Version 2 from the current Active Version 1. Existing Requisitions and Tenders will remain bound to Version 1.") }}
			</p>

			<div class="kt-card" style="padding: 10px 16px; margin-bottom: 16px">
				<span class="kt-muted">{{ __("Based on") }} — </span><strong>{{ basedOnLabel }}</strong>
			</div>

			<div class="kt-field" style="margin: 0 0 16px">
				<label for="kt-cfg-version-issue">{{ __("Official issue") }}</label>
				<input
					id="kt-cfg-version-issue"
					ref="issueInput"
					v-model="form.official_issue_label"
					class="kt-input"
					type="text"
					placeholder="e.g. June 2028 revision"
				/>
			</div>

			<div class="kt-field" style="margin: 0 0 16px">
				<label>{{ __("Official source") }}</label>
				<div style="display: flex; align-items: center; gap: 10px">
					<span class="kt-muted">{{ form.official_source_file_name || __("No file selected") }}</span>
					<button type="button" class="kt-btn kt-btn-secondary" @click="pickSourceFile">{{ __("Replace") }}</button>
				</div>
			</div>

			<p v-if="error" class="kt-status is-critical" style="display: inline-block">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="saving || !form.official_issue_label"
					@click="onConfirm"
				>
					{{ __("Create Draft Version 2") }}
				</button>
			</div>
		</div>
	</div>
</template>
