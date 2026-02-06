import { ReactNode } from 'react';

export function Microcopy({
  tone = 'subtle',
  children,
}: {
  tone?: 'subtle' | 'info' | 'warning';
  children: ReactNode;
}) {
  const toneStyles = {
    subtle: 'text-slate-400',
    info: 'text-cyan-200',
    warning: 'text-amber-200',
  };

  return <p className={`text-sm ${toneStyles[tone]}`}>{children}</p>;
}
