import { useState } from 'react'
import { Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, ApiError, type Case } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'
import { CLOSE_REASONS } from './caseInfo'

// D60: closing a case is final (no reopen). Like deleting something, the helper has to type the words
// CASE CLOSED before the button works. After closing, no new threats can be logged; the record, the PDF
// and Verify stay. If the lender starts again, a new case (new code) is opened.

const CONFIRM = 'CASE CLOSED'
const field = 'h-12 w-full rounded-lg border border-border bg-background px-3 text-base text-foreground'

export function CloseCaseDialog({ caseId, onClosed }: { caseId: string; onClosed: (c: Case) => void }) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [note, setNote] = useState('')
  const [typed, setTyped] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = () => {
    setReason('')
    setNote('')
    setTyped('')
    setError(null)
    setOpen(true)
  }

  const confirmed = typed.trim().toUpperCase() === CONFIRM

  const submit = async () => {
    setSaving(true)
    setError(null)
    try {
      const closed = await api.closeCase(caseId, { reason, ...(note.trim() ? { note: note.trim() } : {}) })
      setOpen(false)
      onClosed(closed)
    } catch (e) {
      setError(e instanceof ApiError && e.status !== 0 ? e.text_hi : ERROR_MESSAGES.SERVER_OFF)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Button
        onClick={start}
        variant="outline"
        className="h-14 w-full gap-2 border-red-700/40 text-base font-semibold text-red-700 hover:bg-red-700/10 dark:border-red-400/40 dark:text-red-400"
      >
        <Lock className="size-5" aria-hidden />
        Close case
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Close this case?</DialogTitle>
            <DialogDescription>
              No new threats can be logged after this, and it cannot be opened again. The record, the evidence PDF and
              Verify stay available. If the lender starts again, start a new case.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Why is it closed?
              <select value={reason} onChange={(e) => setReason(e.target.value)} className={field}>
                <option value="">Choose a reason</option>
                {CLOSE_REASONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Note (optional)
              <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} placeholder="e.g. Complaint filed on Sachet" className={field} />
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Type <span className="font-mono font-bold">{CONFIRM}</span> to confirm
              <input
                value={typed}
                onChange={(e) => setTyped(e.target.value)}
                autoComplete="off"
                autoCapitalize="characters"
                placeholder={CONFIRM}
                className={`${field} font-mono tracking-wider`}
              />
            </label>
            {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
            <Button
              onClick={submit}
              disabled={saving || !reason || !confirmed}
              className="h-14 w-full gap-2 bg-red-700 text-base font-semibold text-white hover:bg-red-700/90 dark:bg-red-500 dark:hover:bg-red-500/90"
            >
              <Lock className="size-5" aria-hidden />
              {saving ? 'Closing…' : 'Close case'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
