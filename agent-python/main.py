from tools import get_all_tools, get_functions_xml, parse_and_execute_function_calls
from core.context import ContextBuilder
from core.state import Event, EventTypes, StateManager
from llm.llm_client import llm_call

# 全局变量
event_stream = []

# Reducer 就是一个简单的追加函数
def reducer(current_state, new_event):
    return current_state + [new_event]

def create_context_from_state(state):
    """创建上下文的简化函数"""
    context_builder = ContextBuilder()
    # 将简单的事件转换为 Event 对象
    events = []
    for event_dict in state:
        event = Event(
            type=event_dict["type"],
            timestamp=None,  # 会自动设置
            data=event_dict
        )
        events.append(event)
    return context_builder.create_context_from_state(events)

def call_llm(context):
    """调用 LLM 的简化函数"""
    return llm_call(context)

def run_agent(initial_prompt=None):
    # 1. 初始化状态
    state = []
    
    # 获取工具注册表（测试用）
    registry = get_all_tools()
    
    # 显示工具的 functions XML（测试用）
    print("=== 工具定义 (Functions XML) ===")
    print(get_functions_xml())
    print("\n=== 开始 Agent 对话 ===")
    print("输入 'quit' 或 'exit' 退出对话")
    
    # 如果有初始提示，先处理它
    if initial_prompt:
        print(f"用户: {initial_prompt}")
        event = {"type": "user_message", "content": initial_prompt}
        state = reducer(state, event)
        state = process_user_input(state)
    
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
            event = {"type": "user_message", "content": user_input}
            state = reducer(state, event)
            
            # 处理用户输入并更新状态
            state = process_user_input(state)
            
        except KeyboardInterrupt:
            print("\n再见！")
            break

def process_user_input(state):
    """处理用户输入的函数"""
    iteration = 0
    max_iterations = 3  # 防止无限循环

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- 处理中 {iteration} ---")
        
        # 2. 上下文工程：用当前状态生成 prompt
        context = create_context_from_state(state)
        print("context: \n", context)

        # 3. LLM 决策：把决策外包给 LLM
        try:
            llm_response = call_llm(context)
            print(f"Agent_test: {llm_response[:300]}...")  # 显示前300字符
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            break

        # 4. 解析并执行工具调用
        calls = parse_and_execute_function_calls(llm_response)

        if not calls:
            # 没有工具调用，直接回复用户
            print(f"Agent: {llm_response}")
            new_event = {"type": "agent_message", "content": llm_response}
            state = reducer(state, new_event)
            break

        # 5. 处理工具调用结果
        results = []
        for call in calls:
            if call.get("success"):
                results.append(call)
                print(f"工具 {call['tool_name']} 执行成功")
            else:
                results.append(call)
                print(f"工具 {call['tool_name']} 执行失败: {call['error']}")

        # 6. 更新状态：用 Reducer 生成新状态
        if results:
            new_event = {"type": "tool_result", "results": results}
            state = reducer(state, new_event)

    if iteration >= max_iterations:
        print("达到最大迭代次数")
    
    return state

if __name__ == "__main__":
    run_agent()