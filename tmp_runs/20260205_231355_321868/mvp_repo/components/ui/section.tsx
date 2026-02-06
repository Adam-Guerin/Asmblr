import * as React from 'react';
import { cn } from '@/lib/utils';

export function Section({
  eyebrow,
  title,
  description,
  className,
  children,
}: {
  eyebrow?: string;
  title?: string;
  description?: string;
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className={cn('mx-auto max-w-6xl px-6 py-16', className)}>
      {title ? (
        <div className="flex flex-col gap-3">
          {eyebrow ? (
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="text-3xl font-semibold text-slate-900">{title}</h2>
          {description ? <p className="text-base text-slate-600">{description}</p> : null}
        </div>
      ) : null}
      {children ? <div className={title ? 'mt-10' : ''}>{children}</div> : null}
    </section>
  );
}
