# Instrumentação do Cluster Kubernetes com Istio e Kiali

Você é um(a) DevOps sênior. já migramos a orquestração do Docker Compose para Kubernetes (conforme a estrutura em `app_v1/k8s/`), agora queremos evoluir a arquitetura para adotar um service mesh. A tarefa é instrumentar o cluster local kind com Istio e Kiali para gerenciar o tráfego e prover observabilidade.

## Contexto Atual (Kubernetes)

A aplicação já está rodando em um cluster kind no namespace `app`. Os serviços se comunicam internamente via DNS do Kubernetes (por exemplo, o backend acessa o postgres em `postgres:5432`). O monitoramento de métricas com Prometheus/Grafana e a coleta de logs com OpenSearch já estão operacionais.

**Serviços atuais no cluster:**
- db (Postgres)
- backend (FastAPI)
- frontend (Streamlit)
- postgres-exporter
- prometheus
- grafana
- opensearch
- opensearch-dashboards

## Objetivo da Instrumentação

Prover uma infraestrutura de service mesh para gerenciar o tráfego, implementar políticas de segurança e obter visibilidade completa sobre a comunicação entre os microserviços. Manter o foco didático, usando o perfil demo do Istio e um exemplo simples de gerenciamento de tráfego.

## Entregáveis (diretório `app_v1/k8s/istio/`)

Adicionar a seguinte estrutura e arquivos YAML:

```
app_v1/k8s/
  istio/
      install-istio.yaml               # Comandos de instalação (istioctl)
      kiali-dashboard.yaml             # Comandos para acessar o Kiali
      traffic-management.yaml          # Exemplo de Gateway e VirtualService
  README_k8s.md                        # Atualizar com nova seção Istio
```

## Requisitos Técnicos por Componente

### Istio e Kiali

- Usar a ferramenta oficial `istioctl` para a instalação.
- A instalação deve usar o perfil demo para incluir automaticamente todos os componentes, incluindo o istiod, gateways e o Kiali.
- O Istio deve ser instalado no namespace `istio-system`.

### Injeção do Sidecar

- Após a instalação do Istio, todos os pods no namespace `app` devem receber a injeção automática do sidecar proxy do Istio.
- Isso deve ser feito com um único comando de label no namespace `app`.
- Todos os deployments (backend, frontend, postgres, prometheus, etc.) devem ser reiniciados para que o sidecar seja injetado.

### Gerenciamento de Tráfego (Exemplo Prático)

- Criar um arquivo `traffic-management.yaml` que demonstre um caso de uso simples.
- Usar um Gateway do Istio para expor o frontend e o backend externamente (via NodePort ou port-forward conforme a configuração do cluster).
- Usar um VirtualService para rotear o tráfego externo para o serviço frontend (`frontend.app.svc.cluster.local`).

### Observabilidade

- Kiali deve estar acessível via port-forward.
- O dashboard do Kiali deve mostrar o mapa completo da malha de serviços, com setas indicando o fluxo de tráfego entre todos os componentes (frontend, backend, postgres, prometheus, etc.).
- A telemetria do Istio (métricas, logs, traces) deve ser capturada automaticamente e visualizada no Kiali.

## Passo a Passo Esperado (Seção no README_k8s.md)

Adicionar uma nova seção no `README_k8s.md` com os seguintes passos:

1. **Instalar o Istio:** Descrever o comando para instalar o istioctl e, em seguida, o comando para instalar o Istio no cluster.
2. **Habilitar o Service Mesh:** Explicar como rotular o namespace `app` e reiniciar todos os deployments para que os sidecars sejam injetados.
3. **Configurar Acesso Externo e Tráfego:** Descrever os comandos para aplicar o `traffic-management.yaml` e como usar o `kubectl port-forward` para acessar o Kiali e o frontend.
4. **Validar a Instalação:** Instruir o usuário a abrir o Kiali e verificar se o mapa da malha de serviço está completo e se o tráfego está fluindo corretamente.

## Critérios de Aceite (Checklist)

- [ ] Arquivos em `app_v1/k8s/istio/` estão presentes e com sintaxe YAML correta.
- [ ] O namespace `istio-system` existe e contém os pods do plano de controle.
- [ ] Todos os pods no namespace `app` têm 2/2 containers (<seu-container> + istio-proxy).
- [ ] O dashboard do Kiali está acessível e mostra o mapa completo da aplicação.
- [ ] VirtualService e Gateway são aplicados com sucesso.
- [ ] A documentação no `README_k8s.md` foi atualizada com os novos passos.
- [ ] A aplicação é acessível externamente via Istio Gateway.
- [ ] Instalação do istio e kiali no SO [Atual windows 11 - terminal power shell]  e instrumentação e validação completa no Kubernetes feita pelo agente

## Troubleshooting (devem constar no README)

