<script setup>
// The values of one chart as a real table, in the chart's visual order, visible only to assistive
// technology (KT-STD-001 §2.6.10 item 8; ANL §10A.1). No visible toggle. The first cell of each body
// row is its row header.
defineProps({
	caption: { type: String, default: "" },
	headers: { type: Array, required: true },
	rows: { type: Array, required: true },
});
</script>

<template>
	<table class="sr-only">
		<caption>{{ caption }}</caption>
		<thead>
			<tr>
				<th v-for="(heading, c) in headers" :key="c" scope="col">{{ heading }}</th>
			</tr>
		</thead>
		<tbody>
			<tr v-for="(row, r) in rows" :key="r">
				<template v-for="(cell, c) in row" :key="c">
					<th v-if="c === 0" scope="row">{{ cell }}</th>
					<td v-else>{{ cell }}</td>
				</template>
			</tr>
		</tbody>
	</table>
</template>
