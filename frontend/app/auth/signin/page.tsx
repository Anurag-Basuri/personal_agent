'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/hooks/useTheme';
import { Icons } from '@/components/ui/Icons';
import { Sun, Moon } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export default function SignInPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  const { resolvedTheme, toggleTheme } = useTheme();

  const handleCredentialsAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (!isLogin) {
        // Register flow
        const res = await fetch(`${API_BASE}/api/agent/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name }),
        });
        
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.message || 'Registration failed');
        }
      }

      // Login flow (runs after register too)
      const res: any = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });
      
      if (res?.error) {
        if (res.error.includes('CredentialsSignin')) {
          setError('Invalid email or password.');
        } else {
          setError('Authentication failed. Please try again.');
        }
      } else if (res?.ok) {
        router.push('/chat');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
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
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-4 shadow-inner shadow-primary/20">
              <Icons.Agent className="h-6 w-6" />
            </div>
            <h1 className="text-2xl font-display font-bold text-foreground text-center">
              Welcome Back
            </h1>
            <p className="text-sm text-muted-foreground mt-2 text-center">
              Sign in to your intelligent workspace
            </p>
          </div>

          <div className="flex bg-muted/50 p-1 rounded-xl mb-6">
            <button
              onClick={() => { setIsLogin(true); setError(''); }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${isLogin ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(''); }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${!isLogin ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleCredentialsAuth} className="space-y-4">
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-xl bg-destructive/10 p-3 border border-destructive/20 text-destructive text-sm"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {!isLogin && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-1"
              >
                <label className="text-xs font-semibold text-muted-foreground px-1">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={!isLogin}
                  className="w-full rounded-xl bg-background border border-border px-4 py-3 text-sm text-foreground focus-ring outline-none transition-all"
                  placeholder="John Doe"
                  disabled={isLoading}
                />
              </motion.div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground px-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-xl bg-background border border-border px-4 py-3 text-sm text-foreground focus-ring outline-none transition-all"
                placeholder="you@example.com"
                disabled={isLoading}
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground px-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-xl bg-background border border-border px-4 py-3 text-sm text-foreground focus-ring outline-none transition-all"
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="mt-6 w-full flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3.5 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none focus-ring outline-none"
            >
              {isLoading ? (
                <div className="h-5 w-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          <div className="relative mt-8 mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground tracking-widest font-semibold">Or</span>
            </div>
          </div>

          <button
            onClick={() => signIn('google', { callbackUrl: '/chat' })}
            className="w-full flex items-center justify-center gap-3 rounded-xl bg-background border border-border px-4 py-3.5 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-muted focus-ring outline-none"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>
          
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
