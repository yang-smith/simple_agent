



export default {
  async fetch(request, env) {
    // 处理预检请求 (OPTIONS)
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          'Access-Control-Max-Age': '86400', // 24小时
        }
      });
    }

    // 用户验证
    const authResult = authenticateUser(request, env);
    if (!authResult.success) {
      return new Response(JSON.stringify({ error: authResult.error }), {
        status: 401,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
      });
    }
    
    try {
      // 解析请求体以获取模型信息
      const requestBody = await request.json();
      const model = requestBody.model || 'google/gemini-2.5-flash';
      
      // 根据模型决定目标URL和API Key
      const routeInfo = getRouteInfo(model, env);
      
      // 创建新请求
      const newRequest = new Request(routeInfo.url, {
        method: request.method,
        headers: request.headers,
        body: JSON.stringify(requestBody)
      });
      
      // 设置对应的API Key
      newRequest.headers.set('Authorization', `Bearer ${routeInfo.apiKey}`);
      
      // 如果是OpenRouter，设置额外的头部
      if (routeInfo.url.includes('openrouter')) {
        newRequest.headers.set('HTTP-Referer', 'simple-test');
        newRequest.headers.set('X-Title', 'simple-agent');
      }
      
      // 发起请求
      const response = await fetch(newRequest);
      
      // 创建新的响应头部，确保不重复CORS头部
      const responseHeaders = new Headers();
      
      // 复制原响应的头部，但跳过CORS相关的头部
      for (const [key, value] of response.headers.entries()) {
        if (!key.toLowerCase().startsWith('access-control-')) {
          responseHeaders.set(key, value);
        }
      }
      
      // 添加我们自己的CORS头部
      responseHeaders.set('Access-Control-Allow-Origin', '*');
      responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      
      // 创建新的响应
      const newResponse = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });
      
      return newResponse;
      
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
      });
    }
  }
};

function authenticateUser(request, env) {
  const authHeader = request.headers.get('Authorization');
  
  if (!authHeader) {
    return { success: false, error: 'Missing Authorization header' };
  }
  
  // 支持 Bearer token 格式
  const token = authHeader.replace('Bearer ', '');
  
  // 检查token是否在允许的列表中
  const validTokens = env.VALID_TOKENS ? env.VALID_TOKENS.split(',') : [];
  
  if (!validTokens.includes(token)) {
    return { success: false, error: 'Invalid token' };
  }
  
  return { success: true };
}

function getRouteInfo(model, env) {
  // 如果是embedding模型，使用dmxapi
  if (model.includes('embedding') || model.includes('embed')) {
    return {
      url: 'https://www.dmxapi.com/v1/chat/completions',
      apiKey: env.DMXAPI_API_KEY
    };
  }
  
  // 其余默认使用openrouter
  return {
    url: 'https://openrouter.ai/api/v1/chat/completions', 
    apiKey: env.OPENROUTER_API_KEY
  };
}