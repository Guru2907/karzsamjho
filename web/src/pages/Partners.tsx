import { ArrowRight, ArrowUpRight, FileText, Headphones, Landmark, Languages, Store, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Columns, PageHero, Section } from '@/site/Page'
import { Magnetic, Reveal } from '@/site/motion'

// Public website: for NGOs, bank mitras and other helpers (task H4, D47).
// The commission model is a proposal for a pilot. Nothing on this page claims it exists today.

const HELPERS = [
  {
    icon: Landmark,
    title: 'Bank mitras',
    body: 'The banking correspondent Raju already trusts. One more service at the same counter: “show me the offer before you sign.”',
  },
  {
    icon: Users,
    title: 'NGOs and self-help groups',
    body: 'Field workers who meet borrowers every week, and who are the first to hear when recovery agents start calling.',
  },
  {
    icon: Store,
    title: 'Shopkeepers and family',
    body: 'Anyone with a smartphone who sits next to a borrower. No training: take a photo, play the voice.',
  },
]

const TOOLS = [
  { icon: Headphones, title: 'A voice, not a form', body: 'What he gets, what he repays and how much extra, in one sentence he can replay.' },
  { icon: Languages, title: 'Three languages', body: 'Hindi, Bengali and Marathi replies today. Adding a language is one sentence template and one voice.' },
  { icon: Landmark, title: 'The right door', body: 'For each lender, the complaint route that fits: grievance officer and RBI Ombudsman, or the Sachet portal and the cyber crime helpline.' },
  { icon: FileText, title: 'Evidence that holds', body: 'Threats become a dated English PDF with the RBI rules they break, a tamper-evident record and a complaint letter ready to sign.' },
]

const PILOT = [
  ['Who', 'One NGO or bank-mitra network, 20 borrowers'],
  ['How long', 'Four weeks'],
  ['What we measure', 'Offers checked, offers refused after hearing the cost, complaints filed with the PDF'],
  ['What we need', 'A native speaker per language, and honest feedback from the helpers'],
]

export default function Partners() {
  return (
    <>
      <PageHero label="For NGOs and bank mitras" title="Built for the helper" accent="beside Raju.">
        Raju will not find this by himself. Someone he trusts shows it to him once. That someone is a bank mitra, a
        field worker, a shopkeeper. This page is for them, and for the organisations behind them.
      </PageHero>

      <Section n="01" label="Who it is for">
        <Columns>
          {HELPERS.map((h, i) => (
            <Reveal key={h.title} delay={i * 0.12}>
              <h.icon className="size-7 text-primary" aria-hidden />
              <h2 className="mt-8 text-2xl font-semibold tracking-tight">{h.title}</h2>
              <p className="mt-3 leading-relaxed text-muted-foreground">{h.body}</p>
            </Reveal>
          ))}
        </Columns>
      </Section>

      <Section n="02" label="What a helper gets" tinted>
        <div className="grid gap-x-12 border-t border-border lg:grid-cols-2">
          {TOOLS.map((t, i) => (
            <Reveal key={t.title} delay={(i % 2) * 0.1}>
              <div className="flex gap-6 border-b border-border py-8">
                <t.icon className="mt-1 size-6 shrink-0 text-primary" aria-hidden />
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
        <div className="grid items-start gap-12 lg:grid-cols-12">
          <Reveal className="lg:col-span-6">
            <p className="mb-6 inline-block border border-primary px-3 py-1 text-xs font-semibold tracking-[0.2em] text-primary uppercase">
              Proposed pilot model · not built yet
            </p>
            <h2 className="text-[clamp(2rem,4vw,3.5rem)] leading-[1] font-semibold tracking-[-0.03em]">
              Pay the helper, never the borrower’s pocket.
            </h2>
            <p className="mt-6 leading-relaxed text-muted-foreground">
              Raju pays nothing. Our idea is that a partner organisation funds a small commission to the bank mitra for
              each offer checked, the way correspondents are already paid per transaction. Whether that works is
              exactly what a pilot should find out. It is an assumption today, not a finding.
            </p>
          </Reveal>
          <Reveal className="lg:col-span-6" delay={0.15}>
            <dl className="border-t border-border">
              {PILOT.map(([k, v]) => (
                <div key={k} className="grid grid-cols-3 gap-6 border-b border-border py-5">
                  <dt className="text-xs tracking-[0.15em] text-muted-foreground uppercase">{k}</dt>
                  <dd className="col-span-2 leading-relaxed">{v}</dd>
                </div>
              ))}
            </dl>
          </Reveal>
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
