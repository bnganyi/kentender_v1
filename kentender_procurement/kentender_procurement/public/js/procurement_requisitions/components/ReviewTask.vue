<!-- REQ-DES-06 — Draft: Review and submit (base, DIRECT-HOD, withdraw
     dialog). The result leads: ready or blocked, the delivery-date warning and
     the three dates, then the complete Version as result-first sections. Who
     may send or submit is the server's `actions`. -->
<template>
	<div data-testid="req-body-review_submit">
		<Notice v-if="review.result" tone="live"><strong data-testid="req-review-result">{{ review.result }}</strong></Notice>
		<AttentionPanel :items="attention" @go="(task) => $emit('select', task)" />
		<div class="req-rule" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row">
				<div v-for="d in review.dates || []" :key="d.label"><span class="kt-label">{{ d.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ d.value }}</span></div>
			</div>
		</div>

		<ReviewSections :sections="review.sections || []" :list-issues="false" />

		<Disclosure title="Record details" testid="req-record-details" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>


		<div class="req-footer">
			<div class="req-actions">
				<button type="button" class="btn btn-ghost" @click="$emit('select', 'requirements')">Back to requirements</button>
				<ActionsMenu v-if="menu.length" :actions="menu" :disabled="busy" @choose="(k) => (dialog = k)" />
			</div>
			<div v-if="actions.save" class="req-footer-right">
				<span v-if="footerStatus" class="req-footer-status" :data-state="footerStatus.state" data-testid="req-footer-status" role="status">{{ footerStatus.text }}</span>
				<div class="req-actions">
					<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-save" @click="confirmSaved">Save draft</button>
					<button
						v-if="primaryLabel"
						type="button"
						class="btn"
						:class="ready ? 'btn-primary' : 'btn-secondary'"
						:disabled="busy || !ready"
						data-testid="req-send"
						@click="send"
					>{{ busy && sending ? "Sending…" : primaryLabel }}</button>
				</div>
			</div>
		</div>

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
import ActionsMenu from "./shared/ActionsMenu.vue";
import AttentionPanel from "./shared/AttentionPanel.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import ReasonDialog from "./shared/ReasonDialog.vue";
import ReviewSections from "./shared/ReviewSections.vue";

const props = defineProps({ view: { type: Object, required: true } });
defineEmits(["select"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const review = computed(() => props.view.review || {});
const actions = computed(() => props.view.actions || {});
const ready = computed(() => !!review.value.result);
const blocking = computed(() => (props.view.findings || []).filter((f) => f.severity === "Blocking"));
// Everything that needs attention, said once (v1.17 §13.4A): a refused send first, then each blocking
// finding (choosing it goes to the task that fixes it), then the advisories that do not block.
const attention = computed(() => {
	const out = [];
	if (error.value) out.push({ message: error.value });
	if (!review.value.result) {
		for (const f of blocking.value) if (!out.some((i) => i.message === f.message)) out.push({ message: f.message, go: f.task });
	}
	for (const w of review.value.warnings || []) if (!out.some((i) => i.message === w.message)) out.push({ message: w.message, advisory: true });
	return out;
});
const footerStatus = computed(() => {
	if (saved.value) return { state: "saved", text: "Your draft is saved." };
	if (primaryLabel.value && !ready.value) return { state: "blocked", text: "Fix what needs attention above to submit." };
	return null;
});

const primaryLabel = computed(() => {
	if (actions.value.submit_to_procurement) return "Submit to Procurement";
	if (actions.value.send_for_department_approval) return "Send for department approval";
	return "";
});
const menu = computed(() => {
	const out = [];
	if (actions.value.request_planning_correction) out.push({ key: "planning", label: "Request Planning correction" });
	if (actions.value.withdraw) out.push({ key: "withdraw", label: "Withdraw requisition" });
	return out;
});

const dialog = ref(null);
const sending = ref(false);
// Every edit is saved by its own command; on this task Save draft confirms
// that against the server rather than pretending to write anything.
const saved = ref(false);
async function confirmSaved() {
	saved.value = false;
	await ctx.reload();
	saved.value = true;
}
const LABELS = { send: "send", withdraw: "withdraw", planning: "planning" };
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "send" ? ctx.commandError.value.message : ""));
function dialogError(label) {
	return ctx.commandError.value && ctx.commandError.value.label === LABELS[label] ? ctx.commandError.value.message : "";
}

const base = () => ({ requisition: props.view.header.requisition, expected_record_version: props.view.header.record_version });
async function send() {
	sending.value = true;
	const call = actions.value.submit_to_procurement ? ctx.api.submitToProcurement : ctx.api.sendForDepartmentApproval;
	await ctx.run("send", (key) => call({ ...base(), idempotency_key: key }));
	sending.value = false;
}
async function withdraw({ reason }) {
	const done = await ctx.run("withdraw", (key) => ctx.api.withdraw({ ...base(), reason, idempotency_key: key }));
	if (done) dialog.value = null;
}
async function requestPlanning({ reason }) {
	const done = await ctx.run("planning", (key) => ctx.api.requestPlanningCorrection({ ...base(), reason, idempotency_key: key }));
	if (done) dialog.value = null;
}
</script>
