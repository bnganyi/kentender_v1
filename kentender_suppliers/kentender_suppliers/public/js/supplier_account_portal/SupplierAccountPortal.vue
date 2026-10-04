<script setup>
// The Account surface root: picks the screen for the current path and hands
// it the server's first payload for the path the page was rendered for
// (KT-STD-001 §3A.1). /account with no Account yet is the registration form.
import { computed, onMounted, onUnmounted, ref } from "vue";
import AccountScreen from "./screens/AccountScreen.vue";
import RegisterScreen from "./screens/RegisterScreen.vue";
import VerifyLinkScreen from "./screens/VerifyLinkScreen.vue";

const props = defineProps({
	initial: { type: Object, default: () => ({}) },
	portal: { type: Object, required: true },
});
const { route, go } = props.portal.useRoute({ ref, onMounted, onUnmounted });

function payload() {
	const initial = props.initial || {};
	return initial.path === route.value.path ? initial.payload || {} : {};
}
const screen = computed(() => {
	const s = route.value.segments;
	if (s.length === 2 && s[1] === "verify") return "verify";
	if (s.length === 2 && s[1] === "register") return "register";
	if (s.length === 1) return payload().screen === "register" ? "register" : "account";
	return "not-found";
});
</script>

<template>
	<RegisterScreen v-if="screen === 'register'" :initial="payload().screen === 'register' ? payload().data : null" @registered="go('/account')" />
	<VerifyLinkScreen v-else-if="screen === 'verify'" :token="(payload().data || {}).token || route.query.token || ''" />
	<AccountScreen v-else-if="screen === 'account'" :initial="['account', 'choose'].includes(payload().screen) ? payload().data : null" @no-account="go('/account/register')" />
	<div v-else class="kt-page" data-testid="acc-not-found">
		<div class="kt-page-head"><div><h1 class="kt-page-title">{{ __("Page not found") }}</h1><p class="kt-page-desc">{{ __("This page is unavailable.") }}</p></div></div>
	</div>
</template>
