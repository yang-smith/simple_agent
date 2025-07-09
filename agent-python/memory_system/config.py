"""
记忆系统配置
"""
from dataclasses import dataclass


@dataclass
class MemoryConfig:
    """记忆系统配置参数"""
    
    # 触发阈值
    STATES_TOKEN_THRESHOLD: int = 80000  # 80k token触发摘要
    SHORT_TERM_MAX_COUNT: int = 50       # 短期记忆最大数量
    
    # 晋升参数
    PROMOTION_BATCH_SIZE: int = 3        # 每次晋升处理的短期记忆数量
    
    # 容量限制
    SHORT_TERM_HOT_CACHE_SIZE: int = 5    # 短期记忆热缓存最多5条
    
    
    # 检索参数
    RELEVANCE_THRESHOLD: float = 0.6      # 相关性阈值
    MAX_MEMORIES_IN_CONTEXT: int = 3      # 上下文中最多包含3条记忆
    DEEP_SEARCH_LIMIT: int = 20           # 深度搜索最多返回20条
    
    # 检索权重 (关键词 + 向量化)
    KEYWORD_WEIGHT: float = 0.5           # 关键词检索权重
    VECTOR_WEIGHT: float = 0.5            # 向量检索权重
    


# 默认配置实例
DEFAULT_CONFIG = MemoryConfig() 