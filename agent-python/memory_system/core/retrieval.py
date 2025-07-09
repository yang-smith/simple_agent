"""
检索模块 - 实现"闪念"(Reflexive Recall)和"深思"(Deep Thought)两种检索逻辑
"""
import re
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..Item import MemoryItem
from .short_term_memory import ShortTermMemoryManager
from .long_term_memory import LongTermMemoryManager
from ..utils.llm_adapter import LLMAdapter
from ..config import MemoryConfig


class MemoryRetriever:
    """记忆检索器"""
    
    def __init__(self, config: MemoryConfig, short_term_mgr: ShortTermMemoryManager, 
                 long_term_mgr: LongTermMemoryManager, llm_adapter: LLMAdapter):
        self.config = config
        self.short_term_mgr = short_term_mgr
        self.long_term_mgr = long_term_mgr
        self.llm_adapter = llm_adapter
    
    def reflexive_recall(self, query: str, user_id: str) -> List[MemoryItem]:
        """闪念检索 - 系统1：直觉反应，极简快速"""
        if not query.strip():
            return []
        
        print(f"闪念检索: {query[:50]}...")
        
        # 只从短期记忆中检索
        short_memories = self.short_term_mgr.get_recent_memories(user_id, limit=20)  # 获取更多候选
        
        if not short_memories:
            print("没有短期记忆可检索")
            return []
        
        # 计算关键词匹配得分
        candidates = []
        for memory in short_memories:
            score = self._calculate_keyword_score(query, memory.content)
            if score > 0:  # 只要有匹配就加入候选
                candidates.append((score, memory))
        
        # 按得分排序，取前3个
        candidates.sort(key=lambda x: x[0], reverse=True)
        results = [memory for score, memory in candidates[:3]]
        
        print(f"闪念检索完成，找到 {len(results)} 条相关记忆")
        return results
    
    def deep_thought(self, query: str, user_id: str) -> List[MemoryItem]:
        """深思检索 - 系统2：全面搜索长期记忆"""
        if not query.strip():
            return []
        
        print(f"深度检索: {query[:50]}...")
        
        # 获取查询向量
        query_embedding = self.llm_adapter.get_text_embedding(query)
        if not query_embedding:
            return []
        
        candidates = []
        
        # 1. 搜索所有长期记忆
        all_long_memories = self.long_term_mgr.get_all_memories(user_id)
        for memory in all_long_memories:
            if memory.embedding:
                score = self._calculate_combined_score(query, query_embedding, memory)
                if score >= self.config.RELEVANCE_THRESHOLD:
                    candidates.append((score, memory))
        
        # 2. 也包含短期记忆（完整搜索）
        short_memories = self.short_term_mgr.get_recent_memories(user_id, limit=20)  # 扩大范围
        for memory in short_memories:
            if memory.embedding:
                score = self._calculate_combined_score(query, query_embedding, memory)
                if score >= self.config.RELEVANCE_THRESHOLD:
                    candidates.append((score, memory))
        
        # 3. 按分数排序，取前N个
        candidates.sort(key=lambda x: x[0], reverse=True)
        results = [memory for score, memory in candidates[:self.config.DEEP_SEARCH_LIMIT]]
        
        
        print(f"深度检索完成，找到 {len(results)} 条相关记忆")
        return results
    
    def _calculate_combined_score(self, query: str, query_embedding: List[float], 
                                memory: MemoryItem) -> float:
        """计算组合评分：关键词检索 * 0.5 + 向量检索 * 0.5"""
        
        # 1. 关键词评分
        keyword_score = self._calculate_keyword_score(query, memory.content)
        
        # 2. 向量相似度评分
        vector_score = self._calculate_vector_score(query_embedding, memory.embedding)
        
        # 3. 组合评分
        combined_score = (keyword_score * self.config.KEYWORD_WEIGHT + 
                         vector_score * self.config.VECTOR_WEIGHT)
        
        return combined_score
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """计算关键词匹配评分 - 简化版"""
        # 简单的关键词匹配
        query_words = set(re.findall(r'\w+', query.lower()))
        content_words = set(re.findall(r'\w+', content.lower()))
        
        if not query_words:
            return 0.0
        
        # 计算交集比例
        intersection = query_words.intersection(content_words)
        
        if not intersection:
            return 0.0
        
        # 简单的匹配得分：匹配词数 / 查询词数
        score = len(intersection) / len(query_words)
        
        # 额外加分：完整短语匹配
        phrase_bonus = 0.0
        for word in query_words:
            if word in content.lower():
                phrase_bonus += 0.1
        
        return score + phrase_bonus
    
    def _calculate_vector_score(self, query_embedding: List[float], 
                              memory_embedding: List[float]) -> float:
        """计算向量相似度评分"""
        try:
            query_vec = np.array(query_embedding).reshape(1, -1)
            memory_vec = np.array(memory_embedding).reshape(1, -1)
            
            similarity = cosine_similarity(query_vec, memory_vec)[0][0]
            return max(0.0, similarity)  # 确保非负
            
        except Exception as e:
            print(f"向量相似度计算失败: {e}")
            return 0.0
    
 