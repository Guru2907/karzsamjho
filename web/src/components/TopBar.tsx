import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/lib/theme'
import { NavLink } from 'react-router-dom'
import { Button } from '@/components/ui/button'

// The PWA's own bar. It never links to the public website at "/" (D47).
const links = [
  { to: '/check', label: 'Check' },
  { to: '/cases', label: 'Cases' },
]

// One shared top bar. It does not change on scroll.
export function TopBar() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'

  return (
    <header className="border-b border-border bg-background">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-2 px-3 sm:px-4">
        <div className="flex items-center gap-3 sm:gap-6">
          <NavLink to="/check" className="font-semibold tracking-tight text-base">
            <span>Karz</span>
            <span className="text-primary">Samjho</span>
          </NavLink>
          <nav className="flex items-center gap-2.5 sm:gap-4 text-xs sm:text-sm">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="size-9 sm:size-10"
            aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            onClick={() => setTheme(dark ? 'light' : 'dark')}
          >
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
        </div>
      </div>
    </header>
  )
}
