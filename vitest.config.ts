import { defineConfig } from "vitest/config";

export default defineConfig({
	test: {
		projects: [
			{
				test: {
					name: "std-engine-node",
					environment: "node",
					include: ["frontend/src/**/*.spec.ts"],
				},
			},
			{
				test: {
					name: "std-engine-jsdom",
					environment: "jsdom",
					include: ["frontend/src/**/*.spec.tsx"],
				},
			},
		],
	},
});
