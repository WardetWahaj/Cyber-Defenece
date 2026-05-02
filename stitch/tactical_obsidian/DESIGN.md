# Design System Specification: Tactical Obsidian Philosophy
**Project:** CyberDefence Analyst Platform v3.1  
**Directive:** High-Density, Authoritative, Enterprise Cybersecurity  

---

## 1. Overview & Creative North Star: "The Silent Sentinel"

This design system is built to convey absolute authority and precision. Moving away from the generic "SaaS Blue" templates, we adopt the **Tactical Obsidian** philosophy—a visual language inspired by advanced command centers and high-end hardware interfaces. 

Our Creative North Star is **"The Silent Sentinel."** The UI does not shout; it hums with quiet intensity. We achieve this through high data density, intentional asymmetry, and a focus on tonal depth over structural lines. By utilizing overlapping surfaces and editorial-grade typography, we create an environment where the analyst feels in total control of a complex digital landscape. This isn't just a dashboard; it’s a high-precision instrument.

---

## 2. Color Architecture & Tonal Layering

The palette is rooted in the deep void of `#0b1326`, using incremental shifts in luminosity to define space.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders for sectioning or containment. Boundaries must be defined through background color shifts or subtle tonal transitions.

### Surface Hierarchy & Nesting
Instead of a flat grid, treat the interface as a series of machined layers. Use the following tiers to create "nested" depth:
- **Background (Base):** `#0b1326` — The foundation of the application.
- **Surface (Low):** `#131b2e` — Standard content areas and sidebars.
- **Surface High (Medium):** `#222a3d` — Hover states, active cards, or focused workspace panels.
- **Surface Highest (Top):** `#2d3449` — Modals, popovers, and high-priority tooltips.

### Signature Textures & Gradients
To provide visual "soul," primary actions should not be flat.
- **The Obsidian Gradient:** Use a linear transition from `Primary Blue (#3B82F6)` to `Dark Blue (#2563eb)` at a 135-degree angle for main CTAs.
- **Glassmorphism:** For floating HUD elements (like a global search or active threat monitor), use the `Surface Highest` color at 70% opacity with a `20px` backdrop-blur.

---

## 3. Typography: Editorial Authority

We use **Inter** not as a default, but as a technical typeface capable of extreme legibility at high densities.

| Token | Size/Weight | Usage |
| :--- | :--- | :--- |
| **Display Large** | 32px / 700 | Critical KPIs and high-level security status. |
| **Headline Large** | 24px / 700 | Major module headers and primary section titles. |
| **Title Medium** | 18px / 600 | Card titles and subsection headers. |
| **Body Med** | 14px / 400 | Standard data entries and analytical descriptions. |
| **Label Small** | 11px / 700 | Monospace-style metadata and system timestamps. |

**Hierarchy Note:** Use `Text Primary (#dae2fd)` for all critical data. `Text Secondary (#c3c6d7)` should be reserved for descriptions, while `Text Muted (#8d90a0)` is strictly for tertiary metadata or disabled states.

---

## 4. Elevation & Depth: The Stacking Principle

In this design system, depth is earned, not given. We avoid traditional drop shadows in favor of ambient light.

- **Stacking Logic:** Place a `Surface High` component on top of a `Surface` background to create a "recessed" or "protruding" look naturally. 
- **Ambient Shadows:** When a floating effect is required (e.g., a context menu), use a shadow with a `24px` blur, `0%` spread, and `#000000` at `40%` opacity. It must feel like the element is casting a shadow onto deep glass.
- **The Ghost Border Fallback:** If accessibility requirements demand a container edge, use the `Border Ghost` token: `#434655` at **15% opacity**. This creates a "glint" on the edge of the obsidian surface rather than a hard line.
- **Interactive Depth:** On hover, a card should not move "up" (Y-axis). Instead, it should transition from `Surface` to `Surface High`, simulating a change in internal illumination.

---

## 5. Component Logic

### Buttons
- **Primary:** `Obsidian Gradient` (Blue to Dark Blue). Text: `White`. No border. Radius: `md (4px)`.
- **Secondary:** Surface High background. Text: `Text Primary`. Subtle `Ghost Border`.
- **Tertiary/Ghost:** Transparent background. Text: `Primary Blue`. 

### Threat Status Chips
Status is conveyed through high-contrast color against the dark obsidian base:
- **Critical:** `#DC2626` background, `White` text.
- **Success:** `#45dfa4` background, `#0b1326` text (high contrast).
- All chips use `sm (2px)` radius to maintain a technical, "blocky" feel.

### Input Fields
Inputs must feel recessed into the UI.
- **Default:** `Surface` background, 1px `Ghost Border` (15% opacity).
- **Focus:** `Surface High` background, `Primary Blue` glow (2px outer blur).
- **Constraint:** Labels must be `Label Small` and always visible (never floating).

### Lists & Data Grids
- **No Dividers:** Vertical white space and alternating row colors (using `Background` and `Surface`) must replace line-based dividers.
- **Density:** Maintain a tight vertical rhythm. Row heights should not exceed `40px` for standard data tables to maximize information density.

---

## 6. Do’s and Don’ts

### Do
- **Do** use asymmetrical layouts to guide the eye toward critical alerts.
- **Do** overlap elements (e.g., a floating detail panel overlapping a data grid) to imply a multi-layered workspace.
- **Do** use `Text Muted` for units (e.g., "ms", "kb/s") to keep the focus on the numerical value.

### Don’t
- **Don't** use 100% opaque borders. They clutter the visual field and break the "Obsidian" flow.
- **Don't** use rounded corners larger than `lg (6px)`. This is a professional tool, not a consumer social app; overly rounded corners feel "soft" and unauthoritative.
- **Don't** use pure white (#FFFFFF) for text. It causes eye strain in dark environments; always use `Text Primary (#dae2fd)`.

---
*End of Specification*