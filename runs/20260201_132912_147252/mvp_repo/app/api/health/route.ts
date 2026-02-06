import { NextResponse } from 'next/server';

export function GET() {
  try {
    return NextResponse.json({
      status: 'ok',
      uptime: Math.round(process.uptime()),
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('health route failed', error);
    return NextResponse.json({ status: 'error', timestamp: new Date().toISOString() }, { status: 500 });
  }
}
