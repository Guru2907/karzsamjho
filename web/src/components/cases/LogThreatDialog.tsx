import { useRef, useState } from 'react'
import { ImagePlus, MessageSquareWarning, X } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, ApiError } from '@/lib/api'
import { RULE_NAMES, THREAT_TYPES } from './caseInfo'

// E5: a helper logs a threat for this case. The API labels it with rules H1-H6 and adds it to the hash chain.
// D60: a type of threat (it can add a rule, e.g. "legal" adds H5) and up to 3 photos (screenshots, a photo
// of a notice). Photos are made smaller here before they are sent; the server cleans them again.

const CHANNELS = [
  ['call', 'Phone call'], ['sms', 'SMS'], ['whatsapp', 'WhatsApp'], ['telegram', 'Telegram'], ['in_person', 'In person'],
] as const
const CONTACTED = [
  ['borrower', 'The borrower'], ['family', 'Family'], ['friend', 'A friend'], ['employer', 'Employer / office'],
  ['neighbour', 'Neighbours'], ['phone_contacts', 'Phone contacts'],
] as const
const MAX_PHOTOS = 3
const MAX_SIDE = 1600

/** Now in Indian time, as the value a datetime-local input expects ("2026-11-14T05:58"). */
function nowIst(): string {
  return new Date(Date.now() + 5.5 * 3600 * 1000).toISOString().slice(0, 16)
}

/** A photo at most 1600 px on its longest side, as a JPEG (smaller upload). The original if that fails. */
async function shrink(file: File): Promise<Blob> {
  try {
    const bitmap = await createImageBitmap(file)
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(bitmap.width * scale)
    canvas.height = Math.round(bitmap.height * scale)
    canvas.getContext('2d')?.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
    bitmap.close()
    const blob = await new Promise<Blob | null>((ok) => canvas.toBlob(ok, 'image/jpeg', 0.85))
    return blob ?? file
  } catch {
    return file
  }
}

const field = 'h-12 w-full rounded-lg border border-border bg-background px-3 text-base text-foreground'

type Picked = { blob: Blob; url: string }

export function LogThreatDialog({ caseId, onLogged }: { caseId: string; onLogged: () => void }) {
  const [open, setOpen] = useState(false)
  const [at, setAt] = useState(nowIst)
  const [channel, setChannel] = useState<string>('call')
  const [contacted, setContacted] = useState<string>('borrower')
  const [threatType, setThreatType] = useState<string>('')
  const [text, setText] = useState('')
  const [photos, setPhotos] = useState<Picked[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const clearPhotos = () => {
    photos.forEach((p) => URL.revokeObjectURL(p.url))
    setPhotos([])
  }

  const start = () => {
    setAt(nowIst())
    setThreatType('')
    setText('')
    clearPhotos()
    setError(null)
    setOpen(true)
  }

  const addPhotos = async (files: FileList | null) => {
    if (!files) return
    const room = MAX_PHOTOS - photos.length
    const chosen = Array.from(files).slice(0, room)
    if (files.length > room) toast(`Only ${MAX_PHOTOS} photos per threat`)
    const added = await Promise.all(chosen.map(async (f) => {
      const blob = await shrink(f)
      return { blob, url: URL.createObjectURL(blob) }
    }))
    setPhotos((old) => [...old, ...added])
    if (fileInput.current) fileInput.current.value = ''
  }

  const removePhoto = (i: number) => {
    setPhotos((old) => {
      URL.revokeObjectURL(old[i].url)
      return old.filter((_, k) => k !== i)
    })
  }

  const submit = async () => {
    setSaving(true)
    setError(null)
    const body = {
      at: `${at}:00+05:30`, channel, contacted, text: text.trim(),
      ...(threatType ? { threat_type: threatType } : {}),
    }
    try {
      const ev = photos.length
        ? await api.addEventWithPhotos(caseId, body, photos.map((p) => p.blob))
        : await api.addEvent(caseId, body)
      const rules = ev.rules ?? []
      toast(rules.length ? `Logged: ${rules.map((r) => `${r} ${RULE_NAMES[r] ?? ''}`).join(' · ')}` : 'Logged, no rule broken')
      clearPhotos()
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
        <DialogContent className="max-h-[92svh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Log a threat</DialogTitle>
            <DialogDescription>When it happened, how, who was contacted, what kind of threat and what was said.</DialogDescription>
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
              Type of threat
              <select value={threatType} onChange={(e) => setThreatType(e.target.value)} className={field}>
                <option value="">Choose one (optional)</option>
                {THREAT_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
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

            {/* Photos (D60) */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">Photos (optional, up to {MAX_PHOTOS})</p>
              {photos.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {photos.map((p, i) => (
                    <div key={p.url} className="relative aspect-square overflow-hidden rounded-lg border border-border">
                      <img src={p.url} alt={`Photo ${i + 1}`} className="size-full object-cover" />
                      <button
                        type="button"
                        onClick={() => removePhoto(i)}
                        aria-label={`Remove photo ${i + 1}`}
                        className="absolute top-1 right-1 flex size-8 items-center justify-center rounded-full bg-foreground/80 text-background"
                      >
                        <X className="size-4" aria-hidden />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {photos.length < MAX_PHOTOS && (
                <Button type="button" variant="outline" onClick={() => fileInput.current?.click()} className="h-14 w-full gap-2 text-base">
                  <ImagePlus className="size-5" aria-hidden />
                  Add photo (screenshot or camera)
                </Button>
              )}
              <input
                ref={fileInput}
                type="file"
                accept="image/*"
                multiple
                hidden
                onChange={(e) => addPhotos(e.target.files)}
              />
              <p className="text-xs text-muted-foreground">
                Photos go into the evidence PDF as they are. Cover any Aadhaar or bank numbers before adding.
              </p>
            </div>

            {error && <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>}
            <Button onClick={submit} disabled={saving || (!text.trim() && photos.length === 0)} className="h-14 w-full text-base font-semibold">
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
