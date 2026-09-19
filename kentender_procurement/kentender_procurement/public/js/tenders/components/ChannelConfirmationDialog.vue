<!-- TPR-DES-08 "Confirm <channel> publication" dialog: available date/time,
     publication reference, the public URL (online channels) or its
     not-applicable reason, the evidence file (frappe.ui.FileUploader — a
     real OS file dialog is the one control Vue cannot own), notes, and the
     attestation checkbox whose wording the server supplies. Used for the
     original publication and for an addendum's own confirmations. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-channel-dialog" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" aria-labelledby="tnd-channel-title" tabindex="-1">
			<div id="tnd-channel-title" class="kt-dialog-title">Confirm {{ channelWord }} publication</div>
			<div class="tnd-dialog-body">
				<p class="tnd-small tnd-muted-700" style="margin: 0 0 14px">Confirm only after the exact approved {{ subjectWord }} {{ subjectWord === "Invitation and complete Tender" ? "were" : "was" }} publicly available through this channel.</p>
				<div class="kt-field"><label for="tnd-ch-available">Available date/time</label><input id="tnd-ch-available" type="datetime-local" class="kt-input" v-model="form.available_at" data-testid="tnd-ch-available" /><p v-if="fieldErrors.available_at" class="tnd-field-error" data-testid="tnd-ch-error-available_at">{{ fieldErrors.available_at }}</p></div>
				<div class="kt-field"><label for="tnd-ch-reference">Publication reference</label><input id="tnd-ch-reference" class="kt-input" maxlength="160" v-model="form.evidence_reference" data-testid="tnd-ch-reference" /><p v-if="fieldErrors.evidence_reference" class="tnd-field-error" data-testid="tnd-ch-error-evidence_reference">{{ fieldErrors.evidence_reference }}</p></div>
				<template v-if="online">
					<div class="kt-field"><label for="tnd-ch-url">Public URL</label><input id="tnd-ch-url" class="kt-input" placeholder="https://" v-model="form.public_url" data-testid="tnd-ch-url" /><p v-if="fieldErrors.public_url" class="tnd-field-error" data-testid="tnd-ch-error-public_url">{{ fieldErrors.public_url }}</p></div>
					<div v-if="!form.public_url" class="kt-field"><label for="tnd-ch-noturl">Why no stable public URL exists</label><input id="tnd-ch-noturl" class="kt-input" v-model="form.url_not_applicable_reason" data-testid="tnd-ch-noturl" /></div>
				</template>
				<div class="kt-field"><label>Evidence file</label>
					<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-ch-choose-file" @click="chooseFile">{{ fileName ? "Replace file" : "Choose file" }}</button>
						<span v-if="fileName" class="tnd-small" data-testid="tnd-ch-filename">{{ fileName }}</span>
					</div>
					<p v-if="fieldErrors.evidence_file" class="tnd-field-error" data-testid="tnd-ch-error-evidence_file">{{ fieldErrors.evidence_file }}</p>
				</div>
				<div class="kt-field"><label for="tnd-ch-notes">Notes (optional, max 500)</label><textarea id="tnd-ch-notes" class="kt-input" rows="2" maxlength="500" v-model="form.evidence_notes" data-testid="tnd-ch-notes"></textarea><p v-if="fieldErrors.evidence_notes" class="tnd-field-error">{{ fieldErrors.evidence_notes }}</p></div>
				<label class="kt-checkbox" style="margin-top: 14px; font-size: 13px"><input type="checkbox" v-model="form.attestation_confirmed" data-testid="tnd-ch-attest" /><span class="box"></span>{{ attestation }}</label>
				<p v-if="fieldErrors.attestation_confirmed" class="tnd-field-error" data-testid="tnd-ch-error-attestation">{{ fieldErrors.attestation_confirmed }}</p>
				<p v-if="error" class="tnd-field-error" role="alert" data-testid="tnd-ch-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-ch-confirm" @click="confirm">Confirm publication</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { fromInputDateTime } from "../data/format.js";

const props = defineProps({
	channel: { type: Object, required: true }, // a confirmation row: channel, channel_label
	attestation: { type: String, default: "" },
	subjectWord: { type: String, default: "Invitation and complete Tender" },
	pending: Boolean,
	error: { type: String, default: "" },
	serverErrors: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["confirm", "cancel"]);

const ONLINE = ["STATE_PORTAL", "MINISTRY_WEBSITE"];
const dialogEl = ref(null);
const fileName = ref("");
const form = reactive({ available_at: "", evidence_reference: "", public_url: "", url_not_applicable_reason: "", evidence_file: "", evidence_notes: "", attestation_confirmed: false });
const localErrors = reactive({});
const fieldErrors = computed(() => ({ ...localErrors, ...(props.serverErrors || {}) }));
const online = computed(() => ONLINE.includes(props.channel.channel));
const channelWord = computed(() => {
	const label = (props.channel.channel_label || "").toLowerCase();
	return label.replace("notice board", "notice-board").replace("two national newspapers", "newspaper").replace("state portal", "State Portal");
});

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
	if (!form.available_at) localErrors.available_at = "Enter the date and time the documents became available.";
	if (!form.evidence_reference.trim()) localErrors.evidence_reference = "Enter the publication reference (1–160 characters).";
	if (!form.evidence_file) localErrors.evidence_file = "Attach the publication evidence file.";
	if (!form.attestation_confirmed) localErrors.attestation_confirmed = "Confirm the attestation to continue.";
	if (Object.keys(localErrors).length) return;
	emit("confirm", { available_at: fromInputDateTime(form.available_at), evidence_reference: form.evidence_reference.trim(), public_url: online.value ? form.public_url.trim() : "", url_not_applicable_reason: online.value ? (form.public_url.trim() ? "" : form.url_not_applicable_reason.trim()) : "Physical channel", evidence_file: form.evidence_file, evidence_notes: form.evidence_notes.trim(), attestation_confirmed: true });
}
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
