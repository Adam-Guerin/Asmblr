'use client';

import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost';
}

const baseStyles =
  'inline-flex items-center justify-center rounded-full border border-transparent px-6 py-2 text-sm font-semibold transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400';

const variantStyles = {
  primary:
    'bg-gradient-to-r from-cyan-400 via-sky-500 to-indigo-500 text-slate-950 shadow-lg shadow-cyan-500/30 hover:scale-[1.02]',
  ghost: 'bg-white/10 text-white hover:bg-white/20 border border-white/10',
};

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button className={`${baseStyles} ${variantStyles[variant]} ${className}`} {...props} />
  );
}
