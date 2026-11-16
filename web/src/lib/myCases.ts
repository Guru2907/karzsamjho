import type { Case } from '@/lib/api'

// "Cases on this phone" (D59). The app never lists every case: a helper opens one with the borrower's
// code. To save retyping, the cases this phone opened or created are remembered HERE, in this browser
// only (localStorage). Another phone sees nothing. Storage can be blocked or empty, so every read and
// write is wrapped, and the app works without it.

export interface MyCase {
  id: string
  code: string | null
  lender_name: string
  borrower_name: string
  opened_at: string
  closed_at?: string | null        // D60: shown under "Closed"
  close_reason?: string | null
}

const KEY = 'karzsamjho.myCases'

export function myCases(): MyCase[] {
  try {
    const list = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export function rememberCase(c: Case): void {
  const item: MyCase = {
    id: c.id, code: c.code, lender_name: c.lender_name, borrower_name: c.borrower_name, opened_at: c.opened_at,
    closed_at: c.closed_at ?? null, close_reason: c.close_reason ?? null,
  }
  try {
    const rest = myCases().filter((m) => m.id !== c.id)
    localStorage.setItem(KEY, JSON.stringify([item, ...rest].slice(0, 50)))
  } catch {
    // storage blocked: the case still opens, it just is not remembered
  }
}

/** Update a remembered case's status in place, without moving it (the Cases page refresh, D60). */
export function refreshCase(c: Case): void {
  try {
    const list = myCases().map((m) => (m.id === c.id
      ? { ...m, closed_at: c.closed_at ?? null, close_reason: c.close_reason ?? null, code: c.code } : m))
    localStorage.setItem(KEY, JSON.stringify(list))
  } catch {
    // ignore
  }
}

export function forgetCase(id: string): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(myCases().filter((m) => m.id !== id)))
  } catch {
    // ignore
  }
}

/** "48217730" -> "4821 7730", easier to read out. */
export function spacedCode(code: string | null | undefined): string {
  return code && code.length === 8 ? `${code.slice(0, 4)} ${code.slice(4)}` : (code ?? '')
}

/** Any phone number -> "XXXXXX 3210". Done on this phone, so the full number is never sent (D59). */
export function maskPhone(phone: string): string | undefined {
  const digits = phone.replace(/\D/g, '')
  return digits.length >= 4 ? `XXXXXX ${digits.slice(-4)}` : undefined
}
