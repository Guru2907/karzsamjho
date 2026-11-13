import { ArrowRight, ArrowUpRight, FileText, Headphones, Landmark, Languages, Store, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { PageHero, Section } from '@/site/Page'
import { HoverRows, ScrollText, ScrollTimeline, type HoverRow, type TimelineItem } from '@/site/fx'
import { Magnetic, Reveal } from '@/site/motion'

// Public website: for NGOs, bank mitras and other helpers (task H4, D47).
// The commission model is a proposal for a pilot. Nothing on this page claims it exists today.

const HELPERS: HoverRow[] = [
  {
    icon: Landmark,
    title: 'Bank mitras',
    body: 'The banking correspondent Raju already trusts. One more service at the same counter: “show me the offer before you sign.”',
  },
  {
    icon: Users,
    title: 'NGOs and SHGs',
    body: 'Field workers who meet borrowers every week, and who are the first to hear when recovery agents start calling.',
  },
  {
    icon: Store,
    title: 'Shopkeepers, family',
    body: 'Anyone with a smartphone who sits next to a borrower. No training: take a photo, play the voice.',
  },
]

const TOOLS = [
  { icon: Headphones, title: 'A voice, not a form', body: 'What he gets, what he repays and how much extra, in one sentence he can replay.' },
  { icon: Languages, title: 'Three languages', body: 'Hindi, Bengali and Marathi replies today. Adding a language is one sentence template and one voice.' },
  { icon: Landmark, title: 'The right door', body: 'For each lender, the complaint route that fits: grievance officer and RBI Ombudsman, or the Sachet portal and the cyber crime helpline.' },
  { icon: FileText, title: 'Evidence that holds', body: 'Threats become a dated English PDF with the RBI rules they break, a tamper-evident record and a complaint letter ready to sign.' },
]

const PILOT: TimelineItem[] = [
  { when: 'Before', title: 'One partner, twenty borrowers', body: 'One NGO or bank-mitra network. One native speaker per language checks every spoken sentence.' },
  { when: 'Weeks 1 to 3', title: 'Helpers check every offer', body: 'Each loan offer a borrower brings is photographed first. Threats from recovery agents are forwarded and logged.' },
  { when: 'Week 4', title: 'Count what changed', body: 'Offers checked, offers refused after hearing the cost, complaints filed with the evidence PDF.' },
  { when: 'After', title: 'Decide on the commission', body: 'Only then: does paying the helper per check hold up? Honest feedback from the helpers decides, not us.' },
]

export default function Partners() {
  return (
    <>
      <PageHero label="For NGOs and bank mitras" title="Built for the helper" accent="beside Raju.">
        Scroll: who that helper is, what they get, and the pilot we want to run.
      </PageHero>

      <section className="border-t border-border px-[3vw] py-28">
        <ScrollText
          className="max-w-[24ch] text-[clamp(2.2rem,5.6vw,6rem)] leading-[1.02] font-semibold tracking-[-0.04em]"
          text="Raju will not find this by himself. Someone he trusts shows it to him once."
        />
      </section>

      <section>
        <p className="flex items-center gap-3 px-[3vw] pb-8 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          <span className="font-mono text-primary">01</span>
          <span className="h-px w-8 bg-foreground/40" aria-hidden />
          That someone
        </p>
        <HoverRows rows={HELPERS} />
      </section>

      <Section n="02" label="What a helper gets" tinted>
        <div className="grid gap-x-12 border-t border-border lg:grid-cols-2">
          {TOOLS.map((t, i) => (
            <Reveal key={t.title} delay={(i % 2) * 0.1}>
              <div className="group flex gap-6 border-b border-border py-8">
                <t.icon className="mt-1 size-6 shrink-0 text-primary transition-transform duration-500 group-hover:-translate-y-1" aria-hidden />
                <div>
                  <h3 className="text-xl font-semibold tracking-tight">{t.title}</h3>
                  <p className="mt-2 leading-relaxed text-muted-foreground">{t.body}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section n="03" label="A proposal, not a product">
        <div className="grid items-start gap-16 lg:grid-cols-12">
          <div className="lg:sticky lg:top-28 lg:col-span-5">
            <Reveal>
              <p className="mb-6 inline-block border border-primary px-3 py-1 text-xs font-semibold tracking-[0.2em] text-primary uppercase">
                Proposed pilot model · not built yet
              </p>
              <h2 className="text-[clamp(2rem,4vw,3.5rem)] leading-[1] font-semibold tracking-[-0.03em]">
                Pay the helper, never the borrower’s pocket.
              </h2>
              <p className="mt-6 leading-relaxed text-muted-foreground">
                Raju pays nothing. Our idea is that a partner organisation funds a small commission to the bank mitra
                for each offer checked, the way correspondents are already paid per transaction. It is an assumption
                today, not a finding. A four-week pilot is how we would find out.
              </p>
            </Reveal>
          </div>
          <div className="lg:col-span-7">
            <ScrollTimeline items={PILOT} />
          </div>
        </div>
      </Section>

      <section className="border-t border-border bg-card">
        <div className="px-[3vw] py-28">
          <Reveal>
            <p className="text-[clamp(3rem,9vw,9rem)] leading-[0.9] font-semibold tracking-[-0.05em]">
              Run it with <span className="text-primary">your people.</span>
            </p>
          </Reveal>
          <div className="mt-12 flex flex-wrap items-center gap-4">
            <Magnetic>
              <Link to="/check" className={buttonVariants({ size: 'lg', className: 'h-16 px-10 text-lg' })}>
                Try the helper view
                <ArrowRight className="size-5" aria-hidden />
              </Link>
            </Magnetic>
            <a
              href="https://github.com/Guru2907/karzsamjho"
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ variant: 'outline', size: 'lg', className: 'h-16 px-8 text-lg' })}
            >
              Read the code
              <ArrowUpRight className="size-5" aria-hidden />
            </a>
          </div>
          <p className="mt-8 max-w-xl text-sm text-muted-foreground">
            Team Y2K Devs, COLOSSUS 3.0. Everything is open in the repository, including the tests and what we have not
            built.
          </p>
        </div>
      </section>
    </>
  )
}
