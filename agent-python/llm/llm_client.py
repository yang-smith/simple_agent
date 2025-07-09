import os
import httpx
import tiktoken
import asyncio
import json
from typing import Union, List, Dict, Any, Optional, AsyncGenerator, Generator
from aiolimiter import AsyncLimiter
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class AIConfig:
    """AI聊天配置管理"""
    DEFAULT_TEMPERATURE = 0.05
    DEFAULT_SYSTEM_MESSAGE = "You are a helpful assistant."
    DEFAULT_TIMEOUT = 200
    MAX_CONCURRENT_REQUESTS = 10


class ClientManager:
    """OpenAI客户端管理器"""
    
    @staticmethod
    def get_client(model: str, is_async: bool = False) -> Union[OpenAI, AsyncOpenAI]:
        """根据模型和类型返回适当的OpenAI客户端"""
        client_class = AsyncOpenAI if is_async else OpenAI
        
        # OpenRouter 模型 (包含 '/' 的模型名称)
        if '/' in model:
            return ClientManager._get_openrouter_client(client_class)
        
        # Deepseek 模型
        if model in ['deepseek-v3-0324', 'deepseek-r1', 'deepseek-v3']:
            return ClientManager._get_deepseek_client(client_class)
        
        # 默认 OpenAI 模型
        return ClientManager._get_openai_client(client_class)
    
    @staticmethod
    def _get_openrouter_client(client_class):
        """获取OpenRouter客户端"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("OPENROUTER_API_KEY is not set")
        base_url = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        
        if not api_key:
            raise ValueError("Missing required environment variable: OPENROUTER_API_KEY")
        
        return client_class(api_key=api_key, base_url=base_url)
    
    @staticmethod
    def _get_deepseek_client(client_class):
        """获取Deepseek客户端"""
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("DEEPSEEK_API_KEY is not set")
        base_url = os.environ.get("DEEPSEEK_API_BASE")
        
        if not api_key or not base_url:
            raise ValueError(
                "Missing required environment variables for Deepseek: "
                "DEEPSEEK_API_KEY and DEEPSEEK_API_BASE must be set"
            )
        
        return client_class(api_key=api_key, base_url=base_url)
    
    @staticmethod
    def _get_openai_client(client_class):
        """获取OpenAI客户端"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY is not set")
        base_url = os.environ.get("OPENAI_API_BASE")
        
        if not api_key:
            raise ValueError("Missing required environment variable: OPENAI_API_KEY")
        
        return client_class(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1"
        )


class MessageProcessor:
    """消息处理器"""
    
    @staticmethod
    def prepare_messages(message: Union[str, List[Dict]], 
                        system_message: str = AIConfig.DEFAULT_SYSTEM_MESSAGE) -> List[Dict]:
        """准备聊天完成的消息"""
        if isinstance(message, list):
            return message
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
    
    @staticmethod
    def process_response(response_message) -> str:
        """处理响应消息，包括函数调用"""
        # 检查是否有函数调用
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            return json.dumps({
                "function_call": {
                    "name": function_name,
                    "arguments": function_args
                }
            })
        
        return response_message.content


class TokenManager:
    """Token管理工具"""
    
    @staticmethod
    def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
        """计算文本字符串中的token数量"""
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    
    @staticmethod
    def truncate_by_tokens(data_list: List[str], max_tokens: int) -> List[str]:
        """根据token大小截断数据列表"""
        total_tokens = 0
        for i, data in enumerate(data_list):
            total_tokens += TokenManager.count_tokens(data)
            if total_tokens > max_tokens:
                return data_list[:i]
        return data_list


