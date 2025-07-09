import { Context } from './context.js';
import { State } from './state.js';
import { v4 as uuidv4 } from 'uuid';

export class Agent {
  constructor({ llmClient, memorySystem, toolRegistry, debug = false }) {
    this.llmClient = llmClient;
    this.memorySystem = memorySystem;
    this.toolRegistry = toolRegistry;
    this.debug = debug;
    
    this.state = new State();
    this.context = new Context(memorySystem, toolRegistry);
  }

  async processMessage(message, options = {}) {
    const sessionId = options.sessionId || uuidv4();
    
    try {
      // 更新状态
      this.state.updateUserMessage(message, sessionId);
      
      // 构建上下文
      const context = await this.context.build(message, this.state);
      
      // 调用LLM
      const response = await this.llmClient.chat({
        messages: context.messages,
        tools: context.tools,
        ...options
      });
      
      // 处理响应和工具调用
      const finalResponse = await this._processResponse(response, context);
      
      // 更新记忆
      await this._updateMemory(message, finalResponse, sessionId);
      
      // 更新状态
      this.state.updateAssistantMessage(finalResponse, sessionId);
      
      return finalResponse;
      
    } catch (error) {
      this._log('Error processing message:', error);
      throw error;
    }
  }

  async *processMessageStream(message, options = {}) {
    const sessionId = options.sessionId || uuidv4();
    
    try {
      this.state.updateUserMessage(message, sessionId);
      const context = await this.context.build(message, this.state);
      
      let fullResponse = '';
      
      for await (const chunk of this.llmClient.chatStream({
        messages: context.messages,
        tools: context.tools,
        ...options
      })) {
        fullResponse += chunk;
        yield chunk;
      }
      
      // 处理工具调用等后续逻辑
      const finalResponse = await this._processResponse(fullResponse, context);
      await this._updateMemory(message, finalResponse, sessionId);
      this.state.updateAssistantMessage(finalResponse, sessionId);
      
    } catch (error) {
      this._log('Error in stream processing:', error);
      throw error;
    }
  }

  async _processResponse(response, context) {
    // 检查是否有工具调用
    if (this._hasToolCalls(response)) {
      return await this._executeTools(response, context);
    }
    
    return response;
  }

  _hasToolCalls(response) {
    // 简化版本，实际需要根据LLM响应格式判断
    return typeof response === 'object' && response.tool_calls;
  }

  async _executeTools(response, context) {
    // 工具执行逻辑
    if (response.tool_calls) {
      for (const toolCall of response.tool_calls) {
        const tool = this.toolRegistry.getTool(toolCall.function.name);
        if (tool) {
          const result = await tool.execute(toolCall.function.arguments);
          // 处理工具执行结果
        }
      }
    }
    
    return response.content || response;
  }

  async _updateMemory(userMessage, assistantMessage, sessionId) {
    try {
      await this.memorySystem.addInteraction({
        userMessage,
        assistantMessage,
        sessionId,
        timestamp: new Date()
      });
    } catch (error) {
      this._log('Memory update error:', error);
    }
  }

  _log(...args) {
    if (this.debug) {
      console.log('[Agent]', ...args);
    }
  }
} 