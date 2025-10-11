"""Helper to create tool decorators for fastmcp versions that don't have them built-in."""

from typing import Callable, Any
from fastmcp.tools import Tool


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to register a function as a tool.
    """
    # Create a tool directly from the function
    tool_instance = Tool.from_function(func)
    
    # Store the tool instance as an attribute on the function
    # so it can be recognized by the server
    func._fastmcp_tool = tool_instance
    
    return func