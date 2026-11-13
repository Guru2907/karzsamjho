import { Outlet, Route, Routes } from 'react-router-dom'
import { TopBar } from '@/components/TopBar'
import { Toaster } from '@/components/ui/sonner'
import CaseDetail from '@/pages/CaseDetail'
import Cases from '@/pages/Cases'
import Check from '@/pages/Check'
import Landing from '@/pages/Landing'
import SiteLayout from '@/site/SiteLayout'
import { SHELL } from '@/site/shell'

// Two front doors in one app (D47):
// - the public website (/ and, later, /how and /partners) with its own layout in web/src/site/;
// - the PWA (/check, /cases) with the app top bar. The PWA never links to the website.

function AppLayout() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <TopBar />
      <main className="mx-auto w-full max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

function NotFound() {
  return <p className={`${SHELL} py-20 text-muted-foreground`}>Page not found.</p>
}

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<SiteLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route element={<AppLayout />}>
          <Route path="/check" element={<Check />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}
