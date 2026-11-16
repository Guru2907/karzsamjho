import { Link } from 'react-router-dom'
import { Camera, ChevronRight, FolderOpen, Send, type LucideIcon } from 'lucide-react'
import { InstallPrompt } from '@/components/InstallPrompt'

// Home of the helper app (D57): what a new helper sees when they open the app without having
// read the website. Short on purpose: what it is, the three things it does, how a check works.
// The installed app starts here (manifest start_url). It never links to the public website.

const BOT_URL = 'https://t.me/karzsamjho_demo_bot'

type Tile = { icon: LucideIcon; title: string; body: string } & ({ to: string } | { href: string })

const TILES: Tile[] = [
  {
    icon: Camera,
    title: 'Check a loan offer',
    body: 'Photo or SMS of the offer. You get the money in hand, the amount to repay, the extra, and a Hindi voice to play to the borrower.',
    to: '/check',
  },
  {
    icon: FolderOpen,
    title: 'Harassment cases',
    body: 'Log threats and calls from a lender. You get a dated evidence PDF and where to complain.',
    to: '/cases',
  },
  {
    icon: Send,
    title: 'For the borrower: Telegram',
    body: 'The borrower can send the photo to our Telegram bot and hear the answer in their language.',
    href: BOT_URL,
  },
]

const STEPS = [
  'The AI only copies the numbers written on the offer.',
  'Python does the maths. Nothing is guessed: unclear numbers are marked as unclear.',
  'The app name is checked against RBI’s list of lending apps, and one next step is given.',
]

function TileBody({ t }: { t: Tile }) {
  const Icon = t.icon
  return (
    <>
      <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icon className="size-6" aria-hidden />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-lg font-semibold text-foreground">{t.title}</span>
        <span className="mt-0.5 block text-sm leading-relaxed text-muted-foreground">{t.body}</span>
      </span>
      <ChevronRight className="size-5 shrink-0 text-muted-foreground" aria-hidden />
    </>
  )
}

export default function AppHome() {
  const tile =
    'flex min-h-20 items-center gap-4 rounded-2xl border border-border bg-card p-4 shadow-sm transition-colors hover:bg-muted'
  return (
    <div className="mx-auto w-full max-w-md space-y-6 py-2">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Loan lene se pehle, suno.</h1>
        <p className="text-base leading-relaxed text-muted-foreground">
          KarzSamjho helps you explain a loan offer to someone who cannot read it, and keep proof if a lender harasses
          them.
        </p>
      </div>

      <div className="space-y-3">
        {TILES.map((t) =>
          'to' in t ? (
            <Link key={t.title} to={t.to} className={tile}>
              <TileBody t={t} />
            </Link>
          ) : (
            <a key={t.title} href={t.href} target="_blank" rel="noreferrer" className={tile}>
              <TileBody t={t} />
            </a>
          ),
        )}
      </div>

      <div className="space-y-3 rounded-2xl border border-border p-5">
        <h2 className="text-base font-semibold text-foreground">How a check works</h2>
        <ol className="space-y-2.5">
          {STEPS.map((s, i) => (
            <li key={s} className="flex gap-3 text-sm leading-relaxed text-muted-foreground">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                {i + 1}
              </span>
              <span>{s}</span>
            </li>
          ))}
        </ol>
      </div>

      <InstallPrompt />

      <p className="text-center text-xs text-muted-foreground">Built on synthetic test offers. No login, no account.</p>
    </div>
  )
}
