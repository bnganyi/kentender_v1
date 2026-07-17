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
  on-surface-variant: '#434750'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737781'
  outline-variant: '#c3c6d1'
  surface-tint: '#395e9b'
  primary: '#001f48'
  on-primary: '#ffffff'
  primary-container: '#00346f'
  on-primary-container: '#7b9ee0'
  inverse-primary: '#abc7ff'
  secondary: '#01629d'
  on-secondary: '#ffffff'
  secondary-container: '#7bbeff'
  on-secondary-container: '#004c7c'
  tertiary: '#102135'
  on-tertiary: '#ffffff'
  tertiary-container: '#26364b'
  on-tertiary-container: '#8f9fb8'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d7e2ff'
  primary-fixed-dim: '#abc7ff'
  on-primary-fixed: '#001b3f'
  on-primary-fixed-variant: '#1d4681'
  secondary-fixed: '#cfe5ff'
  secondary-fixed-dim: '#99cbff'
  on-secondary-fixed: '#001d34'
  on-secondary-fixed-variant: '#004a78'
  tertiary-fixed: '#d3e4ff'
  tertiary-fixed-dim: '#b7c8e2'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485e'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  emerald-available: '#10B981'
  amber-reserved: '#F59E0B'
  indigo-committed: '#6366F1'
  rose-exhausted: '#EF4444'
  surface-white: '#ffffff'
  border-subtle: '#E2E8F0'
typography:
  headline-lg:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
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
  data-mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
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

The design system is a high-performance framework designed for **Decision Support**. It prioritizes **Cognitive Ergonomics**, transforming complex fiscal datasets into actionable insights for procurement officers and executives. The brand personality is authoritative, strategic, and enabling—moving away from the "restrictive ledger" trope toward a "strategic partner" persona that provides essential financial guardrails.

The aesthetic is **Corporate / Modern** with a strict **Minimalist** discipline to manage extreme information density. The visual strategy relies on:
- **Spatial Canvas:** Utilizing expansive whitespace and distinct data blocks to organize the hierarchy from macro-budgets down to micro-allocations.
- **Dynamic Guardrails:** A functional feedback loop where the UI color-shifts based on funding health (Emerald for success, Amber for warning, Rose for exhausted).
- **Decision Focus:** Reducing technical accounting friction by emphasizing procurement outcomes over raw GL entries.

## Colors

The palette is anchored in **Professional Blues** to establish trust, stability, and brand continuity. 

- **Primary & Secondary:** These deep blues are reserved for brand identity, primary navigation, and high-priority action wayfinding.
- **Dynamic Guardrail Colors:** These serve as the functional intelligence of the UI. **Emerald (Available)**, **Amber (Reserved)**, and **Rose (Exhausted)** provide pre-attentive processing, allowing users to understand budget health before reading a single digit.
- **Neutral Palette:** A cool-gray scale maintains the "Spatial Canvas." The background utilizes a near-white neutral to allow the pure white Data Blocks to stand out with minimal visual noise.

## Typography

Typography establishes a strict distinction between narrative context and financial data.

- **Headlines (Manrope):** Geometric and modern, used for section titles and budget names to provide a contemporary professional feel.
- **Body (Inter):** The workhorse font for descriptions, notes, and general interface text, optimized for readability in dense layouts.
- **Data & Figures (JetBrains Mono):** Mandated for all currency values, budget codes, and fiscal years. Monospacing ensures numerical columns align perfectly for rapid comparison.
- **Label Caps:** Used for structural metadata (e.g., "FUND SOURCE") to categorize information without adding bulk.

## Layout & Spacing

This design system utilizes a **Fluid Grid** model to ensure financial transparency across all device types.

- **The Data Block Model:** Content is encapsulated in logical groups. Each block is separated by a 24px `section-gap` to prevent visual crowding.
- **Information Density:** For complex tables or multi-stage timelines (Draft > Approved), a horizontal overflow pattern is preferred over wrapping to maintain the integrity of the data rows.
- **Responsive Guardrails:** On mobile, a 16px lateral margin is strictly enforced. Elements within data blocks scale fluidly, while gaps between blocks remain fixed to ensure clear structural separation.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layers** and **Low-Contrast Outlines**, avoiding the "fuzzy" look of heavy shadows in favor of a clean, technical aesthetic.

- **Canvas (Level 0):** The foundational surface using the neutral background color.
- **Data Blocks (Level 1):** Pure white surfaces defined by a 1px `border-subtle`. This is the primary work surface.
- **Interactive Layers (Level 2):** Modals and dropdowns use a very soft, 10% opacity shadow tinted with the primary blue color to indicate temporary elevation.
- **State Depth:** Active budget lines or selected states use a 4px left-border accent in the primary color to create focus through saturation rather than shadow.

## Shapes

The shape language is **Rounded**, designed to soften the inherent rigidity of financial data.

- **Structural Elements:** Data blocks, cards, and input fields utilize a 0.5rem (8px) radius.
- **Actionable Elements:** Buttons follow the 8px standard for a unified interactive language.
- **Status Pills:** Budget health indicators and status tags use a full pill-shape (999px) to differentiate them from structural containers, ensuring they are instantly recognizable as metadata.

## Components

### Buttons
- **Primary:** High-contrast solid primary blue with white text. Reserved for finality (e.g., "Approve Budget").
- **Secondary:** Outlined with a 1px `border-subtle`. Used for additive actions like "Add Budget Line."
- **Destructive:** Minimalist text-only buttons using the Rose-exhausted color for "Cancel" or "Void."

### Funding Status Chips
- High-visibility markers using 10% background opacity of the status color with high-contrast text. These communicate the state of the "Dynamic Guardrail."

### Data Blocks (Cards)
- The core container. Features a `label-caps` header for the category, a large `data-mono` figure for the amount, and a subtle footer for strategy links.

### Progress Indicators
- 4px horizontal bars embedded within cards. These show segmented consumption: Indigo (Committed) + Amber (Reserved) vs. the remaining gray track (Available).

### Input Fields
- Understated 1px borders. Upon focus, the border shifts to the secondary blue with a subtle 2px outer glow to provide clear active-state feedback.

### Movement Timeline
- A vertical list component that chronicles "Budget Movements." Each entry uses a specific icon and monospaced figures to describe transfers, releases, or allocations.