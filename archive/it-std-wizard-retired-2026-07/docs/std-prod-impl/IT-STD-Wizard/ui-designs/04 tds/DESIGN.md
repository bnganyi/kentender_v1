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

The design system is engineered for **Decision Support** within the KenTender ecosystem. It prioritizes **Cognitive Ergonomics**, ensuring that complex financial data is parsed effortlessly by procurement officers and executives.

## Data Table Standards

All screens containing high-density data tables must adhere to the following structural rules to ensure consistent governance and scanning efficiency.

### Table Header Layout
The header area above any primary data table must use a two-tier or unified horizontal layout:
- **Search Bar (Left):** A prominent text input with a magnifying glass icon. Placeholder should specific the searchable attributes (e.g., "Search Tender Ref / Title...").
- **Quick Filters (Center):** 3-4 dropdown menus for high-frequency filtering (e.g., Status, Entity, Method). 
- **Advanced Controls (Right):** 
    - **"More Filters" Button:** A ghost or outlined button with a filter icon that opens a right-side drawer.
    - **Drawer Structure:** Categorized filters (Identity, Tracking, Governance) with multi-select capabilities.

### Table Footer Layout
The footer provides navigation and view control. It must include:
- **Left Alignment:** Record count indicator (e.g., "Showing 1-10 of 25") using `body-md` typography.
- **Right Alignment:** 
    - **Rows Selector:** A "Rows:" label followed by a dropdown menu (e.g., 10, 25, 50, 100).
    - **Numbered Pagination:** A list of page numbers with clear "Next" and "Previous" arrows. The active page must be highlighted using the `primary` color theme.

### Interaction Rules
- **Row States:** Rows must remain **strictly static** on hover (no background shifts, elevation changes, or animations) to prevent "dancing" effects during rapid scanning.
- **Action Menus:** Row-level overflow menus must use a high `z-index` and a global stacking context to ensure they float over all other content (header, footer, adjacent rows) without clipping.