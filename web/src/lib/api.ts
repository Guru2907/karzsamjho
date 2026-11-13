// Typed helpers for the KarzSamjho API. Shapes match CLAUDE.md ("API contract").
// Do not change these types without the whole team agreeing.

export type Status = 'read' | 'derived' | 'computed' | 'unverified'
export type Verdict = 'USUAL' | 'COSTLY' | 'VERY_COSTLY' | 'CANNOT_SAY'
export type LenderMatch = 'FOUND' | 'SIMILAR' | 'NOT_FOUND'

export interface NumberField {
  value: number | null
  status: Status
}

export interface CheckResult {
  id: string
  verdict: Verdict
  numbers: Record<string, NumberField>
  unverified: string[]
  lender: {
    name_read: string | null
    match: LenderMatch
    score: number | null
    closest: string | null
    list_date: string | null
  }
  next_step: { code: string; text_hi: string }
  speech_text_hi: string
  audio_url: string | null
  engines: { read: string | null; second_read: string | null; speak: string | null }
  seconds: number
  cached: boolean
}

export interface CaseEvent {
  id: string
  at: string
  channel: string | null
  contacted: string | null
  text: string | null
  rules: string[]
  hash: string
  prev_hash: string
}

export interface Case {
  id: string
  borrower_name: string
  lender_name: string
  check_id: string | null
  route: string | null
  opened_at: string
  day: number | null
  events: CaseEvent[]
}

export interface Stats {
  checks: number
  median_seconds: number
  extra_rupees_flagged: number
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) throw new Error(`API ${res.status} on ${path}`)
  return res.json() as Promise<T>
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  checkImage(image: File, lang = 'hi', source = 'web') {
    const form = new FormData()
    form.append('image', image)
    form.append('lang', lang)
    form.append('source', source)
    return request<CheckResult>('/api/checks', { method: 'POST', body: form })
  },
  checkText: (text: string, lang = 'hi', source = 'web') =>
    request<CheckResult>('/api/checks', json({ text, lang, source })),
  getCheck: (id: string) => request<CheckResult>(`/api/checks/${id}`),
  listChecks: (limit = 20) => request<CheckResult[]>(`/api/checks?limit=${limit}`),
  createCase: (body: { borrower_name: string; lender_name: string; check_id?: string }) =>
    request<Case>('/api/cases', json(body)),
  listCases: () => request<Case[]>('/api/cases'),
  getCase: (id: string) => request<Case>(`/api/cases/${id}`),
  addEvent: (caseId: string, body: { at: string; channel: string; contacted: string; text: string }) =>
    request<CaseEvent>(`/api/cases/${caseId}/events`, json(body)),
  verifyCase: (id: string) => request<{ ok: boolean }>(`/api/cases/${id}/verify`),
  evidenceUrl: (id: string) => `/api/cases/${id}/evidence.pdf`,
  stats: () => request<Stats>('/api/stats'),
  health: () => request<Record<string, boolean | string>>('/api/health'),
}
