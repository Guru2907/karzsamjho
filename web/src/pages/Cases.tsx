import { useEffect, useState } from 'react'
import { ChevronRight, FolderOpen, MessageSquareWarning, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NewCaseDialog } from '@/components/cases/NewCaseDialog'
import { Button } from '@/components/ui/button'
import { RouteBadge, RuleBadges } from '@/components/cases/meta'
import { dayLine, uniqueRules } from '@/components/cases/caseInfo'
import { api, type Case } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'

export default function Cases() {
  const [cases, setCases] = useState<Case[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const loadCases = () => {
    setLoading(true)
    setError(null)
    api
      .listCases()
      .then((data) => {
        setCases(data)
        setLoading(false)
      })
      .catch(() => {
        setError(ERROR_MESSAGES.SERVER_OFF)
        setLoading(false)
      })
  }

  useEffect(() => {
    let active = true
    api
      .listCases()
      .then((data) => {
        if (!active) return
        setCases(data)
        setLoading(false)
      })
      .catch(() => {
        if (!active) return
        setError(ERROR_MESSAGES.SERVER_OFF)
        setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="w-full max-w-md mx-auto py-2 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Cases</h1>
      </div>

      <NewCaseDialog />

      {loading && (
        <p className="text-sm text-muted-foreground text-center py-12">Loading cases…</p>
      )}

      {!loading && error && (
        <div className="py-12 px-4 flex flex-col items-center text-center space-y-4">
          <div className="p-4 rounded-full bg-muted text-muted-foreground">
            <WifiOff className="size-10" />
          </div>
          <p className="text-sm font-medium text-foreground max-w-xs">{error}</p>
          <Button onClick={loadCases} className="h-12 w-full font-semibold">
            Try again
          </Button>
        </div>
      )}

      {!loading && !error && cases && cases.length === 0 && (
        <div className="py-16 px-4 flex flex-col items-center text-center space-y-3">
          <div className="p-4 rounded-full bg-muted text-muted-foreground">
            <FolderOpen className="size-12" />
          </div>
          <p className="text-base font-medium text-foreground">No cases yet</p>
          <p className="text-xs text-muted-foreground max-w-xs">
            Start one above, or forward a threat to the Telegram bot: both appear here.
          </p>
        </div>
      )}

      {!loading && !error && cases && cases.length > 0 && (
        <div className="space-y-3">
          {[...cases]
            .sort((x, y) => (y.opened_at ?? '').localeCompare(x.opened_at ?? ''))
            .map((c) => {
              const rules = uniqueRules(c)
              const n = c.events?.length ?? 0
              return (
                <Link
                  key={c.id}
                  to={`/cases/${c.id}`}
                  className="block min-h-14 rounded-2xl border border-border bg-card p-4 shadow-sm transition-colors hover:bg-muted/50"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate text-lg font-semibold text-foreground">{c.lender_name}</h3>
                      <p className="text-xs text-muted-foreground">{c.borrower_name}</p>
                    </div>
                    <ChevronRight className="mt-1 size-5 shrink-0 text-muted-foreground" aria-hidden />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <RouteBadge route={c.route} />
                    <span className="text-xs font-medium text-foreground">{dayLine(c)}</span>
                  </div>
                  <div className="mt-3 flex items-center justify-between gap-2 border-t border-border pt-3">
                    <RuleBadges rules={rules} />
                    <span className="ml-auto inline-flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
                      <MessageSquareWarning className="size-3.5" aria-hidden />
                      {n} {n === 1 ? 'message' : 'messages'}
                    </span>
                  </div>
                </Link>
              )
            })}
        </div>
      )}
    </div>
  )
}
