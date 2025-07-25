/**
 * Memory Processing Functions - Pure and side-effect separated
 */
import { MemoryItem } from './base.js';
import { summarizeStates, cognitiveReconstruction } from './llm-operations.js';
import { estimateTokenCount, shouldProcessStates, createMemoryBatch, initializeCognitiveModel } from './utils.js';
import * as storage from './storage.js';

export const processStates = async (states, userId = 'default', config, forceProcess = false) => {
  if (!shouldProcessStates(states, config.STATES_TOKEN_THRESHOLD, forceProcess)) {
    const tokenCount = estimateTokenCount(states);
    console.log(`Token count (${tokenCount}) below threshold (${config.STATES_TOKEN_THRESHOLD})`);
    return null;
  }
  
  const tokenCount = estimateTokenCount(states);
  console.log(`Processing states: ${states.length} events, ${tokenCount} tokens`);
  
  try {
    const summaryContent = await summarizeStates(states);
    if (!summaryContent?.trim()) {
      console.log('LLM summary generation failed');
      return null;
    }
    
    const shortMemory = new MemoryItem({
      content: summaryContent,
      timestamp: new Date(),
      hp: 1,
      userId
    });
    
    const success = await storage.saveShortTermMemory(shortMemory);
    if (success) {
      console.log(`Short-term memory saved: ${shortMemory.id}`);
      return shortMemory;
    } else {
      console.log('Short-term memory save failed');
      return null;
    }
  } catch (error) {
    console.error('Process states failed:', error);
    return null;
  }
};

export const performCognitiveReconstruction = async (userId, newStimuli) => {
  try {
    const currentModel = await storage.getLongTermMemory(userId) || 
                        initializeCognitiveModel();
    
    const newModel = await cognitiveReconstruction(currentModel, newStimuli);
    if (newModel.trim()) {
      const success = await storage.saveLongTermMemory(userId, newModel);
      if (success) {
        console.log(`Cognitive reconstruction completed: ${userId}`);
        return true;
      }
    }
    return false;
  } catch (error) {
    console.error('Cognitive reconstruction failed:', error);
    return false;
  }
};

export const performBatchCognitiveReconstruction = async (userId, memories) => {
  const combinedContent = createMemoryBatch(memories);
  return await performCognitiveReconstruction(userId, combinedContent);
}; 