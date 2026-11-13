# web/ (frontend)

React + Vite + TypeScript + Tailwind + shadcn/ui. Icons: lucide-react only.

- `src/pages/`: one file per route: `/` Landing (H1-H3), `/check` (E2, E3, E7), `/cases` (E4), `/cases/:id` (E5).
- `src/components/ui/`: shadcn components (button, card, badge, dialog, input, tabs, sonner). Add more with `npx shadcn@latest add <name>`.
- `src/components/TopBar.tsx`: the shared top bar with the light/dark toggle.
- `src/lib/api.ts`: every API call and the TypeScript types. Pages never call `fetch` directly.

Run: `npm install` once, then `npm run dev -- --host`. The dev server sends `/api` calls to `http://localhost:8000`, so start the API first.
Tasks in docs/TASKS.md that touch this folder: E1-E8, H1-H3.
