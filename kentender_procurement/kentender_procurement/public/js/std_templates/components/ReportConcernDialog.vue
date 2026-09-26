<!-- STD-DES-02C Report concern — ported class-for-class (DS .dialog/.field/
     .input/.btn -> .kt-dialog/.kt-field/.kt-input/.kt-btn). The only write
     action on STD Templates: it records a bounded concern and never edits,
     blocks, approves or withdraws the release. Invalid input keeps what was
     entered and names each field (STD_CONCERN_INVALID; AGENTS.md §6.10). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="stdt-concern-dialog" @keydown.esc.stop="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog stdt-dialog" role="dialog" aria-modal="true" aria-labelledby="stdt-rc-title" tabindex="-1">
			<div>
				<div id="stdt-rc-title" class="kt-dialog-title">Report concern</div>
				<div style="font-size: 13px; color: var(--kt-color-neutral-800); margin-top: 4px">{{ release.display_name }} · Release {{ release.template_release }}</div>
			</div>
			<div class="kt-field">
				<label for="stdt-rc-cat">Category</label>
				<select id="stdt-rc-cat" ref="firstEl" v-model="form.category" class="kt-input" :aria-invalid="!!errors.category" data-testid="stdt-rc-category">
					<option value="" disabled>Choose a category</option>
					<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
				</select>
				<p v-if="errors.category" class="kt-field-error">{{ errors.category }}</p>
			</div>
			<div class="kt-field">
				<label for="stdt-rc-loc">Source locator or section</label>
				<input id="stdt-rc-loc" v-model="form.source_locator" class="kt-input" maxlength="140" :aria-invalid="!!errors.source_locator" data-testid="stdt-rc-locator" />
				<p v-if="errors.source_locator" class="kt-field-error">{{ errors.source_locator }}</p>
			</div>
			<div class="kt-field">
				<label for="stdt-rc-sum">Summary</label>
				<input id="stdt-rc-sum" v-model="form.summary" class="kt-input" maxlength="140" :aria-invalid="!!errors.summary" data-testid="stdt-rc-summary" />
				<p v-if="errors.summary" class="kt-field-error">{{ errors.summary }}</p>
			</div>
			<div class="kt-field">
				<label for="stdt-rc-desc">Description</label>
				<textarea id="stdt-rc-desc" v-model="form.description" class="kt-input" rows="4" maxlength="2000" style="resize: vertical; height: auto" :aria-invalid="!!errors.description" data-testid="stdt-rc-description"></textarea>
				<p v-if="errors.description" class="kt-field-error">{{ errors.description }}</p>
			</div>
			<div class="kt-field">
				<label for="stdt-rc-file">Evidence attachment (optional)</label>
				<input id="stdt-rc-file" class="kt-input" type="file" accept=".pdf,.png,.jpg,.jpeg" :aria-invalid="!!errors.evidence_file_id" data-testid="stdt-rc-file" @change="onFile" />
				<p v-if="errors.evidence_file_id" class="kt-field-error">{{ errors.evidence_file_id }}</p>
			</div>
			<p class="kt-dialog-body" style="margin: 0">Reporting a concern does not change this release's availability.</p>
			<div v-if="error" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ error }}</div></div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="stdt-rc-cancel" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="stdt-rc-submit" @click="submit">{{ pending ? "Reporting…" : "Report concern" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from "vue";

defineProps({
	release: { type: Object, required: true },
	categories: { type: Array, default: () => [] },
	pending: { type: Boolean, default: false },
	errors: { type: Object, default: () => ({}) },
	error: { type: String, default: "" },
});
const emit = defineEmits(["submit", "cancel"]);

const form = reactive({ category: "", source_locator: "", summary: "", description: "" });
const file = ref(null);
const firstEl = ref(null);

function onFile(event) {
	file.value = (event.target.files || [])[0] || null;
}
function submit() {
	emit("submit", { values: { ...form }, file: file.value });
}
onMounted(() => nextTick(() => firstEl.value && firstEl.value.focus()));
</script>
