export class LLMClient {
  constructor({ apiKey, model = 'google/gemini-2.5-flash', baseURL }) {
    this.apiKey = apiKey;
    this.model = model;
    this.baseURL = baseURL || this._getDefaultBaseURL(model);
    
    if (!this.apiKey) {
      throw new Error('API key is required for LLM client');
    }
  }

  _getDefaultBaseURL(model) {
    if (model.startsWith('google/')) {
      return 'https://generativelanguage.googleapis.com/v1beta';
    }
    // 可以扩展支持其他LLM提供商
    return 'https://api.openai.com/v1';
  }

  async chat({ messages, tools, temperature = 0.7, maxTokens = 1000, ...options }) {
    try {
      const requestBody = this._buildChatRequest({
        messages,
        tools,
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

  async *chatStream({ messages, tools, temperature = 0.7, maxTokens = 1000, ...options }) {
    try {
      const requestBody = this._buildChatRequest({
        messages,
        tools,
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

  _buildChatRequest({ messages, tools, temperature, maxTokens, stream = false, ...options }) {
    const request = {
      model: this.model,
      messages: this._formatMessages(messages),
      temperature,
      max_tokens: maxTokens,
      stream,
      ...options
    };

    if (tools && tools.length > 0) {
      request.tools = this._formatTools(tools);
    }

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

  _formatTools(tools) {
    return tools.map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters || {}
      }
    }));
  }

  async _makeRequest(endpoint, body) {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json'
    };

    // 根据不同的模型提供商设置认证头
    if (this.model.startsWith('google/')) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    } else {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

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
      'Content-Type': 'application/json'
    };

    if (this.model.startsWith('google/')) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    } else {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

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
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              const content = this._extractStreamChunk(parsed);
              if (content) {
                yield content;
              }
            } catch (e) {
              // 忽略解析错误的行
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  _extractResponse(response) {
    if (response.choices && response.choices[0]) {
      const choice = response.choices[0];
      
      // 处理工具调用
      if (choice.message && choice.message.tool_calls) {
        return {
          content: choice.message.content,
          tool_calls: choice.message.tool_calls
        };
      }
      
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
} 