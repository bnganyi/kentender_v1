<!-- TPR-DES-03/04 progress row: three numbered dots joined by lines, a
     completed task shows a tick on a live dot, the current task an accent
     dot, and the three labels beneath carry the server's own task status
     (Needs attention / Not started / Complete). Labels are buttons so the
     officer can move between tasks; the row never derives a status itself. -->
<template>
	<div class="tnd-progress" data-testid="tnd-progress">
		<div class="tnd-progress-track">
			<template v-for="(task, index) in TASKS" :key="task.key">
				<div class="tnd-step-dot" :class="{ 'is-current': task.key === current, 'is-done': isDone(task.key) && task.key !== current }" :data-testid="`tnd-step-dot-${task.key}`">
					<svg v-if="isDone(task.key) && task.key !== current" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg>
					<template v-else>{{ index + 1 }}</template>
				</div>
				<div v-if="index < TASKS.length - 1" class="tnd-step-line" :class="{ 'is-done': isDone(task.key) }"></div>
			</template>
		</div>
		<div class="tnd-step-labels">
			<div v-for="task in TASKS" :key="task.key" class="tnd-step-label">
				<button type="button" class="tnd-step-name" :class="{ 'is-current': task.key === current }" :disabled="!navigable" :data-testid="`tnd-step-${task.key}`" @click="$emit('go', task.key)">{{ task.label }}</button>
				<div><span class="kt-status" :class="statusClass(statuses[task.key])" :data-testid="`tnd-step-status-${task.key}`">{{ statuses[task.key] || "Not started" }}</span></div>
			</div>
		</div>
	</div>
</template>

<script setup>
const props = defineProps({
	current: { type: String, default: "details" },
	statuses: { type: Object, default: () => ({}) },
	navigable: { type: Boolean, default: true },
});
defineEmits(["go"]);

const TASKS = [
	{ key: "details", label: "Tender details" },
	{ key: "requirements", label: "Supplier and contract requirements" },
	{ key: "review", label: "Review and submit" },
];

function isDone(key) {
	return props.statuses[key] === "Complete";
}
function statusClass(status) {
	if (status === "Complete") return "is-live";
	if (status === "Needs attention") return "is-attention";
	return "is-pending";
}
</script>
