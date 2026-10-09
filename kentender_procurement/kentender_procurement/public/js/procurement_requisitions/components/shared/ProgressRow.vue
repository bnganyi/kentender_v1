<!-- §6.1 — exactly three steps with Not started / Needs attention / Complete.
     Drawn as the design system's numbered journey (bar, number, label, state),
     so the row reads as steps to take in order rather than as anonymous boxes;
     each step is still a button, because the requester may go to any of them.
     Navigation and progress, not a lifecycle (REQ-CHG-001 v1.17 §13.4B). -->
<template>
	<nav class="req-steps-nav" aria-label="Requisition steps">
		<ol class="kt-journey req-steps" :style="{ '--kt-journey-n': tasks.length }">
			<li
				v-for="(task, index) in tasks"
				:key="task.key"
				class="kt-journey-stage"
				:class="[STAGE[task.status] || 'is-not-started', { 'is-selected': task.key === selected }]"
				:aria-current="task.key === selected ? 'step' : null"
			>
				<button type="button" class="req-step" :data-testid="`req-task-${task.key}`" @click="$emit('select', task.key)">
					<span class="kt-journey-bar" aria-hidden="true"></span>
					<span class="kt-journey-title">
						<svg v-if="task.status === 'Complete'" class="kt-journey-check" aria-hidden="true" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5" /></svg>
						<span v-else class="kt-journey-num">{{ index + 1 }}</span>{{ task.label }}
					</span>
					<span class="kt-journey-state" data-testid="req-step-state">{{ stateLine(task) }}</span>
				</button>
			</li>
		</ol>
	</nav>
</template>

<script setup>
const props = defineProps({ tasks: { type: Array, required: true }, selected: { type: String, default: "" } });
defineEmits(["select"]);
const STAGE = { "Not started": "is-not-started", "Needs attention": "is-blocked", Complete: "is-done" };
// The state is always said in words; the step being looked at is also named.
function stateLine(task) {
	return task.key === props.selected ? `You are here · ${task.status}` : task.status;
}
</script>
