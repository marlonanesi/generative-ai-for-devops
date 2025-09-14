# Operação do Cluster kind (Ciclo de Vida)

Este documento complementa o `README.md` e foca nas operações do cluster **kind** e estratégias de pausa, retomada e recriação do ambiente.

## Visão Geral
O cluster kind criado via `kind-cluster.yaml` executa toda a stack da aplicação (namespace `app`). Você pode:
- Pausar temporariamente (economia de CPU/RAM) sem perder dados críticos (Postgres)
- Reduzir réplicas a zero para “hibernar” workloads
- Deletar e recriar com passos repetíveis
- Evoluir para persistência de métricas/logs se necessário

---
## 1. Criar o Cluster
```powershell
kind create cluster --config app_v1/k8s/kind-cluster.yaml --name app-cluster
```
Ver info:
```powershell
kubectl cluster-info --context kind-app-cluster
```

## 2. Carregar Imagens Locais (backend / frontend)
Sempre que rebuildar: 
```powershell
docker build -t backend-local:latest -f app_v1/backend/Dockerfile app_v1
docker build -t frontend-local:latest -f app_v1/frontend/Dockerfile app_v1
kind load docker-image backend-local:latest --name app-cluster
kind load docker-image frontend-local:latest --name app-cluster
```

## 3. Aplicar Manifests
Aplicação recursiva:
```powershell
kubectl apply -R -f app_v1/k8s/
```
Listar pods:
```powershell
kubectl get pods -n app
```

---
## 4. Pausar o Cluster (Economizar Recursos)
Parar o container do node kind (pausa rápida):
```powershell
docker stop app-cluster-control-plane
```
Retomar depois:
```powershell
docker start app-cluster-control-plane
kubectl get pods -n app
```
O que persiste:
| Componente | Persiste? | Observação |
|------------|-----------|------------|
| Postgres (PVC) | Sim | Dados mantidos |
| Backend/Frontend | Sim (recriados) | Estado em memória não importa |
| Prometheus dados | Não | Precisaria PVC/config extra |
| Grafana config | Sim | Datasource/dashboard via ConfigMap |
| OpenSearch dados | Não | `emptyDir` atual |
| k6 Job | Não reutilizado | Reaplicar se necessário |

---
## 5. Hibernar Workloads (Escalar a Zero)
Para reduzir consumo mantendo cluster ativo:
```powershell
kubectl scale deploy backend frontend grafana prometheus opensearch-dashboards -n app --replicas=0
kubectl scale statefulset opensearch -n app --replicas=0
```
Manter Postgres normalmente.
Voltar:
```powershell
kubectl scale statefulset opensearch -n app --replicas=1
kubectl scale deploy backend frontend grafana prometheus opensearch-dashboards -n app --replicas=1
```

---
## 6. Recriar do Zero (Fluxo Determinístico)
Use quando quiser ambiente limpo:
```powershell
kind delete cluster --name app-cluster
kind create cluster --config app_v1/k8s/kind-cluster.yaml --name app-cluster
# Rebuild se código mudou
docker build -t backend-local:latest -f app_v1/backend/Dockerfile app_v1
docker build -t frontend-local:latest -f app_v1/frontend/Dockerfile app_v1
kind load docker-image backend-local:latest --name app-cluster
kind load docker-image frontend-local:latest --name app-cluster
kubectl apply -R -f app_v1/k8s/
```

---
## 7. Reexecutar o Job k6
Após retomada ou recriação:
```powershell
kubectl delete job k6-smoke -n app 2>$null
kubectl apply -f app_v1/k8s/loadtest/k6-job.yaml
kubectl logs -n app job/k6-smoke -f
```
Executar variante CRUD (exemplo manual):
```powershell
kubectl create job k6-crud --image=grafana/k6:latest -n app -- \
  k6 run --vus 5 --duration 30s /scripts/test_crud.js
```
(Exigiria montar o ConfigMap de scripts numa spec própria ou adaptar manifest.)

