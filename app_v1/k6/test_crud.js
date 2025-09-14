import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

export const options = {
  scenarios: {
    smoke: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 30 },
        { duration: '90s', target: 50 },
        { duration: '30s', target: 0 },
      ],
      exec: 'listItems'
    },
    crud_load: {
      executor: 'constant-vus',
      vus: 5,
      duration: '30s',
      exec: 'crudFlow'
    }
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<700'],
  }
};

const API = __ENV.API_BASE || 'http://backend:8000';
const createTrend = new Trend('custom_create_duration');

export function listItems() {
  const res = http.get(`${API}/items?limit=20`);
  check(res, { 'list 200': r => r.status === 200 });
  sleep(1);
}

export function crudFlow() {
  // CREATE
  // Backend exige campos: title (obrigatório), description (opcional), status (pending|in_progress|done)
  const payload = JSON.stringify({ title: `item-${Date.now()}`, description: 'k6 created', status: 'pending' });
  const headers = { 'Content-Type': 'application/json' };
  const createRes = http.post(`${API}/items`, payload, { headers });
  check(createRes, { 'create 201': r => r.status === 201 });
  const id = (createRes.json() || {}).id;
  // READ
  if (id) {
    const getRes = http.get(`${API}/items/${id}`);
    check(getRes, { 'get 200': r => r.status === 200 });
    // UPDATE
  const updPayload = JSON.stringify({ description: 'updated by k6', status: 'done' });
    const updRes = http.put(`${API}/items/${id}`, updPayload, { headers });
    check(updRes, { 'update 200': r => r.status === 200 });
    // DELETE
    const delRes = http.del(`${API}/items/${id}`);
    check(delRes, { 'delete 204': r => r.status === 204 });
  }
  sleep(0.5);
}