| Sintoma                       | Possível causa                  | Ação                                      |
|-------------------------------|---------------------------------|-------------------------------------------|
| Kiali dashboard não abre      | Port-forward não está ativo     | Rodar `istioctl dashboard kiali`          |
| Pods no app não têm sidecar   | Namespace não foi rotulado      | Rotular o namespace e reiniciar os deployments |
| Tráfego não flui após injeção | VirtualService ou Gateway com erro de configuração | Verificar logs do istio-proxy e do istiod |


## Extensão: Execução Automatizada pelo Agente (Copilot)

Você (agente) NÃO deve apenas gerar comandos; deve:
1. Detectar SO (Windows 11 PowerShell) e instalar `istioctl` (via winget ou download direto).
2. Verificar conectividade com o cluster (`kubectl cluster-info`).
3. Criar namespace `istio-system` se ausente.
4. Instalar Istio perfil `demo` usando:
   - `istioctl install -f app_v1/k8s/istio/install-istio.yaml -y` (preferencial) ou fallback `istioctl install --set profile=demo -y`.
5. Validar pods (`kubectl get pods -n istio-system`) até todos estarem Running.
6. Habilitar injeção: `kubectl label namespace app istio-injection=enabled --overwrite`.
7. Reiniciar workloads: `kubectl rollout restart deployment -n app --all`.
8. Aguardar sidecars (todos os pods 2/2 containers).
9. Aplicar recursos de tráfego: `kubectl apply -f app_v1/k8s/istio/traffic-management.yaml -n app`.
10. Validar:
    - `kubectl get gw,vs,dr -n app`
    - `istioctl proxy-status`
    - `kubectl logs <pod> -c istio-proxy -n app --tail=50`
11. Expor Kiali: `istioctl dashboard kiali` (manter sessão; se falhar usar port-forward manual).
12. Expor frontend via Gateway (usar NodePort do ingressgateway ou port-forward):
    - `kubectl -n istio-system get svc istio-ingressgateway`
13. Gerar tráfego (curl/browser) para popular métricas e depois capturar gráfico no Kiali.
14. Se falhar algum passo, executar bloco de troubleshooting (abaixo) antes de prosseguir.
15. Reportar resumo final (status pods, recursos aplicados, endpoint externo).

O agente deve repetir (polling) com timeout razoável (ex: 300s) a checagem de readiness.

### Comandos Principais (Base)
```powershell
# Verificar se esta instalado
istioctl version

# Instalar istioctl (opção 1)
winget install -e --id Istio.Istioctl

# (Fallback) Download manual
curl -L https://istio.io/downloadIstio | powershell
# Mover binário para PATH se necessário

# Ver versão
istioctl version

# Instalar usando manifest operator
istioctl install -f app_v1/k8s/istio/install-istio.yaml -y

# Label namespace para injeção
kubectl label ns app istio-injection=enabled --overwrite

# Reiniciar deployments
kubectl rollout restart deployment -n app --all
```

### Critérios de Validação Automática pelo Agente do Copilot
- Todos os pods `istio-system` Running.
- Todos os pods em `app` com coluna READY = 2/2.
- `Gateway` e `VirtualService` em `kubectl get gw,vs -n app`.
- `istioctl proxy-status` sem entradas SYNCED = False.
- Acesso ao Kiali funcional.
- Resposta HTTP do frontend via ingress (cURL retorna 200).
- Kiali exibe grafo com frontend → backend → postgres (+ métricas para prometheus/opensearch se tráfego gerado).

### Troubleshooting Ampliado (o agente deve usar quando falhar)
| Etapa | Sintoma | Ação Automatizada |
|-------|---------|-------------------|
| Instalação | Pods istiod CrashLoopBackOff | `kubectl describe pod -n istio-system <pod>`; coletar eventos |
| Sidecar | Pods sem 2/2 | Confirmar label ns; verificar annotation `sidecar.istio.io/inject` |
| Tráfego | 404 no frontend | `kubectl get virtualservice -n app -o yaml`; checar hosts/gateway |
| Tráfego | 503 UF | Verificar endpoints: `kubectl get endpoints frontend -n app` |
| Kiali | Timeout | Reiniciar port-forward / comando `istioctl dashboard kiali` |
| Proxy | SYNC problemas | `istioctl proxy-status`; `istioctl proxy-config clusters <pod> -n app` |
| DNS | Falha backend → postgres | `kubectl exec -n app <backend-pod> -c istio-proxy -- nslookup postgres` |

### Saída Esperada

Ao final, os comandos:

```bash
kubectl get pods -n app
kubectl get pods -n istio-system
```

Devem mostrar todos os pods em estado Running ou Completed e os serviços no namespace `app` devem estar acessíveis através das novas configurações do Istio.

### Observação (Atualizada)
Entregue manifests prontos e inclua instruções de execução automatizada para o agente (não apenas texto). O agente deve relatar no final: tabela de pods, recursos do Istio, endpoints e status de sincronização dos proxies.