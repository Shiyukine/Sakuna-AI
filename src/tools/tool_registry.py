import json
import inspect

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, func):
        """Decorator to register a tool."""
        self.tools[func.__name__] = func
        return func

    def get_tool_definitions(self):
        """Returns tool schema definitions for the prompt."""
        definitions = []
        for name, func in self.tools.items():
            doc = inspect.getdoc(func) or ""
            # Simple inference: in a real scenario you might parse arg types.
            definitions.append({
                "name": name,
                "description": doc,
            })
        return definitions

    def execute(self, tool_name, kwargs):
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."
        func = self.tools[tool_name]
        try:
            return func(**kwargs)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

registry = ToolRegistry()

@registry.register
def think(prompt: str):
    """
    Use this tool to think step by step before generating the final JSON response.
    Pass a thinking prompt or question to guide your thoughts.
    """
    # In a real environment, this could trigger a separate LLM call or just print thoughts
    print(f"\n[Sakuna Thinking]: {prompt}\n")
    return "Thinking complete. You may now formulate your final JSON response."
