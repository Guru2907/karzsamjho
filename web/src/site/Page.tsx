import type { ReactNode } from 'react'
import { Reveal, WordReveal } from './motion'
import { SHELL } from './shell'

// Building blocks shared by the inner pages of the public website (/how, /partners; D47).

export function Eyebrow({ n, children }: { n: string; children: string }) {
  return (
    <p className="mb-8 flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
      <span className="font-mono text-primary">{n}</span>
      <span className="h-px w-8 bg-foreground/40" aria-hidden />
      {children}
    </p>
  )
}

/** The big opening of an inner page: a label, a two-part headline and one paragraph. */
export function PageHero({ label, title, accent, children }: { label: string; title: string; accent: string; children: ReactNode }) {
  return (
    <section className="px-[3vw] pt-36 pb-20">
      <Reveal>
        <p className="mb-[2vw] flex items-center gap-3 text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          <span className="h-px w-8 bg-foreground/40" aria-hidden />
          {label}
        </p>
      </Reveal>
      <WordReveal
        text={title}
        label={`${title} ${accent}`}
        className="text-[clamp(3rem,8.2vw,9rem)] leading-[0.92] font-semibold tracking-[-0.05em]"
      />
      <WordReveal
        as="p"
        text={accent}
        label=""
        delay={0.35}
        className="text-[clamp(3rem,8.2vw,9rem)] leading-[0.92] font-semibold tracking-[-0.05em] text-primary"
      />
      <Reveal delay={0.7}>
        <p className="mt-10 max-w-2xl text-lg leading-relaxed text-muted-foreground lg:text-xl">{children}</p>
      </Reveal>
    </section>
  )
}

/** A numbered section in the centred column with a hairline on top. */
export function Section({ n, label, children, tinted }: { n: string; label: string; children: ReactNode; tinted?: boolean }) {
  return (
    <section className={`border-t border-border ${tinted ? 'bg-card' : ''}`}>
      <div className={`${SHELL} py-24`}>
        <Eyebrow n={n}>{label}</Eyebrow>
        {children}
      </div>
    </section>
  )
}

/** Columns separated by hairlines. Each child is one column. */
export function Columns({ children, cols = 3 }: { children: ReactNode; cols?: 2 | 3 | 4 }) {
  const grid = { 2: 'lg:grid-cols-2', 3: 'lg:grid-cols-3', 4: 'lg:grid-cols-4' }[cols]
  return (
    <div
      className={`grid border-t border-border ${grid} [&>*]:border-b [&>*]:border-border [&>*]:py-10 lg:[&>*]:border-r lg:[&>*]:border-b-0 lg:[&>*]:px-8 lg:[&>*:first-child]:pl-0 lg:[&>*:last-child]:border-r-0`}
    >
      {children}
    </div>
  )
}
