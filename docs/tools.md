

# Tools 系统设计文档 v2.0

## 1. 系统概述

基于简化的 Agent 架构设计的 Tools 系统，采用事件驱动和状态机模式。系统遵循"LLM 作为无状态函数"的核心理念，通过标准化的工具接口和 XML 格式调用，实现模块化的功能扩展。

## 2. 设计哲学

### 2.1 核心原则
- **简约至上**: 最小化复杂度，保持代码清晰
- **标准化接口**: 统一的工具定义和调用规范
- **事件驱动**: 工具调用结果作为事件进入状态流
- **XML 原生**: 使用对 LLM 友好的 XML 格式而非 JSON

### 2.2 架构思想
```
State → Context Builder → LLM → Tool Calls → New State
  ↑                                              ↓
  ← ← ← ← ← Reducer ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

## 3. 当前架构状态

### 3.1 文件结构
```
test-agent/
├── main.py              # 简化的主循环 (39 lines)
├── core/                # 核心组件
│   ├── agent.py         # Agent 主循环逻辑
│   ├── state.py         # 状态管理和事件系统
│   └── context.py       # 上下文构建器
├── tools/               # 工具系统
│   ├── __init__.py      # 统一入口和简化接口
│   ├── base.py          # 工具基类定义
│   ├── registry.py      # 工具注册表和解析器
│   ├── tool_list.py     # 中心化工具管理
│   └── implementations/ # 具体工具实现
└── llm/                 # LLM 客户端模块
```


## 4. Tools 系统核心设计

### 4.1 工具基类架构

```python
# tools/base.py
@dataclass
class ParameterSchema:
    """参数定义标准"""
    name: str
    description: str
    type: str = "string"           # JSON Schema 类型
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

class BaseTool(ABC):
    """工具统一接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """工具唯一标识符"""
        
    @abstractmethod
    def get_description(self) -> str:
        """工具功能描述，用于 LLM 理解"""
        
    @abstractmethod
    def get_parameters(self) -> List[ParameterSchema]:
        """参数定义列表"""
        
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """工具执行逻辑"""
        
    def get_function_schema(self) -> Dict[str, Any]:
        """自动生成 JSON Schema 定义"""
```

### 4.2 工具注册表设计

```python
# tools/registry.py
class ToolRegistry:
    """工具生命周期管理器"""
    
    def register(self, tool: BaseTool) -> None:
        """注册工具到系统"""
        
    def get_functions_xml(self) -> str:
        """生成标准 <functions> XML 块"""
        
    def parse_function_calls(self, response: str) -> List[Dict]:
        """解析 LLM 响应中的工具调用"""
        
    def execute_function_calls(self, calls: List[Dict]) -> List[Dict]:
        """批量执行工具调用"""
```

## 5. XML 调用协议

### 5.1 工具定义格式

系统生成的 `<functions>` 块包含所有可用工具的 JSON Schema 定义：

```xml
<functions>
<function>{"description":"检查会议室可用性","name":"check_availability","parameters":{"additionalProperties":false,"properties":{"room":{"description":"会议室名称","title":"Room","type":"string"},"time":{"description":"时间范围","title":"Time","type":"string"}},"required":["room","time"],"title":"CheckAvailabilityParams","type":"object"}}</function>
<function>{"description":"预订会议室","name":"book_room","parameters":...}</function>
</functions>
```

### 5.2 调用格式规范

LLM 使用标准化的 XML 格式调用工具：

```xml
<function_calls>
<invoke name="check_availability">
<parameter name="room">观星阁</parameter>
<parameter name="time">15:00-16:00</parameter>
</invoke>
<invoke name="tell_user">
<parameter name="message">正在为您检查会议室可用性...</parameter>
</invoke>
</function_calls>
```

### 5.3 解析算法

```python
def parse_function_calls(self, response: str) -> List[Dict[str, Any]]:
    """解析 XML 格式的工具调用"""
    # 1. 提取 <function_calls> 块
    # 2. 解析多个 <invoke> 调用
    # 3. 提取参数键值对
    # 4. 返回标准化的调用列表
```

## 6. Context 集成机制

### 6.1 工具定义注入

```python
# core/context.py
class ContextBuilder:
    def create_context_from_state(self, events: List[Event]) -> str:
        context_parts = [
            self._get_system_instructions(),  # 角色和规则
            get_functions_xml(),              # 工具定义 ← 关键集成点
            self._format_events(events),      # 历史状态
            self._get_output_format()         # 输出规范
        ]
        return "\n\n".join(context_parts)

    def _get_output_format(self) -> str:
        """输出格式要求"""
        return """<output_instructions>
如果需要调用工具，请使用以下格式：
<function_calls>
<invoke name="工具名称">
<parameter name="参数名">参数值</parameter>
<parameter name="另一个参数名">另一个参数值</parameter>
</invoke>
</function_calls>
如果需要调用多个工具，可以在 function_calls 中包含多个 invoke 块。
如果不需要调用工具，直接回复用户即可。
注意：
- 工具名称必须精确匹配 functions 中定义的名称
- 参数名必须精确匹配工具定义中的参数名
- 必需的参数不能省略
</output_instructions>"""
```


### 6.2 事件格式标准

工具调用结果以标准事件格式进入状态流：

```python
{
    "type": "tool_result",
    "timestamp": "2024-01-01T12:00:00",
    "data": {
        "results": [
            {
                "tool_name": "check_availability",
                "success": True,
                "result": {"available": True, "room": "观星阁"}
            }
        ]
    }
}
```

## 7. 简化集成接口

### 7.1 统一调用入口

```python
# tools/__init__.py
def execute_tool_call(tool_name: str, params: dict) -> dict:
    """统一工具调用接口 - 最小化集成复杂度"""
    
def get_functions_xml() -> str:
    """获取工具定义 XML - Context 模块专用"""
    
def parse_and_execute_function_calls(llm_response: str) -> list:
    """一站式解析和执行 - Agent 主循环专用"""
```

### 7.2 向后兼容层

为现有代码提供兼容性支持：

```python
# 兼容原有调用方式
def check_availability_tool(params):
    return execute_tool_call("check_availability", params)

def book_room_tool(params):
    return execute_tool_call("book_room", params)
```

## 8. 工具开发标准流程

### 8.1 新工具创建步骤

1. **创建实现文件**: `tools/implementations/your_tool.py`
2. **继承基类**: 实现所有抽象方法
3. **定义参数**: 使用 `ParameterSchema` 声明参数
4. **注册工具**: 在 `tool_list.py` 中添加注册代码

### 8.2 标准实现模板

```python
class YourTool(BaseTool):
    def get_name(self) -> str:
        return "your_tool"
    
    def get_description(self) -> str:
        return "您的工具功能描述"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="param1",
                description="参数1的详细描述",
                type="string",
                required=True
            )
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # 实现具体逻辑
        return {"success": True, "result": "..."}
```
