import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import { SignJWT } from "jose"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000"

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_CLIENT_ID,
      clientSecret: process.env.AUTH_GOOGLE_CLIENT_SECRET,
    }),
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null

        try {
          const res = await fetch(`${API_URL}/api/agent/auth/verify`, {
            method: 'POST',
            body: JSON.stringify(credentials),
            headers: { "Content-Type": "application/json" }
          })
          
          const responseData = await res.json()
          
          if (res.ok && responseData?.data) {
            return responseData.data
          }
          return null
        } catch (e) {
          console.error("Auth verify error:", e)
          return null
        }
      }
    })
  ],
  secret: process.env.AUTH_SECRET,
  pages: {
    signIn: '/',
    error: '/',
  },
  callbacks: {
    authorized: async ({ auth }) => {
      return !!auth
    },
    async jwt({ token, account, user }) {
      // If user is logging in (account and user are available on sign-in)
      if (user) {
        // We generate a unified backend token for ALL providers
        const secret = new TextEncoder().encode(process.env.AUTH_SECRET)
        const alg = 'HS256'
        
        const backendToken = await new SignJWT({ 
            email: user.email, 
            name: user.name,
            sub: user.id 
          })
          .setProtectedHeader({ alg })
          .setIssuedAt()
          .setExpirationTime('24h')
          .sign(secret)

        token.apiToken = backendToken
      }
      return token
    },
    async session({ session, token }) {
      // Expose the unified token to the client via session
      // The frontend sends this as `Authorization: Bearer <apiToken>` to FastAPI
      (session as any).apiToken = token.apiToken as string;
      return session
    }
  },
})
