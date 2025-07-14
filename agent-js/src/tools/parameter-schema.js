export function createParameterSchema({
  name,
  description,
  type = "string",
  required = true,
  enum: enumValues = null,
  default: defaultValue = null
}) {
  return {
    name,
    description,
    type,
    required,
    enum: enumValues,
    default: defaultValue,
    
    toJSONSchema() {
      const schema = {
        type: this.type,
        description: this.description
      };

      if (this.enum) {
        schema.enum = this.enum;
      }

      if (this.default !== null) {
        schema.default = this.default;
      }

      return schema;
    }
  };
} 