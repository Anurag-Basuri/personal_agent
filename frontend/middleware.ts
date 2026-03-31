import { auth } from "@/auth"

export default auth((req) => {
  const isAuth = !!req.auth
  const isChatPage = req.nextUrl.pathname.startsWith('/chat')

  if (isChatPage && !isAuth) {
    // Redirect unauthenticated users back to landing page
    return Response.redirect(new URL('/', req.nextUrl))
  }
})

// Optionally, don't invoke Middleware on some paths
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
