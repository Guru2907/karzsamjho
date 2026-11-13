import { ArrowRight, Check, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Columns, PageHero, Section } from '@/site/Page'
import { ScrollText, StickySteps, TypedLines, type Step } from '@/site/fx'
import { CountUp, Magnetic, Reveal } from '@/site/motion'

// Public website: how it works, the proof and the limits (task H5, D47).
// Every number here is from the repo: docs/TESTING.md and the code in api/core/.

const mono = 'font-mono text-sm leading-8'

/** Step 1 picture: the ad's printed numbers become a fixed form. */
function ReadVisual() {
  const ring = 'rounded-sm px-1 shadow-[0_0_0_2px_var(--primary)]'
  return (
    <div className="grid gap-6">
      <div className="bg-foreground p-5 text-background">
        <p className="text-xl leading-none font-black tracking-tight uppercase">Instant loan in 5 min!</p>
        <p className="mt-4 flex flex-wrap gap-x-5 gap-y-3 text-sm font-medium">
          <span>
            Loan <span className={ring}>₹5,000</span>
          </span>
          <span>
            Fee <span className={ring}>₹1,200</span>
          </span>
          <span>
            Repay <span className={ring}>₹5,000</span>
          </span>
          <span>
            In <span className={ring}>7 days</span>
          </span>
        </p>
      </div>
      <pre className={`${mono} text-muted-foreground`}>
        {'{ '}
        <span className="text-foreground">"principal"</span>: 5000, <span className="text-foreground">"fees"</span>: 1200,
        {'\n  '}
        <span className="text-foreground">"repay_total"</span>: 5000, <span className="text-foreground">"tenure_days"</span>: 7,
        {'\n  '}
        <span className="text-foreground">"in_hand"</span>: <span className="text-primary">null</span>{' '}
        <span className="opacity-70"># not printed, so not guessed</span>
        {' }'}
      </pre>
    </div>
  )
}

/** Step 2 picture: the ledger the code works out. */
function MathsVisual() {
  const row = 'flex items-baseline justify-between gap-6 border-b border-border py-3 font-mono text-sm'
  return (
    <div>
      <div className={row}>
        <span className="text-muted-foreground">5,000 − 1,200</span>
        <span className="text-4xl font-semibold tracking-tight text-emerald-700 dark:text-emerald-400">₹3,800</span>
      </div>
      <div className={row}>
        <span className="text-muted-foreground">5,000 − 3,800</span>
        <span className="text-4xl font-semibold tracking-tight text-red-700 dark:text-red-400">₹1,200</span>
      </div>
      <div className={`${row} border-b-0`}>
        <span className="text-muted-foreground">1,200 ÷ 3,800 × 365 ÷ 7</span>
        <span className="text-4xl font-semibold tracking-tight text-primary">1,647%</span>
      </div>
      <p className="mt-4 text-sm text-muted-foreground">in hand · extra · a year. Same offer, same answer, every time.</p>
    </div>
  )
}

/** Step 3 picture: two readers compared field by field (the case from our tests). */
function RecheckVisual() {
  const rows: [string, string, string, boolean][] = [
    ['fee', '1,200', '1,200', true],
    ['repay', '5,000', '5,000', true],
    ['in hand', '4,000', 'not printed', false],
  ]
  return (
    <div>
      <div className="grid grid-cols-4 border-b border-border pb-3 font-mono text-xs tracking-wide text-muted-foreground uppercase">
        <span />
        <span>Reader 1</span>
        <span>Reader 2</span>
        <span className="text-right">Agree</span>
      </div>
      {rows.map(([field, a, b, ok]) => (
        <div key={field} className="grid grid-cols-4 items-center border-b border-border py-4 font-mono text-sm">
          <span className="text-muted-foreground">{field}</span>
          <span>{a}</span>
          <span>{b}</span>
          <span className="flex justify-end">
            {ok ? (
              <Check className="size-5 text-emerald-700 dark:text-emerald-400" aria-label="agree" />
            ) : (
              <X className="size-5 text-red-700 dark:text-red-400" aria-label="disagree" />
            )}
          </span>
        </div>
      ))}
      <p className="mt-5 leading-relaxed">
        The first reader invented an in-hand amount. The second did not see one. So that value is set aside and the
        code works it out: <span className="font-semibold text-emerald-700 dark:text-emerald-400">₹3,800</span>.
      </p>
    </div>
  )
}

