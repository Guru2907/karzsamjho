import { useState } from 'react'
import { MessageSquareWarning } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, ApiError } from '@/lib/api'
import { RULE_NAMES } from './caseInfo'

// E5: a helper logs a threat for this case. The API labels it with rules H1-H6 and adds it to the hash chain.

const CHANNELS = [
  ['call', 'Phone call'], ['sms', 'SMS'], ['whatsapp', 'WhatsApp'], ['telegram', 'Telegram'], ['in_person', 'In person'],
] as const
const CONTACTED = [
  ['borrower', 'The borrower'], ['family', 'Family'], ['friend', 'A friend'], ['employer', 'Employer / office'],
  ['neighbour', 'Neighbours'], ['phone_contacts', 'Phone contacts'],
] as const

/** Now in Indian time, as the value a datetime-local input expects ("2026-11-14T05:58"). */
function nowIst(): string {
  return new Date(Date.now() + 5.5 * 3600 * 1000).toISOString().slice(0, 16)
}

const field = 'h-12 w-full rounded-lg border border-border bg-background px-3 text-base text-foreground'

export function LogThreatDialog({ caseId, onLogged }: { caseId: string; onLogged: () => void }) {
  const [open, setOpen] = useState(false)
  const [at, setAt] = useState(nowIst)
  const [channel, setChannel] = useState<string>('call')
  const [contacted, setContacted] = useState<string>('borrower')
  const [text, setText] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = () => {
    setAt(nowIst())
    setText('')
    setError(null)
    setOpen(true)
  }

  const submit = async () => {
    setSaving(true)
    setError(null)
    try {
      const ev = await api.addEvent(caseId, { at: `${at}:00+05:30`, channel, contacted, text: text.trim() })
      const rules = ev.rules ?? []
      toast(rules.length ? `Logged: ${rules.map((r) => `${r} ${RULE_NAMES[r] ?? ''}`).join(' · ')}` : 'Logged, no rule broken')
      setOpen(false)
      onLogged()
    } catch (e) {
      setError(e instanceof ApiError ? e.text_hi : 'Server se baat nahi ho pa rahi. Thodi der baad dobara try karo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Button onClick={start} className="h-14 w-full text-base font-semibold">
        <MessageSquareWarning className="size-5" aria-hidden />
        Log a threat
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log a threat</DialogTitle>
            <DialogDescription>When it happened, how, who was contacted and what was said.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="block space-y-1 text-sm font-medium text-foreground">
              When
              <input type="datetime-local" value={at} onChange={(e) => setAt(e.target.value)} className={field} />
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              How
              <select value={channel} onChange={(e) => setChannel(e.target.value)} className={field}>
                {CHANNELS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              Who was contacted
              <select value={contacted} onChange={(e) => setContacted(e.target.value)} className={field}>
                {CONTACTED.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-sm font-medium text-foreground">
              What was said
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={4}
                placeholder="Copy the message, or write what the caller said"
                className="w-full rounded-lg border border-border bg-background p-3 text-base text-foreground"
              />
            </label>
            {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
            <Button onClick={submit} disabled={saving || !text.trim()} className="h-14 w-full text-base font-semibold">
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
