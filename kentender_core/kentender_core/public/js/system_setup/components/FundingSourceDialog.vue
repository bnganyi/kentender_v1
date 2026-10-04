<script setup>
// CFG-CHG-002 v0.14 §10.5 (C03A #add, #edit, #duplicate; tracker CFG14-5C) —
// one funding source: its name and whether it is available for new
// selection. Ported from the board's two dialogs, drawn over the list. Saves
// directly: no reason, no approval, no draft. A rename is refused server-side
// while a Budget line references the entry (`CFG_CATALOGUE_IN_USE`), so the
// name of a referenced source is not offered for editing at all. Escape stops
// here: Frappe's window-level Escape handler blurs the focused element, which
// would undo the list returning focus to the control that opened the dialog.
import { computed, nextTick, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";

const props = defineProps({
	source: { type: Object, default: null },
	creating: { type: Boolean, default: false },
	// Every existing source, so a duplicate name is refused before submit
	// (§10.5's exact defect) — `add_funding_source` is deliberately tolerant
	// of a repeat so the canonical seed stays idempotent, and would otherwise
	// report a silent success here.
	existing: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel"]);

const label = ref(props.source?.label || "");
const enabled = ref(props.source ? !!props.source.enabled : true);
const error = ref("");
const field = ref(null);
const yes = ref(null);
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

const title = computed(() => (props.creating ? __("Add funding source") : __("Edit funding source")));
const locked = computed(() => !!props.source?.referenced);
const duplicate = computed(() => {
	const wanted = label.value.trim().toLowerCase();
	if (!wanted) return false;
	return props.existing.some(
		(row) => row.name !== props.source?.name && (row.label || "").trim().toLowerCase() === wanted
	);
});
const canSave = computed(() => !busy.value && !duplicate.value && label.value.trim().length >= 2);

onMounted(async () => {
	await nextTick();
	// Focus the first control the user can change: the name, or, when a
	// referenced source's name is fixed, its availability.
	(locked.value ? yes.value : field.value)?.focus();
});

function save() {
	if (!canSave.value) return;
	return run(async () => {
		if (props.creating) {
			const created = await procurementSettingsApi.addFundingSource(label.value.trim());
			// `add_funding_source` takes a name only; an entry created as "not
			// available" is the same catalogue entry disabled immediately after,
			// through the one command that owns availability.
			if (!enabled.value) {
				await procurementSettingsApi.updateFundingSource(created.name, { enabled: false }, "");
			}
		} else {
			await procurementSettingsApi.updateFundingSource(
				props.source.name,
				{ label: label.value.trim(), enabled: enabled.value },
				props.source.expected_version
			);
		}
		emit("saved");
	});
}
</script>

<template>
	<div class="kt-dialog-backdrop">
		<div
			class="kt-dialog kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="title"
			data-testid="kt-procset-source-editor"
			@keydown.esc.stop="emit('cancel')"
		>
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<div class="dialog-body">
				<div class="kt-field">
					<label for="kt-fs-name">{{ __("Funding source name") }}</label>
					<input
						id="kt-fs-name"
						ref="field"
						v-model="label"
						class="kt-input"
						:disabled="locked"
						:aria-invalid="duplicate ? 'true' : 'false'"
						data-testid="kt-fs-name"
						@keydown.enter.prevent="save"
					>
				</div>
				<p v-if="locked" class="text-muted" style="font-size:12px;margin-top:6px" data-testid="kt-fs-locked">
					{{ __("This source is referenced by a Budget line and cannot be renamed.") }}
				</p>
				<!-- §10.5 — an explicit Yes/No choice stating what it governs,
				     never a bare "Enabled" checkbox. -->
				<div class="kt-field" style="margin-top:10px">
					<label id="kt-fs-avail-label">{{ __("Available for new selection") }}</label>
					<div style="display:flex;gap:16px" role="radiogroup" aria-labelledby="kt-fs-avail-label">
						<label class="kt-radio" data-testid="kt-fs-enabled-yes">
							<input ref="yes" type="radio" name="kt-fs-avail" :checked="enabled" @change="enabled = true">
							<span class="dot" />{{ __("Yes") }}
						</label>
						<label class="kt-radio" data-testid="kt-fs-enabled-no">
							<input type="radio" name="kt-fs-avail" :checked="!enabled" @change="enabled = false">
							<span class="dot" />{{ __("No") }}
						</label>
					</div>
				</div>
				<p class="text-muted" style="font-size:12px;margin-top:6px">{{ __("Turning this off prevents new selection; existing records keep their funding history.") }}</p>
				<div v-if="duplicate" class="kt-notice is-critical" role="alert" data-testid="kt-fs-duplicate">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body"><strong>{{ __("Duplicate.") }}</strong> {{ __("A funding source with this name already exists.") }}</div>
				</div>
				<div v-else-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-fs-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-fs-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-fs-save" @click="save">
					<svg v-if="creating" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ creating ? __("Add funding source") : __("Save changes") }}
				</button>
			</div>
		</div>
	</div>
</template>
