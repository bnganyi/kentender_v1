---
name: KenTender Catalyst
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
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#002113'
  on-tertiary-container: '#009668'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
  max-width: 1440px
---

## Brand & Style
The brand personality of the design system is defined by a synthesis of **Minimalism** and **Corporate Modernism**. It is engineered to evoke a sense of precision, reliability, and high-velocity efficiency. The target audience consists of enterprise stakeholders and technical professionals who require a tool that prioritizes clarity and functional density without sacrificing aesthetic refinement.

The visual style utilizes expansive whitespace to reduce cognitive load, paired with high-quality, systematic typography that ensures information hierarchy is immediate and intuitive. This design system maintains a professional and balanced posture, drawing inspiration from contemporary software standards while asserting a unique identity through disciplined execution and a focused, utilitarian elegance.

## Colors
The color strategy employs a deep Navy primary (`#0F172A`) to anchor the interface with authority and trust. A vibrant Blue secondary (`#3B82F6`) is utilized for primary actions and interactive states, providing high-contrast affordances against the Slate-based neutral scale. An Emerald tertiary (`#10B981`) is reserved for success states and growth indicators.

The default color mode is **light**. The background surfaces should utilize the neutral tint to differentiate between the canvas and nested containers, maintaining a sophisticated, high-clarity environment.

## Typography
This design system utilizes a three-tier typographic stack to balance brand character with technical utility. **Hanken Grotesk** is used for headlines to provide a sharp, contemporary edge. **Inter** serves as the workhorse for body copy, ensuring maximum readability across all screen densities. **JetBrains Mono** is introduced for labels, metadata, and technical strings to reinforce the "Catalyst" theme of precision and data-driven logic.

Maintain strict adherence to the defined line heights to preserve vertical rhythm. Headline tracking is slightly tightened for impact, while labels are loosened to improve legibility at small scales.

## Layout & Spacing
The layout follows a **fluid grid** model based on a 12-column system for desktop and a 4-column system for mobile. A strict 4px baseline grid governs all internal component spacing and vertical rhythm.

- **Desktop (1024px+):** 12 columns, 24px gutters, 48px side margins.
- **Tablet (768px - 1023px):** 8 columns, 16px gutters, 32px side margins.
- **Mobile (Up to 767px):** 4 columns, 16px gutters, 16px side margins.

Use `lg` and `xl` spacing tokens for section-level separation, while `sm` and `md` are reserved for internal component padding and proximity grouping.

## Elevation & Depth
Elevation is conveyed through **Tonal Layers** and **Ambient Shadows**. Instead of heavy shadows, the design system utilizes subtle background shifts (Surface-to-Container) to indicate hierarchy. 

When depth is required for transient elements like modals or dropdowns, use highly diffused, low-opacity shadows (`0px 4px 20px rgba(15, 23, 42, 0.08)`). Surfaces are reinforced with a 1px low-contrast outline (`#E2E8F0`) to maintain structural integrity in high-density layouts, ensuring elements remain distinct without the need for aggressive visual weight.

## Shapes
The shape language is defined as **Soft**, prioritizing a professional and tailored appearance. This choice avoids the clinical feel of sharp corners while remaining more formal than fully rounded systems.

- **Standard Elements (Buttons, Inputs):** 0.25rem (4px)
- **Large Elements (Cards, Modals):** 0.5rem (8px)
- **Extra Large Elements (Promos, Hero containers):** 0.75rem (12px)

Consistency in radius helps harmonize different UI elements, creating a cohesive visual language that feels engineered and intentional.

## Components
- **Buttons:** Primary buttons use the `secondary_color_hex` with white text; secondary buttons use a ghost style with a 1px border. Use `label-md` for button text.
- **Inputs:** Fields are defined by a 1px border (`#CBD5E1`) and a subtle inner shadow. Focus states must use a 2px `secondary_color_hex` ring with an offset.
- **Cards:** Cards should have a white background, a 1px border (`#E2E8F0`), and the `rounded-lg` radius. Use internal padding of `lg` (24px).
- **Chips/Badges:** Use `label-sm` typography with high-contrast background tints and 100px pill rounding to distinguish them from actionable buttons.
- **Lists:** List items should have a 1px bottom border and utilize `md` spacing for vertical padding.
- **Checkboxes/Radios:** Use the `secondary_color_hex` for active states with a crisp white inner icon/dot for high visibility.


# Canonical Layout Standards

These patterns are locked for all subsequent designs in the IT Tender Configuration Wizard to ensure perfect parity with the established dashboard standards.

## Global Top Bar
- **Product Title:** Left-aligned text in `primary` color using `headline-sm`.
- **Separator:** A thin 1px grey vertical line (`outline-variant`) between title and current screen name.
- **User Profile:** Far-right aligned. Includes Agency/User avatar and name.
- **Exclusion:** Navigation tabs are explicitly forbidden in this toolbar.

## Page Header Stack
- **Hierarchy:** H1 Title (`headline-md`) on top, directly followed by a supporting Subtitle (`body-md`) with `base` spacing.
- **Spacing:** `xl` (32px) bottom margin to separate from the main content/table.

## Table Governance Shell
- **Search & Filter Bar:** Full-width container above the table. Includes a left-aligned search input and a right-aligned "More Filters" button.
- **Filter Cloud:** A `flex-wrap` container below the search bar where applied filter chips appear.
- **Row Pattern:** Multi-content column layout. Primary data in `body-lg` / bold, with secondary metadata in `label-sm` using `JetBrains Mono`.
- **Standardized Footer:** 
  - **Left:** "Showing X-Y of Z" record count.
  - **Right:** Rows-per-page dropdown and numbered pagination with active state highlighting.