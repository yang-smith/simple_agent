import { Agent } from './core/agent.js';
import { MemorySystem } from './memory-system/index.js';
import { LLMClient } from './llm/llm-client.js';
import { ToolRegistry } from './tools/registry.js';
import { updateMemory, getRelevantMemories, getBaseMemory } from './memory-system/index.js';

export class SimpleAgent {
  constructor(config = {}) {
    this.config = {
      apiKey: config.apiKey || process.env.GOOGLE_API_KEY,
      model: config.model || 'google/gemini-2.5-flash',
      memoryConfig: config.memory || {},
      toolsEnabled: config.tools !== false,
      debug: config.debug || false,
      ...config
    };
    
    this.initialized = false;
    this.agent = null;
  }

  async init() {
    if (this.initialized) return;

    try {
      // 初始化LLM客户端
      this.llmClient = new LLMClient({
        apiKey: this.config.apiKey,
        model: this.config.model
      });

      // 初始化记忆系统
      this.memorySystem = new MemorySystem(this.config.memoryConfig);
      await this.memorySystem.init();

      // 初始化工具注册表
      this.toolRegistry = new ToolRegistry();
      if (this.config.toolsEnabled) {
        await this.toolRegistry.loadDefaultTools();
      }

      // 初始化Agent核心
      this.agent = new Agent({
        llmClient: this.llmClient,
        memorySystem: this.memorySystem,
        toolRegistry: this.toolRegistry,
        debug: this.config.debug
      });

      this.initialized = true;
      if (this.config.debug) {
        console.log('SimpleAgent initialized successfully');
      }
    } catch (error) {
      console.error('Failed to initialize SimpleAgent:', error);
      throw error;
    }
  }

  async chat(message, options = {}) {
    if (!this.initialized) {
      await this.init();
    }

    try {
      const response = await this.agent.processMessage(message, options);
      return response;
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  }

  async *chatStream(message, options = {}) {
    if (!this.initialized) {
      await this.init();
    }

    try {
      for await (const chunk of this.agent.processMessageStream(message, options)) {
        yield chunk;
      }
    } catch (error) {
      console.error('Chat stream error:', error);
      throw error;
    }
  }

  async updateMemory(states, forceProcess = false) {
    return await updateMemory(states, this.userId, this.config.memory, forceProcess);
  }

  async getRelevantMemories(userInput) {
    return await getRelevantMemories(userInput, this.userId, this.config.memory);
  }

  async getBaseMemory() {
    return await getBaseMemory(this.userId);
  }

  async getMemoryStats() {
    if (!this.memorySystem) return null;
    return await this.memorySystem.getStats();
  }

  async clearMemory() {
    if (!this.memorySystem) return;
    await this.memorySystem.clear();
  }

  destroy() {
    if (this.memorySystem) {
      this.memorySystem.destroy();
    }
    this.initialized = false;
  }
}

// 便捷创建函数
export async function createAgent(config = {}) {
  const agent = new SimpleAgent(config);
  await agent.init();
  return agent;
}

// 导出主要类供高级用户使用
export { Agent } from './core/agent.js';
export * from './memory-system/index.js';
export { LLMClient } from './llm/llm-client.js'; 
export { ToolRegistry } from './tools/registry.js';