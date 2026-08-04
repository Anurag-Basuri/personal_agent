'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAgentStore } from '@/store/useAgentStore';
import { useAdminAPI } from '@/hooks/useAdminAPI';
import { TopNav } from '@/components/layout/TopNav';
import { HealthCard } from '@/components/admin/HealthCard';
import { CircuitBreakerStatus } from '@/components/admin/CircuitBreakerStatus';
import { Icons } from '@/components/ui/Icons';
import { motion } from 'framer-motion';

export default function AdminDashboard() {
  const { isAdmin, adminToken } = useAgentStore();
  const router = useRouter();
  const { getHealth, reloadMCP } = useAdminAPI();
  
  const [healthData, setHealthData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReloading, setIsReloading] = useState(false);

  useEffect(() => {
    if (!isAdmin || !adminToken) {
      router.push('/admin/login');
      return;
    }

    const fetchHealth = async () => {
      setIsLoading(true);
      const data = await getHealth();
      if (data) setHealthData(data);
      setIsLoading(false);
    };

    fetchHealth();
    // Poll every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [isAdmin, adminToken, router, getHealth]);

  const handleReloadMCP = async () => {
    setIsReloading(true);
    await reloadMCP();
    const data = await getHealth();
    if (data) setHealthData(data);
    setIsReloading(false);
  };

  if (!isAdmin || !adminToken) return null;

  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      
      <main className="mx-auto max-w-6xl pt-24 pb-12 px-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">System Health</h1>
            <p className="text-muted-foreground mt-1 font-mono text-sm">Dashboard Overview</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/admin/chat')}
              className="flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-xl font-semibold hover:bg-primary/20 transition-colors"
            >
              <Icons.Agent className="h-4 w-4" />
              Admin Chat
            </button>
            <button
              onClick={() => router.push('/admin/mcp')}
              className="flex items-center gap-2 px-4 py-2 bg-secondary/10 text-secondary rounded-xl font-semibold hover:bg-secondary/20 transition-colors"
            >
              <Icons.Tool className="h-4 w-4" />
              MCP Manager
            </button>
          </div>
        </div>

        {isLoading && !healthData ? (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 rounded-full border-4 border-primary border-t-transparent animate-spin" />
          </div>
        ) : healthData ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* Core Subsystems */}
            <div>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Icons.Settings className="h-5 w-5 text-muted-foreground" />
                Subsystems
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <HealthCard 
                  title="Database" 
                  status={healthData.subsystems.database ? 'operational' : 'offline'} 
                  description="PostgreSQL connection and R/W access."
                  icon={<div className="font-bold">DB</div>}
                />
                <HealthCard 
                  title="LLM Cascade" 
                  status={healthData.subsystems.llms ? 'operational' : 'degraded'} 
                  description={`${healthData.llm_cascade.tiers_up} of ${healthData.llm_cascade.tiers_total} tiers active.`}
                  icon={<div className="font-bold">AI</div>}
                />
                <HealthCard 
                  title="Vector Store" 
                  status={healthData.subsystems.vector_store ? 'operational' : 'offline'} 
                  description="pgvector semantic search capability."
                  icon={<div className="font-bold">V</div>}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Circuit Breakers */}
              <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Icons.Warning className="h-5 w-5 text-muted-foreground" />
                  Circuit Breakers
                </h2>
                <div className="glass-card rounded-2xl p-6 border border-border/50 space-y-3">
                  {Object.entries(healthData.circuit_breakers).map(([tier, cb]: [string, any]) => (
                    <CircuitBreakerStatus
                      key={tier}
                      name={cb.name}
                      state={cb.state}
                      failureCount={cb.failure_count}
                      failureThreshold={cb.failure_threshold}
                    />
                  ))}
                </div>
              </div>

              {/* MCP Summary */}
              <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Icons.Tool className="h-5 w-5 text-muted-foreground" />
                  MCP Servers
                </h2>
                <div className="glass-card rounded-2xl p-6 border border-border/50">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <div className="text-3xl font-display font-bold">
                        {healthData.mcp_servers.connected} / {Object.keys(healthData.mcp_servers.status).length}
                      </div>
                      <div className="text-sm text-muted-foreground">Servers Connected</div>
                    </div>
                    <div>
                      <div className="text-3xl font-display font-bold text-right">
                        {healthData.mcp_servers.total_tools}
                      </div>
                      <div className="text-sm text-muted-foreground text-right">Available Tools</div>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleReloadMCP}
                    disabled={isReloading}
                    className="w-full flex justify-center items-center gap-2 py-3 rounded-xl bg-accent/10 text-accent font-semibold hover:bg-accent/20 transition-colors disabled:opacity-50"
                  >
                    <Icons.Reset className={`h-4 w-4 ${isReloading ? 'animate-spin' : ''}`} />
                    {isReloading ? 'Reloading...' : 'Reload All Servers'}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="text-center py-20 text-destructive">
            Failed to load health data. Ensure backend is running.
          </div>
        )}
      </main>
    </div>
  );
}
