import { ArrowRight, FileText, Landmark, ShieldAlert } from 'lucide-react'
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { QRCodeSVG } from 'qrcode.react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { api, type Stats } from '@/lib/api'
import { CountUp, EASE, Magnetic, Reveal, Rule } from './motion'
import { SHELL } from './shell'

// The sections of the public Home page below the scroll story (H2, H3, H7; D47).

function Eyebrow({ n, children }: { n: string; children: string }) {
  return (
    <p className="mb-8 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
      <span className="font-mono text-primary">{n}</span>
      <span className="h-px w-8 bg-foreground/40" aria-hidden />
      {children}
    </p>
  )
}

// ---------------------------------------------------------------- scam marquee + stamp
const ROW_A = ['Instant loan ₹50,000 in 5 minutes', 'No documents needed', 'Guaranteed ₹5 lakh approval', 'Pre-approved! Apply now']
const ROW_B = ['Pay ₹1,499 to release funds', 'Urgent! Offer ends today', 'Refundable insurance charge ₹1,200', 'Click the link now']

function MarqueeRow({ items, outlined }: { items: string[]; outlined?: boolean }) {
  const text = outlined
    ? 'text-transparent [-webkit-text-stroke:1.5px_var(--foreground)] opacity-70'
    : 'text-foreground/15'
  return (
    <div className="flex shrink-0 items-center gap-[4vw] pr-[4vw]">
      {[...items, ...items, ...items].map((line, i) => (
        <span key={i} className={`text-[6.5vw] leading-none font-semibold tracking-[-0.03em] whitespace-nowrap ${text}`}>
          {line}
        </span>
      ))}
    </div>
  )
}

