"""
通信工具
"""

from typing import Dict, Any, List
from ..base import BaseTool, ParameterSchema

class TellUserTool(BaseTool):
    """向用户发送消息工具"""
    
    def get_name(self) -> str:
        return "tell_user"
    
    def get_description(self) -> str:
        return "向用户发送消息或回复"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="message",
                description="要发送给用户的消息内容",
                type="string",
                required=True
            ),
            ParameterSchema(
                name="message_type",
                description="消息类型",
                type="string",
                required=False,
                enum=["info", "success", "warning", "error"],
                default="info"
            )
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行消息发送"""
        message = parameters.get("message", "").strip()
        message_type = parameters.get("message_type", "info").strip()
        
        if not message:
            return {
                "success": False,
                "error": "消息内容不能为空"
            }
        
        # 根据消息类型添加前缀
        type_prefixes = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌"
        }
        
        prefix = type_prefixes.get(message_type, "🤖")
        print(f"\n{prefix} Agent: {message}")
        
        return {
            "success": True,
            "message": message,
            "message_type": message_type,
            "sent_at": "now"
        } 