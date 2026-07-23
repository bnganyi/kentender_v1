---
name: Civic Ledger
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
  on-surface-variant: '#44474c'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#75777d'
  outline-variant: '#c5c6cd'
  surface-tint: '#525f74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#0e1c2e'
  on-primary-container: '#77859b'
  inverse-primary: '#bac7e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d2e1fa'
  on-secondary-container: '#556379'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#001c3a'
  on-tertiary-container: '#6b85ac'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3fd'
  primary-fixed-dim: '#bac7e0'
  on-primary-fixed: '#0e1c2e'
  on-primary-fixed-variant: '#3a475c'
  secondary-fixed: '#d5e3fc'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2e'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#d4e3ff'
  tertiary-fixed-dim: '#adc8f3'
  on-tertiary-fixed: '#001c3a'
  on-tertiary-fixed-variant: '#2d486c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  status-approved: '#065f46'
  status-approved-bg: '#ecfdf5'
  status-pending: '#92400e'
  status-pending-bg: '#fffbeb'
  status-error: '#ba1a1a'
  status-error-bg: '#fff1f2'
  outline-strong: '#74777f'
  outline-subtle: '#c4c6cf'
typography:
  display:
    fontFamily: Public Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-md:
    fontFamily: Public Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.04em
  headline-lg-mobile:
    fontFamily: Public Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gap-component: 8px
  gutter: 12px
  container-padding: 16px
  max-width: 1280px
  sidebar-width: 256px
---

## Brand & Style

The design system for KenTender is built upon a philosophy of **Technical Authority and Institutional Transparency**. It is designed specifically for the high-stakes environment of public sector procurement, where information density, auditability, and clarity are paramount.

The visual style is a fusion of **Corporate Modernism** and **Functional Minimalism**. It utilizes a structured "Bento-style" layout to organize complex data into digestible modules, ensuring the interface feels "Electronic-first" and schema-driven. The aesthetic avoids decorative fluff in favor of crisp borders, high-contrast typography, and a sober professional palette that evokes the reliability of a ledger. It communicates a message of efficiency and uncompromising government-grade standards.

## Colors

The color palette is strictly institutional, designed to facilitate long periods of administrative work without eye strain while maintaining high accessibility standards.

- **Primary (Navy):** Used for core branding, global navigation, and high-priority action buttons. It represents the "Ledger" foundation.
- **Secondary (Slate):** Utilized for auxiliary icons, utility buttons, and secondary UI text.
- **Neutral (Slate/White):** A multi-tiered grey scale for surface containers that provides depth without relying on shadows.
- **Semantic Statuses:** High-contrast color pairs (Emerald, Amber, and Red) are reserved strictly for system-driven status indicators. These colors must always include a high-contrast text color against a desaturated background container to ensure WCAG compliance.

## Typography

This design system employs a dual-font strategy to separate UI narrative from technical data.

**Public Sans** is the primary typeface for all interface elements, headings, and body copy. It provides an approachable yet official tone suitable for government applications.

**JetBrains Mono** is utilized for data-heavy labels, financial figures, transaction IDs, and technical metadata. This monospaced treatment ensures that numerical data is easily scannable and conveys a sense of precision and "computed" accuracy.

Typography levels are intentionally compact to support high information density. In mobile contexts, the `display` role should be swapped for `headline-lg-mobile` to prevent text wrapping issues.

## Layout & Spacing

The layout follows a **Fixed Grid Model** with a 12-column structure, constrained to a maximum width of 1280px to preserve readability on modern displays.

- **Bento Grid:** The dashboard leverages a Bento-style arrangement where content is grouped into discrete, high-contrast containers. This allows for a modular reflow across different screen sizes.
- **Rhythm:** A 4px base unit drives all spacing. Component gaps use 8px (2 units), while container internal padding defaults to 16px (4 units).
- **Density:** The system prioritizes vertical efficiency. Table rows are capped at a 32px-40px height to ensure a high volume of procurement records can be viewed without excessive scrolling.
- **Side Navigation:** A persistent 256px left-hand sidebar manages deep information architecture, collapsing into a condensed icon bar or hamburger menu on mobile devices.

## Elevation & Depth

Hierarchy in this design system is established through **Tonal Layering** and **Crisp Outlines** rather than traditional drop shadows.

- **Surface Tiers:** Backgrounds use a slightly off-white `neutral`. Active content cards use pure white `#FFFFFF` to create immediate visual separation.
- **Low-Contrast Outlines:** Every card and container is defined by a 1px border using `outline-subtle`. This reinforces the "schema-driven" look and provides structural rigidity to the grid.
- **Interactive Depth:** Shadows are used sparingly (only `shadow-sm` at 5% opacity) and are reserved for indicating a card's "hover" state or the elevation of a modal dialog. This keeps the interface feeling flat, technical, and fast.

## Shapes

The shape language is conservative and geometric to match the institutional brand.

- **Structural Elements:** Most containers, cards, and input fields use a **Soft** (4px) corner radius. This provides just enough softness to feel modern without compromising the "software tool" aesthetic.
- **Micro-Elements:** Status badges and chips use a **Sharp** (2px) radius to maintain crispness within high-density rows.
- **Distinctive Shapes:** Search bars and specific global action buttons may use a **Pill-shaped** radius to distinguish them from the rigid structural grid of the data containers.

## Components

- **Data Tables:** The core of the system. Tables must use high-density 32px rows with 1px `outline-subtle` dividers. Headers should be sticky, using `label-md` in uppercase with a `neutral` background fill.
- **Buttons:**
    - **Primary:** Solid `primary` (Navy) with white text.
    - **Secondary:** Outlined `secondary` (Slate) with 1px border.
    - **Status:** Icons inside buttons should be 16px to maintain a compact footprint.
- **KPI Cards:** Feature a top-weighted layout. The value uses `headline-lg` while the label above uses `label-sm` in JetBrains Mono. A 4px vertical accent bar on the left edge identifies the card's category or status.
- **Status Chips:** Rectangular badges with a subtle color-tinted background. They must include a 6px leading dot in the solid semantic color (e.g., solid Emerald dot on a light Emerald background for "Approved").
- **Inputs:** Outlined style with a 1px border. Focus states use a 1px ring in the `primary` color. Labels are always positioned above the input field using `body-sm` for maximum clarity in complex forms.
- **Side Navigation:** Active items are indicated by a 4px solid vertical bar on the right edge and a subtle background tint of `#f2f4f6`.