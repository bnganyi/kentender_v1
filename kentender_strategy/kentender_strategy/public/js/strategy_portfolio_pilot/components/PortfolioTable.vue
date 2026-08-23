<script setup>
import StatusTag from "./StatusTag.vue";

const props = defineProps({
	rows: { type: Array, required: true },
	countLabel: { type: String, required: true },
	loading: { type: Boolean, default: false },
	isServerEmpty: { type: Boolean, default: false }, // zero plans returned at all, distinct from filtered-to-zero
});
defineEmits(["clear-filters", "open-plan"]);
</script>

<template>
	<section class="kt-pp-panel">
		<div class="kt-pp-panel__head">
			<h2>Strategy portfolio</h2>
			<span class="kt-pp-panel__count">{{ countLabel }}</span>
		</div>

		<div v-if="loading" class="kt-pp-loading">Loading strategy portfolio…</div>

		<table v-else-if="rows.length" class="kt-pp-table">
			<thead>
				<tr>
					<th style="width: 32%">Plan</th>
					<th style="width: 13%">Type</th>
					<th style="width: 16%">Effective period</th>
					<th style="width: 6%">Version</th>
					<th style="width: 10%">Status</th>
					<th style="width: 16%">Current attention</th>
					<th style="width: 7%; text-align: right">Action</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="plan in rows" :key="plan.code">
					<td>
						<div class="kt-pp-table__code">{{ plan.code }}</div>
						<div class="kt-pp-table__title">{{ plan.title }}</div>
					</td>
					<td class="kt-pp-table__muted">{{ plan.type }}</td>
					<td class="kt-pp-table__nowrap">{{ plan.period }}</td>
					<td>{{ plan.version }}</td>
					<td><StatusTag :status="plan.status" :tone="plan.statusTone" /></td>
					<td :class="{ 'kt-pp-table__muted': plan.attentionMuted }">
						{{ plan.attention }}
					</td>
					<td class="kt-pp-table__action">
						<button
							type="button"
							class="kt-pp-link-btn"
							data-testid="kt-pp-open-plan"
							@click="$emit('open-plan', plan.code)"
						>
							{{ plan.status === "Draft" ? "Open" : "View" }}
						</button>
					</td>
				</tr>
			</tbody>
		</table>

		<div v-else class="kt-pp-empty">
			<p v-if="isServerEmpty">No strategic plans are available to you yet.</p>
			<p v-else>No strategic plans match these filters.</p>
			<button
				v-if="!isServerEmpty"
				type="button"
				class="kt-pp-btn kt-pp-btn--secondary"
				@click="$emit('clear-filters')"
			>
				Clear filters
			</button>
		</div>
	</section>
</template>

<style scoped>
.kt-pp-panel {
	border: 1px solid var(--ktpp-color-divider);
}
.kt-pp-panel__head {
	display: flex;
	align-items: baseline;
	gap: 10px;
	padding: 12px 17px;
	border-bottom: 1px solid var(--ktpp-color-divider);
}
.kt-pp-panel__head h2 {
	font-size: 19px;
}
.kt-pp-panel__count {
	font-size: 12px;
	color: color-mix(in srgb, var(--ktpp-color-text) 55%, transparent);
}
.kt-pp-table {
	width: 100%;
	border-collapse: collapse;
	font-size: 14px;
}
.kt-pp-table th {
	text-align: left;
	font-size: 11px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--ktpp-color-text) 60%, transparent);
	padding: 11px 17px;
	border-bottom: 1px solid var(--ktpp-color-divider);
}
.kt-pp-table td {
	padding: 11px 17px;
	border-bottom: 1px solid color-mix(in srgb, var(--ktpp-color-text) 8%, transparent);
}
.kt-pp-table tbody tr:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 4%, transparent);
}
.kt-pp-table__code {
	font-family: var(--ktpp-font-heading);
	font-size: 12px;
	letter-spacing: 0.08em;
	color: var(--ktpp-color-accent-700);
}
.kt-pp-table__title {
	font-size: 14.5px;
	line-height: 1.3;
}
.kt-pp-table__muted {
	color: color-mix(in srgb, var(--ktpp-color-text) 75%, transparent);
}
.kt-pp-table__nowrap {
	font-variant-numeric: tabular-nums;
	white-space: nowrap;
}
.kt-pp-table__action {
	text-align: right;
}
.kt-pp-link-btn {
	background: none;
	border: 0;
	padding: 0;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-size: 14px;
	color: var(--ktpp-color-text);
}
.kt-pp-loading {
	padding: 54px 17px 58px;
	text-align: center;
	font-size: 14px;
	color: color-mix(in srgb, var(--ktpp-color-text) 60%, transparent);
}
.kt-pp-empty {
	padding: 54px 17px 58px;
	text-align: center;
}
.kt-pp-empty p {
	margin: 0 0 14px;
	font-family: var(--ktpp-font-heading);
	font-size: 19px;
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	padding: 7px 12px;
	border-radius: var(--ktpp-radius-md);
}
.kt-pp-btn--secondary {
	border: 1px solid var(--ktpp-color-divider);
	background: transparent;
	color: var(--ktpp-color-text);
}
.kt-pp-btn--secondary:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 7%, transparent);
}
</style>
