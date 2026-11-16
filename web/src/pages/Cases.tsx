import { useEffect, useState, type FormEvent } from 'react'
import { ChevronDown, ChevronRight, FolderOpen, KeyRound, Lock, Smartphone } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { NewCaseDialog } from '@/components/cases/NewCaseDialog'
import { Button } from '@/components/ui/button'
import { api, ApiError } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'
import { CLOSE_REASON_NAME, shortDate } from '@/components/cases/caseInfo'
import { myCases, refreshCase, rememberCase, spacedCode, type MyCase } from '@/lib/myCases'

// E4, changed by D59: there is no list of everyone's cases. A helper opens a borrower's case with the
// 8-digit code the borrower got from the Telegram bot (/helper), or starts a case by hand for someone
// without Telegram. Cases this phone has opened are listed from this phone's own storage only.

export default function Cases() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [opening, setOpening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mine, setMine] = useState<MyCase[]>(myCases)
  const [showClosed, setShowClosed] = useState(false)
  const digits = code.replace(/\D/g, '')

  // D60: a case closed on another helper's phone shows as closed here too. Each remembered case is
  // asked for once when the page opens; a failure just keeps what this phone already knew.
  useEffect(() => {
    let active = true
    Promise.allSettled(myCases().map((m) => api.getCase(m.id))).then((results) => {
      results.forEach((r) => r.status === 'fulfilled' && refreshCase(r.value))
      if (active) setMine(myCases())
    })
    return () => {
      active = false
    }
  }, [])
  const openOnes = mine.filter((m) => !m.closed_at)
  const closedOnes = mine.filter((m) => m.closed_at)

  const open = async (e: FormEvent) => {
    e.preventDefault()
    setOpening(true)
    setError(null)
    try {
      const found = await api.getCaseByCode(digits)
      rememberCase(found)
      navigate(`/cases/${found.id}`)
    } catch (err) {
      setError(err instanceof ApiError && err.status === 404 ? err.text_hi : ERROR_MESSAGES.SERVER_OFF)
    } finally {
      setOpening(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-md space-y-6 py-2">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Cases</h1>

      {/* 1. Open a borrower's case with their code */}
      <form onSubmit={open} className="space-y-3 rounded-2xl border border-border bg-card p-5 shadow-sm">
        <div className="flex items-center gap-2">
          <KeyRound className="size-5 text-primary" aria-hidden />
          <h2 className="text-lg font-semibold text-foreground">Open a borrower's case</h2>
        </div>
        <label className="block space-y-1 text-sm text-muted-foreground">
          Case code (8 digits)
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            inputMode="numeric"
            autoComplete="off"
            placeholder="4821 7730"
            maxLength={12}
            className="h-14 w-full rounded-lg border border-border bg-background px-3 text-center font-mono text-2xl tracking-[0.2em] text-foreground"
          />
        </label>
        {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
        <Button type="submit" disabled={opening || digits.length !== 8} className="h-14 w-full text-base font-semibold">
          {opening ? 'Opening…' : 'Open case'}
        </Button>
        <p className="text-xs leading-relaxed text-muted-foreground">
          The borrower gets this code from the KarzSamjho Telegram bot by sending <span className="font-mono">/helper</span>.
        </p>
      </form>

      {/* 2. A case for someone without Telegram */}
      <NewCaseDialog label="New case (borrower without Telegram)" variant="outline" />

      {/* 3. Cases this phone already opened */}
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-base font-semibold text-foreground">
          <Smartphone className="size-4 text-muted-foreground" aria-hidden />
          Cases on this phone
        </h2>
        {mine.length === 0 && (
          <div className="flex flex-col items-center space-y-2 rounded-2xl border border-dashed border-border px-4 py-10 text-center">
            <FolderOpen className="size-10 text-muted-foreground" aria-hidden />
            <p className="text-sm text-muted-foreground">
              None yet. Cases you open with a code or start here are kept on this phone only.
            </p>
          </div>
        )}
        {mine.length > 0 && openOnes.length === 0 && (
          <p className="text-sm text-muted-foreground">No open cases on this phone.</p>
        )}
        {openOnes.map((c) => <CaseRow key={c.id} c={c} />)}

        {closedOnes.length > 0 && (
          <div className="space-y-3 pt-2">
            <button
              type="button"
              onClick={() => setShowClosed((v) => !v)}
              aria-expanded={showClosed}
              className="flex min-h-12 w-full items-center gap-2 text-left text-sm font-semibold text-muted-foreground"
            >
              <Lock className="size-4" aria-hidden />
              Closed ({closedOnes.length})
              <ChevronDown className={`ml-auto size-5 transition-transform ${showClosed ? 'rotate-180' : ''}`} aria-hidden />
            </button>
            {showClosed && closedOnes.map((c) => <CaseRow key={c.id} c={c} />)}
          </div>
        )}
      </section>
    </div>
  )
}


function CaseRow({ c }: { c: MyCase }) {
  const closed = Boolean(c.closed_at)
  return (
    <Link
      to={`/cases/${c.id}`}
      className={`flex min-h-16 items-center gap-3 rounded-2xl border border-border p-4 transition-colors hover:bg-muted/50 ${
        closed ? 'bg-muted/40' : 'bg-card shadow-sm'
      }`}
    >
      <div className="min-w-0 flex-1">
        <p className={`truncate text-lg font-semibold ${closed ? 'text-muted-foreground' : 'text-foreground'}`}>{c.lender_name}</p>
        <p className="text-xs text-muted-foreground">
          {c.borrower_name}
          {c.code && <span className="font-mono"> · {spacedCode(c.code)}</span>}
        </p>
        {closed && (
          <p className="mt-0.5 text-xs text-muted-foreground">
            Closed {shortDate(c.closed_at)}
            {c.close_reason && <> · {CLOSE_REASON_NAME[c.close_reason] ?? c.close_reason}</>}
          </p>
        )}
      </div>
      <ChevronRight className="size-5 shrink-0 text-muted-foreground" aria-hidden />
    </Link>
  )
}