---
## 8. Testes Rápidos Pós-Retomada
```powershell
kubectl get pods -n app
kubectl port-forward svc/backend -n app 8000:8000
# Em outro terminal:
Invoke-WebRequest http://localhost:8000/items?limit=1 -UseBasicParsing | Select-Object StatusCode
```
Prometheus targets (após port-forward 9090): http://localhost:9090/targets
Grafana (port-forward 3000): http://localhost:3000 (admin/admin)

---
## 9. Persistência (Evoluções Futuras)
| Serviço | Evolução | Passo Futuro |
|---------|----------|--------------|
| Prometheus | Retenção de métricas | Adicionar PVC + args de storage TSDB |
| OpenSearch | Persistir índices | Substituir `emptyDir` por PVC (1–5Gi) |
| Grafana | Credenciais seguras | Secret separado + provisionamento ─ remover plaintext |
| Backend | AutoScaling | Adicionar HPA baseado em CPU ou latency via custom metrics |
| Ingress | Acesso unificado | Implantar ingress-controller (nginx) |

---
## 10. Problemas Comuns ao Retomar
| Sintoma | Causa Provável | Ação |
|---------|----------------|------|
| Pods CrashLoopBackOff | Ordem de dependências / DNS atrasado | Aguardar alguns segundos ou `kubectl describe pod` |
| OpenSearch demora a responder | Inicialização JVM | Aguardar ~30s; verificar logs |
| Falta de métricas k6 | Job não reexecutado | Reaplicar Job k6 |
| Backend sem resposta local | Port-forward travado | Encerrar sessão anterior e refazer `kubectl port-forward` |
| PVC Postgres não monta | Cluster recriado | Recriação zera storage; é esperado |

---
## 11. Scripts Sugeridos (Opcional)
Crie `scripts/pause.ps1`:
```powershell
docker stop app-cluster-control-plane
```
Crie `scripts/resume.ps1`:
```powershell
docker start app-cluster-control-plane
kubectl get pods -n app
```

---
## 12. Checklist Rápido de Operações
| Ação | Comando Principal |
|------|-------------------|
| Pausar cluster | `docker stop app-cluster-control-plane` |
| Retomar cluster | `docker start app-cluster-control-plane` |
| Escalar a zero | `kubectl scale deploy <...> --replicas=0` |
| Recriar cluster | `kind delete cluster` → `kind create cluster ...` |
| Recarregar imagens | `kind load docker-image backend-local:latest` |
| Reexecutar k6 | `kubectl apply -f k8s/loadtest/k6-job.yaml` |

---
## 13. Verificação Final
Ao retomar:
```powershell
kubectl get pods -n app
# Esperado: todos Running; job k6 (se reaplicado) Completed
```
Se algo persistir em estado Pending/CrashLoop, ver seção de troubleshooting.

---
## 14. Observações
- Uso de tags explícitas (ex.: `backend-local:v2`) ajuda a garantir que a imagem mais recente foi carregada.
- Para Prometheus/Grafana OpenSearch persistentes, adicionaria PVCs e ajustaria spec (fora do escopo inicial didático).

---
## Istio Service Mesh (Perfil Demo)

### 1. Instalação do istioctl (Windows 11 PowerShell)
```powershell
winget install -e --id Istio.Istioctl
# (Fallback)
curl -L https://istio.io/downloadIstio | powershell
istioctl version
```

### 2. Instalar Istio (usando IstioOperator)
```powershell
kubectl create namespace istio-system 2>$null || echo "namespace existe"
istioctl install -f app_v1/k8s/istio/install-istio.yaml -y
kubectl get pods -n istio-system
```

### 3. Habilitar Injeção de Sidecar
```powershell
kubectl label namespace app istio-injection=enabled --overwrite
kubectl rollout restart deployment -n app --all
kubectl get pods -n app -w
```
Esperar todos com READY 2/2.

### 4. Aplicar Gerenciamento de Tráfego
```powershell
kubectl apply -f app_v1/k8s/istio/traffic-management.yaml -n app
kubectl get gateway,virtualservice,destinationrule -n app
```

### 5. Acessar Kiali
```powershell
istioctl dashboard kiali
# Alternativa
kubectl -n istio-system port-forward svc/kiali 20001:20001
```
Abrir: http://localhost:20001

