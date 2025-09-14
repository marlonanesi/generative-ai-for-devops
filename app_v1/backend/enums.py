from __future__ import annotations

from enum import Enum

class Status(str, Enum):
    pending = 'pending'
    in_progress = 'in_progress'
    done = 'done'
