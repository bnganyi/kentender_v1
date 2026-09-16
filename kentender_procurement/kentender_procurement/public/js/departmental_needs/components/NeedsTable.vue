<!-- The one role-appropriate table §1.1 leaves in place of the retired summary
     cards and split sections. Shared by NDS-DES-01, 02 and 02b — the caller
     supplies the columns each role sees. NDS-CHG-001 v1.13 §11.2/§11.3 render
     this directly inside the workspace's .kt-panel-lg, with no separate
     bordered card of its own. -->
<template>
	<div>
		<table class="kt-table" data-testid="nds-needs-table" style="width: 100%">
			<thead>
				<tr>
					<th
						v-for="column in columns"
						:key="column.key"
						:style="column.align === 'right' ? 'text-align: right' : ''"
						:scope="'col'"
					>
						{{ column.label }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="row in needs" :key="row.name" data-testid="nds-need-row" :data-reference="row.reference" :data-status="row.status">
					<td v-for="column in columns" :key="column.key" :style="cellStyle(column)">
						<template v-if="column.key === 'need'">
							<span style="font-weight: 500">{{ row.title || "Untitled need" }}</span>
							<br />
							<span style="color: var(--kt-color-neutral-600); font-size: 13px">{{
								row.reference
							}}</span>
						</template>
						<template v-else-if="column.key === 'action'">
							<!-- §12.1/§12.2 — one row exposes one action, and the server
							     decides which; the UI never invents an action a role
							     does not have. -->
							<button
								v-if="primaryAction(row)"
								type="button"
								class="kt-action-link"
								data-testid="nds-row-action"
								:data-action="primaryAction(row).code"
								@click="$emit('action', row, primaryAction(row))"
							>
								{{ primaryAction(row).label }}
							</button>
						</template>
						<StatusPill
							v-else-if="column.status"
							:label="row[column.key] || ''"
						/>
						<template v-else>{{ row[column.key] }}</template>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import StatusPill from "./StatusPill.vue";

defineProps({
	needs: { type: Array, required: true },
	columns: { type: Array, required: true },
});
defineEmits(["action"]);

function cellStyle(column) {
	return column.align === "right" ? "text-align: right" : "";
}

function primaryAction(row) {
	return (row.actions || [])[0] || null;
}
</script>
