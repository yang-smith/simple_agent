import { createTool } from '../base.js';
import { createParameterSchema } from '../parameter-schema.js';
import { chat } from '../../llm/llm-client.js';

/**
 * 创建网络搜索工具
 */
export function createWebSearchTool() {
  return createTool({
    name: 'web_search',
    description: '通过网络搜索获取信息。当用户提出外部搜索或需要查询最新数据、时事新闻、实时状态或当前知识库无法提供准确答案时使用此工具。',
    parameters: [
      createParameterSchema({
        name: 'search_input',
        description: '具体的搜索查询内容，应包含明确的关键词和上下文信息，以确保搜索结果的准确性和相关性。',
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
        // 使用简化的 chat 接口，会自动获取用户 token
        const result = await chat({
          model: 'perplexity/sonar',
          messages: [{ role: 'user', content: searchQuery }],
          temperature: 0.3,
          maxTokens: 2000
        });

        return {
          message: result,
          query: searchQuery,
          timestamp: new Date().toISOString()
        };

      } catch (error) {
        console.error('Web search failed:', error);
        throw new Error(`网络搜索失败: ${error.message}`);
      }
    },
  });
} 