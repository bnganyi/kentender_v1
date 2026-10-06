<!-- TPR-DES-03 drawer / TPR-DES-04 "Show full requirements": every
     authorised requirement as the boards' four tables (equipment, technical,
     warranty and support, acceptance). The server shapes each table
     (`inherited.requirement_tables`); nothing here is editable (§4.3). -->
<template>
	<div class="tnd-requirement-tables" data-testid="tnd-requirement-tables">
		<table v-for="(table, index) in tables" :key="table.key" class="table tnd-xs" :class="{ 'tnd-table-gap': index > 0 }" :data-testid="`tnd-requirements-${table.key}`">
			<thead>
				<tr><th v-for="column in table.columns" :key="column.label" :class="{ 'is-num': column.num }">{{ column.label }}</th></tr>
			</thead>
			<tbody>
				<tr v-for="(row, r) in table.rows" :key="r">
					<td v-for="(cell, c) in row" :key="c" :class="{ 'is-num': table.columns[c] && table.columns[c].num }">{{ cell }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
defineProps({ tables: { type: Array, default: () => [] } });
</script>
