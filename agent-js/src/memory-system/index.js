/**
 * Memory System - Main Interface
 */
import { MemoryItem, createConfig } from './base.js';
import * as storage from './storage.js';
import { updateMemory } from './memory-manager.js';
import { calculateKeywordScore, findRelevantMemories } from './utils.js';

export const getRelevantMemories = async (userInput, userId = 'default', config = null) => {
  if (!userInput.trim()) return '';
  
  const cfg = config || createConfig();
  
  try {
    const candidates = [];
    
    // 1. 从短期记忆检索
    const shortMemories = await storage.getShortTermMemories(userId);
    const recentMemories = shortMemories.slice(0, 20);
    
    const relevantShortMemories = findRelevantMemories(userInput, recentMemories);
    relevantShortMemories.forEach(memory => {
      const score = calculateKeywordScore(userInput, memory.content);
      candidates.push([score, memory.content, '短期记忆']);
    });
    
    // 2. 从长期记忆Dynamic部分检索
    const dynamicModel = await storage.getDynamicMemory(userId);
    if (dynamicModel.trim()) {
      const dynamicSections = dynamicModel.split('\n\n').filter(s => s.trim());
      
      const mockMemories = dynamicSections.map(section => ({ content: section }));
      const relevantDynamicMemories = findRelevantMemories(userInput, mockMemories);
      
      relevantDynamicMemories.forEach(memory => {
        const score = calculateKeywordScore(userInput, memory.content);
        candidates.push([score, memory.content, '长期记忆Dynamic']);
      });
    }
    
    if (candidates.length === 0) return '';
    
    candidates.sort((a, b) => b[0] - a[0]);
    const top3 = candidates.slice(0, 3);
    const memoryStrings = top3.map(item => item[1]);
    
    return JSON.stringify(memoryStrings);
    
  } catch (error) {
    console.error('Memory retrieval failed:', error);
    return '';
  }
};

export const getBaseMemory = async (userId = 'default') => {
  return await storage.getBaseMemory(userId);
};

// Re-export main functions
export { updateMemory };

// Re-export base classes and utilities
export { MemoryItem, createConfig };
export * as storage from './storage.js'; 