const STEPS: Step[] = [
  {
    n: '01',
    title: 'The AI only reads.',
    body: 'A vision model copies the numbers printed on the offer into a fixed form. It is told never to add, subtract or guess. For a pasted SMS, any number it returns that is not written in the message is thrown away.',
    visual: <ReadVisual />,
  },
  {
    n: '02',
    title: 'Python calculates.',
    body: 'Plain, tested code checks that the printed numbers agree, works out what the ad left unsaid, and does every rupee of the maths.',
    visual: <MathsVisual />,
  },
  {
    n: '03',
    title: 'A second AI re-checks.',
    body: 'If the sums do not add up, a model from a different company reads the photo again. What the two disagree on is never shown as fact. If code cannot work it out either, Raju hears “pata nahi chala”.',
    visual: <RecheckVisual />,
  },
]

const CODE = [
  <span key="c" className="text-muted-foreground"># api/core/maths.py · the demo offer: loan 5,000 · fee 1,200 · 7 days</span>,
  <span key="l1">in_hand    = principal - fees              <span className="text-emerald-700 dark:text-emerald-400">→ 3,800</span></span>,
  <span key="l2">extra      = repay_total - in_hand         <span className="text-red-700 dark:text-red-400">→ 1,200</span></span>,
  <span key="l3">per_day    = extra / tenure_days           <span className="text-muted-foreground">→ 171</span></span>,
  <span key="l4">cost_pct   = extra / in_hand               <span className="text-muted-foreground">→ 0.316</span></span>,
  <span key="l5">apr_simple = cost_pct * 365 / tenure_days  <span className="text-primary">→ 1,647%</span></span>,
]

const LADDER = [
  ['Read a photo', 'Qwen (on Groq)', 'Gemini Flash-Lite', '“Photo saaf nahi hai, dobara bhejo”'],
  ['Read an SMS', 'gpt-oss-20b (on Groq)', 'Gemini Flash-Lite, then plain pattern matching', 'more “pata nahi chala”'],
  ['Hear a voice note', 'Whisper (on Groq)', 'Gemini Flash-Lite', '“Awaaz saaf nahi aayi, dobara bolo”'],
  ['Speak the answer', 'edge-tts', 'none', 'the card arrives without audio'],
  ['Same photo again', 'saved answer', 'no AI call at all', 'instant'],
]

const LIMITS = [
  'Every test offer is synthetic. No real borrower has used it yet.',
  '“Not found in RBI’s list” is never “illegal”: the directory is reported by lenders themselves, and names vary.',
  'The cost bands (36% and 100% a year) are our own rule of thumb, not an RBI limit.',
  'Voice notes are understood in Hindi only. Bengali and Marathi are reply voices, and their sentences still need a native speaker’s check.',
  'The evidence PDF cannot prove a message is genuine. Its hash chain proves the record was not edited after logging.',
  'Free AI tiers may learn from what they are sent. A real deployment needs paid or self-hosted models.',
]

