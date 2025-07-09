"""
工具基类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ParameterSchema:
    """参数模式定义"""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

class BaseTool(ABC):
    """工具基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取工具名称"""
        pass
    
    @abstractmethod 
    def get_description(self) -> str:
        """获取工具描述"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[ParameterSchema]:
        """获取参数定义"""
        pass
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具
        
        Args:
            parameters: 解析后的参数字典
            
        Returns:
            执行结果字典
        """
        pass
    
    def get_function_schema(self) -> Dict[str, Any]:
        """生成 JSONSchema 格式的工具定义"""
        parameters = self.get_parameters()
        
        # 构建 properties
        properties = {}
        required = []
        
        for param in parameters:
            prop_def = {
                "description": param.description,
                "title": param.name.title(),
                "type": param.type
            }
            
            if param.enum:
                prop_def["enum"] = param.enum
            
            if param.default is not None:
                prop_def["default"] = param.default
                
            properties[param.name] = prop_def
            
            if param.required:
                required.append(param.name)
        
        return {
            "description": self.get_description(),
            "name": self.get_name(),
            "parameters": {
                "additionalProperties": False,
                "properties": properties,
                "required": required,
                "title": f"{self.get_name().title()}Params",
                "type": "object"
            }
        }

    def parse_params(self, params: str) -> Dict[str, Any]:
        """解析参数 - 子类可以重写此方法来自定义参数解析"""
        # 默认实现：简单的键值对解析
        result = {}
        if not params.strip():
            return result
            
        # 简单解析，实际可以更复杂
        lines = params.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result 