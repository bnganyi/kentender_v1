<!-- §12.6 — the structured-issue return dialog: at least one issue with the
     affected entry, the concise problem and the exact correction required.
     No reason category, attachment, assignee or optional note (§11.17). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="dppv-return-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="dppv-return-title">
			<div id="dppv-return-title" class="kt-dialog-title">Return to department?</div>
			<p class="pln-dialog-lede">
				The submitted plan remains unchanged. State each issue and the exact
				correction required.
			</p>

			<div v-for="(issue, index) in issues" :key="index" class="pln-issue-row">
				<div class="pln-field">
					<label :for="`dppv-issue-entry-${index}`">Affected requirement</label>
					<select
						:id="`dppv-issue-entry-${index}`"
						class="kt-input"
						:data-testid="`dppv-issue-entry-${index}`"
						v-model="issue.entry_id"
					>
						<option v-for="entry in entries" :key="entry.entry_id" :value="entry.entry_id">
							{{ entry.title }}
						</option>
					</select>
				</div>
				<div class="pln-field">
					<label :for="`dppv-issue-problem-${index}`">Problem</label>
					<input
						:id="`dppv-issue-problem-${index}`"
						type="text"
						class="kt-input"
						:data-testid="`dppv-issue-problem-${index}`"
						v-model="issue.problem"
					/>
				</div>
				<div class="pln-field">
					<label :for="`dppv-issue-correction-${index}`">Correction required</label>
					<textarea
						:id="`dppv-issue-correction-${index}`"
						class="kt-input"
						rows="2"
						:data-testid="`dppv-issue-correction-${index}`"
						v-model="issue.correction"
					></textarea>
				</div>
			</div>

			<button class="kt-btn kt-btn-ghost" data-testid="dppv-issue-add" @click="addIssue">
				Add another issue
			</button>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="dppv-return-error">
				{{ error }}
			</p>

			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary"
					data-testid="dppv-return-confirm"
					:disabled="pending || !complete"
					@click="$emit('confirm', issues)"
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

defineEmits(["confirm", "cancel"]);

const issues = reactive([
	{ entry_id: props.entries[0]?.entry_id || "", problem: "", correction: "" },
]);

function addIssue() {
	issues.push({ entry_id: props.entries[0]?.entry_id || "", problem: "", correction: "" });
}

const complete = computed(
	() =>
		issues.length > 0 &&
		issues.every(
			(issue) => issue.entry_id && issue.problem.trim() && issue.correction.trim()
		)
);
</script>
