import { AlertTriangle } from 'lucide-react'
import { RULE_NAMES, routeInfo } from './caseInfo'

// Small shared components for /cases and /cases/:id (E4, E5); the helpers are in caseInfo.ts.

export function RouteBadge({ route }: { route: string | null | undefined }) {
  const info = routeInfo(route)
  const Icon = info.icon
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted px-2 py-1 text-xs font-medium text-foreground">
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {info.label}
    </span>
  )
}

/** Red rule chips with their meaning: colour + icon + words, never colour alone. */
export function RuleBadges({ rules, named = false }: { rules: string[]; named?: boolean }) {
  if (!rules.length) return null
  return (
    <div className="flex flex-wrap gap-1.5">
      {rules.map((r) => (
        <span
          key={r}
          title={RULE_NAMES[r] ?? r}
          className="inline-flex items-center gap-1 rounded-md bg-red-700/10 px-2 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-400/10 dark:text-red-400"
        >
          <AlertTriangle className="size-3" aria-hidden />
          {named ? `${r} · ${RULE_NAMES[r] ?? ''}` : r}
        </span>
      ))}
    </div>
  )
}

export function RulesLegend() {
  return (
    <div className="space-y-1.5 rounded-2xl border border-border bg-card p-4 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground">What the rules mean</p>
      {Object.entries(RULE_NAMES).map(([k, v]) => (
        <p key={k}>
          <span className="font-semibold text-foreground">{k}</span> {v}
        </p>
      ))}
      <p className="pt-1">Basis: RBI rules on recovery agents (12 Aug 2022). H6 is our own threshold.</p>
    </div>
  )
}
