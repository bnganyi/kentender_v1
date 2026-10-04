<!-- REQ-DES-11 — Planning correction requested (Open, In progress, Resolved,
     Closed without change, Outcome unavailable, Another request unresolved,
     Procurement Planner) and the fresh-start confirmation. The stopped
     requisition is read-only; it never reopens. A fresh start is a new Draft,
     offered only when the server says this actor is eligible. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-stopped" :data-status="view.status">
		<div class="req-title-row">
			<h3>{{ view.header.title }}</h3>
			<span class="kt-status" :class="view.status_tone" data-testid="req-badge">{{ view.status_label }}</span>
		</div>
		<div class="kt-label req-reference">{{ view.header.reference }}</div>
		<p style="font-size: 14px; margin: 8px 0 var(--kt-space-6)">{{ view.header.description }}</p>

		<div v-if="view.other_unresolved.length" class="req-actions" style="margin-bottom: var(--kt-space-4)">
			<span class="kt-status" :class="terminal ? 'is-live' : 'is-attention'">{{ view.request.reference }} · {{ view.status }}</span>
			<span v-for="r in view.other_unresolved" :key="r.reference" class="kt-status is-attention">{{ r.reference }} · {{ r.status }}</span>
		</div>
		<Notice v-if="view.hold_notice" tone="warning"><span data-testid="req-hold-notice">{{ view.hold_notice }}</span></Notice>

		<template v-if="view.unavailable">
			<p class="kt-muted" style="font-size: 13px; margin: 0">Last confirmed: {{ view.request.status }}<template v-if="view.request.started"> · {{ view.request.started }}</template></p>
			<Notice tone="critical"><span data-testid="req-outcome-unavailable">Planning response is temporarily unavailable. The stopped requisition has not changed.</span></Notice>
		</template>

		<div class="req-rule" style="margin-bottom: var(--kt-space-4)" data-testid="req-correction-request">
			<CardTitle title="Planning correction request" icon="target" style="margin-bottom: 10px" />
			<div class="kt-meta-row">
				<div><span class="kt-label">Reference</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.reference }}</span></div>
				<div><span class="kt-label">Status</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.status }}</span></div>
				<div><span class="kt-label">Plan Item</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.plan_item }}</span></div>
			</div>
			<div class="kt-meta-row" style="margin-top: 12px"><div><span class="kt-label">Reason</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.reason }}</span></div></div>
			<div class="kt-meta-row" style="margin-top: 12px">
				<div><span class="kt-label">Requested by</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.requested_by }}</span></div>
				<div><span class="kt-label">Requested at</span><span class="kt-meta-value" style="font-size: 14px">{{ view.request.requested_at }}</span></div>
			</div>
		</div>
		<p v-if="view.request.started && !terminal && !view.unavailable" class="kt-muted" style="font-size: 13px; margin: 0 0 var(--kt-space-4)">{{ view.request.started }}.</p>
		<p v-if="view.outcome_text" class="kt-muted" style="font-size: 13px; margin: 0 0 var(--kt-space-3)" data-testid="req-outcome-text">{{ view.outcome_text }}</p>
		<p v-if="view.unchanged_notice" style="font-size: 13px; margin: 0 0 var(--kt-space-4)">{{ view.unchanged_notice }}</p>

		<DecisionChain :rows="view.correction_chain || []" label="Correction chain" style="margin-bottom: var(--kt-space-6)" />

		<ReviewSections :sections="view.sections || []" />
		<Disclosure title="Record details" testid="req-record-details">
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>

		<Notice v-if="error" tone="critical"><span data-testid="req-stopped-error">{{ error }}</span></Notice>

		<div class="req-footer">
			<div class="req-actions">
				<button type="button" class="kt-btn kt-btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
				<button v-if="actions.view_planning_request && !actions.start_new_requisition" type="button" class="kt-btn kt-btn-secondary" data-testid="req-view-planning-request" @click="ctx.goPath(view.planning_route)">View Planning request</button>
				<button v-if="actions.export" type="button" class="kt-btn kt-btn-ghost" :disabled="busy" data-testid="req-export" @click="downloadExport(ctx, view.requisition)">Export</button>
			</div>
			<div class="req-actions">
				<button v-if="actions.try_again" type="button" class="kt-btn kt-btn-secondary" data-testid="req-try-again" @click="ctx.reload()">Try again</button>
				<button v-if="actions.open_planning_task" type="button" class="kt-btn kt-btn-primary" data-testid="req-open-planning-task" @click="ctx.goPath(view.planning_route)">Open Planning correction task</button>
				<button v-if="view.fresh_start" type="button" class="kt-btn kt-btn-primary" data-testid="req-start-new" @click="dialog = true">Start a new requisition</button>
			</div>
		</div>

		<DialogFrame v-if="dialog && view.fresh_start" :title="view.fresh_start.heading" :width="480" :busy="busy" testid="req-fresh-start-dialog" @close="dialog = false">
			<p class="req-dialog-body">{{ view.fresh_start.text }}</p>
			<Notice v-if="!actions.start_new_requisition && view.fresh_start.blocked_message" tone="critical"><span data-testid="req-fresh-start-blocked">{{ view.fresh_start.blocked_message }}</span></Notice>
			<div v-if="actions.start_new_requisition" class="req-rule">
				<div class="kt-meta-row">
					<div v-for="fact in view.fresh_start.facts.slice(0, 2)" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
				</div>
				<div class="kt-meta-row" style="margin-top: 10px">
					<div v-for="fact in view.fresh_start.facts.slice(2)" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
				</div>
			</div>
			<Notice v-if="dialogError" tone="critical">{{ dialogError }}</Notice>
			<template #actions>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="dialog = false">Cancel</button>
				<button v-if="actions.start_new_requisition" type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-fresh-start-confirm" @click="startNew">Start new Draft</button>
			</template>
		</DialogFrame>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import { downloadExport } from "../data/export.js";
import CardTitle from "./shared/CardTitle.vue";
import DecisionChain from "./shared/DecisionChain.vue";
import DialogFrame from "./shared/DialogFrame.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import ReviewSections from "./shared/ReviewSections.vue";

const props = defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const actions = computed(() => props.view.actions || {});
const terminal = computed(() => ["Resolved", "Closed without change"].includes(props.view.status));
const dialog = ref(false);
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "export" ? ctx.commandError.value.message : ""));
const dialogError = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "fresh-start" ? ctx.commandError.value.message : ""));

async function startNew() {
	const result = await ctx.run("fresh-start", (key) => ctx.api.prepareAfterCorrection({ requisition: props.view.requisition, idempotency_key: key }), { noReload: true });
	if (result && result.requisition) {
		dialog.value = false;
		ctx.go(result.requisition);
	}
}
</script>
