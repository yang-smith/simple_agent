import { createStateManager, addUserMessage, addAgentMessage, addToolResult } from './state.js';
import { createContextBuilder } from './context.js';

// Agent 工厂函数
export function createAgent(options = {}) {
  const maxIterations = options.maxIterations || 3;
  const maxContextLength = options.maxContextLength || 8000;
  
  const stateManager = createStateManager();
  const contextBuilder = createContextBuilder({ maxContextLength });

  // 添加用户消息到状态
  function addUserMessageToState(content) {
    return addUserMessage(content, stateManager);
  }

  // 添加智能体回复到状态
  function addAgentMessageToState(content) {
    return addAgentMessage(content, stateManager);
  }

  // 添加工具执行结果到状态
  function addToolResultToState(results) {
    return addToolResult(results, stateManager);
  }

  // 处理用户输入
  async function processUserInput(llmCallFunction) {
    let iteration = 0;

    while (iteration < maxIterations) {
      iteration++;
      console.log(`\n--- 处理中 ${iteration} ---`);

      // 1. 上下文工程：用当前状态生成 prompt
      const currentState = stateManager.getState();
      const context = await contextBuilder.createContextFromState(currentState);
      console.log("context: \n", context);

      // 2. LLM 决策：把决策外包给 LLM
      let llmResponse;
      try {
        llmResponse = await llmCallFunction(context);
        console.log(`Agent_test: ${llmResponse.substring(0, 300)}...`); // 显示前300字符
      } catch (error) {
        console.log(`LLM 调用失败: ${error}`);
        break;
      }

      // 3. 解析并执行工具调用 - 使用tools模块的函数
      let calls;
      try {
        // 先解析是否有工具调用，如果有就显示状态
        if (llmResponse.includes('<function_calls>')) {
          const toolNameMatch = llmResponse.match(/<invoke name="([^"]+)">/);
          if (toolNameMatch) {
            const toolName = toolNameMatch[1];
            setGlobalStatus('tool_calling', `正在调用 ${toolName} 工具...`);
          }
        }
        
        const { parseAndExecuteFunctionCalls } = await import('../tools/index.js');
        const results = await parseAndExecuteFunctionCalls(llmResponse);
        calls = results; // parseAndExecuteFunctionCalls 已经执行了工具并返回结果
        
        // 工具执行完成后更新状态
        if (calls && calls.length > 0) {
          setGlobalStatus('thinking', '正在处理工具结果...');
        }
      } catch (error) {
        console.error('Tool execution failed:', error);
        calls = [];
      }

      if (!calls || calls.length === 0) {
        // 没有工具调用，直接回复用户
        console.log(`Agent: ${llmResponse}`);
        addAgentMessageToState(llmResponse);
        break;
      }

      // 4. 处理工具调用结果
      for (const result of calls) {
        if (result.success) {
          console.log(`工具 ${result.tool_name} 执行成功`);
        } else {
          console.log(`工具 ${result.tool_name} 执行失败: ${result.error}`);
        }
      }

      // 5. 更新状态：添加工具执行结果
      if (calls.length > 0) {
        addToolResultToState(calls);
      }
    }

    if (iteration >= maxIterations) {
      console.log("达到最大迭代次数");
    }
  }

  // 设置全局状态
  function setGlobalStatus(status, details = '') {
    const statusData = {
      status,
      details,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('agent_status', JSON.stringify(statusData));
    
    // 触发自定义事件通知UI更新
    window.dispatchEvent(new CustomEvent('agentStatusChange', { detail: statusData }));
  }

  // 处理单条消息并返回回复（用于API调用等场景）
  async function processSingleMessage(message, llmCallFunction) {
    try {
      setGlobalStatus('processing', '正在处理用户消息...');
      
      // 添加用户消息
      addUserMessageToState(message);

      setGlobalStatus('thinking', '正在思考回复...');
      
      // 生成上下文
      const currentState = stateManager.getState();
      const context = await contextBuilder.createContextFromState(currentState);

      // 调用LLM
      let llmResponse = await llmCallFunction(context);

      // 检查是否有工具调用 - 使用tools模块的函数
      let toolResults;
      try {
        // 先解析是否有工具调用，如果有就显示状态
        if (llmResponse.includes('<function_calls>')) {
          // 简单解析工具名称
          const toolNameMatch = llmResponse.match(/<invoke name="([^"]+)">/);
          if (toolNameMatch) {
            const toolName = toolNameMatch[1];
            setGlobalStatus('tool_calling', `正在调用 ${toolName} 工具...`);
          }
        }
        
        const { parseAndExecuteFunctionCalls } = await import('../tools/index.js');
        toolResults = await parseAndExecuteFunctionCalls(llmResponse);
        
        // 工具执行完成后更新状态
        if (toolResults && toolResults.length > 0) {
          setGlobalStatus('thinking', '正在处理工具结果...');
        }
      } catch (error) {
        console.error('Tool execution failed:', error);
        toolResults = [];
      }

      if (toolResults && toolResults.length > 0) {
        // 执行工具调用
        addToolResultToState(toolResults);

        setGlobalStatus('thinking', '正在整理工具执行结果...');
        
        // 再次调用LLM获取最终回复
        const updatedState = stateManager.getState();
        const updatedContext = await contextBuilder.createContextFromState(updatedState);
        const finalResponse = await llmCallFunction(updatedContext);
        addAgentMessageToState(finalResponse);
        
        setGlobalStatus('idle', '就绪');
        return finalResponse;
      } else {
        // 直接回复
        addAgentMessageToState(llmResponse);
        setGlobalStatus('idle', '就绪');
        return llmResponse;
      }
    } catch (error) {
      setGlobalStatus('error', `处理消息时出错: ${error.message}`);
      const errorMsg = `处理消息时出错: ${error}`;
      addAgentMessageToState(errorMsg);
      return errorMsg;
    }
  }

  // 获取当前状态
  function getCurrentState() {
    return stateManager.getState();
  }

  // 清空状态
  function clearState() {
    stateManager.clearState();
  }

  // 获取统计信息
  function getStats() {
    return stateManager.getStats();
  }

  return {
    addUserMessage: addUserMessageToState,
    addAgentMessage: addAgentMessageToState,
    addToolResult: addToolResultToState,
    processUserInput,
    processSingleMessage,
    getCurrentState,
    clearState,
    getStats,
    setGlobalStatus
  };
}

// 创建默认Agent实例
export const defaultAgent = createAgent();

// 便捷函数
export async function processMessage(message, llmCallFunction, agent = defaultAgent) {
  return agent.processSingleMessage(message, llmCallFunction);
}