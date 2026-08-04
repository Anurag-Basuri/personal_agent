'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/hooks/useTheme';
import { useAdminAPI } from '@/hooks/useAdminAPI';
import { Icons } from '@/components/ui/Icons';
import { Sun, Moon } from 'lucide-react';

export default function AdminLoginPage() {
  const [adminId, setAdminId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { adminLogin } = useAdminAPI();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const success = await adminLogin(adminId, password);
      if (success) {
        router.push('/admin/dashboard');
      } else {
        setError('Invalid admin credentials.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during login.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-6 relative overflow-hidden transition-colors duration-300">
      {/* Background Mesh */}
      <div className="absolute inset-0 z-0 pointer-events-none gradient-mesh opacity-50 dark:opacity-100" />
      
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="absolute top-6 right-6 flex h-10 w-10 items-center justify-center rounded-full bg-card shadow-md border border-border text-foreground transition-colors hover:bg-muted focus-ring outline-none z-20"
        aria-label="Toggle theme"
      >
        {resolvedTheme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, type: 'spring' }}
        className="z-10 w-full max-w-md"
      >
        <div className="glass-card rounded-3xl p-8 shadow-2xl">
          <div className="flex flex-col items-center mb-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive mb-4">
              <Icons.Warning className="h-6 w-6" />
            </div>
            <h1 className="text-2xl font-display font-bold text-foreground text-center">
              Restricted Access
            </h1>
            <p className="text-sm text-muted-foreground mt-2 font-mono text-center">
              System Administration Level 5
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="rounded-xl bg-destructive/10 p-3 border border-destructive/20 text-destructive text-sm"
              >
                {error}
              </motion.div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest px-1">
                Admin ID
              </label>
              <input
                type="text"
                value={adminId}
                onChange={(e) => setAdminId(e.target.value)}
                required
                className="w-full rounded-xl bg-background border border-border px-4 py-3 text-sm text-foreground focus-ring outline-none transition-all"
                placeholder="Enter admin identifier"
                disabled={isLoading}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest px-1">
                Passkey
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-xl bg-background border border-border px-4 py-3 text-sm text-foreground focus-ring outline-none transition-all font-mono"
                placeholder="••••••••••••"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="mt-6 w-full flex items-center justify-center gap-2 rounded-xl bg-destructive px-4 py-3.5 text-sm font-bold text-destructive-foreground shadow-lg shadow-destructive/20 transition-all hover:bg-destructive/90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none focus-ring outline-none"
            >
              {isLoading ? (
                <div className="h-5 w-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                'Authenticate'
              )}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <a href="/" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              &larr; Return to public interface
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
