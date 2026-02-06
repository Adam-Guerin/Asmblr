import { ReactNode } from 'react';

export function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-2xl font-semibold text-white">{title}</h2>
        {subtitle ? <p className="text-slate-400">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
