/**
 * 创建工具的工厂函数
 * @param {Object} toolConfig - 工具配置
 * @returns {Object} 工具实例
 */
export function createTool(toolConfig) {
  const {
    name,
    description,
    parameters = [],
    execute
  } = toolConfig;

  if (!name || typeof name !== 'string') {
    throw new Error('Tool name is required and must be a string');
  }

  if (!description || typeof description !== 'string') {
    throw new Error('Tool description is required and must be a string');
  }

  if (!execute || typeof execute !== 'function') {
    throw new Error('Tool execute function is required');
  }

  const tool = {
    name,
    description,
    parameters,
    execute,

    /**
     * 获取工具名称
     */
    getName() {
      return this.name;
    },

    /**
     * 获取工具描述
     */
    getDescription() {
      return this.description;
    },

    /**
     * 获取参数定义
     */
    getParameters() {
      return this.parameters;
    },

    /**
     * 生成JSON Schema
     */
    getFunctionSchema() {
      const properties = {};
      const required = [];

      this.parameters.forEach(param => {
        properties[param.name] = param.toJSONSchema();
        if (param.required) {
          required.push(param.name);
        }
      });

      return {
        name: this.name,
        description: this.description,
        parameters: {
          type: "object",
          properties,
          required,
          additionalProperties: false
        }
      };
    },

    /**
     * 验证参数
     */
    validate(parameters) {
      for (const param of this.parameters) {
        if (param.required && !(param.name in parameters)) {
          throw new Error(`Missing required parameter: ${param.name}`);
        }
      }
      return true;
    },

    /**
     * 安全执行工具
     */
    async safeExecute(parameters) {
      try {
        this.validate(parameters);
        const result = await this.execute(parameters);
        return {
          success: true,
          result,
          tool: this.name
        };
      } catch (error) {
        console.error(`Tool ${this.name} execution failed:`, error);
        return {
          success: false,
          error: error.message,
          tool: this.name
        };
      }
    }
  };

  return tool;
}

/**
 * 工具验证函数
 */
export function isValidTool(tool) {
  return tool && 
         typeof tool.getName === 'function' &&
         typeof tool.getDescription === 'function' &&
         typeof tool.getParameters === 'function' &&
         typeof tool.execute === 'function' &&
         typeof tool.safeExecute === 'function';
} 