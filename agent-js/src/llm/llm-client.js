export class LLMClient {
  constructor({ model = 'google/gemini-2.5-flash', baseURL, userToken }) {
    this.model = model;
    // 统一使用网关地址
    this.baseURL = baseURL || 'https://my-llm-gateway.zy892065502.workers.dev';
    // 用户认证token - 在浏览器环境中不使用 process.env
    this.userToken = (typeof process !== 'undefined' ? process.env.GATEWAY_USER_TOKEN : null) || 'sk-gw-7f8a9b2c4d6e1f3a5b7c9d2e4f6a8b1c';
    
    if (!this.userToken) {
      throw new Error('User token is required for gateway access');
    }
  }

  async chat({ messages, temperature = 0.7, maxTokens = 1000, ...options }) {
    try {
      const requestBody = this._buildChatRequest({
        messages,
        temperature,
        maxTokens,
        ...options
      });

      const response = await this._makeRequest('/chat/completions', requestBody);
      return this._extractResponse(response);
      
    } catch (error) {
      console.error('LLM chat error:', error);
      throw new Error(`LLM request failed: ${error.message}`);
    }
  }

  async *chatStream({ messages, temperature = 0.7, maxTokens = 1000, ...options }) {
    try {
      const requestBody = this._buildChatRequest({
        messages,
        temperature,
        maxTokens,
        stream: true,
        ...options
      });

      const response = await this._makeStreamRequest('/chat/completions', requestBody);
      
      for await (const chunk of this._parseStreamResponse(response)) {
        if (chunk) {
          yield chunk;
        }
      }
      
    } catch (error) {
      console.error('LLM stream error:', error);
      throw new Error(`LLM stream failed: ${error.message}`);
    }
  }

  async embedding({ input, model, ...options }) {
    try {
      const requestBody = {
        model: model || this.model,
        input: Array.isArray(input) ? input : [input],
        ...options
      };

      const response = await this._makeRequest('/embeddings', requestBody);
      return this._extractEmbeddingResponse(response);
      
    } catch (error) {
      console.error('LLM embedding error:', error);
      throw new Error(`LLM embedding failed: ${error.message}`);
    }
  }

  _buildChatRequest({ messages, temperature, maxTokens, stream = false, ...options }) {
    const request = {
      model: this.model,
      messages: this._formatMessages(messages),
      temperature,
      max_tokens: maxTokens,
      stream,
      ...options
    };

    return request;
  }

  _formatMessages(messages) {
    if (!Array.isArray(messages)) {
      return [{ role: 'user', content: String(messages) }];
    }
    
    return messages.map(msg => ({
      role: msg.role || 'user',
      content: String(msg.content || msg)
    }));
  }

  async _makeRequest(endpoint, body) {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.userToken}`
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return await response.json();
  }

  async _makeStreamRequest(endpoint, body) {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.userToken}`
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return response;
  }

  async *_parseStreamResponse(response) {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append new chunk to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines from buffer
        while (true) {
          const lineEnd = buffer.indexOf('\n');
          if (lineEnd === -1) break;

          const line = buffer.slice(0, lineEnd).trim();
          buffer = buffer.slice(lineEnd + 1);

          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices[0]?.delta?.content;
              if (content) {
                yield content;
              }
            } catch (e) {
              // Ignore invalid JSON
            }
          }
        }
      }
    } finally {
      reader.cancel();
    }
  }

  _extractResponse(response) {
    if (response.choices && response.choices[0]) {
      const choice = response.choices[0];
      
      return choice.message?.content || choice.text || '';
    }
    
    return response.content || '';
  }

  _extractStreamChunk(chunk) {
    if (chunk.choices && chunk.choices[0]) {
      const delta = chunk.choices[0].delta;
      return delta?.content || '';
    }
    return '';
  }

  _extractEmbeddingResponse(response) {
    if (response.data && response.data.length > 0) {
      return response.data.map(item => ({
        embedding: item.embedding,
        index: item.index
      }));
    }
    
    return response;
  }
} 