import { Route, Routes } from 'react-router-dom'
import { TopBar } from '@/components/TopBar'
import { Toaster } from '@/components/ui/sonner'
import CaseDetail from '@/pages/CaseDetail'
import Cases from '@/pages/Cases'
import Check from '@/pages/Check'
import Landing from '@/pages/Landing'

export default function App() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <TopBar />
      <main className="mx-auto w-full max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/check" element={<Check />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="*" element={<p className="text-muted-foreground">Page not found.</p>} />
        </Routes>
      </main>
      <Toaster />
    </div>
  )
}
