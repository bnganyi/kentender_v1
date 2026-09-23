<!-- PLN-CHG-001 v1.24 §10.9 U10-RETURN, ported from Artboards-U10.dc.html
     (re-diffed 23 Sep 2026 against the real §10.9/U10-RETURN section: the
     artboard draws only the heading, the read-only Context and the Reason
     field above Cancel / Return to planner — no explanatory lede paragraph.
     The template previously carried one ("No reservation is created. State
     the correction required.") that the artboard never draws; removed. No
     reason category, attachment, assignee, due date or optional note, same
     as every other "return for correction" dialog in this app. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="fnt-return-dialog">
		<div class="kt-dialog" style="width: 520px" role="dialog" aria-modal="true" aria-labelledby="fnt-return-title">
			<div id="fnt-return-title" class="kt-dialog-title">What needs to change?</div>
			<div class="kt-group">
				<span class="kt-label">Context</span>
				<div style="font-size: 14px; margin-top: 2px" data-testid="fnt-return-context">Whole annual plan</div>
			</div>
			<div class="pln-field">
				<label for="fnt-return-reason">Reason</label>
				<textarea
					id="fnt-return-reason" class="kt-input" rows="3"
					data-testid="fnt-return-reason" v-model="reason"
				></textarea>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="fnt-return-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="fnt-return-confirm"
					:disabled="pending || reason.trim().length < 10"
					@click="$emit('confirm', reason.trim())"
				>
					Return to planner
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
