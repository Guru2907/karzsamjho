import { useState, type FormEvent } from 'react'
import { ChevronRight, FolderOpen, KeyRound, Smartphone } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { NewCaseDialog } from '@/components/cases/NewCaseDialog'
import { Button } from '@/components/ui/button'
import { api, ApiError } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'
import { myCases, rememberCase, spacedCode } from '@/lib/myCases'

// E4, changed by D59: there is no list of everyone's cases. A helper opens a borrower's case with the
// 8-digit code the borrower got from the Telegram bot (/helper), or starts a case by hand for someone
// without Telegram. Cases this phone has opened are listed from this phone's own storage only.

export default function Cases() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [opening, setOpening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mine = myCases()
  const digits = code.replace(/\D/g, '')

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
        {mine.length === 0 ? (
          <div className="flex flex-col items-center space-y-2 rounded-2xl border border-dashed border-border px-4 py-10 text-center">
            <FolderOpen className="size-10 text-muted-foreground" aria-hidden />
            <p className="text-sm text-muted-foreground">
              None yet. Cases you open with a code or start here are kept on this phone only.
            </p>
          </div>
        ) : (
          mine.map((c) => (
            <Link
              key={c.id}
              to={`/cases/${c.id}`}
              className="flex min-h-16 items-center gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm transition-colors hover:bg-muted/50"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-lg font-semibold text-foreground">{c.lender_name}</p>
                <p className="text-xs text-muted-foreground">
                  {c.borrower_name}
                  {c.code && <span className="font-mono"> · {spacedCode(c.code)}</span>}
                </p>
              </div>
              <ChevronRight className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            </Link>
          ))
        )}
      </section>
    </div>
  )
}
