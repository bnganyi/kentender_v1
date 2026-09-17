<!-- U10-history — Funding evidence history: the two named states (evidence
     at approval vs the current confirmation) and every review attempt in
     order. A later Review's own outcome never overwrites an earlier one's
     row; this is a read-only projection, no action lives here. -->
<template>
	<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-history">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div class="kt-card-title">Funding evidence history</div>
		<div class="pln-facts-row" style="margin-bottom: 16px">
			<div class="pln-fact">
				<span class="kt-label">Funding evidence at approval</span>
				<span class="kt-status" :class="atApproval ? 'is-live' : 'is-pending'">{{ atApproval ? "Confirmed" : "Not yet confirmed" }}</span>
			</div>
			<div class="pln-fact">
				<span class="kt-label">Current funding confirmation</span>
				<span class="kt-status" :class="currentStateClass">{{ evidence.state || "Awaiting confirmation" }}</span>
			</div>
		</div>
		<table class="pln-table">
			<thead><tr><th>Review</th><th>Basis</th><th>Outcome</th><th>Actor</th><th>Time</th></tr></thead>
			<tbody>
				<tr v-for="row in rows" :key="row.review" :data-testid="`fnt-history-${row.review.replace(' ', '-').toLowerCase()}`">
					<td>{{ row.review }}</td>
					<td>{{ row.basis }}</td>
					<td>
						<span class="kt-status" :class="row.outcome === 'Confirmed' ? 'is-live' : row.outcome === 'Returned' ? 'is-critical' : 'is-pending'">{{ row.outcome }}</span>
					</td>
					<td>{{ row.actor }}</td>
					<td>{{ row.time_display }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	history: { type: Array, default: () => [] },
	fundingEvidence: { type: Object, default: () => ({}) },
});

const rows = computed(() => props.history);
const evidence = computed(() => props.fundingEvidence || {});
const atApproval = computed(() => !!evidence.value.at_approval);
const currentStateClass = computed(() => {
	const state = evidence.value.state;
	if (state === "Confirmed") return "is-live";
	if (state === "Stale" || state === "Returned") return "is-critical";
	return "is-pending";
});
</script>
