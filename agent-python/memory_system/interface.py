"""
记忆系统的干净外部接口
"""
from typing import List, Any
from datetime import datetime

from .config import MemoryConfig, DEFAULT_CONFIG
from .storage.memory_store import MemoryStore
from .utils.llm_adapter import LLMAdapter
from .core.short_term_memory import ShortTermMemoryManager
from .core.long_term_memory import LongTermMemoryManager
from .core.retrieval import MemoryRetriever
from .Item import MemoryItem


class MemorySystem:
    """记忆系统主接口"""
    
    def __init__(self, config: MemoryConfig = None, llm_client=None):
        self.config = config or DEFAULT_CONFIG
        
        # 初始化组件
        self.store = MemoryStore(self.config)
        self.llm_adapter = LLMAdapter(llm_client)
        self.short_term_mgr = ShortTermMemoryManager(self.config, self.store, self.llm_adapter)
        self.long_term_mgr = LongTermMemoryManager(self.config, self.store, self.llm_adapter)
        self.retriever = MemoryRetriever(self.config, self.short_term_mgr, self.long_term_mgr, self.llm_adapter)
        
        print("记忆系统初始化完成")
    
    def get_relevant_memories(self, user_input: str, user_id: str = "default") -> str:
        """
        读取接口：获取相关记忆用于context
        从短期记忆和长期记忆Dynamic部分检索，返回分数最高的3个部分
        """
        if not user_input.strip():
            return ""
        
        try:
            candidates = []
            
            # 1. 从短期记忆中检索
            short_memories = self.short_term_mgr.get_recent_memories(user_id, limit=20)
            
            for memory in short_memories:
                score = self._calculate_keyword_score(user_input, memory.content)
                if score > 0:
                    candidates.append((score, memory.content, "短期记忆"))
            
            # 2. 从长期记忆的Dynamic部分检索
            dynamic_model = self.long_term_mgr.get_dynamic_model(user_id)
            
            if dynamic_model.strip():
                # 按照两个换行符分割Dynamic部分
                dynamic_sections = [section.strip() for section in dynamic_model.split('\n\n') if section.strip()]
                
                for section in dynamic_sections:
                    score = self._calculate_keyword_score(user_input, section)
                    if score > 0:
                        candidates.append((score, section, "长期记忆Dynamic"))
            
            # 3. 按分数排序，取前3个
            if not candidates:
                return ""
            
            candidates.sort(key=lambda x: x[0], reverse=True)
            top_3 = candidates[:3]
            
            # 4. 格式化返回结果
            memory_strings = []
            for score, content, source in top_3:
                memory_strings.append(content)
            
            return str(memory_strings)
            
        except Exception as e:
            print(f"记忆检索失败: {e}")
            return ""
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """计算关键词匹配评分 - 使用TF-IDF"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import jieba
            import re
            
            # 预处理：分词
            def preprocess_text(text):
                # 英文分词
                english_words = re.findall(r'[a-zA-Z]+', text.lower())
                # 中文分词
                chinese_text = re.sub(r'[a-zA-Z0-9\s]+', '', text)
                chinese_words = list(jieba.cut(chinese_text))
                # 过滤停用词和短词
                chinese_words = [word for word in chinese_words if len(word) > 1 and word.strip()]
                
                return ' '.join(english_words + chinese_words)
            
            # 预处理文本
            processed_query = preprocess_text(query)
            processed_content = preprocess_text(content)
            
            if not processed_query.strip() or not processed_content.strip():
                return 0.0
            
            # 使用TF-IDF计算相似度
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),  # 使用1-2gram
                max_features=1000,   # 限制特征数量
                lowercase=True
            )
            
            # 构建语料库
            corpus = [processed_query, processed_content]
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # 计算余弦相似度
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return max(0.0, similarity)
            
        except ImportError:
            # 如果没有安装依赖，使用简单匹配
            return self._simple_keyword_score(query, content)
        except Exception as e:
            # 计算失败时使用简单匹配
            return self._simple_keyword_score(query, content)
    
    def _simple_keyword_score(self, query: str, content: str) -> float:
        """简单关键词匹配评分 - 备用方案"""
        import re
        
        # 对中文和英文都进行处理
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 英文单词匹配
        query_words = set(re.findall(r'[a-zA-Z]+', query_lower))
        content_words = set(re.findall(r'[a-zA-Z]+', content_lower))
        
        # 中文字符匹配（2-3字组合）
        query_chars = set()
        content_chars = set()
        
        # 提取中文字符组合
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', query)
        if len(chinese_chars) >= 2:
            for i in range(len(chinese_chars) - 1):
                query_chars.add(chinese_chars[i] + chinese_chars[i+1])
                if i < len(chinese_chars) - 2:
                    query_chars.add(chinese_chars[i] + chinese_chars[i+1] + chinese_chars[i+2])
        
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        if len(chinese_chars) >= 2:
            for i in range(len(chinese_chars) - 1):
                content_chars.add(chinese_chars[i] + chinese_chars[i+1])
                if i < len(chinese_chars) - 2:
                    content_chars.add(chinese_chars[i] + chinese_chars[i+1] + chinese_chars[i+2])
        
        # 计算匹配得分
        total_query_terms = len(query_words) + len(query_chars)
        if total_query_terms == 0:
            return 0.0
        
        # 英文匹配
        word_intersection = query_words.intersection(content_words)
        # 中文匹配
        char_intersection = query_chars.intersection(content_chars)
        
        total_matches = len(word_intersection) + len(char_intersection)
        
        if total_matches == 0:
            return 0.0
        
        # 基础得分
        score = total_matches / total_query_terms
        
        # 额外加分：完整短语匹配
        phrase_bonus = 0.0
        if query_lower in content_lower:
            phrase_bonus += 0.3
        
        return score + phrase_bonus
    
    def update_memory(self, states: List[Any], user_id: str = "default", force_process: bool = False):
        """
        写入接口：处理新的states，更新记忆
        启动短期记忆存储与长期记忆晋升判断
        
        Args:
            states: 对话状态列表
            user_id: 用户标识
            force_process: 是否强制处理（忽略token阈值）
        """
        if not states:
            return
        
        try:
            # 1. 处理states，生成短期记忆摘要
            short_memory = self.short_term_mgr.process_states(states, user_id, force_process)
            
            if short_memory:
                # 2. 检查是否需要认知重构
                self._check_and_reconstruct(user_id)
                
        except Exception as e:
            print(f"更新记忆失败: {e}")
    
    def _check_and_reconstruct(self, user_id: str):
        """检查并执行认知重构"""
        try:
            # 检查短期记忆是否超过数量限制
            if self.short_term_mgr.check_overflow(user_id):
                print(f"用户 {user_id} 短期记忆超过限制，开始批量认知重构...")
                
                # 批量获取最老的短期记忆
                batch_memories = self.short_term_mgr.get_oldest_memories_batch(user_id, self.config.PROMOTION_BATCH_SIZE)
                
                if batch_memories:
                    print(f"准备晋升 {len(batch_memories)} 条短期记忆")
                    
                    # 合并多条记忆的内容和时间信息
                    combined_content = self._combine_memories_for_reconstruction(batch_memories)
                    
                    # 执行认知重构
                    success = self.long_term_mgr.cognitive_reconstruction_batch(user_id, combined_content)
                    
                    # 删除已处理的短期记忆
                    for memory in batch_memories:
                        self.short_term_mgr.delete_memory(memory.id, user_id)
                    
                    if success:
                        print(f"批量认知重构完成: {len(batch_memories)} 条记忆已处理")
                    else:
                        print(f"认知重构失败，但已删除 {len(batch_memories)} 条短期记忆")
                    
                    # 递归检查是否还需要继续重构
                    if self.short_term_mgr.check_overflow(user_id):
                        self._check_and_reconstruct(user_id)
            
        except Exception as e:
            print(f"认知重构检查失败: {e}")
    
    def _combine_memories_for_reconstruction(self, memories: List[MemoryItem]) -> str:
        """合并多条记忆为认知重构的输入"""
        combined_parts = []
        
        for memory in memories:
            timestamp_str = memory.timestamp.strftime("%Y年%m月%d日 %H:%M")
            combined_parts.append(f"[{timestamp_str}] {memory.content}")
        
        return "\n\n".join(combined_parts) 


    def get_base_memory(self, user_id: str = "default") -> str:
        """
        获取基础记忆
        """
        return self.store.get_base_memory(user_id)