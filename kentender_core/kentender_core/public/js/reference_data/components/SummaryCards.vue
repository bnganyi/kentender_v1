<script setup>
import { computed } from "vue";

const props = defineProps({
	peRows: { type: Array, default: () => [] },
	fyRows: { type: Array, default: () => [] },
	contextRows: { type: Array, default: () => [] },
});

const activePeCount = computed(() => props.peRows.filter((r) => r.status === "Active").length);
const availableFyCount = computed(() => props.fyRows.filter((r) => r.record_status === "Available").length);
const activeContextCount = computed(() => props.contextRows.filter((r) => r.status === "Active").length);
const configRequiredCount = computed(() => props.contextRows.filter((r) => r.readiness === "Configuration required").length);
</script>

<template>
	<div style="margin:32px 48px 0;display:grid;grid-template-columns:repeat(4,1fr);gap:24px">
		<div class="kt-card kt-blueprint" style="padding:20px 22px;gap:14px">
			<div style="font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">{{ __("Active procuring entities") }}</div>
			<div class="kt-figure is-live">{{ activePeCount }}</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
		<div class="kt-card kt-blueprint" style="padding:20px 22px;gap:14px">
			<div style="font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">{{ __("Available financial years") }}</div>
			<div class="kt-figure is-live">{{ availableFyCount }}</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
		<div class="kt-card kt-blueprint" style="padding:20px 22px;gap:14px">
			<div style="font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">{{ __("Active PE/FY contexts") }}</div>
			<div class="kt-figure is-live">{{ activeContextCount }}</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
		<div class="kt-card kt-blueprint" style="padding:20px 22px;gap:14px">
			<div style="font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">{{ __("Configuration required") }}</div>
			<div class="kt-figure is-attention">{{ configRequiredCount }}</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
	</div>
</template>
