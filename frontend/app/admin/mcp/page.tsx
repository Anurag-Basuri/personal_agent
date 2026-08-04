'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAgentStore } from '@/store/useAgentStore';
import { useAdminAPI } from '@/hooks/useAdminAPI';
import { TopNav } from '@/components/layout/TopNav';
import { MCPServerCard } from '@/components/admin/MCPServerCard';
import { Icons } from '@/components/ui/Icons';
import { motion } from 'framer-motion';

export default function MCPManagerPage() {
  const { isAdmin, adminToken } = useAgentStore();
  const router = useRouter();
  const { getMCPServers, toggleMCP, deleteMCP } = useAdminAPI();
  
  const [mcpData, setMcpData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMCP = async () => {
    setIsLoading(true);
    const data = await getMCPServers();
    if (data) setMcpData(data);
    setIsLoading(false);
  };

  useEffect(() => {
    if (!isAdmin || !adminToken) {
      router.push('/admin/login');
      return;
    }
    fetchMCP();
  }, [isAdmin, adminToken, router]);

  const handleToggle = async (name: string) => {
    const success = await toggleMCP(name);
    if (success) {
      await fetchMCP(); // Refresh list
    }
  };

  const handleDelete = async (name: string) => {
    const success = await deleteMCP(name);
    if (success) {
      await fetchMCP(); // Refresh list
    }
  };

  if (!isAdmin || !adminToken) return null;

  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      
      <main className="mx-auto max-w-6xl pt-24 pb-12 px-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">MCP Manager</h1>
            <p className="text-muted-foreground mt-1 font-mono text-sm">Model Context Protocol Servers</p>
          </div>
          <button
            onClick={() => router.push('/admin/dashboard')}
            className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-xl font-semibold hover:bg-muted/80 hover:text-foreground transition-colors"
          >
            &larr; Back to Dashboard
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 rounded-full border-4 border-secondary border-t-transparent animate-spin" />
          </div>
        ) : mcpData ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(mcpData.servers).map(([name, config]: [string, any]) => {
                const statusInfo = mcpData.status[name] || {};
                return (
                  <MCPServerCard
                    key={name}
                    name={name}
                    config={config}
                    status={statusInfo.status || 'unknown'}
                    onToggle={handleToggle}
                    onDelete={handleDelete}
                  />
                );
              })}
            </div>
            
            {Object.keys(mcpData.servers).length === 0 && (
              <div className="text-center py-20 text-muted-foreground bg-muted/20 rounded-3xl border border-border border-dashed">
                <Icons.Tool className="h-10 w-10 mx-auto mb-4 opacity-50" />
                <p>No MCP servers registered.</p>
                <p className="text-sm opacity-70">Add servers directly to the config file or via the API.</p>
              </div>
            )}
          </motion.div>
        ) : (
          <div className="text-center py-20 text-destructive">
            Failed to load MCP server data.
          </div>
        )}
      </main>
    </div>
  );
}
