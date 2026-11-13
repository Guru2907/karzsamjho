import { ArrowUpRight, Moon, Sun } from 'lucide-react'
import { motion, useMotionValueEvent, useReducedMotion, useScroll } from 'motion/react'
import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { useTheme } from '@/lib/theme'
import { NAV } from './shell'

// Layout of the public website (D47). It is separate from the PWA layout in App.tsx: its own
// floating nav and footer, full width, and the PWA never links back here.

/** A floating pill. It slides away while scrolling down and comes back on any scroll up. */
function SiteNav() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'
  const reduce = useReducedMotion()
  const { scrollY } = useScroll()
  const [hidden, setHidden] = useState(false)

  useMotionValueEvent(scrollY, 'change', (y) => {
    const before = scrollY.getPrevious() ?? 0
    setHidden(y > 160 && y > before)
  })

  return (
    <motion.header
      className="fixed inset-x-0 top-4 z-30 flex justify-center px-4"
      animate={{ y: hidden && !reduce ? -96 : 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="flex h-14 items-center gap-1 rounded-full border border-foreground/20 bg-background py-2 pr-2 pl-6">
        <Link to="/" className="mr-4 text-base font-semibold tracking-tight">
          Karz<span className="text-primary">Samjho</span>
        </Link>
        <nav className="hidden items-center sm:flex">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-full px-3 py-2 text-sm transition-colors hover:text-foreground ${isActive ? 'text-foreground' : 'text-muted-foreground'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
          onClick={() => setTheme(dark ? 'light' : 'dark')}
          className="ml-2 flex size-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </button>
        <Link to="/check" className={buttonVariants({ className: 'h-10 rounded-full px-5' })}>
          Open the app
          <ArrowUpRight className="size-4" aria-hidden />
        </Link>
      </div>
    </motion.header>
  )
}

function SiteFooter() {
  return (
    <footer className="overflow-hidden border-t border-border">
      <p
        aria-hidden
        className="px-[3vw] pt-[3vw] text-[17.5vw] leading-[0.8] font-semibold tracking-[-0.06em] whitespace-nowrap text-transparent select-none [-webkit-text-stroke:1.5px_var(--foreground)]"
      >
        Karz<span className="[-webkit-text-stroke:1.5px_var(--primary)]">Samjho</span>
      </p>
      <div className="mt-[3vw] flex flex-col gap-2 border-t border-border px-[3vw] py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
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
