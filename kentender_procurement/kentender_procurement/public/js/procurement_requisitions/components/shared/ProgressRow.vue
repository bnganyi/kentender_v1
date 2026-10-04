<!-- §6.1 — exactly three tasks with Not started / Needs attention / Complete.
     Navigation and progress, not a lifecycle. -->
<template>
	<div class="req-progress" role="tablist" aria-label="Requisition tasks">
		<button
			v-for="task in tasks"
			:key="task.key"
			type="button"
			role="tab"
			class="req-progress-task"
			:class="{ 'is-selected': task.key === selected }"
			:aria-selected="task.key === selected ? 'true' : 'false'"
			:data-testid="`req-task-${task.key}`"
			@click="$emit('select', task.key)"
		>
			<div class="kt-label">{{ task.label }}</div>
			<span v-if="!(task.key === 'review_submit' && task.key === selected)" class="kt-status" :class="TONES[task.status]">{{ task.status }}</span>
		</button>
	</div>
</template>

<script setup>
defineProps({ tasks: { type: Array, required: true }, selected: { type: String, default: "" } });
defineEmits(["select"]);
const TONES = { "Not started": "is-pending", "Needs attention": "is-attention", Complete: "is-live" };
</script>
