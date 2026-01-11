"""Lightweight connection handling for MCP servers."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from types import TracebackType
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

# Constants for context result lengths
CONTEXT_RESULT_TWO_TUPLE = 2
CONTEXT_RESULT_THREE_TUPLE = 3


class MCPConnection(ABC):
    """Base class for MCP server connections."""

    def __init__(self) -> None:
        """Initialize MCP connection with session and stack."""
        self.session: ClientSession | None = None
        self._stack: AsyncExitStack | None = None

    @abstractmethod
    def _create_context(self) -> AbstractAsyncContextManager[Any]:
        """Create the connection context based on connection type.

        Returns:
            An async context manager for the connection.
        """

    async def __aenter__(self) -> "MCPConnection":
        """Initialize MCP server connection.

        Returns:
            Self for use in async context manager.
        """
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        ctx = self._create_context()
        result = await self._stack.enter_async_context(ctx)

        if len(result) == CONTEXT_RESULT_TWO_TUPLE:
            read, write = result
        elif len(result) == CONTEXT_RESULT_THREE_TUPLE:
            read, write, _ = result
        else:
            await self._stack.__aexit__(None, None, None)
            raise ValueError(f"Unexpected context result: {result}")

        session_ctx = ClientSession(read, write)
        self.session = await self._stack.enter_async_context(session_ctx)
        if self.session is not None:
            await self.session.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up MCP server connection resources.

        Args:
            exc_type: Type of exception if one occurred.
            exc_val: Exception value if one occurred.
            exc_tb: Exception traceback if one occurred.
        """
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
        self.session = None
        self._stack = None

    async def list_tools(self) -> list[dict[str, Any]]:
        """Retrieve available tools from the MCP server.

        Returns:
            List of tool dictionaries with name, description, and input schema.
        """
        if self.session is None:
            raise RuntimeError("Session not initialized")
        response = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> list[Any] | dict[str, Any] | str:
        """Call a tool on the MCP server with provided arguments.

        Args:
            tool_name: Name of the tool to call.
            arguments: Arguments to pass to the tool.

        Returns:
            Tool execution result content.
        """
        if self.session is None:
            raise RuntimeError("Session not initialized")
        result = await self.session.call_tool(tool_name, arguments=arguments)
        return result.content


class MCPConnectionStdio(MCPConnection):
    """MCP connection using standard input/output."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        """Initialize stdio MCP connection.

        Args:
            command: Command to run for the MCP server.
            args: Command-line arguments for the command.
            env: Environment variables for the command.
        """
        super().__init__()
        self.command = command
        self.args = args or []
        self.env = env

    def _create_context(self) -> AbstractAsyncContextManager[Any]:
        """Create stdio connection context.

        Returns:
            Stdio client async context manager.
        """
        return stdio_client(
            StdioServerParameters(command=self.command, args=self.args, env=self.env)
        )


class MCPConnectionSSE(MCPConnection):
    """MCP connection using Server-Sent Events."""

    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        """Initialize SSE MCP connection.

        Args:
            url: URL of the SSE MCP server.
            headers: HTTP headers for the connection.
        """
        super().__init__()
        self.url = url
        self.headers = headers or {}

    def _create_context(self) -> AbstractAsyncContextManager[Any]:
        """Create SSE connection context.

        Returns:
            SSE client async context manager.
        """
        return sse_client(url=self.url, headers=self.headers)


class MCPConnectionHTTP(MCPConnection):
    """MCP connection using Streamable HTTP."""

    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        """Initialize HTTP MCP connection.

        Args:
            url: URL of the HTTP MCP server.
            headers: HTTP headers for the connection.
        """
        super().__init__()
        self.url = url
        self.headers = headers or {}

    def _create_context(self) -> AbstractAsyncContextManager[Any]:
        """Create HTTP connection context.

        Returns:
            HTTP client async context manager.
        """
        return streamablehttp_client(url=self.url, headers=self.headers)


def create_connection(
    transport: str,
    *,
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    url: str | None = None,
    headers: dict[str, str] | None = None,
) -> MCPConnection:
    """Factory function to create the appropriate MCP connection.

    Args:
        transport: Connection type ("stdio", "sse", or "http")
        command: Command to run (stdio only)
        args: Command arguments (stdio only)
        env: Environment variables (stdio only)
        url: Server URL (sse and http only)
        headers: HTTP headers (sse and http only)

    Returns:
        MCPConnection instance

    Raises:
        ValueError: If required parameters are missing or transport type is invalid.
    """
    transport = transport.lower()

    if transport == "stdio":
        if not command:
            raise ValueError("Command is required for stdio transport")
        return MCPConnectionStdio(command=command, args=args, env=env)

    if transport == "sse":
        if not url:
            raise ValueError("URL is required for sse transport")
        return MCPConnectionSSE(url=url, headers=headers)

    if transport in {"http", "streamable_http", "streamable-http"}:
        if not url:
            raise ValueError("URL is required for http transport")
        return MCPConnectionHTTP(url=url, headers=headers)

    raise ValueError(
        f"Unsupported transport type: {transport}. Use 'stdio', 'sse', or 'http'"
    )
