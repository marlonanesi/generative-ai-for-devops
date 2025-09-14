from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os



# Tenta carregar .env da raiz do projeto e da pasta backend, mas não exige
from pathlib import Path
base_dir = Path(__file__).resolve().parent.parent.parent.parent
env_root = base_dir / '.env'
env_backend = Path(__file__).resolve().parent / '.env'
if env_root.exists():
    load_dotenv(dotenv_path=env_root, override=False)
elif env_backend.exists():
    load_dotenv(dotenv_path=env_backend, override=False)


class Settings:
    def __init__(self) -> None:
        self.DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
        self.API_HOST: str = os.getenv('API_HOST', '127.0.0.1')
        self.API_PORT: int = int(os.getenv('API_PORT', '8000'))
        if not self.DATABASE_URL:
            raise RuntimeError('DATABASE_URL não definido. Configure via variável de ambiente ou .env.')

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
