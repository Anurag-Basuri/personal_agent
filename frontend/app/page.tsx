'use client';

import { motion, Variants } from 'framer-motion';
import { AuthButton } from '@/components/auth/AuthButton';
import { Icons } from '@/components/ui/Icons';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { TopNav } from '@/components/layout/TopNav';

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } },
};

const FEATURES = [
  {
    icon: <Icons.Tool className="h-6 w-6 text-primary" />,
    title: 'Tool Orchestration',
    desc: 'Autonomous execution across 18+ MCP servers, GitHub, Vercel, Notion, Google Calendar, and custom pipelines.',
  },
  {
    icon: <Icons.Check className="h-6 w-6 text-secondary" />,
    title: 'Contextual RAG',
    desc: 'pgvector-powered semantic search over resume, projects, and skills data for deeply personalized responses.',
  },
  {
    icon: <Icons.User className="h-6 w-6 text-accent" />,
    title: 'Persistent Memory',
    desc: 'Cross-transport conversation summarization and preference extraction. Remembers context across Web and Telegram.',
  },
];

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'You Send a Message',
    desc: 'Your message is encrypted (AES-256-GCM), sent to the backend, and routed through strict RBAC.',
  },
  {
    step: '02',
    title: 'Agent Thinks & Acts',
    desc: 'LangGraph orchestrates a multi-step reasoning loop. The agent decides which tools to call, executes them, and synthesizes results.',
  },
  {
    step: '03',
    title: 'LLM Cascade Responds',
    desc: 'A 6-layer fallback cascade (GPT-4o → Llama 3.3 70B → Groq → HF) ensures you always get a response.',
  },
  {
    step: '04',
    title: 'Memory Persists',
    desc: 'Conversations are summarized and stored in pgvector for long-term RAG retrieval across sessions.',
  },
];

const TECH_STACK = [
  { category: 'Frontend', items: ['Next.js 16', 'React 19', 'Zustand', 'Framer Motion', 'Tailwind CSS'] },
  { category: 'Backend', items: ['FastAPI', 'LangGraph', 'SQLAlchemy', 'Pydantic'] },
  { category: 'AI / LLM', items: ['GPT-4o', 'Llama 3.3 70B', 'Groq', 'HuggingFace', 'Circuit Breakers'] },
  { category: 'Infrastructure', items: ['PostgreSQL', 'pgvector', 'Neon DB', 'MCP Protocol', 'Telegram Bot'] },
];

