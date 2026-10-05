<!-- Decisions and progress — OVS-CHG-001 v0.6 §8, §13. The stages after this
     Tender closed for bids, each as its owner discloses it to this reader
     (server `stage_summaries`): status, the decision or the administrative
     facts, the recorded reason, what is outstanding, and a way to the owner's
     record. Ported from the review board
     `17_oversight_visibility/design/OVS First Slice Review.dc.html`
     (OVS-TPR-01 to 06): a titled working section, one row per stage, no
     tracker, stepper or card. A stage that could not be loaded says so and
     offers Try again while the others stay usable. -->
<template>
	<section class="tnd-section tnd-stages" data-testid="tnd-decisions-progress">
		<h2 class="tnd-stages-title">Decisions and progress</h2>
		<div v-for="s in stages" :key="s.key" class="tnd-stage" :data-testid="`tnd-stage-${s.key}`" :data-disclosure="s.disclosure" :data-state="s.state">
			<div class="tnd-stage-head">
				<div class="tnd-stage-name">{{ s.label }}</div>
				<div v-if="s.status"><span class="kt-status" :class="tone(s)">{{ s.status }}</span></div>
			</div>
			<template v-if="s.state === 'unavailable'">
				<div class="tnd-stage-body"><p class="tnd-stage-line" role="alert">{{ s.message || "We could not load this stage" }}</p></div>
				<div class="tnd-stage-actions"><button type="button" class="btn btn-secondary" data-testid="tnd-stage-retry" @click="$emit('refresh')">Try again</button></div>
			</template>
			<template v-else>
				<div class="tnd-stage-body">
					<div v-if="s.facts.length" class="kt-meta-row tnd-stage-facts">
						<div v-for="f in s.facts" :key="f.label"><span class="kt-label">{{ f.label }}</span><span class="tnd-stage-value">{{ f.value }}</span></div>
					</div>
					<div v-if="s.reason"><span class="kt-label">Recorded reason</span><p class="tnd-stage-line">{{ s.reason }}</p></div>
					<p v-if="s.outstanding" class="tnd-stage-line" data-testid="tnd-stage-outstanding">{{ s.outstanding.text }}</p>
					<p v-if="s.notice" class="tnd-stage-line tnd-stage-muted">{{ s.notice }}</p>
				</div>
				<div class="tnd-stage-actions">
					<button v-for="l in s.links" :key="l.key" type="button" class="btn" :class="l.key === 'view-record' ? 'btn-secondary' : 'btn-ghost'" :data-testid="`tnd-stage-${s.key}-${l.key}`"
						:aria-label="l.key === 'view-record' ? `View ${s.label.toLowerCase()} record` : l.label" @click="$emit('open-link', l.route)">{{ l.key === "view-record" ? "View record" : l.label }}</button>
				</div>
			</template>
		</div>
	</section>
</template>

<script setup>
defineProps({ stages: { type: Array, default: () => [] } });
defineEmits(["open-link", "refresh"]);

// the board's badge tones: working states are neutral, a return needs attention, a recorded stage is settled
function tone(s) {
	if (/returned/i.test(s.status)) return "is-attention";
	if (["Preparing", "Reviewing", "Signing", "Opinion", "Decision", "In session", "Paused"].includes(s.status)) return "is-draft";
	return "is-pending";
}
</script>
