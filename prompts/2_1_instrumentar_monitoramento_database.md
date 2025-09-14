Você é um(a) DevOps sênior. Instrumente métricas do banco de dados Postgres da aplicação em `app_v1` usando o Postgres Exporter (Prometheus) e exponha-as para o Prometheus já presente no `docker-compose`.

Contexto do projeto
- Raiz: `app_v1/`
- Serviços atuais no compose: `db` (Postgres 16), `backend` (FastAPI com `/metrics`), `frontend` (Streamlit), `prometheus`.
- Banco: usuário `app`, senha `app`, DB `appdb` (definidos no compose).
- Se baseie a implementação somente na pasta indicada

Objetivo
- Adicionar um serviço `postgres-exporter` (imagem `prometheuscommunity/postgres-exporter`) ao `docker-compose` para expor métricas do Postgres em `:9187/metrics`.
- Configurar o Prometheus para fazer scrape do `postgres-exporter`.
- Validar as métricas principais (ex.: `pg_up`, `pg_stat_database_*`, `pg_database_size_bytes`).

Boas práticas e observações didáticas
- Use uma string de conexão somente-leitura quando possível. Para fins didáticos, pode-se reutilizar `app/app` e `appdb`.
- Evite expor a porta do exporter externamente em produção; aqui ela será mapeada para facilitar a inspeção local.
- Em ambientes reais, considere criar um usuário dedicado (ex.: `metrics`) com privilégios mínimos.

Tarefas (caminhos relativos a `app_v1`)
1) Adicionar serviço Postgres Exporter no `docker-compose.yml`
   - Acrescente o serviço abaixo sob `services:`:
     ```yaml
     postgres-exporter:
       image: prometheuscommunity/postgres-exporter:latest
       environment:
         - DATA_SOURCE_NAME=postgresql://app:app@db:5432/appdb?sslmode=disable
       ports:
         - "9187:9187"  # opcional, útil para inspeção local
       depends_on:
         db:
           condition: service_healthy
     ```
   - Observação: `DATA_SOURCE_NAME` é o DSN usado pelo exporter para conectar no Postgres.

2) Configurar scrape no `prometheus/prometheus.yml`
   - Adicione um novo job:
     ```yaml
     - job_name: 'postgres-exporter'
       static_configs:
         - targets: ['postgres-exporter:9187']
     ```
   - Mantenha os jobs existentes (ex.: `backend`, `prometheus`).

3) Subir/atualizar o stack
   - No PowerShell (Windows):
     ```powershell
     cd c:\cursos\generative_ai_for_devops\app_v1
     docker compose build
     docker compose up -d
     ```

4) Validação
   - Exporter direto (opcional):
     - Abra `http://localhost:9187/metrics` e busque por `pg_up` (deve ser 1).
   - Prometheus Targets:
     - Acesse `http://localhost:9090/targets` e verifique `postgres-exporter` como `UP`.
   - Consultas iniciais no Prometheus (Graph):
     - `pg_up`
     - `pg_stat_database_xact_commit` por database
     - `pg_stat_database_tup_inserted` por database
     - `pg_database_size_bytes{datname="appdb"}` para tamanho do banco `appdb`
     - Taxa de commits por segundo (ex.: `rate(pg_stat_database_xact_commit[1m])`)

5) Atualize o README.md conforme atualizacoes e boas praticas     

Critérios de aceite
- Serviço `postgres-exporter` presente no `docker-compose.yml` e conectado ao `db`.
- `prometheus/prometheus.yml` atualizado com job `postgres-exporter` apontando para `postgres-exporter:9187`.
- Após `docker compose up -d`, o target `postgres-exporter` aparece como `UP` no Prometheus.
- Métricas do Postgres disponíveis (p.ex., `pg_up` e `pg_stat_database_*`).

Extras
- Consultas customizadas:
  - Montar um arquivo `queries.yml` e usar `PG_EXPORTER_EXTEND_QUERY_PATH=/etc/postgres_exporter/queries.yml` no exporter para métricas de negócio (ex.: contagem de linhas por tabela).
- `pg_stat_statements` (avançado):
  - Requer `shared_preload_libraries=pg_stat_statements` no Postgres (configuração avançada), criação da extensão e permissões — útil para análise de queries, mas fora do escopo básico.

Notas de segurança
- Evite credenciais no compose em produção; prefira variáveis em `.env` ou secrets.
- Restrinja acesso ao `postgres-exporter` por rede/ACL em ambientes reais.
