<!-- REQ-DES-02 — Start requisition dialog (board v2 base, UNSUPPORTED,
     RULE-UNAVAILABLE, RESERVATION-UNSUPPORTED; the REQ-DES-12 purchase states
     — multi-year, existing scope, existing open — in the same frame).
     Opening it creates nothing; the server decides whether Start is allowed
     (`may_start`) and which state applies. -->
<template>
	<DialogFrame title="Start this requisition?" :width="520" :busy="ctx.pending.value" testid="req-start-dialog" @close="$emit('close')">
		<template v-if="preview.outcome !== 'OK'">
			<p class="req-dialog-body">{{ preview.outcome === "FORBIDDEN" ? preview.message : "This approved purchase is not available." }}</p>
		</template>
		<template v-else-if="preview.state === 'ready'">
			<p class="req-dialog-body">A Draft will be created from the approved purchase below.</p>
			<MetaFacts :rows="readyFacts" />
			<Notice tone="info">This release supports straightforward off-the-shelf IT equipment. It does not support software development, integration or migration.</Notice>
			<div class="kt-muted" style="font-size: 13px">{{ submitting }}</div>
		</template>
		<template v-else-if="preview.state === 'unsupported'">
			<div class="kt-meta-row"><div><span class="kt-label">Requirement product</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.requirement_product }}</span></div></div>
			<Notice tone="critical">{{ preview.message }}</Notice>
		</template>
		<template v-else-if="preview.state === 'rule_unavailable'">
			<div class="kt-meta-row"><div><span class="kt-label">Approved purchase</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.title }}</span></div></div>
			<div class="kt-meta-row" style="margin-top: 10px">
				<div><span class="kt-label">Reserved for</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.reserved_for }}</span></div>
				<div><span class="kt-label">Reservation rule</span><span class="kt-meta-value req-critical" style="font-size: 14px">Not ready</span></div>
			</div>
			<Notice tone="critical">{{ preview.message }}</Notice>
			<a v-if="preview.is_system_manager" class="kt-label" href="/app/system-setup" data-testid="req-inspect-rule" @click.stop.prevent="frappe.set_route('system-setup')">Inspect the reservation rule in System setup</a>
		</template>
		<template v-else-if="preview.state === 'reservation_unsupported'">
			<div class="kt-meta-row"><div><span class="kt-label">Approved purchase</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.title }}</span></div></div>
			<div class="kt-meta-row" style="margin-top: 10px">
				<div><span class="kt-label">Reserved for</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.reserved_for }}</span></div>
				<div><span class="kt-label">County requirement</span><span class="kt-meta-value req-critical" style="font-size: 14px">{{ preview.county_requirement || "County residents" }} · overlap not supported</span></div>
			</div>
			<Notice tone="critical">{{ preview.message }}</Notice>
		</template>
		<template v-else-if="preview.state === 'multi_year'">
			<div class="kt-meta-row"><div><span class="kt-label">Approved purchase</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.title }}</span></div></div>
			<div class="kt-meta-row" style="margin-top: 10px"><div><span class="kt-label">Plan horizon</span><span class="kt-meta-value req-critical" style="font-size: 14px">Multi-year</span></div></div>
			<Notice tone="critical">{{ preview.message }}</Notice>
			<div class="kt-label">Failed procurement check: {{ preview.failed_check }}</div>
		</template>
		<template v-else-if="preview.state === 'existing_open'">
			<div class="kt-meta-row"><div><span class="kt-label">Approved purchase</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.title }}</span></div></div>
			<Notice tone="info">This approved purchase already has an open requisition.<template v-if="preview.existing"> {{ preview.existing.summary }}</template></Notice>
		</template>
		<template v-else>
			<div class="kt-meta-row">
				<div><span class="kt-label">Approved purchase</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.title }}</span></div>
				<div><span class="kt-label">Departments</span><span class="kt-meta-value" style="font-size: 14px">{{ preview.departments }}</span></div>
			</div>
			<Notice tone="info">{{ preview.message }}</Notice>
		</template>

		<Notice v-if="error" tone="critical"><span data-testid="req-start-error">{{ error.message }}</span></Notice>

		<template #actions>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="ctx.pending.value" data-testid="req-start-cancel" @click="$emit('close')">Cancel</button>
			<button
				v-if="preview.state === 'existing_open' && preview.existing"
				type="button"
				class="kt-btn kt-btn-primary"
				data-testid="req-open-existing"
				@click="ctx.goPath(preview.existing.route)"
			>Open existing requisition</button>
			<button
				v-else
				type="button"
				class="kt-btn"
				:class="preview.may_start ? 'kt-btn-primary' : 'kt-btn-secondary'"
				:disabled="!preview.may_start || ctx.pending.value"
				data-testid="req-start-confirm"
				@click="start"
			>{{ ctx.pending.value ? "Starting…" : "Start requisition" }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import MetaFacts from "./shared/MetaFacts.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ preview: { type: Object, required: true } });
defineEmits(["close"]);
const ctx = useReq();
const frappe = window.frappe;

const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "prepare" ? ctx.commandError.value : null));

const readyFacts = computed(() => {
	const p = props.preview;
	const reserved = [{ label: "Reserved for", value: p.reserved_for }];
	if (p.county_requirement) reserved.push({ label: "County requirement", value: p.county_requirement });
	return [
		[{ label: "Approved purchase", value: p.title }],
		[{ label: "Departments", value: p.departments }],
		[{ label: "Still available", value: p.available_quantity }, { label: "", value: p.available_value }],
		[{ label: "Plan completion boundary", value: p.plan_completion_boundary }, { label: "Requirement product", value: p.requirement_product }],
		reserved,
	];
});

const submitting = computed(() =>
	props.preview.combined
		? `${props.preview.submitting_department} will submit this combined departmental request.`
		: `${props.preview.submitting_department} will submit this departmental request.`
);

async function start() {
	const result = await ctx.run(
		"prepare",
		(key) => ctx.api.prepare({ plan_item_id: props.preview.plan_item_id, idempotency_key: key }),
		{ noReload: true }
	);
	if (result && result.requisition) ctx.go(result.requisition);
}
</script>
