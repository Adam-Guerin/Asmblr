import { ReactNode } from 'react';

export function Card({
  title,
  children,
  className = '',
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <article className={`glass rounded-3xl p-6 space-y-3 card-hover ${className}`}>
      <p className="text-xs uppercase tracking-[0.4em] text-slate-400">{title}</p>
      <div className="text-lg text-slate-100">{children}</div>
    </article>
  );
}
