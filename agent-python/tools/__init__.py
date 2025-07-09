"""
Tools 模块 - 提供简单统一的工具调用接口
"""

from .registry import ToolRegistry
from .tool_list import get_all_tools

# 全局工具注册表
_registry = None

def get_registry():
    """获取全局工具注册表（单例模式）"""
    global _registry
    if _registry is None:
        _registry = get_all_tools()
    return _registry

def execute_tool_call(tool_name: str, params: dict) -> dict:
    """
    执行工具调用的统一接口
    
    Args:
        tool_name: 工具名称
        params: 参数字典
        
    Returns:
        执行结果字典
    """
    try:
        registry = get_registry()
        tool = registry.get_tool(tool_name)
        return tool.execute(params)
    except Exception as e:
        return {
            "success": False,
            "error": f"工具调用失败: {str(e)}"
        }

def get_functions_xml() -> str:
    """获取工具定义的 XML 格式"""
    registry = get_registry()
    return registry.get_functions_xml()

def parse_and_execute_function_calls(llm_response: str) -> list:
    """
    解析 LLM 响应并执行工具调用
    
    Args:
        llm_response: LLM 的完整响应文本
        
    Returns:
        执行结果列表
    """
    registry = get_registry()
    calls = registry.parse_function_calls(llm_response)
    return registry.execute_function_calls(calls)

# 为了兼容现有代码，提供简单的工具函数
def check_availability_tool(params):
    """兼容函数：检查可用性"""
    return execute_tool_call("check_availability", params)

def book_room_tool(params):
    """兼容函数：预订房间"""
    return execute_tool_call("book_room", params)

def tell_user_tool(message):
    """兼容函数：告知用户"""
    return execute_tool_call("tell_user", {"message": message})
