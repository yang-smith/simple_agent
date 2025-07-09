"""
长期记忆模块 - AI的自适应认知模型
"""
from typing import List, Optional
from datetime import datetime

from ..storage.memory_store import MemoryStore
from ..utils.llm_adapter import LLMAdapter
from ..config import MemoryConfig
from ..Item import MemoryItem


class LongTermMemoryManager:
    """长期记忆管理器 - 自适应认知模型"""
    
    def __init__(self, config: MemoryConfig, store: MemoryStore, llm_adapter: LLMAdapter):
        self.config = config
        self.store = store
        self.llm_adapter = llm_adapter
    
    def cognitive_reconstruction(self, user_id: str, short_memory: MemoryItem) -> bool:
        """认知重构 - 核心机制"""
        try:
            print(f"开始认知重构: {user_id}")
            
            # 获取当前认知模型
            current_model = self.store.get_long_term_memory(user_id)
            
            if not current_model.strip():
                # 初始化认知模型
                current_model = self._initialize_cognitive_model()
            
            # 构建带时间信息的新刺激
            timestamp_str = short_memory.timestamp.strftime("%Y年%m月%d日 %H:%M")
            new_stimuli_with_time = f"[{timestamp_str}] {short_memory.content}"
            
            # 执行认知重构
            new_model = self.llm_adapter.cognitive_reconstruction(current_model, new_stimuli_with_time)
            
            if new_model.strip():
                # 原子性替换
                success = self.store.save_long_term_memory(user_id, new_model)
                if success:
                    print(f"认知重构完成: {user_id} (时间: {timestamp_str})")
                    print(f"新模型长度: {len(new_model)} 字符")
                    return True
                else:
                    print("认知模型保存失败")
                    return False
            else:
                print("LLM未生成有效的认知模型")
                return False
                
        except Exception as e:
            print(f"认知重构失败: {e}")
            return False
    
    def cognitive_reconstruction_batch(self, user_id: str, combined_content: str) -> bool:
        """批量认知重构 - 处理多条短期记忆"""
        try:
            print(f"开始批量认知重构: {user_id}")
            
            # 获取当前认知模型
            current_model = self.store.get_long_term_memory(user_id)
            
            if not current_model.strip():
                # 初始化认知模型
                current_model = self._initialize_cognitive_model()
            
            # 执行认知重构
            new_model = self.llm_adapter.cognitive_reconstruction(current_model, combined_content)
            
            if new_model.strip():
                # 原子性替换
                success = self.store.save_long_term_memory(user_id, new_model)
                if success:
                    print(f"批量认知重构完成: {user_id}")
                    print(f"新模型长度: {len(new_model)} 字符")
                    return True
                else:
                    print("认知模型保存失败")
                    return False
            else:
                print("LLM未生成有效的认知模型")
                return False
                
        except Exception as e:
            print(f"批量认知重构失败: {e}")
            return False
    
    def get_cognitive_model(self, user_id: str) -> str:
        """获取完整认知模型"""
        return self.store.get_long_term_memory(user_id)
    
    def get_bedrock_model(self, user_id: str) -> str:
        """提取基石模型部分"""
        model = self.get_cognitive_model(user_id)
        return self._extract_section(model, "Bedrock")
    
    def get_evolutionary_model(self, user_id: str) -> str:
        """提取演化模型部分"""
        model = self.get_cognitive_model(user_id)
        return self._extract_section(model, "Evolutionary")
    
    def get_dynamic_model(self, user_id: str) -> str:
        """提取动态模型部分"""
        model = self.get_cognitive_model(user_id)
        return self._extract_section(model, "Dynamic")
    
    def _extract_section(self, model: str, section_name: str) -> str:
        """从认知模型中提取特定章节"""
        import re
        pattern = f'<{section_name}>(.*?)</{section_name}>'
        match = re.search(pattern, model, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _initialize_cognitive_model(self) -> str:
        """初始化空的认知模型结构"""
        return """<Bedrock>

</Bedrock>

<Evolutionary>

</Evolutionary>

<Dynamic>

</Dynamic>"""
    
    def clear_user_memories(self, user_id: str):
        """清除用户的长期记忆"""
        try:
            import os
            file_path = os.path.join(self.store.storage_dir, f"long_term_{user_id}.txt")
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"已清除用户 {user_id} 的长期记忆")
        except Exception as e:
            print(f"清除长期记忆失败: {e}") 