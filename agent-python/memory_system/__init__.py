"""
PersonaFlow Memory System - 仿生记忆模块

为无状态LLM提供自适应认知记忆架构：
- 短期记忆: 近期对话摘要，快速检索
- 长期记忆: AI的自适应认知模型，分层存储

核心接口：
- update_memory(states, user_id): 写入接口，处理新的states
- get_relevant_memories(query, user_id): 读取接口，获取相关记忆
"""

import asyncio
import threading
from typing import List, Any
from .interface import MemorySystem
from .config import MemoryConfig

# 创建默认记忆系统实例
_default_memory_system = None
_background_loop = None
_background_thread = None

def get_memory_system(config=None, llm_client=None):
    """获取记忆系统实例（单例模式）"""
    global _default_memory_system
    if _default_memory_system is None:
        _default_memory_system = MemorySystem(config=config, llm_client=llm_client)
    return _default_memory_system

def _ensure_background_loop():
    """确保后台事件循环存在"""
    global _background_loop, _background_thread
    
    if _background_loop is None or _background_loop.is_closed():
        def run_background_loop():
            global _background_loop
            _background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_background_loop)
            _background_loop.run_forever()
        
        _background_thread = threading.Thread(target=run_background_loop, daemon=True)
        _background_thread.start()
        
        # 等待循环启动
        import time
        while _background_loop is None:
            time.sleep(0.01)

async def _async_update_memory(states: List[Any], user_id: str = "default", force_process: bool = False):
    """异步更新记忆"""
    try:
        print(f"后台协程: 开始处理 {len(states)} 个事件的记忆更新...")
        memory_system = get_memory_system()
        memory_system.update_memory(states, user_id, force_process)
        print("后台协程: 记忆更新完成")
    except Exception as e:
        print(f"后台协程: 记忆更新失败: {e}")

def schedule_memory_update(states: List[Any], user_id: str = "default", force_process: bool = False):
    """调度异步记忆更新"""
    _ensure_background_loop()
    
    # 在后台事件循环中调度协程
    future = asyncio.run_coroutine_threadsafe(
        _async_update_memory(states, user_id, force_process),
        _background_loop
    )
    
    # 可以选择是否等待结果（这里不等待，实现真正的异步）
    return future

def update_memory(states, user_id="default", force_process=False):
    """
    写入接口：处理新的states，更新记忆
    
    Args:
        states: 对话状态列表
        user_id: 用户标识
        force_process: 是否强制处理（忽略token阈值）
    """
    memory_system = get_memory_system()
    return memory_system.update_memory(states, user_id, force_process)

def get_relevant_memories(query, user_id="default"):
    """
    读取接口：获取相关记忆用于context
    
    Args:
        query: 查询内容
        user_id: 用户标识
    
    Returns:
        str: 相关记忆片段列表的字符串表示
    """
    memory_system = get_memory_system()
    return memory_system.get_relevant_memories(query, user_id)

def get_base_memory(user_id="default"):
    """
    获取基础记忆
    """
    memory_system = get_memory_system()
    return memory_system.get_base_memory(user_id)

def shutdown_background_loop():
    """关闭后台事件循环（用于清理资源）"""
    global _background_loop, _background_thread
    if _background_loop and not _background_loop.is_closed():
        _background_loop.call_soon_threadsafe(_background_loop.stop)
        _background_loop = None
    if _background_thread:
        _background_thread = None

# 对外开放的核心接口
__all__ = [
    'update_memory',           # 写入接口
    'schedule_memory_update',  # 异步调度接口
    'get_relevant_memories',   # 读取接口
    'get_base_memory',         # 获取基础记忆
    'MemoryConfig',           # 配置类（用于自定义配置）
    'shutdown_background_loop', # 清理接口
]

__version__ = "0.1.0"
