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
      // On initial sign-in, capture the Google ID token
      if (account && user) {
        token.id_token = account.id_token
      }
      return token
    },
    async session({ session, token }) {
      // Expose the Google ID token to the client via session
      // The frontend sends this as `Authorization: Bearer <id_token>` to FastAPI
      (session as any).apiToken = token.id_token as string;
      return session
    }
  },
})
