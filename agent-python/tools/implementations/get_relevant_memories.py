"""
从记忆模块中获取相关记忆
"""

from typing import Dict, Any, List
import uuid
from ..base import BaseTool, ParameterSchema
from memory_system import get_relevant_memories

class GetRelevantMemoriesTool(BaseTool):
    """从记忆模块中获取相关记忆"""

    def get_name(self) -> str:
        return "get_relevant_memories"
    
    def get_description(self) -> str:
        return "从记忆模块中获取相关记忆。只有当用户说出\"你仔细想想\"、\"帮我回忆一下\"等明确的指令时，使用这个工具。"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="user_input",
                description="需要回忆的相关内容。用于去记忆模块查询。",
                type="string",
                required=True
            ),
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行获取相关记忆"""
        user_input = parameters.get("user_input", "").strip()
        
        if not user_input:
            return {
                "success": False,
                "error": "缺少必要参数：user_input"
            }
        
        try:
            # 获取相关记忆
            relevant_memories = get_relevant_memories(user_input)
            
            # 检查是否有记忆内容
            if not relevant_memories or relevant_memories == "[]":
                return {
                    "success": True,
                    "message": f"查询'{user_input}'没有找到相关记忆",
                    "query": user_input
                }
            
            return {
                "success": True,
                "message": f"查询'{user_input}'找到相关记忆: {relevant_memories}",
                "query": user_input
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取记忆失败: {str(e)}",
                "query": user_input
            }
