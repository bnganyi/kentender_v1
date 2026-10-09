<!-- REQ-DES-07 — Head of User Department review (base, return dialog,
     SUBMITTED; the REQ-DES-12 uncertain-result state in its footer). The
     question, certification and decision chain lead; the complete immutable
     Version follows as result-first sections. Only the lead HoD decides. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-department-task" :data-mode="view.mode">
		<div class="req-title-row">
			<h3>{{ view.header.title }}</h3>
			<span class="kt-status" :class="view.header.badge.tone" data-testid="req-badge">{{ view.header.badge.label }}</span>
		</div>
		<div class="kt-label req-reference">{{ view.header.reference }}</div>
		<p class="kt-muted req-lede" style="margin-top: 6px">{{ view.header.description }}</p>

		<div class="req-rule" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row">
				<div v-for="fact in view.context" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</div>
		<div v-if="decider" class="req-question" style="margin-top: calc(-1 * var(--kt-space-3))" data-testid="req-question">{{ view.question }}</div>

		<DecisionChain :rows="view.decision_chain || []" style="margin-bottom: var(--kt-space-6)" />

		<Notice v-for="(f, i) in blocking" :key="i" tone="critical">{{ f.message }}</Notice>
		<ReviewSections :sections="view.sections || []" />

		<Disclosure title="Record details" testid="req-record-details" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row req-facts" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px"><span v-for="(part, i) in String(fact.value).split('; ')" :key="i" class="req-fact-line">{{ part }}</span></span></div>
			</div>
		</Disclosure>

		<div v-if="decider" class="req-statement">
			<div class="req-statement-box"><div class="kt-label" style="margin-bottom: 4px">Certification</div>{{ view.certification }}</div>
		</div>

		<template v-if="uncertain">
			<p v-if="uncertain === 'checking'" style="font-size: 14px" data-testid="req-uncertain-checking">{{ CHECKING }}</p>
			<Notice v-else-if="uncertain === 'committed'" tone="live"><span data-testid="req-uncertain-committed">{{ committedText }}</span></Notice>
			<Notice v-else tone="warning"><span data-testid="req-uncertain-unconfirmed">{{ RETRY_SAFE }}</span></Notice>
		</template>
		<Notice v-if="error" tone="critical"><span data-testid="req-decision-error">{{ error }}</span></Notice>

		<div v-if="decider && uncertain !== 'checking' && uncertain !== 'committed'" class="req-footer">
			<button v-if="actions.request_planning_correction" type="button" class="btn btn-ghost" :disabled="busy" data-testid="req-action-planning" @click="dialog = 'planning'">Request Planning correction</button>
			<div class="req-actions">
				<ActionsMenu v-if="menu.length" :actions="menu" :disabled="busy" @choose="(k) => (dialog = k)" />
				<button v-if="actions.return_for_correction" type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-return" @click="dialog = 'return'">Return for correction</button>
				<button type="button" class="btn" :class="actions.submit_to_procurement ? 'btn-primary' : 'btn-secondary'" :disabled="busy || !actions.submit_to_procurement" data-testid="req-submit" @click="submit">
					{{ busy && acting === 'submit' ? "Submitting…" : "Submit to Procurement" }}
				</button>
			</div>
		</div>
		<div v-else-if="uncertain !== 'checking'" class="req-footer">
			<button type="button" class="btn btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
			<ActionsMenu v-if="readerMenu.length" :actions="readerMenu" :disabled="busy" @choose="(k) => (dialog = k)" />
		</div>

		<ReasonDialog
			v-if="dialog === 'return'"
			title="Return this requisition for correction?"
			reason-label="Correction required (20–1,000 characters)"
			hint="State what must change and identify the affected section."
			confirm-label="Return for correction"
			:sections="(view.catalogue || {}).affected_sections"
			:busy="busy"
			:error="dialogError('return')"
			testid="req-return-dialog"
			@close="dialog = null"
			@confirm="returnForCorrection"
		/>
		<ReasonDialog
			v-if="dialog === 'withdraw'"
			v-bind="WITHDRAW"
			:busy="busy"
			:error="dialogError('withdraw')"
			@close="dialog = null"
			@confirm="withdraw"
		/>
		<ReasonDialog
			v-if="dialog === 'planning'"
			v-bind="PLANNING_CORRECTION"
			:busy="busy"
			:error="dialogError('planning')"
			@close="dialog = null"
			@confirm="requestPlanning"
		/>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import { PLANNING_CORRECTION, WITHDRAW } from "../data/dialogs.js";
import { CHECKING, RETRY_SAFE, useDecision } from "../data/decision.js";
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
const decider = computed(() => props.view.mode === "decider");
const blocking = computed(() => (props.view.findings || []).filter((f) => f.severity === "Blocking"));
const menu = computed(() => (actions.value.withdraw ? [{ key: "withdraw", label: "Withdraw requisition" }] : []));
// After submission the lead HoD keeps these two quiet actions (REQ-DES-07-SUBMITTED).
const readerMenu = computed(() => [
	...(actions.value.request_planning_correction ? [{ key: "planning", label: "Request Planning correction" }] : []),
	...(actions.value.withdraw ? [{ key: "withdraw", label: "Withdraw requisition" }] : []),
]);

const dialog = ref(null);
const acting = ref("");
const { uncertain, committedText, decide } = useDecision(ctx);
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "submit" ? ctx.commandError.value.message : ""));
function dialogError(label) {
	return ctx.commandError.value && ctx.commandError.value.label === label ? ctx.commandError.value.message : "";
}
const taskClosed = () => (props.view.task || {}).status !== "Open";

async function submit() {
	acting.value = "submit";
	await decide(
		"submit",
		(key) => ctx.api.submitToProcurement({ requisition: props.view.requisition, task: props.view.task.task, expected_record_version: props.view.root_record_version, idempotency_key: key }),
		{ committed: taskClosed, text: "Requisition submitted to Procurement" }
	);
	acting.value = "";
}
async function returnForCorrection({ reason, affected_section }) {
	const done = await decide(
		"return",
		(key) => ctx.api.returnToAuthor({ task: props.view.task.task, reason, affected_section, expected_record_version: props.view.task.record_version, idempotency_key: key }),
		{ committed: taskClosed, text: "Requisition returned for correction" }
	);
	if (done || uncertain.value) dialog.value = null;
}
async function withdraw({ reason }) {
	const done = await ctx.run("withdraw", (key) => ctx.api.withdraw({ requisition: props.view.requisition, reason, expected_record_version: props.view.root_record_version, idempotency_key: key }));
	if (done) dialog.value = null;
}
async function requestPlanning({ reason }) {
	const done = await ctx.run("planning", (key) => ctx.api.requestPlanningCorrection({ requisition: props.view.requisition, reason, expected_record_version: props.view.root_record_version, idempotency_key: key }));
	if (done) dialog.value = null;
}
</script>
