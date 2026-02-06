import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const startTime = Date.now()
    
    // Test server health
    const healthCheck = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.version,
      environment: process.env.NODE_ENV || 'development'
    }

    // Simulate some work
    await new Promise(resolve => setTimeout(resolve, 10))

    const responseTime = Date.now() - startTime

    return NextResponse.json({
      ...healthCheck,
      responseTime: `${responseTime}ms`,
      endpoints: {
        status: '/api/status',
        health: '/api/health'
      }
    })
    
  } catch (error) {
    console.error('Health check failed:', error)
    
    return NextResponse.json(
      { 
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    )
  }
}
