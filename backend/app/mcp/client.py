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
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("servers", {})
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
                enabled_servers[name] = config
                self._status[name] = "connecting"
            else:
                self._status[name] = "disabled"

        if not enabled_servers:
            return

        try:
            agent_logger.info("MCP", f"Connecting to {len(enabled_servers)} servers...")
            # MultiServerMCPClient handles connecting to multiple servers concurrently
            self.client = MultiServerMCPClient(enabled_servers)
            
            # The async enter pattern connects the transport and initializes the session
            await self.client.__aenter__()
            
            # Discover tools from all servers (auto-converted to LangChain format)
            self._tools = await self.client.get_tools()
            
            self.connected_count = len(enabled_servers)
            for name in enabled_servers:
                self._status[name] = "connected"
                
            agent_logger.info("MCP", f"Successfully discovered {len(self._tools)} tools from {self.connected_count} servers.")
            
        except Exception as e:
            agent_logger.error("MCP", "Failed to start MCP connections", e)
            # Mark all attempting servers as failed
            for name in enabled_servers:
                if self._status.get(name) == "connecting":
                    self._status[name] = "error"
            
            # We don't raise here, we want the agent to start even if MCP fails
            # The agent will just run with 0 MCP tools, using only its local tools.

    async def shutdown(self) -> None:
        """Cleanly disconnect from all servers."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
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
        """Return the list of discovered LangChain-compatible tools."""
        return self._tools

    def get_status(self) -> dict[str, str]:
        """Return the connection status of configured servers."""
        return self._status


# Singleton instance
mcp_manager = MCPManager()
