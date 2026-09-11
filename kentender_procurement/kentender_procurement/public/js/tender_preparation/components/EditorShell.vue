<!-- TPR-DES-03 five-task workspace chrome (§13.5), ported class-for-class:
     eyebrow TENDER PREPARATION, the requirement title, the quiet
     "TND · REQ · Version n" line with the status pill, the 280 px left task
     navigation (five tasks + Review and readiness) and the footer with
     Save draft + Continue (Task 5: Review Tender). -->
<template>
	<div class="tpr-editor">
		<header class="tpr-editor-header">
			<div class="tpr-cap">Tender Preparation</div>
			<h1>{{ title }}</h1>
			<div class="tpr-editor-line">
				<span class="tpr-editor-ref">{{ reference }}</span>
				<span class="kt-status" :class="statusClass">{{ status }}</span>
			</div>
		</header>
		<div class="tpr-editor-body">
			<nav class="tpr-task-nav" aria-label="Tasks">
				<button v-for="task in tasks" :key="task.number" type="button" class="tpr-task-nav-item" :class="{ 'is-active': task.number === activeTask }" :data-testid="`tpr-task-${task.number}`" @click="$emit('go-to-task', task.number)">
					<span class="tpr-task-num">{{ task.number }}</span>
					<span class="tpr-task-label">{{ task.label }}</span>
					<span class="tpr-tag" :class="task.number === activeTask ? 'is-accent' : 'is-neutral'">{{ task.statusText }}</span>
				</button>
				<div class="tpr-task-hr"></div>
				<button type="button" class="tpr-task-nav-item" :class="{ 'is-active': activeTask === 6 }" data-testid="tpr-task-review" @click="$emit('go-to-task', 6)">
					<span class="tpr-task-num is-review">✓</span>
					<span class="tpr-task-label">Review and readiness</span>
					<span class="tpr-tag" :class="readiness.ready ? 'is-accent' : 'is-neutral'">{{ readinessText }}</span>
				</button>
			</nav>
			<main class="tpr-task-main">
				<p v-if="error" class="tpr-error-banner" role="alert" data-testid="tpr-editor-inline-error">{{ error }}</p>
				<slot />
			</main>
		</div>
		<footer class="tpr-editor-footer">
			<slot name="footer">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending || !canSave" data-testid="tpr-save-draft" @click="$emit('save-draft')">Save draft</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tpr-continue" @click="$emit('continue')">{{ continueLabel }}</button>
			</slot>
		</footer>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	title: { type: String, default: "" },
	status: { type: String, default: "Draft" },
	reference: { type: String, default: "" },
	tasks: { type: Array, required: true }, // [{ number, label, statusText }]
	activeTask: { type: Number, required: true },
	readiness: { type: Object, default: () => ({}) },
	continueLabel: { type: String, default: "Continue" },
	pending: Boolean,
	canSave: { type: Boolean, default: true },
	error: { type: String, default: "" },
});
defineEmits(["go-to-task", "save-draft", "continue"]);

const STATUS_CLASS = { Draft: "is-draft", Returned: "is-attention", Submitted: "is-pending", Approved: "is-live", "Upstream correction required": "is-attention" };
const statusClass = computed(() => STATUS_CLASS[props.status] || "is-draft");
const readinessText = computed(() => {
	const r = props.readiness || {};
	if (!r.run_at) return "Not run";
	return r.ready ? `Ready · ${r.blocking_count} Blocking · ${r.warning_count} Warning` : `${r.blocking_count} Blocking · ${r.warning_count} Warning`;
});
</script>
