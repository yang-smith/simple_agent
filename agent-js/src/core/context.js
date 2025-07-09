export class Context {
  constructor(memorySystem, toolRegistry) {
    this.memorySystem = memorySystem;
    this.toolRegistry = toolRegistry;
  }

  async build(userMessage, state, options = {}) {
    const context = {
      messages: [],
      tools: [],
      memories: [],
      metadata: {}
    };

    try {
      // 1. 构建消息历史
      await this._buildMessageHistory(context, userMessage, state, options);
      
      // 2. 检索相关记忆
      await this._retrieveRelevantMemories(context, userMessage, options);
      
      // 3. 准备可用工具
      await this._prepareTools(context, userMessage, options);
      
      // 4. 构建系统提示
      await this._buildSystemPrompt(context, options);
      
      return context;
      
    } catch (error) {
      console.error('Context building error:', error);
      throw error;
    }
  }

  async _buildMessageHistory(context, userMessage, state, options) {
    const maxHistory = options.maxHistory || 10;
    
    // 获取最近的消息历史
    const recentMessages = state.getRecentMessages(maxHistory);
    
    // 添加系统消息占位符（稍后填充）
    context.messages.push({
      role: 'system',
      content: '' // 将在 _buildSystemPrompt 中填充
    });
    
    // 添加历史消息
    context.messages.push(...recentMessages);
    
    // 添加当前用户消息
    context.messages.push({
      role: 'user',
      content: userMessage
    });
  }

  async _retrieveRelevantMemories(context, userMessage, options) {
    if (!this.memorySystem) return;
    
    try {
      const maxMemories = options.maxMemories || 5;
      const memories = await this.memorySystem.retrieve(userMessage, {
        limit: maxMemories,
        threshold: options.memoryThreshold || 0.7
      });
      
      context.memories = memories;
    } catch (error) {
      console.warn('Memory retrieval failed:', error);
    }
  }

  async _prepareTools(context, userMessage, options) {
    if (!this.toolRegistry || options.disableTools) return;
    
    try {
      // 获取所有可用工具
      const availableTools = this.toolRegistry.getAllTools();
      
      // 可以在这里添加工具筛选逻辑
      // 比如根据用户消息内容判断需要哪些工具
      context.tools = availableTools.map(tool => ({
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters
      }));
      
    } catch (error) {
      console.warn('Tool preparation failed:', error);
    }
  }

  async _buildSystemPrompt(context, options) {
    const parts = [];
    
    // 基础系统提示
    parts.push(this._getBaseSystemPrompt());
    
    // 添加记忆信息
    if (context.memories.length > 0) {
      parts.push(this._buildMemorySection(context.memories));
    }
    
    // 添加工具信息
    if (context.tools.length > 0) {
      parts.push(this._buildToolSection(context.tools));
    }
    
    // 添加自定义指令
    if (options.systemPrompt) {
      parts.push(options.systemPrompt);
    }
    
    // 更新系统消息
    if (context.messages[0] && context.messages[0].role === 'system') {
      context.messages[0].content = parts.join('\n\n');
    }
  }

  _getBaseSystemPrompt() {
    return `你是一个智能助手，具有记忆能力和工具使用能力。

核心原则：
1. 根据用户的问题提供准确、有用的回答
2. 利用历史记忆来提供连贯的对话体验
3. 必要时使用可用的工具来获取信息或执行任务
4. 保持友好、专业的语调

请根据用户的问题，结合提供的记忆信息和可用工具，给出最佳回答。`;
  }

  _buildMemorySection(memories) {
    const memoryTexts = memories.map(memory => 
      `- ${memory.content} (${memory.timestamp || '时间未知'})`
    );
    
    return `相关记忆信息：
${memoryTexts.join('\n')}`;
  }

  _buildToolSection(tools) {
    const toolDescriptions = tools.map(tool => 
      `- ${tool.name}: ${tool.description}`
    );
    
    return `可用工具：
${toolDescriptions.join('\n')}

当需要使用工具时，请按照标准格式调用。`;
  }
} 