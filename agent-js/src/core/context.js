export function createContextBuilder(options = {}) {
  const maxContextLength = options.maxContextLength || 8000;
  
  return {
    createContextFromState,
    _getSystemPrompt,
    _formatEvents,
    _getBaseInfoSection,
    _getOutputFormat,
    _truncateContext
  };

  async function createContextFromState(events) {
    const messages = [];

    messages.push({
      role: "system",
      content: _getSystemPrompt()
    });
    
    const contextParts = [];
    
    // 1. 基础信息部分
    contextParts.push(_getBaseInfoSection());
    
    // 2. 工具系统部分
    const toolsSection = await _getToolsSection();
    contextParts.push(toolsSection);
    
    // 3. 记忆系统部分
    const memorySection = await _getMemorySection();
    contextParts.push(memorySection);
    
    // 4. 历史记录部分
    const historySection = _getHistorySection(events);
    contextParts.push(historySection);

    let fullContext = contextParts.join("\n\n");
    
    // 如果超长，进行智能截断
    if (fullContext.length > maxContextLength) {
      fullContext = await _truncateContext(fullContext, events);
    }
        
    messages.push({
      role: "user",
      content: fullContext
    });

    return messages;
  }

  function _getSystemPrompt() {
    return `
你是一个真诚的人。
你对第一性原理，多维度思考，批判性思考，逆向思维，系统理论、行为心理学、群体心理学、传播学、经济学、认知论、演化心理学、生物学、进化论等领域都有深刻的见解。
你尊重事实，实事求是，逻辑严密。你会指出用户存在的事实错误或逻辑错误。
你的语言风格自然质朴，说人话，有自己鲜明的观点，不会只顾着面面俱到。你不会简单地附和用户，你会说出你自己的想法。
你每次不会说过多的内容，因为人都有认知负荷，我们有的是时间，不急。
你要透过用户的文字感受用户背后的真实意图，真正地看见那个意图，并与那个意图进行对话。
现在是夏日傍晚，微风荡漾，你我是多年好友，在森林的小路上散步，对谈。

function调用原则：
你自由决定调用工具。工具调用完成后，根据状况思考下一步动作（直接回复用户或者继续调用function）。
在涉及用户隐私、外部资源调用（如可能产生费用）或需要用户明确授权的操作前，应优先征询用户意愿。
`;
  }
  
  function _formatEvents(events) {
    if (!events || events.length === 0) {
      return "暂无对话历史";
    }
        
    const formattedEvents = [];
    
    for (const event of events) {
      if (event.type === 'user_message') {
        const content = event.data?.content || '';
        formattedEvents.push(`用户说: ${content}`);
      } else if (event.type === 'tool_result') {
        // 适配 tools 系统的结果格式
        const results = event.data?.results || [];
        for (const result of results) {
          const toolName = result.tool_name || '';
          const success = result.success || false;
          if (success) {
            const resultData = result.result || {};
            // 统一使用工具返回的message字段
            const message = resultData.message || `${toolName}执行成功`;
            formattedEvents.push(`🔧 调用工具 [${toolName}] → ${message}`);
          } else {
            const errorMsg = result.error || '';
            formattedEvents.push(`❌ 工具调用失败 [${toolName}] → ${errorMsg}`);
          }
        }
      } else if (event.type === 'agent_message') {
        const content = event.data?.content || '';
        formattedEvents.push(`我回复: ${content}`);
      }
    }
    
    return formattedEvents.join('\n');
  }
  
  
  function _getOutputFormat() {
    return `**使用说明**：
- 需要调用工具时，使用 \`<function_calls>\` 格式
- 可在一个调用块中包含多个工具
- 工具名称和参数必须精确匹配定义
- 不需要工具时直接回复用户

**调用格式**：
\`\`\`xml
<function_calls>
<invoke name="工具名称">
<parameter name="参数名">参数值</parameter>
<parameter name="另一个参数名">另一个参数值</parameter>
</invoke>
</function_calls>
\`\`\``;
  }
  
  async function _truncateContext(context, events) {
    // 如果事件数量少于3个，直接保留最近的事件
    if (events.length <= 3) {
      return context;
    }
    
    // 计算需要移除的事件数量（最老的三分之一）
    let removeCount = Math.floor(events.length / 3);
    if (removeCount === 0) {
      removeCount = 1; // 至少移除1个
    }
    
    // 获取最老的事件（按时间正序排列）
    const sortedEvents = [...events].sort((a, b) => a.timestamp - b.timestamp);
    const oldestEvents = sortedEvents.slice(0, removeCount);
    
    // 将最老的事件转换为记忆系统的states格式
    const statesForMemory = oldestEvents.map(event => event.data);
    
    // 异步调度记忆更新
    try {
      const { updateMemory } = await import('../memory-system/index.js');
      await updateMemory(statesForMemory, { userId: "default", forceProcess: true });
      console.log(`已调度 ${oldestEvents.length} 个事件的记忆存储`);
    } catch (error) {
      console.warn('Memory update scheduling failed:', error);
    }
    
    // 保留剩余的事件
    const remainingEvents = sortedEvents.slice(removeCount);
    // 按原始顺序重新排列
    const recentEvents = remainingEvents.sort((a, b) => a.timestamp - b.timestamp);
    
    // 重新构建上下文时也使用新的格式
    const contextParts = [
      _getBaseInfoSection(),
      await _getToolsSection(),
      await _getMemorySection(),
      _getHistorySection(recentEvents)
    ];
    
    const truncatedNote = `\n> ⚠️ 由于上下文长度限制，已将 ${removeCount} 个最早的对话存储到记忆中\n`;
    
    return contextParts.join("\n\n") + truncatedNote;
  }

  function _getBaseInfoSection() {
    const today = new Date().toLocaleString('zh-CN');
    return `
## 基础信息
- 当前时间：${today}`;
  }

  async function _getToolsSection() {
    try {
      const { getFunctionsXML } = await import('../tools/index.js');
      const toolsXML = getFunctionsXML();
      
      return `## 可用工具

### 工具定义
${toolsXML}

### 工具调用格式
${_getOutputFormat()}`;
    } catch (error) {
      console.warn('Tools system not available:', error);
      return `## 工具系统
⚠️ 工具系统暂不可用：${error.message}`;
    }
  }

  async function _getMemorySection() {
    try {
      const { getBaseMemory } = await import('../memory-system/index.js');
      const memoryContent = await getBaseMemory({ userId: "default" });
      
      if (!memoryContent || memoryContent.trim() === '') {
        return ``;
      }
      
      return `## 记忆内容
${memoryContent}`;
    } catch (error) {
      console.warn('Memory system not available:', error);
      return `## 记忆系统
⚠️ 记忆系统暂不可用：${error.message}`;
    }
  }

  function _getHistorySection(events) {
    const formattedEvents = _formatEvents(events);
    
    return `## 对话历史
> 📌 说明：以下是本次会话的历史记录，包括用户消息、AI回复和工具执行结果
> 用户可见对话历史，但工具调用过程对用户不可见

${formattedEvents}`;
  }
}

// 创建默认的上下文构建器实例
export const defaultContextBuilder = createContextBuilder();

// 便捷函数
export async function createContextFromState(events, options = {}) {
  const builder = createContextBuilder(options);
  return builder.createContextFromState(events);
}
