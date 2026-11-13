import type { CheckResult } from '@/lib/api'
import { rupees } from '@/lib/format'

const STATUS_LABELS: Record<string, string> = {
  read: 'Printed on the ad',
  derived: 'Worked out from the ad',
  computed: 'Calculated',
  unverified: "Couldn't verify",
}

export function HelperDetails({ result }: { result: CheckResult }) {
  const { numbers, lender, engines, seconds, cached } = result
  const perDay = numbers?.per_day
  const aprSimple = numbers?.apr_simple

  return (
    <div className="w-full max-w-md mx-auto mt-6 rounded-2xl border border-border bg-card p-5 text-xs text-muted-foreground space-y-4">
      <h3 className="font-semibold text-sm text-foreground">For the helper</h3>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 border-b border-border pb-4">
        <div>
          <span className="font-medium text-foreground">Cost per day:</span>{' '}
          {perDay?.status === 'unverified' || perDay?.value == null
            ? "Couldn't verify"
            : rupees(perDay.value)}
        </div>

        <div>
          <span className="font-medium text-foreground">Yearly rate (estimate):</span>{' '}
          {aprSimple?.status === 'unverified' || aprSimple?.value == null
            ? "Couldn't verify"
            : `${aprSimple.value}%`}
          <p className="text-[10px] text-muted-foreground mt-0.5">Our own estimate, not an RBI number</p>
        </div>

        {lender?.nbfc?.name && (
          <div className="col-span-2">
            <span className="font-medium text-foreground">Registered NBFC:</span> {lender.nbfc.name}
          </div>
        )}

        <div className="col-span-2">
          <span className="font-medium text-foreground">How it was read:</span>{' '}
          {engines?.read || 'AI reader'}
          {engines?.second_read ? ` (checked again by ${engines.second_read})` : ''}
        </div>

        <div className="col-span-2">
          <span className="font-medium text-foreground">Time:</span>{' '}
          {cached ? 'pehle se jaancha hua' : `${seconds} s`}
        </div>
      </div>

      <div className="space-y-1.5">
        <h4 className="font-medium text-foreground">Where each number came from</h4>
        <ul className="space-y-1 text-muted-foreground">
          <li>
            <span className="text-foreground">In hand:</span>{' '}
            {STATUS_LABELS[numbers?.in_hand?.status] || numbers?.in_hand?.status || 'Unknown'}
          </li>
          <li>
            <span className="text-foreground">You repay:</span>{' '}
            {STATUS_LABELS[numbers?.repay_total?.status] || numbers?.repay_total?.status || 'Unknown'}
          </li>
          <li>
            <span className="text-foreground">Days:</span>{' '}
            {STATUS_LABELS[numbers?.tenure_days?.status] || numbers?.tenure_days?.status || 'Unknown'}
          </li>
          <li>
            <span className="text-foreground">Extra:</span>{' '}
            {STATUS_LABELS[numbers?.extra?.status] || numbers?.extra?.status || 'Unknown'}
          </li>
        </ul>
      </div>
    </div>
  )
}
