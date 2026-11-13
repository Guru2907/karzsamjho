import { useEffect, useState } from 'react'
import { RajuCard } from '@/components/RajuCard'
import { api, type CheckResult } from '@/lib/api'
import { sampleResults } from '@/lib/sample'
import { useRajuMode } from '@/lib/raju'

export default function Check() {
  const [rajuMode] = useRajuMode()
  const [check, setCheck] = useState<CheckResult | null>(() => {
    if (typeof window === 'undefined') return null
    const params = new URLSearchParams(window.location.search)
    const sampleKey = params.get('sample')
    return (sampleKey && sampleResults[sampleKey]) || null
  })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (check) return
    api
      .getCheck('chk_0042')
      .then(setCheck)
      .catch(() => setError('Could not reach the API. Is it running on port 8000?'))
  }, [check])

  return (
    <div className="w-full max-w-md mx-auto py-4 space-y-4">
      {error && !check && <p className="text-sm text-destructive">{error}</p>}
      {!check && !error && <p className="text-sm text-muted-foreground text-center py-8">Loading check…</p>}
      {check && <RajuCard result={check} raju={rajuMode} />}
    </div>
  )
}
