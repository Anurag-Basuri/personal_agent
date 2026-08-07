'use client';

import { motion, Variants, useMotionValue, useTransform, animate } from 'framer-motion';
import { AuthButton } from '@/components/auth/AuthButton';
import { Icons } from '@/components/ui/Icons';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import Image from 'next/image';
import { TopNav } from '@/components/layout/TopNav';
import { useEffect, useState, useRef } from 'react';
import {
  Github, Linkedin, Instagram, Code2, Twitter,
  Brain, Cpu, Database, Shield, Zap, Globe, MessageSquare,
  ArrowRight, Sparkles, ExternalLink, Bot
} from 'lucide-react';

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.15 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
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

const TERMINAL_LINES = [
  { type: 'input' as const, text: '> What can you do for me?' },
  { type: 'output' as const, text: 'I can search your GitHub repos, manage your calendar, send emails, run web searches, check LeetCode stats, and more.' },
  { type: 'input' as const, text: '> Summarize my latest project.' },
  { type: 'output' as const, text: 'Your latest project is "BuzzHive" — a full-stack social platform built with React, Node.js, and MongoDB. It features real-time chat, post feeds, and OAuth authentication.' },
  { type: 'input' as const, text: '> Schedule a reminder for tomorrow at 10 AM.' },
  { type: 'output' as const, text: '✓ Done. Reminder set for tomorrow at 10:00 AM via Google Calendar.' },
];

const SOCIAL_LINKS = [
  { href: 'https://anuragbasuri.vercel.app/portfolio', label: 'Portfolio', icon: ExternalLink },
  { href: 'https://github.com/Anurag-Basuri', label: 'GitHub', icon: Github },
  { href: 'https://www.linkedin.com/in/anuragbasuri/', label: 'LinkedIn', icon: Linkedin },
  { href: 'https://www.instagram.com/anuragbasuri/', label: 'Instagram', icon: Instagram },
  { href: 'https://leetcode.com/u/Anurag_Basuri/', label: 'LeetCode', icon: Code2 },
  { href: 'https://x.com/anurag_basuri', label: 'X / Twitter', icon: Twitter },
];

