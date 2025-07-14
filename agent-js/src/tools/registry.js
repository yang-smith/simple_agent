import { isValidTool } from './base.js';

export class ToolRegistry {
  constructor() {
    this.tools = new Map();
  }

  /**
   * 注册工具到系统
   * @param {Object} tool
   */
  register(tool) {
    if (!isValidTool(tool)) {
      throw new Error('Invalid tool: must implement required methods');
    }
    
    const name = tool.getName();
    this.tools.set(name, tool);
    console.log(`Tool registered: ${name}`);
  }

  /**
   * 获取工具实例
   * @param {string} name
   * @returns {Object|null}
   */
  getTool(name) {
    return this.tools.get(name) || null;
  }

  /**
   * 获取所有工具名称
   * @returns {string[]}
   */
  getToolNames() {
    return Array.from(this.tools.keys());
  }

  /**
   * 生成标准 <functions> XML 块
   * @returns {string}
   */
  getFunctionsXML() {
    if (this.tools.size === 0) {
      return '';
    }

    const functions = Array.from(this.tools.values())
      .map(tool => {
        const schema = tool.getFunctionSchema();
        return `<function>${JSON.stringify(schema)}</function>`;
      })
      .join('\n');

    return `<functions>\n${functions}\n</functions>`;
  }

  /**
   * 解析 LLM 响应中的工具调用
   * @param {string} response
   * @returns {Array}
   */
  parseFunctionCalls(response) {
    const calls = [];
    
    // 提取 <function_calls> 块
    const functionCallsMatch = response.match(/<function_calls>(.*?)<\/function_calls>/s);
    if (!functionCallsMatch) {
      return calls;
    }

    const functionCallsContent = functionCallsMatch[1];
    
    // 解析多个 <invoke> 调用
    const invokeMatches = functionCallsContent.matchAll(/<invoke name="([^"]+)">(.*?)<\/invoke>/gs);
    
    for (const match of invokeMatches) {
      const toolName = match[1];
      const parametersContent = match[2];
      
      // 解析参数键值对
      const parameters = {};
      const paramMatches = parametersContent.matchAll(/<parameter name="([^"]+)">(.*?)<\/parameter>/gs);
      
      for (const paramMatch of paramMatches) {
        const paramName = paramMatch[1];
        const paramValue = paramMatch[2].trim();
        parameters[paramName] = paramValue;
      }
      
      calls.push({
        tool_name: toolName,
        parameters
      });
    }
    
    return calls;
  }

  /**
   * 批量执行工具调用
   * @param {Array} calls
   * @returns {Array}
   */
  async executeFunctionCalls(calls) {
    const results = [];
    
    for (const call of calls) {
      const { tool_name, parameters } = call;
      const tool = this.getTool(tool_name);
      
      if (!tool) {
        results.push({
          tool_name,
          success: false,
          error: `Tool '${tool_name}' not found`
        });
        continue;
      }
      
      const result = await tool.safeExecute(parameters);
      results.push({
        tool_name,
        ...result
      });
    }
    
    return results;
  }
}

// 全局单例实例
export const toolRegistry = new ToolRegistry(); 