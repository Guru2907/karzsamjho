import type { CheckResult } from './api'

export const sampleResult1: CheckResult = {
  id: 'chk_sample_01',
  verdict: 'VERY_COSTLY',
  numbers: {
    in_hand: { value: 3800, status: 'derived' },
    repay_total: { value: 5000, status: 'read' },
    tenure_days: { value: 7, status: 'read' },
    extra: { value: 1200, status: 'computed' },
    per_day: { value: 171, status: 'computed' },
    apr_simple: { value: 1647, status: 'computed' },
  },
  unverified: ['interest_rate'],
  lender: {
    name_read: 'QuickCash',
    match: 'NOT_FOUND',
    score: 41,
    closest: null,
    list_date: '2026-11-12',
    nbfc: null,
    warning: null,
  },
  next_step: {
    code: 'ASK_BANK_MITRA',
    text_hi: 'Bank mitra se poochho',
  },
  speech_text_hi:
    'Aapko haath mein 3800 rupaye milenge aur 7 din baad 5000 lautane honge. Yeh loan bahut mehenga hai.',
  audio_url: null,
  engines: {
    read: 'qwen',
    second_read: null,
    speak: 'edge-tts',
  },
  seconds: 5.4,
  cached: false,
}

export const sampleResult2: CheckResult = {
  id: 'chk_sample_02',
  verdict: 'CANNOT_SAY',
  numbers: {
    in_hand: { value: 5000, status: 'read' },
    repay_total: { value: null, status: 'unverified' },
    tenure_days: { value: 15, status: 'read' },
    extra: { value: null, status: 'unverified' },
    per_day: { value: null, status: 'unverified' },
    apr_simple: { value: null, status: 'unverified' },
  },
  unverified: ['repay_total', 'extra'],
  lender: {
    name_read: 'FastRupee',
    match: 'NOT_FOUND',
    score: 30,
    closest: null,
    list_date: '2026-11-12',
    nbfc: null,
    warning: null,
  },
  next_step: {
    code: 'UNVERIFIED_TERMS',
    text_hi: 'Pehle poori shartein pata karo',
  },
  speech_text_hi: 'Loan ki poori shartein saaf nahi hain. Pata nahi chal raha.',
  audio_url: null,
  engines: {
    read: 'qwen',
    second_read: null,
    speak: 'edge-tts',
  },
  seconds: 4.8,
  cached: false,
}

export const sampleResults: Record<string, CheckResult> = {
  '1': sampleResult1,
  '2': sampleResult2,
}
