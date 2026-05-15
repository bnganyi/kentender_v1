import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OperationErrorNotice } from "./OperationErrorNotice";
import { OperationLoadingState } from "./OperationLoadingState";
import { useOperationInFlight } from "./useOperationInFlight";

function DuplicatePublishDemo(props: { onPublish: () => Promise<void> }) {
	const { isRunning, run } = useOperationInFlight();
	return (
		<div>
			{isRunning ? <OperationLoadingState label="Publishing tender…" /> : null}
			<button type="button" onClick={() => void run(props.onPublish)}>
				Publish
			</button>
		</div>
	);
}

describe("UI-HARD-1400 operation state", () => {
	afterEach(() => {
		cleanup();
	});

	it("OperationErrorNotice exposes pack testids and redacts probable stacks", () => {
		const stack = `Error: boom\n    at Object.<anonymous> (/app/server.js:12:3)\n    at Module.run (node:internal:99:1)`;
		render(
			<OperationErrorNotice
				message={stack}
				resolutionAction="Retry after cache clear or contact support with reference ERR-9F2."
				referenceCode="ERR-9F2"
				affectedAreaHref="/desk/tenders/TND-1"
				affectedAreaLabel="Open tender"
			/>,
		);
		expect(screen.getByTestId("operation-error-notice")).toBeInTheDocument();
		expect(screen.getByTestId("operation-error-notice")).not.toHaveTextContent("at Object");
		expect(screen.getByTestId("operation-resolution-action")).toHaveTextContent(/Retry after cache clear/i);
		expect(screen.getByText("ERR-9F2")).toBeInTheDocument();
		expect(screen.getByRole("link", { name: /Open tender/i })).toHaveAttribute("href", "/desk/tenders/TND-1");
	});

	it("OperationLoadingState exposes operation-loading-state with busy semantics", () => {
		render(<OperationLoadingState label="Exporting evidence package…" progressPercent={42} />);
		const el = screen.getByTestId("operation-loading-state");
		expect(el).toHaveAttribute("aria-busy", "true");
		expect(el).toHaveTextContent("Exporting evidence package");
		const bar = el.querySelector("progress") as HTMLProgressElement | null;
		expect(bar).toBeTruthy();
		expect(bar!.value).toBe(42);
	});

	it("useOperationInFlight ignores overlapping runs (duplicate publish guard)", async () => {
		const publish = vi.fn(
			() =>
				new Promise<void>((resolve) => {
					setTimeout(resolve, 50);
				}),
		);
		render(<DuplicatePublishDemo onPublish={publish} />);
		const btn = screen.getByRole("button", { name: /Publish/i });
		await act(async () => {
			fireEvent.click(btn);
			fireEvent.click(btn);
			fireEvent.click(btn);
		});
		await act(async () => {
			await new Promise((r) => setTimeout(r, 80));
		});
		expect(publish).toHaveBeenCalledTimes(1);
	});
});
