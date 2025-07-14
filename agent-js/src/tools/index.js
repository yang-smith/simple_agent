import { toolManager } from './tool-list.js';
import { toolRegistry } from './registry.js';

/**
 * 统一工具调用接口
 */
export async function executeToolCall(toolName, params) {
  const tool = toolRegistry.getTool(toolName);
  if (!tool) {
    throw new Error(`Tool '${toolName}' not found`);
  }
  
  return await tool.safeExecute(params);
}

/**
 * 获取工具定义 XML
 */
export function getFunctionsXML() {
  return toolManager.getFunctionsXML();
}

/**
 * 解析并执行工具调用
 */
export async function parseAndExecuteFunctionCalls(llmResponse) {
  return await toolManager.parseAndExecute(llmResponse);
}

/**
 * 初始化工具系统
 */
export async function initializeTools() {
  await toolManager.initialize();
}

/**
 * 注册自定义工具
 */
export function registerTool(tool) {
  toolManager.registerTool(tool);
}

// 导出核心函数和类
export { createTool, isValidTool } from './base.js';
export { createParameterSchema } from './parameter-schema.js';
export { ToolRegistry, toolRegistry } from './registry.js';
export { ToolManager, toolManager } from './tool-list.js';