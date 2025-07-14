import { toolRegistry } from './registry.js';

/**
 * 中心化工具管理器
 */
export class ToolManager {
  constructor() {
    this.registry = toolRegistry;
  }

  /**
   * 初始化所有工具
   */
  async initialize() {
    await this.registerBuiltinTools();
  }

  /**
   * 注册内置工具
   */
  async registerBuiltinTools() {
    try {
      // 注册网络搜索工具
      const { createWebSearchTool } = await import('./implementations/web-search.js');
      const webSearchTool = createWebSearchTool();
      this.registry.register(webSearchTool);
      
      console.log('Built-in tools registered successfully');
    } catch (error) {
      console.error('Failed to register built-in tools:', error);
      throw error;
    }
  }

  /**
   * 注册自定义工具
   * @param {Object} tool
   */
  registerTool(tool) {
    this.registry.register(tool);
  }

  /**
   * 获取工具定义 XML
   * @returns {string}
   */
  getFunctionsXML() {
    return this.registry.getFunctionsXML();
  }

  /**
   * 解析并执行工具调用
   * @param {string} llmResponse
   * @returns {Array}
   */
  async parseAndExecute(llmResponse) {
    const calls = this.registry.parseFunctionCalls(llmResponse);
    if (calls.length === 0) {
      return [];
    }

    return await this.registry.executeFunctionCalls(calls);
  }
}

// 全局单例实例
export const toolManager = new ToolManager(); 