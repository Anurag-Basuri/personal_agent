"""
MCP Client Manager.

Connects to all third-party MCP servers defined in mcp_servers.json,
discovers their tools, and exposes them in LangChain format.
"""

from __future__ import annotations

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
        self.client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []
        self._status: dict[str, str] = {}
        self.connected_count: int = 0

    def _load_config(self) -> dict[str, Any]:
        if not os.path.exists(self.config_path):
            agent_logger.warn("MCP", f"Config {self.config_path} not found. MCP disabled.")
            return {}
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                
            servers = data.get("servers", {})
            # Interpolate env vars like {VERCEL_TOKEN} or standard env loading
            for name, server_cfg in servers.items():
                if "env" in server_cfg:
                    resolved_env = {}
                    for k, v in server_cfg["env"].items():
                        if v.startswith("${") and v.endswith("}"):
                            env_var_name = v[2:-1]
                            resolved_env[k] = os.environ.get(env_var_name, "")
                        else:
                            resolved_env[k] = v
                    server_cfg["env"] = resolved_env
                
                if "args" in server_cfg:
                    resolved_args = []
                    for arg in server_cfg["args"]:
                        if "${" in arg:
                            for key in os.environ:
                                if f"${{{key}}}" in arg:
                                    arg = arg.replace(f"${{{key}}}", os.environ.get(key, ""))
                        resolved_args.append(arg)
                    server_cfg["args"] = resolved_args
                    
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
        """Connect to all enabled servers and discover tools."""
        servers = self._load_config()
        if not servers:
            return

        enabled_servers = {}
        for name, config in servers.items():
            if config.get("enabled", True):
                # Ensure transport is specified, default to stdio
                if "transport" not in config:
                    config["transport"] = "stdio"
                    
                # MultiServerMCPClient does not accept arbitrary fields like 'enabled'
                client_config = dict(config)
                client_config.pop("enabled", None)
                enabled_servers[name] = client_config
                self._status[name] = "connecting"
            else:
                self._status[name] = "disabled"

        if not enabled_servers:
            return

        try:
            agent_logger.info("MCP", f"Connecting to {len(enabled_servers)} servers...")
            # MultiServerMCPClient handles connecting to multiple servers concurrently
            self.client = MultiServerMCPClient(enabled_servers)

            # Discover tools from all servers (auto converted to LangChain format)
            self._tools = await self.client.get_tools()

            self.connected_count = len(enabled_servers)
            for name in enabled_servers:
                self._status[name] = "connected"

            agent_logger.info("MCP", f"Successfully discovered {len(self._tools)} tools from {self.connected_count} servers.")
            system_health.mark_up("mcp")

        except Exception as e:
            agent_logger.error("MCP", "Failed to start MCP connections", e)
            # Mark all attempting servers as failed
            for name in enabled_servers:
                if self._status.get(name) == "connecting":
                    self._status[name] = "error"
            system_health.mark_down("mcp")

            # We don't raise here, we want the agent to start even if MCP fails
            # The agent will just run with 0 MCP tools, using only its local tools.
    async def shutdown(self) -> None:
        """Cleanly disconnect from all servers."""
        if self.client:
            try:
                # MultiServerMCPClient does not expose __aexit__, we can just clear it
                agent_logger.info("MCP", "Disconnected from MCP servers.")
            except Exception as e:
                agent_logger.error("MCP", "Error during MCP shutdown", e)
            finally:
                self.client = None
                self._tools = []
                self.connected_count = 0
                for name in self._status:
                    if self._status[name] == "connected":
                        self._status[name] = "disconnected"

    def get_tools(self) -> list[BaseTool]:
        """Return the list of discovered LangChain compatible tools."""
        return self._tools

    def get_status(self) -> dict[str, str]:
        """Return the connection status of configured servers."""
        return self._status


# Singleton instance
mcp_manager = MCPManager()
