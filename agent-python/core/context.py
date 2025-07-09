from typing import List
from .state import Event, EventTypes
from tools import get_functions_xml
from memory_system import get_base_memory, update_memory, schedule_memory_update
from datetime import date
import threading

class ContextBuilder:
    """上下文构建器"""
    
    def __init__(self, max_context_length: int = 8000):
        self.max_context_length = max_context_length

    def create_context_from_state(self, events: List[Event]) -> List[dict]:
        """将事件流转换为结构化上下文"""

        messages = []

        messages.append({
            "role": "system",
            "content": self._get_system_prompt()
        })
        
        context_parts = []
        
        # 1. base_prompt
        context_parts.append(self._get_base_prompt())
        
        # 2. 基础记忆
        context_parts.append("# 这是记忆里的内容：\n"+get_base_memory(user_id="default"))
        
        # 2. 工具定义
        context_parts.append("# 这是工具定义：\n"+get_functions_xml())
        
        # 3. 工具使用格式要求
        context_parts.append("# 这是工具使用格式要求：\n"+self._get_output_format())

        # 4. 历史事件
        context_parts.append("# 历史状态记录（注意对话历史用户是可见的，工具调用部分用户不可见）：\n"+self._format_events(events))


        full_context = "\n\n".join(context_parts)
        
        # 如果超长，进行智能截断
        if len(full_context) > self.max_context_length:
            full_context = self._truncate_context(full_context, events)
            
        messages.append({
            "role": "assistant",
            "content": full_context
        })

        return messages
    
    def _get_system_prompt(self) -> str:
        """系统指令"""
        return """
你是一个真诚的人。
你对第一性原理，多维度思考，批判性思考，逆向思维，系统理论、行为心理学、群体心理学、传播学、经济学、认知论、演化心理学、生物学、进化论等领域都有深刻的见解。你同时是专业的开发者。
你尊重事实，实事求是。  
你的语言风格自然质朴，说人话，有自己鲜明的观点，不会只顾着面面俱到。你每次不会说过多的内容，因为人都有认知负荷，我们有的是时间，不急。
你要透过用户的文字感受用户背后的真实意图，真正地看见那个意图，并与那个意图进行对话。
你不会简单地附和用户，你会说出你自己的想法。


function调用原则：
你自由决定调用工具。工具调用完成后，根据状况思考下一步动作（直接回复用户或者继续调用function）。
在涉及用户隐私、外部资源调用（如可能产生费用）或需要用户明确授权的操作前，应优先征询用户意愿。

"""
    
    def _format_events(self, events: List[Event]) -> str:
        """格式化事件历史"""
        if not events:
            return "暂无对话历史"
            
        formatted_events = []
        for event in events:
            if event.type == EventTypes.USER_MESSAGE:
                content = event.data.get('content', '')
                formatted_events.append(f"用户说: {content}")
            elif event.type == EventTypes.TOOL_RESULT:
                # 适配 tools 系统的结果格式
                results = event.data.get('results', [])
                for result in results:
                    tool_name = result.get('tool_name', '')
                    success = result.get('success', False)
                    if success:
                        result_data = result.get('result', {})
                        # 统一使用工具返回的message字段
                        message = result_data.get('message', f"{tool_name}执行成功")
                        formatted_events.append(f"工具执行结果: {message}")
                    else:
                        error_msg = result.get('error', '')
                        formatted_events.append(f"工具执行失败: {tool_name} - {error_msg}")
            elif event.type == EventTypes.AGENT_MESSAGE:
                content = event.data.get('content', '')
                formatted_events.append(f"我回复: {content}")
                
        return "\n".join(formatted_events)
    
    def _get_base_prompt(self) -> str:
        """基础提示词"""
        return f"""
今天是{date.today()}
"""
    
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
    
    def _truncate_context(self, context: str, events: List[Event]) -> str:
        """智能截断上下文"""
        from memory_system import schedule_memory_update
        
        # 如果事件数量少于3个，直接保留最近的事件
        if len(events) <= 3:
            recent_events = events
        else:
            # 计算需要移除的事件数量（最老的三分之一）
            remove_count = len(events) // 3
            if remove_count == 0:
                remove_count = 1  # 至少移除1个
            
            # 获取最老的事件（按时间正序排列）
            sorted_events = sorted(events, key=lambda x: x.timestamp)
            oldest_events = sorted_events[:remove_count]
            
            # 将最老的事件转换为记忆系统的states格式
            states_for_memory = []
            for event in oldest_events:
                states_for_memory.append(event.data)
            
            # 异步调度记忆更新
            schedule_memory_update(states_for_memory, user_id="default", force_process=True)
            print(f"已调度 {len(oldest_events)} 个事件的记忆存储")
            
            # 保留剩余的事件
            remaining_events = sorted_events[remove_count:]
            # 按原始顺序重新排列
            recent_events = sorted(remaining_events, key=lambda x: x.timestamp)
        
        # 重新构建上下文
        context_parts = [
            self._get_base_prompt(),
            "# 这是记忆里的内容：\n" + get_base_memory(user_id="default"),
            "# 这是工具定义：\n" + get_functions_xml(),
            "# 这是工具使用格式要求：\n" + self._get_output_format(),
            "# 历史状态记录（注意对话历史用户是可见的，工具部分用户不可见，你需要结合工具调用结果和对话历史回答用户）：\n" + self._format_events(recent_events)
        ]
        
        return "\n\n".join(context_parts) 