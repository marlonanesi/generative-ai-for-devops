Você é um(a) DevOps sênior. Migre a orquestração atual da aplicação (definida hoje em `app_v1/docker-compose.yml`) para Kubernetes rodando localmente em um cluster **kind** (Kubernetes in Docker)

## Contexto Atual (Compose)
Serviços existentes no `docker-compose.yml`:
- `db` (Postgres 16)
- `backend` (FastAPI + métricas Prometheus + logs estruturados + OpenSearch client)
- `frontend` (Streamlit)
- `prometheus`
- `postgres-exporter`
- `grafana`
- `opensearch`
- `opensearch-dashboards`
- `k6` (apenas para execução de testes de carga sob demanda via profile)

Portas expostas atualmente:
- 8000 (API), 8501 (UI), 5432 (DB), 9090 (Prometheus), 3000 (Grafana), 9200 (OpenSearch), 5601 (OpenSearch Dashboards), 9187 (Postgres Exporter)

## Objetivo da Migração
Prover uma estrutura Kubernetes equivalente, organizada, com separação de responsabilidades e fácil extensão futura (Ingress, autoscaling, etc.). Manter o foco didático — simplicidade, mas contemplando recursos essenciais: Deployments/StatefulSets, Services, ConfigMaps, Secrets, Volumes, Jobs (k6).

## Entregáveis (diretório `app_v1/k8s/`)
Estrutura mínima esperada:
```
app_v1/k8s/
	kind-cluster.yaml                # Config kind (port mappings ou uso de port-forward)
	namespace.yaml                   # Namespace 'app'
	config/
		prometheus-config.yaml         # ConfigMap Prometheus
		grafana-datasource.yaml        # ConfigMap datasource Prometheus
		grafana-dashboards-config.yaml # ConfigMap (provisioning) apontando para /var/lib/grafana/dashboards
		grafana-dashboard-app.json     # (Opcional) Dashboard principal da API
	postgres/
		postgres.yaml                  # Secret + StatefulSet + Service
	backend/
		backend-deployment.yaml        # Deployment + Service
	frontend/
		frontend-deployment.yaml       # Deployment + Service
	monitoring/
		prometheus-deployment.yaml     # Deployment + Service
		grafana-deployment.yaml        # Deployment + Service
		postgres-exporter.yaml         # Deployment + Service
	logging/
		opensearch.yaml                # StatefulSet + Service (simplificado: single-node)
		opensearch-dashboards.yaml     # Deployment + Service
	loadtest/
		k6-job.yaml                    # Job k6 (executa test_basico ou test_crud)
	README.md                        # Passo a passo: criar cluster, aplicar manifests, validar
```

Observação: nomes de arquivos podem variar levemente desde que mantenham organização lógica e todos os recursos sejam entregues.

## Requisitos Técnicos por Componente

### Namespace
- Criar namespace único `app` para isolar recursos.

### Postgres
- Usar StatefulSet (1 réplica) + PVC (1Gi) para persistência.
- Secret com `POSTGRES_USER=app`, `POSTGRES_PASSWORD=app`, `POSTGRES_DB=appdb`.
- Readiness probe: `pg_isready -U app -d appdb`.
- Service ClusterIP `postgres` porta 5432.

### Backend (FastAPI)
- Deployment (replicas=1 inicialmente) com labels consistentes (`app=backend`).
- Container image: preferir reutilizar imagem já construída localmente (instruir build/tag: `docker build -t backend-local -f backend/Dockerfile .`), ou usar `imagePullPolicy: IfNotPresent`.
- Variável de ambiente `DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/appdb`.
- Variáveis OpenSearch (podem permanecer apontando para `opensearch:9200`).
- Liveness/Readiness probes HTTP simples em `/items?limit=1` (GET) ou `/docs` (Readiness: initialDelay 5s, period 10s).
- Service ClusterIP `backend` porta 8000.
- Recursos (requests mínimos): cpu 50m, memory 128Mi.

### Frontend (Streamlit)
- Deployment com variáveis `API_HOST=backend` e `API_PORT=8000`.
- Service ClusterIP `frontend` porta 8501.
- Probes opcionais (readiness: `/` HTTP 200; liveness igual).

### Prometheus
- ConfigMap com scrape jobs:
	- `backend:8000/metrics`
	- `postgres-exporter:9187`
	- Autosscrape de si próprio (opcional).
- Deployment + volume (emptyDir ou configMap para config). Persistência não obrigatória didaticamente.
- Service `prometheus` porta 9090.
- Habilitar remote write receiver: args `--web.enable-remote-write-receiver`.

### Postgres Exporter
- Deployment com `DATA_SOURCE_NAME=postgresql://app:app@postgres:5432/appdb?sslmode=disable`.
- Service `postgres-exporter` porta 9187.

### Grafana
- Deployment com env `GF_SECURITY_ADMIN_USER=admin`, `GF_SECURITY_ADMIN_PASSWORD=admin` (ConfigMap ou Secret — pode ser simples neste exercício).
- Mount ConfigMap(s) para datasources e dashboards provisioning.
- Service `grafana` porta 3000.

### OpenSearch
- StatefulSet single-node (`discovery.type=single-node`, `plugins.security.disabled=true`).
- Reduzir memória via `OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m`.
- Service `opensearch` portas 9200, 9600 (opcional).

### OpenSearch Dashboards
- Deployment com `OPENSEARCH_HOSTS=["http://opensearch:9200"]` e `DISABLE_SECURITY_DASHBOARDS_PLUGIN=true`.
- Service `opensearch-dashboards` porta 5601.

