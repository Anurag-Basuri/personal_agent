"""
MCP Client Manager.

Connects to all third-party MCP servers defined in mcp_servers.json,
discovers their tools, and exposes them in LangChain format.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.degradation import system_health
from app.core.logger import agent_logger


class MCPManager:
    """Singleton manager for all MCP client connections."""

    def __init__(self, config_path: str = "mcp_servers.json"):
        self.config_path = config_path
        self._clients: list[MultiServerMCPClient] = []
        self._tools: list[BaseTool] = []
        self._status: dict[str, str] = {}
        self.connected_count: int = 0

    def _load_config(self) -> dict[str, Any]:
        """Load and interpolate MCP server configuration from JSON file."""
        if not os.path.exists(self.config_path):
            agent_logger.warn("MCP", f"Config {self.config_path} not found. MCP disabled.")
            return {}
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            servers = data.get("servers", {})
            for name, server_cfg in servers.items():
                # Resolve environment variables in env block
                if "env" in server_cfg:
                    resolved_env = {}
                    for k, v in server_cfg["env"].items():
                        if v.startswith("${") and v.endswith("}"):
                            env_var_name = v[2:-1]
                            resolved_env[k] = os.environ.get(env_var_name, "")
                        else:
                            resolved_env[k] = v
                    server_cfg["env"] = resolved_env

                # Resolve environment variables in args
                if "args" in server_cfg:
                    resolved_args = []
                    for arg in server_cfg["args"]:
                        if "${" in arg:
                            for key in os.environ:
                                if f"${{{key}}}" in arg:
                                    arg = arg.replace(f"${{{key}}}", os.environ.get(key, ""))
                        resolved_args.append(arg)
                    server_cfg["args"] = resolved_args

                # Resolve environment variables in headers
                if "headers" in server_cfg:
                    resolved_headers = {}
                    for k, v in server_cfg["headers"].items():
                        if isinstance(v, str) and "${" in v:
                            for key in os.environ:
                                if f"${{{key}}}" in v:
                                    v = v.replace(f"${{{key}}}", os.environ.get(key, ""))
                        resolved_headers[k] = v
                    server_cfg["headers"] = resolved_headers

            return servers
        except Exception as e:
            agent_logger.error("MCP", f"Failed to parse {self.config_path}", e)
            return {}

    async def startup(self) -> None:
        """Connect to all enabled servers and discover tools.

        Each server is connected independently so a single failing server
        does not prevent the others from loading successfully.
        Client handles are stored in self._clients for proper shutdown.
        """
        servers = self._load_config()
        if not servers:
            return

        enabled_servers = {}
        for name, config in servers.items():
            if config.get("enabled", True):
                if "transport" not in config:
                    config["transport"] = "stdio"

                client_config = dict(config)
                client_config.pop("enabled", None)
                enabled_servers[name] = client_config
                self._status[name] = "connecting"
            else:
                self._status[name] = "disabled"

        if not enabled_servers:
            return

        agent_logger.info("MCP", f"Connecting to {len(enabled_servers)} servers concurrently...")
        
        async def connect_server(name: str, server_config: dict):
            try:
                single_client = MultiServerMCPClient({name: server_config})
                # 90 second timeout per server (npx downloads and OAuth servers need extra time)
                tools = await asyncio.wait_for(
                    single_client.get_tools(server_name=name),
                    timeout=90.0,
                )
                return name, single_client, tools, None
            except asyncio.TimeoutError:
                return name, None, None, "TimeoutError: Timed out after 90s"
            except Exception as e:
                # Unwrap ExceptionGroup from anyio/TaskGroup to show the real error
                if type(e).__name__ in ("ExceptionGroup", "BaseExceptionGroup"):
                    sub_errors = [str(exc) for exc in getattr(e, "exceptions", [])]
                    real_error = " | ".join(sub_errors) if sub_errors else str(e)
                    if "TimeoutError" in real_error or "Timeout" in real_error:
                        return name, None, None, "TimeoutError: Timed out during initialization"
                    else:
                        return name, None, None, real_error
                return name, None, None, str(e)

        tasks = [connect_server(name, cfg) for name, cfg in enabled_servers.items()]
        results = await asyncio.gather(*tasks)

        for name, single_client, tools, error in results:
            if error:
                self._status[name] = "error"
                agent_logger.warn("MCP", f"Server '{name}' failed to connect: {error}")
            else:
                self._clients.append(single_client)
                if tools:
                    self._tools.extend(tools)
                self._status[name] = "connected"
                self.connected_count += 1

        if self.connected_count > 0:
            system_health.mark_up("mcp")
        else:
            agent_logger.warn("MCP", "All MCP servers failed to connect.")
            system_health.mark_down("mcp")

    async def shutdown(self) -> None:
        """Cleanly disconnect from all servers by closing tracked client handles."""
        if not self._clients:
            return

        agent_logger.info("MCP", f"Shutting down {len(self._clients)} MCP clients...")

        for client in self._clients:
            try:
                # MultiServerMCPClient removed context manager support in newer versions.
                # We check for a close method dynamically to avoid type checker errors
                # and gracefully handle future changes.
                close_method = getattr(client, "close", None)
                if callable(close_method):
                    res = close_method()
                    if asyncio.iscoroutine(res):
                        await res
            except Exception as e:
                agent_logger.warn("MCP", f"Error closing MCP client: {e}")

        self._clients.clear()
        self._tools.clear()
        self.connected_count = 0
        for name in self._status:
            if self._status[name] == "connected":
                self._status[name] = "disconnected"

        agent_logger.info("MCP", "All MCP connections closed.")

    def get_tools(self) -> list[BaseTool]:
        """Return the list of discovered LangChain compatible tools."""
        return self._tools

    def get_status(self) -> dict[str, str]:
        """Return the connection status of configured servers."""
        return self._status


# Singleton instance
mcp_manager = MCPManager()