export default function How() {
  return (
    <>
      <PageHero label="How it works" title="The AI reads." accent="Python calculates.">
        Scroll: three jobs, kept strictly apart.
      </PageHero>

      <section className="border-t border-border px-[3vw] py-28">
        <ScrollText
          className="max-w-[22ch] text-[clamp(2.2rem,5.6vw,6rem)] leading-[1.02] font-semibold tracking-[-0.04em] lg:max-w-[24ch]"
          text="A wrong rupee number is the one mistake this product cannot make. So the AI is only the eyes."
        />
      </section>

      <section className="border-t border-border bg-card px-[3vw] py-16 lg:py-0">
        <StickySteps steps={STEPS} />
      </section>

      <Section n="04" label="All of the maths">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          <Reveal className="lg:col-span-4">
            <h2 className="text-[clamp(2rem,4vw,3.5rem)] leading-[1] font-semibold tracking-[-0.03em]">
              Five lines. No model involved.
            </h2>
            <p className="mt-6 leading-relaxed text-muted-foreground">
              If an input is missing or does not add up, every number that depends on it becomes “could not verify”,
              and the verdict becomes “cannot say”.
            </p>
          </Reveal>
          <div className="overflow-x-auto border border-foreground/25 bg-card p-8 lg:col-span-8">
            <TypedLines lines={CODE} className="font-mono text-[0.95rem] leading-9" />
          </div>
        </div>
      </Section>

      <Section n="05" label="When a service is down" tinted>
        <div className="border-t border-foreground/25">
          {LADDER.map((row, i) => (
            <Reveal key={row[0]} delay={i * 0.06}>
              <div className="group grid items-baseline gap-2 border-b border-border py-6 transition-colors hover:bg-background lg:grid-cols-12 lg:gap-6 lg:px-4">
                <p className="text-2xl font-semibold tracking-tight lg:col-span-3">{row[0]}</p>
                <p className="lg:col-span-3">{row[1]}</p>
                <p className="flex items-baseline gap-2 text-muted-foreground lg:col-span-3">
                  <ArrowRight className="size-4 shrink-0 translate-y-0.5 text-primary transition-transform group-hover:translate-x-1" aria-hidden />
                  {row[2]}
                </p>
                <p className="text-sm text-muted-foreground lg:col-span-3 lg:text-right">{row[3]}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <p className="mt-6 max-w-2xl text-sm text-muted-foreground">
          First choice, then the backup, then what Raju sees if both fail. Each service is tried once, with a time
          limit and no retry. He never sees an error code.
        </p>
      </Section>

      <Section n="06" label="Measured, not promised">
        <Columns cols={4}>
          <div>
            <p className="text-[clamp(3rem,5.5vw,5rem)] leading-none font-semibold tracking-[-0.04em]">
              <CountUp to={450} suffix="+" />
            </p>
            <p className="mt-3 text-muted-foreground">automated tests, run on every change, with no internet needed</p>
          </div>
          <div>
            <p className="text-[clamp(3rem,5.5vw,5rem)] leading-none font-semibold tracking-[-0.04em]">3.9 s</p>
            <p className="mt-3 text-muted-foreground">photo to card and voice, on free AI tiers</p>
          </div>
          <div>
            <p className="text-[clamp(3rem,5.5vw,5rem)] leading-none font-semibold tracking-[-0.04em]">7.5 s</p>
            <p className="mt-3 text-muted-foreground">when the numbers contradict and the second AI reads again</p>
          </div>
          <div>
            <p className="text-[clamp(3rem,5.5vw,5rem)] leading-none font-semibold tracking-[-0.04em] text-primary">0.0 s</p>
            <p className="mt-3 text-muted-foreground">for a photo seen before: the saved answer, no AI call</p>
          </div>
        </Columns>
        <p className="mt-8 text-sm text-muted-foreground">Real runs on 13 and 14 Nov 2026, on synthetic loan offers.</p>
      </Section>

      <Section n="07" label="What it cannot do" tinted>
        <ul className="grid gap-x-12 border-t border-border lg:grid-cols-2">
          {LIMITS.map((limit, i) => (
            <Reveal key={limit} delay={(i % 2) * 0.1}>
              <li className="flex gap-5 border-b border-border py-6">
                <span className="font-mono text-xs text-primary">{String(i + 1).padStart(2, '0')}</span>
                <span className="leading-relaxed">{limit}</span>
              </li>
            </Reveal>
          ))}
        </ul>
        <div className="mt-14">
          <Magnetic>
            <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-16 px-10 text-lg' })}>
              Check an offer
              <ArrowRight className="size-5" aria-hidden />
            </Link>
          </Magnetic>
        </div>
      </Section>
    </>
  )
}
