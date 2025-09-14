from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from pythonjsonlogger import jsonlogger

try:
    from opensearchpy import OpenSearch, helpers  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    OpenSearch = None  # type: ignore
    helpers = None  # type: ignore


# ---- JSON formatter -------------------------------------------------------

class UtcIsoTimeFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:  # noqa: D401
        super().add_fields(log_record, record, message_dict)
        # Normalize timestamp and basic fields
        if 'timestamp' not in log_record:
            ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
            log_record['timestamp'] = ts
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        # "message" already set by base class; ensure it's a string
        if 'message' in log_record and not isinstance(log_record['message'], str):
            log_record['message'] = str(log_record['message'])


# ---- OpenSearch async handler ---------------------------------------------

class OpenSearchHandler(logging.Handler):
    """Non-blocking handler that ships logs to OpenSearch in background.

    Env vars:
      - OPENSEARCH_ENABLED (bool)
      - OPENSEARCH_HOST (default: opensearch)
      - OPENSEARCH_PORT (default: 9200)
      - OPENSEARCH_SCHEME (default: http)
      - OPENSEARCH_USER (optional)
      - OPENSEARCH_PASSWORD (optional)
      - OPENSEARCH_INDEX (default: logs-app-v1)
    """

    def __init__(self, level: int = logging.INFO) -> None:
        super().__init__(level)
        self.enabled = os.getenv('OPENSEARCH_ENABLED', 'false').lower() == 'true'
        self.host = os.getenv('OPENSEARCH_HOST', 'opensearch')
        self.port = int(os.getenv('OPENSEARCH_PORT', '9200'))
        self.scheme = os.getenv('OPENSEARCH_SCHEME', 'http')
        self.username = os.getenv('OPENSEARCH_USER') or None
        self.password = os.getenv('OPENSEARCH_PASSWORD') or None
        self.index = os.getenv('OPENSEARCH_INDEX', 'logs-app-v1')

        self._q: 'queue.Queue[Dict[str, Any]]' = queue.Queue(maxsize=10000)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._client = None
        if self.enabled and OpenSearch is not None:
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            url = f"{self.scheme}://{self.host}:{self.port}"
            self._client = OpenSearch(
                hosts=[url],
                http_auth=auth,
                timeout=5,
                max_retries=2,
                retry_on_timeout=True,
            )
            self._thread = threading.Thread(target=self._worker, name='os-logger', daemon=True)
            self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            if not self.enabled or self._client is None:
                # Fallback: just print to stdout via base handler-less behavior
                return
            # Expect record.msg to be JSON already via formatter; but we push dict
            msg = self.format(record)
            obj = json.loads(msg)
            self._q.put_nowait(obj)
        except Exception:
            # Fallback: swallow errors to not break app
            pass

    def _worker(self) -> None:
        assert helpers is not None
        backoff = 0.5
        while not self._stop.is_set():
            batch: List[Dict[str, Any]] = []
            try:
                # Drain quickly, up to 500 docs or 1s
                start = time.time()
                while len(batch) < 500 and (time.time() - start) < 1.0:
                    try:
                        item = self._q.get(timeout=0.2)
                        batch.append(item)
                    except queue.Empty:
                        break
                if not batch:
                    continue
                actions = (
                    {"_index": self.index, "_source": doc} for doc in batch
                )
                helpers.bulk(self._client, actions, refresh=False, raise_on_error=False)
                backoff = 0.5
            except Exception:
                # Light backoff and requeue
                for doc in batch:
                    try:
                        self._q.put_nowait(doc)
                    except queue.Full:
                        break
                time.sleep(backoff)
                backoff = min(backoff * 2, 10.0)

    def close(self) -> None:  # noqa: D401
        try:
            self._stop.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            super().close()


# ---- Setup logging ---------------------------------------------------------

STANDARD_FIELDS = [
    'timestamp', 'level', 'logger', 'message',
    'request_id', 'method', 'path', 'status_code',
    'duration_ms', 'client_ip', 'user_agent'
]


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root and relevant loggers with JSON format + OpenSearch handler."""
    fmt = UtcIsoTimeFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(level)

    os_handler = OpenSearchHandler(level=level)
    os_handler.setFormatter(fmt)

    # Root logger
    logging.basicConfig(level=level, handlers=[stream_handler, os_handler])

    # Align key loggers to same level and handlers
    for name in ['uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi', 'sqlalchemy.engine']:
        logger = logging.getLogger(name)
        logger.handlers = [stream_handler, os_handler]
        logger.setLevel(level)
        logger.propagate = False

    # Reduce noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
