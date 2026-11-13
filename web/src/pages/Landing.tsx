import { ArrowDown, ArrowRight } from 'lucide-react'
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react'
import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { BigNumbers, CallToAction, Catches, LiveStats, ScamWall } from '@/site/Sections'
import { Story } from '@/site/Story'
import { Magnetic, Reveal, WordReveal } from '@/site/motion'

// Public website, Home (tasks H1 to H3 and H7, D47). Desktop first.
// Hero (type as the picture) -> pinned scroll story -> scam wall -> big numbers -> what it
// catches -> live numbers -> call to action with the QR.

function Hero() {
  const ref = useRef<HTMLElement>(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] })
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.86])
  const opacity = useTransform(scrollYProgress, [0, 0.85], [1, 0])
  const y = useTransform(scrollYProgress, [0, 1], [0, -120])

  return (
    <section ref={ref} className="relative flex min-h-[calc(100svh-4rem)] flex-col overflow-hidden px-[3vw] pt-[3vw] pb-8">
      <motion.div className="flex flex-1 origin-top-left flex-col" style={reduce ? undefined : { scale, opacity, y }}>
        <Reveal>
          <p className="mb-[2vw] flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
            <span className="font-mono text-primary">01</span>
            <span className="h-px w-8 bg-foreground/40" aria-hidden />
            Loan offers, read aloud
          </p>
        </Reveal>
        <WordReveal
          text="Loan lene se pehle,"
          label="Loan lene se pehle, suno."
          className="text-[9.6vw] leading-[0.9] font-semibold tracking-[-0.055em] whitespace-nowrap"
        />
        <div className="flex flex-1 flex-col justify-between gap-10 lg:flex-row lg:items-end">
          <WordReveal
            as="p"
            text="suno."
            label=""
            accent="suno."
            delay={0.4}
            className="text-[25vw] leading-[0.82] font-semibold tracking-[-0.07em] lg:text-[23vw]"
          />
          <Reveal delay={0.9} className="max-w-md pb-[1.5vw] lg:text-right">
            <p className="text-lg leading-relaxed text-muted-foreground lg:text-xl">
              Raju sells vegetables and cannot read loan terms. He sends a photo of the offer and hears, in his own
              language, what he gets, what he repays and how much extra that is.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4 lg:justify-end">
              <Magnetic>
                <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-14 px-8 text-base' })}>
                  Check an offer
                  <ArrowRight className="size-4" aria-hidden />
                </Link>
              </Magnetic>
            </div>
          </Reveal>
        </div>
      </motion.div>
      <p className="mt-6 flex items-center gap-2 text-xs tracking-[0.2em] text-muted-foreground uppercase">
        <ArrowDown className="size-3.5 animate-bounce" aria-hidden />
        Scroll to watch one check
      </p>
    </section>
  )
}

export default function Landing() {
  return (
    <>
      <Hero />
      <Story />
      <ScamWall />
      <BigNumbers />
      <Catches />
      <LiveStats />
      <CallToAction />
    </>
  )
}
