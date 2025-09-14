
# 🚀 Generative AI for DevOps – Material de apoio - Curso Udemy

Aprenda (ou refine) habilidades de DevOps acelerando o desenvolvimento de uma aplicação FastAPI + Streamlit, evoluindo de um MVP simples (app_v0) para uma versão instrumentada e observável (app_v1) usando **Prompts bem estruturados** e ferramentas de **Generative AI** como copilots/assistentes.


## 🎯 Objetivo do Treinamento
Mostrar, de ponta a ponta, como um(a) profissional DevOps / Platform / SRE pode:

1. Entender rapidamente uma base de código inicial.
2. Formular prompts eficazes para implementar incrementos.
3. Containerizar e orquestrar serviços (Docker Compose → Kubernetes).
4. Instrumentar métricas, logs estruturados e dashboards.
5. Validar performance e resiliência com testes de carga (k6) e fault injection (Istio).
6. Criar um ciclo iterativo: Ideia → Prompt → Código → Observabilidade → Ajuste.



## 🧱 Estrutura do Repositório

| Pasta | Descrição | Seu Papel |
|-------|-----------|-----------|
| `app_v0/` | Versão base mínima: FastAPI CRUD + Postgres + Streamlit (sem observabilidade, sem Docker oficial) | Ponto de partida para praticar e gerar melhorias via prompts |
| `app_v1/` | Versão evoluída: Docker Compose, métricas Prometheus, logs estruturados, Grafana, k6, OpenSearch, infra de observabilidade | Referência / inspiração do que você pode construir |
| `grafana_dashboards/` | Dashboards JSON prontos (API, Postgres, k6) | Importar / estudar / adaptar |
| `prompts/` | Roteiro textual dos incrementos (containerização, métricas, logging, testes, K8s, Istio, etc.) | Base para criar seus próprios prompts | 
| `app_v1/k8s/` | Manifests para migração Docker Compose → Kubernetes (kind) | Prática guiada de orquestração |

## 🔍 Diferenças Essenciais (v0 → v1)

| Tema | v0 | v1 |
|------|----|----|
| Execução | Local manual | Docker Compose orquestrado |
| Observabilidade | Não | Métricas + Dashboards + Logs estruturados |
| Métricas | — | `/metrics` (Prometheus Exporter) |
| Logs | Console simples | JSON + OpenSearch |
| Teste de Carga | — | Scripts k6 integrados |
| Dashboards | — | Provisionados (Grafana) |
| Preparação p/ K8s | Não | Manifests e orientação para migração |
| Estudos de Resiliência | Não | Fault Injection / Istio (exemplos) |

## 🧪 Tecnologias-Chave
FastAPI, Uvicorn, SQLAlchemy 2.0, Postgres, Streamlit, Prometheus, Grafana, k6, OpenSearch, Docker / Compose, (Kubernetes + Istio nos exercícios avançados), Logging estruturado JSON, Generative AI (assistentes/copilots) para aceleração.

## 📚 Grade do Curso
<ol>
	<li>Assistentes de GenAI aplicados ao DevOps</li>
	<li>Automatizando tarefas repetitivas com IA</li>
	<li>Conteinerização e Orquestração automatizada (Docker & Compose)</li>
	<li>Monitoramento com Prometheus – métricas e instrumentação automatizada</li>
	<li>Observabilidade com Grafana & OpenSearch – dashboards inteligentes</li>
	<li>Stress Test com K6 – validando resiliência e autoscaling</li>
	<li>Migrando para Kubernetes com Kind – prática guiada</li>
	<li>Istio & Kiali – observabilidade avançada em malha de serviços</li>
	<li>Automatizando lançamentos CI/CD com GenAI</li>
	<li>Integrando logs com API de GenAI (personalização de alertas)</li>
</ol>

## ☸️ Migração para Kubernetes (Visão Geral)
A pasta `app_v1/k8s/` contém manifests que reproduzem a stack do `docker-compose.yml` em um cluster **kind** (Kubernetes in Docker). Elementos presentes:

- Namespace `app`.
- Postgres (StatefulSet + PVC + Secret embutido).
- Backend FastAPI e Frontend Streamlit (Deployments + Services).
- Prometheus + Exporter do Postgres.
- Grafana provisionada (datasource/dashboards via ConfigMaps).
- OpenSearch e OpenSearch Dashboards.
- Job k6 para carga.

Fluxo resumido (factual conforme README de `k8s`):
1. Criar cluster kind com arquivo `kind-cluster.yaml`.
2. Aplicar `namespace.yaml`.
3. Build e load das imagens locais para o cluster (`kind load docker-image`...).
4. Aplicar ConfigMaps e Postgres.
5. Aplicar Deployments / Services (backend, frontend, monitoring, logging).
6. Executar Job de carga k6 (`k6-job.yaml`).
7. Acessar serviços via `kubectl port-forward`.

