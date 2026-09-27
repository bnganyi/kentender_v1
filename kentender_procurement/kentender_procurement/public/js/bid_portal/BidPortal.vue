<script setup>
// The surface root: picks the screen for the current path and hands it the
// server's first payload only for the path the page was rendered for
// (KT-STD-001 §3A.1). Screens are added slice by slice (plan Phase 11); any
// other path shows the Tender-not-found state rather than a guess.
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import AvailableTendersScreen from "./screens/AvailableTendersScreen.vue";
import TenderOverviewScreen from "./screens/TenderOverviewScreen.vue";
import CommonState from "./components/CommonState.vue";

const props = defineProps({
	initial: { type: Object, default: () => ({}) },
	portal: { type: Object, required: true },
});
const { route } = props.portal.useRoute({ ref, onMounted, onUnmounted });
// The server said this path has no Tender (first paint) or a later read did.
const notFound = ref(!!(props.initial && props.initial.path === route.value.path && (props.initial.payload || {}).screen === "tender-not-found"));
watch(() => route.value.path, () => (notFound.value = false));

const screen = computed(() => {
	const segments = route.value.segments;
	if (segments.length === 1 && segments[0] === "tenders") return "available-tenders";
	if (segments.length === 2 && segments[0] === "tenders" && !notFound.value) return "tender-overview";
	return "not-found";
});

// A screen sets its own title when it mounts; a common state names itself.
watch(screen, (name) => name === "not-found" && props.portal.setTitle(__("Tender not found")), { immediate: true });

function firstPayload(name) {
	const initial = props.initial || {};
	const payload = initial.payload || {};
	return initial.path === route.value.path && payload.screen === name ? payload.data || null : null;
}
</script>

<template>
	<AvailableTendersScreen v-if="screen === 'available-tenders'" :initial="firstPayload('available-tenders')" />
	<TenderOverviewScreen v-else-if="screen === 'tender-overview'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('tender-overview')" @not-found="notFound = true" />
	<CommonState
		v-else
		state="tender-not-found"
		heading="Tender not found."
		message="Return to Tenders."
		action-label="Back to Tenders"
		action-href="/tenders"
	/>
</template>
