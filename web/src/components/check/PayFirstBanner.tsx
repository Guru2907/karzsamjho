import { Hand } from 'lucide-react'

export function PayFirstBanner() {
  return (
    <div
      role="alert"
      className="w-full max-w-md mx-auto mb-4 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-400 flex items-center justify-center gap-3 font-bold"
    >
      <Hand className="size-6 shrink-0" />
      <span className="text-base sm:text-lg">Savdhaan! Paise mat bhejo</span>
    </div>
  )
}