### 6. Acessar Aplicação via Gateway
1. Obter NodePort ou usar port-forward:
```powershell
kubectl -n istio-system get svc istio-ingressgateway
# Opcional port-forward:
kubectl -n istio-system port-forward deploy/istio-ingressgateway 8080:8080
```
2. Navegar: http://localhost/ (ou http://<nodeIP>:<nodePort>/)

Observação: O `VirtualService` agora inclui `localhost` e `127.0.0.1` na lista de hosts, então não é mais necessário usar `-H "Host: frontend"` para teste local via NodePort ou port-forward. Se você remover esses hosts por algum motivo, volte a usar:
```powershell
curl -H "Host: frontend" http://localhost:<porta>/api/docs
```

### 7. Validação
```powershell
kubectl get pods -n istio-system
kubectl get pods -n app
istioctl proxy-status
kubectl get gw,vs,dr -n app
```
No Kiali: ver grafo com frontend → backend → postgres (gerar tráfego antes).

### 8. Troubleshooting Rápido
| Sintoma | Comando | Ação |
|---------|---------|------|
| Pods sem sidecar | kubectl get pods -n app -o wide | Ver se label existe; reiniciar |
| Kiali indisponível | istioctl dashboard kiali | Verificar pod kiali |
| 404/503 | kubectl describe vs -n app | Conferir host/portas |
| Proxy fora de sync | istioctl proxy-status | Inspecionar config: proxy-config |
| DNS falha | kubectl exec <pod> -c istio-proxy -- nslookup postgres | Conferir CoreDNS / svc |

### 9. Remoção (Opcional)
```powershell
istioctl uninstall --purge -y
kubectl delete ns istio-system
```

### 10. Checklist
- Pods istio-system Running
- Pods app com 2/2
- Gateway + VirtualService aplicados
- Tráfego acessível via ingressgateway
- Kiali exibe grafo completo

### 11. Critérios de Aceite (Detalhado)
| Item | Critério | Status esperado |
|------|----------|-----------------|
| 1 | Namespace `istio-system` criado | `kubectl get ns istio-system` retorna Active |
| 2 | Istio control plane instalado | Pods (`istiod`, `istio-ingressgateway`, `kiali`, etc.) Running |
| 3 | Sidecar injetado | `kubectl get pods -n app` mostra READY = 2/2 |
| 4 | Gateway aplicado | `kubectl get gateway -n app` lista `app-gateway` |
| 5 | VirtualService aplicado | `kubectl get virtualservice -n app` lista `app-virtualservice` |
| 6 | DestinationRules aplicadas | `kubectl get dr -n app` lista backend/front-end |
| 7 | Proxy sync ok | `istioctl proxy-status` sem linhas SYNCED = False |
| 8 | Kiali acessível | Dashboard abre via `istioctl dashboard kiali` |
| 9 | Frontend acessível via gateway | curl retorna HTTP 200 em `/` |
| 10 | Backend via rota `/api` | curl `<gateway>/api/docs` retorna 200/redirect |
| 11 | Grafo Kiali completo | Fluxos frontend → backend → postgres (e métricas) |

Checklist Markdown rápida:
```markdown
- [ ] Namespace istio-system
- [ ] Pods control plane Running
- [ ] Sidecars 2/2 em app
- [ ] Gateway aplicado
- [ ] VirtualService aplicado
- [ ] DestinationRules aplicadas
- [ ] Proxy status sincronizado
- [ ] Kiali acessível
- [ ] Frontend via gateway 200
- [ ] Backend /api 200
- [ ] Grafo completo no Kiali
```

