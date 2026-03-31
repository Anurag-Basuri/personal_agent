import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
 
export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [Google],
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
      if (account && user) {
        token.accessToken = account.access_token // Google Access Token (optional)
        token.id_token = account.id_token
      }
      return token
    },
    async session({ session, token }) {
      // Pass the Google id_token to the frontend so it can be sent to FastAPI
      // FastAPI will decode it or we can just pass the NextAuth token.
      // Wait, Google id_token is a standard JWT!
      // If we pass the id_token, FastAPI can decode Google JWT easily using standard libraries.
      // But we built NextAuth JWE decoding.
      // Let's just create a custom token or pass the NextAuth session token.
      // Actually, passing the RAW NextAuth session encrypted string isn't easy via callbacks.
      // We will securely pass the Google id_token as the API Bearer token!
      (session as any).apiToken = token.id_token;
      return session
    }
  },
})
