/**
 * Memory Management Functions - Coordination layer
 */
import { processStates, performBatchCognitiveReconstruction } from './memory-processor.js';
import * as storage from './storage.js';

const checkAndReconstruct = async (userId, config) => {
  try {
    const count = await storage.countShortTermMemories(userId);
    if (count <= config.SHORT_TERM_MAX_COUNT) return;
    
    console.log(`User ${userId} short-term memory overflow, starting batch cognitive reconstruction...`);
    
    const batchMemories = await storage.getOldestShortTermMemories(userId, config.PROMOTION_BATCH_SIZE);
    if (batchMemories.length === 0) return;
    
    const success = await performBatchCognitiveReconstruction(userId, batchMemories);
    
    // Delete processed memories
    for (const memory of batchMemories) {
      await storage.deleteShortTermMemory(memory.id, userId);
    }
    
    if (success) {
      console.log(`Batch cognitive reconstruction completed: ${batchMemories.length} memories processed`);
    }
    
    // Recursive check for remaining overflow
    const stillOverflow = await storage.countShortTermMemories(userId) > config.SHORT_TERM_MAX_COUNT;
    if (stillOverflow) {
      await checkAndReconstruct(userId, config);
    }
  } catch (error) {
    console.error('Cognitive reconstruction check failed:', error);
  }
};

export const updateMemory = async (states, userId = 'default', config, forceProcess = false) => {
  if (!states || states.length === 0) return;
  
  try {
    const shortMemory = await processStates(states, userId, config, forceProcess);
    if (shortMemory) {
      await checkAndReconstruct(userId, config);
    }
  } catch (error) {
    console.error('Update memory failed:', error);
  }
};
