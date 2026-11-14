import { useSyncExternalStore } from 'react'
import { Download, Share } from 'lucide-react'
import { Button } from '@/components/ui/button'

// "Install KarzSamjho" on /check (D54): the closest a website can get to "scan the QR and the app is on the
// home screen". Phones never let a site install itself; this makes it ONE tap.
// - Android / Chrome / Edge: the browser fires `beforeinstallprompt`; we keep it and show a button that opens
//   the phone's own install window.
// - iPhone / iPad (Safari): Apple has no install API, so we show the two taps instead.
// - Hidden when already installed (opened from the home-screen icon) or once the install finishes.

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

type InstallState = { kind: 'none' } | { kind: 'android' } | { kind: 'ios' }

let deferred: BeforeInstallPromptEvent | null = null
let installed = false
let state: InstallState = { kind: 'none' }
const listeners = new Set<() => void>()

function standalone(): boolean {
  if (typeof window === 'undefined') return true
  const nav = window.navigator as Navigator & { standalone?: boolean }
  return window.matchMedia?.('(display-mode: standalone)').matches || nav.standalone === true
}

function isIos(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  // iPadOS reports itself as a Mac with touch.
  return /iphone|ipad|ipod/i.test(ua) || (/macintosh/i.test(ua) && navigator.maxTouchPoints > 1)
}

function recompute(): void {
  if (installed || standalone()) state = { kind: 'none' }
  else if (deferred) state = { kind: 'android' }
  else if (isIos()) state = { kind: 'ios' }
  else state = { kind: 'none' }
  listeners.forEach((l) => l())
}

// Listen from the moment the app loads: the browser can fire the event before /check is on screen.
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault() // keep it for our button instead of the browser's mini bar
    deferred = e as BeforeInstallPromptEvent
    recompute()
  })
  window.addEventListener('appinstalled', () => {
    installed = true
    deferred = null
    recompute()
  })
  recompute()
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

async function install(): Promise<void> {
  if (!deferred) return
  const event = deferred
  deferred = null // a prompt event can be used only once
  await event.prompt()
  const { outcome } = await event.userChoice
  if (outcome === 'accepted') installed = true
  recompute()
}

export function InstallPrompt() {
  const s = useSyncExternalStore(subscribe, () => state, () => state)
  if (s.kind === 'android') {
    return (
      <Button onClick={install} variant="outline" className="h-14 w-full gap-2 text-base font-semibold">
        <Download className="size-5" aria-hidden />
        Install KarzSamjho on this phone
      </Button>
    )
  }
  if (s.kind === 'ios') {
    return (
      <p className="flex items-center justify-center gap-2 rounded-xl border border-border bg-muted px-4 py-3 text-sm text-foreground">
        <Share className="size-4 shrink-0" aria-hidden />
        <span>
          To install: tap <span className="font-semibold">Share</span>, then{' '}
          <span className="font-semibold">Add to Home Screen</span>
        </span>
      </p>
    )
  }
  return null
}
