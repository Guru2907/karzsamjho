// Typed helpers for the KarzSamjho API. Shapes match CLAUDE.md ("API contract").
// Do not change these types without the whole team agreeing.

import { ERROR_MESSAGES } from './format'

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
    match: LenderMatch | null
    score: number | null
    closest: string | null
    list_date: string | null
    nbfc?: { name: string; list_date: string | null } | null
    warning?: { list: string; name: string; source_type: string; date: string | null; source: string } | null
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
  threat_type?: string | null       // D60: death | verbal | legal | shaming | visit | other
  photos?: { id: string; sha256: string }[]
}

export interface Case {
  id: string
  code: string | null               // 8 digits, made once with the case, never changed (D59)
  borrower_name: string
  borrower_phone: string | null     // always masked: XXXXXX 1234
  source: string | null             // telegram | app
  lender_name: string
  check_id: string | null
  route: string | null
  opened_at: string
  closed_at?: string | null         // D60: closed for good; no new threats after this
  close_reason?: string | null
  close_note?: string | null
  day: number | null
  events: CaseEvent[]
}

export interface Stats {
  checks: number
  median_seconds: number
  extra_rupees_flagged: number
}

export class ApiError extends Error {
  status: number
  code: string
  text_hi: string

  constructor(status: number, code: string, text_hi: string) {
    super(text_hi)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.text_hi = text_hi
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 45000)

  let res: Response
  try {
    res = await fetch(path, {
      ...init,
      signal: init?.signal ?? controller.signal,
    })
  } catch (err: unknown) {
    clearTimeout(timeoutId)
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(0, 'TIMEOUT', ERROR_MESSAGES.TIMEOUT)
    }
    throw new ApiError(0, 'SERVER_OFF', ERROR_MESSAGES.SERVER_OFF)
  } finally {
    clearTimeout(timeoutId)
  }

  if (!res.ok) {
    if (res.status === 422) {
      let data: any = null
      try {
        data = await res.json()
      } catch {}
      const detail = data?.detail
      const code = typeof detail === 'object' && detail?.code ? detail.code : 'UNPROCESSABLE_ENTITY'
      const text_hi =
        typeof detail === 'object' && detail?.text_hi
          ? detail.text_hi
          : typeof detail === 'string'
            ? detail
            : ERROR_MESSAGES.SERVER_OFF
      throw new ApiError(res.status, code, text_hi)
    }

    if (res.status >= 500) {
      throw new ApiError(res.status, 'SERVER_OFF', ERROR_MESSAGES.SERVER_OFF)
    }

    let data: any = null
    try {
      data = await res.json()
    } catch {}
    const text_hi = data?.detail?.text_hi || ERROR_MESSAGES.SERVER_OFF
    const code = data?.detail?.code || `HTTP_${res.status}`
    throw new ApiError(res.status, code, text_hi)
  }

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
  createCase: (body: { borrower_name: string; lender_name: string; check_id?: string; borrower_phone?: string }) =>
    request<Case>('/api/cases', json(body)),
  // D59: there is no "list every case". A helper opens a case with the borrower's 8-digit code.
  getCaseByCode: (code: string) => request<Case>(`/api/cases/code/${encodeURIComponent(code.replace(/\D/g, ''))}`),
  getCase: (id: string) => request<Case>(`/api/cases/${id}`),
  // D60: with photos it goes as a form (fields + up to 3 `photos`); without, as JSON like before.
  addEventWithPhotos: (
    caseId: string,
    body: { at: string; channel: string; contacted: string; text: string; threat_type?: string },
    photos: Blob[],
  ) => {
    const form = new FormData()
    Object.entries(body).forEach(([k, v]) => v != null && form.append(k, v))
    photos.forEach((p, i) => form.append('photos', p, `photo${i + 1}.jpg`))
    return request<CaseEvent>(`/api/cases/${caseId}/events`, { method: 'POST', body: form })
  },
  closeCase: (caseId: string, body: { reason: string; note?: string }) =>
    request<Case>(`/api/cases/${caseId}/close`, json(body)),
  photoUrl: (caseId: string, photoId: string) => `/api/cases/${caseId}/photos/${photoId}.jpg`,
  addEvent: (caseId: string, body: { at: string; channel: string; contacted: string; text: string; threat_type?: string }) =>
    request<CaseEvent>(`/api/cases/${caseId}/events`, json(body)),
  verifyCase: (id: string) => request<{ ok: boolean }>(`/api/cases/${id}/verify`),
  evidenceUrl: (id: string) => `/api/cases/${id}/evidence.pdf`,
  stats: () => request<Stats>('/api/stats'),
  health: () => request<Record<string, boolean | string>>('/api/health'),
}
