---
name: Strategic Procurement Workbench
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#43474f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#0061a5'
  on-secondary: '#ffffff'
  secondary-container: '#0095f8'
  on-secondary-container: '#002b4e'
  tertiary: '#381300'
  on-tertiary: '#ffffff'
  tertiary-container: '#592300'
  on-tertiary-container: '#d8885c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#d2e4ff'
  secondary-fixed-dim: '#9fcaff'
  on-secondary-fixed: '#001d36'
  on-secondary-fixed-variant: '#00497e'
  tertiary-fixed: '#ffdbca'
  tertiary-fixed-dim: '#ffb690'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#723610'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  status-success: '#10B981'
  status-warning: '#F59E0B'
  status-error: '#EF4444'
  status-neutral: '#64748B'
  cat-goods: '#6366F1'
  cat-works: '#8B5CF6'
  cat-services: '#EC4899'
  cat-consultancy: '#06B6D4'
typography:
  display-hero:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  display-hero-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  workbench-gutter: 24px
  card-padding: 20px
  stack-gap-sm: 8px
  stack-gap-md: 16px
  container-max-width: 1440px
---

## Brand & Style
The design system is anchored in a **Corporate / Modern** aesthetic, specifically tailored for enterprise procurement management. It prioritizes a "Work-Not-Records" philosophy, transforming dry database entries into an actionable, high-productivity workbench environment. 

The visual tone is professional, authoritative, and protective, designed to evoke a sense of precision and reliability. By utilizing a clean, white-space-heavy interface with structured information layering, the system reduces the cognitive load of complex fiscal planning. It uses high-contrast functional color cues to guide users through rigorous procurement workflows—ensuring readiness, budget compliance, and regulatory adherence are always at the forefront of the experience.

## Colors
This design system uses a palette rooted in institutional trust and functional clarity. 

- **Primary & Secondary:** A deep "Navy" (#003366) serves as the primary anchor for navigation and major actions, while a vibrant "Action Blue" (#0099FF) highlights interactive elements and active states.
- **Surface & Backgrounds:** The base interface uses a near-white neutral (#F8FAFC) to create a clean canvas for information-dense cards.
- **Functional Semantics:** Status colors (Success, Warning, Error) are applied with "Readability First" logic—utilizing tinted backgrounds with high-contrast text for badges.
- **Category Identifiers:** Distinct hues are assigned to procurement types (Goods, Works, Services, Consultancy) to provide instant visual categorization in dense data tables and card views.

## Typography
The typography system balances the modern, sharp personality of **Hanken Grotesk** for headings with the high legibility of **Inter** for data and body content.

- **Headlines:** Used for page titles and high-level workbench summaries. They use a tighter letter-spacing to maintain a professional, "tight" feel.
- **Body:** Inter is used for all record data, descriptions, and user inputs to ensure clarity in dense procurement tables.
- **Labels:** Small caps and increased letter-spacing are used for metadata and field headers (e.g., "PROCURING ENTITY") to distinguish them from the actual data values.
- **Status Badges:** Text within badges uses `label-md` for maximum visibility at small sizes.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy for the main content area to maintain a structured "Workbench" feel, centered on a 1440px max-width container.

- **Workbench Queues:** Content is organized into multi-column flex layouts (e.g., Needs Planning | In Creation | Awaiting Review). Each column maintains a 24px gutter.
- **The Drawer Model:** An "Evidence Drawer" slides from the right (width: 480px), overlaying the content to provide technical depth without losing the user's place in the workflow.
- **Mobile Adaption:** On mobile, columns stack vertically. Large cards reflow into a "list-item" format with condensed headers to prioritize status and primary action buttons.

## Elevation & Depth
This design system uses **Tonal Layers** and **Ambient Shadows** to define the hierarchy of work.

- **Base Layer (L0):** The foundation is a light gray (#F8FAFC) flat surface.
- **Card Surface (L1):** White cards feature a very subtle, diffused shadow (0px 2px 4px rgba(0,0,0,0.05)) and a 1px border (#E2E8F0). This creates a "sheet of paper" look that feels organized.
- **Active Workspace (L2):** Drawers and Modals use a more pronounced shadow (0px 10px 25px rgba(0,0,0,0.1)) and a backdrop blur on the layer below to focus the user on the specific "Evidence" or "Wizard" task.
- **Interactive States:** Buttons and clickable cards use a subtle "lift" effect (y-offset increase) on hover to signal interactivity.

## Shapes
A **Soft** shape language is employed to balance professional rigor with modern approachability. 

- **Cards & Containers:** Use a 0.25rem (4px) radius to maintain a precise, structured appearance.
- **Buttons & Inputs:** Follow the same 4px radius for a unified, "tool-like" feel.
- **Status Badges:** Use a more pronounced 1rem (pill-shape) to distinguish functional status markers from structural UI elements.
- **Visual Gate:** The "No Active Plan" setup area is enclosed in a dashed border with a slightly larger radius to indicate it is a "placeholder" or "setup" state.

## Components
- **Buttons:** Primary buttons are solid Navy (#003366) with white text. Secondary buttons use the "Action Blue" as an outline or text color. Ghost buttons are reserved for low-priority actions in the Evidence Drawer.
- **Status Badges:** Use high-contrast pairings (e.g., Deep Green text on Light Green background). Icons (Check, Alert, Clock) should precede the text for "Readiness" indicators.
- **Package Cards:** Must include a "Category Label" on the top right, a bold Title, and a "Metadata Row" for Ref IDs and Dates.
- **Evidence Drawer:** A persistent right-aligned panel. Content should be grouped by "Evidence Type" (Specifications, Funding, Scope) with clear "Download" or "View" icons.
- **Planning Tabs:** A 5-step horizontal tab system (Overview, Lines, Readiness, Review, Release) with a progress indicator for the "Active Plan" workflow.
- **Data Tables:** High-density, borderless rows with a subtle hover state highlight. Headers use the `label-md` typography style.