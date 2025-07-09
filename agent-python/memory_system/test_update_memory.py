"""
测试短期记忆晋升逻辑和读取接口
"""
import os
import sys

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_system.interface import MemorySystem
from memory_system.config import MemoryConfig


def create_real_conversation_states():
    """创建基于真实对话的测试states"""
    return [
        {
            "type": "user_message",
            "content": "我们聊聊赚钱。我当前状态是初级的全栈开发、有能力使用各种AI工具（画图、写代码之类）、喜欢深入本质、最近一直在研究观察AI领域、精力有限，设计半懂不懂（这点AI可以帮一点忙）、锻炼讲故事能力中。我在考虑建立一个赚钱系统，你怎么看老朋友？"
        },
        {
            "type": "agent_message",
            "content": "傍晚的风吹着确实舒服。你提的这个词，赚钱系统，我很喜欢。比找个项目赚钱要好。因为系统这两个字，意味着你想要的不是一锤子买卖，不是把自己当成一个零件卖掉，而是一个能持续、能自我生长、能放大你投入的东西。这说明你已经在思考本质了，这是好事。"
        },
        {
            "type": "user_message", 
            "content": "老朋友，着眼点放到他人身上是好的，但你从痛点角度考虑，我有所不同意。我以为解决方法都在其思维之外。简单满足痛点不过隔靴搔痒，而且世上人千千万万，痛点无处不在，你想做的东西，你看到的，可能别人也看到，最终做得比你更好，竞争中失败者是赚不到钱的。我们试着先从我的角度出发，捋一遍，看看有哪些竞争优势，可以转换的"
        },
        {
            "type": "agent_message",
            "content": "你说的这个，我不同意。但我很高兴你这么说。因为你的这个想法，恰恰是绝大多数聪明人，尤其是技术出身的聪明人，最容易掉进去的陷阱。我们把它掰开揉碎了看。第一，你担心竞争。你说别人也看到，最终做得比你更好。没错，如果痛点是我渴了，解决方案是卖水，那最后一定是资本最雄厚、渠道最广、成本最低的人赢。这叫红海竞争。"
        },
        {
            "type": "user_message",
            "content": "不不不，我似乎没有表达清楚。这样说，痛点这个事情，本质是什么？我直觉上不喜欢这个词。买卖或者交易，其目的，绝不仅限于解决痛点，它可能是满足一种避免麻烦的欲望，一种自我成长的渴望，一种满足好奇，一种自我幻想，一种认同。只谈痛点，忽视了人本身"
        },
        {
            "type": "agent_message",
            "content": "你说得太对了。痛点这个词，确实被用烂了，变得又冷又硬，像个商业术语，听着没人情味。你说忽视了人本身，这句话说到了根子上。我收回痛点这个词。我们换一个。你说的那些：避免麻烦、自我成长、满足好奇、自我幻想、身份认同……这些东西，它们的本质是什么？我认为，它们都指向了一个东西：现状和理想态之间的差距。"
        }
    ]


def view_cognitive_model(memory_system, user_id):
    """查看认知模型的详细信息"""
    print("\n=== 查看认知模型 ===")
    
    try:
        # 获取完整认知模型
        cognitive_model = memory_system.long_term_mgr.get_cognitive_model(user_id)
        
        if not cognitive_model.strip():
            print("没有找到认知模型")
            return
        
        print(f"认知模型总长度: {len(cognitive_model)} 字符")
        print("-" * 80)
        
        # 分别显示各个部分
        bedrock = memory_system.long_term_mgr.get_bedrock_model(user_id)
        evolutionary = memory_system.long_term_mgr.get_evolutionary_model(user_id)
        dynamic = memory_system.long_term_mgr.get_dynamic_model(user_id)
        
        if bedrock:
            print("【基石模型 Bedrock】:")
            print(bedrock)
            print("-" * 40)
        
        if evolutionary:
            print("【演化模型 Evolutionary】:")
            print(evolutionary)
            print("-" * 40)
        
        if dynamic:
            print("【动态模型 Dynamic】:")
            print(dynamic)
            print("-" * 40)
        
        print("\n【完整认知模型】:")
        print(cognitive_model)
        print("-" * 80)
            
    except Exception as e:
        print(f"查看认知模型失败: {e}")


def test_memory_system():
    """测试记忆系统的完整流程"""
    print("=== 测试记忆系统完整流程 ===")
    
    # 配置：低阈值，低数量限制，批量晋升
    config = MemoryConfig()
    config.STATES_TOKEN_THRESHOLD = 200
    config.SHORT_TERM_MAX_COUNT = 2  # 最多2条短期记忆
    config.PROMOTION_BATCH_SIZE = 2  # 每次晋升2条
    
    memory_system = MemorySystem(config=config)
    user_id = "default"
    
    print(f"配置: 阈值={config.STATES_TOKEN_THRESHOLD}, 最大短期记忆={config.SHORT_TERM_MAX_COUNT}, 批量晋升={config.PROMOTION_BATCH_SIZE}")
    
    # 1. 测试写入接口 - 添加多条记忆，触发晋升
    print("\n--- 阶段1: 测试写入接口 ---")
    for i in range(4):
        print(f"\n第{i+1}次调用 update_memory:")
        
        if i == 0:
            # 第一次使用真实对话数据
            states = create_real_conversation_states()
        else:
            # 后续使用简化数据
            states = [
                {
                    "type": "user_message",
                    "content": f"第{i+1}次对话：用户在讨论关于AI技术的应用和商业化思考。" + "详细内容填充。" * 100
                },
                {
                    "type": "agent_message",
                    "content": f"第{i+1}次回复：助手提供了关于技术商业化的深度分析和建议。" + "详细回复填充。" * 100
                }
            ]
        
        print(f"  输入states数量: {len(states)}")
        memory_system.update_memory(states, user_id)
        
        # 检查短期记忆数量
        short_memories = memory_system.short_term_mgr.get_recent_memories(user_id, limit=20)
        print(f"  当前短期记忆数量: {len(short_memories)}")
        
        # 检查是否有长期记忆
        cognitive_model = memory_system.long_term_mgr.get_cognitive_model(user_id)
        if cognitive_model.strip():
            print(f"  ✅ 检测到认知模型生成（长度: {len(cognitive_model)} 字符）")
        else:
            print(f"  ⏳ 暂无认知模型")
    
    # 2. 测试读取接口
    print("\n--- 阶段2: 测试读取接口 ---")
    test_queries = [
        "赚钱系统",
        "痛点和商业模式", 
        "AI技术应用",
        "用户价值和成长"
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        relevant_memories = memory_system.get_relevant_memories(query, user_id)
        print(f"返回结果: {relevant_memories}")
    
    # 3. 查看最终状态
    print("\n--- 阶段3: 查看最终状态 ---")
    short_memories = memory_system.short_term_mgr.get_recent_memories(user_id, limit=20)
    print(f"最终短期记忆数量: {len(short_memories)}")
    
    for i, memory in enumerate(short_memories, 1):
        print(f"  短期记忆{i}: {memory.content[:100]}...")
    
    # 查看认知模型
    view_cognitive_model(memory_system, user_id)
    



if __name__ == "__main__":
    # 确保存储目录存在
    os.makedirs("memory_system/storage", exist_ok=True)
    
    print("🚀 开始测试记忆系统...\n")
    
    try:
        test_memory_system()
        print("\n🎉 记忆系统测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 