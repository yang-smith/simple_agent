// 事件类型常量
export const EventTypes = {
  USER_MESSAGE: "user_message",
  AGENT_MESSAGE: "agent_message",
  TOOL_CALL: "tool_call",
  TOOL_RESULT: "tool_result",
  ERROR: "error",
  SYSTEM: "system"
};

// 创建事件的工厂函数
export function createEvent(type, data, timestamp = null) {
  return {
    type,
    timestamp: timestamp || new Date(),
    data: data || {}
  };
}

// 状态管理器工厂函数
export function createStateManager() {
  let events = [];

  // Reducer 函数 - 纯函数，返回新状态
  function reducer(currentEvents, newEvent) {
    return [...currentEvents, newEvent];
  }

  // 添加新事件到状态
  function addEvent(eventType, data) {
    const event = createEvent(eventType, data);
    events = reducer(events, event);
    return event;
  }

  // 获取当前状态
  function getState() {
    return [...events]; // 返回副本
  }

  // 按类型筛选事件
  function getEventsByType(eventType) {
    return events.filter(e => e.type === eventType);
  }

  // 清空状态
  function clearState() {
    events = [];
  }

  // 获取最近的N个事件
  function getRecentEvents(count = 10) {
    return events.slice(-count);
  }

  // 获取统计信息
  function getStats() {
    const typeStats = {};
    events.forEach(event => {
      typeStats[event.type] = (typeStats[event.type] || 0) + 1;
    });

    return {
      totalEvents: events.length,
      eventTypes: typeStats,
      firstEvent: events[0]?.timestamp,
      lastEvent: events[events.length - 1]?.timestamp
    };
  }

  return {
    addEvent,
    getState,
    getEventsByType,
    clearState,
    getRecentEvents,
    getStats
  };
}

// 默认状态管理器实例
export const defaultStateManager = createStateManager();

// 便捷函数
export function addUserMessage(content, stateManager = defaultStateManager) {
  return stateManager.addEvent(EventTypes.USER_MESSAGE, { content });
}

export function addAgentMessage(content, stateManager = defaultStateManager) {
  return stateManager.addEvent(EventTypes.AGENT_MESSAGE, { content });
}

export function addToolResult(results, stateManager = defaultStateManager) {
  return stateManager.addEvent(EventTypes.TOOL_RESULT, { results });
}

export function addToolCall(toolName, parameters, stateManager = defaultStateManager) {
  return stateManager.addEvent(EventTypes.TOOL_CALL, { toolName, parameters });
}

export function addError(error, stateManager = defaultStateManager) {
  return stateManager.addEvent(EventTypes.ERROR, { error: error.toString(), stack: error.stack });
}