import { ArrowUpRight, Moon, Sun } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { useTheme } from '@/lib/theme'
import { SHELL } from './shell'

// Layout of the public website (/, later /how and /partners; D47). It is separate from the PWA
// layout in App.tsx: its own nav and footer, full width, and the PWA never links back here.

function SiteNav() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background">
      <div className={`${SHELL} flex h-16 items-center gap-4`}>
        <Link to="/" className="text-lg font-semibold tracking-tight">
          Karz<span className="text-primary">Samjho</span>
        </Link>
        <div className="flex-1" />
        <button
          type="button"
          aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
          onClick={() => setTheme(dark ? 'light' : 'dark')}
          className={buttonVariants({ variant: 'ghost', size: 'icon-lg' })}
        >
          {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </button>
        <Link to="/check" className={buttonVariants({ size: 'lg', className: 'px-4' })}>
          Open the app
          <ArrowUpRight className="size-4" aria-hidden />
        </Link>
      </div>
    </header>
  )
}

function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className={`${SHELL} flex flex-col gap-2 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between`}>
        <p>
          <span className="font-medium text-foreground">KarzSamjho</span> · Team Y2K Devs · COLOSSUS 3.0, 2026
        </p>
        <p>Built on synthetic test offers. Not tested with real borrowers yet.</p>
      </div>
    </footer>
  )
}

export default function SiteLayout() {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <SiteNav />
      <main className="flex-1">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}
