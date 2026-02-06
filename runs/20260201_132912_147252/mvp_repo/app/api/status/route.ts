import { NextResponse } from 'next/server';

export function GET() {
  try {
    return NextResponse.json({
      status: 'ok',
      stack: 'Next.js + Tailwind + SQLite',
      uptime: Math.round(process.uptime()),
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('status route failed', error);
    return NextResponse.json(
      { status: 'error', stack: 'Next.js + Tailwind + SQLite', timestamp: new Date().toISOString() },
      { status: 500 }
    );
  }
}
