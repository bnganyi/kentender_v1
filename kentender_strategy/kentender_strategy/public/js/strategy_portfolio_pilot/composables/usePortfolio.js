import { ref } from "vue";
import { fetchPortfolio, toPortfolioRow, toWorkItem } from "../data/portfolioApi.js";

export function usePortfolio() {
	const plans = ref([]);
	const counts = ref({});
	const entities = ref([]);
	const myWork = ref([]);
	const capabilities = ref({});
	const loading = ref(true);
	const error = ref(null);

	async function refresh() {
		loading.value = true;
		error.value = null;
		try {
			const data = await fetchPortfolio();
			plans.value = (data.plans || []).map(toPortfolioRow);
			counts.value = data.counts || {};
			entities.value = data.entities || [];
			myWork.value = (data.my_work || []).map(toWorkItem);
			capabilities.value = data.capabilities || {};
		} catch (err) {
			error.value = err;
		} finally {
			loading.value = false;
		}
	}

	return { plans, counts, entities, myWork, capabilities, loading, error, refresh };
}
