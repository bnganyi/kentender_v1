<!-- REQ-DES-10 — Authorised requisition (Procurement Officer base, HOPF,
     Consumed, Revoked, Auditor, revocation dialog; the REQ-DES-12
     revocation/consumption race). Which controls appear is the server's
     `actions` for this actor and state. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-authorised" :data-mode="view.mode" :data-state="view.state">
		<div class="req-authorised-head">
			<div>
				<div class="req-title-row">
					<h3>{{ view.header.title }}</h3>
					<span v-if="!view.consumed" class="kt-status" :class="view.header.badge.tone" data-testid="req-badge">{{ view.header.badge.label }}</span>
				</div>
				<div class="req-reference req-actions" style="align-items: center"><span class="kt-label">{{ view.header.reference }}</span><span class="kt-muted" style="font-size: 13px">{{ view.header.tagline }}</span></div>
				<p v-if="view.header.description" class="kt-muted" style="font-size: 13px; margin: 10px 0 0">{{ view.header.description }}</p>
			</div>
			<button v-if="actions.continue_to_tender_preparation" type="button" class="btn btn-primary" style="white-space: nowrap" data-testid="req-continue-tender" @click="ctx.goPath(view.tender_route)">Continue to Tender Preparation</button>
		</div>

		<template v-if="view.consumed">
			<Notice tone="live"><span data-testid="req-consumed"><strong>Tender Preparation started</strong> · {{ view.consumed.tender_reference }}</span></Notice>
			<div class="req-actions" style="justify-content: flex-end; margin-top: var(--kt-space-4)">
				<button type="button" class="btn btn-primary" data-testid="req-open-tender" @click="ctx.goPath(view.consumed.route)">Open Tender</button>
			</div>
		</template>
		<template v-if="race">
			<Notice tone="warning"><span data-testid="req-revoke-race">Tender Preparation has already started. This authorisation can no longer be revoked.</span></Notice>
		</template>

		<div class="req-rule" style="margin: var(--kt-space-4) 0 var(--kt-space-6)">
			<div class="kt-meta-row">
				<div v-for="fact in view.facts" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</div>

		<div v-if="view.revoked" class="req-rule" style="margin-bottom: var(--kt-space-6)" data-testid="req-revoked">
			<div class="kt-meta-row">
				<div><span class="kt-label">Reason</span><span class="kt-meta-value" style="font-size: 14px">{{ view.revoked.reason }}</span></div>
				<div><span class="kt-label">Revoked by</span><span class="kt-meta-value" style="font-size: 14px">{{ view.revoked.by }} · {{ view.revoked.at }}</span></div>
			</div>
			<div class="kt-meta-row" style="margin-top: 12px">
				<div><span class="kt-label">Planning reversal</span><span class="kt-meta-value" style="font-size: 14px">{{ view.revoked.planning_reversal }}</span></div>
				<div><span class="kt-label">Funding releases</span><span class="kt-meta-value" style="font-size: 14px">{{ view.revoked.funding_releases }}</span></div>
			</div>
		</div>

		<DecisionChain :rows="view.decision_chain || []" style="margin-bottom: var(--kt-space-6)" />

		<ReviewSections :sections="leading" />
		<section v-if="(view.reservations || []).length" style="margin: var(--kt-space-3) 0 var(--kt-space-6)">
			<CardTitle title="Funding reservations" icon="wallet" />
			<table class="table" data-testid="req-reservations">
				<thead><tr><th>Funding reservation (financial hold)</th><th>Department</th><th class="is-num">Value</th></tr></thead>
				<tbody><tr v-for="r in view.reservations" :key="r.reservation"><td>{{ r.reservation }}</td><td>{{ r.department }}</td><td class="is-num">{{ r.value }}</td></tr></tbody>
			</table>
		</section>
		<ReviewSections :sections="trailing" />

		<Disclosure title="Record details" testid="req-record-details">
			<p class="kt-muted" style="font-size: 12px; margin: 0 0 12px">Each value below is supporting evidence; none is an editable command key.</p>
			<div class="kt-meta-row" style="flex-wrap: wrap">
				<div v-for="fact in view.record_details || []" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
			</div>
		</Disclosure>

		<Notice v-if="error" tone="critical"><span data-testid="req-authorised-error">{{ error }}</span></Notice>

		<div class="req-footer">
			<button type="button" class="btn btn-ghost" data-testid="req-back" @click="ctx.go()">Back to Requisitions</button>
			<div class="req-actions">
				<button v-if="actions.export" type="button" class="btn btn-ghost" :disabled="busy" data-testid="req-export" @click="downloadExport(ctx, view.requisition, view.header.version)">Export</button>
				<button v-if="actions.revoke && !race" type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-revoke" @click="dialog = 'revoke'">Revoke authorisation</button>
				<button v-if="actions.start_corrected_draft" type="button" class="btn btn-primary" :disabled="busy" data-testid="req-start-corrected" @click="startCorrected">Start corrected Draft</button>
			</div>
		</div>

		<ReasonDialog
			v-if="dialog === 'revoke'"
			title="Revoke this authorisation?"
			confirm-label="Revoke authorisation"
			:body-text="`The approved-plan amounts and ${reservationWords} will be reversed. The authorised requisition will remain in history.`"
			danger
			:busy="busy"
			:error="dialogError"
			testid="req-revoke-dialog"
			@close="dialog = null"
			@confirm="revoke"
		/>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useReq } from "../data/context.js";
import { downloadExport } from "../data/export.js";
import CardTitle from "./shared/CardTitle.vue";
import DecisionChain from "./shared/DecisionChain.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import ReasonDialog from "./shared/ReasonDialog.vue";
import ReviewSections from "./shared/ReviewSections.vue";

const props = defineProps({ view: { type: Object, required: true } });
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const actions = computed(() => props.view.actions || {});

// Funding reservations sit after Amounts requested (REQ-DES-10 note).
const split = computed(() => {
	const sections = props.view.sections || [];
	const at = sections.findIndex((s) => s.key === "amounts");
	return at < 0 ? [sections, []] : [sections.slice(0, at + 1), sections.slice(at + 1)];
});
const leading = computed(() => split.value[0]);
const trailing = computed(() => split.value[1]);
const reservationWords = computed(() => {
	const n = (props.view.reservations || []).length;
	return n === 2 ? "both funding reservations" : n === 1 ? "the funding reservation" : `all ${n} funding reservations`;
});

const dialog = ref(null);
const race = ref(false);
const error = computed(() => {
	const e = ctx.commandError.value;
	return e && (e.label === "corrected" || e.label === "export") ? e.message : "";
});
const dialogError = computed(() => {
	const e = ctx.commandError.value;
	return e && e.label === "revoke" && e.code !== "REQ_HANDOFF_CONSUMED" ? e.message : "";
});

async function revoke({ reason }) {
	race.value = false;
	const done = await ctx.run("revoke", (key) => ctx.api.revoke({ requisition: props.view.requisition, reason, expected_record_version: props.view.root_record_version, idempotency_key: key }));
	if (done) {
		dialog.value = null;
		return;
	}
	// Revocation lost the race to Tender Preparation (REQ-DES-12): say so and
	// show the consumed state; no funding release and no retry.
	if (ctx.commandError.value && ctx.commandError.value.code === "REQ_HANDOFF_CONSUMED") {
		dialog.value = null;
		race.value = true;
		ctx.clearError();
		await ctx.reload();
	}
}
async function startCorrected() {
	await ctx.run("corrected", (key) => ctx.api.createCorrectionDraft({ requisition: props.view.requisition, expected_record_version: props.view.root_record_version, idempotency_key: key }));
}
</script>
