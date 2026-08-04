'use client';

import { signIn, signOut, useSession } from "next-auth/react"
import { Icons } from "@/components/ui/Icons";
import { cn } from "@/utils/cn";
import { useRouter } from 'next/navigation';

export function AuthButton({ className }: { className?: string }) {
  const { data: session, status } = useSession()
  const router = useRouter();

  if (status === "loading") {
    return <div className={cn("h-10 w-24 rounded-full bg-zinc-200 animate-pulse", className)} />
  }

  if (session) {
    return (
      <div className={cn("flex items-center gap-4", className)}>
        <div className="flex items-center gap-2 group cursor-pointer" onClick={() => router.push('/chat')}>
          {session.user?.image ? (
            <img src={session.user.image} alt="User Avatar" className="h-8 w-8 rounded-full border border-border shadow-sm group-hover:ring-2 ring-primary/50 transition-all" />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-all">
              <Icons.User className="h-4 w-4" />
            </div>
          )}
          <span className="text-sm font-medium hidden sm:inline-block text-foreground group-hover:text-primary transition-colors">{session.user?.name}</span>
        </div>
        <button 
          onClick={() => signOut({ callbackUrl: '/' })} 
          className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors focus-ring outline-none rounded-md px-2 py-1"
        >
          Sign out
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={() => router.push('/auth/signin')}
      className={cn(
        "flex h-10 items-center justify-center gap-2 rounded-full bg-foreground px-6 text-sm font-medium text-background shadow-md transition-all hover:bg-foreground/90 hover:shadow-lg hover:-translate-y-0.5 focus-ring outline-none",
        className
      )}
    >
      Sign In
    </button>
  )
}
