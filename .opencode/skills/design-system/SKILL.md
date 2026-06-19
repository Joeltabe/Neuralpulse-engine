---
name: design-system
description: "Token architecture (primitive, semantic, component), component specifications, CSS variables, spacing/typography scales, and strategic slide generation. Use when creating design tokens, systematic design, brand-compliant presentations, or design-to-code handoff with Tailwind theme configuration."
license: MIT
metadata:
  author: nextlevelbuilder
  version: "1.0.0"
---

# Design System

Token architecture, component specifications, systematic design, slide generation.

## Token Architecture

```
Primitive (raw values) → Semantic (purpose aliases) → Component (component-specific)
```

**Example:**
```css
--color-blue-600: #2563EB;          /* Primitive */
--color-primary: var(--color-blue-600);  /* Semantic */
--button-bg: var(--color-primary);       /* Component */
```

## Component Spec Pattern

| Property | Default | Hover | Active | Disabled |
|----------|---------|-------|--------|----------|
| Background | primary | primary-dark | primary-darker | muted |
| Text | white | white | white | muted-fg |
| Border | none | none | none | muted-border |
| Shadow | sm | md | none | none |

## Slide System

Brand-compliant presentations using design tokens + Chart.js.

### Contextual Decision Flow

1. Parse goal/context
2. Search slide strategies → Get strategy + emotion beats
3. For each slide: query layout logic, typography, color logic, backgrounds
4. Generate HTML with design tokens
5. Validate token compliance

### Chart.js Integration

```html
<canvas id="chart"></canvas>
<script>
new Chart(document.getElementById('chart'), {
    type: 'line',
    data: { labels: [...], datasets: [{ ... }] }
});
</script>
```

## Best Practices

1. Never use raw hex in components — always reference tokens
2. Semantic layer enables theme switching (light/dark)
3. Use HSL/OKLCH format for opacity control
4. Slides must use design tokens and CSS variables exclusively
