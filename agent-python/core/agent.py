import re
from typing import Dict, Any, List, Optional
from .state import StateManager, EventTypes, Event
from .context import ContextBuilder
from tools import get_all_tools, get_functions_xml, parse_and_execute_function_calls
from llm.llm_client import llm_call

class Agent:
    """Agent 核心 - 实现状态机循环"""
    
    def __init__(self, max_iterations: int = 3, max_context_length: int = 8000):
        self.state_manager = StateManager()
        self.context_builder = ContextBuilder(max_context_length)
        self.max_iterations = max_iterations
        self.tools_registry = get_all_tools()
    
    def run(self, initial_prompt: Optional[str] = None) -> None:
        """启动 Agent 对话循环"""
        print("=== 工具定义 (Functions XML) ===")
        print(get_functions_xml())
        print("\n=== 开始 Agent 对话 ===")
        print("输入 'quit' 或 'exit' 退出对话")
        
        # 如果有初始提示，先处理它
        if initial_prompt:
            print(f"用户: {initial_prompt}")
            self.add_user_message(initial_prompt)
            self.process_user_input()
        
        # 进入对话循环
        while True:
            try:
                user_input = input("\n用户: ").strip()
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("再见！")
                    break
                
                if not user_input:
                    continue
                    
                # 添加用户消息到状态
                self.add_user_message(user_input)
                
                # 处理用户输入
                self.process_user_input()
                
            except KeyboardInterrupt:
                print("\n再见！")
                break
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息到状态"""
        self.state_manager.add_event(EventTypes.USER_MESSAGE, {"content": content})
    
    def add_agent_message(self, content: str) -> None:
        """添加智能体回复到状态"""
        self.state_manager.add_event(EventTypes.AGENT_MESSAGE, {"content": content})
    
    def add_tool_result(self, results: List[Dict[str, Any]]) -> None:
        """添加工具执行结果到状态"""
        self.state_manager.add_event(EventTypes.TOOL_RESULT, {"results": results})
    
    def process_user_input(self) -> None:
        """处理用户输入的函数"""
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- 处理中 {iteration} ---")
            
            # 1. 上下文工程：用当前状态生成 prompt
            current_state = self.state_manager.get_state()
            context = self.context_builder.create_context_from_state(current_state)
            print("context: \n", context)

            # 2. LLM 决策：把决策外包给 LLM
            try:
                llm_response = llm_call(context)
                print(f"Agent_test: {llm_response[:300]}...")  # 显示前300字符
            except Exception as e:
                print(f"LLM 调用失败: {e}")
                break

            # 3. 解析并执行工具调用
            calls = parse_and_execute_function_calls(llm_response)

            if not calls:
                # 没有工具调用，直接回复用户
                print(f"Agent: {llm_response}")
                self.add_agent_message(llm_response)
                break

            # 4. 处理工具调用结果
            results = []
            for call in calls:
                if call.get("success"):
                    results.append(call)
                    print(f"工具 {call['tool_name']} 执行成功")
                else:
                    results.append(call)
                    print(f"工具 {call['tool_name']} 执行失败: {call['error']}")

            # 5. 更新状态：添加工具执行结果
            if results:
                self.add_tool_result(results)

        if iteration >= self.max_iterations:
            print("达到最大迭代次数")
    
    def get_current_state(self) -> List[Event]:
        """获取当前状态"""
        return self.state_manager.get_state()
    
    def clear_state(self) -> None:
        """清空状态"""
        self.state_manager.events = []
    
    def process_single_message(self, message: str) -> str:
        """处理单条消息并返回回复（用于API调用等场景）"""
        # 添加用户消息
        self.add_user_message(message)
        
        # 生成上下文
        current_state = self.state_manager.get_state()
        context = self.context_builder.create_context_from_state(current_state)
        
        # 调用LLM
        try:
            llm_response = llm_call(context)
            
            # 检查是否有工具调用
            calls = parse_and_execute_function_calls(llm_response)
            
            if calls:
                # 处理工具调用
                results = []
                for call in calls:
                    results.append(call)
                
                self.add_tool_result(results)
                
                # 再次调用LLM获取最终回复
                current_state = self.state_manager.get_state()
                context = self.context_builder.create_context_from_state(current_state)
                final_response = llm_call(context)
                self.add_agent_message(final_response)
                return final_response
            else:
                # 直接回复
                self.add_agent_message(llm_response)
                return llm_response
                
        except Exception as e:
            error_msg = f"处理消息时出错: {e}"
            self.add_agent_message(error_msg)
            return error_msg
    