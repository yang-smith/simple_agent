/**
 * Memory System Utilities - Pure functions
 */

export const estimateTokenCount = (states) => {
  return states.reduce((total, state) => {
    const text = typeof state === 'object' ? JSON.stringify(state) : String(state);
    return total + text.length;
  }, 0);
};

export const calculateKeywordScore = (query, content) => {
  const queryLower = query.toLowerCase();
  const contentLower = content.toLowerCase();
  
  const queryWords = new Set(queryLower.match(/[a-zA-Z]+/g) || []);
  const contentWords = new Set(contentLower.match(/[a-zA-Z]+/g) || []);
  
  const queryChars = new Set();
  const contentChars = new Set();
  
  const chineseCharsQuery = query.match(/[\u4e00-\u9fff]/g) || [];
  if (chineseCharsQuery.length >= 2) {
    for (let i = 0; i < chineseCharsQuery.length - 1; i++) {
      queryChars.add(chineseCharsQuery[i] + chineseCharsQuery[i + 1]);
      if (i < chineseCharsQuery.length - 2) {
        queryChars.add(chineseCharsQuery[i] + chineseCharsQuery[i + 1] + chineseCharsQuery[i + 2]);
      }
    }
  }
  
  const chineseCharsContent = content.match(/[\u4e00-\u9fff]/g) || [];
  if (chineseCharsContent.length >= 2) {
    for (let i = 0; i < chineseCharsContent.length - 1; i++) {
      contentChars.add(chineseCharsContent[i] + chineseCharsContent[i + 1]);
      if (i < chineseCharsContent.length - 2) {
        contentChars.add(chineseCharsContent[i] + chineseCharsContent[i + 1] + chineseCharsContent[i + 2]);
      }
    }
  }
  
  const totalQueryTerms = queryWords.size + queryChars.size;
  if (totalQueryTerms === 0) return 0.0;
  
  const wordIntersection = new Set([...queryWords].filter(x => contentWords.has(x)));
  const charIntersection = new Set([...queryChars].filter(x => contentChars.has(x)));
  
  const totalMatches = wordIntersection.size + charIntersection.size;
  if (totalMatches === 0) return 0.0;
  
  let score = totalMatches / totalQueryTerms;
  if (contentLower.includes(queryLower)) {
    score += 0.3;
  }
  
  return score;
};

export const initializeCognitiveModel = () => `<Bedrock>

</Bedrock>

<Evolutionary>

</Evolutionary>

<Dynamic>

</Dynamic>`;

export const createMemoryBatch = (memories) => {
  return memories.map(memory => {
    const timestampStr = memory.timestamp.toLocaleString('zh-CN');
    return `[${timestampStr}] ${memory.content}`;
  }).join('\n\n');
};

export const shouldProcessStates = (states, threshold, forceProcess) => {
  if (!states || states.length === 0) return false;
  if (forceProcess) return true;
  
  const tokenCount = estimateTokenCount(states);
  return tokenCount >= threshold;
};

export const findRelevantMemories = (query, memories, maxResults = 3) => {
  const candidates = memories
    .map(memory => ({
      memory,
      score: calculateKeywordScore(query, memory.content)
    }))
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, maxResults);
    
  return candidates.map(({ memory }) => memory);
}; 