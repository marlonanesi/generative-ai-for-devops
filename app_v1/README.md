# App v1 - FastAPI + Streamlit (CRUD de Items)

Aplicação didática com backend FastAPI (SQLAlchemy 2.0 + Postgres) e frontend Streamlit consumindo a API por HTTP.

Portas padrão:
- Backend: 8000
- Frontend: 8501
- Postgres: 5432
- Prometheus: 9090
- Grafana: 3000
- OpenSearch: 9200
- OpenSearch Dashboards: 5601

## Rodando com Docker Compose

Arquivos adicionados:
- `backend/Dockerfile`: imagem do backend (FastAPI + Uvicorn)
- `frontend/Dockerfile`: imagem do frontend (Streamlit)
- `docker-compose.yml`: orquestra backend, frontend e Postgres
- `prometheus/prometheus.yml`: configuração do Prometheus para scrape do backend
- `.dockerignore`: ignora artefatos locais ao buildar

Compose cria um volume nomeado `pgdata` para o banco e usa bind mounts (`./:/app`) para hot-reload em desenvolvimento.

Windows PowerShell:

```powershell
docker compose build
docker compose up -d
```

Acesse:
- UI: http://localhost:8501
- API: http://localhost:8000
- Prometheus: http://localhost:9090 (targets e consultas)
  - Postgres Exporter: http://localhost:9187/metrics (opcional)
- Grafana: http://localhost:3000 (admin/admin)
- OpenSearch (API): http://localhost:9200
- OpenSearch Dashboards: http://localhost:5601

Logs:
```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

Parar:
```powershell
docker compose down
```

## Variáveis de ambiente

- Backend lê `DATABASE_URL` (Compose).
- Frontend usa `API_HOST` e `API_PORT`.
- Backend expõe métricas em `/metrics` (Prometheus format) via middleware.

## Observabilidade (Grafana)
- Datasource Prometheus provisionado (`http://prometheus:9090`).
- Dashboards em `grafana/provisioning/dashboards/json/`.

## Logs estruturados + OpenSearch
Campos principais de log JSON: `timestamp`, `level`, `logger`, `message`, `request_id`, `method`, `path`, `status_code`, `duration_ms`, `client_ip`, `user_agent`.
Envio para índice `logs-app-v1` se `OPENSEARCH_ENABLED=true`.

## CORS
Backend permite `http://localhost:8501`.

## Observações
- Criação de tabelas automática (didático). Em produção: Alembic.
- Dockerfiles usam `python:3.11-slim` e usuário não-root.

## Observabilidade (Prometheus)
Consultas exemplo:
- RPS: `sum(rate(http_requests_total[1m]))`
- Latência média: `rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])`
- Em progresso: `sum(http_requests_in_progress)`
- Exceções: `sum(rate(http_exceptions_total[1m])) by (exception_type)`
- DB: `pg_up`, `pg_stat_database_tup_inserted`, `pg_database_size_bytes{datname="appdb"}`

## Entidade e Endpoints (resumo)
- Item: `id` (UUID), `title`, `description?`, `status` (`pending|in_progress|done`), `created_at`, `updated_at`.
- Endpoints: `GET /items`, `GET /items/{id}`, `POST /items` (201), `PUT /items/{id}`, `DELETE /items/{id}` (204).

## Testes de Carga com k6
Esta aplicação inclui dois scripts de teste de carga usando k6, integrados ao Docker Compose via profile `k6`.

### Objetivos
1. Validar disponibilidade e latência básica (`test_basico.js`).
2. Exercitar o ciclo CRUD completo (`test_crud.js`).
3. Exportar métricas para Prometheus (remote write) e visualizar no Grafana.

### Serviços necessários
`db`, `backend`, `prometheus` (Grafana opcional para visualização). Compose resolve dependências.