export function ScamWall() {
  const ref = useRef<HTMLElement>(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const left = useTransform(scrollYProgress, [0, 1], ['0%', '-45%'])
  const right = useTransform(scrollYProgress, [0, 1], ['-45%', '0%'])
  return (
    <section ref={ref} className="overflow-hidden border-y border-border py-24">
      <div className={SHELL}>
        <Eyebrow n="02">What lands on his phone every week</Eyebrow>
      </div>
      <div aria-hidden className="space-y-[2vw]">
        <motion.div className="flex w-max" style={reduce ? undefined : { x: left }}>
          <MarqueeRow items={ROW_A} outlined />
        </motion.div>
        <motion.div className="flex w-max" style={reduce ? undefined : { x: right }}>
          <MarqueeRow items={ROW_B} />
        </motion.div>
      </div>

      <div className={`${SHELL} mt-24 grid items-center gap-12 lg:grid-cols-12`}>
        <div className="relative pb-24 lg:col-span-8">
          <p className="text-[clamp(2rem,4.6vw,4.5rem)] leading-[1.02] font-semibold tracking-[-0.03em]">
            “Your loan is approved. Pay ₹1,499 processing fee to release funds.”
          </p>
          <motion.div
            className="absolute bottom-0 left-0 border-4 border-primary bg-background px-6 py-3 text-primary lg:left-[38%]"
            initial={reduce ? false : { scale: 2.6, opacity: 0, rotate: -18 }}
            whileInView={{ scale: 1, opacity: 1, rotate: -7 }}
            viewport={{ once: true, margin: '-25% 0px' }}
            transition={{ type: 'spring', stiffness: 260, damping: 15, delay: 0.25 }}
            style={{ rotate: -7 }}
          >
            <p className="text-xs font-semibold tracking-[0.3em] uppercase">Savdhaan</p>
            <p className="text-2xl leading-tight font-black tracking-tight uppercase sm:text-3xl">Paise mat bhejo</p>
          </motion.div>
        </div>
        <Reveal className="lg:col-span-4" delay={0.2}>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Asking for money before a loan is the scam itself. KarzSamjho says so out loud, in Hindi, Bengali or
            Marathi, before Raju pays anything.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- the two big numbers
export function BigNumbers() {
  return (
    <section className={`${SHELL} py-28`}>
      <Eyebrow n="03">The same offer, in plain numbers</Eyebrow>
      <div className="grid items-end gap-6 lg:grid-cols-12">
        <p className="text-[clamp(4.5rem,13vw,11.5rem)] leading-[0.82] font-semibold tracking-[-0.06em] text-primary lg:col-span-8">
          <CountUp to={1200} prefix="₹" />
        </p>
        <Reveal className="pb-4 lg:col-span-4">
          <p className="text-2xl leading-snug font-medium tracking-tight">extra, on ₹3,800 in hand, in 7 days.</p>
          <p className="mt-3 text-muted-foreground">The ad said “loan ₹5,000”. The fee came out first.</p>
        </Reveal>
      </div>
      <Rule className="my-16" />
      <div className="grid items-end gap-6 lg:grid-cols-12">
        <Reveal className="order-2 pb-4 lg:order-1 lg:col-span-4">
          <p className="text-2xl leading-snug font-medium tracking-tight">a year, as a simple yearly rate.</p>
          <p className="mt-3 text-muted-foreground">
            Raju does not need the percentage. He hears one line: “1200 rupaye zyada.”
          </p>
        </Reveal>
        <p className="order-1 text-right text-[clamp(4.5rem,13vw,11.5rem)] leading-[0.82] font-semibold tracking-[-0.06em] lg:order-2 lg:col-span-8">
          <CountUp to={1647} suffix="%" />
        </p>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- what it catches
const CATCHES = [
  {
    icon: ShieldAlert,
    title: 'Money asked first',
    body: 'An offer that wants a fee before the loan gets a spoken warning. A code rule backs up the AI in five scripts.',
  },
  {
    icon: Landmark,
    title: 'Who stands behind the app',
    body: 'The app name and its link are matched against RBI’s directory of digital lending apps. Found, similar or not found, with the list date. Never “safe”, never “illegal”.',
  },
  {
    icon: FileText,
    title: 'Harassment, on record',
    body: 'Forwarded threats are matched to RBI’s recovery rules, chained with SHA-256 so edits show, and turned into an English evidence PDF with a complaint letter.',
  },
]

export function Catches() {
  return (
    <section className="border-t border-border">
      <div className={`${SHELL} py-28`}>
        <Eyebrow n="04">Beyond the cost</Eyebrow>
        <div className="grid border-t border-border lg:grid-cols-3">
          {CATCHES.map((c, i) => (
            <Reveal
              key={c.title}
              delay={i * 0.12}
              className="group border-b border-border py-10 lg:border-r lg:border-b-0 lg:px-8 lg:first:pl-0 lg:last:border-r-0"
            >
              <c.icon className="size-7 text-primary transition-transform duration-500 group-hover:-translate-y-1" aria-hidden />
              <h3 className="mt-8 text-2xl font-semibold tracking-tight">{c.title}</h3>
              <p className="mt-3 leading-relaxed text-muted-foreground">{c.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- live numbers (H2)
type Live = { state: 'loading' } | { state: 'error' } | { state: 'ready'; stats: Stats }

export function LiveStats() {
  const [live, setLive] = useState<Live>({ state: 'loading' })

  useEffect(() => {
    let alive = true
    const load = () =>
      api
        .stats()
        .then((stats) => alive && setLive({ state: 'ready', stats }))
        .catch(() => alive && setLive((prev) => (prev.state === 'ready' ? prev : { state: 'error' })))
    load()
    const timer = setInterval(load, 15000)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [])

  const cell = 'border-b border-border py-10 lg:border-r lg:border-b-0 lg:px-8 lg:first:pl-0 lg:last:border-r-0'
  const big = 'text-[clamp(3rem,6vw,5.5rem)] leading-none font-semibold tracking-[-0.04em]'

  return (
    <section className="border-t border-border bg-card">
      <div className={`${SHELL} py-28`}>
        <Eyebrow n="05">Live from this server</Eyebrow>
        {live.state === 'loading' && (
          <div className="grid border-t border-border lg:grid-cols-3" aria-busy="true" aria-label="Loading the numbers">
            {[0, 1, 2].map((i) => (
              <div key={i} className={cell}>
                <div className="h-16 w-40 animate-pulse rounded-md bg-foreground/10" />
                <div className="mt-4 h-4 w-48 animate-pulse rounded-md bg-foreground/10" />
              </div>
            ))}
          </div>
        )}
        {live.state === 'error' && (
          <div className="border-t border-border py-10">
            <p className="text-2xl font-semibold tracking-tight">The server is resting.</p>
            <p className="mt-2 max-w-xl text-muted-foreground">
              These numbers come straight from the running app, so there is nothing to show while it is off. They
              appear here by themselves when it is back.
            </p>
          </div>
        )}
        {live.state === 'ready' && live.stats.checks === 0 && (
          <div className="border-t border-border py-10">
            <p className="text-2xl font-semibold tracking-tight">No checks yet.</p>
            <p className="mt-2 max-w-xl text-muted-foreground">
              Send the first loan offer and this page starts counting.{' '}
              <Link to="/check" className="text-primary underline-offset-4 hover:underline">
                Check an offer
              </Link>
            </p>
          </div>
        )}
        {live.state === 'ready' && live.stats.checks > 0 && (
          <dl className="grid border-t border-border lg:grid-cols-3">
            <div className={cell}>
              <dd className={big}>
                <CountUp to={live.stats.checks} />
              </dd>
              <dt className="mt-3 text-muted-foreground">offers checked</dt>
            </div>
            <div className={cell}>
              <dd className={big}>
                {live.stats.median_seconds.toFixed(1)}
                <span className="text-[0.4em] tracking-normal"> sec</span>
              </dd>
              <dt className="mt-3 text-muted-foreground">median time to an answer</dt>
            </div>
            <div className={cell}>
              <dd className={`${big} text-primary`}>
                <CountUp to={Math.round(live.stats.extra_rupees_flagged)} prefix="₹" />
              </dd>
              <dt className="mt-3 text-muted-foreground">extra cost flagged on costly offers</dt>
            </div>
          </dl>
        )}
        <p className="mt-8 text-sm text-muted-foreground">
          Counted by the app itself. Test offers are synthetic; no real borrower data.
        </p>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- call to action + QR (H7)
export function CallToAction() {
  const reduce = useReducedMotion()
  const url = `${window.location.origin}/check?mode=raju`
  return (
    <section className="border-t border-border">
      <div className={`${SHELL} grid items-end gap-12 py-28 lg:grid-cols-12`}>
        <div className="lg:col-span-8">
          <Eyebrow n="06">Try it</Eyebrow>
          <motion.p
            className="text-[clamp(3.5rem,11vw,10rem)] leading-[0.88] font-semibold tracking-[-0.05em]"
            initial={reduce ? false : { opacity: 0, y: 60 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-15% 0px' }}
            transition={{ duration: 1, ease: EASE }}
          >
            Ek photo. <span className="text-primary">Ek awaaz.</span>
          </motion.p>
          <div className="mt-12">
            <Magnetic>
              <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-16 px-10 text-lg' })}>
                Check an offer
                <ArrowRight className="size-5" aria-hidden />
              </Link>
            </Magnetic>
          </div>
        </div>
        <Reveal className="lg:col-span-4" delay={0.2}>
          <div className="inline-block border border-border bg-background p-4 text-foreground">
            <QRCodeSVG value={url} size={168} bgColor="transparent" fgColor="currentColor" marginSize={0} />
          </div>
          <p className="mt-4 text-sm font-medium">Scan to open it on a phone</p>
          <p className="mt-1 max-w-xs text-sm text-muted-foreground">
            Opens the simple mode for Raju: one camera button, one play button. Phone and this screen must be on
            the same Wi-Fi.
          </p>
        </Reveal>
      </div>
    </section>
  )
}
