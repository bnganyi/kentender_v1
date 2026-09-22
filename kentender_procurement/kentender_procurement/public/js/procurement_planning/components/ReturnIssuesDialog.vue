<!-- PLN-CHG-001 v1.24 §4.4/§10.5 U06-RETURN, ported class-for-class from
     Artboards-U06.dc.html. One or more issues, each a single required
     comment ("What needs to change?") against one requirement or the whole
     departmental plan — no second problem/issue field, and no forced
     per-issue requirement (§4.4 supersedes the retired two-field, entry-only
     contract). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="dppv-return-dialog">
		<div class="kt-dialog" style="width: 520px" role="dialog" aria-modal="true" aria-labelledby="dppv-return-title">
			<div id="dppv-return-title" class="kt-dialog-title">What needs to change?</div>

			<div v-for="(issue, index) in issues" :key="index" class="pln-issue-row">
				<div class="pln-field">
					<label :for="`dppv-issue-context-${index}`">Context</label>
					<select
						:id="`dppv-issue-context-${index}`"
						class="kt-input"
						:data-testid="`dppv-issue-context-${index}`"
						v-model="issue.entry_id"
					>
						<option value="">Whole departmental plan</option>
						<option v-for="entry in entries" :key="entry.entry_id" :value="entry.entry_id">
							{{ entry.title }}
						</option>
					</select>
				</div>
				<div class="pln-field">
					<label :for="`dppv-issue-comment-${index}`">Comment</label>
					<textarea
						:id="`dppv-issue-comment-${index}`"
						class="kt-input"
						rows="4"
						:data-testid="`dppv-issue-comment-${index}`"
						v-model="issue.correction_required"
					></textarea>
				</div>
			</div>

			<button type="button" class="kt-btn kt-btn-ghost" data-testid="dppv-issue-add" @click="addIssue">
				Add another issue
			</button>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="dppv-return-error">
				{{ error }}
			</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dppv-return-confirm"
					:disabled="pending || !complete"
					@click="onConfirm"
				>
					Return to department
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";

const props = defineProps({
	entries: { type: Array, default: () => [] },
	pending: Boolean,
	error: String,
});

const emit = defineEmits(["confirm", "cancel"]);

const issues = reactive([{ entry_id: props.entries[0]?.entry_id || "", correction_required: "" }]);

function addIssue() {
	issues.push({ entry_id: props.entries[0]?.entry_id || "", correction_required: "" });
}

const complete = computed(() => issues.length > 0 && issues.every((issue) => issue.correction_required.trim()));

function onConfirm() {
	emit(
		"confirm",
		issues.map((issue) => ({ entry_id: issue.entry_id || null, correction_required: issue.correction_required.trim() })),
	);
}
</script>
