import { ArrowRight } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { Link, useLocation } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Reveal } from '@/site/motion'

// The website's own 404 (task H6, D47), written like one of our answers:
// a number we could not verify.

const DIGITS = ['4', '0', '4']

export default function NotFound() {
  const reduce = useReducedMotion()
  const { pathname } = useLocation()
  return (
    <section className="flex min-h-svh flex-col justify-between px-[3vw] pt-36 pb-10">
      <div>
        <Reveal>
          <p className="mb-[2vw] flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
            <span className="h-px w-8 bg-foreground/40" aria-hidden />
            Pata nahi chala
          </p>
        </Reveal>
        <h1 className="flex text-[34vw] leading-[0.78] font-semibold tracking-[-0.02em]" aria-label="404">
          {DIGITS.map((d, i) => (
            <span key={i} aria-hidden className="inline-block overflow-hidden px-[0.02em] pb-[0.05em]">
              <motion.span
                className={`inline-block ${i === 1 ? 'text-transparent [-webkit-text-stroke:2px_var(--primary)]' : ''}`}
                initial={reduce ? false : { y: '110%', rotate: i === 1 ? 0 : i === 0 ? -6 : 6 }}
                animate={{ y: 0, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 90, damping: 14, delay: 0.12 * i }}
              >
                {d}
              </motion.span>
            </span>
          ))}
        </h1>
      </div>
      <Reveal delay={0.5}>
        <div className="grid items-end gap-8 border-t border-border pt-6 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <p className="text-3xl font-semibold tracking-tight">Yeh page nahi mila.</p>
            <p className="mt-2 max-w-xl text-muted-foreground">
              We could not verify <span className="font-mono text-sm text-foreground">{pathname}</span>, and we do not
              guess. Nothing was charged, nothing was lost.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:col-span-5 lg:justify-end">
            <Link to="/" className={buttonVariants({ variant: 'outline', size: 'lg', className: 'h-14 px-8 text-base' })}>
              Back home
            </Link>
            <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-14 px-8 text-base' })}>
              Check an offer
              <ArrowRight className="size-4" aria-hidden />
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  )
}
