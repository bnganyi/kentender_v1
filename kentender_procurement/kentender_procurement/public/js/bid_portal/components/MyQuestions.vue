<script setup>
// The asking bidder's own questions (BDS-CHG-001 v0.8 §5.4 and the owner's
// 2 Oct 2026 request): each question this bid sent, when Tenders received it,
// where it stands and, once answered, the answer — including an answer sent to
// the asker only. The server reads Tenders' projection for this bid's own
// candidate; nothing is derived here and no other bidder's question is ever in
// the payload.
defineProps({
	questions: { type: Array, default: () => [] },
	testid: { type: String, default: "bds-my-questions" },
});
</script>

<template>
	<div v-if="questions.length" class="bds-my-questions" :data-testid="testid">
		<h3 class="bds-my-questions-title">{{ __("Your questions") }}</h3>
		<div v-for="q in questions" :key="q.key" class="kt-group bds-answer" :data-testid="testid + '-item'">
			<span class="bds-strong">{{ q.question }}</span>
			<div class="bds-notice-line">
				<span class="kt-label">{{ q.answered || q.received }}</span>
				<span class="kt-status" :class="'is-' + q.tone" :data-testid="testid + '-status'">{{ q.status_label }}</span>
			</div>
			<span v-if="q.answer" class="bds-answer-text" :data-testid="testid + '-answer'">{{ q.answer }}</span>
			<span v-if="q.private" class="kt-label">{{ __("This answer was sent to you only.") }}</span>
		</div>
	</div>
</template>
