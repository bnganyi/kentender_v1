<script setup>
const props = defineProps({
	activeTab: { type: String, required: true },
	peCount: { type: Number, default: 0 },
	fyCount: { type: Number, default: 0 },
	contextCount: { type: Number, default: 0 },
});
const emit = defineEmits(["select"]);
</script>

<template>
	<div style="margin:32px 48px 0;display:flex;gap:36px;border-bottom:1px solid var(--kt-color-divider)">
		<button type="button" class="kt-tab" :aria-selected="activeTab === 'pe'" @click="emit('select', 'pe')">
			{{ __("Procuring Entities") }} <span class="kt-count">{{ peCount }}</span>
		</button>
		<button type="button" class="kt-tab" :aria-selected="activeTab === 'fy'" @click="emit('select', 'fy')">
			{{ __("Financial Years") }} <span class="kt-count">{{ fyCount }}</span>
		</button>
		<button type="button" class="kt-tab" :aria-selected="activeTab === 'context'" @click="emit('select', 'context')">
			{{ __("PE/FY Contexts") }} <span class="kt-count">{{ contextCount }}</span>
		</button>
	</div>
</template>
