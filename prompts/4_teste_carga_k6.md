Você é um(a) DevOps sênior. Adicione testes de carga com k6 à stack de `app_v1`, integrando as métricas do k6 ao Prometheus (e Grafana) já existentes, usando Prometheus Remote Write (receiver) no servidor Prometheus.

Contexto atual
- Stack `app_v1` no docker-compose com: `db` (Postgres), `backend` (FastAPI com `/metrics`), `frontend` (Streamlit), `prometheus` (scrape backend e postgres-exporter), `postgres-exporter`, `grafana`.
- Prometheus acessível em `http://localhost:9090` e Grafana em `http://localhost:3000`.
- Se baseie a implementação somente na pasta indicada

Objetivo
- Incluir k6 como serviço (ou perfil) no compose, com script de carga voltado ao backend.
- Habilitar o Prometheus como “remote write receiver” para receber séries do k6 em `/api/v1/write`.
- Visualizar métricas do k6 no Prometheus/Grafana (`k6_*`).

Boas práticas e observações
- Para laboratório, usaremos o output nativo “experimental-prometheus-rw” do k6, enviando diretamente ao Prometheus (com feature `remote-write-receiver` habilitada).
- O serviço k6 pode rodar sob um `profile` para não executar sempre no `up -d`.
- Scripts k6 ficam versionados em `app_v1/k6/` e são montados no container.

Tarefas (caminhos relativos a `app_v1`)
1) Criar pasta e script k6
	 - Pasta: `k6/`
	 - Arquivo: `k6/test_basico.js` com um smoke + pequena rampa de carga:
		 ```js
		 import http from 'k6/http';
		 import { check, sleep } from 'k6';

		 export const options = {
			 stages: [
				 { duration: '10s', target: 5 },   // rampa até 5 VUs
				 { duration: '30s', target: 5 },   // sustenta
				 { duration: '10s', target: 0 },   // rampa para zero
			 ],
			 thresholds: {
				 http_req_duration: ['p(95)<500'], // 95% < 500ms
				 http_req_failed: ['rate<0.01'],   // <1% erros
			 },
		 };

		 const API = __ENV.API_BASE || 'http://backend:8000';

		 export default function () {
			 // GET lista
			 const res = http.get(`${API}/items?limit=10`);
			 check(res, {
				 'status is 200': (r) => r.status === 200,
			 });
			 // Pequena pausa entre iterações
			 sleep(1);
		 }
		 ```
	 - Observação: o script usa `API_BASE` (com default `http://backend:8000` dentro da rede do compose).

2) Habilitar receiver no Prometheus
	 - Em `docker-compose.yml`, no serviço `prometheus`, adicione o comando/args para habilitar o receiver:
		 ```yaml
		 prometheus:
			 image: prom/prometheus:latest
			 command:
				 - "--config.file=/etc/prometheus/prometheus.yml"
				 - "--enable-feature=remote-write-receiver"
			 # ...demais campos (volumes, ports, depends_on) permanecem
		 ```
	 - Isso permite que o k6 envie séries diretamente para `http://prometheus:9090/api/v1/write`.

3) Adicionar serviço k6 ao compose
	 - Em `docker-compose.yml`, acrescente o serviço com profile `k6` (opcional) e output Prometheus RW:
		 ```yaml
		 k6:
			 image: grafana/k6:latest
			 profiles: ["k6"]
			 depends_on:
				 backend:
					 condition: service_started
				 prometheus:
					 condition: service_started
			 environment:
				 - K6_OUT=experimental-prometheus-rw
				 - K6_PROMETHEUS_RW_SERVER_URL=http://prometheus:9090/api/v1/write
				 - K6_PROMETHEUS_RW_TREND_STATS=p(95),p(99),avg,med,min,max
				 - API_BASE=http://backend:8000
			 volumes:
				 - ./k6:/scripts
			 command: ["run", "/scripts/test_basico.js"]
		 ```
	 - Observação: o serviço executa e finaliza após o teste. Com `profiles`, só sobe quando explicitamente solicitado.

4) Subir/rodar os testes
	 - Atualize o stack (para aplicar o comando do Prometheus):
		 ```powershell
		 cd c:\cursos\generative_ai_for_devops\app_v1
		 docker compose up -d prometheus
		 ```
	 - Executar o teste de carga via profile:
		 ```powershell
		 docker compose --profile k6 up --build k6
		 ```
	 - Alternativa (sem profile), usando `compose run` ad-hoc:
		 ```powershell
		 docker compose run --rm \
			 -e K6_OUT=experimental-prometheus-rw \
			 -e K6_PROMETHEUS_RW_SERVER_URL=http://prometheus:9090/api/v1/write \
			 -e K6_PROMETHEUS_RW_TREND_STATS=p(95),p(99),avg,med,min,max \
			 -e API_BASE=http://backend:8000 \
			 -v .\k6:/scripts grafana/k6:latest run /scripts/test_basico.js
		 ```

5) Validação
	 - Prometheus (UI):
		 - Abra `http://localhost:9090/graph` e procure por métricas iniciando com `k6_`.
		 - Exemplos de queries:
			 - `sum(rate(k6_http_reqs[1m]))`
			 - `k6_vus` (virtual users)
			 - `rate(k6_iterations[1m])`
			 - Para latência: navegue por métricas `k6_http_req_duration*` e aplique `rate/avg` ou `histogram_quantile` conforme séries disponíveis.
	 - Grafana:
		 - Use o datasource Prometheus e crie um painel rápido com `sum(rate(k6_http_reqs[1m]))` e outro com `k6_vus`.

Critérios de aceite
- `prometheus` roda com `--enable-feature=remote-write-receiver` e o endpoint `/api/v1/write` responde (internamente na rede do compose).
- Serviço `k6` executa o script e finaliza com status 0.
- Métricas `k6_*` ficam visíveis no Prometheus/Grafana após a execução.

Extras
- Scripts adicionais: criar `k6/test_crud.js` simulando GET/POST/PUT/DELETE nos endpoints para carga de escrita. Baseado nas apis do backend no fastapi.
- Cenários: usar `scenarios` do k6 para testes paralelos (smoke + endurance + spike).
- Alternativa Pushgateway: se não quiser habilitar remote-write no Prometheus, use a extensão `xk6-output-prometheus` com Pushgateway (exige imagem customizada do k6).

Notas de troubleshooting
- Se não aparecerem séries `k6_*`, verifique se o Prometheus está com o receiver habilitado e se o k6 reportou envio de métricas sem erro.
- Para ver logs do Prometheus: `docker compose logs -f prometheus`.
- Para rodar o k6 várias vezes, reexecute o serviço `k6` ou use `compose run`.

