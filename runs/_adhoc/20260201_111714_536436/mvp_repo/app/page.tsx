'use client';

import { Button } from '@/components/ui/button';

const stackCards = [
  "Prototype ready for fast validation",
  "Frontend: Next.js + Tailwind CSS + shadcn-inspired UI + TypeScript",
  "Backend: Next.js API routes + Prisma + SQLite"
];

const metrics = [
  { label: 'Flows', value: '3 ready' },
  { label: 'API', value: 'status + data' },
  { label: 'Focus', value: 'Prototype built' },
];

export default function Page() {
  return (
    <main className="max-w-5xl mx-auto p-6 space-y-10">
      <section className="space-y-4">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Audit-ready MVP</p>
        <h1 className="text-4xl font-semibold text-white">Prototype launched</h1>
        <p className="text-lg text-slate-300">
          Audit-ready MVP
        </p>
        <div className="flex gap-3 flex-wrap">
          <Button>Launch prototype</Button>
          <Button variant="ghost">View docs</Button>
        </div>
      </section>
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {metrics.map((metric) => (
            <article
              key={metric.label}
              className="rounded-2xl border border-slate-800 bg-white/5 p-4 space-y-2"
            >
              <p className="text-sm uppercase tracking-[0.4em] text-slate-400">{metric.label}</p>
              <p className="text-2xl font-semibold text-white">{metric.value}</p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2 className="text-2xl font-semibold text-white">Stack highlights</h2>
        <ul className="mt-4 list-disc list-inside space-y-2 text-slate-200">
          {stackCards.map((card) => (
            <li key={card}>{card}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
