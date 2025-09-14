# App v0 - FastAPI + Streamlit (CRUD de Items)

Projeto mínimo para aulas: backend FastAPI com CRUD completo de `Item` persistido em Postgres via SQLAlchemy 2.0 e frontend Streamlit consumindo a API via HTTP.

## Pré-requisitos
- Python 3.11
- Postgres em execução e acessível.
- Criar um arquivo `.env` baseado em `.env.example` na raiz `app_v0/`.

```
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/appdb
API_HOST=127.0.0.1
API_PORT=8000
```

## Instalação

Windows PowerShell:
```
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```
(CMD tradicional: ` .\.venv\Scripts\activate.bat`)

Linux/macOS:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Subir banco no docker
docker run --name devops-postgres -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=appdb -p 5432:5432 -d postgres:16

## Executar Backend
```
uvicorn app_v0.backend.main:app --reload --host 127.0.0.1 --port 8000
```

## Executar Frontend
```
streamlit run app_v0/frontend/app.py
```

## Entidade Item
Campos:
- id: UUID
- title: str (obrigatório, não vazio)
- description: str | None
- status: enum (pending, in_progress, done) default pending
- created_at, updated_at: datetimes UTC

## Endpoints
- GET /items?limit=50&offset=0&status=
- GET /items/{id}
- POST /items (201)
- PUT /items/{id}
- DELETE /items/{id} (204)

Paginação: `limit <= 200`.

## Observação
Tabelas são criadas automaticamente no startup apenas para fins didáticos. Em produção usar Alembic.

## Notas
- Sem Docker, sem Alembic neste exemplo.
- Frontend nunca acessa o banco diretamente.
