import { motion, useMotionValueEvent, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { AnswerCard, PhoneCard, PhoneFrame } from './PhoneCard'
import { formatIndian } from './motion'
import { SHELL } from './shell'

// The pinned scroll story (D47): the screen stays still while scrolling plays the product.
// 0 the loan ad -> 1 the AI reads the numbers -> 2 Python does the maths -> 3 Raju's answer.
// On small screens, or with reduced motion, it becomes a plain list with the finished card.

const STEPS = [
  { n: '01', title: 'He sends a photo', body: 'A loan ad, an SMS or a voice note, in Telegram. Nothing to install, no login.' },
  { n: '02', title: 'The AI only reads', body: 'Two models from two companies copy the printed numbers. They never calculate.' },
  { n: '03', title: 'Python does the maths', body: 'Loan minus fee, the extra, the cost per day: plain tested code. Numbers that do not add up get a second reading.' },
  { n: '04', title: 'He hears the answer', body: 'One fixed sentence in Hindi, Bengali or Marathi, and a card with four numbers.' },
]

function useDesktop() {
  const [desktop, setDesktop] = useState(() => window.matchMedia('(min-width: 1024px)').matches)
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const on = () => setDesktop(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return desktop
}

const lerp = (p: number, from: number, to: number, a: number, b: number) =>
  Math.round(a + (b - a) * Math.min(1, Math.max(0, (p - from) / (to - from))))

/** The loud loan ad as it arrives on Raju's phone. `read` rings the numbers the AI copies. */
function LoanAd({ read }: { read: boolean }) {
  const ring = `rounded-sm px-1 transition-shadow duration-500 ${read ? 'shadow-[0_0_0_2px_var(--primary)]' : ''}`
  return (
    <div className="flex h-full flex-col bg-foreground p-6 text-background">
      <p className="text-xs font-semibold tracking-[0.25em] uppercase opacity-70">PaisaTurant</p>
      <p className="mt-3 text-4xl leading-none font-black tracking-tight uppercase">Instant loan in 5 min!</p>
      <div className="mt-6 space-y-3 text-lg font-medium">
        <p>
          Loan amount <span className={ring}>₹5,000</span>
        </p>
        <p>
          Processing fee <span className={ring}>₹1,200</span>
        </p>
        <p>
          Repay <span className={ring}>₹5,000</span>
        </p>
        <p>
          Tenure <span className={ring}>7 days</span>
        </p>
      </div>
      <p className="mt-auto border-t border-background/30 pt-4 text-sm font-semibold tracking-wide uppercase">
        Download now · Limited offer
      </p>
    </div>
  )
}

function Ledger({ stage, inHand, extra }: { stage: number; inHand: number; extra: number }) {
  const row = 'flex items-baseline justify-between gap-6 py-3'
  return (
    <div
      className={`transition-opacity duration-500 ${stage >= 2 ? 'opacity-100' : 'opacity-0'}`}
      aria-hidden={stage < 2}
    >
      <p className="mb-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">maths.py</p>
      <div className="divide-y divide-border border-y border-border font-mono text-sm">
        <div className={row}>
          <span className="text-muted-foreground">loan</span>
          <span>₹5,000</span>
        </div>
        <div className={row}>
          <span className="text-muted-foreground">fee, taken first</span>
          <span>− ₹1,200</span>
        </div>
        <div className={`${row} text-emerald-700 dark:text-emerald-400`}>
          <span>in hand</span>
          <span className="text-3xl font-semibold tracking-tight tabular-nums">₹{formatIndian(inHand)}</span>
        </div>
        <div className={row}>
          <span className="text-muted-foreground">to repay in 7 days</span>
          <span>₹5,000</span>
        </div>
        <div className={`${row} text-red-700 dark:text-red-400`}>
          <span>extra</span>
          <span className="text-3xl font-semibold tracking-tight tabular-nums">₹{formatIndian(extra)}</span>
        </div>
      </div>
      <p
        className={`mt-4 text-sm leading-relaxed text-muted-foreground transition-opacity duration-500 ${stage >= 3 ? 'opacity-100' : 'opacity-0'}`}
      >
        “Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye lautane honge. Yaani 1200 rupaye zyada.”
      </p>
    </div>
  )
}

function PinnedStory() {
  const ref = useRef<HTMLElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const [stage, setStage] = useState(0)
  const [inHand, setInHand] = useState(5000)
  const [extra, setExtra] = useState(0)
  const scanTop = useTransform(scrollYProgress, [0.15, 0.4], ['0%', '100%'])
  const barWidth = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])

  useMotionValueEvent(scrollYProgress, 'change', (p) => {
    setStage(p < 0.15 ? 0 : p < 0.42 ? 1 : p < 0.7 ? 2 : 3)
    setInHand(lerp(p, 0.44, 0.56, 5000, 3800))
    setExtra(lerp(p, 0.56, 0.68, 0, 1200))
  })

  return (
    <section ref={ref} className="relative h-[260vh]" aria-label="How one check works">
      <div className="sticky top-0 flex h-svh items-center overflow-hidden">
        <div className={`${SHELL} grid grid-cols-12 items-center gap-8`}>
          <ol className="col-span-4 space-y-7">
            {STEPS.map((s, i) => (
              <li
                key={s.n}
                className={`border-l-2 pl-5 transition-all duration-500 ${i === stage ? 'border-primary opacity-100' : 'border-border opacity-35'}`}
              >
                <p className="font-mono text-xs text-muted-foreground">{s.n}</p>
                <p className="mt-1 text-2xl font-semibold tracking-tight">{s.title}</p>
                <p
                  className={`mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground transition-all duration-500 ${i === stage ? 'max-h-32 opacity-100' : 'max-h-0 overflow-hidden opacity-0'}`}
                >
                  {s.body}
                </p>
              </li>
            ))}
          </ol>

          <div className="col-span-4">
            <PhoneFrame>
              <div className="relative h-[30rem]">
                <div
                  className={`absolute inset-0 transition-opacity duration-700 ${stage >= 3 ? 'opacity-0' : stage === 2 ? 'opacity-40' : 'opacity-100'}`}
                  aria-hidden={stage >= 3}
                >
                  <LoanAd read={stage >= 1} />
                </div>
                <motion.div
                  aria-hidden
                  className={`absolute inset-x-0 h-0.5 bg-primary transition-opacity duration-300 ${stage === 1 ? 'opacity-100' : 'opacity-0'}`}
                  style={{ top: scanTop }}
                />
                <div
                  className={`absolute inset-0 bg-background transition-opacity duration-700 ${stage >= 3 ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
                  aria-hidden={stage < 3}
                >
                  <AnswerCard count={false} />
                </div>
              </div>
            </PhoneFrame>
          </div>

          <div className="col-span-4 pl-4">
            <Ledger stage={stage} inHand={inHand} extra={extra} />
          </div>
        </div>
        <motion.div aria-hidden className="absolute bottom-0 left-0 h-0.5 bg-primary" style={{ width: barWidth }} />
      </div>
    </section>
  )
}

function StaticStory() {
  return (
    <section className={`${SHELL} grid gap-10 py-16 lg:grid-cols-2`} aria-label="How one check works">
      <ol className="space-y-6">
        {STEPS.map((s) => (
          <li key={s.n} className="border-l-2 border-primary pl-5">
            <p className="font-mono text-xs text-muted-foreground">{s.n}</p>
            <p className="mt-1 text-xl font-semibold tracking-tight">{s.title}</p>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
          </li>
        ))}
      </ol>
      <PhoneCard />
    </section>
  )
}

export function Story() {
  const desktop = useDesktop()
  const reduce = useReducedMotion()
  return desktop && !reduce ? <PinnedStory /> : <StaticStory />
}
