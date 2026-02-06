import { NextRequest, NextResponse } from 'next/server';

// Rate limiting simple
const requestCounts = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 60; // requests per minute
const WINDOW_MS = 60000; // 1 minute

function getClientIP(request: NextRequest): string {
  return request.ip || 
         request.headers.get('x-forwarded-for')?.split(',')[0] || 
         'unknown';
}

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const record = requestCounts.get(ip);
  
  if (!record || now > record.resetTime) {
    requestCounts.set(ip, { count: 1, resetTime: now + WINDOW_MS });
    return true;
  }
  
  if (record.count >= RATE_LIMIT) {
    return false;
  }
  
  record.count++;
  return true;
}

export async function GET(request: NextRequest) {
  try {
    const ip = getClientIP(request);
    
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { error: 'Too many requests' },
        { status: 429 }
      );
    }

    // Simulate potential database or service errors
    if (Math.random() < 0.05) { // 5% chance of error for testing
      throw new Error('Service temporarily unavailable');
    }

    return NextResponse.json({
      status: 'prototype built',
      stack: 'Next.js + Tailwind + SQLite',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    });
    
  } catch (error) {
    console.error('API Error:', error);
    
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
