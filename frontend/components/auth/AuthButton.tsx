'use client';

import { signIn, signOut, useSession } from "next-auth/react"
import { Icons } from "@/components/ui/Icons";
import { cn } from "@/utils/cn";
import { useRouter, usePathname } from 'next/navigation';
import { LogOut } from 'lucide-react';

export function AuthButton({ className }: { className?: string }) {
  const { data: session, status } = useSession()
  const router = useRouter();
  const pathname = usePathname();

  if (status === "loading") {
    return <div className={cn("h-8 w-24 rounded-xl bg-zinc-200 dark:bg-white/10 animate-pulse", className)} />
  }

  const handleAvatarClick = () => {
    if (pathname !== '/chat') {
      router.push('/chat');
    }
  };

  if (session) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div 
          className={cn(
            "flex items-center gap-2.5 group",
            pathname !== '/chat' ? "cursor-pointer" : "cursor-default"
          )} 
          onClick={handleAvatarClick}
        >
          {session.user?.image ? (
            <img src={session.user.image} alt="User Avatar" className="h-7 w-7 rounded-full border border-zinc-200 dark:border-white/10 shadow-sm group-hover:ring-2 ring-primary/50 transition-all" />
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 dark:bg-primary/15 text-primary group-hover:bg-primary group-hover:text-white transition-all">
              <Icons.User className="h-3.5 w-3.5" />
            </div>
          )}
          <span className="text-sm font-medium hidden sm:inline-block text-foreground/80 group-hover:text-foreground transition-colors">{session.user?.name}</span>
        </div>
        <button 
          onClick={() => signOut({ callbackUrl: '/' })} 
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground/60 hover:text-destructive/80 transition-all focus-ring outline-none rounded-lg px-2 py-1.5 hover:bg-destructive/5"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={() => router.push('/auth/signin')}
      className={cn(
        "flex h-9 items-center justify-center gap-2 rounded-xl bg-foreground px-5 text-sm font-medium text-background shadow-md transition-all hover:bg-foreground/90 hover:shadow-lg hover:-translate-y-0.5 focus-ring outline-none",
        className
      )}
    >
      Sign In
    </button>
  )
}