const LLM_CASCADE = [
  { name: 'GPT-4o', provider: 'GitHub Models', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  { name: 'Llama 3.3 70B', provider: 'GitHub Models', color: 'text-blue-500', bg: 'bg-blue-500/10 border-blue-500/20' },
  { name: 'GPT-4o Mini', provider: 'GitHub Models', color: 'text-teal-500', bg: 'bg-teal-500/10 border-teal-500/20' },
  { name: 'Llama 3.1 8B', provider: 'Groq', color: 'text-orange-500', bg: 'bg-orange-500/10 border-orange-500/20' },
  { name: 'Qwen2.5 72B', provider: 'HuggingFace', color: 'text-yellow-500', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  { name: 'Static Fallback', provider: 'Python', color: 'text-zinc-500', bg: 'bg-zinc-500/10 border-zinc-500/20' },
];

function TerminalAnimation() {
  const [visibleLines, setVisibleLines] = useState<number>(0);
  const [currentText, setCurrentText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    let charIndex = 0;

    function typeLine(lineIndex: number) {
      if (lineIndex >= TERMINAL_LINES.length) {
        timeout = setTimeout(() => {
          setVisibleLines(0);
          setCurrentText('');
          typeLine(0);
        }, 3000);
        return;
      }

      const line = TERMINAL_LINES[lineIndex];
      setIsTyping(true);
      charIndex = 0;

      function typeChar() {
        if (charIndex <= line.text.length) {
          setCurrentText(line.text.substring(0, charIndex));
          charIndex++;
          timeout = setTimeout(typeChar, line.type === 'input' ? 40 : 15);
        } else {
          setIsTyping(false);
          setVisibleLines(lineIndex + 1);
          setCurrentText('');
          timeout = setTimeout(() => typeLine(lineIndex + 1), line.type === 'input' ? 600 : 1200);
        }
      }

      typeChar();
    }

    timeout = setTimeout(() => typeLine(0), 1000);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [visibleLines, currentText]);

  const completedLines = TERMINAL_LINES.slice(0, visibleLines);
  const currentLine = visibleLines < TERMINAL_LINES.length ? TERMINAL_LINES[visibleLines] : null;

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="rounded-2xl overflow-hidden border border-zinc-200 dark:border-white/10 shadow-2xl bg-white dark:bg-zinc-950">
        {/* Window Chrome */}
        <div className="flex items-center gap-2 px-4 py-3 bg-zinc-50 dark:bg-zinc-900 border-b border-zinc-200 dark:border-white/10">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
          </div>
          <span className="text-xs font-mono text-muted-foreground ml-2">cortex-agent</span>
        </div>
        {/* Terminal Body */}
        <div ref={containerRef} className="p-5 font-mono text-sm space-y-3 h-64 overflow-y-auto">
          {completedLines.map((line, i) => (
            <div key={i} className={line.type === 'input' ? 'text-primary font-semibold' : 'text-muted-foreground pl-2 border-l-2 border-primary/20'}>
              {line.text}
            </div>
          ))}
          {currentLine && currentText && (
            <div className={currentLine.type === 'input' ? 'text-primary font-semibold' : 'text-muted-foreground pl-2 border-l-2 border-primary/20'}>
              {currentText}
              <span className="inline-block w-2 h-4 bg-primary/60 ml-0.5 animate-pulse align-middle" />
            </div>
          )}
          {!currentText && isTyping && (
            <div className="flex items-center gap-1 pl-2">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnimatedCounter({ target, suffix = '' }: { target: number; suffix?: string }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v));
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const controls = animate(count, target, { duration: 2, ease: 'easeOut' });
    const unsubscribe = rounded.on('change', (v) => setDisplay(v));
    return () => { controls.stop(); unsubscribe(); };
  }, [count, rounded, target]);

  return <span>{display}{suffix}</span>;
}

export default function LandingPage() {
  const { data: session } = useSession();

  return (
    <div className="relative min-h-screen bg-background selection:bg-primary/20 overflow-x-hidden transition-colors duration-500">
      {/* Background Mesh */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none gradient-mesh" />
      
      {/* Floating Ambient Orbs */}
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

      {/* ========== HERO ========== */}
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
              Autonomous Agent System
            </span>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="font-display text-5xl sm:text-7xl lg:text-8xl font-black tracking-tight text-foreground leading-[1.05] max-w-5xl"
          >
            Anurag&apos;s{' '}
            <span className="gradient-text italic">Cortex.</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="max-w-2xl text-lg sm:text-xl text-muted-foreground leading-relaxed text-balance font-medium"
          >
            An AI-powered autonomous ecosystem that thinks, acts, and remembers.
            From deep code analysis to seamless tool orchestration across 18+ integrations.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="mt-4 flex flex-col items-center gap-4 sm:flex-row w-full sm:w-auto"
          >
            {session ? (
              <Link
                href="/chat"
                className="group flex h-14 w-full sm:w-auto items-center justify-center gap-3 rounded-full bg-primary px-8 text-base font-bold text-white shadow-xl shadow-primary/20 transition-all active:scale-95 hover:bg-primary/90 focus-ring outline-none"
              >
                Launch Console
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <AuthButton className="h-14 px-8 text-base rounded-full shadow-xl" />
            )}
            <a
              href="https://anuragbasuri.vercel.app/portfolio"
              target="_blank"
              rel="noreferrer"
              className="flex h-14 w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-zinc-200 dark:border-white/10 bg-white/50 dark:bg-white/5 backdrop-blur-md px-8 text-base font-bold text-foreground shadow-sm transition-all hover:bg-zinc-50 dark:hover:bg-white/10 focus-ring outline-none"
            >
              View Portfolio
              <ExternalLink className="h-4 w-4" />
            </a>
          </motion.div>

          {/* Stats Bar */}
          <motion.div
            variants={itemVariants}
            className="mt-8 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-center"
          >
            {[
              { value: 6, suffix: '', label: 'LLM Layers' },
              { value: 18, suffix: '+', label: 'Tool Integrations' },
              { value: 3, suffix: '', label: 'Access Tiers' },
              { value: 99.9, suffix: '%', label: 'Uptime Target' },
            ].map((stat, i) => (
              <div key={i} className="flex flex-col items-center">
                <span className="font-display text-3xl sm:text-4xl font-black text-foreground">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix} />
                </span>
                <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mt-1">{stat.label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* ========== TERMINAL DEMO ========== */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-32"
        >
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">See It In Action</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">
              Watch the agent process real queries in real-time.
            </p>
          </div>
          <TerminalAnimation />
        </motion.section>

        {/* ========== BENTO GRID: CAPABILITIES ========== */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">Core Capabilities</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">Not just another chatbot. An autonomous engine.</p>
          </div>

          {/* Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Large Card: Tool Orchestration */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="lg:col-span-2 group rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-8 transition-all hover:shadow-2xl hover:shadow-primary/5 hover:border-primary/20 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
              <div className="relative">
                <div className="mb-6 inline-flex rounded-2xl bg-primary/10 border border-primary/20 p-4">
                  <Zap className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-3 text-xl font-bold text-foreground tracking-tight">Tool Orchestration</h3>
                <p className="text-base leading-relaxed text-muted-foreground font-medium mb-6">
                  Autonomous execution across 18+ integrations. GitHub, Vercel, Notion, Google Calendar, Telegram, and custom MCP pipelines — all orchestrated by LangGraph.
                </p>
                <div className="flex flex-wrap gap-2">
                  {['GitHub', 'Calendar', 'Email', 'Telegram', 'Web Search', 'LeetCode', 'Wikipedia', 'Notion'].map((tool) => (
                    <span key={tool} className="px-3 py-1 rounded-full text-xs font-semibold bg-zinc-100 dark:bg-white/5 text-muted-foreground border border-zinc-200 dark:border-white/8">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Contextual RAG */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="group rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-8 transition-all hover:shadow-2xl hover:shadow-secondary/5 hover:border-secondary/20 relative overflow-hidden"
            >
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-secondary/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 pointer-events-none" />
              <div className="relative">
                <div className="mb-6 inline-flex rounded-2xl bg-secondary/10 border border-secondary/20 p-4">
                  <Database className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="mb-3 text-xl font-bold text-foreground tracking-tight">Contextual RAG</h3>
                <p className="text-base leading-relaxed text-muted-foreground font-medium">
                  pgvector-powered semantic search over resume, projects, and skills. Deeply personalized responses grounded in real data.
                </p>
              </div>
            </motion.div>

            {/* Persistent Memory */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="group rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-8 transition-all hover:shadow-2xl hover:shadow-accent/5 hover:border-accent/20 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-48 h-48 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2 pointer-events-none" />
              <div className="relative">
                <div className="mb-6 inline-flex rounded-2xl bg-accent/10 border border-accent/20 p-4">
                  <Brain className="h-6 w-6 text-accent" />
                </div>
                <h3 className="mb-3 text-xl font-bold text-foreground tracking-tight">Persistent Memory</h3>
                <p className="text-base leading-relaxed text-muted-foreground font-medium">
                  Cross-session summarization and preference extraction. Remembers context across Web, Telegram, and every future transport.
                </p>
              </div>
            </motion.div>

            {/* LLM Cascade — Wide */}
            <motion.div
              whileHover={{ y: -4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="lg:col-span-2 group rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-8 transition-all hover:shadow-2xl hover:shadow-primary/5 relative overflow-hidden"
            >
              <div className="relative">
                <div className="mb-6 inline-flex rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-4">
                  <Cpu className="h-6 w-6 text-emerald-500" />
                </div>
                <h3 className="mb-3 text-xl font-bold text-foreground tracking-tight">6-Layer LLM Cascade</h3>
                <p className="text-base leading-relaxed text-muted-foreground font-medium mb-6">
                  Intelligent fallback ensures you always get a response. Each tier has an independent circuit breaker.
                </p>
                <div className="flex flex-wrap gap-2">
                  {LLM_CASCADE.map((llm, i) => (
                    <div key={i} className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${llm.bg}`}>
                      <span className={`text-xs font-bold ${llm.color}`}>{llm.name}</span>
                      <span className="text-[10px] text-muted-foreground">{llm.provider}</span>
                      {i < LLM_CASCADE.length - 1 && (
                        <ArrowRight className="h-3 w-3 text-muted-foreground/40 hidden sm:block" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </motion.section>

        {/* ========== ARCHITECTURE ========== */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">Security & Architecture</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">
              Strict RBAC segregation with physically isolated routing tiers.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                tier: 'Public Tier',
                prefix: '/api/public/*',
                desc: 'Ephemeral sessions. 20 message cap. Portfolio-safe tools only. No authentication required.',
                icon: <Globe className="h-5 w-5" />,
                color: 'text-emerald-600 dark:text-emerald-400',
                accent: 'from-emerald-500/20 to-emerald-500/0',
                border: 'hover:border-emerald-500/30',
                iconBg: 'bg-emerald-500/10 border-emerald-500/20',
              },
              {
                tier: 'Agent Tier',
                prefix: '/api/agent/*',
                desc: 'Authenticated users. One continuous conversation per account. Full RAG context and memory.',
                icon: <MessageSquare className="h-5 w-5" />,
                color: 'text-violet-600 dark:text-violet-400',
                accent: 'from-violet-500/20 to-violet-500/0',
                border: 'hover:border-violet-500/30',
                iconBg: 'bg-violet-500/10 border-violet-500/20',
              },
              {
                tier: 'Admin Tier',
                prefix: '/api/admin/*',
                desc: 'Exclusive to Anurag. Unrestricted access to ALL tools, MCP management, and system health.',
                icon: <Shield className="h-5 w-5" />,
                color: 'text-rose-600 dark:text-rose-400',
                accent: 'from-rose-500/20 to-rose-500/0',
                border: 'hover:border-rose-500/30',
                iconBg: 'bg-rose-500/10 border-rose-500/20',
              },
            ].map((t, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -4 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                className={`rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-8 transition-all hover:shadow-xl relative overflow-hidden ${t.border}`}
              >
                <div className={`absolute inset-0 bg-linear-to-b ${t.accent} pointer-events-none`} />
                <div className="relative">
                  <div className={`mb-5 inline-flex rounded-2xl border p-3.5 ${t.iconBg}`}>
                    <div className={t.color}>{t.icon}</div>
                  </div>
                  <div className={`font-display font-black text-xl mb-2 ${t.color}`}>{t.tier}</div>
                  <div className="inline-block px-3 py-1 rounded-lg bg-zinc-100 dark:bg-white/5 border border-zinc-200 dark:border-white/8 mb-4">
                    <code className={`text-xs font-bold font-mono ${t.color}`}>{t.prefix}</code>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground font-medium">{t.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* ========== CREATOR / PORTFOLIO ========== */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mt-40"
        >
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl sm:text-4xl font-black text-foreground tracking-tight">The Creator</h2>
            <p className="mt-4 text-base text-muted-foreground max-w-lg mx-auto font-medium">
              Built from scratch by Anurag Basuri.
            </p>
          </div>

          <div className="relative rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-white/8 p-10 sm:p-14 overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-primary/5 via-transparent to-secondary/5 pointer-events-none" />
            <div className="relative flex flex-col lg:flex-row items-center gap-10">
              {/* Avatar */}
              <div className="relative shrink-0">
                <div className="relative h-32 w-32 rounded-3xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 overflow-hidden shadow-xl flex items-center justify-center">
                  <Image src="/logo.png" alt="Anurag Basuri" width={80} height={80} className="object-contain drop-shadow-[0_0_12px_rgba(139,92,246,0.5)]" />
                </div>
                <div className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full bg-success border-4 border-white dark:border-zinc-900 flex items-center justify-center">
                  <Sparkles className="h-3.5 w-3.5 text-white" />
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 text-center lg:text-left">
                <h3 className="font-display text-2xl sm:text-3xl font-black text-foreground tracking-tight mb-3">
                  Anurag Basuri
                </h3>
                <p className="text-base text-muted-foreground font-medium leading-relaxed mb-6 max-w-xl">
                  Full-stack engineer obsessed with autonomous systems, AI infrastructure, and building things that think for themselves.
                  This entire ecosystem — from the LangGraph agent to the circuit breakers to this UI — is a solo build.
                </p>
                <div className="flex flex-wrap gap-3 justify-center lg:justify-start">
                  {SOCIAL_LINKS.map((link) => (
                    <a
                      key={link.label}
                      href={link.href}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-muted-foreground hover:text-foreground bg-zinc-100 dark:bg-white/5 border border-zinc-200 dark:border-white/8 hover:border-primary/30 hover:bg-primary/5 transition-all outline-none focus-ring"
                    >
                      <link.icon className="h-4 w-4" />
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.section>

        {/* ========== CTA ========== */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-40 text-center"
        >
          <div className="relative overflow-hidden rounded-[2.5rem] bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 p-16 sm:p-20 shadow-2xl">
            <div className="absolute inset-0 bg-linear-to-b from-primary/10 to-transparent pointer-events-none" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.08),transparent_70%)] pointer-events-none" />
            
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
                <Bot className="h-3.5 w-3.5" />
                Ready to explore?
              </div>
              <h2 className="font-display text-4xl sm:text-5xl font-black text-foreground tracking-tight mb-4">
                Start a Conversation.
              </h2>
              <p className="text-lg text-muted-foreground mb-10 max-w-lg mx-auto font-medium">
                Sign in and experience an AI agent that actually understands your context.
              </p>
              {session ? (
                <Link
                  href="/chat"
                  className="inline-flex h-14 items-center justify-center gap-3 rounded-full bg-primary px-10 text-base font-bold text-white shadow-xl shadow-primary/20 transition-all hover:bg-primary/90 focus-ring outline-none hover:scale-105 active:scale-95"
                >
                  Launch Console
                  <ArrowRight className="h-4 w-4" />
                </Link>
              ) : (
                <AuthButton className="h-14 px-10 text-base rounded-full shadow-xl" />
              )}
            </div>
          </div>
        </motion.section>

        {/* ========== FOOTER ========== */}
        <footer className="mt-24 border-t border-zinc-200 dark:border-white/10 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden">
                <Image src="/logo.png" alt="Cortex Logo" width={20} height={20} className="object-contain" />
              </div>
              <span className="font-display font-bold text-base text-foreground tracking-tight">Anurag&apos;s Cortex</span>
            </div>

            <div className="flex items-center gap-4">
              {SOCIAL_LINKS.slice(0, 4).map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground bg-zinc-100 dark:bg-white/5 border border-zinc-200 dark:border-white/8 hover:border-primary/30 transition-all outline-none focus-ring"
                  aria-label={link.label}
                >
                  <link.icon className="h-4 w-4" />
                </a>
              ))}
            </div>

            <p className="text-sm text-muted-foreground font-mono font-medium">
              &copy; {new Date().getFullYear()} Anurag Basuri
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
