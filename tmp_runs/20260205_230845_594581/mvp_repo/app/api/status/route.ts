import { NextResponse } from 'next/server';

export function GET(request: Request) {
  try {
    const apiKey = process.env.API_KEY;
    const providedKey = request.headers.get('x-api-key');
    if (apiKey && providedKey !== apiKey) {
      return NextResponse.json(
        { status: 'unauthorized', timestamp: new Date().toISOString() },
        { status: 401 }
      );
    }
    return NextResponse.json({
      status: 'prototype built',
      stack: 'Next.js + Tailwind + SQLite',
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
