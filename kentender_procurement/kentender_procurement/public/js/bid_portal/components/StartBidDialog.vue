<script setup>
// BDS-CHG-001 v0.8 §10.3 BDS-DES-02-JV-START / §11.2 Start bid: the short
// "Who is bidding?" step. The board names the step in its caption only; its
// content is the spec's (registered departure). Choices are My organisation
// and, where this Tender permits it, A joint venture (name, members by
// country and registration number, agreement from the Account's evidence,
// signatory); both choose the verified Tender notice email. One `StartBid`
// command creates or returns the arrangement and the Draft together; a
// refusal names each field and keeps what was entered. A bid format this
// portal cannot render is the §10.17 Format unsupported state: nothing was
// created, and Contact support is the one way on.
import { computed, inject, nextTick, onMounted, reactive, ref } from "vue";
import { useDialogFocus } from "../composables/useDialogFocus.js";
import CommonState from "./CommonState.vue";

const METHOD = "kentender_procurement.bid_submission.api.start_bid";
const props = defineProps({
	tender: { type: Object, required: true },
	start: { type: Object, required: true },
});
const emit = defineEmits(["close", "started"]);
const portal = inject("portal");
const form = reactive({
	arrangement_type: "Single organisation", joint_venture_name: "", members: [{ country: "Kenya", registration_number: "" }],
	agreement_evidence_id: "", signatory_assignment_id: "", notice_contact_id: (props.start.notice_contacts[0] || {}).contact_id || "",
});
const errors = ref({});
const failure = ref("");
const unsupported = ref(false);
const first = ref(null);
const key = `bds-start-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const UNSUPPORTED = "BDS_DEFINITION_UNSUPPORTED";
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (e.code === UNSUPPORTED ? (unsupported.value = true) : (failure.value = e.message)) });
const pending = computed(() => runner.pending.value);
const jv = computed(() => form.arrangement_type === "Joint venture");

function addMember() {
	form.members.push({ country: "Kenya", registration_number: "" });
}
function removeMember(index) {
	form.members.splice(index, 1);
}
function submit() {
	errors.value = {};
	failure.value = "";
	const arrangement = jv.value
		? { arrangement_type: "Joint venture", joint_venture_name: form.joint_venture_name, members: form.members, agreement_evidence_id: form.agreement_evidence_id, signatory_assignment_id: form.signatory_assignment_id }
		: { arrangement_type: "Single organisation" };
	return runner.run(async () => {
		const result = await portal.call(METHOD, { tender_reference: props.tender.reference, organisation: props.start.organisation.id, arrangement, notice_contact_id: form.notice_contact_id, idempotency_key: key }, { type: "POST" });
		if (result && result.ok) emit("started", result);
		else if (result && result.code === UNSUPPORTED) unsupported.value = true;
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Start bid");
}
const dialogBox = ref(null);
useDialogFocus(first, dialogBox);
</script>

<template>
	<div ref="dialogBox" class="dialog-backdrop" data-testid="bds-start-dialog" @keydown.esc.stop="emit('close')">
		<div class="dialog bds-dialog" role="dialog" aria-modal="true" aria-labelledby="bds-start-title">
			<div id="bds-start-title" class="dialog-title">{{ __("Who is bidding?") }}</div>
			<fieldset class="field bds-choice">
				<legend>{{ __("Who is bidding?") }}</legend>
				<label class="bds-radio"><input ref="first" v-model="form.arrangement_type" type="radio" value="Single organisation" data-testid="bds-start-single" /> {{ __("My organisation") }} <span class="bds-help">{{ start.organisation.legal_name }}</span></label>
				<label v-if="start.joint_venture_permitted" class="bds-radio"><input v-model="form.arrangement_type" type="radio" value="Joint venture" data-testid="bds-start-jv" /> {{ __("A joint venture") }}</label>
				<p v-if="errors.arrangement_type" class="kt-field-error">{{ errors.arrangement_type }}</p>
			</fieldset>
			<template v-if="jv">
				<div class="field">
					<label for="bds-jv-name">{{ __("Joint-venture name") }}</label>
					<input id="bds-jv-name" v-model="form.joint_venture_name" class="input" maxlength="160" :aria-invalid="!!errors.joint_venture_name" data-testid="bds-jv-name" />
					<p v-if="errors.joint_venture_name" class="kt-field-error">{{ errors.joint_venture_name }}</p>
				</div>
				<div class="bds-dialog-fact"><span class="kt-label">{{ __("Lead member") }}</span><span>{{ start.organisation.legal_name }}</span></div>
				<div v-for="(member, index) in form.members" :key="index" class="bds-member-row">
					<div class="field">
						<label :for="`bds-member-country-${index}`">{{ __("Member country") }}</label>
						<input :id="`bds-member-country-${index}`" v-model="member.country" class="input" />
					</div>
					<div class="field">
						<label :for="`bds-member-reg-${index}`">{{ __("Member registration number") }}</label>
						<input :id="`bds-member-reg-${index}`" v-model="member.registration_number" class="input" :aria-invalid="!!errors[`members.${index}`]" :data-testid="`bds-member-reg-${index}`" />
						<p v-if="errors[`members.${index}`]" class="kt-field-error">{{ errors[`members.${index}`] }}</p>
					</div>
					<button v-if="form.members.length > 1" type="button" class="btn btn-ghost" @click="removeMember(index)">{{ __("Remove member") }}</button>
				</div>
				<p v-if="errors.members" class="kt-field-error">{{ errors.members }}</p>
				<button type="button" class="btn btn-ghost" data-testid="bds-add-member" @click="addMember">{{ __("Add member") }}</button>
				<div class="field">
					<label for="bds-jv-agreement">{{ __("Joint-venture agreement") }}</label>
					<select id="bds-jv-agreement" v-model="form.agreement_evidence_id" class="input" :aria-invalid="!!errors.agreement_evidence_id" data-testid="bds-jv-agreement">
						<option value="" disabled>{{ __("Choose from your account evidence") }}</option>
						<option v-for="e in start.agreements" :key="e.evidence_id" :value="e.evidence_id">{{ e.title }}</option>
					</select>
					<p v-if="errors.agreement_evidence_id" class="kt-field-error">{{ errors.agreement_evidence_id }}</p>
				</div>
				<div class="field">
					<label for="bds-jv-signatory">{{ __("Authorised Signatory") }}</label>
					<select id="bds-jv-signatory" v-model="form.signatory_assignment_id" class="input" :aria-invalid="!!errors.signatory_assignment_id" data-testid="bds-jv-signatory">
						<option value="" disabled>{{ __("Choose the signatory") }}</option>
						<option v-for="s in start.signatories" :key="s.assignment_id" :value="s.assignment_id">{{ s.name }}</option>
					</select>
					<p v-if="errors.signatory_assignment_id" class="kt-field-error">{{ errors.signatory_assignment_id }}</p>
				</div>
			</template>
			<div class="field">
				<label for="bds-notice-contact">{{ __("Tender notice email") }}</label>
				<select id="bds-notice-contact" v-model="form.notice_contact_id" class="input" :aria-invalid="!!errors.notice_contact_id" aria-describedby="bds-notice-help" data-testid="bds-notice-contact">
					<option v-for="c in start.notice_contacts" :key="c.contact_id" :value="c.contact_id">{{ c.value }}</option>
				</select>
				<p v-if="errors.notice_contact_id" class="kt-field-error">{{ errors.notice_contact_id }}</p>
				<p v-else id="bds-notice-help" class="bds-help">{{ start.notice_contact_help }}</p>
			</div>
			<CommonState v-if="unsupported" inline state="format-unsupported" :action-href="start.support_href || ''" />
			<div v-else-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="bds-start-cancel" @click="emit('close')">{{ __("Cancel") }}</button>
				<button v-if="!unsupported" type="button" class="btn btn-primary" :disabled="pending" data-testid="bds-start-submit" @click="submit">{{ pending ? __("Starting…") : __("Start bid") }}</button>
			</div>
		</div>
	</div>
</template>
