<!-- The result-first review composition (REQ-DES-06/07/08, §13.7): each
     section of the complete Version, in order. A section with an exception
     starts open; the rest start closed with a plain summary and Show details.
     Disclosure is presentation only — every section is in the payload. -->
<template>
	<div data-testid="req-review-sections">
		<template v-for="section in sections" :key="section.key">
			<div v-if="section.compact" class="req-compact-row" :data-testid="`req-review-${section.key}`">
				<span class="kt-label">{{ section.title }}</span><span class="kt-muted" style="font-size: 13px">{{ section.empty_text || section.summary }}</span>
			</div>
			<div v-else class="req-review-section" :data-testid="`req-review-${section.key}`" :data-open="isOpen(section) ? 'true' : 'false'">
				<div v-if="isOpen(section)" class="req-review-head">
					<CardTitle :title="section.title" :icon="section.icon" style="margin: 0" />
					<button type="button" class="req-review-toggle" :aria-expanded="'true'" @click="toggle(section)">Hide details</button>
				</div>
				<div v-else class="req-review-head">
					<div>
						<CardTitle :title="section.title" :icon="section.icon" style="margin: 0" />
						<p class="kt-muted req-review-summary">{{ section.summary }}</p>
					</div>
					<button type="button" class="req-review-toggle" :aria-expanded="'false'" :data-testid="`req-review-show-${section.key}`" @click="toggle(section)">Show details</button>
				</div>
				<template v-if="isOpen(section)">
					<p style="font-size: 14px; margin: 6px 0 12px">{{ section.summary }}</p>
					<Notice v-for="(issue, i) in bodyIssues(section)" :key="i" :tone="issue.severity === 'Blocking' ? 'critical' : 'warning'">{{ issue.message }}</Notice>

					<template v-if="section.key === 'purpose'">
						<div class="kt-meta-row">
							<div v-for="fact in section.facts" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
						</div>
						<div v-for="fact in section.narrative" :key="fact.label" class="kt-meta-row" style="margin-top: 12px">
							<div><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
						</div>
					</template>

					<table v-else-if="section.key === 'amounts'" class="kt-table">
						<thead><tr><th>Department and requirement</th><th class="is-num">Requested quantity</th><th class="is-num">Requested value</th></tr></thead>
						<tbody>
							<tr v-for="row in section.rows" :key="row.drawdown_line_id"><td><div style="font-weight: 600">{{ row.department }}</div><div class="kt-label">{{ row.requirement }}</div></td><td class="is-num">{{ row.requested_quantity }}</td><td class="is-num">{{ row.requested_value }}</td></tr>
							<tr><td style="font-weight: 600">Total</td><td class="is-num" style="font-weight: 600">{{ section.total_quantity }}</td><td class="is-num" style="font-weight: 600">{{ section.total_value }}</td></tr>
						</tbody>
					</table>

					<table v-else-if="section.key === 'equipment'" class="kt-table" style="font-size: 13px">
						<thead><tr><th>Item</th><th>Approved requirement</th><th class="is-num">Quantity</th><th>Intended use</th><th>Delivery</th></tr></thead>
						<tbody>
							<tr v-for="item in section.rows" :key="item.requisition_item_id"><td>{{ item.item_name }}</td><td>{{ item.approved_requirement }}</td><td class="is-num">{{ item.quantity }}</td><td>{{ item.intended_use }}</td><td>{{ item.delivery }}</td></tr>
						</tbody>
					</table>

					<template v-else-if="section.key === 'requirements'">
						<template v-for="group in section.groups" :key="group.group">
							<div class="kt-label req-group-label">{{ group.group }}</div>
							<table class="kt-table" style="margin-bottom: var(--kt-space-4)">
								<thead><tr><th>Requirement</th><th>Minimum or required value</th><th>Unit</th></tr></thead>
								<tbody>
									<tr v-for="row in group.rows" :key="row.technical_requirement_id"><td>{{ row.label }}<div class="kt-muted req-comparison">{{ row.comparison }}</div></td><td>{{ row.display }}</td><td>{{ row.unit }}</td></tr>
								</tbody>
							</table>
						</template>
						<div v-for="(pair, i) in supportRows(section.support)" :key="i" class="kt-meta-row" :style="i ? 'margin-top: 12px' : ''">
							<div v-for="fact in pair" :key="fact.field"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
						</div>
					</template>

					<table v-else-if="section.key === 'services'" class="kt-table">
						<thead><tr><th>Service</th><th>Applies to</th><th>Required result</th><th>Quantity or coverage</th><th>Completion</th></tr></thead>
						<tbody>
							<tr v-for="s in section.rows" :key="s.service_requirement_id"><td>{{ s.service_type }}</td><td>{{ s.applies_to }}</td><td>{{ s.required_result }}</td><td>{{ s.quantity_or_coverage }}</td><td>{{ s.completion_date_label }}</td></tr>
						</tbody>
					</table>

					<table v-else-if="section.key === 'acceptance'" class="kt-table">
						<thead><tr><th>Check</th><th>Applies to</th><th>Pass condition</th><th>Evidence</th></tr></thead>
						<tbody>
							<tr v-for="row in section.rows" :key="row.acceptance_requirement_id"><td>{{ row.check_type }}</td><td>{{ row.applies_to }}</td><td>{{ row.pass_condition }}</td><td>{{ row.evidence }}</td></tr>
						</tbody>
					</table>

					<table v-else-if="section.key === 'supporting_materials'" class="kt-table">
						<thead><tr><th>Title</th><th>Type</th><th>Treatment</th><th>Version</th></tr></thead>
						<tbody>
							<tr v-for="m in section.rows" :key="m.supporting_material_id"><td>{{ m.title }}</td><td>{{ m.document_type }}</td><td>{{ m.treatment }}</td><td>{{ m.document_version }}</td></tr>
						</tbody>
					</table>
				</template>
			</div>
		</template>
	</div>
</template>

<script setup>
import { reactive } from "vue";
import CardTitle from "./CardTitle.vue";
import Notice from "./Notice.vue";

const props = defineProps({
	sections: { type: Array, required: true },
	// Findings shown above the sections already (the date warning) are not repeated inside.
	shownAbove: { type: Array, default: () => [] },
});
const state = reactive({});
const isOpen = (section) => (section.key in state ? state[section.key] : !!section.open);
function toggle(section) {
	state[section.key] = !isOpen(section);
}
function bodyIssues(section) {
	return (section.issues || []).filter((i) => !props.shownAbove.includes(i.code));
}
function supportRows(rows) {
	const out = [];
	for (let i = 0; i < (rows || []).length; i += 3) out.push(rows.slice(i, i + 3));
	return out;
}
</script>