### Como executar
```powershell
# Subir stack (se necessário)
docker compose up -d

# Teste básico
docker compose --profile k6 run --rm k6

# Teste CRUD
docker compose --profile k6 run --rm k6 run /scripts/test_crud.js
```

### Scripts
1. `k6/test_basico.js`
   - GET /items
   - Stages: 10s→5 VUs, 30s estável, 10s descendo
   - Thresholds: p95 < 500ms, erros < 1%
2. `k6/test_crud.js`
   - Fluxo: create → get → update → delete + list
   - Cenários:
     - smoke (ramping-vus 0→3→0)
     - crud_load (constant-vus: 5 VUs / 30s)
   - Thresholds: erros <2%, p95 <700ms
   - Trend custom: `custom_create_duration`

### Conceitos
| Conceito | Explicação |
|----------|-----------|
| VU | Usuário virtual concorrente |
| Stage | Período com alvo de VUs |
| Scenario | Padrão de carga isolado |
| Threshold | Regra de aprovação/falha |
| Iteration | Uma execução da função de teste |
| Trend | Métrica custom com distribuição |

### Variáveis de ambiente (serviço k6)
| Variável | Função | Default |
|----------|--------|---------|
| API_BASE | Base da API | http://backend:8000 |
| K6_OUT | Output/export | experimental-prometheus-rw |
| K6_PROMETHEUS_RW_SERVER_URL | Remote write endpoint | http://prometheus:9090/api/v1/write |
| K6_PROMETHEUS_RW_TREND_STATS | Estatísticas de Trend | p(95),p(99),avg,med,min,max |

Prometheus inicia com `--web.enable-remote-write-receiver` para expor `/api/v1/write`.

### Métricas k6 no Prometheus
| Métrica | Descrição |
|---------|-----------|
| http_reqs | Total de requisições |
| http_req_duration | Latência (s) |
| http_req_failed | Proporção de falhas |
| vus / vus_max | VUs atuais / máximo |
| iterations | Iterações completas |
| data_sent / data_received | Tráfego |
| checks | Resultados de check() |
| custom_create_duration | Tempo de criação (Trend) |

### Queries exemplo
| Objetivo | Query |
|----------|-------|
| RPS | rate(http_reqs[1m]) |
| Latência p95 | histogram_quantile(0.95, sum(rate(http_req_duration_bucket[5m])) by (le)) |
| Erro (%) | rate(http_req_failed[5m]) |
| VUs | avg(vus) |
| Iterações/s | rate(iterations[1m]) |

### Customizações rápidas
1. Aumentar carga:
```javascript
export const options = { stages: [
  { duration: '30s', target: 20 },
  { duration: '2m', target: 20 },
  { duration: '30s', target: 0 },
] }
```
2. Header de auth:
```javascript
const params = { headers: { Authorization: `Bearer ${__ENV.TOKEN}` } }
```
Execução: `TOKEN=seu_token docker compose --profile k6 run --rm k6`
3. Exportar resumo JSON:
```powershell
docker compose --profile k6 run --rm k6 run --summary-export=/scripts/saida.json /scripts/test_crud.js
```

### Exemplo novo script (`k6/stress_ramp.js`)
```javascript
import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 30 },
    { duration: '3m', target: 30 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01']
  }
};

const API = __ENV.API_BASE || 'http://backend:8000';
export default function () {
  http.get(`${API}/items?limit=5`);
  sleep(0.5);
}
```
Execução:
```powershell
docker compose --profile k6 run --rm k6 run /scripts/stress_ramp.js
```

### Interpretação rápida
- checks_total / checks_failed: validações lógicas
- http_req_duration: comparar média vs p95
- http_req_failed: se > threshold => exit code ≠ 0
- iteration_duration: inclui sleeps + requisições

### Boas práticas
- Escale gradualmente.
- Use tags por operação.
- Thresholds = SLOs automatizados.
- Diferencie smoke, load, stress, spike.
- Correlacione com métricas de backend e DB.