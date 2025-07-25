/**
 * Browser Storage Implementation - Functional Style
 */
import { MemoryItem } from './base.js';

const STORAGE_PREFIX = 'memory_system_';

// 纯函数工具
const getStorageKey = (type, userId) => `${STORAGE_PREFIX}${type}_${userId}`;

const parseStorageItem = (key, defaultValue) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Parse storage item failed:', error);
    return defaultValue;
  }
};

const extractSection = (model, sectionName) => {
  const pattern = new RegExp(`<${sectionName}>(.*?)</${sectionName}>`, 's');
  const match = model.match(pattern);
  return match ? match[1].trim() : '';
};

// 短期记忆操作
export const saveShortTermMemory = async (memory) => {
  try {
    const key = getStorageKey('short_term', memory.userId);
    const existing = parseStorageItem(key, []);
    existing.push(memory.toJSON());
    localStorage.setItem(key, JSON.stringify(existing));
    return true;
  } catch (error) {
    console.error('Save short-term memory failed:', error);
    return false;
  }
};

export const getShortTermMemories = async (userId) => {
  try {
    const key = getStorageKey('short_term', userId);
    const memoriesData = parseStorageItem(key, []);
    const memories = memoriesData.map(data => MemoryItem.fromJSON(data));
    return memories.sort((a, b) => b.timestamp - a.timestamp);
  } catch (error) {
    console.error('Get short-term memories failed:', error);
    return [];
  }
};

export const deleteShortTermMemory = async (memoryId, userId) => {
  try {
    const key = getStorageKey('short_term', userId);
    const existing = parseStorageItem(key, []);
    const filtered = existing.filter(m => m.id !== memoryId);
    localStorage.setItem(key, JSON.stringify(filtered));
    return true;
  } catch (error) {
    console.error('Delete short-term memory failed:', error);
    return false;
  }
};

export const countShortTermMemories = async (userId) => {
  const memories = await getShortTermMemories(userId);
  return memories.length;
};

export const getOldestShortTermMemories = async (userId, count = 1) => {
  const memories = await getShortTermMemories(userId);
  if (memories.length === 0) return count === 1 ? null : [];
  
  const sorted = memories.sort((a, b) => a.timestamp - b.timestamp);
  return count === 1 ? sorted[0] : sorted.slice(0, count);
};

// 长期记忆操作
export const saveLongTermMemory = async (userId, cognitiveModel) => {
  try {
    const key = getStorageKey('long_term', userId);
    localStorage.setItem(key, cognitiveModel);
    return true;
  } catch (error) {
    console.error('Save long-term memory failed:', error);
    return false;
  }
};

export const getLongTermMemory = async (userId) => {
  try {
    const key = getStorageKey('long_term', userId);
    return localStorage.getItem(key) || '';
  } catch (error) {
    console.error('Get long-term memory failed:', error);
    return '';
  }
};

export const getBaseMemory = async (userId) => {
  try {
    const cognitiveModel = await getLongTermMemory(userId);
    if (!cognitiveModel.trim()) return '';

    const bedrockModel = extractSection(cognitiveModel, 'Bedrock');
    const evolutionaryModel = extractSection(cognitiveModel, 'Evolutionary');
    
    let baseMemory = '';
    if (bedrockModel) {
      baseMemory += `<Bedrock>\n${bedrockModel}\n</Bedrock>`;
    }
    if (evolutionaryModel) {
      if (baseMemory) baseMemory += '\n\n';
      baseMemory += `<Evolutionary>\n${evolutionaryModel}\n</Evolutionary>`;
    }
    
    return baseMemory;
  } catch (error) {
    console.error('Get base memory failed:', error);
    return '';
  }
};

export const getDynamicMemory = async (userId) => {
  const cognitiveModel = await getLongTermMemory(userId);
  return extractSection(cognitiveModel, 'Dynamic');
};

// 清理操作
export const clearUserMemories = async (userId) => {
  try {
    const shortTermKey = getStorageKey('short_term', userId);
    const longTermKey = getStorageKey('long_term', userId);
    
    localStorage.removeItem(shortTermKey);
    localStorage.removeItem(longTermKey);
    
    console.log(`Cleared memories for user ${userId}`);
  } catch (error) {
    console.error('Clear user memories failed:', error);
  }
}; 