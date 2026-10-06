<!-- REQ-DES-06 — Draft: Review and submit (base, DIRECT-HOD, withdraw
     dialog). The result leads: ready or blocked, the delivery-date warning and
     the three dates, then the complete Version as result-first sections. Who
     may send or submit is the server's `actions`. -->
<template>
	<div data-testid="req-body-review_submit">
		<Notice v-if="review.result" tone="live"><strong data-testid="req-review-result">{{ review.result }}</strong></Notice>
		<template v-else>
			<Notice v-for="(f, i) in blocking" :key="i" tone="critical">
				<a href="#" data-testid="req-review-blocker" @click.stop.prevent="$emit('select', f.task)">{{ f.message }}</a>
			</Notice>
		</template>
		<Notice v-for="(w, i) in review.warnings || []" :key="`w${i}`" tone="warning"><span data-testid="req-review-warning">{{ w.message }}</span></Notice>
		<div class="req-rule" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row">
				<div v-for="d in review.dates || []" :key="d.label"><span class="kt-label">{{ d.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ d.value }}</span></div>
			</div>
		</div>

		<ReviewSections :sections="review.sections || []" :shown-above="['DATE_AFTER_ESTIMATE']" />

		<Disclosure title="Record details" testid="req-record-details" style="margin-bottom: var(--kt-space-6)">
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>

		<Notice v-if="error" tone="critical"><span data-testid="req-review-error">{{ error }}</span></Notice>
		<Notice v-if="saved" tone="live"><span data-testid="req-saved">Your draft is saved.</span></Notice>

		<div class="req-footer">
			<div class="req-actions">
				<button type="button" class="btn btn-ghost" @click="$emit('select', 'requirements')">Back to requirements</button>
				<ActionsMenu v-if="menu.length" :actions="menu" :disabled="busy" @choose="(k) => (dialog = k)" />
			</div>
			<div v-if="actions.save" class="req-footer-right">
				<span v-if="primaryLabel && !ready" class="kt-label" data-testid="req-footer-hint">{{ (view.footer_hints || {}).review_submit || (blocking[0] || {}).message || "" }}</span>
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
