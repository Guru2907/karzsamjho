import { Moon, Sun, ToggleLeft, ToggleRight } from 'lucide-react'
import { useTheme } from '@/lib/theme'
import { NavLink } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useRajuMode } from '@/lib/raju'

// The PWA's own bar. It never links to the public website at "/" (D47).
const links = [
  { to: '/check', label: 'Check an offer' },
  { to: '/cases', label: 'Cases' },
]

// One shared top bar. It does not change on scroll.
export function TopBar() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'
  const [rajuMode, setRajuMode] = useRajuMode()

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center gap-4 px-4">
        <NavLink to="/check" className="font-semibold tracking-tight">
          <span>Karz</span>
          <span className="text-primary">Samjho</span>
        </NavLink>
        <nav className="flex flex-1 items-center gap-4 text-sm">
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
        <Button
          variant="outline"
          size="sm"
          className="h-10 px-3 flex items-center gap-2 text-xs font-medium"
          aria-pressed={rajuMode}
          onClick={() => setRajuMode((prev) => !prev)}
        >
          {rajuMode ? (
            <ToggleRight className="size-5 text-primary" />
          ) : (
            <ToggleLeft className="size-5 text-muted-foreground" />
          )}
          <span>Easy mode</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
          onClick={() => setTheme(dark ? 'light' : 'dark')}
        >
          {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
      </div>
    </header>
  )
}
