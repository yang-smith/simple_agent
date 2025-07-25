import { createTool } from '../base.js';
import { createParameterSchema } from '../parameter-schema.js';
import { getRelevantMemories } from '../../memory-system/index.js';

/**
 * 创建网络搜索工具
 */
export function createMemorySearchTool() {
  return createTool({
    name: 'memory_search',
    description: '从记忆中搜索相关信息。当用户明确需要你从过往记忆中搜索相关信息时，使用这个工具。',
    parameters: [
      createParameterSchema({
        name: 'search_input',
        description: '记忆检索查询内容，应包含具体的关键词、主题或相关上下文，以精确定位记忆中的相关信息。',
        type: 'string',
        required: true
      })
    ],
    
    async execute(parameters) {
      const { search_input } = parameters;
      
      if (!search_input || !search_input.trim()) {
        throw new Error('缺少必要参数：search_input');
      }

      const searchQuery = search_input.trim();

      try {
        // 使用记忆模块的搜索功能
        
        const result = await getRelevantMemories(searchQuery);
        
        return {
          message: result,
          query: searchQuery,
          timestamp: new Date().toISOString()
        };

      } catch (error) {
        console.error('Memory search failed:', error);
        throw new Error(`记忆搜索失败: ${error.message}`);
      }
    },
  });
} 