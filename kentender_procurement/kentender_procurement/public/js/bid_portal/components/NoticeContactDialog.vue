<script setup>
// BDS-CHG-001 v0.8 §10.8 BDS-DES-07-NOTICE › Update notice email
// (`UpdateTenderNoticeContact`): the candidate's Tender notice email is
// changed to another verified Account email. Only verified emails are
// offered; an earlier notice is never re-sent or rewritten here.
import { computed, inject, nextTick, onMounted, ref } from "vue";
import { useDialogFocus } from "../composables/useDialogFocus.js";

const METHOD = "kentender_procurement.bid_submission.api.update_tender_notice_contact";
const props = defineProps({ contact: { type: Object, required: true } });
const emit = defineEmits(["close", "saved"]);
const portal = inject("portal");
const choice = ref(props.contact.current || ((props.contact.options || [])[0] || {}).contact_id || "");
const error = ref("");
const failure = ref("");
const first = ref(null);
const key = `bds-notice-contact-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function save() {
	error.value = "";
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.call(METHOD, { bidder_arrangement_id: props.contact.arrangement, notice_contact_id: choice.value, expected_record_version: props.contact.record_version, idempotency_key: key }, { type: "POST" });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) error.value = result.errors.notice_contact_id || result.message;
		else if (result) failure.value = result.message || "";
	}, "Update notice email");
}
const dialogBox = ref(null);
useDialogFocus(first, dialogBox);
</script>

<template>
	<div ref="dialogBox" class="kt-dialog-backdrop" data-testid="bds-notice-contact-dialog" @keydown.esc.stop="emit('close')">
		<div class="kt-dialog bds-dialog" role="dialog" aria-modal="true" aria-labelledby="bds-notice-contact-title">
			<div id="bds-notice-contact-title" class="kt-dialog-title">{{ __("Update notice email") }}</div>
			<div class="kt-field">
				<label for="bds-notice-contact-choice">{{ __("Tender notice email") }}</label>
				<select id="bds-notice-contact-choice" ref="first" v-model="choice" class="kt-input" :aria-invalid="!!error" aria-describedby="bds-notice-contact-help" data-testid="bds-notice-contact-choice">
					<option v-for="o in contact.options" :key="o.contact_id" :value="o.contact_id">{{ o.value }}</option>
				</select>
				<p v-if="error" class="kt-field-error">{{ error }}</p>
				<p v-else id="bds-notice-contact-help" class="bds-help">{{ __("Only verified Account emails can receive Tender notices. Notices already sent are not changed.") }}</p>
			</div>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-notice-contact-save" @click="save">{{ pending ? __("Saving…") : __("Update notice email") }}</button>
			</div>
		</div>
	</div>
</template>
