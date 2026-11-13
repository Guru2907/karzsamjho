import { ArrowUpRight } from 'lucide-react'
import { AnimatePresence, motion, useReducedMotion, useScroll, useTransform, type MotionValue } from 'motion/react'
import { useRef, useState, type ComponentType, type ReactNode } from 'react'

// Scroll and hover components for the inner pages of the public website (D47), built with the
// `motion` library in the style of the component kits the lead likes (Aceternity and similar),
// but with our rules: one accent, hairlines, no gradients, no glow. Each one has a still
// version for prefers-reduced-motion.

const EASE = [0.22, 1, 0.36, 1] as const

// ---------------------------------------------------------------- text that lights up on scroll
function LitWord({ children, progress, range }: { children: string; progress: MotionValue<number>; range: [number, number] }) {
  const opacity = useTransform(progress, range, [0.14, 1])
  return (
    <motion.span style={{ opacity }} className="mr-[0.24em] inline-block">
      {children}
    </motion.span>
  )
}

/** A statement whose words go from faint to full as the reader scrolls through it. */
export function ScrollText({ text, className = '' }: { text: string; className?: string }) {
  const ref = useRef<HTMLParagraphElement>(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 0.85', 'end 0.5'] })
  const words = text.split(' ')
  if (reduce) return <p className={className}>{text}</p>
  return (
    <p ref={ref} className={className} aria-label={text}>
      {words.map((w, i) => (
        <LitWord key={i} progress={scrollYProgress} range={[i / words.length, (i + 1) / words.length]}>
          {w}
        </LitWord>
      ))}
    </p>
  )
}

// ---------------------------------------------------------------- sticky steps
export type Step = { n: string; title: string; body: string; visual: ReactNode }

/** Text scrolls on the left; a pinned panel on the right swaps its picture for each step. */
export function StickySteps({ steps }: { steps: Step[] }) {
  const [active, setActive] = useState(0)
  const reduce = useReducedMotion()
  return (
    <div className="grid gap-12 lg:grid-cols-2 lg:gap-20">
      <div>
        {steps.map((s, i) => (
          <motion.div
            key={s.n}
            className="flex flex-col justify-center py-10 lg:min-h-[72vh]"
            onViewportEnter={() => setActive(i)}
            viewport={{ amount: 0.6 }}
          >
            <p className="font-mono text-sm text-primary">{s.n}</p>
            <h2
              className={`mt-4 text-[clamp(2.2rem,4.4vw,4rem)] leading-[1] font-semibold tracking-[-0.035em] transition-opacity duration-500 ${i === active ? 'opacity-100' : 'lg:opacity-25'}`}
            >
              {s.title}
            </h2>
            <p className={`mt-6 max-w-md text-lg leading-relaxed text-muted-foreground transition-opacity duration-500 ${i === active ? 'opacity-100' : 'lg:opacity-25'}`}>
              {s.body}
            </p>
            <div className="mt-8 border border-border bg-background p-6 lg:hidden">{s.visual}</div>
          </motion.div>
        ))}
      </div>
      <div className="hidden lg:block">
        <div className="sticky top-28 flex h-[72vh] items-center">
          <div className="relative w-full border border-border bg-background p-8">
            <p className="absolute -top-3 left-6 bg-background px-2 font-mono text-xs text-muted-foreground">
              {steps[active].n} / {String(steps.length).padStart(2, '0')}
            </p>
            <AnimatePresence mode="wait">
              <motion.div
                key={active}
                initial={reduce ? false : { opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduce ? undefined : { opacity: 0, y: -24 }}
                transition={{ duration: 0.35, ease: EASE }}
              >
                {steps[active].visual}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- lines that type themselves in
/** Each line wipes in from the left, one after the other, when the block scrolls into view. */
export function TypedLines({ lines, className = '' }: { lines: ReactNode[]; className?: string }) {
  const reduce = useReducedMotion()
  return (
    <div className={className}>
      {lines.map((line, i) => (
        <motion.div
          key={i}
          className="whitespace-pre"
          initial={reduce ? false : { clipPath: 'inset(0 100% 0 0)' }}
          whileInView={{ clipPath: 'inset(0 0% 0 0)' }}
          viewport={{ once: true, margin: '-15% 0px' }}
          transition={{ duration: 0.7, delay: 0.25 + i * 0.35, ease: 'linear' }}
        >
          {line}
        </motion.div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------- rows that fill on hover
export type HoverRow = { title: string; body: string; icon: ComponentType<{ className?: string }> }

/** Big list rows. On hover the accent colour rises from the bottom and the text flips colour. */
export function HoverRows({ rows }: { rows: HoverRow[] }) {
  return (
    <ul className="border-t border-foreground/25">
      {rows.map((r, i) => (
        <li key={r.title} className="group relative overflow-hidden border-b border-foreground/25">
          <span
            aria-hidden
            className="absolute inset-0 origin-bottom scale-y-0 bg-primary transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-y-100"
          />
          <div className="relative grid items-center gap-4 px-[3vw] py-9 transition-colors duration-300 group-hover:text-primary-foreground lg:grid-cols-12">
            <span className="font-mono text-sm text-muted-foreground transition-colors duration-300 group-hover:text-primary-foreground lg:col-span-1">
              {String(i + 1).padStart(2, '0')}
            </span>
            <h3 className="text-[clamp(2.2rem,5.4vw,5.5rem)] leading-[0.95] font-semibold tracking-[-0.04em] lg:col-span-6">
              {r.title}
            </h3>
            <p className="leading-relaxed text-muted-foreground transition-colors duration-300 group-hover:text-primary-foreground lg:col-span-4">
              {r.body}
            </p>
            <span className="hidden justify-end lg:col-span-1 lg:flex">
              <r.icon className="size-7 transition-transform duration-500 group-hover:hidden" />
              <ArrowUpRight className="hidden size-8 group-hover:block" aria-hidden />
            </span>
          </div>
        </li>
      ))}
    </ul>
  )
}

// ---------------------------------------------------------------- a timeline that draws on scroll
export type TimelineItem = { when: string; title: string; body: string }

/** A vertical line that fills with the accent colour as the reader scrolls past each stage. */
export function ScrollTimeline({ items }: { items: TimelineItem[] }) {
  const ref = useRef<HTMLOListElement>(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 0.75', 'end 0.55'] })
  return (
    <ol ref={ref} className="relative">
      <span aria-hidden className="absolute top-2 bottom-2 left-[7px] w-px bg-foreground/20" />
      <motion.span
        aria-hidden
        className="absolute top-2 bottom-2 left-[6px] w-[3px] origin-top bg-primary"
        style={{ scaleY: reduce ? 1 : scrollYProgress }}
      />
      {items.map((item, i) => (
        <motion.li
          key={item.when}
          className="relative grid gap-2 pb-14 pl-12 last:pb-0 lg:grid-cols-12 lg:gap-8"
          initial={reduce ? false : { opacity: 0.25 }}
          whileInView={{ opacity: 1 }}
          viewport={{ margin: '-35% 0px -35% 0px' }}
          transition={{ duration: 0.4 }}
        >
          <span aria-hidden className="absolute top-2 left-0 size-[15px] rounded-full border-[3px] border-primary bg-background" />
          <p className="font-mono text-sm text-primary lg:col-span-3">{item.when}</p>
          <div className="lg:col-span-9">
            <h3 className="text-3xl font-semibold tracking-tight">{item.title}</h3>
            <p className="mt-2 max-w-xl leading-relaxed text-muted-foreground">{item.body}</p>
          </div>
          <span className="sr-only">Step {i + 1}</span>
        </motion.li>
      ))}
    </ol>
  )
}
