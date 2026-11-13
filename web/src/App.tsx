import { Outlet, Route, Routes } from 'react-router-dom'
import { TopBar } from '@/components/TopBar'
import { Toaster } from '@/components/ui/sonner'
import CaseDetail from '@/pages/CaseDetail'
import Cases from '@/pages/Cases'
import Check from '@/pages/Check'
import How from '@/pages/How'
import Landing from '@/pages/Landing'
import NotFound from '@/pages/NotFound'
import Partners from '@/pages/Partners'
import SiteLayout from '@/site/SiteLayout'

// Two front doors in one app (D47):
// - the public website (/, /how, /partners and its own 404) with its own layout in web/src/site/;
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

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<SiteLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/how" element={<How />} />
          <Route path="/partners" element={<Partners />} />
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
