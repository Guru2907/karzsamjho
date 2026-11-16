import { ArrowRight, QrCode } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

// The website never opens the helper app on a laptop (D57). The site is there to explain; the app
// lives on the phone. So:
// - on a laptop or desktop (fine pointer): a QR code to scan with the phone, no link into the app;
// - on a phone or tablet (coarse pointer): no QR (you cannot scan your own screen), one button to /app.
// The QR is a fixed picture made by scripts/make_qr.py: it always opens the hosted app home,
// https://karzsamjho.vercel.app/app, whatever address this site is being read on.

const QR_SRC = '/qr-app.png'

/** The QR keeps its own cream margin, in dark mode too: phone cameras misread light-on-dark codes.
 *  Show/hide sits on a wrapper: buttonVariants sets its own display, which would beat "hidden". */
export function QrCard({ size = 'md' }: { size?: 'md' | 'lg' }) {
  const box = size === 'lg' ? 'size-64' : 'size-52'
  return (
    <div className="pointer-coarse:hidden">
      <div className="inline-block border border-border">
        <img src={QR_SRC} alt="QR code that opens the KarzSamjho helper app" width={984} height={984} className={box} />
      </div>
      <p className="mt-4 text-sm font-medium">Scan with your phone camera</p>
      <p className="mt-1 max-w-xs text-sm text-muted-foreground">
        It opens the KarzSamjho helper app on your phone. Install it from there, with one tap.
      </p>
    </div>
  )
}

/** Only on phones and tablets: straight into the app home. */
export function PhoneAppLink({ className = 'h-16 px-10 text-lg' }: { className?: string }) {
  return (
    <span className="hidden pointer-coarse:inline-flex">
      <Link to="/app" className={buttonVariants({ size: 'lg', className })}>
        Open the app
        <ArrowRight className="size-5" aria-hidden />
      </Link>
    </span>
  )
}

/** The call to action on a page: QR on a laptop, one button on a phone. */
export function GetTheApp({ size = 'md' }: { size?: 'md' | 'lg' }) {
  return (
    <>
      <QrCard size={size} />
      <PhoneAppLink />
    </>
  )
}

/** The small "Get the app" in the site nav: opens the QR in a window on a laptop, a link on a phone. */
export function NavGetApp() {
  return (
    <>
      <Dialog>
        <span className="pointer-coarse:hidden">
          <DialogTrigger className={buttonVariants({ className: 'h-10 px-5' })}>
            <QrCode className="size-4" aria-hidden />
            Get the app
          </DialogTrigger>
        </span>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Get KarzSamjho on your phone</DialogTitle>
            <DialogDescription>Point your phone camera at the code. The app opens there, ready to install.</DialogDescription>
          </DialogHeader>
          <div className="flex justify-center">
            <img src={QR_SRC} alt="QR code that opens the KarzSamjho helper app" width={984} height={984} className="size-64 border border-border" />
          </div>
        </DialogContent>
      </Dialog>
      <span className="hidden pointer-coarse:inline-flex">
        <Link to="/app" className={buttonVariants({ className: 'h-10 px-5' })}>
          Open the app
          <ArrowRight className="size-4" aria-hidden />
        </Link>
      </span>
    </>
  )
}
