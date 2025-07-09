"""
从网络中搜索相关信息
"""

from typing import Dict, Any, List
import uuid
from ..base import BaseTool, ParameterSchema
from llm.llm_client import llm_call

class WebSearchTool(BaseTool):
    """从网络中搜索相关信息"""

    def get_name(self) -> str:
        return "web_search"
    
    def get_description(self) -> str:
        return "从网络中搜索相关信息。当用户明确需要外部检索时或者你的知识库里明确没有相关信息时候，使用这个工具。"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="search_input",
                description="需要搜索的相关内容。用于去网络查询。",
                type="string",
                required=True
            ),
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行网络搜索"""
        search_input = parameters.get("search_input", "").strip()
        
        if not search_input:
            return {
                "success": False,
                "error": "缺少必要参数：search_input"
            }
        
        try:
            result = llm_call(search_input,model="perplexity/sonar") # 使用perplexity/sonar模型进行网络搜索
            return {
                "success": True,
                "message": result,
                "query": search_input
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"网络搜索失败: {str(e)}",
                "query": search_input
            }
