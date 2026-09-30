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
import ReviewTaskScreen from "./screens/ReviewTaskScreen.vue";
import SubmitScreen from "./screens/SubmitScreen.vue";
import ReceiptScreen from "./screens/ReceiptScreen.vue";
import ReplacementScreen from "./screens/ReplacementScreen.vue";
import StatusScreen from "./screens/StatusScreen.vue";
import RequirementsTaskScreen from "./screens/RequirementsTaskScreen.vue";
import DocumentsTaskScreen from "./screens/DocumentsTaskScreen.vue";
import MyBidsScreen from "./screens/MyBidsScreen.vue";
import ReceiptHistoryScreen from "./screens/ReceiptHistoryScreen.vue";
import TenderOverviewScreen from "./screens/TenderOverviewScreen.vue";
import CommonState from "./components/CommonState.vue";
// BOP-CHG-001 v0.10 plan D10: Bid Opening's public page, rendered here for
// /tenders/{ref}/opening (the file is Bid Opening's; this portal hosts it).
import PublicOpeningScreen from "../bid_opening/portal/PublicOpeningScreen.vue";
import EvaluationClarificationScreen from "../bid_evaluation/portal/ClarificationScreen.vue";

const props = defineProps({
	initial: { type: Object, default: () => ({}) },
	portal: { type: Object, required: true },
});
const { route } = props.portal.useRoute({ ref, onMounted, onUnmounted });
// The server said this path has nothing to show (first paint) or a later read did.
const notFound = ref(!!(props.initial && props.initial.path === route.value.path && ["tender-not-found", "not-found", "receipt-not-found"].includes((props.initial.payload || {}).screen)));
watch(() => route.value.path, () => (notFound.value = false));

const screen = computed(() => {
	const segments = route.value.segments;
	if (notFound.value) return "not-found";
	if (segments.length === 1 && segments[0] === "tenders") return "available-tenders";
	if (segments.length === 2 && segments[0] === "tenders") return "tender-overview";
	if (segments.length === 3 && segments[0] === "tenders" && segments[2] === "bid") return "workspace";
	if (segments.length === 3 && segments[0] === "tenders" && segments[2] === "opening") return "public-opening";
	// EVL-CHG-001 v0.4 plan D14: the evaluation committee's question, Bid Evaluation's screen
	if (segments.length === 5 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "evaluation-clarifications") return "evaluation-clarification";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "documents") return "documents-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "company") return "company-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "requirements") return "requirements-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "price") return "price-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "review") return "review-task";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "submit") return "submit";
	if (segments.length === 5 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "receipt") return "receipt";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "replace") return "replace";
	if (segments.length === 4 && segments[0] === "tenders" && segments[2] === "bid" && segments[3] === "status") return "status";
	if (segments.length === 1 && segments[0] === "my-bids") return "my-bids";
	if (segments.length === 2 && segments[0] === "account" && segments[1] === "receipts") return "receipts";
	return "not-found";
});

// A screen sets its own title when it mounts; a common state names itself.
function notFoundTitle() {
	const s = route.value.segments;
	if (s[0] === "tenders" && s[2] === "bid" && s[3] === "receipt") return __("Receipt not found");
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
	<PublicOpeningScreen v-else-if="screen === 'public-opening'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('public-opening')" @not-found="notFound = true" />
	<EvaluationClarificationScreen v-else-if="screen === 'evaluation-clarification'" :key="route.path" :reference="route.segments[1]" :clarification="route.segments[4]" :initial="firstPayload('evaluation-clarification')" @not-found="notFound = true" />
	<BidWorkspaceScreen v-else-if="screen === 'workspace'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('workspace')" @not-found="notFound = true" />
	<DocumentsTaskScreen v-else-if="screen === 'documents-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('documents-task')" @not-found="notFound = true" />
	<CompanyTaskScreen v-else-if="screen === 'company-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('company-task')" @not-found="notFound = true" />
	<RequirementsTaskScreen v-else-if="screen === 'requirements-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('requirements-task')" @not-found="notFound = true" />
	<PriceTaskScreen v-else-if="screen === 'price-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('price-task')" @not-found="notFound = true" />
	<ReviewTaskScreen v-else-if="screen === 'review-task'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('review-task')" @not-found="notFound = true" />
	<SubmitScreen v-else-if="screen === 'submit'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('submit')" @not-found="notFound = true" />
	<StatusScreen v-else-if="screen === 'status'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('status')" @not-found="notFound = true" />
	<ReplacementScreen v-else-if="screen === 'replace'" :key="route.path" :reference="route.segments[1]" :initial="firstPayload('replace')" @not-found="notFound = true" />
	<ReceiptScreen v-else-if="screen === 'receipt'" :key="route.path" :reference="route.segments[1]" :receipt="route.segments[4]" :initial="firstPayload('receipt')" @not-found="notFound = true" />
	<MyBidsScreen v-else-if="screen === 'my-bids'" :initial="firstPayload('my-bids')" />
	<ReceiptHistoryScreen v-else-if="screen === 'receipts'" :initial="firstPayload('receipts')" @not-found="notFound = true" />
	<CommonState v-else-if="route.segments[0] === 'tenders' && route.segments[2] === 'bid' && route.segments[3] === 'receipt'" state="receipt-not-found" action-href="/my-bids" />
	<CommonState v-else-if="route.segments[0] === 'tenders' && route.segments[2] === 'bid'" state="bid-not-found" action-href="/my-bids" />
	<CommonState v-else-if="route.segments[0] !== 'tenders'" state="page-not-found" action-href="/my-bids" />
	<CommonState v-else state="tender-not-found" action-href="/tenders" />
</template>
