"""
Admin API for managing MCP servers dynamically.

Requires admin role authentication.
Provides endpoints to list, add, update, delete, and reload MCP servers.
"""

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_admin_user
from app.core.rate_limiter import rate_limit
from app.core.responses import success_response
from app.mcp.client import mcp_manager
from app.core.exceptions import ForbiddenError, ConflictError, NotFoundError
from app.models.user import User

router = APIRouter(prefix="/api/admin/mcp", tags=["Admin MCP"])

class MCPServerConfig(BaseModel):
    """Configuration for adding or updating an MCP server.

    Supports all transport types:
      stdio: requires command + args
      streamable_http: requires url (+ optional headers)
      sse: requires url (+ optional headers)
    """

    name: str = Field(..., description="Unique name of the MCP server")
    transport: str = Field("stdio", description="Transport type: stdio, streamable_http, or sse")
    command: str | None = Field(None, description="Command to run (required for stdio transport)")
    args: list[str] = Field(default_factory=list, description="Arguments for the command")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables (e.g., API keys)")
    url: str | None = Field(None, description="Server URL (required for streamable_http/sse transport)")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers (for streamable_http/sse)")
    description: str | None = Field(None, description="Optional description of the server")
    enabled: bool = Field(True, description="Whether the server is enabled")



def _load_config() -> dict[str, Any]:
    if not os.path.exists(mcp_manager.config_path):
        return {"servers": {}}
    try:
        with open(mcp_manager.config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"servers": {}}

def _save_config(config: dict[str, Any]) -> None:
    with open(mcp_manager.config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

@router.get("")
async def list_servers(user: User = Depends(get_admin_user)):
    """List all configured MCP servers and their current status."""
    config = _load_config()
    servers = config.get("servers", {})
    status = mcp_manager.get_status()

    result = {}
    for name, srv in servers.items():
        result[name] = {
            "config": srv,
            "status": status.get(name, "disconnected")
        }

    return success_response(
        data={
            "servers": result,
            "connected_count": mcp_manager.connected_count,
            "total_tools": len(mcp_manager.get_tools()),
        },
        message="Retrieved MCP servers"
    )

@router.post("")
async def add_server(server: MCPServerConfig, user: User = Depends(get_admin_user)):
    """Add a new MCP server configuration."""
    config = _load_config()
    if "servers" not in config:
        config["servers"] = {}

    if server.name in config["servers"]:
        raise ConflictError(f"Server '{server.name}' already exists")

    server_dict = server.model_dump(exclude={"name"})
    config["servers"][server.name] = server_dict
    _save_config(config)

    return success_response(
        data=server_dict,
        message=f"Added MCP server '{server.name}'. Call /reload to connect."
    )

@router.put("/{name}")
async def update_server(name: str, server: MCPServerConfig, user: User = Depends(get_admin_user)):
    """Update an existing MCP server configuration."""
    config = _load_config()
    if "servers" not in config or name not in config["servers"]:
        raise NotFoundError(f"Server '{name}' not found")

    server_dict = server.model_dump(exclude={"name"})

    # If the name is changing
    if name != server.name:
        if server.name in config["servers"]:
            raise ConflictError(f"Target server '{server.name}' already exists")
        del config["servers"][name]

    config["servers"][server.name] = server_dict
    _save_config(config)

    return success_response(
        data=server_dict,
        message=f"Updated MCP server '{server.name}'. Call /reload to connect."
    )

@router.delete("/{name}")
async def remove_server(name: str, user: User = Depends(get_admin_user)):
    """Remove an MCP server from configuration."""
    config = _load_config()
    if "servers" not in config or name not in config["servers"]:
        raise NotFoundError(f"Server '{name}' not found")

    del config["servers"][name]
    _save_config(config)

    return success_response(
        data=None,
        message=f"Removed MCP server '{name}'. Call /reload to apply."
    )

@router.post("/{name}/toggle")
async def toggle_server(name: str, user: User = Depends(get_admin_user)):
    """Toggle a server's enabled status."""
    config = _load_config()
    if "servers" not in config or name not in config["servers"]:
        raise NotFoundError(f"Server '{name}' not found")

    current_enabled = config["servers"][name].get("enabled", True)
    config["servers"][name]["enabled"] = not current_enabled
    _save_config(config)

    return success_response(
        data={"enabled": not current_enabled},
        message=f"Toggled MCP server '{name}' to {'enabled' if not current_enabled else 'disabled'}."
    )

@router.post("/reload")
async def reload_servers(
    user: User = Depends(get_admin_user),
    _rate: None = Depends(rate_limit("mcp_reload")),
):
    """Disconnect all servers, re read config, and reconnect."""
    await mcp_manager.shutdown()
    await mcp_manager.startup()

    return success_response(
        data={
            "connected_count": mcp_manager.connected_count,
            "total_tools": len(mcp_manager.get_tools()),
            "status": mcp_manager.get_status()
        },
        message="Reloaded MCP servers"
    )
