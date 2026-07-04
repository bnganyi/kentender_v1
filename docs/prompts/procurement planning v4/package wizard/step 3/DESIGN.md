---
name: KenTender Enterprise
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
  on-surface-variant: '#44474e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#485f84'
  primary: '#000511'
  on-primary: '#ffffff'
  primary-container: '#001e40'
  on-primary-container: '#6f87ae'
  inverse-primary: '#afc8f2'
  secondary: '#0061a5'
  on-secondary: '#ffffff'
  secondary-container: '#73b5fe'
  on-secondary-container: '#004578'
  tertiary: '#0e0200'
  on-tertiary: '#ffffff'
  tertiary-container: '#381300'
  on-tertiary-container: '#b47858'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#afc8f2'
  on-primary-fixed: '#001b3b'
  on-primary-fixed-variant: '#2f476b'
  secondary-fixed: '#d2e4ff'
  secondary-fixed-dim: '#9fcaff'
  on-secondary-fixed: '#001d36'
  on-secondary-fixed-variant: '#00497e'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#fdb793'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#6a3a20'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  cat-goods: '#6366F1'
  cat-works: '#8B5CF6'
  cat-consultancy: '#06B6D4'
  cat-services: '#EC4899'
  status-success: '#10B981'
  status-warning: '#F59E0B'
  status-error: '#EF4444'
  status-neutral: '#64748B'
typography:
  display-hero:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
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
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  container-max-width: 1440px
  workbench-gutter: 24px
  card-padding: 20px
  stack-gap-md: 16px
  stack-gap-sm: 8px
  sidebar-width: 256px
  header-height: 64px
---

## Brand & Style
The brand personality is authoritative, institutional, and highly organized. It is designed for government and enterprise-scale procurement, emphasizing transparency, rigorous process control, and high-stakes data management.

The design style is **Corporate / Modern**, utilizing a structured Material-inspired framework. It balances a deep, "Trust-Blue" primary palette with a utilitarian grayscale to ensure that complex data remains legible and actionable. The aesthetic is clean and professional, using subtle containers rather than heavy lines to define hierarchy, creating a sense of a modern, digitized bureaucracy.

## Colors
The palette is built on a foundation of deep navy (`#001e40`) to convey stability. A vibrant secondary blue (`#0061a5`) is used for interactive elements and highlights to guide the eye. 

The system employs a specific "Category Palette" to differentiate procurement types (Goods, Works, Consultancy) at a glance. Neutral surfaces use a cooling off-white (`#f7f9fb`) to reduce eye strain during long periods of data entry and review. Surface containers are derived from a tonal scale of the neutral base to create subtle logical groupings without introducing visual noise.

## Typography
The system uses a dual-font strategy. **Hanken Grotesk** is reserved for headlines and hero statements to provide a sharp, contemporary edge to the enterprise identity. **Inter** is the workhorse font for all UI elements, body text, and data tables due to its exceptional legibility at small sizes.

Uppercase styling with tracking (`0.05em`) is used for labels and table headers to create a distinct visual layer for metadata. Font weights are used strategically: 600+ for emphasis and branding, 400 for standard reading paths.

## Layout & Spacing
The layout follows a **Fixed Grid** model within a 1440px max-width container, centered on the screen. It features a persistent left-hand navigation sidebar (256px) and a fixed top app bar (64px) to ensure global controls are always accessible.

The internal rhythm is based on an 8px base unit. Wide gutters (24px) separate major content blocks to prevent the interface from feeling cluttered despite the high density of information. Tabbed interfaces and data tables utilize horizontal scrolling on smaller viewports while maintaining column alignment on desktop.

## Elevation & Depth
Elevation is primarily conveyed through **Tonal Layers** and **Low-Contrast Outlines**. Surfaces are categorized into:
- **Base:** The background layer (`#f7f9fb`).
- **Surface-Lowest:** Primary content cards and containers (`#ffffff`), utilizing a `shadow-sm` for subtle lift.
- **Surface-Low:** Used for inset elements like table headers and search inputs to provide a "carved" or "protected" feel.

Outlines (`#737780` at low opacity) are the primary method of defining boundaries. Shadows are used sparingly—only on the main navigation bars and primary content cards—to maintain a flat, professional profile that doesn't distract from data.

## Shapes
The shape language is **Soft**. Standard buttons and inputs use a 4px (0.25rem) radius. Cards and large containers use a more pronounced 12px (0.75rem) or 16px radius to soften the technical nature of the application. Status chips and indicators use "full" pill-rounding to distinguish them from interactive buttons and structural containers.

## Components
- **Buttons:** Primary buttons are solid navy with white text. Secondary buttons use a white background with a border. All buttons have a scale micro-interaction (`0.96`) on click.
- **Chips:** Used for Categories (e.g., "GOODS") and Statuses (e.g., "Published"). They feature a 10% opacity background of their respective semantic color with high-contrast text.
- **Data Tables:** Headers are `surface-low` with uppercase labels. Rows feature a subtle hover state change. Cell content is vertically centered.
- **Input Fields:** Search bars are borderless but use a `surface-low` background to define their hit area, featuring an inset icon.
- **Cards:** White background, `shadow-sm`, and a 12px border radius. Used to group KPI metrics and major content sections.
- **Navigation:** The sidebar uses a high-contrast active state (Background: `surface-container-high`, Border-right: 2px Primary) to indicate location.