import { Clock, ImageOff, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface ErrorViewProps {
  code?: string
  text_hi: string
  onRetry: () => void
  raju?: boolean
}

export function ErrorView({ code, text_hi, onRetry, raju = false }: ErrorViewProps) {
  let Icon = ImageOff
  if (code === 'SERVER_OFF') {
    Icon = WifiOff
  } else if (code === 'TIMEOUT') {
    Icon = Clock
  } else if (code === 'NOT_A_LOAN' || code?.includes('PHOTO') || code?.includes('IMAGE')) {
    Icon = ImageOff
  }

  return (
    <div className="w-full max-w-md mx-auto py-12 px-4 flex flex-col items-center text-center space-y-6">
      <div className="p-5 rounded-full bg-muted text-muted-foreground">
        <Icon className={raju ? 'size-16' : 'size-12'} />
      </div>

      {!raju && (
        <p className="text-base sm:text-lg font-medium text-foreground max-w-sm leading-relaxed">
          {text_hi}
        </p>
      )}

      <Button
        type="button"
        onClick={onRetry}
        className="w-full h-14 text-base font-semibold"
      >
        Try again
      </Button>
    </div>
  )
}
