Você é um(a) DevOps sênior. Inclua o Grafana ao stack em `app_v1` para visualizar as métricas do backend (FastAPI + Prometheus client) e do banco (Postgres Exporter).

Contexto do projeto
- Raiz: `app_v1/`
- Compose já contém: `db`, `backend` (expõe `/metrics`), `frontend`, `prometheus` (scrape de `backend` e `postgres-exporter`), `postgres-exporter`.
- Se baseie a implementação somente na pasta indicada

Objetivo
- Adicionar serviço `grafana` ao `docker-compose.yml`.
- Configurar um datasource Prometheus apontando para `http://prometheus:9090`.
- Disponibilizar acesso em `http://localhost:3000`.
- Opcional: provisionar dashboards e datasource via arquivos de provisionamento.

Boas práticas e observações
- Use a imagem `grafana/grafana:latest` (para o curso). Em produção, pinne versões.
- Utilize provisionamento para datasources/dashboards para reprodutibilidade do ambiente.
- Mantenha credenciais padrão apenas no laboratório; em produção, configure usuários/senhas seguras e persistência.

Tarefas (caminhos relativos a `app_v1`)
1) Adicionar serviço Grafana ao `docker-compose.yml`
	 - Acrescente o serviço:
		 ```yaml
		 grafana:
			 image: grafana/grafana:latest
			 ports:
				 - "3000:3000"
			 depends_on:
				 prometheus:
					 condition: service_started
			 environment:
				 - GF_SECURITY_ADMIN_USER=admin
				 - GF_SECURITY_ADMIN_PASSWORD=admin
			 volumes:
				 - ./grafana/provisioning/:/etc/grafana/provisioning/
		 ```
	 - Observação: o mapeamento de `./grafana/provisioning` permite provisionar datasource/dashboards.

2) Provisionar datasource Prometheus
	 - Crie o arquivo `grafana/provisioning/datasources/datasource.yml` com:
		 ```yaml
		 apiVersion: 1
		 datasources:
			 - name: Prometheus
				 type: prometheus
				 access: proxy
				 url: http://prometheus:9090
				 isDefault: true
				 editable: true
		 ```

3) Provisionar dashboards
	 - Crie `grafana/provisioning/dashboards/dashboards.yml`:
		 ```yaml
		 apiVersion: 1
		 providers:
			 - name: 'default'
				 orgId: 1
				 folder: ''
				 type: file
				 disableDeletion: false
				 editable: true
				 options:
					 path: /etc/grafana/provisioning/dashboards/json
		 ```
	 - Crie a pasta `grafana/provisioning/dashboards/json/` e adicione dashboards JSON (utilize os dashboards dentro da pasta na raiz \grafana_dashboards):

4) Subir/atualizar o stack
	 - PowerShell (Windows):
		 ```powershell
		 cd c:\cursos\generative_ai_for_devops\app_v1
		 docker compose up -d
		 ```

5) Validação
	 - Acesse Grafana em `http://localhost:3000` (admin/admin ou credenciais definidas).
	 - Em Settings -> Datasources, confirme que o datasource Prometheus existe e está `Connected` (Test).

6) Atualize o README.md conforme atualizacoes e boas praticas

Critérios de aceite
- Serviço `grafana` presente no docker-compose e acessível em `http://localhost:3000`.
- Datasource Prometheus configurado (provisionado ou via UI) apontando para `http://prometheus:9090`.
- É possível visualizar métricas do backend e do Postgres em dashboards (manuais ou provisionados).

Extras
- Persistência: mapear volume para `/var/lib/grafana` e manter dashboards/sources entre reinícios.
- Segurança: alterar `GF_SECURITY_ADMIN_PASSWORD`, habilitar autenticação externa.
- Dashboards prontos: importar IDs do Grafana.com (ex.: Node Exporter, PostgreSQL exporter), adaptando às métricas disponíveis.

