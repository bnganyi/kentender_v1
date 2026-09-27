<script setup>
// BDS-CHG-001 v0.8 §10.7 BDS-DES-06 — Your bid, ported from "Bid Board v3 - B"
// (1440 tables; 390 labelled cards). `GetBidWorkspace` decides the header
// action, the next step and journey, the deadline and time remaining, the
// availability notice, the current notices and every task's state, last
// change and action; nothing here derives them. Five ordinary tasks, current
// notices, the deadline and one next action — no dashboard, no Submit here.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const METHOD = "kentender_procurement.bid_submission.api.get_bid_workspace";
const TASK_TONES = { Complete: "is-live", "Needs attention": "is-attention" };
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
	bid: { type: String, default: "" },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();

const header = computed(() => (data.value && data.value.header) || {});
const notice = computed(() => data.value && data.value.availability_notice);
const bidReference = computed(() => props.bid || (data.value && data.value.bid && data.value.bid.reference) || "");

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(METHOD, { tender_reference: props.reference, bid_reference: bidReference.value, organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
// A fix on the next step names where it is done; the server gives the route.
function onFix(fix) {
	const href = fixRoute(fix, props.reference) || (header.value.action && header.value.action.href);
	if (href) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Your bid"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-workspace">
		<div class="kt-page-head" :class="{ 'bds-head-stack': narrow }">
			<div class="bds-head-main">
				<div class="bds-title-row"><h1 class="kt-page-title">{{ __("Your bid") }}</h1></div>
				<div class="bds-reference" data-testid="bds-workspace-refs">{{ header.title_line }}<br>{{ header.refs_line }}</div>
				<p class="kt-page-desc">{{ header.description }}</p>
			</div>
			<div v-if="header.action" class="kt-page-actions" :class="{ 'bds-actions-stack': narrow }">
				<a :href="header.action.href" class="kt-btn" :class="[header.action.tone === 'secondary' ? 'kt-btn-secondary' : 'kt-btn-primary', { 'bds-btn-block': narrow }]" data-testid="bds-workspace-action">{{ __(header.action.label) }}</a>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<div class="kt-region">
			<h2>{{ __("Deadline") }}</h2>
			<div class="bds-region-body">
				<div class="kt-meta-row" data-testid="bds-workspace-deadline">
					<div v-for="row in data.deadline.rows" :key="row.label"><span class="kt-label">{{ __(row.label) }}</span><span class="kt-meta-value">{{ row.value }}</span></div>
				</div>
			</div>
		</div>

		<div v-if="notice" class="kt-notice" :class="notice.tone === 'critical' ? 'is-critical' : 'is-warning'" role="status" data-testid="bds-workspace-availability">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
			<div class="kt-notice-body">
				<strong>{{ notice.title }}</strong>
				<div class="bds-notice-text">{{ notice.text }}<template v-for="(link, i) in notice.links" :key="link.label">{{ i === 0 ? " " : " · " }}<a :href="link.href">{{ __(link.label) }}</a></template></div>
			</div>
		</div>

		<div class="kt-region is-secondary">
			<h2>{{ __("Current notices") }}</h2>
			<div class="bds-region-body">
				<template v-if="data.notices.length">
					<table v-if="!narrow" class="kt-table" data-testid="bds-notices-table">
						<thead><tr><th>{{ __("Notice") }}</th><th>{{ __("Status") }}</th><th>{{ __("Action") }}</th></tr></thead>
						<tbody>
							<tr v-for="n in data.notices" :key="n.key">
								<td class="bds-strong">{{ n.label }}</td>
								<td><span class="kt-status" :class="'is-' + n.tone">{{ n.status }}</span></td>
								<td><a :href="n.action.href">{{ __(n.action.label) }}</a></td>
							</tr>
						</tbody>
					</table>
					<div v-else data-testid="bds-notices-cards">
						<div v-for="n in data.notices" :key="n.key" class="bds-card">
							<div class="bds-card-title">{{ n.label }}</div>
							<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="'is-' + n.tone">{{ n.status }}</span></span></div>
							<div class="bds-card-actions"><a :href="n.action.href">{{ __(n.action.label) }}</a></div>
						</div>
					</div>
				</template>
				<p v-else class="bds-muted" data-testid="bds-no-notices">{{ __("No answers or addenda have been published for this Tender.") }}</p>
				<p v-if="data.notices.length" class="bds-muted">{{ data.notices_note }}</p>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Bid tasks") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-tasks-table">
					<thead><tr><th>{{ __("Task") }}</th><th>{{ __("Status") }}</th><th>{{ __("Updated") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="t in data.tasks" :key="t.key" :data-testid="'bds-task-' + t.key">
							<td class="bds-strong">{{ t.label }}</td>
							<td><span class="kt-status" :class="TASK_TONES[t.status] || 'is-draft'">{{ t.status }}</span></td>
							<td>{{ t.updated_label }}</td>
							<td>
								<a v-if="t.action.primary" :href="t.action.href" class="kt-btn kt-btn-primary">{{ __(t.action.label) }}</a>
								<a v-else :href="t.action.href">{{ __(t.action.label) }}</a>
							</td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-tasks-cards">
					<div v-for="t in data.tasks" :key="t.key" class="bds-card" :data-testid="'bds-task-' + t.key">
						<div class="bds-card-title">{{ t.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="TASK_TONES[t.status] || 'is-draft'">{{ t.status }}</span></span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Updated") }}</span><span>{{ t.updated_label }}</span></div>
						<div class="bds-card-actions">
							<a v-if="t.action.primary" :href="t.action.href" class="kt-btn kt-btn-primary bds-btn-touch">{{ __(t.action.label) }}</a>
							<a v-else :href="t.action.href">{{ __(t.action.label) }}</a>
						</div>
					</div>
				</div>
				<p v-if="data.saved_text" class="bds-muted" data-testid="bds-workspace-saved">{{ data.saved_text }}</p>
			</div>
		</div>
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-workspace-loading"></div></div>
</template>
