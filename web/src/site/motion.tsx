import { animate, motion, useInView, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState, type ReactNode } from 'react'

// Small motion helpers for the public website only (D47). The PWA never imports this file.
// Every helper shows its final state at once when the visitor prefers reduced motion.

const EASE = [0.22, 1, 0.36, 1] as const

/** Fades and lifts its children into place the first time they scroll into view. */
export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-10% 0px' }}
      transition={{ duration: 0.7, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  )
}

/** A headline that rises word by word. Screen readers get the plain sentence. */
export function WordReveal({ text, accent, className }: { text: string; accent?: string; className?: string }) {
  const reduce = useReducedMotion()
  const words = text.split(' ')
  return (
    <h1 className={className} aria-label={text}>
      {words.map((word, i) => (
        <span key={i} aria-hidden className="inline-block overflow-hidden pb-[0.12em] align-bottom">
          <motion.span
            className={`inline-block ${word === accent ? 'text-primary' : ''}`}
            initial={reduce ? false : { y: '110%' }}
            animate={{ y: 0 }}
            transition={{ duration: 0.8, delay: 0.08 * i, ease: EASE }}
          >
            {word}
            {i < words.length - 1 ? ' ' : ''}
          </motion.span>
        </span>
      ))}
    </h1>
  )
}

const rupees = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

/** Counts up to a number once it is on screen. Indian digit grouping (1,00,000). */
export function CountUp({ to, prefix = '', duration = 1.2, delay = 0 }: { to: number; prefix?: string; duration?: number; delay?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const reduce = useReducedMotion()
  const [value, setValue] = useState(reduce ? to : 0)

  useEffect(() => {
    if (!inView || reduce) return
    const controls = animate(0, to, { duration, delay, ease: EASE, onUpdate: (v) => setValue(Math.round(v)) })
    return () => controls.stop()
  }, [inView, reduce, to, duration, delay])

  return (
    <span ref={ref} className="tabular-nums">
      {prefix}
      {rupees.format(reduce ? to : value)}
    </span>
  )
}
