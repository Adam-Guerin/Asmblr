import { NextResponse } from 'next/server';

export function GET() {
  return NextResponse.json({
    status: 'prototype built',
    stack: 'Next.js + Tailwind + SQLite',
  });
}
