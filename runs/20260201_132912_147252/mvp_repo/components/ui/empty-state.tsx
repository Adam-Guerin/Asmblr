import { ReactNode } from 'react';

export function EmptyState({
  title,
  description,
  hint,
  action,
}: {
  title: string;
  description: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <div className="glass rounded-3xl p-6 text-center space-y-3">
      <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Empty state</p>
      <h3 className="text-xl font-semibold text-white">{title}</h3>
      <p className="text-slate-300">{description}</p>
      {hint ? <p className="text-sm text-slate-400">{hint}</p> : null}
      {action ? <div className="flex justify-center">{action}</div> : null}
    </div>
  );
}
