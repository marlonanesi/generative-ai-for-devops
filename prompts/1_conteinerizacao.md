Você é um(a) DevOps sênior. Containerize a aplicação Python localizada em app_v1 criando Dockerfiles separados para backend (FastAPI) e frontend (Streamlit) e um docker-compose para subir backend, frontend e Postgres.

Contexto do projeto:
- Raiz: app_v1/
- Backend: FastAPI em app_v1/backend/main.py, usa SQLAlchemy 2.0 + Postgres (psycopg), cria tabelas no startup, lê DATABASE_URL de .env via backend/config.py.
- Frontend: Streamlit em app_v1/frontend/app.py, consome API via HTTP usando API_HOST e API_PORT; carrega .env da raiz.
- Dependências: app_v1/requirements.txt (FastAPI, Uvicorn, SQLAlchemy, psycopg[binary], python-dotenv, streamlit, httpx).
- Portas esperadas: backend 8000, frontend 8501, Postgres 5432.
- Baseie a implementação somente na pasta indicada

Tarefas (entregar arquivos prontos, caminhos relativos a app_v1):
1) backend/Dockerfile
   - Base: python:3.11-slim
   - WORKDIR /app
   - Copiar requirements.txt e instalar com pip --no-cache-dir
   - Copiar o código
   - Criar usuário não-root (uid 1000) e usar USER
   - Expor 8000
   - CMD: uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000

2) frontend/Dockerfile
   - Base: python:3.11-slim
   - WORKDIR /app
   - Copiar requirements.txt e instalar
   - Copiar o código
   - Criar usuário não-root
   - Expor 8501
   - CMD: streamlit run app/frontend/app.py --server.port 8501 --server.address 0.0.0.0

3) docker-compose.yml
   - Serviços: db (postgres:16), backend, frontend
   - db:
     - env: POSTGRES_USER=app, POSTGRES_PASSWORD=app, POSTGRES_DB=appdb
     - volume nomeado: pgdata:/var/lib/postgresql/data
     - healthcheck com pg_isready
   - backend:
     - build: ./backend (contexto raiz app_v1 para acessar requirements.txt)
     - environment:
       - DATABASE_URL=postgresql+psycopg://app:app@db:5432/appdb
     - ports: "8000:8000"
     - volumes (dev/hot-reload): ./:/app
     - depends_on: db (condition: service_healthy)
   - frontend:
     - build: ./frontend (contexto raiz app_v1)
     - environment:
       - API_HOST=backend
       - API_PORT=8000
     - ports: "8501:8501"
     - volumes (dev/hot-reload): ./:/app
     - depends_on: backend (service_started ou service_healthy se healthcheck no backend)
   - volumes: pgdata:
   - networks padrão

4) .dockerignore (na raiz e, se preferir, em backend/ e frontend/):
   - .venv, __pycache__, *.pyc, .git, .gitignore, .vscode, .DS_Store, .mypy_cache, .pytest_cache, dist, build, .env, logs

5) Atualize o README.md conforme atualizacoes e boas praticas

Boas práticas mínimas:
- Usar python:3.11-slim, pip com --no-cache-dir.
- Não rodar como root.
- Bind mounts para hot-reload em dev (volumes mapeando o código).
- CORS já permite http://localhost:8501 no backend.
- Healthcheck no db; opcional no backend (ex.: curl http://localhost:8000/items?limit=1).

Validação esperada (Windows PowerShell):
- docker compose build
- docker compose up -d
- UI em http://localhost:8501 e API em

