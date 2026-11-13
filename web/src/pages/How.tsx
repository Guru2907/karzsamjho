import { ArrowRight, Calculator, Eye, RefreshCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Columns, PageHero, Section } from '@/site/Page'
import { CountUp, Reveal } from '@/site/motion'

// Public website: how it works, the proof and the limits (task H5, D47).
// Every number here is from the repo: docs/TESTING.md and the code in api/core/.

const STEPS = [
  {
    icon: Eye,
    title: 'The AI only reads',
    body: 'A vision model copies the numbers printed on the offer into a fixed form: loan, fee, repayment, days. It is told never to add, subtract or guess. For a pasted SMS, any number it returns that is not written in the message is thrown away.',
  },
  {
    icon: Calculator,
    title: 'Python calculates',
    body: 'Plain, tested code checks that the printed numbers agree, works out what the ad left unsaid, and does every rupee of the maths. The same offer always gives the same answer.',
  },
  {
    icon: RefreshCcw,
    title: 'A second AI re-checks',
    body: 'If the sums do not add up, a model from a different company reads the photo again. Whatever the two disagree on is shown as “pata nahi chala”: could not verify. Never a guess.',
  },
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
        A wrong rupee number is the one mistake this product cannot make. So the AI is only the eyes. Everything that
        becomes a number on Raju’s card is worked out by code a person can read and test.
      </PageHero>

      <Section n="01" label="Three jobs, kept apart">
        <Columns>
          {STEPS.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.12}>
              <s.icon className="size-7 text-primary" aria-hidden />
              <h2 className="mt-8 text-2xl font-semibold tracking-tight">{s.title}</h2>
              <p className="mt-3 leading-relaxed text-muted-foreground">{s.body}</p>
            </Reveal>
          ))}
        </Columns>
      </Section>

      <Section n="02" label="All of the maths" tinted>
        <div className="grid items-start gap-12 lg:grid-cols-12">
          <Reveal className="lg:col-span-5">
            <h2 className="text-[clamp(2rem,4vw,3.5rem)] leading-[1] font-semibold tracking-[-0.03em]">
              Five lines. No model involved.
            </h2>
            <p className="mt-6 leading-relaxed text-muted-foreground">
              From <span className="font-mono text-sm text-foreground">api/core/maths.py</span>. If an input is missing
              or does not add up, every number that depends on it becomes “could not verify”, and the verdict becomes
              “cannot say”.
            </p>
          </Reveal>
          <Reveal className="lg:col-span-7" delay={0.15}>
            <pre className="overflow-x-auto border border-border bg-background p-6 font-mono text-sm leading-8">
              <span className="text-muted-foreground"># the demo offer: loan 5,000 · fee 1,200 · repay 5,000 · 7 days{'\n'}</span>
              in_hand    = principal - fees              <span className="text-emerald-700 dark:text-emerald-400">→ 3,800</span>
              {'\n'}extra      = repay_total - in_hand         <span className="text-red-700 dark:text-red-400">→ 1,200</span>
              {'\n'}per_day    = extra / tenure_days           <span className="text-muted-foreground">→ 171</span>
              {'\n'}cost_pct   = extra / in_hand               <span className="text-muted-foreground">→ 0.316</span>
              {'\n'}apr_simple = cost_pct * 365 / tenure_days  <span className="text-primary">→ 1,647%</span>
            </pre>
          </Reveal>
        </div>
      </Section>

      <Section n="03" label="When a service is down">
        <Reveal>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[44rem] border-t border-border text-left">
              <thead>
                <tr className="text-xs tracking-[0.15em] text-muted-foreground uppercase">
                  {['Job', 'First', 'Backup', 'If both fail'].map((h) => (
                    <th key={h} className="border-b border-border py-4 pr-6 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {LADDER.map((row) => (
                  <tr key={row[0]} className="border-b border-border align-top">
                    <td className="py-5 pr-6 text-lg font-semibold tracking-tight">{row[0]}</td>
                    <td className="py-5 pr-6">{row[1]}</td>
                    <td className="py-5 pr-6 text-muted-foreground">{row[2]}</td>
                    <td className="py-5 text-muted-foreground">{row[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-6 max-w-2xl text-sm text-muted-foreground">
            Each service is tried once, with a time limit and no retry. A rate limit moves to the backup at once. Raju
            never sees an error code, only a short line in Hindi.
          </p>
        </Reveal>
      </Section>

      <Section n="04" label="Measured, not promised" tinted>
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

      <Section n="05" label="What it cannot do">
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
          <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-14 px-8 text-base' })}>
            Check an offer
            <ArrowRight className="size-4" aria-hidden />
          </Link>
        </div>
      </Section>
    </>
  )
}
