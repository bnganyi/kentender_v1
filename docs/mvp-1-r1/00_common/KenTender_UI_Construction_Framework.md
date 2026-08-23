KenTender UI Construction Framework

The best course for KenTender is to stop translating generated Tailwind HTML into large jQuery/Frappe pages. For complex custom screens, standardize on:

**Claude Design → Vue 3 components → Frappe UI/Tailwind → mounted inside a Frappe Desk Page.**

This aligns the design output with Frappe's supported frontend stack. Frappe UI is built with Vue 3 and Tailwind, and Frappe officially supports mounting compiled Vue applications inside Desk pages. Its bundler handles Vue, TypeScript, JavaScript and CSS. [Frappe UI](https://github.com/frappe/frappe-ui?utm_source=chatgpt.com), [Vue in a Desk Page](https://docs.frappe.io/framework/using-vue-inside-a-desk-page?utm_source=chatgpt.com), [Frappe asset bundling](https://docs.frappe.io/framework/user/en/basics/asset-bundling?utm_source=chatgpt.com).

**1\. Use three UI approaches—not one approach everywhere**

| **Surface**                                                | **Recommended construction**                                                |
| ---------------------------------------------------------- | --------------------------------------------------------------------------- |
| Routine CRUD and administration                            | Standard Frappe Form, List, Report, Workflow and Dialog APIs                |
| Module landing/navigation                                  | Standard Frappe Workspace                                                   |
| Complex queues, workbenches, builders and guided workflows | Vue 3 application using Frappe UI, mounted inside a Frappe Desk Page        |
| Public supplier/bidder experiences                         | Dedicated Frappe UI frontend or portal application, depending on complexity |

Do not put raw HTML/Tailwind, Frappe controls, jQuery re-rendering and Vue components into the same screen.

For KenTender's sophisticated planning, evaluation, contract and departmental-needs workspaces, the embedded Vue/Frappe UI approach is the strongest fit.

**2\. Keep Frappe as the application shell**

A custom page should still be a real Frappe Page created with frappe.ui.make_app_page(). The page controller should:

1. Create the Frappe page and header.
2. Lazy-load the relevant compiled bundle.
3. Mount one Vue application into .layout-main-section.
4. Pass the current route and context to Vue.
5. Avoid re-mounting the application or duplicating event listeners on every on_page_show.

