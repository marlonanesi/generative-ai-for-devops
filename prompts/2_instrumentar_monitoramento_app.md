Você é um(a) DevOps sênior. Instrumente a aplicação Python localizada em `app_v1` com métricas Prometheus, exponha-as em `/metrics` no backend FastAPI e adicione um serviço Prometheus no `docker-compose` existente para realizar o scrape.

Contexto do projeto:
- Raiz: `app_v1/`
- Backend: FastAPI em `app_v1/backend/main.py`, usa SQLAlchemy 2.0 + Postgres (psycopg), cria tabelas no startup, lê `DATABASE_URL` via `backend/config.py`.
- Frontend: Streamlit em `app_v1/frontend/app.py`.
- Dependências atuais: `app_v1/requirements.txt` (FastAPI, Uvicorn, SQLAlchemy, psycopg[binary], python-dotenv, streamlit, httpx).
- Compose já possui serviços: `db` (Postgres 16), `backend`, `frontend`.
- Se baseie a implementação somente na pasta indicada

Objetivo:
- Instrumentar métricas de HTTP (contagem de requisições e latência) com a biblioteca oficial `prometheus-client`.
- Expor endpoint `/metrics` no backend em formato do Prometheus (text/plain; version 0.0.4).
- Adicionar serviço `prometheus` ao `docker-compose` para fazer scrape do `backend:8000/metrics` e disponibilizar UI em `http://localhost:9090`.

Boas práticas e observações didáticas:
- Utilize `prometheus-client` para criar Counter e Histogram. Evite alta cardinalidade em labels (por exemplo, paths dinâmicos). Para simplicidade do curso, pode usar `request.url.path`, mas registre a observação no código.
- Monte `/metrics` via `prometheus_client.make_asgi_app()` (forma simples e compatível com FastAPI/Starlette).
- Use middleware HTTP para medir tempo de resposta e contabilizar status por método e caminho.
- Não altere comportamento funcional das rotas; apenas adicione a instrumentação.
- Mantenha o app rodando como não-root nos containers (já atendido nos Dockerfiles existentes).

Tarefas (entregar arquivos prontos, caminhos relativos a `app_v1`):
1) Atualizar dependências
	 - Em `requirements.txt`, adicionar a linha: `prometheus-client`

2) Criar módulo de métricas no backend
	 - Criar arquivo `backend/metrics.py` com:
		 - Imports: `time`, `from fastapi import FastAPI, Request`, `from prometheus_client import Counter, Histogram, Gauge, make_asgi_app`.
		 - Definir métricas globais:
			 - `http_requests_total` (Counter) com labels `method`, `path`, `status_code`.
			 - `http_request_duration_seconds` (Histogram) com labels `method`, `path`.
			 - `http_requests_in_progress` (Gauge) com labels `method`, `path` — indica requisições em andamento (útil para observar concorrência sob carga).
			 - `http_exceptions_total` (Counter) com labels `method`, `path`, `exception_type` — total de exceções por rota/tipo.
		 - Função `setup_metrics(app: FastAPI) -> None` que:
			 - Registra `@app.middleware("http")` para: (a) incrementar `in_progress` no início e decrementar ao final; (b) medir duração (Histogram) e (c) contabilizar `requests_total` por status; (d) em caso de exceção, incrementar `http_exceptions_total` com o nome da classe da exceção e marcar status 500.
			 - Monta o app do Prometheus: `app.mount("/metrics", make_asgi_app())`.
		 - Comentários no código explicando risco de cardinalidade alta em `path` e como, em produção, mapear para rotas normalizadas (ex.: `/items/{id}` ao invés de `/items/123`).

3) Integrar métricas ao app FastAPI
	 - Em `backend/main.py`:
		 - Adicionar `from .metrics import setup_metrics` após os imports existentes.
		 - Logo após a criação da instância `app = FastAPI(...)`, chamar `setup_metrics(app)`.
		 - Não alterar as rotas existentes. Manter CORS como está.

4) Adicionar serviço Prometheus no Compose
	 - Em `docker-compose.yml`, adicionar serviço `prometheus`:
		 - `image: prom/prometheus:latest`
		 - `volumes`: montar arquivo de configuração `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
		 - `ports`: `"9090:9090"`
		 - `depends_on`: `backend` (condition: `service_started`)
	 - Em `volumes:` pode-se manter `pgdata:` como está (Prometheus pode rodar sem volume de dados para fins didáticos).

5) Adicionar configuração do Prometheus
	 - Criar arquivo `prometheus/prometheus.yml` com conteúdo mínimo:
		 ```yaml
		 global:
			 scrape_interval: 5s

		 scrape_configs:
			 - job_name: 'backend'
				 metrics_path: /metrics
				 static_configs:
					 - targets: ['backend:8000']

			 - job_name: 'prometheus'
				 static_configs:
					 - targets: ['localhost:9090']
		 ```

6) Validação esperada (Windows PowerShell)
	 - Rebuild para instalar a nova dependência e subir o stack:
		 - `docker compose build`
		 - `docker compose up -d`
	 - Verificar endpoint de métricas do backend:
		 - Acesse `http://localhost:8000/metrics` e confira saída em texto com métricas (incluindo `http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`, `http_exceptions_total`).
	 - Gerar tráfego na API (ex.: `GET http://localhost:8000/items`) e verificar:
		 - RPS: `sum(rate(http_requests_total[1m]))`
		 - Latência média: `rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])`
		 - Em progresso (instantâneo): `sum(http_requests_in_progress)`
		 - Exceções por tipo: `sum(rate(http_exceptions_total[1m])) by (exception_type)`
	 - Abrir Prometheus UI:
		 - `http://localhost:9090/targets` deve mostrar o alvo `backend` como `UP`.
		 - Em `http://localhost:9090/graph`, consultar `http_requests_total` e `rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])` para latência média.

7) Atualize o README.md conforme atualizacoes e boas praticas

Critérios de aceite
- Dependência `prometheus-client` adicionada em `requirements.txt`.
- Novo arquivo `backend/metrics.py` criado com Counter, Histogram, Gauge (in-progress) e Counter de exceções, e middleware conforme descrito.
- `backend/main.py` atualizado para chamar `setup_metrics(app)` e montar `/metrics`.
- `docker-compose.yml` estendido com serviço `prometheus` e bind do arquivo de configuração.
- Arquivo `prometheus/prometheus.yml` presente e válido.
- Após `docker compose up -d`, `/metrics` responde e Prometheus lista o `backend` como `UP`.

Extras
- Adicionar `histogram_buckets` customizados para latência (p.ex.: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5]).
- Expor métricas de banco (via exporters específicos) em exercícios avançados.
- Adicionar healthcheck no `backend` no compose (ex.: `curl -f http://localhost:8000/items || exit 1`).

Observações de segurança e performance
- Não exponha `/metrics` publicamente em produção; proteja com autenticação/autorização ou restrinja por rede.
- Cuidado com cardinalidade de labels (especialmente `path` e IDs dinâmicos). Em produção, normalize caminhos ou use middlewares que mapeiam para nomes de rotas.
- Evite `--reload` em produção; aqui é útil para hot-reload no ambiente de desenvolvimento do curso.

