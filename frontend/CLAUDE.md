# Frontend

React + TypeScript SPA built with Vite. Visualises Riksdagen (Swedish parliament) member voting similarity as an interactive hexagonal grid.

## Dev commands

| Command | What it does |
|---------|-------------|
| `npm run dev` | Start dev server at http://localhost:5173 |
| `npm run build` | Type-check and produce static build in `dist/` |
| `npm test` | Run Vitest suite once |
| `npm run test:watch` | Vitest in watch mode |
| `npm run lint` | ESLint |
| `npm run preview` | Preview the production build locally |

## CSS — CSS Modules

Every component has a co-located `.module.css` file. Import and use as:

```tsx
import styles from './MyComponent.module.css'
<div className={styles.container} />
```

Class names are automatically scoped — two files can both have `.container` without conflict. Write plain CSS inside module files. Use `index.css` only for global resets and custom properties.

## Testing — Vitest + React Testing Library

Tests live next to their source file as `*.test.tsx`. Run with `npm test`.

- Test behaviour through the public interface (what the user sees), not implementation details.
- Prefer `screen.getByRole`, `screen.getByText`, and `userEvent` interactions.
- Vitest globals (`describe`, `it`, `expect`) are available without imports.
- `@testing-library/jest-dom` matchers (`toBeInTheDocument`, `toHaveTextContent`, etc.) are available via the setup file.

## Pipeline JSON

The pipeline exports `frontend/public/data.json` (run `uv run riksdagen` from the repo root). During development, Vite serves `public/` at the root, so `fetch('/data.json')` works in both dev and production.

Schema:

```json
{
  "grid": { "width": 10, "height": 8 },
  "party_colors": { "S": "#E8112d", "M": "#52BDEC" },
  "cells": [
    {
      "row": 0,
      "col": 0,
      "dominant_party": "S",
      "members": [
        {
          "intressent_id": "...",
          "namn": "...",
          "parti": "S",
          "low_confidence": false,
          "metadata": { "kon": "kvinna", "fodd_ar": 1975, "vote_count": 312 }
        }
      ]
    }
  ]
}
```
