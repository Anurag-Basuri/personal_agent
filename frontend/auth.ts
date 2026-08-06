import NextAuth, { CredentialsSignin } from "next-auth"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import { SignJWT } from "jose"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

class CustomAuthError extends CredentialsSignin {
  constructor(msg: string) {
    super();
    this.code = msg;
  }
}

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
          
          throw new CustomAuthError(responseData?.message || "Invalid credentials")
        } catch (e: any) {
          if (e instanceof CustomAuthError) {
            throw e
          }
          console.error("Auth verify error:", e)
          return null
        }
      }
    })
  ],
  secret: process.env.AUTH_SECRET || "fje9j3r29fj94j3o2fj304jf9e0jflsfjd2lkjsdf92",
  trustHost: true,
  pages: {
    signIn: '/auth/signin',
    error: '/auth/signin',
  },
  callbacks: {
    authorized: async ({ auth }) => {
      return !!auth
    },
    async jwt({ token, account, user }) {
      const secretKey = process.env.AUTH_SECRET || "fje9j3r29fj94j3o2fj304jf9e0jflsfjd2lkjsdf92";
      const secret = new TextEncoder().encode(secretKey)
      const alg = 'HS256'

      // On initial sign-in, capture the user's identity into the NextAuth token
      if (user) {
        token.email = user.email
        token.name = user.name
        token.sub = user.id
      }

      // Check if apiToken needs minting or refreshing
      let needsRefresh = !token.apiToken

      if (token.apiToken && !needsRefresh) {
        try {
          // Decode without verification to check expiry
          const [, payloadB64] = (token.apiToken as string).split('.')
          const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString())
          const expiresAt = payload.exp * 1000
          const oneHourFromNow = Date.now() + (60 * 60 * 1000)
          if (expiresAt < oneHourFromNow) {
            needsRefresh = true
          }
        } catch {
          needsRefresh = true
        }
      }

      if (needsRefresh && token.email) {
        token.apiToken = await new SignJWT({
            email: token.email,
            name: token.name,
            sub: token.sub
          })
          .setProtectedHeader({ alg })
          .setIssuedAt()
          .setExpirationTime('24h')
          .sign(secret)
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
