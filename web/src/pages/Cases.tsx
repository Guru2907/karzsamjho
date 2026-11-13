import { useEffect, useState } from 'react'
import { FolderOpen, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
            Cases are created when a borrower logs harassment or needs an evidence PDF.
          </p>
        </div>
      )}

      {!loading && !error && cases && cases.length > 0 && (
        <div className="space-y-3">
          {cases.map((c) => (
            <Link
              key={c.id}
              to={`/cases/${c.id}`}
              className="block p-4 rounded-2xl border border-border bg-card hover:bg-muted/50 transition-colors shadow-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <h3 className="font-semibold text-foreground text-base">{c.lender_name}</h3>
                  <p className="text-xs text-muted-foreground">{c.borrower_name}</p>
                </div>
                {c.route && (
                  <Badge variant="outline" className="text-xs shrink-0">
                    {c.route}
                  </Badge>
                )}
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
                <span>{c.day != null ? `Day ${c.day} of 30` : 'Day 1 of 30'}</span>
                <span>
                  {c.events?.length ?? 0} {c.events?.length === 1 ? 'event' : 'events'}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
