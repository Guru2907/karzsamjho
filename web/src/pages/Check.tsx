import { useRef, useState } from 'react'
import {
  Camera,
  Image as ImageIcon,
  IndianRupee,
  RotateCcw,
  Share2,
  Volume2,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { RajuCard } from '@/components/RajuCard'
import { HelperDetails } from '@/components/check/HelperDetails'
import { PayFirstBanner } from '@/components/check/PayFirstBanner'
import { ErrorView } from '@/components/check/ErrorView'
import { api, ApiError, type CheckResult } from '@/lib/api'
import { days, ERROR_MESSAGES, rupees } from '@/lib/format'
import { sampleResults } from '@/lib/sample'
import { InstallPrompt } from '@/components/InstallPrompt'

function buildShareText(result: CheckResult): string {
  const lines: string[] = []
  const { numbers, lender, next_step } = result

  if (numbers?.in_hand?.value != null) {
    lines.push(`In hand: ${rupees(numbers.in_hand.value)}`)
  }
  if (numbers?.repay_total?.value != null) {
    lines.push(`You repay: ${rupees(numbers.repay_total.value)}`)
  }
  if (numbers?.tenure_days?.value != null) {
    lines.push(`Days: ${days(numbers.tenure_days.value)}`)
  }
  if (numbers?.extra?.value != null) {
    lines.push(`Extra you pay: +${rupees(numbers.extra.value)}`)
  }

  if (lender?.warning) {
    let warn = `RBI cancelled this company's NBFC registration`
    if (lender.warning.date) warn += ` · list as on ${lender.warning.date}`
    lines.push(`RBI: ${warn}`)
  } else if (lender?.match != null) {
    let rbi = ''
    if (lender.match === 'FOUND') {
      rbi = `Found in RBI's directory, linked to ${lender.closest || lender.name_read || 'registered lender'}`
    } else if (lender.match === 'SIMILAR') {
      rbi = `A similar name is in RBI's directory: ${lender.closest}. Check the exact name`
    } else if (lender.match === 'NOT_FOUND') {
      rbi = `Not found in RBI's directory`
    }
    if (lender.list_date) {
      rbi += ` · RBI list as on ${lender.list_date}`
    }
    lines.push(`RBI: ${rbi}`)
  }

  if (next_step?.text_hi) {
    lines.push(`Next step: ${next_step.text_hi}`)
  }

  lines.push('')
  lines.push('Checked with KarzSamjho')

  return lines.join('\n')
}

export default function Check() {
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const galleryInputRef = useRef<HTMLInputElement>(null)

  const [view, setView] = useState<'start' | 'waiting' | 'result' | 'error'>(() => {
    if (typeof window === 'undefined') return 'start'
    const params = new URLSearchParams(window.location.search)
    const sampleKey = params.get('sample')
    return sampleKey && sampleResults[sampleKey] ? 'result' : 'start'
  })

  const [result, setResult] = useState<CheckResult | null>(() => {
    if (typeof window === 'undefined') return null
    const params = new URLSearchParams(window.location.search)
    const sampleKey = params.get('sample')
    return (sampleKey && sampleResults[sampleKey]) || null
  })

  const [error, setError] = useState<{ code?: string; text_hi: string } | null>(null)
  const [smsText, setSmsText] = useState('')


  const runCheck = async (fn: () => Promise<CheckResult>) => {
    setView('waiting')
    try {
      const res = await fn()
      setResult(res)
      setView('result')
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ code: err.code, text_hi: err.text_hi })
      } else {
        setError({ code: 'SERVER_OFF', text_hi: ERROR_MESSAGES.SERVER_OFF })
      }
      setView('error')
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      runCheck(() => api.checkImage(file))
    }
    e.target.value = ''
  }

  const handleSendSms = () => {
    const trimmed = smsText.trim()
    if (!trimmed) return
    runCheck(() => api.checkText(trimmed))
  }

  const handleShare = async () => {
    if (!result) return
    const text = buildShareText(result)
    let shared = false
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({ title: 'KarzSamjho', text })
        shared = true
      } catch (err: unknown) {
        if (err instanceof Error && err.name === 'AbortError') return
      }
    }
    if (!shared) {
      try {
        await navigator.clipboard.writeText(text)
        toast('Copied')
      } catch {
        toast('Copied')
      }
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    setSmsText('')
    setView('start')
    if (typeof window !== 'undefined' && window.location.search) {
      window.history.replaceState({}, '', window.location.pathname)
    }
  }


  return (
    <div className="w-full max-w-md mx-auto py-2">
      {/* Hidden file inputs */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
      />
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* 1. START state */}
      {view === 'start' && (
        <>
          {/* Normal mode: heading, camera, gallery, divider, textarea, send */}
            <div className="space-y-6">
              <InstallPrompt />
              <div className="text-center space-y-1">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Check a loan ad or SMS
                </h1>
              </div>

              <div className="space-y-3">
                <Button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="w-full h-24 text-lg font-semibold flex flex-col gap-1 items-center justify-center rounded-2xl shadow-sm"
                >
                  <Camera className="size-8" />
                  <span>Take photo</span>
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => galleryInputRef.current?.click()}
                  className="w-full h-14 text-base font-medium flex items-center justify-center gap-2 rounded-xl"
                >
                  <ImageIcon className="size-5" />
                  <span>Choose from gallery</span>
                </Button>
              </div>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-3 text-muted-foreground font-medium">or</span>
                </div>
              </div>

              <div className="space-y-3">
                <textarea
                  value={smsText}
                  onChange={(e) => setSmsText(e.target.value)}
                  placeholder="Paste the SMS here"
                  rows={4}
                  className="w-full p-4 rounded-xl border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none text-sm leading-relaxed"
                />

                <Button
                  type="button"
                  disabled={!smsText.trim()}
                  onClick={handleSendSms}
                  className="w-full h-14 text-base font-semibold rounded-xl"
                >
                  Send
                </Button>
              </div>
            </div>
        </>
      )}

      {/* 2. WAITING state */}
      {view === 'waiting' && (
        <>
          <div className="py-20 flex flex-col items-center justify-center text-center space-y-4">
              <div className="p-6 rounded-full bg-muted">
                <IndianRupee className="size-16 text-primary animate-pulse" />
              </div>
              <p className="text-lg font-medium text-foreground">Reading your offer…</p>
              <p className="text-xs text-muted-foreground">can take up to 15 seconds</p>
            </div>
        </>
      )}

      {/* 3. RESULT state */}
      {view === 'result' && result && (
        <div className="space-y-6">
          {result.next_step?.code === 'DO_NOT_PAY_FIRST' && (
            <PayFirstBanner />
          )}

          <RajuCard result={result} />

          {/* Normal mode: audio player, share button, new check button, helper details */}
            <>
              {result.audio_url && (
                <div className="rounded-2xl border border-border bg-card p-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <Volume2 className="size-4" />
                    <span>Listen · Suno</span>
                  </div>
                  <audio controls src={result.audio_url} className="w-full" />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  onClick={handleShare}
                  className="h-14 font-semibold flex items-center justify-center gap-2 rounded-xl"
                >
                  <Share2 className="size-5" />
                  <span>Share with helper</span>
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={handleReset}
                  className="h-14 font-semibold flex items-center justify-center gap-2 rounded-xl"
                >
                  <RotateCcw className="size-5" />
                  <span>New check</span>
                </Button>
              </div>

              <HelperDetails result={result} />
            </>
        </div>
      )}

      {/* 4. ERROR state */}
      {view === 'error' && error && (
        <>
          {/* Normal mode: ErrorView with icon, Hindi text, try again */}
            <ErrorView
              code={error.code}
              text_hi={error.text_hi}
              onRetry={handleReset}
            />
        </>
      )}
    </div>
  )
}
