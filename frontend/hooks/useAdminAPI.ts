'use client';

import { useCallback } from 'react';
import { useAgentStore } from '../store/useAgentStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export function useAdminAPI() {
  const { setAdminState, adminToken } = useAgentStore();

  const getAdminHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (adminToken) {
      headers['Authorization'] = `Bearer ${adminToken}`;
    }

    return headers;
  }, [adminToken]);

  const adminLogin = useCallback(
    async (adminId: string, password: string): Promise<boolean> => {
      try {
        const res = await fetch(`${API_BASE}/api/admin/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_id: adminId, password }),
        });

        const data = await res.json();
        
        if (res.ok && data.success && data.data?.token) {
          setAdminState(true, data.data.token);
          return true;
        }
        return false;
      } catch (err) {
        console.error('Admin login error:', err);
        return false;
      }
    },
    [setAdminState]
  );

  const getHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/health`, {
        headers: getAdminHeaders(),
      });
      const data = await res.json();
      return data.success ? data.data : null;
    } catch (err) {
      console.error('Failed to get health:', err);
      return null;
    }
  }, [getAdminHeaders]);

  const getMCPServers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mcp`, {
        headers: getAdminHeaders(),
      });
      const data = await res.json();
      return data.success ? data.data : null;
    } catch (err) {
      console.error('Failed to get MCP servers:', err);
      return null;
    }
  }, [getAdminHeaders]);

  const reloadMCP = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mcp/reload`, {
        method: 'POST',
        headers: getAdminHeaders(),
      });
      const data = await res.json();
      return data.success;
    } catch (err) {
      console.error('Failed to reload MCP servers:', err);
      return false;
    }
  }, [getAdminHeaders]);

  const toggleMCP = useCallback(async (name: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mcp/${name}/toggle`, {
        method: 'POST',
        headers: getAdminHeaders(),
      });
      const data = await res.json();
      return data.success;
    } catch (err) {
      console.error('Failed to toggle MCP server:', err);
      return false;
    }
  }, [getAdminHeaders]);

  const deleteMCP = useCallback(async (name: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/mcp/${name}`, {
        method: 'DELETE',
        headers: getAdminHeaders(),
      });
      const data = await res.json();
      return data.success;
    } catch (err) {
      console.error('Failed to delete MCP server:', err);
      return false;
    }
  }, [getAdminHeaders]);

  return { 
    adminLogin, 
    getHealth, 
    getMCPServers, 
    reloadMCP, 
    toggleMCP, 
    deleteMCP 
  };
}
