---
name: ui-styling
description: "Create beautiful, accessible user interfaces with shadcn/ui (Radix UI + Tailwind) and Tailwind CSS. Use when building UI, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes, implementing dark mode, generating visual designs, or establishing consistent styling patterns."
license: MIT
metadata:
  author: nextlevelbuilder
  version: "1.0.0"
---

# UI Styling

shadcn/ui + Tailwind CSS + canvas-based visual design.

## Core Stack

- **Component Layer**: shadcn/ui (pre-built accessible components via Radix UI primitives)
- **Styling Layer**: Tailwind CSS (utility-first, build-time processing)
- **Visual Design Layer**: Canvas (museum-quality visual compositions)

## Quick Start

```bash
npx shadcn@latest init
npx shadcn@latest add button card dialog form
```

## Theme & Dark Mode

Use `next-themes` with Tailwind dark variant:
```tsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
```

## Component Patterns

**Form with validation:**
```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
```

**Responsive grid:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```

## Best Practices

1. Component Composition: Build complex UIs from simple, composable primitives
2. Utility-First Styling: Use Tailwind classes directly
3. Mobile-First Responsive: Start with mobile styles, layer responsive variants
4. Accessibility-First: Leverage Radix UI primitives
5. Design Tokens: Use consistent spacing scale, color palettes, typography system
6. Dark Mode Consistency: Apply dark variants to all themed elements
7. TypeScript: Use full type safety

## Resources

- shadcn/ui Docs: https://ui.shadcn.com
- Tailwind CSS Docs: https://tailwindcss.com
- Radix UI: https://radix-ui.com
