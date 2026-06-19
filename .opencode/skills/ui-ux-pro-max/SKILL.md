---
name: ui-ux-pro-max
description: "UI/UX design intelligence suite with 67 styles, 161 palettes, 57 font pairings, 25 charts, 15 stacks (React, Next.js, Vue, Svelte, Astro, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, Nuxt, Jetpack Compose). Use ONLY when user asks to design, build, implement, review, fix, improve, optimize, enhance, refactor, or check UI/UX code for projects like websites, landing pages, dashboards, admin panels, e-commerce, SaaS, portfolio, blog, or mobile apps. Covers: banner design, brand identity, design tokens, slides/presentations, UI styling, and general design."
license: MIT
metadata:
  author: nextlevelbuilder
  version: "2.5.0"
---

# UI/UX Pro Max

Comprehensive UI/UX design intelligence skill suite for OpenCode.

## Available Sub-skills

| Skill | Purpose |
|-------|---------|
| `design` | Master design: logos, CIP, banners, icons, social photos, slides, brand, tokens, UI styling |
| `banner-design` | Multi-format banners: social, ads, web heroes, print (22 styles) |
| `brand` | Brand voice, visual identity, messaging, asset management, consistency |
| `design-system` | Token architecture (primitive→semantic→component), CSS vars, component specs, slide generation |
| `slides` | Strategic HTML presentations with Chart.js, design tokens, copywriting formulas |
| `ui-styling` | shadcn/ui + Tailwind CSS + canvas-based visual design |

## Quick Reference

### Color Palette
Consult the design-system skill for token-based color management.

### Typography
Use the brand skill for font pairing and typography specifications.

### Responsive Breakpoints (Tailwind)
| Breakpoint | Width |
|------------|-------|
| sm | 640px |
| md | 768px |
| lg | 1024px |
| xl | 1280px |
| 2xl | 1536px |

### Component Stack Selection
| Stack | Best For |
|-------|----------|
| shadcn/ui + Tailwind | React, Next.js, Astro, Remix |
| Vue + Nuxt UI | Vue/Nuxt projects |
| SwiftUI | iOS/macOS native |
| React Native / Flutter | Cross-platform mobile |
| Jetpack Compose | Android native |

### Accessibility (WCAG 2.1)
| Level | Contrast Ratio |
|-------|---------------|
| AA normal text | 4.5:1 |
| AA large text | 3:1 |
| AAA normal text | 7:1 |
| AAA large text | 4.5:1 |

## Design Tokens Pattern
```css
/* Primitive */
--color-blue-600: #2563EB;
/* Semantic */
--color-primary: var(--color-blue-600);
/* Component */
--button-bg: var(--color-primary);
```
