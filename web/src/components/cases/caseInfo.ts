import { HelpCircle, Landmark, ShieldAlert, type LucideIcon } from 'lucide-react'
import type { Case } from '@/lib/api'

// Shared bits for /cases and /cases/:id (E4, E5). Harassment rules H1-H6: basis RBI's rules on
// recovery agents (12 Aug 2022); H6 is our own threshold. Never "fraud", "fake" or "illegal".

export const RULE_NAMES: Record<string, string> = {
  H1: 'Contact at night (before 8 AM or after 7 PM)',
  H2: 'Threats or abuse',
  H3: 'Contacted family, friends or employer',
  H4: 'Public shaming',
  H5: 'False arrest, court or police claim',
  H6: '5 or more calls in one day (our threshold)',
}

export interface RouteInfo {
  label: string
  icon: LucideIcon
  regulated: boolean
}

/** The complaint route text from the API (F5) -> a short badge. */
export function routeInfo(route: string | null | undefined): RouteInfo {
  const r = route ?? ''
  if (r.startsWith('Regulated lender')) return { label: 'Grievance officer → RBI Ombudsman', icon: Landmark, regulated: true }
  if (r.startsWith('App not found')) return { label: 'Sachet + 1930', icon: ShieldAlert, regulated: false }
  return { label: 'Check the name first', icon: HelpCircle, regulated: false }
}

/** "Day 3 of 30" for a regulated lender (the 30-day wait before the RBI Ombudsman), else "Day 3". */
export function dayLine(c: Pick<Case, 'day' | 'route'>): string {
  const day = c.day ?? 1
  return routeInfo(c.route).regulated ? `Day ${day} of 30` : `Day ${day}`
}

/** Any 12-digit number (Aadhaar-like) shows as XXXX XXXX 1234, as in the evidence PDF. */
export function maskNumbers(text: string | null | undefined): string {
  return (text ?? '').replace(/\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})\b/g, (_m, _a, _b, last) => `XXXX XXXX ${last}`)
}

/** "13 Nov, 11:30 pm" in Indian time. */
export function formatAt(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', {
    day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata',
  })
}

export function uniqueRules(c: Pick<Case, 'events'>): string[] {
  const seen = new Set<string>()
  for (const e of c.events ?? []) for (const r of e.rules ?? []) seen.add(r)
  return [...seen].sort()
}