class AIChat:
    """AI聊天主类"""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(AIConfig.MAX_CONCURRENT_REQUESTS)
    
    def _build_kwargs(self, messages: List[Dict], model: str, 
                     response_format: str, tools: Optional[List], 
                     stream: bool = False) -> Dict[str, Any]:
        """构建API调用参数"""
        kwargs = {
            "messages": messages,
            "model": model,
            "temperature": AIConfig.DEFAULT_TEMPERATURE
        }
        
        if stream:
            kwargs["stream"] = True
        
        if response_format == 'json':
            kwargs["response_format"] = {"type": "json_object"}
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        return kwargs
    
    def chat(self, message: Union[str, List[Dict]], 
             model: str = "google/gemini-2.5-flash", 
             response_format: str = 'NOT_GIVEN', 
             tools: Optional[List] = None) -> str:
        """同步聊天完成"""
        client = ClientManager.get_client(model)
        messages = MessageProcessor.prepare_messages(message)
        kwargs = self._build_kwargs(messages, model, response_format, tools)
        
        chat_completion = client.chat.completions.create(**kwargs)
        return MessageProcessor.process_response(chat_completion.choices[0].message)
    
    async def chat_async(self, message: Union[str, List[Dict]], 
                        model: str = "google/gemini-2.5-flash", 
                        response_format: str = 'NOT_GIVEN', 
                        tools: Optional[List] = None) -> str:
        """异步聊天完成"""
        client = ClientManager.get_client(model, is_async=True)
        messages = MessageProcessor.prepare_messages(message)
        kwargs = self._build_kwargs(messages, model, response_format, tools)
        
        try:
            async with self.semaphore:
                chat_completion = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=AIConfig.DEFAULT_TIMEOUT
                )
            return MessageProcessor.process_response(chat_completion.choices[0].message)
        except asyncio.TimeoutError:
            raise TimeoutError(f"API request timed out after {AIConfig.DEFAULT_TIMEOUT} seconds")
    
    def chat_stream(self, message: Union[str, List[Dict]], 
                   model: str = "google/gemini-2.5-flash", 
                   response_format: str = 'NOT_GIVEN',
                   tools: Optional[List] = None) -> Generator[str, None, None]:
        """流式聊天完成"""
        client = ClientManager.get_client(model)
        messages = MessageProcessor.prepare_messages(message)
        kwargs = self._build_kwargs(messages, model, response_format, tools, stream=True)
        
        try:
            stream = client.chat.completions.create(**kwargs)
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        finally:
            if hasattr(client, 'close'):
                client.close()
    
    async def chat_stream_async(self, message: Union[str, List[Dict]], 
                               model: str = "google/gemini-2.5-flash", 
                               response_format: str = 'NOT_GIVEN',
                               tools: Optional[List] = None) -> AsyncGenerator[str, None]:
        """异步流式聊天完成"""
        client = ClientManager.get_client(model, is_async=True)
        messages = MessageProcessor.prepare_messages(message)
        kwargs = self._build_kwargs(messages, model, response_format, tools, stream=True)
        
        try:
            stream = await client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        finally:
            if hasattr(client, 'close'):
                await client.close()


# 全局实例和便捷函数
_ai_chat = AIChat()

def llm_call(message: Union[str, List[Dict]], 
            model: str = "google/gemini-2.5-flash", 
            response_format: str = 'NOT_GIVEN', 
            tools: Optional[List] = None) -> str:
    """同步聊天完成 - 便捷函数"""
    return _ai_chat.chat(message, model, response_format, tools)

async def llm_call_async(message: Union[str, List[Dict]], 
                       model: str = "google/gemini-2.5-flash", 
                       response_format: str = 'NOT_GIVEN', 
                       tools: Optional[List] = None) -> str:
    """异步聊天完成 - 便捷函数"""
    return await _ai_chat.chat_async(message, model, response_format, tools)

def llm_call_stream(message: Union[str, List[Dict]], 
                  model: str = "google/gemini-2.5-flash", 
                  response_format: str = 'NOT_GIVEN',
                  tools: Optional[List] = None) -> Generator[str, None, None]:
    """流式聊天完成 - 便捷函数"""
    return _ai_chat.chat_stream(message, model, response_format, tools)

async def llm_call_stream_async(message: Union[str, List[Dict]], 
                              model: str = "google/gemini-2.5-flash", 
                              response_format: str = 'NOT_GIVEN',
                              tools: Optional[List] = None) -> AsyncGenerator[str, None]:
    """异步流式聊天完成 - 便捷函数"""
    async for chunk in _ai_chat.chat_stream_async(message, model, response_format, tools):
        yield chunk


def get_embedding(text, model="text-embedding-3-small"):
    client = OpenAI(base_url="https://www.dmxapi.com/v1/", api_key=os.environ.get("DMXAPI_API_KEY"))
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding

# Token处理便捷函数
def count_tokens(string: str, encoding_name: str = "cl100k_base") -> int:
    """计算文本中的token数量 - 便捷函数"""
    return TokenManager.count_tokens(string, encoding_name)

def truncate_by_tokens(list_data: List[str], max_token_size: int) -> List[str]:
    """根据token大小截断列表 - 便捷函数"""
    return TokenManager.truncate_by_tokens(list_data, max_token_size)