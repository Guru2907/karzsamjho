import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft, FileDown, MessageCircle, MessageSquare, Phone, Send, ShieldCheck, ShieldX, User, WifiOff,
  type LucideIcon,
} from 'lucide-react'
import { Button, buttonVariants } from '@/components/ui/button'
import { LogThreatDialog } from '@/components/cases/LogThreatDialog'
import { RouteBadge, RuleBadges, RulesLegend } from '@/components/cases/meta'
import { dayLine, formatAt, maskNumbers } from '@/components/cases/caseInfo'
import { api, type Case } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'

// E5: one harassment case. Timeline with the rules each message breaks, a "Log a threat" dialog,
// the English evidence PDF, and a check that the record was not edited after logging (hash chain, F4).

const CHANNEL_ICON: Record<string, LucideIcon> = {
  call: Phone, sms: MessageSquare, whatsapp: MessageCircle, telegram: Send, in_person: User,
}
const CONTACTED_LABEL: Record<string, string> = {
  borrower: 'the borrower', family: 'family', friend: 'a friend', employer: 'employer / office',
  neighbour: 'neighbours', phone_contacts: 'phone contacts',
}

type VerifyState = 'idle' | 'checking' | 'ok' | 'changed' | 'error'

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>()
  const [caseItem, setCaseItem] = useState<Case | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [verify, setVerify] = useState<VerifyState>('idle')

  const loadCase = useCallback(
    (quiet = false) => {
      if (!id) return
      if (!quiet) setLoading(true)
      setError(null)
      api
        .getCase(id)
        .then((data) => {
          setCaseItem(data)
          setLoading(false)
        })
        .catch(() => {
          setError(ERROR_MESSAGES.SERVER_OFF)
          setLoading(false)
        })
    },
    [id],
  )

  useEffect(() => {
    if (!id) return
    let active = true
    api
      .getCase(id)
      .then((data) => {
        if (active) setCaseItem(data)
      })
      .catch(() => {
        if (active) setError(ERROR_MESSAGES.SERVER_OFF)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [id])

  const runVerify = () => {
    if (!id) return
    setVerify('checking')
    api
      .verifyCase(id)
      .then((r) => setVerify(r.ok ? 'ok' : 'changed'))
      .catch(() => setVerify('error'))
  }

  const events = [...(caseItem?.events ?? [])].sort((a, b) => (b.at ?? '').localeCompare(a.at ?? ''))

  return (
    <div className="mx-auto w-full max-w-md space-y-4 py-2">
      <div className="flex items-center gap-2">
        <Link to="/cases" className="text-muted-foreground hover:text-foreground" aria-label="Back to cases">
          <ArrowLeft className="size-5" />
        </Link>
        <h1 className="truncate text-xl font-bold tracking-tight text-foreground">
          {caseItem ? caseItem.lender_name : 'Case'}
        </h1>
      </div>

      {loading && <p className="py-12 text-center text-sm text-muted-foreground">Loading case details…</p>}

      {!loading && error && (
        <div className="flex flex-col items-center space-y-4 px-4 py-12 text-center">
          <div className="rounded-full bg-muted p-4 text-muted-foreground">
            <WifiOff className="size-10" />
          </div>
          <p className="max-w-xs text-sm font-medium text-foreground">{error}</p>
          <Button onClick={() => loadCase()} className="h-12 w-full font-semibold">
            Try again
          </Button>
        </div>
      )}

      {!loading && !error && caseItem && (
        <>
          {/* Who, which lender, where to complain */}
          <div className="space-y-3 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Lender</p>
                <p className="truncate text-lg font-semibold text-foreground">{caseItem.lender_name}</p>
                <p className="text-xs text-muted-foreground">Borrower: {caseItem.borrower_name}</p>
              </div>
              <span className="shrink-0 text-sm font-semibold text-foreground">{dayLine(caseItem)}</span>
            </div>
            <RouteBadge route={caseItem.route} />
            {caseItem.route && (
              <p className="text-xs leading-relaxed text-muted-foreground">
                <span className="font-semibold text-foreground">Where to complain: </span>
                {caseItem.route}
              </p>
            )}
          </div>

          {/* Actions */}
          <LogThreatDialog caseId={caseItem.id} onLogged={() => { setVerify('idle'); loadCase(true) }} />
          <div className="grid grid-cols-2 gap-3">
            <a
              href={api.evidenceUrl(caseItem.id)}
              download={`${caseItem.id}_evidence.pdf`}
              className={buttonVariants({ variant: 'outline', className: 'h-14 text-base font-semibold' })}
            >
              <FileDown className="size-5" aria-hidden />
              Evidence PDF
            </a>
            <Button
              variant="outline"
              onClick={runVerify}
              disabled={verify === 'checking' || events.length === 0}
              className="h-14 text-base font-semibold"
            >
              <ShieldCheck className="size-5" aria-hidden />
              {verify === 'checking' ? 'Checking…' : 'Verify record'}
            </Button>
          </div>
          {verify === 'ok' && (
            <p className="flex items-center gap-2 rounded-xl bg-emerald-700/10 px-4 py-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-400">
              <ShieldCheck className="size-5 shrink-0" aria-hidden />
              Record not edited since logging
            </p>
          )}
          {verify === 'changed' && (
            <p className="flex items-center gap-2 rounded-xl bg-red-700/10 px-4 py-3 text-sm font-semibold text-red-700 dark:bg-red-400/10 dark:text-red-400">
              <ShieldX className="size-5 shrink-0" aria-hidden />
              Record changed after logging
            </p>
          )}
          {verify === 'error' && <p className="text-sm text-muted-foreground">{ERROR_MESSAGES.SERVER_OFF}</p>}

          {/* Timeline, newest first */}
          <div className="space-y-3">
            <h2 className="text-base font-semibold text-foreground">
              Timeline · {events.length} {events.length === 1 ? 'message' : 'messages'}
            </h2>
            {events.length === 0 && (
              <p className="rounded-2xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                Nothing logged yet. Use “Log a threat”, or forward the message to the Telegram bot.
              </p>
            )}
            {events.map((e) => {
              const Icon = CHANNEL_ICON[e.channel ?? ''] ?? MessageSquare
              return (
                <div key={e.id} className="space-y-2 rounded-2xl border border-border bg-card p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Icon className="size-4 shrink-0" aria-hidden />
                    <span className="font-medium text-foreground">{formatAt(e.at)}</span>
                    <span>· {e.channel ?? 'message'}</span>
                    {e.contacted && <span>· to {CONTACTED_LABEL[e.contacted] ?? e.contacted}</span>}
                  </div>
                  <p className="text-sm leading-relaxed text-foreground">{maskNumbers(e.text)}</p>
                  <RuleBadges rules={e.rules ?? []} named />
                  {(e.rules ?? []).length === 0 && <p className="text-xs text-muted-foreground">No rule broken.</p>}
                  <p className="font-mono text-[10px] text-muted-foreground">hash {e.hash?.slice(0, 8)}…</p>
                </div>
              )
            })}
          </div>

          <RulesLegend />
        </>
      )}
    </div>
  )
}
