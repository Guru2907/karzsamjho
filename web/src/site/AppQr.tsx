import { ArrowRight, QrCode } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

// The website never opens the helper app on a laptop (D57). The site is there to explain; the app
// lives on the phone. So every "get the app" spot is a button:
// - on a laptop or desktop (fine pointer): it opens a window with a QR to scan with the phone;
// - on a phone or tablet (coarse pointer): no QR (you cannot scan your own screen), it goes to /app.
// The QR is a fixed picture made by scripts/make_qr.py (the vendor's portrait in the centre): it always
// opens the hosted app home, https://karzsamjho.vercel.app/app, whatever address this site is read on.
// Show/hide sits on wrappers: buttonVariants sets its own display, which would beat "hidden".

const QR_SRC = '/qr-app.png'

function QrDialog({ trigger, className }: { trigger: string; className: string }) {
  return (
    <span className="pointer-coarse:hidden">
      <Dialog>
        <DialogTrigger className={buttonVariants({ className })}>
          <QrCode className="size-4" aria-hidden />
          {trigger}
        </DialogTrigger>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Get KarzSamjho on your phone</DialogTitle>
            <DialogDescription>
              Point your phone camera at the code. The helper app opens there; install it with one tap.
            </DialogDescription>
          </DialogHeader>
          {/* The QR keeps its cream background in dark mode too: cameras misread light-on-dark codes. */}
          <img
            src={QR_SRC}
            alt="QR code that opens the KarzSamjho helper app"
            width={984}
            height={984}
            className="mx-auto size-96 max-w-full rounded-lg border border-border"
          />
        </DialogContent>
      </Dialog>
    </span>
  )
}

function PhoneLink({ className }: { className: string }) {
  return (
    <span className="hidden pointer-coarse:inline-flex">
      <Link to="/app" className={buttonVariants({ className })}>
        Open the app
        <ArrowRight className="size-4" aria-hidden />
      </Link>
    </span>
  )
}

/** The big call to action on a page: QR window on a laptop, straight to the app on a phone. */
export function GetTheApp({ className = 'h-16 px-10 text-lg' }: { className?: string }) {
  return (
    <>
      <QrDialog trigger="Get the app on your phone" className={className} />
      <PhoneLink className={className} />
    </>
  )
}

/** The small one in the site nav. */
export function NavGetApp() {
  return (
    <>
      <QrDialog trigger="Get the app" className="h-10 px-5" />
      <PhoneLink className="h-10 px-5" />
    </>
  )
}