export default function LandingPage() {
  const { data: session } = useSession();

  return (
    <div className="relative min-h-screen bg-background selection:bg-primary/20 overflow-x-hidden transition-colors duration-500">
      {/* Background Mesh */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none gradient-mesh" />
      
      {/* Floating Ambient Orbs (Subtle) */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none mix-blend-screen dark:mix-blend-color-dodge">
        <motion.div
          animate={{ scale: [1, 1.05, 1], opacity: [0.1, 0.15, 0.1], x: [0, 30, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px]"
        />
        <motion.div
          animate={{ scale: [1, 1.1, 1], opacity: [0.08, 0.12, 0.08], x: [0, -30, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-secondary/15 rounded-full blur-[100px]"
        />
      </div>

      <TopNav />

      {/* Hero */}
      <main className="relative z-10 mx-auto max-w-6xl pt-36 pb-24 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center gap-8 text-center"
        >
          <motion.div variants={itemVariants}>
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.25em] text-primary shadow-sm backdrop-blur-md font-mono">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
              </span>
              Neural Agent System 2.5
            </span>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="font-display text-5xl sm:text-7xl lg:text-8xl font-black tracking-tight text-foreground leading-[1.05] max-w-5xl drop-shadow-sm"
          >
            Intelligence, <br />
            <span className="gradient-text italic pr-2">Amplified.</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="max-w-2xl text-lg sm:text-xl text-muted-foreground leading-relaxed text-balance font-medium"
          >
            An autonomous ecosystem designed to master your context. From technical deep-dives to seamless tool orchestration, experience the next generation of productivity.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="mt-6 flex flex-col items-center gap-4 sm:flex-row w-full sm:w-auto"
          >
            {session ? (
              <Link
                href="/chat"
                className="group flex h-14 w-full sm:w-auto items-center justify-center gap-3 rounded-full bg-primary px-8 text-base font-bold text-white shadow-xl shadow-primary/20 transition-all active:scale-95 hover:bg-primary/90 focus-ring outline-none"
              >
                Launch Console
                <Icons.Send className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <AuthButton className="h-14 px-8 text-base rounded-full shadow-xl" />
            )}
            <a
              href="https://github.com/Anurag-Basuri/personal_agent"
              target="_blank"
              rel="noreferrer"
              className="flex h-14 w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-zinc-200 dark:border-white/10 bg-white/50 dark:bg-white/5 backdrop-blur-md px-8 text-base font-bold text-foreground shadow-sm transition-all hover:bg-zinc-50 dark:hover:bg-white/10 focus-ring outline-none"
            >
              View Source
            </a>
          </motion.div>
        </motion.div>

        {/* Features */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">Core Capabilities</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">Built for engineers, not just another chatbot.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {FEATURES.map((feat, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -5, scale: 1.01 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                className="group rounded-3xl bg-white dark:bg-zinc-900/40 border border-zinc-200 dark:border-white/10 p-8 transition-all hover:shadow-2xl hover:shadow-primary/5 hover:border-zinc-300 dark:hover:border-primary/30"
              >
                <div className="mb-6 inline-flex rounded-2xl bg-zinc-50 dark:bg-white/5 border border-zinc-100 dark:border-white/10 p-4 shadow-sm">
                  {feat.icon}
                </div>
                <h3 className="mb-3 text-xl font-bold text-foreground tracking-tight">{feat.title}</h3>
                <p className="text-base leading-relaxed text-muted-foreground font-medium">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* How It Works */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">How It Works</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">The pipeline from request to autonomous execution.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 relative">
            <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-zinc-200 dark:via-border to-transparent -translate-y-1/2 -z-10" />
            {HOW_IT_WORKS.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                className="flex flex-col items-center text-center rounded-3xl bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md border border-zinc-200 dark:border-white/10 p-8 shadow-sm hover:shadow-xl transition-shadow"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white shadow-lg shadow-primary/30 font-display font-black text-lg mb-6">
                  {step.step}
                </div>
                <h3 className="font-bold text-foreground text-lg mb-3 tracking-tight">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground font-medium">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Architecture */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">Security & Architecture</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">Strict RBAC segregation with independent routing tiers.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              { tier: 'Public Tier', prefix: '/api/public/*', desc: 'Ephemeral sessions. 20 message cap. Safe portfolio tools only.', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200/50 dark:border-emerald-800/30' },
              { tier: 'Agent Tier', prefix: '/api/agent/*', desc: 'Authenticated users. Continuous conversation, full RAG context.', color: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-50/50 dark:bg-violet-950/20 border-violet-200/50 dark:border-violet-800/30' },
              { tier: 'Admin Tier', prefix: '/api/admin/*', desc: 'Exclusive access. Unrestricted tools, MCP management, system health.', color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-50/50 dark:bg-rose-950/20 border-rose-200/50 dark:border-rose-800/30' },
            ].map((t, i) => (
              <div key={i} className={`rounded-3xl border p-8 shadow-sm transition-all hover:shadow-md ${t.bg}`}>
                <div className={`font-display font-black text-xl mb-2 ${t.color}`}>{t.tier}</div>
                <div className="inline-block px-3 py-1 rounded-md bg-white/80 dark:bg-black/20 border border-black/5 dark:border-white/5 mb-4">
                  <code className={`text-xs font-bold font-mono ${t.color}`}>{t.prefix}</code>
                </div>
                <p className="text-base leading-relaxed text-muted-foreground font-medium">{t.desc}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Tech Stack */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">Built With</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">A modern, production-grade technology stack.</p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {TECH_STACK.map((group, i) => (
              <div key={i} className="rounded-3xl bg-white dark:bg-zinc-900/40 border border-zinc-200 dark:border-white/10 p-8 shadow-sm">
                <h3 className="font-bold text-foreground text-sm uppercase tracking-widest mb-6 font-mono opacity-80">{group.category}</h3>
                <div className="flex flex-col gap-3">
                  {group.items.map((item) => (
                    <div key={item} className="flex items-center gap-3">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary/50" />
                      <span className="text-sm font-semibold text-muted-foreground">
                        {item}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        {/* CTA */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-40 text-center"
        >
          <div className="relative overflow-hidden rounded-[2.5rem] bg-zinc-100 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 p-16 sm:p-20 shadow-2xl">
            {/* Dark CTA Background Glow */}
            <div className="absolute inset-0 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none" />
            
            <div className="relative z-10">
              <h2 className="font-display text-4xl sm:text-5xl font-black text-foreground tracking-tight mb-4">
                Ready to explore?
              </h2>
              <p className="text-lg text-muted-foreground mb-10 max-w-lg mx-auto font-medium">
                Sign in to your account and experience the future of autonomous agents.
              </p>
              {session ? (
                <Link
                  href="/chat"
                  className="inline-flex h-14 items-center justify-center gap-3 rounded-full bg-primary px-10 text-base font-bold text-white shadow-xl shadow-primary/20 transition-all hover:bg-primary/90 focus-ring outline-none hover:scale-105 active:scale-95"
                >
                  Launch Console
                  <Icons.Send className="h-4 w-4" />
                </Link>
              ) : (
                <AuthButton className="h-14 px-10 text-base rounded-full shadow-xl" />
              )}
            </div>
          </div>
        </motion.section>

        {/* Footer */}
        <footer className="mt-24 border-t border-zinc-200 dark:border-white/10 py-12 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-foreground text-background">
              <Icons.Agent className="h-4 w-4" />
            </div>
            <span className="font-display font-bold text-base text-foreground tracking-tight">Personal Agent</span>
          </div>
          <p className="text-sm text-muted-foreground font-mono font-medium">
            &copy; {new Date().getFullYear()} Anurag Basuri
          </p>
        </footer>
      </main>
    </div>
  );
}
