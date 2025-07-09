"""
预订工具
"""

from typing import Dict, Any, List
import uuid
from ..base import BaseTool, ParameterSchema

class BookRoomTool(BaseTool):
    """预订会议室工具"""
    
    def get_name(self) -> str:
        return "book_room"
    
    def get_description(self) -> str:
        return "预订指定会议室"
    
    def get_parameters(self) -> List[ParameterSchema]:
        return [
            ParameterSchema(
                name="room",
                description="会议室名称",
                type="string",
                required=True
            ),
            ParameterSchema(
                name="time", 
                description="时间范围，格式为 HH:MM-HH:MM",
                type="string",
                required=True
            ),
            ParameterSchema(
                name="date",
                description="日期，格式为 YYYY-MM-DD，默认为今天",
                type="string",
                required=False,
                default="today"
            ),
            ParameterSchema(
                name="organizer",
                description="组织者姓名",
                type="string",
                required=False,
                default="未知用户"
            ),
            ParameterSchema(
                name="purpose",
                description="会议目的或主题",
                type="string", 
                required=False
            )
        ]
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行预订"""
        room = parameters.get("room", "").strip()
        time = parameters.get("time", "").strip()
        date = parameters.get("date", "今天").strip()
        organizer = parameters.get("organizer", "未知用户").strip()
        purpose = parameters.get("purpose", "").strip()
        
        if not room or not time:
            return {
                "success": False,
                "error": "缺少必要参数：room 和 time"
            }
        
        # 模拟预订逻辑
        booking_result = self._mock_book_room(room, time, date, organizer, purpose)
        
        return booking_result
    
    def _mock_book_room(self, room: str, time: str, date: str, organizer: str, purpose: str) -> Dict[str, Any]:
        """模拟预订逻辑"""
        booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
        
        result = {
            "success": True,
            "booking_id": booking_id,
            "room": room,
            "time": time,
            "date": date,
            "organizer": organizer,
            "message": f"成功预订 {room}，时间：{date} {time}，预订号：{booking_id}"
        }
        
        if purpose:
            result["purpose"] = purpose
            result["message"] += f"，会议主题：{purpose}"
        
        return result 