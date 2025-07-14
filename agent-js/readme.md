
本部分还在开发中

simple-agent-js/
├── package.json
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── index.js                   # 主要对外接口
│   ├── core/
│   │   ├── agent.js               # Agent核心逻辑
│   │   ├── context.js             # 上下文构建
│   │   └── state.js               # 状态管理
│   ├── llm/
│   │   └── llm-client.js          # LLM调用客户端
│   ├── memory-system/
│   │   ├── index.js               # 记忆系统入口
│   │   ├── config.js
│   │   ├── interface.js
│   │   ├── item.js
│   │   ├── core/
│   │   │   ├── long-term-memory.js
│   │   │   ├── short-term-memory.js
│   │   │   └── retrieval.js
│   │   ├── storage/
│   │   │   └── memory-store.js    # 使用IndexedDB
│   │   └── utils/
│   │       └── llm-adapter.js
│   ├── tools/
│   │   ├── index.js
│   │   ├── base.js
│   │   ├── registry.js
│   │   ├── tool-list.js
│   │   └── implementations/
│   │       ├── get-relevant-memories.js
│   │       ├── web-search.js
│   │       └── communication.js
│   └── utils/
│       ├── storage.js             # IndexedDB封装
│       ├── async-queue.js         # 异步任务队列
│       └── event-emitter.js       # 事件系统
├── examples/                      # 使用示例
│   ├── simple-chat.html           # 简单的HTML聊天界面
│   ├── simple-chat.js
│   └── node-example.js            # Node.js使用示例
└── dist/                          # 构建输出
    ├── simple-agent.esm.js        # ES模块版本
    ├── simple-agent.umd.js        # UMD版本（兼容各种环境）
    └── simple-agent.d.ts           # TypeScript类型定义