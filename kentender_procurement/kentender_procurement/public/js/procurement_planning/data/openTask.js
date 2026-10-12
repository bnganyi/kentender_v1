// A governance task (the Accounting Officer's adoption, the statutory
// approval) is the page for deciding, and the plan page it would otherwise
// show first is a near-identical read of the same plan. So the plan page hands
// its task holder to the task. Only `opens_directly` tasks do this: the
// Finance officer still needs the live plan beside their task, so theirs stays
// a button.
export function directTaskRoute(screen, loaded) {
	if (screen !== "plan") return null;
	const task = loaded && loaded.open_task;
	return task && task.opens_directly ? task.route : null;
}
