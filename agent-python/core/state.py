from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    """事件基类"""
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventTypes:
    """事件类型常量"""
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message" 
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM = "system"

class StateManager:
    """状态管理器 - 实现 Reducer 模式"""
    
    def __init__(self):
        self.events: List[Event] = []
    
    def reducer(self, new_event: Event) -> List[Event]:
        """Reducer 函数 - 纯函数，返回新状态"""
        return self.events + [new_event]
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """添加新事件到状态"""
        event = Event(type=event_type, timestamp=datetime.now(), data=data)
        self.events = self.reducer(event)
    
    def get_state(self) -> List[Event]:
        """获取当前状态"""
        return self.events.copy()
    
    def get_events_by_type(self, event_type: str) -> List[Event]:
        """按类型筛选事件"""
        return [e for e in self.events if e.type == event_type] 