import { createTool } from '../base.js';
import { createParameterSchema } from '../parameter-schema.js';
import { LLMClient } from '../../llm/llm-client.js';

/**
 * 创建网络搜索工具
 */
export function createWebSearchTool() {
  return createTool({
    name: 'web_search',
    description: '从网络中搜索相关信息。当用户明确需要外部检索时或者你的知识库里明确没有相关信息时候，使用这个工具。',
    parameters: [
      createParameterSchema({
        name: 'search_input',
        description: '需要搜索的相关内容。用于去网络查询。',
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
        const searchClient = new LLMClient({
          model: 'perplexity/sonar',
        });

        // 使用perplexity/sonar模型进行网络搜索
        const result = await searchClient.chat({
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