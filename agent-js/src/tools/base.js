export class BaseTool {
  constructor(name, description, parameters = {}) {
    this.name = name;
    this.description = description;
    this.parameters = parameters;
  }

  async execute(args) {
    throw new Error('execute method must be implemented by subclass');
  }

  validate(args) {
    // 基础参数验证
    if (this.parameters.required) {
      for (const required of this.parameters.required) {
        if (!(required in args)) {
          throw new Error(`Missing required parameter: ${required}`);
        }
      }
    }
    return true;
  }

  async safeExecute(args) {
    try {
      this.validate(args);
      return await this.execute(args);
    } catch (error) {
      console.error(`Tool ${this.name} execution failed:`, error);
      return {
        success: false,
        error: error.message,
        tool: this.name
      };
    }
  }
} 