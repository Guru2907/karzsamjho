import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/lib/theme'
import { NavLink } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const links = [
  { to: '/', label: 'Home' },
  { to: '/check', label: 'Check an offer' },
  { to: '/cases', label: 'Cases' },
]

// One shared top bar. It does not change on scroll.
export function TopBar() {
  const { theme, setTheme } = useTheme()
  const dark = theme === 'dark'
  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center gap-4 px-4">
        <NavLink to="/" className="font-semibold">
          KarzSamjho
        </NavLink>
        <nav className="flex flex-1 items-center gap-4 text-sm">
          {links.slice(1).map((l) => (
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
