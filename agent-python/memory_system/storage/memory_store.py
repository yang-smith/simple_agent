"""
简化的文件存储接口 - 使用文本文件存储记忆
"""
import os
import json
import hashlib
from typing import List, Optional, Any
from datetime import datetime

from ..Item import MemoryItem
from ..config import MemoryConfig


class MemoryStore:
    """简化的记忆存储接口"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        # 直接使用当前文件所在目录作为存储目录
        self.storage_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_short_term_memory(self, memory: MemoryItem) -> bool:
        """保存短期记忆到JSON文件"""
        try:
            file_path = os.path.join(self.storage_dir, f"short_term_{memory.user_id}.json")
            
            # 读取现有记忆
            memories = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
            
            # 添加新记忆
            memory_dict = {
                "id": memory.id,
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "hp": memory.hp
            }
            memories.append(memory_dict)
            
            # 保存回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存短期记忆失败: {e}")
            return False
    
    def get_short_term_memories(self, user_id: str) -> List[MemoryItem]:
        """获取短期记忆"""
        try:
            file_path = os.path.join(self.storage_dir, f"short_term_{user_id}.json")
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                memories_data = json.load(f)
            
            memories = []
            for data in memories_data:
                memory = MemoryItem(
                    id=data["id"],
                    content=data["content"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    hp=data["hp"],
                    user_id=user_id
                )
                memories.append(memory)
            
            # 按时间倒序排列
            memories.sort(key=lambda x: x.timestamp, reverse=True)
            return memories
            
        except Exception as e:
            print(f"读取短期记忆失败: {e}")
            return []
    
    def delete_short_term_memory(self, memory_id: str, user_id: str) -> bool:
        """删除短期记忆"""
        try:
            file_path = os.path.join(self.storage_dir, f"short_term_{user_id}.json")
            
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            # 过滤掉要删除的记忆
            memories = [m for m in memories if m["id"] != memory_id]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"删除短期记忆失败: {e}")
            return False
    
    def save_long_term_memory(self, user_id: str, cognitive_model: str) -> bool:
        """保存长期记忆认知模型"""
        try:
            file_path = os.path.join(self.storage_dir, f"long_term_{user_id}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cognitive_model)
            
            return True
            
        except Exception as e:
            print(f"保存长期记忆失败: {e}")
            return False
    
    def get_long_term_memory(self, user_id: str) -> str:
        """获取长期记忆认知模型"""
        try:
            file_path = os.path.join(self.storage_dir, f"long_term_{user_id}.txt")
            
            if not os.path.exists(file_path):
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"读取长期记忆失败: {e}")
            return ""
            
    def get_base_memory(self, user_id: str) -> str:
        """获取基础记忆 - 从长期记忆中提取基石和演化部分"""
        try:
            # 获取完整的长期记忆认知模型
            cognitive_model = self.get_long_term_memory(user_id)
            
            if not cognitive_model.strip():
                return ""
            
            # 提取基石模型部分
            bedrock_model = self._extract_section(cognitive_model, "Bedrock")
            
            # 提取演化模型部分
            evolutionary_model = self._extract_section(cognitive_model, "Evolutionary")
            
            # 拼接基础记忆
            base_memory = ""
            
            if bedrock_model:
                base_memory += f"<Bedrock>\n{bedrock_model}\n</Bedrock>"
            
            if evolutionary_model:
                if base_memory:
                    base_memory += "\n\n"
                base_memory += f"<Evolutionary>\n{evolutionary_model}\n</Evolutionary>"
            
            return base_memory
            
        except Exception as e:
            print(f"获取基础记忆失败: {e}")
            return ""
    
    def _extract_section(self, model: str, section_name: str) -> str:
        """从认知模型中提取特定章节"""
        import re
        pattern = f'<{section_name}>(.*?)</{section_name}>'
        match = re.search(pattern, model, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def count_short_term_memories(self, user_id: str) -> int:
        """统计短期记忆数量"""
        memories = self.get_short_term_memories(user_id)
        return len(memories)
    
    def get_oldest_short_term_memory(self, user_id: str) -> Optional[MemoryItem]:
        """获取最老的短期记忆"""
        memories = self.get_short_term_memories(user_id)
        if not memories:
            return None
        
        # 按时间正序排列，取第一个
        memories.sort(key=lambda x: x.timestamp)
        return memories[0]
    
    @staticmethod
    def hash_states(states: List[Any]) -> str:
        """生成states的哈希值"""
        states_str = json.dumps([str(state) for state in states], sort_keys=True, ensure_ascii=False)
        return hashlib.md5(states_str.encode()).hexdigest() 