### 12. Troubleshooting Ampliado
| Etapa | Sintoma | Possível causa | Ação |
|-------|---------|---------------|------|
| Instalação | Pods `istiod` CrashLoopBackOff | Falha de config/recursos | `kubectl describe pod -n istio-system <pod>`; verificar events e logs |
| Instalação | `istioctl install` pendura | Falha webhook / CRDs incompletos | Reexecutar `istioctl install -y`; checar `kubectl get crds | findstr istio` |
| Sidecar | Pods em `app` continuam 1/1 | Namespace sem label ou pods não reiniciados | `kubectl label ns app istio-injection=enabled --overwrite`; `kubectl rollout restart deployment -n app --all` |
| Sidecar | Apenas alguns 2/2 | Reinício parcial / readiness lento | Aguardar; verificar `kubectl describe pod` |
| Tráfego | 404 no acesso `/` | VirtualService não casando host/rota | `kubectl get vs -n app -o yaml`; validar `hosts` e `gateways` |
| Tráfego | 503 UF | Endpoints vazios (backend ou frontend não prontos) | `kubectl get endpoints backend -n app`; verificar readinessProbe |
| Tráfego | 503 NR | Rota não configurada / listener errado | `istioctl proxy-config routes <pod> -n app` |
| Proxy | SYNCED = False | Config não propagada | `istioctl proxy-status`; `istioctl proxy-config clusters <pod> -n app` |
| Kiali | Dashboard não abre | Port-forward não ativo | Reexecutar `istioctl dashboard kiali` ou `kubectl port-forward` |
| DNS | Backend não resolve postgres | CoreDNS / Service ausente | `kubectl exec <backend-pod> -c istio-proxy -- nslookup postgres` |
| Observabilidade | Grafo vazio | Sem tráfego recente | Gerar requisições (curl loop) |
| Desinstalação | CRDs permanecem | Uninstall parcial | `istioctl uninstall --purge -y`; depois deletar ns |

Tabela resumida (Sintoma -> Ação rápida):
| Sintoma | Ação rápida |
|---------|-------------|
| Pods sem sidecar | Re-label ns + restart deployments |
| 404 | Ver VS hosts/gateway paths |
| 503 UF | Checar endpoints do serviço |
| Kiali indisponível | Refazer port-forward |
| Proxy desincronizado | `istioctl proxy-status` / `proxy-config` inspeção |

### 13. Script de Automação (PowerShell)
Script opcional para rodar após instalar binário `istioctl` (ajuste versão se diferente):
```powershell
$ErrorActionPreference = 'Stop'
$istioVersion = '1.22.3'
if (-not (Get-Command istioctl -ErrorAction SilentlyContinue)) {
  Write-Host 'istioctl não encontrado no PATH. Baixe manualmente conforme README.' -ForegroundColor Yellow
}
kubectl create ns istio-system 2>$null | Out-Null
istioctl install -f app_v1/k8s/istio/install-istio.yaml -y
kubectl label ns app istio-injection=enabled --overwrite
kubectl rollout restart deployment -n app --all
Write-Host 'Aguardando sidecars...' -ForegroundColor Cyan
$timeout = (Get-Date).AddMinutes(5)
do {
  $pods = kubectl get pods -n app --no-headers 2>$null
  $allInjected = $true
  foreach ($line in $pods) {
    if ($line -notmatch '2/2') { $allInjected = $false; break }
  }
  if (-not $allInjected) { Start-Sleep 5 }
} while (-not $allInjected -and (Get-Date) -lt $timeout)
if (-not $allInjected) { Write-Host 'Timeout aguardando sidecars.' -ForegroundColor Red } else { Write-Host 'Sidecars ok.' -ForegroundColor Green }
kubectl apply -f app_v1/k8s/istio/traffic-management.yaml -n app
kubectl get gw,vs,dr -n app
istioctl proxy-status
Write-Host 'Validar acesso: executar istioctl dashboard kiali em outra janela.' -ForegroundColor Cyan
```

### 14. Validação Final Automatizada
```powershell
kubectl get pods -n istio-system
kubectl get pods -n app
kubectl get gw,vs,dr -n app
istioctl proxy-status
```

### 15. Próximos Passos (Opcional)
- Adicionar regras de mTLS (`PeerAuthentication` + `DestinationRule`).
- Introduzir canary (subset version labels + VirtualService weighted routes).
- Integrar tracing Jaeger (já habilitado demo) no Kiali UI.
- Criar alertas Prometheus para erros 5xx e latência p95.


---
Qualquer melhoria adicional (Ingress, HPA, PVC para logs/metrics) pode ser adicionada incrementalmente.

