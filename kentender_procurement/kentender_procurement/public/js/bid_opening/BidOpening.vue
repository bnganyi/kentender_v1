<!-- Bid Opening — BOP-CHG-001 v0.10 §9, §10. Mounted by the Tenders page into
     its host for every route under /app/tenders/{ref}/opening:
       /app/tenders/{ref}/opening           the opening, as this viewer sees it
       /app/tenders/{ref}/opening/correct   correct the completed record (h4)
     The server's GetOpening picks what is shown: its state and this viewer's
     place in it (Prepare a1–a5, Open bids c1–c13b/z1/n1/n2, Opening record
     r1–r5, Completed r6/h1–h5). One loader with a sequence guard, one pending gate for every
     command, a reload after each command, and a quiet poll while the opening
     is live (plan D7: no socket.io on this bench). -->
<template>
	<div class="kt-bop" data-testid="bop-root" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-pending="pending ? 'true' : 'false'">
		<StateCard v-if="failure" :kind="failure" @action="onStateAction" />
		<div v-else-if="!data" class="kt-page" aria-busy="true" data-testid="bop-skeleton"><div class="kt-skeleton" style="height:48px;max-width:480px"></div><div class="kt-skeleton" style="height:120px;margin-top:24px"></div></div>
		<PrepareScreen v-else-if="screen === 'prepare'" :key="`prepare:${ref_}`" :data="data" :pending="pending" :error="error" :refusal="refusal" @appoint="appoint" @publish="publish" @edited="refusal = null" />
		<OpenBidsScreen v-else-if="screen === 'open-bids'" :key="`open:${ref_}`" :data="data" :pending="pending" :error="error" :refusal="refusal" @command="onCommand" />
		<RecordScreen v-else-if="screen === 'record'" :key="`record:${ref_}`" :data="data" :pending="pending" :error="error" @command="onCommand" />
		<CompletedScreen v-else :key="`completed:${ref_}`" :data="data" :pending="pending" :error="error" :sub="sub" @command="onCommand" @navigate="navigate" />
	</div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from "vue";
import * as api from "./data/api.js";
import { useRouteState } from "./composables/useRouteState.js";
import StateCard from "./components/StateCard.vue";
import CompletedScreen from "./screens/CompletedScreen.vue";
import OpenBidsScreen from "./screens/OpenBidsScreen.vue";
import PrepareScreen from "./screens/PrepareScreen.vue";
import RecordScreen from "./screens/RecordScreen.vue";

const PAGE = "tenders";
const POLL_MS = 5000;
const HEARTBEAT_MS = 20000;
const LIVE = ["Awaiting deadline", "Ready to open", "Opening", "Interrupted", "Readout complete", "Awaiting attestations"];

const { route, epoch } = useRouteState(PAGE);
const segments = computed(() => route.value.slice(1).filter(Boolean));
const ref_ = computed(() => (segments.value[1] === "opening" ? segments.value[0] : ""));
const sub = computed(() => (segments.value[1] === "opening" ? segments.value[2] || "" : ""));

const data = ref(null);
const loading = ref(false);
const failure = ref("");
const pending = ref(false);
const error = ref("");
const refusal = ref(null);
let seq = 0;

const state = computed(() => (data.value && data.value.opening.state) || "");
const viewer = computed(() => (data.value && data.value.viewer) || {});
// The screen follows the server's state and this viewer's place in it.
const screen = computed(() => {
	if (!data.value) return "";
	if (viewer.value.technical || state.value === "Opening complete") return "completed";
	if (["Readout complete", "Awaiting attestations"].includes(state.value)) return "record";
	const primary = (data.value.next_step || {}).primary_action;
	if (viewer.value.is_accounting_officer && !viewer.value.is_member && ["Awaiting deadline", "Ready to open"].includes(state.value) && primary !== "record_not_held") return "prepare";
	return "open-bids";
});

async function load({ quiet = false } = {}) {
	const reference = ref_.value;
	if (!reference) return;
	const token = ++seq;
	if (!quiet) loading.value = true;
	try {
		const loaded = await api.getOpening(reference);
		if (token !== seq) return;
		data.value = loaded;
		failure.value = "";
	} catch (e) {
		if (token !== seq) return;
		if (!quiet || !data.value) failure.value = e.httpStatus === 404 || /not found/i.test(e.message || "") ? "not-found" : "failure";
	} finally {
		if (token === seq) loading.value = false;
	}
}

// One pending gate for every command; the page reloads after each. A refused
// command's guard (when it has one) becomes the screen's blocked next step.
// Commands whose endpoint checks the record version it was shown (plan D3).
const VERSIONED = new Set(["appoint_committee", "publish_arrangements", "record_not_held", "begin_opening", "open_next_bid", "retry_opening", "resume_opening",
	"record_readout", "end_opening", "end_opening_with_no_bids", "finish_opening_record", "correct_opening_record_draft", "correct_opening_record"]);

async function run(method, args) {
	if (pending.value || !data.value) return null;
	pending.value = true;
	error.value = "";
	try {
		const version = VERSIONED.has(method) ? { expected_version: data.value.opening.record_version } : {};
		const result = await api.command(method, ref_.value, { ...version, ...args });
		if (result && result.ok === false) {
			refusal.value = result.guard ? result : null;
			error.value = result.guard ? "" : result.message || Object.values(result.errors || {})[0] || "The action could not be completed.";
		} else {
			refusal.value = null;
		}
		await load({ quiet: true });
		return result;
	} catch (e) {
		error.value = e.message || "The action could not be completed.";
		await load({ quiet: true });
		return null;
	} finally {
		pending.value = false;
	}
}

const appoint = (members) => run("appoint_committee", { members: JSON.stringify(members) });
const publish = (values) => run("publish_arrangements", values);
async function onCommand({ method, args }) {
	const result = await run(method, args || {});
	// a correction added returns to the completed record (board h5)
	if (method === "correct_opening_record" && result && result.ok !== false) navigate("");
}
function navigate(to) {
	frappe.set_route(PAGE, ref_.value, "opening", ...(to ? [to] : []));
}

function onStateAction(key) {
	if (key === "back") frappe.set_route(PAGE, ref_.value);
	else load();
}

watch(ref_, (now, before) => {
	if (now !== before) {
		data.value = null;
		refusal.value = null;
		error.value = "";
	}
	load();
}, { immediate: true });
watch(epoch, () => load({ quiet: true }));

// A quiet poll while the opening is live, and a heartbeat while this viewer is
// a present member (plan D7).
const poll = setInterval(() => {
	if (document.hidden || pending.value || !LIVE.includes(state.value)) return;
	load({ quiet: true });
}, POLL_MS);
const beat = setInterval(() => {
	const me = data.value && (data.value.committee.members || []).find((m) => m.member_user === frappe.session.user);
	if (me && me.present && !document.hidden) api.heartbeat(ref_.value).catch(() => {});
}, HEARTBEAT_MS);
onUnmounted(() => {
	clearInterval(poll);
	clearInterval(beat);
	seq++;
});
</script>
