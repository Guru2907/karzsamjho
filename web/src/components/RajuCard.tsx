import {
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  HelpCircle,
  Landmark,
  Undo2,
  Wallet,
} from 'lucide-react'
import type { CheckResult, Verdict } from '@/lib/api'
import { days, rupees } from '@/lib/format'

export interface RajuCardProps {
  result: CheckResult
  raju?: boolean
}

interface VerdictConfig {
  icon: typeof CheckCircle2
  label: string
  colorClass: string
}

const VERDICT_CONFIG: Record<Verdict, VerdictConfig> = {
  USUAL: {
    icon: CheckCircle2,
    label: 'Usual cost · Aam kharcha',
    colorClass: 'text-emerald-700 dark:text-emerald-400',
  },
  COSTLY: {
    icon: AlertTriangle,
    label: 'Costly · Mehenga',
    colorClass: 'text-amber-600 dark:text-amber-400',
  },
  VERY_COSTLY: {
    icon: AlertOctagon,
    label: 'Very costly · Bahut mehenga',
    colorClass: 'text-red-700 dark:text-red-400',
  },
  CANNOT_SAY: {
    icon: HelpCircle,
    label: "Can't say · Pata nahi chala",
    colorClass: 'text-muted-foreground',
  },
}

// Raju mode: the whole verdict band is the verdict colour (with a white icon), so it reads without words.
const RAJU_BAND: Record<Verdict, string> = {
  USUAL: 'bg-emerald-700',
  COSTLY: 'bg-amber-600',
  VERY_COSTLY: 'bg-red-700',
  CANNOT_SAY: 'bg-muted',
}

