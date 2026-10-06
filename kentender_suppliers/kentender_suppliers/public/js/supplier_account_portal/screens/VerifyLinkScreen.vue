<script setup>
// BDS-CHG-001 v0.8 §5.2 / §7.2 `VerifyAccountCommunication`: the link from
// the verification email. Opening it is the verification; the screen says
// what happened and leads to the Account. An expired, replaced or unknown
// link says so and offers a new one from the Account (never an error page).
import { computed, inject, onMounted, ref } from "vue";

const METHOD = "kentender_suppliers.supplier_accounts.api.verify_account_communication";
const props = defineProps({ token: { type: String, default: "" } });
const portal = inject("portal");
const result = ref(null);
const failure = ref("");
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value || (!result.value && !failure.value));

function verify() {
	failure.value = "";
	return runner.run(async () => {
		result.value = await portal.call(METHOD, { token: props.token }, { type: "POST" });
	}, "Verify email");
}
onMounted(() => {
	portal.setTitle(__("Verify your contact"));
	verify();
});
</script>

<template>
	<div class="kt-page" data-testid="acc-verify-link">
		<div class="kt-page-head">
			<div class="acc-head-main">
				<div class="acc-title-row"><h1 class="kt-page-title">{{ __("Verify your contact") }}</h1></div>
				<p v-if="pending" class="kt-page-desc" role="status">{{ __("Checking your verification link…") }}</p>
				<p v-else-if="result && result.ok" class="kt-page-desc" role="status" data-testid="acc-verified">{{ result.already_verified ? __("This email is already verified.") : __("Your email is verified. The supplier account is ready.") }}</p>
				<p v-else-if="result" class="kt-page-desc" role="alert" data-testid="acc-verify-refused">{{ result.message }}</p>
			</div>
		</div>
		<div v-if="failure" class="kt-notice is-critical acc-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="btn btn-secondary" @click="verify">{{ __("Try again") }}</button>
		</div>
		<div v-if="!pending" class="acc-actions">
			<a href="/account" class="btn btn-primary" data-testid="acc-verify-continue" @click.prevent="portal.go('/account')">{{ __("Go to Account") }}</a>
		</div>
	</div>
</template>
