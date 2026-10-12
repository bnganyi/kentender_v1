<!-- The electronic tender-security journey (Project Owner, 10 Oct 2026): four
     separate facts — Submission, Physical original, Issuer verification and
     Compliance with the published requirement — and the two explicit actions.
     An upload is never "verified". The verification source, the issuer's
     answer and its response time are shown with the result. -->
<script setup>
defineProps({
	electronic: { type: Object, default: null },
	canEdit: { type: Boolean, default: true },
	pending: { type: Boolean, default: false },
});
defineEmits(["submit", "check"]);
const tone = (state) => ({ Confirmed: "is-live", Meets: "is-live", Submitted: "is-live", Mismatch: "is-critical", "Does not meet": "is-critical", Pending: "is-pending", "Changed since submitted": "is-pending" }[state] || "is-draft");
</script>

<template>
	<div v-if="electronic" class="bds-security-status" data-testid="bds-security-status">
		<div class="bds-facts">
			<div class="bds-fact" data-testid="bds-security-submission">
				<span class="kt-label">{{ __("Electronic submission") }}</span>
				<span class="bds-fact-value"><span class="kt-status" :class="tone(electronic.submission.state)">{{ electronic.submission.state }}</span></span>
				<span class="bds-muted">{{ electronic.submission.text }}</span>
			</div>
			<div class="bds-fact" data-testid="bds-security-verification">
				<span class="kt-label">{{ __("Issuer verification") }}</span>
				<span class="bds-fact-value"><span class="kt-status" :class="tone(electronic.verification.state)">{{ electronic.verification.label || electronic.verification.state }}</span></span>
				<span class="bds-muted">{{ electronic.verification.text }}</span>
				<span v-if="electronic.verification.source" class="bds-muted" data-testid="bds-security-verification-details">
					{{ __("Source") }}: {{ electronic.verification.source }}<template v-if="electronic.verification.responded_at"> · {{ electronic.verification.responded_at }}</template><template v-if="electronic.verification.response_ms"> · {{ electronic.verification.response_ms }} ms</template>
				</span>
			</div>
			<div class="bds-fact" data-testid="bds-security-compliance">
				<span class="kt-label">{{ __("Compliance with the published requirement") }}</span>
				<span class="bds-fact-value"><span class="kt-status" :class="tone(electronic.compliance.state)">{{ electronic.compliance.state }}</span></span>
				<span class="bds-muted">{{ electronic.compliance.text }}</span>
			</div>
		</div>
		<div v-if="canEdit" class="bds-actions">
			<button v-if="electronic.submission.state !== 'Submitted' || electronic.verification.state === 'Mismatch'" type="button" class="btn btn-secondary" :disabled="pending || !electronic.submission.can_submit" data-testid="bds-security-submit" @click="$emit('submit')">
				{{ electronic.submission.state === "Not submitted" ? __("Submit tender security") : __("Submit tender security again") }}
			</button>
			<button v-else-if="electronic.verification.state === 'Pending'" type="button" class="btn btn-secondary" :disabled="pending" data-testid="bds-security-check" @click="$emit('check')">{{ __("Check with the issuer again") }}</button>
			<p v-if="!electronic.submission.can_submit && electronic.submission.state !== 'Submitted'" class="bds-muted" data-testid="bds-security-submit-help">{{ __("Complete the form and add the proof to submit your tender security.") }}</p>
		</div>
		<p v-if="electronic.verification.state !== 'Confirmed'" class="bds-muted" data-testid="bds-security-after-opening">{{ __("Security will be checked against your bid after opening.") }}</p>
		<p class="bds-muted">{{ __("Submitting your tender security does not submit your bid, and an upload alone is never treated as verified by the issuer.") }}</p>
	</div>
</template>
