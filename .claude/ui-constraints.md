# UI Constraints

Apply these opinionated constraints when building a web interface (e.g. if
this repo ever grows a BOM/part-tracker web tool). Not relevant to the
KiCad/OpenSCAD/markdown work this repo is primarily about — kept here only
so `discovery` can inject it if it ever creates a frontend supervisor.

## Stack

- MUST use Tailwind CSS defaults unless custom values already exist or are explicitly requested
- MUST use `motion/react` (formerly `framer-motion`) when JavaScript animation is required
- SHOULD use `tw-animate-css` for entrance and micro-animations in Tailwind CSS
- MUST use `cn` utility (`clsx` + `tailwind-merge`) for class logic

## Components

- MUST use accessible component primitives for anything with keyboard or focus behavior (`Base UI`, `React Aria`, `Radix`)
- MUST use the project's existing component primitives first
- NEVER mix primitive systems within the same interaction surface
- MUST add an `aria-label` to icon-only buttons
- NEVER rebuild keyboard or focus behavior by hand unless explicitly requested

## Interaction

- MUST use an `AlertDialog` for destructive or irreversible actions
- SHOULD use structural skeletons for loading states
- NEVER use `h-screen`, use `h-dvh`
- MUST show errors next to where the action happens

## Animation

- NEVER add animation unless it is explicitly requested
- MUST animate only compositor props (`transform`, `opacity`)
- NEVER animate layout properties (`width`, `height`, `top`, `left`, `margin`, `padding`)
- SHOULD respect `prefers-reduced-motion`

## Accessibility

- MUST meet WCAG AA color contrast (4.5:1 for text, 3:1 for large text/UI)
- MUST ensure all interactive elements are keyboard accessible
- SHOULD provide visible focus indicators
