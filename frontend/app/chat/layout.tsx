import { auth } from "@/auth"

export default async function ChatLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();

  // If we wanted to protect this purely on server components level we could redirect here, 
  // but we will use middleware.ts for global protection.
  
  return <>{children}</>
}
