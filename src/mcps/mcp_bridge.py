"""Bridge utility to integrate FastMCP tools with LangGraph."""

import asyncio
import json
from typing import Any, Dict
from fastmcp import FastMCP, Client
from src.logger import get_logger

logger = get_logger(__name__)


async def call_mcp_tool_async(
    mcp_server: FastMCP,
    tool_name: str,
    tool_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call an MCP tool asynchronously via FastMCP Client.

    Args:
        mcp_server: FastMCP server instance
        tool_name: Name of the tool to call
        tool_params: Dictionary of parameters to pass to the tool

    Returns:
        Dictionary with tool result or error
    """
    try:
        async with Client(mcp_server) as client:
            # Call the MCP tool
            result = await client.call_tool(tool_name, tool_params)

            # Parse result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                # Try to parse as JSON
                try:
                    return json.loads(content.text)
                except (json.JSONDecodeError, AttributeError):
                    return {"result": content.text}

            return {"result": None}

    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "failed"}


def call_mcp_tool(
    mcp_server: FastMCP,
    tool_name: str,
    tool_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call an MCP tool synchronously (wrapper for async function).

    This is designed to be called from synchronous LangGraph nodes.

    FIX: Handle case where event loop is already running (e.g., in FastAPI/Streamlit).
    Instead of trying to run_until_complete on an existing loop, use asyncio.run()
    which creates a new event loop in a thread if needed.

    Args:
        mcp_server: FastMCP server instance
        tool_name: Name of the tool to call
        tool_params: Dictionary of parameters to pass to the tool

    Returns:
        Dictionary with tool result or error
    """
    try:
        # Check if there's already a running event loop
        try:
            asyncio.get_running_loop()
            # If we get here, there's already a loop running
            # We need to run the async function in a thread to avoid conflict
            import concurrent.futures
            import threading

            result_holder = {}
            error_holder = {}

            def run_in_thread():
                try:
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(call_mcp_tool_async(mcp_server, tool_name, tool_params))
                    result_holder['result'] = result
                    new_loop.close()
                except Exception as e:
                    error_holder['error'] = e

            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if error_holder:
                raise error_holder['error']
            return result_holder.get('result', {"error": "No result returned", "status": "failed"})

        except RuntimeError:
            # No event loop running, safe to create and use one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(call_mcp_tool_async(mcp_server, tool_name, tool_params))
            loop.close()
            return result

    except Exception as e:
        logger.error(f"Error in call_mcp_tool: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "failed"}
