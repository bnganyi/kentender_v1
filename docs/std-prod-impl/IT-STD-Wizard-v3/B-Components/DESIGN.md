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
  on-surface-variant: '#43474e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#456085'
  primary: '#000b1d'
  on-primary: '#ffffff'
  primary-container: '#002244'
  on-primary-container: '#708ab2'
  inverse-primary: '#adc8f3'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d2e1fa'
  on-secondary-container: '#556379'
  tertiary: '#030a1d'
  on-tertiary: '#ffffff'
  tertiary-container: '#192135'
  on-tertiary-container: '#8088a1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d4e3ff'
  primary-fixed-dim: '#adc8f3'
  on-primary-fixed: '#001c3a'
  on-primary-fixed-variant: '#2d486c'
  secondary-fixed: '#d5e3fc'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2e'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2f'
  on-tertiary-fixed-variant: '#3e465c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
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
  body-sm:
    fontFamily: Public Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
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
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  component-gap: 8px
  gutter: 12px
  container-padding: 16px
  input-height: 28px
  table-row-height: 32px
---

## Brand & Style
Civic Ledger is a design system tailored for government and large-scale public sector management. The brand personality is **Institutional, Transparent, and Authoritative**. It prioritizes clarity and information density over decorative flourish, evoking a sense of stability and trustworthy governance.

The design style is **Corporate Modern**, leveraging a structured "Bento Box" layout and Material-inspired surface hierarchy. It utilizes a conservative, high-contrast color palette to ensure accessibility and readability across diverse user groups. The interface is characterized by clean lines, functional iconography, and a systematic approach to data presentation that feels reliable and efficient.

## Colors
The palette is rooted in deep navy tones to project authority and trust. 

- **Primary (#002244):** A heavy, institutional blue used for core navigation, primary actions, and brand identification.
- **Secondary (#515f74):** A slate blue-grey used for supporting UI elements and interactive states that require less visual weight.
- **Tertiary (#030a1d):** An almost-black shade reserved for high-contrast text and deep background accents.
- **Functional Palettes:** The system employs semantic gradients for status indicators:
    - **Approved:** Emerald green tones signify completion and validity.
    - **Pending:** Amber tones signal the need for attention/review.
    - **Rejected/Error:** Soft red containers with sharp red icons.

## Typography
The system uses **Public Sans** as the workhorse typeface for its clarity and accessibility in official contexts. For data-heavy labels, financial figures, and technical metadata, **JetBrains Mono** is introduced to provide a distinct, legible contrast that feels precise and "computed."

Hierarchy is strictly enforced through weight (SemiBold/Bold for headers) and size. On mobile, `display` sizes should scale down to `headline-lg` to maintain readability without excessive scrolling.

## Layout & Spacing
Civic Ledger utilizes a **fixed grid model** for its main content area, maxing out at 1280px to ensure line lengths remain readable on ultrawide monitors.

- **Sidebar:** A fixed 256px (64 units) left-hand navigation allows for deep information architecture without cluttering the header.
- **Bento Grid:** Dashboard views use a 12-column grid. Key metrics often span 8 columns, while utility widgets (like the calendar) span 4.
- **Rhythm:** An 8px base unit is used for component spacing, while a tighter 4px unit is used for internal element grouping (e.g., label-to-input distance).
- **Responsive:** On mobile, the sidebar collapses into a hamburger menu or bottom bar, and grid columns stack vertically (12-column becomes 1-column).

## Elevation & Depth
Depth is conveyed primarily through **Tonal Layering** rather than heavy shadows. 

- **Surface Levels:** The background uses `surface-bright`. Content cards use `surface-container-lowest` (pure white) to pop against the subtle grey background.
- **Shadows:** A single `shadow-sm` (low-offset, 5% opacity black) is used to indicate interactivity on cards and buttons.
- **Borders:** Crisp `outline-variant` (#c4c6cf) borders define the boundaries of containers, creating a structured, grid-like feel that avoids the "floating" look of many modern consumer apps.

## Shapes
The shape language is conservative and geometric. 

- **Containers:** Dashboard cards and table containers use a standard 4px or 8px radius.
- **Inputs & Search:** Search bars and specific notifications use **Pill-shaped** (full) rounding to distinguish them from structural layout elements.
- **Badges:** Small status chips use a minimal 2px radius, maintaining a sharp, professional look that fits within compact table rows.

## Components
- **Buttons:** Primary buttons are solid navy with white text. Secondary buttons use a hollow outline style with a subtle hover tint. Both use `label-md` for text to maintain a technical feel.
- **Data Tables:** High-density with 32px row heights. Alternating row colors (`surface-bright/50`) enhance readability across long lists.
- **Status Chips:** Small, rectangular indicators with a leading 6px dot. Colors are semantic (Green/Amber/Red) but used at 20-30% opacity for the background to keep the interface calm.
- **Side Navigation:** Active states are marked by a high-contrast right-border and a subtle background tint (`primary-fixed-dim/20`).
- **Progress Bars:** Thin 6px tracks used within metric cards to show budget allocation or goal completion without dominating the visual space.

### Vibrant KPI Cards
Primary metrics are displayed in cards featuring a top-weighted layout: a small label in `data-mono`, followed by a large `kpi-value`. A 4px vertical accent bar in the Primary Navy or Secondary Teal should be placed on the left edge to denote category or status.

### Professional Data Tables
Tables are high-density. Headers use `table-header` with an uppercase treatment and a subtle background fill. Row height is capped at 40px. Cell content uses `body-main` or `data-mono` for IDs.

### Navigation Items
Parent items include a chevron icon on the right for expand/collapse states. Active states are indicated by a subtle background tint of the Secondary Teal at 10% opacity and a solid Teal 3px left-border accent.

### Input Fields
Inputs are outlined with a 1px border. Focus states use a 1px Teal ring. Labels are positioned above the field in `nav-child` weight for maximum clarity in complex forms.