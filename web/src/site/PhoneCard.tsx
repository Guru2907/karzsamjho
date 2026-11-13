import { CalendarDays, HandCoins, OctagonAlert, Pause, Play, TriangleAlert, Undo2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { CountUp } from './motion'

// The answer Raju gets, shown in a phone frame on the website. Illustration only: the numbers are
// the demo offer (loan 5,000, fee 1,200, 7 days) worked out by the real maths, and the audio is the
// real fixed Hindi sentence made by the app. The PWA's own card is Tejaswini's RajuCard.

const ROWS = [
  { icon: HandCoins, label: 'haath mein', sub: 'in hand', value: 3800, tone: 'text-emerald-700 dark:text-emerald-400' },
  { icon: Undo2, label: 'lautana hai', sub: 'to repay', value: 5000, tone: 'text-sky-700 dark:text-sky-400' },
  { icon: TriangleAlert, label: 'zyada', sub: 'extra', value: 1200, tone: 'text-red-700 dark:text-red-400' },
] as const

const BARS = [3, 6, 9, 5, 8, 4, 7, 10, 6, 3, 8, 5, 9, 4, 6, 7, 3, 5]

export function PhoneCard() {
  const audio = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const el = audio.current
    if (!el) return
    const stop = () => setPlaying(false)
    el.addEventListener('ended', stop)
    el.addEventListener('pause', stop)
    return () => {
      el.removeEventListener('ended', stop)
      el.removeEventListener('pause', stop)
    }
  }, [])

  const toggle = async () => {
    const el = audio.current
    if (!el) return
    if (playing) return el.pause()
    try {
      await el.play()
      setPlaying(true)
      setFailed(false)
    } catch {
      setFailed(true)
    }
  }

  return (
    <div className="mx-auto w-full max-w-[22rem] rounded-[2rem] border border-foreground/25 bg-card p-3">
      <div className="mx-auto mb-3 h-1 w-12 rounded-full bg-foreground/20" aria-hidden />
      <div className="rounded-[1.4rem] border border-border bg-background p-5">
        <div className="flex items-center gap-2 border-b border-border pb-4 text-red-700 dark:text-red-400">
          <OctagonAlert className="size-5" aria-hidden />
          <span className="text-sm font-semibold tracking-wide uppercase">Bahut mehenga loan</span>
        </div>

        <dl className="divide-y divide-border">
          {ROWS.map((row, i) => (
            <div key={row.label} className="flex items-center justify-between gap-4 py-4">
              <dt className="flex items-center gap-3">
                <row.icon className={`size-5 ${row.tone}`} aria-hidden />
                <span>
                  <span className="block text-sm font-medium">{row.label}</span>
                  <span className="block text-xs text-muted-foreground">{row.sub}</span>
                </span>
              </dt>
              <dd className={`text-3xl font-semibold tracking-tight ${row.tone}`}>
                <CountUp to={row.value} prefix="₹" delay={0.5 + i * 0.25} />
              </dd>
            </div>
          ))}
          <div className="flex items-center justify-between gap-4 py-4">
            <dt className="flex items-center gap-3">
              <CalendarDays className="size-5 text-muted-foreground" aria-hidden />
              <span>
                <span className="block text-sm font-medium">din</span>
                <span className="block text-xs text-muted-foreground">days</span>
              </span>
            </dt>
            <dd className="text-3xl font-semibold tracking-tight">7</dd>
          </div>
        </dl>

        <div className="mt-2 flex items-center gap-3 border-t border-border pt-4">
          <button
            type="button"
            onClick={toggle}
            aria-label={playing ? 'Pause the Hindi voice' : 'Play the Hindi voice'}
            className="flex size-12 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-primary/85 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            {playing ? <Pause className="size-5" /> : <Play className="size-5 translate-x-px" />}
          </button>
          <div className="flex h-8 flex-1 items-center gap-[3px]" aria-hidden>
            {BARS.map((h, i) => (
              <span
                key={i}
                className={`w-[3px] rounded-full ${playing ? 'bg-primary' : 'bg-foreground/25'}`}
                style={{ height: `${h * 10}%` }}
              />
            ))}
          </div>
          <span className="text-xs text-muted-foreground">Hindi</span>
        </div>
        {failed && <p className="mt-2 text-xs text-muted-foreground">Awaaz abhi nahi chal payi. Dobara dabao.</p>}
        <audio ref={audio} src="/sample-hi.mp3" preload="none" />
      </div>
    </div>
  )
}
