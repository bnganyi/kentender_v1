<script setup>
// BDS-CHG-001 v0.8 §10.4 BDS-DES-03 (and -VERIFY), ported from "Bid Board v3
// - A": the short registration form, explicitly not a qualification; Create
// account sends `RegisterSupplierOrganisation` with the authority evidence;
// the page then says where the verification link went (Pending verification).
// Every refused field is named in place and the entry is kept.
import { computed, inject, onMounted, reactive, ref } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import { useNarrow } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/useNarrow.js";

const REGISTER = "kentender_suppliers.supplier_accounts.api.register_supplier_organisation";
const READ = "kentender_suppliers.supplier_accounts.api.get_supplier_account";
const RESEND = "kentender_suppliers.supplier_accounts.api.send_account_verification";
const props = defineProps({ initial: { type: Object, default: null } });
const emit = defineEmits(["registered"]);
const portal = inject("portal");
const narrow = useNarrow();
const form = reactive({ legal_name: "", country: "Kenya", registration_number: "", tax_identifier: "", registered_address: "", official_email: "", official_phone: "", job_title: "" });
const file = ref(null);
const picker = ref(null);
const errors = ref({});
const failure = ref("");
const done = ref(null); // the Account read after Create account
const resent = ref("");
const key = `acc-register-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const guide = computed(() => (done.value ? done.value : props.initial) || {});
const userName = computed(() => (props.initial && props.initial.user_name) || "");

function chooseFile(event) {
	file.value = (event.target.files || [])[0] || null;
}
function create() {
	errors.value = {};
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.upload(REGISTER, { ...form, idempotency_key: key }, { authority_evidence: file.value });
		if (result && result.ok) {
			done.value = { ...(await portal.call(READ, { organisation: result.organisation })), sent_to: result.verification_sent_to };
		} else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Create account");
}
function resend() {
	return runner.run(async () => {
		const result = await portal.call(RESEND, { organisation: done.value.organisation.organisation, idempotency_key: `acc-resend-${Date.now().toString(36)}` }, { type: "POST" });
		resent.value = result && result.message ? result.message : result && result.sent_to ? `We sent a new verification link to ${result.sent_to}.` : "";
	}, "Resend verification link");
}
onMounted(() => portal.setTitle(__("Set up your supplier account")));
</script>

<template>
	<div class="kt-page" data-testid="acc-register">
		<div class="kt-page-head" :class="{ 'acc-head-stack': narrow }">
			<div class="acc-head-main">
				<div class="acc-title-row"><h1 class="kt-page-title">{{ __("Set up your supplier account") }}</h1></div>
				<p class="kt-page-desc">{{ __("Enter the organisation that will prepare and submit bids.") }}</p>
			</div>
		</div>
		<PortalGuidance :journey="guide.journey" :answer="guide.next_step" :label="__('Supplier account journey')" />

		<template v-if="done">
			<div class="kt-region" data-testid="acc-verify-sent">
				<h2>{{ __("Verify your contact") }}</h2>
				<div class="acc-region-body">
					<p class="acc-text">{{ __("We sent a verification link to {0}. Verify it before starting a bid.", [done.sent_to]) }}</p>
					<div><span class="kt-status is-attention">{{ __("Pending verification") }}</span></div>
					<p v-if="resent" class="acc-muted" role="status">{{ resent }}</p>
					<div class="acc-actions">
						<button type="button" class="btn btn-primary" :class="{ 'acc-btn-touch': narrow }" :disabled="pending" data-testid="acc-resend" @click="resend">{{ __("Resend verification link") }}</button>
						<a href="/account" class="btn btn-secondary" :class="{ 'acc-btn-touch': narrow }" data-testid="acc-back" @click.prevent="emit('registered')">{{ __("Back to Account") }}</a>
					</div>
				</div>
			</div>
		</template>

		<template v-else>
			<div class="kt-notice">
				<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg>
				<div class="kt-notice-body"><div>{{ __("Account setup gives your organisation access to bid preparation. It does not prequalify or approve the organisation for a Tender.") }}</div></div>
			</div>
			<div class="kt-region">
				<h2>{{ __("Organisation details") }}</h2>
				<div class="acc-region-body">
					<div class="field">
						<label for="acc-legal-name">{{ __("Legal name") }}</label>
						<input id="acc-legal-name" v-model="form.legal_name" class="input" :placeholder="__('Registered name of the organisation')" :aria-invalid="!!errors.legal_name" data-testid="acc-legal-name" />
						<p v-if="errors.legal_name" class="kt-field-error">{{ errors.legal_name }}</p>
					</div>
					<div class="acc-grid-2">
						<div class="field">
							<label for="acc-country">{{ __("Country") }}</label>
							<select id="acc-country" v-model="form.country" class="input" data-testid="acc-country"><option>Kenya</option></select>
							<p v-if="errors.country" class="kt-field-error">{{ errors.country }}</p>
						</div>
						<div class="field">
							<label for="acc-registration">{{ __("Registration number") }}</label>
							<input id="acc-registration" v-model="form.registration_number" class="input" :aria-invalid="!!errors.registration_number" data-testid="acc-registration" />
							<p v-if="errors.registration_number" class="kt-field-error">{{ errors.registration_number }}</p>
						</div>
					</div>
					<div class="acc-grid-2">
						<div class="field">
							<label for="acc-kra">{{ __("KRA PIN") }}</label>
							<input id="acc-kra" v-model="form.tax_identifier" class="input" :aria-invalid="!!errors.tax_identifier" data-testid="acc-kra" />
							<p v-if="errors.tax_identifier" class="kt-field-error">{{ errors.tax_identifier }}</p>
						</div>
					</div>
					<div class="field">
						<label for="acc-address">{{ __("Registered address") }}</label>
						<input id="acc-address" v-model="form.registered_address" class="input" :aria-invalid="!!errors.registered_address" data-testid="acc-address" />
						<p v-if="errors.registered_address" class="kt-field-error">{{ errors.registered_address }}</p>
					</div>
				</div>
			</div>
			<div class="kt-region">
				<h2>{{ __("Official contact") }}</h2>
				<div class="acc-region-body">
					<div class="acc-grid-2">
						<div class="field">
							<label for="acc-email">{{ __("Official email") }}</label>
							<input id="acc-email" v-model="form.official_email" class="input" type="email" :aria-invalid="!!errors.official_email" aria-describedby="acc-email-help" data-testid="acc-email" />
							<p v-if="errors.official_email" class="kt-field-error">{{ errors.official_email }}</p>
							<p v-else id="acc-email-help" class="acc-help">{{ __("You are signed in as {0}. Enter the organisation’s official email, not your personal sign-in email.", [userName]) }}</p>
						</div>
						<div class="field">
							<label for="acc-phone">{{ __("Official phone") }}</label>
							<input id="acc-phone" v-model="form.official_phone" class="input" type="tel" :aria-invalid="!!errors.official_phone" data-testid="acc-phone" />
							<p v-if="errors.official_phone" class="kt-field-error">{{ errors.official_phone }}</p>
						</div>
					</div>
				</div>
			</div>
			<div class="kt-region">
				<h2>{{ __("Your responsibility") }}</h2>
				<div class="acc-region-body">
					<div class="acc-grid-2">
						<div class="field">
							<label for="acc-responsibility">{{ __("Responsibility") }}</label>
							<input id="acc-responsibility" class="input" :value="__('Authorised Signatory')" disabled />
						</div>
						<div class="field">
							<label for="acc-job-title">{{ __("Job title") }}</label>
							<input id="acc-job-title" v-model="form.job_title" class="input" :aria-invalid="!!errors.job_title" data-testid="acc-job-title" />
							<p v-if="errors.job_title" class="kt-field-error">{{ errors.job_title }}</p>
						</div>
					</div>
					<div class="field">
						<label for="acc-authority">{{ __("Authority evidence") }}</label>
						<input id="acc-authority" ref="picker" class="acc-file-input" type="file" tabindex="-1" accept=".pdf,.png,.jpg,.jpeg" :aria-invalid="!!errors.authority_evidence" data-testid="acc-authority" @change="chooseFile" />
						<div class="acc-upload">
							<button type="button" class="btn btn-secondary" :class="{ 'acc-btn-touch': narrow }" data-testid="acc-authority-choose" @click="picker && picker.click()">
								<span class="acc-btn-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5-5 5 5" /><path d="M12 5v12" /></svg>{{ __("Upload evidence") }}</span>
							</button>
							<span class="acc-file-name" data-testid="acc-authority-name">{{ file ? file.name : __("No file chosen") }}</span>
						</div>
						<p v-if="errors.authority_evidence" class="kt-field-error">{{ errors.authority_evidence }}</p>
					</div>
				</div>
			</div>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<div v-if="narrow" class="acc-footer-stack">
				<button type="button" class="btn btn-primary acc-btn-block" :disabled="pending" data-testid="acc-create" @click="create">{{ pending ? __("Creating…") : __("Create account") }}</button>
				<a href="/tenders" class="btn btn-secondary acc-btn-block">{{ __("Cancel") }}</a>
			</div>
			<div v-else class="acc-footer">
				<a href="/tenders" class="btn btn-secondary">{{ __("Cancel") }}</a>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="acc-create" @click="create">{{ pending ? __("Creating…") : __("Create account") }}</button>
			</div>
		</template>
	</div>
</template>
