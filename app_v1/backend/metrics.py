import time
from typing import Callable

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app

# Observação: usar o caminho bruto (request.url.path) como label pode causar alta cardinalidade
# quando há IDs dinâmicos (ex.: /items/123). Para fins didáticos, usaremos o path literal.
# Em produção, normalize para padrões de rota (ex.: /items/{id}) ou use middlewares que exponham
# nomes de rotas para reduzir cardinalidade.

# Métricas globais
http_requests_total = Counter(
    "http_requests_total",
    "Total de requisições HTTP",
    labelnames=["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    labelnames=["method", "path"],
    # Buckets sugeridos para APIs web (extras do enunciado)
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Requisições HTTP em andamento",
    labelnames=["method", "path"],
)

http_exceptions_total = Counter(
    "http_exceptions_total",
    "Total de exceções levantadas por requisição",
    labelnames=["method", "path", "exception_type"],
)


def setup_metrics(app: FastAPI) -> None:
    """Configura middleware de métricas e expõe /metrics.

    - Contabiliza requests por método, path e status_code.
    - Mede duração em histogram por método e path.
    - Gauge de requisições em progresso.
    - Contador de exceções por tipo.
    - Monta endpoint /metrics via make_asgi_app (content-type do Prometheus).
    """

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):  # type: ignore[override]
        method = request.method
        path = request.url.path
        start = time.perf_counter()

        # In-progress + duração
        http_requests_in_progress.labels(method=method, path=path).inc()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = int(getattr(response, "status_code", 500))
            return response
        except Exception as exc:  # noqa: BLE001 - contamos exceções genéricas para métricas
            # Conta exceções por tipo
            http_exceptions_total.labels(
                method=method, path=path, exception_type=exc.__class__.__name__
            ).inc()
            # Repropaga após marcar; FastAPI tratará e retornará 500
            raise
        finally:
            duration = time.perf_counter() - start
            http_request_duration_seconds.labels(method=method, path=path).observe(duration)
            http_requests_in_progress.labels(method=method, path=path).dec()
            http_requests_total.labels(
                method=method, path=path, status_code=str(status_code)
            ).inc()

    # Expor /metrics (Prometheus exposition format - text/plain; version 0.0.4)
    app.mount("/metrics", make_asgi_app())
