import { useEffect, useState } from 'react'
import { Placeholder } from '@/components/Placeholder'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api, type CheckResult } from '@/lib/api'

// Wiring check only: shows the sample check from the API as raw numbers.
// Tasks E2, E3 and E7 replace this with the real Raju card and helper view.
export default function Check() {
  const [check, setCheck] = useState<CheckResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getCheck('chk_0042')
      .then(setCheck)
      .catch(() => setError('Could not reach the API. Is it running on port 8000?'))
  }, [])

  return (
    <>
      <Placeholder title="Check an offer" task="Tasks E2, E3 and E7 build this page." />
      {error && <p className="text-sm text-destructive">{error}</p>}
      {!check && !error && <p className="text-sm text-muted-foreground">Loading sample check…</p>}
      {check && (
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2">
              <span>Sample check {check.id}</span>
              <Badge variant="outline">{check.verdict}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(check.numbers).map(([name, field]) => (
                  <tr key={name} className="border-b last:border-0">
                    <td className="py-1.5 text-muted-foreground">{name}</td>
                    <td className="py-1.5 text-right font-medium tabular-nums">{field.value ?? '—'}</td>
                    <td className="py-1.5 pl-3 text-right text-xs text-muted-foreground">{field.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted-foreground">
              Lender: {check.lender.name_read} · {check.lender.match} · {check.seconds} s
            </p>
          </CardContent>
        </Card>
      )}
    </>
  )
}
