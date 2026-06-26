---
name: Strategic Procurement System
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
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#00201d'
  on-tertiary-container: '#0c9488'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#89f5e7'
  tertiary-fixed-dim: '#6bd8cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#005049'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
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
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  sidebar-width: 260px
  panel-width: 380px
---

## Brand & Style

The design system is engineered for high-stakes enterprise procurement environments. It prioritizes **clarity, efficiency, and institutional trust**. The brand personality is "The Expert Facilitator"—someone who is precise, reliable, and removes friction from complex financial workflows.

The visual style is **Corporate / Modern** with a focus on information density and data integrity. It utilizes a structured "Side-Sheet" layout for contextual actions and a modular card-based system for managing work queues. High-contrast labels and disciplined whitespace ensure that users can navigate large volumes of procurement data without cognitive overload. The aesthetic is clean and professional, using a mix of deep slate tones for navigation and bright, neutral workspaces for operational tasks.

## Colors

The palette is anchored by a deep **Primary Slate (#0F172A)**, used for primary navigation and high-level structural elements to ground the interface in authority. A vibrant **Secondary Blue (#2563EB)** serves as the primary action color, guiding users toward key interactions.

For the procurement lifecycle, distinct functional colors are assigned to track workflows:
- **Demands:** Indigo-based to represent intake and planning.
- **Packages:** Amber to signal active preparation and resource grouping.
- **Tender Releases:** Emerald to signify the "go" signal and external market visibility.

The background uses a cool **Neutral Gray (#F8FAFC)** to reduce eye strain during long working sessions, with white surfaces for active work cards to create a clear visual hierarchy of "layering."

## Typography

This design system uses a triple-font strategy to balance character and utility. **Hanken Grotesk** is used for headlines to provide a modern, sharp executive feel. **Inter** is the workhorse for body text, chosen for its exceptional legibility in dense data grids and forms.

A unique addition is **JetBrains Mono** for labels and financial figures. This monospaced font ensures that currency values and ID numbers align perfectly in vertical lists, facilitating easier visual comparison of budgets and quantities.

**Mobile Scaling:** Headlines scale down by 20% on mobile devices, while body text remains consistent at 14px to maintain readability. All labels utilize uppercase styling when used for metadata headers to further differentiate from narrative text.

## Layout & Spacing

The system follows a **Fluid-Fixed Hybrid** model. The main content area expands to fill the viewport, but is constrained by a fixed-width global sidebar (Left) and a contextual action panel (Right).

### Grid Strategy
- **Mobile:** Single column layout. Sidebars collapse into an overlay "Drawer" or "Sheet."
- **Desktop:** 12-column grid within the central workspace.
- **Rhythm:** A 4px baseline grid ensures tight vertical rhythm, particularly important for the "Work List" components where vertical space is at a premium.

### Panels
The right-side "Selected Work" panel is a core feature of this design system. It uses a fixed width of 380px on desktop to provide a persistent "Inspect and Act" area, allowing the main list to remain scrollable while actions are always within reach.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** rather than heavy shadows. This keeps the interface feeling "flat" and professional, preventing visual clutter in data-heavy screens.

- **Level 0 (Background):** The base neutral canvas (#F8FAFC).
- **Level 1 (Cards/Sidebar):** Pure white (#FFFFFF) with a 1px border (Slate-200) and a very subtle 4px blur ambient shadow. Used for the main work items.
- **Level 2 (Panels/Modals):** These use a more pronounced "Floating" effect with a 12px blur shadow, indicating they are temporary or contextual layers on top of the primary workspace.
- **Active State:** Items currently selected in a list use a 2px "Inset" border of the Secondary Blue to show focus without shifting the layout.

## Shapes

The design system adopts a **Soft (0.25rem)** roundedness approach. This strikes a balance between the rigid precision of traditional financial software and the approachability of modern SaaS tools.

- **Standard Elements:** Buttons, input fields, and tags use `0.25rem`.
- **Containers:** Main work cards and side panels use `rounded-lg` (0.5rem) to distinguish them as structural containers.
- **Interactive States:** Hover states on list items should reveal a `0.25rem` background fill rather than sharp corners.

## Components

### Buttons & Actions
- **Primary:** Solid Secondary Blue with white text.
- **Secondary/Ghost:** Slate-100 background with Slate-900 text.
- **Action Sidebar Buttons:** Fixed at the bottom of the right panel, these should be full-width to accommodate mobile thumb zones.

### Work Queues (Tabs)
Tabs function as filters for the workbench. They should include a numeric badge (e.g., "Needs Planning (12)"). Active tabs are indicated by a bottom-border and a high-contrast text color.

### Procurement Cards
Cards are the primary unit of the 'Work List'. They must contain:
- **Title:** Hanken Grotesk (Bold).
- **Metadata Row:** Monospaced currency and ID values.
- **Status Chip:** Color-coded based on the Procurement Lifecycle (Indigo/Amber/Emerald).
- **Next Step Hint:** Small body text in a muted slate color to guide the user.

### Status Indicators
Use "Pill" shapes for statuses. The background should be a 10% opacity version of the status color with 100% opacity text for maximum readability without visual heaviness.

### Sidebar/Panels
The sidebar uses a dark theme (Primary Slate) to recede into the background, while the Right-Side Action Panel uses a white theme to bring focus to current tasks. The panel should be collapsible to maximize the data grid when needed.