### (Nova) Estrutura Istio
```
app_v1/k8s/istio/
  install-istio.yaml        # IstioOperator perfil demo
  traffic-management.yaml   # Gateway + VirtualService + DestinationRules
  kiali-dashboard.yaml      # Referência de comandos (não é manifest k8s)
```
Use `install-istio.yaml` como fonte principal para instalação (perfil demo customizado NodePort para kind).

> Seções detalhadas já presentes em "Istio Service Mesh (Perfil Demo)" abaixo utilizam agora estes arquivos. Ajuste comandos se mudar nomes.

### (Addendum) Kiali Graph vazio / Erro prometheus.istio-system
Se o Kiali mostrar erro:
```
Cannot load the graph: Post "http://prometheus.istio-system:9090/api/v1/query": dial tcp: lookup prometheus.istio-system ... no such host
```
Isso significa que o addon Prometheus do Istio não está instalado (Kiali procura no namespace `istio-system`). Soluções:
1. Instalar addon Prometheus do Istio:
```powershell
kubectl apply -f istio-1.22.3/samples/addons/prometheus.yaml
kubectl wait --for=condition=available deployment/prometheus -n istio-system --timeout=180s
```
2. (Opcional) Definir URL explicitamente via env var no Deployment do Kiali:
```powershell
kubectl set env deployment/kiali -n istio-system PROMETHEUS_URL=http://prometheus.istio-system:9090
kubectl rollout restart deployment/kiali -n istio-system
```
3. Gerar tráfego para popular métricas:
```powershell
kubectl exec -n app deploy/frontend -c istio-proxy -- bash -c "for i in {1..10}; do curl -s http://backend.app.svc.cluster.local:8000/items?limit=1 >$null; sleep 1; done"
```
Após alguns segundos recarregar o grafo no Kiali.

### Demonstração: Fault Injection via Kiali
1. Garantir que existe VirtualService dedicado ao backend (sem fault):
```powershell
kubectl apply -f app_v1/k8s/istio/backend-virtualservice-baseline.yaml -n app
kubectl delete virtualservice backend-fault-vs -n app 2>$null
```
2. Gerar tráfego inicial (para Kiali mapear):
```powershell
kubectl exec -n app deploy/frontend -c istio-proxy -- bash -c "for i in {1..8}; do curl -s http://backend.app.svc.cluster.local:8000/items?limit=1 > /dev/null; sleep 1; done"
```
3. Abrir Kiali → Services → `backend` → botão/menú `Actions` → `Create Traffic Policy` / `Fault Injection` (dependendo da UI) e configurar:
   - Delay: 2s em 30%
   - Abort: 503 em 5%
   Salvar (gera patch no VirtualService `backend-vs`).
4. Validar:
```powershell
istioctl proxy-config routes $(kubectl get pod -n app -l app=frontend -o jsonpath='{.items[0].metadata.name}') -n app | Select-String fault -Context 2
```
5. Rodar teste k6 e observar aumento de latência / 503s.
6. Remover fault (no mesmo wizard: limpar campos) ou:
```powershell
kubectl apply -f app_v1/k8s/istio/backend-virtualservice-baseline.yaml -n app
```

### 16. Fault Injection Rápido (Abort 90% HTTP 500)
Para demonstrar resiliência / circuit breakers, você pode aplicar um VirtualService que devolve HTTP 500 em 90% das requisições ao backend.

Habilitar (aplicar fault):
```powershell
kubectl apply -f app_v1/k8s/istio/backend-fault-90pct.yaml -n app
kubectl get virtualservice -n app | findstr backend-fault-90pct
```
Gerar algumas requisições de teste (exemplo usando pod temporário sem sidecar):
```powershell
kubectl run curltest --image=curlimages/curl:8.8.0 -n app --restart=Never --command -- /bin/sh -c "for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w '%{http_code}\n' http://backend.app.svc.cluster.local:8000/items; sleep 0.3; done"
```
(Deve retornar maioria 500.)

Desabilitar (remover fault):
```powershell
kubectl delete virtualservice backend-fault-90pct -n app
```
Verificar que o VS foi removido:
```powershell
kubectl get virtualservice -n app | findstr backend-fault-90pct || echo 'removido'
```
Após remover, as requisições voltam a retornar 200 (salvo erros reais da aplicação).