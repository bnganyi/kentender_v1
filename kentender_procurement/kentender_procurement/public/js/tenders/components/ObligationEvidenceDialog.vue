<!-- TPR-DES-12 "Record evidence" for one cancellation obligation: the
     evidence reference, an optional evidence file (notice channels record a
     real confirmation with attestation), the date it was available. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-obligation-dialog" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" aria-labelledby="tnd-ob-title" tabindex="-1">
			<div id="tnd-ob-title" class="kt-dialog-title">Record evidence — {{ obligation.label }}</div>
			<div class="tnd-dialog-body">
				<p class="tnd-small tnd-muted-700" style="margin: 0 0 14px">Due {{ obligation.due_by }}. Record the reference under which this obligation was met.</p>
				<div class="kt-field"><label for="tnd-ob-reference">Evidence reference</label><input id="tnd-ob-reference" class="kt-input" maxlength="160" v-model="form.evidence_reference" data-testid="tnd-ob-reference" /><p v-if="fieldErrors.evidence_reference" class="tnd-field-error" data-testid="tnd-ob-error-reference">{{ fieldErrors.evidence_reference }}</p></div>
				<div class="kt-field"><label for="tnd-ob-available">Available date/time</label><input id="tnd-ob-available" type="datetime-local" class="kt-input" v-model="form.available_at" data-testid="tnd-ob-available" /><p v-if="fieldErrors.available_at" class="tnd-field-error">{{ fieldErrors.available_at }}</p></div>
				<div v-if="online" class="kt-field"><label for="tnd-ob-url">Public URL</label><input id="tnd-ob-url" class="kt-input" placeholder="https://" v-model="form.public_url" data-testid="tnd-ob-url" /><p v-if="fieldErrors.public_url" class="tnd-field-error">{{ fieldErrors.public_url }}</p></div>
				<div class="kt-field"><label>Evidence file</label>
					<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-ob-choose-file" @click="chooseFile">{{ fileName ? "Replace file" : "Choose file" }}</button>
						<span v-if="fileName" class="tnd-small" data-testid="tnd-ob-filename">{{ fileName }}</span>
					</div>
					<p v-if="fieldErrors.evidence_file" class="tnd-field-error" data-testid="tnd-ob-error-file">{{ fieldErrors.evidence_file }}</p>
				</div>
				<label v-if="isChannel" class="kt-checkbox" style="margin-top: 14px; font-size: 13px"><input type="checkbox" v-model="form.attestation_confirmed" data-testid="tnd-ob-attest" /><span class="box"></span>I confirm that the cancellation notice was publicly available through {{ obligation.label }} at the date and time stated above.</label>
				<p v-if="error" class="tnd-field-error" role="alert" data-testid="tnd-ob-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-ob-confirm" @click="confirm">Record evidence</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { fromInputDateTime } from "../data/format.js";

const props = defineProps({
	obligation: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
	serverErrors: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["confirm", "cancel"]);
const dialogEl = ref(null);
const fileName = ref("");
const form = reactive({ evidence_reference: "", available_at: "", public_url: "", evidence_file: "", attestation_confirmed: false });
const localErrors = reactive({});
const fieldErrors = computed(() => ({ ...localErrors, ...(props.serverErrors || {}) }));
const isChannel = computed(() => props.obligation.obligation_type === "Notice channel");
const online = computed(() => ["STATE_PORTAL", "MINISTRY_WEBSITE"].includes(props.obligation.channel));

function chooseFile() {
	new frappe.ui.FileUploader({
		restrictions: { max_number_of_files: 1, allowed_file_types: [".pdf", ".png", ".jpg", ".jpeg"] },
		make_attachments_public: false,
		on_success: (file) => {
			form.evidence_file = file.name;
			fileName.value = file.file_name || file.name;
			delete localErrors.evidence_file;
		},
	});
}
function confirm() {
	for (const k of Object.keys(localErrors)) delete localErrors[k];
	if (!form.evidence_reference.trim()) localErrors.evidence_reference = "Enter the evidence reference (1–160 characters).";
	if (isChannel.value && !form.evidence_file) localErrors.evidence_file = "Attach the publication evidence file.";
	if (Object.keys(localErrors).length) return;
	emit("confirm", { evidence_reference: form.evidence_reference.trim(), available_at: form.available_at ? fromInputDateTime(form.available_at) : "", public_url: online.value ? form.public_url.trim() : "", url_not_applicable_reason: online.value && !form.public_url.trim() ? "No stable public URL" : online.value ? "" : "Physical channel", evidence_file: form.evidence_file, attestation_confirmed: !!form.attestation_confirmed });
}
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
