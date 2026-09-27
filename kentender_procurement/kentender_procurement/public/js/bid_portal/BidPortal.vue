<script setup>
// The surface root: picks the screen for the current path and hands it the
// server's first payload only for the path the page was rendered for
// (KT-STD-001 §3A.1). Screens are added slice by slice (plan Phase 11); any
// other path shows the Tender-not-found state rather than a guess.
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import AvailableTendersScreen from "./screens/AvailableTendersScreen.vue";
import BidWorkspaceScreen from "./screens/BidWorkspaceScreen.vue";
import CompanyTaskScreen from "./screens/CompanyTaskScreen.vue";
import PriceTaskScreen from "./screens/PriceTaskScreen.vue";
import RequirementsTaskScreen from "./screens/RequirementsTaskScreen.vue";
import DocumentsTaskScreen from "./screens/DocumentsTaskScreen.vue";
import MyBidsScreen from "./screens/MyBidsScreen.vue";
import ReceiptHistoryScreen from "./screens/ReceiptHistoryScreen.vue";
import TenderOverviewScreen from "./screens/TenderOverviewScreen.vue";
import CommonState from "./components/CommonState.vue";

const props = defineProps({
	initial: { type: Object, default: () => ({}) },
	portal: { type: Object, required: true },
});
const { route } = props.portal.useRoute({ ref, onMounted, onUnmounted });
// The server said this path has nothing to show (first paint) or a later read did.
const notFound = ref(!!(props.initial && props.initial.path === route.value.path && ["tender-not-found", "not-found"].includes((props.initial.payload || {}).screen)));
watch(() => route.value.path, () => (notFound.value = false));

const screen = computed(() => {
	const segments = route.value.segments;
	if (notFound.value) return "not-found";
	if (segments.length === 1 && segments[0] === "tenders") return "available-tenders";
	if (segments.length === 2 && segments[0] === "tenders") return "tender-overview";
	if (segments.length === 3 && segments[0] === "tenders" && segments[2] === "bid") return "workspace";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "documents") return "documents-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "company") return "company-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "requirements") return "requirements-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "price") return "price-task";
	if (segments.length === 1 && segments[0] === "my-bids") return "my-bids";
	if (segments.length === 2 && segments[0] === "account" && segments[1] === "receipts") return "receipts";
	return "not-found";
});

// A screen sets its own title when it mounts; a common state names itself.
function notFoundTitle() {
	const s = route.value.segments;
	if (s[0] === "tenders" && s[2] === "bid") return __("Bid not found");
	return s[0] === "tenders" ? __("Tender not found") : __("Page not found");
}
watch(screen, (name) => name === "not-found" && props.portal.setTitle(notFoundTitle()), { immediate: true });

function firstPayload(name) {
	const initial = props.initial || {};
	const payload = initial.payload || {};
	return initial.path === route.value.path && payload.screen === name ? payload.data || null : null;
}
</script>

<template>
	<AvailableTendersScreen v-if="screen === 'available-tenders'" :initial="firstPayload('available-tenders')" />
	<TenderOverviewScreen v-else-if="screen === 'tender-overview'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('tender-overview')" @not-found="notFound = true" />
	<BidWorkspaceScreen v-else-if="screen === 'workspace'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('workspace')" @not-found="notFound = true" />
	<DocumentsTaskScreen v-else-if="screen === 'documents-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('documents-task')" @not-found="notFound = true" />
	<CompanyTaskScreen v-else-if="screen === 'company-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('company-task')" @not-found="notFound = true" />
	<RequirementsTaskScreen v-else-if="screen === 'requirements-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('requirements-task')" @not-found="notFound = true" />
	<PriceTaskScreen v-else-if="screen === 'price-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('price-task')" @not-found="notFound = true" />
	<MyBidsScreen v-else-if="screen === 'my-bids'" :initial="firstPayload('my-bids')" />
	<ReceiptHistoryScreen v-else-if="screen === 'receipts'" :initial="firstPayload('receipts')" @not-found="notFound = true" />
	<CommonState
		v-else-if="route.segments[0] === 'tenders' && route.segments[2] === 'bid'"
		state="bid-not-found"
		heading="Bid not found."
		message="This bid is unavailable or you do not have permission to view it."
		action-label="Back to My bids"
		action-href="/my-bids"
	/>
	<CommonState
		v-else-if="route.segments[0] !== 'tenders'"
		state="not-found"
		heading="Page not found."
		message="This page is unavailable or you do not have permission to view it."
		action-label="Back to My bids"
		action-href="/my-bids"
	/>
	<CommonState
		v-else
		state="tender-not-found"
		heading="Tender not found."
		message="Return to Tenders."
		action-label="Back to Tenders"
		action-href="/tenders"
	/>
</template>
