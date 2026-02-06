'use client';

import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost';
}

const baseStyles =
  'inline-flex items-center justify-center rounded-full border border-transparent px-6 py-2 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';

const variantStyles = {
  primary: 'bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500 text-white shadow-lg',
  ghost: 'bg-white/10 text-white hover:bg-white/20',
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
