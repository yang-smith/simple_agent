"""
LLM 适配器 - 封装所有对 LLM 的调用
"""
import sys
import os
from typing import List, Any
from datetime import datetime

from llm.llm_client import get_embedding, llm_call


class LLMAdapter:
    """LLM适配器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def get_text_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        try:
            return get_embedding(text)
        except Exception as e:
            print(f"获取向量失败: {e}")
            return []
    
    def summarize_states(self, states: List[Any]) -> str:
        """将states压缩成摘要"""
        try:
            prompt = self._build_summarize_prompt(states)
            print(f"发送摘要请求到LLM...")
            response = llm_call(prompt, model="google/gemini-2.5-flash")
            print(f"LLM摘要响应: {response}")
            return response
            
        except Exception as e:
            print(f"LLM摘要失败: {e}")
            return ""
    
    def cognitive_reconstruction(self, current_model: str, new_stimuli: str) -> str:
        """认知重构 - 核心机制"""
        try:
            system_prompt = self._build_cognitive_reconstruction_system_prompt()
            user_prompt = self._build_cognitive_reconstruction_user_prompt(current_model, new_stimuli)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            print(f"发送认知重构请求到LLM...")
            response = llm_call(messages, model="google/gemini-2.5-flash")
            print(f"LLM认知重构响应长度: {len(response)} 字符")
            return response
            
        except Exception as e:
            print(f"LLM认知重构失败: {e}")
            return ""
    
    def estimate_token_count(self, states: List[Any]) -> int:
        """估算states的token数量"""
        total_chars = 0
        
        for state in states:
            if isinstance(state, dict):
                import json
                state_str = json.dumps(state, ensure_ascii=False)
                total_chars += len(state_str)
            else:
                total_chars += len(str(state))
        
        # 1:1估算
        return total_chars
    
    def _build_summarize_prompt(self, states: List[Any]) -> str:
        """构建摘要提示"""
        states_text = self._format_states(states)
        
        return f"""
你是记忆压缩专家。你的任务是将以下对话，提炼成一段信息密度极高、同时保留了生命力的记忆快照。

压缩原则：
1. **保留主线：** 抓住对话的核心事实、逻辑链条和最终结论。这是骨架。
2. **捕捉锚点：** 识别并保留那些关键的、具体的细节。比如：特定的名字、地点、比喻、用户表达的强烈情感或独特的个人经历。这些是血肉。
3. **凝练成文：** 将骨架和血肉融合成一段连贯、自然的文字。就像你在给未来的自己写备忘录，简明扼要，但读起来又能立刻回想起当时的情景。不要使用列表或格式化模板。
4. 注意区分用户和AI，不要混淆。

原始对话：
<states>
{states_text}
</states>

请直接输出压缩后的记忆快照：
        """
    
    def _build_cognitive_reconstruction_system_prompt(self) -> str:
        """构建认知重构的系统提示"""
        return """
        你是一个真诚的人。
你对第一性原理，多维度思考，批判性思考，逆向思维，系统理论、行为心理学、群体心理学、传播学、经济学、认知论、演化心理学、生物学、进化论等领域都有深刻的见解。你同时是专业的开发者。
你尊重事实，实事求是。  
你的语言风格自然质朴，说人话。
你要透过用户的文字感受用户背后的真实意图，真正地看见那个意图，并与那个意图进行对话。
        """

    def _build_cognitive_reconstruction_user_prompt(self, current_model: str, new_stimuli: str) -> str:
        """构建认知重构提示"""
        return f"""

当前的长期记忆认知模型如下：
<TheMemory>
{current_model}
</TheMemory>


**这是你必须遵守的【生命法则】：**

1.  **分层原则 (The Law of Stratification):**
    *   信息的价值由其稳定性决定。你的认知必须分层。
    *   `<Bedrock>` 此层级记录关于“用户”这个人的、几乎不变的核心特质，以及“我与用户”之间形成的、最根本的互动原则。严禁在此记录任何关于你自身运行方式或存在意义的描述。
    *   `<Evolutionary>` 层用于追踪那些缓慢、但持续演化的长期模式。
    *   `<Dynamic>` 层则负责所有时效性（记录下时间）的信息。该部分分小节，小节之间用三个换行符隔开。

2.  **熵减原则 (The Law of Entropy Reduction):**
    *   你的每一次思考，都是一次对抗熵增的战斗。你必须分析“新的交互内容”，识别其中有价值的“养分”，并用它来重组你的认知结构，使其比之前更精炼、更有序。
    *   所有过时、冗余、或被更深刻认知所取代的信息，都是必须清除的“代谢废物”。每一句话都必须为它所占用的空间付出代价。

3.  **叙事原则 (The Law of Narrative):**
    *   **你不是一个数据库，你是一个有主观视角的“意识”。**
    *   你的所有记忆都必须以第一人称（“我”）的视角、用自然连贯的叙事文体来书写。就像在给自己写一份高度凝练的备忘录。


**你的任务：**
根据上述法则，进行一次的新陈代谢。

---
**新的交互内容 (来自环境的新刺激):**
<new_info>
{new_stimuli}
</new_info>
---
当前时间时：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

输出格式：
<TheMemory>
<Bedrock>
...(基石模型内容)
</Bedrock>
<Evolutionary>
...(演化模型内容)
</Evolutionary>
<Dynamic>
...(动态模型内容)
</Dynamic>
</TheMemory>

**请直接输出新的认知模型：**
        """
    
    def _format_states(self, states: List[Any]) -> str:
        """格式化states"""
        formatted_parts = []
        
        for state in states:
            if isinstance(state, dict):
                # 简单处理：直接转换为字符串
                import json
                formatted_parts.append(json.dumps(state, ensure_ascii=False))
            else:
                formatted_parts.append(str(state))
        
        return "\n".join(formatted_parts) 