---
name: KenTender Decision System
colors:
  surface: '#f8f9fb'
  surface-dim: '#d9dadc'
  surface-bright: '#f8f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f6'
  surface-container: '#edeef0'
  surface-container-high: '#e7e8ea'
  surface-container-highest: '#e1e2e4'
  on-surface: '#191c1e'
  on-surface-variant: '#434654'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f3'
  outline: '#737685'
  outline-variant: '#c3c6d6'
  surface-tint: '#0c56d0'
  primary: '#003d9b'
  on-primary: '#ffffff'
  primary-container: '#0052cc'
  on-primary-container: '#c4d2ff'
  inverse-primary: '#b2c5ff'
  secondary: '#00687b'
  on-secondary: '#ffffff'
  secondary-container: '#50dcff'
  on-secondary-container: '#005f71'
  tertiary: '#3d4354'
  on-tertiary: '#ffffff'
  tertiary-container: '#545a6c'
  on-tertiary-container: '#ccd2e7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b2c5ff'
  on-primary-fixed: '#001848'
  on-primary-fixed-variant: '#0040a2'
  secondary-fixed: '#afecff'
  secondary-fixed-dim: '#48d7f9'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5d'
  tertiary-fixed: '#dce2f8'
  tertiary-fixed-dim: '#c0c6db'
  on-tertiary-fixed: '#151b2b'
  on-tertiary-fixed-variant: '#404658'
  background: '#f8f9fb'
  on-background: '#191c1e'
  surface-variant: '#e1e2e4'
  status-available: '#10B981'
  status-reserved: '#F59E0B'
  status-exhausted: '#E11D48'
  data-committed: '#6366F1'
  border-subtle: '#DFE1E6'
typography:
  headline-lg:
    fontFamily: Manrope
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
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
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-padding: 1rem
  section-gap: 1.5rem
  gutter-md: 1rem
  stack-sm: 0.5rem
  stack-xs: 0.25rem
---

## Brand & Style

The design system is centered on **Decision Support** and **Cognitive Ergonomics**, specifically tailored for the Kenyan public procurement sector. The brand personality is authoritative, strategic, and enabling, moving away from restrictive ledgers toward a partnership-driven interface that provides clear financial guardrails.

The aesthetic follows a **Corporate / Modern** movement with a **Minimalist** execution. The UI is designed as a "Spatial Canvas" to manage high information density without overwhelming the user. It utilizes a **Flat-Plus** aesthetic, where depth is communicated through subtle tonal changes and purposeful borders rather than heavy ornamentation. The primary goal is to transform technical accounting data into actionable procurement outcomes.

## Colors

The palette uses **Professional Blues** to establish trust and institutional reliability. 

- **Primary & Secondary:** Reserved for branding, navigational wayfinding, and primary calls to action.
- **Dynamic Guardrails:** This functional trio—**Emerald (Available)**, **Amber (Reserved)**, and **Rose (Exhausted)**—serves as the cognitive shortcut for funding health. These colors must be used consistently to signal status before a user even reads the numerical data.
- **Neutral Palette:** A cool-gray scale is used for the "Spatial Canvas." The `neutral_color_hex` is applied to the main background, allowing white "Data Blocks" to stand out with minimal elevation.

## Typography

Typography is used to distinguish narrative context from financial figures, enhancing "Cognitive Ergonomics."

- **Headlines (Manrope):** Used for section titles and budget headers. It provides a contemporary, geometric balance.
- **Body (Inter):** The workhorse for descriptions, instructions, and standard UI text. It is optimized for high legibility at various scales.
- **Data & Figures (JetBrains Mono):** Mandatory for all currency values, budget codes, and fiscal years. Its monospaced nature ensures vertical alignment in tables, allowing for rapid comparison of figures.
- **Label Caps:** Used for metadata (e.g., "FUND SOURCE") to provide structural cues without adding visual noise.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a specific focus on "Data Blocks."

- **Data Block Model:** Logical groupings (e.g., Budget Details, Line Allocations) are contained within discrete blocks. These blocks should be separated by a `section-gap` (24px) to create a clear visual hierarchy.
- **Mobile Reflow:** On mobile devices, data blocks expand to full width. Lateral margins must maintain a `container-padding` of 16px to protect readability.
- **Horizontal Tiers:** For dense financial tables that exceed the viewport, use horizontal overflow patterns with sticky headers/columns to keep context visible.
- **Responsive Breakpoints:** 
  - **Mobile:** < 600px (1-column stack).
  - **Tablet:** 600px - 1024px (2-column grid for smaller blocks).
  - **Desktop:** > 1024px (Multi-column dashboard with 24px gutters).

## Elevation & Depth

This system utilizes **Tonal Layers** and **Low-Contrast Outlines** to achieve its "flat-plus" look.

- **Canvas (Level 0):** The background uses `neutral_color_hex`.
- **Data Blocks (Level 1):** These are the primary containers. They feature a white background and a 1px `border-subtle`. No shadows are used at this level.
- **Interactive Layers (Level 2):** Modals, dropdowns, and focused inputs use a soft shadow (10% opacity) tinted with the `primary_color_hex` to suggest they are floating above the work surface.
- **Contextual Accents:** Active states (like a selected budget line) are indicated by a 4px solid left-border in the primary color, providing depth through saturation rather than shadow.

## Shapes

The shape language is consistently **Rounded** to soften the institutional nature of procurement.

- **Structural Elements:** Data blocks, cards, and input fields use an 8px (0.5rem) radius.
- **Buttons:** Mirror the 8px radius for a professional, cohesive feel.
- **Status Pills:** Use a full pill-shape (999px) for status indicators. This distinct geometry separates them from structural blocks, signaling that they represent a "state" rather than a "container."

## Components

### Buttons
- **Primary:** Solid `primary_color_hex` with white text. Used for definitive actions (e.g., "Approve").
- **Secondary:** Outlined with `border-subtle` and primary-colored text. Used for supportive actions.
- **Destructive:** Text-only or ghost buttons using `status-exhausted` red for high-risk actions like "Cancel."

### Funding Status Chips
- **Dynamic Guardrails:** High-visibility pills. 
- **Style:** Background at 10% opacity of the status color with the text at 100% opacity of the same color (e.g., Light Emerald background with Dark Emerald text).

### Data Blocks (Cards)
- The core container. Includes a `label-caps` header, a prominent `data-lg` figure for the total amount, and a `body-sm` footer for metadata.

### Progress Indicators
- A 4px high horizontal bar used for "Budget Consumption."
- **Color Coding:** Use `data-committed` (Indigo) for committed funds, `status-reserved` (Amber) for reserved, and a light gray for the remaining available balance.

### Input Fields
- Understated 1px border. On focus, the border changes to `secondary_color_hex` with a subtle 2px glow. Labeling uses `label-caps` for clarity.

### Movement Timeline
- A vertical list for tracking fiscal mutations. Each entry uses a small icon and `body-md` text to describe the movement (e.g., "Allocation," "Transfer").