Frappe documents this exact pattern, including .vue components, .bundle.js entry points and frappe.require() lazy loading. [Frappe Page API](https://docs.frappe.io/framework/user/en/api/page?utm_source=chatgpt.com), [Vue in a Desk Page](https://docs.frappe.io/framework/using-vue-inside-a-desk-page?utm_source=chatgpt.com).

A suitable structure would be:

kentender_module/

├── kentender_module/

│ └── module/page/planning_workspace/

│ ├── planning_workspace.json

│ └── planning_workspace.js

└── public/frontend/planning/

├── planning.bundle.js

├── PlanningWorkspace.vue

├── components/

├── composables/

├── services/

└── styles/

**3\. Create one real KenTender component system**

Claude Design should design with the same components that Claude Code will implement.

Start with a small production component library:

- KtPageHeader
- KtWorkbench
- KtQueueTable
- KtFilterBar
- KtStatusBadge
- KtFormField
- KtMoneyField
- KtEmptyState
- KtEvidencePanel
- KtWorkflowTimeline
- KtDialog
- KtActionBar

Build these on Frappe UI primitives, then apply KenTender tokens and behaviour. Frappe UI already provides accessible components, data-fetching utilities and Tailwind conventions. Its official repository now includes an agent skill specifically for Claude Code, Cursor and Codex. Frappe UI agent guidance.

Create an actual KenTender UI Lab Desk page that renders every production component in every state. This is more valuable than a style guide document because it exposes the components to real Desk CSS, routing and browser behaviour.

The UI Lab should show:

- default, hover, focus and disabled controls;
- empty, loading, populated and error states;
- short and overflowing text;
- permission-restricted actions;
- tables, dialogs and responsive layouts;
- light/dark treatment if both are supported.

**4\. Make the repository—not Claude Design—the design authority**

Claude Design supports organization design systems built from codebases, screenshots, components and brand assets. Use this, but feed it the approved KenTender component library and UI Lab—not the historical collection of independent Stitch exports. [Claude Design systems](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design?utm_source=chatgpt.com).

Keep the authoritative design assets in the repository:

kentender_core/public/frontend/design-system/

├── tokens.css

├── components/

├── icons/

├── patterns/

└── ui-contract.md

Claude Design can consume this material, but it must not become an independent source of colors, spacing or component variants.

**5\. Control Tailwind carefully inside Desk**

Tailwind itself is no longer the problem if it is compiled as part of Frappe UI. Uncontrolled global Tailwind is the problem.

Rules:

- Never load Tailwind from a CDN.
- Never paste generated Tailwind HTML directly into a page controller.
- Never add generated Tailwind output to global app_include_css.
- Scope or disable reset/Preflight styles so they cannot restyle the entire Frappe Desk.
- Prefix application utilities where supported by the pinned Tailwind configuration.
- Load page bundles lazily.
- Use semantic design tokens rather than arbitrary values such as mt-\[13px\].
- Extract repeated utility combinations into Vue components.
- Pin Frappe UI, Vue, Tailwind and Node versions.

This prevents a new module's CSS from altering forms, dialogs or pages elsewhere in Desk.

**6\. Give Claude Design a Frappe-aware handoff contract**

Do not ask only for "the HTML." Require every handoff to include:

- screen and route identifier;
- purpose and primary user;
- component inventory;
- components reused versus newly proposed;
- exact tokens;
- loading, empty, populated, validation, permission and server-error states;
- actions and confirmation behaviour;
- responsive behaviour;
- keyboard and accessibility expectations;
- sample content clearly identified as sample data;
- screenshots at agreed viewport sizes;
- design intent explaining important visual decisions.

A suitable standing instruction is:

Design the content area of an existing Frappe Desk page.

Use the approved KenTender design system and component names. Do not

recreate the Frappe sidebar, navbar, routing, authentication or page shell.

Target implementation is Vue 3 with Frappe UI and compiled Tailwind.

Do not create client-side business rules, database calls or fake production

services.

Provide every applicable loading, empty, populated, validation, permission,

confirmation, success and server-error state. Include exact responsive and

interaction behaviour in the Claude Code handoff.

Claude Design can export standalone HTML and a Claude Code handoff bundle, but it is still a beta design/prototyping product. Treat the bundle as design evidence, not as production-ready Frappe code. [Claude Design announcement](https://www.anthropic.com/news/claude-design-anthropic-labs?utm_source=chatgpt.com).

**7\. Keep the server boundary strict**

Vue components should call small frontend service adapters, which call explicit Frappe endpoints:

Vue component

→ frontend service/composable

→ whitelisted Frappe API

→ Python domain service

→ DocTypes

The server must determine:

- permissions and organizational scope;
- allowed actions;
- workflow transitions;
- validation;
- resulting status;
- audit effects.

Do not recreate action eligibility or governance logic in Vue merely to make a button work.

**8\. Test UI changes in a narrow ladder**

For each screen:

1. Vitest component test for the changed state or interaction.
2. Focused server/API test.
3. One targeted Playwright test for the primary journey.
4. Visual comparison at fixed viewport sizes.
5. Direct, click-through, refresh and browser-back navigation checks.
6. One module UI gate at completion.

Do not run the complete KenTender suite after each CSS or component correction.

The browser test should also fail on:

- console errors;
- failed API requests;
- duplicate dialogs;
- missing route identifiers;
- stale status after actions;
- unexpected horizontal overflow;
- unscoped Desk style changes.

**9\. Migrate incrementally**

Do not rewrite working KenTender screens wholesale.

Use this standard for:

1. all new complex screens;
2. existing screens undergoing material revision;
3. shared components that repeatedly cause defects;
4. the most expensive legacy UI surface after the new approach succeeds in a pilot.

The first pilot should be one representative screen containing a queue, filters, a record panel, a workflow action and a dialog. Prove the complete Claude Design → Frappe UI → Vue-in-Desk → targeted-test workflow before adopting it across modules.

The critical change is therefore not merely replacing Stitch with Claude Design. It is eliminating the repeated **HTML/Tailwind-to-jQuery/plain-CSS conversion** and establishing Frappe UI/Vue as the controlled production landing zone.