# Steam Price Tracker

![CI](https://github.com/AndersonGabrielBD/steam-price-tracker/actions/workflows/ci.yml/badge.svg)

Rastreador de preços de jogos da Steam **em reais (R$)**, com histórico de preço e atualização ao vivo via WebSocket. Preços reais cobrados pela Steam no Brasil (não conversão por câmbio) — a consulta usa `cc=br` na API da Steam.

## Como funciona

```
Celery Beat (a cada N min)
        │
        ▼
Celery Worker ──► Steam Store API (cc=br) ──► preço mudou? ──► PostgreSQL (histórico)
        │                                                              │
        └──────────────────► Redis pub/sub ──────────────────► FastAPI ──► WebSocket ──► React (gráfico ao vivo)
```

- **FastAPI**: API REST para adicionar/listar jogos e consultar histórico de preço, com WebSocket para push de atualizações. Docs automáticas em `/docs`.
- **Celery + Redis**: job periódico (Celery Beat) dispara uma task por jogo rastreado; cada task consulta a Steam, compara com o último preço salvo (dedup/idempotência: só grava se mudou) e publica o evento no Redis se o preço mudar. Falhas de rede na Steam acionam retry com backoff exponencial.
- **PostgreSQL**: histórico de preços como série temporal (`price_history`), indexado por jogo + data.
- **Frontend (React + Recharts)**: busca jogo por nome ou appid, lista jogos rastreados com preço atual, gráfico de histórico que atualiza sozinho quando um preço muda (sem dar refresh).

## Rodando com Docker

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Rodando localmente sem Docker

**Backend** (precisa de PostgreSQL e Redis rodando):

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
cp ../.env.example .env        # ajuste DATABASE_URL/REDIS_URL para localhost
uvicorn app.main:app --reload
```

Em outros dois terminais, dentro de `backend/` com o venv ativo:

```bash
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
pytest -q       # 17 testes, mockando a API da Steam (não bate na Steam de verdade)
ruff check .
```

## Stack

Python · FastAPI · Celery · Redis · PostgreSQL · SQLAlchemy · pytest · Docker · React · Vite · Recharts · GitHub Actions