export function RajuCard({ result, raju = false }: RajuCardProps) {
  const { verdict, numbers, lender, next_step } = result
  const vConfig = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.CANNOT_SAY
  const VerdictIcon = vConfig.icon

  const inHandField = numbers?.in_hand
  const repayField = numbers?.repay_total
  const tenureField = numbers?.tenure_days
  const extraField = numbers?.extra

  // Format RBI text or warning
  let rbiText: string | null = null
  let isRbiWarning = false

  if (lender?.warning) {
    isRbiWarning = true
    rbiText = `RBI cancelled this company's NBFC registration`
    if (lender.warning.date) {
      rbiText += ` · list as on ${lender.warning.date}`
    }
  } else if (lender?.match != null) {
    if (lender.match === 'FOUND') {
      const closestName = lender.closest || lender.name_read || 'registered lender'
      rbiText = `Found in RBI's directory, linked to ${closestName}`
    } else if (lender.match === 'SIMILAR') {
      rbiText = `A similar name is in RBI's directory: ${lender.closest}. Check the exact name`
    } else if (lender.match === 'NOT_FOUND') {
      rbiText = `Not found in RBI's directory`
    }
    if (rbiText && lender.list_date) {
      rbiText += ` · RBI list as on ${lender.list_date}`
    }
  }

  if (raju) {
    // Raju mode: taller verdict band (no label), rows 1, 2, 4 only at text-5xl with icons,
    // no labels, no RBI line, no next step.
    return (
      <div className="w-full max-w-md mx-auto rounded-2xl border border-border bg-card text-card-foreground shadow-sm overflow-hidden">
        {/* Taller verdict band */}
        <div
          className={`flex items-center justify-center py-6 px-4 border-b border-border ${RAJU_BAND[verdict] ?? RAJU_BAND.CANNOT_SAY}`}
          aria-label={vConfig.label}
        >
          <VerdictIcon className={`size-14 ${verdict === 'CANNOT_SAY' ? 'text-muted-foreground' : 'text-white'}`} />
        </div>

        {/* Rows 1, 2, 4 at text-5xl */}
        <div className="p-6 space-y-6">
          {/* Row 1: In Hand */}
          <div className="flex items-center justify-between gap-4">
            <Wallet className="size-10 shrink-0 text-muted-foreground" />
            <div className="text-right">
              {inHandField?.status === 'unverified' || inHandField?.value == null ? (
                <div className="flex items-center justify-end gap-1.5 text-muted-foreground text-xl font-medium">
                  <HelpCircle className="size-8 shrink-0" />
                  <span>Couldn't verify</span>
                </div>
              ) : (
                <span className="text-5xl font-semibold tabular-nums text-foreground">
                  {rupees(inHandField.value)}
                </span>
              )}
            </div>
          </div>

          {/* Row 2: Repay Total */}
          <div className="flex items-center justify-between gap-4">
            <Undo2 className="size-10 shrink-0 text-muted-foreground" />
            <div className="text-right">
              {repayField?.status === 'unverified' || repayField?.value == null ? (
                <div className="flex items-center justify-end gap-1.5 text-muted-foreground text-xl font-medium">
                  <HelpCircle className="size-8 shrink-0" />
                  <span>Couldn't verify</span>
                </div>
              ) : (
                <span className="text-5xl font-semibold tabular-nums text-foreground">
                  {rupees(repayField.value)}
                </span>
              )}
            </div>
          </div>

          {/* Row 4: Extra You Pay (Red, with '+') */}
          <div className="flex items-center justify-between gap-4">
            <AlertTriangle className="size-10 shrink-0 text-red-700 dark:text-red-400" />
            <div className="text-right">
              {extraField?.status === 'unverified' || extraField?.value == null ? (
                <div className="flex items-center justify-end gap-1.5 text-muted-foreground text-xl font-medium">
                  <HelpCircle className="size-8 shrink-0" />
                  <span>Couldn't verify</span>
                </div>
              ) : (
                <span className="text-5xl font-semibold tabular-nums text-red-700 dark:text-red-400">
                  +{rupees(extraField.value)}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Normal mode: verdict band + 4 rows + RBI line + next step
  return (
    <div className="w-full max-w-md mx-auto rounded-2xl border border-border bg-card text-card-foreground shadow-sm overflow-hidden">
      {/* 1. Verdict band */}
      <div className="flex items-center gap-3 px-5 py-4 bg-muted border-b border-border">
        <VerdictIcon className={`size-6 shrink-0 ${vConfig.colorClass}`} />
        <span className={`text-base font-semibold ${vConfig.colorClass}`}>
          {vConfig.label}
        </span>
      </div>

      {/* 2. Four rows */}
      <div className="p-5 space-y-4">
        {/* Row 1: in_hand */}
        <div className="flex items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Wallet className="size-5 shrink-0" />
            <span className="text-sm font-medium">In hand · Haath mein</span>
          </div>
          <div className="text-right">
            {inHandField?.status === 'unverified' || inHandField?.value == null ? (
              <div className="flex items-center justify-end gap-1 text-muted-foreground text-sm font-medium">
                <HelpCircle className="size-4 shrink-0" />
                <span>Couldn't verify</span>
              </div>
            ) : (
              <span className="text-4xl font-semibold tabular-nums text-foreground">
                {rupees(inHandField.value)}
              </span>
            )}
          </div>
        </div>

        {/* Row 2: repay_total */}
        <div className="flex items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Undo2 className="size-5 shrink-0" />
            <span className="text-sm font-medium">You repay · Lautana</span>
          </div>
          <div className="text-right">
            {repayField?.status === 'unverified' || repayField?.value == null ? (
              <div className="flex items-center justify-end gap-1 text-muted-foreground text-sm font-medium">
                <HelpCircle className="size-4 shrink-0" />
                <span>Couldn't verify</span>
              </div>
            ) : (
              <span className="text-4xl font-semibold tabular-nums text-foreground">
                {rupees(repayField.value)}
              </span>
            )}
          </div>
        </div>

        {/* Row 3: tenure_days */}
        <div className="flex items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2 text-muted-foreground">
            <CalendarDays className="size-5 shrink-0" />
            <span className="text-sm font-medium">Days · Din</span>
          </div>
          <div className="text-right">
            {tenureField?.status === 'unverified' || tenureField?.value == null ? (
              <div className="flex items-center justify-end gap-1 text-muted-foreground text-sm font-medium">
                <HelpCircle className="size-4 shrink-0" />
                <span>Couldn't verify</span>
              </div>
            ) : (
              <span className="text-4xl font-semibold tabular-nums text-foreground">
                {days(tenureField.value)}
              </span>
            )}
          </div>
        </div>

        {/* Row 4: extra */}
        <div className="flex items-center justify-between gap-3 pb-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <AlertTriangle className="size-5 shrink-0 text-red-700 dark:text-red-400" />
            <span className="text-sm font-medium">Extra you pay · Zyada</span>
          </div>
          <div className="text-right">
            {extraField?.status === 'unverified' || extraField?.value == null ? (
              <div className="flex items-center justify-end gap-1 text-muted-foreground text-sm font-medium">
                <HelpCircle className="size-4 shrink-0" />
                <span>Couldn't verify</span>
              </div>
            ) : (
              <span className="text-4xl font-semibold tabular-nums text-red-700 dark:text-red-400">
                +{rupees(extraField.value)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 3. RBI line / Warning line */}
      {rbiText && (
        <div
          className={`px-5 py-3 border-t border-border flex items-start gap-2.5 text-xs ${
            isRbiWarning
              ? 'text-red-700 dark:text-red-400 font-medium'
              : 'text-muted-foreground'
          }`}
        >
          {isRbiWarning ? (
            <AlertTriangle className="size-4 shrink-0 mt-0.5" />
          ) : (
            <Landmark className="size-4 shrink-0 mt-0.5" />
          )}
          <span>{rbiText}</span>
        </div>
      )}

      {/* 4. Next step */}
      {next_step?.text_hi && (
        <div className="px-5 py-3 border-t border-border bg-muted/50 flex items-center gap-2.5 text-sm font-medium text-foreground">
          <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
          <span>{next_step.text_hi}</span>
        </div>
      )}
    </div>
  )
}
