<!-- Departmental Needs shared inline page-state notice, ported class-for-class
     from NDS Artboards.dc.html — NDS-DES-14-MASKED-DETAIL, NDS-DES-14-
     LOAD-FAILURE (the non-workspace routes; WorkspaceScreen.vue keeps its own
     copy of this exact state for the workspace route itself) and
     NDS-DES-14-AUTHORITY-CHANGED. Occupies the sheet alone (KT-PAT-001 §5's
     page-states recipe): no protected header, filters or rows behind it.
     Mounted by DepartmentalNeeds.vue in place of the detail/editor/task/
     withdrawal screen it would otherwise show, before that screen's own
     component ever sees the (denied/failed) data. -->
<template>
	<div class="kt-page">
		<div style="max-width: 620px; margin: 0 auto; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px">
			<div style="font-family: var(--kt-font-heading); font-size: 20px; font-weight: 600" data-testid="nds-page-notice-heading">
				{{ heading }}
			</div>
			<p v-if="body" style="margin: 0; font-size: 14.5px; color: var(--kt-color-neutral-700)">{{ body }}</p>
			<button
				v-if="actionLabel"
				type="button"
				class="btn btn-secondary"
				style="margin-top: 6px"
				data-testid="nds-page-notice-action"
				@click="$emit('action')"
			>
				{{ actionLabel }}
			</button>
		</div>
	</div>
</template>

<script setup>
defineProps({
	heading: { type: String, required: true },
	body: { type: String, default: "" },
	actionLabel: { type: String, default: "" },
});
defineEmits(["action"]);
</script>
