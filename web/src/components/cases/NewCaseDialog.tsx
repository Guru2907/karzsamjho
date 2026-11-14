import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'

// Open a harassment case from the helper app (D56). Until now only the Telegram bot could create one.
// From /cases: borrower + lender typed by the helper. From a /check result: the lender comes from that
// check and the case is linked to it (check_id), so the complaint route uses that exact RBI result,
// the same as the bot does. Then the helper lands on the case page to log threats, get the PDF, verify.

const field = 'h-12 w-full rounded-lg border border-border bg-background px-3 text-base text-foreground'

export function NewCaseDialog({
  label = 'New case',
  defaultLender = '',
  checkId,
  variant = 'default',
}: {
  label?: string
  defaultLender?: string
  checkId?: string
  variant?: 'default' | 'outline'
}) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [borrower, setBorrower] = useState('')
  const [lender, setLender] = useState(defaultLender)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = () => {
    setBorrower('')
    setLender(defaultLender)
    setError(null)
    setOpen(true)
  }

  const submit = async () => {
    setSaving(true)
    setError(null)
    try {
      const created = await api.createCase({
        borrower_name: borrower.trim(),
        lender_name: lender.trim(),
        ...(checkId ? { check_id: checkId } : {}),
      })
      setOpen(false)
      navigate(`/cases/${created.id}`)
    } catch {
      setError(ERROR_MESSAGES.SERVER_OFF)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Button onClick={start} variant={variant} className="h-14 w-full gap-2 text-base font-semibold">
        <FolderPlus className="size-5" aria-hidden />
        {label}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start a harassment case</DialogTitle>
            <DialogDescription>
              Then log each threat or call. The case keeps a dated record and makes the evidence PDF.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Borrower's name
              <input value={borrower} onChange={(e) => setBorrower(e.target.value)} placeholder="e.g. Raju" className={field} />
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Lender or app name
              <input value={lender} onChange={(e) => setLender(e.target.value)} placeholder="As written on the offer" className={field} />
            </label>
            {checkId && <p className="text-xs text-muted-foreground">Linked to this loan check, so the complaint route uses its RBI result.</p>}
            {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
            <Button
              onClick={submit}
              disabled={saving || !borrower.trim() || !lender.trim()}
              className="h-14 w-full text-base font-semibold"
            >
              {saving ? 'Opening…' : 'Open case'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
