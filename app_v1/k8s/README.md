# Migração para Kubernetes (kind)

Este diretório contém manifests Kubernetes que reproduzem a stack definida em `docker-compose.yml`.

## Componentes
- Postgres (StatefulSet + PVC)
- Backend (FastAPI)
- Frontend (Streamlit)
- Prometheus + Postgres Exporter
- Grafana (datasource e dashboard provisionados)
- OpenSearch + OpenSearch Dashboards
- k6 (Job de carga)

Namespace único: `app`.

## 1. Criar o cluster kind
```bash
kind create cluster --config kind-cluster.yaml --name app-cluster
```
Se não quiser expor NodePorts, pode usar `kind create cluster --name app-cluster` e depois apenas `kubectl port-forward`.

## 2. Aplicar namespace
```bash
kubectl apply -f namespace.yaml
```

## 3. Build das imagens locais
Execute a partir de `app_v1/` (onde estão `backend/` e `frontend/`).
```bash
docker build -t backend-local:latest -f backend/Dockerfile .
docker build -t frontend-local:latest -f frontend/Dockerfile .
kind load docker-image backend-local:latest --name app-cluster
kind load docker-image frontend-local:latest --name app-cluster
```

## 4. Aplicar ConfigMaps e Secrets
```bash
kubectl apply -f k8s/config/ -n app
kubectl apply -f k8s/postgres/postgres.yaml
```
(Secret está embutido em `postgres.yaml`).

## 5. Aplicar Deployments/StatefulSets + Services (ordem sugerida)
```bash
kubectl apply -f k8s/postgres/postgres.yaml
kubectl apply -f k8s/monitoring/postgres-exporter.yaml
kubectl apply -f k8s/backend/backend-deployment.yaml
kubectl apply -f k8s/frontend/frontend-deployment.yaml
kubectl apply -f k8s/logging/opensearch.yaml
kubectl apply -f k8s/logging/opensearch-dashboards.yaml
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

## 6. Executar Job k6 (após backend e prometheus prontos)
```bash
kubectl apply -f k8s/loadtest/k6-job.yaml
kubectl logs -l app=k6 -n app -f
```
Reexecutar (limpando job anterior se quiser):
```bash
kubectl delete job k6-smoke -n app
kubectl apply -f k8s/loadtest/k6-job.yaml
```
Para testar o script CRUD manualmente (exemplo):
```bash
kubectl create job k6-crud --image=grafana/k6:latest -n app -- "k6" "run" "--vus" "5" "--duration" "30s" \
  "/scripts/test_crud.js"
```
(montar CM: usar o mesmo volume `k6-scripts` se criar spec customizada; ou reutilizar Job base adaptando spec.)

## 7. Acesso aos serviços
### Via NodePort (mapeado pelo kind-cluster.yaml)
Exponha adicionando NodePort patch (exemplo simplificado) se desejar. Alternativa principal: port-forward.

### Via port-forward (recomendado didaticamente)
Em terminais separados:
```bash
kubectl port-forward svc/backend -n app 8000:8000
kubectl port-forward svc/frontend -n app 8501:8501
kubectl port-forward svc/prometheus -n app 9090:9090
kubectl port-forward svc/grafana -n app 3000:3000
kubectl port-forward svc/opensearch -n app 9200:9200
kubectl port-forward svc/opensearch-dashboards -n app 5601:5601
```

## 8. Validação
```bash
kubectl get pods -n app
```
Todos devem estar `Running` ou `Completed` (Job k6). Verifique:
- Backend readiness: `kubectl describe pod -l app=backend -n app` (probes OK)
- Prometheus target list: http://localhost:9090/targets (após port-forward)
- Grafana: http://localhost:3000 (user/pass admin/admin) -> dashboard "App - FastAPI Overview" carregado
- OpenSearch: `curl http://localhost:9200` deve retornar JSON cluster_name

## 9. Métricas k6
Após job:
- Ver Prometheus: query `rate(http_reqs_total[1m])` ou métricas `k6_`/`http_req_duration`.
- Threshold p(95) < 500ms (básico) / <700ms (CRUD) — se violado, Job finaliza com código de erro (>0).

## Troubleshooting
| Sintoma | Possível causa | Ação |
|--------|----------------|------|
| Pod Postgres Pending | StorageClass ausente | Ver `kubectl get sc`; usar default do kind ou criar SC simples |
| Backend CrashLoop | Postgres não pronto / URL errada | Checar logs `kubectl logs` e readiness de Postgres |
| Prometheus sem séries k6 | Flag remote write não aplicada | Ver args do container (`--web.enable-remote-write-receiver`) |
| k6 Job falha | API não pronta / thresholds violados | Reaplicar job após readiness | 
| Grafana sem datasource | ConfigMap naming incorreto | Conferir mounts `grafana-datasource` e logs |
| OpenSearch lento | JVM heap insuficiente | Ajustar `OPENSEARCH_JAVA_OPTS` |
| Dashboards vazios | Falta de tráfego | Executar novamente job k6 |

## Limpeza
```bash
kubectl delete namespace app
kind delete cluster --name app-cluster
```

## Próximos Passos (Evoluções)
- Ingress Controller (Nginx) unificando hostnames.
- AutoScaling (HPA) para backend.
- NetworkPolicies restringindo acesso ao banco.
- Persistência real para OpenSearch (PVC) & Prometheus.
- Secrets em formato externo (SOPS / External Secrets) e RBAC granular.

## Aplicação em lote
Para aplicar tudo (exceto cluster creation e imagens):
```bash
kubectl apply -R -f k8s/
```
Se houver erros, corrija pela ordem sugerida.

## Checklist de Aceite
- Infraestrutura: diretórios & namespace OK.
- Postgres: StatefulSet + PVC + Secret + readiness.
- Backend: Deployment + Service + probes + env.
- Frontend: Deployment + Service + env.
- Observabilidade: Prometheus scrape backend/exporter; Grafana datasource OK; Dashboard provisionado.
- Exporters/Logs: Postgres exporter, OpenSearch, Dashboards.
- Carga: Job k6 executa e envia métricas.
- Documentação: este README cobre passos e troubleshooting.
- Boas práticas: requests mínimas backend & postgres; secrets para credenciais; labels consistentes.

## Comando Final de Verificação
```bash
kubectl get pods -n app
```
