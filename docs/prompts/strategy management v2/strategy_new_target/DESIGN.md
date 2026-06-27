---
name: Strategic Workbench
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
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Hanken Grotesk
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Hanken Grotesk
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
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-padding: 24px
  hierarchy-indent: 32px
---

## Brand & Style

This design system is engineered for **Strategic Procurement**, prioritizing high-density information architecture and professional clarity. The brand personality is authoritative yet unobtrusive, functioning as a sophisticated "Workbench" for complex decision-making. 

The aesthetic follows a **Corporate / Modern** style with a focus on:
- **Precision:** Tight alignment and consistent spacing to handle nested hierarchies.
- **Clarity:** A "light" interface that reduces cognitive load during data entry and strategic planning.
- **Efficiency:** Streamlined component borders and a focus on content over decoration.

The target audience consists of procurement directors and strategic planners who require a high-fidelity environment to manage the lineage of 'Strategic Plans > Programs > Objectives > Targets'.

## Colors

The palette is anchored by **Deep Navy (#0f172a)**, providing a strong sense of stability and institutional trust. 

- **Primary:** Deep Navy for primary navigation, headers, and high-emphasis text.
- **Secondary/Tertiary:** Slate Grays (Slate 700 and Slate 500) for sub-headers and supporting information.
- **Neutral:** A range of Slate Grays (50-200) for backgrounds and borders.
- **Functional:** A crisp Blue accent for calls to action, ensuring interactive elements stand out against the monochrome base.

Surfaces are primarily white or very light gray (#f8fafc) to maintain the "Workbench" feel and ensure high legibility.

## Typography

The design system utilizes **Hanken Grotesk** exclusively to provide a modern, geometric, and highly legible experience across all data points.

- **Headlines:** Use tighter letter spacing and bolder weights to establish a clear vertical hierarchy for Strategic Plans and Program titles.
- **Body:** Standardized at 14px for maximum information density without sacrificing readability.
- **Labels:** Small, all-caps labels are used for form field headers and metadata to differentiate them from user-generated content.
- **Scale:** On mobile devices, `headline-xl` should scale down to `headline-lg` (24px) to prevent text wrapping in tight containers.

## Layout & Spacing

The system employs a **Fixed Grid** model for desktop "Workbenches" and a **Fluid Grid** for mobile views. 

- **The Workbench:** A 12-column grid with 24px gutters.
- **Hierarchy Visualization:** To represent the 'Strategic Plans > Programs > Objectives' lineage, a consistent 32px horizontal indent is used for each nested level, often accompanied by a subtle vertical guide rail.
- **Sidebar:** A light-themed, fixed-width sidebar (280px) provides primary navigation.
- **Safe Areas:** Form modals and data entry sheets utilize a 24px internal padding (lg) to ensure content breathes, while input rows use 16px (md) vertical spacing.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Low-Contrast Outlines** rather than aggressive shadows, maintaining a flat, professional "Workbench" aesthetic.

- **Level 0 (Background):** #f8fafc (Slate 50).
- **Level 1 (Cards/Sidebar):** Pure white with a 1px solid border (#e2e8f0). No shadow.
- **Level 2 (Modals/Popovers):** Pure white with a soft, ambient shadow (0px 10px 15px -3px rgba(15, 23, 42, 0.1)).
- **Overlays:** A semi-transparent Slate 900 backdrop at 40% opacity is used for modals to maintain focus on the "New Strategic Plan" or "New Target" tasks.

## Shapes

The design system uses a **Soft (0.25rem)** roundedness approach to strike a balance between a rigorous professional tool and a modern web application.

- **Base (Buttons, Inputs):** 4px (0.25rem) radius for a precise, sharp feel.
- **Large (Cards, Modals):** 8px (0.5rem) radius to define major layout containers.
- **Pill (Status Chips):** 100px radius for high-contrast tags and badges to differentiate them from interactive buttons.

## Components

### Buttons
- **Primary:** Deep Navy (#0f172a) background with White text. Sharp 4px corners.
- **Secondary:** White background with 1px border (#e2e8f0) and Deep Navy text.
- **Ghost:** Transparent background with Slate 600 text, used for secondary actions like "Cancel."

### Input Fields
- **Default:** Light gray background (#f1f5f9) with no border until focused.
- **Focus:** 1px solid border using the Primary Navy color or Accent Blue.
- **Labels:** 12px Hanken Grotesk, Semi-bold, positioned above the field with 8px spacing.

### Cards & Containers
- Cards represent Programs and Objectives. They feature a 1px border and no shadow.
- Use a "Header" section within cards with a light gray fill (#f8fafc) to group title and actions.

### Hierarchy Tree
- Use "L-shaped" connector lines (1px solid, Slate 300) to visually link child elements (Programs) to parents (Strategic Plans).

### Chips/Status
- Small, uppercase text within a pill-shaped container.
- Use subtle background tints (e.g., light green for 'Active', light amber for 'Draft') to indicate status without overpowering the UI.