### k6 (Job)
- Job que monta um ConfigMap contendo os scripts `test_basico.js` e `test_crud.js`.
- Container image: `grafana/k6:latest`.
- Variável `API_BASE=http://backend:8000`.
- Comando exemplo (básico): `k6 run /scripts/test_basico.js`.
- Segunda variante (comentada) para CRUD.

### Acesso Externo
Opções didáticas:
1. `kubectl port-forward` (documentado no README).
2. NodePort (mapear algumas portas — opcional; se usar, alinhar com `kind-cluster.yaml`).
3. (Opcional) Ingress Controller (Nginx) — mencionar como passo futuro.

### Observabilidade
- Confirmar que as métricas de backend continuam acessíveis em `/metrics` via Service interno e são scrapadas.
- Grafana deve conectar no Prometheus automaticamente (datasource provisionado).
- k6 exporta métricas (remote write) para Prometheus (validar série `http_reqs`).

## Passo a Passo Esperado (README em `k8s/`)
1. Criar cluster kind.
2. Aplicar namespace.
3. Build das imagens locais (backend/frontend) e tag se necessário.
4. Aplicar ConfigMaps/Secrets.
5. Aplicar StatefulSets/Deployments + Services (ordem sugerida: Postgres -> Exporter -> Backend -> Frontend -> OpenSearch -> Dashboards -> Prometheus -> Grafana -> k6 Job).
6. Port-forward ou NodePorts para acesso local.
7. Executar Job k6 e inspecionar métricas.
8. Critérios de validação (ver abaixo).

## Critérios de Aceite (Checklist)
Infraestrutura:
- [ ] Diretório `app_v1/k8s/` com estrutura organizada (subpastas por componente).
- [ ] `kind-cluster.yaml` funcional (ou README explicando alternativa sem mapear portas).
- [ ] `namespace.yaml` cria namespace `app`.

Banco de Dados:
- [ ] StatefulSet Postgres com PVC 1Gi e readiness probe.
- [ ] Secret com credenciais presentes e referenciadas.
- [ ] Service `postgres` resolvendo via DNS interno.

Backend:
- [ ] Deployment com env `DATABASE_URL` correto e variáveis OpenSearch.
- [ ] Probes HTTP configuradas (readiness/liveness) retornando 200.
- [ ] Service `backend` porta 8000.

Frontend:
- [ ] Deployment referenciando API via env (`API_HOST`, `API_PORT`).
- [ ] Service `frontend` porta 8501.

Observabilidade:
- [ ] ConfigMap Prometheus inclui jobs backend e postgres-exporter.
- [ ] Prometheus com arg `--web.enable-remote-write-receiver` ativo.
- [ ] Grafana datasource configurado automaticamente (sem intervenção manual).
- [ ] Dashboard exemplo ou instruções claras para importar.

Exporters e Logs:
- [ ] Postgres Exporter coletando em `/metrics` (job visível no Prometheus).
- [ ] OpenSearch acessível (índice de logs criado após tráfego gerado se logging ativo).

Testes de Carga:
- [ ] Job k6 concluindo com exit code 0 em teste básico.
- [ ] Métricas k6 visíveis (ex.: `rate(http_reqs[1m])`).
- [ ] Thresholds não violados (p95 dentro do definido nos scripts). Caso violem, job deve falhar (exit code ≠ 0), validando gate.

Documentação:
- [ ] README em `k8s/` descreve todos os passos, comandos e validações.
- [ ] Seções de troubleshooting (ex.: pods CrashLoopBackOff, DNS, volume Pending).

Boas Práticas:
- [ ] Resources (requests) definidos ao menos para backend e Postgres.
- [ ] Uso de Secrets para credenciais sensíveis.
- [ ] Labels consistentes (`app`, `component`, `tier` opcionais).
- [ ] Manifests aplicáveis via `kubectl apply -R -f k8s/` sem erros.

## Troubleshooting (devem constar no README)
| Sintoma | Possível causa | Ação |
|---------|----------------|------|
| Pod Postgres Pending | Sem storage class | Usar kind default / ajustar PVC |
| Backend CrashLoop | DATABASE_URL errado ou Postgres não pronto | Ver logs `kubectl logs` e events |
| Prometheus sem séries k6 | Remote write receiver não habilitado | Conferir args do container |
| k6 Job falha | API não pronta ou thresholds violados | Reexecutar após readiness, ajustar carga |
| Grafana sem datasource | ConfigMap provisioning incorreto | Ver logs container grafana |

## Instruções Adicionais
1. Evitar ferramentas externas complexas (Helm/Kustomize) neste primeiro passo — manifests YAML simples.
2. Usar nomes e labels previsíveis para facilitar futuras queries (ex.: `app=backend`, `app=grafana`).
3. Scripts k6 podem ser montados via ConfigMap (evitar build de imagem custom agora).
4. Não focar em segurança avançada (NetworkPolicies, RBAC fino) — mencionar como evolução.

## Saída Esperada
Ao final, um único comando:
```bash
kubectl get pods -n app
```
Deve listar todos os pods em estado `Running` ou `Completed` (para o Job k6), e os serviços acessíveis via port-forward ou NodePort.

---
Entregue os manifests prontos; não apenas descreva. Garanta que nomes de arquivos e referências (ex.: nomes de ConfigMaps em volumes) estejam consistentes para aplicação direta.

