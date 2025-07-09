"""
记忆系统的数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import uuid4


@dataclass
class MemoryItem:
    """统一的记忆条目"""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    embedding: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    hp: int = 1  # 保留HP字段用于兼容性
    user_id: str = ""