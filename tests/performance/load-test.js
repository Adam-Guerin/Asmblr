import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 50 }, // Ramp up to 50 users
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.1'],    // Error rate under 10%
    errors: ['rate<0.1'],             // Custom error rate under 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test API endpoints
  const endpoints = [
    { path: '/health', method: 'GET', expected: 200 },
    { path: '/api/status', method: 'GET', expected: 200 },
    { path: '/api/v1/runs', method: 'GET', expected: 200 },
    { path: '/metrics', method: 'GET', expected: 200 },
  ];

  endpoints.forEach(endpoint => {
    const response = http.get(`${BASE_URL}${endpoint.path}`, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'k6-performance-test',
      },
    });

    const success = check(response, {
      [`${endpoint.method} ${endpoint.path} status is ${endpoint.expected}`]: (r) => r.status === endpoint.expected,
      [`${endpoint.method} ${endpoint.path} response time < 500ms`]: (r) => r.timings.duration < 500,
      [`${endpoint.method} ${endpoint.path} response body not empty`]: (r) => r.body.length > 0,
    });

    errorRate.add(!success);

    // Add small delay between requests
    sleep(0.1);
  });

  // Test POST endpoint (create run)
  const payload = JSON.stringify({
    topic: "Performance test run",
    n_ideas: 3,
    fast: true,
  });

  const postResponse = http.post(`${BASE_URL}/api/v1/runs`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-performance-test',
    },
  });

  const postSuccess = check(postResponse, {
    'POST /api/v1/runs status is 200': (r) => r.status === 200,
    'POST /api/v1/runs response time < 2000ms': (r) => r.timings.duration < 2000,
    'POST /api/v1/runs has run_id': (r) => JSON.parse(r.body).run_id !== undefined,
  });

  errorRate.add(!postSuccess);

  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
