"""
工具注册表 - 管理所有工具实例
"""

import json
from typing import Dict, List, Any
from .base import BaseTool

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        name = tool.get_name()
        self.tools[name] = tool
        print(f"已注册工具: {name}")
    
    def get_tool(self, name: str) -> BaseTool:
        """获取工具"""
        if name not in self.tools:
            raise ValueError(f"工具 '{name}' 未找到")
        return self.tools[name]
    
    def get_functions_xml(self) -> str:
        """生成 <functions> XML 块，用于 LLM 上下文"""
        functions_list = []
        
        for tool in self.tools.values():
            schema = tool.get_function_schema()
            # 转换为紧凑的 JSON 格式
            json_str = json.dumps(schema, ensure_ascii=False, separators=(',', ':'))
            functions_list.append(f"<function>{json_str}</function>")
        
        return f"<functions>\n{chr(10).join(functions_list)}\n</functions>"
    
    def parse_function_calls(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 响应中的 <function_calls> 块"""
        import re
        
        # 提取 function_calls 块
        function_calls_match = re.search(r'<function_calls>(.*?)</function_calls>', response, re.DOTALL)
        if not function_calls_match:
            return []
        
        function_calls_content = function_calls_match.group(1)
        
        # 提取所有 invoke 块
        invoke_matches = re.findall(r'<invoke name="([^"]+)">(.*?)</invoke>', function_calls_content, re.DOTALL)
        
        calls = []
        for tool_name, params_content in invoke_matches:
            # 解析参数
            param_matches = re.findall(r'<parameter name="([^"]+)">(.*?)</parameter>', params_content, re.DOTALL)
            parameters = {name: value.strip() for name, value in param_matches}
            
            calls.append({
                "tool_name": tool_name,
                "parameters": parameters
            })
        
        return calls
    
    def execute_function_calls(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用列表"""
        results = []
        
        for call in calls:
            tool_name = call["tool_name"]
            parameters = call["parameters"]
            
            try:
                tool = self.get_tool(tool_name)
                result = tool.execute(parameters)
                results.append({
                    "tool_name": tool_name,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool_name": tool_name,
                    "success": False,
                    "error": str(e)
                })
        
        return results 