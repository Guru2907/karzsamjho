import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, type Case } from '@/lib/api'
import { ERROR_MESSAGES } from '@/lib/format'
import { maskPhone, rememberCase, spacedCode } from '@/lib/myCases'

// Open a harassment case from the helper app (D56), for a borrower who does not use Telegram.
// From /cases: borrower + lender typed by the helper. From a /check result: the lender comes from that
// check and the case is linked to it (check_id), so the complaint route uses that exact RBI result.
// D59: the phone (optional) is masked on this phone before it is sent, so the full number never leaves
// it; the new case's 8-digit code is shown big, for the borrower to keep; the case is remembered on
// this phone ("Cases on this phone").

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
  const [phone, setPhone] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<Case | null>(null)

  const start = () => {
    setBorrower('')
    setLender(defaultLender)
    setPhone('')
    setError(null)
    setCreated(null)
    setOpen(true)
  }

  const masked = maskPhone(phone)
  const phoneTyped = phone.trim().length > 0

  const submit = async () => {
    setSaving(true)
    setError(null)
    try {
      const c = await api.createCase({
        borrower_name: borrower.trim(),
        lender_name: lender.trim(),
        ...(checkId ? { check_id: checkId } : {}),
        ...(masked ? { borrower_phone: masked } : {}),
      })
      rememberCase(c)
      setCreated(c)
    } catch {
      setError(ERROR_MESSAGES.SERVER_OFF)
    } finally {
      setSaving(false)
    }
  }

  const openCase = () => {
    if (!created) return
    setOpen(false)
    navigate(`/cases/${created.id}`)
  }

  return (
    <>
      <Button onClick={start} variant={variant} className="h-14 w-full gap-2 text-base font-semibold">
        <FolderPlus className="size-5" aria-hidden />
        {label}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          {created ? (
            <>
              <DialogHeader>
                <DialogTitle>Case opened</DialogTitle>
                <DialogDescription>
                  Give this code to the borrower and write it down. It opens this case on any helper's phone, and
                  it never changes.
                </DialogDescription>
              </DialogHeader>
              <p className="rounded-xl border border-border bg-muted py-5 text-center font-mono text-4xl font-bold tracking-[0.15em] text-foreground">
                {spacedCode(created.code)}
              </p>
              <Button onClick={openCase} className="h-14 w-full text-base font-semibold">
                Open the case
              </Button>
            </>
          ) : (
            <>
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
                <label className="block space-y-1 text-sm font-medium text-foreground">
                  Borrower's phone (optional)
                  <input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    type="tel"
                    inputMode="tel"
                    autoComplete="off"
                    placeholder="98765 43210"
                    className={field}
                  />
                  <span className="block text-xs font-normal text-muted-foreground">
                    {masked
                      ? `Saved as ${masked}. Only the last 4 digits are kept.`
                      : 'Only the last 4 digits are kept, to recognise the borrower.'}
                  </span>
                </label>
                {checkId && <p className="text-xs text-muted-foreground">Linked to this loan check, so the complaint route uses its RBI result.</p>}
                {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
                <Button
                  onClick={submit}
                  disabled={saving || !borrower.trim() || !lender.trim() || (phoneTyped && !masked)}
                  className="h-14 w-full text-base font-semibold"
                >
                  {saving ? 'Opening…' : 'Open case'}
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
