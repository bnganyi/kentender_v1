<template>
	<!-- The plan-level Reservation allocation block, ported from the boards
	     (U07 base/ready: Artboards-U07-U08 "Reservation allocation"; U11 and
	     U21: inside "Review Plan checks"). The result comes first — what
	     remains, what is required, what qualifies — then the working behind
	     it: what the target is a share of, under which exact Plan and rule
	     Versions, and each purchase with whether and why it counts. Stated
	     once at plan level, never repeated on a purchase (PLN v1.25). -->
	<div data-testid="reservation-allocation">
		<div :style="collapsible ? 'margin-top: var(--kt-space-5)' : ''">
			<div style="display: flex; align-items: baseline; gap: var(--kt-space-4); flex-wrap: wrap; margin-bottom: var(--kt-space-3)">
				<span style="font-family: var(--font-heading); font-size: 17px">Reservation allocation</span>
				<span class="kt-status" :class="`is-${block.status_kind}`" data-testid="reservation-status">{{ block.status_label }}</span>
			</div>
			<div class="kt-meta-row" style="max-width: 1000px" data-testid="reservation-result">
				<div><span class="kt-label">Remaining allocation</span><span class="kt-meta-value">{{ block.remaining_display }}</span></div>
				<div><span class="kt-label">Required allocation</span><span class="kt-meta-value">{{ block.required_display }}</span></div>
				<div><span class="kt-label">Planned qualifying allocation</span><span class="kt-meta-value">{{ block.qualifying_display }}</span></div>
				<div v-if="block.share_display"><span class="kt-label">Qualifying share</span><span class="kt-meta-value">{{ block.share_display }}</span></div>
			</div>
		</div>
		<!-- U07 hides the working under its own disclosure; U11/U21 are
		     already inside "Review Plan checks" and show it inline. -->
		<component
			:is="collapsible ? 'details' : 'div'"
			:class="{ 'kt-disclosure': collapsible }"
			:style="collapsible ? 'margin-top: var(--kt-space-4)' : 'margin-top: var(--kt-space-5)'"
			data-testid="reservation-details"
		>
			<summary v-if="collapsible" class="kt-disclosure-head">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Reservation allocation details</span></div>
				<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
			</summary>
			<div :class="{ 'kt-disclosure-body': collapsible }">
				<div class="kt-meta-row" style="margin-bottom: var(--kt-space-4)" data-testid="reservation-basis">
					<div><span class="kt-label">Eligible planned procurement</span><span style="font-size: 14px">{{ block.eligible_display }}</span></div>
					<div><span class="kt-label">Target</span><span style="font-size: 14px">{{ block.target_display }}</span></div>
					<div><span class="kt-label">Required allocation</span><span style="font-size: 14px">{{ block.required_display }}</span></div>
					<div><span class="kt-label">Planned qualifying allocation</span><span style="font-size: 14px">{{ block.qualifying_display }}</span></div>
					<div><span class="kt-label">Remaining allocation</span><span style="font-size: 14px">{{ block.remaining_display }}</span></div>
					<div v-if="block.share_display"><span class="kt-label">Qualifying share</span><span style="font-size: 14px">{{ block.share_display }}</span></div>
				</div>
				<div class="kt-meta-row" style="margin-bottom: var(--kt-space-4)" data-testid="reservation-scope">
					<div><span class="kt-label">Plan basis</span><span style="font-size: 14px">{{ block.plan_basis }}</span></div>
					<div><span class="kt-label">Rule version</span><span style="font-size: 14px">{{ block.rule_version }}</span></div>
					<div><span class="kt-label">County requirement</span><span style="font-size: 14px">{{ block.county_display }}</span></div>
					<div><span class="kt-label">Mandatory restrictions</span><span style="font-size: 14px">{{ block.restrictions_line }}</span></div>
				</div>
				<table class="kt-table" data-testid="reservation-items">
					<thead>
						<tr>
							<th>Purchase</th>
							<th class="is-num">Estimated cost</th>
							<th>Applicability</th>
							<th>Reason</th>
							<th>Planned designation</th>
							<th class="is-num">Qualifying allocation</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in block.items || []" :key="row.plan_item_id">
							<td>
								<div style="font-weight: 600">{{ row.title }}</div>
								<div style="font-size: 12px; color: var(--color-neutral-700); margin-top: 2px">{{ row.plan_item_id }}</div>
							</td>
							<td class="is-num">{{ row.value_display }}</td>
							<td>{{ row.applicability }}</td>
							<td>{{ row.reason }}</td>
							<td>{{ row.designation }}</td>
							<td class="is-num" :class="{ 'is-zero': row.qualifying_is_zero }">{{ row.qualifying_display }}</td>
						</tr>
					</tbody>
				</table>
				<p style="margin: var(--kt-space-4) 0 0; font-size: 13.5px; color: var(--color-neutral-800); max-width: 900px">
					Calculated on the eligible value of this plan version. The approved budget is a separate funding ceiling, checked under Funding, and is not used here.
				</p>
			</div>
		</component>
	</div>
</template>

<script setup>
defineProps({
	block: { type: Object, required: true },
	collapsible: { type: Boolean, default: false },
});
</script>
