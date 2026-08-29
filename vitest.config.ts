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
			{
				// NDS-906 — the Departmental Needs presentation helpers. These are
				// plain ES modules with no Vue or frappe dependency, so they need
				// no component toolchain; the components that consume them are
				// asserted in the browser layer (tests/ui/smoke/departmental_needs).
				test: {
					name: "departmental-needs",
					environment: "node",
					include: [
						"kentender_procurement/kentender_procurement/public/js/departmental_needs/**/*.spec.js",
					],
				},
			},
		],
	},
});
