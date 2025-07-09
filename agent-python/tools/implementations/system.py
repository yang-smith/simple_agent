"""
系统工具
"""

from typing import Dict, Any
from ..base import BaseTool, ToolMetadata

class FinishTool(BaseTool):
    """完成任务工具"""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="finish",
            description="标记任务完成",
            parameters={
                "summary": "任务完成总结（可选）"
            },
            examples="summary: 已成功为用户预订会议室"
        )
    
    def execute(self, params: str) -> Dict[str, Any]:
        """执行任务完成"""
        parsed_params = self.parse_params(params)
        summary = parsed_params.get("summary", "任务已完成").strip()
        
        return {
            "success": True,
            "finished": True,
            "summary": summary
        } 