<script setup>
// C03-source-editor — one funding source: name and enabled. Rename is refused
// server-side while a Budget line version references the entry
// (`CFG_CATALOGUE_IN_USE`); no approval, no draft.
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
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

const title = computed(() => (props.creating ? __("Add funding source") : __("Edit funding source")));
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
	field.value?.focus();
});

function save() {
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
	<div class="kt-procset-view" data-testid="kt-procset-source-editor">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title">{{ title }}</h2>
			</div>
		</div>
		<div class="kt-card kt-blueprint kt-procset-narrow">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-field">
				<label for="kt-fs-name">{{ __("Funding source name") }}</label>
				<input id="kt-fs-name" ref="field" v-model="label" class="kt-input" data-testid="kt-fs-name">
				<p v-if="source && source.referenced" class="kt-hint">{{ __("This source is referenced by a Budget line and cannot be renamed.") }}</p>
			</div>
			<!-- §10.5 — an explicit Yes/No choice stating what it governs,
			     never a bare "Enabled" checkbox. -->
			<div class="kt-field">
				<label id="kt-fs-avail-label">{{ __("Available for new selection") }}</label>
				<div style="display:flex;gap:16px" role="radiogroup" aria-labelledby="kt-fs-avail-label">
					<label class="kt-radio" data-testid="kt-fs-enabled-yes">
						<input type="radio" name="kt-fs-avail" :checked="enabled" @change="enabled = true">
						<span class="dot" />{{ __("Yes") }}
					</label>
					<label class="kt-radio" data-testid="kt-fs-enabled-no">
						<input type="radio" name="kt-fs-avail" :checked="!enabled" @change="enabled = false">
						<span class="dot" />{{ __("No") }}
					</label>
				</div>
				<p class="kt-hint">{{ __("Turning this off prevents new selection; existing records keep their funding history.") }}</p>
			</div>
			<div v-if="duplicate" class="kt-notice is-critical" role="alert" data-testid="kt-fs-duplicate">
				<strong>{{ __("Duplicate.") }}</strong> {{ __("A funding source with this name already exists.") }}
			</div>
			<p v-else-if="error" class="kt-inline-error" role="alert" data-testid="kt-fs-error">{{ error }}</p>
		</div>
		<div class="kt-procset-footer kt-procset-narrow">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-fs-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-fs-save" @click="save">
				{{ creating ? __("Add funding source") : __("Save changes") }}
			</button>
		</div>
	</div>
</template>
