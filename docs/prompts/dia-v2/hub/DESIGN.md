---
name: KenTender Budget Catalyst
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
  on-surface-variant: '#424751'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737783'
  outline-variant: '#c2c6d3'
  surface-tint: '#255dad'
  primary: '#00346f'
  on-primary: '#ffffff'
  primary-container: '#004a99'
  on-primary-container: '#9bbdff'
  inverse-primary: '#abc7ff'
  secondary: '#00629d'
  on-secondary: '#ffffff'
  secondary-container: '#00a2fd'
  on-secondary-container: '#003558'
  tertiary: '#26364b'
  on-tertiary: '#ffffff'
  tertiary-container: '#3d4d62'
  on-tertiary-container: '#adbed7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d7e2ff'
  primary-fixed-dim: '#abc7ff'
  on-primary-fixed: '#001b3f'
  on-primary-fixed-variant: '#00458f'
  secondary-fixed: '#cfe5ff'
  secondary-fixed-dim: '#98cbff'
  on-secondary-fixed: '#001d33'
  on-secondary-fixed-variant: '#004a77'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  status-available: '#10B981'
  status-reserved: '#F59E0B'
  status-committed: '#6366F1'
  status-exhausted: '#EF4444'
  data-block-bg: '#FFFFFF'
  border-subtle: '#E2E8F0'
typography:
  headline-lg:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  headline-sm:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
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
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 16px
  gutter: 12px
  section-gap: 24px
  card-padding: 20px
---

## Brand & Style

The design system is engineered for **Decision Support** within the KenTender ecosystem. It prioritizes **Cognitive Ergonomics**, ensuring that complex financial data is parsed effortlessly by procurement officers and executives. The brand personality is authoritative yet enabling—positioning the software not as a restrictive ledger, but as a strategic partner that provides the "financial guardrails" for organizational success.

The aesthetic follows a **Corporate / Modern** movement with a heavy emphasis on **Minimalism** to manage information density. Key characteristics include:
- **Spatial Canvas:** Using data blocks and generous whitespace to separate hierarchical levels (Budget > Line > Allocation).
- **Dynamic Guardrails:** A systematic approach to visual feedback where the UI shifts state based on funding health (Success for available, Warning for reserved, Error for exhausted).
- **Decision Focus:** Reducing the visibility of technical accounting jargon (GL entries, mutations) in favor of actionable procurement outcomes.

## Colors

The palette is anchored in **Professional Blues** to establish trust and continuity with the KenTender brand. 

- **Primary & Secondary:** Used for brand identity, primary actions, and navigational wayfinding.
- **Dynamic Guardrail Colors:** These are the functional core of the system. **Emerald (Available)**, **Amber (Reserved)**, and **Rose (Exhausted/Error)** provide immediate visual confirmation of funding status without requiring the user to read specific values first.
- **Neutral Palette:** Utilizes a cool-gray scale to maintain a clean "Spatial Canvas." Backgrounds use a near-white `neutral_color_hex` to make the white "Data Blocks" pop with subtle elevation.

## Typography

Typography is used to create a clear information hierarchy, distinguishing between narrative content and financial data.

- **Headlines (Manrope):** Chosen for its modern, geometric balance. It feels professional and contemporary, ideal for budget headers and section titles.
- **Body (Inter):** A systematic typeface that excels in readability at small sizes, used for descriptions and supporting text.
- **Data & Figures (JetBrains Mono):** Used specifically for currency values, budget codes, and fiscal years. The monospaced nature ensures that columns of numbers align perfectly, aiding in quick comparison and "Cognitive Ergonomics."
- **Label Caps:** Used for metadata tags (e.g., "FISCAL YEAR", "FUND SOURCE") to provide structure without cluttering the canvas.

## Layout & Spacing

The layout utilizes a **Fluid Grid** for mobile, ensuring that data blocks expand to the full width of the viewport while maintaining consistent margins. 

- **The Data Block Model:** Content is grouped into logical "blocks" (e.g., Budget Header, Funding Breakdown, Linked Demands). Each block is separated by a `section-gap` of 24px to prevent visual overwhelm.
- **Horizontal Scrolling Tiers:** For dense financial tables or status timelines (Draft > Submitted > Approved), a horizontal overflow pattern is used to keep the primary interface clean.
- **Safe Areas:** Mobile designs must respect a 16px lateral margin (`container-padding`) to ensure high-density data remains readable and touch-targets are accessible.

## Elevation & Depth

This design system uses **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows to maintain a professional, "flat-plus" aesthetic.

- **Level 0 (Canvas):** The base background layer in `neutral_color_hex`.
- **Level 1 (Data Blocks):** White surfaces with a 1px border (`border-subtle`). These house the primary content.
- **Level 2 (Modals/Overlays):** Used for "Funding Check" or "Reservation" actions. These utilize a soft, 10% opacity primary-tinted shadow to indicate they sit above the work surface.
- **Depth through Saturation:** Hierarchy is also achieved by increasing the color saturation of active elements (e.g., an active Budget Line has a subtle primary-color left-border accent).

## Shapes

The shape language is **Rounded**, striking a balance between the rigidity of traditional finance and the approachability of a modern SaaS tool. 

- **Cards & Data Blocks:** Use a 0.5rem (8px) radius to soften the interface.
- **Interactive Elements:** Buttons and input fields mirror this 8px radius for consistency.
- **Status Pills:** Use a full pill-shape (999px) to distinguish them from structural elements, making them instantly recognizable as status indicators (e.g., "Active", "Exhausted").

## Components

### Buttons
- **Primary:** Solid `primary_color_hex` with white text. Used for "Approve Budget" or "Submit Revision."
- **Secondary/Ghost:** Outlined buttons for secondary actions like "Add Budget Line."
- **Destructive:** Minimalist text-only buttons in `status-exhausted` red for "Cancel" or "Delete" actions.

### Funding Status Chips (Dynamic Guardrails)
- High-visibility chips using the named status colors. 
- **Available:** Green background (10% opacity) with dark green text.
- **Exhausted:** Red background (10% opacity) with dark red text.

### Data Blocks (Cards)
- The primary container for budget information. 
- Contains a `label-caps` header, a large `data-mono` figure, and a footer with "Linked Strategy" information.

### Progress Indicators (Budget Consumption)
- A thin, 4px horizontal bar inside data blocks showing the ratio of Reserved + Committed vs. Approved funds. 
- The bar segments are color-coded: Indigo for Committed, Amber for Reserved, Gray for Available.

### Input Fields
- Professional, understated styling with a 1px border. 
- On focus, the border transitions to `secondary_color_hex` with a soft 2px outer glow.

### Movement Timeline
- A vertical list component showing "Budget Movements." Each entry uses a small icon and `body-md` text to describe the movement type (Allocation, Transfer, Release).