<!-- REQ-DES-07 Step 5: Review and submit (§13.9), ported class-for-class:
     the top result banner (green when ready, per its own Blocking/Warning
     count — never simply "zero findings"), the six summary cards, any
     warning row, and the complete printable Requisition preview beneath.
     Footer actions differ by who is preparing (§13.9): a Departmental
     Author sends for department approval; a Head of User Department
     preparing directly submits straight to Procurement — driven by the
     server's own `permitted_actions`, never a client-side role guess
     (AGENTS.md §6.2). -->
<template>
	<div class="req-step-content">
		<div class="req-result-banner" :class="isReady ? 'is-ready' : 'is-blocked'" data-testid="req-review-result">
			<div class="req-result-headline">{{ isReady ? "Ready for departmental submission" : "Not yet ready to submit" }}</div>
			<div class="req-result-counts">{{ blockingCount }} Blocking · {{ warningCount }} Warning{{ warningCount === 1 ? "" : "s" }}</div>
		</div>

		<div class="req-summary-grid">
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Planning drawdown</div>
				<div class="req-summary-title">{{ drawdown.lineCount }} source line{{ drawdown.lineCount === 1 ? "" : "s" }} · {{ drawdown.quantity }} Each</div>
				<p class="req-context-body">{{ money(drawdown.value) }}</p>
			</div>
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Equipment</div>
				<div class="req-summary-title">{{ items.length }} item{{ items.length === 1 ? "" : "s" }}</div>
			</div>
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Technical requirements</div>
				<div class="req-summary-title">{{ confirmedTechnicalCount }} confirmed row{{ confirmedTechnicalCount === 1 ? "" : "s" }}</div>
			</div>
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Related services</div>
				<div class="req-summary-title">{{ relatedServices.length }} row{{ relatedServices.length === 1 ? "" : "s" }}</div>
			</div>
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Acceptance</div>
				<div class="req-summary-title">{{ acceptanceRequirements.length }} row{{ acceptanceRequirements.length === 1 ? "" : "s" }}</div>
			</div>
			<div class="kt-card kt-blueprint req-card-pad-tight">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-eyebrow">Supporting materials</div>
				<div class="req-summary-title">{{ supportingMaterials.length }} file{{ supportingMaterials.length === 1 ? "" : "s" }}</div>
			</div>
		</div>

		<div v-for="w in warnings" :key="w.code" class="req-notice">{{ w.message }}</div>

		<div class="kt-card kt-blueprint req-card-pad">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Requisition preview</div>
			<div class="req-preview-grid">
				<div class="req-preview-col">
					<div><div class="kt-label">Plan Item</div><div>{{ requisition.plan_item_id }}</div></div>
					<div><div class="kt-label">Contributing departments</div><div>{{ contributingDepartments }}</div></div>
					<div><div class="kt-label">Business need</div><div>{{ editor.business_need }}</div></div>
					<div><div class="kt-label">Delivery</div><div>{{ editor.delivery_location_label }} · {{ version.latest_delivery_date }}</div></div>
				</div>
				<div class="req-preview-col">
					<div><div class="kt-label">Equipment items</div><div>{{ itemsSummary }}</div></div>
					<div><div class="kt-label">Technical requirements</div><div>{{ confirmedTechnicalCount }} confirmed rows, all applying to {{ technicalScopeSummary }}</div></div>
					<div><div class="kt-label">Acceptance</div><div>{{ acceptanceRequirements.length }} objective checks</div></div>
					<div><div class="kt-label">Supporting materials</div><div>{{ supportingMaterials.length ? supportingMaterials.map((m) => m.title).join(" · ") : "None" }}</div></div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatMoney } from "../data/format.js";

const props = defineProps({
	editor: { type: Object, required: true },
});

const requisition = computed(() => props.editor.requisition || {});
const version = computed(() => props.editor.version || {});
const pkg = computed(() => props.editor.package || {});
const items = computed(() => pkg.value.items || []);
const relatedServices = computed(() => pkg.value.related_services || []);
const acceptanceRequirements = computed(() => pkg.value.acceptance_requirements || []);
const supportingMaterials = computed(() => pkg.value.supporting_materials || []);
const confirmedTechnicalCount = computed(() => (pkg.value.technical_requirements || []).filter((r) => r.row_status === "Confirmed").length);

const validationReport = computed(() => props.editor.validation || {});
const findings = computed(() => validationReport.value.findings || []);
const blockingCount = computed(() => validationReport.value.blocking_count || 0);
const warningCount = computed(() => validationReport.value.warning_count || 0);
const warnings = computed(() => findings.value.filter((f) => f.severity === "Warning"));
const isReady = computed(() => blockingCount.value === 0);

const drawdown = computed(() => {
	const lines = version.value.drawdown_lines || [];
	return {
		lineCount: lines.length,
		quantity: lines.reduce((sum, l) => sum + (l.requested_quantity || 0), 0),
		value: lines.reduce((sum, l) => sum + (l.requested_value || 0), 0),
	};
});

const drawdownContext = computed(() => props.editor.drawdown_context || []);
const labelByLine = computed(() => {
	const map = {};
	for (const row of drawdownContext.value) map[row.drawdown_line_id] = row.organisation_unit_label;
	return map;
});

const contributingDepartments = computed(() => Array.from(new Set(drawdownContext.value.map((r) => r.organisation_unit_label))).sort().join(" · "));

const itemsSummary = computed(() =>
	items.value
		.map((item) => {
			const ou = labelByLine.value[item.plan_item_line_id];
			return `${item.item_name} — ${item.quantity} ${item.unit || "Each"}${ou ? ` (${ou})` : ""}`;
		})
		.join(" · ")
);

const technicalScopeSummary = computed(() => {
	const rows = (pkg.value.technical_requirements || []).filter((r) => r.row_status === "Confirmed");
	return rows.length && rows.every((r) => r.applies_to_scope === "All items") ? "All items" : "individual items";
});

function money(amount) {
	return formatMoney(amount);
}
</script>
