<script setup>
// BDS-CHG-001 v0.8 §11.5 View status and §10.17: the latest submission
// attempt (or the submission service when there is none) as one common
// state — Confirmation pending, the tender box's rejection, the gate or an
// outage, or not submitted. An accepted attempt goes straight to its
// receipt. Reading changes nothing; the pending state's View status reads
// again.
import { inject, onMounted, onUnmounted, ref, watch } from "vue";
import CommonState from "../components/CommonState.vue";

const READ = "kentender_procurement.bid_submission.api.get_status_page";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { tender_reference: props.reference, organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		if (result && result.redirect) {
			go(result.redirect);
			return;
		}
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function onAction() {
	// the pending state's View status leads here: read again
	load();
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Submission status"));
	if (!data.value) load();
});
</script>

<template>
	<CommonState
		v-if="data && data.state"
		:state="data.state.key"
		:figures="data.state.figures"
		:retry="data.state.retry"
		:action-href="data.state.href === route.path ? '' : data.state.href"
		@action="onAction"
	/>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-status-loading"></div></div>
</template>
