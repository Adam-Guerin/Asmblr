'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Microcopy } from '@/components/ui/microcopy';
import { Section } from '@/components/ui/section';

const stackCards = [
  'Prototype ready for fast validation',
  'Frontend: Next.js + Tailwind CSS + shadcn-inspired UI + TypeScript',
  'Backend: Next.js API routes + Prisma + SQLite',
];

const metrics = [
  { label: 'Flows', value: '3 ready' },
  { label: 'API', value: 'status + data' },
  { label: 'Focus', value: 'Prototype built' },
];

const signals: string[] = [];

export default function Page() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-12 space-y-12">
      <section className="space-y-6 fade-up">
        <div className="flex flex-wrap items-center gap-3">
          <Badge label="Audit MVP" />
          <Badge label="Production-ready structure" />
          <Badge label="Lifecycle: polish" />
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl md:text-5xl font-semibold text-white">
            Prototype launched with a sharper operating system.
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl">
            A high-signal MVP workspace designed to validate execution flow, capture baseline
            metrics, and move quickly between product cycles.
          </p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <Button>Launch prototype</Button>
          <Button variant="ghost">View docs</Button>
        </div>
        <Microcopy>Last run: pending. Typical warm start &lt; 45s.</Microcopy>
      </section>

      <Section
        title="Snapshot metrics"
        subtitle="Readable at a glance across the core surfaces."
        className="fade-up delay-1"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {metrics.map((metric) => (
            <Card key={metric.label} title={metric.label}>
              <p className="text-2xl font-semibold text-white">{metric.value}</p>
              <Microcopy>Updated after each successful run.</Microcopy>
            </Card>
          ))}
        </div>
      </Section>

      <Section
        title="Signal feed"
        subtitle="Automatic insights appear after the first live run."
        className="fade-up delay-2"
      >
        {signals.length === 0 ? (
          <EmptyState
            title="No signals captured yet."
            description="Run the MVP once to populate operational telemetry and see cycle insights."
            hint="Tip: connect your data source to unlock real-time signal drift."
            action={<Button variant="ghost">Run first capture</Button>}
          />
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {signals.map((signal) => (
              <li key={signal} className="glass rounded-3xl p-6 animate-float">
                {signal}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        title="Stack highlights"
        subtitle="Aligned to speed up iteration and delivery."
        className="fade-up delay-3"
      >
        <ul className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stackCards.map((card) => (
            <li key={card} className="glass rounded-3xl p-6 text-slate-200 card-hover">
              {card}
              <Microcopy tone="subtle">Verified in the last build.</Microcopy>
            </li>
          ))}
        </ul>
      </Section>
    </main>
  );
}
