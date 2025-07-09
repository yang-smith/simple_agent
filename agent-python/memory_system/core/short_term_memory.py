"""
短期记忆模块 - 负责处理和存储对话摘要
"""
from typing import List, Any, Optional
from datetime import datetime

from ..Item import MemoryItem
from ..storage.memory_store import MemoryStore
from ..utils.llm_adapter import LLMAdapter
from ..config import MemoryConfig


class ShortTermMemoryManager:
    """短期记忆管理器"""
    
    def __init__(self, config: MemoryConfig, store: MemoryStore, llm_adapter: LLMAdapter):
        self.config = config
        self.store = store
        self.llm_adapter = llm_adapter
    
    def process_states(self, states: List[Any], user_id: str, force_process: bool = False) -> Optional[MemoryItem]:
        """处理states，生成短期记忆"""
        if not states:
            return None
        
        # 估算token数量
        token_count = self.llm_adapter.estimate_token_count(states)
        
        # 如果不是强制处理，检查是否达到阈值
        if not force_process and token_count < self.config.STATES_TOKEN_THRESHOLD:
            print(f"Token数量({token_count})未达到阈值({self.config.STATES_TOKEN_THRESHOLD})")
            return None
        
        print(f"处理states: {len(states)}个事件, {token_count} tokens")
        
        # 生成摘要
        summary_content = self.llm_adapter.summarize_states(states)
        
        if not summary_content.strip():
            print("LLM摘要生成失败")
            return None
        
        print(f"summary_content: {summary_content}")
        
        # 创建短期记忆
        short_memory = MemoryItem(
            content=summary_content,
            timestamp=datetime.now(),
            hp=1,
            user_id=user_id
        )
        
        # 保存到存储
        if self.store.save_short_term_memory(short_memory):
            print(f"短期记忆已保存: {short_memory.id}")
            print(f"摘要: {summary_content[:100]}...")
            return short_memory
        else:
            print("短期记忆保存失败")
            return None
    
    def get_recent_memories(self, user_id: str, limit: int = None) -> List[MemoryItem]:
        """获取最近的短期记忆"""
        if limit is None:
            limit = self.config.SHORT_TERM_HOT_CACHE_SIZE
        
        memories = self.store.get_short_term_memories(user_id)
        return memories[:limit]
    
    def check_overflow(self, user_id: str) -> bool:
        """检查短期记忆是否超过数量限制"""
        count = self.store.count_short_term_memories(user_id)
        return count > self.config.SHORT_TERM_MAX_COUNT
    
    def get_oldest_memory(self, user_id: str) -> Optional[MemoryItem]:
        """获取最老的短期记忆（用于晋升）"""
        return self.store.get_oldest_short_term_memory(user_id)
    
    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除短期记忆"""
        return self.store.delete_short_term_memory(memory_id, user_id)
    
    def clear_user_memories(self, user_id: str):
        """清除用户的短期记忆"""
        try:
            import os
            file_path = os.path.join(self.store.storage_dir, f"short_term_{user_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"已清除用户 {user_id} 的短期记忆")
        except Exception as e:
            print(f"清除短期记忆失败: {e}")
    
    def get_oldest_memories_batch(self, user_id: str, batch_size: int) -> List[MemoryItem]:
        """获取最老的N条短期记忆（用于批量晋升）"""
        memories = self.store.get_short_term_memories(user_id)
        if not memories:
            return []
        
        # 按时间正序排列，取前N个
        memories.sort(key=lambda x: x.timestamp)
        return memories[:batch_size] 