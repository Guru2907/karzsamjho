import { ArrowDown, ArrowUpRight, Check, Copy } from 'lucide-react'
import { AnimatePresence, motion, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { ScrollText } from '@/site/fx'
import { Magnetic, Reveal, WordReveal } from '@/site/motion'
import { SHELL } from '@/site/shell'

// Public website: the call to action for foundations, NGOs, non-profits and other backers
// (task H8, D47). Different shape from the other pages on purpose: an inverted opening, a
// sideways scroll, and a letter the visitor builds and sends.
// Honesty rules: no invented contact details, no invented costs, nothing claimed as running.

const REPO = 'https://github.com/Guru2907/karzsamjho'

// ---------------------------------------------------------------- three ways to back it
const WAYS = [
  {
    n: '01',
    title: 'Run a pilot',
    line: 'Twenty borrowers. Four weeks. One partner.',
    bring: 'A field team or bank-mitra network that already sits beside borrowers.',
    get: 'Counts you can publish: offers checked, offers refused after hearing the cost, complaints filed with evidence.',
  },
  {
    n: '02',
    title: 'Lend a voice',
    line: 'A new language is one sentence and one voice.',
    bring: 'A native speaker to approve each spoken sentence. Today that is Bengali and Marathi; tomorrow, yours.',
    get: 'The same answer, read aloud in the language your borrowers think in.',
  },
  {
    n: '03',
    title: 'Fund the helper',
    line: 'A proposal, not a product.',
    bring: 'Support for a small per-check commission to the bank mitra, so the borrower never pays.',
    get: 'A real test of whether paying the helper makes the checking happen. We do not know yet. That is the point of asking.',
  },
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

function WayPanel({ way }: { way: (typeof WAYS)[number] }) {
  return (
    <article className="flex h-full w-full shrink-0 flex-col justify-between border border-foreground/25 bg-card p-8 lg:w-[74vw] lg:p-14">
      <div>
        <p className="font-mono text-sm text-primary">{way.n} / 03</p>
        <h3 className="mt-6 text-[clamp(3rem,9vw,9.5rem)] leading-[0.88] font-semibold tracking-[-0.05em]">{way.title}</h3>
        <p className="mt-6 text-xl text-muted-foreground lg:text-2xl">{way.line}</p>
      </div>
      <dl className="mt-10 grid gap-8 border-t border-border pt-8 lg:grid-cols-2">
        <div>
          <dt className="text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">You bring</dt>
          <dd className="mt-3 text-lg leading-relaxed">{way.bring}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium tracking-[0.2em] text-primary uppercase">You get</dt>
          <dd className="mt-3 text-lg leading-relaxed">{way.get}</dd>
        </div>
      </dl>
    </article>
  )
}

/** The page pins and the three panels slide past sideways as the reader scrolls down. */
function Ways() {
  const ref = useRef<HTMLElement>(null)
  const desktop = useDesktop()
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  // 3 panels of 74vw + 2 gaps of 2vw + 3vw padding each side = 232vw; slide until the last one rests.
  const x = useTransform(scrollYProgress, [0.05, 0.95], ['0vw', '-132vw'])
  const bar = useTransform(scrollYProgress, [0, 1], ['0%', '100%'])

  if (!desktop || reduce) {
    return (
      <section className="space-y-6 px-[3vw] py-20">
        {WAYS.map((w) => (
          <WayPanel key={w.n} way={w} />
        ))}
      </section>
    )
  }
  return (
    <section ref={ref} className="relative h-[320vh]" aria-label="Three ways to back it">
      <div className="sticky top-0 flex h-svh flex-col justify-center overflow-hidden pt-16">
        <p className="mb-6 flex items-center gap-3 px-[3vw] text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          <span className="font-mono text-primary">02</span>
          <span className="h-px w-8 bg-foreground/40" aria-hidden />
          Three ways to back it · keep scrolling
        </p>
        <motion.div className="flex h-[68vh] w-max gap-[2vw] px-[3vw]" style={{ x }}>
          {WAYS.map((w) => (
            <WayPanel key={w.n} way={w} />
          ))}
        </motion.div>
        <motion.div aria-hidden className="absolute bottom-0 left-0 h-0.5 bg-primary" style={{ width: bar }} />
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- the letter
const ROLES = [
  {
    id: 'foundation',
    label: 'A foundation or funder',
    who: 'a foundation that funds financial inclusion work',
    ask: 'understand what a four-week pilot with one partner would need, and what you would measure',
  },
  {
    id: 'ngo',
    label: 'An NGO or SHG network',
    who: 'an NGO working with borrowers in the field',
    ask: 'try KarzSamjho with about twenty of the people we work with, and tell you honestly what works and what does not',
  },
  {
    id: 'lender',
    label: 'A bank, NBFC or bank-mitra network',
    who: 'part of a lending or banking-correspondent network',
    ask: 'see how our bank mitras could offer a loan-offer check at the counter, and how our apps appear in your RBI directory check',
  },
  {
    id: 'expert',
    label: 'Someone who can help',
    who: 'someone who can help: a native speaker, a lawyer, a researcher or a field worker',
    ask: 'offer my time: checking a language, the complaint routes, or the way you test',
  },
] as const

function letterFor(role: (typeof ROLES)[number]) {
  return [
    'Hello Team Y2K Devs,',
    '',
    `I am writing from ${role.who}.`,
    `We would like to ${role.ask}.`,
    '',
    'Name and organisation:',
    'Where we work:',
    'Best way to reach us:',
  ].join('\n')
}

function Letter() {
  const [roleId, setRoleId] = useState<(typeof ROLES)[number]['id']>('ngo')
  const [copied, setCopied] = useState(false)
  const reduce = useReducedMotion()
  const role = ROLES.find((r) => r.id === roleId) ?? ROLES[0]
  const letter = letterFor(role)
  const issueUrl = `${REPO}/issues/new?title=${encodeURIComponent(`Partner: ${role.label}`)}&body=${encodeURIComponent(letter)}`

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(letter)
      setCopied(true)
      setTimeout(() => setCopied(false), 2200)
    } catch {
      setCopied(false)
    }
  }

  return (
    <section className="border-t border-border">
      <div className={`${SHELL} grid gap-14 py-28 lg:grid-cols-12`}>
        <div className="lg:col-span-5">
          <p className="mb-8 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
            <span className="font-mono text-primary">03</span>
            <span className="h-px w-8 bg-foreground/40" aria-hidden />
            Write to us
          </p>
          <h2 className="text-[clamp(2.4rem,4.6vw,4.2rem)] leading-[0.98] font-semibold tracking-[-0.035em]">
            Who is <span className="text-primary">reading this?</span>
          </h2>
          <div className="mt-10 border-t border-foreground/25" role="radiogroup" aria-label="Who you are">
            {ROLES.map((r) => {
              const on = r.id === roleId
              return (
                <button
                  key={r.id}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => setRoleId(r.id)}
                  className={`group flex w-full items-center justify-between gap-4 border-b border-foreground/25 py-5 text-left text-xl font-medium tracking-tight transition-colors focus-visible:outline-none ${on ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                >
                  <span className="flex items-center gap-4">
                    <span
                      aria-hidden
                      className={`size-3 rounded-full border-2 border-primary transition-colors ${on ? 'bg-primary' : 'bg-transparent'}`}
                    />
                    {r.label}
                  </span>
                  <ArrowUpRight
                    className={`size-5 transition-all duration-300 ${on ? 'translate-x-0 text-primary opacity-100' : '-translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-60'}`}
                    aria-hidden
                  />
                </button>
              )
            })}
          </div>
        </div>

        <div className="lg:col-span-7">
          <div className="border border-foreground/25 bg-card">
            <p className="flex items-center justify-between border-b border-border px-6 py-3 font-mono text-xs text-muted-foreground">
              <span>message.txt</span>
              <span>edit anything before you send</span>
            </p>
            <AnimatePresence mode="wait">
              <motion.pre
                key={role.id}
                className="min-h-[19rem] px-6 py-6 font-sans text-lg leading-relaxed whitespace-pre-wrap"
                initial={reduce ? false : { opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduce ? undefined : { opacity: 0, y: -14 }}
                transition={{ duration: 0.28 }}
              >
                {letter}
              </motion.pre>
            </AnimatePresence>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Magnetic>
              <a
                href={issueUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-16 items-center gap-3 bg-primary px-9 text-lg font-medium text-primary-foreground transition-colors hover:bg-primary/85"
              >
                Send it on GitHub
                <ArrowUpRight className="size-5" aria-hidden />
              </a>
            </Magnetic>
            <button
              type="button"
              onClick={copy}
              className="inline-flex h-16 items-center gap-3 border border-foreground/25 px-8 text-lg font-medium transition-colors hover:bg-muted"
            >
              {copied ? <Check className="size-5 text-primary" aria-hidden /> : <Copy className="size-5" aria-hidden />}
              {copied ? 'Copied' : 'Copy the message'}
            </button>
          </div>
          <p className="mt-5 max-w-xl text-sm text-muted-foreground">
            “Send it on GitHub” opens this message as a public post on our open repository; you need a GitHub account,
            and you can edit it first. Or copy it and reach the team in person at COLOSSUS 3.0.
          </p>
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- page
const TRUTHS = [
  ['Who we are', 'Four students, Team Y2K Devs. Built at the COLOSSUS 3.0 hackathon in one night.'],
  ['What exists', 'A working Telegram bot and web app, 450+ automated tests, everything open source.'],
  ['What does not', 'No real borrower has used it. The test offers are synthetic. The commission model is an idea.'],
]

export default function Join() {
  return (
    <>
      <section className="flex min-h-svh flex-col justify-between bg-foreground px-[3vw] pt-36 pb-10 text-background">
        <div>
          <Reveal>
            <p className="mb-[2vw] flex items-center gap-3 text-xs font-medium tracking-[0.2em] uppercase opacity-60">
              <span className="h-px w-8 bg-background/50" aria-hidden />
              For foundations, NGOs and everyone who backs them
            </p>
          </Reveal>
          <WordReveal
            text="He cannot read it."
            label="He cannot read it. Help us read it to him."
            className="text-[clamp(3rem,9.4vw,10rem)] leading-[0.9] font-semibold tracking-[-0.05em]"
          />
          <WordReveal
            as="p"
            text="Help us read it to him."
            label=""
            delay={0.4}
            className="text-[clamp(3rem,9.4vw,10rem)] leading-[0.9] font-semibold tracking-[-0.05em] text-primary"
          />
        </div>
        <Reveal delay={0.9}>
          <div className="grid items-end gap-8 border-t border-background/25 pt-6 lg:grid-cols-12">
            <p className="max-w-xl text-lg leading-relaxed opacity-75 lg:col-span-7 lg:text-xl">
              KarzSamjho reads a loan offer aloud, in rupees, before the borrower signs. The software works. What it
              needs now is not code: it is people who already sit beside borrowers.
            </p>
            <p className="flex items-center gap-2 text-xs tracking-[0.2em] uppercase opacity-60 lg:col-span-5 lg:justify-end">
              <ArrowDown className="size-3.5 animate-bounce" aria-hidden />
              Three ways to back it
            </p>
          </div>
        </Reveal>
      </section>

      <section className="px-[3vw] py-28">
        <p className="mb-10 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          <span className="font-mono text-primary">01</span>
          <span className="h-px w-8 bg-foreground/40" aria-hidden />
          Why you
        </p>
        <ScrollText
          className="max-w-[26ch] text-[clamp(2.2rem,5.6vw,6rem)] leading-[1.02] font-semibold tracking-[-0.04em]"
          text="An app cannot walk into a village. A bank mitra, a field worker, a self-help group already has."
        />
      </section>

      <Ways />
      <Letter />

      <section className="border-t border-border bg-card">
        <div className={`${SHELL} py-24`}>
          <p className="mb-8 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
            <span className="font-mono text-primary">04</span>
            <span className="h-px w-8 bg-foreground/40" aria-hidden />
            Before you write, the plain truth
          </p>
          <dl className="border-t border-border">
            {TRUTHS.map(([k, v], i) => (
              <Reveal key={k} delay={i * 0.08}>
                <div className="grid gap-2 border-b border-border py-7 lg:grid-cols-12 lg:gap-8">
                  <dt className="text-2xl font-semibold tracking-tight lg:col-span-4">{k}</dt>
                  <dd className="text-lg leading-relaxed text-muted-foreground lg:col-span-8">{v}</dd>
                </div>
              </Reveal>
            ))}
          </dl>
        </div>
      </section>
    </>
  )
}
