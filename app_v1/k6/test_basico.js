import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 5 }, // rampa até 5 VUs
    { duration: '30s', target: 5 }, // sustenta
    { duration: '10s', target: 0 }, // rampa para zero
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% < 500ms
    http_req_failed: ['rate<0.01'], // <1% erros
  },
};

const API = __ENV.API_BASE || 'http://backend:8000';

export default function () {
  const res = http.get(`${API}/items?limit=10`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
