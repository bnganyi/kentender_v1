// Export (§13.13): the server builds the read-only document for the exact
// displayed Version; the browser only saves it as a file.
export async function downloadExport(ctx, requisition, version) {
	return ctx.run(
		"export",
		async () => {
			const result = await ctx.api.exportRequisition(requisition, version);
			if (!result || result.outcome !== "OK") throw new Error("Requisition not found");
			const url = URL.createObjectURL(new Blob([result.content], { type: "application/json" }));
			const link = document.createElement("a");
			link.href = url;
			link.download = result.filename;
			link.rel = "noopener";
			// Frappe's body-level link handler would treat this as a Desk route.
			link.addEventListener("click", (event) => event.stopPropagation());
			document.body.appendChild(link);
			link.click();
			link.remove();
			URL.revokeObjectURL(url);
			return true;
		},
		{ noReload: true }
	);
}
