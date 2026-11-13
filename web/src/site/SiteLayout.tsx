import { ArrowUpRight, Moon, Sun } from 'lucide-react'
import { useMotionValueEvent, useScroll } from 'motion/react'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { useTheme } from '@/lib/theme'
import { NAV } from './shell'

// Layout of the public website (D47). It is separate from the PWA layout in App.tsx: its own
// borderless nav and footer, full width, and the PWA never links back here.

/** No box and no border: clear over the top of the page, frosted glass once the page scrolls
 *  under it, so it never has a closed boundary and never melts into the content. */
function SiteNav() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)

  useMotionValueEvent(scrollY, 'change', (y) => setScrolled(y > 24))

  return (
    <header
      className={`fixed inset-x-0 top-0 z-30 transition-[background-color,backdrop-filter] duration-300 ${
        scrolled ? 'bg-background/70 backdrop-blur-xl backdrop-saturate-150' : 'bg-transparent'
      }`}
    >
      <div className="flex h-[4.5rem] items-center gap-8 px-[3vw]">
        <Link to="/" className="text-xl font-semibold tracking-tight">
          Karz<span className="text-primary">Samjho</span>
        </Link>
        <nav className="hidden flex-1 items-center gap-8 sm:flex">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `group relative py-2 text-sm font-medium transition-colors hover:text-foreground ${isActive ? 'text-foreground' : 'text-muted-foreground'}`
              }
            >
              {({ isActive }) => (
                <>
                  {item.label}
                  <span
                    aria-hidden
                    className={`absolute inset-x-0 bottom-0 h-px origin-left bg-primary transition-transform duration-300 group-hover:scale-x-100 ${isActive ? 'scale-x-100' : 'scale-x-0'}`}
                  />
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            onClick={() => setTheme(dark ? 'light' : 'dark')}
            className="flex size-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground"
          >
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </button>
          <Link to="/check" className={buttonVariants({ className: 'h-10 px-5' })}>
            Open the app
            <ArrowUpRight className="size-4" aria-hidden />
          </Link>
        </div>
      </div>
    </header>
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
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })   // a new page starts at its top
  }, [pathname])
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
