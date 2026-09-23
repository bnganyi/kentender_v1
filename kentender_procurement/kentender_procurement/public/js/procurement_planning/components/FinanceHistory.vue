<!-- PLN-CHG-001 v1.24 §10.9 U10-HISTORY, ported from Artboards-U10.dc.html
     (re-diffed 23 Sep 2026). Funding evidence history: the two named states
     (evidence at approval vs the current confirmation) and every review
     attempt in order. A later Review's own outcome never overwrites an
     earlier one's row; this is a read-only projection, no action lives here.

     Known, already-tracked discrepancy (FU-V123-08, see
     tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts's own
     "U10-HISTORY" test comment): §10.9's own U10-HISTORY draws two separate
     labelled blocks ("Funding checked at approval" / "Latest funding check",
     each with Review/Budget version/Plan version/Outcome/Person/Date-and-
     time), not this component's one "Funding evidence history" region with
     two status facts plus a Review/Basis/Outcome/Actor/Time table. That
     table form is not a fabrication, though: it is load-bearing for the
     reassessment case both this suite and `pln-finance.spec.ts`'s own
     "Finance reassesses funding for an Active Version" test assert on
     directly (`fnt-history-review-1`/`fnt-history-review-2`, two rows) — the
     single-review U10-HISTORY artboard fixture never exercises that case, so
     its two-block layout cannot itself show what more than one review looks
     like. Reconciling the two is FU-V123-08's job, not this pass's: it would
     mean changing `tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts`,
     which this remediation batch is instructed not to touch. Left as built,
     flagged here rather than silently ported. -->
<template>
	<div class="kt-region is-secondary" data-testid="fnt-history">
		<h2>Funding evidence history</h2>
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
