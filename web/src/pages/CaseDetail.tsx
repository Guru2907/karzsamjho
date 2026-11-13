import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { api, type Case } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>()
  const [caseItem, setCaseItem] = useState<Case | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const loadCase = () => {
    if (!id) return
    setLoading(true)
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
  }

  useEffect(() => {
    if (!id) return
    let active = true
    api
      .getCase(id)
      .then((data) => {
        if (!active) return
        setCaseItem(data)
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
  }, [id])

  return (
    <div className="w-full max-w-md mx-auto py-2 space-y-4">
      <div className="flex items-center gap-2">
        <Link to="/cases" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-5" />
        </Link>
        <h1 className="text-xl font-bold tracking-tight text-foreground truncate">
          {caseItem ? caseItem.lender_name : `Case ${id}`}
        </h1>
      </div>

      {loading && (
        <p className="text-sm text-muted-foreground text-center py-12">Loading case details…</p>
      )}

      {!loading && error && (
        <div className="py-12 px-4 flex flex-col items-center text-center space-y-4">
          <div className="p-4 rounded-full bg-muted text-muted-foreground">
            <WifiOff className="size-10" />
          </div>
          <p className="text-sm font-medium text-foreground max-w-xs">{error}</p>
          <Button onClick={loadCase} className="h-12 w-full font-semibold">
            Try again
          </Button>
        </div>
      )}

      {!loading && !error && caseItem && (
        <div className="p-5 rounded-2xl border border-border bg-card space-y-4 shadow-sm">
          <div>
            <span className="text-xs text-muted-foreground">Borrower</span>
            <p className="font-semibold text-foreground text-base">{caseItem.borrower_name}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Lender</span>
            <p className="font-semibold text-foreground text-base">{caseItem.lender_name}</p>
          </div>
          {caseItem.route && (
            <div>
              <span className="text-xs text-muted-foreground">Complaint Route</span>
              <p className="font-medium text-foreground text-sm">{caseItem.route}</p>
            </div>
          )}
          <div className="flex justify-between items-center pt-3 border-t border-border text-xs text-muted-foreground">
            <span>{caseItem.day != null ? `Day ${caseItem.day} of 30` : 'Day 1 of 30'}</span>
            <span>{caseItem.events?.length ?? 0} events</span>
          </div>
        </div>
      )}
    </div>
  )
}
