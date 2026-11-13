import { animate, motion, useInView, useMotionValue, useReducedMotion, useSpring } from 'motion/react'
import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react'

// Small motion helpers for the public website only (D47). The PWA never imports this file.
// Every helper shows its final state at once when the visitor prefers reduced motion.

export const EASE = [0.22, 1, 0.36, 1] as const

/** Fades and lifts its children into place the first time they scroll into view. */
export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-10% 0px' }}
      transition={{ duration: 0.8, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  )
}

/** A hairline that draws itself from left to right when it scrolls into view. */
export function Rule({ className = '' }: { className?: string }) {
  const reduce = useReducedMotion()
  return (
    <motion.div
      aria-hidden
      className={`h-px origin-left bg-foreground/25 ${className}`}
      initial={reduce ? false : { scaleX: 0 }}
      whileInView={{ scaleX: 1 }}
      viewport={{ once: true, margin: '-10% 0px' }}
      transition={{ duration: 1.1, ease: EASE }}
    />
  )
}

/** Text that rises word by word. Pass the full sentence as `label` once for screen readers. */
export function WordReveal({
  text,
  accent,
  className,
  delay = 0,
  as: Tag = 'h1',
  label,
}: {
  text: string
  accent?: string
  className?: string
  delay?: number
  as?: 'h1' | 'h2' | 'p'
  label?: string
}) {
  const reduce = useReducedMotion()
  const words = text.split(' ')
  return (
    <Tag className={className} aria-label={label ?? text}>
      {words.map((word, i) => (
        <span key={i} aria-hidden className="inline-block overflow-hidden pb-[0.14em] align-bottom">
          <motion.span
            className={`inline-block ${word === accent ? 'text-primary' : ''}`}
            initial={reduce ? false : { y: '115%' }}
            animate={{ y: 0 }}
            transition={{ duration: 0.9, delay: delay + 0.09 * i, ease: EASE }}
          >
            {word}
            {i < words.length - 1 ? ' ' : ''}
          </motion.span>
        </span>
      ))}
    </Tag>
  )
}

const indian = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })
export const formatIndian = (n: number) => indian.format(n)

/** Counts up to a number once it is on screen. Indian digit grouping (1,00,000). */
export function CountUp({
  to,
  prefix = '',
  suffix = '',
  duration = 1.4,
  delay = 0,
}: {
  to: number
  prefix?: string
  suffix?: string
  duration?: number
  delay?: number
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-15% 0px' })
  const reduce = useReducedMotion()
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!inView || reduce) return
    const controls = animate(0, to, { duration, delay, ease: EASE, onUpdate: (v) => setValue(Math.round(v)) })
    return () => controls.stop()
  }, [inView, reduce, to, duration, delay])

  return (
    <span ref={ref} className="tabular-nums">
      {prefix}
      {formatIndian(reduce ? to : value)}
      {suffix}
    </span>
  )
}

/** Its child leans a little toward the cursor, then springs back. Desktop pointer only. */
export function Magnetic({ children, strength = 0.3 }: { children: ReactNode; strength?: number }) {
  const reduce = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 220, damping: 16 })
  const sy = useSpring(y, { stiffness: 220, damping: 16 })
  if (reduce) return <>{children}</>
  const move = (e: MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    x.set((e.clientX - (r.left + r.width / 2)) * strength)
    y.set((e.clientY - (r.top + r.height / 2)) * strength)
  }
  const leave = () => {
    x.set(0)
    y.set(0)
  }
  return (
    <motion.div className="inline-block" style={{ x: sx, y: sy }} onMouseMove={move} onMouseLeave={leave}>
      {children}
    </motion.div>
  )
}
