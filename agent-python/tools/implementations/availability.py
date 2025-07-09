"""
可用性检查工具
"""

from typing import Dict, Any, List
from ..base import BaseTool, ParameterSchema

class CheckAvailabilityTool(BaseTool):
    """检查会议室可用性工具"""
    
    def get_name(self) -> str:
        return "check_availability"
    
    def get_description(self) -> str:
        return "检查指定会议室在指定时间的可用性"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="room",
                description="会议室名称，如：观星阁、会议室A、大会议室等",
                type="string",
                required=True
            ),
            ParameterSchema(
                name="time",
                description="时间范围，格式为 HH:MM-HH:MM，如：15:00-16:00",
                type="string", 
                required=True
            ),
            ParameterSchema(
                name="date",
                description="日期，格式为 YYYY-MM-DD，默认为今天",
                type="string",
                required=False,
                default="today"
            )
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行可用性检查"""
        room = parameters.get("room", "").strip()
        time = parameters.get("time", "").strip()
        date = parameters.get("date", "今天").strip()
        
        if not room or not time:
            return {
                "success": False,
                "error": "缺少必要参数：room 和 time"
            }
        
        # 模拟检查逻辑
        # 实际应用中这里会调用真实的预订系统 API
        available = self._mock_check_availability(room, time, date)
        
        return {
            "success": True,
            "available": available,
            "room": room,
            "time": time,
            "date": date,
            "message": f"{room} 在 {date} {time} {'可用' if available else '不可用'}"
        }
    
    def _mock_check_availability(self, room: str, time: str, date: str) -> bool:
        """模拟检查可用性的逻辑"""
        # 简单模拟：观星阁在下午时段通常可用
        if "观星阁" in room and "15:00" in time:
            return True
        # 其他情况随机决定
        import random
        return random.choice([True, False]) 