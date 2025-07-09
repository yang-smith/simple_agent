"""
工具列表 - 中心化管理所有可用工具
这个文件是工具系统的"目录"，main.py 只需要导入这里即可
"""

from .registry import ToolRegistry
from .implementations.availability import CheckAvailabilityTool
from .implementations.booking import BookRoomTool  
from .implementations.communication import TellUserTool
from .implementations.get_relevant_memories import GetRelevantMemoriesTool
from .implementations.web_search import WebSearchTool

def get_all_tools() -> ToolRegistry:
    """
    获取包含所有工具的注册表
    """
    registry = ToolRegistry()
    
    # 注册所有工具
    # registry.register(CheckAvailabilityTool())
    # registry.register(BookRoomTool())
    # registry.register(TellUserTool())
    registry.register(GetRelevantMemoriesTool())
    registry.register(WebSearchTool())
    
    return registry

def get_functions_xml() -> str:
    """
    获取 <functions> XML 块，用于 LLM 上下文
    """
    registry = get_all_tools()
    return registry.get_functions_xml() 