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

  // 检查并清理超长上下文
  async function checkAndCleanupContext() {
    const estimatedLength = stateManager.estimateContextLength();
    console.log("estimatedLength: ", estimatedLength);
    if (estimatedLength <= maxContextLength) {
      return; // 不需要清理
    }
    
    const currentEvents = stateManager.getState();
    if (currentEvents.length <= 3) {
      return; // 事件太少，不清理
    }
    
    // 计算需要移除的事件数量（最老的1/3）
    let removeCount = Math.floor(currentEvents.length / 3);
    if (removeCount === 0) {
      removeCount = 1; // 至少移除1个
    }
    
    console.log(`上下文长度预估 ${estimatedLength}，将移除 ${removeCount} 个最老事件`);
    
    // 立即从状态中移除老事件
    const removedEvents = stateManager.removeOldestEvents(removeCount);
    
    if (removedEvents.length > 0) {
      console.log(`已从状态中移除 ${removedEvents.length} 个事件`);
      
      // 异步调度记忆更新（不阻塞主流程）
      scheduleMemoryUpdate(removedEvents);
    }
  }

  // 异步调度记忆更新
  function scheduleMemoryUpdate(removedEvents) {
    // 使用 Promise.resolve().then() 确保异步执行
    Promise.resolve().then(async () => {
      try {
        const statesForMemory = removedEvents.map(event => event.data);
        const { updateMemory } = await import('../memory-system/index.js');
        await updateMemory(statesForMemory, "default", undefined, true);
        console.log(`✅ 已将 ${removedEvents.length} 个事件存储到记忆系统`);
      } catch (error) {
        console.warn('⚠️ 记忆更新失败（不影响主对话）:', error.message);
      }
    });
  }

  // 处理用户输入
  async function processUserInput(llmCallFunction) {
    let iteration = 0;

    while (iteration < maxIterations) {
      iteration++;
      console.log(`\n--- 处理中 ${iteration} ---`);

      // 0. 检查并清理上下文（新增）
      await checkAndCleanupContext();

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

      // 检查并清理上下文（新增）
      await checkAndCleanupContext();

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
    setGlobalStatus,
    checkAndCleanupContext  
  };
}

// 创建默认Agent实例
export const defaultAgent = createAgent();

// 便捷函数
export async function processMessage(message, llmCallFunction, agent = defaultAgent) {
  return agent.processSingleMessage(message, llmCallFunction);
}