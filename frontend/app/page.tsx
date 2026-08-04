'use client';

import { motion, AnimatePresence, Variants } from 'framer-motion';
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

export default function LandingPage() {
  const { data: session } = useSession();

  return (
    <div className="relative min-h-screen bg-background selection:bg-primary/30 overflow-x-hidden transition-colors duration-300">
      {/* Animated Background Mesh */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none gradient-mesh opacity-50 dark:opacity-100 transition-opacity" />

      {/* Floating Orbs */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.3, 0.5, 0.3],
            x: [0, 50, 0],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px]"
        />
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.2, 0.4, 0.2],
            x: [0, -50, 0],
          }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-secondary/15 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.1, 0.3, 0.1],
            y: [0, -30, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
          className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-accent/15 rounded-full blur-[120px]"
        />
      </div>

      <TopNav />

      {/* Hero Section */}
      <main className="relative z-10 mx-auto max-w-7xl pt-40 pb-20 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center gap-8 text-center"
        >
          <motion.div variants={itemVariants}>
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-primary shadow-sm backdrop-blur-sm font-mono">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
              </span>
              Agentic Core 2.5
            </span>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="font-display text-5xl sm:text-7xl lg:text-8xl font-black tracking-tight text-foreground lg:leading-[1.1] max-w-5xl"
          >
            Your Intelligence, <br />
            <span className="gradient-text italic">Amplified.</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="max-w-2xl text-lg text-muted-foreground leading-relaxed text-balance"
          >
            An autonomous ecosystem designed to master your context. From technical deep-dives to seamless tool orchestration, experience the next generation of productivity.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="mt-6 flex flex-col items-center gap-5 sm:flex-row w-full sm:w-auto"
          >
            {session ? (
              <Link
                href="/chat"
                className="group flex h-14 w-full sm:w-auto items-center justify-center gap-3 rounded-full bg-primary px-10 text-base font-bold text-white shadow-lg shadow-primary/25 transition-all active:scale-95 hover:bg-primary/90 focus-ring outline-none"
              >
                Launch Console
                <Icons.Send className="h-4 w-4 transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
              </Link>
            ) : (
              <AuthButton className="h-14 px-10 text-base rounded-full shadow-xl" />
            )}
            <a
              href="https://github.com/Anurag-Basuri"
              target="_blank"
              rel="noreferrer"
              className="flex h-14 w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-border glass-subtle px-10 text-base font-bold text-foreground transition hover:bg-muted focus-ring outline-none"
            >
              Portfolio
            </a>
          </motion.div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8 }}
          className="mt-40 grid gap-6 md:grid-cols-3"
        >
          {[
            {
              icon: <Icons.Tool className="h-6 w-6 text-primary" />,
              title: 'Tool Orchestration',
              desc: 'Autonomous execution of GitHub fetches, API interactions, and complex pipeline logic with precision.',
            },
            {
              icon: <Icons.Check className="h-6 w-6 text-secondary" />,
              title: 'Contextual RAG',
              desc: 'Dynamic ingestion of resume, skill, and project data to provide highly personalized technical responses.',
            },
            {
              icon: <Icons.User className="h-6 w-6 text-accent" />,
              title: 'Omni-Memory',
              desc: 'Cross-transport persistence that remembers your preferences across Web and Telegram interfaces.',
            },
          ].map((feat, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -8, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="group relative overflow-hidden rounded-3xl glass-card p-10 transition-all hover:shadow-2xl hover:shadow-primary/10"
            >
              {/* Subtle background glow on hover */}
              <div className="absolute top-0 right-0 -mr-10 -mt-10 h-40 w-40 bg-primary/10 rounded-full blur-[50px] opacity-0 transition-opacity group-hover:opacity-100" />
              
              <div className="mb-8 inline-flex rounded-2xl glass-subtle p-4 ring-1 ring-white/10 dark:ring-white/5">
                {feat.icon}
              </div>
              <h3 className="mb-4 text-xl font-bold text-foreground tracking-tight">{feat.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {feat.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>
        
        {/* Footer */}
        <footer className="mt-40 border-t border-border/50 py-12 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2 opacity-50">
            <Icons.Agent className="h-5 w-5" />
            <span className="font-display font-bold">Personal Agent System</span>
          </div>
          <p className="text-sm text-muted-foreground font-mono">
            &copy; {new Date().getFullYear()} Anurag Basuri
          </p>
        </footer>
      </main>
    </div>
  );
}
