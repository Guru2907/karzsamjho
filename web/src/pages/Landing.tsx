import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { PhoneCard } from '@/site/PhoneCard'
import { Reveal, WordReveal } from '@/site/motion'
import { SHELL } from '@/site/shell'

// Public website, Home (tasks H1 to H3, D47). W1: the hero only, as the look-and-feel preview.

const FACTS = [
  { value: '~4 sec', label: 'from photo to answer, measured' },
  { value: '3 voices', label: 'Hindi, Bengali, Marathi' },
  { value: '0 guesses', label: 'unclear numbers are said to be unclear' },
]

function Hero() {
  return (
    <section className={`${SHELL} grid gap-12 py-14 sm:py-20 lg:grid-cols-12 lg:gap-8 lg:py-28`}>
      <div className="lg:col-span-7">
        <Reveal>
          <p className="mb-6 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
            <span className="h-px w-8 bg-foreground/40" aria-hidden />
            Loan offers, read aloud
          </p>
        </Reveal>
        <WordReveal
          text="Loan lene se pehle, suno."
          accent="suno."
          className="text-[clamp(3rem,9.5vw,7rem)] leading-[0.95] font-semibold tracking-[-0.04em]"
        />
        <Reveal delay={0.5}>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Raju sells vegetables and cannot read loan terms. He sends a photo of the offer and hears, in his own
            language, what he gets, what he repays and how much extra that is.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-12 px-6 text-base' })}>
              Check an offer
              <ArrowRight className="size-4" aria-hidden />
            </Link>
            <span className="text-sm text-muted-foreground">No login. A photo, an SMS or a voice note.</span>
          </div>
        </Reveal>
        <Reveal delay={0.7}>
          <dl className="mt-14 grid grid-cols-1 border-t border-border sm:grid-cols-3">
            {FACTS.map((f) => (
              <div
                key={f.value}
                className="border-b border-border py-5 sm:border-r sm:border-b-0 sm:px-5 sm:first:pl-0 sm:last:border-r-0"
              >
                <dt className="text-2xl font-semibold tracking-tight">{f.value}</dt>
                <dd className="mt-1 text-sm text-muted-foreground">{f.label}</dd>
              </div>
            ))}
          </dl>
        </Reveal>
      </div>
      <Reveal delay={0.3} className="lg:col-span-5 lg:pl-8">
        <PhoneCard />
        <p className="mx-auto mt-4 max-w-[22rem] text-center text-xs text-muted-foreground">
          The demo offer: loan ₹5,000, fee ₹1,200, 7 days. Press play to hear the answer.
        </p>
      </Reveal>
    </section>
  )
}

export default function Landing() {
  return <Hero />
}
