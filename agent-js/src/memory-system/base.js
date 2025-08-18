/**
 * Memory System Base Classes and Interfaces
 */

export class MemoryItem {
  constructor({
    id = null,
    content = '',
    embedding = [],
    timestamp = null,
    hp = 1,
    userId = ''
  } = {}) {
    this.id = id || generateId();
    this.content = content;
    this.embedding = embedding;
    this.timestamp = timestamp || new Date();
    this.hp = hp;
    this.userId = userId;
  }

  toJSON() {
    return {
      id: this.id,
      content: this.content,
      embedding: this.embedding,
      timestamp: this.timestamp.toISOString(),
      hp: this.hp,
      userId: this.userId
    };
  }

  static fromJSON(data) {
    return new MemoryItem({
      ...data,
      timestamp: new Date(data.timestamp)
    });
  }
}

// 纯函数工具
export const generateId = () => 'mem_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);

export const defaultConfig = {
  // 状态处理阈值：超过此token数量才会触发状态压缩处理
  STATES_TOKEN_THRESHOLD: 5000,
  
  // 短期记忆最大数量：超过此数量会触发批量认知重构
  SHORT_TERM_MAX_COUNT: 50,
  
  // 晋升批次大小：每次认知重构处理的短期记忆数量
  PROMOTION_BATCH_SIZE: 3,
  
  // 短期记忆热缓存大小：保留在快速访问缓存中的记忆数量
  SHORT_TERM_HOT_CACHE_SIZE: 5,
  
  // 相关性阈值：记忆检索时的最低相关性分数要求
  RELEVANCE_THRESHOLD: 0.6,
  
  // 上下文中最大记忆数量：单次查询返回的最大记忆条数
  MAX_MEMORIES_IN_CONTEXT: 3,
  
  // 深度搜索限制：深度记忆检索时的最大搜索范围
  DEEP_SEARCH_LIMIT: 20,
  
  // 关键词权重：在混合检索中关键词匹配的权重比例
  KEYWORD_WEIGHT: 0.5,
  
  // 向量权重：在混合检索中向量相似度的权重比例
  VECTOR_WEIGHT: 0.5
};

export const createConfig = (overrides = {}) => ({ ...defaultConfig, ...overrides });