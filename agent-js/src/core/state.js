import { v4 as uuidv4 } from 'uuid';

export class State {
  constructor() {
    this.currentSession = null;
    this.sessions = new Map();
    this.globalContext = {};
  }

  updateUserMessage(message, sessionId = null) {
    if (!sessionId) {
      sessionId = uuidv4();
    }
    
    this.currentSession = sessionId;
    
    if (!this.sessions.has(sessionId)) {
      this.sessions.set(sessionId, {
        id: sessionId,
        messages: [],
        startTime: new Date(),
        lastUpdate: new Date(),
        metadata: {}
      });
    }
    
    const session = this.sessions.get(sessionId);
    session.messages.push({
      role: 'user',
      content: message,
      timestamp: new Date(),
      id: uuidv4()
    });
    
    session.lastUpdate = new Date();
  }

  updateAssistantMessage(message, sessionId = null) {
    sessionId = sessionId || this.currentSession;
    
    if (!sessionId || !this.sessions.has(sessionId)) {
      console.warn('No active session for assistant message');
      return;
    }
    
    const session = this.sessions.get(sessionId);
    session.messages.push({
      role: 'assistant',
      content: message,
      timestamp: new Date(),
      id: uuidv4()
    });
    
    session.lastUpdate = new Date();
  }

  getCurrentSession() {
    if (!this.currentSession) return null;
    return this.sessions.get(this.currentSession);
  }

  getSession(sessionId) {
    return this.sessions.get(sessionId);
  }

  getRecentMessages(count = 10, sessionId = null) {
    sessionId = sessionId || this.currentSession;
    
    if (!sessionId || !this.sessions.has(sessionId)) {
      return [];
    }
    
    const session = this.sessions.get(sessionId);
    return session.messages.slice(-count);
  }

  getAllSessions() {
    return Array.from(this.sessions.values());
  }

  setGlobalContext(key, value) {
    this.globalContext[key] = value;
  }

  getGlobalContext(key) {
    return this.globalContext[key];
  }

  clearSession(sessionId) {
    this.sessions.delete(sessionId);
    if (this.currentSession === sessionId) {
      this.currentSession = null;
    }
  }

  clearAllSessions() {
    this.sessions.clear();
    this.currentSession = null;
  }

  getStats() {
    return {
      totalSessions: this.sessions.size,
      currentSession: this.currentSession,
      totalMessages: Array.from(this.sessions.values())
        .reduce((sum, session) => sum + session.messages.length, 0),
      globalContextKeys: Object.keys(this.globalContext)
    };
  }
} 