Objetivo pedagógico: mostrar continuidade natural da orquestração (Compose → K8s) e manter observabilidade equivalente.

## 🧠 Como Usaremos Generative AI
Você será conduzido a escrever prompts progressivamente melhores. Cada prompt deve ter:

1. Contexto: “Tenho um CRUD FastAPI sem métricas…”
2. Objetivo claro: “Quero expor métricas padrão HTTP e DB no formato Prometheus.”
3. Restrições: “Sem quebrar a API existente, manter Python 3.11, evitar libs muito pesadas.”
4. Critérios de aceitação: “Endpoint `/metrics` acessível; métricas de requisição e contagem de exceções; atualizar README.”
5. Passo seguinte: “Gerar testes de carga básicos.”

> Boas respostas vêm de bons prompts. Mantenha-os estruturados, incrementais e verificáveis

## 🧪 Desafios (Hands-on)
| Nº | Desafio | Objetivo de Aprendizagem |
|----|---------|--------------------------|
| 1 | Adicionar validação extra no modelo Item | Revisar schemas / Pydantic |
| 2 | Implementar paginação robusta com ordenação | Query params + repositório |
| 3 | Expor métricas de latência por rota | Instrumentação |
| 4 | Criar dashboard custom (RPS, p95, erros) | Observabilidade |
| 5 | Adicionar log de correlação `request_id` | Tracing lógico básico |
| 6 | Escrever teste k6 para CRUD completo | Automação de performance |
| 7 | Simular falha 90% no backend (Istio) | Resiliência / fallback |
| 8 | Adicionar retry exponencial no frontend | Tolerância a falhas |
| 9 | Detectar regressão de latência via thresholds k6 | Qualidade contínua |
| 10 | Documentar checklist de produção | Síntese / maturidade |

## 🔄 Ciclo de Prompt Iterativo (Exemplo)
1. Prompt inicial amplo → receber resposta.
2. Rodar código gerado / adaptar.
3. Observar métricas/logs.
4. Refinar prompt especificando gaps: “A métrica X não apareceu…”
5. Repetir até cumprir critérios de aceitação.

## 🗂️ Visão Rápida de Arquivos Importantes
| Caminho | Função |
|---------|--------|
| `app_v0/backend/main.py` | API CRUD inicial |
| `app_v1/backend/metrics.py` | Instrumentação Prometheus |
| `app_v1/docker-compose.yml` | Orquestração serviços |
| `app_v1/k6/` | Scripts de carga |
| `app_v1/k8s/` | Yaml do Kubernetes |
| `grafana_dashboards/` | Dashboards prontos |
| `prompts/` | Guias de evolução / instruções |

## 💡 Dicas para Prompts Eficazes
- Use listas numeradas para requisitos.
- Explicite formato de saída desejado (ex: “apenas patch diff” ou “função completa”).
- Informe contexto técnico (linguagem, libs, versão Python).
- Peça testes ou exemplos de uso.
- Depois de aplicar, sempre valide antes de partir para o próximo passo.

## 🧭 Critérios de Sucesso do Curso
- Você entende as diferenças arquiteturais entre v0 e v1.
- Consegue adicionar uma métrica ou log novo sem “tentar e errar” às cegas.
- Sabe criar e evoluir um dashboard relevante para SLOs.
- Consegue transformar um ticket textual em um prompt objetivo.
- Consegue justificar cada melhoria (valor observável / operacional).

## 🛠️ Setup Rápido (Local - v0)
```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r app_v0/requirements.txt
uvicorn app_v0.backend.main:app --reload --port 8000
streamlit run app_v0/frontend/app.py
```

## 🐳 Stack Observável (v1 via Docker Compose)
```powershell
cd app_v1
docker compose up -d --build
# UI:       http://localhost:8501
# API:      http://localhost:8000
# Grafana:  http://localhost:3000  (admin/admin)
# Prometheus: http://localhost:9090
# OpenSearch: http://localhost:9200
```

## 🔬 Teste de Carga Rápido (k6)
```powershell
cd app_v1
docker compose --profile k6 run --rm k6
```

## 🧾 Licença / Uso
Material educacional. Adapte livremente nos seus estudos ou em treinamentos internos, mantendo referências quando apropriado.

## 🤝 Contribuições
Sugestões de novos desafios ou melhorias de dashboards são bem-vindas via issues / pull requests. Foque em exemplos claros e incrementais.

---

Boa jornada! Utilize a GenAI apenas dentro do escopo evidenciado no repositório e valide sempre cada modificação com execução local ou via Docker Compose. 🙌

