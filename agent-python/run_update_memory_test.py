"""
运行 update_memory 测试的脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 确保存储目录存在
    os.makedirs("memory_system/storage", exist_ok=True)
    
    print("🚀 开始测试 update_memory 功能...")
    
    try:
        from memory_system.test_update_memory import (
            test_promotion_logic,
            view_all_long_term_memories
        )
        from memory_system.config import MemoryConfig
        from memory_system.interface import MemorySystem
        config = MemoryConfig()
        memory_system = MemorySystem(config=config)
        # 逐个运行测试
        test_promotion_logic()
        # view_all_long_term_memories(memory_system, "promotion_test")
        
        print("\n🎉 所有 update_memory 测试完成！")
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保所有必要的文件都已正确创建")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 