<!-- A pre-authorisation record read outside its task route (REQ-DES-07
     record, REQ-DES-12 Withdrawn and Technical read). Complete and read-only;
     the only controls are the quiet ones the server allows this actor. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-locked" :data-mode="view.mode">
		<div class="req-title-row">
			<h3>{{ view.header.title }}</h3>
			<span class="kt-status" :class="view.header.badge.tone" data-testid="req-badge">{{ view.header.badge.label }}</span>
		</div>
		<div class="kt-label req-reference" style="margin-bottom: var(--kt-space-6)">{{ view.header.reference }}</div>

		<template v-if="view.withdrawn">
			<div class="kt-meta-row" data-testid="req-withdrawn">
				<div><span class="kt-label">Withdrawn by</span><span class="kt-meta-value" style="font-size: 14px">{{ view.withdrawn.by }}</span></div>
				<div><span class="kt-label">Withdrawn at</span><span class="kt-meta-value" style="font-size: 14px">{{ view.withdrawn.at }}</span></div>
			</div>
			<div class="kt-meta-row" style="margin-top: 12px"><div><span class="kt-label">Reason</span><span class="kt-meta-value" style="font-size: 14px">{{ view.withdrawn.reason }}</span></div></div>
			<p style="font-size: 14px; margin: 12px 0 0">No approved-plan amount or funding was used.</p>
			<p class="kt-muted" style="font-size: 12px; margin: 6px 0 var(--kt-space-6)">The complete preserved Version follows read-only.</p>
		</template>
		<template v-else-if="view.mode === 'technical'">
			<p style="font-size: 14px; margin: 0 0 var(--kt-space-6)">Complete record in its actual state.</p>
		</template>

		<DecisionChain :rows="view.decision_chain || []" style="margin-bottom: var(--kt-space-6)" />
		<ReviewSections :sections="view.sections || []" />
		<Disclosure title="Record details" testid="req-record-details">
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>

		<Notice v-if="error" tone="critical"><span data-testid="req-locked-error">{{ error }}</span></Notice>

		<div class="req-footer">
			<div class="req-actions">
				<button type="button" class="kt-btn kt-btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
				<ActionsMenu v-if="menu.length" :actions="menu" :disabled="busy" @choose="(k) => (dialog = k)" />
			</div>
			<button v-if="actions.export" type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="req-export" @click="downloadExport(ctx, view.requisition)">Export</button>
		</div>

		<ReasonDialog v-if="dialog === 'withdraw'" v-bind="WITHDRAW" :busy="busy" :error="dialogError('withdraw')" @close="dialog = null" @confirm="withdraw" />
		<ReasonDialog v-if="dialog === 'planning'" v-bind="PLANNING_CORRECTION" :busy="busy" :error="dialogError('planning')" @close="dialog = null" @confirm="requestPlanning" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import { PLANNING_CORRECTION, WITHDRAW } from "../data/dialogs.js";
import { downloadExport } from "../data/export.js";
import ActionsMenu from "./shared/ActionsMenu.vue";
import DecisionChain from "./shared/DecisionChain.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import ReasonDialog from "./shared/ReasonDialog.vue";
import ReviewSections from "./shared/ReviewSections.vue";

const props = defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const actions = computed(() => props.view.actions || {});
const menu = computed(() => [
	...(actions.value.request_planning_correction ? [{ key: "planning", label: "Request Planning correction" }] : []),
	...(actions.value.withdraw ? [{ key: "withdraw", label: "Withdraw requisition" }] : []),
]);
const dialog = ref(null);
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "export" ? ctx.commandError.value.message : ""));
function dialogError(label) {
	return ctx.commandError.value && ctx.commandError.value.label === label ? ctx.commandError.value.message : "";
}
const base = () => ({ requisition: props.view.requisition, expected_record_version: props.view.root_record_version });
async function withdraw({ reason }) {
	const done = await ctx.run("withdraw", (key) => ctx.api.withdraw({ ...base(), reason, idempotency_key: key }));
	if (done) dialog.value = null;
}
async function requestPlanning({ reason }) {
	const done = await ctx.run("planning", (key) => ctx.api.requestPlanningCorrection({ ...base(), reason, idempotency_key: key }));
	if (done) dialog.value = null;
}
</script>
